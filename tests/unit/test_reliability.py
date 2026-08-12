"""Aptitude, unreliability, and what repeats actually buy.

The case that matters most here is the one the whole module exists for: two
score sets with the *same mean* and different spreads must come back different.
A test suite that only checked means would pass against an implementation that
silently returned the mean twice.
"""

from __future__ import annotations

import numpy as np
import pytest

from decision_evals.stats.reliability import (
    DEFAULT_HIGH,
    DEFAULT_LOW,
    aptitude_unreliability,
    per_item_reliability,
    repeat_reliability,
    repeats_for_reliability,
    repeats_for_scatter_precision,
)


class TestAptitudeUnreliability:
    """The arXiv:2505.06120 §4.2 estimator."""

    def test_matches_numpy_percentiles_directly(self) -> None:
        scores = [0.1, 0.4, 0.5, 0.55, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0]
        result = aptitude_unreliability(scores)
        low, high = np.percentile(scores, (DEFAULT_LOW, DEFAULT_HIGH))
        assert result.aptitude == pytest.approx(high)
        assert result.unreliability == pytest.approx(high - low)

    def test_defaults_are_the_papers_percentiles(self) -> None:
        """``A^90`` and ``U^90_10`` are the published names; the numbers follow."""
        assert (DEFAULT_LOW, DEFAULT_HIGH) == (10.0, 90.0)

    def test_a_constant_score_set_has_zero_unreliability(self) -> None:
        result = aptitude_unreliability([0.7] * 12)
        assert result.unreliability == pytest.approx(0.0)
        assert result.aptitude == pytest.approx(0.7)
        assert result.mean_score == pytest.approx(0.7)

    def test_same_mean_different_spread_is_the_whole_point(self) -> None:
        """A mean-only metric cannot tell these apart. This one must."""
        steady = aptitude_unreliability([0.5] * 10)
        scattered = aptitude_unreliability([0.0] * 5 + [1.0] * 5)
        assert steady.mean_score == pytest.approx(scattered.mean_score)
        assert scattered.unreliability > steady.unreliability

    def test_aptitude_ignores_a_collapse_in_the_worst_runs(self) -> None:
        """Best-case is meant to survive bad runs; that is why it is separate."""
        base = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
        collapsed = [0.0, 0.0, 0.0, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]
        assert aptitude_unreliability(collapsed).aptitude == pytest.approx(
            aptitude_unreliability(base).aptitude
        )
        assert aptitude_unreliability(collapsed).unreliability > 0.0

    def test_a_single_score_is_admissible_and_has_no_spread(self) -> None:
        result = aptitude_unreliability([0.42])
        assert result.n_scores == 1
        assert result.unreliability == pytest.approx(0.0)

    def test_custom_percentiles_are_recorded(self) -> None:
        result = aptitude_unreliability([0.0, 1.0], low=25.0, high=75.0)
        assert (result.low, result.high) == (25.0, 75.0)

    @pytest.mark.parametrize(
        ("low", "high", "message"),
        [
            (-1.0, 90.0, "low must be in"),
            (10.0, 101.0, "high must be in"),
            (90.0, 10.0, "strictly below"),
            (50.0, 50.0, "strictly below"),
        ],
    )
    def test_percentiles_are_validated(self, low: float, high: float, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            aptitude_unreliability([0.5], low=low, high=high)

    def test_empty_input_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            aptitude_unreliability([])

    def test_two_dimensional_input_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="one-dimensional"):
            aptitude_unreliability([[0.1, 0.2], [0.3, 0.4]])


class TestPerItemReliability:
    """Our per-item extension: scatter as a paired array."""

    def test_scatter_is_one_number_per_item_in_item_order(self) -> None:
        scores = [[0.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 1.0]]
        result = per_item_reliability(scores)
        assert result.scatter.shape == (2,)
        assert result.scatter[0] == pytest.approx(0.0)
        assert result.scatter[1] > 0.0

    def test_item_mean_is_the_ordinary_mean(self) -> None:
        result = per_item_reliability([[0.0, 1.0], [0.25, 0.75]])
        assert result.item_mean == pytest.approx([0.5, 0.5])

    def test_shape_is_reported(self) -> None:
        result = per_item_reliability(np.zeros((5, 3)))
        assert (result.n_items, result.n_repeats) == (5, 3)

    def test_perfectly_repeatable_items_have_icc_one(self) -> None:
        """Every repeat identical within an item, items differing: all variance between."""
        result = per_item_reliability([[0.1, 0.1, 0.1], [0.9, 0.9, 0.9]])
        assert result.icc == pytest.approx(1.0)

    def test_pure_noise_has_icc_at_the_floor(self) -> None:
        """Identical items scattering identically: nothing is between-item."""
        result = per_item_reliability([[0.0, 1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0]])
        assert result.icc == pytest.approx(0.0)

    def test_a_single_item_reports_icc_zero(self) -> None:
        """One cluster has no between-cluster term, so ICC is not estimable."""
        result = per_item_reliability([[0.0, 0.5, 1.0]])
        assert result.n_items == 1
        assert result.icc == 0.0
        assert result.scatter[0] > 0.0

    def test_one_repeat_is_refused_with_the_reason(self) -> None:
        """The design consequence, not a shape complaint."""
        with pytest.raises(ValueError, match="undefined, not merely imprecise"):
            per_item_reliability([[0.5], [0.7]])

    def test_a_one_dimensional_array_is_refused(self) -> None:
        with pytest.raises(ValueError, match="two-dimensional"):
            per_item_reliability([0.1, 0.2, 0.3])

    def test_zero_items_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least one item"):
            per_item_reliability(np.zeros((0, 3)))

    def test_percentiles_are_validated_here_too(self) -> None:
        with pytest.raises(ValueError, match="strictly below"):
            per_item_reliability([[0.0, 1.0]], low=90.0, high=10.0)

    def test_scatter_feeds_a_paired_test_unchanged(self) -> None:
        """The reason scatter is per-item: a skill that only steadies the model."""
        from decision_evals.stats.paired import paired_permutation_test

        rng = np.random.default_rng(20260811)
        control = rng.uniform(0.0, 1.0, size=(24, 8))
        # Same per-item mean, tighter around it.
        treatment = control.mean(axis=1, keepdims=True) + 0.1 * (
            control - control.mean(axis=1, keepdims=True)
        )

        off = per_item_reliability(control)
        on = per_item_reliability(treatment)
        assert on.item_mean == pytest.approx(off.item_mean)

        result = paired_permutation_test(
            off.scatter, on.scatter, alternative="less", n_resamples=2000, seed=7
        )
        assert result.p_value < 0.01


class TestRepeatReliability:
    """Spearman-Brown, and the count a mean outcome needs."""

    def test_one_repeat_is_the_single_measurement_icc(self) -> None:
        assert repeat_reliability(0.4, 1) == pytest.approx(0.4)

    def test_reliability_rises_with_repeats(self) -> None:
        values = [repeat_reliability(0.3, k) for k in (1, 2, 4, 8, 16)]
        assert values == sorted(values)
        assert all(0.0 <= v <= 1.0 for v in values)

    def test_zero_icc_stays_zero_however_many_repeats(self) -> None:
        assert repeat_reliability(0.0, 100) == pytest.approx(0.0)

    def test_perfect_icc_is_perfect_at_one_repeat(self) -> None:
        assert repeat_reliability(1.0, 1) == pytest.approx(1.0)

    @pytest.mark.parametrize(
        ("icc", "target"),
        [
            (0.25, 0.8),  # exact integer solution: k = 12 on the nose
            (0.3, 0.85),  # non-integer solution, so the ceil is genuinely needed
            (0.05, 0.9),
            (0.7, 0.95),
        ],
    )
    def test_round_trips_against_the_inverse(self, icc: float, target: float) -> None:
        """The returned count must be the *smallest* one that reaches the target.

        The exact-integer case is the one that caught a real defect: ``k`` came
        out as 12.000000000000002 and a bare ceil charged 13 repeats.
        """
        k = repeats_for_reliability(icc, target)
        assert repeat_reliability(icc, k) >= target
        assert repeat_reliability(icc, k - 1) < target

    def test_a_target_below_the_icc_needs_one_repeat(self) -> None:
        assert repeats_for_reliability(0.9, 0.5) == 1

    def test_zero_icc_can_never_reach_a_target(self) -> None:
        with pytest.raises(ValueError, match="no number of them reaches"):
            repeats_for_reliability(0.0, 0.8)

    @pytest.mark.parametrize("icc", [-0.01, 1.01])
    def test_icc_is_bounded(self, icc: float) -> None:
        with pytest.raises(ValueError, match=r"icc must be in \[0, 1\]"):
            repeat_reliability(icc, 2)

    def test_icc_is_bounded_on_the_inverse_too(self) -> None:
        with pytest.raises(ValueError, match=r"icc must be in \[0, 1\]"):
            repeats_for_reliability(1.5, 0.8)

    def test_repeat_count_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="n_repeats must be >= 1"):
            repeat_reliability(0.5, 0)

    @pytest.mark.parametrize("target", [0.0, 1.0, -0.5, 1.5])
    def test_target_must_be_strictly_inside_the_unit_interval(self, target: float) -> None:
        with pytest.raises(ValueError, match=r"target must be in \(0, 1\)"):
            repeats_for_reliability(0.5, target)


class TestRepeatsForScatterPrecision:
    """The count a *reliability* outcome needs, which is the different answer."""

    def test_matches_the_closed_form(self) -> None:
        # rse = 0.25 -> k = 1 + 1/(2 * 0.0625) = 9
        assert repeats_for_scatter_precision(0.25) == 9

    def test_tighter_precision_costs_more_repeats(self) -> None:
        counts = [repeats_for_scatter_precision(r) for r in (0.5, 0.25, 0.1)]
        assert counts == sorted(counts)

    def test_never_returns_fewer_than_two(self) -> None:
        """One repeat cannot estimate a spread at any precision."""
        assert repeats_for_scatter_precision(0.99) == 2

    @pytest.mark.parametrize("rse", [0.0, 1.0, -0.1, 2.0])
    def test_relative_standard_error_must_be_a_proper_fraction(self, rse: float) -> None:
        with pytest.raises(ValueError, match="relative_standard_error must be in"):
            repeats_for_scatter_precision(rse)

    def test_it_disagrees_with_the_mean_outcome_answer(self) -> None:
        """The finding that reverses the long-context plan's repeats argument.

        At an ICC typical of this repository's data, a *mean* outcome is served
        by a couple of repeats while a *scatter* outcome needs several times
        more. The two questions do not share an answer, and the plan that called
        repeats near-worthless was answering only the first.
        """
        assert repeats_for_reliability(0.6, 0.8) < repeats_for_scatter_precision(0.25)
