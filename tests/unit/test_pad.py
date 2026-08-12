"""Tests for the padding assembler.

The assembler manufactures the independent variable, so a defect here does not
produce a wrong number -- it produces a plausible number about something else.
Each test below names the specific way the experiment would have faked itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "pad.py"
    spec = importlib.util.spec_from_file_location("pad", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["pad"] = module
    spec.loader.exec_module(module)
    return module


pad = _load()

#: Long enough that a 40k-token target needs a plausible number of them, which is
#: what makes the domination cap bite in a realistic place rather than never.
_BODY = (
    "The regional operations review for the period notes that scheduling was "
    "carried out under the standing arrangements and that no variation was "
    "sought. The reviewer records that the position is unchanged from the "
    "previous reporting cycle and that no further action is proposed. "
) * 12


def _document(doc_id: str, body: str = _BODY) -> object:
    return pad.Document(id=doc_id, title=f"Note {doc_id}", body=body)


def _library(n: int, suffix: str = "") -> list:
    """``suffix`` is appended to every body, so a whole library can be poisoned.

    Poisoning one document and hoping it is drawn does not work: the draw takes
    a seeded subset, so the assertion would pass or fail with the seed.
    """
    return [_document(f"pad{i:03d}", f"{_BODY} Reference {i:03d}. {suffix}") for i in range(n)]


def _fat_library(n: int) -> list:
    """Few documents, each large. Fills a target on chars while staying small
    enough in count to trip the domination cap rather than the size check."""
    return [_document(f"fat{i:03d}", f"{_BODY * 11} Reference {i:03d}.") for i in range(n)]


def _core(governing_text: str = "The correction charge is $297,000 under s.216(5).") -> object:
    return pad.Core(
        case_id="probe-test",
        documents=(
            _document("doc1", governing_text),
            _document("doc2", "The Year 1 workpaper records the same period."),
        ),
        question="What should the firm do, and in what order?",
    )


# -- determinism ------------------------------------------------------------


def test_the_same_seed_draws_the_same_documents() -> None:
    """A cell that redraws on a resumed run is a different item with the same id."""
    first = pad.draw(_library(400), target_tokens=10_000, seed=7)
    second = pad.draw(_library(400), target_tokens=10_000, seed=7)
    assert [d.id for d in first] == [d.id for d in second]


def test_a_different_seed_draws_differently() -> None:
    first = pad.draw(_library(400), target_tokens=10_000, seed=7)
    second = pad.draw(_library(400), target_tokens=10_000, seed=8)
    assert [d.id for d in first] != [d.id for d in second]


def test_the_draw_does_not_reorder_the_callers_library() -> None:
    """The library is reused across every cell; a shuffle in place would make the
    draw depend on call sequence rather than on the seed."""
    library = _library(400)
    before = [d.id for d in library]
    pad.draw(library, target_tokens=10_000, seed=1)
    assert [d.id for d in library] == before


# -- invariance -------------------------------------------------------------


def test_padding_that_repeats_a_governing_figure_is_refused() -> None:
    """On-topic at the client level, off-topic at the decision level.

    A padding document repeating a figure from the governing chain is neither,
    and it is the single most likely way a padded corpus acquires a second
    correct answer that the key does not know about.
    """
    poisoned = _library(400, suffix="The prior-year charge was $297,000.")

    with pytest.raises(pad.PaddingError, match="297,000"):
        pad.assemble(_core(), poisoned, target_tokens=10_000, seed=1)


def test_padding_that_repeats_a_section_reference_is_refused() -> None:
    poisoned = _library(400, suffix="Consideration was given to s.216(5).")

    with pytest.raises(pad.PaddingError, match=r"s\.216"):
        pad.assemble(_core(), poisoned, target_tokens=10_000, seed=1)


def test_small_numerals_are_not_treated_as_load_bearing() -> None:
    """A rule that flags every "14" is a rule that gets switched off."""
    tokens = pad.load_bearing_tokens("The figure was restated to 14 after the audit.")
    assert tokens == set()


def test_amounts_dates_sections_and_parties_are_load_bearing() -> None:
    tokens = pad.load_bearing_tokens(
        "Larkin Fabrication Ltd owes $297,000 under s.216(5), due 2026-03-14."
    )
    assert "297,000" in tokens
    assert "s.216(5)" in tokens
    assert "2026-03-14" in tokens
    assert "Larkin Fabrication Ltd" in tokens


def test_clean_padding_assembles() -> None:
    prompt = pad.assemble(_core(), _library(400), target_tokens=10_000, seed=1)
    assert "What should the firm do" in prompt


# -- depth ------------------------------------------------------------------


def test_governing_documents_sit_in_the_stated_depth_band() -> None:
    """Depth is held proportional so absolute distance varies with length while
    relative position does not. If this drifts, the dose curve is a position
    curve wearing a length label."""
    core = _core()
    prompt = pad.assemble(core, _library(900), target_tokens=40_000, seed=1)

    assert pad.within_band(prompt, core)


def test_every_governing_document_survives_the_weave() -> None:
    core = _core()
    prompt = pad.assemble(core, _library(900), target_tokens=40_000, seed=3)

    assert len(pad.governing_depths(prompt, core)) == len(core.documents)


def test_a_governing_document_missing_from_the_prompt_is_an_error() -> None:
    """Silently dropping one leaves an item with no answer and a full score sheet."""
    with pytest.raises(pad.PaddingError, match="not in the assembled prompt"):
        pad.governing_depths("nothing here", _core())


def test_the_conjuncts_are_separated_by_real_material() -> None:
    """Distributed conjunction needs distance between the conjuncts. Blocking the
    core would leave them adjacent and the mechanism would not be built."""
    core = _core()
    prompt = pad.assemble(core, _library(900), target_tokens=40_000, seed=1)
    first, second = pad.governing_depths(prompt, core)

    assert second - first > 0.05


# -- domination -------------------------------------------------------------


def test_a_library_too_small_to_serve_a_cell_is_refused() -> None:
    """A document drawn into many cells is a crossed random effect: one that
    perturbs truth contaminates many cells and the standard errors are wrong in
    the anti-conservative direction."""
    with pytest.raises(pad.PaddingError, match="past the 30% cap"):
        pad.draw(_fat_library(12), target_tokens=40_000, seed=1)


def test_no_library_document_dominates_across_cells() -> None:
    """The empirical check the cap exists to guarantee."""
    library = _library(900)
    cells = [{d.id for d in pad.draw(library, target_tokens=40_000, seed=s)} for s in range(30)]

    for document in library:
        appearances = sum(1 for cell in cells if document.id in cell)
        assert appearances / len(cells) <= pad.MAX_CELL_SHARE


def test_a_library_too_small_for_the_target_is_an_error_not_a_short_prompt() -> None:
    """Silently returning 12k tokens when 100k was asked for would put the wrong
    length label on a whole stratum."""
    with pytest.raises(pad.PaddingError, match="too small"):
        pad.draw(_library(3), target_tokens=100_000, seed=1)


def test_an_empty_library_is_refused() -> None:
    with pytest.raises(pad.PaddingError, match="empty"):
        pad.draw([], target_tokens=10_000, seed=1)


def test_a_core_that_already_fills_the_target_needs_no_padding() -> None:
    """The 2k anchor: the core is most of the prompt and there is nothing to add."""
    assert pad.draw(_library(400), target_tokens=100, seed=1, core_chars=100_000) == []


# -- ablation ---------------------------------------------------------------


def test_the_ablated_prompt_keeps_the_padding_and_drops_the_core() -> None:
    """If the core survived ablation the gate would pass for the wrong reason."""
    core = _core()
    library = _library(900)

    ablated = pad.ablate(core, library, target_tokens=40_000, seed=1)

    assert "$297,000" not in ablated
    assert "The regional operations review" in ablated
    assert core.question in ablated


# -- casefile adapter -------------------------------------------------------


def test_a_casefile_becomes_a_core_carrying_only_its_governing_documents() -> None:
    raw = {
        "case_id": "probe-07",
        "question": "What should the firm do?",
        "documents": [
            {"id": "doc1", "title": "Code", "body": "s.214(3) applies."},
            {"id": "doc2", "title": "Letter", "body": "Unrelated."},
        ],
    }
    core = pad.core_from_casefile(raw, {"doc1"})

    assert [d.id for d in core.documents] == ["doc1"]


def test_a_casefile_with_no_governing_documents_named_is_an_error() -> None:
    raw = {"case_id": "probe-07", "question": "?", "documents": [{"id": "doc1", "body": "x"}]}
    with pytest.raises(pad.PaddingError, match="none of"):
        pad.core_from_casefile(raw, {"doc9"})


def test_the_low_anchor_is_unbanded_and_that_is_not_a_failure() -> None:
    """A real core runs to about 1,650 tokens against an 8,000-char budget at the
    2k anchor, so it cannot fit inside a band 30% of the prompt wide.

    The band is a property of the padded strata. Reporting the low anchor as
    banded would be a claim the arithmetic does not support, and ``within_band``
    returning False here is the honest answer rather than a defect.
    """
    core = pad.Core(
        case_id="probe-test",
        documents=tuple(_document(f"doc{k}", f"{_BODY} Governing fact {k}.") for k in range(1, 5)),
        question="What should the firm do?",
    )
    prompt = pad.assemble(core, _library(400), target_tokens=2_000, seed=1)

    assert not pad.within_band(prompt, core)
    # No padding is drawn at all: the core already overruns the character budget,
    # so the first governing document opens the prompt.
    assert pad.governing_depths(prompt, core)[0] == 0.0
    assert all(depth < 1.0 for depth in pad.governing_depths(prompt, core))
