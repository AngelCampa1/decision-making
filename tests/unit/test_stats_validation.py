"""Validation and edge-case tests for the statistics layer.

The property tests cover mathematical behaviour. These cover the refusal paths:
every ``raise`` must have a test asserting it fires, because a stats function
that silently accepts malformed input will produce a plausible number rather
than an error, and a plausible wrong number is the worst outcome available here.
"""

from __future__ import annotations

import numpy as np
import pytest

from decision_evals.stats import (
    benjamini_hochberg,
    brier_score,
    cluster_bootstrap_diff,
    design_effect,
    effective_sample_size,
    expected_calibration_error,
    intraclass_correlation,
    log_score,
    mcnemar_exact,
    minimum_detectable_effect,
    murphy_decomposition,
    paired_permutation_test,
    reliability_curve,
    required_pairs,
    smooth_calibration_error,
)


class TestMcNemarValidation:
    def test_rejects_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            mcnemar_exact([True, False], [True])

    def test_rejects_empty_input(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            mcnemar_exact([], [])

    def test_rejects_two_dimensional_input(self) -> None:
        with pytest.raises(ValueError, match="one-dimensional"):
            mcnemar_exact([[True, False]], [[True, False]])

    def test_rejects_non_binary_values(self) -> None:
        with pytest.raises(ValueError, match="only booleans or 0/1"):
            mcnemar_exact([2, 0], [1, 0])

    def test_rejects_unknown_alternative(self) -> None:
        with pytest.raises(ValueError, match="alternative must be"):
            mcnemar_exact([True], [False], alternative="sideways")

    def test_accepts_integer_zero_one_encoding(self) -> None:
        result = mcnemar_exact([0, 1, 1, 0], [1, 1, 1, 0])
        assert result.treatment_wins == 1
        assert result.control_wins == 0

    def test_known_case_matches_hand_calculation(self) -> None:
        """8 treatment wins, 2 control wins: one-sided exact p = P(X >= 8 | n=10)."""
        control = [False] * 8 + [True] * 2
        treatment = [True] * 8 + [False] * 2
        result = mcnemar_exact(control, treatment, alternative="greater")
        assert result.n_discordant == 10
        assert result.treatment_wins == 8
        assert result.p_value == pytest.approx(0.0546875)


class TestPermutationValidation:
    def test_rejects_zero_resamples(self) -> None:
        with pytest.raises(ValueError, match="n_resamples must be >= 1"):
            paired_permutation_test([1.0], [2.0], n_resamples=0)

    def test_rejects_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            paired_permutation_test([1.0, 2.0], [1.0])

    def test_rejects_empty_input(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            paired_permutation_test([], [])

    def test_rejects_two_dimensional_input(self) -> None:
        with pytest.raises(ValueError, match="one-dimensional"):
            paired_permutation_test([[1.0]], [[2.0]])

    def test_rejects_unknown_alternative(self) -> None:
        with pytest.raises(ValueError, match="alternative must be"):
            paired_permutation_test([1.0], [2.0], alternative="nope")

    @pytest.mark.parametrize("alternative", ["greater", "less", "two-sided"])
    def test_all_alternatives_return_valid_probabilities(self, alternative: str) -> None:
        result = paired_permutation_test(
            [0.0, 1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0, 4.0],
            alternative=alternative,
            n_resamples=200,
            seed=5,
        )
        assert 0.0 < result.p_value <= 1.0

    def test_is_reproducible_under_a_fixed_seed(self) -> None:
        kwargs = {"n_resamples": 200, "seed": 99}
        a = paired_permutation_test([0.0, 1.0, 2.0], [3.0, 4.0, 5.0], **kwargs)
        b = paired_permutation_test([0.0, 1.0, 2.0], [3.0, 4.0, 5.0], **kwargs)
        assert a.p_value == b.p_value


class TestClusterBootstrapValidation:
    def test_rejects_zero_resamples(self) -> None:
        with pytest.raises(ValueError, match="n_resamples must be >= 1"):
            cluster_bootstrap_diff([1.0], [2.0], [0], n_resamples=0)

    @pytest.mark.parametrize("confidence", [0.0, 1.0, -0.1, 1.5])
    def test_rejects_confidence_outside_unit_interval(self, confidence: float) -> None:
        with pytest.raises(ValueError, match="confidence must be in"):
            cluster_bootstrap_diff([1.0], [2.0], [0], confidence=confidence)

    def test_rejects_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            cluster_bootstrap_diff([1.0, 2.0], [1.0, 2.0], [0])

    def test_rejects_two_dimensional_input(self) -> None:
        with pytest.raises(ValueError, match="one-dimensional"):
            cluster_bootstrap_diff([[1.0]], [[2.0]], [0])

    def test_rejects_empty_clusters(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            cluster_bootstrap_diff([], [], [])

    def test_rejects_two_dimensional_clusters(self) -> None:
        with pytest.raises(ValueError, match="clusters must be one-dimensional"):
            cluster_bootstrap_diff([1.0, 2.0], [1.0, 2.0], [[0, 1]])

    def test_single_resample_reports_zero_standard_error(self) -> None:
        """With one replicate there is no spread to estimate."""
        result = cluster_bootstrap_diff([1.0, 2.0], [2.0, 3.0], [0, 1], n_resamples=1, seed=1)
        assert result.standard_error == 0.0

    def test_accepts_string_cluster_labels(self) -> None:
        result = cluster_bootstrap_diff(
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 4.0, 5.0],
            ["tpl-a", "tpl-a", "tpl-b", "tpl-b"],
            n_resamples=100,
            seed=1,
        )
        assert result.n_clusters == 2
        assert result.n_items == 4

    def test_excludes_zero_detects_both_directions(self) -> None:
        positive = cluster_bootstrap_diff(
            np.zeros(20), np.ones(20), np.arange(20), n_resamples=100, seed=1
        )
        assert positive.excludes_zero
        negative = cluster_bootstrap_diff(
            np.ones(20), np.zeros(20), np.arange(20), n_resamples=100, seed=1
        )
        assert negative.excludes_zero
        straddling = cluster_bootstrap_diff(
            np.zeros(20),
            np.array([1.0, -1.0] * 10),
            np.arange(20),
            n_resamples=200,
            seed=1,
        )
        assert not straddling.excludes_zero


class TestIntraclassCorrelation:
    def test_rejects_single_cluster(self) -> None:
        with pytest.raises(ValueError, match="at least 2 clusters"):
            intraclass_correlation([1.0, 2.0], [0, 0])

    def test_rejects_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            intraclass_correlation([1.0, 2.0], [0])

    def test_rejects_two_dimensional_values(self) -> None:
        with pytest.raises(ValueError, match="one-dimensional"):
            intraclass_correlation([[1.0, 2.0]], [0, 1])

    def test_singleton_clusters_give_zero(self) -> None:
        """No within-cluster variance exists to estimate."""
        assert intraclass_correlation([1.0, 5.0, 9.0], [0, 1, 2]) == 0.0

    def test_identical_within_clusters_gives_one(self) -> None:
        values = [1.0, 1.0, 1.0, 9.0, 9.0, 9.0]
        clusters = [0, 0, 0, 1, 1, 1]
        assert intraclass_correlation(values, clusters) == pytest.approx(1.0)

    def test_no_between_cluster_variance_gives_zero(self) -> None:
        values = [1.0, 9.0, 1.0, 9.0]
        clusters = [0, 0, 1, 1]
        assert intraclass_correlation(values, clusters) == 0.0

    def test_constant_values_give_zero(self) -> None:
        """Zero total variance: the denominator vanishes rather than dividing by it."""
        assert intraclass_correlation([3.0] * 6, [0, 0, 0, 1, 1, 1]) == 0.0


class TestDesignEffectValidation:
    def test_rejects_cluster_size_below_one(self) -> None:
        with pytest.raises(ValueError, match="mean_cluster_size must be >= 1"):
            design_effect(0.5, 0.2)

    @pytest.mark.parametrize("icc", [-0.1, 1.1])
    def test_rejects_icc_outside_unit_interval(self, icc: float) -> None:
        with pytest.raises(ValueError, match=r"icc must be in \[0, 1\]"):
            design_effect(5.0, icc)

    def test_rejects_non_positive_item_count(self) -> None:
        with pytest.raises(ValueError, match="n_items must be >= 1"):
            effective_sample_size(0, 5.0, 0.2)

    def test_matches_the_documented_worked_example(self) -> None:
        """Six variants per template at ICC 0.2 halves the effective sample."""
        assert design_effect(6.0, 0.2) == pytest.approx(2.0)
        assert effective_sample_size(300, 6.0, 0.2) == pytest.approx(150.0)


class TestCalibrationValidation:
    def test_rejects_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            brier_score([0.5, 0.5], [1.0])

    def test_rejects_empty_input(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            brier_score([], [])

    def test_rejects_two_dimensional_input(self) -> None:
        with pytest.raises(ValueError, match="one-dimensional"):
            brier_score([[0.5]], [[1.0]])

    @pytest.mark.parametrize("bad", [-0.01, 1.01])
    def test_rejects_forecasts_outside_unit_interval(self, bad: float) -> None:
        with pytest.raises(ValueError, match=r"forecasts must lie in \[0, 1\]"):
            brier_score([bad], [1.0])

    def test_rejects_non_binary_outcomes(self) -> None:
        with pytest.raises(ValueError, match="outcomes must be binary"):
            brier_score([0.5], [0.5])

    @pytest.mark.parametrize("epsilon", [0.0, 0.5, -1.0, 0.9])
    def test_log_score_rejects_bad_epsilon(self, epsilon: float) -> None:
        with pytest.raises(ValueError, match=r"epsilon must be in \(0, 0.5\)"):
            log_score([0.5], [1.0], epsilon=epsilon)

    def test_log_score_stays_finite_at_the_boundaries(self) -> None:
        """A confident-and-wrong forecast must be penalised, not produce infinity."""
        assert np.isfinite(log_score([0.0, 1.0], [1.0, 0.0]))

    def test_reliability_curve_rejects_zero_bins(self) -> None:
        with pytest.raises(ValueError, match="n_bins must be >= 1"):
            reliability_curve([0.5], [1.0], n_bins=0)

    def test_reliability_curve_omits_empty_bins(self) -> None:
        bins = reliability_curve([0.05, 0.05], [1.0, 0.0], n_bins=10)
        assert len(bins) == 1
        assert bins[0].count == 2

    def test_reliability_curve_includes_a_forecast_of_exactly_one(self) -> None:
        """The top bin is closed, so 1.0 is binned rather than silently dropped."""
        bins = reliability_curve([1.0], [1.0], n_bins=10)
        assert len(bins) == 1
        assert bins[0].count == 1
        assert bins[0].upper == pytest.approx(1.0)

    def test_expected_calibration_error_of_a_perfect_forecaster_is_zero(self) -> None:
        assert expected_calibration_error([0.0, 1.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_smooth_calibration_error_rejects_non_positive_bandwidth(self) -> None:
        with pytest.raises(ValueError, match="bandwidth must be positive"):
            smooth_calibration_error([0.5], [1.0], bandwidth=0.0)

    def test_smooth_calibration_error_accepts_an_explicit_bandwidth(self) -> None:
        value = smooth_calibration_error([0.2, 0.8, 0.5], [0.0, 1.0, 1.0], bandwidth=0.1)
        assert 0.0 <= value <= 1.0

    def test_smooth_calibration_error_handles_a_single_observation(self) -> None:
        """Self-weight is 1, so the estimator degrades rather than dividing by zero."""
        assert smooth_calibration_error([0.3], [1.0]) == pytest.approx(0.7)

    def test_skill_score_is_zero_when_every_outcome_is_identical(self) -> None:
        """No forecaster can beat the constant prediction on a degenerate set."""
        d = murphy_decomposition([0.3, 0.7], [1.0, 1.0])
        assert d.uncertainty == 0.0
        assert d.skill_score == 0.0

    def test_skill_score_rewards_beating_the_base_rate(self) -> None:
        d = murphy_decomposition([0.0, 1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0])
        assert d.skill_score == pytest.approx(1.0)

    def test_forecasts_differing_only_by_float_noise_group_together(self) -> None:
        forecasts = [0.5, 0.5 + 1e-15, 0.5 - 1e-15, 0.5]
        d = murphy_decomposition(forecasts, [1.0, 0.0, 1.0, 0.0])
        assert d.n_groups == 1


class TestBenjaminiHochbergValidation:
    @pytest.mark.parametrize("q", [0.0, -0.1, 1.5])
    def test_rejects_q_outside_valid_range(self, q: float) -> None:
        with pytest.raises(ValueError, match=r"q must be in \(0, 1\]"):
            benjamini_hochberg([0.01], q=q)

    def test_rejects_empty_family(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            benjamini_hochberg([])

    def test_rejects_two_dimensional_input(self) -> None:
        with pytest.raises(ValueError, match="one-dimensional"):
            benjamini_hochberg([[0.01, 0.02]])

    @pytest.mark.parametrize("bad", [-0.01, 1.01])
    def test_rejects_values_outside_unit_interval(self, bad: float) -> None:
        with pytest.raises(ValueError, match=r"p_values must lie in \[0, 1\]"):
            benjamini_hochberg([bad])

    def test_counts_rejections_at_the_chosen_level(self) -> None:
        result = benjamini_hochberg([0.001, 0.008, 0.04, 0.6, 0.9], q=0.10)
        assert result.n_rejected == sum(result.rejected)
        assert result.n_tests == 5
        assert result.rejected[0]
        assert not result.rejected[-1]


class TestPowerValidation:
    def test_rejects_zero_effect(self) -> None:
        with pytest.raises(ValueError, match="effect must be non-zero"):
            required_pairs(0.0, 0.5)

    def test_rejects_effect_exceeding_discordant_probability(self) -> None:
        with pytest.raises(ValueError, match="cannot exceed p_discordant"):
            required_pairs(0.6, 0.5)

    @pytest.mark.parametrize("p_discordant", [0.0, -0.1, 1.5])
    def test_rejects_invalid_discordant_probability(self, p_discordant: float) -> None:
        with pytest.raises(ValueError, match="p_discordant must be in"):
            required_pairs(0.1, p_discordant)

    @pytest.mark.parametrize("alpha", [0.0, 1.0, -0.5])
    def test_rejects_invalid_alpha(self, alpha: float) -> None:
        with pytest.raises(ValueError, match="alpha must be in"):
            required_pairs(0.1, 0.5, alpha=alpha)

    @pytest.mark.parametrize("power", [0.0, 1.0, 2.0])
    def test_rejects_invalid_power(self, power: float) -> None:
        with pytest.raises(ValueError, match="power must be in"):
            required_pairs(0.1, 0.5, power=power)

    def test_rejects_design_effect_below_one(self) -> None:
        with pytest.raises(ValueError, match="design_effect must be >= 1"):
            required_pairs(0.1, 0.5, design_effect=0.5)

    def test_rejects_unknown_alternative(self) -> None:
        with pytest.raises(ValueError, match="alternative must be"):
            required_pairs(0.1, 0.5, alternative="less")

    def test_two_sided_needs_more_items_than_one_sided(self) -> None:
        assert (
            required_pairs(0.1, 0.5, alternative="two-sided").n_pairs
            > required_pairs(0.1, 0.5, alternative="greater").n_pairs
        )

    def test_mde_rejects_non_positive_item_count(self) -> None:
        with pytest.raises(ValueError, match="n_pairs must be >= 1"):
            minimum_detectable_effect(0, 0.5)

    def test_mde_rejects_non_positive_tolerance(self) -> None:
        with pytest.raises(ValueError, match="tolerance must be positive"):
            minimum_detectable_effect(100, 0.5, tolerance=0.0)

    def test_mde_refuses_when_no_effect_is_detectable(self) -> None:
        """The useful answer for an underpowered budget is 'do not run this'."""
        with pytest.raises(ValueError, match="cannot detect any effect"):
            minimum_detectable_effect(2, 0.5)

    def test_mde_shrinks_as_items_are_added(self) -> None:
        assert (
            minimum_detectable_effect(2000, 0.5).effect < minimum_detectable_effect(200, 0.5).effect
        )

    def test_reports_both_adjusted_and_unadjusted_counts(self) -> None:
        result = required_pairs(0.1, 0.5, design_effect=2.0)
        assert result.n_pairs >= 2 * result.n_pairs_unadjusted - 1
        assert result.design_effect == 2.0
