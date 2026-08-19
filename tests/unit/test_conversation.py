"""The multi-turn transport and the isolation receipt.

No model is called. A fake process replays a scripted event stream, which is
enough to pin down everything that is ours: the wire format, the receipt, the
refusals, and what happens when the CLI dies mid-turn.

The one thing a fake cannot establish is that context actually carries across
turns. That is a behavioural claim about the CLI, it was verified against the
real thing, and it lives in ``notebook/2026-08-11-multi-turn-already-worked.md``
and in the ``llm``-marked integration test.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from decision_evals.providers.claude_code import (
    ISOLATION_FLAGS,
    AuthenticationError,
    CliError,
    Conversation,
    InitReceipt,
    IsolationError,
    build_command,
    parse_init_receipt,
    user_event,
)


def _result_event(text: str, *, input_tokens: int = 100) -> dict[str, Any]:
    return {
        "type": "result",
        "result": text,
        "modelUsage": {"claude-haiku-4-5-20251001": {"contextWindow": 200000}},
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": 12,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
        "total_cost_usd": 0.001,
        "duration_ms": 900,
        "session_id": "abc",
    }


_INIT_EVENT = {
    "type": "system",
    "subtype": "init",
    "tools": [],
    "skills": [],
    "agents": ["general-purpose", "Explore"],
    # A mapping, not a list -- checked live against claude-code 2.1.159 on
    # 2026-08-18, where every `system`/`init` event declares
    # `{"auto": "<cwd-keyed-path>"}`. A list-shaped fixture here would test a
    # shape the real CLI has never sent.
    "memory_paths": {"auto": "/tmp/whatever/memory"},
    "apiKeySource": "none",
    "model": "claude-haiku-4-5-20251001",
    "cwd": "/tmp/run",
    "session_id": "abc",
}


class FakeProcess:
    """Replays scripted stdout lines, one batch per turn written to stdin."""

    def __init__(self, batches: list[list[dict[str, Any] | str]]) -> None:
        self._batches = batches
        self._turn = 0
        self.stdin = io.StringIO()
        self.stdout = self
        self.stderr = io.StringIO()
        self.written: list[str] = []
        self.waited = False
        self._pending: list[str] = []

    # -- stdin ------------------------------------------------------------
    def write(self, text: str) -> int:
        self.written.append(text)
        if self._turn < len(self._batches):
            self._pending = [
                line if isinstance(line, str) else json.dumps(line)
                for line in self._batches[self._turn]
            ]
            self._turn += 1
        else:
            self._pending = []
        return len(text)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.closed_flag = True

    @property
    def closed(self) -> bool:
        return getattr(self, "closed_flag", False)

    # -- stdout -----------------------------------------------------------
    def __iter__(self):  # type: ignore[no-untyped-def]
        while self._pending:
            yield self._pending.pop(0) + "\n"

    def wait(self, timeout: float | None = None) -> int:
        self.waited = True
        return 0


def _conversation(batches: list[list[dict[str, Any] | str]]) -> tuple[Conversation, FakeProcess]:
    process = FakeProcess(batches)
    chat = Conversation(
        system_prompt="s",
        model="haiku",
        cwd="/tmp/run",
        spawn=lambda command, cwd: process,
    )
    # The fake serves as both pipes; wire stdin explicitly for clarity.
    process.stdin = process  # type: ignore[assignment]
    return chat, process


class TestStreamingCommand:
    def test_streaming_selects_the_stream_json_input_form(self) -> None:
        command = build_command(system_prompt="s", model="haiku", streaming=True)
        assert command[command.index("--input-format") + 1] == "stream-json"
        assert command[command.index("--output-format") + 1] == "stream-json"

    def test_verbose_is_required_for_the_init_receipt(self) -> None:
        assert "--verbose" in build_command(system_prompt="s", model="haiku", streaming=True)

    def test_the_single_shot_form_is_unchanged(self) -> None:
        command = build_command(system_prompt="s", model="haiku")
        assert command[command.index("--output-format") + 1] == "json"
        assert "--input-format" not in command

    def test_isolation_flags_survive_in_the_streaming_form(self) -> None:
        """The reason every command goes through one function."""
        command = build_command(system_prompt="s", model="haiku", streaming=True)
        for flag in ISOLATION_FLAGS:
            assert flag in command

    def test_a_json_schema_still_attaches(self) -> None:
        command = build_command(system_prompt="s", model="haiku", streaming=True, json_schema="{}")
        assert command[command.index("--json-schema") + 1] == "{}"


class TestUserEvent:
    def test_it_is_one_json_line_the_cli_accepts(self) -> None:
        event = json.loads(user_event("hello"))
        assert event["type"] == "user"
        assert event["message"]["content"][0]["text"] == "hello"

    def test_it_contains_no_newline_so_one_turn_is_one_line(self) -> None:
        assert "\n" not in user_event("a\nb")


class TestInitReceipt:
    def test_it_reads_the_declared_capabilities(self) -> None:
        receipt = parse_init_receipt(_INIT_EVENT)
        assert receipt.tools == ()
        assert receipt.agents == ("general-purpose", "Explore")
        assert receipt.api_key_source == "none"

    def test_an_isolated_receipt_passes(self) -> None:
        parse_init_receipt(_INIT_EVENT).assert_isolated()
        assert parse_init_receipt(_INIT_EVENT).tools_disabled

    def test_memory_paths_reads_the_real_mapping_shape(self) -> None:
        """The CLI declares this field as ``{"auto": path}``, not a list. A
        plain ``isinstance(value, list)`` check -- correct for every other
        field on this event -- silently read it as empty regardless of what
        the CLI said. Checked live against claude-code 2.1.159, 2026-08-18."""
        receipt = parse_init_receipt(_INIT_EVENT)
        assert receipt.memory_paths == ("/tmp/whatever/memory",)

    def test_a_list_shaped_memory_paths_still_parses(self) -> None:
        """Nothing pins the CLI's shape upstream; this branch is insurance in
        case it reverts to what an earlier version of this fixture assumed."""
        event = {**_INIT_EVENT, "memory_paths": ["/tmp/whatever/memory"]}
        assert parse_init_receipt(event).memory_paths == ("/tmp/whatever/memory",)

    def test_declared_memory_paths_do_not_fail_isolation(self) -> None:
        """Recorded, not gated -- checked live rather than assumed. A planted
        CLAUDE.md does not change this field at all under the isolation flag
        stack (`--setting-sources ""` blocks it from being read in the first
        place, per notebook/2026-08-10-isolation-canary.md), so there is no
        known value of this field that distinguishes a clean isolated call
        from a compromised one. Gating on it would refuse every run, not the
        contaminated ones."""
        receipt = parse_init_receipt(_INIT_EVENT)
        assert receipt.memory_paths
        receipt.assert_isolated()

    def test_declared_agents_do_not_fail_isolation(self) -> None:
        """They are latent under --tools "": declared, unreachable, tested inert."""
        assert parse_init_receipt(_INIT_EVENT).agents
        parse_init_receipt(_INIT_EVENT).assert_isolated()

    def test_loaded_tools_fail_isolation(self) -> None:
        event = {**_INIT_EVENT, "tools": ["Bash", "Read"]}
        with pytest.raises(IsolationError, match="loaded 2 tool"):
            parse_init_receipt(event).assert_isolated()

    def test_a_skill_picked_up_from_disk_fails_isolation(self) -> None:
        event = {**_INIT_EVENT, "skills": ["decision-making"]}
        with pytest.raises(IsolationError, match="loaded skill"):
            parse_init_receipt(event).assert_isolated()

    def test_missing_keys_become_empty_rather_than_raising(self) -> None:
        receipt = parse_init_receipt({"type": "system", "subtype": "init"})
        assert receipt == InitReceipt()
        receipt.assert_isolated()

    def test_a_non_list_field_is_ignored_rather_than_coerced(self) -> None:
        receipt = parse_init_receipt({**_INIT_EVENT, "tools": "Bash"})
        assert receipt.tools == ()

    def test_an_isolation_error_is_a_cli_error(self) -> None:
        """So a run loop that already stops on CliError does not need changing."""
        assert issubclass(IsolationError, CliError)


class TestConversation:
    def test_a_turn_returns_a_parsed_result(self) -> None:
        chat, _ = _conversation([[_INIT_EVENT, _result_event("hello")]])
        assert chat.send("hi").text == "hello"

    def test_the_receipt_is_captured_from_the_first_turn(self) -> None:
        chat, _ = _conversation([[_INIT_EVENT, _result_event("hello")]])
        chat.send("hi")
        chat.receipt.assert_isolated()

    def test_the_receipt_is_unavailable_before_the_first_turn(self) -> None:
        chat, _ = _conversation([[_INIT_EVENT, _result_event("x")]])
        with pytest.raises(CliError, match="no system/init event"):
            _ = chat.receipt

    def test_turns_are_counted(self) -> None:
        chat, _ = _conversation([[_INIT_EVENT, _result_event("one")], [_result_event("two")]])
        assert chat.turn_index == 0
        chat.send("a")
        chat.send("b")
        assert chat.turn_index == 2

    def test_each_turn_is_written_as_its_own_json_line(self) -> None:
        chat, process = _conversation([[_INIT_EVENT, _result_event("one")], [_result_event("two")]])
        chat.send("first")
        chat.send("second")
        texts = [json.loads(line)["message"]["content"][0]["text"] for line in process.written]
        assert texts == ["first", "second"]

    def test_non_json_verbose_lines_are_skipped(self) -> None:
        chat, _ = _conversation([["not json at all", _INIT_EVENT, _result_event("ok")]])
        assert chat.send("hi").text == "ok"

    def test_blank_lines_are_skipped(self) -> None:
        chat, _ = _conversation([["", _result_event("ok")]])
        assert chat.send("hi").text == "ok"

    def test_non_object_json_lines_are_skipped(self) -> None:
        chat, _ = _conversation([["[1, 2, 3]", _result_event("ok")]])
        assert chat.send("hi").text == "ok"

    def test_unrelated_event_types_are_ignored(self) -> None:
        chat, _ = _conversation([[{"type": "assistant", "message": {}}, _result_event("ok")]])
        assert chat.send("hi").text == "ok"

    def test_a_stream_that_ends_without_a_result_is_an_error(self) -> None:
        """The process died mid-turn; scoring that as an answer would be wrong."""
        chat, _ = _conversation([[_INIT_EVENT]])
        with pytest.raises(CliError, match="ended without a result on turn 1"):
            chat.send("hi")

    def test_an_authentication_failure_propagates(self) -> None:
        event = {"type": "result", "is_error": True, "result": "please authenticate"}
        chat, _ = _conversation([[event]])
        with pytest.raises(AuthenticationError):
            chat.send("hi")

    def test_it_closes_stdin_and_waits(self) -> None:
        chat, process = _conversation([[_result_event("ok")]])
        chat.send("hi")
        chat.close()
        assert process.waited

    def test_closing_twice_does_not_reclose_stdin(self) -> None:
        chat, process = _conversation([[_result_event("ok")]])
        chat.close()
        chat.close()
        assert process.waited

    def test_it_works_as_a_context_manager(self) -> None:
        process = FakeProcess([[_INIT_EVENT, _result_event("ok")]])
        process.stdin = process  # type: ignore[assignment]
        with Conversation(
            system_prompt="s", model="haiku", cwd="/tmp", spawn=lambda c, d: process
        ) as chat:
            assert chat.send("hi").text == "ok"
        assert process.waited

    def test_a_process_without_pipes_is_refused(self) -> None:
        class NoPipes:
            stdin = None
            stdout = None

        with pytest.raises(CliError, match="no stdin/stdout pipe"):
            Conversation(system_prompt="s", model="haiku", cwd="/tmp", spawn=lambda c, d: NoPipes())

    def test_the_spawned_command_is_the_streaming_form(self) -> None:
        captured: list[list[str]] = []

        def spawn(command: list[str], cwd: str) -> Any:
            captured.append(command)
            process = FakeProcess([[_result_event("ok")]])
            process.stdin = process  # type: ignore[assignment]
            return process

        Conversation(system_prompt="s", model="haiku", cwd="/tmp", spawn=spawn)
        assert "--input-format" in captured[0]


class TestSpawn:
    """The real process factory, exercised on a harmless command.

    Every other test injects a fake, which leaves the one function that actually
    touches ``subprocess`` untested. It is also the function carrying the
    ``encoding``/``errors`` settings that took 280 clean items to discover the
    need for, so "it is only three lines" is precisely the wrong reason to skip
    it.
    """

    def test_it_opens_three_pipes_and_decodes_as_utf8(self, tmp_path: Path) -> None:
        from decision_evals.providers.claude_code import _spawn

        # Raw UTF-8 bytes, not print(): a child print() encodes with *its* locale
        # codec, so it would emit the replacement character itself and the test
        # would pass while proving nothing about our reader. An em dash is the
        # case that matters -- undecodable in cp1252, which is what `text=True`
        # alone would use here. 0xE2 0x80 0x94 is an em dash in UTF-8, and 0x94
        # alone is undefined in cp1252, so this stops round-tripping the moment
        # `encoding="utf-8"` is lost.
        process = _spawn(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(bytes([226, 128, 148, 10]))",
            ],
            str(tmp_path),
        )
        try:
            assert process.stdin is not None
            assert process.stderr is not None
            assert process.stdout.readline().strip() == "—"
        finally:
            process.stdin.close()
            process.wait(timeout=30)
