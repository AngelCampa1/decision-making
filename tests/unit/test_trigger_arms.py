"""Tests for arm scoring.

The last section is the one that matters: this module has to reproduce the
numbers already published in `results/` from the same checkpoints. A scoring
library that gives different answers from the scripts that produced the record
is not a refactor, it is a fifth estimator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import pytest

from decision_evals.trigger_arms import (
    ArmError,
    compare,
    covers_rates,
    format_comparison,
    load_arm,
    per_item_correctness,
    summarise,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "results" / "decision-making"


def row(
    case: str,
    *,
    fired: bool | None,
    should_fire: bool,
    repeat: int = 0,
    covers: bool | None = None,
) -> dict[str, object]:
    return {
        "case": case,
        "repeat": repeat,
        "fired": fired,
        "should_fire": should_fire,
        "covers": covers,
    }


# -- summarise --------------------------------------------------------------


class TestSummarise:
    def test_a_perfect_arm(self) -> None:
        report = summarise(
            [row("p1", fired=True, should_fire=True), row("n1", fired=False, should_fire=False)]
        )
        assert (report.precision, report.recall, report.false_positive_rate) == (1.0, 1.0, 0.0)
        assert report.accuracy == 1.0
        assert report.missed == ()

    def test_an_arm_that_never_fires(self) -> None:
        report = summarise(
            [row("p1", fired=False, should_fire=True), row("n1", fired=False, should_fire=False)]
        )
        assert report.recall == 0.0
        assert report.precision == 0.0, "no fires means no precision, not a division by zero"
        assert report.missed == ("p1",)

    def test_unparseable_rows_are_counted_and_not_scored(self) -> None:
        """A row with no verdict is a missing measurement, not a decline to fire.

        Scoring it as a non-fire would turn a format problem into a recall
        result, which is how a broken response contract gets published as a
        finding about the skill.
        """
        report = summarise(
            [
                row("p1", fired=True, should_fire=True),
                row("p1", fired=None, should_fire=True, repeat=1),
                row("n1", fired=False, should_fire=False),
            ]
        )
        assert report.unparseable == 1
        assert report.n_records == 3
        assert report.recall == 1.0, "the parsed positive fired; the null must not dilute it"
        assert report.missed == ()

    def test_a_case_missed_in_every_repeat_is_listed(self) -> None:
        report = summarise(
            [
                row("p1", fired=False, should_fire=True),
                row("p1", fired=False, should_fire=True, repeat=1),
                row("p2", fired=False, should_fire=True),
                row("p2", fired=True, should_fire=True, repeat=1),
                row("n1", fired=False, should_fire=False),
            ]
        )
        assert report.missed == ("p1",), "p2 fired once and is not a miss"

    def test_no_records_is_an_error(self) -> None:
        with pytest.raises(ArmError, match="no records"):
            summarise([])

    def test_an_entirely_unparseable_arm_is_an_error(self) -> None:
        with pytest.raises(ArmError, match="unparseable"):
            summarise([row("p1", fired=None, should_fire=True)])

    def test_an_arm_with_one_label_is_an_error(self) -> None:
        """0.0 would read as a measurement; the rate is undefined."""
        with pytest.raises(ArmError, match="needs both labels"):
            summarise([row("p1", fired=True, should_fire=True)])


# -- covers -----------------------------------------------------------------


class TestCoversRates:
    ROWS: ClassVar[list[dict[str, Any]]] = [
        row("p1", fired=True, should_fire=True, covers=True),
        row("p2", fired=True, should_fire=True, covers=False),
        row("p3", fired=False, should_fire=True, covers=False),
        row("n1", fired=False, should_fire=False),
    ]

    def test_both_denominators_are_returned(self) -> None:
        rates = covers_rates(self.ROWS)
        assert (rates.n_labelled, rates.n_answered) == (3, 2)
        assert rates.over_labelled == pytest.approx(1 / 3)
        assert rates.over_answered == pytest.approx(1 / 2)

    def test_they_differ_and_that_is_the_point(self) -> None:
        rates = covers_rates(self.ROWS)
        assert rates.over_labelled != rates.over_answered

    def test_chance_is_reported_when_the_entry_count_is_known(self) -> None:
        assert covers_rates(self.ROWS, n_entries=2).chance == 0.5
        assert covers_rates(self.ROWS).chance is None

    def test_an_arm_with_no_labelled_routes_is_an_error(self) -> None:
        with pytest.raises(ArmError, match="no labelled routes"):
            covers_rates([row("n1", fired=False, should_fire=False)])

    def test_an_arm_that_never_fired_has_a_defined_answered_rate(self) -> None:
        rates = covers_rates([row("p1", fired=False, should_fire=True, covers=False)])
        assert rates.n_answered == 0
        assert rates.over_answered == 0.0


# -- pairing ----------------------------------------------------------------


class TestPerItemCorrectness:
    def test_it_averages_over_repeats(self) -> None:
        rates = per_item_correctness(
            [
                row("p1", fired=True, should_fire=True),
                row("p1", fired=False, should_fire=True, repeat=1),
            ]
        )
        assert rates == {"p1": 0.5}

    def test_a_case_whose_every_repeat_failed_to_parse_is_absent(self) -> None:
        rates = per_item_correctness(
            [
                row("p1", fired=None, should_fire=True),
                row("p2", fired=True, should_fire=True),
            ]
        )
        assert "p1" not in rates, "absent, not zero -- zero would be a measurement"


class TestCompare:
    def test_identical_arms_do_not_raise(self) -> None:
        """`wilcoxon` raises on an all-zero difference vector.

        Comparing an arm against itself is a thing a script does, and it must
        return p = 1.0 rather than an exception.
        """
        arm = [row("p1", fired=True, should_fire=True), row("n1", fired=False, should_fire=False)]
        result = compare(arm, arm)
        assert result.p_value == 1.0
        assert result.n_differing == 0
        assert result.moved == ()

    def test_it_pairs_on_case_id_not_on_position(self) -> None:
        """Two arms may carry different repeat counts.

        Positional pairing would compare p1's first repeat against p2's, which
        is a silently wrong answer rather than an error.
        """
        a = [
            row("p1", fired=True, should_fire=True),
            row("p1", fired=True, should_fire=True, repeat=1),
            row("n1", fired=False, should_fire=False),
        ]
        b = [row("n1", fired=False, should_fire=False), row("p1", fired=False, should_fire=True)]
        result = compare(a, b)
        assert result.n_shared == 2
        assert result.moved == (("p1", 1.0, 0.0),)
        assert (result.favouring_a, result.favouring_b) == (1, 0)

    def test_it_uses_only_the_shared_cases(self) -> None:
        a = [row("p1", fired=True, should_fire=True), row("n1", fired=False, should_fire=False)]
        b = [row("p1", fired=True, should_fire=True), row("n2", fired=True, should_fire=False)]
        assert compare(a, b).n_shared == 1

    def test_disjoint_arms_are_an_error(self) -> None:
        a = [row("p1", fired=True, should_fire=True)]
        b = [row("p2", fired=True, should_fire=True)]
        with pytest.raises(ArmError, match="share no case ids"):
            compare(a, b)

    def test_the_direction_columns_are_not_symmetric(self) -> None:
        a = [row("p1", fired=True, should_fire=True), row("p2", fired=False, should_fire=True)]
        b = [row("p1", fired=False, should_fire=True), row("p2", fired=False, should_fire=True)]
        result = compare(a, b)
        assert (result.favouring_a, result.favouring_b) == (1, 0)
        assert compare(b, a).favouring_b == 1


def test_format_comparison_names_both_arms_and_the_test() -> None:
    a = [row("p1", fired=True, should_fire=True), row("n1", fired=False, should_fire=False)]
    b = [row("p1", fired=False, should_fire=True), row("n1", fired=False, should_fire=False)]
    lines = "\n".join(format_comparison("one", "four", compare(a, b)))
    assert "one" in lines
    assert "four" in lines
    assert "paired Wilcoxon" in lines, "the estimator must be named in the output it produces"
    assert "p1: 1.00 -> 0.00" in lines


# -- the published numbers --------------------------------------------------


class TestItReproducesThePublishedNumbers:
    """The point of the module.

    These are read off the committed `results/**/README.md` files, which were
    produced by ad-hoc scripts. If this library disagrees with them, one of the
    two is wrong and the run records cannot be trusted either way.
    """

    @pytest.mark.parametrize(
        ("directory", "accuracy", "recall", "false_positive_rate"),
        [
            ("2026-08-12-615f7cb-four-arm", 0.951, 0.800, 0.000),
            ("2026-08-12-c2673c5-m5-two-entries", 0.940, 0.756, 0.000),
            ("2026-08-13-82b4ab8-m6-pairing", 0.952, 0.806, 0.000),
        ],
    )
    def test_firing_matches_the_published_readme(
        self, directory: str, accuracy: float, recall: float, false_positive_rate: float
    ) -> None:
        path = RESULTS / directory / "verdicts.jsonl"
        if not path.exists():  # pragma: no cover - published results are committed
            pytest.skip(f"{directory} not published")
        report = summarise(load_arm(path))
        assert report.unparseable == 0
        assert report.accuracy == pytest.approx(accuracy, abs=0.001)
        assert report.recall == pytest.approx(recall, abs=0.001)
        assert report.false_positive_rate == pytest.approx(false_positive_rate, abs=0.001)

    @pytest.mark.parametrize(
        ("directory", "over_labelled", "over_answered"),
        [
            ("2026-08-12-c2673c5-m5-two-entries", 0.743, 0.897),
            ("2026-08-13-82b4ab8-m6-pairing", 0.857, 1.000),
        ],
    )
    def test_covers_matches_both_published_denominators(
        self, directory: str, over_labelled: float, over_answered: float
    ) -> None:
        path = RESULTS / directory / "verdicts.jsonl"
        if not path.exists():  # pragma: no cover - published results are committed
            pytest.skip(f"{directory} not published")
        rates = covers_rates(load_arm(path), n_entries=2)
        assert rates.over_labelled == pytest.approx(over_labelled, abs=0.001)
        assert rates.over_answered == pytest.approx(over_answered, abs=0.001)

    def test_m6_against_m5_reproduces_the_published_p_value(self) -> None:
        """The M6 README states 4 items differ at p = 0.273."""
        m5 = RESULTS / "2026-08-12-c2673c5-m5-two-entries" / "verdicts.jsonl"
        m6 = RESULTS / "2026-08-13-82b4ab8-m6-pairing" / "verdicts.jsonl"
        if not (m5.exists() and m6.exists()):  # pragma: no cover - both are committed
            pytest.skip("results not published")
        result = compare(load_arm(m5), load_arm(m6))
        assert result.n_shared == 73
        assert result.n_differing == 4
        assert result.p_value == pytest.approx(0.273, abs=0.001)

    def test_covers_is_not_stable_across_partitions(self) -> None:
        """M6's finding, asserted as a regression test on the record itself.

        If these two ever come out equal, either a checkpoint has been
        overwritten or the partition stopped mattering, and both are things
        someone must be told about rather than discover in a write-up.
        """
        m5 = RESULTS / "2026-08-12-c2673c5-m5-two-entries" / "verdicts.jsonl"
        m6 = RESULTS / "2026-08-13-82b4ab8-m6-pairing" / "verdicts.jsonl"
        if not (m5.exists() and m6.exists()):  # pragma: no cover - both are committed
            pytest.skip("results not published")
        gap = covers_rates(load_arm(m6)).over_labelled - covers_rates(load_arm(m5)).over_labelled
        assert gap > 0.10, "the two partitions differ by more than ten points on covers"
