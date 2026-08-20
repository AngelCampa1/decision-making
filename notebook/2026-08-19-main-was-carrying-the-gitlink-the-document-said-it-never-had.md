# 2026-08-19 — `main` was carrying the gitlink the document said it never had

A consolidation pass, asked for in plain terms: reconcile every worktree, every
branch, every untracked file into `main`, finish whatever was left half-done,
and delete the rest. The interesting part was not the reconciling. It was that
the tidying turned up a defect in `main` that a document had already ruled out
in writing.

## What was there

- One live worktree, the shared checkout at `D:/code/decision-making`, on `main`.
- Two local branches: `main`, level with `origin/main` at `53d87ce`, and
  `site/instrument-redesign` at `f86269a`.
- One remote branch, `origin/main`. Nothing else on the remote.
- No stashes.
- Two leftover directories where worktrees used to be:
  `.claude/worktrees/instrument-redesign` with 105 files in it, and
  `/d/code/decision-making-wt-toolchain`, empty.
- Untracked: fifteen `.playwright-mcp/` snapshots, and — appearing mid-pass, at
  17:18, from another live session — `scripts/check_git_hygiene.py` with a
  matching `pre-commit` hook.

## The gitlink

`docs/AUTONOMOUS_WORK_ORDER.md` carried this, in a section written to correct an
*earlier* mis-telling of the same incident:

> the one gitlink this repository has had lived in two `WIP:` auto-commits that
> never reached `main`, and no `git rm --cached` appears anywhere in the history

Two `WIP:` auto-commits is right. *Neither reached `main`* is wrong:

```
$ git ls-files -s | grep 160000
160000 f12b444fafbbc9c8e3b696e49127c97ea209d2d1 0	.claude/worktrees/instrument-redesign

$ git merge-base --is-ancestor 91f2313 main && echo YES
YES
```

`91f2313` added the entry and is an ancestor of `main`. `f86269a` removed it and
stayed on a branch, unmerged, which is the only reason the entry survived. So
`main` held mode 160000 for as long as the paragraph denying it has existed.

It reproduces on a clean checkout, which is what makes it more than cosmetic.
`git worktree add -b consolidation .claude/worktrees/consolidation origin/main`
materialised an empty `instrument-redesign` directory inside the new tree, from
the gitlink, before anything had been done in it.

**The document was not wrong about the mechanism, only about whether it had
fired here.** Its own prescription — `git rm --cached <path>`, never delete the
worktree — was the fix, unused for as long as the sentence saying it had never
been needed sat above it.

## The contradiction in `AGENTS.md`

`datasets/triggers/decision-making/index.yaml` grew an `ancestry:` block on
2026-08-19 recording that `s13p` descends from v2's `x-n22`, that the text was
edited rather than carried over, and that it "fires in 11 of 14 v4 rows".

`AGENTS.md` still said, in the standing rule on recall bands:

> `x-n22` has never fired in any arm on any version

Both are in `main`. The dataset correction landed; the rule it was written to
correct did not — the corrected wording existed only on `f86269a`, on the branch
nobody merged. A standing rule contradicted by the dataset it reasons about is
worse than either being wrong alone, because the rule is what gets read while
setting the next band.

## What the two leftovers turned out to be

`.claude/worktrees/instrument-redesign` looked alarming: 105 files, ten of them
differing from `main`. All ten differences were line endings until normalised,
and after normalising, every one of the 57 source files hashes to a blob already
in the object database:

```
checked=57  not_in_db=0
```

It is the abandoned working tree of `worktree-instrument-redesign`, which merged
at `889268c` and was pushed. Its genuinely disk-only lines are all code `main`
deliberately deleted — the `de site --deploy` machinery and its `ghp-import`
dependency. Nothing to keep.

`site/instrument-redesign` is the same story with two exceptions. Its instrument
work — the item-analysis estimators, `report_item_analysis`, the notebook entry —
all landed on `main` by a different route and was then hardened by review that
the branch never saw. What did *not* land is the pair above — the gitlink removal
and the recall-band correction — **and two tracked files nobody was looking for**:
`page-2026-08-19T18-10-55-531Z.yml` and `page-2026-08-19T18-14-38-466Z.yml`, 264
lines each, committed on that branch and on no other ref.

Those two are worth dwelling on, because the method missed them and a review
caught them. The pass asked two questions — what is untracked in the working
tree, and what does the branch change in *source* — and these were neither. They
were tracked, on a branch, and they are snapshot dumps, the category already
filed as debris. Deleting the branch would have destroyed them, which is exactly
what the same pass had argued against one commit earlier while committing fifteen
of their siblings. A category judgement made once ("debris") kept being applied
after the pass had itself decided the opposite ("committed as a record").

## Two sessions landed the same work, and `main` got the worse copy

While this pass was finishing the hygiene chunk in an isolated worktree, the
session that wrote it committed its own copy straight onto `main` and pushed:
`c9f210c`, at 09:18 the following morning. Same script, same `pre-commit` block.

What landed there is the version *before* the review: no
`tests/unit/test_check_git_hygiene.py` at all, and `check_bare` still reading

```python
git("config", "--local", "--get", "core.bare")
```

which is the raw-string comparison that reports `git hygiene: clean` on a
repository with `bare = 1`. So for several hours `main` carried the guard with
its one real bug intact and nothing to catch a regression in it.

This is not a complaint about the other session — it committed work it had
written, which is the normal thing to do. It is a note about what "consolidate
into `main`" means when `main` is moving: the rebase turned into a conflict whose
only hunk was the bug fix, and resolving it correctly meant knowing which side
had been reviewed. A merge that took `main`'s side, or a fast `--ours`, would
have silently thrown the fix and the 35 tests away and left every gate green.

The isolation was worth it for exactly this reason. Had the pass been working in
the shared tree, its copy and the other session's copy of the same file would
have been the same bytes on disk, and there would have been nothing to conflict.

## The gitlink was holding the documentation gate up

Removing it turned the documentation step red, and not on the sentence that was
edited. `check_path_references` counts a code span as a repository path only when
its first segment is a top-level **directory on disk**:

```python
top_level = {path.name for path in repo_root.iterdir() if path.is_dir()}
...
if candidate.split("/", 1)[0] in top_level:
    found.add(candidate)
```

The gitlink made `.claude` such a directory in *every* checkout, clean clones
included, because a mode-160000 entry materialises an empty placeholder. So every
`.claude/...` span in the living documents was being resolved — and
`docs/DECISION_FRAMEWORKS.md` carried a `docs-external-paths` line for a
directory in wanikua/thinking-skills purely because of that. The register line
existed to excuse a reference that was only being checked because of a defect.

With the gitlink gone, `.claude` exists only where an agent has made a worktree.
That reference stops being extracted on a clean clone, and the one register line
justifying it becomes "declared ... and named nowhere in the documentation" —
red in CI, green on the maintainer's machine.

**One line, not two.** An earlier draft of this entry and of the commit message
said "both lines are deleted". Only one existed to delete:
`[tool.decision-evals.docs-external-paths]` held exactly one key on `53d87ce`,
and the second line was one this pass had added and then removed again on
discovering it could never be justified either. Corrected here rather than
quietly, since the miscount was in the commit message too.

The line is deleted — which the register itself demands, an entry named nowhere
being a line to delete — and the sentence it excused no longer puts the path in a
code span at all. The two `.claude/` spans that remain resolve wherever `.claude`
exists and are invisible where it does not, which is safe in both worlds.

**Checked in both worlds rather than one.** `de check --fast` with `.claude`
present, then again with it removed — the documentation step passes in each, and
the second is the one CI runs. A gate that reads the filesystem has two answers
and the local one is not the one that matters.

**And the same mechanism sits under `.venv`, which is why "both worlds" needed
saying more carefully.** `.venv/Scripts/de.exe` is in the ignored register and
its span flips on whether `.venv` is a directory, exactly as `.claude` did. Both
verification runs above happened to have a `.venv`, so neither would have caught
it; a review did. It is not a live defect — `de` lives inside `.venv`, so the
world where it fires is a world with no `de check` to fire in — but the claim
"verified in both worlds" was true by accident before it was true by argument,
and those are different things.

## The chunk that arrived mid-pass

`scripts/check_git_hygiene.py` and its `pre-commit` entry were untracked in the
shared tree, written by another session at 17:18 while this pass was reading the
same directory. Its intent is legible from its own docstring: two invariants out
of the 2026-08-19 failure where a branch switch left `core.bare = true` and every
working-tree operation in the shared checkout refused for four hours. The drift
half is a hook that refuses a commit on `main` while `main` is behind
`origin/main`; the `core.bare` half is `--doctor`/`--fix` and deliberately not a
hook, because with `core.bare` set git aborts before any hook runs.

Finishing it turned up a false negative in the half that exists for the emergency.
`check_bare` compared the raw config string to `"true"`, and git accepts `1`,
`yes` and `on` as spellings of the same flag. `bare = 1` makes `git status` exit
128 identically, and the doctor printed `git hygiene: clean` on exactly that
repository — the one command you reach for when git is refusing everything,
silent on a real instance of what it looks for. It now reads the value through
git's own bool parser.

`tests/unit/test_check_git_hygiene.py` covers both halves, and two of its tests
are load-bearing rather than incidental: one asserts the refusal comes from the
fetch rather than from the ref already on disk, which is the case where the check
would otherwise return a plausible zero on the exact situation it exists to
catch; the other pins that a flagless run — what the hook actually invokes — does
*not* check `core.bare`, so the `--doctor` tests cannot later be misread as
evidence that a commit is guarded against it. Removing the fetch and reverting
the bool parse fails eight tests, so the suite discriminates.

No coverage floor was added, and that is the precedent rather than an omission:
`[tool.coverage.run]` measures `evals/src/decision_evals` only, `scripts/` is
outside it, and `scripts/run_triggers.py` is tested the same way with no floor
and no register entry.

**What was left alone.** `DE_SKIP_GIT_HYGIENE` is checked before the mode is
dispatched, so it silences `--doctor` and `--fix` too — someone reaching for
`--fix` with the variable still exported from an earlier bypass gets exit 0 and
no repair. It also treats any non-empty value as "skip", so `=0` skips. Both are
pinned by tests that say in their docstrings that the behaviour is recorded
rather than endorsed. Changing either needs a decision about whether the variable
names the hook or the script, and nobody has written that down.

## The guard had five defects, four in the half that runs on every commit

The hygiene script was reviewed as recovered work, by an agent briefed to break
it. It found six things; five reproduced. Listing them because the pattern is
more useful than any one of them: **every single one was a case where the check
returned a plausible zero, or fired on the wrong thing, and nothing looked
wrong.**

- **A failed fetch armed the ten-minute suppression window.** `git fetch` creates
  `FETCH_HEAD` even when it fails, and staleness was read from that mtime alone.
  One unreachable-remote run therefore blinded the check for ten minutes. This is
  the exact failure the suite's own central test was written to prevent — "the
  estimator returns a plausible zero on the situation it exists to catch" —
  reached through the ordinary offline path instead of by deleting the fetch.
- **The hook refused the merge that resolves the drift.** Mid-conflict, `main` is
  both behind and ahead. The guard fired on the merge commit, stated on its
  second line that `--ff-only` would refuse, and advised `git pull --ff-only` on
  its fourth. Git answers that with `fatal: Exiting because of unfinished merge.`
  A guard whose only exit is the bypass teaches the bypass.
- **`--doctor` false-positived on a genuine bare repository with linked
  worktrees, and `--fix` then corrupted it** — set `core.bare` false on the
  shared config and left `git status` failing with `must be run in a work tree`.
  The repair tool inflicting the symptom it exists to cure, printing "clean" as
  it went.
- **A `core.bare` git cannot parse reported clean.** The same defect as `bare = 1`
  one spelling along, and the reported fix location was wrong: `rev-parse
  --git-dir` itself exits 128 on `bare = maybe`, so no later exit code is ever
  reached. Worth recording because the first fix attempt failed for that reason,
  and a fix that is not re-checked against the original reproduction would have
  shipped looking correct.
- **The fetch was never time-boxed**, though the docstring and the hook comment
  both promised it. `subprocess.run(timeout=…)` kills the child and then blocks
  draining pipes the transport grandchild still holds: 60.4s measured under a 2s
  timeout against a hung `ssh`.

Four of the five sit in the drift half, which runs on every commit to `main`.

**The tests did not catch any of them, and they were not bad tests.** 35 tests,
mutation-checked before the review: removing the fetch failed eight of them. But
four mutants survived all 35 — most sharply `FETCH_STALE_SECONDS = 10**9`, which
gates the fetch off entirely without deleting it. The test written to prove the
fetch is load-bearing was immune, because a fresh `git clone` writes no
`FETCH_HEAD`, so the staleness window never mattered in the fixture. **A test can
pin a line against deletion and leave it free to be disabled.**

What made the replacements discriminate was recording every `git` argv around the
call under test, so a guard is pinned by *what it stops* rather than by a return
value that a later `return []` produces anyway — two tests were passing with
their guard deleted for exactly that reason. And backdating fixtures by a fixed
hour rather than by `FETCH_STALE_SECONDS`, since a test that backdates by the
constant it tests moves with the mutant. 63 tests now, 13 of 14 mutants dead, the
fourteenth equivalent and documented rather than given an invented test.

## What this cost, and what it did not

Nothing here was found by being careful. The gitlink was found by making a
worktree and noticing a directory that should not have been there; the
`AGENTS.md` contradiction was found by diffing a branch nobody expected to
contain anything. Both had been sitting in `main` through every green `de check`,
because neither is a thing the gate can ask about: `git ls-files -s` is not
consulted anywhere, and no check compares a sentence in `AGENTS.md` against a
`note:` in a dataset.

The second one is not worth building a gate for — that way lies a prose linter,
which `docs.py` declines to become for reasons already written down. The first
one might be. A check that refuses mode 160000 anywhere in the index is three
lines and has no false positives in a repository with no submodules.
