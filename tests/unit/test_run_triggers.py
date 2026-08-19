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
