# Track N9 — the in-situ arm, void on parse rate

**2026-08-19.** 258 items × 2 repeats = **516 `claude -p` calls**, `haiku`,
`--append-system-prompt`, **70 unparseable**. Code at `505b236`.

**Answer key:** `datasets/triggers/decision-making/index.yaml` v4

Prediction: [`notebook/2026-08-19-prediction-n9-does-position-move-firing.md`](../../../notebook/2026-08-19-prediction-n9-does-position-move-firing.md),
committed before the launch.

**This run is void and none of its three predictions are scored.** No accuracy,
precision, recall or FPR is computed from these records, and none appears
anywhere in this repository. The void condition was registered in advance and
checked before any interpretation.

## The parse rate is three different numbers

| | over | value |
|---|---|---|
| what the gate computes (`run_triggers.py:918`) | **repeat 0 only**, 258 items | **0.8566** |
| repeat 1 alone | 258 items | 0.8721 |
| aggregate over every call | 516 calls | 0.8643 |

`row = done.get((case.id, 0))` reads repeat 0 and nothing else, so **the gate is
blind to repeat 1.** Every reading here is below the 0.90 floor and below the
0.95 the prediction registered, so the disposition is correct — but a run whose
repeat 0 cleared 0.90 while repeat 1 dragged the aggregate under it would exit
zero and be published. That is a standing instrument gap, recorded and not
fixed.

## What the 70 unparseable responses are

**Not one contains a `"fire"` key**, the substring "fire" in any casing, or any
parseable embedded JSON of any shape. They are prose — the model answering as
Claude Code instead of emitting the contract.

**The finer classification is not reliable and no count from it should be
quoted.** The regex labels were written after reading the data with one
category as a residual bucket. An independent reviewer hand-read all 70 and
blind-classified a random 30:

| | regex, all 70 | independent hand read, n=30 |
|---|---|---|
| answers the question in prose | 54.3% | 40.0% |
| scope refusal, on host identity | 27.1% | 26.7% |
| declines the tool, answers anyway | 14.3% | 20.0% |
| clarifying question | 4.3% | 13.3% |

Only the scope-refusal row agrees. Two claims survive an independent read and
are the only two this record stands behind: **no `fire` key anywhere**, and
**the identity-refusal language is absent from `technical` and `career`**.

## Two clusters, not a gradient

| domain | calls | parse rate |
|---|---|---|
| technical | 102 | 0.951 |
| money | 108 | 0.907 |
| career | 102 | 0.882 |
| relationships | 108 | 0.806 |
| health | 96 | 0.771 |

**No adjacent pair in that ordering is distinguishable** — Fisher exact p =
0.287, 0.654, 0.135, 0.607. The split that is:

| | parse rate | |
|---|---|---|
| `technical`, `money`, `career` | 0.9135 (285/312) | |
| `relationships`, `health` | 0.7892 (161/204) | Fisher **p = 0.00011** |

χ² across all five domains: 18.86, df 4, **p = 0.00084**, driven entirely by
that break. A step function with one edge, not a slope.

Turn length does not explain it (median 376 vs 405.5 chars, Mann-Whitney
p = 0.155), band does not (`m` worst at 0.819, `l` best at 0.921), and stakes
does not (`health` is majority low-stakes and worst). A simpler variable was
looked for and not found.

`--system-prompt` replaces the host identity; `--append-system-prompt` leaves it
in place. The description is byte-identical across the two arms.

## Why nothing is rescued from this

Recovering decisions by re-reading prose would be post-hoc scoring of a voided
run against a rule invented after seeing it. The tables above are description,
and the classification one is description with a stated disagreement rate.

## The instrument is not what failed

446 of 516 calls parsed and scored normally, so a response existed that would
have scored above zero for this arm. Item-level coverage 0.957: 11 of 258 items
lost every repeat. **No isolation claim is made** — there is no isolation field
in the checkpoint and no run log was kept beside it.

## Comparability

These records are stamped `"in_situ": true`.
`trigger_arms.venue_comparable()` refuses to compare them against any arm sent
through `--system-prompt`, which is every other arm on disk.

## Files

- `verdicts-in-situ.jsonl` — all 516 records, including the 70 with `fired: null`
  and their full `raw` text.
