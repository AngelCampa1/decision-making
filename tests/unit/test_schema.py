"""Tests for template validation.

Every case here is a benchmark defect that would otherwise surface weeks later
as inexplicable model failures. The schema's job is to convert each one into a
load-time error naming the field.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

from decision_evals.generators.schema import Template

Build = Callable[..., dict[str, Any]]


def test_the_baseline_template_is_valid(template_dict: Build) -> None:
    """Guards the other tests: each asserts a *deviation* is caught."""
    template = Template.model_validate(template_dict())
    assert template.template_id == "tst-001-example"
    assert [fact.id for fact in template.all_facts] == ["r1", "r2", "d1", "d2"]


@pytest.mark.parametrize(
    ("variables", "match"),
    [
        ({"thing": {}}, "exactly one"),
        ({"thing": {"choice": ["a"], "int": [1, 2]}}, "exactly one"),
        ({"thing": {"choice": []}}, "must not be empty"),
        ({"thing": {"int": [9, 2]}}, "inverted"),
    ],
)
def test_variable_specifications_are_checked(
    template_dict: Build, variables: dict[str, Any], match: str
) -> None:
    with pytest.raises(ValidationError, match=match):
        Template.model_validate(template_dict(variables=variables))


def test_duplicate_fact_ids_are_rejected(template_dict: Build) -> None:
    facts = [
        {"id": "r1", "text": "The limit is {limit}."},
        {"id": "r1", "text": "The value is {value}."},
    ]
    with pytest.raises(ValidationError, match="duplicate fact ids"):
        Template.model_validate(template_dict(relevant_facts=facts))


def test_fact_id_prefixes_must_match_their_role(template_dict: Build) -> None:
    """`r` and `d` prefixes are how a score record recovers a fact's role."""
    with pytest.raises(ValidationError, match="must have an `r` prefix"):
        Template.model_validate(
            template_dict(
                relevant_facts=[{"id": "d9", "text": "The limit is {limit}."}],
                solution={"expr": "'act' if value > limit else 'hold'", "load_bearing": ["d9"]},
            )
        )


def test_a_distractor_cannot_masquerade_as_a_relevant_fact(template_dict: Build) -> None:
    with pytest.raises(ValidationError, match="must have a `d` prefix"):
        Template.model_validate(
            template_dict(distractor_facts=[{"id": "r9", "text": "Blue.", "strength": "low"}])
        )


def test_load_bearing_must_name_real_relevant_facts(template_dict: Build) -> None:
    with pytest.raises(ValidationError, match="load_bearing names facts"):
        Template.model_validate(
            template_dict(
                solution={"expr": "'act' if value > limit else 'hold'", "load_bearing": ["r7"]}
            )
        )


def test_an_undeclared_placeholder_is_caught_at_load_time(template_dict: Build) -> None:
    """Otherwise this is a KeyError from str.format several frames from the cause."""
    with pytest.raises(ValidationError, match="undeclared variable 'ghost'"):
        Template.model_validate(
            template_dict(
                relevant_facts=[{"id": "r1", "text": "The {ghost} appeared."}],
                solution={"expr": "'act' if value > limit else 'hold'", "load_bearing": ["r1"]},
            )
        )


def test_an_undeclared_placeholder_in_the_question_is_caught(template_dict: Build) -> None:
    with pytest.raises(ValidationError, match="question references undeclared"):
        Template.model_validate(template_dict(question="What about {phantom}?"))


def test_the_solution_cannot_reference_undeclared_variables(template_dict: Build) -> None:
    with pytest.raises(ValidationError, match="solution expression references undeclared"):
        Template.model_validate(
            template_dict(
                solution={"expr": "'act' if nowhere > 1 else 'hold'", "load_bearing": ["r1"]}
            )
        )


def test_an_unsafe_solution_expression_is_rejected(template_dict: Build) -> None:
    with pytest.raises(ValidationError):
        Template.model_validate(
            template_dict(solution={"expr": "__import__('os').getcwd()", "load_bearing": ["r1"]})
        )


def test_strata_must_include_the_clean_room_split(template_dict: Build) -> None:
    """The protocol's first dataset gate is defined on the zero-distractor split."""
    with pytest.raises(ValidationError, match="must include 0"):
        Template.model_validate(
            template_dict(strata={"distractors": [1, 4], "position": ["early"]})
        )


def test_negative_distractor_counts_are_rejected(template_dict: Build) -> None:
    with pytest.raises(ValidationError, match="non-negative"):
        Template.model_validate(
            template_dict(strata={"distractors": [0, -1], "position": ["early"]})
        )


def test_strata_cannot_ask_for_more_distractors_than_exist(template_dict: Build) -> None:
    with pytest.raises(ValidationError, match="only 2 are defined"):
        Template.model_validate(
            template_dict(strata={"distractors": [0, 5], "position": ["early"]})
        )


def test_unknown_keys_are_rejected(template_dict: Build) -> None:
    """A typo'd key would otherwise be silently ignored."""
    with pytest.raises(ValidationError):
        Template.model_validate(template_dict(varaints=4))


@pytest.mark.parametrize("bad_id", ["Rel-001-x", "rel-1-x", "rel-001", "001-rel-x"])
def test_template_ids_follow_the_naming_convention(template_dict: Build, bad_id: str) -> None:
    with pytest.raises(ValidationError):
        Template.model_validate(template_dict(template_id=bad_id))


def test_a_template_needs_at_least_two_options(template_dict: Build) -> None:
    with pytest.raises(ValidationError):
        Template.model_validate(template_dict(options=["only"]))


def test_templates_are_frozen(template_dict: Build) -> None:
    """Nothing downstream may mutate a loaded template in place."""
    template = Template.model_validate(template_dict())
    with pytest.raises(ValidationError):
        template.variants = 9


# -- collisions -------------------------------------------------------------


def test_a_template_with_no_colliding_distractor_is_rejected(template_dict: Build) -> None:
    """The lesson of the first control run, encoded as a load-time error.

    A corpus of off-topic distractors scored 110/110 and measured nothing.
    """
    with pytest.raises(ValidationError, match="no distractor declares `collides_with`"):
        Template.model_validate(
            template_dict(
                distractor_facts=[
                    {"id": "d1", "text": "The office is {colour}.", "strength": "high"},
                    {"id": "d2", "text": "The office is open.", "strength": "low"},
                ]
            )
        )


def test_colliding_with_something_the_solution_ignores_is_rejected(template_dict: Build) -> None:
    with pytest.raises(ValidationError, match="which the solution does not read"):
        Template.model_validate(
            template_dict(
                distractor_facts=[
                    {
                        "id": "d1",
                        "text": "An unrelated item costs {other_value}.",
                        "strength": "high",
                        "collides_with": "colour",
                    },
                    {"id": "d2", "text": "The office is open.", "strength": "low"},
                ]
            )
        )


def test_a_collision_carrying_no_competing_quantity_is_rejected(template_dict: Build) -> None:
    """Declaring a collision does not create one."""
    with pytest.raises(ValidationError, match="carries 0 competing variable"):
        Template.model_validate(
            template_dict(
                distractor_facts=[
                    {
                        "id": "d1",
                        "text": "The {thing} was reviewed last year.",
                        "strength": "high",
                        "collides_with": "value",
                    },
                    {"id": "d2", "text": "The office is open.", "strength": "low"},
                ]
            )
        )


def test_an_ambiguous_collision_is_rejected(template_dict: Build) -> None:
    """Two competing quantities of the same kind: which one is it competing with?"""
    with pytest.raises(ValidationError, match="carries 2 competing variable"):
        Template.model_validate(
            template_dict(
                variables={
                    "thing": {"choice": ["alpha", "beta"]},
                    "value": {"int": [1, 10]},
                    "limit": {"int": [1, 10]},
                    "other_value": {"int": [1, 10]},
                    "third_value": {"int": [1, 10]},
                    "colour": {"choice": ["red", "blue"]},
                },
                distractor_facts=[
                    {
                        "id": "d1",
                        "text": "Two unrelated readings were {other_value} and {third_value}.",
                        "strength": "high",
                        "collides_with": "value",
                    },
                    {"id": "d2", "text": "The office is open.", "strength": "low"},
                ],
            )
        )


def test_a_choice_in_the_same_sentence_is_not_a_competing_quantity(template_dict: Build) -> None:
    """`{thing}` sits beside the number and must not be mistaken for it."""
    template = Template.model_validate(template_dict())
    assert template.collision_pairs() == [("value", "other_value")]
