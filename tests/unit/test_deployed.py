"""Every branch of the online check, because each one is a different verdict.

The module carries a 100/100 floor for the reason the floors on the other gates
exist: the failure it reports is silent, so a branch nothing exercises is a
wrong answer nobody sees. The sharpest case is *unreachable*, which must never
collapse into *current* -- a script treating "could not ask" as "up to date"
rebuilds the hole this command was added to close.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from decision_evals import deployed as dep

HEAD = "f01d325cf1c2199d4f69e845efa9d806c4e805eb"
OTHER = "bd86e862101bd7ba96e6f9a71d3c64334561b244"
#: 39 characters. A truncated body is the case a length check catches and a
#: "is it a non-empty string" check does not.
SHORT = HEAD[:-1]


class _Completed:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


@contextmanager
def _response(payload: str, url: str) -> Iterator[Any]:
    class _R:
        def read(self, amount: int | None = None) -> bytes:
            # The real reader caps the read, so the stub must accept a size.
            return payload.encode("utf-8")[:amount]

        def geturl(self) -> str:
            # A server that did not redirect answers at the URL it was asked
            # about. Echoing the request rather than hardcoding a string is what
            # makes the redirect test below a different case and not a different
            # stub.
            return url

    yield _R()


def _serve(monkeypatch: pytest.MonkeyPatch, payload: str, landed_at: str | None = None) -> None:
    def urlopen(request: Any, timeout: float | None = None) -> Any:
        return _response(payload, landed_at or request.full_url)

    monkeypatch.setattr(dep.urllib.request, "urlopen", urlopen)


def _provenance(**overrides: object) -> str:
    record: dict[str, object] = {"commit": HEAD, "ref": "refs/heads/main"}
    record.update(overrides)
    return json.dumps(record)


class TestExitCode:
    """Three codes, not two. The third is the point."""

    def test_current_is_zero(self) -> None:
        assert dep.DeployState(dep.CURRENT, "").exit_code == 0

    def test_behind_is_one(self) -> None:
        assert dep.DeployState(dep.BEHIND, "").exit_code == 1

    def test_unreachable_is_two(self) -> None:
        assert dep.DeployState(dep.UNREACHABLE, "").exit_code == 2

    def test_str_is_the_detail(self) -> None:
        assert str(dep.DeployState(dep.CURRENT, "a sentence")) == "a sentence"


class TestGit:
    def test_returns_stripped_stdout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(dep.subprocess, "run", lambda *a, **k: _Completed(0, " x \n"))
        assert dep._git(Path(), ["rev-parse"]) == "x"

    def test_a_failure_is_not_an_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(dep.subprocess, "run", lambda *a, **k: _Completed(1, "x"))
        assert dep._git(Path(), ["rev-parse"]) is None

    def test_a_hang_is_not_an_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`ls-remote` talks to the network, so the module's timeout promise has
        to cover git too. Without it an auth-challenging remote blocks forever,
        and on Windows the credential helper can raise a GUI prompt nobody is
        there to answer."""

        def hang(*a: object, **k: object) -> _Completed:
            raise subprocess.TimeoutExpired(cmd="git", timeout=1.0)

        monkeypatch.setattr(dep.subprocess, "run", hang)
        assert dep._git(Path(), ["ls-remote"]) is None

    def test_it_never_prompts_for_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: dict[str, object] = {}

        def record(*a: object, **k: object) -> _Completed:
            seen.update(k)
            return _Completed(0, "x")

        monkeypatch.setattr(dep.subprocess, "run", record)
        dep._git(Path(), ["ls-remote"])
        assert seen["env"]["GIT_TERMINAL_PROMPT"] == "0"  # type: ignore[index]
        assert seen["timeout"] == dep.GIT_TIMEOUT

    def test_a_missing_git_is_not_an_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(*a: object, **k: object) -> _Completed:
            raise OSError("no git")

        monkeypatch.setattr(dep.subprocess, "run", boom)
        assert dep._git(Path(), ["rev-parse"]) is None


class TestFetchProvenance:
    def test_reads_the_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _serve(monkeypatch, _provenance())
        assert dep.fetch_provenance("http://x")["commit"] == HEAD

    def test_an_unreachable_host_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(url: str, timeout: float | None = None) -> None:
            raise OSError("refused")

        monkeypatch.setattr(dep.urllib.request, "urlopen", boom)
        with pytest.raises(dep.UnreachableError, match="could not fetch"):
            dep.fetch_provenance("http://x")

    def test_a_non_json_body_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A 404 page is HTML with a 200-shaped body from some hosts."""
        _serve(monkeypatch, "<!doctype html>")
        with pytest.raises(dep.UnreachableError, match="not JSON"):
            dep.fetch_provenance("http://x")

    def test_the_request_is_cache_busted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Pages sits behind a CDN, and a plain re-fetch is a byte-identical
        request that hits the same edge object. The work order's remedy for a
        surprising *behind* is "run it again", which without this is not a
        remedy at all."""
        seen: list[str] = []

        def urlopen(request: Any, timeout: float | None = None) -> Any:
            seen.append(request.full_url)
            return _response(_provenance(), request.full_url)

        monkeypatch.setattr(dep.urllib.request, "urlopen", urlopen)
        dep.fetch_provenance("http://x")
        dep.fetch_provenance("http://x")
        assert len(set(seen)) == 2, seen
        assert all(u.startswith("http://x?t=") for u in seen), seen

    def test_a_redirect_is_not_an_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`urlopen` follows one silently, and a repository rename leaves one in
        place. JSON read from a URL that is no longer the one asked about is a
        confident answer to a different question."""
        _serve(monkeypatch, _provenance(), landed_at="http://elsewhere/deploy-provenance.json")
        with pytest.raises(dep.UnreachableError, match="redirected"):
            dep.fetch_provenance("http://x")

    def test_a_query_string_in_the_url_keeps_the_cache_buster_separate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen: list[str] = []

        def urlopen(request: Any, timeout: float | None = None) -> Any:
            seen.append(request.full_url)
            return _response(_provenance(), request.full_url)

        monkeypatch.setattr(dep.urllib.request, "urlopen", urlopen)
        dep.fetch_provenance("http://x?a=1")
        assert seen[0].startswith("http://x?a=1&t="), seen

    def test_json_that_is_not_an_object_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _serve(monkeypatch, "[1, 2]")
        with pytest.raises(dep.UnreachableError, match="not an object"):
            dep.fetch_provenance("http://x")


class TestRemoteHead:
    def test_reads_the_sha(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(dep, "_git", lambda root, args: f"{HEAD}\trefs/heads/main")
        assert dep.remote_head(Path()) == HEAD

    def test_more_than_one_matching_ref_is_ambiguous_not_a_guess(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`ls-remote <remote> <pattern>` matches the *tail* of a ref name, so a
        branch called `feature/refs/heads/main` matches too and sorts first.
        Taking `split()[0]` of the body would compare against a branch nobody
        deployed and report *behind* with confidence."""
        body = f"{OTHER}\trefs/heads/feature/refs/heads/main\n{HEAD}\trefs/heads/main"
        monkeypatch.setattr(dep.subprocess, "run", lambda *a, **k: _Completed(0, body))
        with pytest.raises(dep.UnreachableError, match="ambiguous"):
            dep.remote_head(Path())

    @pytest.mark.parametrize("token", ["HEAD", SHORT, HEAD.upper()])
    def test_something_that_is_not_a_commit_is_not_an_answer(
        self, monkeypatch: pytest.MonkeyPatch, token: str
    ) -> None:
        """The fetched record is validated with this same regex before a verdict
        is taken from it. This side was not, until it was."""
        monkeypatch.setattr(
            dep.subprocess,
            "run",
            lambda *a, **k: _Completed(0, f"{token}\trefs/heads/main"),
        )
        with pytest.raises(dep.UnreachableError, match="not a commit"):
            dep.remote_head(Path())

    def test_an_unreadable_remote_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(dep, "_git", lambda root, args: None)
        with pytest.raises(dep.UnreachableError, match="could not read"):
            dep.remote_head(Path())


class TestManifestDigest:
    def test_absent_manifest_is_none(self, tmp_path: Path) -> None:
        assert dep.manifest_digest(tmp_path) is None

    def test_line_endings_do_not_change_the_digest(self, tmp_path: Path) -> None:
        """The workflow that writes this digest runs on Linux; the command that
        reads it usually does not."""
        unix = tmp_path / "unix"
        windows = tmp_path / "windows"
        for root, newline in ((unix, b"\n"), (windows, b"\r\n")):
            (root / "site").mkdir(parents=True)
            (root / dep.MANIFEST_PATH).write_bytes(b"{" + newline + b"}")
        assert dep.manifest_digest(unix) == dep.manifest_digest(windows)


class TestCheckDeployed:
    def test_current(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _serve(monkeypatch, _provenance())
        monkeypatch.setattr(dep, "remote_head", lambda root, ref=dep.REMOTE_REF: HEAD)
        state = dep.check_deployed(tmp_path, "http://x")
        assert state.status == dep.CURRENT
        assert state.exit_code == 0

    def test_behind_names_both_commits_and_the_distance(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _serve(monkeypatch, _provenance(commit=OTHER))
        monkeypatch.setattr(dep, "remote_head", lambda root, ref=dep.REMOTE_REF: HEAD)
        monkeypatch.setattr(dep, "_git", lambda root, args: "" if args[0] == "merge-base" else "3")
        state = dep.check_deployed(tmp_path, "http://x")
        assert state.status == dep.BEHIND
        assert OTHER[:7] in state.detail
        assert HEAD[:7] in state.detail
        assert "3 commit(s) behind" in state.detail

    def test_it_does_not_claim_a_distance_when_history_diverged(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """If `main` were force-pushed backwards the deployed commit would be a
        *descendant* of the new tip and `rev-list --count` would return 0, so
        the old wording said "0 commit(s) behind" beside a verdict of behind.
        Ancestry is checked first now."""
        _serve(monkeypatch, _provenance(commit=OTHER))
        monkeypatch.setattr(dep, "remote_head", lambda root, ref=dep.REMOTE_REF: HEAD)
        monkeypatch.setattr(dep, "_git", lambda root, args: None)
        state = dep.check_deployed(tmp_path, "http://x")
        assert state.status == dep.BEHIND
        assert "diverged" in state.detail
        assert "commit(s) behind" not in state.detail

    def test_it_says_so_when_the_count_is_unavailable(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Ancestry resolves, the count does not: a shallow clone."""
        _serve(monkeypatch, _provenance(commit=OTHER))
        monkeypatch.setattr(dep, "remote_head", lambda root, ref=dep.REMOTE_REF: HEAD)
        monkeypatch.setattr(dep, "_git", lambda root, args: "" if args[0] == "merge-base" else None)
        state = dep.check_deployed(tmp_path, "http://x")
        assert state.status == dep.BEHIND
        assert "cannot be counted" in state.detail

    def test_a_differing_manifest_is_not_reported_as_drift(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Pins a decision rather than a behaviour. Comparing the published
        manifest digest against the local working tree fired on every branch it
        was tried on, because a checkout is hardly ever sitting exactly on the
        deployed commit; comparing it against the manifest in the deployed
        commit can never disagree. The commit SHA already determines the tree,
        so no verdict is taken from this field."""
        (tmp_path / "site").mkdir()
        (tmp_path / dep.MANIFEST_PATH).write_text("{}", encoding="utf-8")
        _serve(monkeypatch, _provenance(build_manifest_sha256="something-else"))
        monkeypatch.setattr(dep, "remote_head", lambda root, ref=dep.REMOTE_REF: HEAD)
        assert dep.check_deployed(tmp_path, "http://x").status == dep.CURRENT

    def test_unreachable_is_not_reported_as_current(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        def boom(url: str, timeout: float | None = None) -> None:
            raise OSError("refused")

        monkeypatch.setattr(dep.urllib.request, "urlopen", boom)
        state = dep.check_deployed(tmp_path, "http://x")
        assert state.status == dep.UNREACHABLE
        assert state.exit_code == 2

    @pytest.mark.parametrize("commit", [None, "", 7, "abc1234", SHORT, HEAD.upper()])
    def test_a_record_without_a_usable_commit_is_unreachable(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, commit: object
    ) -> None:
        """Not *behind*: what is deployed was never established, and reporting
        drift would send somebody to fix the wrong thing."""
        _serve(monkeypatch, json.dumps({"commit": commit}))
        monkeypatch.setattr(dep, "remote_head", lambda root, ref=dep.REMOTE_REF: HEAD)
        state = dep.check_deployed(tmp_path, "http://x")
        assert state.status == dep.UNREACHABLE


class TestDistanceAgainstRealGit:
    """The one place the stubs cannot answer the question.

    Everything above replaces `subprocess.run`, so it tests `_distance` against
    a model of git rather than against git. That model is where the risk is:
    `merge-base --is-ancestor` reports its answer in the *exit code* and prints
    nothing at all, so a successful call comes back from `_git` as `""` -- falsy,
    but not `None`. Written as `if not _git(...)` this function would report
    every ancestor as a divergence, and every stubbed test above would still
    pass, because a stub returning `""` is indistinguishable from one returning
    `None` under a truthiness check.
    """

    @staticmethod
    def _repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, str, str]:
        """Two commits in a throwaway repository, and their real SHAs.

        **`cwd` is not enough, and the environment has to be cleaned for the
        whole process rather than for one subprocess.** Run from a git hook --
        which is where `de check` runs at `pre-push` -- the environment carries
        `GIT_DIR` and `GIT_INDEX_FILE` pointing at the *outer* repository, and
        git prefers those over the working directory it was given. These two
        tests passed everywhere except inside the hook, where they built their
        commits into this repository instead and were refused; one run left a
        stray file staged in the worktree root, which is what that was.

        Cleaning only this helper's own subprocess is not enough either, because
        `_distance` shells out through `deployed._git`, which passes
        `os.environ` straight through and would still be pointed at the outer
        repository.
        """
        for name in [k for k in os.environ if k.startswith("GIT_")]:
            monkeypatch.delenv(name, raising=False)
        for name, value in {
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.invalid",
        }.items():
            monkeypatch.setenv(name, value)

        def run(*args: str) -> str:
            return subprocess.run(
                ["git", *args],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

        run("init", "--quiet")
        (tmp_path / "a").write_text("1", encoding="utf-8")
        run("add", "a")
        run("commit", "--quiet", "-m", "one")
        first = run("rev-parse", "HEAD")
        (tmp_path / "a").write_text("2", encoding="utf-8")
        run("commit", "--quiet", "-am", "two")
        return tmp_path, first, run("rev-parse", "HEAD")

    def test_an_ancestor_gets_a_counted_distance(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        root, first, head = self._repo(monkeypatch, tmp_path)
        assert dep._distance(root, first, head) == "and the live site is 1 commit(s) behind"

    def test_a_commit_this_checkout_never_saw_is_not_counted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An unknown SHA makes `merge-base` exit non-zero for a different
        reason than "not an ancestor", and both must land on the same refusal
        rather than on a fabricated count."""
        root, _, head = self._repo(monkeypatch, tmp_path)
        assert "diverged or it is not in this checkout" in dep._distance(root, "0" * 40, head)
