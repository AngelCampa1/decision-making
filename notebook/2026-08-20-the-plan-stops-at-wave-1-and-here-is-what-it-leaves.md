# 2026-08-20 — The plan stops partway through wave 1, and this is what it leaves

A four-wave plan was approved on 2026-08-20 and stopped by the maintainer partway
through the second wave. Nothing here is abandoned and nothing here is claimed.
This entry is the record of where the cut fell, so the next session picks the
work up from a written state rather than from a reading of the diff.

The plan is `what-part-of-these-nifty-kahan.md` in the maintainer's plan
directory, which is outside this repository and is not a durable store. Its
substance is reproduced below, which is the point of writing this down.

## What landed

Wave 0 in full, seven items, one commit each, every one of them free of model
calls:

| Item | What it was | Where it is |
| --- | --- | --- |
| 0.1 | The pooled item analysis had no entry point outside a test. The wired caller passed one arm, so the registered twelve-respondent estimator only ever saw two. | `scripts/run_triggers.py` |
| 0.2 | `s13p`'s annotation cited seven verdict files under a directory nothing has ever written to. | `datasets/triggers/decision-making/s.yaml` |
| 0.3 | Nothing computed MCC or a confusion matrix, and every accuracy on record sat on an unprinted 2/3 baseline. | `evals/src/decision_evals/trigger_arms.py` |
| 0.4 | Fleiss κ was reported without saying how many judges it is worth. Three samples of one model are 1.07 effective raters. | `scripts/adjudicate.py` |
| 0.5 | `corrections.jsonl`, a machine-readable label-correction changelog, and the `de check` step that refuses a `set_version` bump whose label moves are not in it. | `evals/src/decision_evals/corrections.py` |
| 0.6 | No backoff, no jitter, no breaker anywhere in the tree, on a runner that had just become concurrent. | `evals/src/decision_evals/runner.py` |
| 0.7 | The "venue map" in the programme is the internal 2×2 experiment taxonomy, not a submission map, and no document said so. | `docs/RESEARCH_PROGRAMME.md` |

And one item of wave 1: **answer key v5**, twenty-four triples authored so that
`council` and `hinge` have positives to be correct about. Registered in
`docs/DECISIONS.md` under "council and hinge get positives, and the key moves to
version 5". Two things about it are unfinished and are listed below rather than
here.

Two incidents are also on this branch and belong to neither wave. The git
hygiene tests reconfigured the repository they promised not to touch, setting
`core.bare = true` on the real checkout; the fixture now scrubs every
repo-scoped `GIT_*` variable, and a second session had found the same defect
independently. And rebasing twice invalidated the shas that `docs/DECISIONS.md`
points at, which is why this branch landed by merge.

## What is pending

Ordered as the plan ordered it. Each line says what state it is actually in,
which for three of these is "partly built" rather than "not started".

**1.1 The concurrency falsifier on the Claude CLI backend. Infrastructure and
prediction landed; the run is incomplete and nothing is published.**
`CONCURRENCY_UNSAFE` names only `ollama/`, so `concurrency > 1` is permitted
today on the backend every published number came from, with no measurement
behind it. `scripts/concurrency_equivalence.py` takes `--backend cli` and the
prediction is committed at
[`2026-08-20-prediction-concurrency-on-the-cli-backend.md`](2026-08-20-prediction-concurrency-on-the-cli-backend.md).
The run itself reached S1 280/280, C 280/280, S2 187/280 before the stop. Its
checkpoints are under the gitignored `results/track-0/`, it is resumable, and
until it finishes and is scored, **no arm may set `concurrency > 1` on a CLI
model.** The prediction records the scoping fact that softens this: no caller
passes it today either, so the door is unlocked rather than open.

**1.2 The v5 items are unadjudicated.** The corpus rule is blind three-judge
adjudication with a pre-registered kill at more than 20% of labels moving. It
has not run on these seventy-two items. The `docs/DECISIONS.md` entry says so
and the constraint it states holds: **no number may be published against version
5 until it has.** This is the single most consequential pending item, because
every downstream run in the plan is scored against this key.

**1.3 The six description arms have not been re-run on v5.** They cannot be, per
1.2. When they are, they are the new baseline everything downstream is scored
against, and `label_versions_comparable` refuses every v4-to-v5 comparison in
the meantime, which is what the version bump was for.

**2.1 OASST1 has not been fetched.** Track N4's licence survey is complete and
recommends it; nothing is on disk, which is what keeps the human-authored
holdout from existing, which is what keeps N5 retired and the noise floor
unquotable.

**2.2 The corpus is not published to the Hub**, and the dataset-card-versus-
datasheet gate that would keep the two from drifting does not exist. This is
Track J starting.

**2.3 No OTLP exporter.** `telemetry.py` computes the span attributes; nothing
writes them anywhere. The wiring gate will refuse a floored module nothing
reaches, so this needs a caller or a register entry when it lands.

**3.1 to 3.3, the confirm pathway, entirely unbuilt.** `de screen`, `de confirm`
and `de report` do not exist and are registered in
`[tool.decision-evals.docs-absent-commands]` as deliberately absent.
`decision_evals.prereg` is the only remaining entry in
`[tool.decision-evals.unwired]`. This is the largest unbuilt piece and the
binding one: **until it exists no skill can leave `UNTESTED` and `SCORECARD.md`
cannot have a row.**

**4.1 to 4.4, the results, unstarted.** Cross-tier validity per tier rather than
as an arm comparison; GEPA in Track L6 scored on firing over the full corpus
rather than on 14-item routing; the ABA-style item audit, which is a different
thing from label adjudication and is not `generators/audit.py`; the noise floor,
publishable once 2.1 exists.

## Drift this leaves behind, named so it is not found by surprise

Answer key v5 moved the corpus from 258 items in 86 triples to 330 in 110. The
present-tense descriptions in `docs/METHODS.md`, `docs/RESEARCH_PROGRAMME.md`
and `docs/STATUS.md` are updated in the same change as this entry. What is **not**
updated is the registered call-count arithmetic inside Track N, which derives
run sizes from "258 items" at v4 in three places. Those are plans for runs that
have not happened, they were correct when registered, and rewriting a registered
number to match a corpus that moved under it is the failure mode this repository
exists to police. They must be recomputed at 330 as part of registering each run,
not swept.

`SCORECARD.md` and the dated sections of `docs/STATUS.md` also say 258 items.
Those are scoped to runs that happened on v4 and are correct as written.

---

## Postscript, same day: 1.1 finished on its own

The concurrency run was mid-flight when this entry was written and it completed
after the entry was committed, so the line above saying it reached S2 187/280 is
the state at the time of writing and not the state now. It reached 280/280 in
all three arms, the registered primary landed inside its band, and
`CONCURRENCY_UNSAFE` does not move. The outcome is in
[`concurrency on the CLI backend changes nothing`](2026-08-20-concurrency-on-the-cli-backend-changes-nothing.md).

**1.1 is closed. Everything else on the pending list above still stands**, and
1.2 -- the unadjudicated version 5 items -- is still the binding one.
