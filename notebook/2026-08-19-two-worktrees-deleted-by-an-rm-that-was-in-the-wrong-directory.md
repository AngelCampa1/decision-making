# Two worktrees deleted by an `rm` that was in the wrong directory

**2026-08-19.** While writing the rule that moves worktrees *into* the
repository, I destroyed two other sessions' worktrees with a single `rm -rf
.claude`. This entry is the record, and the reason the new rule carries a
warning it would not otherwise have.

## What happened

I was testing whether the documentation gate breaks when `.claude/` exists at
the repository root. The probe was `mkdir -p .claude/worktrees/scratchprobe`,
run the gate, `rm -rf .claude`. I believed the shell was inside my own worktree.
It was not: the `cd` into that worktree had been issued several commands
earlier, in a different tool call, and the working directory had reverted to
`D:/code/decision-making`. So the delete landed on the real scratch directory.

| Worktree | Owner | State after |
|---|---|---|
| `item-analysis` | another session | emptied to zero files |
| `instrument-redesign` | another session, `locked` | everything but `site/` removed |
| `landing-workflow` | mine | destroyed |

`instrument-redesign` survived in part only because Windows refused to unlink
files another process held open. The lock did not protect it; a file handle did.

## What came back, and what did not

Everything under `.git/worktrees/` survived — the per-worktree admin
directories, their `HEAD` files and their indexes. So branch refs were intact
and committed work was never at risk. I checked each damaged worktree's index
against its `HEAD` before touching anything: **both matched exactly**, meaning
nothing was staged-but-uncommitted, and restoring from `HEAD` could not
overwrite staged work. Both were then restored with `git checkout -- .` and
report clean on their original branches.

**Unstaged edits and untracked files in those two worktrees are gone.** Git
never held them. I do not know whether either session had any in flight, and
there is no way to find out from here — which is the part of this that cannot be
repaired by being careful next time.

## Why it is in the record rather than only in the rule

Three things this cost that are worth more than the apology:

1. **The hazard was predicted and I hit it anyway.** An adversarial reviewer had
   flagged, hours earlier, that moving worktrees into an *ignored* directory
   puts every session's work inside the blast radius of one delete at the
   repository root — impossible under the sibling layout. It was filed as a
   medium-severity defect. It then happened, to the person holding the finding,
   via an ordinary `rm` rather than the `git clean -xdff` the reviewer named.
2. **A shell's working directory is not state you may assume across tool
   calls.** The `cd` and the `rm` were in different calls. Nothing between them
   announced that the directory had reverted. Any destructive command must
   re-derive its own target — an absolute path, or a `pwd` in the same
   invocation — rather than inherit one.
3. **`locked` is not protection.** `git worktree lock` guards against git's own
   pruning and removal. It does nothing about a filesystem delete, which is what
   actually threatens a worktree that lives inside an ignored directory.

## What changed as a result

[`docs/AUTONOMOUS_WORK_ORDER.md`](../docs/AUTONOMOUS_WORK_ORDER.md) now says, in
the section that mandates the nested location, that the ignore rule which makes
the location workable is the same property that makes it destructible, and that
a recursive delete or forced clean at the repository root is never to be run.
The rule is kept — this was maintainer instruction and the two arguments
originally given against nesting were, on measurement, one false and one already
fixed — but it now ships with the cost stated beside it rather than discovered
later.

Nothing mechanical prevents a recurrence. `de check` cannot see a shell's
working directory, and no gate in this repository runs before an `rm`.
