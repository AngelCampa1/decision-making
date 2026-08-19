# 2026-08-19 — `de check` had never run on a clean clone, and it does not pass there

Adding CI was meant to be half a day of YAML. The first thing it did was fail,
and the reason is not CI's.

`de check` has been the answer to "does this work" since the repository started.
It is offline, deterministic, makes no model calls, and it is run before anything
is believed. What nobody had checked is the assumption underneath every green
run: **that the tree which passes the gate is the tree that was committed.**

It is not. A fresh `git worktree` off local `main`, `uv sync`, `de check` — the
sequence a new contributor would run — fails.

## What was found

`main` at `f12b444` does not import.

```
File "evals/src/decision_evals/cli.py", line 25, in <module>
    from decision_evals.claims import census as claims_census
ModuleNotFoundError: No module named 'decision_evals.claims'
```

`git log -S"decision_evals.claims" -- evals/src/decision_evals/cli.py` returns
`f12b444` and nothing else, and `git show --stat f12b444` adds no `claims` file
anywhere. The commit added the import and not the module. `claims.py` exists,
untracked, in the working tree it was written in. So the tip of `main` is a
commit at which the CLI cannot start, and no local gate could ever have said so,
because the file was on disk every time the gate ran.

Backing up one commit to `0ee75d4`, which imports, and running the full gate:

| step | result |
|---|---|
| git identity, ruff, ruff format, mypy, skill lint, trigger sets, plugin manifests, citations, run provenance, integrity wiring, decision register, checkpoint label versions, coverage floors | **13 pass** |
| documentation | **fail**, 4 unresolvable links |
| site | **fail**, manifest stale against 1 input |
| pytest | **fail**, 4 of 1,603 |

Every failure has the same shape.

**The documentation gate, 4 links.** Two name paths that `.gitignore` excludes
by design — `results/track-0/tree_smoke.jsonl` (`docs/AUTONOMOUS_WORK_ORDER.md`)
and `results/triggers/adjudication.jsonl` (`docs/STATUS.md`). Those directories
are ignored for a stated and correct reason: they are append-only working files
that cannot be committed mid-run. But it means those two links **can never
resolve for anyone who clones this repository**, and the gate's own sentence is
the indictment — *a link the reader cannot follow is the same defect as a command
that does not run*. The other two name
`notebook/2026-08-13-the-gate-that-was-documented-and-never-ran.md`, which is
untracked. That title is not lost on me.

**The site gate.** `site/build-manifest.json` at `0ee75d4` was built from a tree
containing that same uncommitted notebook entry, so the committed manifest
describes 161 inputs of which 1 is not in the repository. The manifest is
evidence of a build that cannot be reproduced from the commit it sits in.

**pytest, 4 failures, in two classes.** Two —
`test_bfcl.py::test_every_actions_record_in_the_corpus_parses` and
`test_sharded.py::test_the_real_corpus_carries_what_is_declared` — need the
vendored corpus, which is pinned by hash and deliberately not committed. `de
fetch` resolves both, and CI now runs it; that one is setup, not a defect.
`test_cli.py::TestSiteStep::test_the_real_repository_is_current` is the site
manifest again. And
`test_telemetry.py::TestRecordSchema::test_the_published_checkpoints_were_actually_found`
asserts `len(_RUN_RECORD_CHECKPOINTS) >= 2` and finds 1, because the second
checkpoint lives under the ignored `results/track-0/`. That assertion exists to
stop an empty glob making the test above it vacuously green — it is a good test —
and on a clean clone it is structurally unpassable.

## What this is, and what it is not

It is not that the gate is wrong. Every one of these refusals is the gate working:
it says a referenced path does not exist, and the path does not exist. It is that
the gate has only ever been asked about a tree that was a superset of the commit.

The failure mode is the one this repository keeps rediscovering under different
names — `triggers` tested to 100% and called by nothing, `prereg.py` carrying
every refusal with no caller, `docs/PROTOCOL.md` §3 describing a refusal that had
never run. Each time, something was verified in an arena where it could not fail.
This is that again, one level out: **the gate itself had never been run in the
arena it is a claim about.** `de check` passing has always meant "passes on the
maintainer's machine". It was read as "passes".

Two of the defects are permanent and need a decision rather than a fix — a living
document may not link a path the `.gitignore` guarantees is absent, and a test may
not assert on one. The rest resolve when the sessions holding those files commit
them.

## What changed

`.github/workflows/check.yml`. Full `de check`, not `--fast`, on every push and
pull request. `fetch-depth: 0`, because the run-provenance gate walks git
ancestry and a shallow clone has none. `de fetch` before the tests, because the
pinned corpus is how a clean checkout reaches the state the tests describe. A
commit identity configured to the address the gate demands.

It is red on arrival, and that is the finding rather than a snag to route around.
A CI made green by relaxing any of the above would have re-created, in a new
place, exactly the thing it just caught.

A second job deploys the site on pushes to `main`, gated on `check`. That closes
the other gap the repository names about itself: `de check` is offline by design
and so cannot consult `origin/gh-pages`, and nothing checked that anyone had run
`de site --deploy`.

## Predicted, and wrong

The plan that produced this work said to expect Windows-only path assumptions in
`isolated_cwd()` and `site.py` to surface on Linux. That is untested — nothing
got as far as the Linux run, because the failures above reproduce on the
authoring machine the moment the tree is a clean checkout rather than a working
directory. The prediction may still be right; it has not been checked.
