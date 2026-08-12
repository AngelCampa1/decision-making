# Seven-eighths of the effect is scatter, and we were measuring the other eighth

**2026-08-11.** Track I1. No model calls — this is arithmetic and a module.

## What I went to check

`stats/reliability.py` was on the work order's unattended list as "within-item
scatter, at the repo's 100% line+branch floor with property tests, matching
`paired.py`". Before writing an estimator I fetched the paper it comes from,
because Rule 5 says cite nothing you have not opened and the whole module is an
implementation of somebody else's definition.

The abstract does not define the terms. The full text does, in §4.2:

> A^90 = percentile_90(S)
>
> U^90_10 = percentile_90(S) − percentile_10(S)

and gives the split:

> Model aptitude degrades in a non-significant way between the full and sharded
> settings, with an average drop of 16%

> unreliability skyrockets with an average increase of 112% (more than doubling)

(arXiv:2505.06120, read 2026-08-11; now in `paper/refs.bib` as a `quote` field.)

## The thing worth writing down

**The −39% this programme is built on is not mostly a drop in what the model can
do.** Aptitude falls 16% and the paper calls that non-significant. Unreliability
more than doubles. The degradation is overwhelmingly the model becoming
*inconsistent*, not becoming *worse*.

Every measurement this repository has taken is a mean. Three corpora, one run per
item, averaged. If the effect here behaves like the effect there, **a mean-only
design was pointed at the smaller and less significant of the two components** —
and the three nulls are exactly what you would expect from that.

I am not claiming the nulls are explained by this. The corpora were also short,
single-turn and under-powered, and any of those is sufficient on its own. But it
is the first account I have of the nulls that predicts *which* number would come
back flat, and it was available in a paper already cited in the programme.

## A correction to a document in this repository

`docs/superpowers/plans/2026-08-11-long-context-experiment.md` says:

> for any ICC > 0 the between-item variance dominates the within-item sampling
> variance, so **24 cores × 1 repeat strictly dominates 12 cores × 2 repeats**

That is correct for estimating a **mean** and wrong for estimating a **spread**,
and the programme already flagged it as a task rather than a footnote. The sharp
version, now enforced in code: at one repeat per item the within-item scatter is
not imprecise, it is **undefined**. `per_item_reliability` refuses `n_repeats=1`
and says why in the error message, because a silent zero would have been worse
than a crash.

The two questions have different answers and `repeats_for_scatter_precision`
prices the second. At ICC 0.6, a mean outcome reaches reliability 0.8 in **2**
repeats; estimating a per-item spread to a relative standard error of 0.25 takes
**9**. That is a 4.5× difference in run count arriving from a choice of outcome,
and it is the kind of thing that has to be settled before a grid is sized rather
than after.

## Prediction, registered now, for whenever Track A5 runs

Track A5 is "*k* repeats per item at each venue. Measure the scatter, not the
mean." Writing the number down first, per the standing rule:

**I predict A5 finds unreliability increasing by more than 50% between the
single-call and multi-turn venues, while aptitude moves by less than 15%.**
That is directionally the paper's result at roughly half its magnitude, discounted
because our tasks are shorter and our scorer is coarser than theirs.

My last five predictions were wrong in the same direction — toward the experiment
working — and this one is in that same direction again. Noted here so that when
it is scored, the prior is already on the record.

## A defect the property test caught

`repeats_for_reliability` inverts Spearman-Brown and rounds up. At ICC 0.25 and
target 0.8 the exact answer is 12 on the nose; binary floating point returns
12.000000000000002 and a bare `ceil` charged **13** repeats. Across a grid that
is a systematic over-spend of quota, silent, and always in the same direction.

Fixed by checking the answer against the forward function rather than by adding a
tolerance constant — `repeat_reliability(icc, k-1) >= target` means `k` was one
too many. The property test asserts the returned count is *sufficient and
minimal*; an example-based test only catches this if the author happens to pick a
pair whose exact solution is an integer, and I did not, twice.

## State

- `evals/src/decision_evals/stats/reliability.py`, 100% line and branch.
- 50 unit tests, 7 property tests.
- `de check` green, 9 of 9.
- Not yet done in Track I: **I2** (every experiment reports scatter alongside its
  mean — nothing calls this module yet) and **I3** (power re-derived for a
  reliability outcome). I1 is a tool, not a result.
