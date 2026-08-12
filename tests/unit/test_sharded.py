"""Track A1's runner.

Two things here are refusals rather than features, and they carry most of the
tests: the full condition may never be built from joined shards, and no record
may carry a correctness verdict.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from decision_evals.corpora import ShardedInstruction
from decision_evals.providers.claude_code import CliResult
from decision_evals.sharded import (
    EXCLUDED_FAMILIES,
    FULL,
    FULL_INSTRUCTION_FIELD,
    SHARDED,
    ShardedRecord,
    ShardedRunError,
    append_record,
    completed_keys,
    full_instruction,
    load_records,
    pairable,
    plan_run,
    run_full,
    run_sharded,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _instruction(task: str = "math", **payload: Any) -> ShardedInstruction:
    return ShardedInstruction(
        task_id=f"sharded-{task}-1",
        task=task,
        shards=("a train leaves at noon", "it goes 60mph", "how far by 3pm?"),
        payload=payload,
    )


def _result(text: str, *, input_tokens: int = 100) -> CliResult:
    return CliResult(
        text=text,
        model="claude-haiku-4-5-20251001",
        cost_usd=0.001,
        input_tokens=input_tokens,
        output_tokens=20,
        duration_ms=500,
        session_id="s",
    )


class FakeConversation:
    """Returns a scripted result per turn, with a climbing prompt size."""

    def __init__(self, replies: list[str]) -> None:
        self._replies = replies
        self.sent: list[str] = []

    def send(self, text: str) -> CliResult:
        self.sent.append(text)
        index = len(self.sent)
        return _result(self._replies[index - 1], input_tokens=100 * index)


class TestFullInstruction:
    def test_it_reads_the_declared_field(self) -> None:
        item = _instruction("math", question="How far by 3pm?")
        assert full_instruction(item) == "How far by 3pm?"

    def test_actions_and_database_share_a_field(self) -> None:
        for task in ("actions", "database"):
            item = _instruction(task, fully_specified_question="which countries?")
            assert full_instruction(item) == "which countries?"

    def test_an_excluded_family_is_refused_with_its_reason(self) -> None:
        with pytest.raises(ShardedRunError, match="the input is a table"):
            full_instruction(_instruction("data2text", raw_table="..."))

    def test_the_refusal_names_the_trap_it_is_closing(self) -> None:
        """Joined shards are not the full instruction, and the error says so."""
        with pytest.raises(ShardedRunError, match="Joining the shards is NOT a substitute"):
            full_instruction(_instruction("summary", query="q"))

    def test_a_declared_family_missing_its_field_is_refused(self) -> None:
        with pytest.raises(ShardedRunError, match="no usable 'question'"):
            full_instruction(_instruction("math"))

    def test_a_blank_field_is_refused(self) -> None:
        with pytest.raises(ShardedRunError, match="no usable"):
            full_instruction(_instruction("math", question="   "))

    def test_a_non_string_field_is_refused(self) -> None:
        with pytest.raises(ShardedRunError, match="no usable"):
            full_instruction(_instruction("math", question=42))

    def test_there_is_no_fallback_to_joined_shards(self) -> None:
        """The property, stated directly: no input produces the joined shards."""
        item = _instruction("math", question="How far by 3pm?")
        assert full_instruction(item) != " ".join(item.shards)

    def test_every_excluded_family_carries_a_reason(self) -> None:
        assert set(EXCLUDED_FAMILIES) & set(FULL_INSTRUCTION_FIELD) == set()
        assert all(reason for reason in EXCLUDED_FAMILIES.values())


class TestPlan:
    def test_it_counts_pairs_calls_and_turns(self) -> None:
        items = [
            _instruction("math", question="q"),
            _instruction("database", fully_specified_question="q"),
            _instruction("data2text"),
        ]
        plan = plan_run(items)
        assert plan.n_pairs == 2
        assert plan.full_calls == 2
        assert plan.sharded_turns == 6  # two items, three shards each
        assert plan.total_model_calls == 8

    def test_excluded_families_are_reported_not_dropped_silently(self) -> None:
        plan = plan_run([_instruction("data2text"), _instruction("code")])
        assert plan.excluded == {"data2text": 1, "code": 1}
        assert "data2text (1)" in plan.describe()

    def test_repeats_multiply_the_cost(self) -> None:
        items = [_instruction("math", question="q")]
        assert plan_run(items, repeats=3).total_model_calls == 3 * plan_run(items).total_model_calls

    def test_repeats_below_one_are_refused(self) -> None:
        with pytest.raises(ValueError, match="repeats must be >= 1"):
            plan_run([], repeats=0)

    def test_describe_is_readable_without_exclusions(self) -> None:
        text = plan_run([_instruction("math", question="q")]).describe()
        assert "1 pairs" in text
        assert "excluded" not in text

    def test_pairable_preserves_input_order(self) -> None:
        items = [
            _instruction("data2text"),
            _instruction("math", question="q"),
            _instruction("database", fully_specified_question="q"),
        ]
        assert [item.task for item in pairable(items)] == ["math", "database"]


class TestRunFull:
    def test_it_sends_the_full_instruction_not_the_shards(self) -> None:
        sent: list[str] = []

        def call(prompt: str, system: str) -> CliResult:
            sent.append(prompt)
            return _result("42 miles")

        item = _instruction("math", question="How far by 3pm?")
        record = run_full(item, model="haiku", system_prompt="s", call=call, conversation_id="c1")
        assert sent == ["How far by 3pm?"]
        assert record.condition == FULL
        assert record.n_turns == 1
        assert record.final_response == "42 miles"

    def test_the_resolved_model_is_recorded_not_the_alias(self) -> None:
        record = run_full(
            _instruction("math", question="q"),
            model="haiku",
            system_prompt="s",
            call=lambda p, s: _result("x"),
            conversation_id="c1",
        )
        assert record.model == "claude-haiku-4-5-20251001"


class TestRunSharded:
    def test_each_shard_becomes_one_turn(self) -> None:
        item = _instruction("math", question="q")
        chat = FakeConversation(["ok", "ok", "180 miles"])
        record = run_sharded(
            item,
            model="haiku",
            system_prompt="s",
            conversation=chat,  # type: ignore[arg-type]
            conversation_id="c1",
        )
        assert chat.sent == list(item.shards)
        assert record.n_turns == 3
        assert record.condition == SHARDED

    def test_the_final_response_is_the_last_turn(self) -> None:
        record = run_sharded(
            _instruction("math", question="q"),
            model="haiku",
            system_prompt="s",
            conversation=FakeConversation(["a", "b", "180 miles"]),  # type: ignore[arg-type]
            conversation_id="c1",
        )
        assert record.final_response == "180 miles"

    def test_intermediate_turns_are_kept(self) -> None:
        """The paper's mechanism is a claim about early turns; discarding them
        would make it unrecoverable from our own records."""
        record = run_sharded(
            _instruction("math", question="q"),
            model="haiku",
            system_prompt="s",
            conversation=FakeConversation(["first", "second", "third"]),  # type: ignore[arg-type]
            conversation_id="c1",
        )
        assert record.turn_responses == ("first", "second", "third")

    def test_cost_and_duration_accumulate_across_turns(self) -> None:
        record = run_sharded(
            _instruction("math", question="q"),
            model="haiku",
            system_prompt="s",
            conversation=FakeConversation(["a", "b", "c"]),  # type: ignore[arg-type]
            conversation_id="c1",
        )
        assert record.cost_usd == pytest.approx(0.003)
        assert record.duration_ms == 1500

    def test_prompt_tokens_climbing_is_visible_on_the_record(self) -> None:
        record = run_sharded(
            _instruction("math", question="q"),
            model="haiku",
            system_prompt="s",
            conversation=FakeConversation(["a", "b", "c"]),  # type: ignore[arg-type]
            conversation_id="c1",
        )
        assert record.prompt_tokens_by_turn == (100, 200, 300)
        assert record.prompt_tokens_climb

    def test_a_non_climbing_prompt_is_detectable(self) -> None:
        """If this is ever false, the turns were not accumulating."""
        record = ShardedRecord(
            task_id="t",
            task="math",
            condition=SHARDED,
            model="m",
            n_turns=2,
            final_response="x",
            turn_responses=("a", "x"),
            prompt_tokens_by_turn=(300, 100),
            output_tokens_by_turn=(1, 1),
            cost_usd=0.0,
            duration_ms=0,
            conversation_id="c",
        )
        assert not record.prompt_tokens_climb


class TestNoScoring:
    """Rule 3, enforced by the schema rather than by discipline."""

    def test_the_record_has_no_correctness_field(self) -> None:
        fields = set(ShardedRecord.__dataclass_fields__)
        assert not fields & {"correct", "score", "admissible", "passed", "accuracy"}

    def test_the_record_keeps_the_raw_text(self) -> None:
        assert "final_response" in ShardedRecord.__dataclass_fields__
        assert "turn_responses" in ShardedRecord.__dataclass_fields__


class TestCheckpoint:
    def _record(self, task_id: str, condition: str) -> ShardedRecord:
        return ShardedRecord(
            task_id=task_id,
            task="math",
            condition=condition,
            model="m",
            n_turns=1,
            final_response="x",
            turn_responses=("x",),
            prompt_tokens_by_turn=(10,),
            output_tokens_by_turn=(2,),
            cost_usd=0.001,
            duration_ms=100,
            conversation_id="c",
        )

    def test_round_trips_through_a_checkpoint(self, tmp_path: Path) -> None:
        path = tmp_path / "a1.jsonl"
        append_record(path, self._record("t1", FULL))
        append_record(path, self._record("t1", SHARDED))
        loaded = load_records(path)
        assert [r.condition for r in loaded] == [FULL, SHARDED]
        assert loaded[0].turn_responses == ("x",)

    def test_completed_keys_are_item_and_condition(self, tmp_path: Path) -> None:
        path = tmp_path / "a1.jsonl"
        append_record(path, self._record("t1", FULL))
        assert completed_keys(path) == {("t1", FULL)}

    def test_an_absent_checkpoint_is_empty(self, tmp_path: Path) -> None:
        assert completed_keys(tmp_path / "nope.jsonl") == set()
        assert load_records(tmp_path / "nope.jsonl") == []

    def test_a_partial_final_line_is_tolerated(self, tmp_path: Path) -> None:
        """A run killed mid-write must still resume."""
        path = tmp_path / "a1.jsonl"
        append_record(path, self._record("t1", FULL))
        with path.open("a", encoding="utf-8") as handle:
            handle.write('{"task_id": "t2", "cond')
        assert len(load_records(path)) == 1
        assert completed_keys(path) == {("t1", FULL)}

    def test_corruption_in_the_middle_is_refused(self, tmp_path: Path) -> None:
        path = tmp_path / "a1.jsonl"
        append_record(path, self._record("t1", FULL))
        with path.open("a", encoding="utf-8") as handle:
            handle.write("not json\n")
        append_record(path, self._record("t2", FULL))
        with pytest.raises(ShardedRunError, match="corruption rather than an interrupted write"):
            load_records(path)

    def test_an_unknown_column_fails_loudly(self, tmp_path: Path) -> None:
        path = tmp_path / "a1.jsonl"
        path.write_text(json.dumps({"task_id": "t", "invented": 1}) + "\n", encoding="utf-8")
        with pytest.raises(ShardedRunError, match="does not match the current ShardedRecord"):
            load_records(path)

    def test_blank_lines_are_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "a1.jsonl"
        append_record(path, self._record("t1", FULL))
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n")
        assert len(load_records(path)) == 1


def test_the_declared_families_match_the_real_corpus() -> None:
    """Every family named here must exist upstream, and vice versa.

    Guards the map against the corpus moving underneath it -- a family renamed
    upstream would otherwise silently drop out of A1 with no error at all.
    """
    from decision_evals.corpora import TASKS

    assert set(FULL_INSTRUCTION_FIELD) | set(EXCLUDED_FAMILIES) == set(TASKS)


class TestActionsMessageList:
    """The `actions` family stores its full instruction as a nested message list.

    Uniform across all 105 records at the pinned commit, so unwrapping is a
    faithful read. The shape is asserted anyway: if upstream ever ships a
    multi-turn seed, taking [0][0] would silently redefine the full condition.
    """

    def test_a_single_user_message_is_unwrapped(self) -> None:
        item = _instruction(
            "actions",
            fully_specified_question=[[{"role": "user", "content": "compute the mean"}]],
        )
        assert full_instruction(item) == "compute the mean"

    def test_a_multi_turn_seed_is_refused_rather_than_truncated(self) -> None:
        item = _instruction(
            "actions",
            fully_specified_question=[
                [{"role": "user", "content": "a"}, {"role": "user", "content": "b"}]
            ],
        )
        with pytest.raises(ShardedRunError, match="silently redefine the full condition"):
            full_instruction(item)

    def test_several_outer_entries_are_refused(self) -> None:
        item = _instruction(
            "actions",
            fully_specified_question=[
                [{"role": "user", "content": "a"}],
                [{"role": "user", "content": "b"}],
            ],
        )
        with pytest.raises(ShardedRunError, match="not the single"):
            full_instruction(item)

    def test_a_non_user_role_is_refused(self) -> None:
        item = _instruction(
            "actions",
            fully_specified_question=[[{"role": "system", "content": "a"}]],
        )
        with pytest.raises(ShardedRunError, match="expected a user message"):
            full_instruction(item)

    def test_a_non_dict_message_is_refused(self) -> None:
        item = _instruction("actions", fully_specified_question=[["just a string"]])
        with pytest.raises(ShardedRunError, match="expected a user message"):
            full_instruction(item)

    def test_non_string_content_is_refused_downstream(self) -> None:
        item = _instruction("actions", fully_specified_question=[[{"role": "user", "content": 7}]])
        with pytest.raises(ShardedRunError, match="no usable"):
            full_instruction(item)

    def test_an_inner_non_list_is_refused(self) -> None:
        item = _instruction("actions", fully_specified_question=[{"role": "user"}])
        with pytest.raises(ShardedRunError, match="not the single"):
            full_instruction(item)
