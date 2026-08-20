"""Inter-rater agreement, for the runs where the thing measured is the key.

Twenty-one of twenty-one scored failures across three corpora were the answer
key being wrong rather than the model, so this repository's most consequential
comparisons are not model against key but **label against label**.
``scripts/adjudicate.py`` runs three blind adjudicators per turn and resolves
them by majority against a pre-registered 20% movement kill. Until this module
existed it reported raw concordance and nothing chance-corrected, which is the
one number that says whether three judges agreeing means anything: on a binary
question with a 3-to-1 class balance, two judges who have learned nothing at all
agree about 62% of the time.

Four estimators, because they answer four different questions and this
repository has been bitten by reporting one and calling it another:

* :func:`percent_agreement` — raw pairwise concordance. No correction for
  chance, so it is a description rather than a measurement, and it is here so
  that the corrected coefficients can be read against it.
* :func:`unanimity_rate` — how often *everyone* said the same thing. This is a
  strictness measure, not an agreement coefficient, and it is the number
  ``adjudicate.py`` reports.
* :func:`cohen_kappa` — two raters, each judged against **their own** marginal
  distribution.
* :func:`fleiss_kappa` — N raters against a **pooled** marginal.
* :func:`krippendorff_alpha` — the one that tolerates a missing rating.

**Cohen and Fleiss do not agree at two raters, and it is not a bug.** Fleiss'
coefficient with two raters is Scott's pi: it estimates chance agreement from
the pooled category distribution, while Cohen's estimates it from each rater's
own. They coincide exactly when the two raters' marginals coincide and diverge
otherwise, which is asserted in both directions in the property tests. Anything
claiming Fleiss at N=2 *is* Cohen has picked a dataset where the marginals
happen to match.

**Missing is not "no".** ``adjudicate.parse`` returns ``None`` for a reply it
cannot read, and scoring that as disagreement would convert a formatting problem
into label movement — the exact defect shape the adjudication run exists to
detect. So ``None`` is admissible input here, it is excluded from pair counts
rather than counted against, and the estimators that cannot represent it say so
and name the one that can.

**Every estimator states what it divides by.** Four pre-registration defects on
this repository's record came from a measure whose denominator was never
written down — including one that fell inside its band under both readings,
which is luck rather than method.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations

from .cluster import design_effect

#: A category. Anything hashable and comparable by equality would do; the union
#: is narrowed to what this repository actually labels with so that mypy can
#: check call sites. Note that ``True`` and ``1`` are one category, because they
#: are equal — a mixed-type label set is a corpus bug, not a feature to support.
Label = bool | int | str


class DegenerateAgreementError(ValueError):
    """A coefficient is undefined for this input, rather than zero or NaN.

    Chance-corrected agreement divides by the room left above chance. When every
    rating falls in one category there is no such room: the coefficient is 0/0,
    and both of the values a naive implementation returns there are lies — 0.0
    says the raters agreed no better than chance when they agreed perfectly, and
    ``nan`` propagates silently into a mean.

    A :class:`ValueError` subclass, so callers written against the convention in
    :mod:`decision_evals.stats.paired` keep catching it.
    """


@dataclass(frozen=True, slots=True)
class PercentAgreementResult:
    """Raw pairwise concordance, uncorrected for chance.

    Attributes:
        n_units: Units contributing at least one rater pair. A unit rated once
            or not at all has no pair that could agree and is excluded from
            **both** numerator and denominator rather than scored as agreement.
        n_pairs: Unordered rater pairs summed over those units. **This is the
            denominator** — pairs, not units, so a unit rated by more raters
            weighs more.
        n_agreeing_pairs: Pairs whose two ratings were equal. The numerator.
        agreement: ``n_agreeing_pairs / n_pairs``.
    """

    n_units: int
    n_pairs: int
    n_agreeing_pairs: int
    agreement: float


@dataclass(frozen=True, slots=True)
class UnanimityResult:
    """How often every rater said the same thing.

    Attributes:
        n_units: **The denominator: every unit passed in**, including units on
            which nothing was readable. A unit nobody could be scored on is not
            evidence of agreement, so it lowers the rate rather than vanishing
            from it. This is the one place in the module where a missing rating
            counts against the result, and it is deliberate: the question
            "did all three judges agree" has the answer "no" when one of them
            produced nothing.
        n_unanimous: Units where every observed rating was equal — and, when
            ``require_complete``, where none was missing.
        rate: ``n_unanimous / n_units``.
        require_complete: Whether a missing rating disqualifies a unit.
    """

    n_units: int
    n_unanimous: int
    rate: float
    require_complete: bool


@dataclass(frozen=True, slots=True)
class CohenKappaResult:
    """Two raters, chance estimated from each rater's own marginal.

    Attributes:
        n_units: Items both raters rated. The denominator of
            ``observed_agreement``.
        observed_agreement: Share of items the two raters put in the same
            category.
        expected_agreement: ``sum_c p_a(c) * p_b(c)`` — agreement expected if
            the two raters assigned categories independently at their own
            observed rates.
        kappa: ``(observed - expected) / (1 - expected)``. The denominator is
            the room above chance, which is why a single-category input is
            refused rather than scored.
        categories: Categories either rater used, in order of first appearance.
    """

    n_units: int
    observed_agreement: float
    expected_agreement: float
    kappa: float
    categories: tuple[Label, ...]


@dataclass(frozen=True, slots=True)
class FleissKappaResult:
    """N raters per unit, chance estimated from the pooled marginal.

    Attributes:
        n_units: Units rated. Each must be rated by the same number of raters;
            Fleiss' coefficient is not defined otherwise.
        n_raters: Raters per unit.
        observed_agreement: Mean over units of the share of *rater pairs within
            the unit* that agreed — the paper's ``P-bar``. Denominator per unit
            is ``n_raters * (n_raters - 1)`` ordered pairs.
        expected_agreement: ``sum_c p(c)^2`` over the pooled category
            proportions, where ``p(c)`` divides by ``n_units * n_raters``.
        kappa: ``(observed - expected) / (1 - expected)``.
        categories: Categories used anywhere, in order of first appearance.

    Note:
        The raters are not identified across units. Fleiss' coefficient assumes
        the ``n_raters`` ratings on a unit are exchangeable, which is exactly
        true of the adjudication design here — each of the three judges is a
        fresh instance in an isolated conversation — and would be false of three
        named humans with stable individual biases.
    """

    n_units: int
    n_raters: int
    observed_agreement: float
    expected_agreement: float
    kappa: float
    categories: tuple[Label, ...]


@dataclass(frozen=True, slots=True)
class KrippendorffAlphaResult:
    """Nominal alpha: the coefficient that survives a missing rating.

    Attributes:
        n_units: Units carrying at least two observed ratings — the ones alpha
            is computed over.
        n_units_dropped: Units carrying fewer than two. They are dropped rather
            than imputed, which is the whole reason to reach for alpha instead
            of padding the matrix with a guess.
        n_pairable_values: Total observed ratings over the retained units. **The
            ``n`` in the expected-disagreement denominator ``n(n - 1)``**, and
            the reason alpha is not simply a rescaled kappa: it corrects for
            sampling without replacement from the observed ratings.
        observed_disagreement: ``D_o``, mean disagreement within units, each
            unit weighted by its rating count and normalised by ``m - 1``.
        expected_disagreement: ``D_e``, disagreement expected from the pooled
            marginal under random pairing without replacement.
        alpha: ``1 - D_o / D_e``.
        categories: Categories observed, in order of first appearance.

    Note:
        On complete data with a constant rater count the two coefficients are
        related exactly: ``1 - alpha == (1 - kappa) * (n - 1) / n`` with ``n =
        n_pairable_values``. That identity is a property test, and it is the
        cross-check that makes two independent implementations believable.
    """

    n_units: int
    n_units_dropped: int
    n_pairable_values: int
    observed_disagreement: float
    expected_disagreement: float
    alpha: float
    categories: tuple[Label, ...]


def _as_units(
    ratings: Sequence[Sequence[Label | None]], name: str
) -> tuple[tuple[Label | None, ...], ...]:
    """Coerce to a tuple of per-unit rating tuples, rejecting a bare string.

    A string is a ``Sequence`` of characters, so ``"yn"`` would silently become
    two ratings and a corpus of labels would become a corpus of letters. Both
    levels are checked because both are reachable by an ordinary typo.
    """
    if isinstance(ratings, str):
        raise ValueError(f"{name} must be a sequence of per-unit rating sequences, not a string")
    units: list[tuple[Label | None, ...]] = []
    for index, unit in enumerate(ratings):
        if isinstance(unit, str):
            raise ValueError(
                f"{name}[{index}] must be a sequence of ratings, not the string {unit!r} — "
                "a string would be split into one rating per character"
            )
        units.append(tuple(unit))
    if not units:
        raise ValueError(f"{name} must not be empty")
    return tuple(units)


def _complete(
    units: tuple[tuple[Label | None, ...], ...], name: str
) -> tuple[tuple[Label, ...], ...]:
    """Narrow to complete units, refusing missing ratings and naming the fix."""
    complete: list[tuple[Label, ...]] = []
    for index, unit in enumerate(units):
        row: list[Label] = []
        for rating in unit:
            if rating is None:
                raise ValueError(
                    f"{name}[{index}] has a missing rating. This estimator is defined only "
                    "for complete data; krippendorff_alpha is the one that tolerates gaps."
                )
            row.append(rating)
        complete.append(tuple(row))
    return tuple(complete)


def _rectangular(units: tuple[tuple[Label, ...], ...], name: str) -> int:
    """The common rater count, refusing a ragged matrix."""
    widths = {len(unit) for unit in units}
    if len(widths) != 1:
        raise ValueError(
            f"{name} must have the same number of raters on every unit, got widths "
            f"{sorted(widths)}. A ragged matrix is missing data by another name; "
            "krippendorff_alpha handles it directly."
        )
    (width,) = widths
    if width < 2:
        raise ValueError(f"{name} needs at least 2 raters per unit, got {width}")
    return width


def _flat_labels(values: Sequence[Label | None], name: str) -> tuple[Label, ...]:
    """One rater's ratings: non-empty, no gaps, not a bare string."""
    if isinstance(values, str):
        raise ValueError(f"{name} must be a sequence of ratings, not a string")
    labels: list[Label] = []
    for index, value in enumerate(values):
        if value is None:
            raise ValueError(
                f"{name}[{index}] is missing. Cohen's kappa is defined only over items both "
                "raters rated; drop the item, or use krippendorff_alpha."
            )
        labels.append(value)
    if not labels:
        raise ValueError(f"{name} must not be empty")
    return tuple(labels)


def percent_agreement(ratings: Sequence[Sequence[Label | None]]) -> PercentAgreementResult:
    """Share of rater pairs that agreed, uncorrected for chance.

    Args:
        ratings: One sequence of ratings per unit. Units may have different
            rater counts, and ``None`` marks a rating that was not obtained.

    Returns:
        A :class:`PercentAgreementResult`. The denominator is **rater pairs**
        summed over units with at least two observed ratings, not units.

    Raises:
        ValueError: If ``ratings`` is empty, or a unit is given as a string.
        DegenerateAgreementError: If no unit carries two observed ratings, so
            there is no pair to score.

    Note:
        This number is not comparable across corpora with different class
        balances, which is the entire reason the chance-corrected coefficients
        exist. Report it beside one of them, never instead of one.
    """
    units = _as_units(ratings, "ratings")
    n_units = 0
    n_pairs = 0
    n_agreeing = 0
    for unit in units:
        observed = [rating for rating in unit if rating is not None]
        if len(observed) < 2:
            continue
        n_units += 1
        for left, right in combinations(observed, 2):
            n_pairs += 1
            if left == right:
                n_agreeing += 1

    if n_pairs == 0:
        raise DegenerateAgreementError(
            "no unit carries two observed ratings, so there is no rater pair to agree. "
            "Percent agreement over zero pairs is undefined, not 0.0."
        )
    return PercentAgreementResult(
        n_units=n_units,
        n_pairs=n_pairs,
        n_agreeing_pairs=n_agreeing,
        agreement=n_agreeing / n_pairs,
    )


def unanimity_rate(
    ratings: Sequence[Sequence[Label | None]],
    *,
    require_complete: bool = True,
) -> UnanimityResult:
    """Share of units on which every rater said the same thing.

    Args:
        ratings: One sequence of ratings per unit, ``None`` for a rating that
            was not obtained.
        require_complete: When true (the default) a unit with any missing rating
            is not unanimous, because a rater who produced nothing did not
            agree. When false, unanimity is judged over the observed ratings
            only and a single-rating unit counts as unanimous — which flatters
            the number and is offered only so that the two readings can be
            reported side by side rather than confused.

    Returns:
        A :class:`UnanimityResult`. **The denominator is every unit passed in**,
        including units with no readable rating at all.

    Raises:
        ValueError: If ``ratings`` is empty, or a unit is given as a string.

    Note:
        Unanimity is a strictness measure, not an agreement coefficient: it has
        no chance correction and it falls as raters are added even when they
        agree just as well. Two runs' unanimity rates are comparable only at
        equal rater counts.
    """
    units = _as_units(ratings, "ratings")
    n_unanimous = 0
    for unit in units:
        observed = [rating for rating in unit if rating is not None]
        if not observed:
            continue
        if require_complete and len(observed) != len(unit):
            continue
        if all(rating == observed[0] for rating in observed):
            n_unanimous += 1

    return UnanimityResult(
        n_units=len(units),
        n_unanimous=n_unanimous,
        rate=n_unanimous / len(units),
        require_complete=require_complete,
    )


def cohen_kappa(
    rater_a: Sequence[Label | None],
    rater_b: Sequence[Label | None],
) -> CohenKappaResult:
    """Cohen's kappa for two raters over categorical labels.

    ``kappa = (p_o - p_e) / (1 - p_e)``, where ``p_o`` divides agreements by the
    number of items and ``p_e`` is ``sum_c p_a(c) * p_b(c)`` — each rater's own
    marginal, which is what distinguishes this from Fleiss at two raters.

    Args:
        rater_a: One rating per item.
        rater_b: One rating per item, in the same item order.

    Returns:
        A :class:`CohenKappaResult`.

    Raises:
        ValueError: If the sequences differ in length, are empty, are given as
            strings, or contain ``None``.
        DegenerateAgreementError: If both raters used exactly one category, in
            common. Chance agreement is then total, the denominator is zero, and
            kappa is undefined rather than 0 or 1.

    Note:
        Kappa is bounded above by 1 and below by ``-p_e / (1 - p_e)``, which is
        above -1 unless the marginals are symmetric. A negative value means the
        raters agreed *less* than independent raters with those marginals would
        have, which on a blind adjudication run means the prompt is inverted
        somewhere, not that the judges are adversaries.
    """
    a = _flat_labels(rater_a, "rater_a")
    b = _flat_labels(rater_b, "rater_b")
    if len(a) != len(b):
        raise ValueError(f"rater_a and rater_b must be the same length, got {len(a)} and {len(b)}")

    n = len(a)
    observed = sum(1 for left, right in zip(a, b, strict=True) if left == right) / n
    counts_a = Counter(a)
    counts_b = Counter(b)
    categories = tuple(dict.fromkeys([*a, *b]))
    expected = sum(counts_a[c] * counts_b[c] for c in categories) / (n * n)

    if expected >= 1.0:
        raise DegenerateAgreementError(
            "both raters used a single common category, so chance agreement is total and "
            "kappa divides by zero. Observed agreement is 1.0 and carries no information: "
            "a rater who always says the same thing cannot be shown to be reliable."
        )
    return CohenKappaResult(
        n_units=n,
        observed_agreement=observed,
        expected_agreement=expected,
        kappa=(observed - expected) / (1.0 - expected),
        categories=categories,
    )


def fleiss_kappa(ratings: Sequence[Sequence[Label | None]]) -> FleissKappaResult:
    """Fleiss' kappa for a constant number of raters per unit.

    ``P_i = (sum_c n_ic^2 - m) / (m(m - 1))`` per unit, ``P-bar`` their mean,
    ``P-bar_e = sum_c p_c^2`` over pooled proportions dividing by ``n_units *
    m``, and ``kappa = (P-bar - P-bar_e) / (1 - P-bar_e)``.

    Args:
        ratings: One sequence of ratings per unit. Every unit must carry the
            same number of ratings, at least two, and none may be ``None``.

    Returns:
        A :class:`FleissKappaResult`.

    Raises:
        ValueError: If ``ratings`` is empty, ragged, has fewer than two raters
            per unit, contains ``None``, or a unit is given as a string.
        DegenerateAgreementError: If every rating falls in one category.

    Note:
        With two raters this is Scott's pi, **not** Cohen's kappa. The two
        differ whenever the raters' marginal distributions differ, and reporting
        one under the other's name overstates agreement exactly when the raters
        are differently biased — which is the case a reliability check exists to
        find.
    """
    units = _complete(_as_units(ratings, "ratings"), "ratings")
    n_raters = _rectangular(units, "ratings")
    n_units = len(units)
    total = n_units * n_raters

    agreements = 0
    for unit in units:
        agreements += sum(count * count for count in Counter(unit).values()) - n_raters
    observed = agreements / (n_units * n_raters * (n_raters - 1))

    pooled = Counter(rating for unit in units for rating in unit)
    expected = sum((count / total) ** 2 for count in pooled.values())

    if expected >= 1.0:
        raise DegenerateAgreementError(
            "every rating falls in one category, so chance agreement is total and kappa "
            "divides by zero. A key on which all raters always say the same thing has no "
            "measurable reliability."
        )
    return FleissKappaResult(
        n_units=n_units,
        n_raters=n_raters,
        observed_agreement=observed,
        expected_agreement=expected,
        kappa=(observed - expected) / (1.0 - expected),
        categories=tuple(dict.fromkeys(rating for unit in units for rating in unit)),
    )


@dataclass(frozen=True, slots=True)
class EffectiveRatersResult:
    """How many independent raters a panel is worth, given how much it agrees.

    Kappa answers *how much do these raters agree*. It does not answer *how
    many raters is this*, and the two are routinely read as one number.
    Kohli (arXiv:2605.29800) makes the point at scale: nine frontier judges
    from seven model families "effectively provide only about 2 independent
    votes' worth of information". The figure often quoted alongside that,
    n_eff = 2.18, is **not in the abstract** and `paper/refs.bib` records it as
    unverified, so the verified sentence is the one carried here.

    The arithmetic here is the design effect, `1 + (m - 1) * rho`, with the
    raters as the members of a cluster. For binary ratings at a constant rater
    count, Fleiss' kappa **is** an intraclass correlation, so it is what goes in
    as ``rho`` and no second estimator is introduced to disagree with the first.

    **What this is not, stated because the name invites the mistake.** It is not
    Kohli's cross-family n_eff and cannot be computed on this repository's
    adjudication design. That number measures whether judges drawn from
    different model families make *correlated errors*. Three fresh instances of
    one model at one tier cannot answer it: agreement driven by the item and
    agreement driven by the shared model are not separately identified from the
    ratings, and any single number over them is both. What this does say is the
    weaker, true thing -- given the agreement observed, the panel carries the
    information of about this many independent raters -- and the panel's
    composition has to be reported beside it or the reader will supply the
    stronger reading.

    Attributes:
        n_raters: Raters per unit, as :func:`fleiss_kappa` counts them.
        icc: Observed Fleiss kappa, used as the intraclass correlation.
        icc_used: ``icc`` clamped into ``[0, 1]``. A negative kappa estimate is
            a sampling artefact of a true correlation near zero, and the design
            effect is not defined below zero; clamping is the standard
            treatment and is recorded separately so the raw value stays
            visible.
        design_effect: ``1 + (n_raters - 1) * icc_used``. Variance inflation.
        effective: ``n_raters / design_effect``. Never above ``n_raters``, and
            never below 1.
    """

    n_raters: int
    icc: float
    icc_used: float
    design_effect: float
    effective: float


def effective_raters(ratings: Sequence[Sequence[Label | None]]) -> EffectiveRatersResult:
    """The panel's effective size under its own observed agreement.

    Args:
        ratings: One sequence of ratings per unit, as :func:`fleiss_kappa`
            takes them. Same constraints, because it is computed from that.

    Returns:
        An :class:`EffectiveRatersResult`.

    Raises:
        ValueError: As :func:`fleiss_kappa` raises it -- empty, ragged, fewer
            than two raters, or a ``None`` present.
        DegenerateAgreementError: As :func:`fleiss_kappa` raises it. A panel
            that always says the same thing has no measurable reliability and
            therefore no measurable independence either.
    """
    result = fleiss_kappa(ratings)
    icc_used = min(max(result.kappa, 0.0), 1.0)
    inflation = design_effect(float(result.n_raters), icc_used)
    return EffectiveRatersResult(
        n_raters=result.n_raters,
        icc=result.kappa,
        icc_used=icc_used,
        design_effect=inflation,
        effective=result.n_raters / inflation,
    )


def krippendorff_alpha(ratings: Sequence[Sequence[Label | None]]) -> KrippendorffAlphaResult:
    """Krippendorff's alpha for nominal data, with missing ratings allowed.

    ``alpha = 1 - D_o / D_e``. Observed disagreement divides each unit's
    disagreeing pairs by ``m_u - 1`` and the total by ``n``, the number of
    pairable values; expected disagreement divides the pooled disagreeing pairs
    by ``n(n - 1)``, which is sampling without replacement rather than the
    ``n^2`` a kappa uses.

    Args:
        ratings: One sequence of ratings per unit. Rater counts may differ
            between units and ``None`` marks a rating that was not obtained —
            ``adjudicate.parse`` returns exactly that for a reply it could not
            read, and it is a missing measurement, not a "no".

    Returns:
        A :class:`KrippendorffAlphaResult`. Units with fewer than two observed
        ratings are dropped and counted in ``n_units_dropped``.

    Raises:
        ValueError: If ``ratings`` is empty or a unit is given as a string.
        DegenerateAgreementError: If fewer than two pairable values survive, or
            every observed rating falls in one category.

    Note:
        Nominal only. The whole point of alpha in its general form is the
        difference function, and an ordinal or interval one applied to labels
        that are not ordered would be an invented parameter. If a run ever needs
        ordered categories, add the metric explicitly rather than reusing this.
    """
    units = _as_units(ratings, "ratings")

    retained: list[tuple[Label, ...]] = []
    dropped = 0
    for unit in units:
        observed = tuple(rating for rating in unit if rating is not None)
        if len(observed) < 2:
            dropped += 1
            continue
        retained.append(observed)

    n_pairable = sum(len(unit) for unit in retained)
    if n_pairable < 2:
        raise DegenerateAgreementError(
            "no unit carries two observed ratings, so there is nothing to disagree. "
            "Alpha over zero pairable values is undefined, not 0.0."
        )

    observed_disagreement = 0.0
    for unit in retained:
        m = len(unit)
        within = m * m - sum(count * count for count in Counter(unit).values())
        observed_disagreement += within / (m - 1)
    observed_disagreement /= n_pairable

    pooled = Counter(rating for unit in retained for rating in unit)
    expected_disagreement = (
        n_pairable * n_pairable - sum(count * count for count in pooled.values())
    ) / (n_pairable * (n_pairable - 1))

    if expected_disagreement == 0.0:
        raise DegenerateAgreementError(
            "every observed rating falls in one category, so expected disagreement is zero "
            "and alpha divides by zero. Perfect agreement on a constant is not reliability."
        )
    return KrippendorffAlphaResult(
        n_units=len(retained),
        n_units_dropped=dropped,
        n_pairable_values=n_pairable,
        observed_disagreement=observed_disagreement,
        expected_disagreement=expected_disagreement,
        alpha=1.0 - observed_disagreement / expected_disagreement,
        categories=tuple(dict.fromkeys(rating for unit in retained for rating in unit)),
    )
