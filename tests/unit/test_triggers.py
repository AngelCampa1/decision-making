"""Tests for trigger-quality measurement."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from decision_evals.generators.loader import REPO_ROOT
from decision_evals.triggers import (
    PROCEDURES,
    TriggerCase,
    TriggerSet,
    TriggerSetError,
    _check_routes,
    _check_separability,
    check_trigger_sets,
    decision,
    evaluate,
    evaluate_routing,
    length_separability,
    load_trigger_set,
    parse_only,
    routing_is_by_name,
    select_cases,
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
        """The check that would have caught the orphan, run on the real tree.

        Green does not mean the corpus is clean. Two findings are deferred by
        ``datasets/triggers/corpus-baseline.txt`` and printed on every run;
        what they are, why they cannot be fixed today and what closes them
        lives in that file and is asserted in ``test_corpus_battery.py``, which
        is the **one** place either question is answered. A second list here
        would be a place a finding could be closed and left open.
        """
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


class TestADraftCorpusIsCheckedWhereItLives:
    """A corpus of band files one directory down was outside every gate.

    ``check_trigger_sets`` globs ``datasets/triggers/*.yaml``. Version 3 is a
    directory of band files, so 120 authored turns and the whole shortcut
    battery sat where no gate could see them while ``de check`` reported green.
    Same shape as ``triggers`` at 100% coverage with no caller, caught this time
    before anything had been published from it.
    """

    @staticmethod
    def _tree(root: Path, *, index: str, band: str) -> None:
        (root / "skills" / "real").mkdir(parents=True)
        (root / "skills" / "real" / "SKILL.md").write_text("x", encoding="utf-8")
        draft = root / "datasets" / "triggers" / "real"
        draft.mkdir(parents=True)
        (root / "datasets" / "triggers" / "real.yaml").write_text(
            "skill: real\npositive:\n  - {id: p1, turn: t, why: w}\n"
            "negative:\n  - {id: n1, turn: t2, why: w}\n",
            encoding="utf-8",
        )
        (draft / "index.yaml").write_text(index, encoding="utf-8")
        (draft / "s.yaml").write_text(band, encoding="utf-8")

    #: One positive, two negatives, all in band `s`, all the same length.
    BAND = """
positive:
  - {id: s1p, triple: s1, band: s, domain: money, stakes: low, ask: explicit,
     turn: do i take the offer or not, why: w}
negative:
  - {id: s1n1, triple: s1, band: s, domain: money, stakes: low, ask: explicit,
     kind: lookup, turn: what does the offer letter mean, why: w}
  - {id: s1n2, triple: s1, band: s, domain: money, stakes: low, ask: explicit,
     kind: compute, turn: add up the offer for me now, why: w}
"""

    def test_a_draft_that_breaks_a_triple_is_reported(self, tmp_path: Path) -> None:
        self._tree(
            tmp_path,
            index="version: 3\nskill: real\nincludes:\n  - s.yaml\n",
            band=self.BAND.replace(
                "  - {id: s1n2, triple: s1, band: s, domain: money, stakes: low, ask: explicit,\n"
                "     kind: compute, turn: add up the offer for me now, why: w}\n",
                "",
            ),
        )
        issues = check_trigger_sets(tmp_path)
        assert any("every triple is one positive" in i for i in issues)

    def test_a_draft_naming_a_skill_that_does_not_exist_is_reported(self, tmp_path: Path) -> None:
        self._tree(
            tmp_path,
            index="version: 3\nskill: ghost\nincludes:\n  - s.yaml\n",
            band=self.BAND,
        )
        assert any("will not ship" in i for i in check_trigger_sets(tmp_path))

    def test_a_malformed_draft_index_is_reported_rather_than_raising(self, tmp_path: Path) -> None:
        self._tree(tmp_path, index="[]", band=self.BAND)
        assert any("expected a mapping" in i for i in check_trigger_sets(tmp_path))

    def test_the_repository_draft_is_reached_and_is_the_whole_corpus(self) -> None:
        """A green gate means nothing unless it read something.

        ``check_trigger_sets(REPO_ROOT) == []`` above is only evidence that the
        draft is sound if the draft was loaded, and the reason this check exists
        at all is that a set nobody loads reports green. So the count is
        asserted here rather than assumed: every band, every item.
        """
        corpus = REPO_ROOT / "datasets" / "triggers" / "decision-making"
        draft = load_trigger_set(corpus / "index.yaml")
        # Pinned on purpose, and it did its job: this literal is what made the
        # 2026-08-18 bump to 4 a reviewed edit rather than a silent one. Unlike
        # the count below, a version is supposed to move only deliberately.
        assert draft.version == 4
        assert {case.band for case in draft.cases} == {"s", "m", "l", "xl"}
        assert len(draft.positives) * 2 == len(draft.negatives)

        # The count is *recomputed from the band files*, not pinned to a literal.
        # A literal here was 120 and the corpus is 261; re-pinning it would have
        # meant a test that passes by being edited every time the corpus grows,
        # which is the same defect as a hand-maintained count in prose. What the
        # check is for is that nothing is *missed* — the original bug globbed
        # `datasets/triggers/*.yaml` and never saw the bands one directory down.
        on_disk = 0
        for band in sorted(corpus.glob("*.yaml")):
            if band.name == "index.yaml":
                continue
            loaded = yaml.safe_load(band.read_text(encoding="utf-8"))
            on_disk += len(loaded["positive"]) + len(loaded["negative"])
        assert on_disk > 0, "no band file was read, so this check proves nothing"
        assert len(draft.cases) == on_disk


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


class TestASecondRouteIsAllowed:
    """The maintainer's 2026-08-13 decision, and the rule attached to it.

    Three of fourteen labelled turns had a second defensible route, and scoring
    it as a fault measured the answer key rather than the model. The rule is
    that a second route needs a written defence and that the whole set is
    reviewed at once -- not only the turns that failed.
    """

    def _set(self, tmp_path: Path, route: object) -> TriggerSet:
        payload = {
            "skill": "x",
            "positive": [{"id": "p1", "turn": "t", "why": "w", "route": route}],
            "negative": [{"id": "n1", "turn": "u", "why": "w"}],
        }
        return load_trigger_set(_write(tmp_path / "s.yaml", payload))

    def test_a_scalar_route_still_loads(self, tmp_path: Path) -> None:
        """The older one-route form is not a migration."""
        case = self._set(tmp_path, "ledger").positives[0]
        assert case.routes == ("ledger",)
        assert case.route == "ledger"

    def test_a_list_loads_as_several_acceptable_routes(self, tmp_path: Path) -> None:
        case = self._set(tmp_path, ["cascade", "timing"]).positives[0]
        assert case.routes == ("cascade", "timing")
        assert case.route == "cascade", "reports print one name; scoring accepts either"

    def test_either_declared_route_scores_correct(self, tmp_path: Path) -> None:
        trigger_set = self._set(tmp_path, ["cascade", "timing"])
        for chosen in ("cascade", "timing"):
            assert evaluate_routing(trigger_set, lambda _, c=chosen: c).accuracy == 1.0

    def test_an_undeclared_route_is_still_wrong(self, tmp_path: Path) -> None:
        report = evaluate_routing(self._set(tmp_path, ["cascade", "timing"]), lambda _: "ledger")
        assert report.accuracy == 0.0
        assert report.confusions == (("p1", "cascade or timing", "ledger"),)

    def test_naming_nothing_is_still_wrong(self, tmp_path: Path) -> None:
        report = evaluate_routing(self._set(tmp_path, ["cascade", "timing"]), lambda _: None)
        assert report.accuracy == 0.0

    def test_an_empty_list_is_refused(self, tmp_path: Path) -> None:
        """`route: []` would read as "no acceptable route", which is not a label."""
        with pytest.raises(TriggerSetError, match="one procedure name"):
            self._set(tmp_path, [])

    def test_a_repeated_route_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(TriggerSetError, match="lists a route twice"):
            self._set(tmp_path, ["timing", "timing"])

    def test_every_second_route_in_the_shipped_set_carries_its_defence(self) -> None:
        """The rule is enforced, not remembered.

        A second route that nobody had to argue for is how an answer key gets
        widened until it stops disagreeing with anything.
        """
        for case in load_trigger_set(SET_PATH).positives:
            if len(case.routes) > 1:
                assert "second acceptable route" in case.why, case.id

    def test_the_shipped_set_still_has_fourteen_labelled_turns(self) -> None:
        """Widening a label must not quietly add or drop one."""
        labelled = [case for case in load_trigger_set(SET_PATH).positives if case.routes]
        assert len(labelled) == 14


class TestLengthSeparability:
    """How much of the set a ruler solves, found 2026-08-13.

    The maintainer observed that real users write paragraphs and nothing in the
    set exceeds 25 words. Checking that turned up a confound rather than only a
    gap: positives run at a median of 18 words and negatives at 8, so a bare
    word-count rule scores 0.890 accuracy with no model involved.
    """

    def _set(self, tmp_path: Path, positives: list[str], negatives: list[str]) -> TriggerSet:
        payload = {
            "skill": "x",
            "positive": [{"id": f"p{i}", "turn": t, "why": "w"} for i, t in enumerate(positives)],
            "negative": [{"id": f"n{i}", "turn": t, "why": "w"} for i, t in enumerate(negatives)],
        }
        return load_trigger_set(_write(tmp_path / "s.yaml", payload))

    def test_identical_lengths_carry_no_signal(self, tmp_path: Path) -> None:
        trigger_set = self._set(tmp_path, ["a b c", "d e f"], ["g h i", "j k l"])
        assert length_separability(trigger_set) == 0.5

    def test_longer_positives_score_above_a_half(self, tmp_path: Path) -> None:
        trigger_set = self._set(tmp_path, ["a b c d e"], ["f"])
        assert length_separability(trigger_set) == 1.0

    def test_longer_negatives_score_below_a_half(self, tmp_path: Path) -> None:
        trigger_set = self._set(tmp_path, ["a"], ["b c d e f"])
        assert length_separability(trigger_set) == 0.0

    def test_a_set_with_one_label_is_uninformative_rather_than_an_error(
        self, tmp_path: Path
    ) -> None:
        payload = {"skill": "x", "positive": [{"id": "p1", "turn": "a b", "why": "w"}]}
        assert length_separability(load_trigger_set(_write(tmp_path / "s.yaml", payload))) == 0.5

    def test_the_shipped_set_is_where_the_notebook_says(self) -> None:
        """0.850, recorded rather than rounded away."""
        assert length_separability(load_trigger_set(SET_PATH)) == pytest.approx(0.850, abs=0.002)

    def test_the_shipped_set_declares_a_ceiling_it_is_under(self) -> None:
        trigger_set = load_trigger_set(SET_PATH)
        assert trigger_set.length_separability_ceiling is not None
        assert length_separability(trigger_set) <= trigger_set.length_separability_ceiling

    def test_the_ceiling_is_a_ratchet_and_only_turns_down(self, tmp_path: Path) -> None:
        """A new turn that widens the length gap must fail the check."""
        payload = {
            "skill": "decision-making",
            "length_separability_ceiling": 0.60,
            "positive": [{"id": "p1", "turn": "a b c d e f g h", "why": "w"}],
            "negative": [{"id": "n1", "turn": "z", "why": "w"}],
        }
        trigger_set = load_trigger_set(_write(tmp_path / "s.yaml", payload))
        issues = _check_separability(trigger_set, tmp_path / "s.yaml")
        assert issues
        assert "only turns down" in issues[0]

    def test_a_set_over_target_with_no_ceiling_is_refused(self, tmp_path: Path) -> None:
        """Silence is not a waiver. Declaring the number is."""
        trigger_set = self._set(tmp_path, ["a b c d e f"], ["z"])
        issues = _check_separability(trigger_set, tmp_path / "s.yaml")
        assert issues
        assert "declares no ceiling" in issues[0]

    def test_a_set_under_the_target_needs_no_ceiling(self, tmp_path: Path) -> None:
        trigger_set = self._set(tmp_path, ["a b c"], ["d e f"])
        assert _check_separability(trigger_set, tmp_path / "s.yaml") == []


# -- partial adjudication runs -----------------------------------------------
#
# Added for Track N3's continuation: re-running `scripts/adjudicate.py` after a
# corpus edit had no way to touch only the changed items, so a re-run meant
# re-adjudicating everything. `select_cases` and `parse_only` are the pure,
# testable core of `--only` / `--missing-only`; the script itself only wires
# argv to these.


def _cases(*ids: str) -> tuple[TriggerCase, ...]:
    return tuple(TriggerCase(id=i, turn=f"turn {i}", should_fire=True, why="w") for i in ids)


class TestSelectCases:
    def test_with_no_filters_everything_passes_through(self) -> None:
        cases = _cases("a", "b", "c")
        assert select_cases(cases) == cases

    def test_only_narrows_to_the_named_ids(self) -> None:
        cases = _cases("a", "b", "c")
        selected = select_cases(cases, only=["a", "c"])
        assert [case.id for case in selected] == ["a", "c"]

    def test_only_preserves_the_original_order_not_the_argument_order(self) -> None:
        """The corpus's own order, not whatever order a hand-typed list used."""
        cases = _cases("a", "b", "c")
        selected = select_cases(cases, only=["c", "a"])
        assert [case.id for case in selected] == ["a", "c"]

    def test_an_unknown_id_in_only_raises_rather_than_selecting_nothing(self) -> None:
        """A typo must fail loudly. Silently adjudicating zero cases is the M4
        parser-whitelist defect one layer up: a clean run and a plausible zero."""
        cases = _cases("a", "b")
        with pytest.raises(TriggerSetError, match="not in this set"):
            select_cases(cases, only=["a", "nope"])

    def test_exclude_ids_drops_cases_already_adjudicated(self) -> None:
        cases = _cases("a", "b", "c")
        selected = select_cases(cases, exclude_ids=frozenset({"b"}))
        assert [case.id for case in selected] == ["a", "c"]

    def test_only_and_exclude_ids_compose(self) -> None:
        cases = _cases("a", "b", "c")
        selected = select_cases(cases, only=["a", "b"], exclude_ids=frozenset({"b"}))
        assert [case.id for case in selected] == ["a"]

    def test_an_unknown_id_still_raises_even_if_it_would_have_been_excluded(self) -> None:
        """Narrow-then-exclude, fixed: excluding first would let a typo'd id that
        happens to already be done vanish instead of raising."""
        cases = _cases("a", "b")
        with pytest.raises(TriggerSetError, match="not in this set"):
            select_cases(cases, only=["nope"], exclude_ids=frozenset({"nope"}))

    def test_exclude_ids_alone_can_empty_the_set(self) -> None:
        cases = _cases("a")
        assert select_cases(cases, exclude_ids=frozenset({"a"})) == ()


class TestParseOnly:
    def test_a_comma_separated_list_splits_and_strips(self) -> None:
        assert parse_only("a, b ,c") == ("a", "b", "c")

    def test_a_single_id_is_a_one_tuple(self) -> None:
        assert parse_only("a") == ("a",)

    def test_an_at_prefixed_path_reads_ids_one_per_line(self, tmp_path: Path) -> None:
        path = tmp_path / "ids.txt"
        path.write_text("a\nb\n\nc\n", encoding="utf-8")
        assert parse_only(f"@{path}") == ("a", "b", "c")

    def test_a_file_of_ids_skips_comments_and_blank_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "ids.txt"
        path.write_text("# the s+m gap\na\n\n# note\nb\n", encoding="utf-8")
        assert parse_only(f"@{path}") == ("a", "b")
