# Prediction: the collision was hiding inside the entry

**2026-08-12**, written and committed **before the run starts**. Track M6.

## The question M5 could not ask

[M5](2026-08-12-m5-the-floor-is-at-two-and-the-recall-curve-is-not-monotone.md)
spread the four procedures across two entries and got `covers` 0.743. Its
partition is **contiguous in table order** by construction, so that the arm was
a function of `n` alone — and table order pairs `cascade` with `timing`.

Those two rows were diagnosed as colliding on the morning of 2026-08-12, before
any of this ran: [the table gives *order* to `cascade` and *when* to
`timing`](2026-08-12-cascade-and-timing-collide-in-the-table.md), and `p07` —
the item that turns on exactly that distinction — scored **1/5** in the
one-entry arm and **5/5** in the four-entry arm, which has no table.

**M5 put the colliding pair inside a single entry, where a confusion between
them cannot be observed at all.** `p07` is labelled `cascade`; the arm answers
`cascade-timing`; `covers` scores it correct whether the model meant `cascade`
or `timing`. So some unknown share of M5's 0.743 is the defect being concealed
by the grouping rather than solved by it.

M6 splits the pair: **`ledger-cascade` and `fit-timing`**, two entries, same
count, same four rows.

## Why this arm is the cleanest one this repository has built

The two groupings are **word-multiset identical** — the same four conditions and
the same four products, merged two ways, with the shared opener and exclusions
unchanged and `or` the only connective either arm adds. A test asserts the
multiset equality and fails if prose ever starts varying alongside grouping.
Clause order inside an entry stays table order whatever the grouping, so
regrouping cannot smuggle in a reordering. Lengths differ by one character.

Nothing else in the M or L track has had this property. L5's arms differ by
whole sentences; M4's differ in entry count; M5's differ in count and in how
clumsy the merge reads. **Here the manipulation is the grouping and literally
nothing else.**

## Predictions

73 cases × 2 repeats, one arm. Two repeats rather than five because
[M5 measured ICC 0.833 and 3 of 73 items with any
scatter](2026-08-12-m5-the-floor-is-at-two-and-the-recall-curve-is-not-monotone.md),
and `repeats_for_reliability` asks for 2 at r=0.9.

Reference points, both measured, both at 5 repeats:

| | n=2 contiguous (`ledger-fit` / `cascade-timing`) |
|---|---|
| firing accuracy | 0.940 |
| FPR | 0.000 |
| recall | 0.756 |
| `covers`, all labelled calls | 0.743 |

| # | Prediction | Band | Estimator |
|---|---|---|---|
| 1 | Parseable verdicts | ≥ 98% | share of records with non-null `fired` |
| 2 | **`covers` falls under the split pairing** | **< 0.743** | `covers` over **all labelled calls**, a non-answer counting as a miss — the same denominator M5 reports and `evaluate_routing` uses |
| 3 | `covers` stays above chance | > 0.500 | same |
| 4 | Firing accuracy is unmoved | 0.90–0.97 | `fired == should_fire` over all 146 records |
| 5 | FPR stays at the floor | ≤ 0.018 | false fires ÷ 55 negatives, per repeat then meaned |
| 6 | No difference from the contiguous arm on firing | paired Wilcoxon p ≥ 0.05 | per-item fire-correctness rates, 73 pairs, `zero_method="wilcox"` |

**2 is the experiment.** If splitting the colliding pair costs nothing, the
collision either is not real or does not reach this instrument, and M5's routing
number stands as measured. If it costs a lot, then M5's 0.743 was partly an
artefact of *which* two procedures happened to be adjacent in the table, and no
routing number at n=2 can be quoted without naming its pairing.

**4, 5 and 6 are the control.** Every word available to the model is identical
across the two arms and all four procedures are offered either way, so firing
has no reason to move. If it moves, the arm is not doing what this design says
it does and predictions 2 and 3 cannot be read.

## Where I expect to be wrong

**Band 3 is soft.** Chance is 0.500 only for a model that answers every labelled
call; non-answers count as misses in this denominator and drag the number below
what a two-way guess would score, so 3 is not quite the floor it reads as. I am
registering it anyway because it is the direction that matters, and recording
here that it is not a clean chance comparison.

**And band 2 has a confound I cannot remove.** `ledger-cascade` merges *"a pile
of context arrived…"* with *"the action looks fine and the worry is what it
starts"*, which is a less natural pair of clauses than `ledger-fit`. So a fall in
`covers` could be the merged sentence reading worse rather than the collision
being exposed. **The diagnostic is `p07` specifically** — the item the collision
was diagnosed on. If `covers` falls and `p07` is where it falls, that is the
collision. If `covers` falls evenly across items, it is prose.

That per-item check is named here, before the run, because naming it afterwards
is how the last three of these went wrong.

## Cost

73 cases × 2 repeats = **146 isolated calls**, one arm, own checkpoint
(`verdicts-pairing-ledger+cascade,fit+timing.jsonl`).
