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
`--fix` repairs neither -- see `_git_is_refusing`.

**Deciding that takes two signals, and either one alone gets a case wrong.**
Replacing the stderr sniff with a filesystem walk moved the wrong answer rather
than removing it: with discovery blocked by `GIT_CEILING_DIRECTORIES`, a
healthy checkout was reported as broken, because `.git` was sitting there while
git had been told not to look at it. And the walk missed bare repositories
entirely, which carry no `.git` at all, so `git init --bare` plus a junk line in
`config` still printed `clean`. Both reproduced 2026-08-20. Git's message
settles the cases it names -- "discovery found nothing" is not a thing a
filesystem walk can second-guess -- and the filesystem settles the cases where
the message names nothing. See `_git_is_refusing` and `_repository_shape`.

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

**Credentials are left alone, and the time-box is what pays for that.** For
one round of review this fetch ran with `-c credential.helper= -c
core.askPass=` and the askpass variables emptied, to stop Git Credential
Manager opening a dialog nobody could see. That does not merely stop a
*hanging* helper; it stops a *working* one, and on any private HTTPS remote --
the default GitHub setup -- every fetch the hook made then failed, after which
the drift check compared against the stale ref on disk and passed, rc 0, with
nothing on either stream. Measured 2026-08-20 against a local server requiring
Basic auth: 0.40-0.51s and success with the helper active, 0.07-0.09s and
failure with it emptied; `GIT_ASKPASS` and `core.askPass` measured the same way
round. A silent blind spot on every private remote is worse than the ten-second
stall it replaced, so the switches are gone. What remains is
`GIT_TERMINAL_PROMPT=0`, which fails git's own prompt rather than waiting on
it, and `GCM_INTERACTIVE=never`, which git itself does not read and so cannot
break a fetch GCM is not part of. `credential.interactive=false` looked like
the same kind of knob and is not -- git core reads it, and it breaks an askpass
that would have answered -- so it is named in `_fetch` as a switch deliberately
not thrown. A helper that hangs anyway costs one bounded budget, once per ten
minutes.

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
import re
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


#: Git's own words for "discovery ran to exhaustion and found nothing here".
#: The parenthetical is the load-bearing half, and it is not decoration:
#: `not a git repository: <path>` *without* it is git having been pointed at
#: something that is not there -- `GIT_DIR`, or a `.git` file naming a gitdir
#: that has gone -- which is a broken repository rather than an absent one.
#: Both messages measured 2026-08-20; they must not be collapsed into a
#: substring search for "not a git repository".
DISCOVERY_EXHAUSTED = "not a git repository (or any of the parent directories)"

#: Git names the file it could not parse, so the remedy can name it back
#: instead of guessing `.git/config`. Matches a local config, a global one and
#: a system one identically, because git's message does.
BAD_CONFIG_FILE = re.compile(r"bad config line \d+ in file (?P<path>.+)")


def _repository_shape(start: Path) -> str | None:
    """What on the filesystem says a repository is here, phrased for the report.

    Consulted only where git's own message settles nothing -- see
    `_git_is_refusing` -- because a git that is refusing every command cannot be
    asked anything about itself.

    Two shapes, because a repository has two. A checkout carries a `.git`
    entry: a directory in a main worktree and a file in a linked one, so
    existence rather than type is the test. The walk upwards mirrors git's own
    discovery, so that a subdirectory of a checkout git will not open is not
    reported as standing outside a repository -- the same defect one directory
    down.

    **A bare repository carries no `.git` at all**, which is how that whole
    class escaped until 2026-08-20: `git init --bare`, a junk line appended to
    `config`, `git status` exits 128 with `fatal: bad config line 7 in file
    ./config` -- and `--doctor` printed `git hygiene: clean`, rc 0, standing in
    it. Requiring a `.git` entry exempted every bare repository there is. One is
    recognised by its own shape instead: a `HEAD` file beside `objects/` and
    `refs/`, which is what git's own `is_git_directory` looks for.
    """
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return "a .git entry exists at or above this directory."
        if (
            (directory / "HEAD").is_file()
            and (directory / "objects").is_dir()
            and (directory / "refs").is_dir()
        ):
            return f"a bare repository is laid out at {directory}."
    return None


def _said(stderr: str) -> list[str]:
    """Every non-empty line git wrote, not only the first, as one quoted block.

    The first line was all that used to be quoted, and it threw away the half
    that mattered for one class: `fatal: detected dubious ownership in
    repository at ...` is followed by git printing the exact `git config
    --global --add safe.directory ...` that repairs it. Quoting line one alone
    dropped git's own remedy and then printed a wrong one underneath. Measured
    2026-08-20 via `GIT_TEST_ASSUME_DIFFERENT_OWNER=1`.

    The continuation lines are aligned under the first rather than each
    carrying its own `git said:`, so that a command git printed for the reader
    to run still looks like a command.
    """
    lines = [line.rstrip() for line in stderr.splitlines() if line.strip()] or ["(nothing)"]
    first, *rest = lines
    return [f"    git said: {first}", *(f"{' ' * 14}{line}" for line in rest)]


def _remedy(stderr: str) -> list[str]:
    """One line of advice, and only where the evidence supports one.

    Every report used to end with `Start with .git/config -- a value git cannot
    parse is the usual cause`, which is right for exactly one of the classes
    that reach here and wrong for the rest. `detected dubious ownership` is
    repaired by `safe.directory`, and the repository itself is fine. A broken
    *global* config is repaired in `~/.gitconfig`, and git names that path in
    its own message. A `GIT_DIR` pointing at nothing leaves the checkout
    entirely healthy. Three classes newly detected on 2026-08-20, three wrong
    remedies -- the detection was the improvement, the advice was not.

    So where git names the file it could not parse, that file is named back --
    and where it does not, there is no specific remedy at all and the quoted
    `git said:` lines carry it, which for dubious ownership is git's own
    command.
    """
    match = BAD_CONFIG_FILE.search(stderr)
    if match is None:
        return []
    return [
        f"Start with {match.group('path').strip()} -- a value git cannot parse is the usual cause."
    ]


def _git_is_refusing(stderr: str) -> list[str]:
    """Report a git that will not run here, having already exited non-zero.

    `git rev-parse --git-dir` fails for two very different reasons: there is no
    repository here, or there is one and git is refusing to open it. Nothing git
    can be *asked* separates them, because everything git is asked fails the
    same way. Checked 2026-08-20: `-c core.bare=false` does not override a bad
    value, `git config -f .git/config` does not sidestep it, and a subdirectory
    behaves identically.

    **So two signals answer it, and neither is trusted alone.** Each was the
    sole discriminator for one round of review, and each was wrong on its own:

    - **What git said, where it names the outcome.** `DISCOVERY_EXHAUSTED` is
      git reporting that its own walk ran and found nothing, and no filesystem
      inspection may overrule it. Reproduced 2026-08-20: with
      `GIT_CEILING_DIRECTORIES` set to a repository's root and the command run
      from a subdirectory, git says exactly that while `.git` sits one level up
      -- and a filesystem-only discriminator failed a perfectly healthy
      repository, rc 1, on the literal case it claimed to exclude.
    - **What is on disk, where the message names nothing.** A junk line in
      `.git/config` gives `fatal: bad config line 8 in file .git/config`, and
      `core.repositoryformatversion = banana` gives its own; both break the
      checkout completely and neither names `core.bare` or "not a git
      repository". Sniffing stderr for `core.bare` printed `git hygiene: clean`,
      rc 0, standing in one. Reproduced 2026-08-20.

    The division is what makes the pair safe. The message is consulted only for
    the one outcome it states outright, the filesystem only for the messages
    that state nothing -- so neither signal is ever in a position to produce the
    other's wrong answer. Both halves are locale-dependent to the extent that
    git translates its messages, which by default it does not.

    `core.bare` keeps its own message where git names it, because that value can
    be repaired by hand and the general case cannot even be named. Neither is
    repaired by `--fix`: `check_bare` returns through here before `fix` is ever
    consulted.

    Two cases are still missed, and are named rather than guessed at. A
    repository reached through `GIT_DIR` or `--git-dir` from a directory with no
    repository shape above it leaves nothing on the filesystem to find. And a
    broken *global* config outside any repository is silent here, because this
    script has no opinion outside a repository -- inside one it is reported,
    with git's own path in the remedy.
    """
    if "core.bare" in stderr:
        return [
            "core.bare cannot be read at all, and git is refusing every command here.",
            *_said(stderr),
            "--fix will not touch this one. Git cannot be asked whether the repository is",
            "meant to be bare while the value is unreadable, and `git config` is refusing",
            "for the same reason -- so edit the `bare =` line in .git/config by hand.",
        ]

    if DISCOVERY_EXHAUSTED in stderr:
        return []  # git looked, and it says there is nothing here to look at

    try:
        here = Path.cwd()
    except OSError:  # pragma: no cover - the working directory was deleted under us
        return []
    shape = _repository_shape(here)
    if shape is None:
        return []  # no repository here; nothing to have an opinion about

    return [
        "git is refusing to operate here, and it is not that there is no repository:",
        shape,
        *_said(stderr),
        "Every git command in this checkout will fail the same way, including the ones",
        "this script would need to diagnose it, so --fix will not touch this one.",
        *_remedy(stderr),
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

    **And the stamp has to be a regular file, tested without following a
    link.** `mkdir <git-dir>/de-git-hygiene-fetch` suppressed the check for ten
    minutes at a time while `_record_fetch` could never arm it -- writing to a
    directory raises `OSError` and is suppressed -- so the window renewed itself
    off the directory's own mtime and nothing here could close it. Reproduced
    2026-08-20 on a `main` one commit behind: rc 0, no fetch.

    `stat()` closed that one instance and left the class open, because it
    follows symlinks. A symlink at the stamp path pointing at any regular file
    reads as a regular file, so the window was suppressed off an mtime
    `_record_fetch` never wrote -- and `_record_fetch` writes *through* the
    link, so a symlink to `.git/config` was truncated by the next successful
    fetch. Both measured 2026-08-20: `_fetch_is_stale` returned False, and the
    target came back empty. `lstat` answers about the link itself, so a symlink
    is no longer mistaken for a regular file here -- and `_record_fetch` carries
    the other half, because reading with `lstat` does nothing whatever about
    writing with `write_text`.

    **A hardlink is still indistinguishable, and that is not fixed here.**
    `lstat` reports a hardlink to `.git/config` as exactly the regular file it
    is, because that is what it is; `st_nlink > 1` would catch it on some
    filesystems and not others. The class is narrowed, not closed. Nothing
    inside the git dir is normally hardlinked, and creating one there is a
    deliberate act rather than an accident like `mkdir`.
    """
    if stamp is None:
        return True
    try:
        stamped = stamp.lstat()
    except OSError:
        return True  # missing, or unreadable; either way, fetch
    if not stat.S_ISREG(stamped.st_mode):
        return True  # a directory or a symlink; not something `_record_fetch` wrote
    age = time.time() - stamped.st_mtime
    return not 0 <= age <= FETCH_STALE_SECONDS


def _record_fetch(stamp: Path | None) -> None:
    """Arm the suppression window. Called only after a fetch that succeeded.

    **Nothing is written through a link, and this is the destructive half of the
    symlink defect.** Teaching `_fetch_is_stale` to use `lstat` stops a symlink
    *suppressing* the window and does nothing at all about `write_text`
    following one: measured 2026-08-20 with the stamp path a symlink to a
    `config` file, a successful fetch left the target empty. `.git/config` is
    one `ln -s` away from the stamp path, and truncating it breaks the whole
    checkout -- so this would have destroyed the file the rest of the script
    exists to complain about.

    So the shape is checked on this side too, and anything already there that is
    not a plain file is left exactly as it is. `Path.is_symlink`, `exists` and
    `is_file` all answer False rather than raising, so there is no error branch
    here to go untested. The cost is the window, never the check: a stamp that
    is never written is always stale, so the hook simply fetches every time.
    """
    if stamp is None:
        return
    if stamp.is_symlink() or (stamp.exists() and not stamp.is_file()):
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

    **Credential helpers stay enabled, and the last round of review is why
    that has to be said out loud.** A hanging Git Credential Manager was
    measured here on 2026-08-20 -- against a local server answering 401 the
    fetch returned False after 10.01s, the whole budget, on every commit, and
    left an orphaned `git-credential-manager.exe` holding a dialog nobody could
    see -- and the fix was `-c credential.helper= -c core.askPass=` with
    `GIT_ASKPASS` and `SSH_ASKPASS` emptied. That does not disable a *hanging*
    helper. It disables a *working* one.

    Measured the same day against a local server requiring Basic auth, with a
    helper that answers correctly: the fetch succeeds in 0.40-0.51s with the
    helper active and fails in 0.07-0.09s with the list emptied, and the reset
    takes URL-scoped `credential.<url>.helper` with it. `GIT_ASKPASS` and
    `core.askPass` measure the same way round: 0.44s and 0.30s answering, both
    `fatal: could not read Password` once emptied. So on any private HTTPS
    remote -- the default GitHub plus GCM setup -- every fetch this hook made
    failed, and `check_main_drift` then compared against the stale ref on disk
    and returned nothing, rc 0, with both streams discarded. That is the
    estimator-returns-a-plausible-zero failure, permanent and invisible, traded
    for a stall that was bounded.

    So the switches are gone. What is left is prompt suppression that does not
    touch authentication:

    - `GIT_TERMINAL_PROMPT=0` turns git's *own* terminal prompt into an
      immediate failure -- the same variable, for the same reason, as
      `decision_evals.deployed._git`. Every successful authenticated fetch
      measured above had it set, so it costs nothing.
    - `GCM_INTERACTIVE=never` asks Git Credential Manager not to raise a GUI
      while leaving stored credentials readable. **Measured only for what it
      does not break**: an authenticated fetch still succeeds with it set,
      through a helper (0.44s) and through askpass (0.36s). Git itself does not
      read the variable, so it cannot break a fetch that GCM is not part of.
      That it actually suppresses GCM's dialog is *not* measured here -- there
      is no GCM on the machine these numbers came from -- and against a generic
      helper that simply sleeps it was measured to do nothing at all. It is a
      best-effort narrowing, not the defence.

    **`-c credential.interactive=false` was in this list for about an hour and
    is deliberately not here now.** It looked like the same kind of knob and it
    is not: git core reads it, and with it set an askpass that would have
    answered fails with `fatal: unable to get password from user`. Measured
    2026-08-20 -- rc 128 in 0.09s with it, rc 0 in 0.23s without. It passed a
    first check only because that check went through a credential *helper*,
    which returns a stored credential without prompting, so the setting had
    nothing to suppress. The same over-fix as the one above, one config key
    over, caught only because the second measurement was taken.

    **The defence is the time-box**, which is now genuinely sound: a helper that
    hangs anyway costs one bounded budget, once per `FETCH_STALE_SECONDS`, and
    then the commit proceeds against the ref on disk. A bounded stall that
    fetches correctly beats an instant failure that never does.
    """
    try:
        proc = subprocess.run(
            [
                "git",
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
                "GCM_INTERACTIVE": "never",
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
