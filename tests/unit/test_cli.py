"""Tests for the CLI gate.

The subprocess-running steps are exercised through the integration path rather
than mocked here; what these tests pin down is the logic that decides pass or
fail — particularly the git-identity guard, whose whole job is to refuse.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from decision_evals import cli
from decision_evals.cli import (
    StepResult,
    _summarise,
    app,
    check_decisions_step,
    check_git_identity,
    check_provenance_step,
    check_wiring_step,
    lint_skills_step,
    validate_manifests_step,
)
from decision_evals.corpora import CorpusError
from decision_evals.decisions import DecisionIssue
from decision_evals.provenance import ProvenanceIssue, discover_runs
from decision_evals.provenance import RunRecord as ProvenanceRun
from decision_evals.wiring import WiringIssue

runner = CliRunner()


class TestGitIdentityGuard:
    def test_passes_with_a_valid_repo_local_identity(self) -> None:
        """The repository itself must satisfy the guard."""
        result = check_git_identity()
        assert result.passed, result.detail

    def test_rejects_a_forbidden_domain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli,
            "_git_output",
            lambda args: (
                "angel.campa@ventoralabs.com" if args == ["config", "user.email"] else "Angel Campa"
            ),
        )
        result = check_git_identity()
        assert not result.passed
        assert "ventoralabs.com" in result.detail
        assert "git config user.email" in result.detail

    def test_rejects_a_missing_email(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cli, "_git_output", lambda args: None)
        result = check_git_identity()
        assert not result.passed
        assert "user.email is not set" in result.detail

    def test_rejects_a_missing_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli,
            "_git_output",
            lambda args: "someone@example.com" if args == ["config", "user.email"] else None,
        )
        result = check_git_identity()
        assert not result.passed
        assert "user.name is not set" in result.detail

    def test_skips_outside_a_git_repository(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = check_git_identity()
        assert result.passed
        assert result.detail == "not a git repository"

    def test_git_output_returns_none_on_failure(self) -> None:
        assert cli._git_output(["config", "--get", "no.such.key.exists"]) is None


class TestSkillLint:
    def test_reports_no_directory(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = lint_skills_step()
        assert result.passed
        assert result.detail == "no skills directory"

    def test_reports_an_empty_directory(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        (tmp_path / "skills").mkdir()
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = lint_skills_step()
        assert result.passed
        assert result.detail == "no skills"

    def test_an_incomplete_skill_fails_the_gate(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Was written against the stub validator, which passed anything.

        Now that the validator is real, a skill with nothing but a name is
        exactly what the gate exists to stop.
        """
        skill = tmp_path / "skills" / "evidence-ledger"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: evidence-ledger\n---\n", encoding="utf-8")
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = lint_skills_step()
        assert not result.passed
        assert "issue(s)" in (result.detail or "")

    def test_the_real_skills_directory_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No monkeypatching: the shipped skills must satisfy the shipped gate."""
        assert lint_skills_step().passed


class TestManifestValidation:
    """Cheap because it reads two JSON files — no model call, no network."""

    def test_reports_no_manifests(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = validate_manifests_step()
        assert result.passed
        assert result.detail == "no manifests"

    def test_reports_a_missing_claude_cli(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Fails rather than skips: an unvalidated manifest is what installers hit."""
        (tmp_path / ".claude-plugin").mkdir()
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(cli.shutil, "which", lambda _: None)
        result = validate_manifests_step()
        assert not result.passed
        assert "not on PATH" in result.detail

    def test_a_rejected_manifest_fails_the_gate(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        (tmp_path / ".claude-plugin").mkdir()
        (tmp_path / ".claude-plugin" / "marketplace.json").write_text("{}", encoding="utf-8")
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = validate_manifests_step()
        assert not result.passed
        assert "rejected" in (result.detail or "")

    def test_the_real_manifests_validate(self) -> None:
        """No monkeypatching. Shells out to the real `claude plugin validate`."""
        assert validate_manifests_step().passed


class TestSummary:
    def test_returns_zero_when_everything_passes(self) -> None:
        assert _summarise([StepResult("a", True), StepResult("b", True)]) == 0

    def test_returns_one_when_any_step_fails(self) -> None:
        assert _summarise([StepResult("a", True), StepResult("b", False, "broke")]) == 1


class TestCommands:
    def test_lint_command_exits_cleanly(self) -> None:
        assert runner.invoke(app, ["lint"]).exit_code == 0

    def test_mirror_command_is_a_no_op_on_a_synced_tree(self) -> None:
        """If this writes anything, a mirror was committed stale."""
        result = runner.invoke(app, ["mirror"])
        assert result.exit_code == 0
        assert "0 mirror(s) updated" in result.stdout

    def test_help_lists_the_gate_commands(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "check" in result.stdout
        assert "lint" in result.stdout


class TestRunStep:
    def test_reports_a_missing_command_rather_than_raising(self) -> None:
        result = cli._run("bogus", ["definitely-not-a-real-binary-xyz"])
        assert not result.passed
        assert "command not found" in result.detail

    def test_detects_a_non_zero_exit_code(self) -> None:
        import sys

        assert not cli._run("failing", [sys.executable, "-c", "raise SystemExit(3)"]).passed

    def test_detects_a_zero_exit_code(self) -> None:
        import sys

        assert cli._run("passing", [sys.executable, "-c", "pass"]).passed


class TestCheckCitationsStep:
    """The gate step, including the truncation branch.

    Worth testing rather than trusting: this step is the only thing standing
    between a misattributed figure and the file the repository calls the
    product, and it was added after three such figures shipped.
    """

    @staticmethod
    def _repo(root: Path, *, doc: str, bib: str, baseline: str = "") -> None:
        (root / "docs").mkdir(exist_ok=True)
        (root / "docs" / "x.md").write_text(doc, encoding="utf-8")
        (root / "paper").mkdir(exist_ok=True)
        (root / "paper" / "refs.bib").write_text(bib, encoding="utf-8")
        (root / "paper" / "citations-baseline.txt").write_text(baseline, encoding="utf-8")

    _BIB = "@article{a,\n journal = {arXiv preprint arXiv:2605.24050},\n quote = {x}\n}\n"

    def test_passes_when_every_citation_resolves(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._repo(tmp_path, doc="Degrades 21% (arXiv:2605.24050).", bib=self._BIB)
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        assert cli.check_citations_step().passed

    def test_fails_on_a_number_without_a_quote(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        bib = "@article{a,\n journal = {arXiv preprint arXiv:2605.24050}\n}\n"
        self._repo(tmp_path, doc="Degrades 21% (arXiv:2605.24050).", bib=bib)
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = cli.check_citations_step()
        assert not result.passed
        assert "1 issue" in result.detail

    def test_truncates_a_long_issue_list(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A wall of 60 identical lines buries the first one, which is the useful one."""
        doc = "\n".join(f"arXiv:26{index:02d}.11111" for index in range(25))
        self._repo(tmp_path, doc=doc, bib=self._BIB)
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = cli.check_citations_step()
        assert not result.passed
        assert "25 issue(s)" in result.detail


class TestFetch:
    """The vendoring command.

    The network call is stubbed. What is worth pinning down is that the command
    verifies *after* writing, so a corrupted or redirected download cannot leave
    a plausible-looking file in the vendor directory and exit zero.
    """

    _PAYLOAD = b'[{"task_id": "t", "task": "math", "shards": ["a"]}]'

    @staticmethod
    def _lock(root: Path, payload: bytes, *, sha: str | None = None) -> None:
        import hashlib
        import json as _json

        (root / "datasets" / "vendor").mkdir(parents=True, exist_ok=True)
        (root / "datasets" / "vendor" / "lost_in_conversation.lock.json").write_text(
            _json.dumps(
                {
                    "repo": "microsoft/lost_in_conversation",
                    "commit": "c" * 40,
                    "member": "data/sharded_instructions_600.json",
                    "size_bytes": len(payload),
                    "sha256": sha or hashlib.sha256(payload).hexdigest(),
                    "code_license": "MIT",
                    "data_license": "CDLA-Permissive-2.0",
                    "retrieved": "2026-08-11",
                }
            ),
            encoding="utf-8",
        )

    def _stub_urlopen(self, monkeypatch: pytest.MonkeyPatch, payload: bytes) -> list[str]:
        import contextlib
        import urllib.request

        called: list[str] = []

        @contextlib.contextmanager
        def fake(url: str):  # type: ignore[no-untyped-def]
            called.append(url)

            class _Response:
                @staticmethod
                def read() -> bytes:
                    return payload

            yield _Response()

        monkeypatch.setattr(urllib.request, "urlopen", fake)
        return called

    def test_downloads_and_verifies(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        self._lock(tmp_path, self._PAYLOAD)
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        called = self._stub_urlopen(monkeypatch, self._PAYLOAD)

        result = runner.invoke(app, ["fetch"])
        assert result.exit_code == 0, result.output
        assert "verified" in result.output
        assert len(called) == 1
        assert called[0].startswith("https://raw.githubusercontent.com/")

    def test_a_second_run_is_a_no_op(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        self._lock(tmp_path, self._PAYLOAD)
        (tmp_path / "datasets" / "vendor" / "sharded_instructions_600.json").write_bytes(
            self._PAYLOAD
        )
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        called = self._stub_urlopen(monkeypatch, self._PAYLOAD)

        result = runner.invoke(app, ["fetch"])
        assert result.exit_code == 0
        assert "already matches the lock" in result.output
        assert called == []

    def test_force_re_downloads_an_already_valid_copy(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._lock(tmp_path, self._PAYLOAD)
        (tmp_path / "datasets" / "vendor" / "sharded_instructions_600.json").write_bytes(
            self._PAYLOAD
        )
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        called = self._stub_urlopen(monkeypatch, self._PAYLOAD)

        result = runner.invoke(app, ["fetch", "--force"])
        assert result.exit_code == 0
        assert len(called) == 1

    def test_a_download_that_does_not_match_the_lock_fails_loudly(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The case this command exists for: something else arrived."""
        self._lock(tmp_path, self._PAYLOAD, sha="a" * 64)
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        self._stub_urlopen(monkeypatch, self._PAYLOAD)

        result = runner.invoke(app, ["fetch"])
        assert result.exit_code != 0
        assert isinstance(result.exception, CorpusError)

    def test_a_missing_lock_is_refused_before_any_network_call(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        called = self._stub_urlopen(monkeypatch, self._PAYLOAD)

        result = runner.invoke(app, ["fetch"])
        assert result.exit_code != 0
        assert called == []


class TestPower:
    """The MDE table.

    The headline figures are pinned here because they are transcribed into
    `docs/RESEARCH_PROGRAMME.md`, and a hand-copied power figure is the same
    class of error as a hand-copied citation.
    """

    def test_it_prints_a_table(self) -> None:
        result = runner.invoke(app, ["power"])
        assert result.exit_code == 0
        assert "n_pairs" in result.output
        assert "percentage points" in result.output

    def test_twelve_items_cannot_detect_most_effects(self) -> None:
        """The finding: at the old corpus size, most columns are undetectable."""
        result = runner.invoke(app, ["power"])
        twelve = next(
            line for line in result.output.splitlines() if line.strip().startswith("12 |")
        )
        assert twelve.count("n/a") == 4

    def test_the_vendored_corpus_size_is_well_powered(self) -> None:
        from decision_evals.stats import minimum_detectable_effect

        # 527 = 627 records minus the Unix-only `code` family.
        assert minimum_detectable_effect(527, 0.30).effect * 100 < 10.0

    def test_the_design_effect_option_inflates_the_mde(self) -> None:
        plain = runner.invoke(app, ["power"]).output
        clustered = runner.invoke(app, ["power", "--design-effect", "2.0"]).output
        assert plain != clustered
        assert "design_effect=2.0" in clustered


class TestProvenanceStep:
    """The gate over published run records.

    Exercised against the real repository rather than a fixture, because the
    claim worth pinning is that the tree it ships with satisfies its own rule —
    the same reason `check_git_identity` is tested that way above.
    """

    def test_the_repository_passes_its_own_provenance_gate(self) -> None:
        assert check_provenance_step().passed

    def test_it_fails_when_a_run_is_defective(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli, "check_provenance", lambda root, git: [ProvenanceIssue("results/x", "broken")]
        )
        result = check_provenance_step()
        assert not result.passed
        assert "1 issue" in result.detail

    def test_a_stale_index_fails_the_step(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A run published without appearing in the index is a failing build."""
        monkeypatch.setattr(cli, "index_is_current", lambda root: False)
        assert not check_provenance_step().passed

    def test_index_regenerates_the_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = runner.invoke(app, ["index"])
        assert result.exit_code == 0
        assert (tmp_path / "docs" / "RUN_INDEX.md").is_file()


class TestGitFacts:
    def test_a_commit_is_its_own_ancestor(self) -> None:
        """What lets a run register its prediction in the commit that runs it."""
        head = cli._git_output(["rev-parse", "--short", "HEAD"])
        assert head is not None
        assert cli._is_ancestor(head, head)

    def test_an_unknown_commit_is_not_an_ancestor(self) -> None:
        assert not cli._is_ancestor("0" * 40, "HEAD")

    def test_it_reports_unavailable_outside_a_repository(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        assert not cli._gather_git_facts([]).available

    def test_it_dates_the_real_predictions(self) -> None:
        facts = cli._gather_git_facts(discover_runs(cli.REPO_ROOT))
        assert facts.available
        assert facts.first_commit
        assert facts.ancestry

    def test_a_run_without_a_readme_is_skipped(self, tmp_path: Path) -> None:
        run = ProvenanceRun(path="results/x/y", name="y", readme=tmp_path / "gone.md", jsonl=())
        assert cli._gather_git_facts([run]).first_commit == {}


class TestWiringStep:
    def test_the_repository_passes_its_own_wiring_gate(self) -> None:
        assert check_wiring_step().passed

    def test_it_fails_on_an_inert_integrity_lock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli, "check_wiring", lambda root: [WiringIssue("decision_evals.prereg", "inert")]
        )
        result = check_wiring_step()
        assert not result.passed
        assert "1 issue" in result.detail


class TestDecisionsStep:
    def test_the_repository_explains_its_own_governed_commits(self) -> None:
        assert check_decisions_step().passed

    def test_it_fails_on_an_unexplained_commit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli, "check_decisions", lambda root, governed: [DecisionIssue("d43c490", "unexplained")]
        )
        result = check_decisions_step()
        assert not result.passed
        assert "1 issue" in result.detail

    def test_governed_commits_are_found_in_the_real_history(self) -> None:
        commits = cli._governed_commits()
        assert commits
        assert all(len(commit.sha) == 7 and commit.date.count("-") == 2 for commit in commits)

    def test_no_governed_commits_outside_a_repository(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cli, "_git_output", lambda args: None)
        assert cli._governed_commits() == []

    def test_a_malformed_log_line_is_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cli, "_git_output", lambda args: "no-pipes-here\nabc1234|2026-08-13|x")
        assert [c.sha for c in cli._governed_commits()] == ["abc1234"]
