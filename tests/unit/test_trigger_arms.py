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
    bootstrap_rate,
    compare,
    covers_rates,
    format_bands,
    format_comparison,
    format_rate,
    label_versions_comparable,
    load_arm,
    models_comparable,
    per_item_correctness,
    skill_versions_comparable,
    summarise,
    summarise_by_band,
    venue_comparable,
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


def banded(
    case: str,
    *,
    fired: bool | None,
    should_fire: bool,
    band: str,
    triple: str,
    repeat: int = 0,
) -> dict[str, object]:
    """A version 3 row: the same verdict, carrying its stratum and its cluster."""
    return row(case, fired=fired, should_fire=should_fire, repeat=repeat) | {
        "band": band,
        "triple": triple,
    }


def a_triple(name: str, *, band: str, correct: bool, repeat: int = 0) -> list[dict[str, object]]:
    """One positive and two negatives from one body, all right or all wrong.

    The extreme case on purpose. Three items built from one body are one
    authored artefact seen three times, and a body that is confusing moves all
    three together; this is that correlation at its maximum, which is where an
    item-level bootstrap is most wrong.
    """
    return [
        banded(
            f"{name}p",
            fired=correct,
            should_fire=True,
            band=band,
            triple=name,
            repeat=repeat,
        ),
        *(
            banded(
                f"{name}n{index}",
                fired=not correct,
                should_fire=False,
                band=band,
                triple=name,
                repeat=repeat,
            )
            for index in (1, 2)
        ),
    ]


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


# -- per band ---------------------------------------------------------------


class TestSummariseByBand:
    """Track N. The question version 3 of the corpus exists to ask.

    Every published number here sits on turns of 25 words or fewer. Whether
    firing survives at 1,200 words is the thing a pooled figure cannot say, and
    the pooled figure is what a caller gets by default.
    """

    #: Perfect on the short band, half wrong on the long one. Not a fixture that
    #: merely parses: the two bands must come out with *different* numbers, or
    #: the function is splitting records and computing nothing.
    ROWS: ClassVar[list[dict[str, Any]]] = [
        *a_triple("s01", band="s", correct=True),
        *a_triple("s02", band="s", correct=True),
        *a_triple("x01", band="xl", correct=True),
        *a_triple("x02", band="xl", correct=False),
    ]

    def test_the_bands_carry_different_rates(self) -> None:
        bands = summarise_by_band(self.ROWS)
        assert bands["s"].accuracy == 1.0
        assert bands["xl"].accuracy == 0.5, "a real drop, not a rounding difference"
        assert bands["s"].recall == 1.0
        assert bands["xl"].recall == 0.5
        assert bands["xl"].false_positive_rate == 0.5
        assert bands["xl"].missed == ("x02p",)

    def test_the_denominators_are_per_band_and_not_the_pooled_one(self) -> None:
        bands = summarise_by_band(self.ROWS)
        assert bands["s"].n_records == 6
        assert bands["xl"].n_records == 6
        assert summarise(self.ROWS).accuracy == 0.75, (
            "the pooled figure sits between the two bands and hides both"
        )

    def test_it_returns_the_bands_shortest_first(self) -> None:
        """Corpus order, not insertion order and not alphabetical.

        Alphabetical would read l, m, s, xl, which puts the 200-word band first
        and reads as though accuracy rose with length.
        """
        rows = [
            *a_triple("x01", band="xl", correct=True),
            *a_triple("l01", band="l", correct=True),
            *a_triple("s01", band="s", correct=False),
            *a_triple("m01", band="m", correct=True),
        ]
        assert list(summarise_by_band(rows)) == ["s", "m", "l", "xl"]

    def test_a_band_the_corpus_does_not_declare_sorts_last(self) -> None:
        rows = [
            *a_triple("z01", band="xxl", correct=True),
            *a_triple("s01", band="s", correct=False),
        ]
        assert list(summarise_by_band(rows)) == ["s", "xxl"]

    def test_a_checkpoint_with_no_bands_is_refused(self) -> None:
        """A version 2 checkpoint. `{}` would read as "the bands agree"."""
        with pytest.raises(ArmError, match="no record carries a `band`"):
            summarise_by_band(
                [
                    row("p1", fired=True, should_fire=True),
                    row("n1", fired=False, should_fire=False),
                ]
            )

    def test_a_half_collected_band_is_refused_by_name(self) -> None:
        """The shape an interrupted `--band` run leaves behind.

        Its precision would read 0.000, which is a number rather than the
        absence of one.
        """
        rows = [
            *a_triple("s01", band="s", correct=True),
            banded("x01p", fired=True, should_fire=True, band="xl", triple="x01"),
        ]
        with pytest.raises(ArmError, match="band 'xl' cannot be scored"):
            summarise_by_band(rows)


def test_format_bands_prints_a_row_per_band_with_its_denominator() -> None:
    lines = "\n".join(format_bands(summarise_by_band(TestSummariseByBand.ROWS)))
    assert "band" in lines
    assert "  s    " in lines
    assert "  xl   " in lines
    assert "1.000" in lines, "the short band's accuracy"
    assert "0.500" in lines, "the long band's"
    assert "never fired: x02p" in lines


# -- the clustered bootstrap ------------------------------------------------


class TestBootstrapRate:
    """The resampling unit is the triple, and it is not the item.

    Three items sharing a body are one authored artefact seen three times.
    Resampling items pretends they are three independent draws and returns an
    interval that is too narrow -- wrong in the anti-conservative direction,
    which is the direction that publishes an effect that is not there.
    """

    #: Six triples, three of them right throughout and three wrong throughout.
    #: The correlation at its maximum, which is where the wrong unit is most
    #: wrong and therefore where the difference is visible rather than argued.
    ROWS: ClassVar[list[dict[str, Any]]] = [
        *a_triple("t1", band="l", correct=True),
        *a_triple("t2", band="l", correct=True),
        *a_triple("t3", band="l", correct=True),
        *a_triple("t4", band="l", correct=False),
        *a_triple("t5", band="l", correct=False),
        *a_triple("t6", band="l", correct=False),
    ]

    def test_the_point_estimate_is_the_mean_per_item_correctness(self) -> None:
        rate = bootstrap_rate(self.ROWS, seed=0)
        assert rate.point_estimate == pytest.approx(0.5)
        assert (rate.n_items, rate.n_clusters) == (18, 6)

    def test_the_interval_is_not_degenerate(self) -> None:
        """The non-zero check. A resampler that returns a point is not one."""
        rate = bootstrap_rate(self.ROWS, seed=0)
        assert rate.standard_error > 0.0
        assert rate.width > 0.0
        assert rate.ci_low < rate.point_estimate < rate.ci_high

    def test_clustering_widens_the_interval_over_resampling_items(self) -> None:
        """The reason the function exists, asserted rather than described.

        At three items per cluster and an ICC of 1 the design effect is 3, so
        the clustered standard error should run about sqrt(3) times the
        item-level one. If these two ever come out equal, the cluster label is
        being ignored and every interval this reports is too narrow.
        """
        clustered = bootstrap_rate(self.ROWS, seed=0)
        per_item = bootstrap_rate(self.ROWS, cluster_on="case", seed=0)
        assert clustered.standard_error > 1.4 * per_item.standard_error
        assert clustered.width > per_item.width

    def test_the_design_effect_is_reported_and_is_above_one(self) -> None:
        rate = bootstrap_rate(self.ROWS, seed=0)
        assert rate.icc == pytest.approx(1.0)
        assert rate.design_effect == pytest.approx(3.0)
        assert rate.effective_n == pytest.approx(6.0)
        assert rate.effective_n < rate.n_items, "eighteen items are worth six"

    def test_resampling_items_reports_no_clustering_cost(self) -> None:
        """`cluster_on="case"` is the wrong unit, and says so in its own fields."""
        rate = bootstrap_rate(self.ROWS, cluster_on="case", seed=0)
        assert rate.n_clusters == rate.n_items == 18
        assert rate.icc == 0.0
        assert rate.design_effect == 1.0
        assert rate.effective_n == pytest.approx(18.0)

    def test_it_is_reproducible_under_a_seed(self) -> None:
        """A report that moves between two readings of one checkpoint is not one."""
        first = bootstrap_rate(self.ROWS, seed=7)
        second = bootstrap_rate(self.ROWS, seed=7)
        assert (first.ci_low, first.ci_high) == (second.ci_low, second.ci_high)

    def test_filtering_to_the_positives_gives_recall(self) -> None:
        """And each triple then contributes one item, so there is nothing to cluster.

        Worth pinning: the same call on a filtered subset is a different measure,
        and the class cannot tell the caller which one it returned.
        """
        positives = [dict(record) for record in self.ROWS if record["should_fire"]]
        rate = bootstrap_rate(positives, seed=0)
        assert rate.point_estimate == pytest.approx(summarise(self.ROWS).recall)
        assert rate.point_estimate == pytest.approx(0.5)
        assert (rate.n_items, rate.n_clusters) == (6, 6)
        assert rate.icc == 0.0

    def test_filtering_to_the_negatives_gives_one_minus_the_false_positive_rate(self) -> None:
        negatives = [dict(record) for record in self.ROWS if not record["should_fire"]]
        rate = bootstrap_rate(negatives, seed=0)
        assert rate.point_estimate == pytest.approx(1.0 - summarise(self.ROWS).false_positive_rate)
        assert rate.point_estimate == pytest.approx(0.5)

    def test_a_confidence_level_widens_the_interval(self) -> None:
        narrow = bootstrap_rate(self.ROWS, confidence=0.50, seed=0)
        wide = bootstrap_rate(self.ROWS, confidence=0.99, seed=0)
        assert wide.width > narrow.width
        assert (narrow.confidence, wide.confidence) == (0.50, 0.99)

    def test_an_unparseable_repeat_does_not_remove_its_item(self) -> None:
        rows = [
            *a_triple("t1", band="s", correct=True),
            *a_triple("t2", band="s", correct=False),
            banded("t1p", fired=None, should_fire=True, band="s", triple="t1", repeat=1),
        ]
        rate = bootstrap_rate(rows, seed=0)
        assert rate.n_items == 6, "t1p is still an item; only its null repeat is dropped"

    def test_an_item_whose_every_repeat_failed_to_parse_is_absent(self) -> None:
        rows = [
            *a_triple("t1", band="s", correct=True),
            *a_triple("t2", band="s", correct=False),
            banded("t3p", fired=None, should_fire=True, band="s", triple="t3"),
        ]
        rate = bootstrap_rate(rows, seed=0)
        assert rate.n_items == 6, "absent, not scored as a failure to fire"
        assert rate.n_clusters == 2

    def test_a_checkpoint_with_no_triples_is_refused(self) -> None:
        with pytest.raises(ArmError, match="no record carries 'triple'"):
            bootstrap_rate(
                [
                    row("p1", fired=True, should_fire=True),
                    row("n1", fired=False, should_fire=False),
                ]
            )

    def test_a_partly_labelled_checkpoint_is_refused(self) -> None:
        """Dropping the unlabelled rows would move the denominator in silence."""
        rows = [*self.ROWS, row("p9", fired=True, should_fire=True)]
        with pytest.raises(ArmError, match="carry no 'triple'"):
            bootstrap_rate(rows)

    def test_an_entirely_unparseable_arm_is_refused(self) -> None:
        rows = [
            banded("t1p", fired=None, should_fire=True, band="s", triple="t1"),
            banded("t2p", fired=None, should_fire=True, band="s", triple="t2"),
        ]
        with pytest.raises(ArmError, match="no rate to resample"):
            bootstrap_rate(rows)

    def test_a_single_cluster_is_refused(self) -> None:
        """One cluster resamples to itself: a zero-width interval reading as certainty."""
        with pytest.raises(ArmError, match="single 'triple'"):
            bootstrap_rate(a_triple("t1", band="s", correct=True))

    def test_a_case_under_two_triples_is_refused(self) -> None:
        """Two corpora appended to one checkpoint, which the runner's paths prevent."""
        rows = [
            *a_triple("t1", band="s", correct=True),
            *a_triple("t2", band="s", correct=False),
            banded("t1p", fired=True, should_fire=True, band="s", triple="other", repeat=1),
        ]
        with pytest.raises(ArmError, match="appears under two 'triple' labels"):
            bootstrap_rate(rows)

    def test_an_impossible_confidence_level_is_refused(self) -> None:
        with pytest.raises(ValueError, match="confidence"):
            bootstrap_rate(self.ROWS, confidence=1.0)


def test_format_rate_names_the_cluster_count_and_the_design_effect() -> None:
    """A width nobody can attribute is a width taken on trust."""
    lines = "\n".join(format_rate("accuracy", bootstrap_rate(TestBootstrapRate.ROWS, seed=0)))
    assert "accuracy" in lines
    assert "18 item(s) in 6 cluster(s)" in lines
    assert "ICC 1.000" in lines
    assert "design effect 3.00" in lines
    assert "effective n 6.0" in lines


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
            ("2026-08-13-5ccedb9-m6b-third-partition", 0.945, 0.806, 0.009),
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
            ("2026-08-13-5ccedb9-m6b-third-partition", 0.571, 0.696),
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
        m6b = RESULTS / "2026-08-13-5ccedb9-m6b-third-partition" / "verdicts.jsonl"
        rates = [
            covers_rates(load_arm(path)).over_labelled for path in (m5, m6, m6b) if path.exists()
        ]
        assert len(rates) == 3, "all three partitions at n=2 are published"
        assert max(rates) - min(rates) > 0.25, (
            "the complete partition set at n=2 spans more than twenty-five points"
        )


class TestLabelVersionsComparable:
    """The fourth defect of this shape, guarded before it could produce a number.

    Moving `x-n21` from the positives to the negatives on 2026-08-13 raised
    recall between 3 and 5 points on every arm on disk. No model was re-run. A
    comparison spanning that change would have read as an improvement.
    """

    def test_two_arms_at_the_same_version_compare(self) -> None:
        a = [
            row("p1", fired=True, should_fire=True) | {"set_version": 2},
            row("n1", fired=False, should_fire=False) | {"set_version": 2},
        ]
        assert label_versions_comparable(a, a) is None
        assert compare(a, a).p_value == 1.0

    def test_records_without_the_field_are_version_one(self) -> None:
        """The runs the guard was written for predate the field."""
        a = [row("p1", fired=True, should_fire=True)]
        b = [row("p1", fired=True, should_fire=True) | {"set_version": 1}]
        assert label_versions_comparable(a, b) is None

    def test_a_mixed_comparison_is_refused(self) -> None:
        a = [row("p1", fired=True, should_fire=True)]
        b = [row("p1", fired=False, should_fire=True) | {"set_version": 2}]
        assert label_versions_comparable(a, b) is not None
        with pytest.raises(ArmError, match="different label revisions"):
            compare(a, b)

    def test_the_refusal_names_both_revisions(self) -> None:
        a = [row("p1", fired=True, should_fire=True) | {"set_version": 1}]
        b = [row("p1", fired=True, should_fire=True) | {"set_version": 3}]
        reason = label_versions_comparable(a, b)
        assert reason is not None
        assert "[1]" in reason
        assert "[3]" in reason


class TestModelsComparable:
    """Track N8. The same defect one axis over from the label revision.

    `--model` is an argument with a default that moves every number in a run,
    and the tier survived only as prose in a hand-written README while the
    verdict records carried no model at all.
    """

    def test_two_arms_on_the_same_model_compare(self) -> None:
        a = [
            row("p1", fired=True, should_fire=True) | {"model": "haiku"},
            row("n1", fired=False, should_fire=False) | {"model": "haiku"},
        ]
        assert models_comparable(a, a) is None
        assert compare(a, a).p_value == 1.0

    def test_two_unstamped_arms_still_compare(self) -> None:
        """Every published comparison predates the stamp and none is voided.

        The guard knows nothing about these records and says nothing about
        them, which is a different statement from saying they match.
        """
        a = [row("p1", fired=True, should_fire=True)]
        b = [row("p1", fired=False, should_fire=True)]
        assert models_comparable(a, b) is None

    def test_a_stamped_arm_against_an_unstamped_one_is_refused(self) -> None:
        """An absent model is unknown, not the default. Standing rule 1."""
        a = [row("p1", fired=True, should_fire=True)]
        b = [row("p1", fired=False, should_fire=True) | {"model": "haiku"}]
        reason = models_comparable(a, b)
        assert reason is not None
        assert "does not mean the default tier" in reason
        with pytest.raises(ArmError, match="records the model it ran on"):
            compare(a, b)

    def test_two_different_models_are_refused(self) -> None:
        a = [row("p1", fired=True, should_fire=True) | {"model": "haiku"}]
        b = [row("p1", fired=True, should_fire=True) | {"model": "sonnet"}]
        reason = models_comparable(a, b)
        assert reason is not None
        assert "haiku" in reason
        assert "sonnet" in reason
        with pytest.raises(ArmError, match="ran on different models"):
            compare(a, b)

    def test_the_label_guard_runs_first(self) -> None:
        """Both differ; the reported reason is the one already published about."""
        a = [row("p1", fired=True, should_fire=True) | {"set_version": 1, "model": "haiku"}]
        b = [row("p1", fired=True, should_fire=True) | {"set_version": 3, "model": "sonnet"}]
        with pytest.raises(ArmError, match="different label revisions"):
            compare(a, b)


class TestVenueComparable:
    """Track N9. The description sits in a different place, not just a
    different tier or a different label revision -- ``--append-system-prompt``
    versus ``--system-prompt``.

    Standing rule 2: this guard must be shown passing a known-good case before
    it is shown refusing a bad one. `test_two_arms_at_the_same_venue_compare`
    and `test_two_unstamped_arms_are_both_treated_as_substituted` are the
    known-good cases; the rest are the refusals.
    """

    def test_two_arms_at_the_same_venue_compare(self) -> None:
        """Known-good case, run first: both arms in situ, same venue, no refusal."""
        a = [
            row("p1", fired=True, should_fire=True) | {"in_situ": True},
            row("n1", fired=False, should_fire=False) | {"in_situ": True},
        ]
        assert venue_comparable(a, a) is None
        assert compare(a, a).p_value == 1.0

    def test_two_unstamped_arms_are_both_treated_as_substituted(self) -> None:
        """Every arm published before this stamp existed sent the description via

        --system-prompt -- `ask()` built every `Conversation` with no `in_situ`
        argument at all, which resolves to `in_situ=False` by the parameter's
        own default. So two unstamped arms are exactly as comparable as they
        were yesterday, unlike the model guard's unstamped case.
        """
        a = [row("p1", fired=True, should_fire=True)]
        b = [row("p1", fired=False, should_fire=True)]
        assert venue_comparable(a, b) is None
        assert compare(a, b).n_shared == 1

    def test_an_explicit_false_matches_an_unstamped_row(self) -> None:
        """`in_situ=False` and an absent field are the same fact, not two."""
        a = [row("p1", fired=True, should_fire=True) | {"in_situ": False}]
        b = [row("p1", fired=True, should_fire=True)]
        assert venue_comparable(a, b) is None

    def test_an_in_situ_arm_against_an_unstamped_one_is_refused(self) -> None:
        """The transition where the risk is real: N9's own comparison against N6."""
        a = [row("p1", fired=True, should_fire=True) | {"in_situ": True}]
        b = [row("p1", fired=False, should_fire=True)]
        reason = venue_comparable(a, b)
        assert reason is not None
        assert "in situ" in reason
        assert "substituted" in reason
        with pytest.raises(ArmError, match="different prompt venues"):
            compare(a, b)

    def test_the_label_guard_runs_before_the_venue_guard(self) -> None:
        """Both differ; the reported reason is the one this repository has

        already been burned by -- checked so the ordering in `compare` does not
        silently change which refusal a caller sees.
        """
        a = [row("p1", fired=True, should_fire=True) | {"set_version": 1, "in_situ": True}]
        b = [row("p1", fired=True, should_fire=True) | {"set_version": 3, "in_situ": False}]
        with pytest.raises(ArmError, match="different label revisions"):
            compare(a, b)

    def test_the_model_guard_runs_before_the_venue_guard(self) -> None:
        a = [row("p1", fired=True, should_fire=True) | {"model": "haiku", "in_situ": True}]
        b = [row("p1", fired=True, should_fire=True) | {"model": "sonnet", "in_situ": False}]
        with pytest.raises(ArmError, match="ran on different models"):
            compare(a, b)


class TestSkillVersionsComparable:
    """The fourth guard. `set_version` tracks the corpus; this tracks

    `SKILL.md`'s own `metadata.version`, which is a different axis -- the
    2026-08-19 bump (0.2.1 -> 0.3.0) rewrote the frontmatter `description`
    itself (four procedures to six) without moving a single label, so
    `set_version` alone cannot see it. Before this guard existed, `compare()`
    silently scored a v0.2.1 arm against a v0.3.0 arm as if they measured the
    same description; see the reproduction below.

    An absent `skill_version` is read the same way `models_comparable` reads
    an absent `model` -- unknown, not a default -- because `metadata.version`
    has moved three times on record (0.2.0, 0.2.1, 0.3.0) and an unstamped
    row could have run against any of them. That is the opposite call from
    `venue_comparable`'s `in_situ`, which had no prior value to have been
    silently at.
    """

    def test_it_reproduces_the_defect_this_guard_closes(self) -> None:
        """This is the failure demonstrated against the pre-fix code: two arms

        explicitly stamped at different skill revisions compared cleanly and
        returned a p-value, because nothing before this guard looked at
        `skill_version` at all. Run against `trigger_arms.py` before
        `skill_versions_comparable` was wired into `compare()`, this test's
        final `pytest.raises` fails -- `compare()` returns
        `ArmComparison(n_shared=2, n_differing=2, favouring_a=2, favouring_b=0,
        p_value=0.5, ...)` instead of raising, exactly the two-different-
        products comparison the task exists to close.
        """
        a = [
            row("p1", fired=True, should_fire=True) | {"skill_version": "0.2.1"},
            row("n1", fired=False, should_fire=False) | {"skill_version": "0.2.1"},
        ]
        b = [
            row("p1", fired=False, should_fire=True) | {"skill_version": "0.3.0"},
            row("n1", fired=True, should_fire=False) | {"skill_version": "0.3.0"},
        ]
        assert skill_versions_comparable(a, b) is not None
        with pytest.raises(ArmError, match="different skill revisions"):
            compare(a, b)

    def test_two_arms_at_the_same_skill_version_compare(self) -> None:
        """Known-good case, run first: same revision, no refusal."""
        a = [
            row("p1", fired=True, should_fire=True) | {"skill_version": "0.3.0"},
            row("n1", fired=False, should_fire=False) | {"skill_version": "0.3.0"},
        ]
        assert skill_versions_comparable(a, a) is None
        assert compare(a, a).p_value == 1.0

    def test_two_unstamped_arms_still_compare(self) -> None:
        """Every record on disk predates this field, and none is voided.

        The guard knows nothing about these records and says nothing about
        them -- the `models_comparable` reading, not the `venue_comparable` one.
        """
        a = [row("p1", fired=True, should_fire=True)]
        b = [row("p1", fired=False, should_fire=True)]
        assert skill_versions_comparable(a, b) is None
        assert compare(a, b).n_shared == 1

    def test_a_stamped_arm_against_an_unstamped_one_is_refused(self) -> None:
        """An absent skill_version is unknown, not the shipped revision.

        Standing rule 1: `metadata.version` has been 0.2.0, 0.2.1 and 0.3.0 on
        record, and an unstamped row does not say which of those it ran
        against.
        """
        a = [row("p1", fired=True, should_fire=True)]
        b = [row("p1", fired=False, should_fire=True) | {"skill_version": "0.3.0"}]
        reason = skill_versions_comparable(a, b)
        assert reason is not None
        assert "does not mean any particular" in reason
        with pytest.raises(ArmError, match="records the skill revision it ran against"):
            compare(a, b)

    def test_two_different_skill_versions_are_refused(self) -> None:
        a = [row("p1", fired=True, should_fire=True) | {"skill_version": "0.2.1"}]
        b = [row("p1", fired=True, should_fire=True) | {"skill_version": "0.3.0"}]
        reason = skill_versions_comparable(a, b)
        assert reason is not None
        assert "0.2.1" in reason
        assert "0.3.0" in reason
        with pytest.raises(ArmError, match="different skill revisions"):
            compare(a, b)

    def test_the_label_guard_runs_before_the_skill_version_guard(self) -> None:
        a = [row("p1", fired=True, should_fire=True) | {"set_version": 1, "skill_version": "0.2.1"}]
        b = [row("p1", fired=True, should_fire=True) | {"set_version": 3, "skill_version": "0.3.0"}]
        with pytest.raises(ArmError, match="different label revisions"):
            compare(a, b)

    def test_the_venue_guard_runs_before_the_skill_version_guard(self) -> None:
        a = [row("p1", fired=True, should_fire=True) | {"in_situ": True, "skill_version": "0.2.1"}]
        b = [row("p1", fired=True, should_fire=True) | {"in_situ": False, "skill_version": "0.3.0"}]
        with pytest.raises(ArmError, match="different prompt venues"):
            compare(a, b)
