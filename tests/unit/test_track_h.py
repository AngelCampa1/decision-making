"""Track H Phase 0 scoring: the J-equals-d identity, the clustering guard, the
falsifier gate, and the threshold's base-arm-only provenance.

Four proofs standing rule 2 and the H1 registration both ask for, each its own
section below:

1. Youden's J is numerically identical to the programme's ``d`` (module
   docstring's algebra, checked rather than trusted).
2. Clustering on the triplet gives a materially different interval than
   pooling over files/items — the exact defect ``docs/STATUS.md`` records as
   "pooled AUC used on a matched corpus".
3. The falsifier battery passes a known-good extractor and refuses on a
   known-bad one, and no ``Phase0Result`` is reachable without a passed
   battery.
4. The movement threshold is derivable from, and only from, base-arm records.

Everything else here is the ordinary edge-case sweep needed for the 100%
line+branch floor on ``decision_evals/stats``.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from decision_evals.stats.agreement import fleiss_kappa
from decision_evals.stats.cluster import cluster_bootstrap_diff
from decision_evals.stats.track_h import (
    ADEQUACY_CEILING,
    KILL_THRESHOLD_J,
    BaseRepeatPair,
    FalsifierBatteryFailedError,
    FalsifierBatteryResult,
    FalsifierCase,
    MovementThreshold,
    TripletEvent,
    classify_movement,
    compute_phase0_result,
    derive_movement_threshold,
    extractor_movement_agreement,
    relative_movement,
    run_falsifier_battery,
)

# --------------------------------------------------------------------------- #
# Shared fixtures
# --------------------------------------------------------------------------- #

#: A threshold with a round value, for tests that don't need to derive one.
THRESHOLD = MovementThreshold(value=0.10, n_base_pairs=20, max_triplet_id="t07")


def _events(
    n_triplets: int = 20,
    *,
    sensitivity_rate: float = 0.85,
    specificity_rate: float = 0.60,
    seed: int = 0,
) -> list[TripletEvent]:
    """40 synthetic Phase 0 events (n_triplets triplets x 2 repeats).

    Governing contrasts move at ``sensitivity_rate``; matched contrasts hold at
    ``specificity_rate``. Movement is encoded directly as a 10x jump (always
    above THRESHOLD) or a 0.1% wiggle (always below it), so the classification
    is unambiguous and the test is about the estimator, not the boundary.
    """
    rng = np.random.default_rng(seed)
    events: list[TripletEvent] = []
    for t in range(n_triplets):
        triplet_id = f"t{t:02d}"
        for repeat in (0, 1):
            q_base = 10.0
            q_governing = q_base * 10.0 if rng.random() < sensitivity_rate else q_base * 1.001
            q_matched = q_base * 10.0 if rng.random() < (1 - specificity_rate) else q_base * 1.001
            events.append(
                TripletEvent(
                    triplet_id=triplet_id,
                    repeat=repeat,
                    q_base=q_base,
                    q_governing=q_governing,
                    q_matched=q_matched,
                )
            )
    return events


def _passed_battery() -> FalsifierBatteryResult:
    cases = [
        FalsifierCase(
            name="obvious-move",
            q_base=10.0,
            q_governing=100.0,
            q_matched=10.05,
            expect_governing_change=True,
            expect_matched_change=False,
        ),
        FalsifierCase(
            name="obvious-still",
            q_base=20.0,
            q_governing=90.0,
            q_matched=20.02,
            expect_governing_change=True,
            expect_matched_change=False,
        ),
    ]
    return run_falsifier_battery(cases, THRESHOLD)


# --------------------------------------------------------------------------- #
# 1. J is identically d
# --------------------------------------------------------------------------- #


class TestJEqualsD:
    def test_j_equals_sensitivity_plus_specificity_minus_one(self) -> None:
        """J = sens + spec - 1, computed two independent ways, must agree.

        ``compute_phase0_result`` reports J as the cluster-bootstrap point
        estimate (mean(governing_change) - mean(matched_change)) and,
        separately, sensitivity and specificity as their own means. The
        registration's algebra says these must coincide; this asserts it
        numerically rather than trusting the derivation in the docstring.
        """
        events = _events(seed=1)
        battery = _passed_battery()
        result = compute_phase0_result(events, THRESHOLD, battery, seed=42)

        assert result.j == pytest.approx(result.sensitivity + result.specificity - 1.0, abs=1e-12)

    def test_j_equals_d_the_raw_paired_mean_difference(self) -> None:
        """d = P(change|governing) - P(change|matched), computed from raw
        indicator arrays with plain numpy, must equal the reported J exactly
        up to floating summation order.
        """
        events = _events(seed=2)
        battery = _passed_battery()
        result = compute_phase0_result(events, THRESHOLD, battery, seed=7)

        governing = np.array(
            [classify_movement(e.q_base, e.q_governing, THRESHOLD) for e in events],
            dtype=np.float64,
        )
        matched = np.array(
            [classify_movement(e.q_base, e.q_matched, THRESHOLD) for e in events],
            dtype=np.float64,
        )
        d = float(governing.mean() - matched.mean())

        assert result.j == pytest.approx(d, abs=1e-12)

    def test_symmetric_0_85_reaches_the_registered_kill_exactly(self) -> None:
        """0.85 + 0.85 - 1 == KILL_THRESHOLD_J, the arithmetic the registration
        checks rather than asserts. 34/40 on each arm is the reachable state at
        this resolution (0.85 * 40 == 34, an integer).
        """
        assert pytest.approx(KILL_THRESHOLD_J) == 0.85 + 0.85 - 1.0
        assert 0.85 * 40 == 34.0
        assert ADEQUACY_CEILING == 0.85


# --------------------------------------------------------------------------- #
# 2. Clustering on the triplet is not optional
# --------------------------------------------------------------------------- #


class TestClusteringVersusPooling:
    def test_pooling_over_items_gives_a_different_interval_than_clustering_on_triplets(
        self,
    ) -> None:
        """Matched-triplet data with strong within-triplet correlation, scored
        two ways: once clustered on the triplet id (correct — what
        ``compute_phase0_result`` always does) and once with every item its own
        singleton cluster (the "pooled over files" shape defect nine on
        ``docs/STATUS.md`` names). If clustering did nothing, the two intervals
        would coincide; they must not.
        """
        rng = np.random.default_rng(11)
        n_triplets = 20
        triplet_ids: list[str] = []
        diffs: list[float] = []
        # A large per-triplet random effect plus small item-level noise: high
        # within-triplet correlation, the shape Track H's matched design has.
        for t in range(n_triplets):
            triplet_effect = rng.normal(loc=0.3, scale=0.4)
            for _repeat in (0, 1):
                triplet_ids.append(f"t{t:02d}")
                diffs.append(triplet_effect + rng.normal(scale=0.02))

        zeros = np.zeros(len(diffs), dtype=np.float64)
        treatment = np.array(diffs, dtype=np.float64)

        clustered = cluster_bootstrap_diff(
            control=zeros, treatment=treatment, clusters=triplet_ids, seed=99
        )
        # "Pooled over files": every item is its own cluster, which is exactly
        # what an item-level (ordinary) bootstrap does.
        item_level_clusters = list(range(len(diffs)))
        pooled = cluster_bootstrap_diff(
            control=zeros, treatment=treatment, clusters=item_level_clusters, seed=99
        )

        clustered_width = clustered.ci_high - clustered.ci_low
        pooled_width = pooled.ci_high - pooled.ci_low

        # Point estimates agree (same data, same mean); only the interval,
        # which is what clustering actually changes, differs.
        assert clustered.point_estimate == pytest.approx(pooled.point_estimate)
        assert clustered.n_clusters == n_triplets
        assert pooled.n_clusters == len(diffs)
        assert clustered_width > pooled_width * 1.3, (
            f"clustering on the triplet ({clustered_width:.4f}) did not read materially "
            f"wider than pooling over items ({pooled_width:.4f}); clustering would be "
            "doing nothing"
        )

    def test_compute_phase0_result_clusters_on_triplet_not_on_event(self) -> None:
        """`Phase0Result.n_clusters` must equal the triplet count, not the
        event count -- the public entry point never exposes an item-level
        clustering option, which is what stops a caller from pooling by
        accident.
        """
        events = _events(n_triplets=20, seed=3)
        battery = _passed_battery()
        result = compute_phase0_result(events, THRESHOLD, battery, seed=5)

        assert result.n_clusters == 20
        assert result.n_sensitivity_events == 40
        assert result.n_specificity_events == 40


# --------------------------------------------------------------------------- #
# 3. The falsifier battery: known-good passes, known-bad refuses
# --------------------------------------------------------------------------- #


class TestFalsifierBattery:
    def test_known_good_extractor_passes_and_unlocks_a_result(self) -> None:
        """Standing rule 2: a falsifier must pass a known-good case before it
        may fail anything. Here the "known-good case" is an extractor that
        correctly reads two planted triplets -- obvious movement on governing,
        no movement on matched -- and the battery must score 1.0/1.0 and let
        `compute_phase0_result` proceed.
        """
        battery = _passed_battery()
        assert battery.passed
        assert battery.sensitivity == 1.0
        assert battery.specificity == 1.0
        assert battery.n_cases == 2

        events = _events(seed=4)
        result = compute_phase0_result(events, THRESHOLD, battery, seed=1)
        assert result.j == pytest.approx(result.sensitivity + result.specificity - 1.0)

    def test_known_bad_extractor_fails_the_battery_and_no_j_is_reported(self) -> None:
        """A planted case where the extractor cannot see the governing
        movement it obviously should (q_governing left at q_base) fails
        sensitivity, and `compute_phase0_result` must refuse outright -- not
        emit a J with a caveat attached.
        """
        cases = [
            FalsifierCase(
                name="obvious-move-but-extractor-blind",
                q_base=10.0,
                q_governing=10.001,  # should have moved to ~100; extractor missed it
                q_matched=10.02,
                expect_governing_change=True,
                expect_matched_change=False,
            ),
            FalsifierCase(
                name="obvious-still",
                q_base=20.0,
                q_governing=90.0,
                q_matched=20.02,
                expect_governing_change=True,
                expect_matched_change=False,
            ),
        ]
        battery = run_falsifier_battery(cases, THRESHOLD)

        assert not battery.passed
        assert battery.sensitivity == pytest.approx(0.5)
        assert battery.specificity == 1.0

        events = _events(seed=5)
        with pytest.raises(FalsifierBatteryFailedError, match="extractor is the finding"):
            compute_phase0_result(events, THRESHOLD, battery, seed=1)

    def test_known_bad_extractor_that_sees_movement_everywhere_fails_specificity(self) -> None:
        """The mirror-image known-bad case: an extractor that calls movement on
        the matched (non-governing) contrast it should have held still on.
        Specificity fails even though sensitivity is perfect, and the gate
        still refuses -- either half failing is enough.
        """
        cases = [
            FalsifierCase(
                name="obvious-move",
                q_base=10.0,
                q_governing=100.0,
                q_matched=95.0,  # matched should not have moved; extractor says it did
                expect_governing_change=True,
                expect_matched_change=False,
            ),
        ]
        battery = run_falsifier_battery(cases, THRESHOLD)

        assert not battery.passed
        assert battery.sensitivity == 1.0
        assert battery.specificity == 0.0

        with pytest.raises(FalsifierBatteryFailedError):
            compute_phase0_result(_events(seed=6), THRESHOLD, battery, seed=1)

    def test_run_falsifier_battery_refuses_empty_cases(self) -> None:
        with pytest.raises(ValueError, match="at least one planted case"):
            run_falsifier_battery([], THRESHOLD)


# --------------------------------------------------------------------------- #
# 4. The movement threshold is derived from, and only from, base-arm records
# --------------------------------------------------------------------------- #


class TestThresholdDerivation:
    def test_base_repeat_pair_carries_no_governing_or_matched_field(self) -> None:
        """The type itself is the enforcement: there is no field on
        `BaseRepeatPair` a caller could accidentally fill with a
        governing/matched-arm quantity.
        """
        field_names = {f.name for f in dataclasses.fields(BaseRepeatPair)}
        assert field_names == {"triplet_id", "q_repeat0", "q_repeat1"}

    def test_threshold_is_the_max_relative_base_vs_base_difference(self) -> None:
        pairs = [
            BaseRepeatPair(triplet_id="t00", q_repeat0=10.0, q_repeat1=10.5),  # 0.05
            BaseRepeatPair(triplet_id="t01", q_repeat0=20.0, q_repeat1=20.2),  # 0.01
            BaseRepeatPair(triplet_id="t02", q_repeat0=5.0, q_repeat1=6.0),  # 0.20 <- max
        ]
        threshold = derive_movement_threshold(pairs)
        assert threshold.value == pytest.approx(0.20)
        assert threshold.max_triplet_id == "t02"
        assert threshold.n_base_pairs == 3

    def test_threshold_derivation_reads_only_the_base_arm_even_when_other_arms_are_present(
        self,
    ) -> None:
        """Simulates the real pipeline: a pool of raw extraction rows tagged by
        arm ("base" / "governing" / "matched"). A loader filters to "base" and
        pairs repeat 0 against repeat 1 per triplet -- exactly what
        `scripts/score_track_h.py`'s `load_base_pairs` does. Planting an
        extreme governing/matched value in the same pool must not move the
        derived threshold at all, because those rows are never turned into a
        `BaseRepeatPair` in the first place.
        """
        raw_records = [
            {"triplet_id": "t00", "arm": "base", "repeat": 0, "quantity": 10.0},
            {"triplet_id": "t00", "arm": "base", "repeat": 1, "quantity": 10.4},  # 0.04
            {"triplet_id": "t01", "arm": "base", "repeat": 0, "quantity": 8.0},
            {"triplet_id": "t01", "arm": "base", "repeat": 1, "quantity": 8.2},  # 0.025
            # Planted decoys: if these ever leaked into the derivation the
            # threshold would jump to ~9.0 (900% relative movement).
            {"triplet_id": "t00", "arm": "governing", "repeat": 0, "quantity": 100.0},
            {"triplet_id": "t01", "arm": "matched", "repeat": 1, "quantity": 0.5},
        ]

        def base_pairs_from(records: list[dict]) -> list[BaseRepeatPair]:
            by_triplet: dict[str, dict[int, float]] = {}
            for row in records:
                if row["arm"] != "base":
                    continue
                by_triplet.setdefault(row["triplet_id"], {})[row["repeat"]] = row["quantity"]
            return [
                BaseRepeatPair(triplet_id=tid, q_repeat0=reps[0], q_repeat1=reps[1])
                for tid, reps in sorted(by_triplet.items())
            ]

        pairs = base_pairs_from(raw_records)
        threshold = derive_movement_threshold(pairs)

        assert threshold.value == pytest.approx(0.04)
        assert threshold.max_triplet_id == "t00"

        # Removing the decoy rows entirely must give the identical threshold --
        # proof that they never contributed.
        base_only = [r for r in raw_records if r["arm"] == "base"]
        threshold_without_decoys = derive_movement_threshold(base_pairs_from(base_only))
        assert threshold_without_decoys.value == threshold.value
        assert threshold_without_decoys.max_triplet_id == threshold.max_triplet_id

    def test_derive_movement_threshold_refuses_empty_input(self) -> None:
        with pytest.raises(ValueError, match="at least one base-arm pair"):
            derive_movement_threshold([])


# --------------------------------------------------------------------------- #
# relative_movement / classify_movement: edge cases
# --------------------------------------------------------------------------- #


class TestRelativeMovementAndClassification:
    def test_relative_movement_is_symmetric_in_direction(self) -> None:
        assert relative_movement(10.0, 12.0) == pytest.approx(0.2)
        assert relative_movement(10.0, 8.0) == pytest.approx(0.2)

    def test_relative_movement_refuses_zero_base(self) -> None:
        with pytest.raises(ValueError, match="undefined when the base quantity is zero"):
            relative_movement(0.0, 5.0)

    def test_classify_movement_is_strict_not_at_or_above(self) -> None:
        """A contrast exactly at the threshold has not exceeded pure noise."""
        threshold = MovementThreshold(value=0.10, n_base_pairs=1, max_triplet_id="t00")
        assert classify_movement(10.0, 11.0, threshold) is False  # exactly 0.10
        assert classify_movement(10.0, 11.01, threshold) is True  # just above


# --------------------------------------------------------------------------- #
# Phase0Result.disposition(): every branch, min(sensitivity, specificity)
# --------------------------------------------------------------------------- #


class TestDisposition:
    def test_disposition_reports_min_not_just_j_when_kill_is_asymmetric(self) -> None:
        """(1.00, 0.75) reaches J = 0.75 -- above the kill, exactly like
        (0.85, 0.85) reaching 0.70 would be -- but is not "both arms adequate".
        The disposition must say so in those words. (0.75 rather than the
        registration's exact boundary 0.70 is a test-robustness choice, so the
        assertion is not riding a single floating-point rounding of a literal
        equality; it is comfortably on the kill side either way.)
        """
        events: list[TripletEvent] = []
        for t in range(20):
            triplet_id = f"t{t:02d}"
            for repeat in (0, 1):
                # Governing always moves (sensitivity 1.00).
                q_governing = 100.0
                # Matched moves on exactly 25% of events (specificity 0.75).
                q_matched = 100.0 if (t * 2 + repeat) % 4 == 0 else 10.001
                events.append(
                    TripletEvent(
                        triplet_id=triplet_id,
                        repeat=repeat,
                        q_base=10.0,
                        q_governing=q_governing,
                        q_matched=q_matched,
                    )
                )
        battery = _passed_battery()
        result = compute_phase0_result(events, THRESHOLD, battery, seed=1)

        assert result.sensitivity == pytest.approx(1.0)
        assert result.specificity == pytest.approx(0.75)
        assert result.min_sens_spec == pytest.approx(0.75)
        assert result.j >= KILL_THRESHOLD_J
        assert result.kill is True

        text = result.disposition()
        assert "NOT both arms adequate" in text
        assert f"{result.min_sens_spec:.3f}" in text

    def test_disposition_reports_survives_when_j_below_kill(self) -> None:
        events = _events(sensitivity_rate=0.60, specificity_rate=0.55, seed=8)
        battery = _passed_battery()
        result = compute_phase0_result(events, THRESHOLD, battery, seed=2)

        assert result.j < KILL_THRESHOLD_J
        assert result.kill is False
        assert "venue survives" in result.disposition()

    def test_disposition_reports_closes_when_both_arms_genuinely_adequate(self) -> None:
        events = []
        for t in range(20):
            for repeat in (0, 1):
                events.append(
                    TripletEvent(
                        triplet_id=f"t{t:02d}",
                        repeat=repeat,
                        q_base=10.0,
                        # Sensitivity 0.90, specificity 0.90: both above 0.85.
                        q_governing=100.0 if (t * 2 + repeat) % 10 < 9 else 10.001,
                        q_matched=10.001 if (t * 2 + repeat) % 10 < 9 else 100.0,
                    )
                )
        battery = _passed_battery()
        result = compute_phase0_result(events, THRESHOLD, battery, seed=3)

        assert result.min_sens_spec >= ADEQUACY_CEILING
        assert result.kill is True
        assert "venue closes" in result.disposition()

    def test_compute_phase0_result_refuses_empty_events(self) -> None:
        with pytest.raises(ValueError, match="at least one triplet event"):
            compute_phase0_result([], THRESHOLD, _passed_battery())


# --------------------------------------------------------------------------- #
# fleiss_kappa across the three extractors: exists, used, not reimplemented
# --------------------------------------------------------------------------- #


class TestExtractorAgreement:
    def test_extractor_movement_agreement_delegates_to_fleiss_kappa(self) -> None:
        """Same input into the module's wrapper and into the raw
        `decision_evals.stats.agreement.fleiss_kappa` must give the identical
        result -- proof this is a pointer at the existing estimator, not a
        second implementation of chance-corrected agreement.
        """
        ratings: list[list[bool]] = [
            [True, True, True],
            [False, False, False],
            [True, True, False],
            [False, True, False],
            [True, False, False],
            [True, True, True],
            [False, False, True],
            [True, False, True],
        ]
        wrapped = extractor_movement_agreement(ratings)
        direct = fleiss_kappa(ratings)
        assert wrapped == direct
