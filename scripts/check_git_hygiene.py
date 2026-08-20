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

**`--doctor` answers for a git that refuses everything, not only for
`core.bare`.** Until 2026-08-20 it reported `git hygiene: clean`, rc 0, in a
repository where every git command exited 128, because it recognised a setup
failure only by finding the string `core.bare` in git's stderr. A junk line in
`.git/config`, or `core.repositoryformatversion = banana`, names neither
`core.bare` nor "not a git repository", and both break the checkout completely.
The discriminator is the filesystem now: git refused *and* a `.git` entry is
here or above. `--fix` repairs neither -- see `_git_is_refusing`.

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

**The exemption says so out loud**, because an unbounded exemption that says
nothing is one nobody can debug. `mkdir .git/rebase-apply` is what a crashed
`git am` leaves behind, and until 2026-08-20 it turned the drift guard off with
no output at all -- `--doctor` in that state even printed `git hygiene: clean`.
The check now prints which marker it found and skips. Note the arena: run
directly, the note is on stdout. Under `pre-commit` it is swallowed, because
`pre-commit` shows a passing hook's output only when the hook is configured
`verbose: true`, which this one is not -- so the note reaches a person who runs
the script, not a person who commits.

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
import stat
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


def _run(*args: str) -> tuple[int, str, str]:
    """Run a git command, returning (exit code, stripped stdout, stripped stderr).

    There is no `timeout=` here, and there was one until 2026-08-20 that no
    production caller ever passed. `_fetch` is the only time-boxed call in this
    script and it cannot come through this function, because it must not ask
    for pipes -- see `_fetch` for why. So the parameter could not acquire a
    caller without undoing that fix, and a tested path with no caller is inert
    whatever the coverage number says. Mutating `_run` to drop `timeout=timeout`
    survived all 63 tests, which is what that looks like from the outside.

    `subprocess.TimeoutExpired` went with it. `subprocess.run` cannot raise it
    when no timeout is passed, so catching it here was a second inert path
    behind the first.
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
        )
    except OSError:
        return 1, "", ""
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git(*args: str) -> tuple[int, str]:
    """Run a git command, returning (exit code, stripped stdout)."""
    code, out, _ = _run(*args)
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
        return _git_is_refusing(stderr)

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


def _looks_like_a_repository(start: Path) -> bool:
    """Whether a `.git` entry sits at `start` or above it.

    Filesystem only, and deliberately so: this is consulted after git has
    already refused to answer, which makes anything git says about itself
    unavailable. `.git` is a directory in a main worktree and a file in a
    linked one, so existence rather than type is the test. The walk upwards
    mirrors git's own discovery, so that `--doctor` run from a subdirectory of
    a repository git will not open is not reported as standing outside a
    repository -- which is the same defect one directory down.
    """
    return any((directory / ".git").exists() for directory in (start, *start.parents))


def _git_is_refusing(stderr: str) -> list[str]:
    """Report a git that will not run here, having already exited non-zero.

    `git rev-parse --git-dir` fails for two very different reasons: there is no
    repository here, or there is one and git is refusing to open it. Nothing
    git can be asked separates them, because everything git is asked fails the
    same way. Checked 2026-08-20: `-c core.bare=false` does not override a bad
    value, `git config -f .git/config` does not sidestep it, and a
    subdirectory behaves identically.

    **So the discriminator is the filesystem, not the message.** Until
    2026-08-20 this sniffed stderr for `core.bare` and returned `[]` for
    everything else, on a stated dichotomy -- the failure either names
    `core.bare` or is "not a git repository" -- that is false. There is a third
    class naming neither: a junk line in `.git/config` gives `fatal: bad config
    line 8 in file .git/config`, and `core.repositoryformatversion = banana`
    gives its own. Both make every git command in the checkout exit 128, and
    `--doctor` printed `git hygiene: clean`, rc 0, standing in one. Reproduced
    and fixed 2026-08-20. `.git` existing while git refuses to open it is
    message-independent and locale-independent, which the sniff was not.

    `core.bare` keeps its own message where git names it, because that value can
    be repaired by hand and the general case cannot even be named. Neither is
    repaired by `--fix`: `check_bare` returns through here before `fix` is ever
    consulted.

    One case is still missed, and is named rather than guessed at: a repository
    reached through `GIT_DIR` or `--git-dir` from a directory with no `.git`
    above it leaves nothing on the filesystem to find.
    """
    said = stderr.splitlines()[0] if stderr.strip() else "(nothing)"

    if "core.bare" in stderr:
        return [
            "core.bare cannot be read at all, and git is refusing every command here.",
            f"    git said: {said}",
            "--fix will not touch this one. Git cannot be asked whether the repository is",
            "meant to be bare while the value is unreadable, and `git config` is refusing",
            "for the same reason -- so edit the `bare =` line in .git/config by hand.",
        ]

    try:
        here = Path.cwd()
    except OSError:  # pragma: no cover - the working directory was deleted under us
        return []
    if not _looks_like_a_repository(here):
        return []  # no repository here; nothing to have an opinion about

    return [
        "git is refusing to operate here, and it is not that there is no repository:",
        "a .git entry exists at or above this directory.",
        f"    git said: {said}",
        "Every git command in this checkout will fail the same way, including the ones",
        "this script would need to diagnose it, so --fix will not touch this one.",
        "Start with .git/config -- a value git cannot parse is the usual cause.",
    ]


def _git_path(name: str) -> Path | None:
    """Resolve a per-worktree path inside the git dir, or None outside a repo."""
    code, path = git("rev-parse", "--git-path", name)
    if code != 0 or not path:
        return None
    return Path(path)


def _integration_in_progress() -> str | None:
    """Which integration git is part-way through, or None if it is not.

    One `rev-parse` covers all of `INTEGRATION_MARKERS`; the flag repeats, and
    git answers one line per flag in order.

    The marker *name* is returned rather than a bool because the caller says it
    out loud. Planting any of these turns the drift guard off for as long as the
    file is there, and `mkdir .git/rebase-apply` is what a crashed `git am`
    leaves behind -- so the exemption has to be able to name itself.
    """
    args: list[str] = ["rev-parse"]
    for name in INTEGRATION_MARKERS:
        args += ["--git-path", name]
    code, out = git(*args)
    if code != 0:
        return None

    paths = [line for line in out.splitlines() if line]
    if len(paths) != len(INTEGRATION_MARKERS):
        # git answered a shape this cannot pair up. Keep the exemption, since
        # refusing the merge that resolves the drift is the failure it closes,
        # but do not claim to know which marker was found.
        return "an integration marker" if any(Path(p).exists() for p in paths) else None
    for name, path in zip(INTEGRATION_MARKERS, paths, strict=True):
        if Path(path).exists():
            return name
    return None


def _fetch_is_stale(stamp: Path | None) -> bool:
    """Whether a fetch is due, judged by a stamp this script writes itself.

    The stamp is written only after a fetch that exited zero, and the reason it
    exists rather than reading `FETCH_HEAD` is that git truncates and re-creates
    `FETCH_HEAD` even when the fetch *fails*. An mtime read off it is therefore
    armed by failure: one run against an unreachable remote blinded this check
    for the next ten minutes, and the case it then waved through -- a `main`
    that fell behind while the remote was briefly away -- is the exact case the
    hook exists for. Reproduced and fixed 2026-08-20.

    **An age outside the window in either direction counts as stale**, and the
    negative half is not hypothetical. `age > FETCH_STALE_SECONDS` is never true
    of a stamp dated ahead of the clock -- a VM clock jump, a restored backup,
    an unzipped archive, a dual boot -- so such a stamp blinded the drift check
    *permanently* rather than for ten minutes, reopening the exact defect the
    stamp was introduced to close. Reproduced 2026-08-20: arm the stamp, set its
    mtime a year ahead, leave `main` genuinely one commit behind -- rc 0 and no
    fetch attempted; remove the stamp -- rc 1.

    No grace is allowed on the negative side, so a filesystem that rounds an
    mtime up past `time.time()` fetches on every commit until the rounding stops
    mattering. That is the safe direction: this fails towards fetching, never
    towards silence.

    **And the stamp has to be a regular file.** `mkdir
    <git-dir>/de-git-hygiene-fetch` suppressed the check for ten minutes at a
    time while `_record_fetch` could never arm it -- writing to a directory
    raises `OSError` and is suppressed -- so the window renewed itself off the
    directory's own mtime and nothing here could close it. Reproduced 2026-08-20
    on a `main` one commit behind: rc 0, no fetch.
    """
    if stamp is None:
        return True
    try:
        stamped = stamp.stat()
    except OSError:
        return True  # missing, or unreadable; either way, fetch
    if not stat.S_ISREG(stamped.st_mode):
        return True  # not something `_record_fetch` could have written
    age = time.time() - stamped.st_mtime
    return not 0 <= age <= FETCH_STALE_SECONDS


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

    **Credential helpers are disabled for this one fetch, and
    `GIT_TERMINAL_PROMPT` alone does not do that.** That variable governs git's
    *own* prompt; a helper is a separate program git launches, and Git
    Credential Manager on Windows launches a GUI. Measured 2026-08-20 against a
    local server answering 401: the fetch returned False after 10.01s -- the
    whole budget, on every commit, for as long as the credentials stay lapsed --
    and left an orphaned `git-credential-manager.exe` holding a dialog, one per
    timed-out fetch, with nothing written anywhere to connect it to a commit
    because both streams are discarded.

    `-c credential.helper=` resets the helper list to empty, `-c core.askPass=`
    and the emptied askpass variables close the other doors, and
    `GIT_TERMINAL_PROMPT=0` turns the remaining prompt into an immediate
    failure -- the same variable, for the same reason, as
    `decision_evals.deployed._git`. Measured after the change: 0.07s against a
    hanging helper that had eaten the full budget before it. A fetch that needs
    credentials is a fetch this hook cannot make, so failing at once beats
    blocking the commit and then failing anyway.
    """
    try:
        proc = subprocess.run(
            [
                "git",
                "-c",
                "credential.helper=",
                "-c",
                "core.askPass=",
                "fetch",
                REMOTE,
                PROTECTED_BRANCH,
                "--quiet",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            env={
                **os.environ,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_ASKPASS": "",
                "SSH_ASKPASS": "",
            },
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return proc.returncode == 0


def check_main_drift() -> list[str]:
    """Refuse a commit on `main` while `main` is behind `origin/main`.

    Only fires on `main` itself, and only when no integration is in progress --
    and it says so when it skips for that reason, naming the marker, because an
    exemption nobody can see is one nobody can debug.
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

    marker = _integration_in_progress()
    if marker is not None:
        # Said out loud: the exemption lasts as long as the marker does, and a
        # crashed `git am` leaves one behind that nobody put there.
        print(f"git hygiene: drift check skipped, integration in progress ({marker})")
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
