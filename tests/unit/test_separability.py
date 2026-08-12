"""Tests for the surface-separability gate.

The gate exists to say "no signal", so it has to be shown to have teeth before
that answer means anything. A detector that cannot separate obviously different
registers would pass every corpus and license every dose curve.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "separability.py"
    spec = importlib.util.spec_from_file_location("separability", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["separability"] = module
    spec.loader.exec_module(module)
    return module


sep = _load()

_CORE = [
    "s.44(1) The employer must serve written notice within 14 days of 3 March 2026, "
    "and must pay $12,400 on or before 2026-04-01.",
    "s.46(3) The trustee shall file the amended return by 17 June 2026. The charge "
    "is $297,000 and section 12 requires it be paid within 30 days.",
    "s.211(1) The power to reassess expires four years after 1 January 2024. "
    "The taxpayer must be notified in writing and may not appeal after 2026-02-28.",
    "s.216(2) A member is required to advise the client in writing without delay. "
    "The correction charge of $45,000 falls due on 9 September 2026.",
    "s.49(2) Notice must be served by 2026-05-15. The employer shall not dismiss "
    "before that date, and the protected period runs 90 days from 4 April 2026.",
]

_PADDING = [
    "The regional operations review notes that scheduling for the period was carried "
    "out under the standing arrangements and that no variation was sought.",
    "The reviewer records that the position is broadly unchanged from the previous "
    "reporting cycle and that no further action is proposed at this stage.",
    "Correspondence on this matter has been filed. The team considers the approach "
    "taken to be consistent with what was agreed at the time.",
    "It was noted that arrangements remain as previously described and that nothing "
    "has arisen which would suggest a different view is warranted.",
    "The file records a general discussion of the working arrangements, with no "
    "particular conclusion reached and no follow-up identified.",
]


def test_obviously_different_registers_are_separable() -> None:
    """The detector must have teeth before it is trusted to say 'no signal'."""
    assert sep.auc(sep.features(_CORE), sep.features(_PADDING)) > 0.90


def test_identical_documents_score_at_chance() -> None:
    same = ["s.44(1) The employer must serve notice within 14 days."] * 10
    assert sep.auc(sep.features(same[:5]), sep.features(same[5:])) == pytest.approx(0.5)


def test_the_feature_vector_names_every_feature_it_extracts() -> None:
    """Six features, and a reader must be able to see which one carried the AUC."""
    extracted = sep.features(["s.44(1) The employer must pay $12,000 by 3 March 2026."])
    assert set(extracted[0]) == set(sep.FEATURES)


def test_the_per_feature_breakdown_says_which_knob_to_turn() -> None:
    """A failed gate is only actionable if it names the feature that failed."""
    per_feature = sep.feature_auc(sep.features(_CORE), sep.features(_PADDING))

    assert set(per_feature) == set(sep.FEATURES)
    assert per_feature["citations"] > 0.90
    assert per_feature["deontic_verbs"] > 0.90


def test_the_auc_is_folded_so_direction_does_not_matter() -> None:
    """Padding reliably *denser* in numerals separates just as well as thinner."""
    forwards = sep.auc(sep.features(_CORE), sep.features(_PADDING))
    backwards = sep.auc(sep.features(_PADDING), sep.features(_CORE))
    assert forwards == pytest.approx(backwards)


def test_an_empty_side_is_chance_rather_than_a_crash() -> None:
    assert sep.auc(sep.features(_CORE), []) == pytest.approx(0.5)
    assert sep.auc([], sep.features(_PADDING)) == pytest.approx(0.5)


def test_an_empty_document_does_not_divide_by_zero() -> None:
    extracted = sep.features([""])
    assert all(value == 0.0 for value in extracted[0].values())


def test_a_document_with_no_sentence_break_still_has_a_length() -> None:
    extracted = sep.features(["one two three four five"])
    assert extracted[0]["mean_sentence_length"] == 5.0


def test_numerals_and_dates_are_counted_per_hundred_words_not_absolutely() -> None:
    """Otherwise the feature is document length wearing another name."""
    short = sep.features(["The charge is $297,000."])[0]
    long = sep.features(["The charge is $297,000. " + "filler word here. " * 50])[0]
    assert short["numerals"] > long["numerals"]
