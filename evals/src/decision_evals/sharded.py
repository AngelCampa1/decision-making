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
from collections.abc import Callable, Iterable, Sequence
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

#: Which payload field carries the task's **standing context** -- the material an
#: answer is impossible without, which no shard ever states.
#:
#: This exists because the pilot ran without it and the omission was invisible.
#: ``database`` was asked *"which countries' tv channels are playing some cartoon
#: written by Todd Casey?"* with no schema, and answered *"I don't have access to
#: real-time TV broadcasting schedules"* -- a correct response to the question it
#: was actually asked, and not the text-to-SQL task the corpus is. ``actions``
#: was asked to use ``create_histogram`` with no function definitions and wrote
#: prose. Neither is a hard item; both were unanswerable.
#:
#: A map with no default, for the same reason as
#: :data:`FULL_INSTRUCTION_FIELD`. ``None`` means *declared to need none* --
#: ``math`` is a word problem and carries its own numbers -- which is a different
#: statement from a family nobody has considered, and the second one raises.
TASK_CONTEXT_FIELD: Final[dict[str, str | None]] = {
    "actions": "function",
    "database": "schema_sql",
    "math": None,
}

#: How each context field is introduced. Identical in both conditions, so it
#: cannot be a confound with delivery; it is a confound with the *published*
#: task, which is why it is stated here rather than composed at the call site.
TASK_CONTEXT_PREAMBLE: Final[dict[str, str]] = {
    "actions": "The following functions are available to you:",
    "database": "You are writing SQL against this database:",
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

#: A closing instruction both conditions may carry, verbatim.
#:
#: It exists because of a question that has no good answer once the data is in:
#: *does a final turn that asks a question instead of answering count as wrong?*
#: Judging that after the fact means classifying responses into "answer attempt"
#: and "not one", which is a scoring act on raw output and is exactly what
#: standing rule 3 forbids this module from doing.
#:
#: So it is moved before the run and made unconditional. Every conversation gets
#: the same closing turn whether or not the model was already answering, and the
#: full condition gets the same sentence appended to its single prompt. Nothing
#: is classified, the arms carry identical instructions, and a model that still
#: does not answer has produced a finding rather than an ambiguity.
#:
#: **It is not free, and the write-up must say which way it cuts.** The extra
#: turn is an extra generation, and only the sharded arm gets one -- the full
#: condition is one call by definition. So this hands the sharded arm a chance to
#: recover that the full arm never needed, which biases *against* the paper's
#: effect. Runs that use it and runs that do not are not comparable, which is why
#: the text is recorded on the record rather than assumed.
FINAL_TURN: Final = (
    "Give your final answer now, complete and self-contained, without asking any further questions."
)


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
        model: The **resolved** model id the CLI reports, never the alias asked
            for. ``haiku`` is not a version, and the two conditions of one pair
            must land in the same group when this column is grouped on.
        system_prompt: Verbatim, because the pilot's worst defect was in it and
            nothing in the record showed it. Forty ``actions`` and ``database``
            pairs ran with no function list and no schema, and every trace reads
            as a plausible answer to a question that was not the task. Stored in
            full rather than hashed: a hash proves two runs differ and cannot say
            what was missing.
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
    final_turn: str | None = None
    system_prompt: str | None = None

    @property
    def shard_turns(self) -> int:
        """Turns that carried a shard, excluding any closing instruction.

        ``n_turns`` counts generations, because generations are the unit of the
        quota and of the paper's mechanism. This one counts the instruction, so
        a run made with :data:`FINAL_TURN` and a run made without it can be
        compared on the same axis.
        """
        return self.n_turns - (1 if self.final_turn else 0)

    @property
    def prompt_tokens_climb(self) -> bool:
        """Whether the prompt grew monotonically — half the Track 0 falsifier.

        Trivially true for ``full``, which has one turn. Meaningful for
        ``sharded``: if it is false, the turns were not accumulating and the
        record is measuring something other than a conversation.
        """
        counts = self.prompt_tokens_by_turn
        return list(counts) == sorted(counts)


def final_responses_comparable(records: Iterable[ShardedRecord]) -> str | None:
    """Whether ``final_response`` means the same thing in both conditions.

    Returns ``None`` when it does, or a sentence saying why not.

    A scorer that reads ``final_response`` is comparing one arm's *whole answer*
    against the other arm's *last shard* unless a closing instruction was sent.
    ``full`` has one turn, so its final response is everything it said.
    A ``sharded`` conversation has four to ten, and without :data:`FINAL_TURN`
    the last of them answers a sub-question with no reason to restate what was
    said three turns earlier.

    This is not hypothetical. On 2026-08-12 a 50-pair ``actions`` run scored
    ``full`` 45/50 against ``sharded`` 23/50 on function naming, with discordance
    24-to-2 in the predicted direction — a clean replication, and entirely this
    defect. Crediting a name anywhere in the conversation moved ``sharded`` to
    47/50 and reversed the direction. Neither number was right: final-only
    penalises the arm for not repeating itself, anywhere rewards it for having
    more turns to say it in, and both are reading turn count, which is the
    independent variable.

    So the guard is on the run, not on the scorer's arithmetic. A run without a
    closing instruction cannot be scored on its final responses at all, and
    saying that in one line beats printing a plausible number.
    """
    offenders = sorted(
        {
            r.task_id
            for r in records
            if r.condition == SHARDED and r.n_turns > 1 and not r.final_turn
        }
    )
    if not offenders:
        return None
    shown = ", ".join(offenders[:3])
    more = f" (+{len(offenders) - 3} more)" if len(offenders) > 3 else ""
    return (
        f"{len(offenders)} sharded conversation(s) carry no closing instruction, so their "
        f"final response answers the last shard while full's answers the whole task. "
        f"Re-run with --final-turn. Offenders: {shown}{more}"
    )


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


def task_context(instruction: ShardedInstruction) -> str:
    """The standing context this task is unanswerable without, or ``""``.

    Belongs in the system prompt, identical in both conditions. It is not part
    of the manipulation -- delivery is -- so giving it to one condition and not
    the other, or to neither, changes the task rather than the treatment.

    Raises:
        ShardedRunError: The family is not in :data:`TASK_CONTEXT_FIELD`, or is
            declared to need context and does not carry it. Returning ``""`` on
            a missing field is how the pilot asked for SQL without a schema and
            recorded the refusal as data.
    """
    if instruction.task not in TASK_CONTEXT_FIELD:
        raise ShardedRunError(
            f"task family {instruction.task!r} has no declared standing context. "
            "Whether it needs one is a research decision; there is no default."
        )
    field_name = TASK_CONTEXT_FIELD[instruction.task]
    if field_name is None:
        return ""
    value = instruction.payload.get(field_name)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ShardedRunError(
            f"{instruction.task_id} is declared to need {field_name!r} and does not carry it; "
            "the item is unanswerable and must not be run"
        )
    body = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
    return f"{TASK_CONTEXT_PREAMBLE[instruction.task]}\n\n{body.strip()}"


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


def plan_run(
    instructions: Sequence[ShardedInstruction], *, repeats: int = 1, final_turn: bool = False
) -> RunPlan:
    """Price a run in calls and turns.

    Args:
        repeats: Repeats per item. Above 1 this is a reliability design, and
            :mod:`decision_evals.stats.reliability` prices how many are needed
            to estimate a spread rather than a mean.
        final_turn: Whether a closing instruction will be sent -- see
            :data:`FINAL_TURN`. It costs one extra generation per sharded
            conversation and nothing in the full condition, so the price of the
            run is not the same and the plan must say so before it is approved.

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
        sharded_turns=sum(item.n_turns + (1 if final_turn else 0) for item in usable) * repeats,
        excluded=excluded,
    )


#: How a single-shot call is made. Injected so the loop is testable without a model.
SingleCallFn = Callable[[str, str], CliResult]


def run_full(
    instruction: ShardedInstruction,
    *,
    system_prompt: str,
    call: SingleCallFn,
    conversation_id: str,
    final_turn: str | None = None,
) -> ShardedRecord:
    """Deliver the whole instruction in one call.

    There is no ``model`` parameter. The model is whatever ``call`` resolved,
    read back off the result -- an argument here would be a second source of
    truth for the same column, and the caller could set it to something the CLI
    did not actually run.

    Args:
        final_turn: A closing instruction -- see :data:`FINAL_TURN`. Appended to
            the prompt rather than sent separately, because this condition is one
            call by definition. Whatever is passed here must be passed to
            :func:`run_sharded` for the same pair or the arms differ by an
            instruction as well as by delivery.
    """
    prompt = full_instruction(instruction)
    if final_turn:
        prompt = f"{prompt}\n\n{final_turn}"
    result = call(prompt, system_prompt)
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
        final_turn=final_turn,
        system_prompt=system_prompt,
    )


def run_sharded(
    instruction: ShardedInstruction,
    *,
    system_prompt: str,
    conversation: Conversation,
    conversation_id: str,
    final_turn: str | None = None,
) -> ShardedRecord:
    """Deliver the shards one per turn down a live conversation.

    The caller owns the :class:`Conversation` so that its isolation receipt can
    be asserted before any turn is scored, and so a failure closes one
    conversation rather than the run.

    Args:
        final_turn: A closing instruction sent as one further turn after the last
            shard -- see :data:`FINAL_TURN`. Sent **unconditionally**, never only
            when the model appeared not to answer: deciding that it appeared not
            to answer is the classification this module refuses to make.

    Raises:
        ShardedRunError: The turns did not all resolve to the same model. A
            conversation that changed tier partway is not one observation, and
            it is invisible in the response text.
    """
    texts: list[str] = []
    prompts: list[int] = []
    outputs: list[int] = []
    models: list[str] = []
    cost = 0.0
    duration = 0
    turns = [*instruction.shards, final_turn] if final_turn else list(instruction.shards)
    for shard in turns:
        result = conversation.send(shard)
        texts.append(result.text)
        prompts.append(result.input_tokens)
        outputs.append(result.output_tokens)
        models.append(result.model)
        cost += result.cost_usd
        duration += result.duration_ms

    resolved = set(models)
    if len(resolved) > 1:
        raise ShardedRunError(
            f"{instruction.task_id}: the conversation resolved to more than one "
            f"model across its turns ({sorted(resolved)}). That is not one "
            "observation and the response text does not show it."
        )

    return ShardedRecord(
        task_id=instruction.task_id,
        task=instruction.task,
        condition=SHARDED,
        model=models[0] if models else "",
        n_turns=len(texts),
        final_response=texts[-1] if texts else "",
        turn_responses=tuple(texts),
        prompt_tokens_by_turn=tuple(prompts),
        output_tokens_by_turn=tuple(outputs),
        cost_usd=cost,
        duration_ms=duration,
        conversation_id=conversation_id,
        final_turn=final_turn,
        system_prompt=system_prompt,
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
