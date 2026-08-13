# Track L7 — an eager opener that keeps the boilerplate

**2026-08-13.** 73 cases × 2 repeats × 2 arms = **292 isolated `claude -p`
calls**, Haiku, 0 unparseable, 0 isolation failures. Code at `abb6862`.

The maintainer chose **eager** and named what the skill should key on: stakes,
real consequences, complexity, nuance. The only eager arm on record was
`opener-only`, which reaches recall 0.956 by *deleting* the routing summary and
the exclusion list — the two clauses L5 measured at −5.8pp and −3.7pp of false
firing. That is eagerness by subtraction and it costs 12.9% of ordinary turns.

L7 asks whether eagerness is reachable by **widening the opener while keeping
both clauses verbatim**. Two arms, because the design question — *name* the
criteria or *show* them by example — is empirical, and asking a person a
question the instrument answers for 146 calls is the wrong way round.

| arm | opener |
|---|---|
| `stakes-named` | *"…and the choice has stakes — it is costly to undo, several things pull against each other, or it lands on someone else."* |
| `stakes-shown` | *"…'should I take the offer', 'do I raise this now or wait', 'is it worth the risk', 'what does this commit us to'…"* |

Same middle, same exclusions, matched length (within 10%, observed 6%).

## Results

| arm | FPR | recall | precision | accuracy | never fired |
|---|---|---|---|---|---|
| `opener-only` | 0.1286 | **0.9529** | 0.735 | — | — |
| `no-exclusions` | 0.0571 | **0.9529** | 0.845 | — | — |
| `full` (shipped) | 0.0179 | 0.9294 | 0.941 | — | `x-n22` |
| **`stakes-shown`** | **0.0000** | 0.9118 | **1.0000** | **0.9795** | `x-n22` |
| `stakes-named` | 0.0179 | 0.8824 | 0.9375 | 0.9589 | `x-n03`, `x-n22` |
| `no-opener` | 0.0036 | 0.9059 | — | — | `x-n20` |

**Showing beat naming.** `stakes-shown` did not fire once across 110 negative
observations and **dominates `no-opener` on both axes** — the first Pareto
improvement of one arm over another here. It does not dominate `full`: 1.8
points of FPR bought for 1.8 points of recall is a trade.

The two openers are **not distinguishable**: paired Wilcoxon p = 0.257, 4 of 73
items differing, 3 favouring `shown`.

## The bands, as registered

| # | Band | Result | |
|---|---|---|---|
| 1 | parseable ≥ 98% | 146/146 both arms | ✅ |
| 2 | both arms beat `opener-only` on FPR | 0.018, 0.000 | ✅ |
| 3 | one arm reaches recall ≥ 0.94 | best 0.912 | ❌ |
| 4 | **one arm at FPR ≤ 0.06 *and* recall ≥ 0.94** | neither | ❌ |
| 5 | the arms differ on FPR (descriptive) | 0.018 vs 0.000 | ✅ |
| 6 | neither fires on the lowest-stakes negatives | 0/2 both arms | ✅ |

**Band 4 was the experiment and it failed.** The precision/recall frontier is
intact after seven arms — a description moves where on the line the skill sits,
not the line.

**Band 3 was unsettable and was set anyway.** `x-n22` fires in no arm on any
version, a fact stated in the prediction's own *"where I expect to be wrong"*
section, so the ceiling was 16/17 = 0.941. A recall band must be set against the
observed per-item ceiling, not a round number.

**Band 6 passed and was the one expected to fail.** Both stakes openers score
0/2 on tabs-vs-spaces, variable naming, list-vs-set and the plot twist, while
`opener-only` fires **5/5 on all four**. The stakes criterion reads content, not
sentence shape.

## The item that separates the two openers

`x-n03` *"Should I learn Rust?"* — `stakes-shown` 2/2, `stakes-named` **0/2**.
Naming stakes as a criterion makes the model apply it strictly, and a real
decision about a person's own time does not look expensive. `stakes-named`
refuses exactly the two positives (`x-n03`, `x-n22`) that were kept on a
maintainer's judgement. It is the most coherent behaviour in the run and it
disagrees with the answer key.

## Limits

- **The corpus is solvable at 0.890 by counting words** (`length_separability`
  AUC 0.850). `stakes-shown` at 0.9795 is nine points above a ruler. Whether
  showing beats naming on turns a real person would send is not established here
  and cannot be on this corpus — see **Track N** in
  [`docs/RESEARCH_PROGRAMME.md`](../../../docs/RESEARCH_PROGRAMME.md).
- **These openers are authored**, not derived. Every earlier arm in Tracks L and
  M was produced by deletion or mechanical partition precisely so no result
  could be "the prose I happened to write". No deletion of the shipped
  description produces a stakes criterion, so L7 gives that up and substitutes
  constraint: same middle, same exclusions, matched length, both written before
  either ran.
- **One model tier, one instrument.** Haiku, and a proxy — the model is shown
  the description and asked whether it would fire, which is not the same as a
  description sitting among other skills in a real session.
- **Reference arms re-scored, not re-run.** `full`, `opener-only`,
  `no-opener` and `no-exclusions` are v1 checkpoints re-scored against v2
  labels. `summarise()` reads `should_fire` from the record, so the naive call
  reports v1 silently; the figures above are re-scored explicitly at the call
  site.

**Answer key:** [`datasets/triggers/decision-making.yaml`](../../../datasets/triggers/decision-making.yaml) **v2**. Not comparable with a v1 run: on 2026-08-13 one turn moved from the positives to the negatives and recall rose on every arm on disk with no call re-made.

Prediction: [`notebook/2026-08-13-l7-prediction-eager-without-deleting-what-works.md`](../../../notebook/2026-08-13-l7-prediction-eager-without-deleting-what-works.md), committed at `1cfd90b` before either arm ran.

Outcome: [`notebook/2026-08-13-l7-showing-beat-naming-and-nothing-left-the-frontier.md`](../../../notebook/2026-08-13-l7-showing-beat-naming-and-nothing-left-the-frontier.md).
