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

**Several tests here assert on which git commands ran, not only on the return
value.** That is deliberate and it is the lesson of the 2026-08-20 review: this
function has five independent guards that all return `[]`, so a test asserting
only `== []` passes with the guard it is named after deleted. `_recording_git`
exists so a guard can be pinned by what it *stops* -- almost always a fetch.

**A constant may not be its own assertion.** `COMFORTABLY_STALE_SECONDS` was
written after `FETCH_STALE_SECONDS = 1_000_000_000` -- the fetch switched off
entirely -- passed every test, because the tests backdated by the constant they
were testing. The same defect was still sitting one constant over on the
budget: `FETCH_TIMEOUT_SECONDS = 10 -> 100000` survived all 63 tests, so
`FETCH_BUDGET_CEILING_SECONDS` is here for the same reason and is likewise a
literal.

**No test may depend on a live `git fetch` finishing inside the shipped
budget.** Most tests here drive a real fetch between two directories under
`tmp_path` and several assert on its result, which at ten seconds is a bet on
machine load rather than on the hook. The `patient_fetch` fixture takes the
production budget out of every test except the ones that are about the
time-box; see its docstring for what was observed failing.
"""

from __future__ import annotations

import base64
import contextlib
import importlib.util
import inspect
import os
import stat
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple

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

#: The fetch budget as the module ships it, read once at import and therefore
#: before any fixture can patch it. `patient_fetch` below replaces the live
#: constant for the whole module, so this is the only handle left on the real
#: one -- and the real one is what `TestTheFetchIsTimeBoxed` has to assert
#: against.
SHIPPED_FETCH_TIMEOUT_SECONDS = hygiene.FETCH_TIMEOUT_SECONDS

#: Older than any suppression window this hook should ever carry. Deliberately
#: *not* derived from `hygiene.FETCH_STALE_SECONDS`: a test that backdates by
#: the constant it is testing moves with the constant, so raising the window to
#: a billion seconds -- which switches the fetch off entirely -- would not fail
#: a single test. An hour is the assertion: the window is shorter than this.
COMFORTABLY_STALE_SECONDS = 3600

#: An upper bound on `hygiene.FETCH_TIMEOUT_SECONDS`, and a literal for the same
#: reason as the constant above. `test_the_fetch_passes_a_timeout_and_asks_for
#: _no_pipes` compared the passed timeout against the module constant, so
#: `FETCH_TIMEOUT_SECONDS = 10 -> 100000` -- a hook that blocks a commit for a
#: day, which is the time-box deleted in all but name -- survived all 63 tests.
#: A pre-commit hook that stalls a commit for a whole minute is already broken,
#: so a minute is the value that must *not* pass: the assertion below is strict.
#: It read `<= 60` until 2026-08-20, admitting the exact number its own sentence
#: called broken.
FETCH_BUDGET_CEILING_SECONDS = 60

#: A lower bound, and the same trap one bound over. `FETCH_TIMEOUT_SECONDS =
#: 0.001` survived all 88 tests on 2026-08-20: the ceiling admitted it, and
#: `patient_fetch` means no test observes the shipped value behaving. Measured
#: on a `main` one commit behind, the drift is refused at the shipped budget and
#: the hook is **silent** at 0.001 -- the time-box deleted from the other end,
#: and the same plausible zero as a fetch that cannot authenticate.
#:
#: The number is a judgement resting on a measurement, and both halves are said
#: so neither is mistaken for the other. A real fetch is a connect, a handshake
#: and a ref advertisement; the slowest one measured for this file was 1.54s to
#: github.com, with a local authenticated one at 0.30-0.51s. Five seconds is
#: several times the slowest fetch this machine actually made, so a budget under
#: it cannot reliably finish one.
FETCH_BUDGET_FLOOR_SECONDS = 5

#: What tests that drive a *real* local fetch patch the budget to. This is test
#: patience and not a claim about the product: it is deliberately larger than
#: the ceiling above, because a loaded machine is why it exists. A local fetch
#: that has not finished in two minutes has hung, and the test should say so by
#: failing rather than by being flaky at ten seconds.
PATIENT_FETCH_SECONDS = 120


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


@pytest.fixture(autouse=True)
def patient_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Take the production fetch budget out of the tests' wall clock.

    Most tests here drive a *real* `git fetch` between two directories under
    `tmp_path`, and several of them assert on its result: that the stamp was
    armed, that the refusal happened, that the next run looked again. At the
    shipped ten seconds those assertions are a bet that a local fetch finishes
    inside ten seconds on a loaded machine, and it is a bet that loses --
    `test_a_failed_fetch_leaves_the_next_run_to_fetch_again` was observed
    failing six runs out of six under load and passing three out of three on a
    quiet machine, at the line asserting the second run refused.

    So the budget is patched module-wide rather than test by test, because the
    coupling was never specific to one test. Two tests override it in their own
    bodies, which wins over this: the two in `TestTheFetchIsTimeBoxed` that are
    *about* the time-box. And the shipped value is still asserted, against
    `SHIPPED_FETCH_TIMEOUT_SECONDS` and a literal ceiling, so raising it out of
    all usefulness still fails a test.
    """
    monkeypatch.setattr(hygiene, "FETCH_TIMEOUT_SECONDS", PATIENT_FETCH_SECONDS)


def _git(cwd: Path, *args: str) -> str:
    """Run git in ``cwd``, failing the test loudly rather than silently."""
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {cwd}:\n{proc.stderr}")
    return proc.stdout.strip()


def _git_allowing_failure(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git in ``cwd`` where a non-zero exit is the point of the test."""
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


class _GitCall(NamedTuple):
    argv: tuple[str, ...]
    kwargs: dict[str, Any]


@contextlib.contextmanager
def _recording_git() -> Iterator[list[_GitCall]]:
    """Record every `git` the script runs, and how, without changing behaviour.

    Wrapped around the call under test rather than installed as a fixture, so
    that the git commands a test uses to *build* its repository are not counted.
    """
    calls: list[_GitCall] = []
    real: Callable[..., Any] = subprocess.run

    def spy(args: Any, **kwargs: Any) -> Any:
        if isinstance(args, list) and args and args[0] == "git":
            calls.append(_GitCall(tuple(args), dict(kwargs)))
        return real(args, **kwargs)

    subprocess.run = spy
    try:
        yield calls
    finally:
        subprocess.run = real


def _fetches(calls: list[_GitCall]) -> list[_GitCall]:
    return [call for call in calls if "fetch" in call.argv]


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


def _main_left_behind(root: Path) -> Path:
    """A clone whose `main` is one commit behind the remote, unbeknownst to it."""
    upstream, seed = _upstream_with_seed(root)
    work = _clone(root, upstream, "work")
    _commit(seed, "2\n", "c2")
    _git(seed, "push", "--quiet", "origin", "main")
    return work


def _behind(repo: Path) -> int:
    """How far `main` trails `origin/main` *according to the refs on disk*."""
    counts = _git(repo, "rev-list", "--left-right", "--count", "main...origin/main")
    return int(counts.split()[1])


def _stamp(repo: Path) -> Path:
    return repo / ".git" / hygiene.FETCH_STAMP


def _backdate(path: Path, seconds: float) -> None:
    old = time.time() - seconds
    os.utime(path, (old, old))


def _make_core_bare_unreadable(repo: Path) -> None:
    """Put a value in `.git/config` that git cannot parse as a boolean.

    Everything after this -- `git status`, `git commit`, `git config`, even
    `git rev-parse --git-dir` -- exits 128 in this repository.
    """
    config = repo / ".git" / "config"
    kept = [
        line
        for line in config.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("bare")
    ]
    out: list[str] = []
    for line in kept:
        out.append(line)
        if line.strip() == "[core]":
            out.append("\tbare = maybe")
    config.write_text("\n".join(out) + "\n", encoding="utf-8")


def _break_the_config(repo: Path, text: str) -> None:
    """Append something to `.git/config` that git refuses without naming `core.bare`.

    The third class of setup failure: not "no repository here", and not a value
    of `core.bare` git cannot parse. Every git command in the repository exits
    128 afterwards, and nothing in the message mentions `core.bare`.
    """
    config = repo / ".git" / "config"
    with config.open("a", encoding="utf-8") as handle:
        handle.write(f"{text}\n")


@contextlib.contextmanager
def _server_demanding_credentials() -> Iterator[str]:
    """A local HTTP server answering every request with a Basic-auth challenge.

    Enough to make `git fetch` go looking for credentials, which is the whole
    point: the hazard is not the transport but the helper git launches when the
    401 comes back.
    """

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="git"')
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self) -> None:
            self.do_GET()

        def log_message(self, *_args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/x.git"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextlib.contextmanager
def _server_serving_a_repository_behind_basic_auth(repo: Path) -> Iterator[str]:
    """A local HTTP server that serves a real repository, but only to a caller
    that authenticates.

    The counterpart to `_server_demanding_credentials`, and the one the
    2026-08-20 review turned on. A server that only ever answers 401 cannot tell
    a hook that suppresses *prompting* from a hook that has disabled
    *authentication*: both fail, quickly, and look identical. This one answers
    the fetch once the credentials arrive, so a fetch that cannot authenticate
    fails a test instead of passing one.

    Dumb HTTP, which needs `git update-server-info` in the served repository --
    `_upstream_over_http` does that. Git tries the smart protocol, gets a plain
    file server, and falls back.
    """

    expected = "Basic " + base64.b64encode(b"u:p").decode()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(repo), **kwargs)

        def _unauthorised(self) -> bool:
            if self.headers.get("Authorization") == expected:
                return False
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="git"')
            self.send_header("Content-Length", "0")
            self.end_headers()
            return True

        def do_GET(self) -> None:
            if not self._unauthorised():
                super().do_GET()

        def do_HEAD(self) -> None:
            if not self._unauthorised():
                super().do_HEAD()

        def log_message(self, *_args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _upstream_over_http(root: Path) -> tuple[Path, Path]:
    """`_main_left_behind`, with the upstream prepared for a dumb HTTP fetch.

    Returns the clone and the upstream. The caller points the clone's `origin`
    at whichever server it is testing against.
    """
    upstream, seed = _upstream_with_seed(root)
    work = _clone(root, upstream, "work")
    _commit(seed, "2\n", "c2")
    _git(seed, "push", "--quiet", "origin", "main")
    _git(upstream, "update-server-info")
    return work, upstream


def _install_an_answering_credential_helper(repo: Path, tmp_path: Path) -> None:
    """A credential helper that supplies the password the server wants.

    The mirror image of `_install_a_hanging_credential_helper`: this is what a
    working GCM looks like from git's side, and it is what the hook broke.
    """
    helper = tmp_path / "answering_helper.py"
    helper.write_text(
        "import sys\n"
        "if sys.argv[1:2] == ['get']:\n"
        "    print('username=u')\n"
        "    print('password=p')\n",
        encoding="utf-8",
    )
    executable = sys.executable.replace("\\", "/")
    _git(repo, "config", "--local", "credential.helper", f"!'{executable}' '{helper.as_posix()}'")


def _an_askpass_that_answers(tmp_path: Path) -> Path:
    """A program git can run to be told the password, on either platform.

    `GIT_ASKPASS` and `core.askPass` name an executable, so this cannot be a
    bare `.py` file. The wrapper is the only part that differs by platform.
    """
    answer = tmp_path / "askpass_answer.py"
    answer.write_text("print('p')\n", encoding="utf-8")
    if os.name == "nt":
        program = tmp_path / "askpass.cmd"
        program.write_text(f'@"{sys.executable}" "{answer}"\n', encoding="utf-8")
    else:
        program = tmp_path / "askpass.sh"
        program.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{answer}"\n', encoding="utf-8")
        program.chmod(0o755)
    return program


def _install_a_hanging_credential_helper(repo: Path, tmp_path: Path) -> None:
    """Configure a credential helper that never answers, standing in for GCM.

    `git-credential-manager` on Windows opens a GUI and waits for a person. A
    helper that sleeps is the same shape and runs everywhere: git launches it,
    blocks on it, and the "time-boxed" fetch spends its whole budget waiting.
    """
    helper = tmp_path / "hanging_helper.py"
    helper.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    executable = sys.executable.replace("\\", "/")
    _git(repo, "config", "--local", "credential.helper", f"!'{executable}' '{helper.as_posix()}'")


def _bare_with_linked_worktree(root: Path) -> tuple[Path, Path]:
    """A genuinely bare repository that has a linked worktree checked out.

    This is the shape `--doctor` used to report as broken and `--fix` used to
    break: the worktree's git dir is `<bare>/worktrees/<name>/`, which is a
    directory *and* holds an `index`, while `git config --local` reads the
    shared config where `core.bare = true` is entirely correct.
    """
    bare = root / "shared.git"
    _git(root, "init", "--quiet", "--bare", "-b", "main", str(bare))
    seed = root / "bare-seed"
    _git(root, "clone", "--quiet", str(bare), str(seed))
    _commit(seed, "1\n", "c1")
    _git(seed, "push", "--quiet", "origin", "main")
    linked = root / "linked"
    _git(bare, "worktree", "add", "--quiet", str(linked), "main")
    return bare, linked


# --------------------------------------------------------------------------- #
# The drift half: refuse a commit on a stale `main`
# --------------------------------------------------------------------------- #


class TestMainBehindOriginIsRefused:
    def test_one_commit_behind_is_named_with_the_catch_up_command(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        work = _main_left_behind(tmp_path)

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
        work = _main_left_behind(tmp_path)

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
        work = _main_left_behind(tmp_path)
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

    def test_no_remote_tracking_ref_is_silent_and_attempts_no_fetch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Silence alone does not test the guard, so this tests the fetch.

        Every later guard in `check_main_drift` also returns `[]` on a
        repository with no `origin/main` -- `rev-list` fails, and that failure
        is swallowed. Deleting the `rev-parse --verify` guard therefore left all
        35 tests passing. What the guard actually buys is not reaching the
        network at all, so that is what is asserted.
        """
        monkeypatch.chdir(_standalone(tmp_path))

        with _recording_git() as calls:
            assert hygiene.check_main_drift() == []

        assert _fetches(calls) == []

    def test_a_deleted_remote_tracking_ref_is_silent_even_though_main_is_behind(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The same guard, in the shape where deleting it changes the verdict.

        `main` here really is a commit behind the remote. With the guard, that
        is unknowable without a fetch and the hook says nothing. Without it, the
        fetch runs, recreates `origin/main`, and the commit is refused on a
        repository the hook was never asked to have an opinion about.
        """
        work = _main_left_behind(tmp_path)
        _git(work, "update-ref", "-d", "refs/remotes/origin/main")

        monkeypatch.chdir(work)
        with _recording_git() as calls:
            assert hygiene.check_main_drift() == []

        assert _fetches(calls) == []

    def test_outside_a_repository_is_silent_and_gives_up_on_the_first_call(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Return value alone cannot discriminate here, so the call list does.

        Outside a repository every guard in the function returns `[]`, so this
        test passed with its own guard deleted. What the guard buys is that
        nothing further is attempted.
        """
        elsewhere = tmp_path / "not-a-repo"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        with _recording_git() as calls:
            assert hygiene.check_main_drift() == []

        assert [call.argv[1:] for call in calls] == [("rev-parse", "--abbrev-ref", "HEAD")]


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
        work = _main_left_behind(tmp_path)
        _git(work, "checkout", "--quiet", "--detach", "HEAD")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []


class TestIntegrationInProgressIsSilent:
    """The hook used to refuse the merge that was resolving the drift.

    During a conflicted `git merge origin/main`, `main` is both behind *and*
    ahead. The refusal said so on line 2 -- "--ff-only will refuse" -- and then
    advised `git pull --ff-only origin main` on line 4, which git answers with
    `fatal: Exiting because of unfinished merge.` The only way to make the
    commit was `--no-verify`, so the hook trained you to bypass it on the one
    flow it should have been helping. Reproduced 2026-08-20.
    """

    #: Hard-coded rather than read from `hygiene.INTEGRATION_MARKERS`, so that
    #: deleting a marker from the module fails a test instead of silently
    #: deleting the test that covered it.
    MARKERS = ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply")

    def test_the_marker_list_is_the_documented_one(self) -> None:
        assert hygiene.INTEGRATION_MARKERS == self.MARKERS

    def test_a_clean_repository_reports_no_integration(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(_standalone(tmp_path))
        assert hygiene._integration_in_progress() is None

    def test_a_conflicted_merge_that_resolves_the_drift_is_not_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The reported bug, end to end, with the advice checked too.

        The last two assertions are the bug report: the drift is real and would
        be refused, and the command the refusal recommends is one git will not
        run while the merge is open.
        """
        work = _main_left_behind(tmp_path)
        _commit(work, "local\n", "local-c2")
        _git(work, "fetch", "--quiet", "origin", "main")

        merge = _git_allowing_failure(work, "merge", "origin/main")
        assert merge.returncode != 0, "precondition: the merge conflicts"
        assert (work / ".git" / "MERGE_HEAD").exists()

        # Resolve and stage, which is where the hook actually fires: the next
        # thing anyone types here is `git commit`.
        (work / "f.txt").write_text("resolved\n", encoding="utf-8")
        _git(work, "add", "f.txt")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []

        pull = _git_allowing_failure(work, "pull", "--ff-only", "origin", "main")
        assert "unfinished merge" in pull.stderr, "the advice git refuses to run"

        (work / ".git" / "MERGE_HEAD").unlink()
        assert hygiene.check_main_drift(), "without the marker this is exactly what fires"

    @staticmethod
    def _plant(work: Path, marker: str) -> None:
        path = work / ".git" / marker
        if marker.startswith("rebase-"):
            path.mkdir()
        else:
            path.write_text(f"{'0' * 40}\n", encoding="utf-8")

    @pytest.mark.parametrize(
        "marker", ["MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"]
    )
    def test_every_marker_silences_a_main_that_really_is_behind(
        self, marker: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        work = _main_left_behind(tmp_path)

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift(), "precondition: this main really is behind"

        self._plant(work, marker)

        assert hygiene.check_main_drift() == []

    @pytest.mark.parametrize(
        "marker", ["MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"]
    )
    def test_every_marker_names_itself_rather_than_disappearing(
        self, marker: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unbounded exemption that says nothing is one nobody can debug.

        Planting any of these turns the drift guard off for as long as the
        marker is there, and `mkdir .git/rebase-apply` is what a crashed `git
        am` leaves behind -- nobody decided to disable anything. Until
        2026-08-20 the state was completely invisible: rc 0, no output, and
        `--doctor` in that state printed `git hygiene: clean`.
        """
        work = _main_left_behind(tmp_path)
        self._plant(work, marker)

        monkeypatch.chdir(work)
        assert hygiene._integration_in_progress() == marker

    def test_the_skipped_check_says_so_and_names_the_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        work = _main_left_behind(tmp_path)
        self._plant(work, "rebase-apply")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []

        note = capsys.readouterr().out
        assert "skipped" in note
        assert "rebase-apply" in note

    def test_a_ragged_answer_keeps_the_exemption_without_naming_a_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The fallback for a `rev-parse` answer that cannot be paired up.

        Untested until 2026-08-20 and it survived mutation: replacing the whole
        branch with `return None` left all 88 tests passing. It is not
        decoration -- refusing the merge that resolves the drift is the failure
        this exemption exists to close, so an answer this cannot interpret keeps
        the exemption while declining to say which marker it found.

        Git is not asked to produce the ragged shape, because nothing makes it:
        one line per flag is what it does. `hygiene.git` is replaced instead,
        which is the only way this branch can be reached at all.
        """
        repo = _standalone(tmp_path)
        monkeypatch.chdir(repo)
        planted = repo / ".git" / "MERGE_HEAD"
        planted.write_text("x\n", encoding="utf-8")

        def one_line_for_five_flags(*_args: str) -> tuple[int, str]:
            return 0, str(planted)

        monkeypatch.setattr(hygiene, "git", one_line_for_five_flags)
        assert hygiene._integration_in_progress() == "an integration marker"

        def one_line_naming_nothing(*_args: str) -> tuple[int, str]:
            return 0, str(repo / ".git" / "NOTHING_HERE")

        monkeypatch.setattr(hygiene, "git", one_line_naming_nothing)
        assert hygiene._integration_in_progress() is None, (
            "an unpairable answer is not a licence to exempt every commit"
        )

    def test_a_repository_with_no_integration_says_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The note is a note, not a banner. Every other commit stays silent."""
        upstream, _seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []
        assert capsys.readouterr().out == ""


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
        work = _main_left_behind(tmp_path)
        _git(work, "fetch", "--quiet", "origin", "main")
        _git(work, "remote", "set-url", "origin", str(tmp_path / "gone.git"))

        monkeypatch.chdir(work)
        assert _behind(work) == 1
        assert hygiene.check_main_drift()


class TestAFailedFetchDoesNotArmTheWindow:
    """The suppression window belongs to success, not to having tried.

    `git fetch` truncates and re-creates `FETCH_HEAD` even when it fails, so
    the old staleness check -- an mtime read off `FETCH_HEAD` -- was armed by
    failure. One run against an unreachable remote blinded the hook for ten
    minutes, and the case it then waved through is the case it exists for.
    Reproduced 2026-08-20: unreachable remote, run (rc 0), restore the remote
    with `main` genuinely one commit behind, run again -- rc 0, no fetch.
    """

    def test_a_failed_fetch_leaves_the_next_run_to_fetch_again(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Depends on a live fetch succeeding, which is why `patient_fetch` exists.

        The last assertion here is the one that broke under load -- six runs out
        of six, against three out of three on a quiet machine -- because at the
        shipped ten-second budget it was betting that a local fetch finishes in
        ten seconds. It is not a bet about the hook; the hook is allowed to give
        up. The module-wide fixture takes the production budget out of it.
        """
        work = _main_left_behind(tmp_path)
        gone = str(tmp_path / "gone.git")
        reachable = _git(work, "remote", "get-url", "origin")
        _git(work, "remote", "set-url", "origin", gone)

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == [], "offline is best-effort, not a refusal"
        assert not _stamp(work).exists(), "a failed fetch must not arm the window"

        _git(work, "remote", "set-url", "origin", reachable)
        assert hygiene.check_main_drift(), "the very next run must still look"

    def test_a_successful_fetch_does_arm_the_window(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The other half, and the cost of the window stated as a test.

        Inside the ten minutes the check runs against whatever `origin/main`
        already says, so a `main` that went stale during them commits. That is
        the deliberate trade -- a fetch on every commit is what the window buys
        off -- and it is here so the next reader does not meet it as a surprise.
        """
        upstream, seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift() == []
        assert _stamp(work).exists(), "a fetch that succeeded arms the window"

        _commit(seed, "2\n", "c2")
        _git(seed, "push", "--quiet", "origin", "main")

        with _recording_git() as calls:
            assert hygiene.check_main_drift() == []
        assert _fetches(calls) == [], "suppressed inside the window"


class TestFetchStaleness:
    def test_a_missing_stamp_counts_as_stale(self, tmp_path: Path) -> None:
        repo = _standalone(tmp_path)
        assert hygiene._fetch_is_stale(_stamp(repo)) is True

    def test_no_stamp_path_at_all_counts_as_stale(self) -> None:
        assert hygiene._fetch_is_stale(None) is True

    def test_a_fresh_stamp_is_not_stale(self, tmp_path: Path) -> None:
        repo = _standalone(tmp_path)
        _stamp(repo).write_text("", encoding="utf-8")
        assert hygiene._fetch_is_stale(_stamp(repo)) is False

    def test_an_hour_old_stamp_is_stale(self, tmp_path: Path) -> None:
        repo = _standalone(tmp_path)
        _stamp(repo).write_text("", encoding="utf-8")
        _backdate(_stamp(repo), COMFORTABLY_STALE_SECONDS)
        assert hygiene._fetch_is_stale(_stamp(repo)) is True

    def test_a_stamp_dated_in_the_future_is_stale(self, tmp_path: Path) -> None:
        """`age > FETCH_STALE_SECONDS` is never true of a negative age.

        A clock that jumped, a restored backup, an unzipped archive, a dual
        boot: any of them can leave an mtime ahead of `time.time()`, and the
        comparison then reads "not stale" for as long as the stamp is there.
        Not for ten minutes -- for ever.
        """
        repo = _standalone(tmp_path)
        _stamp(repo).write_text("", encoding="utf-8")
        _backdate(_stamp(repo), -COMFORTABLY_STALE_SECONDS)
        assert hygiene._fetch_is_stale(_stamp(repo)) is True

    def test_a_future_stamp_does_not_switch_the_check_off_end_to_end(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The unit assertion above with the hook wrapped around it.

        Reproduced 2026-08-20 with the mtime a year ahead: rc 0, no fetch
        attempted, on a `main` genuinely one commit behind -- which is the
        defect the stamp was introduced to close, reopened by the arithmetic
        used to read it.
        """
        work = _main_left_behind(tmp_path)
        _stamp(work).write_text("", encoding="utf-8")
        _backdate(_stamp(work), -365 * 24 * 3600)

        assert _behind(work) == 0, "precondition: the ref on disk says nothing is wrong"

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift(), "a stamp from the future must not blind the check"
        assert _behind(work) == 1, "the script fetched"

    def test_a_directory_where_the_stamp_belongs_is_stale(self, tmp_path: Path) -> None:
        """`_record_fetch` cannot write one, so nothing here may trust one.

        A directory's mtime is its own, so it read as fresh for ten minutes at a
        time and renewed itself: `_record_fetch` calls `write_text`, which
        raises `OSError` on a directory and is suppressed, so the window could
        never be closed by anything this script does. `mkdir` is all it takes.
        """
        repo = _standalone(tmp_path)
        _stamp(repo).mkdir()
        assert hygiene._fetch_is_stale(_stamp(repo)) is True

    def test_a_directory_where_the_stamp_belongs_does_not_suppress_the_fetch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        work = _main_left_behind(tmp_path)
        _stamp(work).mkdir()

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift(), "a directory is not a stamp"
        assert _behind(work) == 1, "the script fetched"
        assert _stamp(work).is_dir(), "and it did not manage to overwrite it either"

    def test_an_expired_window_fetches_again_end_to_end(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The window has to expire, and nothing used to drive that end to end.

        Setting `FETCH_STALE_SECONDS` to a billion switches the fetch off
        entirely, and all 35 tests passed with it there: the unit tests around
        `_fetch_is_stale` backdated by the constant itself, so they moved with
        it. This one backdates by a fixed hour and asserts on the refusal, so it
        fails if the window ever grows past that.
        """
        work = _main_left_behind(tmp_path)
        _stamp(work).write_text("", encoding="utf-8")
        _backdate(_stamp(work), COMFORTABLY_STALE_SECONDS)

        assert _behind(work) == 0, "precondition: the ref on disk says nothing is wrong"

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift(), "an expired window must fetch again"
        assert _behind(work) == 1, "the script fetched"

    def test_a_symlink_where_the_stamp_belongs_is_stale(self, tmp_path: Path) -> None:
        """`stat()` follows links, so `S_ISREG` closed one instance of a class.

        A symlink at the stamp path pointing at any regular file read as a
        regular file, so the window was suppressed off an mtime `_record_fetch`
        never wrote -- the directory defect one indirection over. Measured
        2026-08-20: `_fetch_is_stale` returned False. `lstat` answers about the
        link rather than its target.
        """
        repo = _standalone(tmp_path)
        elsewhere = tmp_path / "some-regular-file"
        elsewhere.write_text("", encoding="utf-8")
        _stamp(repo).symlink_to(elsewhere)

        assert _stamp(repo).is_file(), "precondition: it looks like a file through the link"
        assert hygiene._fetch_is_stale(_stamp(repo)) is True

    def test_a_successful_fetch_does_not_write_through_a_symlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The destructive half, which `lstat` alone does nothing about.

        `_record_fetch` calls `write_text`, and `write_text` follows a link. The
        stamp lives inside the git dir, so `.git/config` is one `ln -s` away --
        and a successful fetch truncated it, breaking the checkout this script
        exists to complain about. Measured 2026-08-20: the target came back
        empty.
        """
        work = _main_left_behind(tmp_path)
        precious = work / ".git" / "config"
        before = precious.read_text(encoding="utf-8")
        _stamp(work).symlink_to(precious)

        monkeypatch.chdir(work)
        assert hygiene.check_main_drift(), "a symlink is not a stamp; the check still runs"

        assert precious.read_text(encoding="utf-8") == before, "the fetch destroyed .git/config"
        assert _stamp(work).is_symlink(), "and it did not replace the link either"

    def test_a_hardlink_is_not_claimed_to_be_caught(self, tmp_path: Path) -> None:
        """The class is narrowed, not closed, and the docstring says so.

        `lstat` reports a hardlink as the regular file it is, because that is
        what it is. Pinned as a known limitation rather than left for the next
        review to discover as a surprise -- and skipped where the filesystem
        will not make one, since that is the platform's answer and not the
        script's.
        """
        repo = _standalone(tmp_path)
        target = tmp_path / "target"
        target.write_text("", encoding="utf-8")
        try:
            os.link(target, _stamp(repo))
        except (OSError, NotImplementedError, AttributeError):  # pragma: no cover
            pytest.skip("this filesystem will not make a hardlink")

        assert hygiene._fetch_is_stale(_stamp(repo)) is False, (
            "a hardlink is indistinguishable from the file it links to"
        )
        assert stat.S_ISREG(_stamp(repo).lstat().st_mode)

    def test_an_unwritable_stamp_location_just_fetches_every_time(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A repository this cannot write to loses the window, not the check."""
        work = _main_left_behind(tmp_path)
        monkeypatch.chdir(work)

        missing = work / ".git" / "no-such-dir" / hygiene.FETCH_STAMP
        hygiene._record_fetch(missing)  # must not raise
        hygiene._record_fetch(None)

        assert not missing.exists()
        assert hygiene._fetch_is_stale(missing) is True

    def test_a_stamp_that_cannot_be_read_is_stale_rather_than_a_traceback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The broad `except OSError` is load-bearing, and it had no test.

        Narrowed to `FileNotFoundError` the whole suite still passed, and an
        unreadable stamp would then abort a commit with a traceback out of a
        pre-commit hook. `PermissionError` is *injected* rather than provoked,
        and that is a limitation worth stating: this platform would not produce
        a non-`FileNotFoundError` on demand -- `stat` on a child of a directory
        denied with `icacls` still succeeded, and the ENOTDIR case surfaces as
        `FileNotFoundError` (winerror 3), so neither discriminates. Checked
        2026-08-20.
        """
        repo = _standalone(tmp_path)
        _stamp(repo).write_text("", encoding="utf-8")

        def denied(*_args: object, **_kwargs: object) -> None:
            raise PermissionError(13, "permission denied")

        monkeypatch.setattr(Path, "lstat", denied)
        assert hygiene._fetch_is_stale(_stamp(repo)) is True


class TestTheFetchIsTimeBoxed:
    """`.pre-commit-config.yaml` and the module docstring both promise this.

    They were wrong until 2026-08-20. `subprocess.run(timeout=...)` with
    `capture_output=True` kills the child and then calls `communicate()` again
    to drain the pipes; the transport helper git spawned inherited them,
    outlives the kill, and holds them open. Measured on Windows against a
    helper that slept 60s: `timeout=3` returned after 60.21s. The same
    measurement with `DEVNULL` returned after 3.00s.
    """

    def test_the_fetch_passes_a_timeout_and_asks_for_no_pipes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The portable half: deleting `timeout=` left all 35 tests passing.

        The wall-clock test below cannot cover it everywhere -- on POSIX,
        `subprocess.run` waits rather than draining after the kill, so the hang
        is a Windows shape. This assertion holds on every platform.
        """
        work = _main_left_behind(tmp_path)
        monkeypatch.chdir(work)

        with _recording_git() as calls:
            hygiene.check_main_drift()

        fetches = _fetches(calls)
        assert len(fetches) == 1
        kwargs = fetches[0].kwargs
        assert kwargs.get("timeout") == hygiene.FETCH_TIMEOUT_SECONDS
        assert kwargs.get("stdout") is subprocess.DEVNULL
        assert kwargs.get("stderr") is subprocess.DEVNULL
        assert not kwargs.get("capture_output"), "pipes are what the helper holds open"

    def test_the_budget_is_a_commit_hook_budget_and_not_just_a_number(self) -> None:
        """The assertion the test above cannot make, because it moves with it.

        Comparing the passed timeout against `hygiene.FETCH_TIMEOUT_SECONDS`
        pins that the constant is what flows through, and nothing else:
        `FETCH_TIMEOUT_SECONDS = 10 -> 100000` survived all 63 tests, which is a
        hook that can block a commit for a day with the time-box deleted in all
        but name. That is the same shape as the `FETCH_STALE_SECONDS` failure
        that `COMFORTABLY_STALE_SECONDS` was written for, one constant over.
        Both bounds here are literals for the same reason.

        **The band is two-sided, because `0 <` was not a bound.**
        `FETCH_TIMEOUT_SECONDS = 0.001` satisfied it and survived all 88 tests,
        and a budget no fetch can finish inside is the time-box deleted from
        below -- measured silent on a `main` that really was behind. The upper
        bound is strict for a smaller reason: the comment on
        `FETCH_BUDGET_CEILING_SECONDS` calls a one-minute stall already broken,
        and `<=` admitted exactly that.
        """
        assert FETCH_BUDGET_FLOOR_SECONDS <= SHIPPED_FETCH_TIMEOUT_SECONDS
        assert SHIPPED_FETCH_TIMEOUT_SECONDS < FETCH_BUDGET_CEILING_SECONDS

    def test_a_transport_helper_holding_the_pipes_does_not_outlast_the_timeout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The behavioural half, run against a helper that hangs for 25 seconds.

        `GIT_SSH_COMMAND` answers git's `ssh -G` probe and then sleeps, so git
        is genuinely blocked inside a transport it spawned. With the pipes
        asked for, this took the full sleep; the bound below is five times the
        timeout and still well under it.
        """
        upstream, _seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        sleeper = tmp_path / "sleeper.py"
        sleeper.write_text(
            "import sys, time\n"
            "if '-G' in sys.argv[1:]:\n"
            "    sys.stdout.write('user u\\nhostname h\\nport 22\\n')\n"
            "    raise SystemExit(0)\n"
            "time.sleep(25)\n",
            encoding="utf-8",
        )
        _git(work, "remote", "set-url", "origin", "ssh://nowhere.invalid/x.git")
        monkeypatch.setenv("GIT_SSH_COMMAND", f'"{sys.executable}" "{sleeper}"')
        monkeypatch.setattr(hygiene, "FETCH_TIMEOUT_SECONDS", 2)
        monkeypatch.chdir(work)

        started = time.monotonic()
        assert hygiene.check_main_drift() == [], "a hung fetch may not block a commit"
        elapsed = time.monotonic() - started

        assert elapsed < 10, f"the fetch was not time-boxed: {elapsed:.1f}s"
        assert not _stamp(work).exists(), "a fetch that timed out has not succeeded"


class TestTheFetchAuthenticatesAndIsBoundedWhenItCannot:
    """A fetch that needs a password must still be able to get one.

    This class asserted the opposite for one round of review, under the name
    `TestTheFetchNeverAsksForCredentials`, and the sentence it was built on --
    "a fetch that needs credentials is a fetch this hook cannot make" -- was
    false. A hanging Git Credential Manager was measured on 2026-08-20 costing
    the whole ten-second budget on every commit, and the fix emptied the helper
    list, `core.askPass`, `GIT_ASKPASS` and `SSH_ASKPASS`. Emptying those does
    not disable a *hanging* helper; it disables a *working* one.

    Measured the same day against a local server requiring Basic auth and a
    helper that answers it: success in 0.40-0.51s with the helper active,
    failure in 0.07-0.09s with the list emptied, and `GIT_ASKPASS` and
    `core.askPass` the same way round at 0.44s and 0.30s. On a private HTTPS
    remote every fetch the hook made therefore failed, and `check_main_drift`
    compared against the stale ref on disk and returned nothing, rc 0, with both
    streams discarded. End to end through `_fetch`: SILENT before the fix,
    REFUSED after it, on a `main` genuinely one commit behind.

    So the trade is the other way round. Authentication works, and a helper that
    hangs costs one bounded budget -- which the time-box now genuinely delivers.

    **The 401-only server cannot police this and never could.** It fails both a
    hook that suppresses prompting and a hook that has disabled authentication,
    identically and fast, which is why the over-fix passed a green suite.
    `_server_serving_a_repository_behind_basic_auth` answers once the
    credentials arrive, so only one of those two passes now.
    """

    #: Long enough that a fetch which went looking for credentials spends
    #: visibly more than the bound asserted below, and short enough that a
    #: regression fails in seconds rather than minutes.
    BUDGET = 3.0

    def test_an_authenticated_fetch_still_succeeds(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The regression test for the over-fix, through a credential helper.

        Without it, every assertion in this class is satisfied by a hook that
        cannot authenticate at all -- which is what shipped.
        """
        work, upstream = _upstream_over_http(tmp_path)
        _install_an_answering_credential_helper(work, tmp_path)

        with _server_serving_a_repository_behind_basic_auth(upstream) as url:
            _git(work, "remote", "set-url", "origin", url)
            monkeypatch.chdir(work)

            assert _behind(work) == 0, "precondition: the ref on disk says nothing is wrong"
            assert hygiene._fetch(PATIENT_FETCH_SECONDS) is True, (
                "a remote that answers once authenticated must be fetchable"
            )

        assert _behind(work) == 1, "the fetch brought the remote ref forward"

    def test_an_authenticated_fetch_through_askpass_still_succeeds(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The second door the over-fix closed, and it closed it two ways.

        `GIT_ASKPASS` was emptied in the child environment and `core.askPass`
        was reset with `-c`, so a repository authenticating through either was
        blinded exactly as one using a helper was. The username rides in the
        URL so that only the password is asked for.
        """
        work, upstream = _upstream_over_http(tmp_path)
        monkeypatch.setenv("GIT_ASKPASS", str(_an_askpass_that_answers(tmp_path)))

        with _server_serving_a_repository_behind_basic_auth(upstream) as url:
            _git(work, "remote", "set-url", "origin", url.replace("http://", "http://u@"))
            monkeypatch.chdir(work)

            assert hygiene._fetch(PATIENT_FETCH_SECONDS) is True, (
                "GIT_ASKPASS is a way of authenticating, not a way of prompting"
            )

        assert _behind(work) == 1, "the fetch brought the remote ref forward"

    def test_the_drift_is_refused_on_a_private_remote(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The whole hook, on the shape the over-fix made permanently silent.

        The ref on disk says zero behind and the remote says one, so this passes
        only if the fetch inside `check_main_drift` authenticated. It returned
        `[]` before the fix -- rc 0, nothing on either stream, on a `main` that
        really had drifted.
        """
        work, upstream = _upstream_over_http(tmp_path)
        _install_an_answering_credential_helper(work, tmp_path)

        with _server_serving_a_repository_behind_basic_auth(upstream) as url:
            _git(work, "remote", "set-url", "origin", url)
            monkeypatch.chdir(work)

            assert _behind(work) == 0, "precondition: the ref on disk says nothing is wrong"
            assert hygiene.check_main_drift(), "a private remote may not blind the drift check"

        assert _stamp(work).exists(), "a fetch that succeeded arms the window"

    def test_a_hanging_credential_helper_costs_one_budget_and_no_more(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The stall is real, it is bounded, and that is the trade.

        This asserted "no more than a moment" until 2026-08-20 and achieved it
        by making authentication impossible. The bound is the budget now: a
        helper that never answers is paid for once per `FETCH_STALE_SECONDS`,
        and then the commit proceeds against the ref on disk.
        """
        upstream, _seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _install_a_hanging_credential_helper(work, tmp_path)

        with _server_demanding_credentials() as url:
            _git(work, "remote", "set-url", "origin", url)
            monkeypatch.chdir(work)

            started = time.monotonic()
            assert hygiene._fetch(self.BUDGET) is False, "a 401 is not a successful fetch"
            elapsed = time.monotonic() - started

        assert elapsed < self.BUDGET * 5, f"the fetch was not bounded by its budget: {elapsed:.1f}s"

    def test_lapsed_credentials_do_not_block_the_commit_or_arm_the_window(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """End to end: a helper that never answers is offline, and offline is
        best-effort."""
        upstream, _seed = _upstream_with_seed(tmp_path)
        work = _clone(tmp_path, upstream, "work")
        _install_a_hanging_credential_helper(work, tmp_path)
        monkeypatch.setattr(hygiene, "FETCH_TIMEOUT_SECONDS", self.BUDGET)

        with _server_demanding_credentials() as url:
            _git(work, "remote", "set-url", "origin", url)
            monkeypatch.chdir(work)

            started = time.monotonic()
            assert hygiene.check_main_drift() == [], "lapsed credentials may not block a commit"
            elapsed = time.monotonic() - started

        assert elapsed < self.BUDGET * 5, f"the commit was not bounded: {elapsed:.1f}s"
        assert not _stamp(work).exists(), "a fetch that failed has not armed the window"

    def test_prompting_is_suppressed_and_authentication_is_not(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The switches, asserted as switches -- including the ones not thrown.

        The wall-clock tests above can only say that something was fast or slow.
        These say which knobs `_fetch` reaches for, and the negative half is the
        point: four switches that disable authentication were here and are gone,
        so re-adding any of them fails this rather than passing everything else.

        The environment variables are set to values the fix must leave alone,
        and that is load-bearing rather than tidy. `_fetch` builds its
        environment on top of `os.environ`, so asserting a value the ambient
        environment already carries is an assertion that cannot come out wrong.
        """
        work = _main_left_behind(tmp_path)
        monkeypatch.setenv("GIT_TERMINAL_PROMPT", "1")
        monkeypatch.setenv("GIT_ASKPASS", "a-program-that-answers")
        monkeypatch.setenv("SSH_ASKPASS", "another-one")
        monkeypatch.setenv("GCM_INTERACTIVE", "auto")
        monkeypatch.chdir(work)

        with _recording_git() as calls:
            hygiene.check_main_drift()

        fetches = _fetches(calls)
        assert len(fetches) == 1
        argv = fetches[0].argv
        env = fetches[0].kwargs.get("env")
        assert env is not None

        # Thrown: prompting, and a request that GCM not raise a window.
        assert env["GIT_TERMINAL_PROMPT"] == "0"
        assert env["GCM_INTERACTIVE"] == "never"

        # Not thrown: anything that stops git obtaining credentials at all.
        # `credential.interactive=false` belongs in this half rather than the
        # one above, and finding that out cost a measurement: git core reads it,
        # and it breaks an askpass that would have answered.
        assert "credential.helper=" not in argv, "an empty helper list is a hook that cannot fetch"
        assert "core.askPass=" not in argv, "core.askPass answers, it does not prompt"
        assert "credential.interactive=false" not in argv, (
            "git core reads this one; it breaks askpass"
        )
        assert env["GIT_ASKPASS"] == "a-program-that-answers"
        assert env["SSH_ASKPASS"] == "another-one"
        assert env.get("PATH") == os.environ.get("PATH"), "the rest of the environment survives"


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

    @pytest.mark.parametrize("spelling", ["true", "1", "yes", "on"])
    def test_every_spelling_of_true_is_caught(
        self, spelling: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`bare = 1` breaks a checkout exactly as `bare = true` does.

        Reading the raw config string missed it and printed "clean" on a
        repository where `git status` was already exiting 128 -- the one moment
        this command exists to be reached for. Fixed 2026-08-19 by asking git
        for the value as a bool. The assertion on `git status` below is what
        makes this a bug report rather than a preference.
        """
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", spelling)

        broken = _git_allowing_failure(repo, "status", "--short")
        assert broken.returncode != 0, "precondition: git really is refusing to work"

        monkeypatch.chdir(repo)
        assert hygiene.check_bare(fix=False)

    def test_the_index_path_in_the_message_is_one_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """It used to be an f-string gluing a `Path` to a literal `/index`.

        On Windows that printed `...\\worktrees\\A-wt/index`. Only the native
        separator can be asserted, so this is a real assertion on Windows and a
        tautology on POSIX -- which is the platform the defect could not occur
        on anyway.
        """
        repo = _standalone(tmp_path)
        _git(repo, "config", "--local", "core.bare", "true")

        monkeypatch.chdir(repo)
        problems = hygiene.check_bare(fix=False)

        assert str(Path(".git") / "index") in problems[0]

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

    def test_outside_a_repository_is_silent_and_gives_up_on_the_first_call(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The guard is load-bearing now, and this pins what it stops.

        `git config --local` outside a repository exits 128 -- the same exit
        code an unreadable `core.bare` produces. Reaching it from here is how a
        directory that is simply not a repository would be reported as a broken
        one, so the assertion is that it is never reached.
        """
        elsewhere = tmp_path / "not-a-repo"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        with _recording_git() as calls:
            assert hygiene.check_bare(fix=False) == []

        assert [call.argv[1:] for call in calls] == [("rev-parse", "--git-dir")]


class TestBareRepositoriesWithLinkedWorktrees:
    """`--doctor` reported a defect here, and `--fix` then created one.

    In a linked worktree of a bare repository the git dir is
    `<bare>/worktrees/<name>/`, which *is* a directory and *does* contain
    `index`, while `git config --local` reads the shared config where
    `core.bare = true` is correct. The old docstring's claim that this "never
    fires on a real bare repo" was false. Reproduced 2026-08-20: `--doctor`
    exited 1, and `--fix` printed "repaired: core.bare true -> false" and left
    the bare repository no longer bare.
    """

    def test_a_linked_worktree_of_a_bare_repository_is_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _bare, linked = _bare_with_linked_worktree(tmp_path)

        assert (Path(_git(linked, "rev-parse", "--git-dir")) / "index").exists(), (
            "precondition: the git dir here really does hold an index"
        )
        assert _git(linked, "config", "--local", "--type=bool", "--get", "core.bare") == "true", (
            "precondition: the shared config really does say bare"
        )
        assert _git_allowing_failure(linked, "status", "--short").returncode == 0, (
            "precondition: nothing is wrong here"
        )

        monkeypatch.chdir(linked)
        assert hygiene.check_bare(fix=False) == []

    def test_fix_in_a_linked_worktree_leaves_the_bare_repository_bare(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bare, linked = _bare_with_linked_worktree(tmp_path)

        monkeypatch.chdir(linked)
        assert hygiene.check_bare(fix=True) == []
        assert capsys.readouterr().out == "", "nothing was repaired, so nothing is claimed"

        assert _git(bare, "config", "--local", "--type=bool", "--get", "core.bare") == "true"
        assert _git(bare, "rev-parse", "--is-bare-repository") == "true"
        assert _git_allowing_failure(linked, "status", "--short").returncode == 0

    def test_the_bare_repository_itself_is_silent_even_with_worktrees(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bare, _linked = _bare_with_linked_worktree(tmp_path)

        monkeypatch.chdir(bare)
        assert hygiene.check_bare(fix=False) == []

    def test_the_main_worktree_of_a_broken_repository_is_still_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The false negative the fix costs, named rather than left to be found.

        A non-bare repository with `core.bare = true` and a linked worktree is
        broken in its *main* worktree only; git commands in the linked worktree
        work normally. So the doctor is silent there and reports from here, and
        that is the trade.
        """
        repo = _standalone(tmp_path, "mainwt")
        side = tmp_path / "side"
        _git(repo, "worktree", "add", "--quiet", str(side), "-b", "side")
        _git(repo, "config", "--local", "core.bare", "true")

        assert _git_allowing_failure(side, "status", "--short").returncode == 0
        assert _git_allowing_failure(repo, "status", "--short").returncode != 0

        monkeypatch.chdir(side)
        assert hygiene.check_bare(fix=False) == []

        monkeypatch.chdir(repo)
        assert hygiene.check_bare(fix=False)


class TestUnreadableCoreBare:
    """The exit code of the `core.bare` read used to be discarded.

    `_, bare = git(...)` reproduced, through a second door, the exact bug the
    `--type=bool` change of 2026-08-19 was made to close: `bare = maybe` makes
    every git command in the repository exit 128 with `bad boolean config
    value`, and `--doctor` printed `git hygiene: clean`, rc 0. Reproduced
    2026-08-20.
    """

    def test_a_value_git_cannot_parse_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _standalone(tmp_path)
        _make_core_bare_unreadable(repo)

        broken = _git_allowing_failure(repo, "status", "--short")
        assert broken.returncode == 128, "precondition: git really is refusing to work"
        assert "bad boolean config value" in broken.stderr

        monkeypatch.chdir(repo)
        problems = hygiene.check_bare(fix=False)

        assert problems
        assert "core.bare" in problems[0]
        assert any("bad boolean config value" in line for line in problems), (
            "git's own words, so the reader can see which value it choked on"
        )

    def test_the_doctor_exits_one_rather_than_reporting_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        repo = _standalone(tmp_path)
        _make_core_bare_unreadable(repo)

        monkeypatch.chdir(repo)
        assert _main(monkeypatch, "--doctor") == 1
        captured = capsys.readouterr()
        assert "clean" not in captured.out
        assert "core.bare" in captured.err

    def test_fix_does_not_touch_a_value_it_cannot_interpret(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Refusing to guess, on purpose.

        Git cannot be asked whether the repository is meant to be bare while
        the value is unreadable, and `git config --local core.bare false` fails
        for the same reason -- checked 2026-08-20, it exits 128 too. So the
        message says to edit `.git/config`, and `--fix` changes nothing.
        """
        repo = _standalone(tmp_path)
        _make_core_bare_unreadable(repo)
        before = (repo / ".git" / "config").read_text(encoding="utf-8")

        monkeypatch.chdir(repo)
        assert hygiene.check_bare(fix=True)
        assert (repo / ".git" / "config").read_text(encoding="utf-8") == before

    def test_a_missing_repository_is_not_reported_as_an_unreadable_value(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`core.bare` keeps its own message, because that one can be repaired.

        The `chdir` is load-bearing now. `_git_is_refusing` reads the
        filesystem, so run from anywhere inside a repository -- which is where
        pytest starts -- every one of these would report.
        """
        elsewhere = tmp_path / "not-a-repo"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        not_a_repo = "fatal: not a git repository (or any of the parent directories): .git"
        assert hygiene._git_is_refusing(not_a_repo) == []
        assert hygiene._git_is_refusing("") == []
        assert hygiene._git_is_refusing("fatal: bad boolean config value 'x' for 'core.bare'")


class TestGitRefusingEveryCommand:
    """`--doctor` reported `clean`, rc 0, where every git command exited 128.

    The module docstring sells `--doctor` as the thing to reach for "when git
    starts refusing everything", and it recognised a refusal only by finding
    the string `core.bare` in git's stderr. The old `_unreadable_core_bare`
    stated the dichotomy outright -- the failure either names `core.bare` or is
    "not a git repository" -- and there is a third class that names neither. Reproduced
    2026-08-20 with a junk line appended to `.git/config`: `git status` exited
    128 with `fatal: bad config line 8 in file .git/config`, and `--doctor`
    printed `git hygiene: clean`.

    The discriminator is the filesystem now, so it is neither message-dependent
    nor locale-dependent -- which the sniff was, twice over.
    """

    BREAKAGE = pytest.mark.parametrize(
        "junk",
        [
            pytest.param("this is not valid", id="junk-line"),
            pytest.param("[core]\n\trepositoryformatversion = banana", id="bad-format-version"),
        ],
    )

    @BREAKAGE
    def test_a_repository_git_will_not_open_is_reported(
        self, junk: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _standalone(tmp_path)
        _break_the_config(repo, junk)

        broken = _git_allowing_failure(repo, "status", "--short")
        assert broken.returncode == 128, "precondition: git really is refusing to work"
        assert "core.bare" not in broken.stderr, "precondition: and it does not name core.bare"

        monkeypatch.chdir(repo)
        problems = hygiene.check_bare(fix=False)

        assert problems
        assert any(broken.stderr.splitlines()[0] in line for line in problems), (
            "git's own words, since this script cannot get any of its own"
        )

    @BREAKAGE
    def test_the_doctor_exits_one_rather_than_reporting_clean(
        self,
        junk: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo = _standalone(tmp_path)
        _break_the_config(repo, junk)

        monkeypatch.chdir(repo)
        assert _main(monkeypatch, "--doctor") == 1
        captured = capsys.readouterr()
        assert "clean" not in captured.out
        assert "refusing" in captured.err

    @BREAKAGE
    def test_fix_attempts_no_repair(
        self, junk: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """There is nothing to repair by name, so nothing is guessed at.

        `--fix` reaches this through the same early return as `--doctor`, before
        the `fix` flag is consulted at all.
        """
        repo = _standalone(tmp_path)
        _break_the_config(repo, junk)
        before = (repo / ".git" / "config").read_text(encoding="utf-8")

        monkeypatch.chdir(repo)
        with _recording_git() as calls:
            assert hygiene.check_bare(fix=True)

        assert (repo / ".git" / "config").read_text(encoding="utf-8") == before
        assert [call.argv[1:] for call in calls] == [("rev-parse", "--git-dir")], (
            "no second git command, because none of them would work"
        )

    def test_a_subdirectory_of_such_a_repository_is_reported_too(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Git's discovery walks upwards, so the marker check has to.

        Otherwise the same defect is one directory down: no `.git` in the
        current directory, so a checkout git refuses to open reads as simply
        not being a repository.
        """
        repo = _standalone(tmp_path)
        _break_the_config(repo, "this is not valid")
        deep = repo / "a" / "b"
        deep.mkdir(parents=True)

        monkeypatch.chdir(deep)
        assert hygiene.check_bare(fix=False)

    def test_outside_a_repository_it_stays_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The other half. `--doctor` in a plain directory reports clean."""
        elsewhere = tmp_path / "not-a-repo"
        elsewhere.mkdir()

        monkeypatch.chdir(elsewhere)
        assert hygiene.check_bare(fix=False) == []
        assert _main(monkeypatch, "--doctor") == 0

    def test_the_marker_is_a_git_entry_at_or_above_the_directory(self, tmp_path: Path) -> None:
        """`.git` is a directory in a main worktree and a file in a linked one."""
        plain = tmp_path / "plain"
        (plain / "deep").mkdir(parents=True)
        assert hygiene._repository_shape(plain) is None
        assert hygiene._repository_shape(plain / "deep") is None

        (plain / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        assert hygiene._repository_shape(plain) is not None
        assert hygiene._repository_shape(plain / "deep") is not None

    def test_a_bare_repository_is_recognised_by_its_own_shape(self, tmp_path: Path) -> None:
        """It carries no `.git`, which exempted the whole class from the walk."""
        bare = tmp_path / "bare.git"
        _git(tmp_path, "init", "--quiet", "--bare", "-b", "main", str(bare))

        shape = hygiene._repository_shape(bare)
        assert shape is not None
        assert "bare" in shape

        (bare / "refs" / "deep").mkdir(parents=True)
        assert hygiene._repository_shape(bare / "refs" / "deep") is not None, (
            "git discovers upwards from a subdirectory of a bare repository too"
        )

    def test_two_of_the_three_pieces_is_not_a_repository(self, tmp_path: Path) -> None:
        """The bare shape is HEAD *and* objects *and* refs, so it is hard to
        stumble into by accident."""
        nearly = tmp_path / "nearly"
        (nearly / "objects").mkdir(parents=True)
        (nearly / "refs").mkdir()
        assert hygiene._repository_shape(nearly) is None, "no HEAD"

        (nearly / "HEAD").mkdir()
        assert hygiene._repository_shape(nearly) is None, "HEAD is a directory, not a file"


class TestABrokenBareRepositoryIsReported:
    """`--doctor` printed `clean`, rc 0, in a bare repository git refused.

    The class was exempt by construction: the discriminator required a `.git`
    entry at or above the directory, and a bare repository has none anywhere.
    Reproduced 2026-08-20 -- `git init --bare`, a junk line appended to
    `config`, `git status` exits 128 with `fatal: bad config line 7 in file
    ./config`, and the doctor reported the repository healthy.
    """

    def _broken_bare(self, tmp_path: Path) -> Path:
        bare = tmp_path / "broken.git"
        _git(tmp_path, "init", "--quiet", "--bare", "-b", "main", str(bare))
        with (bare / "config").open("a", encoding="utf-8") as handle:
            handle.write("this is not valid\n")
        return bare

    def test_it_is_reported_rather_than_reported_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bare = self._broken_bare(tmp_path)

        refusing = _git_allowing_failure(bare, "status", "--short")
        assert refusing.returncode == 128, "precondition: git really is refusing to work"
        assert "core.bare" not in refusing.stderr, "precondition: and it does not name core.bare"

        monkeypatch.chdir(bare)
        problems = hygiene.check_bare(fix=False)

        assert problems
        assert any(refusing.stderr.splitlines()[0] in line for line in problems)

    def test_the_doctor_exits_one_rather_than_reporting_clean(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(self._broken_bare(tmp_path))
        assert _main(monkeypatch, "--doctor") == 1
        assert "clean" not in capsys.readouterr().out

    def test_a_healthy_bare_repository_is_still_silent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The other half, and the one the new shape test could have broken.

        A healthy bare repository never reaches `_git_is_refusing` at all --
        `rev-parse` exits zero -- so `core.bare = true` is judged by the branch
        that knows a real bare repository has no index.
        """
        bare = tmp_path / "fine.git"
        _git(tmp_path, "init", "--quiet", "--bare", "-b", "main", str(bare))

        monkeypatch.chdir(bare)
        assert hygiene.check_bare(fix=False) == []
        assert _main(monkeypatch, "--doctor") == 0


class TestDiscoveryGitDeclinedToDoIsNotADefect:
    """A healthy repository was failed, rc 1, by the fix for the class above.

    Replacing the stderr sniff with a filesystem walk moved the wrong answer
    rather than removing it. With `GIT_CEILING_DIRECTORIES` set to a
    repository's root and the command run from a subdirectory, git stops
    searching before it reaches `.git` and says so in as many words -- and a
    walk that only looks at the filesystem sees `.git` sitting right there and
    calls a perfectly healthy checkout broken. Reproduced 2026-08-20; the
    previous version was correctly silent, which makes this a regression rather
    than a gap.

    Git's own message settles it, so it is consulted first and nothing on disk
    is allowed to overrule it.
    """

    def test_a_ceiling_that_blocks_discovery_is_not_a_broken_repository(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _standalone(tmp_path)
        deep = repo / "a" / "b"
        deep.mkdir(parents=True)

        monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(repo))
        monkeypatch.chdir(deep)

        blocked = _git_allowing_failure(deep, "rev-parse", "--git-dir")
        assert blocked.returncode != 0, "precondition: discovery really is blocked"
        assert hygiene.DISCOVERY_EXHAUSTED in blocked.stderr, "precondition: git says so"
        assert (repo / ".git").is_dir(), "precondition: and the repository is right there"

        assert hygiene.check_bare(fix=False) == [], "a healthy repository may not be failed"
        assert _main(monkeypatch, "--doctor") == 0

    def test_the_two_not_a_git_repository_messages_are_not_the_same_message(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`GIT_DIR` pointing nowhere says `not a git repository: <path>`.

        No parenthetical, and it is not discovery reporting an empty result --
        it is git having been pointed at something that is not there, with the
        checkout underfoot possibly fine. Collapsing the two into a substring
        search for "not a git repository" would silence a genuinely broken
        pointer, so the constant carries the parenthetical.
        """
        repo = _standalone(tmp_path)
        monkeypatch.chdir(repo)
        monkeypatch.setenv("GIT_DIR", str(tmp_path / "no-such-dir.git"))

        pointed = _git_allowing_failure(repo, "rev-parse", "--git-dir")
        assert pointed.returncode != 0
        assert "not a git repository" in pointed.stderr
        assert hygiene.DISCOVERY_EXHAUSTED not in pointed.stderr

        assert hygiene._git_is_refusing(pointed.stderr), "a broken pointer is still a refusal"


class TestTheRemedyFollowsTheEvidence:
    """Three newly detected classes were all told to start with `.git/config`.

    Detection was the improvement; the advice underneath it was not. Dubious
    ownership is repaired by `safe.directory` and the repository is fine; a
    broken *global* config is repaired in the global file, which git names
    itself; a `GIT_DIR` pointing nowhere leaves the checkout healthy. All three
    printed `Start with .git/config -- a value git cannot parse is the usual
    cause`, and for two of them there was nothing wrong with `.git/config` at
    all.
    """

    def test_a_config_git_names_is_the_config_the_remedy_names(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A broken *global* config is not repaired in the repository."""
        repo = _standalone(tmp_path)
        broken_global = tmp_path / "broken-gitconfig"
        broken_global.write_text("[core]\n\tjunk line here\n", encoding="utf-8")
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(broken_global))
        monkeypatch.chdir(repo)

        problems = hygiene.check_bare(fix=False)

        assert problems
        remedies = [line for line in problems if line.startswith("Start with ")]
        assert len(remedies) == 1
        assert str(broken_global) in remedies[0], "git named the file; so does the advice"
        assert ".git/config" not in remedies[0]

    def test_dubious_ownership_carries_gits_own_command_and_no_invented_one(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """git prints the exact `safe.directory` line; quoting one line lost it.

        `GIT_TEST_ASSUME_DIFFERENT_OWNER` is git's own switch for this, so the
        message under test is the real one rather than a fixture.
        """
        repo = _standalone(tmp_path)
        monkeypatch.setenv("GIT_TEST_ASSUME_DIFFERENT_OWNER", "1")
        monkeypatch.chdir(repo)

        refusing = _git_allowing_failure(repo, "rev-parse", "--git-dir")
        assert "dubious ownership" in refusing.stderr, "precondition: git refuses for that reason"

        problems = hygiene.check_bare(fix=False)

        assert problems
        assert not [line for line in problems if line.startswith("Start with ")], (
            "the repository is fine; there is nothing to start with"
        )
        assert any("safe.directory" in line for line in problems), (
            "git printed the fix on a later line, and every line is quoted"
        )
        assert sum("git said:" in line for line in problems) == 1, (
            "one quoted block, with the continuation aligned under it"
        )

    def test_a_broken_pointer_gets_no_config_advice_at_all(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`GIT_DIR` pointing nowhere leaves `.git/config` entirely correct."""
        repo = _standalone(tmp_path)
        monkeypatch.chdir(repo)
        monkeypatch.setenv("GIT_DIR", str(tmp_path / "no-such-dir.git"))

        problems = hygiene.check_bare(fix=False)

        assert problems, "a pointer to nothing is still a git that will not run"
        assert not [line for line in problems if line.startswith("Start with ")]
        assert any("git said:" in line for line in problems), "git's words carry it instead"

    def test_a_repository_config_git_names_is_still_named(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The one class the old advice was right about keeps it."""
        repo = _standalone(tmp_path)
        _break_the_config(repo, "this is not valid")
        monkeypatch.chdir(repo)

        problems = hygiene.check_bare(fix=False)

        assert any(line.startswith("Start with ") and ".git/config" in line for line in problems), (
            "here .git/config really is the file git could not parse"
        )


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

        assert _git_allowing_failure(repo, "status", "--short").returncode == 0

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

        def failing_git(*args: str) -> tuple[int, str]:
            if args[:3] == ("config", "--local", "core.bare"):
                return 1, ""
            return real(*args)

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
        work = _main_left_behind(tmp_path)

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
        work = _main_left_behind(tmp_path)

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
        work = _main_left_behind(tmp_path)
        monkeypatch.chdir(work)

        monkeypatch.setenv(hygiene.OVERRIDE_ENV, "0")
        assert _main(monkeypatch) == 0

        monkeypatch.setenv(hygiene.OVERRIDE_ENV, "")
        assert _main(monkeypatch) == 1


# Four mutations survive this suite, and the comment that used to stand here
# claimed one -- while describing a mutation of `check_main_drift` and calling
# it `check_bare`. All four were re-run against the whole suite on 2026-08-20;
# each is argued equivalent below, and "argued" is the right word for three of
# them. The argument is the evidence, not a measurement.
#
#   1. `if code != 0 or branch != PROTECTED_BRANCH:` in `check_main_drift`,
#      with `code != 0 or` dropped. Outside a repository `git rev-parse
#      --abbrev-ref HEAD` writes nothing to stdout, so `branch` is the empty
#      string and the second half returns early anyway.
#   2. `if code != 0 or bare != "true":` in `check_bare`, likewise. A failing
#      `git config --get` writes nothing to stdout, so `bare` cannot be the
#      string "true" when the exit code is non-zero.
#   3. `if not (git_path.is_dir() and (git_path / "index").exists()):`, with
#      `git_path.is_dir() and` dropped. A path cannot hold a child unless it is
#      a directory, so `is_dir()` is implied by the half that follows it.
#   4. `--quiet` dropped from the fetch argv. Not equivalent in the strict
#      sense -- git writes different bytes -- but both streams go to `DEVNULL`,
#      so nothing observable changes.
#
# None of them has an input that distinguishes the two versions, so no test can
# have one either, and inventing one that pokes at internals would pin the
# implementation rather than the behaviour. Every clause stays because it says
# what its guard is for. Recorded here so that "equivalent" has something
# behind it, and so nobody reads this as a survivor count of one.


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
        assert hygiene._run("rev-parse", "--git-dir") == (1, "", "")
        assert hygiene._fetch(1.0) is False

    def test_a_timeout_is_a_failure_not_an_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Only `_fetch` can time out, because only `_fetch` passes a timeout.

        `_run` and `git` carried a `timeout=` parameter until 2026-08-20 that no
        production caller ever passed -- mutating `_run` to drop
        `timeout=timeout` survived all 63 tests -- and this test was the only
        thing touching it, through a monkeypatched `subprocess.run` raising an
        exception the real one cannot raise without a timeout. The parameter is
        gone rather than routed through, because `_fetch` cannot use `_run`: it
        must not ask for pipes, which is the whole point of `_fetch`.
        """

        def time_out(*_args: object, **_kwargs: object) -> None:
            raise subprocess.TimeoutExpired(cmd="git", timeout=1.0)

        monkeypatch.setattr(subprocess, "run", time_out)
        assert hygiene._fetch(1.0) is False

    def test_neither_helper_takes_a_timeout(self) -> None:
        """Pinned, so that re-adding it needs a caller rather than a habit."""
        assert "timeout" not in inspect.signature(hygiene._run).parameters
        assert "timeout" not in inspect.signature(hygiene.git).parameters

    def test_a_git_path_outside_a_repository_is_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        elsewhere = tmp_path / "not-a-repo"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        assert hygiene._git_path(hygiene.FETCH_STAMP) is None
        assert hygiene._integration_in_progress() is None
