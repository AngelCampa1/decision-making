"""Tests for trigger-quality measurement."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from decision_evals.generators.loader import REPO_ROOT
from decision_evals.triggers import (
    TriggerSetError,
    evaluate,
    load_trigger_set,
)

SET_PATH = REPO_ROOT / "datasets" / "triggers" / "evidence-ledger.yaml"


# -- the shipped set --------------------------------------------------------


def test_the_shipped_trigger_set_loads() -> None:
    trigger_set = load_trigger_set(SET_PATH)
    assert trigger_set.skill == "evidence-ledger"
    assert len(trigger_set.positives) >= 10
    assert len(trigger_set.negatives) >= 50


def test_every_case_records_why_it_belongs() -> None:
    """A negative without a stated reason is an assertion, not a test case."""
    for case in load_trigger_set(SET_PATH).cases:
        assert case.why.strip()


#: Surface features that make a negative *tempting* — the phrasings that read
#: like a decision or a supplied context pile without being one. Deliberately
#: broad: an earlier, narrower list scored the shipped set at 0.34 and would
#: have failed a set whose negatives are genuinely hard, because it missed lures
#: like "rank", "evidence" and "recommend". That was a bug in the measurement,
#: not a problem with the data.
LURES = (
    "should",
    "here's",
    "pasted",
    "attach",
    "below",
    "given",
    "which",
    "context",
    "rank",
    "evidence",
    "decide",
    "decision",
    "recommend",
    "prioriti",
    "option",
    "do we",
    "can i",
    " best",
    "ideas",
    "review",
    "why is",
    "how many",
    "how likely",
    "full ",
    "whole ",
    "these ",
)


def test_the_negatives_are_hard_rather_than_obvious() -> None:
    """Precision against easy negatives is free and means nothing.

    Crude by necessity — "tempting" is not something a string match settles. The
    check is only that the set has not drifted into unrelated chit-chat, which
    would inflate precision without testing anything. A handful of genuinely
    easy negatives (acknowledgements, meta-questions) are deliberate: a
    description that fires on "thanks, that worked" is also worth catching.
    """
    negatives = load_trigger_set(SET_PATH).negatives
    tempting = [c for c in negatives if any(lure in c.turn.casefold() for lure in LURES)]
    assert len(tempting) / len(negatives) >= 0.5


# -- loading ----------------------------------------------------------------


def _write(path: Path, payload: object) -> Path:
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def test_a_missing_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(TriggerSetError):
        load_trigger_set(tmp_path / "absent.yaml")


def test_a_document_without_a_skill_key_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(TriggerSetError, match="`skill` key"):
        load_trigger_set(_write(tmp_path / "s.yaml", {"positive": []}))


def test_malformed_yaml_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("skill: [unclosed\n", encoding="utf-8")
    with pytest.raises(TriggerSetError):
        load_trigger_set(path)


def test_a_malformed_case_is_rejected(tmp_path: Path) -> None:
    payload = {"skill": "x", "positive": [{"id": "p1", "turn": "t"}]}
    with pytest.raises(TriggerSetError, match="malformed positive case"):
        load_trigger_set(_write(tmp_path / "s.yaml", payload))


def test_an_empty_set_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(TriggerSetError, match="no cases"):
        load_trigger_set(_write(tmp_path / "s.yaml", {"skill": "x"}))


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    payload = {
        "skill": "x",
        "positive": [{"id": "a", "turn": "t", "why": "w"}],
        "negative": [{"id": "a", "turn": "u", "why": "w"}],
    }
    with pytest.raises(TriggerSetError, match="duplicate case ids"):
        load_trigger_set(_write(tmp_path / "s.yaml", payload))


# -- scoring ----------------------------------------------------------------


def test_a_perfect_trigger_scores_one_on_both() -> None:
    trigger_set = load_trigger_set(SET_PATH)
    positives = {case.turn for case in trigger_set.positives}
    report = evaluate(trigger_set, lambda turn: turn in positives)
    assert report.precision == 1.0
    assert report.recall == 1.0
    assert report.false_positive_rate == 0.0
    assert report.missed == ()


def test_a_skill_that_always_fires_has_perfect_recall_and_poor_precision() -> None:
    """The failure the daily-use argument is about.

    Recall alone would score this a triumph. It interrupts every ordinary turn.
    """
    trigger_set = load_trigger_set(SET_PATH)
    report = evaluate(trigger_set, lambda _: True)
    assert report.recall == 1.0
    assert report.precision < 0.25
    assert report.false_positive_rate == 1.0


def test_a_skill_that_never_fires_scores_zero_on_both() -> None:
    """cc-thinking-skills' `disable-model-invocation: true`, in effect."""
    report = evaluate(load_trigger_set(SET_PATH), lambda _: False)
    assert report.precision == 0.0
    assert report.recall == 0.0
    assert report.false_positive_rate == 0.0
    assert len(report.missed) == len(load_trigger_set(SET_PATH).positives)


def test_the_report_names_what_fired_and_what_was_missed(tmp_path: Path) -> None:
    """Actionable output: a low recall should point at specific turns."""
    payload = {
        "skill": "x",
        "positive": [
            {"id": "p1", "turn": "fires", "why": "w"},
            {"id": "p2", "turn": "missed", "why": "w"},
        ],
        "negative": [{"id": "n1", "turn": "fires", "why": "w"}],
    }
    trigger_set = load_trigger_set(_write(tmp_path / "s.yaml", payload))
    report = evaluate(trigger_set, lambda turn: turn == "fires")
    assert report.fired_on == ("p1", "n1")
    assert report.missed == ("p2",)
    assert (report.true_positives, report.false_positives) == (1, 1)
    assert (report.true_negatives, report.false_negatives) == (0, 1)
    assert report.precision == 0.5


def test_an_all_negative_set_has_defined_rates(tmp_path: Path) -> None:
    payload = {"skill": "x", "negative": [{"id": "n1", "turn": "t", "why": "w"}]}
    report = evaluate(load_trigger_set(_write(tmp_path / "s.yaml", payload)), lambda _: False)
    assert report.precision == 0.0
    assert report.recall == 0.0


def test_an_all_positive_set_has_a_defined_false_positive_rate(tmp_path: Path) -> None:
    payload = {"skill": "x", "positive": [{"id": "p1", "turn": "t", "why": "w"}]}
    report = evaluate(load_trigger_set(_write(tmp_path / "s.yaml", payload)), lambda _: True)
    assert report.false_positive_rate == 0.0
