"""Tests for the Claude Code CLI backend.

The most important test in this file is
:func:`test_isolation_flags_present_in_every_mode`. It is a regression guard for
a measured result: a planted ``CLAUDE.md`` is still injected when the system
prompt is fully replaced, and only ``--setting-sources ""`` blocks it. If a
future refactor makes that flag conditional, every arm silently inherits
whatever project memory sits above the working directory.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

import pytest

from decision_evals.providers import claude_code as cc


def _payload(**overrides: Any) -> dict[str, Any]:
    """A successful CLI payload, shaped like a real one."""
    base: dict[str, Any] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "api_error_status": None,
        "result": "42",
        "duration_ms": 2582,
        "session_id": "bcb39659",
        "total_cost_usd": 0.001014,
        "usage": {"input_tokens": 183, "output_tokens": 63},
        "modelUsage": {"claude-haiku-4-5-20251001": {"inputTokens": 634}},
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------
# build_command
# --------------------------------------------------------------------------


def test_isolated_arm_replaces_the_system_prompt() -> None:
    command = cc.build_command(system_prompt="be terse", model="haiku")
    assert "--system-prompt" in command
    assert "--append-system-prompt" not in command
    assert command[command.index("--system-prompt") + 1] == "be terse"


def test_in_situ_arm_appends_instead_of_replacing() -> None:
    command = cc.build_command(system_prompt="be terse", model="haiku", in_situ=True)
    assert "--append-system-prompt" in command
    assert "--system-prompt" not in command


@pytest.mark.parametrize("in_situ", [False, True])
def test_isolation_flags_present_in_every_mode(in_situ: bool) -> None:
    """Both arms must be isolated, and isolation does not come from the prompt.

    The in-situ arm keeps the CLI's built-in system prompt on purpose. That is
    an ecological-validity choice, not a relaxation of isolation -- it must
    still be sealed off from project memory, and this asserts it.
    """
    command = cc.build_command(system_prompt="s", model="haiku", in_situ=in_situ)
    for flag in cc.ISOLATION_FLAGS:
        assert flag in command

    # Named explicitly rather than relied on via the loop above: this is the
    # one flag measured to do the work.
    index = command.index("--setting-sources")
    assert command[index + 1] == ""


def test_json_schema_is_appended_only_when_given() -> None:
    without = cc.build_command(system_prompt="s", model="haiku")
    assert "--json-schema" not in without

    with_schema = cc.build_command(system_prompt="s", model="haiku", json_schema='{"a":1}')
    assert with_schema[with_schema.index("--json-schema") + 1] == '{"a":1}'


def test_command_requests_json_output_and_the_named_model() -> None:
    command = cc.build_command(system_prompt="s", model="sonnet")
    assert command[:2] == ["claude", "-p"]
    assert command[command.index("--model") + 1] == "sonnet"
    assert command[command.index("--output-format") + 1] == "json"


def test_the_command_line_stays_small_whatever_the_item_size() -> None:
    """The command line must not grow with the item, because it cannot.

    Windows caps a whole command line near 32 KB. The corpus this harness is
    being pointed at runs to 100k tokens per item -- roughly 400 KB -- so a
    prompt on argv is not a tight fit, it is an impossibility, and it would have
    failed as a ``CliError`` scored ``infrastructure`` for an entire stratum.
    """
    command = cc.build_command(system_prompt="s", model="haiku")
    assert sum(len(part) for part in command) < 1_000


def test_run_sends_a_long_prompt_on_stdin_and_none_of_it_on_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 640 KB item goes through stdin intact and leaves argv untouched."""
    seen: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen["command"] = command
        seen["input"] = kwargs.get("input")
        return subprocess.CompletedProcess(command, 0, json.dumps(_payload()), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    prompt = "MERIDIAN-CANARY " * 40_000
    cc.run(prompt, system_prompt="s", model="haiku", cwd=".")

    assert seen["input"] == prompt
    assert not any("MERIDIAN-CANARY" in part for part in seen["command"])
    assert sum(len(part) for part in seen["command"]) < 1_000


# --------------------------------------------------------------------------
# parse_result
# --------------------------------------------------------------------------


def test_parse_result_extracts_a_complete_run_record() -> None:
    result = cc.parse_result(_payload())
    assert result == cc.CliResult(
        text="42",
        model="claude-haiku-4-5-20251001",
        cost_usd=0.001014,
        input_tokens=183,
        output_tokens=63,
        duration_ms=2582,
        session_id="bcb39659",
    )


def test_parse_result_defaults_missing_usage_to_zero() -> None:
    result = cc.parse_result(_payload(usage=None, total_cost_usd=None, duration_ms=None))
    assert (result.input_tokens, result.output_tokens, result.duration_ms) == (0, 0, 0)
    assert result.cost_usd == 0.0


def test_cached_prompt_tokens_are_counted_as_prompt_tokens() -> None:
    """A measured defect, not a hypothetical one.

    A 380 KB casefile came back reporting ``input_tokens: 10`` while
    ``cache_creation_input_tokens`` carried the other 24,285 and the cost tracked
    the real figure. Reading ``input_tokens`` alone put ~10 in the token column of
    every long item -- the column ``docs/HARNESS_DISCLOSURE.md`` commits to
    reporting at p90/p99, wrong in exactly the stratum it describes.
    """
    result = cc.parse_result(
        _payload(
            usage={
                "input_tokens": 10,
                "cache_creation_input_tokens": 24_285,
                "cache_read_input_tokens": 0,
                "output_tokens": 69,
            }
        )
    )
    assert result.input_tokens == 24_295
    assert result.cache_creation_tokens == 24_285
    assert result.cache_read_tokens == 0


def test_a_repeat_served_from_cache_still_reports_the_whole_prompt() -> None:
    """The second repeat of an item arrives as ``cache_read`` and costs less.

    Cheaper is not smaller. The prompt the model read is identical, so the token
    column must be identical too, or the two repeats of one cell look like two
    different items.
    """
    result = cc.parse_result(
        _payload(
            usage={
                "input_tokens": 10,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 24_285,
                "output_tokens": 69,
            }
        )
    )
    assert result.input_tokens == 24_295
    assert result.cache_read_tokens == 24_285


def test_context_window_is_recorded_and_yields_a_fraction() -> None:
    result = cc.parse_result(
        _payload(
            usage={"input_tokens": 100_000, "output_tokens": 0},
            modelUsage={"claude-haiku-4-5-20251001": {"contextWindow": 200_000}},
        )
    )
    assert result.context_window == 200_000
    assert result.context_fraction == 0.5


def test_context_fraction_is_zero_when_no_window_is_reported() -> None:
    result = cc.parse_result(_payload())
    assert result.context_window == 0
    assert result.context_fraction == 0.0


def test_a_401_is_an_authentication_error_not_a_scoreable_failure() -> None:
    payload = _payload(
        is_error=True,
        api_error_status=401,
        result="Failed to authenticate. API Error: 401 OAuth access token has been revoked.",
    )
    with pytest.raises(cc.AuthenticationError, match="claude auth login"):
        cc.parse_result(payload)


def test_authentication_failure_detected_from_the_message_without_a_status() -> None:
    """The status field is not always populated, so the message is a fallback."""
    payload = _payload(is_error=True, api_error_status=None, result="Failed to authenticate.")
    with pytest.raises(cc.AuthenticationError):
        cc.parse_result(payload)


def test_an_overflowing_prompt_is_its_own_failure_not_infrastructure() -> None:
    """Observed at a nominal 350k tokens: the CLI returns "Prompt is too long".

    It has to be distinguishable from a flaky call. A prompt that overflows the
    window does so deterministically, on every retry, and it is an authoring
    defect in the item -- bucketing it as infrastructure hides a reproducible
    mistake behind a retry loop.
    """
    payload = _payload(is_error=True, api_error_status=None, result="Prompt is too long")
    with pytest.raises(cc.PromptTooLongError):
        cc.parse_result(payload)


def test_overflow_is_still_a_cli_error_for_callers_that_catch_broadly() -> None:
    payload = _payload(is_error=True, result="Prompt is too long")
    with pytest.raises(cc.CliError):
        cc.parse_result(payload)


def test_other_errors_are_plain_cli_errors() -> None:
    payload = _payload(is_error=True, api_error_status=500, result="upstream exploded")
    with pytest.raises(cc.CliError, match="upstream exploded") as caught:
        cc.parse_result(payload)
    assert not isinstance(caught.value, cc.AuthenticationError)


def test_an_error_with_no_message_still_raises() -> None:
    with pytest.raises(cc.CliError, match="unknown CLI error"):
        cc.parse_result(_payload(is_error=True, result=""))


@pytest.mark.parametrize("bad", [None, 42, ["not", "a", "string"]])
def test_a_non_string_result_is_rejected(bad: object) -> None:
    with pytest.raises(cc.CliError, match="no string `result` field"):
        cc.parse_result(_payload(result=bad))


@pytest.mark.parametrize("usage", [{}, None, {"a": {}, "b": {}}])
def test_the_resolved_model_must_be_unambiguous(usage: object) -> None:
    """A run record naming two models, or none, cannot be reproduced."""
    with pytest.raises(cc.CliError, match="exactly one resolved model"):
        cc.parse_result(_payload(modelUsage=usage))


# --------------------------------------------------------------------------
# run / preflight
# --------------------------------------------------------------------------


class _Completed:
    def __init__(self, stdout: str, stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_run_passes_the_scratch_cwd_through_and_parses_the_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> _Completed:
        seen["command"] = command
        seen["kwargs"] = kwargs
        return _Completed(json.dumps(_payload()))

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = cc.run("q", system_prompt="s", model="haiku", cwd="/scratch")

    assert result.text == "42"
    assert seen["kwargs"]["cwd"] == "/scratch"
    assert seen["kwargs"]["check"] is False
    assert seen["command"][0] == "claude"


def test_run_forwards_the_in_situ_and_schema_options(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_run(command: list[str], **_: Any) -> _Completed:
        seen["command"] = command
        return _Completed(json.dumps(_payload()))

    monkeypatch.setattr(subprocess, "run", fake_run)
    cc.run("q", system_prompt="s", model="haiku", cwd=".", in_situ=True, json_schema="{}")

    assert "--append-system-prompt" in seen["command"]
    assert "--json-schema" in seen["command"]


def test_non_json_output_reports_the_exit_code_and_both_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: _Completed("not json", stderr="boom", returncode=2),
    )
    with pytest.raises(cc.CliError, match="did not emit JSON"):
        cc.run("q", system_prompt="s", model="haiku", cwd=".")


def test_json_that_is_not_an_object_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Completed("[1, 2, 3]"))
    with pytest.raises(cc.CliError, match="non-object JSON"):
        cc.run("q", system_prompt="s", model="haiku", cwd=".")


def test_preflight_makes_one_call_and_surfaces_auth_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: Any) -> _Completed:
        calls.append(command)
        return _Completed(
            json.dumps(_payload(is_error=True, api_error_status=401, result="Failed to auth"))
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(cc.AuthenticationError):
        cc.preflight(model="haiku", cwd="/scratch")
    assert len(calls) == 1


def test_preflight_returns_the_result_when_the_credential_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _Completed(json.dumps(_payload(result="ready")))
    )
    assert cc.preflight(model="haiku", cwd="/scratch").text == "ready"


def test_the_subprocess_decodes_as_utf8_rather_than_the_locale_codec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bug that killed a run after 280 clean items.

    ``text=True`` alone decodes with the locale codec, which on Windows is
    cp1252. The first curly quote the model emitted raised UnicodeDecodeError
    inside subprocess's reader thread, where it could not propagate; ``run``
    returned normally with ``stdout`` set to None and the failure surfaced
    several frames away as a TypeError about NoneType.
    """
    seen: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> _Completed:
        seen.update(kwargs)
        return _Completed(json.dumps(_payload()))

    monkeypatch.setattr(subprocess, "run", fake_run)
    cc.run("q", system_prompt="s", model="haiku", cwd=".")

    assert seen["encoding"] == "utf-8"
    assert seen["errors"] == "replace"


def test_a_response_with_non_ascii_content_survives_the_round_trip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload()
    payload["result"] = "The window — 12 hours — “exceeds” the threshold."
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Completed(json.dumps(payload)))
    assert "—" in cc.run("q", system_prompt="s", model="haiku", cwd=".").text


def test_stdout_of_none_is_reported_rather_than_crashing_downstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Belt and braces: if a decode ever fails again, it fails here and says so."""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Completed(None, "boom", 1))  # type: ignore[arg-type]
    with pytest.raises(cc.CliError, match="produced no stdout"):
        cc.run("q", system_prompt="s", model="haiku", cwd=".")
