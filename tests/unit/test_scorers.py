"""Verifier fixtures.

Harbor discipline: the verifier is exercised against known-correct, known-wrong,
paraphrased and boundary responses *before* it is trusted with a run. A verifier
defect and a model failure are indistinguishable in the aggregate, and only one
of them is a finding.

The fixtures below are written as real model output -- with the markdown,
restatements and trailing punctuation models actually produce -- rather than as
minimal strings that happen to satisfy the regex.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from decision_evals.generators.generate import Item, generate
from decision_evals.generators.schema import Template
from decision_evals.scorers.answer import (
    ParseStatus,
    parse_answer,
    score_item,
    summarise,
)

Build = Callable[..., dict[str, Any]]
OPTIONS = ["file_sla_claim", "wait"]


@pytest.fixture
def item(template_dict: Build) -> Item:
    return generate(Template.model_validate(template_dict()), 1)[0]


# -- known-correct forms ----------------------------------------------------


@pytest.mark.parametrize(
    "response",
    [
        "ANSWER: file_sla_claim",
        "The downtime exceeded the threshold.\n\nANSWER: file_sla_claim",
        "**ANSWER:** file_sla_claim",
        "ANSWER: **file_sla_claim**",
        "ANSWER: `file_sla_claim`",
        "answer: file_sla_claim",
        "ANSWER:file_sla_claim",
        "ANSWER:    file_sla_claim   ",
        "- ANSWER: file_sla_claim",
        "> ANSWER: file_sla_claim",
        "ANSWER: file_sla_claim.",
        'ANSWER: "file_sla_claim"',
        "Reasoning here.\nANSWER: file_sla_claim\n",
    ],
    ids=lambda r: r[:28],
)
def test_well_formed_answers_parse(response: str) -> None:
    parsed = parse_answer(response, OPTIONS)
    assert parsed.status == "parsed"
    assert parsed.value == "file_sla_claim"


@pytest.mark.parametrize(
    "written",
    ["file sla claim", "File_SLA_Claim", "file-sla-claim", "FILE_SLA_CLAIM"],
)
def test_paraphrased_separators_and_case_are_folded(written: str) -> None:
    """Presentation differences, not content differences.

    The option is recovered because it is unambiguously the same token. This is
    the one place the parser is generous, and it is generous identically in
    every arm.
    """
    parsed = parse_answer(f"ANSWER: {written}", OPTIONS)
    assert parsed.value == "file_sla_claim"


def test_the_last_answer_line_wins() -> None:
    """Models restate; the final statement is the one they stand behind."""
    response = "ANSWER: wait\n\nOn reflection that is wrong.\n\nANSWER: file_sla_claim"
    assert parse_answer(response, OPTIONS).value == "file_sla_claim"


# -- known-wrong and boundary forms -----------------------------------------


@pytest.mark.parametrize(
    ("response", "status"),
    [
        ("The team should file an SLA claim.", "no_answer_line"),
        ("", "no_answer_line"),
        ("I am not sure which option applies.", "no_answer_line"),
        ("ANSWER: maybe_later", "unlisted_option"),
        ("ANSWER: both", "unlisted_option"),
        ("ANSWER:", "no_answer_line"),
    ],
    ids=lambda v: str(v)[:28],
)
def test_malformed_responses_are_classified_not_guessed(response: str, status: ParseStatus) -> None:
    parsed = parse_answer(response, OPTIONS)
    assert parsed.status == status
    assert parsed.value is None


def test_prose_naming_the_option_is_still_a_parse_failure() -> None:
    """No fallback search, deliberately.

    Recovering this would be easy and would corrupt the experiment: recovery
    rates would differ by arm for reasons unrelated to decision quality, and the
    format-integrity guard would stop measuring anything.
    """
    assert parse_answer("Clearly file_sla_claim is right.", OPTIONS).status == "no_answer_line"


def test_options_that_normalise_together_are_reported_as_ambiguous() -> None:
    """A template defect, surfaced rather than silently resolved."""
    parsed = parse_answer("ANSWER: go now", ["go now", "go_now"])
    assert parsed.status == "ambiguous"
    assert parsed.value is None


# -- scoring ----------------------------------------------------------------


def test_a_correct_answer_scores_with_no_zero_cause(item: Item) -> None:
    score = score_item(item, f"ANSWER: {item.answer}")
    assert score.correct
    assert score.zero_cause is None
    assert not score.parse_failed


def test_a_wrong_answer_is_attributed_to_the_agent(item: Item) -> None:
    other = next(option for option in item.options if option != item.answer)
    score = score_item(item, f"ANSWER: {other}")
    assert not score.correct
    assert score.zero_cause == "agent_wrong"
    assert not score.parse_failed


def test_an_unparseable_answer_is_a_format_violation(item: Item) -> None:
    score = score_item(item, "I decline to pick.")
    assert not score.correct
    assert score.zero_cause == "format_violation"
    assert score.parse_failed


def test_infrastructure_failure_outranks_everything(item: Item) -> None:
    """A rate-limited run must not masquerade as a model that stopped answering."""
    score = score_item(item, "", infrastructure_error=True)
    assert score.zero_cause == "infrastructure"


def test_a_correct_response_that_never_happened_is_still_infrastructure(item: Item) -> None:
    score = score_item(item, f"ANSWER: {item.answer}", infrastructure_error=True)
    assert score.zero_cause == "infrastructure"


def test_scores_carry_their_clustering_key(item: Item) -> None:
    """Template id is the resampling unit for every interval we report."""
    assert score_item(item, "ANSWER: nope").template_id == item.template_id


# -- aggregation ------------------------------------------------------------


def test_parse_failures_count_as_incorrect_but_are_reported_separately(item: Item) -> None:
    """The honest denominator, plus what the format-integrity guard needs."""
    other = next(option for option in item.options if option != item.answer)
    scores = [
        score_item(item, f"ANSWER: {item.answer}"),
        score_item(item, f"ANSWER: {other}"),
        score_item(item, "no answer at all"),
        score_item(item, "ANSWER: not_an_option"),
    ]
    summary = summarise(scores)
    assert summary.total == 4
    assert summary.correct == 1
    assert summary.accuracy == 0.25
    assert summary.parse_failures == 2
    assert summary.parse_failure_rate == 0.5


def test_an_empty_run_has_defined_rates() -> None:
    summary = summarise([])
    assert summary.accuracy == 0.0
    assert summary.parse_failure_rate == 0.0
