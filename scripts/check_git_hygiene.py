#!/usr/bin/env python3
"""Two repository-hygiene invariants, checked before a commit lands.

Both come from a real failure on 2026-08-19, when a branch switch out of
`site/instrument-redesign` left `core.bare = true` in `.git/config`. Every
working-tree operation in the shared checkout then failed with `fatal: this
operation must be run in a work tree`, including the app's own "Commit as WIP"
button, which appeared to do nothing at all for four hours.

**The `core.bare` half is deliberately not a hook, and cannot be one.** With
`core.bare = true`, `git commit` aborts before hooks are invoked -- so does
`checkout`, `merge` and `push`, and every hook stage that could plausibly guard
it needs the working tree that the flag denies. There is no stage that fires.
It is exposed as `--doctor` instead: a command to reach for when git starts
refusing everything, plus `--fix` to repair it. Nothing enforces that anyone
runs it. That is a limitation of the mechanism, not an oversight.

The drift half *is* a hook, and it is narrow on purpose: it refuses a commit
on `main` while `main` is behind `origin/main`. Work here happens on branches
and merges to `main`, so committing directly onto a stale `main` is already
the anomaly -- which is what makes refusing it cheap. It says nothing about
branches, and nothing about `main` being merely *ahead*.

**It also says nothing while an integration is in progress**, and that is not a
gap. A conflicted `git merge origin/main` leaves `main` both behind *and*
ahead, so before this exemption existed the hook refused the very merge commit
that was resolving the drift -- and the refusal advised `git pull --ff-only
origin main`, which git answers with `fatal: Exiting because of unfinished
merge.` The only way out was `--no-verify`, so the hook trained you to bypass
it on the one flow it should have been helping. Reproduced and fixed
2026-08-20. A merge, cherry-pick, revert or rebase is integration rather than
new work, so `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD` and a
`rebase-merge`/`rebase-apply` directory each make the drift check silent.

**The hook runs at `pre-commit` only, so it does not run on a clean merge at
all** -- pre-commit's `pre-merge-commit` stage is deliberately not wired. Once
integration is exempt, a clean merge is a case this check has nothing to say
about, and adding the stage would only re-enter the loop above through a second
door. So this is not an oversight to be tidied up later: do not add
`pre-merge-commit` in `.pre-commit-config.yaml`.

**`origin` is hardcoded, and where that is wrong the check fails open and
silent.** `REMOTE` is a module constant. On a clone whose upstream is named
anything else -- `upstream`, a fork remote, a second remote -- or where
`remote.origin.fetch` is unset so `refs/remotes/origin/main` is never written,
`git rev-parse --verify origin/main` fails and this returns nothing. It cannot
tell that case apart from having nothing to compare against, and does not try:
a hygiene hook that guesses which remote you meant is worse than one that is
quiet. Green here is not evidence that `main` is current on such a repository.

Set DE_SKIP_GIT_HYGIENE=1 to bypass.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import subprocess
import sys
import time
from pathlib import Path

PROTECTED_BRANCH = "main"
REMOTE = "origin"
FETCH_STALE_SECONDS = 600
FETCH_TIMEOUT_SECONDS = 10
OVERRIDE_ENV = "DE_SKIP_GIT_HYGIENE"

#: Written by this script inside the per-worktree git dir, after a fetch that
#: exited zero. See `_fetch_is_stale` for why `FETCH_HEAD` cannot serve.
FETCH_STAMP = "de-git-hygiene-fetch"

#: Paths whose existence means git is part-way through integrating somebody
#: else's commits. All are per-worktree, and all are resolved through
#: `git rev-parse --git-path` rather than assembled from `--git-dir`, so that a
#: linked worktree and a `$GIT_COMMON_DIR` redirection both land correctly.
INTEGRATION_MARKERS = (
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "rebase-merge",
    "rebase-apply",
)


def _run(*args: str, timeout: float | None = None) -> tuple[int, str, str]:
    """Run a git command, returning (exit code, stripped stdout, stripped stderr)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return 1, "", ""
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git(*args: str, timeout: float | None = None) -> tuple[int, str]:
    """Run a git command, returning (exit code, stripped stdout)."""
    code, out, _ = _run(*args, timeout=timeout)
    return code, out


def check_bare(fix: bool) -> list[str]:
    """Report `core.bare = true` on a repository git is treating as non-bare.

    Two conditions have to hold together, and the pair is the whole signal.
    Git must actually be acting bare here -- `rev-parse --is-bare-repository`
    -- *and* the git dir must be a directory holding an `index`, which a
    genuine bare repository does not have.

    The first half was missing until 2026-08-20, and the docstring here claimed
    "this never fires on a real bare repo", which was false. Inside a linked
    worktree of a bare repository the git dir is `<bare>/worktrees/<name>/`,
    which *is* a directory and *does* contain `index`, while `git config
    --local` reads the shared config where `core.bare = true` is correct. So
    `--doctor` reported a defect on a healthy repository, and `--fix` then
    printed "repaired: core.bare true -> false" and left `git -C <bare> status`
    failing with `fatal: this operation must be run in a work tree` -- it broke
    the repository it had been run to protect. Git does not treat a linked
    worktree as bare whatever the shared config says, so asking git settles it.

    The cost of asking git is a false negative worth naming: inside a linked
    worktree of a *non-bare* repository carrying the `core.bare` defect, this
    stays silent. Checked 2026-08-20 -- git commands work normally in that
    worktree, only the main worktree is broken, and `--doctor` run there
    reports it.
    """
    code, git_dir, stderr = _run("rev-parse", "--git-dir")
    if code != 0:
        return _unreadable_core_bare(stderr)

    # `--type=bool` rather than the raw value. Git accepts `1`, `yes` and `on`
    # as spellings of true and breaks the checkout for all of them, so reading
    # the raw string reports "clean" on a repository where every working-tree
    # operation is already failing -- which is precisely the moment this is
    # reached for. Verified 2026-08-19: `bare = 1` makes `git status` exit 128.
    code, bare = git("config", "--local", "--type=bool", "--get", "core.bare")
    if code != 0 or bare != "true":
        return []

    if git("rev-parse", "--is-bare-repository")[1] != "true":
        return []  # a linked worktree; git is not acting bare here

    git_path = Path(git_dir)
    if not (git_path.is_dir() and (git_path / "index").exists()):
        return []  # actually bare; nothing wrong

    if fix:
        if git("config", "--local", "core.bare", "false")[0] == 0:
            print("repaired: core.bare true -> false")
            return []
        return ["core.bare is true but repair failed; set it by hand"]

    return [
        "core.bare is true, but this repository has a working checkout "
        f"({git_path / 'index'} exists).",
        "Every working-tree operation will fail until this is cleared:",
        "    git config --local core.bare false",
    ]


def _unreadable_core_bare(stderr: str) -> list[str]:
    """Tell "not a repository" apart from "git cannot read `core.bare` at all".

    Discarding the exit code of the `core.bare` read reproduced, through a
    second door, the exact bug that reading it as a bool was meant to close.
    `bare = maybe` in `.git/config` makes *every* git command in the repository
    exit 128 with `bad boolean config value` -- `git status`, `git commit`,
    `git config` and `git rev-parse --git-dir` alike -- and `--doctor` printed
    `git hygiene: clean`, rc 0, standing in a repository where nothing worked.
    Reproduced and fixed 2026-08-20.

    Nothing git can be asked will separate the two cases, because everything
    git is asked fails the same way. Checked 2026-08-20: `-c core.bare=false`
    does not override it, `git config -f .git/config` does not sidestep it, and
    a subdirectory behaves identically. What does separate them is what git
    *says*: the setup failure names `core.bare`, and `not a git repository`
    does not. The key name survives translation even though the sentence around
    it does not.
    """
    if "core.bare" not in stderr:
        return []  # not a repository, or some unrelated setup failure

    return [
        "core.bare cannot be read at all, and git is refusing every command here.",
        f"    git said: {stderr.splitlines()[0]}",
        "--fix will not touch this one. Git cannot be asked whether the repository is",
        "meant to be bare while the value is unreadable, and `git config` is refusing",
        "for the same reason -- so edit the `bare =` line in .git/config by hand.",
    ]


def _git_path(name: str) -> Path | None:
    """Resolve a per-worktree path inside the git dir, or None outside a repo."""
    code, path = git("rev-parse", "--git-path", name)
    if code != 0 or not path:
        return None
    return Path(path)


def _integration_in_progress() -> bool:
    """Whether git is part-way through a merge, cherry-pick, revert or rebase.

    One `rev-parse` covers all of `INTEGRATION_MARKERS`; the flag repeats.
    """
    args: list[str] = ["rev-parse"]
    for name in INTEGRATION_MARKERS:
        args += ["--git-path", name]
    code, out = git(*args)
    if code != 0:
        return False
    return any(Path(line).exists() for line in out.splitlines() if line)


def _fetch_is_stale(stamp: Path | None) -> bool:
    """Whether a fetch is due, judged by a stamp this script writes itself.

    The stamp is written only after a fetch that exited zero, and the reason it
    exists rather than reading `FETCH_HEAD` is that git truncates and re-creates
    `FETCH_HEAD` even when the fetch *fails*. An mtime read off it is therefore
    armed by failure: one run against an unreachable remote blinded this check
    for the next ten minutes, and the case it then waved through -- a `main`
    that fell behind while the remote was briefly away -- is the exact case the
    hook exists for. Reproduced and fixed 2026-08-20.
    """
    if stamp is None:
        return True
    try:
        age = time.time() - stamp.stat().st_mtime
    except OSError:
        return True  # missing, or unreadable; either way, fetch
    return age > FETCH_STALE_SECONDS


def _record_fetch(stamp: Path | None) -> None:
    """Arm the suppression window. Called only after a fetch that succeeded."""
    if stamp is None:
        return
    # A repository this cannot write to loses the window, not the check: an
    # unwritable stamp is always stale, so it simply fetches every time.
    with contextlib.suppress(OSError):
        stamp.write_text("", encoding="utf-8")


def _fetch(timeout: float) -> bool:
    """Fetch the protected branch, returning whether git reported success.

    stdout and stderr go to `DEVNULL`, which is a correctness fix rather than
    tidiness. `subprocess.run(timeout=...)` kills the child on timeout and then
    calls `communicate()` again to drain the pipes; a transport helper (`ssh`,
    `git-remote-https`) has inherited those pipes, outlives the kill, and holds
    them open -- so the drain blocks for as long as the helper runs and the
    "time-boxed" fetch is bounded by nothing. Measured 2026-08-20 on Windows
    against a helper that slept 60s: with `capture_output=True` and `timeout=3`
    the call returned after **60.21s**; with `DEVNULL`, after 3.00s. The output
    is discarded either way, so there is nothing to lose by not asking for it.
    """
    try:
        proc = subprocess.run(
            ["git", "fetch", REMOTE, PROTECTED_BRANCH, "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return proc.returncode == 0


def check_main_drift() -> list[str]:
    """Refuse a commit on `main` while `main` is behind `origin/main`.

    Only fires on `main` itself, and only when no integration is in progress.
    The comparison uses the already-fetched remote ref; a fetch is attempted
    first when the last *successful* one has gone stale, and a failed fetch is
    ignored so that being offline does not block a commit -- the check then
    runs against whatever ref is on disk, and does not open the ten-minute
    quiet window.

    `origin` is hardcoded. Where the remote is named otherwise, or
    `refs/remotes/origin/main` does not exist, this returns silently; see the
    module docstring.
    """
    code, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if code != 0 or branch != PROTECTED_BRANCH:
        return []  # not a repository, or not the protected branch

    if _integration_in_progress():
        return []  # a merge is integration, not new work

    remote_ref = f"{REMOTE}/{PROTECTED_BRANCH}"
    if git("rev-parse", "--verify", "--quiet", remote_ref)[0] != 0:
        return []  # no remote-tracking ref; nothing to compare against

    stamp = _git_path(FETCH_STAMP)
    if _fetch_is_stale(stamp) and _fetch(FETCH_TIMEOUT_SECONDS):
        _record_fetch(stamp)

    code, counts = git("rev-list", "--left-right", "--count", f"{PROTECTED_BRANCH}...{remote_ref}")
    if code != 0:
        return []
    try:
        ahead_str, behind_str = counts.split()
        ahead, behind = int(ahead_str), int(behind_str)
    except ValueError:
        return []

    if behind == 0:
        return []

    problem = [
        f"{PROTECTED_BRANCH} is {behind} commit(s) behind {remote_ref}.",
        "Committing here now would fork the branch. Catch up first:",
        f"    git pull --ff-only {REMOTE} {PROTECTED_BRANCH}",
    ]
    if ahead:
        problem.insert(
            1,
            f"It is also {ahead} commit(s) ahead, so the histories have "
            "already diverged and --ff-only will refuse.",
        )
    return problem


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="also check core.bare, which no hook stage can reach",
    )
    parser.add_argument(
        "--fix", action="store_true", help="repair what can be repaired (implies --doctor)"
    )
    args = parser.parse_args()

    if os.environ.get(OVERRIDE_ENV):
        return 0

    problems: list[str] = []
    if args.doctor or args.fix:
        problems += check_bare(fix=args.fix)
    problems += check_main_drift()

    if not problems:
        if args.doctor or args.fix:
            print("git hygiene: clean")
        return 0

    print("git hygiene: FAILED", file=sys.stderr)
    for line in problems:
        print(f"  {line}", file=sys.stderr)
    print(f"  (bypass with {OVERRIDE_ENV}=1)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
