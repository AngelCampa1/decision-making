"""Tests for the CLI gate.

The subprocess-running steps are exercised through the integration path rather
than mocked here; what these tests pin down is the logic that decides pass or
fail — particularly the git-identity guard, whose whole job is to refuse.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from decision_evals import cli
from decision_evals.adjudication import AdjudicationIssue
from decision_evals.cli import (
    StepResult,
    _first_line,
    _summarise,
    app,
    check_adjudication_step,
    check_corrections_step,
    check_decisions_step,
    check_drift_step,
    check_git_identity,
    check_provenance_step,
    check_sync_step,
    check_tailoring_step,
    check_wiring_step,
    drift_movements,
    gate_steps,
    lint_skills_step,
    repository_facts,
    validate_manifests_step,
)
from decision_evals.corpora import CorpusError
from decision_evals.corrections import CorrectionIssue
from decision_evals.decisions import DecisionIssue
from decision_evals.deployed import DeployState
from decision_evals.drift import DriftIssue, Movement
from decision_evals.provenance import ProvenanceIssue, discover_runs
from decision_evals.provenance import RunRecord as ProvenanceRun
from decision_evals.site import INPUTS_PATH as SITE_INPUTS_PATH
from decision_evals.site import MANIFEST_PATH as SITE_MANIFEST_PATH
from decision_evals.site import render_manifest
from decision_evals.sync import SyncIssue
from decision_evals.wiring import WiringIssue

runner = CliRunner()


@dataclass(frozen=True)
class _Completed:
    """Stand-in for `subprocess.CompletedProcess` where only the code matters."""

    returncode: int


#: What ``de check`` ran, in order, on the commit before the steps became data.
#: Pinned so that the change making them enumerable is provably a refactor.
#: Changing the gate means changing this list in the same commit, which is the
#: point: the list is small enough to read and the diff says what moved.
GATE_STEPS = (
    ("git identity", True),
    ("ruff check", True),
    ("ruff format", True),
    ("mypy", True),
    ("skill lint", True),
    ("trigger sets", True),
    ("tailoring corpus", True),
    ("plugin manifests", True),
    ("citations", True),
    ("run provenance", True),
    ("integrity wiring", True),
    ("decision register", True),
    ("label corrections", True),
    ("label adjudication", True),
    ("checkpoint label versions", True),
    ("documentation", True),
    ("published claims", True),
    ("generated regions", True),
    ("site", False),
    ("document drift", False),
    ("pytest", False),
    ("coverage floors", False),
)


class TestTheStepTable:
    def test_runs_the_same_steps_in_the_same_order(self) -> None:
        assert [(step.name, step.fast) for step in gate_steps()] == list(GATE_STEPS)

    def test_fast_drops_exactly_four(self) -> None:
        steps = gate_steps()
        assert len(steps) == 21
        assert sum(1 for step in steps if step.fast) == 17

    def test_enumerating_the_gate_does_not_run_it(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A document can state the steps without paying for them.

        The callables come back unevaluated. Were the table to run anything on
        construction, rendering the gate into a document would run the gate.
        """

        def explode(*args: object, **kwargs: object) -> StepResult:
            raise AssertionError("constructing the step table ran a step")

        monkeypatch.setattr(cli, "_run", explode)
        assert len(gate_steps()) == 21


class TestDocumentDrift:
    """The half in the CLI: what git is asked, and what is done when it cannot answer."""

    def test_a_document_naming_nothing_has_not_moved(self) -> None:
        """No dependencies, no git call, and zero rather than unknown."""
        assert cli._commits_touching("650dcbc", ()) == 0

    def test_a_commit_git_does_not_know_reads_as_unknown(self) -> None:
        assert cli._commits_touching("0000000", ("README.md",)) is None

    def test_a_real_range_counts(self) -> None:
        count = cli._commits_touching("650dcbc", ("evals/src/decision_evals/cli.py",))
        assert count is not None
        assert count >= 1

    def test_no_git_means_no_movement(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A source tarball has no history, and the gate has to run there."""
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        assert drift_movements() == {}

    def test_this_repository_is_read(self) -> None:
        assert check_drift_step().passed

    def test_the_step_reports_what_it_refuses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli,
            "check_drift",
            lambda repo_root, movements: [DriftIssue("docs/STATUS.md", "is unread")],
        )
        result = check_drift_step()
        assert not result.passed
        assert result.detail == "1 issue(s)"

    def test_drift_says_when_nothing_has_moved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cli, "drift_movements", dict)
        result = runner.invoke(app, ["drift"])
        assert result.exit_code == 0
        assert "nothing has moved" in result.output

    def test_drift_names_the_paths_and_the_line_to_paste(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        paths = tuple(f"evals/src/decision_evals/m{n}.py" for n in range(8))
        monkeypatch.setattr(
            cli,
            "drift_movements",
            lambda: {
                "docs/ARCHITECTURE.md": Movement("docs/ARCHITECTURE.md", "650dcbc", 12, paths),
                "docs/STATUS.md": Movement("docs/STATUS.md", "650dcbc", None, ("a.py",)),
            },
        )
        result = runner.invoke(app, ["drift"])
        assert result.exit_code == 0
        assert "12 commit(s) since 650dcbc" in result.output
        assert "and 2 more" in result.output
        assert "unknown commit(s)" in result.output
        assert '"docs/ARCHITECTURE.md" = "' in result.output


class TestGeneratedRegions:
    """The half of `de sync` that lives in the CLI: what the facts are gathered from."""

    def test_a_docstring_first_line_is_the_summary(self) -> None:
        assert _first_line("Does a thing.\n\nAt length.\n") == "Does a thing."

    def test_no_docstring_is_an_empty_summary(self) -> None:
        assert _first_line(None) == ""
        assert _first_line("   ") == ""

    def test_the_facts_come_from_the_live_app(self) -> None:
        """Not from parsed source. Adding a subcommand grows the table in the same run."""
        facts = repository_facts()
        names = [command.name for command in facts.commands]
        assert names == sorted(names)
        assert "sync" in names
        assert [step.name for step in facts.steps] == [step.name for step in gate_steps()]
        assert all(command.summary for command in facts.commands)

    def test_the_arms_carry_their_purpose(self) -> None:
        assert dict(repository_facts().arms)["in_situ"]

    def test_this_repository_is_current(self) -> None:
        assert check_sync_step().passed

    def test_the_step_reports_what_it_refuses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli, "check_sync", lambda repo_root, facts: [SyncIssue("README.md", "is stale")]
        )
        result = check_sync_step()
        assert not result.passed
        assert result.detail == "1 issue(s)"

    def test_sync_says_what_it_wrote(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(cli, "sync_regions", lambda repo_root, facts: ["docs/ARCHITECTURE.md"])
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0
        assert "docs/ARCHITECTURE.md" in result.output

    def test_sync_says_when_there_was_nothing_to_write(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cli, "sync_regions", lambda repo_root, facts: [])
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0
        assert "already matches" in result.output


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

        assert not cli._run("failing", [sys.executable, "-c", "raise SystemExit(3)"]).passed

    def test_detects_a_zero_exit_code(self) -> None:

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


class TestTailoringStep:
    """Wiring for the ``datasets/tailoring/`` shortcut battery.

    ``check_tailoring_step`` delegates its logic to
    ``decision_evals.tailoring``, which carries its own thorough tests
    (``tests/unit/test_tailoring_battery.py``, including the real corpus's
    known-bad register split and a known-good synthetic case). What is worth
    pinning down here is the wiring itself: the step passes on an empty or
    absent corpus, fails when the battery finds something, and does not choke
    on a triplet the battery had to skip.
    """

    def _write_variant(self, tailoring: Path, filename: str, arm: str, prompt: str) -> None:
        (tailoring / filename).write_text(
            yaml.safe_dump({"arm": arm, "prompt": prompt}), encoding="utf-8"
        )

    def test_passes_when_no_corpus_is_present(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        assert check_tailoring_step().passed

    def test_passes_on_a_corpus_with_no_surface_shortcut(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Two triplets, the same two shapes with governing/matched swapped.

        Same construction ``test_tailoring_battery.py`` uses for its
        known-good fixture: swapping which shape is governing and which is
        matched makes every feature's pooled AUC exactly 0.5, which is the
        only way one CLI-level test can assert a pass without duplicating the
        battery's own known-good coverage.
        """
        tailoring = tmp_path / "datasets" / "tailoring"
        tailoring.mkdir(parents=True)
        shape_a = "Intro.\n- One.\n- The vendor confirmed delivery next Tuesday.\n- Two.\nOutro.\n"
        shape_b = "Intro.\n- One.\n- On 2025-03-14 the committee approved a small budget.\n- Two.\nOutro.\n"
        self._write_variant(tailoring, "t1-base.yaml", "base", "Intro.\n- One.\n- Two.\nOutro.\n")
        self._write_variant(tailoring, "t1-governing.yaml", "governing", shape_a)
        self._write_variant(tailoring, "t1-matched.yaml", "matched", shape_b)
        self._write_variant(tailoring, "t2-base.yaml", "base", "Intro.\n- One.\n- Two.\nOutro.\n")
        self._write_variant(tailoring, "t2-governing.yaml", "governing", shape_b)
        self._write_variant(tailoring, "t2-matched.yaml", "matched", shape_a)
        (tailoring / "index.yaml").write_text(
            yaml.safe_dump(
                {
                    "triplets": [
                        {
                            "id": "t1",
                            "files": ["t1-base.yaml", "t1-governing.yaml", "t1-matched.yaml"],
                        },
                        {
                            "id": "t2",
                            "files": ["t2-base.yaml", "t2-governing.yaml", "t2-matched.yaml"],
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        assert check_tailoring_step().passed

    def test_fails_when_the_battery_finds_a_shortcut(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        tailoring = tmp_path / "datasets" / "tailoring"
        tailoring.mkdir(parents=True)
        self._write_variant(tailoring, "t1-base.yaml", "base", "Intro.\n- One.\n- Two.\nOutro.\n")
        self._write_variant(
            tailoring,
            "t1-governing.yaml",
            "governing",
            "Intro.\n- One.\n- Clause 9.4 forfeits the balance on breach of the covenant.\n"
            "- Two.\nOutro.\n",
        )
        self._write_variant(
            tailoring, "t1-matched.yaml", "matched", "Intro.\n- One.\n- Hi.\n- Two.\nOutro.\n"
        )
        (tailoring / "index.yaml").write_text(
            yaml.safe_dump(
                {
                    "triplets": [
                        {
                            "id": "t1",
                            "files": ["t1-base.yaml", "t1-governing.yaml", "t1-matched.yaml"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = check_tailoring_step()
        assert not result.passed
        assert "issue" in result.detail

    def test_a_malformed_triplet_is_skipped_rather_than_crashing_the_step(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        tailoring = tmp_path / "datasets" / "tailoring"
        tailoring.mkdir(parents=True)
        (tailoring / "index.yaml").write_text(
            yaml.safe_dump({"triplets": [{"id": "broken", "files": ["missing.yaml"]}]}),
            encoding="utf-8",
        )
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = check_tailoring_step()
        assert result.passed

    def test_the_real_corpus_is_baselined_rather_than_failing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No monkeypatching: the register split the battery was built to
        catch is on disk right now, and it is exactly what
        ``datasets/tailoring/corpus-baseline.txt`` defers -- the corpus is
        committed as evidence of a failed authoring pass, not a defect to
        chase, and re-adding it here would be re-declaring the step's own
        purpose. The finding must still be visible: printed as
        ``known-open (baselined)`` rather than swallowed, the same contract
        ``check_triggers_step`` gives its own baseline.
        """
        result = check_tailoring_step()
        assert result.passed
        assert "known-open (baselined)" in capsys.readouterr().out


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


class TestCorrectionsStep:
    def test_the_repository_accounts_for_its_own_version_bumps(self) -> None:
        assert check_corrections_step().passed

    def test_it_fails_on_an_undeclared_bump(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import decision_evals.corrections as corrections

        monkeypatch.setattr(
            corrections,
            "check_corrections",
            lambda root, version: [CorrectionIssue("datasets/triggers/corrections.jsonl", "gap")],
        )
        result = check_corrections_step()
        assert not result.passed
        assert "1 issue" in result.detail

    def test_a_set_that_will_not_load_contributes_no_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """It is `check_triggers_step`'s job to report that, not this one.

        Failing here too would turn one broken corpus file into two red steps
        and send a reader to the wrong one.
        """
        import decision_evals.triggers as triggers

        def refuse(path: object) -> object:
            raise triggers.TriggerSetError("unreadable")

        monkeypatch.setattr(triggers, "load_trigger_set", refuse)
        # Every set refuses, so the version is unknown and the transition checks
        # are skipped. Defaulting to 1 instead would report all three committed
        # lines as ahead of the corpus, which is three errors about the wrong
        # thing in the wrong step.
        assert check_corrections_step().passed


class TestAdjudicationStep:
    def test_the_repository_has_adjudicated_its_own_answer_keys(self) -> None:
        assert check_adjudication_step().passed

    def test_it_fails_on_an_unadjudicated_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli,
            "check_adjudication",
            lambda root, corpora, runs: [
                AdjudicationIssue("datasets/triggers/x.yaml", "uncovered")
            ],
        )
        result = check_adjudication_step()
        assert not result.passed
        assert "1 issue" in result.detail

    def test_a_set_that_will_not_load_contributes_no_corpus(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """It is `check_triggers_step`'s job to report that, not this one."""
        import decision_evals.triggers as triggers

        def refuse(path: object) -> object:
            raise triggers.TriggerSetError("unreadable")

        monkeypatch.setattr(triggers, "load_trigger_set", refuse)
        # No corpus loads, so nothing is uncovered. The baselined key then names
        # no set that loaded, which is the one refusal left standing.
        result = check_adjudication_step()
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


def _site_project(root: Path, *, installed: bool = False) -> None:
    """A repository with a site project and one document the site renders."""
    (root / "site").mkdir(exist_ok=True)
    (root / SITE_INPUTS_PATH).write_text('{"content": ["*.md"]}', encoding="utf-8")
    (root / "README.md").write_text("# readme\n", encoding="utf-8")
    if installed:
        (root / "site" / "node_modules").mkdir(exist_ok=True)


class TestSiteStep:
    """The gate half. Pure Python, so every branch runs without a Node toolchain."""

    def test_absent_site_is_a_no_op(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """The gate shipped before the site did, so it has to be green without one."""
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = cli.check_site_step()
        assert result.passed
        assert result.detail == ""

    def test_a_stale_build_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        _site_project(tmp_path)
        result = cli.check_site_step()
        assert not result.passed
        assert "1 issue" in result.detail

    def test_a_fresh_build_passes(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        _site_project(tmp_path)
        (tmp_path / SITE_MANIFEST_PATH).write_text(render_manifest(tmp_path), encoding="utf-8")
        assert cli.check_site_step().passed

    def test_the_real_repository_is_current(self) -> None:
        """No monkeypatching. A published site older than its inputs is a failure."""
        assert cli.check_site_step().passed


class TestSiteCommand:
    """The build half.

    `npm` is stubbed rather than run: what these pin down is the ordering that
    makes the manifest trustworthy. A manifest written before a failed build is
    a green gate over a site that does not exist, and nothing downstream can
    tell the difference afterwards.
    """

    def test_refuses_without_a_site_directory(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        result = runner.invoke(app, ["site"])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_refuses_without_npm(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        _site_project(tmp_path)
        monkeypatch.setattr(cli.shutil, "which", lambda _: None)
        result = runner.invoke(app, ["site"])
        assert result.exit_code == 1
        assert "npm is not on PATH" in result.output

    def test_a_failed_install_leaves_the_manifest_alone(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        _site_project(tmp_path)
        monkeypatch.setattr(cli.shutil, "which", lambda _: "npm")
        monkeypatch.setattr(cli.subprocess, "run", lambda *a, **k: _Completed(1))
        result = runner.invoke(app, ["site"])
        assert result.exit_code == 1
        assert "npm ci failed" in result.output
        assert not (tmp_path / SITE_MANIFEST_PATH).exists()

    def test_a_failed_build_leaves_the_manifest_alone(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        _site_project(tmp_path, installed=True)
        monkeypatch.setattr(cli.shutil, "which", lambda _: "npm")
        monkeypatch.setattr(cli.subprocess, "run", lambda *a, **k: _Completed(1))
        result = runner.invoke(app, ["site"])
        assert result.exit_code == 1
        assert "the manifest is unchanged" in result.output
        assert not (tmp_path / SITE_MANIFEST_PATH).exists()

    def test_a_successful_build_writes_the_manifest_and_clears_the_caches(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The caches go first because Astro will otherwise serve markdown
        rendered by the previous version of the link-rewrite plugin, which is a
        stale page that looks perfectly fine."""
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        _site_project(tmp_path, installed=True)
        for stale in (".astro-cache", ".astro", "dist"):
            (tmp_path / "site" / stale).mkdir()
        monkeypatch.setattr(cli.shutil, "which", lambda _: "npm")
        calls: list[list[str]] = []

        def fake_run(command: list[str], **kwargs: object) -> _Completed:
            calls.append(command)
            return _Completed(0)

        monkeypatch.setattr(cli.subprocess, "run", fake_run)
        result = runner.invoke(app, ["site"])

        assert result.exit_code == 0, result.output
        assert calls == [["npm", "run", "build"]]
        assert not (tmp_path / "site" / ".astro-cache").exists()
        assert not (tmp_path / "site" / "dist").exists()
        assert (tmp_path / SITE_MANIFEST_PATH).read_text(encoding="utf-8") == render_manifest(
            tmp_path
        )
        assert "not published" in result.output

    def test_the_deploy_flag_is_gone(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Publishing moved to `.github/workflows/deploy-site.yml` on
        2026-08-19. The flag force-pushed whatever local HEAD happened to be,
        which published a build of a feature branch once before it was removed,
        so this asserts it cannot quietly come back."""
        monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
        _site_project(tmp_path, installed=True)
        monkeypatch.setattr(cli.shutil, "which", lambda _: "npm")
        monkeypatch.setattr(cli.subprocess, "run", lambda *a, **k: _Completed(0))

        result = runner.invoke(app, ["site", "--deploy"])
        assert result.exit_code != 0
        # Rich renders this error into a panel, wraps it to the terminal width
        # and styles the option name, which puts escape sequences *between* the
        # two dashes -- so the literal `--deploy` is not in `output` on a
        # coloured terminal even though it is plainly on screen. The first two
        # CI runs failed here while every local run passed. Strip the escapes
        # and unwrap before asserting on text.
        plain = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
        plain = " ".join(plain.split())
        # Specifically rejected as an unknown option, rather than failing for
        # any of the several other reasons `de site` can fail.
        assert "No such option" in plain
        assert "--deploy" in plain


class TestDeployedCommand:
    """Wiring only. The readings themselves are covered in `test_deployed.py`."""

    def test_a_current_site_exits_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli, "check_deployed", lambda root: DeployState(cli.DEPLOY_CURRENT, "current")
        )
        result = runner.invoke(app, ["deployed"])
        assert result.exit_code == 0
        assert "current" in result.output

    def test_a_stale_site_exits_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            cli, "check_deployed", lambda root: DeployState(cli.DEPLOY_BEHIND, "behind")
        )
        assert runner.invoke(app, ["deployed"]).exit_code == 1

    def test_an_unaskable_site_exits_two_rather_than_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The distinction the command exists to preserve: not knowing is not
        the same as being up to date."""
        monkeypatch.setattr(
            cli, "check_deployed", lambda root: DeployState("unreachable", "no answer")
        )
        assert runner.invoke(app, ["deployed"]).exit_code == 2
