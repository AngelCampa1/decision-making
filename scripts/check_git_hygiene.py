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

Set DE_SKIP_GIT_HYGIENE=1 to bypass.
"""

from __future__ import annotations

import argparse
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


def git(*args: str, timeout: float | None = None) -> tuple[int, str]:
    """Run a git command, returning (exit code, stripped stdout)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return 1, ""
    return proc.returncode, proc.stdout.strip()


def check_bare(fix: bool) -> list[str]:
    """Report `core.bare = true` on a repository that has a real checkout.

    A genuine bare repository has no `.git` subdirectory and no index. So
    `core.bare = true` alongside both of those is a contradiction, and the
    contradiction is the whole signal -- this never fires on a real bare repo.
    """
    code, git_dir = git("rev-parse", "--git-dir")
    if code != 0:
        return []

    _, bare = git("config", "--local", "--get", "core.bare")
    if bare != "true":
        return []

    git_path = Path(git_dir)
    if not (git_path.is_dir() and (git_path / "index").exists()):
        return []  # actually bare; nothing wrong

    if fix:
        if git("config", "--local", "core.bare", "false")[0] == 0:
            print("repaired: core.bare true -> false")
            return []
        return ["core.bare is true but repair failed; set it by hand"]

    return [
        f"core.bare is true, but this repository has a working checkout ({git_path}/index exists).",
        "Every working-tree operation will fail until this is cleared:",
        "    git config --local core.bare false",
    ]


def _fetch_is_stale(git_dir: str) -> bool:
    fetch_head = Path(git_dir) / "FETCH_HEAD"
    if not fetch_head.exists():
        return True
    return (time.time() - fetch_head.stat().st_mtime) > FETCH_STALE_SECONDS


def check_main_drift() -> list[str]:
    """Refuse a commit on `main` while `main` is behind `origin/main`.

    Only fires on `main` itself. The comparison uses the already-fetched
    remote ref; a fetch is attempted first when the last one has gone stale,
    and a failed fetch is ignored so that being offline does not block a
    commit -- the check then runs against whatever ref is on disk.
    """
    code, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if code != 0 or branch != PROTECTED_BRANCH:
        return []

    remote_ref = f"{REMOTE}/{PROTECTED_BRANCH}"
    if git("rev-parse", "--verify", "--quiet", remote_ref)[0] != 0:
        return []  # no remote-tracking ref; nothing to compare against

    code, git_dir = git("rev-parse", "--git-dir")
    if code == 0 and _fetch_is_stale(git_dir):
        git("fetch", REMOTE, PROTECTED_BRANCH, "--quiet", timeout=FETCH_TIMEOUT_SECONDS)

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
