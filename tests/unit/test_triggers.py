"""Tests for trigger-quality measurement."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from decision_evals.generators.loader import REPO_ROOT
from decision_evals.triggers import (
    PROCEDURES,
    TriggerSetError,
    _check_routes,
    check_trigger_sets,
    decision,
    evaluate,
    evaluate_routing,
    load_trigger_set,
    routing_is_by_name,
)

#: The set for the skill that ships. It was `evidence-ledger.yaml` until
#: 2026-08-12, which named a skill retired when the four procedures were
#: consolidated behind one router -- and this constant is why the mismatch
#: survived: the test pinned a path rather than asking which skills exist.
#: `check_trigger_sets` now answers that question, and is asserted below.
SET_PATH = REPO_ROOT / "datasets" / "triggers" / "decision-making.yaml"


# -- the shipped set --------------------------------------------------------


def test_the_shipped_trigger_set_loads() -> None:
    trigger_set = load_trigger_set(SET_PATH)
    assert trigger_set.skill == "decision-making"
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


# -- routing, and the correspondence check ----------------------------------


class TestRouting:
    def test_it_scores_only_the_cases_that_declare_a_route(self) -> None:
        trigger_set = load_trigger_set(SET_PATH)
        report = evaluate_routing(trigger_set, lambda _: "ledger")
        labelled = [c for c in trigger_set.positives if c.route]
        assert report.n_scored == len(labelled)
        assert report.unlabelled == len(trigger_set.positives) - len(labelled)

    def test_a_perfect_router_scores_one(self) -> None:
        trigger_set = load_trigger_set(SET_PATH)
        by_turn = {c.turn: c.route for c in trigger_set.positives}
        report = evaluate_routing(trigger_set, lambda turn: by_turn[turn])
        assert report.accuracy == 1.0
        assert report.confusions == ()

    def test_confusions_name_the_case_the_want_and_the_got(self) -> None:
        trigger_set = load_trigger_set(SET_PATH)
        report = evaluate_routing(trigger_set, lambda _: None)
        assert report.accuracy == 0.0
        case_id, wanted, got = report.confusions[0]
        assert got == "(none)"
        assert wanted in {"ledger", "fit", "cascade", "timing"}
        assert case_id

    def test_no_labelled_cases_divides_by_nothing(self, tmp_path: Path) -> None:
        path = tmp_path / "s.yaml"
        path.write_text(
            "skill: s\npositive:\n  - {id: p1, turn: t, why: w}\n"
            "negative:\n  - {id: n1, turn: t2, why: w}\n",
            encoding="utf-8",
        )
        report = evaluate_routing(load_trigger_set(path), lambda _: "x")
        assert report.n_scored == 0
        assert report.accuracy == 0.0

    def test_a_negative_may_not_declare_a_route(self, tmp_path: Path) -> None:
        """A turn the skill should not fire on has no procedure to route to."""
        path = tmp_path / "s.yaml"
        path.write_text(
            "skill: s\nnegative:\n  - {id: n1, turn: t, why: w, route: ledger}\n",
            encoding="utf-8",
        )
        with pytest.raises(TriggerSetError, match="has no procedure to route to"):
            load_trigger_set(path)


class TestCorrespondence:
    def test_the_repository_satisfies_it(self) -> None:
        """The check that would have caught the orphan, run on the real tree."""
        assert check_trigger_sets(REPO_ROOT) == []

    def test_a_skill_without_a_trigger_set_is_reported(self, tmp_path: Path) -> None:
        (tmp_path / "skills" / "lonely").mkdir(parents=True)
        (tmp_path / "skills" / "lonely" / "SKILL.md").write_text("x", encoding="utf-8")
        (tmp_path / "datasets" / "triggers").mkdir(parents=True)
        assert any("has no trigger set" in i for i in check_trigger_sets(tmp_path))

    def test_a_trigger_set_for_a_retired_skill_is_reported(self, tmp_path: Path) -> None:
        """The actual defect: evidence-ledger.yaml outlived its skill by a day."""
        (tmp_path / "skills").mkdir(parents=True)
        (tmp_path / "datasets" / "triggers").mkdir(parents=True)
        (tmp_path / "datasets" / "triggers" / "ghost.yaml").write_text(
            "skill: ghost\npositive:\n  - {id: p1, turn: t, why: w}\n", encoding="utf-8"
        )
        assert any("not in skills/" in i for i in check_trigger_sets(tmp_path))

    def test_a_set_filed_under_the_wrong_name_is_reported(self, tmp_path: Path) -> None:
        (tmp_path / "skills" / "real").mkdir(parents=True)
        (tmp_path / "skills" / "real" / "SKILL.md").write_text("x", encoding="utf-8")
        (tmp_path / "datasets" / "triggers").mkdir(parents=True)
        (tmp_path / "datasets" / "triggers" / "real.yaml").write_text(
            "skill: other\npositive:\n  - {id: p1, turn: t, why: w}\n"
            "negative:\n  - {id: n1, turn: t2, why: w}\n",
            encoding="utf-8",
        )
        assert any("is filed as" in i for i in check_trigger_sets(tmp_path))

    def test_a_set_with_no_negatives_is_reported(self, tmp_path: Path) -> None:
        """Precision decides whether a skill is worth having installed."""
        (tmp_path / "skills" / "real").mkdir(parents=True)
        (tmp_path / "skills" / "real" / "SKILL.md").write_text("x", encoding="utf-8")
        (tmp_path / "datasets" / "triggers").mkdir(parents=True)
        (tmp_path / "datasets" / "triggers" / "real.yaml").write_text(
            "skill: real\npositive:\n  - {id: p1, turn: t, why: w}\n", encoding="utf-8"
        )
        assert any("no negative cases" in i for i in check_trigger_sets(tmp_path))

    def test_a_malformed_set_is_reported_rather_than_raising(self, tmp_path: Path) -> None:
        (tmp_path / "skills" / "real").mkdir(parents=True)
        (tmp_path / "skills" / "real" / "SKILL.md").write_text("x", encoding="utf-8")
        (tmp_path / "datasets" / "triggers").mkdir(parents=True)
        (tmp_path / "datasets" / "triggers" / "real.yaml").write_text("[]", encoding="utf-8")
        assert any("expected a mapping" in i for i in check_trigger_sets(tmp_path))


class TestRouteLabelsMatchTheRouterTable:
    """A label aimed at a procedure that does not exist scores as a model failure.

    Added after M4 and M5 made the router table load-bearing in two places at
    once: the arms are built from it and the labels point at it.
    """

    SKILL = """---
name: demo
description: >-
  Use when deciding. Routes to one of four procedures. Do not use for lookups.
---

| What is hard | Read | What it produces |
|---|---|---|
| A pile arrived | `ledger.md` | a list |
| It may not fit | `fit.md` | the answer |
"""

    def _skill(self, tmp_path: Path) -> Path:
        directory = tmp_path / "skills" / "demo"
        directory.mkdir(parents=True)
        path = directory / "SKILL.md"
        path.write_text(self.SKILL, encoding="utf-8")
        return path

    def _triggers(self, tmp_path: Path, route: str) -> Path:
        directory = tmp_path / "datasets" / "triggers"
        directory.mkdir(parents=True)
        path = directory / "demo.yaml"
        path.write_text(
            "skill: demo\n"
            "positive:\n"
            f"  - id: p01\n    turn: Should I take it?\n    why: a decision\n    route: {route}\n"
            "negative:\n"
            "  - id: n01\n    turn: What is the capital of France?\n    why: a lookup\n",
            encoding="utf-8",
        )
        return path

    def test_a_route_in_the_table_is_accepted(self, tmp_path: Path) -> None:
        skill = self._skill(tmp_path)
        triggers = self._triggers(tmp_path, "ledger")
        assert _check_routes(load_trigger_set(triggers), skill, triggers) == []

    def test_a_route_that_is_not_a_procedure_is_reported(self, tmp_path: Path) -> None:
        skill = self._skill(tmp_path)
        triggers = self._triggers(tmp_path, "cascade")
        issues = _check_routes(load_trigger_set(triggers), skill, triggers)
        assert len(issues) == 1
        assert "'cascade'" in issues[0]
        assert "fit, ledger" in issues[0]

    def test_a_skill_with_no_router_table_is_not_an_error(self, tmp_path: Path) -> None:
        skill = self._skill(tmp_path)
        skill.write_text(self.SKILL.split("| What is hard")[0], encoding="utf-8")
        triggers = self._triggers(tmp_path, "anything")
        assert _check_routes(load_trigger_set(triggers), skill, triggers) == []

    def test_a_missing_skill_file_is_not_an_error_here(self, tmp_path: Path) -> None:
        """That is ``check_trigger_sets``' job, and it reports it separately."""
        triggers = self._triggers(tmp_path, "ledger")
        absent = tmp_path / "skills" / "gone" / "SKILL.md"
        assert _check_routes(load_trigger_set(triggers), absent, triggers) == []

    def test_the_shipped_trigger_set_passes(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        triggers = repo / "datasets" / "triggers" / "decision-making.yaml"
        skill = repo / "skills" / "decision-making" / "SKILL.md"
        assert _check_routes(load_trigger_set(triggers), skill, triggers) == []


class TestVerdictParsingHonoursTheOfferedNames:
    """The whitelist that voided a 365-call run on 2026-08-12.

    ``decision`` filtered the named tool against the four procedure names. An
    M5 arm at n=2 offers ``ledger-fit`` and ``cascade-timing``, so every answer
    was discarded: the run finished clean, firing was unaffected, and routing
    read 0.000 because nothing had been recorded rather than because the model
    had failed.
    """

    def test_a_procedure_name_is_kept_by_default(self) -> None:
        assert decision('{"fire": true, "procedure": "ledger"}') == (True, "ledger", None)

    def test_a_merged_entry_name_is_kept_when_offered(self) -> None:
        text = '{"fire": true, "tool": "ledger-fit"}'
        assert decision(text, ("ledger-fit", "cascade-timing")) == (True, "ledger-fit", None)

    def test_a_merged_entry_name_is_dropped_when_not_offered(self) -> None:
        """The old behaviour, kept deliberately: an unoffered name is not a route."""
        assert decision('{"fire": true, "tool": "ledger-fit"}') == (True, None, None)

    def test_a_name_outside_the_offered_set_is_dropped(self) -> None:
        assert decision('{"fire": true, "tool": "premortem"}', ("ledger-fit",)) == (
            True,
            None,
            None,
        )

    def test_firing_survives_a_dropped_name(self) -> None:
        """Why the void run's firing numbers were still usable."""
        fired, procedure, _ = decision('{"fire": false, "tool": "ledger-fit"}')
        assert fired is False
        assert procedure is None


class TestRoutingIsByName:
    """The same defect one layer out, found scoring M5 on 2026-08-12.

    The two-entry run finished clean and its report read ``routing accuracy
    0.000`` over 14 labelled items. Nothing had failed: the arm offers
    ``ledger-fit`` and ``cascade-timing``, the labels say ``ledger`` and
    ``cascade``, and no answer the model could give would have matched. The
    parser bug discarded the offered names on the way in; this one graded them
    against names never offered on the way out. Both read as a total failure.
    """

    def test_the_shipped_procedure_names_are_gradeable_by_name(self) -> None:
        assert routing_is_by_name(PROCEDURES)

    def test_a_four_entry_arm_is_gradeable_by_name(self) -> None:
        """n=4 partitions one procedure per entry, so the names coincide."""
        assert routing_is_by_name(("ledger", "fit", "cascade", "timing"))

    def test_a_two_entry_arm_is_not(self) -> None:
        assert not routing_is_by_name(("ledger-fit", "cascade-timing"))

    def test_one_unmatchable_name_is_enough(self) -> None:
        """A partition need not be uniform; any merged entry voids the measure."""
        assert not routing_is_by_name(("ledger", "fit", "cascade-timing"))

    def test_an_empty_offer_is_vacuously_by_name(self) -> None:
        """No entries means no arm to grade; the caller's ``is not None`` gate
        decides, and this must not raise."""
        assert routing_is_by_name(())
