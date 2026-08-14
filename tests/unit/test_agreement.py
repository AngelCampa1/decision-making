"""Inter-rater agreement: the literature pin, the denominators, the refusals.

Three kinds of test here, and the first is the one that would catch a wrong
formula rather than a wrong edge case:

* **A worked example with published intermediate values.** The standard Fleiss'
  kappa example — 10 subjects, 14 raters, 5 categories — is pinned against all
  three of its published quantities (``P-bar``, ``P-bar_e``, ``kappa``), not
  only the headline. A bug that cancels between the two components is otherwise
  invisible.
* **Hand-derived small cases**, with the arithmetic written out in the test so a
  reader can check it without running anything.
* **Every refusal**, because a coefficient that returns 0.0 on a degenerate
  input is worse than one that crashes: 0.0 is a publishable number.
"""

from __future__ import annotations

import pytest

from decision_evals.stats.agreement import (
    DegenerateAgreementError,
    cohen_kappa,
    fleiss_kappa,
    krippendorff_alpha,
    percent_agreement,
    unanimity_rate,
)

#: The standard worked example for Fleiss' kappa, read from
#: https://en.wikipedia.org/wiki/Fleiss%27_kappa on 2026-08-13. Rows are the 10
#: subjects, columns the 5 categories, entries the number of the 14 raters
#: choosing that category. Published alongside it: ``p_j = 0.143, 0.200, 0.279,
#: 0.150, 0.229``; ``P_i = 1.000, 0.253, 0.308, 0.440, 0.330, 0.462, 0.242,
#: 0.176, 0.286, 0.286``; ``P-bar = 0.378``; ``P-bar_e = 0.213``; ``kappa =
#: 0.210``.
FLEISS_EXAMPLE_COUNTS: tuple[tuple[int, ...], ...] = (
    (0, 0, 0, 0, 14),
    (0, 2, 6, 4, 2),
    (0, 0, 3, 5, 6),
    (0, 3, 9, 2, 0),
    (2, 2, 8, 1, 1),
    (7, 7, 0, 0, 0),
    (3, 2, 6, 3, 0),
    (2, 5, 3, 2, 2),
    (6, 5, 2, 1, 0),
    (0, 2, 2, 3, 7),
)

#: The published per-subject agreements ``P_i``, to the three decimals given.
FLEISS_EXAMPLE_P_I: tuple[float, ...] = (
    1.000,
    0.253,
    0.308,
    0.440,
    0.330,
    0.462,
    0.242,
    0.176,
    0.286,
    0.286,
)


def _expand(counts: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    """A counts matrix as one rating per rater, which is what the API takes.

    The published example is tabulated as counts per category; this module's
    input is the ratings themselves. Expanding here rather than accepting counts
    keeps a second input format — and a second thing to get wrong — out of the
    module.
    """
    return [[c for c, n in enumerate(row) for _ in range(n)] for row in counts]


class TestFleissWorkedExample:
    """The literature pin. All three published quantities, not just kappa."""

    def test_matches_the_published_kappa(self) -> None:
        result = fleiss_kappa(_expand(FLEISS_EXAMPLE_COUNTS))
        assert result.kappa == pytest.approx(0.210, abs=5e-4)

    def test_matches_the_published_components(self) -> None:
        """Both components, because an error in one can hide in the ratio."""
        result = fleiss_kappa(_expand(FLEISS_EXAMPLE_COUNTS))
        assert result.observed_agreement == pytest.approx(0.378, abs=5e-4)
        assert result.expected_agreement == pytest.approx(0.213, abs=5e-4)

    def test_reports_the_shape_the_example_describes(self) -> None:
        result = fleiss_kappa(_expand(FLEISS_EXAMPLE_COUNTS))
        assert (result.n_units, result.n_raters) == (10, 14)
        assert sorted(result.categories) == [0, 1, 2, 3, 4]

    def test_per_subject_agreements_match_row_by_row(self) -> None:
        """``P_i`` for every subject, so a bug cannot average itself away.

        The mean is one number over ten subjects; a formula that is wrong on the
        unanimous subject and compensatingly wrong elsewhere would pass the
        ``P-bar`` assertion above and fail here.

        Read through :func:`percent_agreement`, which is a second and
        independent code path to the same quantity: Fleiss' ``P_i`` *is* the
        share of that subject's rater pairs that agreed. Two implementations
        landing on ten published values is worth more than either landing on
        them alone.
        """
        rows = _expand(FLEISS_EXAMPLE_COUNTS)
        for row, published in zip(rows, FLEISS_EXAMPLE_P_I, strict=True):
            assert percent_agreement([row]).agreement == pytest.approx(published, abs=5e-4)


class TestCohenKappa:
    """Two raters, each against their own marginal."""

    def test_hand_derived_two_by_two(self) -> None:
        """50 items: 20 both-yes, 15 both-no, 5 a-only, 10 b-only.

        ``p_o = 35/50 = 0.700``. Marginals are a: 25 yes / 25 no and b: 30 yes /
        20 no, so ``p_e = (25*30 + 25*20) / 2500 = 0.500`` and
        ``kappa = 0.200 / 0.500 = 0.400``.
        """
        a = ["yes"] * 20 + ["no"] * 15 + ["yes"] * 5 + ["no"] * 10
        b = ["yes"] * 20 + ["no"] * 15 + ["no"] * 5 + ["yes"] * 10
        result = cohen_kappa(a, b)
        assert result.observed_agreement == pytest.approx(0.70)
        assert result.expected_agreement == pytest.approx(0.50)
        assert result.kappa == pytest.approx(0.40)
        assert result.n_units == 50

    def test_perfect_agreement_over_two_categories_is_one(self) -> None:
        assert cohen_kappa([True, False, True], [True, False, True]).kappa == pytest.approx(1.0)

    def test_complete_disagreement_on_symmetric_marginals_is_minus_one(self) -> None:
        """The lower bound is only -1 when the marginals are symmetric."""
        assert cohen_kappa([True, False], [False, True]).kappa == pytest.approx(-1.0)

    def test_categories_are_in_order_of_first_appearance(self) -> None:
        """Deterministic without requiring labels to be mutually orderable."""
        assert cohen_kappa(["b", "a", "c"], ["b", "a", "a"]).categories == ("b", "a", "c")

    def test_a_single_shared_category_is_refused(self) -> None:
        with pytest.raises(DegenerateAgreementError, match="single common category"):
            cohen_kappa(["yes"] * 8, ["yes"] * 8)

    def test_disjoint_single_categories_are_scored_not_refused(self) -> None:
        """Chance agreement is zero here, not total, so kappa is defined and 0."""
        result = cohen_kappa(["yes"] * 8, ["no"] * 8)
        assert result.expected_agreement == pytest.approx(0.0)
        assert result.kappa == pytest.approx(0.0)

    def test_mismatched_lengths_are_refused(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            cohen_kappa([True, False], [True])

    def test_empty_input_is_refused(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            cohen_kappa([], [])

    def test_a_missing_rating_names_the_estimator_that_handles_it(self) -> None:
        with pytest.raises(ValueError, match="krippendorff_alpha"):
            cohen_kappa([True, None], [True, True])

    def test_a_bare_string_is_refused(self) -> None:
        """``"ab"`` is a sequence of two ratings, and never what anyone meant."""
        with pytest.raises(ValueError, match="not a string"):
            cohen_kappa("ab", ["a", "b"])


class TestFleissKappa:
    """N raters, pooled marginal."""

    def test_perfect_agreement_is_one(self) -> None:
        result = fleiss_kappa([["a", "a", "a"], ["b", "b", "b"]])
        assert result.observed_agreement == pytest.approx(1.0)
        assert result.kappa == pytest.approx(1.0)

    def test_it_is_scotts_pi_at_two_raters_not_cohens_kappa(self) -> None:
        """The brief for this module asserted these are equal. They are not.

        Four units, two raters. Rater A says ``a, a, a, b``; rater B says ``a, a,
        b, b``. Observed agreement is 3/4 either way.

        *Cohen* uses each rater's own marginal: A is 3/4 ``a``, B is 2/4 ``a``,
        so ``p_e = 0.75*0.5 + 0.25*0.5 = 0.5`` and ``kappa = 0.25/0.5 = 0.5``.

        *Fleiss* pools: 5 of 8 ratings are ``a``, so ``p_e = (5/8)^2 + (3/8)^2 =
        0.53125`` and ``kappa = 0.21875/0.46875 = 0.4667``.

        They coincide only when the marginals do. Asserting the general identity
        would pass on a symmetric fixture and hide a real disagreement.
        """
        a = ["a", "a", "a", "b"]
        b = ["a", "a", "b", "b"]
        paired = [[x, y] for x, y in zip(a, b, strict=True)]

        cohen = cohen_kappa(a, b)
        fleiss = fleiss_kappa(paired)
        assert cohen.observed_agreement == pytest.approx(fleiss.observed_agreement)
        assert cohen.kappa == pytest.approx(0.5)
        assert fleiss.kappa == pytest.approx(0.21875 / 0.46875)
        assert cohen.kappa != pytest.approx(fleiss.kappa)

    def test_a_single_category_is_refused(self) -> None:
        with pytest.raises(DegenerateAgreementError, match="one category"):
            fleiss_kappa([["a", "a"], ["a", "a"]])

    def test_a_ragged_matrix_is_refused(self) -> None:
        with pytest.raises(ValueError, match="same number of raters"):
            fleiss_kappa([["a", "b"], ["a", "b", "b"]])

    def test_one_rater_per_unit_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least 2 raters"):
            fleiss_kappa([["a"], ["b"]])

    def test_a_missing_rating_names_alpha(self) -> None:
        with pytest.raises(ValueError, match="krippendorff_alpha"):
            fleiss_kappa([["a", "b"], ["a", None]])

    def test_empty_input_is_refused(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            fleiss_kappa([])

    def test_a_bare_string_of_units_is_refused(self) -> None:
        with pytest.raises(ValueError, match="not a string"):
            fleiss_kappa("ab")

    def test_a_unit_given_as_a_string_is_refused(self) -> None:
        with pytest.raises(ValueError, match="one rating per character"):
            fleiss_kappa([["a", "b"], "ab"])


class TestKrippendorffAlpha:
    """The one that tolerates a gap, which is why the adjudicator needs it."""

    def test_hand_derived_case_with_a_dropped_unit(self) -> None:
        """Four units of two raters, the last rated once.

        Retained: ``[a,a], [a,b], [b,b]``, so ``n = 6`` pairable values.
        ``D_o = (0 + 2 + 0) / 6 = 1/3``. Pooled counts are 3 and 3, so
        ``D_e = (36 - 18) / (6*5) = 0.6`` and ``alpha = 1 - (1/3)/0.6 = 4/9``.
        """
        result = krippendorff_alpha([["a", "a"], ["a", "b"], ["b", "b"], ["a", None]])
        assert result.n_units == 3
        assert result.n_units_dropped == 1
        assert result.n_pairable_values == 6
        assert result.observed_disagreement == pytest.approx(1 / 3)
        assert result.expected_disagreement == pytest.approx(0.6)
        assert result.alpha == pytest.approx(4 / 9)

    def test_the_dropped_unit_does_not_move_alpha(self) -> None:
        """Dropping is not imputing: a single rating carries no agreement."""
        complete = krippendorff_alpha([["a", "a"], ["a", "b"], ["b", "b"]])
        with_gap = krippendorff_alpha([["a", "a"], ["a", "b"], ["b", "b"], ["a", None]])
        assert with_gap.alpha == pytest.approx(complete.alpha)
        assert with_gap.n_units_dropped == 1
        assert complete.n_units_dropped == 0

    def test_unequal_rater_counts_are_accepted(self) -> None:
        """Ragged is ordinary here — it is the reason this estimator exists."""
        result = krippendorff_alpha([["a", "a", "a"], ["b", "b"], ["a", "b", "a", "a"]])
        assert result.n_pairable_values == 9
        assert -1.0 <= result.alpha <= 1.0

    def test_perfect_agreement_is_one(self) -> None:
        assert krippendorff_alpha([["a", "a"], ["b", "b"]]).alpha == pytest.approx(1.0)

    def test_a_single_category_is_refused(self) -> None:
        with pytest.raises(DegenerateAgreementError, match="one category"):
            krippendorff_alpha([["a", "a"], ["a", "a", "a"]])

    def test_no_pairable_values_is_refused(self) -> None:
        with pytest.raises(DegenerateAgreementError, match="nothing to disagree"):
            krippendorff_alpha([["a", None], [None, None]])

    def test_empty_input_is_refused(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            krippendorff_alpha([])


class TestPercentAgreement:
    """Raw concordance, and the pair-counting denominator."""

    def test_hand_derived_pair_counts(self) -> None:
        """Three raters is three pairs per unit.

        ``[a,a,a]`` gives 3 agreeing pairs; ``[a,a,b]`` gives 1 of 3. Six pairs,
        four agreeing.
        """
        result = percent_agreement([["a", "a", "a"], ["a", "a", "b"]])
        assert (result.n_units, result.n_pairs, result.n_agreeing_pairs) == (2, 6, 4)
        assert result.agreement == pytest.approx(4 / 6)

    def test_units_with_fewer_than_two_ratings_leave_the_denominator(self) -> None:
        """Excluded from both sides, rather than scored as agreement."""
        base = percent_agreement([["a", "a"], ["a", "b"]])
        padded = percent_agreement([["a", "a"], ["a", "b"], ["a", None], [None, None]])
        assert padded.agreement == pytest.approx(base.agreement)
        assert padded.n_units == base.n_units == 2

    def test_a_missing_rating_shrinks_a_units_pair_count(self) -> None:
        result = percent_agreement([["a", "a", None]])
        assert result.n_pairs == 1

    def test_no_pairs_is_refused(self) -> None:
        with pytest.raises(DegenerateAgreementError, match="no rater pair"):
            percent_agreement([["a", None], [None, None]])

    def test_it_is_uncorrected_and_therefore_high_by_default(self) -> None:
        """The reason it never travels alone: chance agreement is large here."""
        raw = percent_agreement([[True, True], [True, True], [True, False]])
        assert raw.agreement == pytest.approx(2 / 3)
        with pytest.raises(DegenerateAgreementError):
            # Two of these three units are constant; had all three been, the
            # corrected coefficient would be undefined while this one still
            # reads 1.0. That gap is the whole argument for reporting both.
            fleiss_kappa([[True, True], [True, True], [True, True]])


class TestUnanimityRate:
    """The number adjudicate.py reports, and its denominator."""

    def test_missing_ratings_count_against_by_default(self) -> None:
        """A judge who produced nothing did not agree."""
        result = unanimity_rate([["a", "a", "a"], ["a", "a", None]])
        assert (result.n_units, result.n_unanimous) == (2, 1)
        assert result.rate == pytest.approx(0.5)
        assert result.require_complete is True

    def test_the_permissive_reading_scores_observed_ratings_only(self) -> None:
        result = unanimity_rate([["a", "a", "a"], ["a", "a", None]], require_complete=False)
        assert result.n_unanimous == 2
        assert result.require_complete is False

    def test_a_unit_with_nothing_readable_is_never_unanimous(self) -> None:
        """Under either reading. Silence is not consensus."""
        for require_complete in (True, False):
            result = unanimity_rate([[None, None]], require_complete=require_complete)
            assert result.n_unanimous == 0
            assert result.rate == pytest.approx(0.0)

    def test_the_denominator_is_every_unit_passed_in(self) -> None:
        result = unanimity_rate([["a", "a"], ["a", "b"], [None, None]])
        assert result.n_units == 3
        assert result.rate == pytest.approx(1 / 3)

    def test_empty_input_is_refused(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            unanimity_rate([])


class TestAdjudicationShape:
    """The shape `scripts/adjudicate.py` actually holds: 3 judges, booleans, gaps."""

    def test_the_three_judge_binary_case_runs_through_every_estimator(self) -> None:
        votes: list[list[bool | None]] = [
            [True, True, True],
            [True, True, False],
            [False, False, False],
            [False, False, None],
            [True, False, True],
        ]
        assert percent_agreement(votes).n_pairs == 3 + 3 + 3 + 1 + 3
        assert unanimity_rate(votes).n_unanimous == 2
        assert -1.0 <= krippendorff_alpha(votes).alpha <= 1.0
        # Fleiss refuses the gap rather than guessing at it, and says so.
        with pytest.raises(ValueError, match="krippendorff_alpha"):
            fleiss_kappa(votes)

    def test_true_and_one_are_the_same_category(self) -> None:
        """Documented, because equality — not identity — defines a category."""
        assert unanimity_rate([[True, 1]]).n_unanimous == 1
