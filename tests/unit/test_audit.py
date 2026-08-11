"""Tests for the two-auditor distractor filter."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from decision_evals.generators.audit import (
    REQUIRED_AUDITORS,
    AuditorVote,
    audit_distractor,
    audit_template,
    build_audit_prompt,
    shared_solution_variables,
    summarise,
    template_variables,
)
from decision_evals.generators.schema import Distractor, Template

Build = Callable[..., dict[str, Any]]


def accepts(_: str) -> AuditorVote:
    return AuditorVote(irrelevant=True, rationale="plays no part in the decision")


def dissents(_: str) -> AuditorVote:
    return AuditorVote(irrelevant=False, rationale="a reader might treat it as grounds")


@pytest.fixture
def template(template_dict: Build) -> Template:
    return Template.model_validate(template_dict())


def _distractor(template: Template, fact_id: str) -> Distractor:
    return next(d for d in template.distractor_facts if d.id == fact_id)


# -- structural check -------------------------------------------------------


def test_template_variables_extracts_placeholders() -> None:
    assert template_variables("The {a} is {b}.") == frozenset({"a", "b"})
    assert template_variables("No placeholders here.") == frozenset()


def test_a_distractor_sharing_a_solution_variable_is_not_provably_inert(
    template_dict: Build,
) -> None:
    template = Template.model_validate(
        template_dict(
            distractor_facts=[
                {"id": "d1", "text": "The limit was set to {limit} last year.", "strength": "high"},
                {"id": "d2", "text": "The office is open.", "strength": "low"},
                {
                    "id": "d3",
                    "text": "An unrelated {thing} has a value of {other_value}.",
                    "strength": "high",
                    "collides_with": "value",
                },
            ]
        )
    )
    assert shared_solution_variables(template, _distractor(template, "d1")) == {"limit"}


def test_a_shared_variable_rejects_without_consulting_the_auditors(
    template_dict: Build,
) -> None:
    """Spending quota to confirm a rejection we have already proven buys nothing."""
    template = Template.model_validate(
        template_dict(
            distractor_facts=[
                {"id": "d1", "text": "The value was {value} last year.", "strength": "high"},
                {"id": "d2", "text": "The office is open.", "strength": "low"},
                {
                    "id": "d3",
                    "text": "An unrelated {thing} has a value of {other_value}.",
                    "strength": "high",
                    "collides_with": "value",
                },
            ]
        )
    )
    calls: list[str] = []

    def counting(prompt: str) -> AuditorVote:
        calls.append(prompt)
        return AuditorVote(irrelevant=True, rationale="")

    verdict = audit_distractor(template, _distractor(template, "d1"), [counting, counting])

    assert calls == []
    assert not verdict.accepted
    assert not verdict.structurally_invariant
    assert "shares solution variables (value)" in verdict.reason


# -- semantic check ---------------------------------------------------------


def test_unanimous_agreement_accepts(template: Template) -> None:
    verdict = audit_distractor(template, _distractor(template, "d2"), [accepts, accepts])
    assert verdict.accepted
    assert verdict.reason.startswith("accepted:")


def test_a_single_dissent_rejects(template: Template) -> None:
    """Unanimity, in the conservative direction.

    A wrongly-admitted distractor mismeasures the headline effect; a
    wrongly-rejected one costs a template one distractor.
    """
    verdict = audit_distractor(template, _distractor(template, "d2"), [accepts, dissents])
    assert not verdict.accepted
    assert verdict.structurally_invariant
    assert "auditor dissent" in verdict.reason


def test_too_few_votes_is_not_an_acceptance(template: Template) -> None:
    verdict = audit_distractor(template, _distractor(template, "d2"), [accepts])
    assert not verdict.accepted
    assert f"only 1 of {REQUIRED_AUDITORS}" in verdict.reason


def test_a_single_auditor_is_refused_at_the_template_level(template: Template) -> None:
    with pytest.raises(ValueError, match="not a filter, it is an opinion"):
        audit_template(template, [accepts])


# -- prompt -----------------------------------------------------------------


def test_the_prompt_shows_the_distractor_in_context(template: Template) -> None:
    """Irrelevance is a property of a statement in context, not on its own."""
    prompt = build_audit_prompt(template, _distractor(template, "d1"))
    assert template.question in prompt
    assert "The limit is {limit}." in prompt
    assert "act, hold" in prompt
    assert "VERDICT: IRRELEVANT" in prompt


def test_the_prompt_asks_about_defensibility_not_necessity(template: Template) -> None:
    """The failure being screened for is ambiguity, and unnecessary != unusable."""
    prompt = build_audit_prompt(template, _distractor(template, "d1"))
    assert "legitimately use" in prompt
    assert "not strictly necessary" in prompt.replace("\n", " ")


# -- aggregation ------------------------------------------------------------


def test_auditing_a_template_covers_every_distractor_in_order(template: Template) -> None:
    verdicts = audit_template(template, [accepts, accepts])
    assert [v.distractor_id for v in verdicts] == ["d1", "d2"]
    assert all(v.template_id == template.template_id for v in verdicts)


def test_summary_reports_attrition(template: Template) -> None:
    verdicts = [
        audit_distractor(template, _distractor(template, "d1"), [accepts, accepts]),
        audit_distractor(template, _distractor(template, "d2"), [accepts, dissents]),
    ]
    summary = summarise(verdicts)
    assert (summary.considered, summary.accepted, summary.rejected) == (2, 1, 1)
    assert summary.acceptance_rate == 0.5


def test_an_empty_audit_has_a_defined_rate() -> None:
    summary = summarise([])
    assert summary.acceptance_rate == 0.0


# -- colliding distractors --------------------------------------------------


def test_the_prompt_names_the_collision(template_dict: Build) -> None:
    """The auditor should not have to spot the near-miss unaided."""
    template = Template.model_validate(template_dict())
    prompt = build_audit_prompt(template, _distractor(template, "d1"))
    assert "same kind as `value`" in prompt
    assert "usable unless that qualifier plainly rules it out" in prompt


def test_the_prompt_stays_quiet_about_a_non_colliding_distractor(template_dict: Build) -> None:
    template = Template.model_validate(template_dict())
    prompt = build_audit_prompt(template, _distractor(template, "d2"))
    assert "same kind as" not in prompt
