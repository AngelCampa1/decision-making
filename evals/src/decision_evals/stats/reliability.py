"""Reliability: scatter as an outcome, not as noise around one.

The multi-turn result this programme is built on decomposes its −39% into two
very unequal parts. From arXiv:2505.06120 §4.2, verbatim: *"Model aptitude
degrades in a non-significant way between the full and sharded settings, with an
average drop of 16%"*, while *"unreliability skyrockets with an average increase
of 112% (more than doubling)"*.

**A mean-only metric would have found almost nothing there.** Seven-eighths of
that degradation lives in the spread, and the spread is invisible to any design
that runs each item once and averages. Binary admissibility in this repository is
already close to a constant — 0.917 with zero variance in two of its three
conjuncts — so a mean is the least informative summary available.

That has a consequence the long-context plan got backwards, and it is worth
stating plainly because the plan is still in the repository saying the opposite.
That plan argues repeats are near-worthless, since for any ICC > 0 the
between-item variance dominates the within-item sampling variance. **That is
correct for estimating a mean and exactly wrong for estimating a spread.** At one
repeat per item, :func:`per_item_reliability` has nothing to compute: the
within-item scatter is not merely imprecise, it is undefined. Repeats go from
nearly worthless to mandatory the moment the outcome is reliability, and
:func:`repeats_for_scatter_precision` prices them.

The two estimators here are kept separate on purpose:

* :func:`aptitude_unreliability` is **the paper's**, applied to whatever score
  set you hand it, and nothing more.
* :func:`per_item_reliability` is **ours** — the same estimator applied per item
  so that scatter becomes a paired per-item quantity and can go straight into
  :func:`~decision_evals.stats.paired.paired_permutation_test`. The paper's
  aggregation level was not confirmed against the text, so this is labelled an
  extension rather than a reimplementation.

A skill that reduces scatter without moving the mean is a **result**, and this
module is what lets it be pre-registered as one instead of discovered post hoc.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from decision_evals.stats.cluster import intraclass_correlation

#: The percentiles arXiv:2505.06120 §4.2 uses: ``A^90 = percentile_90(S)`` and
#: ``U^90_10 = percentile_90(S) - percentile_10(S)``.
DEFAULT_LOW: float = 10.0
DEFAULT_HIGH: float = 90.0


@dataclass(frozen=True, slots=True)
class ReliabilityResult:
    """Aptitude and unreliability over one set of scores.

    Attributes:
        n_scores: Number of scores the estimate is built from.
        aptitude: ``percentile_high(S)`` — the best-case score, the paper's
            ``A^90``.
        unreliability: ``percentile_high(S) - percentile_low(S)`` — the gap
            between best and worst case, the paper's ``U^90_10``.
        mean_score: Ordinary mean, reported alongside so that a change in the
            mean and a change in the spread are never confused for each other.
        low: Lower percentile used.
        high: Upper percentile used.
    """

    n_scores: int
    aptitude: float
    unreliability: float
    mean_score: float
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class PerItemReliability:
    """Per-item aptitude and scatter, plus the pooled reliability of the design.

    Attributes:
        aptitude: One ``percentile_high`` per item.
        scatter: One ``percentile_high - percentile_low`` per item. This is the
            array to pass to a paired test when asking whether a skill makes the
            model *steadier*.
        item_mean: One ordinary mean per item.
        icc: Intraclass correlation treating items as clusters and repeats as
            members — the proportion of total variance that is between items.
            High ICC means repeats agree with each other and the item is the
            real unit; low ICC means the model is scattering.
        n_items: Items measured.
        n_repeats: Repeats per item.
    """

    aptitude: npt.NDArray[np.float64]
    scatter: npt.NDArray[np.float64]
    item_mean: npt.NDArray[np.float64]
    icc: float
    n_items: int
    n_repeats: int


def _validate_percentiles(low: float, high: float) -> None:
    if not 0.0 <= low <= 100.0:
        raise ValueError(f"low must be in [0, 100], got {low}")
    if not 0.0 <= high <= 100.0:
        raise ValueError(f"high must be in [0, 100], got {high}")
    if low >= high:
        raise ValueError(f"low must be strictly below high, got low={low}, high={high}")


def aptitude_unreliability(
    scores: npt.ArrayLike,
    *,
    low: float = DEFAULT_LOW,
    high: float = DEFAULT_HIGH,
) -> ReliabilityResult:
    """The arXiv:2505.06120 §4.2 decomposition, applied to one score set.

    ``A^90 = percentile_90(S)`` and ``U^90_10 = percentile_90(S) -
    percentile_10(S)``. Nothing is assumed about what ``S`` ranges over; hand it
    the score set whose best case and spread you want.

    Args:
        scores: One-dimensional score set.
        low: Lower percentile. Defaults to the paper's 10.
        high: Upper percentile. Defaults to the paper's 90.

    Returns:
        A :class:`ReliabilityResult`.

    Raises:
        ValueError: If ``scores`` is empty or not one-dimensional, or the
            percentiles are outside ``[0, 100]`` or not strictly ordered.

    Note:
        Linear interpolation between order statistics — numpy's default, and
        stated because it matters at the sizes actually run. The paper uses
        ``N=10`` simulations, where the 90th percentile is an interpolation
        between the 9th and 10th of ten values and is therefore driven almost
        entirely by the single best run. Treat it as a best-case *estimate* with
        wide sampling error, not as a stable statistic.
    """
    _validate_percentiles(low, high)
    arr = np.asarray(scores, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"scores must be one-dimensional, got shape {arr.shape}")
    if arr.size == 0:
        raise ValueError("scores must not be empty")

    p_low, p_high = (float(x) for x in np.percentile(arr, (low, high)))
    return ReliabilityResult(
        n_scores=int(arr.size),
        aptitude=p_high,
        unreliability=p_high - p_low,
        mean_score=float(arr.mean()),
        low=low,
        high=high,
    )


def per_item_reliability(
    scores: npt.ArrayLike,
    *,
    low: float = DEFAULT_LOW,
    high: float = DEFAULT_HIGH,
) -> PerItemReliability:
    """Apply the same estimator per item, so scatter becomes a paired quantity.

    Our extension, not the paper's. The point is that ``scatter`` comes back as
    one number per item, in item order, which makes "did the skill reduce
    scatter" an ordinary paired comparison against the control arm's array.

    Args:
        scores: Two-dimensional, ``(n_items, n_repeats)``. Row order is item
            order and must match across arms for the pairing to mean anything.
        low: Lower percentile.
        high: Upper percentile.

    Returns:
        A :class:`PerItemReliability`.

    Raises:
        ValueError: If ``scores`` is not two-dimensional, has no items, or has
            fewer than two repeats.

    Note:
        Two repeats is the arithmetic minimum and is not a recommendation — at
        ``n_repeats=2`` every percentile is an interpolation between the same
        two values, so ``scatter`` degenerates to a fixed fraction of the
        absolute difference. :func:`repeats_for_scatter_precision` gives the
        count that actually supports an estimate.
    """
    _validate_percentiles(low, high)
    arr = np.asarray(scores, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"scores must be two-dimensional (items, repeats), got shape {arr.shape}")
    n_items, n_repeats = arr.shape
    if n_items < 1:
        raise ValueError("scores must contain at least one item")
    if n_repeats < 2:
        raise ValueError(
            f"scatter needs at least 2 repeats per item, got {n_repeats}. At one repeat "
            "within-item spread is undefined, not merely imprecise — this is the whole "
            "reason a reliability outcome changes the design."
        )

    p_low, p_high = np.percentile(arr, (low, high), axis=1)

    # Items are the clusters and repeats are their members, which is exactly the
    # shape cluster.intraclass_correlation already consumes. ICC needs two
    # clusters to have a between-cluster term at all.
    if n_items < 2:
        icc = 0.0
    else:
        labels = np.repeat(np.arange(n_items), n_repeats)
        icc = intraclass_correlation(arr.ravel(), labels)

    return PerItemReliability(
        aptitude=np.asarray(p_high, dtype=np.float64),
        scatter=np.asarray(p_high - p_low, dtype=np.float64),
        item_mean=arr.mean(axis=1),
        icc=icc,
        n_items=int(n_items),
        n_repeats=int(n_repeats),
    )


def _validate_icc(icc: float) -> None:
    if not 0.0 <= icc <= 1.0:
        raise ValueError(f"icc must be in [0, 1], got {icc}")


def repeat_reliability(icc: float, n_repeats: int) -> float:
    """Spearman-Brown: reliability of a mean over ``k`` repeats.

    ``k * ICC / (1 + (k - 1) * ICC)``. This is the *mean* outcome's side of the
    argument — how much averaging repeats sharpens an item's estimated score.

    Args:
        icc: Single-measurement intraclass correlation, in ``[0, 1]``.
        n_repeats: Repeats averaged. Must be >= 1.

    Returns:
        Reliability of the ``k``-repeat mean, in ``[0, 1]``.

    Raises:
        ValueError: If ``icc`` is outside ``[0, 1]`` or ``n_repeats < 1``.
    """
    _validate_icc(icc)
    if n_repeats < 1:
        raise ValueError(f"n_repeats must be >= 1, got {n_repeats}")
    k = float(n_repeats)
    denominator = 1.0 + (k - 1.0) * icc
    return float(k * icc / denominator)


def repeats_for_reliability(icc: float, target: float) -> int:
    """Repeats needed for a ``k``-repeat mean to reach a target reliability.

    Spearman-Brown inverted: ``k = target(1 - ICC) / (ICC(1 - target))``.

    Args:
        icc: Single-measurement intraclass correlation.
        target: Reliability wanted, strictly between 0 and 1.

    Returns:
        Repeats required, at least 1.

    Raises:
        ValueError: If ``icc`` is outside ``[0, 1]``, ``target`` is outside
            ``(0, 1)``, or ``icc == 0`` — at zero single-measurement
            reliability no amount of averaging reaches any positive target, and
            that is the answer rather than an error to work around.
    """
    _validate_icc(icc)
    if not 0.0 < target < 1.0:
        raise ValueError(f"target must be in (0, 1), got {target}")
    if icc == 0.0:
        raise ValueError(
            "icc=0 means repeats carry no shared signal, so no number of them reaches "
            f"reliability {target}. The item is the problem, not the repeat count."
        )
    k = target * (1.0 - icc) / (icc * (1.0 - target))
    n_repeats = max(1, math.ceil(k))

    # The exact solution is an integer surprisingly often -- icc=0.25 at
    # target=0.8 gives exactly 12 -- and binary floating point lands a hair
    # above it, so a bare ceil buys a repeat nobody needs. Checking the answer
    # against the forward function is exact and needs no tolerance constant.
    if n_repeats > 1 and repeat_reliability(icc, n_repeats - 1) >= target:
        n_repeats -= 1
    return n_repeats


def repeats_for_scatter_precision(relative_standard_error: float) -> int:
    """Repeats needed to estimate a within-item spread to a given precision.

    The standard error of a sample standard deviation is approximately
    ``sigma / sqrt(2(k - 1))``, so the relative standard error is
    ``1 / sqrt(2(k - 1))`` and ``k = 1 + 1 / (2 * rse^2)``.

    This is the counterpart to :func:`repeats_for_reliability` and the one that
    matters for a reliability outcome: it prices the repeats needed to *measure
    the spread itself*, rather than to average it away.

    Args:
        relative_standard_error: Wanted ``SE(s) / sigma``, strictly between 0
            and 1. 0.25 is a reasonable working target and costs 9 repeats.

    Returns:
        Repeats required, at least 2.

    Raises:
        ValueError: If ``relative_standard_error`` is outside ``(0, 1)``.

    Note:
        Exact under normality and approximate otherwise. Our scores are bounded
        and often near-binary, so treat the figure as a floor on the repeat
        count rather than a precise requirement.
    """
    if not 0.0 < relative_standard_error < 1.0:
        raise ValueError(
            f"relative_standard_error must be in (0, 1), got {relative_standard_error}"
        )
    return max(2, math.ceil(1.0 + 1.0 / (2.0 * relative_standard_error**2)))
