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
    check_git_identity,
    lint_skills_step,
    validate_manifests_step,
)
from decision_evals.corpora import CorpusError

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
