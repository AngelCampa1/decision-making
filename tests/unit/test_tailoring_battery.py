"""Tests for the tailoring corpus's shortcut battery.

Standing rule 2: a falsifier must be run against a known-good case before it
may fail anything. So these tests are the same two halves
``test_corpus_battery.py`` uses for the trigger corpus:

* the **known-good** synthetic triplets, which the battery must pass; and
* the **known-bad** case, which is the real corpus on disk right now --
  ``datasets/tailoring/`` was found by a human reader to have a register
  split (governing inserts read as penalties, matched inserts read as
  procedure) that this battery exists to catch. If it does not fire on the
  real three triplets, the battery does not work.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest
import yaml

from decision_evals.corpus import Finding, apply_corpus_baseline
from decision_evals.tailoring import (
    CORPUS_SCOPE,
    FEATURES,
    TAILORING_BASELINE_PATH,
    TailoringSetError,
    battery_report,
    check_shortcuts,
    extract_delta,
    inert_features,
    load_deltas,
    load_tailoring_baseline,
)
from decision_evals.triggers import TriggerCase, TriggerSet

REPO_ROOT = Path(__file__).resolve().parents[2]

# --------------------------------------------------------------------------- #
# extract_delta
# --------------------------------------------------------------------------- #


class TestExtractDelta:
    def test_recovers_a_bullet_inserted_between_two_others(self) -> None:
        base = "Intro line.\n- First bullet.\n- Second bullet.\n- Third bullet.\nOutro line.\n"
        variant = (
            "Intro line.\n- First bullet.\n- Inserted bullet with new detail.\n"
            "- Second bullet.\n- Third bullet.\nOutro line.\n"
        )
        assert extract_delta(base, variant) == "Inserted bullet with new detail."

    def test_recovers_an_insertion_immediately_before_the_final_line(self) -> None:
        base = "Intro line.\n- First bullet.\n- Second bullet.\nOutro line.\n"
        variant = (
            "Intro line.\n- First bullet.\n- Second bullet.\n"
            "- Trailing inserted bullet.\nOutro line.\n"
        )
        assert extract_delta(base, variant) == "Trailing inserted bullet."

    def test_identical_strings_have_no_delta(self) -> None:
        text = "Nothing changed here.\n"
        assert extract_delta(text, text) == ""

    def test_no_shared_affix_returns_the_whole_variant(self) -> None:
        # A degraded but loud result, not a silently wrong one -- see the
        # docstring's note on corpora authored outside the base-plus-one-
        # bullet convention.
        assert extract_delta("abc", "xyz") == "xyz"

    def test_real_corpus_triplets_recover_the_authored_fact(self) -> None:
        """The delta text should read as the inserted sentence(s), not a stray
        fragment of a neighbouring bullet -- checked against the real corpus
        rather than only a hand-built fixture, since the affix-scan's line
        snapping was written against this exact file's shape.
        """
        tailoring_dir = REPO_ROOT / "datasets" / "tailoring"
        base = yaml.safe_load(
            (tailoring_dir / "h01-raise-timing-base.yaml").read_text(encoding="utf-8")
        )["prompt"]
        governing = yaml.safe_load(
            (tailoring_dir / "h01-raise-timing-governing.yaml").read_text(encoding="utf-8")
        )["prompt"]
        delta = extract_delta(base, governing)
        assert delta.startswith("Venture debt of $500,000")
        assert delta.endswith("event of default.")
        # And no fragment of the next bullet ("Runway on the face...") leaked
        # in -- the defect the line-snap logic in extract_delta exists for.
        assert "Runway" not in delta

    def test_mid_line_insertion_with_no_earlier_newline_is_still_recovered(self) -> None:
        """A single-line insertion has no preceding newline to snap the suffix
        boundary back to, which exercises the branch where the line-snap
        cannot fire and the raw affix boundary is used as-is."""
        base = "Start middle end."
        variant = "Start inserted content middle end."
        assert extract_delta(base, variant) == "inserted content"


# --------------------------------------------------------------------------- #
# load_deltas
# --------------------------------------------------------------------------- #


class TestLoadDeltas:
    def test_missing_index_returns_an_empty_set_with_no_warnings(self, tmp_path: Path) -> None:
        result = load_deltas(tmp_path)
        assert result.trigger_set.cases == ()
        assert result.warnings == ()

    def test_index_with_no_triplets_returns_an_empty_set(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "index.yaml").write_text("triplets: []\n", encoding="utf-8")
        result = load_deltas(tmp_path)
        assert result.trigger_set.cases == ()
        assert result.warnings == ()

    def test_index_that_is_not_a_mapping_raises(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "index.yaml").write_text("- just a list\n", encoding="utf-8")
        with pytest.raises(TailoringSetError):
            load_deltas(tmp_path)

    def test_unreadable_index_raises(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "index.yaml").write_text("key: [unterminated\n", encoding="utf-8")
        with pytest.raises(TailoringSetError):
            load_deltas(tmp_path)

    def test_malformed_triplet_entry_is_skipped_with_a_warning(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "index.yaml").write_text(
            "triplets:\n  - not_an_id_or_files: true\n", encoding="utf-8"
        )
        result = load_deltas(tmp_path)
        assert result.trigger_set.cases == ()
        assert len(result.warnings) == 1
        assert "malformed" in result.warnings[0]

    def test_triplet_with_wrong_file_count_is_skipped(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "index.yaml").write_text(
            "triplets:\n  - id: t1\n    files: [a.yaml, b.yaml]\n", encoding="utf-8"
        )
        result = load_deltas(tmp_path)
        assert result.trigger_set.cases == ()
        assert "3-element" in result.warnings[0]

    def test_triplet_naming_a_missing_file_is_skipped(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "index.yaml").write_text(
            "triplets:\n  - id: t1\n    files: [a.yaml, b.yaml, c.yaml]\n", encoding="utf-8"
        )
        result = load_deltas(tmp_path)
        assert result.trigger_set.cases == ()
        assert len(result.warnings) == 1
        assert "t1" in result.warnings[0]

    def test_triplet_file_missing_arm_or_prompt_is_skipped(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "a.yaml").write_text("arm: base\nprompt: hi\n", encoding="utf-8")
        (tailoring_dir / "b.yaml").write_text("arm: governing\n", encoding="utf-8")
        (tailoring_dir / "c.yaml").write_text("arm: matched\nprompt: hi too\n", encoding="utf-8")
        (tailoring_dir / "index.yaml").write_text(
            "triplets:\n  - id: t1\n    files: [a.yaml, b.yaml, c.yaml]\n", encoding="utf-8"
        )
        result = load_deltas(tmp_path)
        assert result.trigger_set.cases == ()
        assert len(result.warnings) == 1

    def test_triplet_missing_an_arm_is_skipped(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "a.yaml").write_text("arm: base\nprompt: hi\n", encoding="utf-8")
        (tailoring_dir / "b.yaml").write_text("arm: governing\nprompt: hi too\n", encoding="utf-8")
        (tailoring_dir / "c.yaml").write_text("arm: base\nprompt: hi three\n", encoding="utf-8")
        (tailoring_dir / "index.yaml").write_text(
            "triplets:\n  - id: t1\n    files: [a.yaml, b.yaml, c.yaml]\n", encoding="utf-8"
        )
        result = load_deltas(tmp_path)
        assert result.trigger_set.cases == ()
        assert "missing arm" in result.warnings[0]

    def test_one_good_triplet_among_a_bad_one_still_loads(self, tmp_path: Path) -> None:
        tailoring_dir = tmp_path / "datasets" / "tailoring"
        tailoring_dir.mkdir(parents=True)
        (tailoring_dir / "a.yaml").write_text(
            "arm: base\nprompt: |\n  Intro.\n  - One.\n  - Two.\n  Outro.\n", encoding="utf-8"
        )
        (tailoring_dir / "b.yaml").write_text(
            "arm: governing\nprompt: |\n  Intro.\n  - One.\n  - Extra fact here.\n"
            "  - Two.\n  Outro.\n",
            encoding="utf-8",
        )
        (tailoring_dir / "c.yaml").write_text(
            "arm: matched\nprompt: |\n  Intro.\n  - One.\n  - Different fact here.\n"
            "  - Two.\n  Outro.\n",
            encoding="utf-8",
        )
        (tailoring_dir / "index.yaml").write_text(
            "triplets:\n"
            "  - id: good\n    files: [a.yaml, b.yaml, c.yaml]\n"
            "  - id: bad\n    files: [missing1.yaml, missing2.yaml, missing3.yaml]\n",
            encoding="utf-8",
        )
        result = load_deltas(tmp_path)
        assert len(result.trigger_set.cases) == 2
        assert len(result.warnings) == 1
        assert "bad" in result.warnings[0]

    def test_the_real_corpus_loads_three_triplets(self) -> None:
        result = load_deltas(REPO_ROOT)
        assert result.warnings == ()
        assert len(result.trigger_set.positives) == 3
        assert len(result.trigger_set.negatives) == 3
        assert {case.triple for case in result.trigger_set.cases} == {"h01", "h02", "h03"}


# --------------------------------------------------------------------------- #
# The known-good synthetic corpus.
#
# Four shapes, chosen so that every FEATURES entry takes a different value
# across them (different lengths, one with a date, one with numerals, one
# leaning on penalty vocabulary). Every ordered pair of distinct shapes forms
# one triplet, governing first. Because the pairing is the full permutation,
# every shape appears as governing exactly as often as it appears as matched,
# which makes each feature score *exactly* 0.500 pooled and matched -- not
# approximately, and not because the shapes were tuned until it did. That is
# what makes this known-good rather than hoped-good, the same argument
# ``test_corpus_battery.py`` makes for its own rotating fixture.
# --------------------------------------------------------------------------- #
_SHAPES = {
    "brief": "The vendor confirmed delivery next Tuesday afternoon as agreed.",
    "dated": "On 2025-03-14 the committee approved a small budget line for repairs.",
    "numeric": "Clause 4.1 sets a minimum balance of ten thousand units, checked weekly.",
    "wordy": (
        "Someone mentioned in passing that the schedule might shift a little later "
        "this quarter, though nothing about it is confirmed either way just yet."
    ),
}


def _balanced_corpus() -> TriggerSet:
    cases: list[TriggerCase] = []
    for index, (governing, matched) in enumerate(itertools.permutations(_SHAPES, 2)):
        cases.append(
            TriggerCase(
                id=f"t{index}-governing",
                turn=_SHAPES[governing],
                should_fire=True,
                why="fixture",
                triple=f"t{index}",
            )
        )
        cases.append(
            TriggerCase(
                id=f"t{index}-matched",
                turn=_SHAPES[matched],
                should_fire=False,
                why="fixture",
                triple=f"t{index}",
            )
        )
    return TriggerSet(skill="tailoring", cases=tuple(cases))


class TestTheGuardPassesAKnownGoodCorpus:
    """Standing rule 2: run the falsifier against a known-good case first."""

    def test_the_known_good_corpus_raises_nothing(self) -> None:
        assert check_shortcuts(_balanced_corpus(), Path("known-good.yaml")) == []

    def test_every_feature_scores_exactly_chance_pooled_and_matched(self) -> None:
        corpus = _balanced_corpus()
        for check in battery_report(corpus):
            assert check.auc == pytest.approx(0.5), check.feature
            assert check.matched == pytest.approx(0.5), check.feature

    def test_no_feature_is_inert(self) -> None:
        """A pass built by pinning every feature would be the defect this
        battery exists to avoid, wearing a green tick."""
        corpus = _balanced_corpus()
        assert inert_features(battery_report(corpus)) == ()

    def test_an_empty_set_also_raises_nothing(self) -> None:
        empty = TriggerSet(skill="tailoring", cases=())
        assert check_shortcuts(empty, Path("empty.yaml")) == []


# --------------------------------------------------------------------------- #
# The known-bad case: the real corpus, on disk, right now.
# --------------------------------------------------------------------------- #


class TestTheBatteryCatchesTheRealCorpusRegisterSplit:
    def test_the_battery_flags_the_real_corpus(self) -> None:
        result = load_deltas(REPO_ROOT)
        findings = check_shortcuts(result.trigger_set, Path("datasets/tailoring/index.yaml"))
        assert findings, "the battery must fire on the known register-split defect"

    def test_the_finding_is_keyed_on_the_whole_leaking_set(self) -> None:
        """The key a baseline entry has to name -- one entry, four features,
        sorted and comma-joined, mirroring how ``corpus._check_leaks`` keys a
        derived trigger-corpus view rather than the gated one."""
        result = load_deltas(REPO_ROOT)
        findings = check_shortcuts(result.trigger_set, Path("datasets/tailoring/index.yaml"))
        assert [finding.key for finding in findings] == [
            "leak:delta:delta_word_count,has_date,numeral_count,penalty_lexicon_gap"
        ]

    def test_penalty_lexicon_gap_perfectly_separates_the_real_arms(self) -> None:
        """The specific feature the register split predicts: governing deltas
        lean on penalty vocabulary, matched deltas lean on procedural
        vocabulary, on all three triplets authored so far."""
        result = load_deltas(REPO_ROOT)
        checks = battery_report(result.trigger_set)
        penalty = next(c for c in checks if c.feature == "penalty_lexicon_gap")
        assert penalty.auc == pytest.approx(1.0)
        assert penalty.leaks

    def test_features_used_are_the_ones_the_brief_asked_for(self) -> None:
        assert set(FEATURES) == {
            "delta_char_count",
            "delta_word_count",
            "numeral_count",
            "has_date",
            "penalty_lexicon_gap",
        }


# --------------------------------------------------------------------------- #
# The paired (matched) statistic, exercised on its own: a habit that never
# separates the pooled deltas (equal lengths on each side, so the *pooled*
# AUC alone would not have to leak) but always puts governing on the same
# side of its own matched partner.
# --------------------------------------------------------------------------- #


def _paired_habit_corpus(triplets: int) -> TriggerSet:
    """``triplets`` triples where governing is always longer than its own match."""
    cases: list[TriggerCase] = []
    for index in range(triplets):
        cases.append(
            TriggerCase(
                id=f"p{index}-governing",
                turn="x" * 50,
                should_fire=True,
                why="fixture",
                triple=f"p{index}",
            )
        )
        cases.append(
            TriggerCase(
                id=f"p{index}-matched",
                turn="y" * 10,
                should_fire=False,
                why="fixture",
                triple=f"p{index}",
            )
        )
    return TriggerSet(skill="tailoring", cases=tuple(cases))


class TestTheMatchedStatisticCatchesAPairedHabit:
    def test_ten_triplets_of_a_deterministic_habit_clear_the_matched_z_threshold(self) -> None:
        checks = battery_report(_paired_habit_corpus(10))
        length = next(c for c in checks if c.feature == "delta_char_count")
        assert length.matched == pytest.approx(1.0)
        assert length.matched_leaks

    def test_check_shortcuts_reports_the_paired_habit(self) -> None:
        findings = check_shortcuts(_paired_habit_corpus(10), Path("paired.yaml"))
        assert any("null standard errors" in finding.message for finding in findings)
        assert any(finding.key == "matched:delta:delta_char_count" for finding in findings)


# --------------------------------------------------------------------------- #
# Why ``check_shortcuts`` does not gate on ``Check.cancels``: with exactly one
# governing delta and one matched delta per triplet, the excess-dispersion
# statistic that catches a habit which cancels in the mean is mathematically
# pinned at 0.0. This is the claim ``check_shortcuts``'s docstring makes and
# defers to this test rather than to prose alone.
# --------------------------------------------------------------------------- #


class TestDispersionIsStructurallyInert:
    @pytest.mark.parametrize(
        "corpus",
        [
            pytest.param(_balanced_corpus(), id="balanced"),
            pytest.param(_paired_habit_corpus(10), id="paired-habit"),
        ],
    )
    def test_dispersion_z_is_exactly_zero(self, corpus: TriggerSet) -> None:
        for check in battery_report(corpus):
            assert check.dispersion_z == pytest.approx(0.0), check.feature

    def test_the_real_corpus_also_shows_zero_dispersion(self) -> None:
        result = load_deltas(REPO_ROOT)
        for check in battery_report(result.trigger_set):
            assert check.dispersion_z == pytest.approx(0.0), check.feature

    def test_no_issue_ever_mentions_cancelling(self) -> None:
        """``check_shortcuts`` has no code path that can emit this wording --
        confirmed here rather than merely asserted in the docstring."""
        for corpus in (_balanced_corpus(), _paired_habit_corpus(10)):
            findings = check_shortcuts(corpus, Path("x.yaml"))
            assert not any("cancel" in finding.message for finding in findings)


# --------------------------------------------------------------------------- #
# The baseline: it may defer the exact four-feature finding the real corpus
# produces today, and nothing wider. Same treatment as
# ``test_corpus_battery.py::TestTheBaselineIsNarrowRatherThanBlanket`` and
# ``TestTheShippedBaseline`` -- a baseline is a falsifier with the sign
# flipped, so the thing worth demonstrating is not that it defers the known
# finding (that is what it was written to do) but that a *wider* one still
# turns the build red.
# --------------------------------------------------------------------------- #


def _five_feature_leak_corpus() -> TriggerSet:
    """Three triplets where the governing delta leaks on every feature the
    battery has: longer in words and characters, carrying a date, carrying
    several numerals, and leaning on penalty vocabulary while the matched
    delta leans on procedural vocabulary. Built to leak on all five columns
    of :data:`FEATURES` at once, which the real three-triplet corpus (four
    of five -- ``delta_char_count`` alone stays inside the band) does not.
    """
    cases: list[TriggerCase] = []
    for index in range(3):
        cases.append(
            TriggerCase(
                id=f"f{index}-governing",
                turn=(
                    f"On 2025-0{index + 1}-01 you forfeit access after missing "
                    "3 payments of $500 each under this clause requirement."
                ),
                should_fire=True,
                why="fixture",
                triple=f"f{index}",
            )
        )
        cases.append(
            TriggerCase(
                id=f"f{index}-matched",
                turn="Fees apply.",
                should_fire=False,
                why="fixture",
                triple=f"f{index}",
            )
        )
    return TriggerSet(skill="tailoring", cases=tuple(cases))


class TestAFifthLeakingFeatureIsNotDeferredByTheShippedBaseline:
    """The load-bearing test the task asks for: identity is the whole leaking
    set, not any one feature in it, so a corpus leaking on five features is a
    *different* finding from the shipped four-feature one and the baseline
    must not cover it. Run against the real
    ``datasets/tailoring/corpus-baseline.txt`` on disk rather than a
    hand-built baseline, so an edit to that file is exactly what this test
    protects.
    """

    def test_the_fixture_leaks_on_all_five_features(self) -> None:
        findings = check_shortcuts(_five_feature_leak_corpus(), Path("x.yaml"))
        leak = next(f for f in findings if f.key.startswith("leak:delta:"))
        assert leak.key == (
            "leak:delta:delta_char_count,delta_word_count,has_date,numeral_count,"
            "penalty_lexicon_gap"
        )

    def test_the_shipped_baseline_does_not_defer_it(self) -> None:
        findings = [
            (CORPUS_SCOPE, finding)
            for finding in check_shortcuts(_five_feature_leak_corpus(), Path("x.yaml"))
        ]
        baseline = load_tailoring_baseline(REPO_ROOT)
        issues, deferred = apply_corpus_baseline(
            findings, baseline, baseline_path=TAILORING_BASELINE_PATH
        )
        assert any("5 feature(s)" in issue for issue in issues)
        assert not any("5 feature(s)" in message for message in deferred)

    def test_a_baseline_naming_the_five_feature_key_would_defer_it(self) -> None:
        """The contrast case: the mechanism above is the key not matching,
        not some other reason the finding always fails."""
        findings = [
            (CORPUS_SCOPE, finding)
            for finding in check_shortcuts(_five_feature_leak_corpus(), Path("x.yaml"))
        ]
        wide_baseline = {
            f"{CORPUS_SCOPE}|leak:delta:delta_char_count,delta_word_count,has_date,"
            "numeral_count,penalty_lexicon_gap"
        }
        issues, deferred = apply_corpus_baseline(
            findings, wide_baseline, baseline_path=TAILORING_BASELINE_PATH
        )
        assert issues == []
        assert any("5 feature(s)" in message for message in deferred)

    def test_dropping_one_feature_from_the_shipped_finding_is_also_not_deferred(self) -> None:
        """The other direction of may-only-shrink: an *improved* corpus (three
        leaking features instead of four) produces a different key too, and
        the stale four-feature baseline entry both fails to cover the new
        finding and is reported as no longer matching anything current."""
        narrower = {
            CORPUS_SCOPE: Finding(
                "leak:delta:has_date,numeral_count,penalty_lexicon_gap",
                "x.yaml: 3 feature(s) leak",
            )
        }
        findings = list(narrower.items())
        baseline = load_tailoring_baseline(REPO_ROOT)
        issues, _ = apply_corpus_baseline(findings, baseline, baseline_path=TAILORING_BASELINE_PATH)
        assert any("3 feature(s) leak" in issue for issue in issues)
        assert any(
            "is baselined but matches no current finding" in issue and "Delete the line" in issue
            for issue in issues
        )


class TestTheShippedTailoringBaseline:
    """The real file against the real corpus."""

    def test_it_defers_exactly_the_known_finding_and_nothing_else(self) -> None:
        result = load_deltas(REPO_ROOT)
        findings = [
            (CORPUS_SCOPE, finding)
            for finding in check_shortcuts(
                result.trigger_set, Path("datasets/tailoring/index.yaml")
            )
        ]
        baseline = load_tailoring_baseline(REPO_ROOT)
        issues, deferred = apply_corpus_baseline(
            findings, baseline, baseline_path=TAILORING_BASELINE_PATH
        )
        assert issues == []
        assert len(deferred) == 1
        assert "delta_word_count 0.611" in deferred[0]
        assert "penalty_lexicon_gap 1.000" in deferred[0]

    def test_every_line_in_the_file_names_the_one_real_corpus(self) -> None:
        """A baseline entry for a corpus that does not exist would never go
        stale, which is exactly how one goes unnoticed."""
        baseline = load_tailoring_baseline(REPO_ROOT)
        assert {entry.split("|", 1)[0] for entry in baseline} == {CORPUS_SCOPE}

    def test_a_baseline_entry_that_no_longer_matches_fails(self) -> None:
        stale = load_tailoring_baseline(REPO_ROOT) | {f"{CORPUS_SCOPE}|leak:delta:delta_word_count"}
        result = load_deltas(REPO_ROOT)
        findings = [
            (CORPUS_SCOPE, finding)
            for finding in check_shortcuts(
                result.trigger_set, Path("datasets/tailoring/index.yaml")
            )
        ]
        issues, _ = apply_corpus_baseline(findings, stale, baseline_path=TAILORING_BASELINE_PATH)
        assert any(
            "is baselined but matches no current finding" in issue and "Delete the line" in issue
            for issue in issues
        )
