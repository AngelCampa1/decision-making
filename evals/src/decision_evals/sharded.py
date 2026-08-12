"""Track A1: the same instruction, delivered whole or delivered in pieces.

The comparison is paired. One instruction, two conditions:

* **full** — the fully-specified question, one ``claude -p`` call;
* **sharded** — the same task's shards, one per turn, through
  :class:`~decision_evals.providers.claude_code.Conversation`.

**There is no ``correct`` field on the record, and that is enforcement rather
than omission.** Standing rule 3 in the work order: *you may run experiments and
record raw outputs; you may not decide that a response is wrong.* Twenty-one of
twenty-one scored failures across three corpora were the answer key rather than
the model. So this module records what was said, and scoring is a separate act
by a party who can be blind to the key.

**The full condition comes from a named field, never from joined shards.** This
is the trap the module exists to close. Joining shards produces a bulleted
decomposition, not the original question — for one ``database`` record the full
question is *"which countries' tv channels are playing some cartoon written by
Todd Casey?"* against joined shards beginning *"tv channels airing cartoons
determine which countries…"*. Pairing those measures sharded delivery against a
third instruction **we wrote**, while calling it the published design. That is
the authoring failure the vendored corpus was adopted to avoid, one layer down.

Hence :data:`FULL_INSTRUCTION_FIELD`, which is a map and not a fallback. A family
that is not in it has no A1 pair and is excluded loudly.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Final

from decision_evals.corpora import ShardedInstruction
from decision_evals.providers.claude_code import CliResult, Conversation
from decision_evals.telemetry import RECORD_SCHEMA_VERSION

#: Which upstream field carries the fully-specified instruction, per task family.
#:
#: Deliberately a map with no default. ``data2text`` is absent because its input
#: is a table and there is no single instruction to state; ``code`` is absent
#: because the field is split across two source datasets *and* it is excluded
#: from A1 anyway for a Unix-only grader; ``summary`` is absent because it
#: carries both ``query`` and ``documents`` and deciding which constitutes the
#: instruction is a parameter, not a preference. Adding a family here is a
#: research decision and should arrive with its reasoning.
FULL_INSTRUCTION_FIELD: Final[dict[str, str]] = {
    "actions": "fully_specified_question",
    "database": "fully_specified_question",
    "math": "question",
}

#: Families deliberately left out, with the reason, so an unexplained item count
#: cannot appear downstream.
EXCLUDED_FAMILIES: Final[dict[str, str]] = {
    "code": "graded by executing tests under a Unix-only harness",
    "data2text": "the input is a table; there is no single full instruction",
    "summary": "carries both `query` and `documents`; which is the instruction is undecided",
}

FULL: Final = "full"
SHARDED: Final = "sharded"


class ShardedRunError(RuntimeError):
    """The A1 run cannot proceed."""


@dataclass(frozen=True)
class ShardedRecord:
    """One instruction in one condition. Raw outputs only — nothing scored.

    Attributes:
        final_response: What the model said last. For ``sharded`` this is the
            reply to the final shard, which is the answer the paper grades.
        turn_responses: Every turn's reply, in order. Length 1 for ``full``.
            Kept whole because the paper's mechanism — *anchor early, then
            over-weight the latest turn* — is a claim about intermediate turns,
            and it is unrecoverable if only the last is stored.
        prompt_tokens_by_turn: Real prompt size per turn, meaning
            ``input + cache_creation + cache_read``. The CLI's ``input_tokens``
            alone is the uncached remainder and reads 10 for a 380 KB prompt.
    """

    task_id: str
    task: str
    condition: str
    model: str
    n_turns: int
    final_response: str
    turn_responses: tuple[str, ...]
    prompt_tokens_by_turn: tuple[int, ...]
    output_tokens_by_turn: tuple[int, ...]
    cost_usd: float
    duration_ms: int
    conversation_id: str
    schema_version: int = RECORD_SCHEMA_VERSION
    error: str | None = None

    @property
    def prompt_tokens_climb(self) -> bool:
        """Whether the prompt grew monotonically — half the Track 0 falsifier.

        Trivially true for ``full``, which has one turn. Meaningful for
        ``sharded``: if it is false, the turns were not accumulating and the
        record is measuring something other than a conversation.
        """
        counts = self.prompt_tokens_by_turn
        return list(counts) == sorted(counts)


def full_instruction(instruction: ShardedInstruction) -> str:
    """The fully-specified question for this task.

    Raises:
        ShardedRunError: The family has no declared full-instruction field, or
            the record does not carry it. Both are refusals rather than
            fallbacks — a fallback here is precisely how joined shards would
            sneak in as the full condition.
    """
    field_name = FULL_INSTRUCTION_FIELD.get(instruction.task)
    if field_name is None:
        reason = EXCLUDED_FAMILIES.get(instruction.task, "no full-instruction field is declared")
        raise ShardedRunError(
            f"task family {instruction.task!r} has no A1 pair: {reason}. "
            "Joining the shards is NOT a substitute -- it yields a different instruction."
        )
    value = instruction.payload.get(field_name)
    if isinstance(value, list):
        value = _unwrap_message_list(instruction.task_id, field_name, value)
    if not isinstance(value, str) or not value.strip():
        raise ShardedRunError(
            f"{instruction.task_id} has no usable {field_name!r}; cannot build the full condition"
        )
    return value.strip()


def _unwrap_message_list(task_id: str, field_name: str, value: list[object]) -> str:
    """Extract the instruction from the ``actions`` family's nested message list.

    The ``actions`` records (BFCL) store ``fully_specified_question`` as
    ``[[{"role": "user", "content": "..."}]]`` rather than as a string. Measured
    across all 105 of them: outer length 1, inner length 1, role always
    ``user``, content always a string. So this is a faithful read of a uniform
    shape, not a guess at a ragged one.

    The shape is **asserted rather than assumed**, because that uniformity is a
    fact about one pinned commit. If upstream ever ships a multi-turn seed here,
    taking ``[0][0]`` would silently drop turns and quietly change what the
    "full" condition means -- so it refuses instead.

    Raises:
        ShardedRunError: The shape is anything other than a single user message.
    """
    if len(value) != 1 or not isinstance(value[0], list) or len(value[0]) != 1:
        raise ShardedRunError(
            f"{task_id}: {field_name!r} is a message list of shape "
            f"{[len(v) if isinstance(v, list) else '?' for v in value]}, not the single "
            "user message measured across all 105 `actions` records. Taking the first "
            "element would silently redefine the full condition; decide explicitly instead."
        )
    message = value[0][0]
    if not isinstance(message, dict) or message.get("role") != "user":
        raise ShardedRunError(
            f"{task_id}: {field_name!r} holds a {type(message).__name__} with role "
            f"{message.get('role') if isinstance(message, dict) else '?'!r}, expected a user message"
        )
    content = message.get("content")
    return content if isinstance(content, str) else ""


def pairable(instructions: Sequence[ShardedInstruction]) -> list[ShardedInstruction]:
    """Those instructions that can form an A1 pair, in input order."""
    return [item for item in instructions if item.task in FULL_INSTRUCTION_FIELD]


@dataclass(frozen=True)
class RunPlan:
    """What a run will cost, in calls, before any of it is made.

    Standing rule 5 in the work order: say what a run will cost in calls before
    starting it. The budget is quota and wall-clock, so calls and turns are the
    units that matter, not dollars.
    """

    n_pairs: int
    full_calls: int
    sharded_conversations: int
    sharded_turns: int
    excluded: dict[str, int] = field(default_factory=dict)

    @property
    def total_model_calls(self) -> int:
        """Turns are calls. A 6-shard conversation costs six generations."""
        return self.full_calls + self.sharded_turns

    def describe(self) -> str:
        """One paragraph a human can approve or refuse."""
        lines = [
            f"{self.n_pairs} pairs: {self.full_calls} single-turn calls plus "
            f"{self.sharded_conversations} conversations totalling {self.sharded_turns} turns.",
            f"{self.total_model_calls} model generations in all.",
        ]
        if self.excluded:
            dropped = ", ".join(
                f"{name} ({count})" for name, count in sorted(self.excluded.items())
            )
            lines.append(f"excluded: {dropped}")
        return "\n".join(lines)


def plan_run(instructions: Sequence[ShardedInstruction], *, repeats: int = 1) -> RunPlan:
    """Price a run in calls and turns.

    Args:
        repeats: Repeats per item. Above 1 this is a reliability design, and
            :mod:`decision_evals.stats.reliability` prices how many are needed
            to estimate a spread rather than a mean.

    Raises:
        ValueError: ``repeats`` below 1.
    """
    if repeats < 1:
        raise ValueError(f"repeats must be >= 1, got {repeats}")
    usable = pairable(instructions)
    excluded: dict[str, int] = {}
    for item in instructions:
        if item.task not in FULL_INSTRUCTION_FIELD:
            excluded[item.task] = excluded.get(item.task, 0) + 1
    return RunPlan(
        n_pairs=len(usable),
        full_calls=len(usable) * repeats,
        sharded_conversations=len(usable) * repeats,
        sharded_turns=sum(item.n_turns for item in usable) * repeats,
        excluded=excluded,
    )


#: How a single-shot call is made. Injected so the loop is testable without a model.
SingleCallFn = Callable[[str, str], CliResult]


def run_full(
    instruction: ShardedInstruction,
    *,
    model: str,
    system_prompt: str,
    call: SingleCallFn,
    conversation_id: str,
) -> ShardedRecord:
    """Deliver the whole instruction in one call."""
    result = call(full_instruction(instruction), system_prompt)
    return ShardedRecord(
        task_id=instruction.task_id,
        task=instruction.task,
        condition=FULL,
        model=result.model,
        n_turns=1,
        final_response=result.text,
        turn_responses=(result.text,),
        prompt_tokens_by_turn=(result.input_tokens,),
        output_tokens_by_turn=(result.output_tokens,),
        cost_usd=result.cost_usd,
        duration_ms=result.duration_ms,
        conversation_id=conversation_id,
    )


def run_sharded(
    instruction: ShardedInstruction,
    *,
    model: str,
    system_prompt: str,
    conversation: Conversation,
    conversation_id: str,
) -> ShardedRecord:
    """Deliver the shards one per turn down a live conversation.

    The caller owns the :class:`Conversation` so that its isolation receipt can
    be asserted before any turn is scored, and so a failure closes one
    conversation rather than the run.
    """
    texts: list[str] = []
    prompts: list[int] = []
    outputs: list[int] = []
    cost = 0.0
    duration = 0
    for shard in instruction.shards:
        result = conversation.send(shard)
        texts.append(result.text)
        prompts.append(result.input_tokens)
        outputs.append(result.output_tokens)
        cost += result.cost_usd
        duration += result.duration_ms

    return ShardedRecord(
        task_id=instruction.task_id,
        task=instruction.task,
        condition=SHARDED,
        model=model,
        n_turns=len(texts),
        final_response=texts[-1] if texts else "",
        turn_responses=tuple(texts),
        prompt_tokens_by_turn=tuple(prompts),
        output_tokens_by_turn=tuple(outputs),
        cost_usd=cost,
        duration_ms=duration,
        conversation_id=conversation_id,
    )


def completed_keys(checkpoint: Path) -> set[tuple[str, str]]:
    """``(task_id, condition)`` pairs already recorded, for resuming."""
    if not checkpoint.exists():
        return set()
    done: set[tuple[str, str]] = set()
    for line in checkpoint.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            done.add((record["task_id"], record["condition"]))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return done


def append_record(checkpoint: Path, record: ShardedRecord) -> None:
    """Write one record and flush, so a killed run loses one item at most."""
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    with checkpoint.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        handle.flush()


def load_records(checkpoint: Path) -> list[ShardedRecord]:
    """Read a checkpoint back.

    Raises:
        ShardedRunError: A line does not match the current schema, or is
            unparseable somewhere other than at the end of the file. Silently
            skipping a mismatched record is how adding a column makes an earlier
            run disappear from its own analysis.
    """
    if not checkpoint.exists():
        return []
    lines = checkpoint.read_text(encoding="utf-8").splitlines()
    records: list[ShardedRecord] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            if number == len(lines):
                break  # a partial final write; the run was killed here
            raise ShardedRunError(
                f"{checkpoint}:{number} is not JSON and is not the last line, so it is "
                f"corruption rather than an interrupted write: {exc}"
            ) from exc
        for key in ("turn_responses", "prompt_tokens_by_turn", "output_tokens_by_turn"):
            if key in payload:
                payload[key] = tuple(payload[key])
        try:
            records.append(ShardedRecord(**payload))
        except TypeError as exc:
            raise ShardedRunError(
                f"{checkpoint}:{number} does not match the current ShardedRecord schema: {exc}"
            ) from exc
    return records
