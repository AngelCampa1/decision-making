"""Sample-size planning for paired binary experiments.

Two questions this answers before any model call is made:

*How many items do I need?* — :func:`required_pairs`.
*Given what I can afford, what is the smallest effect I could detect?* —
:func:`minimum_detectable_effect`.

The second is the one that actually governs the project. Subscription rate
limits cap the item count, so the honest move is to compute the minimum
detectable effect up front and write it into the pre-registration. If the MDE
exceeds the effect we plausibly expect, the run is not worth making — that is a
decision to take before spending the budget, not after seeing a null.

Clustering enters through the design effect: templates, not items, are the
independent unit, so the required count is inflated accordingly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from scipy import stats

Alternative = Literal["two-sided", "greater"]

_MAX_PAIRS = 10_000_000


@dataclass(frozen=True, slots=True)
class PowerResult:
    """A sample-size or minimum-detectable-effect calculation.

    Attributes:
        n_pairs: Item pairs required (or assumed, for an MDE calculation), after
            inflation by the design effect.
        n_pairs_unadjusted: The same figure before clustering inflation.
        effect: Accuracy difference ``p01 - p10`` targeted or detectable.
        p_discordant: Assumed probability that a pair is discordant. This is the
            hard input to guess; take it from the screening run rather than
            inventing it.
        alpha: Type I error rate.
        power: Target power.
        design_effect: Clustering inflation factor applied.
        alternative: Directionality of the test.
    """

    n_pairs: int
    n_pairs_unadjusted: int
    effect: float
    p_discordant: float
    alpha: float
    power: float
    design_effect: float
    alternative: Alternative


def _z_scores(alpha: float, power: float, alternative: Alternative) -> tuple[float, float]:
    """Critical values for the given error rates and directionality."""
    tail = alpha / 2.0 if alternative == "two-sided" else alpha
    return float(stats.norm.ppf(1.0 - tail)), float(stats.norm.ppf(power))


def _validate_common(
    p_discordant: float, alpha: float, power: float, design_effect: float, alternative: str
) -> Alternative:
    if not 0.0 < p_discordant <= 1.0:
        raise ValueError(f"p_discordant must be in (0, 1], got {p_discordant}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must be in (0, 1), got {power}")
    if design_effect < 1.0:
        raise ValueError(f"design_effect must be >= 1, got {design_effect}")
    if alternative not in ("two-sided", "greater"):
        raise ValueError(f"alternative must be 'two-sided' or 'greater', got {alternative!r}")
    return alternative  # type: ignore[return-value]


def required_pairs(
    effect: float,
    p_discordant: float,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
    design_effect: float = 1.0,
    alternative: str = "greater",
) -> PowerResult:
    """Item pairs needed to detect a given accuracy difference with McNemar's test.

    Uses Connor's normal approximation for the paired binary design::

        n = [z_a * sqrt(p_d) + z_b * sqrt(p_d - effect^2)]^2 / effect^2

    where ``p_d`` is the discordant-pair probability. The result is then
    multiplied by the design effect and rounded up.

    Args:
        effect: Accuracy difference to detect, ``p01 - p10``. Must be non-zero
            and no larger in magnitude than ``p_discordant``.
        p_discordant: Probability a pair is discordant. Estimate this from the
            screening run; it is the input people most often guess wrong, and
            underestimating it silently underpowers the study.
        alpha: Type I error rate.
        power: Target power.
        design_effect: Clustering inflation from
            :func:`~decision_evals.stats.cluster.design_effect`.
        alternative: ``"greater"`` for the pre-registered directional test.

    Returns:
        A :class:`PowerResult`.

    Raises:
        ValueError: On an invalid probability, a zero effect, or an effect whose
            magnitude exceeds ``p_discordant`` (which is impossible, since the
            difference of two counts cannot exceed their sum).
    """
    alt = _validate_common(p_discordant, alpha, power, design_effect, alternative)
    if effect == 0.0:
        raise ValueError("effect must be non-zero")
    if abs(effect) > p_discordant:
        raise ValueError(
            f"|effect| ({abs(effect)}) cannot exceed p_discordant ({p_discordant}): "
            "the difference of the discordant counts is bounded by their sum"
        )

    z_alpha, z_beta = _z_scores(alpha, power, alt)
    numerator = (z_alpha * p_discordant**0.5 + z_beta * (p_discordant - effect**2) ** 0.5) ** 2
    unadjusted = numerator / effect**2
    return PowerResult(
        n_pairs=math.ceil(unadjusted * design_effect),
        n_pairs_unadjusted=math.ceil(unadjusted),
        effect=effect,
        p_discordant=p_discordant,
        alpha=alpha,
        power=power,
        design_effect=design_effect,
        alternative=alt,
    )


def minimum_detectable_effect(
    n_pairs: int,
    p_discordant: float,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
    design_effect: float = 1.0,
    alternative: str = "greater",
    tolerance: float = 1e-9,
) -> PowerResult:
    """Smallest accuracy difference detectable at a given item count.

    Inverts :func:`required_pairs` by bisection, since the effect appears on both
    sides of the sample-size formula. Required pairs decrease monotonically in
    the effect size, which makes the bisection well-posed.

    Args:
        n_pairs: Item pairs available, after any clustering inflation is
            accounted for by ``design_effect``.
        p_discordant: Probability a pair is discordant.
        alpha: Type I error rate.
        power: Target power.
        design_effect: Clustering inflation factor.
        alternative: ``"greater"`` for the pre-registered directional test.
        tolerance: Bisection convergence width on the effect.

    Returns:
        A :class:`PowerResult` whose ``effect`` is the MDE.

    Raises:
        ValueError: On invalid probabilities, ``n_pairs < 1``, a non-positive
            ``tolerance``, or a sample too small to detect any effect at all —
            which is itself the useful answer, and says do not run this study.
    """
    alt = _validate_common(p_discordant, alpha, power, design_effect, alternative)
    if n_pairs < 1:
        raise ValueError(f"n_pairs must be >= 1, got {n_pairs}")
    if tolerance <= 0.0:
        raise ValueError(f"tolerance must be positive, got {tolerance}")

    def needed(effect: float) -> int:
        return required_pairs(
            effect,
            p_discordant,
            alpha=alpha,
            power=power,
            design_effect=design_effect,
            alternative=alt,
        ).n_pairs

    # The largest admissible effect is p_discordant itself. If even that cannot
    # be detected at this sample size, no effect can be.
    upper = p_discordant
    if needed(upper) > n_pairs:
        raise ValueError(
            f"n_pairs={n_pairs} cannot detect any effect at alpha={alpha}, power={power}, "
            f"p_discordant={p_discordant}. Increase the item count or accept lower power."
        )

    lower = 0.0
    while upper - lower > tolerance:
        midpoint = (lower + upper) / 2.0
        if midpoint <= 0.0 or needed(midpoint) > n_pairs:
            lower = midpoint
        else:
            upper = midpoint

    return PowerResult(
        n_pairs=n_pairs,
        n_pairs_unadjusted=math.ceil(n_pairs / design_effect),
        effect=upper,
        p_discordant=p_discordant,
        alpha=alpha,
        power=power,
        design_effect=design_effect,
        alternative=alt,
    )
