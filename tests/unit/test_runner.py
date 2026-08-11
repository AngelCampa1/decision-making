"""Tests for the run loop.

The resumability tests matter most. A confirmation run spans days against a
rolling quota, so "resume where you stopped" is not a convenience — it is the
only way the run completes at all, and a checkpoint that silently re-runs or
silently skips corrupts the result rather than merely wasting time.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from decision_evals import runner
from decision_evals.budget import BudgetLedger
from decision_evals.generators.generate import Item, generate
from decision_evals.generators.schema import Template
from decision_evals.providers.claude_code import AuthenticationError, CliError, CliResult
from decision_evals.runner import (
    RunError,
    completed_keys,
    iter_items,
    load_records,
    run_arm,
)
from decision_evals.solvers.arms import build_arm

Build = Callable[..., dict[str, Any]]
ARM = build_arm("off")


@pytest.fixture
def items(template_dict: Build) -> list[Item]:
    return generate(Template.model_validate(template_dict()), 1)


def _result(text: str, cost: float = 0.001) -> CliResult:
    return CliResult(
        text=text,
        model="claude-haiku-4-5-20251001",
        cost_usd=cost,
        input_tokens=100,
        output_tokens=20,
        duration_ms=1000,
        session_id="s",
    )


def _answers_correctly(items: list[Item]) -> Callable[[str, str, bool], CliResult]:
    """A stub that reads the expected answer out of the rendered options.

    Deliberately answers the *first* option every time rather than the correct
    one, so a test asserting correctness is asserting the scorer ran, not that
    the stub cheated.
    """
    del items

    def call(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del system_prompt, append
        first_option = prompt.split("Options:\n")[1].splitlines()[0].removeprefix("- ")
        return _result(f"ANSWER: {first_option}")

    return call


def test_a_run_produces_one_record_per_item(items: list[Item], tmp_path: Path) -> None:
    records = run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=tmp_path / "run.jsonl",
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=10.0),
    )
    assert len(records) == len(items)
    assert {r.arm for r in records} == {"off"}
    assert all(r.model == "claude-haiku-4-5-20251001" for r in records)


def test_records_carry_the_stratum_and_cluster_keys(items: list[Item], tmp_path: Path) -> None:
    """Analysis needs the template id to resample and the strata to break down."""
    records = run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=tmp_path / "run.jsonl",
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=10.0),
    )
    assert {r.template_id for r in records} == {items[0].template_id}
    assert {r.n_distractors for r in records} == {i.n_distractors for i in items}


# -- resumability -----------------------------------------------------------


def test_a_resumed_run_skips_completed_work(items: list[Item], tmp_path: Path) -> None:
    checkpoint = tmp_path / "run.jsonl"
    call = _answers_correctly(items)
    first = run_arm(
        items[:3],
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=call,
        ledger=BudgetLedger(limit_usd=10.0),
    )
    second = run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=call,
        ledger=BudgetLedger(limit_usd=10.0),
    )
    assert len(first) == 3
    assert len(second) == len(items) - 3
    assert len(load_records(checkpoint)) == len(items)


def test_completed_keys_are_read_per_arm(items: list[Item], tmp_path: Path) -> None:
    """The same item in a different arm is different work."""
    checkpoint = tmp_path / "run.jsonl"
    call = _answers_correctly(items)
    run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=call,
        ledger=BudgetLedger(limit_usd=10.0),
    )
    on_arm = build_arm("on", skill_body="# Skill\nDo the thing.")
    again = run_arm(
        items,
        on_arm,
        model="haiku",
        checkpoint=checkpoint,
        call=call,
        ledger=BudgetLedger(limit_usd=10.0),
    )
    assert len(again) == len(items)


def test_a_truncated_final_line_does_not_void_the_checkpoint(tmp_path: Path) -> None:
    """A run killed mid-write leaves a partial line; that must not cost the rest."""
    checkpoint = tmp_path / "run.jsonl"
    checkpoint.write_text(
        json.dumps({"item_id": "a", "arm": "off"}) + '\n{"item_id": "b", "ar',
        encoding="utf-8",
    )
    assert completed_keys(checkpoint) == {("a", "off")}


def test_an_absent_checkpoint_is_an_empty_one(tmp_path: Path) -> None:
    assert completed_keys(tmp_path / "nothing.jsonl") == set()
    assert load_records(tmp_path / "nothing.jsonl") == []


def test_unreadable_records_are_skipped_on_load(tmp_path: Path) -> None:
    checkpoint = tmp_path / "run.jsonl"
    checkpoint.write_text('not json\n{"item_id": "a"}\n', encoding="utf-8")
    assert load_records(checkpoint) == []


# -- failure handling -------------------------------------------------------


def test_authentication_failure_stops_the_run(items: list[Item], tmp_path: Path) -> None:
    """Never scored. A revoked token would otherwise look like total model failure."""

    def failing(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del prompt, system_prompt, append
        raise AuthenticationError("token revoked")

    with pytest.raises(RunError, match="authentication failed"):
        run_arm(
            items,
            ARM,
            model="haiku",
            checkpoint=tmp_path / "run.jsonl",
            call=failing,
            ledger=BudgetLedger(limit_usd=10.0),
        )


def test_a_single_call_failure_is_an_infrastructure_zero_not_an_abort(
    items: list[Item], tmp_path: Path
) -> None:
    """One flaky call should not cost the run; it should cost that item."""
    calls = {"n": 0}
    good = _answers_correctly(items)

    def flaky(prompt: str, system_prompt: str, append: bool) -> CliResult:
        calls["n"] += 1
        if calls["n"] == 2:
            raise CliError("transport blew up")
        return good(prompt, system_prompt, append)

    records = run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=tmp_path / "run.jsonl",
        call=flaky,
        ledger=BudgetLedger(limit_usd=10.0),
    )
    failed = [r for r in records if r.zero_cause == "infrastructure"]
    assert len(failed) == 1
    assert len(records) == len(items)
    assert failed[0].cost_usd == 0.0


def test_the_budget_stops_the_run_before_the_call(items: list[Item], tmp_path: Path) -> None:
    """Spend accumulates across items and halts the loop partway through.

    The costs are chosen so the third item is the one that cannot be afforded:
    two calls at 0.02 leave 0.04 spent against a 0.05 limit, and the projected
    0.02 for the next one would overrun.
    """
    checkpoint = tmp_path / "run.jsonl"
    good = _answers_correctly(items)

    def expensive(prompt: str, system_prompt: str, append: bool) -> CliResult:
        cheap = good(prompt, system_prompt, append)
        return replace(cheap, cost_usd=0.02)

    with pytest.raises(RunError, match="stopping before"):
        run_arm(
            items,
            ARM,
            model="haiku",
            checkpoint=checkpoint,
            call=expensive,
            ledger=BudgetLedger(limit_usd=0.05),
            expected_cost_usd=0.02,
        )
    # Whatever completed is still on disk, so the run resumes rather than restarts.
    assert len(load_records(checkpoint)) == 2


def test_the_checkpoint_directory_is_created(items: list[Item], tmp_path: Path) -> None:
    checkpoint = tmp_path / "deep" / "nested" / "run.jsonl"
    run_arm(
        items[:1],
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=10.0),
    )
    assert checkpoint.exists()


# -- ordering ---------------------------------------------------------------


def test_default_call_forwards_the_scratch_cwd_and_arm_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The cwd is the first isolation guard; it must reach the provider intact."""
    seen: dict[str, Any] = {}

    def fake_run(prompt: str, **kwargs: Any) -> CliResult:
        seen.update(kwargs, prompt=prompt)
        return _result("ANSWER: act")

    monkeypatch.setattr(runner, "cli_run", fake_run)
    call = runner.default_call("haiku", "/scratch")
    assert call("the item", "the system prompt", True).text == "ANSWER: act"
    assert seen["cwd"] == "/scratch"
    assert seen["model"] == "haiku"
    assert seen["in_situ"] is True
    assert seen["system_prompt"] == "the system prompt"


def test_preflight_passes_on_a_working_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "cli_preflight", lambda **_: _result("ready"))
    runner.preflight(model="haiku", cwd="/scratch")


def test_preflight_names_the_misleading_status_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """The whole point: `claude auth status` says loggedIn:true while this fails."""

    def revoked(**_: Any) -> CliResult:
        raise AuthenticationError("token revoked")

    monkeypatch.setattr(runner, "cli_preflight", revoked)
    with pytest.raises(RunError, match="not a useful check"):
        runner.preflight(model="haiku", cwd="/scratch")


def test_preflight_surfaces_other_failures_too(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(**_: Any) -> CliResult:
        raise CliError("CLI not on PATH")

    monkeypatch.setattr(runner, "cli_preflight", broken)
    with pytest.raises(RunError, match="preflight failed"):
        runner.preflight(model="haiku", cwd="/scratch")


def test_arms_interleave_per_item(items: list[Item]) -> None:
    """Blocked arms would confound the arm with everything that changed between blocks."""
    arms = [build_arm("off"), build_arm("cot")]
    pairs = iter_items(items[:3], arms)
    assert [arm.arm for _, arm in pairs] == ["off", "cot", "off", "cot", "off", "cot"]
    assert [item.item_id for item, _ in pairs[:2]] == [items[0].item_id] * 2
