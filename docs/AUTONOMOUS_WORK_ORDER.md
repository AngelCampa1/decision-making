# Autonomous work order

**For an agent pointed at this repository and left running for hours or days.**

Read this before [`RESEARCH_PROGRAMME.md`](RESEARCH_PROGRAMME.md). The programme
says what the work is. This says how to do it without a human in the loop.

**Run continuously until the programme is finished.** Maintainer instruction,
2026-08-13, and it replaces the previous framing of this document. There is no
step here that hands work back and waits. When something is ambiguous, resolve
it by the rule that covers it, write down what you resolved and why, and keep
going. An agent idling on a question the maintainer has already answered is the
failure this revision exists to remove.

The rules below are not general good practice. Every one of them exists because
the specific failure it prevents has already happened here, and the reference is
given so you can check rather than take it on trust. **They are about keeping
the record honest, not about pausing.**

---

## The five standing rules

### 1. Never invent a missing parameter. Derive it, or record the choice as a choice.

If a number you need is not written down — an item count, a threshold, a turn
count — **do not quietly choose one.** Derive it from something already measured
and show the derivation, or state in `notebook/` that you picked it, what you
picked, and what it would take to measure instead. Then continue.

*Why.* The programme said Track A1 would shard casefiles "across ~6 turns". That
figure had no source; the paper it came from sweeps 2→8 and reports no mean. It
was invented, written down, and would have been designed around. An invented
parameter is indistinguishable from a measured one three days later.

### 2. A falsifier must be run against a known-good case before it may fail anything.

Before any gate is allowed to kill a venue, construct a case you are confident
*should pass*, and confirm the gate passes it. If it does not, the gate is wrong.

*Why.* Two falsifiers were wrong on 2026-08-11. Track 0's required `cache_read`
to climb turn over turn; measured, it stays at **0** while context demonstrably
carries, so a healthy venue would have been declared dead
([`notebook/2026-08-11-multi-turn-already-worked.md`](../notebook/2026-08-11-multi-turn-already-worked.md)).
Track A's kill condition would have terminated the whole programme on a null
that was underpowered by construction — 12 items against the ~127 pairs needed.
Both were written without being run against anything.

### 3. Score against the key mechanically, and adjudicate every failure before believing it.

Run the experiments, record the raw outputs, and compute the figures. What you
may not do is let a *judgement* about a response enter a number without leaving
a trace: **twenty-one of twenty-one** scored failures across three corpora were
the answer key being wrong, not the model
([`docs/FAILURE_TAXONOMY.md`](FAILURE_TAXONOMY.md)), and twice the model produced
a *better* answer than the key allowed.

So the procedure, which runs without a human and does not pause:

1. Score mechanically. A parser decides `fired` / `procedure`; no prose is read
   into a verdict.
2. Send every scored failure to blind adjudication — fresh instances, given the
   turn and the skill's own `Abort if` clauses and **not** the label.
3. Where adjudication disagrees with the key, **the key moves and the notebook
   says which item, which direction, and on whose vote.** Re-score and report
   both numbers.
4. If more than 20% of labels move, the corpus is retired rather than reported.
   That threshold is pre-registered and is mechanical.

Decision tasks here have no executable verifier, which is why step 2 is not
optional. It is also why it is automated rather than a reason to wait.

### 4. Run the full `de check`, not `--fast`, before calling a unit done.

```bash
python -m uv run de check
```

*Why.* `--fast` is what the pre-commit hook runs and **it skips tests and
coverage**. Two skill tests were broken by a refactor on 2026-08-11 and survived
several commits because every one of them passed `--fast`. A green pre-commit
hook is not a green build.

### 5. Cite nothing you have not opened.

A search-result summary is not the paper. Before asserting any number beside an
arXiv identifier, fetch `https://arxiv.org/abs/<id>` and put the verbatim
sentence in the `quote` field of its `paper/refs.bib` entry. `de check` enforces
this; see [`citations.py`](../evals/src/decision_evals/citations.py).

*Why.* Three numbers were misattributed here in a single morning, **all citing
real papers that existed and said something adjacent** — the hardest kind to
catch. One reached the file this repository calls the product and was used to
justify a design decision.

---

## What you may run unattended

Everything here has a machine-checkable success condition and requires no
judgement about an answer key.

| Work | Done when |
|---|---|
| **Track K5 backlog** — two identifiers are outstanding, `2412.06593` and `2505.02151`, added by the K3/K4 pass on 2026-08-14 with their quotes recorded in `docs/DECISION_FRAMEWORKS.md` because another session held `refs.bib` at the time. Move each into `paper/refs.bib` with its `quote` and delete the line | `de check` green with an empty baseline. **`docs/RESEARCH_PROGRAMME.md` said "K5 is closed" for four days while this backlog was non-empty** — a may-only-shrink list can still be added to |
| ~~**Track 0.5** — the attributes are on `RunRecord`/`NodeRecord` and `telemetry.span_attributes()` is tested to 100%, but **nothing in `evals/src` calls it**~~ **done** on 2026-08-18: wired into `orchestrator.py`, the multi-node run the module's own docstring says the vocabulary was written for. Every `NodeRecord` now carries `attributes`, the node's identity and usage reshaped through `span_attributes()` — request model and response model recorded separately, since the tree already knows both — with a safe `{}` default so `results/track-0/tree_smoke.jsonl` (written before this field existed) still loads. `tests/unit/test_orchestrator.py`'s `TestNodeRecordCarriesTelemetryAttributes` asserts on the mapping directly | — |
| ~~**Track 0.6** — `assert_isolated()` raises on `tools` and on `skills` and **never inspects `memory_paths`**~~ **done** on 2026-08-18, decided **(b)**: checked live against claude-code 2.1.159 that a planted `CLAUDE.md` does not change `memory_paths` at all — `--setting-sources ""` blocks it from being read in the first place, confirming for the receipt what `notebook/2026-08-10-isolation-canary.md` already found for the response — so there is no known value of this field that distinguishes a clean isolated call from a compromised one, and gating on it would refuse every run rather than the contaminated ones. `InitReceipt`'s docstring now says the gate covers `tools` **and** `skills` (the code already did; the prose did not say so) and explains why `memory_paths` is recorded rather than gated. Separately, `memory_paths` itself was silently unreadable in production — the real event is a mapping, `{"auto": path}`, and the old `isinstance(value, list)` check read it as `()` regardless, on every call this harness has ever made; fixed in `_memory_paths()`. See `notebook/2026-08-18-memory-paths-is-not-a-gate.md` | — |
| **Fold the `stream-json` transport** into `providers/claude_code.py` beside the single-shot path | the multi-turn canary reproduces: `input_tokens` climbs *and* turn-*n* recalls turn-1 content |
| **Either write `model_claude_code.py` against `lost_in_conversation`'s `generate()` interface, or retire that plan in writing** — the corpus is vendored and pinned and `sharded.py` already runs live against it through this repository's own `Conversation`, bypassing the upstream plugin protocol entirely, so the shim may simply be obsolete | the shim exists and runs, or the programme stops saying it is "still needed". Either way the pin (`c865793f`, SHA-256) reaches a datasheet — `docs/EVAL_SET_DATASHEET.md` covers the authored trigger corpus and never mentions this one |
| **Compute the MDE** for A1–A5 with `stats/power.py`, and write it into the programme beside each experiment | numbers exist where "sized from the MDE" currently is |
| ~~**Track I1** — `stats/reliability.py`~~ **done**, and the programme said so before this table did | — |
| **Track K1–K4, K6** — the decision-frameworks review | `docs/DECISION_FRAMEWORKS.md` exists, every claim carrying a `quote` |

**Two rows were deleted on 2026-08-18 because the work was already done and the
table had not noticed** — `stats/agreement.py`, which `scripts/adjudicate.py`
imports and calls for all four agreement statistics, and the `inspect-ai`
dependency, which is gone and has a comment in `pyproject.toml` explaining why.
**A backlog nobody prunes advertises finished work and is read as a to-do
list.** The audit that found them was briefed to break the claim that the table
was stale, and it found the opposite in two places: Track 0.6 is *less* done
than the programme says, and the vendored-corpus row names an artefact that was
never built because the work took a different route.

---

## How the work is done: sub-agents, adversarially, and nothing believed once

**Maintainer instruction, 2026-08-13.** This is not a style preference. It is
the working method, and it applies to every track.

### 1. Work is sub-agent driven

Dispatch the work to sub-agents rather than doing it inline. One agent per unit
— a corpus band, a gate, an analysis, a document — each given the context it
needs and nothing else. Run independent units concurrently.

*Why it is not just throughput.* An agent that authored a thing is the worst
available reviewer of it, and an agent holding a whole session's context has
already absorbed every assumption in it. A fresh sub-agent given only the
artefact and the rule it must satisfy is the cheapest approximation of an
outside reader this repository can buy. The alternative is what produced the
three dead corpora: one continuous context, confident throughout.

### 2. Sub-agents perform adversarial review

Every artefact gets a reviewer whose task is to **break it**, not to approve it.
The reviewer is a different agent from the author, is given the artefact and the
standard, and is not told what the author concluded.

The brief is adversarial in the literal sense — find the reading under which
this is wrong. A reviewer that returns "looks good" has not run the task. The
useful output is a list of specific, checkable objections, each naming what
would have to be true for the finding to fail.

This is measured, not assumed: trust-framed system prompts surfaced **59% more
hidden issues** than unframed ones (arXiv:2603.14373), while fear-framing showed
no gain over saying nothing. So brief a reviewer to look hard and to report what
it finds, and never to threaten it into agreement.

### 3. No finding is believed until it is confirmed

**One agent's result is a hypothesis.** It enters the record as a finding only
after an independent confirmation that did not share the first agent's context.

Confirmation means at least one of:

- **Re-derived** — a second agent recomputes the number from the raw records,
  without being shown the first answer, and lands in the same place.
- **Reproduced** — the run is repeated and the effect survives.
- **Falsified-and-survived** — the adversarial reviewer's specific objection was
  checked and did not hold.

A number that fails confirmation does not get quietly dropped. It goes in
`notebook/` as a finding that did not replicate, because the record of what did
not survive is the part that makes the record worth anything.

*Why, and it is the whole history of this repository.* Twenty-one of twenty-one
scored failures were the answer key. A replication at 45/50 against 23/50 with
discordance 24-to-2 in the predicted direction was a scorer reading one turn in
one arm and six in the other. A parser whitelist voided 365 calls and printed a
plausible number. Two falsifiers were wrong the day they were written. **Every
one of those produced a clean, well-shaped, confident result**, and every one
was caught by somebody checking rather than by somebody being careful.

---

## Quota is not a reason to hold back

**Removed 2026-08-13 on maintainer instruction, and the removal is the point.**
This section used to say "stop for significant quota". It does not any more.

There is no API key here and no money. `total_cost_usd` is a notional
API-equivalent price and remains a useful burn meter, so keep reporting it — but
it is not a budget and it may not be a reason to shrink a grid, drop a model
tier, cut a stratum, or defer a run. A long serial grid is hours of wall clock;
run it. The runner is checkpointed and resumable precisely so that a run
spanning quota windows is a scheduling detail rather than a decision.

State a run's call count before starting it, because a reader deserves the
scale. Then start it.

---

## A person is not a step

**Maintainer instruction, 2026-08-18: remove every human gate from the plans.**
The same shape as the quota removal above, and for the same reason — a step that
waits on somebody is a step that does not happen. What it cost, measured rather
than asserted: N4's holdout sat on `STATUS.md`'s maintainer list from the day it
was written to the day it was rerouted, and **not one turn was ever supplied**;
the 10% realism audit was written down at 0% and was still at 0% one hundred and
forty-one items later; five label decisions marked *open* were open long enough
to be forgotten rather than decided.

So: **no plan in this repository may name a person as a prerequisite.** If you
find one, reroute it, and observe the two conditions that make a removal honest
rather than convenient:

- **Name what now does the job.** A gate deleted with nothing behind it is a
  step the plan silently loses, which is worse than a step it openly fails to
  take. Labels go to three-instance blind adjudication. Data-source decisions
  go to the outside-data rule below — executing it *is* the approval, and none
  of its four checks is dropped. A parameter with no derivation goes to standing
  rule 1: record the choice as a choice, in a dated `notebook/` entry.
- **Name what is lost.** Usually it is the last reader outside the model loop,
  and that is a real cost that no amount of procedure buys back. Say so in the
  same paragraph as the removal. What the replacements do buy is *checkability*:
  three blind judges leave a ledger, a pre-registered rule predates its data, a
  licence check leaves a digest. One person's answer left none of those, which
  is the argument — not that a person would judge worse.

**This does not touch the things a person is genuinely for.** Reporting that a
skill made an answer worse, deciding what this repository is for, and reading a
claim before it is published are not gates in a plan. Nor does it loosen
anything protective: the outside-data rule, the pre-registration requirement,
the answer-key versioning and the promotion gate all stand exactly as written.
A gate on evidence is not a gate on a person.

---

## Things that still need care, none of which is a reason to wait

1. **Authoring corpus items.** Three corpora were built and discarded, and the
   published sharded corpus exists so this is not needed for **Track A**. It
   *is* needed for the trigger corpus, which has no published equivalent —
   nobody else has a labelled set for "is this turn a decision". Author it,
   gate it with the shortcut battery, and adjudicate the labels blind.
2. **Scope.** An adversarial review argued the honest minimum is
   `0 → A5 → I → E4`. The maintainer's standing instruction is the whole
   programme, so run the whole programme; the minimum is a fallback ordering if
   something upstream kills a track, not a licence to cut one.
3. **Relaxing `--tools ""`.** It opens two channels that are currently inert:
   six declared subagents, and an auto-memory path keyed on the working
   directory that would become cross-run state a checkpointed record cannot see.
   Track F needs it relaxed. When it is, assert on the `system/init` receipt at
   every node and use a fresh cwd per node — both already implemented — and
   record the canary in the run's README.
4. **Any claim that a skill works.** Nothing here has been shown to work. The
   verdict vocabulary in [`SCORECARD.md`](../SCORECARD.md) governs what may be
   said; `UNTESTED` is the honest state of every skill in this repository. This
   constrains the sentence you write, never whether you run the experiment.
5. **Outside data must be free, redistributable and read before it lands.**
   There is no budget and nothing may be purchased — see
   [`CLAUDE.md`](../CLAUDE.md). So a corpus this repository did not author comes
   from a public source or it does not come at all, and four things are settled
   *before* it is fetched, in a dated `notebook/` entry:

   - **The licence, read first-hand**, and whether it permits redistribution.
     Free to download and free to check in are different permissions, and
     discovering the difference after vendoring is worse than not vendoring.
   - **Attribution and share-alike terms**, where the licence carries them.
     They travel to whatever is built from the data, including the paper.
   - **What is actually in it.** Public human-written text carries personal
     information, and worse. Read a sample, state what was checked and what was
     found, and record the filter applied. Nothing enters unread on the strength
     of its licence.
   - **A pinned digest** in `datasets/vendor/*.lock.json`, with the loader
     refusing anything that does not match — the pattern `lost_in_conversation`
     already follows.

   `de fetch` downloads; it does not vet. **The vetting is the work**, and it
   belongs to whoever proposes the source, before an agent is pointed at it.

---

## Working discipline

- **One unit per commit**, full `de check` green before each.
- **`notebook/` is append-only and dated.** Predictions go in *before* runs. A
  prediction that turned out wrong stays in the record saying so — it is not
  edited. Five consecutive predictions have been wrong in the same direction
  (toward the experiment working), and that record is evidence.
- **Commits attributed to the GitHub noreply address**; `de check` refuses
  otherwise.
- **Golden files pin the corpus byte-exact.** Regeneration needs `pytest
  --bless` and the diff belongs in review.
- **Report what happened, not what was attempted.** If a step was skipped, say
  which and why. If tests fail, quote the output.
- **Never `git stash` in this working tree, and never as a sub-agent.** The tree
  is shared by several concurrent sessions, so a stash is not scoped to the
  files you are working on — it takes everyone's uncommitted work with it and
  hands it back only if the pop succeeds. On 2026-08-19 a sub-agent stashed the
  whole tree to diff its four files against a clean checkout, while three other
  sessions had uncommitted edits to `docs/`, `skills/` and `results/` in it. It
  popped cleanly and nothing was lost, and it self-reported, which is the only
  reason this is a note rather than a recovery. **`git show HEAD:<path>` and
  `git diff -- <path>` answer the same question and touch nothing.** The risk is
  not that stash is broken — it is that its blast radius is the tree and the
  reason to reach for it is always a single file.

---

## Starting the work: which directory the worktree goes in

The worktree rule itself lives in [`AGENTS.md`](../AGENTS.md) — get your own
tree, rejoin `origin/main` daily or every ten commits, land by merging from a
green worktree. This section settles only *where the tree goes*, because that
was written down twice with two different answers.

**Inside the repository, under `.claude/worktrees/`.** Maintainer instruction,
2026-08-19.

```bash
git worktree add -b <slug> .claude/worktrees/<slug> origin/main
```

**Two reasons were previously given for a sibling directory instead, and
neither survives.** Recorded rather than silently overwritten, because one was a
measurement claim:

- *"A worktree under the agent-scratch directory is matched by
  `site/inputs.json` globs."* **False, and checked rather than argued.** With
  three real nested worktrees on disk, each holding a full `docs/`,
  `decision_evals.site.input_files()` returns 192 inputs and **zero** under the
  scratch directory. Every glob in `site/inputs.json` is anchored at a literal
  top-level segment (`docs/**/*.md`, `skills/**/*.md`, `*.md`), so none can
  reach a nested path. Nesting inside a nested worktree does not change it.
  Re-run it before trusting either version of this sentence.
- *"…and shows up in this repository's own `git status`."* **Already fixed
  before this rule existed** — `.gitignore` carries `.claude/`, and git never
  descends into an ignored directory.

**The gitlink hazard is real as a mechanism and was mis-told as history.** With
no ignore rule, `git add -A` records a nested worktree as a *gitlink* — mode
160000, the entry a submodule gets — after which it reports as modified in
every session forever. That was reproduced deliberately in a scratch repository.
What was *not* true is the incident once attached to it: the one gitlink this
repository has had lived in two `WIP:` auto-commits that never reached `main`,
and no `git rm --cached` appears anywhere in the history. If you ever see mode
160000 in `git ls-files -s`, the fix is `git rm --cached <path>` — never
deleting the worktree.

**What actually keeps the toolchain out of a nested tree**, since the mechanisms
are not the obvious ones:

- `pytest` is scoped by `testpaths = ["tests"]`, and `mypy` by `packages =
  ["decision_evals"]`. Both are anchored and safe.
- **`ruff` is *not* protected by any built-in exclusion.** Its default exclude
  list does not contain the agent-scratch directory; what keeps it out is
  `respect-gitignore` plus the `.gitignore` entry. `.gitignore` says so itself,
  and says why: unignored, a scratch worktree's Python went under `ruff check .`
  and broke the gate for every session at once.

**The ignore rule that makes this location workable also makes it
destructible.** Because the directory is ignored, every session's in-progress
worktree sits inside the blast radius of one careless delete at the repository
root. `git clean -xdf` is safe — it skips nested repositories — but `git clean
-xdff` removes the lot, and so does an `rm -rf` aimed at the scratch directory
from a shell whose working directory is not what its author believed. **On
2026-08-19 that happened**: two other sessions' worktrees were emptied by a
single `rm -rf`, and only their committed state came back. The sibling layout
made this impossible; this layout does not, and nothing warns you. Never run a
recursive delete or a forced clean at the repository root.

**A fresh worktree is not a fresh checkout of everything**, and the gate will
fail until you finish the setup. Gitignored and therefore *not* inherited:
`.venv/`, `site/node_modules/`, and `datasets/vendor/`.

```bash
cd .claude/worktrees/<slug>
python -m uv sync --group dev
python -m uv run de fetch          # datasets/vendor/, or the corpus tests fail
```

Give the worktree **its own `.venv`**, and not only to avoid two sessions
fighting over `.venv/Scripts/de.exe`: `de` gates whichever tree its own module
was installed from, so a worktree that picks up the outer `de` silently runs the
gate against the outer tree.

`de site` runs `npm ci` itself when `site/node_modules` is absent, which is
minutes rather than seconds. That setup cost is the only argument for skipping a
worktree, and it holds only for a change small enough to commit in one sitting,
touching files no other session has open, rewriting no shared state. If you are
weighing it, branch the worktree.

---

## Landing the work

**Maintainer instruction, 2026-08-19.** A unit is not finished when `de check`
goes green on a branch. It is finished when the change is on `main`, the site
that renders it is deployed, the deployed page has been fetched and checked, and
the branch and worktree are gone. The deploy itself is automatic now; confirming
it is not.

The merge rules are also in `AGENTS.md`, which carries the worktree and
`main`-parity requirements. What is only here is the *order*, and steps 9 to 11.

**Steps 10 and 11 are the ones nothing here can check.** Step 9 used to be one
of them and no longer is: deploying is a workflow rather than a thing somebody
remembers, and `de deployed` will tell you whether it landed. The rest are written
down because the order matters — and because `de check` at `pre-push` is *not* a
safety net you can count on. It fires only if somebody ran `pre-commit install
--hook-type pre-push` in this clone. Nothing in the repository does that for you,
and the hook it writes hardcodes the shared tree's `.venv`. Treat steps 4 to 7 as
load-bearing on their own.

1. **Catch up to `origin/main` before the review, not after.** In your worktree:
   `git fetch origin`, then `git rebase origin/main`. A review of work that has
   not seen the last commits on `main` reviews a tree that will never exist.

   **Never switch the shared tree's branch, and never `git stash` to make a
   rebase possible.** `D:/code/decision-making` is normally dirty with several
   sessions' uncommitted work, so `git checkout main` there takes their files
   with it and a stash takes the whole tree. If a rebase refuses because the tree
   is dirty with work that is not yours, you are in the wrong tree. To read
   another version of a file, `git show HEAD:<path>` and `git diff -- <path>`
   answer the question and touch nothing.

   **`main`, never `master`.** `origin/HEAD` points at `main`; this machine's
   `init.defaultBranch` is `master`, so a branch created without a name given
   will be called something that does not exist upstream.

2. **Give the work to a review sub-agent whose brief is to break it** — more
   than one when the change spans areas needing different eyes, such as harness
   code, the answer key and prose. A "looks good" review has not run.

3. **Fix what the review found, or record why it stands.** A finding you
   disagree with goes into the record with the disagreement attached. A finding
   dropped in silence is a review that did not happen.

4. **Regenerate whatever the change invalidated.** Each feeds a refusal inside
   `de check`, so skipping one here only moves the failure to step 7 with no
   explanation attached. All are conditional on what you touched:

   - `python -m uv run de mirror` — after editing `AGENTS.md` **or anything
     under `skills/`**. It regenerates `CLAUDE.md`, `.agents/skills/`, and
     `plugin/skills/` for promotable skills.
   - `python -m uv run de index` — after publishing a run, for
     `docs/RUN_INDEX.md`.
   - `python -m uv run de rescore` — after an answer-key version bump.
   - `python -m uv run pytest tests/golden --bless --no-cov` — after a
     deliberate golden-file change, with the diff in the review. Blessing makes
     the golden test *skip*, which can drop coverage under its floor, so run the
     full gate afterwards rather than trusting the bless.

   There is no database here and there are no migrations. These are not
   migration analogues to be caught up on at leisure; they are prerequisites of
   the gate.

5. **Rebuild the site if you touched anything it renders**, and do it *after*
   step 4, which is the only order that works: `de mirror` writes `CLAUDE.md`,
   and `CLAUDE.md` is itself a hashed site input, so rebuilding first records a
   hash that `de mirror` then invalidates.

   `python -m uv run de site`. The globs are in `site/inputs.json`; editing any
   document under `docs/`, `notebook/`, `results/`, `skills/` or the root is
   enough to need this.

   **A merge does not by itself stale the manifest** — that was checked rather
   than assumed. `site/build-manifest.json` is a per-file map of path to sha256,
   not a hash of the tree, so two rebuilt branches that touched different inputs
   merge textually and correctly, and two that touched *adjacent* entries
   conflict loudly rather than silently. Rebuild when you hand-resolved a
   conflict in it, or when either side edited a rendered file without rebuilding.

6. **Commit everything, including what step 4 and step 5 regenerated.**
   `CLAUDE.md`, `docs/RUN_INDEX.md`, the goldens and `site/build-manifest.json`
   are files, and a merge carries commits rather than working trees. This step
   exists because leaving them uncommitted is invisible: **`de check` has no
   dirty-tree refusal**, so step 7 goes green over a tree whose regenerated
   output has never been committed, `main` lands without the mirror, and every
   other session's gate turns red.

   Commit — do not merely stage. A gate that runs in the working tree cannot see
   what the commit is missing, which is how `main` once landed importing a module
   that existed only in somebody's index.

7. **Run the full `de check` against a clean tree.** Not `--fast`. `git status
   --short` must be empty first; if it is not, step 6 is unfinished.

8. **Merge to `main`, push, and prove the work actually landed.** Three things
   have to end up true: `origin/main` contains your commits, local `main` names
   the same commit as `origin/main`, and no other session's tree was touched
   getting there.

   **`git push origin <topic>:main` is not a shortcut for this.** It moves
   `origin/main`, leaves the local ref where it was, and warns nobody. Never
   `git update-ref refs/heads/main` either — it bypasses git's checked-out
   protection rather than satisfying it, and leaves the worktree holding `main`
   with a HEAD its index does not match.

   Read `git worktree list`, then take the case you are in:

   - **No worktree holds `main`** — the normal state, and the portable path.
     Update the local ref without checking anything out, then push it:

     ```bash
     git fetch . <topic>:main && git push origin main
     ```

   - **You hold `main` in one of your own worktrees.** Merge and push from
     there: `git -C <that-worktree> merge <topic> && git -C <that-worktree> push
     origin main`.

   - **Another session holds `main`.** On 2026-08-19 that was a temp scratchpad
     worktree belonging to a live session. **Do not merge, check out, or push
     from inside it** — that is step 1's hazard through a different door. Push
     the remote from your own tree, then say in your report that local `main` is
     behind and only the session holding it can fast-forward
     (`git merge --ff-only origin/main`). Do not do it for them.

   Then verify, rather than assume — and check that *your work* is there, not
   merely that two refs agree, since a no-op merge satisfies the parity check on
   its own:

   ```bash
   git fetch origin
   git rev-parse main origin/main                              # two identical lines
   git merge-base --is-ancestor <your-topic-sha> origin/main   # exit 0 = landed
   ```

   If the `pre-push` hook refuses here, the cause is usually **not** a skipped
   step: `main` moves under you while you work. Step 7 gated your rebased topic
   tree; this gates the post-merge tree, which now holds other sessions'
   commits. Go back to step 1 with a fresh fetch and run 4 to 7 again. Do not
   reach for `--no-verify`.

9. **Deploying is not yours to do. Confirming it happened is.** The push in
   step 8 triggers `.github/workflows/deploy-site.yml`, which builds the site
   and deploys it to Pages. There is nothing to run, no `--group docs` to
   remember, no worktree to go and stand on, and no `gh-pages` branch. Wait for
   the run, then ask the live site what it is serving:

   ```bash
   gh run list --workflow "Deploy site" --limit 1
   python -m uv run de deployed
   ```

   Not a bare `gh run watch`. With no run id and no TTY it exits with *run ID
   required when not running interactively*, and this document is written for
   agents, which are exactly the non-TTY case. To block until it finishes:

   ```bash
   gh run watch "$(gh run list --workflow 'Deploy site' --limit 1 --json databaseId -q '.[0].databaseId')"
   ```

   `de deployed` fetches `deploy-provenance.json` from the published site — the
   record the deploying workflow writes into the tree it uploads — and compares
   the commit in it against `origin/main`. Exit 0 is current, 1 is behind, and
   **2 is "could not tell", which is deliberately not 0.**

   Two things it does not prove, so do not stop here. A deployment can be green
   while a route is missing, which is why step 10 still fetches pages by hand.
   And Pages sits behind a CDN, so a *behind* result within a few minutes of a
   merge may be cache lag rather than a failed deploy — re-run it before
   concluding anything.

   **The same push starts a second run, and it is the one that can fail.**
   `.github/workflows/check.yml` runs the full `de check` on a clean checkout of
   what you just merged. Nothing in this document waits on it unless you do, and
   step 7's green is not a prediction of its result: the first such run went red
   on a tree whose local gate had passed (`76cdfb0`), in four places a working
   directory cannot show — a CLI the runner had no reason to have, and an
   assertion reading an error message Rich had wrapped to eighty columns. Wait
   for it, and treat red as your problem even when the cause is environmental:

   ```bash
   gh run watch "$(gh run list --workflow 'check' --branch main --limit 1 --json databaseId -q '.[0].databaseId')"
   ```

   A red `check` on `main` does not roll the deploy back — the two workflows do
   not gate each other — so the live site can be serving a build of a commit that
   `check` rejects. That is not a bug to fix by chaining them; it is the reason
   to look.

   **What replaced what, so the old instruction is not resurrected from
   memory.** This used to be `de site --deploy`, which force-pushed whatever
   local `HEAD` happened to be. On 2026-08-19 it published a build of a
   work-in-progress commit from a feature branch, and separately left the
   published branch 43 minutes behind `main` with nothing to say so. The flag,
   the `ghp-import` dependency and the `docs` group are all gone.

10. **Then fetch the deployed page and assert against it.** Not the local
    `dist/`, not the manifest.

    The base is `https://angelcampa1.github.io/decision-making-skills/`. The
    path is the section plus the *filename lowercased with `.md` stripped* —
    punctuation kept verbatim, because `site/src/content.config.ts` deliberately
    does not slugify. The section is not always the directory name:

    | Source | URL |
    |---|---|
    | `docs/AUTONOMOUS_WORK_ORDER.md` | `/docs/autonomous_work_order/` — **not** `-work-order`, which 404s |
    | `notebook/<file>.md` | `/notebook/<file>/` |
    | `skills/decision-making/SKILL.md` | `/skill/decision-making/skill/` — the section is **`skill`, singular** |
    | `results/<skill>/<run-id>/README.md` | `/results/<skill>/<run-id>/` — a run record is its own page, not an index |
    | `docs/README.md` | `/docs/` — this one *is* the section index |
    | `AGENTS.md` and other root documents | `/agents/` — no section segment |

    `CLAUDE.md` is published nowhere at all; it is the generated mirror, so
    verify `AGENTS.md` at `/agents/` instead.

    Fetch three things, because one page proves less than it looks:

    - the page you changed, and confirm your words are in the HTML;
    - one `_astro/*` asset that page references, and confirm it is not a 404 —
      the page's own HTML returns fine whether or not its bundles resolve, so
      fetching the page alone cannot detect that failure;
    - the section index, and confirm the document is listed — a document can
      build perfectly while being linked from nowhere.

11. **Delete the worktree first, then the branch.** That order is not a
    preference: `git branch -d` **refuses** while any worktree still holds the
    branch, and the refusal names the worktree. And you cannot remove the
    worktree you are standing in — on Windows it fails partway with `Permission
    denied` and leaves the registry in a state where the retry reports `is not a
    working tree`. So leave first:

    ```bash
    cd <the main checkout>
    git worktree remove .claude/worktrees/<slug>
    git branch -d <topic>
    git worktree prune
    ```

    **Read `git worktree list` before any of it.** Several sessions run here at
    once, worktrees are sometimes `locked`, and a merged branch name is no
    evidence that the session working in it has stopped. A locked worktree, or
    one dirty with work you did not write, is not yours to remove: leave it, say
    that you left it and why, and move on. The parallel-sessions rule outranks
    the tidying.

    `git branch -d` has a *second* refusal — unmerged commits — and that one is a
    real check. Never answer it with `git branch -D`; answer it by finding out
    what has not landed. The order refusal above is not a check, and `-D` would
    not fix it anyway.

**One thing here rots silently.** The link to this section from `AGENTS.md`
carries a `#landing-the-work` fragment, and nothing validates it: the
documentation gate splits the fragment off and checks only the path
(`evals/src/decision_evals/docs.py`), and the site's link rewriter passes
`#anchor` through verbatim. Renaming this heading breaks that link while every
gate stays green.

## As you go

Leave behind, in `notebook/` and dated, without breaking stride:

1. What was completed, and the commit for each.
2. Every parameter you chose rather than derived, and what would measure it.
3. Anything measured that contradicts a document in this repository — including
   this one. Two falsifiers and three citations were wrong on the day this was
   written, and each was found by someone checking rather than assuming.

Then pick up the next item in the programme. The work is finished when the
programme is finished.
