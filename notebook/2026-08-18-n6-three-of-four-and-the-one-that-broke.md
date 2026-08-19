# 2026-08-18 — N6: three bands of four, and the one that broke

Outcome of the grid registered on
[2026-08-13](2026-08-13-n6-prediction-does-accuracy-fall-on-the-long-bands.md),
amended on
[2026-08-14](2026-08-14-n6-unblocked-q1-goes-descriptive-the-test-moves-to-the-ten-point-boundary.md)
and recomputed this morning in
[the addendum](2026-08-18-n6-addendum-the-corpus-shrank-and-the-version-had-to-move.md).
**1,548 calls**, three arms, 258 items, 2 repeats, `haiku`, 0 unparseable.
Published at
[`results/decision-making/2026-08-18-e632659-n6-confirmatory/`](../results/decision-making/2026-08-18-e632659-n6-confirmatory/README.md).

## The thing worth saying first

**This is the first trigger measurement in this repository that is not mostly a
ruler.** Every published number before it ran on a corpus 89% solvable by
counting words. On v4 the best depth-2 stump reads 0.7054, and the three arms
land at 0.9477, 0.9360 and 0.8295 — clearing it by 24, 23 and 12 points.

That does not make the skill good. It makes the number *about the skill*, which
the earlier ones were not, and which is the whole of what Track N was for.

## Q1 met, and in all three arms rather than the one registered

`bootstrap_rate_difference(control=L+XL, treatment=S+M, cluster_on="triple")`
over `full`-arm records, the registered denominator: **+0.0976, 95% CI
[+0.0459, +0.1493]**, seed 17. `stakes-shown` +0.0948, `opener-only` +0.2367,
both also excluding zero.

**Accuracy falls on the long bands, and the fall is in precision, not recall.**
Recall is *higher* on `l` and `xl` in every arm; FPR is what rises. The
2026-08-13 entry's "where I expect to be wrong" said the opposite — it predicted
a recall failure on `xl`, from long positives ending in short asks the
description would miss. That reasoning was wrong in a way worth keeping: the
problem is not that a long turn hides its ask, it is that a long turn gives a
reader enough material to read a decision into an ask that has none.

## Q4 falsified, and the falsification is narrower than it first looked

Registered: *"`settled` has the highest FPR of the seven kinds"*, on the
reasoning that a decision already made and stated is the negative that still
looks like one. Observed: **0.000, 0.025, 0.050** — bottom of the ranking in all
three arms, while `lookup`, predicted lowest, ranks fifth or sixth of seven
everywhere.

**But "settled is lowest" is a ranking, not a separation.** The reviewer briefed
to break this checked `NegativeKindRate.separated_from` and it does not hold up
the way the point estimates suggest: `settled` is separated from **`meta` only**
in `full`, from **nothing at all** in `stakes-shown`, and from four kinds in
`opener-only`. What survives is the half that was actually registered —
`settled` is nowhere near the top — and that half is robust across three
independent descriptions at n = 20.

**And the "so what is highest instead" claim must not ride on it.** It is `meta`
(n = 7, three items firing) in two arms and `compute` (n = 27) in the third.
That is small-n and arm-dependent, and reporting it in the same breath as the
falsification would be smuggling a weak finding in on a strong one's ticket.

## The unregistered finding: `opener-only` breaks on one band, not everywhere

| arm | s | m | l | xl |
|---|---|---|---|---|
| `full` | 0.010 | 0.000 | 0.190 | 0.147 |
| `stakes-shown` | 0.021 | 0.000 | 0.179 | 0.132 |
| `opener-only` | 0.073 | 0.104 | **0.524** | 0.368 |

Its pooled FPR of 0.250 is a blend of near-full-strength short-band behaviour and
**more than half of `l`-band negatives firing** — worse than `xl`, despite `xl`
being longer. `compute` negatives fire 6 of 6 there and `lookup` 6 of 11.

This is the number that prices L7's finding. `opener-only` reaches recall 0.988
by deleting the routing summary and the exclusion list, and what that costs is
not a uniform 25% tax on ordinary turns; it is one band coming apart. It also
means the three arms' Q1 figures are not points on one scale — `opener-only`'s
+0.2367 is disproportionately one band breaking, a difference in kind wearing a
difference in degree.

## Q3 met, and `ledger` is the standing problem

Worst-routed in all three arms: 0.474, 0.579, **0.105**. `ledger` is the one
procedure with no external support (Track K6 ranks elicited confidence above it),
it is the one S7 marked invented outright, and it is now the worst-routed under
three independent descriptions. S9 already had it first in line for replacement.
This is the third independent line of evidence pointing the same way.

## The design effect was assumed 5–25× too high

`design_effect(m=3, icc=0.315) = 1.63` was the planning assumption, with no data
behind it, as the 2026-08-14 entry says itself. Measured: **0.0127, 0.0566,
0.0000**, giving effective n of 251.6, 231.8 and 258.0 against the 158.3 the
assumption implied.

The direction is the safe one — the registered 0.818 power at Δ = 0.10 was an
understatement — so nothing is invalidated. **The obligation is forward-looking:
0.315 is now measured wrong for this instrument and may not be reused.** Matched
triples turn out to induce almost no correlation in whether an arm gets the item
right, which is itself mildly surprising: three turns sharing a body are, for
this purpose, three observations rather than one.

## What was wrong before the run, and stays on the record

Two pre-registration defects, both found by looking for functions rather than
answers, both recorded
[before the analysis](2026-08-18-n6-two-arms-in-and-the-bands-were-checked-before-i-meant-to-look.md):
**Q2 names a quantity nothing computes** — there is no precision-sign function,
`compare()` is a Wilcoxon over correctness — and **Q4's band names no arm**,
which was resolved by declaring `full` and saying that the reading was chosen
after the run started.

And the ordering slip: a readiness check computed three of the four quantities on
the completed `full` arm while proving the estimators could move. The bands were
registered days earlier and `opener-only` was unseen, which is what keeps this a
disclosure rather than a retraction.

## Where this leaves the ledger above it

**Nothing above Track N's ruler may be claimed yet.** N6 is the confirmatory
re-run; N7 (the remaining five arms) has never started, and N4 — the human-written
holdout that controls for a model authoring the corpus that evaluates a model —
is routed to a public source and not fetched. What N6 licenses is narrow and
real: on a corpus whose trivial-feature ceiling is 0.705, three descriptions
separate, the ordering registered from v2 survives, accuracy falls on long turns
through precision, and the eager arm's cost is concentrated rather than spread.
