# Prediction: where the bundle-size curve turns

**2026-08-12**, written and committed **before the run starts**. Track M5.

## What is left to ask

[M4](2026-08-12-m4-shadowing-did-not-appear-at-four.md) raced 1 entry against 4
and found them **level on firing** (0.956 vs 0.951, paired Wilcoxon p = 0.83)
while 4 routed better. M5 asks the shape between them: the same four procedures
spread across **2** entries.

`entries()` partitions the router table contiguously and evenly, so the arm is a
function of `n` alone. At n=2 that is `ledger-fit` and `cascade-timing`.

## The confound, stated before the numbers exist

Mechanical joining reads worse than a human would write. At n=4 each entry is one
clean clause; at n=2 each is *"…what it starts, or what it spends **or** the
direction is settled and the question is when"*. **An n=2 disadvantage may be
prose quality rather than entry count.** Writing two fluent merged descriptions
would fix the prose and reintroduce the authoring problem the whole module exists
to avoid, so the confound is carried rather than removed — and any n=2 result is
reported with it attached.

The clean contrast in this curve remains **n=1 against n=4**, already run.

## Predictions

5 repeats, 73 cases, one arm. Reference points, both measured:

| | n=1 (`full`) | n=4 |
|---|---|---|
| firing accuracy | 0.956 | 0.951 |
| FPR | 0.018 | 0.000 |
| recall | 0.878 | 0.800 |

| # | Prediction | Band |
|---|---|---|
| 1 | Parseable verdicts | ≥ 98% |
| 2 | **n=2 firing accuracy sits between the two** | 0.93–0.97 |
| 3 | **n=2 FPR is at or below n=1's** | ≤ 0.018 |
| 4 | n=2 recall | 0.80–0.90 |
| 5 | `covers` — did the named entry contain the labelled procedure | **0.70–0.95** |
| 6 | No arm's firing accuracy differs from n=1 at p < 0.05 | paired Wilcoxon |

**3 is the mechanism test.** M4's whole explanation was that with separate
entries, *declining to name one is declining to fire*, so the arm never fires on
a message it cannot route. If that is right it should already bite at two
entries, and FPR should fall below the bundle's 0.018 rather than sitting between
0.018 and 0.000.

**5 has a wide band on purpose and it is not comparable across `n`.** A 2-way
choice has chance 0.5 against a 4-way choice's 0.25, so 0.786 at n=4 and 0.786 at
n=2 would not be the same achievement. It is registered descriptive, no p-value,
per [the power check](2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).

**6 is a prediction of a null and it is the honest one.** Two runs today have now
shown firing accuracy unmoved by structure (M4) and moved only along a
precision/recall frontier by content (L5). I expect n=2 to be a third
non-difference. If it is, the finding across M4 and M5 is that **entry count does
not change how well this description selects — it changes only how conservative
the selection is**, and that is a cleaner statement than any single arm.

## Where I expect to be wrong

**2.** "Between the two" is nearly unfalsifiable when the two endpoints are 0.956
and 0.951 — the band is five points wide around a five-thousandth-wide gap, so it
is close to a free pass and I am recording that rather than pretending it is a
test. **3 and 6 are the bands that can actually fail.**

## Cost

73 cases × 5 repeats = **365 isolated calls**, one arm, own checkpoint
(`verdicts-2-entries.jsonl`).
