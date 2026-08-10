"""False discovery rate control across the pre-registered family of skills.

Five skills means five primary tests. Testing each at α = 0.05 gives roughly a
23% chance of at least one false positive, which would be exactly the kind of
unadjusted-comparison problem this project is positioned against.

Benjamini-Hochberg is used rather than Bonferroni: with five hypotheses in a
single family, controlling the *proportion* of false discoveries preserves far
more power than controlling the probability of *any* false discovery, and a
single spurious skill among several genuine ones is a tolerable error here.

Guards are deliberately excluded from correction. They are one-sided
non-inferiority tests in the conservative direction, so adjusting them upward
would make it *easier* for a harmful skill to pass its guard — the correction
would work against safety rather than for it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True, slots=True)
class BenjaminiHochbergResult:
    """Adjusted p-values and rejection flags for a family of tests.

    Attributes:
        p_values: The input p-values, in input order.
        q_values: BH-adjusted p-values, in input order. Monotone in the sorted
            p-values and never smaller than the corresponding raw p-value.
        rejected: Whether each hypothesis is rejected at the given ``q``.
        q: The FDR level applied.
        n_tests: Family size.
        n_rejected: Count of rejections.
    """

    p_values: tuple[float, ...]
    q_values: tuple[float, ...]
    rejected: tuple[bool, ...]
    q: float
    n_tests: int
    n_rejected: int


def benjamini_hochberg(p_values: npt.ArrayLike, *, q: float = 0.10) -> BenjaminiHochbergResult:
    """Control the false discovery rate across a family of tests.

    Args:
        p_values: Raw p-values, one per hypothesis in the pre-registered family.
        q: Target false discovery rate. The protocol uses 0.10. Must lie in
            ``(0, 1]``.

    Returns:
        A :class:`BenjaminiHochbergResult` whose ``q_values`` match
        ``statsmodels.stats.multitest.multipletests(method="fdr_bh")``, asserted
        directly in the test suite.

    Raises:
        ValueError: If ``p_values`` is empty or not one-dimensional, contains a
            value outside ``[0, 1]``, or ``q`` is outside ``(0, 1]``.
    """
    if not 0.0 < q <= 1.0:
        raise ValueError(f"q must be in (0, 1], got {q}")

    p = np.asarray(p_values, dtype=np.float64)
    if p.ndim != 1:
        raise ValueError(f"p_values must be one-dimensional, got shape {p.shape}")
    if p.size == 0:
        raise ValueError("p_values must not be empty")
    if np.any(p < 0.0) or np.any(p > 1.0):
        raise ValueError("p_values must lie in [0, 1]")

    n = p.size
    order = np.argsort(p, kind="stable")
    ranks = np.arange(1, n + 1, dtype=np.float64)

    # Step up from the largest p-value, taking a running minimum so the adjusted
    # values stay monotone in the sorted p-values.
    scaled = p[order] * n / ranks
    adjusted_sorted = np.minimum.accumulate(scaled[::-1])[::-1]
    np.clip(adjusted_sorted, 0.0, 1.0, out=adjusted_sorted)

    adjusted = np.empty(n, dtype=np.float64)
    adjusted[order] = adjusted_sorted
    rejected = adjusted <= q

    return BenjaminiHochbergResult(
        p_values=tuple(float(v) for v in p),
        q_values=tuple(float(v) for v in adjusted),
        rejected=tuple(bool(v) for v in rejected),
        q=q,
        n_tests=int(n),
        n_rejected=int(np.count_nonzero(rejected)),
    )
