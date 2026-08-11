"""Fixture tests for the auditor's verdict parser.

Harbor discipline: the verifier is tested against known-good, known-wrong,
paraphrased and boundary responses *before* any of its outputs are trusted. This
parser decides whether a distractor enters the corpus, so a parsing bug here
would silently change what the benchmark measures.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "audit_distractors.py"
    spec = importlib.util.spec_from_file_location("audit_distractors", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_distractors"] = module
    spec.loader.exec_module(module)
    return module


driver = _load()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Reasoning.\nVERDICT: IRRELEVANT", True),
        ("Reasoning.\nVERDICT: AMBIGUOUS", False),
        ("Reasoning.\nverdict: irrelevant", True),
        ("Reasoning.\n**VERDICT: IRRELEVANT**", True),
        ("Reasoning.\n  VERDICT: AMBIGUOUS  ", False),
    ],
)
def test_recognised_verdict_lines(text: str, expected: bool) -> None:
    assert driver.parse_vote(text).irrelevant is expected


def test_the_last_verdict_wins() -> None:
    """An auditor that revises itself mid-response means the later line."""
    text = "VERDICT: IRRELEVANT\nOn reflection:\nVERDICT: AMBIGUOUS"
    assert driver.parse_vote(text).irrelevant is False


def test_the_word_ambiguous_in_the_reasoning_does_not_decide() -> None:
    """The failure a substring search would produce, and the reason for exact lines."""
    text = "One might call this ambiguous, but it plainly is not.\nVERDICT: IRRELEVANT"
    assert driver.parse_vote(text).irrelevant is True


@pytest.mark.parametrize(
    "text",
    [
        "",
        "I think it's fine.",
        "VERDICT: MAYBE",
        "VERDICT IRRELEVANT",
        "The verdict is irrelevant to my point.",
    ],
)
def test_an_unreadable_response_is_a_dissent(text: str) -> None:
    """Never admit a distractor on the strength of a response nobody could parse."""
    vote = driver.parse_vote(text)
    assert vote.irrelevant is False
    assert "unparseable" in vote.rationale


def test_a_parsed_vote_carries_a_rationale() -> None:
    vote = driver.parse_vote("The window is measured from delivery.\nVERDICT: IRRELEVANT")
    assert vote.rationale == "The window is measured from delivery."
