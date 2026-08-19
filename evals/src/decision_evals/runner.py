"""The run loop.

Checkpointed and resumable, because rate limits rather than dollars are the
budget and a confirmation run may span several days. Records append to JSONL as
they complete, and a resumed run skips item/arm pairs already present. Crashing
halfway through therefore costs the current call and nothing else.

Two behaviours are non-obvious and deliberate.

**Preflight before item 1.** A revoked credential returns a well-formed error on
every call, so without a preflight the run records a few hundred authentication
failures that are indistinguishable, in the results, from a model that got
everything wrong. That is not hypothetical -- it happened during the harness
spike, with ``claude auth status`` reporting ``loggedIn: true`` throughout.

**Arms interleave per item.** Running all of ``off`` and then all of ``on``
would confound the arm with everything that changed in between, including the
served model and the quota state. The loop's outer dimension is the item.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from decision_evals.budget import BudgetLedger, estimate_cost_usd
from decision_evals.generators.generate import Item
from decision_evals.providers.claude_code import AuthenticationError, CliError, CliResult
from decision_evals.providers.claude_code import preflight as cli_preflight
from decision_evals.providers.claude_code import run as cli_run
from decision_evals.providers.openai_compatible import Endpoint
from decision_evals.providers.openai_compatible import run as openai_run
from decision_evals.scorers.answer import score_item
from decision_evals.solvers.arms import ArmPrompt, render_item
from decision_evals.telemetry import RECORD_SCHEMA_VERSION, NodeIdentity

#: How a call is made. Injected so the loop is testable without a model, and so
#: the dev arena can substitute a local backend without a second run loop.
CallFn = Callable[[str, str, bool], CliResult]


@dataclass(frozen=True)
class RunRecord:
    """One item, in one arm, with everything needed to analyse or re-check it.

    The trailing fields carry position in a run tree, named after the
    OpenTelemetry GenAI semantic conventions (see :mod:`decision_evals.telemetry`
    for why the names are pinned rather than imported).

    They default rather than being required, and the reason is not convenience.
    Every record in ``results/`` was written by a single ``claude -p`` call,
    which genuinely has no parent and no turn index — ``None`` is the true value
    for those runs, not a placeholder. ``schema_version`` defaults to 1 so an
    older record loads describing itself accurately instead of claiming to be
    something it is not.
    """

    item_id: str
    template_id: str
    arm: str
    model: str
    n_distractors: int
    position: str
    expected: str
    parsed: str | None
    parse_status: str
    correct: bool
    zero_cause: str | None
    cost_usd: float
    input_tokens: int
    output_tokens: int
    duration_ms: int
    response: str

    schema_version: int = 1
    conversation_id: str | None = None
    node_name: str | None = None
    node_id: str | None = None
    parent_node_id: str | None = None
    turn_index: int | None = None


class RunError(RuntimeError):
    """The run cannot proceed."""


def default_call(model: str, cwd: str) -> CallFn:
    """A :data:`CallFn` bound to the Claude Code backend."""

    def call(prompt: str, system_prompt: str, append: bool) -> CliResult:
        return cli_run(
            prompt,
            system_prompt=system_prompt,
            model=model,
            cwd=cwd,
            in_situ=append,
        )

    return call


def local_call(model: str, endpoint: Endpoint | None = None) -> CallFn:
    """A :data:`CallFn` bound to an OpenAI-compatible server.

    The substitution :data:`CallFn` was written for. No ``cwd``, because nothing
    here reads the filesystem; the contamination channel that replaces it is a
    Modelfile ``SYSTEM`` line, and
    :func:`~decision_evals.providers.openai_compatible.assert_isolated` is what
    checks it. Call that before a run rather than trusting a clean-looking
    response.

    Raises:
        RunError: The in-situ arm was requested. It has no local meaning, and
            the refusal is deliberate.
    """

    def call(prompt: str, system_prompt: str, append: bool) -> CliResult:
        if append:
            # In situ means `--append-system-prompt`: the skill arrives on top
            # of whatever Claude Code already puts in the system prompt, which
            # is the whole point of the arm -- it is the ecological control
            # against the isolated arms. A raw completion has no pre-existing
            # system prompt to append to, so running it here would send the
            # isolated prompt and label the record `in_situ`. That is not a
            # degraded measurement, it is two arms with one meaning, and the
            # scorer could not tell them apart afterwards.
            raise RunError(
                "the in-situ arm has no meaning against a raw completion endpoint: "
                "there is no existing system prompt to append to, so the call would "
                "be the isolated arm wearing another arm's label. Run it on the CLI "
                "backend, or drop it from the local grid and say which."
            )
        return openai_run(
            prompt,
            system_prompt=system_prompt,
            model=model,
            endpoint=endpoint,
        )

    return call


def completed_keys(checkpoint: Path) -> set[tuple[str, str]]:
    """Read ``(item_id, arm)`` pairs already recorded.

    Malformed trailing lines are ignored rather than fatal: a run killed
    mid-write leaves a partial final line, and refusing to resume because of it
    would throw away the whole checkpoint to avoid re-running one item.
    """
    if not checkpoint.exists():
        return set()
    done: set[tuple[str, str]] = set()
    for line in checkpoint.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            done.add((record["item_id"], record["arm"]))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return done


def run_arm(
    items: Sequence[Item],
    arm: ArmPrompt,
    *,
    model: str,
    checkpoint: Path,
    call: CallFn,
    ledger: BudgetLedger,
    expected_cost_usd: float | None = None,
    identity: NodeIdentity | None = None,
) -> list[RunRecord]:
    """Run one arm over a set of items, resuming from any checkpoint.

    Args:
        identity: Where these calls sit in a run tree. ``None`` for the
            single-call venue, which is what every run to date has been; the
            record's node columns then stay ``None``, which is the truth about
            such a run rather than a gap in it.
        expected_cost_usd: What to authorise per call. ``None`` -- the default --
            derives it from the length of the prompt actually about to be sent.
            The flat 0.05 this replaced under-counted a 100k-token casefile by
            roughly fivefold, and the ledger authorises *before* the call, so the
            shortfall would have surfaced as a run that stopped mid-stratum.
            Pass a number to pin it, which the budget tests do.

    Returns:
        The records produced *by this invocation*. Records already on disk from
        an earlier run are not re-read, because the caller reads the checkpoint
        for analysis anyway and returning them would make the count misleading.

    Raises:
        RunError: An authentication failure, or the budget was reached. Both
            stop the run rather than being scored, and both leave the checkpoint
            intact so the run resumes where it stopped.
    """
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    done = completed_keys(checkpoint)
    produced: list[RunRecord] = []

    with checkpoint.open("a", encoding="utf-8") as handle:
        for item in items:
            if (item.item_id, arm.arm) in done:
                continue

            # Rendered once. The string that was measured is the string that is
            # sent, because measuring one and sending another is how a length
            # experiment stops being about length.
            prompt = render_item(item)
            authorised = (
                expected_cost_usd
                if expected_cost_usd is not None
                else estimate_cost_usd(prompt_chars=len(prompt) + len(arm.system_prompt))
            )
            try:
                ledger.assert_can_afford(authorised)
            except Exception as exc:
                raise RunError(f"stopping before {item.item_id}: {exc}") from exc

            record = _run_one(item, arm, model=model, call=call, prompt=prompt, identity=identity)
            ledger = ledger.record(record.cost_usd)
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
            handle.flush()
            produced.append(record)
    return produced


def _run_one(
    item: Item,
    arm: ArmPrompt,
    *,
    model: str,
    call: CallFn,
    prompt: str,
    identity: NodeIdentity | None = None,
) -> RunRecord:
    try:
        result = call(prompt, arm.system_prompt, arm.append)
    except AuthenticationError as exc:
        raise RunError(
            f"authentication failed at {item.item_id}. The run is stopped rather than "
            f"scoring the failures: {exc}"
        ) from exc
    except CliError as exc:
        # A single call failing is an infrastructure zero, not a model failure,
        # and not a reason to abandon the run.
        score = score_item(item, "", infrastructure_error=True)
        return _record(
            item,
            arm,
            model=model,
            score=score,
            result=None,
            response=str(exc),
            identity=identity,
        )

    score = score_item(item, result.text)
    return _record(
        item,
        arm,
        model=result.model,
        score=score,
        result=result,
        response=result.text,
        identity=identity,
    )


def _record(
    item: Item,
    arm: ArmPrompt,
    *,
    model: str,
    score: object,
    result: CliResult | None,
    response: str,
    identity: NodeIdentity | None = None,
) -> RunRecord:
    from decision_evals.scorers.answer import Score

    assert isinstance(score, Score)
    return RunRecord(
        item_id=item.item_id,
        template_id=item.template_id,
        arm=arm.arm,
        model=model,
        n_distractors=item.n_distractors,
        position=item.position,
        expected=score.expected,
        parsed=score.parsed.value,
        parse_status=score.parsed.status,
        correct=score.correct,
        zero_cause=score.zero_cause,
        cost_usd=result.cost_usd if result else 0.0,
        input_tokens=result.input_tokens if result else 0,
        output_tokens=result.output_tokens if result else 0,
        duration_ms=result.duration_ms if result else 0,
        response=response,
        schema_version=RECORD_SCHEMA_VERSION,
        conversation_id=identity.conversation_id if identity else None,
        node_name=identity.node_name if identity else None,
        node_id=identity.node_id if identity else None,
        parent_node_id=identity.parent_node_id if identity else None,
        turn_index=identity.turn_index if identity else None,
    )


def preflight(*, model: str, cwd: str) -> None:
    """Fail loudly before item 1 if the credential does not work.

    Raises:
        RunError: The credential is unusable.
    """
    try:
        cli_preflight(model=model, cwd=cwd)
    except AuthenticationError as exc:
        raise RunError(
            f"preflight failed: {exc}\nNote that `claude auth status` reports "
            "loggedIn:true in this state, so it is not a useful check."
        ) from exc
    except CliError as exc:
        raise RunError(f"preflight failed: {exc}") from exc


def load_records(checkpoint: Path) -> list[RunRecord]:
    """Read a checkpoint back for analysis.

    A JSON parse failure on the *final* line is tolerated: a run killed
    mid-write leaves a partial line, and that is both expected and recoverable.
    Everything else is refused.

    A well-formed line that does not fit :class:`RunRecord` used to be skipped
    silently, which meant adding a column made every earlier record disappear
    and the analysis reported a run that had not happened. Since the next change
    to ``RunRecord`` is a set of stratum columns for the long corpus, that
    failure was queued rather than hypothetical.

    Raises:
        RunError: A record does not match the current schema, or a line is
            unparseable somewhere other than at the end of the file.
    """
    if not checkpoint.exists():
        return []

    lines = checkpoint.read_text(encoding="utf-8").splitlines()
    records: list[RunRecord] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            if number == len(lines):
                break  # a partial final write; the run was killed here
            raise RunError(
                f"{checkpoint}:{number} is not JSON and is not the last line, so it is "
                f"corruption rather than an interrupted write: {exc}"
            ) from exc
        try:
            records.append(RunRecord(**payload))
        except TypeError as exc:
            raise RunError(
                f"{checkpoint}:{number} does not match the current RunRecord schema: {exc}\n"
                "Move the checkpoint aside and re-run rather than analysing a subset."
            ) from exc
    return records


def iter_items(items: Iterable[Item], arms: Sequence[ArmPrompt]) -> list[tuple[Item, ArmPrompt]]:
    """Item-major ordering, so arms interleave rather than run in blocks.

    A run that completes all of ``off`` on Monday and all of ``on`` on Tuesday
    confounds the arm with everything that changed in between.
    """
    return [(item, arm) for item in items for arm in arms]
