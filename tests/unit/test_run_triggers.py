"""Tests for Track N9's venue arm in `scripts/run_triggers.py`.

No model is called anywhere here. `ask()` is tested against a fake
`Conversation` that records its constructor arguments; `collect()` and
`main()` are tested against a fake `ask`/`collect` that never touches a
subprocess. What is checked is the wiring: `--in-situ` reaches
`Conversation(in_situ=...)`, lands on its own checkpoint, is refused beside
the flags that change the response contract, and is stamped onto every row
`collect()` writes.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from decision_evals.triggers import TriggerCase, TriggerSet, load_trigger_set


def _load() -> ModuleType:
    """Import ``scripts/run_triggers.py``, which is not part of the package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_triggers.py"
    spec = importlib.util.spec_from_file_location("run_triggers", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_triggers"] = module
    spec.loader.exec_module(module)
    return module


runner = _load()

CORPUS = (
    Path(__file__).resolve().parents[2] / "datasets" / "triggers" / "decision-making" / "index.yaml"
)


@pytest.fixture(scope="module")
def trigger_set() -> TriggerSet:
    return load_trigger_set(CORPUS)


# --------------------------------------------------------------------------- #
# SYSTEM / SYSTEM_CONFIDENCE: the contract must offer every shipped procedure
# --------------------------------------------------------------------------- #


class TestSystemPromptsOfferEveryShippedProcedure:
    """The router table grew from four rows to six (`council`, `hinge`) on
    2026-08-19 while these prompts still offered only the original four in
    their JSON contract. A model routing correctly to either new procedure
    could not express it, and the old hard-coded whitelist in `triggers.py`
    would have discarded the answer even if it tried.

    Every test here would fail against the old hard-coded
    ``'{"fire": true|false, "procedure": "ledger"|"fit"|"cascade"|"timing"|null}'``
    -- `council` and `hinge` are new to the string, and the count in the prose
    used to be literally the word "four".
    """

    def test_system_names_every_procedure_from_the_shipped_router_table(self) -> None:
        from decision_evals.triggers import default_procedures

        for name in default_procedures():
            assert f'"{name}"' in runner.SYSTEM

    def test_system_confidence_names_every_procedure_too(self) -> None:
        from decision_evals.triggers import default_procedures

        for name in default_procedures():
            assert f'"{name}"' in runner.SYSTEM_CONFIDENCE

    def test_system_prose_does_not_hardcode_the_word_four(self) -> None:
        assert "four procedures" not in runner.SYSTEM
        assert "four procedures" not in runner.SYSTEM_CONFIDENCE

    def test_system_prose_states_the_real_count(self) -> None:
        from decision_evals.triggers import default_procedures

        assert f"{len(default_procedures())} procedures" in runner.SYSTEM
        assert f"{len(default_procedures())} procedures" in runner.SYSTEM_CONFIDENCE


def _case(**overrides: Any) -> TriggerCase:
    defaults: dict[str, Any] = {
        "id": "p1",
        "turn": "Should I take the job?",
        "should_fire": True,
        "why": "test fixture",
    }
    defaults.update(overrides)
    return TriggerCase(**defaults)


# --------------------------------------------------------------------------- #
# ask(): the CLI flag's ultimate destination
# --------------------------------------------------------------------------- #


class _FakeResult:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeReceipt:
    def assert_isolated(self) -> None:
        return None


class _FakeChat:
    def __init__(self, text: str) -> None:
        self._text = text
        self.receipt = _FakeReceipt()

    def send(self, prompt: str) -> _FakeResult:
        return _FakeResult(self._text)

    def __enter__(self) -> _FakeChat:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class _FakeConversationFactory:
    """Records every call's keyword arguments; returns a scripted reply."""

    def __init__(self, text: str = '{"fire": true, "procedure": "ledger"}') -> None:
        self.text = text
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> _FakeChat:
        self.calls.append(kwargs)
        return _FakeChat(self.text)


class TestAskThreadsInSitu:
    """`ask()` is the single place `Conversation` is constructed for this file."""

    def test_in_situ_true_reaches_conversation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _FakeConversationFactory()
        monkeypatch.setattr(runner, "Conversation", fake)
        runner.ask("a description", _case(), "haiku", runner.SYSTEM, in_situ=True)
        assert len(fake.calls) == 1
        assert fake.calls[0]["in_situ"] is True

    def test_in_situ_defaults_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The known-good case: nothing about the existing arms changes."""
        fake = _FakeConversationFactory()
        monkeypatch.setattr(runner, "Conversation", fake)
        runner.ask("a description", _case(), "haiku", runner.SYSTEM)
        assert fake.calls[0]["in_situ"] is False

    def test_the_verdict_still_parses_normally(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Venue changes where the description sits, not how the reply is read."""
        fake = _FakeConversationFactory('{"fire": true, "procedure": "ledger"}')
        monkeypatch.setattr(runner, "Conversation", fake)
        (fired, procedure, p_fire), raw = runner.ask(
            "d", _case(), "haiku", runner.SYSTEM, in_situ=True
        )
        assert fired is True
        assert procedure == "ledger"
        assert p_fire is None
        assert raw == fake.text


# --------------------------------------------------------------------------- #
# collect(): every row is stamped
# --------------------------------------------------------------------------- #


class TestCollectStampsVenue:
    def test_every_row_carries_in_situ_true(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_ask(description, case, model, system, allowed=(), *, in_situ=False):
            return (True, None, None), "raw"

        monkeypatch.setattr(runner, "ask", fake_ask)
        cases = (_case(id="p1"), _case(id="n1", should_fire=False))
        trigger_set = TriggerSet(skill="decision-making", cases=cases, version=4)
        checkpoint = tmp_path / "verdicts-in-situ.jsonl"
        done = runner.collect(trigger_set, "d", "haiku", 1, checkpoint=checkpoint, in_situ=True)
        assert len(done) == 2
        assert all(row["in_situ"] is True for row in done.values())

    def test_the_known_good_case_still_stamps_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Run first, by standing rule 2's spirit: the existing arms are unchanged."""

        def fake_ask(description, case, model, system, allowed=(), *, in_situ=False):
            return (True, None, None), "raw"

        monkeypatch.setattr(runner, "ask", fake_ask)
        cases = (_case(id="p1"),)
        trigger_set = TriggerSet(skill="decision-making", cases=cases, version=4)
        checkpoint = tmp_path / "verdicts.jsonl"
        done = runner.collect(trigger_set, "d", "haiku", 1, checkpoint=checkpoint)
        assert all(row["in_situ"] is False for row in done.values())

    def test_in_situ_reaches_ask(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: list[bool] = []

        def fake_ask(description, case, model, system, allowed=(), *, in_situ=False):
            seen.append(in_situ)
            return (True, None, None), "raw"

        monkeypatch.setattr(runner, "ask", fake_ask)
        cases = (_case(id="p1"),)
        trigger_set = TriggerSet(skill="decision-making", cases=cases, version=4)
        runner.collect(
            trigger_set,
            "d",
            "haiku",
            1,
            checkpoint=tmp_path / "v.jsonl",
            in_situ=True,
        )
        assert seen == [True]


# --------------------------------------------------------------------------- #
# collect(): the skill revision is stamped, with no model call anywhere
# --------------------------------------------------------------------------- #


class TestCollectStampsSkillVersion:
    """`trigger_arms.skill_versions_comparable` reads this field to refuse a

    comparison spanning a `SKILL.md` revision bump, the same way it already
    refuses one spanning `--model`. Nothing here calls a model: `ask` is
    replaced with a fake that returns a scripted verdict, exactly the pattern
    `TestCollectStampsVenue` above uses for `in_situ`.
    """

    def test_every_row_carries_the_given_skill_version(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_ask(description, case, model, system, allowed=(), *, in_situ=False):
            return (True, None, None), "raw"

        monkeypatch.setattr(runner, "ask", fake_ask)
        cases = (_case(id="p1"), _case(id="n1", should_fire=False))
        trigger_set = TriggerSet(skill="decision-making", cases=cases, version=4)
        checkpoint = tmp_path / "verdicts.jsonl"
        done = runner.collect(
            trigger_set, "d", "haiku", 1, checkpoint=checkpoint, skill_version="0.3.0"
        )
        assert len(done) == 2
        assert all(row["skill_version"] == "0.3.0" for row in done.values())

    def test_the_known_good_case_defaults_to_none_not_a_guess(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A caller that passes nothing gets `None` stamped, not an invented

        revision -- `collect()` does not know which `SKILL.md`, if any, a
        caller's `description` came from, and standing rule 1 says record
        that as a fact rather than guess `metadata.version`'s current value.
        """

        def fake_ask(description, case, model, system, allowed=(), *, in_situ=False):
            return (True, None, None), "raw"

        monkeypatch.setattr(runner, "ask", fake_ask)
        cases = (_case(id="p1"),)
        trigger_set = TriggerSet(skill="decision-making", cases=cases, version=4)
        checkpoint = tmp_path / "verdicts-default.jsonl"
        done = runner.collect(trigger_set, "d", "haiku", 1, checkpoint=checkpoint)
        assert all(row["skill_version"] is None for row in done.values())

    def test_main_reads_the_stamp_from_the_shipped_skills_metadata_version(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The stamp `main()` actually passes comes from `parse_skill`, not a

        constant -- so a future version bump is picked up with no code change
        here. Verified against the file on disk rather than a hardcoded
        string, since that file is what this whole guard exists to track.
        """
        from decision_evals.skills import parse_skill

        document = parse_skill(
            Path(__file__).resolve().parents[2] / "skills" / "decision-making" / "SKILL.md"
        )
        expected = str(document.frontmatter["metadata"]["version"])

        captured: dict[str, Any] = {}

        def fake_collect(*args: Any, **kwargs: Any) -> dict[tuple[str, int], dict[str, object]]:
            captured["skill_version"] = kwargs["skill_version"]
            return _fake_collect_from_labels(*args, **kwargs)

        monkeypatch.setattr(runner, "collect", fake_collect)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py"])
        assert runner.main() == 0
        assert captured["skill_version"] == expected


# --------------------------------------------------------------------------- #
# main(): flag parsing, refusals and checkpoint selection
# --------------------------------------------------------------------------- #


def _fake_collect_from_labels(
    trigger_set: TriggerSet,
    description: str,
    model: str,
    repeats: int,
    *,
    system: str,
    checkpoint: Path,
    entry_names: dict[str, str] | None,
    in_situ: bool,
    skill_version: str | None = None,
) -> dict[tuple[str, int], dict[str, object]]:
    """Replays `collect()`'s row shape from the labels, with no model call.

    Used to drive `main()` through its whole report path without a subprocess.
    Firing is set to the label, so parse rate is 100% and nothing downstream
    hits the 90% floor.
    """
    done: dict[tuple[str, int], dict[str, object]] = {}
    for case in trigger_set.cases:
        done[(case.id, 0)] = {
            "case": case.id,
            "repeat": 0,
            "fired": case.should_fire,
            "procedure": case.route,
            "covers": case.route is not None,
            "set_version": trigger_set.version,
            "model": model,
            "in_situ": in_situ,
            "skill_version": skill_version,
            "p_fire": None,
            "should_fire": case.should_fire,
            "route": case.route,
            "routes": list(case.routes),
            "band": case.band,
            "triple": case.triple,
            "domain": case.domain,
            "stakes": case.stakes,
            "ask": case.ask,
            "kind": case.kind,
            "raw": "stub",
        }
    return done


class TestMainInSitu:
    def test_in_situ_and_confidence_together_are_refused(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["run_triggers.py", "--in-situ", "--confidence"])
        assert runner.main() == 1
        assert "response contract" in capsys.readouterr().out

    def test_in_situ_and_arm_four_together_are_refused(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["run_triggers.py", "--in-situ", "--arm", "four"])
        assert runner.main() == 1
        assert "response contract" in capsys.readouterr().out

    def test_in_situ_and_a_non_full_description_together_are_refused(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            sys, "argv", ["run_triggers.py", "--in-situ", "--description", "no-opener"]
        )
        assert runner.main() == 1
        assert "the text" in capsys.readouterr().out

    def test_in_situ_alone_picks_its_own_checkpoint_and_is_threaded_through(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Known-good case: the venue reaches `collect` and the checkpoint is

        Track N9's own file, distinct from every arm above it.
        """
        captured: dict[str, Any] = {}

        def fake_collect(*args: Any, **kwargs: Any) -> dict[tuple[str, int], dict[str, object]]:
            captured["checkpoint"] = kwargs["checkpoint"]
            captured["in_situ"] = kwargs["in_situ"]
            return _fake_collect_from_labels(*args, **kwargs)

        monkeypatch.setattr(runner, "collect", fake_collect)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py", "--in-situ"])
        assert runner.main() == 0
        assert captured["in_situ"] is True
        assert captured["checkpoint"] == runner.CHECKPOINT_IN_SITU
        assert captured["checkpoint"] != runner.CHECKPOINT
        out = capsys.readouterr().out
        assert "checkpoint: verdicts-in-situ.jsonl" in out

    def test_without_in_situ_the_default_checkpoint_is_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The other known-good case: the flag being absent changes nothing."""
        captured: dict[str, Any] = {}

        def fake_collect(*args: Any, **kwargs: Any) -> dict[tuple[str, int], dict[str, object]]:
            captured["checkpoint"] = kwargs["checkpoint"]
            captured["in_situ"] = kwargs["in_situ"]
            return _fake_collect_from_labels(*args, **kwargs)

        monkeypatch.setattr(runner, "collect", fake_collect)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py"])
        assert runner.main() == 0
        assert captured["in_situ"] is False
        assert captured["checkpoint"] == runner.CHECKPOINT


# --------------------------------------------------------------------------- #
# The parse-rate floor: it must be decided over every repeat, not repeat 0
# alone. `done.get((case.id, 0))` used to be the only read a 2-repeat run's
# void decision was made from -- Track N9 exposed it (see
# results/decision-making/2026-08-19-505b236-n9-in-situ-void/README.md).
# --------------------------------------------------------------------------- #


def _multi_repeat_set(n_positive: int = 10, n_negative: int = 10) -> TriggerSet:
    cases = tuple(_case(id=f"p{i}", should_fire=True) for i in range(n_positive)) + tuple(
        _case(id=f"n{i}", should_fire=False) for i in range(n_negative)
    )
    return TriggerSet(skill="decision-making", cases=cases, version=4)


def _row(case: TriggerCase, repeat: int, *, parses: bool) -> dict[str, object]:
    """One checkpoint row, shaped like `collect()`'s output.

    `parses=True` answers correctly (`fired == should_fire`) so a passing gate
    would also score a clean report; `parses=False` is the unparseable shape
    `collect()` writes on a `CliError` -- `fired`, `procedure` and `p_fire` all
    `None`.
    """
    return {
        "case": case.id,
        "repeat": repeat,
        "fired": case.should_fire if parses else None,
        "procedure": case.route if parses else None,
        "covers": None,
        "set_version": 4,
        "model": "haiku",
        "in_situ": False,
        "p_fire": None,
        "should_fire": case.should_fire,
        "route": case.route,
        "routes": list(case.routes),
        "band": case.band,
        "triple": case.triple,
        "domain": case.domain,
        "stakes": case.stakes,
        "ask": case.ask,
        "kind": case.kind,
        "raw": "ok" if parses else "prose with no fire key",
    }


class TestParseRateGateCoversAllRepeats:
    """Constructs the case the old gate misses: repeat 0 clean enough to clear
    the 90% floor on its own, repeat 1 bad enough that the true, all-repeats
    rate falls under it. 20 items, 2 repeats, 40 calls total.

    Every test in this class fails against the pre-fix code, which reads
    only `done.get((case.id, 0))` (`scripts/run_triggers.py`, historical
    line ~929) and therefore never observes repeat 1 at all. Run against
    that code, `test_a_run_with_a_clean_repeat_0_and_a_dirty_repeat_1_is_still_voided`
    fails with `AssertionError: assert 0 == 1` -- the old gate looks only at
    repeat 0 (20/20 parses, 100%), clears 90% and returns 0, exactly the
    "exit zero and be published" failure Track N9's README warned was
    possible but had not been demonstrated.
    """

    def _mixed_done(self, trigger_set: TriggerSet) -> dict[tuple[str, int], dict[str, object]]:
        done: dict[tuple[str, int], dict[str, object]] = {}
        for case in trigger_set.cases:
            done[(case.id, 0)] = _row(case, 0, parses=True)
        # Repeat 1: only the first 6 of 20 cases parse. Aggregate over both
        # repeats: (20 + 6) / 40 = 0.65, below the 90% floor. Repeat 0 alone:
        # 20/20 = 1.00, comfortably above it -- the gap the old gate could not
        # see.
        for index, case in enumerate(trigger_set.cases):
            done[(case.id, 1)] = _row(case, 1, parses=index < 6)
        return done

    def test_a_run_with_a_clean_repeat_0_and_a_dirty_repeat_1_is_still_voided(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        trigger_set = _multi_repeat_set()
        mixed_done = self._mixed_done(trigger_set)

        monkeypatch.setattr(runner, "load_trigger_set", lambda path: trigger_set)
        monkeypatch.setattr(runner, "collect", lambda *a, **k: mixed_done)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py", "--repeats", "2"])

        assert runner.main() == 1
        out = capsys.readouterr().out
        assert "below the 90% floor" in out
        # The printed rate is the aggregate over all 40 calls (0.65), not the
        # repeat-0-only rate (1.00) the old gate would have reported.
        assert "65%" in out
        assert "40 call(s)" in out

    def test_repeat_0_alone_would_have_cleared_the_floor(self) -> None:
        """Documents *why* this case is the one the old gate missed."""
        trigger_set = _multi_repeat_set()
        mixed_done = self._mixed_done(trigger_set)
        repeat_0_rows = [row for (_, repeat), row in mixed_done.items() if repeat == 0]
        assert all(row["fired"] is not None for row in repeat_0_rows)
        assert len(repeat_0_rows) == 20  # 20/20 = 100% >= the 90% floor


class TestParseRateGateKnownGoodCase:
    """Standing rule 2: a falsifier must clear a known-good case before it may
    fail anything. A clean run -- every repeat, every case, parses -- must
    still pass under the fixed gate.
    """

    def test_a_fully_clean_two_repeat_run_still_passes(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        trigger_set = _multi_repeat_set()
        done: dict[tuple[str, int], dict[str, object]] = {}
        for case in trigger_set.cases:
            for repeat in (0, 1):
                done[(case.id, repeat)] = _row(case, repeat, parses=True)

        monkeypatch.setattr(runner, "load_trigger_set", lambda path: trigger_set)
        monkeypatch.setattr(runner, "collect", lambda *a, **k: done)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py", "--repeats", "2"])

        assert runner.main() == 0
        assert "below the 90% floor" not in capsys.readouterr().out

    def test_a_clean_single_repeat_run_still_passes(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """`--repeats 1` (the default) is the shape every published arm used
        before N9 -- this is the case the fix must not disturb.
        """
        trigger_set = _multi_repeat_set()
        monkeypatch.setattr(runner, "collect", _fake_collect_from_labels)
        monkeypatch.setattr(runner, "load_trigger_set", lambda path: trigger_set)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py"])

        assert runner.main() == 0
        assert "below the 90% floor" not in capsys.readouterr().out


class TestParseRateOverAllRepeats:
    """Unit-level coverage of the function the gate now calls."""

    def test_counts_unparseable_across_every_repeat(self) -> None:
        trigger_set = _multi_repeat_set(n_positive=2, n_negative=2)
        done: dict[tuple[str, int], dict[str, object]] = {}
        for case in trigger_set.cases:
            done[(case.id, 0)] = _row(case, 0, parses=True)
            done[(case.id, 1)] = _row(case, 1, parses=False)
        unparseable, total = runner.parse_rate_over_all_repeats(trigger_set, done, 2)
        assert total == 8  # 4 cases * 2 repeats
        assert unparseable == 4  # every repeat-1 row

    def test_a_missing_row_counts_as_unparseable(self) -> None:
        """Collection stopped early: repeat 1 was never attempted for anyone.

        A smaller denominator from missing calls must not let an interrupted
        run look cleaner than a completed one.
        """
        trigger_set = _multi_repeat_set(n_positive=2, n_negative=2)
        done = {(case.id, 0): _row(case, 0, parses=True) for case in trigger_set.cases}
        unparseable, total = runner.parse_rate_over_all_repeats(trigger_set, done, 2)
        assert total == 8
        assert unparseable == 4  # the 4 missing repeat-1 rows

    def test_repeats_1_matches_the_old_repeat_0_only_behaviour(self) -> None:
        """The known-good case for the function itself: at `repeats=1` there is
        only one repeat to read, so the new denominator and the old one agree.
        """
        trigger_set = _multi_repeat_set(n_positive=3, n_negative=3)
        done = {(case.id, 0): _row(case, 0, parses=True) for case in trigger_set.cases}
        unparseable, total = runner.parse_rate_over_all_repeats(trigger_set, done, 1)
        assert (unparseable, total) == (0, 6)


class TestN9Recomputation:
    """Re-derives Track N9's own headline numbers from its checkpoint, so the
    fix is checked against the real run that exposed the defect and not only
    against a constructed example.
    """

    CHECKPOINT = (
        Path(__file__).resolve().parents[2]
        / "results"
        / "decision-making"
        / "2026-08-19-505b236-n9-in-situ-void"
        / "verdicts-in-situ.jsonl"
    )

    def _load(self) -> dict[tuple[str, int], dict[str, object]]:
        return runner.load_done(self.CHECKPOINT)

    def test_the_checkpoint_is_258_items_by_2_repeats(self) -> None:
        done = self._load()
        assert len(done) == 516
        assert {repeat for _, repeat in done} == {0, 1}
        assert len({case_id for case_id, _ in done}) == 258

    def test_repeat_0_alone_reads_the_published_0_8566(self) -> None:
        done = self._load()
        repeat_0 = [row for (_, repeat), row in done.items() if repeat == 0]
        parsed = sum(1 for row in repeat_0 if row["fired"] is not None)
        assert round(parsed / len(repeat_0), 4) == 0.8566

    def test_repeat_1_alone_reads_the_published_0_8721(self) -> None:
        done = self._load()
        repeat_1 = [row for (_, repeat), row in done.items() if repeat == 1]
        parsed = sum(1 for row in repeat_1 if row["fired"] is not None)
        assert round(parsed / len(repeat_1), 4) == 0.8721

    def test_the_new_gate_reads_the_aggregate_0_8643_and_still_voids(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        done = self._load()
        case_ids = sorted({case_id for case_id, _ in done})
        cases = tuple(
            _case(id=cid, should_fire=bool(done[(cid, 0)]["should_fire"])) for cid in case_ids
        )
        trigger_set = TriggerSet(skill="decision-making", cases=cases, version=4)

        unparseable, total = runner.parse_rate_over_all_repeats(trigger_set, done, 2)
        rate = (total - unparseable) / total
        assert total == 516
        assert unparseable == 70
        assert round(rate, 4) == 0.8643
        assert rate < 0.9  # the disposition is still void under the new gate


# --------------------------------------------------------------------------- #
# The item analysis, and `--against`.
#
# Both exist because of the same failure one level up: an estimator with a
# coverage floor and no caller is tested, proven and inert. `decision_evals`
# has shipped four of those. `trigger_arms.item_analysis` is called from the
# report path here so the fifth is not the item analysis registered on
# 2026-08-19, and `--against` is what gives `trigger_arms.compare` -- and the
# four comparability guards inside it -- a caller outside `tests/`.
# --------------------------------------------------------------------------- #


def _paired_rows(*, set_version: int = 4, correct: bool = True) -> list[dict[str, object]]:
    """Two items in one repeat, shaped like a checkpoint and scored by label."""
    return [
        {
            "case": "p1",
            "repeat": 0,
            "fired": correct,
            "should_fire": True,
            "set_version": set_version,
            "model": "haiku",
            "in_situ": False,
            "triple": "t1",
        },
        {
            "case": "n1",
            "repeat": 0,
            "fired": False,
            "should_fire": False,
            "set_version": set_version,
            "model": "haiku",
            "in_situ": False,
            "triple": "t1",
        },
    ]


class TestItemAnalysisIsReachedFromTheReportPath:
    def test_main_prints_it(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The whole point: it runs on a run, not only in a test."""
        monkeypatch.setattr(runner, "collect", _fake_collect_from_labels)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py"])
        assert runner.main() == 0
        out = capsys.readouterr().out
        assert "ITEM ANALYSIS" in out
        assert "respondents" in out
        assert "DIFFICULTY" in out
        assert "DISCRIMINATION" in out
        assert "SCREEN" in out
        assert "TRIPLES" in out

    def test_it_prints_the_reason_rather_than_losing_the_run(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A run that made every call must not lose its report to a refusal."""
        done = {
            ("p1", 0): dict(_paired_rows()[0], fired=None),
        }
        runner.report_item_analysis(done, "arm")
        out = capsys.readouterr().out
        assert "not available" in out
        assert "unparseable" in out


def _write_arm(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return path


class TestPoolAssemblesTheRegisteredRespondentSet:
    """`--pool` is the denominator, and without it the wired path was n=2.

    The pre-registration in
    `notebook/2026-08-19-the-item-analysis-this-instrument-never-ran.md`
    registers twelve respondents -- six description arms at two repeats. The
    report path shipped passing one arm, so `item_discrimination`, which
    refuses below three respondents, was blank in every run that printed it.
    """

    def test_pooling_raises_the_respondent_count(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        pool = [
            _write_arm(tmp_path / "verdicts-opener-only.jsonl", _paired_rows()),
            _write_arm(tmp_path / "verdicts-no-opener.jsonl", _paired_rows(correct=False)),
        ]
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_item_analysis(done, "verdicts-full", pool)
        out = capsys.readouterr().out
        assert "pooled from 3 arms" in out
        assert "verdicts-no-opener" in out
        assert "verdicts-opener-only" in out
        assert "over 3 respondent(s)" in out

    def test_one_arm_names_the_set_it_is_not(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The caveat has to say the denominator is a parameter of the call."""
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_item_analysis(done, "verdicts-full")
        out = capsys.readouterr().out
        assert "from this arm alone" in out
        assert "--pool" in out

    def test_a_comparability_guard_refuses_the_whole_table(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Pooling is a stronger claim than comparing, so a refusal stops it.

        Dropping the offending arm would move the denominator the caller named
        and print a number anyway, which is how a pooled statistic quietly
        becomes a statistic about a different set.
        """
        pool = [_write_arm(tmp_path / "verdicts-v3.jsonl", _paired_rows(set_version=3))]
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_item_analysis(done, "verdicts-full", pool)
        out = capsys.readouterr().out
        assert "not available" in out
        assert "cannot join this respondent set" in out
        assert "label revisions" in out
        assert "DIFFICULTY" not in out

    def test_the_in_situ_arm_is_refused_by_the_venue_guard(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The registered exclusion, enforced rather than remembered.

        The entry excludes `verdicts-in-situ` because 70 of its 516 responses
        are unparseable and the parse rate splits by domain. Every row there
        carries `in_situ: true`, so `venue_comparable` catches the exact file
        the entry names -- the exclusion does not depend on which paths a
        caller happened to type.
        """
        in_situ = [dict(row, in_situ=True) for row in _paired_rows()]
        pool = [_write_arm(tmp_path / "verdicts-in-situ.jsonl", in_situ)]
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_item_analysis(done, "verdicts-full", pool)
        out = capsys.readouterr().out
        assert "not available" in out
        assert "cannot join this respondent set" in out

    def test_a_stem_collision_is_refused(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Two checkpoints under one arm name collapse into one silently."""
        pool = [_write_arm(tmp_path / "verdicts-full.jsonl", _paired_rows())]
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_item_analysis(done, "verdicts-full", pool)
        out = capsys.readouterr().out
        assert "not available" in out
        assert "already in it" in out

    def test_an_unreadable_pooled_checkpoint_costs_the_table_not_the_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_item_analysis(done, "verdicts-full", [tmp_path / "absent.jsonl"])
        assert "could not be read" in capsys.readouterr().out

        broken = tmp_path / "half-written.jsonl"
        broken.write_text('{"case": "p1", "repeat":', encoding="utf-8")
        runner.report_item_analysis(done, "verdicts-full", [broken])
        assert "could not be read" in capsys.readouterr().out

    def test_main_reaches_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The flag has to be wired, not merely accepted."""
        other = _write_arm(tmp_path / "verdicts-pooled.jsonl", _paired_rows())
        monkeypatch.setattr(runner, "collect", _fake_collect_from_labels)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py", "--pool", str(other)])
        assert runner.main() == 0
        out = capsys.readouterr().out
        assert "ITEM ANALYSIS" in out
        # The run's own checkpoint is stamped from the corpus and from
        # `SKILL.md`; this file is stamped at neither, so a guard refuses. Which
        # one depends on the default corpus, so only the refusal is asserted
        # here and the guard-by-guard assertions are above.
        assert "cannot join this respondent set" in out


class TestAgainstReachesCompare:
    def test_it_prints_the_registered_paired_test(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        other = tmp_path / "verdicts-other.jsonl"
        other.write_text(
            "\n".join(json.dumps(record) for record in _paired_rows(correct=False)),
            encoding="utf-8",
        )
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_against(done, other, "arm")
        out = capsys.readouterr().out
        assert "paired Wilcoxon" in out
        assert "verdicts-other" in out

    def test_a_comparability_guard_refuses_and_the_refusal_is_the_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The reason `compare` needed a caller at all.

        Four guards were tested to their floor and reachable from nothing. This
        is one of them firing from an entry point.
        """
        other = tmp_path / "verdicts-old.jsonl"
        other.write_text(
            "\n".join(json.dumps(record) for record in _paired_rows(set_version=3)),
            encoding="utf-8",
        )
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_against(done, other, "arm")
        out = capsys.readouterr().out
        assert "REFUSED" in out
        assert "label revisions" in out

    def test_a_label_that_moved_inside_one_key_version_is_refused(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Identical model behaviour, one moved label, and no stamp to catch it.

        Every verdict here is the same in both arms and both are stamped
        `set_version: 4`, so all four stamp guards pass. Before the label guard
        this printed accuracy 1.0000 against 0.6667 and an item-moved line.
        """
        moved = [dict(record) for record in _paired_rows()]
        moved[0]["should_fire"] = False
        other = tmp_path / "verdicts-relabelled.jsonl"
        other.write_text("\n".join(json.dumps(record) for record in moved), encoding="utf-8")
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_against(done, other, "arm")
        out = capsys.readouterr().out
        assert "REFUSED" in out
        assert "both labels" in out
        assert "accuracy" not in out

    def test_an_unreadable_checkpoint_costs_the_comparison_not_the_report(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """`load_arm` raises `ValueError`, not `OSError`, on a corrupt file.

        This runs after every model call has been made, on a path the caller
        typed. A half-written line and a cp1252 checkpoint both raise
        `ValueError` subclasses, and catching only `OSError` loses a completed
        run's report to a file the run did not write.
        """
        broken = tmp_path / "half-written.jsonl"
        broken.write_text('{"case": "p1", "repeat":', encoding="utf-8")
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_against(done, broken, "arm")
        assert "not available" in capsys.readouterr().out

        latin = tmp_path / "cp1252.jsonl"
        latin.write_bytes(b'{"case": "p\x961"}\n')
        runner.report_against(done, latin, "arm")
        assert "not available" in capsys.readouterr().out

    def test_an_empty_checkpoint_is_reported_not_compared(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        other = tmp_path / "empty.jsonl"
        other.write_text("", encoding="utf-8")
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_against(done, other, "arm")
        assert "holds no records" in capsys.readouterr().out

    def test_a_missing_checkpoint_is_reported_not_raised(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        done = {(str(record["case"]), 0): record for record in _paired_rows()}
        runner.report_against(done, tmp_path / "absent.jsonl", "arm")
        assert "not available" in capsys.readouterr().out

    def test_main_reaches_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        other = tmp_path / "verdicts-unstamped.jsonl"
        other.write_text(
            "\n".join(json.dumps(record) for record in _paired_rows()),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner, "collect", _fake_collect_from_labels)
        monkeypatch.setattr(sys, "argv", ["run_triggers.py", "--against", str(other)])
        assert runner.main() == 0
        out = capsys.readouterr().out
        assert f"AGAINST {other.name}" in out
        # A guard refuses -- this file is stamped at label version 4 and carries
        # no `skill_version`, while the run stamps both from the corpus and from
        # `SKILL.md`. Which of the four fires depends on the default corpus, so
        # only the refusal is asserted here; the guard-by-guard assertions are
        # above, on `report_against` directly. The refusal *is* the output.
        assert "REFUSED" in out
