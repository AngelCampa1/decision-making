"""The Antigravity backend, and the refusals that make its records trustworthy.

Every test here is against a fixture or a fake subprocess. The live calls that
established what the fixtures should contain are recorded in
``notebook/2026-08-21-the-agy-backend-and-two-canaries.md``; re-running them
would spend quota to re-learn a fact already written down.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from decision_evals.providers import antigravity as agy
from decision_evals.providers.claude_code import (
    AuthenticationError,
    CliError,
    IsolationError,
    PromptTooLongError,
    RateLimitedError,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "agy"
MODEL = "gemini-3.7-flash-low"


def init_event(**overrides: Any) -> dict[str, Any]:
    """A real ``init`` event, captured 2026-08-21, with fields swapped out."""
    event = json.loads((FIXTURES / f"init-{MODEL}.json").read_text(encoding="utf-8"))
    event["init"].update(overrides)
    return event


def result_event(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "conversation_id": "c-1",
        "status": "SUCCESS",
        "response": "ready\n",
        "duration_seconds": 2.5,
        "num_turns": 1,
        "usage": {"input_tokens": 13742, "output_tokens": 1, "cache_read_tokens": 0},
    }
    payload.update(overrides)
    return {"event": "result", "result": payload}


def stream(*events: dict[str, Any]) -> list[str]:
    return [json.dumps(event) for event in events]


# --- the receipt --------------------------------------------------------------


def test_the_captured_receipt_matches_the_pinned_tool_set() -> None:
    """The fixture is a real call, so this is the pin agreeing with the venue."""
    receipt = agy.parse_init_receipt(init_event())
    assert len(receipt.tools) == 57
    assert frozenset(receipt.tools) == agy.AGY_TOOLS
    receipt.assert_isolated(model=MODEL, cwd=receipt.cwd)


def test_the_tool_set_is_identical_across_vendors() -> None:
    """57 tools is a property of the harness, not of the weights behind it."""
    other = json.loads((FIXTURES / "init-gpt-oss-120b-medium.json").read_text(encoding="utf-8"))
    assert frozenset(agy.parse_init_receipt(other).tools) == agy.AGY_TOOLS


def test_a_substituted_model_is_refused() -> None:
    """The guard against a silent swap, which no downstream analysis could undo."""
    receipt = agy.parse_init_receipt(init_event(model="gemini-3.7-flash-high"))
    with pytest.raises(IsolationError, match=re.escape("answered as 'gemini-3.7-flash-high'")):
        receipt.assert_isolated(model=MODEL, cwd=receipt.cwd)


def test_the_label_is_stripped_before_the_model_is_compared() -> None:
    """`agy/` is a recording convention; the CLI has never heard of it."""
    receipt = agy.parse_init_receipt(init_event())
    receipt.assert_isolated(model=f"agy/{MODEL}", cwd=receipt.cwd)


def test_a_call_outside_the_scratch_directory_is_refused() -> None:
    receipt = agy.parse_init_receipt(init_event(cwd="C:\\somewhere\\else"))
    with pytest.raises(IsolationError, match="not the scratch directory"):
        receipt.assert_isolated(model=MODEL, cwd="C:\\scratch")


def test_an_added_tool_is_refused() -> None:
    """A fifty-eighth tool makes every later call a different experiment."""
    receipt = agy.parse_init_receipt(init_event(tools=[*sorted(agy.AGY_TOOLS), "new_tool"]))
    with pytest.raises(IsolationError, match=r"1 added \['new_tool'\]"):
        receipt.assert_isolated(model=MODEL, cwd=receipt.cwd)


def test_a_removed_tool_is_refused() -> None:
    """Drift in either direction. A smaller venue is still a different one."""
    receipt = agy.parse_init_receipt(init_event(tools=sorted(agy.AGY_TOOLS)[1:]))
    with pytest.raises(IsolationError, match="1 removed"):
        receipt.assert_isolated(model=MODEL, cwd=receipt.cwd)


@pytest.mark.parametrize("event", [{}, {"init": "not-a-mapping"}, {"init": {"tools": "nope"}}])
def test_a_malformed_init_event_reads_as_no_tools(event: dict[str, Any]) -> None:
    """Absent fields become empty, and empty then fails `assert_isolated` loudly.

    The event is the CLI's and its shape is not ours to require, so parsing does
    not raise. What must not happen is a missing ``tools`` key passing for a
    clean venue, and it does not: an empty set is drift.
    """
    receipt = agy.parse_init_receipt(event)
    assert receipt.tools == ()
    with pytest.raises(IsolationError):
        receipt.assert_isolated(model=MODEL, cwd="")
    # Matching the empty model and cwd gets past the first two checks, so the
    # tool set is what refuses -- an absent `tools` key is drift, not a pass.
    with pytest.raises(IsolationError, match="57 removed"):
        receipt.assert_isolated(model="", cwd="")


# --- the command --------------------------------------------------------------


def test_the_command_pins_the_model_and_streams() -> None:
    command = agy.build_command(prompt="hi", model=f"agy/{MODEL}", timeout=300.0)
    assert command[:3] == [agy.AGY_BIN, "--print", "hi"]
    assert command[command.index("--model") + 1] == MODEL, "the label must be stripped"
    assert command[command.index("--output-format") + 1] == "stream-json"
    assert "--disable-slash-commands" in command
    assert command[command.index("--print-timeout") + 1] == "300s"
    assert "--json-schema" not in command


def test_a_schema_is_passed_through_when_given() -> None:
    command = agy.build_command(prompt="hi", model=MODEL, json_schema='{"type":"object"}')
    assert command[command.index("--json-schema") + 1] == '{"type":"object"}'


def test_an_oversized_prompt_is_refused_before_the_os_sees_it() -> None:
    """`agy --print` takes its prompt in argv and offers no stdin fallback."""
    with pytest.raises(PromptTooLongError, match="argv ceiling"):
        agy.build_command(prompt="x" * (agy._ARGV_CEILING + 1), model=MODEL)


def test_the_namespace_round_trips() -> None:
    assert agy.bare_model(f"agy/{MODEL}") == MODEL
    assert agy.bare_model(MODEL) == MODEL
    assert agy.labelled_model(MODEL) == f"agy/{MODEL}"
    assert agy.labelled_model(f"agy/{MODEL}") == f"agy/{MODEL}"


def test_the_nullable_enum_is_the_shape_the_backend_accepts() -> None:
    """The other spelling is refused outright; see the docstring for the call."""
    assert agy.nullable_enum(("fit", "ledger")) == {
        "type": "string",
        "enum": ["fit", "ledger"],
        "nullable": True,
    }


# --- parsing ------------------------------------------------------------------


def test_a_plain_result_is_read() -> None:
    """With the `step_update` events a real stream actually carries in between."""
    receipt, result = agy.parse_events(
        stream(
            init_event(),
            {"event": "step_update", "step_update": {"step_index": 0, "state": "DONE"}},
            {"event": "step_update", "step_update": {"step_index": 1, "state": "ACTIVE"}},
            result_event(),
        ),
        model=MODEL,
    )
    assert result.text == "ready\n"
    assert result.model == f"agy/{MODEL}"
    assert (result.input_tokens, result.output_tokens) == (13742, 1)
    assert result.duration_ms == 2500
    assert result.session_id == "c-1"
    assert result.status == "SUCCESS"
    assert result.num_turns == 1
    assert result.cost_usd == 0.0, "a subscription call bills nothing, and says so"
    assert frozenset(receipt.tools) == agy.AGY_TOOLS


def test_structured_output_becomes_the_answer_and_the_prose_is_kept() -> None:
    """The whole reason this backend can run the arm that voided N9.

    516 calls were discarded there because the model answered in prose. Here the
    prose is still written -- it is what the agent does -- but the verdict
    arrives beside it in a field that cannot be malformed.
    """
    _, result = agy.parse_events(
        stream(
            init_event(),
            result_event(
                response="Long prose about visas.",
                structured_output={"procedure": "fit", "fire": True},
            ),
        ),
        model=MODEL,
    )
    assert result.text == '{"fire":true,"procedure":"fit"}', "stable key order"
    assert result.reasoning == "Long prose about visas."


def test_an_error_status_carrying_an_answer_is_recorded_not_discarded() -> None:
    """Measured 2026-08-21, and the reason `CliResult.status` exists.

    The agent answered, then reached for a file outside its sandbox and was
    refused by the CLI's own protection boundary. Raising here would have thrown
    away a complete verdict.
    """
    _, result = agy.parse_events(
        stream(
            init_event(),
            result_event(
                status="ERROR",
                response="",
                error="permission check failed for read_file",
                structured_output={"fire": True, "procedure": "timing"},
            ),
        ),
        model=MODEL,
    )
    assert result.status == "ERROR"
    assert json.loads(result.text) == {"fire": True, "procedure": "timing"}


def test_an_error_status_with_no_answer_raises() -> None:
    with pytest.raises(CliError, match="something broke"):
        agy.parse_events(
            stream(
                init_event(), result_event(status="ERROR", response=None, error="something broke")
            ),
            model=MODEL,
        )


def test_an_error_status_falls_back_to_the_response_text() -> None:
    with pytest.raises(CliError, match="half a sentence"):
        agy.parse_events(
            stream(init_event(), result_event(status="ERROR", response="half a sentence")),
            model=MODEL,
        )


def test_a_bare_status_with_no_error_field_still_names_itself() -> None:
    with pytest.raises(CliError, match="CANCELLED"):
        agy.parse_events(
            stream(init_event(), result_event(status="CANCELLED", response=None)),
            model=MODEL,
        )


def test_a_stream_with_no_result_event_is_infrastructure_failure() -> None:
    """The process died mid-call, which is not a model answering badly."""
    with pytest.raises(CliError, match="ended without a `result` event"):
        agy.parse_events(stream(init_event()), model=MODEL)


def test_a_non_object_result_payload_is_read_as_empty() -> None:
    with pytest.raises(CliError, match="no string `response`"):
        agy.parse_events(stream({"event": "result", "result": "nope"}), model=MODEL)


def test_a_result_without_a_response_string_raises() -> None:
    with pytest.raises(CliError, match="no string `response`"):
        agy.parse_events(stream(init_event(), result_event(response=None)), model=MODEL)


@pytest.mark.parametrize("line", ["", "   ", "not json at all", '"a bare string"', "[]"])
def test_junk_lines_are_skipped_rather_than_fatal(line: str) -> None:
    """A partial line is the CLI's business; the contract needed is `result`."""
    _, result = agy.parse_events([line, *stream(init_event(), result_event())], model=MODEL)
    assert result.text == "ready\n"


def test_a_missing_init_event_falls_back_to_the_requested_id() -> None:
    _, result = agy.parse_events(stream(result_event()), model=f"agy/{MODEL}")
    assert result.model == f"agy/{MODEL}"


def test_usage_fields_that_are_absent_or_unusable_read_as_zero() -> None:
    _, result = agy.parse_events(
        stream(init_event(), result_event(usage={"input_tokens": None, "output_tokens": "x"})),
        model=MODEL,
    )
    assert (result.input_tokens, result.output_tokens) == (0, 0)


# --- the error taxonomy -------------------------------------------------------


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("not logged in", AuthenticationError),
        ("Please sign in to continue", AuthenticationError),
        ("context length exceeded", PromptTooLongError),
        ("prompt too long", PromptTooLongError),
        ("RESOURCE_EXHAUSTED", RateLimitedError),
        ("429 too many requests", RateLimitedError),
        ("something else entirely", CliError),
    ],
)
def test_errors_map_onto_the_taxonomy_the_runner_already_catches(
    message: str, expected: type[Exception]
) -> None:
    """One retry policy across backends, which is the point of importing them.

    The markers are a superset written from documented shapes; **none has been
    observed in this repository's records.** They are here so a quota refusal is
    not scored as a model failure, and labelled so nobody later reads them as
    measured.
    """
    error = agy._classify(message)
    assert isinstance(error, expected)
    assert type(error) is expected


# --- the subprocess seam ------------------------------------------------------


def fake_run(stdout: str, returncode: int = 0, stderr: str = "") -> Any:
    def _run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], returncode, stdout, stderr)

    return _run


def test_run_returns_a_receipt_beside_the_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess, "run", fake_run("\n".join(stream(init_event(), result_event())))
    )
    receipt, result = agy.run("hi", model=MODEL, cwd="C:\\scratch")
    assert result.text == "ready\n"
    assert frozenset(receipt.tools) == agy.AGY_TOOLS


def test_run_with_no_stdout_is_classified(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exit 143 is a killed process, and it must not read as a model answer."""
    monkeypatch.setattr(subprocess, "run", fake_run("", returncode=143))
    with pytest.raises(CliError, match="no stdout"):
        agy.run("hi", model=MODEL, cwd="C:\\scratch")


def test_run_maps_a_quota_refusal_on_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", fake_run("", returncode=1, stderr="rate limit hit"))
    with pytest.raises(RateLimitedError):
        agy.run("hi", model=MODEL, cwd="C:\\scratch")


def test_preflight_asks_a_question_with_a_known_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    def _run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen["command"] = command
        return subprocess.CompletedProcess(
            command, 0, "\n".join(stream(init_event(), result_event())), ""
        )

    monkeypatch.setattr(subprocess, "run", _run)
    _, result = agy.preflight(model=MODEL, cwd="C:\\scratch")
    assert result.text.strip() == "ready"
    assert "ready" in seen["command"][2]
