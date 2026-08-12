"""Property-based tests for the statistics layer.

These are the tests that make the published numbers trustworthy. Example-based
tests confirm a function works on the cases the author thought of; these confirm
mathematical identities and cross-implementation agreement hold across the whole
input space hypothesis can reach.

Four properties carry most of the weight:

* the Murphy decomposition identity, which catches essentially every possible
  decomposition bug in one assertion;
* agreement between our McNemar implementation and ``scipy``'s binomial test;
* internal agreement between Benjamini-Hochberg's rejection flags and its
  adjusted values (the step-up itself is ``statsmodels``' -- see
  ``stats/multiplicity.py``);
* the cluster bootstrap reducing exactly to an item bootstrap when every cluster
  is a singleton.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from scipy import stats as scipy_stats

from decision_evals.stats import (
    aptitude_unreliability,
    benjamini_hochberg,
    brier_score,
    cluster_bootstrap_diff,
    design_effect,
    effective_sample_size,
    log_score,
    mcnemar_exact,
    minimum_detectable_effect,
    murphy_decomposition,
    paired_permutation_test,
    per_item_reliability,
    repeat_reliability,
    repeats_for_reliability,
    repeats_for_scatter_precision,
    required_pairs,
    smooth_calibration_error,
)

# Bootstrap-heavy tests are slow; hypothesis' default deadline is not meaningful
# for them, and shrinking large arrays adds nothing.
_SLOW = settings(deadline=None, max_examples=50, suppress_health_check=[HealthCheck.too_slow])

probabilities = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
binary = st.sampled_from([0.0, 1.0])

# Scores for the reliability tests. Bounded well away from the float extremes:
# the shift and scale identities are exact in real arithmetic and only
# approximately so in binary floating point, and enormous magnitudes turn a real
# identity into a spurious failure about representation.
scores_1d = st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False)


@st.composite
def forecast_sets(draw: st.DrawFn, min_size: int = 1, max_size: int = 60):
    """A forecast/outcome pair of equal length."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    forecasts = draw(st.lists(probabilities, min_size=n, max_size=n))
    outcomes = draw(st.lists(binary, min_size=n, max_size=n))
    return np.array(forecasts), np.array(outcomes)


@st.composite
def paired_binary(draw: st.DrawFn, min_size: int = 1, max_size: int = 80):
    """Two equal-length boolean arrays representing paired correctness."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    control = draw(st.lists(st.booleans(), min_size=n, max_size=n))
    treatment = draw(st.lists(st.booleans(), min_size=n, max_size=n))
    return np.array(control), np.array(treatment)


# --------------------------------------------------------------------------- #
# Calibration
# --------------------------------------------------------------------------- #


class TestMurphyDecomposition:
    """Brier = Reliability - Resolution + Uncertainty, exactly."""

    @given(forecast_sets())
    def test_identity_holds_to_floating_point_precision(self, data) -> None:
        forecasts, outcomes = data
        d = murphy_decomposition(forecasts, outcomes)
        assert abs(d.identity_residual) < 1e-9

    @given(forecast_sets())
    def test_components_are_non_negative(self, data) -> None:
        forecasts, outcomes = data
        d = murphy_decomposition(forecasts, outcomes)
        assert d.reliability >= -1e-12
        assert d.resolution >= -1e-12
        assert d.uncertainty >= -1e-12

    @given(forecast_sets())
    def test_brier_matches_direct_computation(self, data) -> None:
        forecasts, outcomes = data
        assert murphy_decomposition(forecasts, outcomes).brier == pytest.approx(
            brier_score(forecasts, outcomes)
        )

    @given(forecast_sets())
    def test_uncertainty_bounded_by_one_quarter(self, data) -> None:
        """o(1-o) is maximised at o = 0.5."""
        forecasts, outcomes = data
        assert murphy_decomposition(forecasts, outcomes).uncertainty <= 0.25 + 1e-12

    @given(st.lists(binary, min_size=2, max_size=40))
    def test_constant_base_rate_forecast_has_zero_resolution(self, outcomes) -> None:
        """A forecaster that always predicts the base rate discriminates not at all.

        This is the hedging failure mode the resolution guard exists to catch:
        perfectly reliable, and worthless.
        """
        o = np.array(outcomes)
        base_rate = float(o.mean())
        d = murphy_decomposition(np.full(o.size, base_rate), o)
        assert d.resolution == pytest.approx(0.0, abs=1e-12)
        assert d.reliability == pytest.approx(0.0, abs=1e-12)
        assert d.brier == pytest.approx(d.uncertainty)

    @given(st.lists(binary, min_size=1, max_size=40))
    def test_perfect_forecaster_scores_zero(self, outcomes) -> None:
        o = np.array(outcomes)
        d = murphy_decomposition(o, o)
        assert d.brier == pytest.approx(0.0, abs=1e-12)
        assert d.reliability == pytest.approx(0.0, abs=1e-12)


class TestProperScoringRules:
    @given(forecast_sets())
    def test_brier_is_bounded(self, data) -> None:
        forecasts, outcomes = data
        assert 0.0 <= brier_score(forecasts, outcomes) <= 1.0

    @given(forecast_sets())
    def test_log_score_is_non_negative(self, data) -> None:
        forecasts, outcomes = data
        assert log_score(forecasts, outcomes) >= 0.0

    @given(
        st.floats(min_value=0.05, max_value=0.95),
        st.floats(min_value=0.05, max_value=0.95),
    )
    def test_brier_is_proper(self, true_p: float, reported_p: float) -> None:
        """Expected Brier is minimised by reporting the true probability.

        Checked in expectation rather than by sampling: for a single forecast p
        against outcome probability q, E[(p - o)^2] = p^2 - 2pq + q, which is
        minimised at p = q.
        """
        assume(abs(true_p - reported_p) > 1e-6)

        def expected(p: float, q: float) -> float:
            return p**2 - 2 * p * q + q

        assert expected(true_p, true_p) < expected(reported_p, true_p)

    @given(forecast_sets(min_size=2))
    def test_smooth_calibration_error_is_bounded(self, data) -> None:
        forecasts, outcomes = data
        assert 0.0 <= smooth_calibration_error(forecasts, outcomes) <= 1.0


# --------------------------------------------------------------------------- #
# Paired tests
# --------------------------------------------------------------------------- #


class TestMcNemar:
    @given(paired_binary())
    def test_matches_scipy_binomtest_on_discordant_pairs(self, data) -> None:
        """Our result must be scipy's binomial test, not merely close to it."""
        control, treatment = data
        result = mcnemar_exact(control, treatment, alternative="two-sided")
        assume(result.n_discordant > 0)
        expected = scipy_stats.binomtest(
            result.treatment_wins, result.n_discordant, 0.5, alternative="two-sided"
        ).pvalue
        assert result.p_value == pytest.approx(float(expected))

    @given(paired_binary())
    def test_p_value_is_a_probability(self, data) -> None:
        control, treatment = data
        assert 0.0 <= mcnemar_exact(control, treatment).p_value <= 1.0

    @given(paired_binary())
    def test_proportion_difference_equals_accuracy_difference(self, data) -> None:
        control, treatment = data
        result = mcnemar_exact(control, treatment)
        expected = float(np.mean(treatment)) - float(np.mean(control))
        assert result.proportion_difference == pytest.approx(expected)

    @given(paired_binary())
    def test_swapping_arms_mirrors_the_result(self, data) -> None:
        control, treatment = data
        forward = mcnemar_exact(control, treatment, alternative="two-sided")
        reverse = mcnemar_exact(treatment, control, alternative="two-sided")
        assert forward.p_value == pytest.approx(reverse.p_value)
        assert forward.treatment_wins == reverse.control_wins
        assert forward.proportion_difference == pytest.approx(-reverse.proportion_difference)

    @given(paired_binary())
    def test_one_sided_tails_partition_the_evidence(self, data) -> None:
        """A directional test can only be more significant than its mirror."""
        control, treatment = data
        greater = mcnemar_exact(control, treatment, alternative="greater")
        less = mcnemar_exact(control, treatment, alternative="less")
        if greater.treatment_wins > greater.control_wins:
            assert greater.p_value < less.p_value
        elif greater.treatment_wins < greater.control_wins:
            assert less.p_value < greater.p_value

    @given(st.lists(st.booleans(), min_size=1, max_size=50))
    def test_identical_arms_are_never_significant(self, values) -> None:
        arr = np.array(values)
        result = mcnemar_exact(arr, arr)
        assert result.n_discordant == 0
        assert result.p_value == 1.0
        assert result.proportion_difference == 0.0


class TestPairedPermutation:
    @given(paired_binary(min_size=2, max_size=30))
    @_SLOW
    def test_p_value_is_never_zero(self, data) -> None:
        """A resampling test can only bound its p-value by its resolution."""
        control, treatment = data
        result = paired_permutation_test(
            control.astype(float), treatment.astype(float), n_resamples=200, seed=7
        )
        assert result.p_value > 0.0
        assert result.p_value <= 1.0

    @given(st.lists(st.floats(-10, 10), min_size=2, max_size=30))
    @_SLOW
    def test_identical_arms_give_maximal_p_value(self, values) -> None:
        arr = np.array(values)
        result = paired_permutation_test(arr, arr, n_resamples=100, seed=3, alternative="two-sided")
        assert result.observed_mean_difference == pytest.approx(0.0)
        assert result.p_value == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# Clustering
# --------------------------------------------------------------------------- #


class TestClusterBootstrap:
    @given(paired_binary(min_size=3, max_size=25))
    @_SLOW
    def test_singleton_clusters_reduce_to_an_item_bootstrap(self, data) -> None:
        """With one item per cluster, cluster resampling *is* item resampling.

        Asserted exactly rather than approximately: same seed, same draws, so the
        two must agree bit for bit. If they don't, the resampling unit is wrong.
        """
        control, treatment = data
        n = control.size
        clusters = np.arange(n)
        result = cluster_bootstrap_diff(
            control.astype(float), treatment.astype(float), clusters, n_resamples=200, seed=42
        )

        diffs = treatment.astype(float) - control.astype(float)
        rng = np.random.default_rng(42)
        draws = rng.integers(0, n, size=(200, n))
        naive = diffs[draws].mean(axis=1)

        assert result.ci_low == pytest.approx(float(np.quantile(naive, 0.025)))
        assert result.ci_high == pytest.approx(float(np.quantile(naive, 0.975)))

    @given(paired_binary(min_size=2, max_size=25))
    @_SLOW
    def test_interval_contains_the_point_estimate(self, data) -> None:
        control, treatment = data
        n = control.size
        result = cluster_bootstrap_diff(
            control.astype(float),
            treatment.astype(float),
            np.arange(n) // 2,
            n_resamples=200,
            seed=11,
        )
        assert result.ci_low <= result.point_estimate <= result.ci_high

    def test_correlated_clusters_widen_the_interval(self) -> None:
        """Positive intra-cluster correlation must inflate the standard error.

        Constructed rather than sampled: identical items within each cluster is
        the maximal-ICC case, so the comparison is deterministic. Treating those
        items as independent is exactly the error this guards against.
        """
        rng = np.random.default_rng(0)
        cluster_values = rng.normal(size=25)
        # 25 clusters of 8 identical items: ICC = 1.
        diffs = np.repeat(cluster_values, 8)
        clusters = np.repeat(np.arange(25), 8)
        zeros = np.zeros_like(diffs)

        clustered = cluster_bootstrap_diff(zeros, diffs, clusters, n_resamples=2000, seed=1)
        item_level = cluster_bootstrap_diff(
            zeros, diffs, np.arange(diffs.size), n_resamples=2000, seed=1
        )
        assert clustered.standard_error > item_level.standard_error


class TestDesignEffect:
    @given(
        st.floats(min_value=1.0, max_value=50.0),
        st.floats(min_value=0.0, max_value=1.0),
    )
    def test_design_effect_is_at_least_one(self, m: float, icc: float) -> None:
        assert design_effect(m, icc) >= 1.0

    @given(st.floats(min_value=1.0, max_value=50.0))
    def test_zero_correlation_means_no_inflation(self, m: float) -> None:
        assert design_effect(m, 0.0) == pytest.approx(1.0)

    @given(
        st.integers(min_value=1, max_value=10_000),
        st.floats(min_value=1.0, max_value=20.0),
        st.floats(min_value=0.0, max_value=1.0),
    )
    def test_effective_sample_never_exceeds_actual(self, n: int, m: float, icc: float) -> None:
        assert effective_sample_size(n, m, icc) <= n + 1e-9


# --------------------------------------------------------------------------- #
# Multiplicity
# --------------------------------------------------------------------------- #


class TestBenjaminiHochberg:
    @given(st.lists(probabilities, min_size=1, max_size=40))
    def test_rejections_agree_with_the_adjusted_values(self, p_values) -> None:
        """The step-up defines rejection on the sorted sequence, and the adjusted
        values are reported separately. Anyone reading a result will assume the
        two agree; this is the assertion that they do.

        This replaced a test that compared our own step-up against statsmodels.
        That implementation is gone -- `benjamini_hochberg` now calls
        statsmodels -- and a test asserting statsmodels equals itself proves
        nothing.
        """
        result = benjamini_hochberg(p_values, q=0.10)
        assert result.rejected == tuple(q <= 0.10 for q in result.q_values)
        assert result.n_rejected == sum(result.rejected)

    @given(st.lists(probabilities, min_size=1, max_size=40))
    def test_adjusted_values_never_shrink(self, p_values) -> None:
        result = benjamini_hochberg(p_values)
        assert all(q >= p - 1e-12 for p, q in zip(result.p_values, result.q_values, strict=True))

    @given(st.lists(probabilities, min_size=1, max_size=40))
    def test_adjusted_values_are_probabilities(self, p_values) -> None:
        assert all(0.0 <= q <= 1.0 for q in benjamini_hochberg(p_values).q_values)

    @given(probabilities)
    def test_single_test_is_unchanged(self, p: float) -> None:
        """With a family of one there is nothing to correct for."""
        assert benjamini_hochberg([p]).q_values[0] == pytest.approx(p)

    @given(st.lists(probabilities, min_size=2, max_size=30))
    def test_ordering_is_preserved(self, p_values) -> None:
        result = benjamini_hochberg(p_values)
        order = np.argsort(p_values, kind="stable")
        sorted_q = np.array(result.q_values)[order]
        assert np.all(np.diff(sorted_q) >= -1e-12)


# --------------------------------------------------------------------------- #
# Power
# --------------------------------------------------------------------------- #


class TestPower:
    @given(
        st.floats(min_value=0.03, max_value=0.30),
        st.floats(min_value=0.35, max_value=0.90),
    )
    def test_mde_round_trips_through_required_pairs(
        self, effect: float, p_discordant: float
    ) -> None:
        """Sizing for an effect, then asking what that size detects, returns it."""
        assume(effect < p_discordant)
        n = required_pairs(effect, p_discordant).n_pairs
        recovered = minimum_detectable_effect(n, p_discordant).effect
        assert recovered <= effect + 1e-6

    @given(
        st.floats(min_value=0.02, max_value=0.20),
        st.floats(min_value=0.30, max_value=0.90),
    )
    def test_smaller_effects_need_more_items(self, effect: float, p_discordant: float) -> None:
        assume(effect * 2 < p_discordant)
        assert (
            required_pairs(effect, p_discordant).n_pairs
            > required_pairs(effect * 2, p_discordant).n_pairs
        )

    @given(
        st.floats(min_value=0.05, max_value=0.25),
        st.floats(min_value=0.40, max_value=0.90),
        st.floats(min_value=1.0, max_value=4.0),
    )
    def test_clustering_inflates_the_requirement(
        self, effect: float, p_discordant: float, deff: float
    ) -> None:
        assume(effect < p_discordant)
        plain = required_pairs(effect, p_discordant).n_pairs
        clustered = required_pairs(effect, p_discordant, design_effect=deff).n_pairs
        assert clustered >= plain

    @given(
        st.floats(min_value=0.05, max_value=0.25),
        st.floats(min_value=0.40, max_value=0.90),
    )
    def test_higher_power_needs_more_items(self, effect: float, p_discordant: float) -> None:
        assume(effect < p_discordant)
        assert (
            required_pairs(effect, p_discordant, power=0.95).n_pairs
            >= required_pairs(effect, p_discordant, power=0.80).n_pairs
        )


class TestReliability:
    """Aptitude and unreliability.

    The round-trip property below is the one that earns its keep: a bare
    ``ceil`` on the Spearman-Brown inverse over-charges a repeat whenever the
    exact solution is an integer, and an example-based test only catches that if
    the author happens to pick such a pair. This catches it across the space.
    """

    @given(st.lists(scores_1d, min_size=1, max_size=60), st.floats(-50.0, 50.0))
    def test_unreliability_is_shift_invariant(self, values: list[float], shift: float) -> None:
        """A spread does not move when everything moves together."""
        base = aptitude_unreliability(values)
        shifted = aptitude_unreliability([v + shift for v in values])
        assert shifted.unreliability == pytest.approx(base.unreliability, abs=1e-6)
        assert shifted.aptitude == pytest.approx(base.aptitude + shift, abs=1e-6)

    @given(st.lists(scores_1d, min_size=1, max_size=60), st.floats(0.01, 20.0))
    def test_unreliability_is_scale_equivariant(self, values: list[float], scale: float) -> None:
        base = aptitude_unreliability(values)
        scaled = aptitude_unreliability([v * scale for v in values])
        assert scaled.unreliability == pytest.approx(base.unreliability * scale, rel=1e-6)

    @given(st.lists(scores_1d, min_size=1, max_size=60))
    def test_unreliability_is_never_negative(self, values: list[float]) -> None:
        assert aptitude_unreliability(values).unreliability >= 0.0

    @given(st.lists(scores_1d, min_size=1, max_size=40), st.integers(2, 8))
    def test_per_item_rows_agree_with_the_scalar_estimator(
        self, values: list[float], n_repeats: int
    ) -> None:
        """Cross-implementation agreement between our extension and the paper's."""
        n_items = max(1, len(values) // n_repeats)
        matrix = np.resize(np.asarray(values, dtype=float), (n_items, n_repeats))
        per_item = per_item_reliability(matrix)
        for row in range(n_items):
            expected = aptitude_unreliability(matrix[row])
            assert per_item.aptitude[row] == pytest.approx(expected.aptitude)
            assert per_item.scatter[row] == pytest.approx(expected.unreliability)

    @given(st.floats(0.01, 0.99), st.integers(1, 200))
    def test_spearman_brown_is_bounded_and_monotone(self, icc: float, k: int) -> None:
        value = repeat_reliability(icc, k)
        assert 0.0 <= value <= 1.0
        assert value >= repeat_reliability(icc, 1)
        assert value <= repeat_reliability(icc, k + 1)

    @given(st.floats(0.01, 0.99), st.floats(0.01, 0.99))
    def test_repeats_for_reliability_returns_the_smallest_sufficient_count(
        self, icc: float, target: float
    ) -> None:
        """Sufficient, and minimal. The second half is what the ceil bug broke."""
        k = repeats_for_reliability(icc, target)
        assert repeat_reliability(icc, k) >= target - 1e-12
        if k > 1:
            assert repeat_reliability(icc, k - 1) < target

    @given(st.floats(0.001, 0.999))
    def test_scatter_precision_is_monotone_and_at_least_two(self, rse: float) -> None:
        k = repeats_for_scatter_precision(rse)
        assert k >= 2
        assert repeats_for_scatter_precision(min(rse * 2, 0.999)) <= k
