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
    is_discriminative,
    is_robust,
    sample_variables,
    satisfies_constraints,
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


def test_generated_items_never_sit_on_a_threshold_edge(template: Template) -> None:
    """The defect the first calibration run surfaced.

    A sampling put ``outage_h == sla_h`` against a fact reading "only after N
    continuous hours". Ground truth said `wait` on a strictly-greater rule; the
    model read the sentence as inclusive and was defensibly right. Items on the
    knife edge test how precisely a threshold sentence is read, not whether
    irrelevant context was ranked out.
    """
    for item in generate(template, seed=5):
        assert is_robust(template, item.variables), item.variables


def test_a_tie_is_not_robust(template: Template) -> None:
    """The exact case that failed: equal values either side of a comparison."""
    assert not is_robust(template, {"value": 5, "limit": 5, "thing": "alpha", "colour": "red"})
    assert not is_robust(template, {"value": 6, "limit": 5, "thing": "alpha", "colour": "red"})
    assert is_robust(template, {"value": 9, "limit": 5, "thing": "alpha", "colour": "red"})


def test_robustness_ignores_non_numeric_variables(template_dict: Build) -> None:
    """A choice variable has no ±1 neighbour; nudging it is meaningless."""
    by_choice = Template.model_validate(
        template_dict(
            solution={"expr": "'act' if thing == 'alpha' else 'hold'", "load_bearing": ["r1"]},
            # The collision has to follow the solution: this one turns on a
            # choice, so the competing quantity is a choice too.
            distractor_facts=[
                {
                    "id": "d1",
                    "text": "An unrelated item is {colour}.",
                    "strength": "high",
                    "collides_with": "thing",
                },
                {"id": "d2", "text": "The office is open.", "strength": "low"},
            ],
        )
    )
    assert is_robust(by_choice, {"thing": "alpha", "value": 1, "limit": 1, "colour": "red"})


def test_a_nudge_that_leaves_the_option_menu_counts_as_an_edge(template_dict: Build) -> None:
    edgy = Template.model_validate(
        template_dict(
            solution={
                "expr": "'act' if value > 5 else ('hold' if value > 3 else 'undefined')",
                "load_bearing": ["r1"],
            }
        )
    )
    # value == 4 is one step from falling out of the option menu entirely.
    assert not is_robust(edgy, {"value": 4, "limit": 1, "thing": "alpha", "colour": "red"})


def test_a_corpus_too_tight_for_a_margin_fails_loudly(template_dict: Build) -> None:
    """Better a build failure than a corpus of knife-edge items."""
    cramped = Template.model_validate(
        template_dict(
            variables={
                "thing": {"choice": ["alpha"]},
                "colour": {"choice": ["red"]},
                "value": {"int": [5, 5]},
                "limit": {"int": [5, 5]},
                "other_value": {"int": [5, 5]},
            }
        )
    )
    with pytest.raises(GenerationError, match="robust, discriminative answer"):
        generate(cramped, seed=1)


def test_an_unreachable_option_fails_loudly(template_dict: Build) -> None:
    """A template that cannot produce one of its options is defective, not unlucky."""
    unreachable = Template.model_validate(
        template_dict(
            solution={"expr": "'act' if value > 0 else 'hold'", "load_bearing": ["r1"]},
            variables={
                "thing": {"choice": ["alpha", "beta"]},
                "value": {"int": [1, 10]},
                "limit": {"int": [1, 10]},
                # Ranged below the threshold so the collision can still flip the
                # answer; otherwise this template would fail the discriminative
                # check first and the test would stop being about reachability.
                "other_value": {"int": [-5, 0]},
                "colour": {"choice": ["red", "blue"]},
            },
        )
    )
    with pytest.raises(GenerationError, match="answer 'hold'"):
        generate(unreachable, seed=1)


def test_a_non_string_answer_is_rejected(template_dict: Build) -> None:
    numeric = Template.model_validate(
        template_dict(solution={"expr": "value + limit", "load_bearing": ["r1"]})
    )
    with pytest.raises(GenerationError, match="expected str"):
        generate(numeric, seed=1)


def test_an_answer_outside_the_option_menu_is_rejected(template_dict: Build) -> None:
    stray = Template.model_validate(
        template_dict(solution={"expr": "'maybe' if value > 0 else 'act'", "load_bearing": ["r1"]})
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


# -- collisions -------------------------------------------------------------


def test_every_generated_item_discriminates(template: Template) -> None:
    """Reading the wrong number must change the answer, on every item.

    Otherwise the careful reader and the number-grabber score identically and
    the item contributes dilution rather than signal.
    """
    for item in generate(template, seed=3):
        assert is_discriminative(template, item.variables), item.variables


def test_a_collision_that_agrees_is_not_discriminative(template: Template) -> None:
    """value=9, other_value=8: both above limit=5, so the substitution changes nothing."""
    agreeing = {"value": 9, "other_value": 8, "limit": 5, "thing": "alpha", "colour": "red"}
    assert not is_discriminative(template, agreeing)
    disagreeing = {**agreeing, "other_value": 2}
    assert is_discriminative(template, disagreeing)


def test_a_substitution_that_leaves_the_option_menu_is_not_discriminative(
    template_dict: Build,
) -> None:
    """If the two quantities are not comparable, the distractor is not competing."""
    narrow = Template.model_validate(
        template_dict(
            solution={
                "expr": "'act' if value > 5 else ('hold' if value > 0 else 'undefined')",
                "load_bearing": ["r1"],
            }
        )
    )
    assert not is_discriminative(
        narrow, {"value": 9, "other_value": -3, "limit": 1, "thing": "a", "colour": "red"}
    )


def test_the_real_templates_all_discriminate() -> None:
    """Not a fixture: every shipped item must carry a live collision."""
    from decision_evals.generators import load_all

    for template in load_all():
        assert template.collision_pairs()
        for item in generate(template, seed=1):
            assert is_discriminative(template, item.variables), item.item_id


def test_the_one_distractor_stratum_always_gets_a_colliding_distractor() -> None:
    """A uniform draw would spend that stratum on a coffee machine most of the time."""
    from decision_evals.generators import load_all

    for template in load_all():
        colliding = {d.id for d in template.distractor_facts if d.collides_with is not None}
        for item in generate(template, seed=1):
            if item.n_distractors == 1:
                assert item.distractor_ids[0] in colliding, item.item_id


# -- constraints ------------------------------------------------------------


def test_a_constraint_excludes_incoherent_samplings(template_dict: Build) -> None:
    """rel-008 drew 155 seats in use against a 116-seat quote, and the rule was silent."""
    bounded = Template.model_validate(template_dict(constraints=["value <= limit + 3"]))
    for item in generate(bounded, seed=2):
        assert item.variables["value"] <= item.variables["limit"] + 3, item.variables


def test_satisfies_constraints_is_vacuously_true_without_any(template: Template) -> None:
    assert satisfies_constraints(template, {"value": 99, "limit": 1})


def test_an_unsatisfiable_constraint_fails_loudly(template_dict: Build) -> None:
    impossible = Template.model_validate(template_dict(constraints=["value > limit + 100"]))
    with pytest.raises(GenerationError, match="robust, discriminative answer"):
        generate(impossible, seed=1)
