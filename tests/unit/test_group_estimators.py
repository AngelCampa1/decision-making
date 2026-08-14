"""The three grouping estimators a held pre-registration names, and the guards around them.

N6's pre-registration registers three bands whose estimators did not exist:
routing accuracy per procedure, false-positive rate per negative kind, and the
difference in firing accuracy between the short bands and the long ones. The
third is the experiment; the first two are the bands that would otherwise be
scored by eye.

**Every test here is written to the same standard the estimators are for.**
Standing rule 2 — *a falsifier must be run against a known-good case before it
may fail anything* — so each refusal is paired with the nearest input that must
be accepted, and each estimator is shown both separating groups that differ and
declining to separate groups that do not. A statistic that always separates is
as broken as one that never does, and neither announces itself.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from decision_evals.stats import (
    cluster_bootstrap_diff,
    cluster_bootstrap_two_sample,
)
from decision_evals.trigger_arms import (
    ArmError,
    BandTable,
    bootstrap_rate,
    bootstrap_rate_difference,
    false_positive_rate_by_kind,
    format_bands,
    format_difference,
    format_negative_kinds,
    format_rate,
    format_routing,
    per_item_fire_rates,
    routing_by_procedure,
    summarise,
    summarise_by_band,
)

# --------------------------------------------------------------------------- #
# Record builders. A checkpoint row, as `collect` writes it.
# --------------------------------------------------------------------------- #


def rec(
    case: str,
    *,
    fired: bool | None,
    should_fire: bool,
    repeat: int = 0,
    band: str | None = None,
    triple: str | None = None,
    route: str | None = None,
    routes: list[str] | None = None,
    procedure: str | None = None,
    kind: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "case": case,
        "repeat": repeat,
        "fired": fired,
        "should_fire": should_fire,
        "procedure": procedure,
    }
    if band is not None:
        row["band"] = band
    if triple is not None:
        row["triple"] = triple
    if route is not None:
        row["route"] = route
    if routes is not None:
        row["routes"] = routes
    if kind is not None:
        row["kind"] = kind
    return row


def triple_rows(name: str, *, band: str, correct: bool, repeats: int = 1) -> list[dict[str, Any]]:
    """One positive and two negatives from one body, all right or all wrong.

    The maximally-correlated case on purpose: it is where an item-level
    bootstrap is most wrong, so it is where the clustered one has to differ.
    """
    return [
        rec(
            f"{name}{suffix}",
            fired=(correct if positive else not correct),
            should_fire=positive,
            repeat=repeat,
            band=band,
            triple=name,
        )
        for repeat in range(repeats)
        for suffix, positive in (("p", True), ("n1", False), ("n2", False))
    ]


# --------------------------------------------------------------------------- #
# 1. The unpaired two-group cluster bootstrap. The one with no prior
#    implementation, and the one the experiment rests on.
# --------------------------------------------------------------------------- #


def clustered_draw(
    rng: np.random.Generator,
    mu: float,
    n_clusters: int,
    *,
    sigma: float = 0.80,
    size: int = 3,
    repeats: int = 2,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-item rates from a cluster random-effects model, and their labels.

    A cluster's difficulty shifts every item in it on the logit scale, which is
    the generative form of "three turns sharing a body move together". Each item
    is then observed at ``repeats`` Bernoulli draws, so the value lands on the
    same ``{0, 0.5, 1}`` grid a two-repeat run produces.
    """
    offsets = rng.normal(0.0, sigma, n_clusters)
    latent = np.log(mu / (1.0 - mu)) + offsets
    probabilities = np.repeat(1.0 / (1.0 + np.exp(-latent)), size)
    hits = rng.binomial(repeats, probabilities)
    return hits / repeats, np.repeat(np.arange(n_clusters), size)


def true_difference(mu_control: float, mu_treatment: float, sigma: float = 0.80) -> float:
    """The estimand: the difference of the two marginal means, not of the two ``mu``.

    ``mu`` is a median on the logit scale, and averaging over the cluster
    random effect pulls both marginal means toward 0.5 by different amounts.
    Testing coverage against ``mu_treatment - mu_control`` would be testing the
    estimator against the wrong number, which would show up as undercoverage and
    be blamed on the bootstrap.
    """
    rng = np.random.default_rng(20260813)
    draws = rng.normal(0.0, sigma, 2_000_000)
    marginal = [
        float((1.0 / (1.0 + np.exp(-(np.log(mu / (1.0 - mu)) + draws)))).mean())
        for mu in (mu_control, mu_treatment)
    ]
    return marginal[1] - marginal[0]


class TestTwoSampleClusterBootstrap:
    """S+M is 72 items in 24 triples, L+XL is 48 in 16. Nothing pairs them."""

    def test_it_detects_a_real_difference(self) -> None:
        """True difference 0.20. The interval must exclude zero."""
        rng = np.random.default_rng(1)
        control, control_clusters = clustered_draw(rng, 0.60, 16)
        treatment, treatment_clusters = clustered_draw(rng, 0.80, 24)
        result = cluster_bootstrap_two_sample(
            control, control_clusters, treatment, treatment_clusters, seed=0
        )
        assert result.point_estimate > 0.10
        assert result.excludes_zero, "a 20-point difference at 40 clusters must be visible"

    def test_it_stays_silent_on_no_difference(self) -> None:
        """True difference 0. The interval must cover zero.

        This is the standing-rule-2 half: an estimator that reports an effect
        when there is none is worse than one that reports nothing.
        """
        rng = np.random.default_rng(2)
        control, control_clusters = clustered_draw(rng, 0.75, 16)
        treatment, treatment_clusters = clustered_draw(rng, 0.75, 24)
        result = cluster_bootstrap_two_sample(
            control, control_clusters, treatment, treatment_clusters, seed=0
        )
        assert not result.excludes_zero
        assert result.ci_low < 0.0 < result.ci_high

    def test_clustering_widens_the_interval_on_correlated_triples(self) -> None:
        """The evidence that the cluster label is not being ignored.

        Every item in a cluster carries the same value, so the corpus holds 40
        independent observations and not 120. Resampling items pretends it holds
        120, and the interval it returns is too narrow — wrong in the
        anti-conservative direction, which is the one that publishes an effect
        that is not there.
        """
        rng = np.random.default_rng(3)
        offsets_control = rng.uniform(0.2, 1.0, 16)
        offsets_treatment = rng.uniform(0.3, 1.0, 24)
        control = np.repeat(offsets_control, 3)
        treatment = np.repeat(offsets_treatment, 3)
        control_clusters = np.repeat(np.arange(16), 3)
        treatment_clusters = np.repeat(np.arange(24), 3)

        clustered = cluster_bootstrap_two_sample(
            control, control_clusters, treatment, treatment_clusters, seed=0
        )
        per_item = cluster_bootstrap_two_sample(
            control,
            np.arange(control.size),
            treatment,
            np.arange(treatment.size),
            seed=0,
        )
        assert clustered.width > per_item.width * 1.5, (
            f"clustered {clustered.width:.4f} against item-level {per_item.width:.4f}; "
            "if these agree the cluster label is being ignored"
        )
        assert clustered.icc > 0.9, "identical within a cluster is ICC 1 up to estimation"
        assert clustered.design_effect > 2.5
        assert clustered.effective_n < 60.0

    def test_it_reduces_to_the_item_bootstrap_when_every_cluster_is_a_singleton(self) -> None:
        rng = np.random.default_rng(4)
        control = rng.uniform(0, 1, 30)
        treatment = rng.uniform(0, 1, 20)
        result = cluster_bootstrap_two_sample(
            control, np.arange(30), treatment, np.arange(20), seed=5
        )
        assert result.icc == 0.0
        assert result.design_effect == 1.0
        assert result.effective_n == pytest.approx(50.0)

    def test_the_icc_is_taken_after_centring_each_group(self) -> None:
        """A large group difference must not be read as agreement inside clusters.

        Without centring, two groups 0.5 apart look like every cluster agreeing
        with itself, the ICC saturates, and the design effect reports the effect
        being measured rather than the clustering.
        """
        control = np.repeat(np.arange(16), 3) * 0.0 + np.tile([0.1, 0.5, 0.9], 16)
        treatment = np.tile([0.6, 1.0, 0.8], 24)
        result = cluster_bootstrap_two_sample(
            control,
            np.repeat(np.arange(16), 3),
            treatment,
            np.repeat(np.arange(24), 3),
            seed=0,
        )
        assert result.point_estimate == pytest.approx(0.3, abs=1e-9)
        assert result.icc == 0.0, "no within-cluster agreement once the group means are out"

    def test_the_same_seed_gives_the_same_interval(self) -> None:
        rng = np.random.default_rng(6)
        control, control_clusters = clustered_draw(rng, 0.7, 16)
        treatment, treatment_clusters = clustered_draw(rng, 0.8, 24)
        first = cluster_bootstrap_two_sample(
            control, control_clusters, treatment, treatment_clusters, seed=42, n_resamples=500
        )
        second = cluster_bootstrap_two_sample(
            control, control_clusters, treatment, treatment_clusters, seed=42, n_resamples=500
        )
        assert (first.ci_low, first.ci_high) == (second.ci_low, second.ci_high)

    def test_a_known_good_call_is_accepted_before_any_refusal_is_believed(self) -> None:
        """Standing rule 2, stated as a test rather than as a comment."""
        result = cluster_bootstrap_two_sample(
            [0.0, 1.0, 0.5, 1.0],
            ["a", "a", "b", "b"],
            [1.0, 1.0, 0.5, 0.0],
            ["c", "c", "d", "d"],
            n_resamples=200,
            seed=0,
        )
        assert result.n_clusters_control == 2
        assert result.n_clusters_treatment == 2
        assert result.n_items_control == 4

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"n_resamples": 0}, "n_resamples must be >= 1"),
            ({"confidence": 0.0}, r"confidence must be in \(0, 1\)"),
            ({"confidence": 1.0}, r"confidence must be in \(0, 1\)"),
        ],
    )
    def test_it_refuses_impossible_parameters(self, kwargs: dict[str, Any], match: str) -> None:
        with pytest.raises(ValueError, match=match):
            cluster_bootstrap_two_sample([0.0, 1.0], ["a", "b"], [1.0, 0.0], ["c", "d"], **kwargs)

    def test_it_refuses_a_group_that_falls_in_one_cluster(self) -> None:
        """A single cluster resamples to itself, contributing no width at all."""
        with pytest.raises(ValueError, match="treatment falls in a single cluster"):
            cluster_bootstrap_two_sample(
                [0.0, 1.0], ["a", "b"], [1.0, 0.0], ["c", "c"], n_resamples=50
            )

    def test_it_refuses_a_group_whose_labels_do_not_match_its_values(self) -> None:
        with pytest.raises(ValueError, match="control and control_clusters must be the same"):
            cluster_bootstrap_two_sample(
                [0.0, 1.0, 0.5], ["a", "b"], [1.0, 0.0], ["c", "d"], n_resamples=50
            )

    def test_it_refuses_a_two_dimensional_group(self) -> None:
        with pytest.raises(ValueError, match="treatment must be one-dimensional"):
            cluster_bootstrap_two_sample(
                [0.0, 1.0], ["a", "b"], [[1.0, 0.0]], ["c", "d"], n_resamples=50
            )

    def test_the_two_groups_may_reuse_the_same_cluster_labels(self) -> None:
        """Labels are namespaced by group, so `t01` in both is two clusters."""
        result = cluster_bootstrap_two_sample(
            [0.0, 0.0, 1.0, 1.0],
            ["t01", "t01", "t02", "t02"],
            [1.0, 1.0, 0.0, 0.0],
            ["t01", "t01", "t02", "t02"],
            n_resamples=200,
            seed=0,
        )
        assert result.n_clusters_control == 2
        assert result.n_clusters_treatment == 2

    @settings(deadline=None, max_examples=25, suppress_health_check=[HealthCheck.too_slow])
    @given(
        control=st.lists(st.floats(0.0, 1.0, allow_nan=False), min_size=2, max_size=12),
        treatment=st.lists(st.floats(0.0, 1.0, allow_nan=False), min_size=2, max_size=12),
    )
    def test_the_point_estimate_is_always_the_observed_mean_difference(
        self, control: list[float], treatment: list[float]
    ) -> None:
        """Resampling may not move the estimate, only the interval around it."""
        result = cluster_bootstrap_two_sample(
            control,
            np.arange(len(control)),
            treatment,
            np.arange(len(treatment)),
            n_resamples=50,
            seed=0,
        )
        assert result.point_estimate == pytest.approx(
            float(np.mean(treatment)) - float(np.mean(control))
        )
        assert result.ci_low <= result.ci_high

    @settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.too_slow])
    @given(values=st.lists(st.floats(0.0, 1.0, allow_nan=False), min_size=3, max_size=10))
    def test_a_group_against_itself_centres_on_zero(self, values: list[float]) -> None:
        result = cluster_bootstrap_two_sample(
            values,
            np.arange(len(values)),
            values,
            np.arange(len(values)),
            n_resamples=200,
            seed=1,
        )
        assert result.point_estimate == pytest.approx(0.0, abs=1e-12)
        assert result.ci_low <= 0.0 <= result.ci_high

    def test_it_agrees_with_the_paired_form_when_the_paired_form_applies(self) -> None:
        """Two groups drawn from one set of clusters, one all-zero.

        The paired bootstrap against a control of zeros is how `bootstrap_rate`
        gets a one-sample interval. Running the unpaired form on the same values
        against a zero group whose clusters are singletons must land close to
        it: the same estimand, resampled with one extra source of noise that the
        zeros cannot contribute.
        """
        rng = np.random.default_rng(9)
        values, clusters = clustered_draw(rng, 0.75, 20)
        paired = cluster_bootstrap_diff(
            np.zeros_like(values), values, clusters, n_resamples=4000, seed=0
        )
        unpaired = cluster_bootstrap_two_sample(
            np.zeros_like(values),
            np.arange(values.size),
            values,
            clusters,
            n_resamples=4000,
            seed=0,
        )
        assert unpaired.point_estimate == pytest.approx(paired.point_estimate)
        assert unpaired.ci_low == pytest.approx(paired.ci_low, abs=0.02)
        assert unpaired.ci_high == pytest.approx(paired.ci_high, abs=0.02)


@pytest.mark.slow
def test_the_nominal_interval_covers_the_truth_at_about_its_nominal_rate() -> None:
    """Coverage simulation. **The test that says the interval means anything.**

    Data are generated under a known true difference, the estimator is run many
    times, and the share of intervals containing the truth is counted. An
    interval that covers 80% of the time is not a 95% interval, and nothing
    about its output would say so.

    Run at 16 and 24 clusters — the real L+XL and S+M counts — because coverage
    of a percentile bootstrap is governed by the number of clusters, not by the
    number of items, and quoting a coverage measured at 200 clusters would be
    quoting a different estimator.

    **Realised coverage: 0.926 over 2,000 replications at 600 resamples**
    (Monte Carlo standard error 0.005), against a nominal 0.95.

    The shortfall is real, it is about two and a half points, and it is the
    cluster *count* rather than anything about the estimator. A sweep at 2,000
    replications each, run before this test was written:

    ======================================  ========  ========
    setting                                 truth     coverage
    ======================================  ========  ========
    0.80 → 0.90, 16 / 24 clusters           +0.1042   0.9325
    0.80 → 0.80, 16 / 24 clusters (null)    −0.0002   0.9310
    0.50 → 0.60, 16 / 24 clusters           +0.0878   0.9295
    0.80 → 0.90, 60 / 90 clusters           +0.1042   0.9460
    ======================================  ========  ========

    Three things follow. The shortfall does **not** come from the ceiling at 1.0
    — it is the same at a base rate of 0.5, where there is no ceiling. It is not
    an artefact of a non-null truth — the null row is no better. And it goes
    away as clusters are added, which is what small-sample percentile-bootstrap
    behaviour looks like and what a bug does not.

    So a band read off this interval at the real corpus size is **very slightly
    liberal**: a nominal 95% interval is really about a 93% one. That belongs in
    the run's README, and it is not worth correcting with a BCa interval that
    nobody here could check. It is asserted loosely below so the test measures
    the estimator rather than the seed.
    """
    control_mu, treatment_mu = 0.80, 0.90
    truth = true_difference(control_mu, treatment_mu)
    rng = np.random.default_rng(11)
    covered = 0
    replications = 300
    for _ in range(replications):
        control, control_clusters = clustered_draw(rng, control_mu, 16)
        treatment, treatment_clusters = clustered_draw(rng, treatment_mu, 24)
        result = cluster_bootstrap_two_sample(
            control,
            control_clusters,
            treatment,
            treatment_clusters,
            n_resamples=500,
            seed=int(rng.integers(0, 2**31)),
        )
        covered += result.ci_low <= truth <= result.ci_high
    realised = covered / replications
    assert 0.88 <= realised <= 0.99, (
        f"realised coverage {realised:.3f} at 16/24 clusters. Below 0.88 the interval is "
        "not a 95% interval and no band read from it means what it says."
    )


# --------------------------------------------------------------------------- #
# 1b. The same estimator, driven from checkpoint records.
# --------------------------------------------------------------------------- #


class TestBootstrapRateDifference:
    """Q1: does firing accuracy fall on the long bands?"""

    SHORT: ClassVar[list[dict[str, Any]]] = [
        *triple_rows("s01", band="s", correct=True, repeats=2),
        *triple_rows("s02", band="s", correct=True, repeats=2),
        *triple_rows("m01", band="m", correct=True, repeats=2),
        *triple_rows("m02", band="m", correct=True, repeats=2),
    ]
    LONG_FLAT: ClassVar[list[dict[str, Any]]] = [
        *triple_rows("l01", band="l", correct=True, repeats=2),
        *triple_rows("l02", band="l", correct=True, repeats=2),
        *triple_rows("x01", band="xl", correct=True, repeats=2),
        *triple_rows("x02", band="xl", correct=True, repeats=2),
    ]
    LONG_WORSE: ClassVar[list[dict[str, Any]]] = [
        *triple_rows("l01", band="l", correct=False, repeats=2),
        *triple_rows("l02", band="l", correct=False, repeats=2),
        *triple_rows("x01", band="xl", correct=True, repeats=2),
        *triple_rows("x02", band="xl", correct=False, repeats=2),
    ]

    def test_it_separates_bands_that_differ(self) -> None:
        result = bootstrap_rate_difference(
            self.LONG_WORSE,
            self.SHORT,
            name_control="L+XL",
            name_treatment="S+M",
            seed=0,
        )
        assert result.difference == pytest.approx(0.75)
        assert result.excludes_zero
        assert not result.within(-0.05, 0.10), "the registered Q1 band must not contain this"

    def test_it_does_not_separate_bands_that_agree(self) -> None:
        result = bootstrap_rate_difference(
            self.LONG_FLAT,
            self.SHORT,
            name_control="L+XL",
            name_treatment="S+M",
            seed=0,
        )
        assert result.difference == pytest.approx(0.0)
        assert result.within(-0.05, 0.10)

    def test_it_reports_both_denominators(self) -> None:
        """Uneven repeats are the resumed-run state, and the two answers differ."""
        long_uneven = [*self.LONG_WORSE, *triple_rows("l03", band="l", correct=True, repeats=6)]
        result = bootstrap_rate_difference(long_uneven, self.SHORT, seed=0)
        assert result.rate_control != pytest.approx(result.accuracy_control_over_records), (
            "18 rows from one triple against 24 from four: the weightings must diverge"
        )

    def test_it_refuses_overlapping_groups(self) -> None:
        with pytest.raises(ArmError, match="share 12 case id"):
            bootstrap_rate_difference(self.SHORT, self.SHORT, seed=0)

    def test_it_refuses_a_group_in_a_single_cluster(self) -> None:
        with pytest.raises(ArmError, match="falls in a single cluster"):
            bootstrap_rate_difference(
                triple_rows("l01", band="l", correct=True), self.SHORT, seed=0
            )

    def test_a_positives_only_split_says_the_clustering_did_nothing(self) -> None:
        """Each triple is one positive and two negatives, so recall has no clusters.

        40 positives in 40 triples is 40 clusters of one. The design effect is
        1.000 by arithmetic rather than by measurement, and the pre-registration
        expects the length effect in *recall* on XL — 7 positives, 7 clusters.
        Describing that interval as clustered would be a word rather than a
        method, so the result says so and the formatter prints it.
        """
        result = bootstrap_rate_difference(
            [row for row in self.LONG_WORSE if row["should_fire"]],
            [row for row in self.SHORT if row["should_fire"]],
            seed=0,
        )
        assert result.clustering_is_inert
        assert result.design_effect == 1.0
        assert "CLUSTERING DID NOTHING" in "\n".join(format_difference(result))

    def test_a_clustered_split_does_not_claim_the_clustering_was_inert(self) -> None:
        """The known-good half: on real triples the flag must stay down."""
        result = bootstrap_rate_difference(self.LONG_WORSE, self.SHORT, seed=0)
        assert not result.clustering_is_inert
        assert "CLUSTERING DID NOTHING" not in "\n".join(format_difference(result))

    def test_the_interval_width_is_the_distance_between_the_bounds(self) -> None:
        result = bootstrap_rate_difference(self.LONG_WORSE, self.SHORT, seed=0)
        assert result.width == pytest.approx(result.ci_high - result.ci_low)

    def test_an_entirely_unparseable_group_is_refused(self) -> None:
        """The record-weighted figure has no denominator, and 0.000 is not it."""
        unparseable = [
            rec(f"u0{i}", fired=None, should_fire=True, band="l", triple=f"u0{i}") for i in range(3)
        ]
        with pytest.raises(ArmError, match="unparseable"):
            bootstrap_rate_difference(unparseable, self.SHORT, seed=0)

    def test_the_report_names_both_groups_and_the_registered_denominator(self) -> None:
        lines = "\n".join(
            format_difference(
                bootstrap_rate_difference(
                    self.LONG_WORSE, self.SHORT, name_control="L+XL", name_treatment="S+M", seed=0
                )
            )
        )
        assert "S+M" in lines
        assert "L+XL" in lines
        assert "the registered denominator" in lines


# --------------------------------------------------------------------------- #
# 2. Routing accuracy per procedure, under a rule the caller must name.
# --------------------------------------------------------------------------- #


def routed(case: str, *, wanted: list[str], named: str | None, repeat: int = 0) -> dict[str, Any]:
    return rec(
        case,
        fired=named is not None,
        should_fire=True,
        repeat=repeat,
        route=wanted[0],
        routes=wanted,
        procedure=named,
        band="s",
        triple=case,
    )


class TestRoutingByProcedure:
    """Q3: `ledger` is the worst-routed of the four procedures."""

    #: `ledger` wrong twice, everything else right. The groups must separate.
    DIFFERING: ClassVar[list[dict[str, Any]]] = [
        routed("p01", wanted=["ledger"], named="fit"),
        routed("p02", wanted=["ledger"], named="cascade"),
        routed("p03", wanted=["ledger"], named="ledger"),
        routed("p04", wanted=["fit"], named="fit"),
        routed("p05", wanted=["fit"], named="fit"),
        routed("p06", wanted=["timing"], named="timing"),
    ]
    #: Everything right. Nothing may separate.
    FLAT: ClassVar[list[dict[str, Any]]] = [
        routed("p01", wanted=["ledger"], named="ledger"),
        routed("p02", wanted=["ledger"], named="ledger"),
        routed("p04", wanted=["fit"], named="fit"),
        routed("p06", wanted=["timing"], named="timing"),
    ]
    #: The three real dual-route positives, and one single-route case each way.
    DUAL: ClassVar[list[dict[str, Any]]] = [
        routed("s04p", wanted=["cascade", "timing"], named="timing"),
        routed("s08p", wanted=["timing", "cascade"], named="cascade"),
        routed("s13p", wanted=["timing", "cascade"], named="timing"),
        routed("s20p", wanted=["cascade"], named="cascade"),
        routed("s21p", wanted=["timing"], named="timing"),
    ]

    def test_the_groups_separate_when_one_procedure_routes_worse(self) -> None:
        result = routing_by_procedure(self.DIFFERING, rule="first")
        assert result.groups["ledger"].over_items == pytest.approx(1 / 3)
        assert result.groups["fit"].over_items == 1.0
        assert result.groups["timing"].over_items == 1.0
        assert min(result.groups, key=lambda name: result.groups[name].over_items) == "ledger"

    def test_the_groups_do_not_separate_when_nothing_differs(self) -> None:
        """The half that says the estimator is not simply always splitting."""
        result = routing_by_procedure(self.FLAT, rule="first")
        assert {group.over_items for group in result.groups.values()} == {1.0}

    def test_the_two_rules_disagree_on_the_verdicts(self) -> None:
        """`s04p` names its second route. One rule calls that right; one does not."""
        first = routing_by_procedure(self.DUAL, rule="first")
        any_of = routing_by_procedure(self.DUAL, rule="any")
        assert first.groups["cascade"].over_items == pytest.approx(0.5)
        assert any_of.groups["cascade"].over_items == 1.0

    def test_the_two_rules_disagree_on_the_denominators(self) -> None:
        """A dual-route turn is one item under `first` and two under `any`.

        On the real corpus this is 8 / 8 / 7 / 10 against 8 / 10 / 8 / 10, and a
        number quoted without its rule is quoted without its denominator too.
        """
        first = routing_by_procedure(self.DUAL, rule="first")
        any_of = routing_by_procedure(self.DUAL, rule="any")
        assert {name: group.n_items for name, group in first.groups.items()} == {
            "cascade": 2,
            "timing": 3,
        }
        assert {name: group.n_items for name, group in any_of.groups.items()} == {
            "cascade": 4,
            "timing": 4,
        }
        assert first.n_items == any_of.n_items == 5
        assert sum(g.n_items for g in any_of.groups.values()) > any_of.n_items

    def test_the_rule_is_carried_on_the_result_and_on_every_group(self) -> None:
        """So a figure lifted into a sentence keeps its rule."""
        result = routing_by_procedure(self.DUAL, rule="any")
        assert result.rule == "any"
        assert {group.rule for group in result.groups.values()} == {"any"}
        assert "'any'" in "\n".join(format_routing(result))

    def test_there_is_no_default_rule(self) -> None:
        with pytest.raises(TypeError):
            routing_by_procedure(self.DUAL)  # type: ignore[call-arg]

    def test_an_unknown_rule_is_refused(self) -> None:
        with pytest.raises(ArmError, match="rule must be one of"):
            routing_by_procedure(self.DUAL, rule="closest")  # type: ignore[arg-type]

    def test_the_membership_rule_refuses_records_carrying_only_the_first_route(self) -> None:
        """`route` is `routes[0]`. Scoring `any` against it is the other rule."""
        rows = [{key: value for key, value in row.items() if key != "routes"} for row in self.DUAL]
        assert routing_by_procedure(rows, rule="first").groups, "the known-good half"
        with pytest.raises(ArmError, match="carries only `route`"):
            routing_by_procedure(rows, rule="any")

    def test_a_supplied_routes_mapping_overrides_the_records(self) -> None:
        rows = [{key: value for key, value in row.items() if key != "routes"} for row in self.DUAL]
        result = routing_by_procedure(
            rows,
            rule="any",
            routes={
                "s04p": ("cascade", "timing"),
                "s08p": ("timing", "cascade"),
                "s13p": ("timing", "cascade"),
                "s20p": ("cascade",),
                "s21p": ("timing",),
            },
        )
        assert result.groups["cascade"].over_items == 1.0

    def test_a_labelled_case_missing_from_the_mapping_is_refused(self) -> None:
        with pytest.raises(ArmError, match="absent from the supplied `routes` mapping"):
            routing_by_procedure(self.DUAL, rule="any", routes={"s04p": ("cascade",)})

    def test_an_empty_route_tuple_in_the_mapping_is_refused(self) -> None:
        with pytest.raises(ArmError, match="empty route tuple"):
            routing_by_procedure([self.DUAL[0]], rule="any", routes={"s04p": ()})

    def test_records_with_no_route_label_are_refused_rather_than_scored_as_zero(self) -> None:
        with pytest.raises(ArmError, match="no parsed record carries a route label"):
            routing_by_procedure(
                [rec("n1", fired=False, should_fire=False, band="s", triple="t")], rule="first"
            )

    def test_the_item_and_record_denominators_are_both_reported(self) -> None:
        rows = [
            routed("p01", wanted=["ledger"], named="ledger", repeat=0),
            routed("p01", wanted=["ledger"], named="fit", repeat=1),
            routed("p02", wanted=["ledger"], named="fit", repeat=0),
        ]
        group = routing_by_procedure(rows, rule="first").groups["ledger"]
        assert group.n_items == 2
        assert group.n_records == 3
        assert group.over_items == pytest.approx(0.25), "0.5 and 0.0, averaged over items"
        assert group.over_records == pytest.approx(1 / 3), "one correct row in three"

    def test_a_group_that_never_answered_reports_none_rather_than_zero(self) -> None:
        rows = [routed("p01", wanted=["ledger"], named=None)]
        group = routing_by_procedure(rows, rule="first").groups["ledger"]
        assert group.n_answered == 0
        assert group.over_answered is None
        assert "--" in "\n".join(format_routing(routing_by_procedure(rows, rule="first")))

    def test_unparseable_rows_are_dropped_and_not_scored_as_misroutes(self) -> None:
        rows = [
            *self.FLAT,
            rec("p99", fired=None, should_fire=True, route="ledger", routes=["ledger"]),
        ]
        result = routing_by_procedure(rows, rule="first")
        assert result.groups["ledger"].n_items == 2, "p99 has no verdict, not a wrong one"


# --------------------------------------------------------------------------- #
# 3. False-positive rate per negative kind.
# --------------------------------------------------------------------------- #


def negative(case: str, *, kind: str, fired: bool | None, repeat: int = 0) -> dict[str, Any]:
    return rec(
        case, fired=fired, should_fire=False, repeat=repeat, kind=kind, band="s", triple=case
    )


class TestFalsePositiveRateByKind:
    """Q4: `settled` has the highest FPR of the seven kinds."""

    #: `settled` fires, `lookup` does not. The groups must separate.
    DIFFERING: ClassVar[list[dict[str, Any]]] = [
        *[negative(f"set{i}", kind="settled", fired=True) for i in range(5)],
        *[negative(f"look{i}", kind="lookup", fired=False) for i in range(27)],
    ]
    #: Nothing fires anywhere. Nothing may separate.
    FLAT: ClassVar[list[dict[str, Any]]] = [
        *[negative(f"set{i}", kind="settled", fired=False) for i in range(5)],
        *[negative(f"look{i}", kind="lookup", fired=False) for i in range(27)],
    ]

    def test_summarise_cannot_answer_this_question_at_all(self) -> None:
        """Why the function exists: a kind subgroup is all negatives by definition."""
        with pytest.raises(ArmError, match="an arm needs both labels"):
            summarise([row for row in self.DIFFERING if row["kind"] == "settled"])

    def test_the_kinds_separate_when_one_fires_and_another_does_not(self) -> None:
        kinds = false_positive_rate_by_kind(self.DIFFERING)
        assert kinds["settled"].over_items == 1.0
        assert kinds["lookup"].over_items == 0.0
        assert kinds["settled"].separated_from(kinds["lookup"])
        assert max(kinds, key=lambda name: kinds[name].over_items) == "settled"

    def test_the_kinds_do_not_separate_when_nothing_fires(self) -> None:
        kinds = false_positive_rate_by_kind(self.FLAT)
        assert {rate.over_items for rate in kinds.values()} == {0.0}
        assert not kinds["settled"].separated_from(kinds["lookup"])

    def test_a_five_item_group_reading_zero_carries_an_interval_that_says_so(self) -> None:
        """**The point of returning an interval.**

        At a plausible false-positive rate near 0.02 a five-item group reads
        exactly 0.000 the large majority of the time. The rate alone is
        indistinguishable from evidence of a floor; ``[0.000, 0.434]`` beside it
        is not, and the twenty-seven-item group's interval is less than half as
        wide on the same point estimate.
        """
        kinds = false_positive_rate_by_kind(self.FLAT)
        assert kinds["settled"].over_items == 0.0
        assert kinds["settled"].ci_low == 0.0
        assert kinds["settled"].ci_high == pytest.approx(0.434, abs=0.01)
        assert kinds["lookup"].ci_high < 0.2
        assert kinds["settled"].width > 2 * kinds["lookup"].width

    def test_every_group_carries_its_denominator(self) -> None:
        kinds = false_positive_rate_by_kind(self.DIFFERING)
        assert kinds["settled"].n_items == 5
        assert kinds["lookup"].n_items == 27
        assert list(kinds) == ["lookup", "settled"], "largest group first"
        lines = "\n".join(format_negative_kinds(kinds))
        assert "items" in lines
        assert "[0.000," in lines or "[0.566," in lines

    def test_the_item_and_record_denominators_are_both_reported(self) -> None:
        rows = [
            negative("s1", kind="settled", fired=True, repeat=0),
            negative("s1", kind="settled", fired=False, repeat=1),
            negative("s2", kind="settled", fired=False, repeat=0),
        ]
        rate = false_positive_rate_by_kind(rows)["settled"]
        assert rate.n_items == 2
        assert rate.n_records == 3
        assert rate.over_items == pytest.approx(0.25)
        assert rate.over_records == pytest.approx(1 / 3)
        assert rate.fired_on == ("s1",)

    def test_a_version_two_checkpoint_is_refused_rather_than_returning_an_empty_table(
        self,
    ) -> None:
        assert false_positive_rate_by_kind(self.FLAT), "the known-good half"
        with pytest.raises(ArmError, match="no record carries a `kind`"):
            false_positive_rate_by_kind(
                [rec("n1", fired=False, should_fire=False, band="s", triple="t")]
            )

    def test_a_positive_carrying_a_kind_is_refused(self) -> None:
        rows = [*self.FLAT, rec("p1", fired=True, should_fire=True, kind="settled")]
        with pytest.raises(ArmError, match="labelled a positive"):
            false_positive_rate_by_kind(rows)

    def test_a_kind_whose_every_row_is_unparseable_is_refused(self) -> None:
        rows = [*self.FLAT, negative("m1", kind="meta", fired=None)]
        with pytest.raises(ArmError, match="every record of kind 'meta' is unparseable"):
            false_positive_rate_by_kind(rows)

    @pytest.mark.parametrize("confidence", [0.0, 1.0, 1.5])
    def test_an_impossible_confidence_is_refused(self, confidence: float) -> None:
        with pytest.raises(ArmError, match=r"confidence must be in \(0, 1\)"):
            false_positive_rate_by_kind(self.FLAT, confidence=confidence)

    def test_a_wider_confidence_gives_a_wider_interval(self) -> None:
        narrow = false_positive_rate_by_kind(self.FLAT, confidence=0.80)["settled"]
        wide = false_positive_rate_by_kind(self.FLAT, confidence=0.99)["settled"]
        assert wide.width > narrow.width


# --------------------------------------------------------------------------- #
# 4. The four defects an independent confirmation pass found in the per-band
#    machinery, each with the known-good case the guard has to pass first.
# --------------------------------------------------------------------------- #


class TestBandDenominators:
    """A denominator that moves without saying so is this instrument's signature failure."""

    #: The confirmation pass's own repro: two banded rows, two unbanded.
    MIXED: ClassVar[list[dict[str, Any]]] = [
        rec("a", fired=True, should_fire=True, band="s", triple="t1"),
        rec("b", fired=False, should_fire=False, band="s", triple="t1"),
        rec("c", fired=True, should_fire=False),
        rec("d", fired=False, should_fire=True),
    ]

    def test_a_fully_banded_checkpoint_is_accepted(self) -> None:
        """Standing rule 2. Run the guard against the case it must pass."""
        rows = [
            *triple_rows("s01", band="s", correct=True),
            *triple_rows("x01", band="xl", correct=False),
        ]
        bands = summarise_by_band(rows)
        assert set(bands) == {"s", "xl"}
        assert summarise(rows).accuracy == pytest.approx(0.5)

    def test_partial_band_labelling_is_refused(self) -> None:
        """0.500 pooled became 1.000 per band, and the printed `n` gave no hint."""
        assert summarise(self.MIXED).accuracy == pytest.approx(0.5)
        with pytest.raises(ArmError, match=r"2 of 4 record\(s\) carry no `band`"):
            summarise_by_band(self.MIXED)

    def test_a_blank_band_is_refused(self) -> None:
        rows = [
            *triple_rows("s01", band="s", correct=True),
            *triple_rows("z01", band="  ", correct=False),
        ]
        with pytest.raises(ArmError, match="blank `band`"):
            summarise_by_band(rows)

    def test_one_case_under_two_bands_is_refused(self) -> None:
        rows = [
            *triple_rows("s01", band="s", correct=True),
            rec("s01p", fired=True, should_fire=True, band="xl", triple="s01"),
        ]
        with pytest.raises(ArmError, match="appears under two bands"):
            summarise_by_band(rows)

    def test_a_band_name_the_corpus_does_not_declare_is_reported_not_hidden(self) -> None:
        """Kept rather than refused: an old checkpoint may predate a rename.

        What must not happen is that it goes by in silence, which is how a typo
        becomes a phantom band with a rate nobody can attribute.
        """
        rows = [
            *triple_rows("s01", band="s", correct=True),
            *triple_rows("z01", band="xxl", correct=False),
        ]
        bands = summarise_by_band(rows)
        assert bands.unrecognised == ("xxl",)
        assert "xxl" in "\n".join(format_bands(bands))

    def test_a_half_collected_band_can_be_reported_instead_of_killing_the_table(self) -> None:
        """A 720-call run designed to resume will be interrupted mid-band.

        `collect` iterates the positives before the negatives, so an interrupted
        run leaves exactly one band holding one label. Under `raise` that costs
        every other band's row too, which buys no correctness at all.
        """
        rows = [
            *triple_rows("s01", band="s", correct=True),
            *triple_rows("m01", band="m", correct=True),
            rec("x01p", fired=True, should_fire=True, band="xl", triple="x01"),
        ]
        with pytest.raises(ArmError, match="band 'xl' cannot be scored"):
            summarise_by_band(rows)

        bands = summarise_by_band(rows, on_unscoreable="report")
        assert set(bands) == {"s", "m"}
        assert [band for band, _ in bands.unscoreable] == ["xl"]
        assert "NOT SCORED  xl" in "\n".join(format_bands(bands))

    def test_reporting_still_refuses_when_no_band_can_be_scored(self) -> None:
        rows = [rec("x01p", fired=True, should_fire=True, band="xl", triple="x01")]
        with pytest.raises(ArmError, match="no band could be scored"):
            summarise_by_band(rows, on_unscoreable="report")

    def test_an_unknown_on_unscoreable_is_refused(self) -> None:
        with pytest.raises(ArmError, match="on_unscoreable must be"):
            summarise_by_band(
                triple_rows("s01", band="s", correct=True),
                on_unscoreable="ignore",  # type: ignore[arg-type]
            )

    def test_the_table_is_still_a_mapping(self) -> None:
        """`BandTable` subclasses `dict` so every existing caller keeps working."""
        bands = summarise_by_band(triple_rows("s01", band="s", correct=True))
        assert isinstance(bands, BandTable)
        assert isinstance(bands, dict)
        assert list(bands) == ["s"]
        assert bands == {"s": bands["s"]}

    def test_a_plain_mapping_still_formats(self) -> None:
        """`format_bands` takes a `Mapping`; only a `BandTable` has anything to add."""
        bands = summarise_by_band(triple_rows("s01", band="s", correct=True))
        lines = "\n".join(format_bands(dict(bands)))
        assert "  s   " in lines
        assert "NOT SCORED" not in lines


class TestItemVersusRecordWeighting:
    """Uneven repeats are the resumed-run state, and the two weightings diverge there."""

    #: `s` at three repeats, `xl` at two: 45% of the rows against 35% of the items.
    UNEVEN: ClassVar[list[dict[str, Any]]] = [
        *triple_rows("s01", band="s", correct=True, repeats=3),
        *triple_rows("s02", band="s", correct=False, repeats=3),
        *triple_rows("x01", band="xl", correct=False, repeats=2),
        *triple_rows("x02", band="xl", correct=False, repeats=2),
    ]

    def test_the_two_weightings_agree_when_the_repeats_are_even(self) -> None:
        """Standing rule 2: the new path must reproduce the old one where both apply."""
        rows = [
            *triple_rows("s01", band="s", correct=True, repeats=2),
            *triple_rows("x01", band="xl", correct=False, repeats=2),
        ]
        by_record = summarise(rows)
        by_item = summarise(rows, weight="item")
        assert by_item.accuracy == pytest.approx(by_record.accuracy)
        assert by_item.recall == pytest.approx(by_record.recall)
        assert by_item.precision == pytest.approx(by_record.precision)
        assert by_item.false_positive_rate == pytest.approx(by_record.false_positive_rate)

    def test_the_two_weightings_disagree_when_the_repeats_are_not(self) -> None:
        by_record = summarise(self.UNEVEN)
        by_item = summarise(self.UNEVEN, weight="item")
        assert by_record.accuracy != pytest.approx(by_item.accuracy)
        assert by_record.accuracy > by_item.accuracy, (
            "the over-collected short band is the one that is right, so row weighting "
            "flatters exactly the comparison the experiment is testing"
        )

    def test_the_weighting_is_carried_on_the_result_and_printed(self) -> None:
        assert summarise(self.UNEVEN).weight == "record"
        assert summarise(self.UNEVEN, weight="item").weight == "item"
        lines = "\n".join(format_bands(summarise_by_band(self.UNEVEN, weight="item")))
        assert "weighted by item" in lines

    def test_the_table_shows_rows_items_and_repeats_per_band(self) -> None:
        lines = "\n".join(format_bands(summarise_by_band(self.UNEVEN)))
        assert "items" in lines
        assert "reps" in lines
        assert "3.0" in lines, "the short band's repeat count, which the headline got wrong"

    def test_an_unknown_weight_is_refused(self) -> None:
        with pytest.raises(ArmError, match="weight must be"):
            summarise(self.UNEVEN, weight="mean")  # type: ignore[arg-type]

    def test_one_case_under_two_labels_is_refused(self) -> None:
        rows = [
            *triple_rows("s01", band="s", correct=True, repeats=2),
            rec("s01n1", fired=True, should_fire=True, band="s", triple="s01"),
        ]
        assert per_item_fire_rates(triple_rows("s01", band="s", correct=True)), "known-good"
        with pytest.raises(ArmError, match="appears with both labels"):
            summarise(rows, weight="item")


class TestClusterFieldRestriction:
    """`cluster_on` reaches every stratum the runner stamps, by a one-word slip."""

    ROWS: ClassVar[list[dict[str, Any]]] = [
        *triple_rows("s01", band="s", correct=True, repeats=2),
        *triple_rows("x01", band="xl", correct=False, repeats=2),
    ]

    def test_the_two_real_units_are_accepted(self) -> None:
        """Standing rule 2 before the refusal is believed."""
        assert bootstrap_rate(self.ROWS, cluster_on="triple", seed=0, n_resamples=200)
        assert bootstrap_rate(self.ROWS, cluster_on="case", seed=0, n_resamples=200)

    @pytest.mark.parametrize("field", ["band", "should_fire", "domain", "stakes", "kind"])
    def test_a_stratum_is_not_a_resampling_unit(self, field: str) -> None:
        with pytest.raises(ArmError, match="is not a resampling unit"):
            bootstrap_rate(self.ROWS, cluster_on=field, seed=0)

    def test_clustering_on_the_triple_is_wider_than_clustering_on_the_case(self) -> None:
        """The reason the restriction matters: the two answers differ."""
        clustered = bootstrap_rate(self.ROWS, cluster_on="triple", seed=0, n_resamples=2000)
        per_item = bootstrap_rate(self.ROWS, cluster_on="case", seed=0, n_resamples=2000)
        assert clustered.width > per_item.width
        assert clustered.icc > 0.5
        assert per_item.clustering_is_inert
        assert not clustered.clustering_is_inert
        assert "CLUSTERING DID NOTHING" in "\n".join(format_rate("per item", per_item))
        assert "CLUSTERING DID NOTHING" not in "\n".join(format_rate("clustered", clustered))
