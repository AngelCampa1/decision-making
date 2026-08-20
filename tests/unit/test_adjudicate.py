"""Tests for the panel description in `scripts/adjudicate.py`.

No model is called. What is checked is that the reliability block says how many
judges it is looking at and what they were, because every coefficient in that
block answers how much the judges agree and none of them answers how many
judges this is. Three fresh instances of one model at one tier read exactly
like three independent raters once the numbers are on the page.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
    """Import ``scripts/adjudicate.py``, which is not part of the package.

    Registered in ``sys.modules`` before execution because the module defines
    dataclasses, and ``dataclasses`` resolves a field annotation through
    ``sys.modules[cls.__module__]``. A module that is not there yet raises an
    ``AttributeError`` from inside ``@dataclass``.
    """
    path = Path(__file__).resolve().parents[2] / "scripts" / "adjudicate.py"
    spec = importlib.util.spec_from_file_location("adjudicate", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["adjudicate"] = module
    spec.loader.exec_module(module)
    return module


adjudicate = _load()


def _rows(*, model: str | None = "haiku", judges: int = 3) -> dict[tuple[str, int], dict]:
    """One case per label, each rated by ``judges`` judges."""
    done: dict[tuple[str, int], dict] = {}
    for case, label in (("p1", True), ("n1", False)):
        for judge in range(judges):
            row: dict = {
                "case": case,
                "judge": judge,
                "adjudicated": label,
                "label": label,
                "band": "s",
                "triple": "t1",
            }
            if model is not None:
                row["model"] = model
            done[(case, judge)] = row
    return done


class TestThePanelIsDescribedBesideTheCoefficients:
    def test_it_counts_judge_slots_and_not_rows(self) -> None:
        """783 rows on record are three judges over 261 cases.

        A panel line reading `haiku x783` would describe the checkpoint rather
        than the panel, and the slot is the rater the coefficients count.
        """
        outcome = adjudicate.adjudication_outcome(_rows())
        assert outcome.panel == ("haiku", "haiku", "haiku")
        assert "haiku x3" in adjudicate._panel_line(outcome.panel)
        assert "one model, sampled 3 times" in adjudicate._panel_line(outcome.panel)

    def test_a_mixed_panel_says_how_many_models(self) -> None:
        assert "2 distinct models" in adjudicate._panel_line(("haiku", "sonnet"))

    def test_a_slot_that_ran_on_two_models_is_named_rather_than_collapsed(self) -> None:
        done = _rows()
        done[("p1", 0)]["model"] = "sonnet"
        outcome = adjudicate.adjudication_outcome(done)
        assert "haiku+sonnet" in adjudicate._panel_line(outcome.panel)

    def test_rows_without_a_model_say_so_rather_than_guessing(self) -> None:
        """Standing rule 1: an invented parameter reads like a measured one."""
        outcome = adjudicate.adjudication_outcome(_rows(model=None))
        assert outcome.panel == ()
        assert "unrecorded" in adjudicate._panel_line(outcome.panel)


class TestEffectiveRatersReachesTheReport:
    def test_the_block_prints_the_panel_and_its_effective_size(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        outcome = adjudicate.adjudication_outcome(_rows())
        adjudicate.report_reliability(outcome)
        out = capsys.readouterr().out
        assert "panel" in out
        assert "Fleiss kappa" in out
        assert "effective raters" in out
        assert "not Kohli's cross-family n_eff" in out

    def test_a_degenerate_panel_prints_the_reason_not_a_number(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Every judge saying the same thing has no measurable independence.

        `_agreement_line` catches it, so the run keeps its report -- the same
        rule the other four coefficients already follow.
        """
        done = _rows()
        for row in done.values():
            row["adjudicated"] = True
            row["label"] = True
        outcome = adjudicate.adjudication_outcome(done)
        adjudicate.report_reliability(outcome)
        out = capsys.readouterr().out
        assert "effective raters     n/a" in out
