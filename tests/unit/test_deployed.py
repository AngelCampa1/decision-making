"""Every branch of the online check, because each one is a different verdict.

The module carries a 100/100 floor for the reason the floors on the other gates
exist: the failure it reports is silent, so a branch nothing exercises is a
wrong answer nobody sees. The sharpest case is *unreachable*, which must never
collapse into *current* -- a script treating "could not ask" as "up to date"
rebuilds the hole this command was added to close.
"""

from __future__ import annotations

import json
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
def _response(payload: str) -> Iterator[Any]:
    class _R:
        def read(self, amount: int | None = None) -> bytes:
            # The real reader caps the read, so the stub must accept a size.
            return payload.encode("utf-8")[:amount]

    yield _R()


def _serve(monkeypatch: pytest.MonkeyPatch, payload: str) -> None:
    monkeypatch.setattr(dep.urllib.request, "urlopen", lambda url, timeout=None: _response(payload))


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

    def test_json_that_is_not_an_object_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _serve(monkeypatch, "[1, 2]")
        with pytest.raises(dep.UnreachableError, match="not an object"):
            dep.fetch_provenance("http://x")


class TestRemoteHead:
    def test_reads_the_sha(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(dep, "_git", lambda root, args: f"{HEAD}\trefs/heads/main")
        assert dep.remote_head(Path()) == HEAD

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
