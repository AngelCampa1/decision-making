"""Tests for the calibration script's corpus lock.

Only the lock is tested here. The rest of ``calibrate.py`` is reporting and a
model loop, both covered elsewhere; the fingerprint is the part whose failure
would be silent and would corrupt a published number.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from pydantic import Field

from decision_evals.generators.generate import Item, RenderedFact


def _load() -> ModuleType:
    """Import ``scripts/calibrate.py``, which is not part of the package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "calibrate.py"
    spec = importlib.util.spec_from_file_location("calibrate", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["calibrate"] = module
    spec.loader.exec_module(module)
    return module


calibrate = _load()


def _item(*, item_id: str = "tst-001-x#v0-d0-none", fact: str = "The limit is 5.") -> Item:
    return Item(
        item_id=item_id,
        template_id="tst-001-x",
        seed=1,
        variant=0,
        n_distractors=0,
        position="none",
        variables={"limit": 5},
        question="Should the team act?",
        options=["act", "hold"],
        facts=[RenderedFact(id="r1", text=fact, role="relevant")],
        answer="act",
        load_bearing=["r1"],
        distractor_ids=[],
    )


def test_the_fingerprint_is_stable_for_identical_items() -> None:
    assert calibrate.corpus_fingerprint([_item()]) == calibrate.corpus_fingerprint([_item()])


def test_changed_fact_text_changes_the_fingerprint() -> None:
    """The case that motivated this: same coordinates, different content.

    Item ids encode template, variant and stratum, so a rewritten template
    produces identical ids over completely different text. A checkpoint keyed on
    ids alone resumes cleanly and reports one number computed from two corpora.
    """
    before = calibrate.corpus_fingerprint([_item(fact="The limit is 5.")])
    after = calibrate.corpus_fingerprint([_item(fact="The limit exceeds 5.")])
    assert before != after


def test_a_first_run_records_the_fingerprint(tmp_path: Path) -> None:
    checkpoint = tmp_path / "run" / "off-arm.jsonl"
    calibrate.assert_checkpoint_matches(checkpoint, [_item()])
    assert checkpoint.with_suffix(".corpus").read_text(encoding="utf-8") == (
        calibrate.corpus_fingerprint([_item()])
    )


def test_resuming_the_same_corpus_is_allowed(tmp_path: Path) -> None:
    checkpoint = tmp_path / "off-arm.jsonl"
    calibrate.assert_checkpoint_matches(checkpoint, [_item()])
    checkpoint.write_text("{}\n", encoding="utf-8")
    calibrate.assert_checkpoint_matches(checkpoint, [_item()])


def test_resuming_a_different_corpus_is_refused(tmp_path: Path) -> None:
    checkpoint = tmp_path / "off-arm.jsonl"
    calibrate.assert_checkpoint_matches(checkpoint, [_item()])
    checkpoint.write_text("{}\n", encoding="utf-8")
    with pytest.raises(calibrate.CorpusMismatchError, match="different corpus"):
        calibrate.assert_checkpoint_matches(checkpoint, [_item(fact="Something else.")])


def test_a_checkpoint_with_no_sidecar_is_refused(tmp_path: Path) -> None:
    """Every checkpoint written before the lock existed, including the first run."""
    checkpoint = tmp_path / "off-arm.jsonl"
    checkpoint.write_text("{}\n", encoding="utf-8")
    with pytest.raises(calibrate.CorpusMismatchError, match="recorded: \\(none\\)"):
        calibrate.assert_checkpoint_matches(checkpoint, [_item()])


# -- documents --------------------------------------------------------------


class _Casefile(Item):
    """An item that carries documents, which is what a casefile is.

    Defined here rather than added to ``Item`` because adding a field to ``Item``
    re-blesses every ``rel-*`` golden file, and those must not move. This is a
    stand-in for what the casefile item kind will be, and it exists so the
    fingerprint's document handling is exercised before that lands rather than
    after the first padded run resumes off a stale checkpoint.
    """

    documents: list[dict[str, str]] = Field(default_factory=list)


def _casefile(bodies: list[tuple[str, str]]) -> _Casefile:
    return _Casefile(
        **_item().model_dump(),
        documents=[{"id": doc_id, "body": body} for doc_id, body in bodies],
    )


def test_changing_a_document_body_changes_the_fingerprint() -> None:
    """Padding lives in documents, not in facts.

    A fingerprint blind to document bodies lets a padded corpus resume off a
    checkpoint built from the unpadded one and report a number computed half on
    each. Length is the independent variable, so this is the version of the bug
    that bites exactly where the experiment lives.
    """
    before = calibrate.corpus_fingerprint([_casefile([("doc1", "The figure was 12.")])])
    after = calibrate.corpus_fingerprint([_casefile([("doc1", "The figure was restated to 14.")])])
    assert before != after


def test_reordering_documents_changes_the_fingerprint() -> None:
    """Padding order is reshuffled between arms, so it is part of the prompt."""
    forwards = _casefile([("doc1", "alpha"), ("doc2", "beta")])
    backwards = _casefile([("doc2", "beta"), ("doc1", "alpha")])
    assert calibrate.corpus_fingerprint([forwards]) != calibrate.corpus_fingerprint([backwards])


def test_an_item_without_documents_still_fingerprints() -> None:
    """The rel-* corpus has no documents and must keep working unchanged."""
    assert calibrate.corpus_fingerprint([_item()])
