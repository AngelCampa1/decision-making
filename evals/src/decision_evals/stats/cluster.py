"""Cluster-aware resampling and variance inflation.

Items generated from the same scenario template share structure, wording, and
difficulty, so their outcomes are correlated. The resampling unit must therefore
be the *template*, not the item. Ignoring this is not a rounding error: at six
variants per template and an intraclass correlation of 0.2 the design effect is
2.0, meaning 300 items carry the information of roughly 150.

This is the concrete form of Miller's clustered-standard-error point
(arXiv:2411.00640) for a benchmark built from parameterised templates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True, slots=True)
class ClusterBootstrapResult:
    """Percentile bootstrap interval for a paired difference, clustered.

    Attributes:
        point_estimate: Observed mean paired difference (treatment − control).
        ci_low: Lower bound of the percentile interval.
        ci_high: Upper bound of the percentile interval.
        standard_error: Standard deviation of the bootstrap distribution.
        confidence: Nominal coverage, e.g. 0.95.
        n_clusters: Number of distinct clusters resampled.
        n_items: Number of items.
        n_resamples: Bootstrap replicates drawn.
    """

    point_estimate: float
    ci_low: float
    ci_high: float
    standard_error: float
    confidence: float
    n_clusters: int
    n_items: int
    n_resamples: int

    @property
    def excludes_zero(self) -> bool:
        """Whether the interval excludes zero in either direction."""
        return self.ci_low > 0.0 or self.ci_high < 0.0


@dataclass(frozen=True, slots=True)
class TwoSampleClusterBootstrapResult:
    """Percentile bootstrap interval for a difference between **disjoint** groups.

    :class:`ClusterBootstrapResult` describes a *paired* difference: the same
    item measured twice, so the difference exists per item and the resampling
    unit carries both arms with it. This describes the other shape — two groups
    of different items, in different clusters, with no pairing available. The
    trigger corpus's length question is exactly that: S+M is 72 items in 24
    triples and L+XL is 48 items in 16 triples, and nothing pairs an S item with
    an L one.

    **The reason this exists rather than two calls to the one-sample form** is
    that a difference interval cannot be recovered by subtracting two independent
    percentile intervals. That subtraction gives an interval for the difference
    of the *bounds*, which is conservative in one direction and simply wrong in
    the other, and it drops the fact that the two groups' resampling error adds
    in variance rather than in width.

    Attributes:
        point_estimate: ``mean(treatment) − mean(control)``, over items. The
            sign convention matches :class:`ClusterBootstrapResult`.
        mean_control: Observed control mean.
        mean_treatment: Observed treatment mean.
        ci_low: Lower bound of the percentile interval on the difference.
        ci_high: Upper bound.
        standard_error: Standard deviation of the bootstrap distribution.
        confidence: Nominal coverage, e.g. 0.95.
        n_clusters_control: Clusters resampled in the control group — the
            number that governs that group's contribution to the width.
        n_clusters_treatment: Clusters resampled in the treatment group.
        n_items_control: Items in the control group.
        n_items_treatment: Items in the treatment group.
        n_resamples: Replicates drawn.
        icc: Intraclass correlation of the **group-centred** values, pooled over
            every cluster in both groups. Centring first is what stops the
            between-group difference itself from being read as within-cluster
            agreement: without it, a large treatment effect inflates the ICC and
            the design effect reports the effect rather than the clustering.
        design_effect: ``1 + (m - 1) * ICC`` at the pooled mean cluster size.
        effective_n: Total items over the design effect.
    """

    point_estimate: float
    mean_control: float
    mean_treatment: float
    ci_low: float
    ci_high: float
    standard_error: float
    confidence: float
    n_clusters_control: int
    n_clusters_treatment: int
    n_items_control: int
    n_items_treatment: int
    n_resamples: int
    icc: float
    design_effect: float
    effective_n: float

    @property
    def excludes_zero(self) -> bool:
        """Whether the interval excludes zero in either direction."""
        return self.ci_low > 0.0 or self.ci_high < 0.0

    @property
    def width(self) -> float:
        """Interval width. The quantity an item-level bootstrap understates."""
        return self.ci_high - self.ci_low


def _grouped_indices(
    clusters: npt.ArrayLike,
) -> tuple[npt.NDArray[np.intp], list[npt.NDArray[np.intp]]]:
    """Return unique cluster codes and, for each, the item indices belonging to it."""
    arr = np.asarray(clusters)
    if arr.ndim != 1:
        raise ValueError(f"clusters must be one-dimensional, got shape {arr.shape}")
    if arr.size == 0:
        raise ValueError("clusters must not be empty")
    _, codes = np.unique(arr, return_inverse=True)
    codes = codes.astype(np.intp, copy=False).ravel()
    n_groups = int(codes.max()) + 1
    order = np.argsort(codes, kind="stable")
    boundaries = np.searchsorted(codes[order], np.arange(n_groups + 1))
    members = [order[boundaries[g] : boundaries[g + 1]] for g in range(n_groups)]
    return np.arange(n_groups, dtype=np.intp), members


def cluster_bootstrap_diff(
    control: npt.ArrayLike,
    treatment: npt.ArrayLike,
    clusters: npt.ArrayLike,
    *,
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int | None = None,
) -> ClusterBootstrapResult:
    """Percentile bootstrap CI for a paired mean difference, resampling clusters.

    Whole clusters are drawn with replacement and all their items come along.
    This propagates within-cluster correlation into the interval, which is
    exactly what an item-level bootstrap fails to do.

    Args:
        control: Per-item control values.
        treatment: Per-item treatment values, same item order.
        clusters: Per-item cluster label (the template id). Any hashable dtype.
        confidence: Nominal coverage. Must lie strictly between 0 and 1.
        n_resamples: Bootstrap replicates.
        seed: Seed for reproducibility.

    Returns:
        A :class:`ClusterBootstrapResult`.

    Raises:
        ValueError: On mismatched lengths, empty input, ``n_resamples < 1``, or
            a ``confidence`` outside ``(0, 1)``.

    Note:
        When every cluster contains exactly one item this reduces to the ordinary
        item-level bootstrap, which is asserted directly in the test suite.
    """
    if n_resamples < 1:
        raise ValueError(f"n_resamples must be >= 1, got {n_resamples}")
    if not 0.0 < confidence < 1.0:
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")

    ctrl = np.asarray(control, dtype=np.float64)
    treat = np.asarray(treatment, dtype=np.float64)
    if ctrl.ndim != 1 or treat.ndim != 1:
        raise ValueError("control and treatment must be one-dimensional")
    if not ctrl.size == treat.size == np.asarray(clusters).size:
        raise ValueError("control, treatment and clusters must all be the same length")

    diffs = treat - ctrl
    _, members = _grouped_indices(clusters)
    n_clusters = len(members)

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, n_clusters, size=(n_resamples, n_clusters))

    replicates = np.empty(n_resamples, dtype=np.float64)
    for r in range(n_resamples):
        picked = np.concatenate([members[g] for g in draws[r]])
        replicates[r] = diffs[picked].mean()

    tail = (1.0 - confidence) / 2.0
    ci_low, ci_high = np.quantile(replicates, (tail, 1.0 - tail))

    return ClusterBootstrapResult(
        point_estimate=float(diffs.mean()),
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        standard_error=float(replicates.std(ddof=1)) if n_resamples > 1 else 0.0,
        confidence=confidence,
        n_clusters=n_clusters,
        n_items=int(diffs.size),
        n_resamples=n_resamples,
    )


def _validated_group(
    values: npt.ArrayLike, clusters: npt.ArrayLike, name: str
) -> tuple[npt.NDArray[np.float64], list[npt.NDArray[np.intp]]]:
    """One group's values and its cluster membership, or a refusal."""
    vals = np.asarray(values, dtype=np.float64)
    if vals.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {vals.shape}")
    if vals.size != np.asarray(clusters).size:
        raise ValueError(
            f"{name} and {name}_clusters must be the same length, got "
            f"{vals.size} and {np.asarray(clusters).size}"
        )
    _, members = _grouped_indices(clusters)
    if len(members) < 2:
        raise ValueError(
            f"{name} falls in a single cluster. Resampling one cluster returns the same "
            "items every replicate, so that group contributes no width and the interval "
            "reads as certainty about it rather than as one cluster."
        )
    return vals, members


def cluster_bootstrap_two_sample(
    control: npt.ArrayLike,
    control_clusters: npt.ArrayLike,
    treatment: npt.ArrayLike,
    treatment_clusters: npt.ArrayLike,
    *,
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int | None = None,
) -> TwoSampleClusterBootstrapResult:
    """Percentile bootstrap CI for an **unpaired** difference of two clustered means.

    Each group is resampled independently: whole clusters are drawn with
    replacement from within the group, all their items come along, and the
    replicate is the difference of the two resampled means. That is what
    propagates both groups' within-cluster correlation into one interval on the
    difference.

    Values are passed immediately before their own cluster labels rather than
    with the two label arrays at the end, because the failure this signature is
    guarding against is a caller handing group B's labels to group A. Adjacency
    makes that visible at the call site; a trailing pair of label arguments does
    not.

    Args:
        control: Per-item values for the first group.
        control_clusters: Per-item cluster label for the first group.
        treatment: Per-item values for the second group. **Need not be the same
            length as** ``control`` — that is the whole point of this function.
        treatment_clusters: Per-item cluster label for the second group. Labels
            are namespaced by group internally, so the two groups may reuse the
            same label values without being merged.
        confidence: Nominal coverage. Must lie strictly between 0 and 1.
        n_resamples: Bootstrap replicates.
        seed: Seed for reproducibility. A report that moves between two readings
            of the same checkpoint is not a report.

    Returns:
        A :class:`TwoSampleClusterBootstrapResult`.

    Raises:
        ValueError: on mismatched lengths within a group, empty input,
            ``n_resamples < 1``, a ``confidence`` outside ``(0, 1)``, or a group
            holding fewer than two clusters.

    Note:
        The interval is a percentile interval on clusters, so its coverage is
        governed by the **number of clusters**, not the number of items. At 24
        and 16 triples the realised coverage is measured rather than assumed —
        see the coverage simulation in ``tests/unit/test_group_estimators.py``.
    """
    if n_resamples < 1:
        raise ValueError(f"n_resamples must be >= 1, got {n_resamples}")
    if not 0.0 < confidence < 1.0:
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")

    ctrl, members_ctrl = _validated_group(control, control_clusters, "control")
    treat, members_treat = _validated_group(treatment, treatment_clusters, "treatment")
    k_ctrl, k_treat = len(members_ctrl), len(members_treat)

    rng = np.random.default_rng(seed)
    draws_ctrl = rng.integers(0, k_ctrl, size=(n_resamples, k_ctrl))
    draws_treat = rng.integers(0, k_treat, size=(n_resamples, k_treat))

    replicates = np.empty(n_resamples, dtype=np.float64)
    for r in range(n_resamples):
        picked_ctrl = np.concatenate([members_ctrl[g] for g in draws_ctrl[r]])
        picked_treat = np.concatenate([members_treat[g] for g in draws_treat[r]])
        replicates[r] = treat[picked_treat].mean() - ctrl[picked_ctrl].mean()

    tail = (1.0 - confidence) / 2.0
    ci_low, ci_high = np.quantile(replicates, (tail, 1.0 - tail))

    # The ICC is computed on values centred within their own group, and the
    # clusters are renumbered so that a label shared by both groups is two
    # clusters rather than one. Skipping either step reports the difference
    # between the groups as agreement inside them, which would inflate the
    # design effect exactly when the effect being measured is largest.
    centred = np.concatenate([ctrl - ctrl.mean(), treat - treat.mean()])
    codes = np.empty(centred.size, dtype=np.intp)
    for g, member in enumerate(members_ctrl):
        codes[member] = g
    for g, member in enumerate(members_treat):
        codes[member + ctrl.size] = k_ctrl + g

    n_items = int(ctrl.size + treat.size)
    icc = intraclass_correlation(centred, codes)
    mean_cluster_size = n_items / (k_ctrl + k_treat)
    return TwoSampleClusterBootstrapResult(
        point_estimate=float(treat.mean() - ctrl.mean()),
        mean_control=float(ctrl.mean()),
        mean_treatment=float(treat.mean()),
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        standard_error=float(replicates.std(ddof=1)) if n_resamples > 1 else 0.0,
        confidence=confidence,
        n_clusters_control=k_ctrl,
        n_clusters_treatment=k_treat,
        n_items_control=int(ctrl.size),
        n_items_treatment=int(treat.size),
        n_resamples=n_resamples,
        icc=icc,
        design_effect=design_effect(mean_cluster_size, icc),
        effective_n=effective_sample_size(n_items, mean_cluster_size, icc),
    )


def intraclass_correlation(values: npt.ArrayLike, clusters: npt.ArrayLike) -> float:
    """One-way random-effects intraclass correlation, ICC(1).

    Computed from the between- and within-cluster mean squares with the
    unequal-size correction ``m0``. Negative estimates — which arise when
    between-cluster variance is smaller than chance — are clamped to zero, since
    a negative correlation is not meaningful as a variance-inflation input.

    Args:
        values: Per-item values, typically the paired difference.
        clusters: Per-item cluster label.

    Returns:
        ICC in ``[0, 1]``. Returns ``0.0`` when every cluster holds one item, as
        there is then no within-cluster variance to estimate.

    Raises:
        ValueError: If fewer than two clusters are present, or lengths differ.
    """
    vals = np.asarray(values, dtype=np.float64)
    if vals.ndim != 1:
        raise ValueError("values must be one-dimensional")
    if vals.size != np.asarray(clusters).size:
        raise ValueError("values and clusters must be the same length")

    _, members = _grouped_indices(clusters)
    k = len(members)
    if k < 2:
        raise ValueError(f"intraclass correlation needs at least 2 clusters, got {k}")

    n_total = vals.size
    sizes = np.array([m.size for m in members], dtype=np.float64)
    if n_total == k:
        # Every cluster is a singleton: within-cluster variance is undefined.
        return 0.0

    grand_mean = float(vals.mean())
    cluster_means = np.array([vals[m].mean() for m in members], dtype=np.float64)

    ss_between = float(np.sum(sizes * (cluster_means - grand_mean) ** 2))
    ss_within = float(sum(np.sum((vals[m] - vals[m].mean()) ** 2) for m in members))

    ms_between = ss_between / (k - 1)
    ms_within = ss_within / (n_total - k)

    m0 = (n_total - float(np.sum(sizes**2)) / n_total) / (k - 1)
    denominator = ms_between + (m0 - 1.0) * ms_within
    if denominator <= 0.0:
        return 0.0

    icc = (ms_between - ms_within) / denominator
    return float(min(max(icc, 0.0), 1.0))


def design_effect(mean_cluster_size: float, icc: float) -> float:
    """Variance inflation from clustering: ``1 + (m - 1) * ICC``.

    Args:
        mean_cluster_size: Average items per cluster. Must be >= 1.
        icc: Intraclass correlation in ``[0, 1]``.

    Returns:
        The design effect, always >= 1.0.

    Raises:
        ValueError: If ``mean_cluster_size < 1`` or ``icc`` is outside ``[0, 1]``.
    """
    if mean_cluster_size < 1.0:
        raise ValueError(f"mean_cluster_size must be >= 1, got {mean_cluster_size}")
    if not 0.0 <= icc <= 1.0:
        raise ValueError(f"icc must be in [0, 1], got {icc}")
    return 1.0 + (mean_cluster_size - 1.0) * icc


def effective_sample_size(n_items: int, mean_cluster_size: float, icc: float) -> float:
    """Items divided by the design effect — the sample size that actually counts.

    Args:
        n_items: Total items.
        mean_cluster_size: Average items per cluster.
        icc: Intraclass correlation.

    Returns:
        Effective sample size, never greater than ``n_items``.

    Raises:
        ValueError: If ``n_items < 1``, or via :func:`design_effect`.
    """
    if n_items < 1:
        raise ValueError(f"n_items must be >= 1, got {n_items}")
    return n_items / design_effect(mean_cluster_size, icc)
