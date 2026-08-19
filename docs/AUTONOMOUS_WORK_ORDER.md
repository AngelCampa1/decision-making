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

## As you go

Leave behind, in `notebook/` and dated, without breaking stride:

1. What was completed, and the commit for each.
2. Every parameter you chose rather than derived, and what would measure it.
3. Anything measured that contradicts a document in this repository — including
   this one. Two falsifiers and three citations were wrong on the day this was
   written, and each was found by someone checking rather than assuming.

Then pick up the next item in the programme. The work is finished when the
programme is finished.
