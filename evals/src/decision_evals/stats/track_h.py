"""Track H Phase 0 scoring: the movement threshold, the falsifier gate, and J.

This module scores Phase 0 (H1) once a corpus and its extractions exist. It
does not author items and it does not call a model — see
``notebook/2026-08-19-prediction-track-h-phase-0.md`` for what Phase 0 is and
``docs/RESEARCH_PROGRAMME.md``'s H1 subsection for why it runs before Track H's
sub-agent tracks (C through F). Everything here is pure arithmetic over
extracted quantities the runner produces.

**The primary is Youden's J, and it is identically the programme's ``d``.**
``J = sensitivity + specificity − 1`` expands to
``P(change | governing) − P(change | matched)`` (the identity is asserted
numerically in ``tests/unit/test_track_h.py``), so there is one estimator, not
two, and it is a *paired* mean difference of two indicator vectors sharing an
item order. That is exactly the shape
:func:`decision_evals.stats.cluster.cluster_bootstrap_diff` takes, with
``control`` the matched-arm change indicators, ``treatment`` the governing-arm
change indicators, and ``clusters`` the triplet id — never the file, never the
response. Defect nine on ``docs/STATUS.md``'s broken-measurement list is a
pooled statistic used on a matched corpus, ranking positives against negatives
drawn from *other* triples and structurally blind to the rank held inside one;
Track H is a matched design of exactly that shape, so this module never offers
a code path that pools over files.

**The movement threshold is derived, not chosen.** Turning a continuous
elicited quantity into `change` / `no change` needs a threshold, and no number
for one exists anywhere in this repository — standing rule 1 forbids inventing
one. The registration's rule: relative movement,
``|q_variant − q_base| / |q_base|``, with the threshold set to the *maximum* of
the 20 base-arm repeat-0 vs repeat-1 relative differences, which carry no
perturbation at all. :func:`derive_movement_threshold` computes exactly that
and returns a :class:`MovementThreshold`; every function here that classifies
movement requires one of those rather than a bare ``float``, so a threshold
cannot enter a governing/matched contrast except by having been derived from
the base arm first — the type is the enforcement.

**No J is reported before the falsifier battery passes.** Standing rule 2: a
falsifier must be run against a known-good case before it may fail anything.
Two falsifiers in this repository's history were wrong the day they were
written and would have killed healthy venues, so :func:`compute_phase0_result`
*requires* a passed :class:`FalsifierBatteryResult` as an argument and raises
:class:`FalsifierBatteryFailedError` — not a caveat, no number — when it has
not passed. ``min(sensitivity, specificity)`` is carried on every
:class:`Phase0Result` and its :meth:`~Phase0Result.disposition` never reports
``J`` alone: ``J >= 0.70`` is *implied by* both arms at 0.85 but is not
equivalent to it, since J is a difference and ``(1.00, 0.70)`` reaches 0.70
too.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from decision_evals.stats.agreement import FleissKappaResult, fleiss_kappa
from decision_evals.stats.cluster import cluster_bootstrap_diff

#: Pre-registered kill: unaided J at or above this closes the venue. Reached at
#: sensitivity 0.85 and specificity 0.85 — 0.85 is ``ADMISSIBILITY_CEILING`` in
#: ``scripts/probe_casefile.py``, this repository's one already-registered
#: adequacy constant. See the H1 prediction entry for the full arithmetic.
KILL_THRESHOLD_J: Final = 0.70

#: The adequacy level the kill's arithmetic is anchored to. J >= KILL_THRESHOLD_J
#: is implied by both arms reaching this but is not equivalent to it — a
#: disposition below this on either arm must say so explicitly rather than
#: report "both arms adequate".
ADEQUACY_CEILING: Final = 0.85


class FalsifierBatteryFailedError(RuntimeError):
    """No J may be reported: the falsifier battery has not passed.

    Standing rule 2 exists because two falsifiers in this repository were wrong
    the day they were written and would have killed a healthy venue. This is
    the refusal that makes the rule load-bearing rather than a comment: there is
    no code path in this module that reaches :class:`Phase0Result` without a
    :class:`FalsifierBatteryResult` whose :attr:`~FalsifierBatteryResult.passed`
    is ``True``.
    """


@dataclass(frozen=True, slots=True)
class BaseRepeatPair:
    """One triplet's repeat-0 vs repeat-1 elicited quantity, base file only.

    Deliberately carries no governing or matched quantity — there is nothing in
    this type for a caller to pass by mistake. That is what makes
    :func:`derive_movement_threshold`'s "reads only the base arm" property a
    fact about the API rather than a convention someone has to remember.

    Attributes:
        triplet_id: The triplet identifier. The cluster label everywhere else
            in this module.
        q_repeat0: The extracted quantity from the base file's first repeat.
        q_repeat1: The extracted quantity from the base file's second repeat,
            same file, same prompt, nothing perturbed.
    """

    triplet_id: str
    q_repeat0: float
    q_repeat1: float


@dataclass(frozen=True, slots=True)
class MovementThreshold:
    """A derived movement threshold, with the arithmetic that produced it.

    Constructed only by :func:`derive_movement_threshold`. Every function here
    that turns a quantity pair into a change/no-change call takes one of these
    rather than a bare ``float``, so a threshold cannot be invented at a call
    site — it can only be carried forward from a derivation.

    Attributes:
        value: The threshold itself: the maximum base-vs-base relative
            difference. A contrast counts as movement only when it *exceeds*
            this, not when it equals it — the threshold is itself the largest
            excursion the instrument produced with nothing perturbed.
        n_base_pairs: How many base repeat-0/repeat-1 pairs contributed. Should
            equal the triplet count (20 in Phase 0).
        max_triplet_id: Which triplet set the bound, so a surprising threshold
            can be traced to one item rather than treated as an aggregate fact.
    """

    value: float
    n_base_pairs: int
    max_triplet_id: str


def relative_movement(q_base: float, q_variant: float) -> float:
    """``|q_variant - q_base| / |q_base|``.

    Raises:
        ValueError: ``q_base`` is zero, where relative movement is undefined
            rather than infinite or zero. This is an implementation decision,
            not a registered parameter: the registration states the rule but
            does not anticipate a zero base quantity, and returning a
            placeholder here would silently manufacture a movement verdict the
            instrument never produced.
    """
    if q_base == 0.0:
        raise ValueError(
            "relative movement is undefined when the base quantity is zero "
            f"(q_variant={q_variant!r})"
        )
    return abs(q_variant - q_base) / abs(q_base)


def derive_movement_threshold(base_pairs: Sequence[BaseRepeatPair]) -> MovementThreshold:
    """The movement threshold: the maximum base-vs-base relative difference.

    Must be called, and its result carried forward, before any governing or
    matched contrast is examined — :class:`MovementThreshold` is the only way
    :func:`classify_movement` accepts a threshold, so that ordering is a type
    error to violate rather than a discipline to remember.

    Args:
        base_pairs: One :class:`BaseRepeatPair` per triplet, base-arm only.

    Returns:
        The derived :class:`MovementThreshold`.

    Raises:
        ValueError: ``base_pairs`` is empty.
    """
    if not base_pairs:
        raise ValueError("derive_movement_threshold needs at least one base-arm pair")
    diffs = [
        (pair.triplet_id, relative_movement(pair.q_repeat0, pair.q_repeat1)) for pair in base_pairs
    ]
    max_triplet_id, max_value = max(diffs, key=lambda item: item[1])
    return MovementThreshold(
        value=max_value,
        n_base_pairs=len(base_pairs),
        max_triplet_id=max_triplet_id,
    )


def classify_movement(q_base: float, q_variant: float, threshold: MovementThreshold) -> bool:
    """Whether a contrast counts as movement: strictly exceeding the threshold.

    Args:
        q_base: The base file's elicited quantity.
        q_variant: The governing- or matched-arm elicited quantity.
        threshold: A :class:`MovementThreshold`, from :func:`derive_movement_threshold`.

    Returns:
        ``True`` iff ``relative_movement(q_base, q_variant) > threshold.value``.
        Strict, not ``>=``: the threshold *is* the largest excursion the
        instrument produced when nothing was perturbed, so a contrast equal to
        it has not exceeded pure noise.
    """
    return relative_movement(q_base, q_variant) > threshold.value


@dataclass(frozen=True, slots=True)
class FalsifierCase:
    """One planted triplet's hand-written, hand-scored falsifier case.

    Attributes:
        name: A label for the planted triplet, for tracing a failure back to it.
        q_base: The hand-written base response's extracted quantity.
        q_governing: The hand-written governing-arm response's extracted
            quantity — constructed so movement is obvious.
        q_matched: The hand-written matched-arm response's extracted quantity —
            constructed so the *absence* of movement is obvious.
        expect_governing_change: Always ``True`` in the registered battery: the
            governing contrast obviously must move.
        expect_matched_change: Always ``False`` in the registered battery: the
            matched contrast obviously must not move. Carried as a field rather
            than hardcoded so a test can also exercise the case where the
            extractor is expected to be wrong.
    """

    name: str
    q_base: float
    q_governing: float
    q_matched: float
    expect_governing_change: bool
    expect_matched_change: bool


@dataclass(frozen=True, slots=True)
class FalsifierBatteryResult:
    """The falsifier battery's verdict on the extractor.

    Attributes:
        n_cases: Planted triplets scored. 2 in the registered battery.
        sensitivity: Share of cases where the governing contrast's movement
            call matched :attr:`FalsifierCase.expect_governing_change`.
        specificity: Share of cases where the matched contrast's movement call
            matched :attr:`FalsifierCase.expect_matched_change`.
        n_sensitivity_events: Denominator behind ``sensitivity`` — equals
            ``n_cases``, printed explicitly per the second guard: a plausible
            zero does not announce itself, so the raw counts travel with the
            rate.
        n_specificity_events: Denominator behind ``specificity``.
    """

    n_cases: int
    sensitivity: float
    specificity: float
    n_sensitivity_events: int
    n_specificity_events: int

    @property
    def passed(self) -> bool:
        """Whether the battery cleared the registered bar: both rates at 1.0."""
        return self.sensitivity == 1.0 and self.specificity == 1.0


def run_falsifier_battery(
    cases: Sequence[FalsifierCase], threshold: MovementThreshold
) -> FalsifierBatteryResult:
    """Score the extractor against the planted, hand-written falsifier cases.

    Args:
        cases: Planted :class:`FalsifierCase` records — 2 in the registered
            battery, one that obviously must move and one that obviously must
            not.
        threshold: The :class:`MovementThreshold`, from
            :func:`derive_movement_threshold`.

    Returns:
        A :class:`FalsifierBatteryResult`. Passing it to
        :func:`compute_phase0_result` is the only way to obtain a
        :class:`Phase0Result` — see :class:`FalsifierBatteryFailedError`.

    Raises:
        ValueError: ``cases`` is empty.
    """
    if not cases:
        raise ValueError("run_falsifier_battery needs at least one planted case")
    governing_correct = 0
    matched_correct = 0
    for case in cases:
        governing_changed = classify_movement(case.q_base, case.q_governing, threshold)
        matched_changed = classify_movement(case.q_base, case.q_matched, threshold)
        if governing_changed == case.expect_governing_change:
            governing_correct += 1
        if matched_changed == case.expect_matched_change:
            matched_correct += 1
    n = len(cases)
    return FalsifierBatteryResult(
        n_cases=n,
        sensitivity=governing_correct / n,
        specificity=matched_correct / n,
        n_sensitivity_events=n,
        n_specificity_events=n,
    )


@dataclass(frozen=True, slots=True)
class TripletEvent:
    """One ``(triplet, repeat)`` pair's elicited quantity across all three arms.

    40 of these exist in Phase 0: 20 triplets × 2 repeats. Each contributes
    exactly one sensitivity event (governing vs base) and one specificity event
    (matched vs base) — never pooled, always keyed by ``triplet_id`` for
    clustering.

    Attributes:
        triplet_id: The triplet identifier — the cluster label.
        repeat: 0 or 1.
        q_base: The base file's elicited quantity for this repeat.
        q_governing: The governing-fact-changed file's elicited quantity.
        q_matched: The matched-non-governing-fact-changed file's elicited
            quantity.
    """

    triplet_id: str
    repeat: int
    q_base: float
    q_governing: float
    q_matched: float


@dataclass(frozen=True, slots=True)
class Phase0Result:
    """Phase 0's disposition: J, its decomposition, and the raw counts.

    ``j`` and ``ci_low``/``ci_high`` come directly from
    :func:`~decision_evals.stats.cluster.cluster_bootstrap_diff` — this is the
    identical number the module docstring's identity refers to, not a second
    computation of it.

    Attributes:
        j: Youden's J, identically ``d = P(change|governing) − P(change|matched)``.
        ci_low: Lower bound of the cluster-bootstrapped percentile interval.
        ci_high: Upper bound.
        standard_error: Bootstrap standard deviation.
        confidence: Nominal coverage, e.g. 0.95.
        sensitivity: ``P(change | governing)``.
        specificity: ``1 − P(change | matched)``.
        min_sens_spec: ``min(sensitivity, specificity)`` — printed because
            ``J >= KILL_THRESHOLD_J`` is reachable asymmetrically, e.g.
            ``(1.00, 0.70)``, and that is not "both arms adequate".
        n_sensitivity_events: Denominator behind ``sensitivity`` (40 in Phase 0).
        n_specificity_events: Denominator behind ``specificity`` (40 in Phase 0).
        n_governing_change: Raw count of governing contrasts scored as movement.
        n_matched_change: Raw count of matched contrasts scored as movement.
        n_clusters: Distinct triplets resampled (20 in Phase 0).
        n_resamples: Bootstrap replicates drawn.
        threshold: The :class:`MovementThreshold` this result was scored under.
        battery: The :class:`FalsifierBatteryResult` that authorised this
            result to exist at all.
    """

    j: float
    ci_low: float
    ci_high: float
    standard_error: float
    confidence: float
    sensitivity: float
    specificity: float
    min_sens_spec: float
    n_sensitivity_events: int
    n_specificity_events: int
    n_governing_change: int
    n_matched_change: int
    n_clusters: int
    n_resamples: int
    threshold: MovementThreshold
    battery: FalsifierBatteryResult

    @property
    def kill(self) -> bool:
        """Whether the pre-registered kill fires: ``J >= KILL_THRESHOLD_J``."""
        return self.j >= KILL_THRESHOLD_J

    def disposition(self) -> str:
        """A one-paragraph disposition that never reports J alone.

        States ``min(sensitivity, specificity)`` beside J in every case, and
        when the kill fires with one arm below :data:`ADEQUACY_CEILING`, says
        so in those words rather than "both arms adequate" — the specific
        wording the registration requires.
        """
        base = (
            f"J = {self.j:.3f} [{self.ci_low:.3f}, {self.ci_high:.3f}] over "
            f"{self.n_clusters} clusters (95% cluster bootstrap) — "
            f"sensitivity {self.sensitivity:.3f} "
            f"({self.n_governing_change}/{self.n_sensitivity_events}), "
            f"specificity {self.specificity:.3f} "
            f"({self.n_specificity_events - self.n_matched_change}/{self.n_specificity_events}), "
            f"min(sensitivity, specificity) = {self.min_sens_spec:.3f}."
        )
        if not self.kill:
            return f"{base} J < {KILL_THRESHOLD_J:.2f}: the venue survives."
        if self.min_sens_spec < ADEQUACY_CEILING:
            return (
                f"{base} J >= {KILL_THRESHOLD_J:.2f}, but at least one arm is below "
                f"{ADEQUACY_CEILING:.2f} — this is NOT both arms adequate, and the kill's "
                "arithmetic (0.85 and 0.85) does not describe this result."
            )
        return (
            f"{base} J >= {KILL_THRESHOLD_J:.2f} with both arms at or above "
            f"{ADEQUACY_CEILING:.2f}: the venue closes."
        )


def compute_phase0_result(
    events: Sequence[TripletEvent],
    threshold: MovementThreshold,
    battery: FalsifierBatteryResult,
    *,
    confidence: float = 0.95,
    n_resamples: int = 10_000,
    seed: int | None = None,
) -> Phase0Result:
    """Score Phase 0: J via a cluster bootstrap on the triplet, plus its decomposition.

    Args:
        events: One :class:`TripletEvent` per ``(triplet, repeat)`` pair — 40 in
            Phase 0. Never pass one row per file; a triplet's three files are
            three fields of one event, which is what stops the analysis from
            offering a pooled-over-files code path at all.
        threshold: The :class:`MovementThreshold`, derived before any of
            ``events`` was examined.
        battery: A passed :class:`FalsifierBatteryResult`. This is the gate:
            see :class:`FalsifierBatteryFailedError`.
        confidence: Nominal bootstrap coverage.
        n_resamples: Bootstrap replicates.
        seed: Seed for reproducibility — a report that moves between two
            readings of the same checkpoint is not a report.

    Returns:
        A :class:`Phase0Result`.

    Raises:
        FalsifierBatteryFailedError: ``battery.passed`` is ``False``. No J is
            computed; the extractor is the finding instead.
        ValueError: ``events`` is empty, or via
            :func:`~decision_evals.stats.cluster.cluster_bootstrap_diff`
            (e.g. a single cluster).
    """
    if not battery.passed:
        raise FalsifierBatteryFailedError(
            "the falsifier battery has not passed "
            f"(sensitivity={battery.sensitivity!r}, specificity={battery.specificity!r} "
            f"over {battery.n_cases} planted cases); standing rule 2 refuses any J until "
            "both read 1.0. The extractor is the finding, not a caveat on a number."
        )
    if not events:
        raise ValueError("compute_phase0_result needs at least one triplet event")

    governing_change = [classify_movement(e.q_base, e.q_governing, threshold) for e in events]
    matched_change = [classify_movement(e.q_base, e.q_matched, threshold) for e in events]
    triplet_ids = [e.triplet_id for e in events]

    boot = cluster_bootstrap_diff(
        control=np.asarray(matched_change, dtype=np.float64),
        treatment=np.asarray(governing_change, dtype=np.float64),
        clusters=triplet_ids,
        confidence=confidence,
        n_resamples=n_resamples,
        seed=seed,
    )

    n = len(events)
    n_governing_change = sum(governing_change)
    n_matched_change = sum(matched_change)
    sensitivity = n_governing_change / n
    specificity = 1.0 - (n_matched_change / n)

    return Phase0Result(
        j=boot.point_estimate,
        ci_low=boot.ci_low,
        ci_high=boot.ci_high,
        standard_error=boot.standard_error,
        confidence=boot.confidence,
        sensitivity=sensitivity,
        specificity=specificity,
        min_sens_spec=min(sensitivity, specificity),
        n_sensitivity_events=n,
        n_specificity_events=n,
        n_governing_change=n_governing_change,
        n_matched_change=n_matched_change,
        n_clusters=boot.n_clusters,
        n_resamples=boot.n_resamples,
        threshold=threshold,
        battery=battery,
    )


def extractor_movement_agreement(ratings: Sequence[Sequence[bool]]) -> FleissKappaResult:
    """Fleiss' kappa across the three extractors' movement calls.

    A health check on the instrument, not a result — the registration is
    explicit that this is reported "beside" ``J``, never in place of it.
    Delegates directly to
    :func:`decision_evals.stats.agreement.fleiss_kappa`: Track H does not need
    a second implementation of chance-corrected agreement, it needs the
    existing one pointed at boolean movement calls (one call per extractor per
    response) instead of the discrete labels it was written for.

    Args:
        ratings: One sequence of three ``bool`` movement calls per response —
            120 responses in Phase 0, one row each.

    Returns:
        A :class:`~decision_evals.stats.agreement.FleissKappaResult`.

    Raises:
        ValueError: Via :func:`fleiss_kappa` — empty, ragged, or fewer than two
            raters.
        DegenerateAgreementError: Via :func:`fleiss_kappa` — every call fell in
            one category.
    """
    return fleiss_kappa(ratings)
