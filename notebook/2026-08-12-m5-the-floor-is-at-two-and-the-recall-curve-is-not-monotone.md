# M5: the conservatism floor is reached at two, and the recall curve is not monotone

**2026-08-12.** Outcome for
[the prediction](2026-08-12-m5-prediction-where-the-curve-turns.md), committed at
`4e437d7` before the run started. Track M5. **365 isolated calls** (73 cases × 5
repeats), one arm, Haiku, **0 unparseable, 0 isolation failures**. The n=1 and
n=4 reference arms are the existing five-repeat runs and were not re-run.

The run was made twice. The first 365 calls were voided by
[the parser whitelist](2026-08-12-m4-shadowing-did-not-appear-at-four.md) — not
in their firing, which was unaffected, but in their routing, every value of which
was discarded on the way in. What follows is the repaired re-run.

## Scored as registered

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | Parseable verdicts | ≥ 98% | **100%** (365/365) | ✅ |
| 2 | n=2 firing accuracy between the two | 0.93–0.97 | **0.940** | ✅ |
| 3 | **n=2 FPR at or below n=1's** | ≤ 0.018 | **0.000** | ✅ |
| 4 | n=2 recall | 0.80–0.90 | **0.756** | ❌ |
| 5 | `covers` | 0.70–0.95 | **0.743** | ✅ |
| 6 | No arm differs from n=1 | paired Wilcoxon p ≥ 0.05 | **p = 0.497** | ✅ |

**Five of six.** Band 2 was recorded in advance as nearly a free pass and it
should be read as one. **Band 3 was the mechanism test and it passed. Band 4 is
the miss and it is the interesting one.**

## The curve

| | n=1 | **n=2** | n=4 |
|---|---|---|---|
| firing accuracy | 0.956 | **0.940** | 0.951 |
| false-positive rate | 0.018 | **0.000** | 0.000 |
| recall | 0.878 | **0.756** | 0.800 |
| precision | 0.940 | **1.000** | 1.000 |

**The false-positive floor is reached at two entries, not four.** M4's
explanation was structural: with separate entries, declining to name a tool *is*
declining to fire, so the arm never fires on a message it cannot confidently
route. If that were an artefact of four-way choice it would not appear at two.
It appears at two, at full strength — 0.000, in every one of five repeats, with
zero variance. That is the strongest form band 3 could have taken.

**And recall is not monotone in entry count.** 0.878 → 0.756 → 0.800. Two entries
recall *worse* than four, which no account of entry count alone predicts.

## The confound was named first, and it is the best available explanation

From the prediction, written before the numbers existed:

> Mechanical joining reads worse than a human would write. At n=4 each entry is
> one clean clause; at n=2 each is *"…what it starts, or what it spends **or**
> the direction is settled and the question is when"*. **An n=2 disadvantage may
> be prose quality rather than entry count.**

The n=2 arm is exactly the arm with the worst prose, and it is exactly the arm
with the anomalous recall. That is what the confound predicted, and it is why
the prediction also said the clean contrast in this curve remains n=1 against
n=4 — which is already run and is M4.

So **M5 does not establish a monotone relationship and it is not reported as
one.** What it establishes is band 3: the conservatism effect is not a four-way
artefact.

## Band 5 named its outcome and not its denominator

`covers` asks whether the entry the model named contained the labelled
procedure. It admits two denominators, and the band said which measure without
saying over what:

| denominator | value |
|---|---|
| all labelled calls, a non-answer counting as a miss | **0.743** ± 0.081 |
| labelled calls where the arm fired and named something | **0.895** ± 0.073 |

**Both sit inside the registered 0.70–0.95, so the ambiguity did not change the
verdict — this time.** It is recorded because it is the fourth pre-registration
slip of the day and the working rule already says a band must name its
estimator. It now has to name the estimator's *denominator* too.

The reported figure is **0.743**, because that is the denominator
`evaluate_routing` uses for the n=1 and n=4 arms — a non-answer is a routing
failure there and must be one here. Chance is 0.500 against n=4's 0.250, so
**this number must not be plotted on one curve with 0.686 and 0.786.**

## The instrument printed a clean zero for the second time in one day

The run finished and its report read:

```
ROUTING  (secondary -- the easier question)
  accuracy   0.000 over 14 labelled (4 excluded as open)
    p01: wanted ledger, got ledger-fit
```

Nothing had failed. The arm offers `ledger-fit` and `cascade-timing`; the labels
say `ledger` and `cascade`; **no answer the model could have produced would have
matched.** This is the parser whitelist one layer further out — that bug
discarded the offered names on the way *in*, this one graded them on the way
*out* against names never offered. Both produce a clean run, a full checkpoint,
and a zero.

`routing_is_by_name` now refuses the measure for any arm whose entry names are
not the procedure names, prints why, and reports `covers` instead. Five tests.

**The pattern across both defects is worth stating plainly: this instrument's
failure mode is not a crash, it is a plausible number.** Firing was correct in
both runs and nothing downstream complained.

## A free replication nobody designed

The voided run and the repaired run are two independent 365-call runs of the
same arm. Firing was never affected by the parser bug, so they can be compared:

**355 of 365 firing decisions are identical — 97.3%.**

The ICC on this run is 0.833 and only 3 of 73 items show any scatter across five
repeats. Both say the same thing: **at this instrument, firing is close to
deterministic, and repeats buy very little.** `repeats_for_reliability` asks for
1 repeat at r=0.8 and 2 at r=0.9. Future arms can run 2 repeats rather than 5
and spend the quota on more arms — which is the first design change any of these
runs has earned.

## What M4 and M5 say together

Three runs today have now moved firing accuracy nowhere: M4 by structure
(p = 0.83), L5 by content (no contrast significant on combined accuracy), M5 by
entry count (p = 0.50). Every one of them moved **where on the precision/recall
frontier the skill sits**, and none of them moved how well it discriminates.

**Entry count does not change how well this description selects. It changes only
how conservative the selection is.** That statement now rests on two arms at
n=2 and n=4 against the same n=1 baseline, and it is the M-track's result.

## For the maintainer

1. **Still the same open question, and it is now blocking three runs' worth of
   interpretation.** `no-opener` at FPR 0.000 / recall 0.867, n=4 at 0.000 /
   0.800, n=2 at 0.000 / 0.756, the shipped bundle at 0.018 / 0.878. **Which
   point is wanted is a product decision nobody has made**, and until it is made
   none of these arms can be called better than another.
2. **`x-n03` is new.** It goes 1.0 at n=1 to 0.0 at n=2 — the largest per-item
   regression in this run, alongside `x-n20`'s 1.0 → 0.2, which was already
   flagged in M4.
3. **M6 is worth running and M5 cannot substitute for it.** Which two procedures
   are paired at n=2 was fixed as a contiguous partition to keep the arm a
   function of `n` alone. Pairing `cascade` with `timing` is a hypothesis about
   their overlap — and the router table already collides on exactly those two.
