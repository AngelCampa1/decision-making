# M4: shadowing did not appear at four, and the table was the problem all along

**2026-08-12.** Outcome for
[the prediction](2026-08-12-m4-prediction-one-entry-against-four.md), registered
and committed at `615f7cb` before the run started. Track M4. 365 isolated calls,
73 cases × 5 repeats, Haiku, **0 unparseable, 0 isolation failures**. Arm `one`'s
five-repeat baseline already existed and was not re-run.

## Scored as registered

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | Parseable verdicts | ≥ 98% | **100%** (365/365) | ✅ |
| 2 | Arm `four` precision | 0.80–0.95 | **1.000** | ❌ *(above)* |
| 3 | Arm `four` recall | 0.80–0.95 | **0.800** | ✅ |
| 4 | **FPR rises above 0.018** | > 0.018 | **0.000** | ❌ |
| 5 | Arm `four` routing | 0.55–0.80 | **0.786** | ✅ |
| 6 | `x-n21`, `x-n22` still miss | ≤ 1/5 each | **1/5, 0/5** | ✅ |

**Band 4 was the one the repository's own design choice rests on, and it failed
in the informative direction.** Not "FPR rose less than expected" — it went to
**zero, in all five repeats, sd 0.000.**

## The two arms, side by side

| | arm `one` | arm `four` |
|---|---|---|
| precision | 0.942 ± 0.039 | **1.000 ± 0.000** |
| recall | **0.878 ± 0.025** | 0.800 ± 0.063 |
| false-positive rate | 0.018 ± 0.013 | **0.000 ± 0.000** |
| routing accuracy | 0.686 ± 0.108 | **0.786 ± 0.051** |

## The headline: they are the same, and that is the result

Per-item correctness (`fired == should_fire`), 73 paired items, 5 repeats each:

| set | arm `one` | arm `four` | items differing | paired Wilcoxon |
|---|---|---|---|---|
| **all 73** | 0.956 | 0.951 | 8 — **4 each way** | **p = 0.83** |
| 55 negatives | 0.982 | 1.000 | 2, both favour `four` | p = 0.18 |
| 18 positives | 0.878 | 0.800 | 6, 4 favour `one` | p = 0.21 |

**Shadowing did not appear at four descriptions on this instrument.** The two
sub-splits point opposite ways and cancel, and the aggregate is a dead heat.

`CLAUDE.md` currently justifies shipping one entry like this:

> The decision procedures live behind **one** entry rather than four because four
> descriptions that all read as "help me decide" look like the same failure.

**That mechanism was not observed.** The four descriptions here share an opener
and an exclusion list *by construction* — they are maximally overlapping — and
the model still selected among them without firing once on a negative.

**What it does not show: anything about n=202.** This was pre-registered and it
stands. Four is four. The published shadowing result is not contradicted; the
extrapolation from it down to four is not supported either.

## The finding I did predict, in writing, before the run

The prediction file's note on band 5:

> **5 is where I would most like to be surprised.** […] today's two table defects
> (`cascade`/`timing` colliding on order/when, and "advice" appearing only in
> `fit`'s row) are both defects **of the table**, which arm `four` does not have.

Those two defects are `p07` and `p03`, named this morning from reading traces
rather than from any aggregate. Both moved, and so did `p06`:

| item | diagnosed this morning as | arm `one` | arm `four` |
|---|---|---|---|
| **`p07`** | `cascade`/`timing` collide on *order* vs *when* | 1/5 | **5/5** |
| **`p03`** | "advice" appears only in `fit`'s row | 1/5 | **3/5** |
| `p06` | partly a trigger-set defect, two routes defensible | 0/5 | **3/5** |

Across all 14 labelled items, `four` routes better on 5 and worse on 2, and its
standard deviation is **half** arm `one`'s.

**So the router table, not the bundling, is what was costing routing accuracy.**
Every procedure describing its own condition in its own entry beats four rows the
model reads past each other in one table. That is a mechanism confirmed on the
two items it was stated about, before the run, which is worth more than the
aggregate it sits inside.

**Held to the pre-registration: no p-value on routing.** It was registered
descriptive-only because 14 items cannot reject at any useful effect size
([the power check](2026-08-12-routing-cannot-be-scored-on-fourteen-items.md)).
The item-level prediction is stronger evidence than the rate precisely because it
named *which* items in advance.

## The mechanism behind the trade, and it is structural rather than incidental

Arm `four` fires less and routes better **for one reason**: in a four-entry
world, *declining to name a tool is declining to fire*. The two decisions are one
act. Arm `one` can fire and then fail to route — it did so on `p03` and `p09` —
and arm `four` cannot.

That explains the whole trade in one sentence. `four` never fires on a message it
cannot confidently route, so its false positives vanish (`n07` 2/5 → 0/5, `n11`
3/5 → 0/5) and its misses grow (`x-n20` 5/5 → 1/5, `p03` 5/5 → 3/5, `p12` 5/5 →
3/5). It is not a better or worse selector. **It is a more conservative one, and
the conservatism is forced by the structure rather than chosen.**

Which arm that favours depends on a judgement nobody here has made explicitly:
**is a missed decision or an unwanted interruption the more expensive error?**
Arm `one` is 0.018 FPR / 0.878 recall; arm `four` is 0.000 / 0.800. Neither
dominates. The repository has never written down which side it wants.

## `x-n20` is the item that argues the other way

`x-n20` — a promoted `evidence-ledger` negative labelled `timing` — fires 5/5 and
routes 4/5 in arm `one`, and fires **1/5** and routes **0/5** in arm `four`. It
is the single largest per-item regression in the run and it is worth a maintainer
reading, alongside `x-n21`/`x-n22`, whose labels were already in question.

## What I am not doing

**Not restructuring the skill.** Four entries routed better in one run on one
instrument at one model tier, and unbundling `decision-making` today on the
strength of it would be the same error as editing the router table this morning:
acting on the measurement that motivated the question. The result goes to Track L
and Track M5 as an input.

**The honest next step is smaller and cheaper.** The router-table defect and the
one-entry structure are now separable claims, and only one of them has support:
give the table's rows the disambiguating clauses (an L6 variant) and re-run arm
`one`. If that closes the routing gap, the bundle was never the problem and the
table always was.

## For `CLAUDE.md` and `AGENTS.md`

The block that says one-entry-not-four is "a judgement call wearing a citation"
was right, and it now has a measurement instead of a citation. It should say:
**at n=4, measured here, one entry and four entries are indistinguishable on
firing accuracy, and four routed better.** That is not a reason to unbundle, and
it is a reason to stop citing a 202-skill result as though it applied.
