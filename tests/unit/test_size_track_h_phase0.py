"""Tests for ``scripts/size_track_h_phase0.py``.

The script answers a power question about Track H's H1 by simulation, so the
things worth testing are the ones that would let it return a confident wrong
number: the mapping from a true J to arm rates, the heterogeneity knob actually
producing the correlation it names, the memoisation being *exact* rather than
approximate, and the standing-rule-2 checker itself failing when it should. That
last one matters most — a gate that cannot fail is the defect this repository has
recorded five times.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest


def _load() -> ModuleType:
    """Import ``scripts/size_track_h_phase0.py``, which is not part of the package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "size_track_h_phase0.py"
    spec = importlib.util.spec_from_file_location("size_track_h_phase0", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["size_track_h_phase0"] = module
    spec.loader.exec_module(module)
    return module


sizer = _load()


# --------------------------------------------------------------------------- #
# The rate mappings
# --------------------------------------------------------------------------- #
class TestRateMappings:
    """A true J must come back out of whatever rates it is turned into."""

    @pytest.mark.parametrize("true_j", [0.0, 0.15, 0.30, 0.50, 0.70, 0.85, 1.0])
    def test_symmetric_reproduces_j(self, true_j: float) -> None:
        p_governing, p_matched = sizer.symmetric_rates(true_j)
        assert p_governing - p_matched == pytest.approx(true_j)

    def test_symmetric_at_the_kill_is_the_registered_pair(self) -> None:
        """J = 0.70 must be sensitivity 0.85 and specificity 0.85 exactly.

        This is the whole reason the symmetric mapping is the primary rather than
        an invention: it reproduces the arithmetic the registration anchors
        ``KILL_THRESHOLD_J`` to, where 0.85 is ``ADEQUACY_CEILING``.
        """
        p_governing, p_matched = sizer.symmetric_rates(sizer.KILL_THRESHOLD_J)
        assert p_governing == pytest.approx(0.85)
        assert 1.0 - p_matched == pytest.approx(0.85)

    @pytest.mark.parametrize("true_j", [-0.01, 1.01])
    def test_symmetric_refuses_j_outside_the_unit_interval(self, true_j: float) -> None:
        with pytest.raises(ValueError, match="true_j must be in"):
            sizer.symmetric_rates(true_j)

    @pytest.mark.parametrize("true_j", [0.0, 0.30, 0.50, 0.70, 0.85])
    def test_sensitivity_anchored_reproduces_j(self, true_j: float) -> None:
        p_governing, p_matched = sizer.sensitivity_anchored_rates(true_j)
        assert p_governing == pytest.approx(sizer.ANCHORED_SENSITIVITY)
        assert p_governing - p_matched == pytest.approx(true_j)

    def test_sensitivity_anchored_refuses_an_unreachable_j(self) -> None:
        with pytest.raises(ValueError, match="unreachable at sensitivity"):
            sizer.sensitivity_anchored_rates(0.95)

    def test_sensitivity_anchored_refuses_a_bad_sensitivity(self) -> None:
        with pytest.raises(ValueError, match="sensitivity must be in"):
            sizer.sensitivity_anchored_rates(0.1, sensitivity=1.5)

    def test_rates_for_dispatches_and_refuses_unknown(self) -> None:
        assert sizer.rates_for(sizer.SHAPE_SYMMETRIC, 0.5) == sizer.symmetric_rates(0.5)
        assert sizer.rates_for(sizer.SHAPE_SENS_ANCHORED, 0.5) == (
            sizer.sensitivity_anchored_rates(0.5)
        )
        with pytest.raises(ValueError, match="unknown rate shape"):
            sizer.rates_for("beta-binomial-ish", 0.5)


# --------------------------------------------------------------------------- #
# Heterogeneity
# --------------------------------------------------------------------------- #
class TestHeterogeneity:
    """The ICC knob must produce the correlation it is named after."""

    @pytest.mark.parametrize("mean", [0.15, 0.5, 0.925])
    @pytest.mark.parametrize("icc", [0.05, 0.20, 0.50])
    def test_beta_shape_gives_the_stated_variance(self, mean: float, icc: float) -> None:
        a, b = sizer.beta_shape(mean, icc)
        total = a + b
        assert a / total == pytest.approx(mean)
        variance = a * b / (total**2 * (total + 1.0))
        assert variance == pytest.approx(icc * mean * (1.0 - mean))

    @pytest.mark.parametrize(("mean", "icc"), [(0.0, 0.2), (1.0, 0.2), (0.5, 0.0), (0.5, 1.0)])
    def test_beta_shape_refuses_the_boundary(self, mean: float, icc: float) -> None:
        with pytest.raises(ValueError, match="strictly inside"):
            sizer.beta_shape(mean, icc)

    def test_zero_icc_is_homogeneous(self) -> None:
        rng = np.random.default_rng(0)
        rates = sizer.draw_triplet_rates(rng, 20, 0.75, 0.0)
        assert np.all(rates == 0.75)

    @pytest.mark.parametrize("mean", [0.0, 1.0])
    def test_degenerate_mean_collapses_whatever_the_icc(self, mean: float) -> None:
        """A mean on the boundary has no room for between-triplet variation.

        This is what makes ``true_j = 1`` runnable as the noiseless known answer.
        """
        rng = np.random.default_rng(0)
        rates = sizer.draw_triplet_rates(rng, 20, mean, 0.5)
        assert np.all(rates == mean)

    def test_drawn_rates_recover_mean_and_icc(self) -> None:
        rng = np.random.default_rng(7)
        rates = sizer.draw_triplet_rates(rng, 200_000, 0.75, 0.20)
        assert float(rates.mean()) == pytest.approx(0.75, abs=0.005)
        assert float(rates.var()) == pytest.approx(0.20 * 0.75 * 0.25, rel=0.05)

    @pytest.mark.parametrize(
        ("n_triplets", "icc", "message"),
        [(0, 0.2, "n_triplets must be"), (5, 1.0, "icc must be in"), (5, -0.1, "icc must be in")],
    )
    def test_draw_triplet_rates_refuses_bad_input(
        self, n_triplets: int, icc: float, message: str
    ) -> None:
        rng = np.random.default_rng(0)
        with pytest.raises(ValueError, match=message):
            sizer.draw_triplet_rates(rng, n_triplets, 0.5, icc)

    def test_icc_is_the_within_triplet_correlation_of_the_outcomes(self) -> None:
        """The name is the claim: two repeats of the same triplet correlate at ``icc``."""
        rng = np.random.default_rng(11)
        icc = 0.30
        rates = sizer.draw_triplet_rates(rng, 400_000, 0.6, icc)
        governing, _ = sizer.draw_event_indicators(rng, rates, rates)
        first, second = governing[:, 0].astype(float), governing[:, 1].astype(float)
        observed = float(np.corrcoef(first, second)[0, 1])
        assert observed == pytest.approx(icc, abs=0.02)


class TestEventIndicators:
    """Marginal rates, the item-level coupling, and the boundary cases."""

    def test_marginal_rates_are_recovered(self) -> None:
        rng = np.random.default_rng(3)
        p_governing = np.full(100_000, 0.8)
        p_matched = np.full(100_000, 0.2)
        governing, matched = sizer.draw_event_indicators(rng, p_governing, p_matched)
        assert float(governing.mean()) == pytest.approx(0.8, abs=0.005)
        assert float(matched.mean()) == pytest.approx(0.2, abs=0.005)

    def test_independent_arms_at_rho_zero(self) -> None:
        rng = np.random.default_rng(4)
        p = np.full(200_000, 0.5)
        governing, matched = sizer.draw_event_indicators(rng, p, p, rho_item=0.0)
        observed = float(np.corrcoef(governing[:, 0], matched[:, 0])[0, 1])
        assert observed == pytest.approx(0.0, abs=0.01)

    def test_positive_coupling_correlates_the_two_arms(self) -> None:
        rng = np.random.default_rng(5)
        p = np.full(200_000, 0.5)
        governing, matched = sizer.draw_event_indicators(rng, p, p, rho_item=0.8)
        observed = float(np.corrcoef(governing[:, 0], matched[:, 0])[0, 1])
        assert observed > 0.5

    def test_boundary_rates_are_deterministic(self) -> None:
        rng = np.random.default_rng(6)
        governing, matched = sizer.draw_event_indicators(
            rng, np.ones(50), np.zeros(50), rho_item=0.5
        )
        assert np.all(governing == 1)
        assert np.all(matched == 0)

    def test_refuses_mismatched_arms(self) -> None:
        rng = np.random.default_rng(0)
        with pytest.raises(ValueError, match="same shape"):
            sizer.draw_event_indicators(rng, np.full(3, 0.5), np.full(4, 0.5))

    @pytest.mark.parametrize("rho_item", [-1.0, 1.0, 1.5])
    def test_refuses_a_bad_rho(self, rho_item: float) -> None:
        rng = np.random.default_rng(0)
        with pytest.raises(ValueError, match="rho_item must be in"):
            sizer.draw_event_indicators(rng, np.full(3, 0.5), np.full(3, 0.5), rho_item=rho_item)

    def test_cluster_diff_sums(self) -> None:
        governing = np.array([[1, 1], [0, 1], [0, 0]], dtype=np.int64)
        matched = np.array([[0, 0], [0, 1], [1, 1]], dtype=np.int64)
        assert sizer.cluster_diff_sums(governing, matched).tolist() == [2, 0, -2]


# --------------------------------------------------------------------------- #
# The estimator wrapper
# --------------------------------------------------------------------------- #
class TestCanonicalArrays:
    """The canonical form must realise the sums it was given, in sorted order."""

    def test_round_trips_the_sums(self) -> None:
        sums = np.array([2, -1, 0, 1, -2], dtype=np.int64)
        control, treatment, clusters = sizer.canonical_arrays(sums)
        diffs = treatment - control
        recovered = [diffs[clusters == c].sum() for c in np.unique(clusters)]
        assert recovered == sorted(sums.tolist())

    def test_every_item_is_a_valid_indicator_difference(self) -> None:
        control, treatment, _ = sizer.canonical_arrays(np.array([2, -2, 1, 0], dtype=np.int64))
        assert set(np.unique(control)) <= {0.0, 1.0}
        assert set(np.unique(treatment)) <= {0.0, 1.0}

    def test_refuses_empty(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            sizer.canonical_arrays(np.array([], dtype=np.int64))

    def test_refuses_an_impossible_sum(self) -> None:
        with pytest.raises(ValueError, match="must lie in"):
            sizer.canonical_arrays(np.array([3], dtype=np.int64))


class TestBootstrapCache:
    """Memoisation must be exact, not approximate."""

    def test_same_multiset_gives_an_identical_result(self) -> None:
        cache = sizer.BootstrapCache(n_resamples=500, seed=1)
        first = cache.interval(np.array([2, 1, 0, -1, 2], dtype=np.int64))
        second = cache.interval(np.array([2, 2, -1, 1, 0], dtype=np.int64))
        assert first is second
        assert cache.hits == 1
        assert cache.misses == 1

    def test_point_estimate_is_the_mean_paired_difference(self) -> None:
        cache = sizer.BootstrapCache(n_resamples=500, seed=1)
        sums = np.array([2, 1, 0, -1, 2], dtype=np.int64)
        result = cache.interval(sums)
        assert result.point_estimate == pytest.approx(
            float(sums.sum()) / (sizer.REPEATS * sums.size)
        )
        assert result.n_clusters == sums.size
        assert result.n_items == sizer.REPEATS * sums.size

    def test_matches_a_direct_call_on_the_canonical_arrays(self) -> None:
        """The cache is a lookup in front of the estimator, not a reimplementation."""
        from decision_evals.stats.cluster import cluster_bootstrap_diff

        sums = np.array([2, 1, 0, -1, 2, 0, 1], dtype=np.int64)
        control, treatment, clusters = sizer.canonical_arrays(sums)
        direct = cluster_bootstrap_diff(
            control=control,
            treatment=treatment,
            clusters=clusters,
            confidence=sizer.CONFIDENCE,
            n_resamples=500,
            seed=1,
        )
        cached = sizer.BootstrapCache(n_resamples=500, seed=1).interval(sums)
        assert cached == direct

    def test_cluster_order_does_not_change_the_interval_materially(self) -> None:
        """Sorting is the canonicalisation; it must not be doing statistical work.

        With a fixed draw matrix, permuting the clusters changes *which* resample
        lands where, so exact equality is not expected. What is expected is that
        the two intervals agree to within bootstrap Monte-Carlo error, which is
        what makes the sort a bookkeeping step rather than an assumption.
        """
        from decision_evals.stats.cluster import cluster_bootstrap_diff

        rng = np.random.default_rng(21)
        sums = rng.integers(-2, 3, size=40).astype(np.int64)
        control, treatment, clusters = sizer.canonical_arrays(sums)
        order = rng.permutation(40)
        shuffled_control = np.concatenate([control.reshape(40, 2)[order].reshape(-1)])
        shuffled_treatment = np.concatenate([treatment.reshape(40, 2)[order].reshape(-1)])
        shuffled = cluster_bootstrap_diff(
            control=shuffled_control,
            treatment=shuffled_treatment,
            clusters=clusters,
            confidence=sizer.CONFIDENCE,
            n_resamples=40_000,
            seed=99,
        )
        canonical = sizer.BootstrapCache(n_resamples=40_000, seed=99).interval(sums)
        assert shuffled.point_estimate == pytest.approx(canonical.point_estimate)
        assert shuffled.ci_low == pytest.approx(canonical.ci_low, abs=0.06)
        assert shuffled.ci_high == pytest.approx(canonical.ci_high, abs=0.06)


class TestClassifyInterval:
    """The three states, including their boundaries."""

    def test_closes_when_the_whole_interval_clears_the_kill(self) -> None:
        assert sizer.classify_interval(0.70, 0.95) == sizer.STATE_CLOSES

    def test_survives_when_the_whole_interval_is_below(self) -> None:
        assert sizer.classify_interval(0.10, 0.699) == sizer.STATE_SURVIVES

    def test_indeterminate_when_it_straddles(self) -> None:
        assert sizer.classify_interval(0.10, 0.80) == sizer.STATE_INDETERMINATE

    def test_an_upper_bound_exactly_at_the_kill_is_indeterminate(self) -> None:
        """``>=`` is the kill, so an interval touching 0.70 has not excluded it."""
        assert sizer.classify_interval(0.10, 0.70) == sizer.STATE_INDETERMINATE

    def test_states_are_exhaustive_and_disjoint(self) -> None:
        rng = np.random.default_rng(1)
        seen = set()
        for _ in range(400):
            low, high = sorted(rng.uniform(-0.2, 1.0, size=2).tolist())
            seen.add(sizer.classify_interval(low, high))
        assert seen == set(sizer.STATES)

    def test_refuses_an_inverted_interval(self) -> None:
        with pytest.raises(ValueError, match="must not exceed"):
            sizer.classify_interval(0.8, 0.2)


class TestPointEstimateSd:
    """The closed form is the simulator's known answer, so it is tested directly."""

    @pytest.mark.parametrize(("n_triplets", "true_j", "icc"), [(5, 0.30, 0.0), (20, 0.50, 0.20)])
    def test_matches_the_empirical_spread(self, n_triplets: int, true_j: float, icc: float) -> None:
        rng = np.random.default_rng(31)
        mean_governing, mean_matched = sizer.symmetric_rates(true_j)
        estimates = []
        for _ in range(4000):
            p_governing = sizer.draw_triplet_rates(rng, n_triplets, mean_governing, icc)
            p_matched = sizer.draw_triplet_rates(rng, n_triplets, mean_matched, icc)
            governing, matched = sizer.draw_event_indicators(rng, p_governing, p_matched)
            sums = sizer.cluster_diff_sums(governing, matched)
            estimates.append(float(sums.sum()) / (sizer.REPEATS * n_triplets))
        predicted = sizer.point_estimate_sd(sizer.SHAPE_SYMMETRIC, true_j, icc, n_triplets)
        assert float(np.std(estimates, ddof=1)) == pytest.approx(predicted, rel=0.06)

    def test_is_zero_at_the_noiseless_ceiling(self) -> None:
        assert sizer.point_estimate_sd(sizer.SHAPE_SYMMETRIC, 1.0, 0.0, 10) == 0.0

    def test_scales_as_one_over_root_n(self) -> None:
        small = sizer.point_estimate_sd(sizer.SHAPE_SYMMETRIC, 0.5, 0.0, 5)
        large = sizer.point_estimate_sd(sizer.SHAPE_SYMMETRIC, 0.5, 0.0, 20)
        assert small / large == pytest.approx(2.0)

    def test_heterogeneity_inflates_it_by_the_design_effect(self) -> None:
        plain = sizer.point_estimate_sd(sizer.SHAPE_SYMMETRIC, 0.5, 0.0, 20)
        varied = sizer.point_estimate_sd(sizer.SHAPE_SYMMETRIC, 0.5, 0.50, 20)
        assert varied / plain == pytest.approx(float(np.sqrt(1.5)))

    def test_refuses_an_empty_design(self) -> None:
        with pytest.raises(ValueError, match="n_triplets must be"):
            sizer.point_estimate_sd(sizer.SHAPE_SYMMETRIC, 0.5, 0.0, 0)


class TestVarianceInflationBound:
    """Two repeats caps what heterogeneity can cost."""

    @pytest.mark.parametrize(("icc", "expected"), [(0.0, 1.0), (0.20, 1.20), (1.0, 2.0)])
    def test_design_effect_at_two_repeats(self, icc: float, expected: float) -> None:
        assert sizer.variance_inflation_bound(icc) == pytest.approx(expected)

    def test_refuses_an_icc_outside_the_unit_interval(self) -> None:
        with pytest.raises(ValueError, match="icc must be in"):
            sizer.variance_inflation_bound(1.5)


# --------------------------------------------------------------------------- #
# Cells and the grid
# --------------------------------------------------------------------------- #
class TestRunCell:
    """One cell, its invariants and its determinism."""

    def test_probabilities_partition(self) -> None:
        cache = sizer.BootstrapCache(n_resamples=400, seed=2)
        result = sizer.run_cell(
            sizer.CellSpec(n_triplets=8, true_j=0.5, icc=0.2),
            n_sims=40,
            rng=np.random.default_rng(0),
            cache=cache,
        )
        total = result.p_closes + result.p_survives + result.p_indeterminate
        assert total == pytest.approx(1.0)

    def test_is_deterministic_given_its_seeds(self) -> None:
        spec = sizer.CellSpec(n_triplets=6, true_j=0.4, icc=0.1)
        first = sizer.run_cell(
            spec,
            n_sims=30,
            rng=np.random.default_rng(123),
            cache=sizer.BootstrapCache(n_resamples=400, seed=2),
        )
        second = sizer.run_cell(
            spec,
            n_sims=30,
            rng=np.random.default_rng(123),
            cache=sizer.BootstrapCache(n_resamples=400, seed=2),
        )
        assert first == second

    def test_noiseless_ceiling_is_certain_and_zero_width(self) -> None:
        """Standing rule 2's known answer, asserted directly rather than only reported."""
        result = sizer.run_cell(
            sizer.CellSpec(n_triplets=5, true_j=1.0, icc=0.0),
            n_sims=25,
            rng=np.random.default_rng(0),
            cache=sizer.BootstrapCache(n_resamples=400, seed=2),
        )
        assert result.p_closes == 1.0
        assert result.p_excludes_zero_above == 1.0
        assert result.mean_width == 0.0
        assert result.mean_j == pytest.approx(1.0)

    def test_refuses_zero_simulations(self) -> None:
        with pytest.raises(ValueError, match="n_sims must be"):
            sizer.run_cell(
                sizer.CellSpec(n_triplets=5, true_j=0.5, icc=0.0),
                n_sims=0,
                rng=np.random.default_rng(0),
                cache=sizer.BootstrapCache(n_resamples=100, seed=2),
            )


class TestBuildGrid:
    """Degenerate combinations must collapse rather than repeat."""

    def test_collapses_the_boundary_j(self) -> None:
        specs = sizer.build_grid([5], [0.30, 1.0], [0.0, 0.2, 0.5])
        boundary = [s for s in specs if s.true_j == 1.0]
        interior = [s for s in specs if s.true_j == 0.30]
        assert len(boundary) == 1
        assert boundary[0].icc == 0.0
        assert len(interior) == 3

    def test_carries_shape_and_rho(self) -> None:
        specs = sizer.build_grid([5], [0.30], [0.2], shape=sizer.SHAPE_SENS_ANCHORED, rho_item=0.5)
        assert specs == [
            sizer.CellSpec(
                n_triplets=5,
                true_j=0.30,
                icc=0.2,
                shape=sizer.SHAPE_SENS_ANCHORED,
                rho_item=0.5,
            )
        ]


# --------------------------------------------------------------------------- #
# The checker itself
# --------------------------------------------------------------------------- #
def _cell(**overrides: object) -> object:
    """A :class:`CellResult` with sane defaults, for exercising the checker."""
    fields: dict[str, object] = {
        "n_triplets": 20,
        "true_j": 0.30,
        "icc": 0.0,
        "shape": sizer.SHAPE_SYMMETRIC,
        "rho_item": 0.0,
        "n_sims": 100,
        "p_closes": 0.0,
        "p_survives": 1.0,
        "p_indeterminate": 0.0,
        "p_point_kill": 0.0,
        "p_excludes_zero_above": 1.0,
        "coverage": 0.95,
        "mean_width": 0.30,
        "p_zero_width": 0.0,
        "mean_j": 0.30,
    }
    fields.update(overrides)
    fields.setdefault(
        "sd_j",
        sizer.point_estimate_sd(
            fields["shape"], fields["true_j"], fields["icc"], fields["n_triplets"]
        ),
    )
    return sizer.CellResult(**fields)


def _healthy_set() -> list[object]:
    """A grid the checker should pass: J=1 certain, and 0.30 unlike 0.85."""
    return [
        _cell(true_j=0.30, p_closes=0.0, p_survives=1.0, mean_j=0.30),
        _cell(true_j=0.85, p_closes=0.9, p_survives=0.0, p_indeterminate=0.1, mean_j=0.85),
        _cell(true_j=1.0, p_closes=1.0, p_survives=0.0, mean_j=1.0, mean_width=0.0, sd_j=0.0),
    ]


class TestCheckKnownAnswers:
    """The gate must pass a known-good case and fail the cases it exists for."""

    def test_passes_a_healthy_grid(self) -> None:
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.025, coverage=0.95, mean_j=0.0)
        checks = sizer.check_known_answers(_healthy_set(), anchor)
        assert checks
        assert all(check.passed for check in checks), [
            (c.name, c.observed) for c in checks if not c.passed
        ]

    def test_fails_when_the_anchor_over_rejects(self) -> None:
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.30, coverage=0.95, mean_j=0.0)
        checks = sizer.check_known_answers(_healthy_set(), anchor)
        failed = [c for c in checks if not c.passed]
        assert [c.name for c in failed] == ["calibration anchor: null false positives, n=20"]

    def test_fails_when_the_anchor_under_covers(self) -> None:
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.02, coverage=0.60, mean_j=0.0)
        checks = sizer.check_known_answers(_healthy_set(), anchor)
        assert any(not c.passed and "coverage" in c.name for c in checks)

    def test_fails_when_the_anchor_is_missing(self) -> None:
        checks = sizer.check_known_answers(_healthy_set(), None)
        assert any(not c.passed and c.name == "calibration anchor" for c in checks)

    def test_fails_when_the_noiseless_ceiling_is_not_certain(self) -> None:
        results = _healthy_set()
        results[2] = _cell(true_j=1.0, p_closes=0.8, mean_j=1.0, mean_width=0.0)
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.025, coverage=0.95, mean_j=0.0)
        checks = sizer.check_known_answers(results, anchor)
        assert any(not c.passed and c.name == "noiseless J=1 detection" for c in checks)

    def test_fails_when_the_generative_model_misses_its_own_j(self) -> None:
        results = _healthy_set()
        results[0] = _cell(true_j=0.30, mean_j=0.55)
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.025, coverage=0.95, mean_j=0.0)
        checks = sizer.check_known_answers(results, anchor)
        assert any(not c.passed and c.name.startswith("estimand recovery") for c in checks)

    def test_fails_when_two_very_different_j_give_the_same_verdict(self) -> None:
        """The failure this repository keeps recording: an estimator that cannot differ."""
        results = _healthy_set()
        results[1] = _cell(true_j=0.85, p_closes=0.0, p_survives=1.0, mean_j=0.85)
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.025, coverage=0.95, mean_j=0.0)
        checks = sizer.check_known_answers(results, anchor)
        assert any(
            not c.passed and c.name == "discrimination between J=0.30 and J=0.85" for c in checks
        )

    def test_fails_when_the_simulated_spread_misses_the_closed_form(self) -> None:
        """The closed form is exact at every n, so a wrong SD is a wrong simulator."""
        results = _healthy_set()
        results[0] = _cell(true_j=0.30, sd_j=0.50)
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.025, coverage=0.95, mean_j=0.0)
        checks = sizer.check_known_answers(results, anchor)
        assert any(not c.passed and c.name.startswith("closed-form SD") for c in checks)

    def test_fails_when_heterogeneity_does_not_widen_as_predicted(self) -> None:
        results = [
            *_healthy_set(),
            _cell(true_j=0.30, icc=0.50, mean_width=0.30),
        ]
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.025, coverage=0.95, mean_j=0.0)
        checks = sizer.check_known_answers(results, anchor)
        assert any(not c.passed and c.name.startswith("design effect") for c in checks)

    def test_passes_when_heterogeneity_widens_as_predicted(self) -> None:
        results = [
            *_healthy_set(),
            _cell(true_j=0.30, icc=0.50, mean_width=0.30 * float(np.sqrt(1.5))),
        ]
        anchor = _cell(true_j=0.0, p_excludes_zero_above=0.025, coverage=0.95, mean_j=0.0)
        checks = sizer.check_known_answers(results, anchor)
        assert all(check.passed for check in checks)


class TestSmallestUsableN:
    """Including the honest answer when there is none."""

    def test_returns_the_smallest_qualifying_n(self) -> None:
        results = [
            _cell(n_triplets=5, p_indeterminate=0.60),
            _cell(n_triplets=10, p_indeterminate=0.18),
            _cell(n_triplets=20, p_indeterminate=0.02),
        ]
        assert (
            sizer.smallest_usable_n(results, true_j=0.30, icc=0.0, shape=sizer.SHAPE_SYMMETRIC)
            == 10
        )

    def test_returns_none_when_nothing_qualifies(self) -> None:
        results = [
            _cell(n_triplets=5, p_indeterminate=0.90),
            _cell(n_triplets=20, p_indeterminate=0.55),
        ]
        assert (
            sizer.smallest_usable_n(results, true_j=0.30, icc=0.0, shape=sizer.SHAPE_SYMMETRIC)
            is None
        )


# --------------------------------------------------------------------------- #
# Rendering and the entry point
# --------------------------------------------------------------------------- #
class TestCheckpointing:
    """A crash must cost one cell, and a resume must be the same run."""

    def test_cell_seeding_depends_only_on_the_cell(self) -> None:
        spec = sizer.CellSpec(n_triplets=8, true_j=0.5, icc=0.2)
        first = sizer.cell_rng(7, spec).standard_normal(5)
        second = sizer.cell_rng(7, spec).standard_normal(5)
        assert first.tolist() == second.tolist()

    def test_different_cells_get_different_streams(self) -> None:
        a = sizer.cell_rng(7, sizer.CellSpec(n_triplets=8, true_j=0.5, icc=0.2))
        b = sizer.cell_rng(7, sizer.CellSpec(n_triplets=8, true_j=0.5, icc=0.5))
        assert a.standard_normal(5).tolist() != b.standard_normal(5).tolist()

    def test_spec_of_round_trips(self) -> None:
        spec = sizer.CellSpec(
            n_triplets=8,
            true_j=0.5,
            icc=0.2,
            shape=sizer.SHAPE_SENS_ANCHORED,
            rho_item=0.5,
        )
        cell = sizer.run_cell(
            spec,
            n_sims=5,
            rng=sizer.cell_rng(1, spec),
            cache=sizer.BootstrapCache(n_resamples=200, seed=1),
        )
        assert sizer.spec_of(cell) == spec

    def test_missing_checkpoint_is_empty(self, tmp_path: Path) -> None:
        assert sizer.load_checkpoint(tmp_path / "absent.jsonl") == []

    def test_checkpoint_round_trips(self, tmp_path: Path) -> None:
        path = tmp_path / "cells.jsonl"
        spec = sizer.CellSpec(n_triplets=6, true_j=0.4, icc=0.1)
        cell = sizer.run_cell(
            spec,
            n_sims=5,
            rng=sizer.cell_rng(1, spec),
            cache=sizer.BootstrapCache(n_resamples=200, seed=1),
        )
        sizer._append_checkpoint(path, cell)
        assert sizer.load_checkpoint(path) == [cell]

    def test_a_corrupt_checkpoint_is_refused_rather_than_resumed(self, tmp_path: Path) -> None:
        path = tmp_path / "cells.jsonl"
        path.write_text('{"n_triplets": 6}' + chr(10), encoding="utf-8")
        with pytest.raises(ValueError, match="is not a cell record"):
            sizer.load_checkpoint(path)

    def test_resume_reproduces_the_uninterrupted_run(self, tmp_path: Path) -> None:
        """The point of per-cell seeding: a restart is not a different experiment."""
        args = [
            "--quick",
            "--sims",
            "10",
            "--resamples",
            "200",
            "--anchor-n",
            "40",
            "--anchor-sims",
            "20",
            "--anchor-resamples",
            "200",
        ]
        straight = tmp_path / "straight.json"
        assert sizer.main([*args, "--out", str(straight)]) == 0

        checkpoint = tmp_path / "partial.jsonl"
        assert sizer.main([*args, "--checkpoint", str(checkpoint)]) == 0
        # Truncate to a partial run, then resume onto it.
        kept = checkpoint.read_text(encoding="utf-8").splitlines()[:4]
        checkpoint.write_text(chr(10).join(kept) + chr(10), encoding="utf-8")
        resumed = tmp_path / "resumed.json"
        assert (
            sizer.main([*args, "--checkpoint", str(checkpoint), "--resume", "--out", str(resumed)])
            == 0
        )

        first = json.loads(straight.read_text(encoding="utf-8"))
        second = json.loads(resumed.read_text(encoding="utf-8"))
        assert first["cells"] == second["cells"]
        assert first["anchor"] == second["anchor"]

    def test_cache_clear_keeps_its_counters(self) -> None:
        cache = sizer.BootstrapCache(n_resamples=200, seed=1)
        cache.interval(np.array([1, 0, 2], dtype=np.int64))
        cache.clear()
        assert cache.misses == 1
        cache.interval(np.array([1, 0, 2], dtype=np.int64))
        assert cache.misses == 2
        assert cache.hits == 0


class TestRendering:
    def test_three_state_table_has_a_row_per_n(self) -> None:
        results = [
            _cell(n_triplets=5, true_j=0.30),
            _cell(n_triplets=20, true_j=0.30),
        ]
        table = sizer.three_state_table(results, shape=sizer.SHAPE_SYMMETRIC, icc=0.0, rho_item=0.0)
        assert "J=0.30" in table
        assert table.count("\n") == 3

    def test_tables_say_so_when_empty(self) -> None:
        assert sizer.three_state_table([], shape="x", icc=0.0, rho_item=0.0) == "_(no cells)_"
        assert sizer.width_table([], shape="x", true_j=0.5, rho_item=0.0) == "_(no cells)_"

    def test_width_table_holds_true_j_fixed(self) -> None:
        results = [
            _cell(n_triplets=20, true_j=0.50, icc=0.0, mean_width=0.25),
            _cell(n_triplets=20, true_j=1.0, icc=0.0, mean_width=0.0),
        ]
        table = sizer.width_table(results, shape=sizer.SHAPE_SYMMETRIC, true_j=0.50, rho_item=0.0)
        assert "0.250" in table
        assert "0.000" not in table


class TestMain:
    """End to end, small enough to run in the suite."""

    def test_quick_run_writes_its_records_and_passes(self, tmp_path: Path) -> None:
        out = tmp_path / "cells.json"
        report = tmp_path / "report.md"
        code = sizer.main(
            [
                "--quick",
                "--sims",
                "12",
                "--resamples",
                "200",
                "--anchor-n",
                "40",
                "--anchor-sims",
                "40",
                "--anchor-resamples",
                "200",
                "--out",
                str(out),
                "--report",
                str(report),
            ]
        )
        assert code == 0
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["cells"]
        assert payload["anchor"]["n_triplets"] == 40
        assert all(check["passed"] for check in payload["checks"])
        assert "Three states" in report.read_text(encoding="utf-8")

    def test_returns_nonzero_when_a_known_answer_is_not_recovered(self, tmp_path: Path) -> None:
        """Skipping the anchor removes a known answer, and the run must refuse."""
        code = sizer.main(
            [
                "--quick",
                "--sims",
                "8",
                "--resamples",
                "200",
                "--anchor-n",
                "0",
                "--out",
                str(tmp_path / "cells.json"),
            ]
        )
        assert code == 1
