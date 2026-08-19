"""Tests for the run loop.

The resumability tests matter most. A confirmation run spans days against a
rolling quota, so "resume where you stopped" is not a convenience — it is the
only way the run completes at all, and a checkpoint that silently re-runs or
silently skips corrupts the result rather than merely wasting time.
"""

from __future__ import annotations

import json
import threading
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
from decision_evals.providers.openai_compatible import Endpoint
from decision_evals.runner import (
    CONCURRENCY_UNSAFE,
    RunError,
    completed_keys,
    iter_items,
    load_records,
    local_call,
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


# -- concurrency ------------------------------------------------------------


def test_concurrency_produces_the_same_records_as_the_serial_loop(
    items: list[Item], tmp_path: Path
) -> None:
    """The stub is deterministic, so any difference here is the loop's."""
    common: dict[str, Any] = {
        "model": "haiku",
        "call": _answers_correctly(items),
        "ledger": BudgetLedger(limit_usd=10.0),
    }
    serial = run_arm(items, ARM, checkpoint=tmp_path / "a.jsonl", **common)
    concurrent = run_arm(items, ARM, checkpoint=tmp_path / "b.jsonl", concurrency=4, **common)

    key = lambda records: sorted((r.item_id, r.parsed, r.correct) for r in records)  # noqa: E731
    assert key(serial) == key(concurrent)
    assert len(concurrent) == len(items)


def test_every_item_is_run_exactly_once_under_concurrency(
    items: list[Item], tmp_path: Path
) -> None:
    """A sliding window that double-submits would be invisible in the totals."""
    seen: list[str] = []
    lock = threading.Lock()

    def call(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del system_prompt, append
        with lock:
            seen.append(prompt)
        return _result("ANSWER: nope")

    records = run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=tmp_path / "run.jsonl",
        call=call,
        ledger=BudgetLedger(limit_usd=10.0),
        concurrency=3,
    )
    assert len(seen) == len(items)
    assert len(set(seen)) == len(items)
    assert len({r.item_id for r in records}) == len(items)


def test_calls_really_do_overlap(items: list[Item], tmp_path: Path) -> None:
    """Otherwise the pool is a slow serial loop and the whole change is inert.

    The failure this guards is the one the repository keeps finding: a clean run
    that measured nothing. A `concurrency` argument nothing acts on would pass
    every other test here.
    """
    # A partial final cycle would block until the timeout and then fail with a
    # barrier error naming nothing about the fixture, so the dependency is
    # asserted rather than left to whoever next edits `tests/conftest.py`.
    assert len(items[:6]) % 3 == 0, "this test needs a multiple of the barrier width"
    barrier = threading.Barrier(3, timeout=30)

    def call(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del prompt, system_prompt, append
        # Only returns once three calls are simultaneously inside it.
        barrier.wait()
        return _result("ANSWER: nope")

    records = run_arm(
        items[:6],
        ARM,
        model="haiku",
        checkpoint=tmp_path / "run.jsonl",
        call=call,
        ledger=BudgetLedger(limit_usd=10.0),
        concurrency=3,
    )
    assert len(records) == 6


def test_the_checkpoint_survives_concurrent_completion(items: list[Item], tmp_path: Path) -> None:
    """One writer on the calling thread; interleaved lines are unreadable."""
    checkpoint = tmp_path / "run.jsonl"
    run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=10.0),
        concurrency=4,
    )
    lines = checkpoint.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(items)
    assert all(json.loads(line)["item_id"] for line in lines)
    assert len(load_records(checkpoint)) == len(items)


def test_a_concurrent_run_resumes_on_the_same_keys(items: list[Item], tmp_path: Path) -> None:
    """Completion-order writes must not break `(item_id, arm)` resume."""
    checkpoint = tmp_path / "run.jsonl"
    call = _answers_correctly(items)
    run_arm(
        items[:3],
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=call,
        ledger=BudgetLedger(limit_usd=10.0),
        concurrency=3,
    )
    second = run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=call,
        ledger=BudgetLedger(limit_usd=10.0),
        concurrency=3,
    )
    assert len(second) == len(items) - 3
    assert len(load_records(checkpoint)) == len(items)


def test_an_authentication_failure_still_stops_a_concurrent_run(
    items: list[Item], tmp_path: Path
) -> None:
    def call(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del prompt, system_prompt, append
        raise AuthenticationError("revoked")

    with pytest.raises(RunError, match="authentication failed"):
        run_arm(
            items,
            ARM,
            model="haiku",
            checkpoint=tmp_path / "run.jsonl",
            call=call,
            ledger=BudgetLedger(limit_usd=10.0),
            concurrency=4,
        )


def _one_fails_after_all_arrive(width: int) -> Callable[[str, str, bool], CliResult]:
    """A `CallFn` where every call parks until all of them have arrived.

    Then exactly one raises. Parking first is what puts the failure and the
    successes into a single `wait()` batch, which is the case the drain in
    `run_arm` exists for; without it the failure usually completes alone and
    the batch has nothing to lose.
    """
    barrier = threading.Barrier(width, timeout=30)
    first = threading.Event()

    def one_bad_apple(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del prompt, system_prompt, append
        barrier.wait()
        if not first.is_set():
            first.set()
            raise AuthenticationError("nope")
        return _result("ANSWER: nope")

    return one_bad_apple


def _counts_into(made: list[str]) -> Callable[[str, str, bool], CliResult]:
    """A `CallFn` that records every prompt it was asked for.

    A factory rather than a closure defined in the loop, which binds the loop
    variable late and is what ruff's B023 is about.
    """

    def counting(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del system_prompt, append
        made.append(prompt)
        # Charges exactly what `expected_cost_usd` authorises below. With the
        # default 0.001 the ledger never catches up with the authorisation and
        # the serial arm runs to the end, so the comparison would pass for the
        # wrong reason.
        return _result("ANSWER: nope", cost=0.02)

    return counting


def test_the_budget_still_stops_a_concurrent_run(items: list[Item], tmp_path: Path) -> None:
    """And it stops after the same number of calls the serial path would make.

    This asked for `limit_usd=0.0` until the adversarial review of 2026-08-19,
    which refuses the first item before anything is dispatched -- so it
    exercised the serial refusal with a `concurrency` argument attached and
    made zero calls. It could not have caught what it was for: authorisation
    read `spent_usd`, which only advances when a record comes back, so every
    call in one window saw the same balance and the budget could refuse
    nothing beyond the first item. Six items at $0.02 against a $0.021 limit
    ran all six.

    The limit here authorises exactly one call, and the assertion is on the
    number of calls actually made rather than on the exception alone.
    """
    made: list[str] = []

    def counting(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del system_prompt, append
        made.append(prompt)
        return _result("ANSWER: nope")

    with pytest.raises(RunError, match="stopping before"):
        run_arm(
            items,
            ARM,
            model="haiku",
            checkpoint=tmp_path / "run.jsonl",
            call=counting,
            ledger=BudgetLedger(limit_usd=0.021),
            expected_cost_usd=0.02,
            concurrency=len(items),
        )
    assert len(made) == 1, f"the window authorised {len(made)} calls against a limit for one"


def test_a_concurrent_run_stops_where_the_serial_one_does(
    items: list[Item], tmp_path: Path
) -> None:
    """The budget is not a different budget at a different concurrency.

    Reserving at dispatch is what makes this hold; charging only on completion
    made the answer depend on the window size.
    """
    counts: dict[int, int] = {}
    for concurrency in (1, 2, len(items)):
        made: list[str] = []
        counting = _counts_into(made)

        with pytest.raises(RunError, match="stopping before"):
            run_arm(
                items,
                ARM,
                model="haiku",
                checkpoint=tmp_path / f"run-{concurrency}.jsonl",
                call=counting,
                ledger=BudgetLedger(limit_usd=0.05),
                expected_cost_usd=0.02,
                concurrency=concurrency,
            )
        counts[concurrency] = len(made)

    assert len(set(counts.values())) == 1, f"call count varied with concurrency: {counts}"


def test_an_abort_keeps_the_calls_it_already_paid_for(items: list[Item], tmp_path: Path) -> None:
    """A failure must not discard its own batch's successes.

    Returning on the first failing future threw away calls that had already
    succeeded alongside it, and which ones survived depended on set iteration
    order -- twelve trials produced three different checkpoints from the same
    inputs. Those calls were made and paid for, so discarding them makes the
    ledger under-read the real burn and makes an aborted run irreproducible.
    """
    survivors = []
    for attempt in range(8):
        one_bad_apple = _one_fails_after_all_arrive(len(items))
        checkpoint = tmp_path / f"run-{attempt}.jsonl"
        with pytest.raises(RunError):
            run_arm(
                items,
                ARM,
                model="haiku",
                checkpoint=checkpoint,
                call=one_bad_apple,
                ledger=BudgetLedger(limit_usd=10.0),
                concurrency=len(items),
            )
        records = load_records(checkpoint)
        # Whatever survived must be intact. A torn line is the one thing
        # `load_records` refuses, so reaching here at all is part of the check.
        assert all(record.arm == ARM.arm for record in records)
        survivors.append(len(records))

    # Not `len(set(survivors)) == 1`, which is what this asserted until the
    # first CI run returned [5, 5, 5, 5, 5, 0, 5, 5]. Draining the batch does
    # not make the *count* deterministic and cannot: which futures are in a
    # given `wait()` return is a timing property, and sometimes the failure
    # completes alone before any success has landed.
    #
    # What the drain does guarantee is that no success is discarded from a
    # batch that also contained the failure. So the observable invariant is
    # that a trial keeps either none of them or all of them, never some -- and
    # an intermediate count is precisely the defect. Before the fix the same
    # experiment returned 3, 2 and 1 across trials.
    allowed = {0, len(items) - 1}
    assert set(survivors) <= allowed, (
        f"an abort kept a partial batch: {survivors}, expected each trial in {sorted(allowed)}. "
        "Returning on the first failing future discarded whichever successes sorted after it."
    )


@pytest.mark.parametrize("bad", [0, -1])
def test_a_non_positive_concurrency_is_refused(items: list[Item], tmp_path: Path, bad: int) -> None:
    with pytest.raises(RunError, match="at least 1"):
        run_arm(
            items,
            ARM,
            model="haiku",
            checkpoint=tmp_path / "run.jsonl",
            call=_answers_correctly(items),
            ledger=BudgetLedger(limit_usd=10.0),
            concurrency=bad,
        )


def test_a_measured_unsafe_model_refuses_concurrency(items: list[Item], tmp_path: Path) -> None:
    """The register is enforced, not merely documented.

    `ollama/qwen3:4b` is in `CONCURRENCY_UNSAFE` because the falsifier measured
    two serial passes agreeing on 31 of 40 items and the concurrent pass on 0 of
    40. A future session speeding up a grid would otherwise get records that
    compare with nothing, and a checkpoint would not say so.
    """
    assert any(model.startswith(tuple(CONCURRENCY_UNSAFE)) for model in ["ollama/qwen3:4b"])
    with pytest.raises(RunError, match="different text under concurrency"):
        run_arm(
            items,
            ARM,
            model="ollama/qwen3:4b",
            checkpoint=tmp_path / "run.jsonl",
            call=_answers_correctly(items),
            ledger=BudgetLedger(limit_usd=10.0),
            concurrency=4,
        )


def test_an_unsafe_model_still_runs_serially(items: list[Item], tmp_path: Path) -> None:
    """The refusal is about concurrency, not about the backend.

    Serial is the arm every published number used, and it is exactly what the
    falsifier found reproducible. Refusing it too would retire a working venue
    over a finding about a different mode.
    """
    records = run_arm(
        items,
        ARM,
        model="ollama/qwen3:4b",
        checkpoint=tmp_path / "run.jsonl",
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=10.0),
    )
    assert len(records) == len(items)


def test_the_falsifier_may_re_measure_an_unsafe_model(items: list[Item], tmp_path: Path) -> None:
    """The register may only shrink, so something has to be able to shrink it.

    Without this escape the entry would be permanent by construction: the run
    that would clear `ollama` is a concurrent run on `ollama`.
    """
    records = run_arm(
        items,
        ARM,
        model="ollama/qwen3:4b",
        checkpoint=tmp_path / "run.jsonl",
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=10.0),
        concurrency=4,
        measuring_concurrency=True,
    )
    assert len(records) == len(items)


def test_a_bare_model_name_cannot_smuggle_past_the_register(tmp_path: Path) -> None:
    """The register matches the recorded string, so the request must carry it.

    `build_payload` strips a `label/` prefix and tolerates a bare name, and
    `parse_completion` stamps the label back on. So `qwen3:4b` reached the same
    server and produced records reading `ollama/qwen3:4b` while the guard never
    fired -- and `qwen3:4b` is what `ollama list` prints, so it is the natural
    thing to type. The register may only shrink by measurement, not by typo.
    """
    del tmp_path
    with pytest.raises(RunError, match="does not name its venue"):
        local_call("qwen3:4b")


def test_the_register_is_not_case_sensitive(items: list[Item], tmp_path: Path) -> None:
    """`Ollama/` is the same venue and was accepted at concurrency 4."""
    with pytest.raises(RunError, match="different text under concurrency"):
        run_arm(
            items,
            ARM,
            model="Ollama/qwen3:4b",
            checkpoint=tmp_path / "run.jsonl",
            call=_answers_correctly(items),
            ledger=BudgetLedger(limit_usd=10.0),
            concurrency=4,
        )


def test_an_unmeasured_model_is_not_refused(items: list[Item], tmp_path: Path) -> None:
    """Unmeasured is not the same as unsafe, and the register says only what was run.

    Claiming otherwise would be the inverse of this repository's usual error:
    asserting a result for a venue nobody has tested.
    """
    # Asked the other way round until the 2026-08-19 review: `prefix.startswith
    # ("haiku")` interrogates the register, not the model, and stays true even
    # when haiku is genuinely registered unsafe.
    assert not "haiku".startswith(tuple(CONCURRENCY_UNSAFE))
    records = run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=tmp_path / "run.jsonl",
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=10.0),
        concurrency=4,
    )
    assert len(records) == len(items)


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


def test_unreadable_records_stop_the_analysis(tmp_path: Path) -> None:
    """This used to assert the records were silently skipped.

    That was the bug: a checkpoint of unreadable lines returned an empty list and
    an analysis over nothing, which is indistinguishable in the summary from a
    run that produced nothing.
    """
    checkpoint = tmp_path / "run.jsonl"
    checkpoint.write_text('not json\n{"item_id": "a"}\n', encoding="utf-8")
    with pytest.raises(RunError, match="not JSON"):
        load_records(checkpoint)


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


def test_local_call_reaches_the_openai_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """The substitution `CallFn` was written for, with no second run loop."""
    seen: dict[str, Any] = {}

    def fake_run(prompt: str, **kwargs: Any) -> CliResult:
        seen.update(kwargs, prompt=prompt)
        return _result("ANSWER: act")

    monkeypatch.setattr(runner, "openai_run", fake_run)
    call = runner.local_call("ollama/qwen3:4b")
    assert call("the item", "the system prompt", False).text == "ANSWER: act"
    assert seen["model"] == "ollama/qwen3:4b"
    assert seen["system_prompt"] == "the system prompt"
    assert seen["endpoint"] is None


def test_local_call_forwards_an_explicit_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_run(prompt: str, **kwargs: Any) -> CliResult:
        seen.update(kwargs)
        return _result("ANSWER: act")

    monkeypatch.setattr(runner, "openai_run", fake_run)
    endpoint = Endpoint(base_url="http://box:8000/v1", label="vllm")
    runner.local_call("vllm/llama", endpoint)("i", "s", False)
    assert seen["endpoint"] is endpoint


def test_local_call_refuses_the_in_situ_arm() -> None:
    """Two arms with one meaning is worse than one arm fewer.

    A raw completion has no pre-existing system prompt to append to, so running
    the in-situ arm here would send the isolated prompt under the other arm's
    label, and nothing downstream could tell them apart.
    """
    with pytest.raises(RunError, match="no meaning against a raw completion"):
        runner.local_call("ollama/qwen3:4b")("i", "s", True)


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


def test_a_long_item_is_authorised_at_more_than_the_old_flat_rate(
    items: list[Item], tmp_path: Path
) -> None:
    """The flat $0.05 default under-counted a 100k prompt roughly fivefold.

    A ledger with room for one flat-rate call must refuse a long item rather
    than authorising it and discovering the shortfall afterwards.
    """
    long_fact = items[0].facts[0].model_copy(update={"text": "x" * 400_000})
    long_item = items[0].model_copy(update={"facts": [long_fact]})

    def never_called(prompt: str, system_prompt: str, append: bool) -> CliResult:
        del prompt, system_prompt, append
        raise AssertionError("the ledger should have refused before the call")

    with pytest.raises(RunError, match="stopping before"):
        run_arm(
            [long_item],
            ARM,
            model="haiku",
            checkpoint=tmp_path / "run.jsonl",
            call=never_called,
            ledger=BudgetLedger(limit_usd=0.06),
        )


def test_a_short_item_is_still_affordable_under_the_derived_estimate(
    items: list[Item], tmp_path: Path
) -> None:
    """The estimate must not be so conservative that ordinary items stop running."""
    records = run_arm(
        items,
        ARM,
        model="haiku",
        checkpoint=tmp_path / "run.jsonl",
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=1.0),
    )
    assert len(records) == len(items)


def test_a_record_from_an_older_schema_is_refused_loudly(tmp_path: Path) -> None:
    """Adding a stratum column must not make every earlier record vanish.

    load_records swallowed TypeError, so a schema change silently returned an
    empty list and the analysis reported a run that had not happened. The next
    change to RunRecord is a set of stratum columns for the long corpus, so this
    is about to matter.
    """
    checkpoint = tmp_path / "run.jsonl"
    checkpoint.write_text('{"item_id": "rel-001-v0", "arm": "off"}\n', encoding="utf-8")

    with pytest.raises(RunError, match="schema"):
        load_records(checkpoint)


def test_a_truncated_final_line_is_tolerated(items: list[Item], tmp_path: Path) -> None:
    """A crash mid-write leaves a partial line; that is expected and recoverable.

    A well-formed record with the wrong columns is not, which is the distinction
    the old blanket except could not draw.
    """
    checkpoint = tmp_path / "run.jsonl"
    run_arm(
        items[:1],
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=1.0),
    )
    with checkpoint.open("a", encoding="utf-8") as handle:
        handle.write('{"item_id": "rel-')

    assert len(load_records(checkpoint)) == 1


def test_unparseable_json_before_the_last_line_is_refused(tmp_path: Path) -> None:
    """Corruption in the middle of a file is not a partial write."""
    checkpoint = tmp_path / "run.jsonl"
    checkpoint.write_text("not json\nalso not json\n", encoding="utf-8")

    with pytest.raises(RunError, match="not JSON"):
        load_records(checkpoint)


def test_blank_lines_in_a_checkpoint_are_ignored(items: list[Item], tmp_path: Path) -> None:
    """An editor, a crash, or a manual inspection can leave one behind.

    A blank line is not corruption and must not stop an analysis that a whole
    day of quota paid for.
    """
    checkpoint = tmp_path / "run.jsonl"
    run_arm(
        items[:2],
        ARM,
        model="haiku",
        checkpoint=checkpoint,
        call=_answers_correctly(items),
        ledger=BudgetLedger(limit_usd=1.0),
    )
    body = checkpoint.read_text(encoding="utf-8").splitlines()
    checkpoint.write_text(f"{body[0]}\n\n{body[1]}\n", encoding="utf-8")

    assert len(load_records(checkpoint)) == 2
