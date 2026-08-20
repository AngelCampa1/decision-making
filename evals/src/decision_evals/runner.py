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
import random
import threading
import time
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

from decision_evals.budget import BudgetLedger, estimate_cost_usd
from decision_evals.generators.generate import Item
from decision_evals.providers.claude_code import (
    AuthenticationError,
    CliError,
    CliResult,
    RateLimitedError,
)
from decision_evals.providers.claude_code import preflight as cli_preflight
from decision_evals.providers.claude_code import run as cli_run
from decision_evals.providers.openai_compatible import Endpoint, ollama
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
#: ``ollama`` is here because it was measured twice, not because it is
#: suspected. The registered falsifier ran 40 items three ways on
#: ``ollama/qwen3:4b`` at ``temperature=0``, and then again: within a single
#: process invocation, a serial repeat agreed with serial on the exact text of
#: 31 of 40 and then 13 of 40, while the concurrent pass at ``concurrency=8``
#: agreed on **0 of 40 both times**. Prompts were byte-identical, so the request
#: is not what changed. A server that batches concurrent requests multiplies
#: different matrix shapes, which changes the floating-point reduction order,
#: which flips a token, which cascades through a reasoning chain thousands of
#: tokens long.
#:
#: **Read the scope carefully, because the replication narrowed it.** The claim
#: is about text, within one invocation. Cross-invocation serial agreement is
#: also low and unstable -- the two available pairs give 0 of 40 and 7 of 40 --
#: so serial is not a way to make this backend reproducible either, and no two
#: runs on it may be compared by text. On the parsed answer -- the
#: quantity that reaches a published number -- the concurrent arms sit at 0.850
#: and 0.825 against a cross-invocation serial baseline of 0.875, which at n=40
#: separates nothing. So this refusal rests on the prose result, and it is a
#: precaution rather than a demonstration that concurrency moves decisions.
#:
#: It is also a statement about a venue rather than about concurrency, which is
#: why it is a register of prefixes and not a flat refusal. It may only shrink,
#: and it shrinks by measurement:
#: ``notebook/2026-08-19-the-replication-moved-the-floor-and-found-a-worse-problem.md``.
CONCURRENCY_UNSAFE: Final[frozenset[str]] = frozenset({"ollama/"})


@dataclass(frozen=True, slots=True)
class Backoff:
    """How long to wait after a rate limit, and how many times to try.

    Full jitter, not equal jitter: the delay is drawn uniformly from
    ``[0, min(max_delay, base_delay * 2 ** attempt)]``. Several workers hit the
    same wall in the same instant, and a deterministic backoff sends all of them
    back at the same instant too. Full jitter is the variant that spreads them.

    Attributes:
        attempts: Tries per call, including the first. ``1`` disables retrying.
        base_delay: Seconds before the first retry.
        max_delay: Ceiling on one wait.
        breaker_trips: Consecutive rate limits, across the whole run and with no
            successful call between them, after which the run aborts instead of
            waiting again. A wall that does not move is a quota window that has
            closed, and the run is checkpointed, so stopping and resuming later
            costs nothing and burning the remaining items costs the items.
    """

    attempts: int = 5
    base_delay: float = 2.0
    max_delay: float = 60.0
    breaker_trips: int = 12

    def __post_init__(self) -> None:
        """Refuse a schedule that cannot be run.

        ``attempts=0`` reads as "do not retry" and means "do not call", which is
        a whole arm silently producing nothing. A negative delay reaches
        ``random.uniform`` and comes back as a negative sleep.
        """
        if self.attempts < 1:
            raise ValueError(
                f"attempts is {self.attempts}. Every call is made at least once, so 1 is the "
                "floor and 1 is what disables retrying."
            )
        if self.base_delay < 0 or self.max_delay < 0:
            raise ValueError(
                f"a delay cannot be negative: base_delay={self.base_delay}, "
                f"max_delay={self.max_delay}."
            )
        if self.breaker_trips < 1:
            raise ValueError(
                f"breaker_trips is {self.breaker_trips}. A breaker that trips before the first "
                "rate limit stops every run on the first wall."
            )


#: The schedule a run uses when the caller names none.
DEFAULT_BACKOFF: Final[Backoff] = Backoff()


class Backpressure:
    """A run-wide pause, tripped by a rate limit and released after a wait.

    **Per-call retry is not enough once the pool has several calls in flight.**
    Concurrency does not create quota. When the window closes, every worker gets
    the same refusal at the same moment, and retrying independently sends the
    same burst back at the same wall -- so the pause has to be shared. A worker
    that trips this one holds every other worker at :meth:`wait` for the
    duration, and the pool stops issuing calls it already knows will fail.

    ``sleep``, ``uniform`` and the clock are injected so the tests exercise the
    schedule rather than spending the schedule.
    """

    def __init__(
        self,
        policy: Backoff | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
        uniform: Callable[[float, float], float] = random.uniform,
    ) -> None:
        self.policy = policy or DEFAULT_BACKOFF
        self._sleep = sleep
        self._uniform = uniform
        self._lock = threading.Lock()
        self._open = threading.Event()
        self._open.set()
        self._consecutive = 0
        self.trips = 0
        self.slept = 0.0

    def wait(self) -> None:
        """Block while another worker is serving a pause."""
        self._open.wait()

    def succeeded(self) -> None:
        """A call got through, so the run is not against the wall any more."""
        with self._lock:
            self._consecutive = 0

    def trip(self, attempt: int, retry_after: float | None = None) -> float:
        """Pause the whole run, and return how long this worker waited.

        Args:
            attempt: Which retry this is, from zero.
            retry_after: What the server asked for, when it asked. Used as the
                ceiling-free delay rather than the computed one, because a
                number the server sent beats a number we guessed.

        Raises:
            RunError: The breaker has tripped ``breaker_trips`` times with no
                successful call between them.
        """
        with self._lock:
            self._consecutive += 1
            self.trips += 1
            consecutive = self._consecutive
            if consecutive > self.policy.breaker_trips:
                raise RunError(
                    f"{consecutive - 1} consecutive rate-limited call(s) with none getting "
                    "through, so the run is stopping rather than waiting again. The window "
                    "has closed rather than narrowed; the checkpoint holds everything "
                    "collected so far and resuming later re-runs nothing."
                )
            ceiling = min(self.policy.max_delay, self.policy.base_delay * 2**attempt)
            delay = retry_after if retry_after is not None else self._uniform(0.0, ceiling)
            self._open.clear()

        try:
            self._sleep(delay)
        finally:
            self._open.set()
        with self._lock:
            self.slept += delay
        return delay


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

    label = (endpoint or ollama()).label
    if not model.lower().startswith(f"{label.lower()}/"):
        # `build_payload` strips a `label/` prefix and tolerates a bare name,
        # and `parse_completion` stamps the label back on, so `qwen3:4b` is a
        # working request whose records claim to be `ollama/qwen3:4b`. That is
        # exactly the string `CONCURRENCY_UNSAFE` matches on, so a bare name
        # un-registers the venue by typo -- and `qwen3:4b` is what `ollama
        # list` prints, so it is the natural thing to type. The register is
        # meant to shrink by measurement.
        raise RunError(
            f"model {model!r} does not name its venue. Use {label}/{model!r} so the "
            f"record, the arena gate and the concurrency register all see which "
            f"server produced it."
        )

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
    backoff: Backoff | None = None,
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
        backoff: How rate limits are waited out, shared across every worker.
            ``None`` uses :data:`DEFAULT_BACKOFF`. Concurrency does not create
            quota, so a closed window otherwise turns into ``concurrency``
            infrastructure zeros per batch as fast as the pool can produce them.
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
    ``(item_id, arm)``. The budget is *reserved* at dispatch and released when
    the record arrives, so a window cannot authorise more than the limit allows.
    That is a correction, not a design note: charging only on completion meant
    every call in one window read the same balance, and six items at $0.02
    against a $0.021 limit ran all six while the serial path stopped after one.
    And when a run aborts, the batch that contained the failure is drained
    first, so calls that already succeeded and were already paid for are kept;
    only results still in flight are discarded, and resume re-runs those.

    **It was measured twice, and the second run narrowed what the first one
    licensed.** The prediction above was registered before this code existed.
    Within one invocation, concurrent-against-serial agreed on the exact text of
    0 of 40 items both times, against a serial repeat of 31 of 40 and 13 of 40,
    so :data:`CONCURRENCY_UNSAFE` refuses the combination. The sharpest form of
    that comparison is between *adjacent* arms, which controls for elapsed time:
    at the same ~23 minute separation, serial-vs-serial is 0.775 and 0.325 while
    serial-vs-concurrent is 0.000 twice. But cross-invocation serial agreement is
    itself only 0 of 40 and 7 of 40, so serial reproducibility is not a property
    this backend has either, and on the parsed answer nothing separates the arms
    at n=40. Every other backend is unmeasured, which is a different thing from
    safe.

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

    # Case-folded, because `Ollama/qwen3:4b` is the same venue and was
    # accepted at concurrency 4 before this line was.
    lowered = model.lower()
    unsafe = sorted(prefix for prefix in CONCURRENCY_UNSAFE if lowered.startswith(prefix))
    if concurrency > 1 and unsafe and not measuring_concurrency:
        raise RunError(
            f"{model} is measured to return different text under concurrency, so "
            f"concurrency={concurrency} would add a known source of variation to a "
            f"venue that already has one. Measured twice: within an invocation the "
            f"concurrent arm agreed with serial on 0 of 40 items both times, against "
            f"a serial repeat of 31 of 40 and 13 of 40. Note that serial runs in "
            f"different invocations agree on only 0 of 40 and 7 of 40 either, so "
            f"serial is not a way to make this backend reproducible. Run it "
            f"serially, or pass "
            f"measuring_concurrency=True if you are the falsifier re-measuring it."
        )

    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    done = completed_keys(checkpoint)
    pending = [item for item in items if (item.item_id, arm.arm) not in done]
    produced: list[RunRecord] = []

    # What has been authorised and not yet paid for. Without it the ledger
    # cannot refuse anything inside one window: `assert_can_afford` reads
    # `spent_usd`, which only advances when a record comes *back*, so every
    # call dispatched together sees the same balance. Measured before the fix:
    # six items at $0.02 against a $0.021 limit ran all six, burning 5.7x the
    # limit and raising nothing, while the serial path stopped after one.
    reserved = 0.0

    def authorise(item: Item) -> tuple[str, float]:
        """Reserve the cost of one item and return its prompt and that cost."""
        nonlocal reserved
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
            ledger.assert_can_afford(amount + reserved)
        except Exception as exc:
            raise RunError(f"stopping before {item.item_id}: {exc}") from exc
        reserved += amount
        return prompt, amount

    # One instance for the whole run. A pause served by any worker is a pause
    # every worker observes; a per-worker backoff would send the same burst back
    # at the same wall.
    backpressure = Backpressure(backoff)

    with (
        checkpoint.open("a", encoding="utf-8") as handle,
        ThreadPoolExecutor(max_workers=concurrency) as pool,
    ):
        submitted = 0
        in_flight: dict[Future[RunRecord], float] = {}

        while submitted < len(pending) or in_flight:
            while len(in_flight) < concurrency and submitted < len(pending):
                item = pending[submitted]
                prompt, amount = authorise(item)
                in_flight[
                    pool.submit(
                        _run_one,
                        item,
                        arm,
                        model=model,
                        call=call,
                        prompt=prompt,
                        identity=identity,
                        backpressure=backpressure,
                    )
                ] = amount
                submitted += 1

            finished, _ = wait(set(in_flight), return_when=FIRST_COMPLETED)

            # Drain the whole batch before re-raising. Returning early on the
            # first failure discarded calls that had already *succeeded* in the
            # same batch, and which ones survived depended on set iteration
            # order -- the same inputs produced three different checkpoints
            # across twelve trials. Those calls were paid for, so throwing them
            # away makes the ledger under-read the real burn by up to
            # `concurrency - 1` calls on every abort.
            failure: RunError | None = None
            for future in finished:
                reserved -= in_flight.pop(future)
                try:
                    record = future.result()
                except RunError as exc:
                    failure = failure or exc
                    continue
                # One writer, on this thread. Appending to one handle from
                # several threads interleaves partial lines, and a corrupt
                # interior line is the one thing `load_records` refuses.
                ledger = ledger.record(record.cost_usd)
                handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
                handle.flush()
                produced.append(record)
            if failure is not None:
                raise failure
    return produced


def _run_one(
    item: Item,
    arm: ArmPrompt,
    *,
    model: str,
    call: CallFn,
    prompt: str,
    identity: NodeIdentity | None = None,
    backpressure: Backpressure,
) -> RunRecord:
    """One call, retried while the answer is "come back later".

    A rate limit is not an infrastructure zero. It clears on its own, so scoring
    it as one records a model failure that never happened and spends the item to
    do it. `AuthenticationError` still aborts the whole run, as it always has: a
    revoked token returns a well-formed refusal on every call, so retrying it is
    a few hundred failures at whatever the backoff costs.

    `backpressure` is shared by every worker, so a pause one of them serves is a
    pause all of them observe. It is required rather than optional: an optional
    one defaults to no retrying, which is the behaviour this exists to replace,
    and `Backoff(attempts=1)` says the same thing where a caller means it.
    """
    try:
        result = _call_with_backoff(arm, call=call, prompt=prompt, backpressure=backpressure)
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


def _call_with_backoff(
    arm: ArmPrompt,
    *,
    call: CallFn,
    prompt: str,
    backpressure: Backpressure,
) -> CliResult:
    """Issue the call, waiting out rate limits until the attempts run out.

    The final attempt is made outside the loop so its refusal propagates
    untouched: a call that never got through is recorded as the infrastructure
    zero it is, carrying the server's own message. Written this way rather than
    with a re-raise inside the loop because the loop then has no unreachable
    exit to explain, and `Backoff.__post_init__` guarantees at least one try.
    """
    for attempt in range(backpressure.policy.attempts - 1):
        backpressure.wait()
        try:
            result = call(prompt, arm.system_prompt, arm.append)
        except RateLimitedError as exc:
            backpressure.trip(attempt, exc.retry_after)
            continue
        backpressure.succeeded()
        return result

    backpressure.wait()
    result = call(prompt, arm.system_prompt, arm.append)
    backpressure.succeeded()
    return result


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
