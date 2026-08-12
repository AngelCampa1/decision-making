# L5: the boilerplate does the work and the good sentence does the least

**2026-08-12.** Outcome for
[the prediction](2026-08-12-l5-prediction-what-each-part-of-a-description-buys.md),
committed at `fe24180` before the run started. Track L5. **1,095 isolated calls**
(3 arms × 73 cases × 5 repeats), Haiku, **0 unparseable, 0 isolation failures**.
The `full` control is the existing five-repeat baseline and was not re-run.

## Scored as registered

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | Parseable verdicts | ≥ 98% | **100%** (1095/1095) | ✅ |
| 2 | **`no-exclusions` FPR rises** | > 0.04 | **0.055** | ✅ |
| 3 | `no-exclusions` recall holds | ≥ 0.85 | **0.911** | ✅ |
| 4 | `opener-only` FPR | > 0.06 | **0.113** | ✅ |
| 5 | `opener-only` recall | 0.85–1.00 | **0.956** | ✅ |
| 6 | `no-opener` recall falls | < 0.80 | **0.867** | ❌ |
| 7 | FPR ordering | `opener-only` ≥ `no-exclusions` > `full` | 0.113 > 0.055 > 0.018 | ✅ |

**Six of seven.** The miss is band 6: deleting the opener barely touched recall
(0.867 against the control's 0.878), which is the first thing this result turns
on.

## The four arms

| arm | parts present | FPR | recall | precision | routing |
|---|---|---|---|---|---|
| `opener-only` | opener | **0.113** ± 0.008 | **0.956** ± 0.025 | 0.735 | 0.429 |
| `no-exclusions` | opener + summary | 0.055 ± 0.013 | 0.911 ± 0.030 | 0.846 | 0.743 |
| `full` *(shipped)* | opener + summary + exclusions | 0.018 ± 0.013 | 0.878 ± 0.025 | 0.942 | 0.686 |
| `no-opener` | summary + exclusions | **0.000** ± 0.000 | 0.867 ± 0.050 | **1.000** | 0.671 |

## The design turned out better identified than I built it

The three parts — opener **O**, routing summary **R**, exclusions **E** — appear
across the arms so that each adjacent pair differs in exactly one:

| contrast | isolates | FPR |
|---|---|---|
| `full` (ORE) vs `no-opener` (·RE) | **the opener** | 0.018 vs 0.000 |
| `full` (ORE) vs `no-exclusions` (OR·) | **the exclusions** | 0.018 vs 0.055 |
| `no-exclusions` (OR·) vs `opener-only` (O··) | **the routing summary** | 0.055 vs 0.113 |

So each part's contribution to false-firing can be read off directly:

| part | what it buys | what it reads like |
|---|---|---|
| **routing summary** | **−5.8pp FPR** | the middle sentence nobody thinks about |
| **exclusions** | **−3.7pp FPR** | boilerplate |
| **opener** | **+1.8pp FPR** — it *costs* | the sentence the whole description is built around |

**The part that reads as the most important is the only one that makes the skill
worse.** *"Use when someone is trying to decide something and wants help deciding
it — 'help me think this through', 'should I take it', 'what would you do'…"* —
the sentence with all the illustrative quotes — is the one whose deletion
improves precision to 1.000 at a cost of one point of recall.

## It is content, not length, and the design proves it for free

| arm | length | FPR |
|---|---|---|
| `opener-only` | 206 ch | 0.113 |
| **`no-opener`** | **342 ch** | **0.000** |
| `no-exclusions` | 385 ch | 0.055 |
| `full` | 549 ch | 0.018 |

**FPR is not monotone in length.** 342 characters gives zero false fires and 385
gives 0.055. My *"where I expect to be wrong"* note worried that a shorter
description might simply be a smaller claim on attention — that the effect would
be L2's length question wearing L5's clothes. The two mid-length arms rule it
out, and they do so because the design deletes *named parts* rather than
truncating.

## What is significant, and what is only directional

Paired Wilcoxon over per-item fire rates, 5 repeats each:

| contrast | on the 55 negatives | on the 18 positives |
|---|---|---|
| `opener-only` vs `full` | 7 items differ, **7 up, 0 down, p = 0.016** | 3 differ, all up, p = 0.11 |
| `no-exclusions` vs `full` | 4 differ, **4 up, 0 down**, p = 0.068 | 3 differ, all up, p = 0.10 |
| `no-opener` vs `full` | 2 differ, **0 up, 2 down**, p = 0.18 | 4 differ, p = 0.72 |

**Only `opener-only` vs `full` clears 0.05**, and every contrast is perfectly
one-directional on the negatives — no arm has a single item moving against the
trend. That unanimity across three independent contrasts is the evidence; the
individual p-values are what 55 items with a 0.018 base rate can buy.

**Combined accuracy is not significant anywhere**, and it should not be quoted:
FPR and recall move in opposite directions and cancel, exactly as they did in
[M4](2026-08-12-m4-shadowing-did-not-appear-at-four.md). A description change
here does not make the skill *better* — it **moves it along a precision/recall
frontier**, and which point is wanted is a decision nobody here has made.

## Routing, descriptive only, and one sanity check worth having

Pre-registered with no p-value, per
[the power check](2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).

`opener-only` routes at **0.429** against 0.686 for the control — the arm whose
description does not list the four procedures cannot pick among them. That is the
instrument confirming it measures something: strip the content routing depends
on and routing collapses, while firing gets *better*. The two outcomes are not
the same measurement wearing two names.

## What I am not doing

**Not deleting the opener from the shipped skill.** It has run once, on one
instrument, at one model tier, and the trade is 1.8pp of FPR against 1.1pp of
recall — which is not obviously a win, and is not a decision an agent should take
on the maintainer's skill. It goes to Track L as the strongest authored-variant
candidate this repository has.

**And the exclusion list stays, with its evidence.** Band 2 was the run's
purpose: deleting *"Do not use for factual lookups, for creative or exploratory
work…"* triples the false-positive rate, 0.018 → 0.055. **The clause is not
decoration.** That question has been asked in this repository three times without
an answer and now has one.

## For the maintainer

1. **The precision/recall point is a product decision, not a measurement.** All
   four arms are defensible skills. `no-opener` never interrupts and misses one
   more decision in a hundred; `opener-only` catches nearly everything and
   interrupts one ordinary turn in nine. **Nothing in this repository says which
   is wanted**, and every skill-quality claim depends on it.
2. **Whether to run L2 (length) at all.** It was pre-registered as a null
   confirmation, and this run has already shown FPR is not monotone in length on
   four points. That is not L2, but it is evidence about what L2 will find.
