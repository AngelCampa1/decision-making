"""Tests for the `git-hygiene` pre-commit hook in `scripts/check_git_hygiene.py`.

No repository on this machine is touched. Every test builds a throwaway git
repository under `tmp_path`, and an autouse fixture points `GIT_CONFIG_GLOBAL`
and `GIT_CONFIG_SYSTEM` at an empty file so that the maintainer's own settings
-- `init.defaultBranch`, `commit.gpgsign`, hooks -- cannot decide whether these
pass.

Two invariants are under test, and they are unrelated except that one script
carries both.

**The drift half is a hook, and its load-bearing step is the fetch.** Refusing a
commit on `main` while `main` is behind `origin/main` is worth nothing if the
comparison runs against a remote-tracking ref that was last updated an hour ago:
the check would pass on exactly the stale `main` it exists to catch, and pass
silently. So the central test here
(`test_the_refusal_comes_from_the_fetch_not_from_the_ref_on_disk`) asserts the
on-disk ref says *zero behind* before the script runs and that the script
refuses anyway. Without the fetch that test passes the commit, which is the
estimator-returns-a-plausible-zero failure this repository keeps hitting.

**The `core.bare` half is not a hook and cannot be one** -- with `core.bare`
set, git aborts a commit before any hook is invoked. It is reached only through
`--doctor`/`--fix`, and `TestPlainRunNeverChecksBare` pins that, so nobody later
reads the `--doctor` tests as evidence that a commit is guarded.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
    """Import ``scripts/check_git_hygiene.py``, which is not part of the package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "check_git_hygiene.py"
    spec = importlib.util.spec_from_file_location("check_git_hygiene", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_git_hygiene"] = module
    spec.loader.exec_module(module)
    return module


hygiene = _load()


# --------------------------------------------------------------------------- #
# Sandbox: git that cannot read, write or be steered by anything on this machine
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point every git subprocess at an empty global and system config.

    Identity comes from the environment rather than `git config user.*` so that
    a repository can be created and committed to in two calls, and so that no
    test depends on a config file it did not write.
    """
    empty = tmp_path / "gitconfig-empty"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "hygiene test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "hygiene@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "hygiene test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "hygiene@example.invalid")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    # The developer running the suite may have the bypass exported.
    monkeypatch.delenv(hygiene.OVERRIDE_ENV, raising=False)


def _git(cwd: Path, *args: str) -> str:
    """Run git in ``cwd``, failing the test loudly rather than silently."""
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {cwd}:\n{proc.stderr}")
    return proc.stdout.strip()


def _commit(repo: Path, text: str, message: str) -> None:
    (repo / "f.txt").write_text(text, encoding="utf-8")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "--quiet", "-m", message)


def _standalone(root: Path, name: str = "solo") -> Path:
    """A repository with one commit on `main` and no remote."""
    repo = root / name
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "main")
    _commit(repo, "1\n", "c1")
    return repo


def _upstream_with_seed(root: Path) -> tuple[Path, Path]:
    """A bare `origin` holding one commit on `main`, plus the clone that pushes to it."""
    upstream = root / "upstream.git"
    _git(root, "init", "--quiet", "--bare", "-b", "main", str(upstream))
    seed = root / "seed"
    _git(root, "clone", "--quiet", str(upstream), str(seed))
    _commit(seed, "1\n", "c1")
    _git(seed, "push", "--quiet", "origin", "main")
    return upstream, seed


def _clone(root: Path, upstream: Path, name: str) -> Path:
    path = root / name
    _git(root, "clone", "--quiet", str(upstream), str(path))
    return path


def _behind(repo: Path) -> int:
    """How far `main` trails `origin/main` *according to the refs on disk*."""
    counts = _git(repo, "rev-list", "--left-right", "--count", "main...origin/main")
    return int(counts.split()[1])


# --------------------------------------------------------------------------- #
# The drift half: refuse a commit on a stale `main`
# --------------------------------------------------------------------------- #


class TestMainBehindOriginIsRefused:
    def test_one_commit_behind_is_named_with_the_catch_up_command(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")

        monkeypatch.chdir(work)
        problems = hygiene.check_main_drift()

        assert problems
        assert "main is 1 commit(s) behind origin/main." in problems[0]
        assert any("git pull --ff-only origin main" in line for line in problems)

    def test_the_refusal_comes_from_the_fetch_not_from_the_ref_on_disk(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The whole check turns on this.

        `origin/main` in the clone still points at `c1`, so the comparison the
        script makes against the refs already on disk reads *zero behind* and
        would wave the commit through. Only the fetch makes the answer non-zero.
        Delete the fetch and this test is the one that fails.
        """
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")

        assert _behind(work) == 0, "precondition: the stale ref alone says nothing is wrong"

        monkeypatch.chdir(work)
        problems = hygiene.check_main_drift()

        assert problems
        assert _behind(work) == 1, "the script fetched"

    def test_two_commits_behind_reports_two(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _commit(seed, "3\n", "c3")
        _git(seed, "push", "--quiet", "origin", "main")

        monkeypatch.chdir(work)
        problems = hygiene.check_main_drift()

        assert "main is 2 commit(s) behind origin/main." in problems[0]

    def test_diverged_says_so_and_warns_that_ff_only_will_refuse(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")
        _commit(work, "local\n", "local-c2")

        monkeypatch.chdir(work)
        problems = hygiene.check_main_drift()

        assert "behind" in problems[0]
        assert "1 commit(s) ahead" in problems[1]
        assert "--ff-only will refuse" in problems[1]


class TestMainCurrentOrAheadPasses:
    def test_up_to_date_is_silent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        upstream, _seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []

    def test_ahead_only_is_silent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """`main` ahead of the remote is the ordinary state after a local commit.

        The hook says nothing about it on purpose; refusing it would refuse the
        second commit of every pair.
        """
        upstream, _seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(work, "2\n", "c2")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []

    def test_no_remote_tracking_ref_is_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(_standalone(tmp_path))
        assert hygiene.check_main_drift() == []

    def test_outside_a_repository_is_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        elsewhere = tmp_path / "not-a-repo"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        assert hygiene.check_main_drift() == []


class TestBranchesAreSilent:
    """Work here happens on branches, so a branch must cost nothing.

    The repository in this test is as stale as the one two classes up -- the
    only difference is the name of the checked-out ref.
    """

    def test_a_branch_far_behind_origin_main_is_not_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _commit(seed, "3\n", "c3")
        _git(seed, "push", "--quiet", "origin", "main")
        _git(work, "checkout", "--quiet", "-b", "topic")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []

    def test_a_detached_head_is_not_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")
        _git(work, "checkout", "--quiet", "--detach", "HEAD")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []


class TestOfflineIsBestEffort:
    """A failed fetch may not block a commit. It falls back to the refs on disk."""

    def test_an_unreachable_remote_still_lets_a_current_main_commit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        upstream, _seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _git(work, "remote", "set-url", "origin", str(tmp_path / "gone.git"))

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []

    def test_an_unreachable_remote_still_refuses_a_main_already_known_to_be_behind(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")
        _git(work, "fetch", "--quiet", "origin", "main")
        _git(work, "remote", "set-url", "origin", str(tmp_path / "gone.git"))

        monkeypatch.chdir(work)
        assert _behind(work) == 1
        assert hygiene.check_main_drift()


class TestFetchStaleness:
    def test_a_missing_fetch_head_counts_as_stale(self, tmp_path: Path) -> None:
        repo = _standalone(tmp_path)
        assert hygiene._fetch_is_stale(str(repo / ".git")) is True

    def test_a_fresh_fetch_head_is_not_stale(self, tmp_path: Path) -> None:
        repo = _standalone(tmp_path)
        (repo / ".git" / "FETCH_HEAD").write_text("", encoding="utf-8")
        assert hygiene._fetch_is_stale(str(repo / ".git")) is False

    def test_an_old_fetch_head_is_stale(self, tmp_path: Path) -> None:
        repo = _standalone(tmp_path)
        fetch_head = repo / ".git" / "FETCH_HEAD"
        fetch_head.write_text("", encoding="utf-8")
        old = time.time() - hygiene.FETCH_STALE_SECONDS - 60
        os.utime(fetch_head, (old, old))
        assert hygiene._fetch_is_stale(str(fetch_head.parent)) is True

    def test_a_fresh_fetch_head_suppresses_the_fetch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The cost of the ten-minute window, stated as a test.

        Inside it the check runs against whatever `origin/main` already says,
        so a `main` that went stale in the last ten minutes commits. That is the
        deliberate trade -- a fetch on every commit is what the window buys off
        -- and it is here so the next reader does not discover it as a surprise.
        """
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")
        (work / ".git" / "FETCH_HEAD").write_text("", encoding="utf-8")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []
        assert _behind(work) == 0, "no fetch happened"


# --------------------------------------------------------------------------- #
# The `core.bare` half: reachable only through --doctor / --fix
# --------------------------------------------------------------------------- #


class TestDoctorFindsBareOnARealCheckout:
    def test_core_bare_true_beside_an_index_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "true")

        monkeypatch.chdir(repo)
        problems = hygiene.check_bare(fix=False)

        assert problems
        assert "core.bare is true" in problems[0]
        assert any("git config --local core.bare false" in line for line in problems)

    def test_the_numeric_spelling_is_caught_too(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`bare = 1` breaks a checkout exactly as `bare = true` does.

        Reading the raw config string missed it and printed "clean" on a
        repository where `git status` was already exiting 128 -- the one moment
        this command exists to be reached for. Fixed 2026-08-19 by asking git
        for the value as a bool. The assertion on `git status` below is what
        makes this a bug report rather than a preference.
        """
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "1")

        broken = subprocess.run(
            ["git", "status", "--short"], cwd=repo, capture_output=True, text=True
        )
        assert broken.returncode != 0, "precondition: git really is refusing to work"

        monkeypatch.chdir(repo)
        assert hygiene.check_bare(fix=False)

    def test_core_bare_false_is_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(_standalone(tmp_path))
        assert hygiene.check_bare(fix=False) == []

    def test_a_genuinely_bare_repository_is_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`core.bare = true` is only a defect where a working checkout exists.

        The signal is the contradiction, so a real bare repository -- no index
        beside the git dir -- must pass. Otherwise the doctor is unusable on
        every `origin` on the machine.
        """
        bare = tmp_path / "real.git"
        _git(tmp_path, "init", "--quiet", "--bare", "-b", "main", str(bare))

        monkeypatch.chdir(bare)
        assert hygiene.check_bare(fix=False) == []

    def test_outside_a_repository_is_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        elsewhere = tmp_path / "not-a-repo"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        assert hygiene.check_bare(fix=False) == []


class TestFixRepairs:
    def test_fix_clears_the_flag_and_git_works_again(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The assertion that matters is the last one: git runs afterwards.

        Checking only that the config value flipped would pass against a repair
        that wrote the key somewhere git does not read.
        """
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "true")

        monkeypatch.chdir(repo)
        assert hygiene.check_bare(fix=True) == []
        assert "repaired" in capsys.readouterr().out

        repaired = subprocess.run(
            ["git", "status", "--short"], cwd=repo, capture_output=True, text=True
        )
        assert repaired.returncode == 0

    def test_fix_on_a_healthy_repository_changes_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.chdir(_standalone(tmp_path))
        assert hygiene.check_bare(fix=True) == []
        assert capsys.readouterr().out == ""

    def test_a_failed_repair_says_so_rather_than_reporting_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A read-only `.git/config` is not reproducible across platforms here,
        so the write is made to fail directly. What is under test is that a
        non-zero `git config` becomes a message rather than a silent pass.
        """
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "true")
        monkeypatch.chdir(repo)

        real = hygiene.git

        def failing_git(*args: str, timeout: float | None = None) -> tuple[int, str]:
            if args[:3] == ("config", "--local", "core.bare"):
                return 1, ""
            return real(*args, timeout=timeout)

        monkeypatch.setattr(hygiene, "git", failing_git)

        assert hygiene.check_bare(fix=True) == [
            "core.bare is true but repair failed; set it by hand"
        ]


# --------------------------------------------------------------------------- #
# main(): exit codes, output stream, and the bypass
# --------------------------------------------------------------------------- #


def _main(monkeypatch: pytest.MonkeyPatch, *args: str) -> int:
    monkeypatch.setattr(sys, "argv", ["check_git_hygiene.py", *args])
    code = hygiene.main()
    assert isinstance(code, int)
    return code


class TestMainExitCodes:
    def test_a_clean_branch_exits_zero_and_says_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.chdir(_standalone(tmp_path))
        assert _main(monkeypatch) == 0
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_a_stale_main_exits_one_on_stderr_with_the_bypass_named(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")

        monkeypatch.chdir(work)
        assert _main(monkeypatch) == 1
        captured = capsys.readouterr()
        assert "git hygiene: FAILED" in captured.err
        assert "behind origin/main" in captured.err
        assert hygiene.OVERRIDE_ENV in captured.err
        assert captured.out == ""

    def test_doctor_on_a_healthy_repository_reports_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.chdir(_standalone(tmp_path))
        assert _main(monkeypatch, "--doctor") == 0
        assert "git hygiene: clean" in capsys.readouterr().out

    def test_doctor_exits_one_on_a_bare_flagged_checkout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "true")

        monkeypatch.chdir(repo)
        assert _main(monkeypatch, "--doctor") == 1
        assert "core.bare is true" in capsys.readouterr().err

    def test_fix_implies_doctor(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """`--fix` alone has to reach the bare check, or the flag does nothing."""
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "true")

        monkeypatch.chdir(repo)
        assert _main(monkeypatch, "--fix") == 0
        assert "repaired" in capsys.readouterr().out
        assert _git(repo, "config", "--local", "--type=bool", "--get", "core.bare") == "false"


class TestPlainRunNeverChecksBare:
    """The limitation, pinned so it cannot be quietly forgotten.

    With `core.bare` set, git aborts a commit before any hook runs, so no hook
    stage can reach this. The hook entry in `.pre-commit-config.yaml` passes no
    flags, and this is what that means: a commit is not guarded against
    `core.bare`, and the `--doctor` tests above are not evidence that it is.
    """

    def test_a_bare_flagged_checkout_passes_the_hook_invocation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "true")

        monkeypatch.chdir(repo)
        assert _main(monkeypatch) == 0
        assert capsys.readouterr().err == ""


class TestOverride:
    def test_the_documented_value_bypasses_a_refusal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")

        monkeypatch.chdir(work)
        assert _main(monkeypatch) == 1  # refused without it

        monkeypatch.setenv(hygiene.OVERRIDE_ENV, "1")
        capsys.readouterr()
        assert _main(monkeypatch) == 0
        assert capsys.readouterr().err == ""

    def test_the_override_also_silences_doctor(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Recorded rather than endorsed.

        The bypass is checked before the mode is dispatched, so
        `DE_SKIP_GIT_HYGIENE=1` turns `--doctor` and `--fix` into no-ops as well
        as the hook. Somebody reaching for `--fix` because git is refusing
        everything, with the variable exported from an earlier bypass, gets
        silence and exit 0. Changing it means deciding whether the variable
        names the hook or the script, which the docstring does not say -- so it
        is left alone and pinned here.
        """
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "true")
        monkeypatch.setenv(hygiene.OVERRIDE_ENV, "1")

        monkeypatch.chdir(repo)
        assert _main(monkeypatch, "--fix") == 0
        assert _git(repo, "config", "--local", "--type=bool", "--get", "core.bare") == "true"

    def test_any_non_empty_value_bypasses(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Including `0`, which reads as "do not skip" and does not.

        Same reasoning as above: picking a truthiness vocabulary is a decision
        the script does not record, so the actual semantics are pinned rather
        than improved.
        """
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")
        monkeypatch.chdir(work)

        monkeypatch.setenv(hygiene.OVERRIDE_ENV, "0")
        assert _main(monkeypatch) == 0

        monkeypatch.setenv(hygiene.OVERRIDE_ENV, "")
        assert _main(monkeypatch) == 1


class TestGitHelper:
    def test_a_missing_executable_is_a_failure_not_an_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every caller reads the exit code and gives up quietly on non-zero.

        An `OSError` escaping here would abort a commit with a traceback on a
        machine where git is not on PATH -- which is every machine where the
        hook is least able to help.
        """

        def explode(*_args: object, **_kwargs: object) -> None:
            raise OSError("git not found")

        monkeypatch.setattr(subprocess, "run", explode)
        assert hygiene.git("rev-parse", "--git-dir") == (1, "")

    def test_a_timeout_is_a_failure_not_an_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def time_out(*_args: object, **_kwargs: object) -> None:
            raise subprocess.TimeoutExpired(cmd="git", timeout=1.0)

        monkeypatch.setattr(subprocess, "run", time_out)
        assert hygiene.git("fetch", timeout=1.0) == (1, "")
