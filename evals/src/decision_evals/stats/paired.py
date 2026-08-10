"""Paired significance tests for skill-on vs skill-off comparisons.

Both arms see the *same* items, so the comparison is paired and the appropriate
tests condition on that pairing. Treating the two arms as independent samples
throws away the pairing and inflates the standard error, which is the most
common statistical error in prompt A/B writeups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy import stats

Alternative = Literal["two-sided", "greater", "less"]

_ALTERNATIVES: frozenset[str] = frozenset({"two-sided", "greater", "less"})


@dataclass(frozen=True, slots=True)
class McNemarResult:
    """Outcome of McNemar's exact test on paired binary results.

    Attributes:
        n_pairs: Total paired observations.
        n_discordant: Pairs where the two arms disagreed. Only these carry
            information; concordant pairs are uninformative by construction.
        treatment_wins: Pairs where control was wrong and treatment was right.
        control_wins: Pairs where control was right and treatment was wrong.
        p_value: Exact binomial p-value on the discordant pairs.
        proportion_difference: ``(treatment_wins - control_wins) / n_pairs`` —
            the accuracy difference, identical to ``acc_treatment - acc_control``.
        alternative: Which alternative hypothesis was tested.
    """

    n_pairs: int
    n_discordant: int
    treatment_wins: int
    control_wins: int
    p_value: float
    proportion_difference: float
    alternative: Alternative


@dataclass(frozen=True, slots=True)
class PermutationResult:
    """Outcome of a paired permutation (randomisation) test on differences."""

    n_pairs: int
    observed_mean_difference: float
    p_value: float
    n_resamples: int
    alternative: Alternative


def _as_bool_array(values: npt.ArrayLike, name: str) -> npt.NDArray[np.bool_]:
    """Coerce to a 1-D boolean array, rejecting anything not 0/1-valued."""
    arr = np.asarray(values)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {arr.shape}")
    if arr.size == 0:
        raise ValueError(f"{name} must not be empty")
    if arr.dtype != np.bool_:
        if not np.isin(arr, (0, 1)).all():
            raise ValueError(f"{name} must contain only booleans or 0/1 values")
        arr = arr.astype(np.bool_)
    return arr


def _validate_alternative(alternative: str) -> Alternative:
    if alternative not in _ALTERNATIVES:
        raise ValueError(f"alternative must be one of {sorted(_ALTERNATIVES)}, got {alternative!r}")
    return alternative  # type: ignore[return-value]


def mcnemar_exact(
    control: npt.ArrayLike,
    treatment: npt.ArrayLike,
    *,
    alternative: str = "greater",
) -> McNemarResult:
    """Run McNemar's exact test on paired binary outcomes.

    The exact test is a binomial test on the discordant pairs under
    ``H0: P(treatment wins | discordant) = 0.5``. It is preferred over the
    chi-squared approximation here because our discordant counts are routinely
    small enough for the approximation to misbehave.

    Args:
        control: Per-item correctness for the control arm (skill off).
        treatment: Per-item correctness for the treatment arm (skill on), in the
            same item order as ``control``.
        alternative: ``"greater"`` (default) tests that treatment beats control,
            which is the directional hypothesis we pre-register. ``"two-sided"``
            and ``"less"`` are also available.

    Returns:
        A :class:`McNemarResult`.

    Raises:
        ValueError: If the arrays differ in length, are empty, are not
            one-dimensional, or contain values other than booleans/0/1.

    Note:
        With no discordant pairs the test has no information and returns
        ``p_value=1.0``. That is the correct conservative answer, not a defect.
    """
    alt = _validate_alternative(alternative)
    ctrl = _as_bool_array(control, "control")
    treat = _as_bool_array(treatment, "treatment")
    if ctrl.size != treat.size:
        raise ValueError(
            f"control and treatment must be the same length, got {ctrl.size} and {treat.size}"
        )

    treatment_wins = int(np.sum(~ctrl & treat))
    control_wins = int(np.sum(ctrl & ~treat))
    n_discordant = treatment_wins + control_wins
    n_pairs = int(ctrl.size)

    if n_discordant == 0:
        p_value = 1.0
    else:
        p_value = float(stats.binomtest(treatment_wins, n_discordant, 0.5, alternative=alt).pvalue)

    return McNemarResult(
        n_pairs=n_pairs,
        n_discordant=n_discordant,
        treatment_wins=treatment_wins,
        control_wins=control_wins,
        p_value=p_value,
        proportion_difference=(treatment_wins - control_wins) / n_pairs,
        alternative=alt,
    )


def paired_permutation_test(
    control: npt.ArrayLike,
    treatment: npt.ArrayLike,
    *,
    alternative: str = "greater",
    n_resamples: int = 10_000,
    seed: int | None = None,
) -> PermutationResult:
    """Paired randomisation test on continuous per-item differences.

    Used where the outcome is not binary — Brier scores, token counts, latency.
    Under H0 the sign of each paired difference is exchangeable, so we flip signs
    at random and count how often the resampled mean is at least as extreme as
    the observed one.

    Args:
        control: Per-item values for the control arm.
        treatment: Per-item values for the treatment arm, same item order.
        alternative: ``"greater"`` tests that the treatment mean exceeds control.
        n_resamples: Number of sign-flip resamples.
        seed: Seed for reproducibility. Runs are recorded in the run config.

    Returns:
        A :class:`PermutationResult`.

    Raises:
        ValueError: On mismatched lengths, empty input, or ``n_resamples < 1``.

    Note:
        The p-value uses the ``(hits + 1) / (n + 1)`` correction, so it is never
        zero. Reporting ``p = 0`` from a resampling test is a category error: the
        test can only bound the p-value by its resampling resolution.
    """
    alt = _validate_alternative(alternative)
    if n_resamples < 1:
        raise ValueError(f"n_resamples must be >= 1, got {n_resamples}")

    ctrl = np.asarray(control, dtype=np.float64)
    treat = np.asarray(treatment, dtype=np.float64)
    if ctrl.ndim != 1 or treat.ndim != 1:
        raise ValueError("control and treatment must be one-dimensional")
    if ctrl.size == 0:
        raise ValueError("control and treatment must not be empty")
    if ctrl.size != treat.size:
        raise ValueError(
            f"control and treatment must be the same length, got {ctrl.size} and {treat.size}"
        )

    diffs = treat - ctrl
    observed = float(np.mean(diffs))

    rng = np.random.default_rng(seed)
    signs = rng.choice((-1.0, 1.0), size=(n_resamples, diffs.size))
    resampled = (signs * diffs).mean(axis=1)

    if alt == "greater":
        hits = int(np.sum(resampled >= observed))
    elif alt == "less":
        hits = int(np.sum(resampled <= observed))
    else:
        hits = int(np.sum(np.abs(resampled) >= abs(observed)))

    return PermutationResult(
        n_pairs=int(diffs.size),
        observed_mean_difference=observed,
        p_value=(hits + 1) / (n_resamples + 1),
        n_resamples=n_resamples,
        alternative=alt,
    )
