"""Tests for item generation."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable
from typing import Any

import pytest

from decision_evals.generators.generate import (
    NO_POSITION,
    GenerationError,
    arrange,
    derive_seed,
    generate,
    sample_variables,
    strata_combinations,
)
from decision_evals.generators.schema import Fact, Template

Build = Callable[..., dict[str, Any]]


@pytest.fixture
def template(template_dict: Build) -> Template:
    return Template.model_validate(template_dict())


# -- seeds ------------------------------------------------------------------


def test_seed_derivation_is_stable_across_processes() -> None:
    """Pinned literally: `hash()` is randomised per process and would not do."""
    assert derive_seed("rel-001-vendor-outage", 1, 0) == 2510269093885445083


def test_each_coordinate_changes_the_seed() -> None:
    base = derive_seed("a-001-b", 1, 0)
    assert derive_seed("a-001-c", 1, 0) != base
    assert derive_seed("a-001-b", 2, 0) != base
    assert derive_seed("a-001-b", 1, 1) != base


# -- strata -----------------------------------------------------------------


def test_the_clean_stratum_appears_once_not_once_per_position() -> None:
    """Otherwise the clean split is over-represented by len(positions)."""
    combos = strata_combinations([0, 1, 4], ["early", "middle", "late"])
    assert combos.count((0, NO_POSITION)) == 1
    assert len(combos) == 7


def test_strata_are_sorted_and_deduplicated() -> None:
    assert strata_combinations([4, 0, 4], ["early"]) == [
        (0, NO_POSITION),
        (4, "early"),
    ]


# -- arrangement ------------------------------------------------------------


def _facts(*ids: str) -> list[Fact]:
    return [Fact(id=i, text=i) for i in ids]


def test_position_controls_where_distractors_land() -> None:
    relevant, distractors = _facts("r1", "r2"), _facts("d1")
    assert [f.id for f in arrange(relevant, distractors, "early")] == ["d1", "r1", "r2"]
    assert [f.id for f in arrange(relevant, distractors, "late")] == ["r1", "r2", "d1"]
    assert [f.id for f in arrange(relevant, distractors, "middle")] == ["r1", "d1", "r2"]


def test_arrangement_is_a_no_op_without_distractors() -> None:
    relevant = _facts("r1", "r2")
    assert arrange(relevant, [], "middle") == relevant


def test_an_unknown_position_is_an_error() -> None:
    with pytest.raises(GenerationError, match="unknown position"):
        arrange(_facts("r1"), _facts("d1"), "sideways")


# -- sampling ---------------------------------------------------------------


def test_sampling_covers_every_declared_variable(template: Template) -> None:
    values = sample_variables(template, random.Random(0))
    assert set(values) == set(template.variables)
    assert values["thing"] in ["alpha", "beta"]
    assert 1 <= values["value"] <= 10


def test_labels_are_balanced_by_construction(template: Template) -> None:
    """The defect this fixes: two of ten templates were single-class at 4 variants."""
    answers = Counter(item.answer for item in generate(template, seed=3))
    assert len(set(answers.values())) == 1, answers


def test_an_unreachable_option_fails_loudly(template_dict: Build) -> None:
    """A template that cannot produce one of its options is defective, not unlucky."""
    unreachable = Template.model_validate(
        template_dict(solution={"expr": "'act'", "load_bearing": ["r1"]})
    )
    with pytest.raises(GenerationError, match="could not produce answer 'hold'"):
        generate(unreachable, seed=1)


def test_a_non_string_answer_is_rejected(template_dict: Build) -> None:
    numeric = Template.model_validate(
        template_dict(solution={"expr": "value + limit", "load_bearing": ["r1"]})
    )
    with pytest.raises(GenerationError, match="expected str"):
        generate(numeric, seed=1)


def test_an_answer_outside_the_option_menu_is_rejected(template_dict: Build) -> None:
    stray = Template.model_validate(
        template_dict(solution={"expr": "'maybe'", "load_bearing": ["r1"]})
    )
    with pytest.raises(GenerationError, match="not one of the options"):
        generate(stray, seed=1)


# -- generated items --------------------------------------------------------


def test_generation_is_deterministic(template: Template) -> None:
    assert generate(template, 7) == generate(template, 7)


def test_a_different_seed_gives_different_items(template: Template) -> None:
    assert generate(template, 7) != generate(template, 8)


def test_item_count_is_variants_times_strata(template: Template) -> None:
    combos = strata_combinations(template.strata.distractors, template.strata.position)
    assert len(generate(template, 1)) == template.variants * len(combos)


def test_strata_of_one_variant_share_their_variable_bindings(template: Template) -> None:
    """The clean and loaded items differ only in irrelevant material.

    This is what makes the clean-room check and the difficulty gate a comparison
    on matched content rather than on independently sampled scenarios.
    """
    by_variant = [item for item in generate(template, 1) if item.variant == 0]
    assert len({tuple(sorted(item.variables.items())) for item in by_variant}) == 1
    assert len({item.answer for item in by_variant}) == 1


def test_larger_strata_are_supersets_of_smaller_ones(template: Template) -> None:
    """Distractor count becomes a within-variant contrast rather than a new draw."""
    items = {(i.n_distractors, i.position): i for i in generate(template, 1) if i.variant == 0}
    clean = items[(0, NO_POSITION)]
    loaded = items[(2, "early")]
    assert clean.distractor_ids == []
    assert set(clean.distractor_ids).issubset(loaded.distractor_ids)
    assert len(loaded.distractor_ids) == 2


def test_placeholders_are_rendered_in_facts_and_question(template: Template) -> None:
    item = generate(template, 1)[0]
    assert "{" not in item.question
    for fact in item.facts:
        assert "{" not in fact.text


def test_facts_carry_their_role_and_strength(template: Template) -> None:
    loaded = next(item for item in generate(template, 1) if item.n_distractors == 2)
    roles = {fact.id: fact.role for fact in loaded.facts}
    assert roles["r1"] == "relevant"
    assert roles["d1"] == "distractor"
    strengths = {fact.id: fact.strength for fact in loaded.facts}
    assert strengths["r1"] is None
    assert strengths["d1"] in {"low", "medium", "high"}


def test_item_ids_encode_their_coordinates(template: Template) -> None:
    ids = [item.item_id for item in generate(template, 1)]
    assert "tst-001-example#v0-d0-none" in ids
    assert len(set(ids)) == len(ids)
