# Prediction: the third partition, and a mechanism that names one item in advance

**2026-08-13**, written and committed **before the run starts**. Track M6, second
arm.

## Why there is a third arm at all

There are exactly **three** ways to split four procedures into two entries of
two, and
[M6](2026-08-12-m6-covers-went-up-and-the-measure-does-not-survive-it.md) ran
two of them:

| partition | `covers` |
|---|---|
| `ledger-fit` / `cascade-timing` (M5, contiguous) | 0.743 |
| `ledger-cascade` / `fit-timing` (M6) | 0.857 |
| **`ledger-timing` / `fit-cascade`** | **this run** |

M6's finding was that `covers` moves with the partition rather than with the
model. On two points that is an observation. On all three it is an **enumeration
of the whole space**, and the spread across it is the size of the artefact — a
quantity the write-up needs and currently does not have.

## The mechanism, stated as a per-item prediction

M6's explanation was specific: `p06` is labelled `fit`, and the model reaches for
something *timing*-flavoured on it in **every** arm. Whether that scores 1 or 0
depends on one thing only — **does `timing` share an entry with `fit`?**

| arm | `timing` shares with | predicted `p06` | observed |
|---|---|---|---|
| M5 | `cascade` | low | **0.2** |
| M6 | **`fit`** | high | **1.0** |
| **this run** | `ledger` | **low** | — |

**So the registered prediction is that `p06` falls back to ≤ 0.5.** This is the
sharpest thing the M track has: a single named item, a stated direction, and a
mechanism that forbids the alternative. If `p06` comes back high under
`ledger-timing`, the boundary-forgiveness account is wrong and M6's conclusion
has to be withdrawn along with M5's.

## Predictions

73 cases × 2 repeats, one arm, on M6's reliability finding (ICC 0.852, 1 of 73
items with any scatter).

| # | Prediction | Band | Estimator |
|---|---|---|---|
| 1 | Parseable verdicts | ≥ 98% | share of records with non-null `fired` |
| 2 | **`p06` falls back** | **≤ 0.5** | mean `covers` over `p06`'s 2 records |
| 3 | `covers` sits between the other two partitions | 0.74–0.86 | `covers` over **all labelled calls**, non-answer a miss |
| 4 | Firing accuracy unmoved | 0.90–0.97 | `fired == should_fire` over all 146 records |
| 5 | FPR at the floor | ≤ 0.018 | false fires ÷ 55 negatives |
| 6 | No firing difference from either n=2 arm | both p ≥ 0.05 | per-item fire-correctness, 73 pairs, paired Wilcoxon, `zero_method="wilcox"` |

**2 is the experiment. 3 is soft and I am saying so** — with two of three points
already at 0.743 and 0.857, "between them" is a 12-point band around a
12-point gap, and the third partition could legitimately sit outside it without the
mechanism being wrong. It is registered because a stated number is better than
none, not because it discriminates.

**4, 5 and 6 are the control**, identical in kind to M6's: the three partitions
are word-multiset identical to each other, so firing has no reason to move. If
it does, band 2 cannot be read.

## What this run cannot do

It does not rescue `covers`. Three points that disagree are still three points
that disagree, and the measure stays retired as a cross-arm routing statistic.
What the third point buys is the **range** — the honest statement of how much of
any merged-arm routing number is partition rather than model.

## Cost

73 × 2 = **146 isolated calls**, one arm, own checkpoint.
