"""Tests for the casefile probe's scorer.

This module did not exist, which is uncomfortable given what it scores: the
admissibility conjunction is the probe's primary metric and the number three
notebook entries are written around. It was reviewed by reading twelve traces
by hand, and reading traces is how the defect it carries was eventually found
rather than how it was prevented.

The defect: admissibility required ``pivot_ok``, so a response was scored
inadmissible when it named a determinative unknown that was not the one in the
answer key. Five of the six scored probe failures were that conjunct alone, and
on probe-09 the model named the exact fact s.46(3) turns on -- a better pivot
than the one written down.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _load() -> ModuleType:
    """Import ``scripts/probe_casefile.py``, which is not part of the package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_casefile.py"
    spec = importlib.util.spec_from_file_location("probe_casefile", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_casefile"] = module
    spec.loader.exec_module(module)
    return module


probe = _load()


def _casefile(
    *,
    required: set[str] = frozenset({"A1"}),  # type: ignore[assignment]
    prohibited: set[str] = frozenset({"A7"}),  # type: ignore[assignment]
    unjustified: set[str] = frozenset(),  # type: ignore[assignment]
    trap: set[str] = frozenset(),  # type: ignore[assignment]
    governing: set[str] = frozenset({"C1"}),  # type: ignore[assignment]
    pivot_present: bool = False,
) -> Any:
    """A minimal casefile with the action and condition tables the scorer reads."""
    actions: list[dict[str, Any]] = []
    for action_id in sorted(required):
        actions.append({"id": action_id, "status": "required"})
    for action_id in sorted(prohibited | unjustified | trap):
        entry: dict[str, Any] = {"id": action_id, "status": "prohibited"}
        if action_id in unjustified:
            entry["failure_kind"] = "unjustified"
            entry["status"] = "permitted" if action_id not in prohibited else "prohibited"
        if action_id in trap:
            entry["failure_kind"] = "trap"
        actions.append(entry)

    conditions: list[dict[str, Any]] = [
        {"id": cid, "governs": True, "source": "doc1"} for cid in sorted(governing)
    ]
    conditions.append({"id": "C99", "governs": False, "source": "doc1"})

    return probe.Casefile(
        raw={
            "case_id": "probe-test",
            "trap_order": 1,
            "trap_kind": "foreclosure",
            "documents": [{"id": "doc1", "kind": "authority", "title": "t", "body": "b"}],
            "question": "What should the firm do?",
            "exposure_question": "What is the expected exposure?",
            "actions": actions,
            "conditions": conditions,
            "exposure": {"band": "moderate", "first_order_wrong_answer": "low"},
            "pivot": {"present": pivot_present, "accepts": ["the signed waiver"]},
        }
    )


def _parsed(
    *,
    actions: set[str] = frozenset({"A1"}),  # type: ignore[assignment]
    missing: str = "NONE",
    conditions: set[str] = frozenset({"C1"}),  # type: ignore[assignment]
    exposure: str | None = "moderate",
) -> Any:
    return probe.Parsed(
        blocks_found=sorted(probe._BLOCK_NAMES),
        condition_votes=dict.fromkeys(sorted(conditions), True),
        exposure=exposure,
        missing=missing,
        actions=sorted(actions),
    )


# -- admissibility ----------------------------------------------------------


def test_naming_a_real_unknown_no_longer_costs_admissibility() -> None:
    """probe-09: the model named the fact s.46(3) turns on and was scored zero."""
    scored = probe.score(
        _casefile(),
        _parsed(missing="Evidence of a compliant written cure notice."),
    )
    assert scored.admissible


def test_a_missing_required_action_costs_admissibility() -> None:
    assert not probe.score(_casefile(required={"A1", "A2"}), _parsed(actions={"A1"})).admissible


def test_a_prohibited_action_costs_admissibility() -> None:
    assert not probe.score(_casefile(), _parsed(actions={"A1", "A7"})).admissible


def test_an_unjustified_action_now_costs_admissibility() -> None:
    """An action licensed only by a non-governing condition is a real failure.

    It was diagnostic only, so a response could take it and still be admissible
    while the metric claimed to be measuring whether the answer was licensed.
    """
    case = _casefile(prohibited=frozenset(), unjustified={"A4"})
    assert not probe.score(case, _parsed(actions={"A1", "A4"})).admissible


def test_a_clean_answer_is_admissible() -> None:
    assert probe.score(_casefile(), _parsed()).admissible


# -- pivot, demoted to a secondary ------------------------------------------


def test_pivot_recall_is_still_recorded_when_the_case_has_one() -> None:
    case = _casefile(pivot_present=True)
    scored = probe.score(case, _parsed(missing="We do not have the signed waiver."))
    assert scored.pivot_ok
    assert scored.named_an_unknown


def test_naming_a_different_unknown_is_recorded_without_costing_the_primary() -> None:
    """The two-by-two the probe exists to fill in: named, but not the key's pivot."""
    case = _casefile(pivot_present=True)
    scored = probe.score(case, _parsed(missing="Evidence of a compliant cure notice."))
    assert not scored.pivot_ok
    assert scored.named_an_unknown
    assert scored.admissible


def test_declining_to_name_an_unknown_is_recorded_as_such() -> None:
    scored = probe.score(_casefile(), _parsed(missing="NONE"))
    assert not scored.named_an_unknown
    assert scored.admissible


def test_an_empty_missing_block_is_not_a_named_unknown() -> None:
    """A blank block is a parse artefact, not a considered 'nothing is missing'."""
    assert not probe.score(_casefile(), _parsed(missing="   ")).named_an_unknown


# -- the graded outcome -----------------------------------------------------


def test_the_graded_score_separates_two_admissible_answers() -> None:
    """Both are admissible. One found every governing condition, one found half.

    A binary primary calls them identical, and with 0/12 prohibited actions and
    0/12 traps taken in the probe, that is nearly all of the variance there was.
    """
    case = _casefile(governing={"C1", "C2", "C3", "C4"})
    thorough = probe.score(case, _parsed(conditions={"C1", "C2", "C3", "C4"}))
    thin = probe.score(case, _parsed(conditions={"C1", "C2"}))

    assert thorough.admissible
    assert thin.admissible
    assert thorough.graded > thin.graded


def test_a_perfect_answer_grades_one() -> None:
    assert probe.score(_casefile(), _parsed()).graded == pytest.approx(1.0)


def test_the_graded_score_is_bounded_below() -> None:
    empty = probe.score(_casefile(), _parsed(actions=frozenset(), conditions=frozenset()))
    assert 0.0 <= empty.graded <= 1.0


def test_a_case_with_nothing_to_get_wrong_is_refused_at_load() -> None:
    """The degenerate denominators in ``graded`` are guarded, but the real
    defence is upstream: a casefile with no required actions and no governing
    conditions never reaches the scorer, because admissibility on it would be
    trivially true and the graded outcome would be measuring nothing."""
    case = _casefile(required=frozenset(), prohibited=frozenset(), governing=frozenset())
    problems = probe.validate([case])

    assert any("no required actions" in problem for problem in problems)
    assert any("no governing conditions" in problem for problem in problems)


def test_a_partial_answer_grades_between_the_bounds() -> None:
    case = _casefile(required={"A1", "A2"}, governing={"C1", "C2"})
    scored = probe.score(case, _parsed(actions={"A1"}, conditions={"C1"}))

    assert not scored.admissible
    assert 0.0 < scored.graded < 1.0


# -- diagnostics that must not regress --------------------------------------


def test_the_trap_is_still_reported_separately() -> None:
    case = _casefile(prohibited={"A7"}, trap={"A7"})
    assert probe.score(case, _parsed(actions={"A1", "A7"})).trap_hit


def test_exposure_scoring_is_unchanged() -> None:
    scored = probe.score(_casefile(), _parsed(exposure="moderate"))
    assert scored.exposure_ok
    assert not scored.exposure_first_order


def test_the_first_order_wrong_answer_is_flagged_when_given() -> None:
    scored = probe.score(_casefile(), _parsed(exposure="low"))
    assert not scored.exposure_ok
    assert scored.exposure_first_order


def test_condition_precision_and_recall_are_reported() -> None:
    case = _casefile(governing={"C1", "C2"})
    scored = probe.score(case, _parsed(conditions={"C1", "C99"}))
    assert scored.condition_precision == pytest.approx(0.5)
    assert scored.condition_recall == pytest.approx(0.5)
