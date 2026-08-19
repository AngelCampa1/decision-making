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
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

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


#: Model prefixes measured to return *different text* when calls run
#: concurrently, and therefore refused above ``concurrency=1``.
#:
#: ``ollama`` is here because it was measured, not because it is suspected. On
#: 2026-08-19 the registered falsifier ran 40 items three times on
#: ``ollama/qwen3:4b`` at ``temperature=0``: two serial passes agreed on the
#: exact text of 31 of 40, and the concurrent pass at ``concurrency=8`` agreed
#: on **0 of 40**, with the parsed answer itself moving on 6 of 39. The prompts
#: were byte-identical -- ``input_tokens`` matched exactly across all three
#: arms -- so the request is not what changed. A server that batches concurrent
#: requests changes the matrix shapes it multiplies, which changes the
#: floating-point reduction order, which flips a token, which cascades through a
#: reasoning chain thousands of tokens long.
#:
#: **This is a statement about a venue, not about concurrency.** Each backend
#: has to be measured before it is trusted, which is why this is a register of
#: prefixes rather than a flat refusal. It may only shrink, and it shrinks by
#: running the falsifier, not by argument:
#: ``notebook/2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md``.
CONCURRENCY_UNSAFE: Final[frozenset[str]] = frozenset({"ollama/"})


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
    concurrency: int = 1,
    measuring_concurrency: bool = False,
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
        concurrency: How many calls may be in flight. ``1`` -- the default --
            is the sequential loop every published run used, unchanged.
        measuring_concurrency: Permit ``concurrency > 1`` on a model listed in
            :data:`CONCURRENCY_UNSAFE`. Only the falsifier that populates that
            register may pass it: the register exists because such a run was
            measured to change every answer, and the one job that still needs to
            make those calls is the job that re-measures it.

    **Threads rather than asyncio, and it is a real choice.** A call is a
    subprocess or an HTTP request; both spend their whole life blocked on I/O
    with the GIL released, so a bounded pool saturates the backend exactly as
    well as an event loop would. Going async would mean an async :data:`CallFn`
    and an async rewrite of both providers, which is a large change to two
    modules at a 100% floor in exchange for nothing measurable. The same
    argument retires Ray and Dask one step earlier: there is no CPU work here to
    distribute.

    **Three things concurrency changes, stated because a checkpoint would not
    say.** Records are written in *completion* order rather than item order, so
    two runs over the same items need not produce byte-identical files; nothing
    downstream reads a checkpoint positionally, and resume is keyed on
    ``(item_id, arm)``. The budget is authorised before dispatch, so up to
    ``concurrency`` calls may be authorised against a ledger that does not yet
    know what the in-flight ones cost -- the overshoot is bounded by the window,
    and the ledger is a burn meter rather than a spend cap. And when a run
    aborts, results still in flight are discarded rather than written, so resume
    re-runs them; that is what makes the abort safe rather than partial.

    **It was measured, and on one backend the answer is that it does.** The
    prediction above was registered before this code existed; the run is in
    ``notebook/2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md``.
    Serial-against-serial agreed on the exact text of 31 of 40 items and
    concurrent-against-serial on 0 of 40, so :data:`CONCURRENCY_UNSAFE` refuses
    the combination rather than leaving the finding written down somewhere. Every
    other backend is unmeasured, which is a different thing from safe.

    Returns:
        The records produced *by this invocation*. Records already on disk from
        an earlier run are not re-read, because the caller reads the checkpoint
        for analysis anyway and returning them would make the count misleading.

    Raises:
        RunError: An authentication failure, the budget was reached, or
            ``concurrency`` was not positive. The first two stop the run rather
            than being scored, and both leave the checkpoint intact so the run
            resumes where it stopped.
    """
    if concurrency < 1:
        raise RunError(f"concurrency must be at least 1, got {concurrency}")

    unsafe = sorted(prefix for prefix in CONCURRENCY_UNSAFE if model.startswith(prefix))
    if concurrency > 1 and unsafe and not measuring_concurrency:
        raise RunError(
            f"{model} is measured to return different text under concurrency, so "
            f"concurrency={concurrency} would produce records that cannot be compared "
            f"with anything already on disk. Two serial passes agreed on 31 of 40 "
            f"items; the concurrent pass agreed on 0 of 40. Run it serially, or pass "
            f"measuring_concurrency=True if you are the falsifier re-measuring it."
        )

    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    done = completed_keys(checkpoint)
    pending = [item for item in items if (item.item_id, arm.arm) not in done]
    produced: list[RunRecord] = []

    def authorise(item: Item) -> str:
        """Charge the ledger for one item and return the prompt to send."""
        # Rendered once. The string that was measured is the string that is
        # sent, because measuring one and sending another is how a length
        # experiment stops being about length.
        prompt = render_item(item)
        amount = (
            expected_cost_usd
            if expected_cost_usd is not None
            else estimate_cost_usd(prompt_chars=len(prompt) + len(arm.system_prompt))
        )
        try:
            ledger.assert_can_afford(amount)
        except Exception as exc:
            raise RunError(f"stopping before {item.item_id}: {exc}") from exc
        return prompt

    with (
        checkpoint.open("a", encoding="utf-8") as handle,
        ThreadPoolExecutor(max_workers=concurrency) as pool,
    ):
        submitted = 0
        in_flight: set[Future[RunRecord]] = set()

        while submitted < len(pending) or in_flight:
            while len(in_flight) < concurrency and submitted < len(pending):
                item = pending[submitted]
                prompt = authorise(item)
                in_flight.add(
                    pool.submit(
                        _run_one,
                        item,
                        arm,
                        model=model,
                        call=call,
                        prompt=prompt,
                        identity=identity,
                    )
                )
                submitted += 1

            finished, in_flight = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in finished:
                # One writer, on this thread. Appending to one handle from
                # several threads interleaves partial lines, and a corrupt
                # interior line is the one thing `load_records` refuses.
                record = future.result()
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
