"""Proper scoring rules and calibration measures for probability forecasts.

The central object is the Murphy decomposition, ``Brier = Reliability −
Resolution + Uncertainty``, because it separates two things that a single Brier
score conflates:

*Reliability* asks whether stated confidence matches observed frequency.
*Resolution* asks whether the forecasts discriminate at all.

A forecaster that always predicts the base rate is perfectly reliable and
completely useless — reliability 0, resolution 0. Without the decomposition, a
"skill" that improves Brier purely by shrinking every forecast toward the base
rate looks like a win. It is hedging, and the resolution term is what exposes it.
That is why the pre-registered guard for the forecasting skill is a floor on
resolution, not just a target on Brier.

Estimation of calibration error itself is handled by a kernel-smoothed
estimator. Classic binned ECE is provided, but it is bin-count dependent and
biased at small n, so it is reported as a secondary alongside the reliability
diagram rather than used as a primary metric.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

# Below this, two float forecasts are treated as the same predicted value when
# grouping for the exact decomposition.
_GROUPING_DECIMALS = 12


@dataclass(frozen=True, slots=True)
class MurphyDecomposition:
    """Exact three-way decomposition of the Brier score.

    Grouping is by *unique forecast value* rather than by histogram bin, which
    makes the identity hold to floating-point precision and turns it into a
    property test. Binned variants only satisfy it up to a within-bin variance
    term.

    Attributes:
        brier: Mean squared error of the forecasts.
        reliability: Calibration penalty; lower is better.
        resolution: Discrimination credit; higher is better.
        uncertainty: Irreducible base-rate variance ``o(1 - o)``. A property of
            the question set, not of the forecaster.
        base_rate: Observed outcome frequency.
        n_groups: Distinct forecast values.
        n_forecasts: Total forecasts.
    """

    brier: float
    reliability: float
    resolution: float
    uncertainty: float
    base_rate: float
    n_groups: int
    n_forecasts: int

    @property
    def identity_residual(self) -> float:
        """``brier - (reliability - resolution + uncertainty)``; ~0 by construction."""
        return self.brier - (self.reliability - self.resolution + self.uncertainty)

    @property
    def skill_score(self) -> float:
        """Brier skill score against the always-predict-base-rate reference.

        Returns 0.0 when uncertainty is zero (every outcome identical), since no
        forecaster can improve on the constant prediction in that case.
        """
        if self.uncertainty == 0.0:
            return 0.0
        return 1.0 - self.brier / self.uncertainty


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    """One bin of a reliability diagram."""

    lower: float
    upper: float
    count: int
    mean_forecast: float
    observed_frequency: float


def _validate(
    forecasts: npt.ArrayLike, outcomes: npt.ArrayLike
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Coerce and check a forecast/outcome pair."""
    f = np.asarray(forecasts, dtype=np.float64)
    o = np.asarray(outcomes, dtype=np.float64)
    if f.ndim != 1 or o.ndim != 1:
        raise ValueError("forecasts and outcomes must be one-dimensional")
    if f.size == 0:
        raise ValueError("forecasts and outcomes must not be empty")
    if f.size != o.size:
        raise ValueError(
            f"forecasts and outcomes must be the same length, got {f.size} and {o.size}"
        )
    if np.any(f < 0.0) or np.any(f > 1.0):
        raise ValueError("forecasts must lie in [0, 1]")
    if not np.isin(o, (0.0, 1.0)).all():
        raise ValueError("outcomes must be binary (0 or 1)")
    return f, o


def brier_score(forecasts: npt.ArrayLike, outcomes: npt.ArrayLike) -> float:
    """Mean squared error of probability forecasts against binary outcomes.

    Args:
        forecasts: Predicted probabilities in ``[0, 1]``.
        outcomes: Realised binary outcomes.

    Returns:
        Brier score in ``[0, 1]``; lower is better. An uninformative 0.5 forecast
        on a balanced question set scores 0.25.

    Raises:
        ValueError: On empty, mismatched, out-of-range, or non-binary input.
    """
    f, o = _validate(forecasts, outcomes)
    return float(np.mean((f - o) ** 2))


def log_score(
    forecasts: npt.ArrayLike, outcomes: npt.ArrayLike, *, epsilon: float = 1e-15
) -> float:
    """Mean negative log-likelihood of the realised outcomes.

    Reported alongside Brier because it punishes confident errors far more
    harshly. A forecaster who says 0.99 and is wrong barely moves Brier but is
    heavily penalised here — which is the behaviour we want to surface.

    Args:
        forecasts: Predicted probabilities in ``[0, 1]``.
        outcomes: Realised binary outcomes.
        epsilon: Clipping bound keeping the score finite at exactly 0 or 1.
            Must be in ``(0, 0.5)``.

    Returns:
        Mean negative log score in nats; lower is better.

    Raises:
        ValueError: On invalid input or an ``epsilon`` outside ``(0, 0.5)``.
    """
    if not 0.0 < epsilon < 0.5:
        raise ValueError(f"epsilon must be in (0, 0.5), got {epsilon}")
    f, o = _validate(forecasts, outcomes)
    clipped = np.clip(f, epsilon, 1.0 - epsilon)
    return float(-np.mean(o * np.log(clipped) + (1.0 - o) * np.log(1.0 - clipped)))


def murphy_decomposition(forecasts: npt.ArrayLike, outcomes: npt.ArrayLike) -> MurphyDecomposition:
    """Decompose the Brier score into reliability, resolution and uncertainty.

    Args:
        forecasts: Predicted probabilities in ``[0, 1]``.
        outcomes: Realised binary outcomes.

    Returns:
        A :class:`MurphyDecomposition` satisfying
        ``brier == reliability - resolution + uncertainty`` to floating-point
        precision.

    Raises:
        ValueError: On empty, mismatched, out-of-range, or non-binary input.
    """
    f, o = _validate(forecasts, outcomes)
    n = f.size
    base_rate = float(o.mean())

    # Grouping by unique value is what makes the identity exact. Rounding first
    # keeps forecasts that differ only by float noise in the same group.
    keys, inverse = np.unique(np.round(f, _GROUPING_DECIMALS), return_inverse=True)
    inverse = inverse.ravel()
    counts = np.bincount(inverse).astype(np.float64)
    group_outcome = np.bincount(inverse, weights=o) / counts
    group_forecast = np.bincount(inverse, weights=f) / counts

    reliability = float(np.sum(counts * (group_forecast - group_outcome) ** 2) / n)
    resolution = float(np.sum(counts * (group_outcome - base_rate) ** 2) / n)
    uncertainty = base_rate * (1.0 - base_rate)

    return MurphyDecomposition(
        brier=float(np.mean((f - o) ** 2)),
        reliability=reliability,
        resolution=resolution,
        uncertainty=uncertainty,
        base_rate=base_rate,
        n_groups=int(keys.size),
        n_forecasts=int(n),
    )


def reliability_curve(
    forecasts: npt.ArrayLike, outcomes: npt.ArrayLike, *, n_bins: int = 10
) -> list[CalibrationBin]:
    """Bin forecasts into a reliability diagram.

    Bins are equal-width over ``[0, 1]`` and the top bin is closed so that a
    forecast of exactly 1.0 is included rather than silently dropped. Empty bins
    are omitted.

    Args:
        forecasts: Predicted probabilities in ``[0, 1]``.
        outcomes: Realised binary outcomes.
        n_bins: Number of equal-width bins. Must be >= 1.

    Returns:
        Non-empty bins in ascending order.

    Raises:
        ValueError: On invalid input or ``n_bins < 1``.
    """
    if n_bins < 1:
        raise ValueError(f"n_bins must be >= 1, got {n_bins}")
    f, o = _validate(forecasts, outcomes)

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    assignment = np.clip(np.digitize(f, edges[1:-1], right=False), 0, n_bins - 1)

    bins: list[CalibrationBin] = []
    for b in range(n_bins):
        mask = assignment == b
        count = int(np.count_nonzero(mask))
        if count == 0:
            continue
        bins.append(
            CalibrationBin(
                lower=float(edges[b]),
                upper=float(edges[b + 1]),
                count=count,
                mean_forecast=float(f[mask].mean()),
                observed_frequency=float(o[mask].mean()),
            )
        )
    return bins


def expected_calibration_error(
    forecasts: npt.ArrayLike, outcomes: npt.ArrayLike, *, n_bins: int = 10
) -> float:
    """Classic binned ECE: count-weighted mean ``|confidence - accuracy|``.

    Provided for comparability with prior work, and reported as a secondary
    metric only. ECE is sensitive to the bin count and biased upward at small
    sample sizes, which is why :func:`smooth_calibration_error` is preferred for
    headline numbers.

    Args:
        forecasts: Predicted probabilities in ``[0, 1]``.
        outcomes: Realised binary outcomes.
        n_bins: Number of equal-width bins.

    Returns:
        ECE in ``[0, 1]``; lower is better.

    Raises:
        ValueError: On invalid input or ``n_bins < 1``.
    """
    f, _ = _validate(forecasts, outcomes)
    bins = reliability_curve(forecasts, outcomes, n_bins=n_bins)
    total = float(f.size)
    return float(sum(b.count / total * abs(b.mean_forecast - b.observed_frequency) for b in bins))


def smooth_calibration_error(
    forecasts: npt.ArrayLike,
    outcomes: npt.ArrayLike,
    *,
    bandwidth: float | None = None,
) -> float:
    """Kernel-smoothed calibration error, a debiased alternative to binned ECE.

    Replaces hard binning with a Gaussian-kernel (Nadaraya-Watson) estimate of
    the observed frequency as a function of the stated probability, then reports
    the mean absolute gap between the two. Removing the bin-edge discontinuity
    removes ECE's dependence on an arbitrary bin count.

    Args:
        forecasts: Predicted probabilities in ``[0, 1]``.
        outcomes: Realised binary outcomes.
        bandwidth: Kernel bandwidth. Defaults to ``n ** (-1/3)`` clipped to
            ``[0.01, 0.25]`` — the usual rate for this class of estimator, with
            bounds that keep it from degenerating on very small or very large
            samples. Must be positive when given explicitly.

    Returns:
        Smoothed calibration error in ``[0, 1]``; lower is better.

    Raises:
        ValueError: On invalid input or a non-positive ``bandwidth``.

    Note:
        This is an estimator with a tuning parameter, not a canonical quantity.
        The bandwidth actually used is recorded in the run config so a reported
        number can be reproduced exactly.
    """
    f, o = _validate(forecasts, outcomes)
    n = f.size

    if bandwidth is None:
        bandwidth = float(np.clip(n ** (-1.0 / 3.0), 0.01, 0.25))
    elif bandwidth <= 0.0:
        raise ValueError(f"bandwidth must be positive, got {bandwidth}")

    # Nadaraya-Watson: weight every observation by its kernel distance to the
    # evaluation point. Self-weight is 1, so a lone point returns its own
    # outcome and the estimator degrades gracefully rather than dividing by zero.
    distances = (f[:, None] - f[None, :]) / bandwidth
    weights = np.exp(-0.5 * distances**2)
    smoothed = (weights @ o) / weights.sum(axis=1)

    return float(np.mean(np.abs(smoothed - f)))
