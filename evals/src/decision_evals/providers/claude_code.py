"""The Claude Code CLI as a model backend.

Every generation in this repository goes through :func:`build_command`. The
point of routing it all through one function is that the isolation flags cannot
be forgotten at a call site: they are baked into :data:`ISOLATION_FLAGS` and
prepended unconditionally.

That matters more than it looks, because of a measured result recorded in
``notebook/2026-08-10-isolation-canary.md``. A ``CLAUDE.md`` planted in the
working directory is **still injected when the system prompt is fully
replaced**. Replacing the system prompt is not an isolation mechanism; it
governs a different injection path. The flag that actually blocks project memory
is ``--setting-sources ""``.

Anyone building this harness would reasonably assume ``--system-prompt``
(documented as a full replacement) removes everything. It does not, and the
failure is silent: runs would quietly inherit whatever ``CLAUDE.md`` happened to
sit above the working directory. On this machine that file mandates an unrelated
copy-editing workflow, which would have been a confound in every arm at once.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

#: Flags that remove every confound the CLI would otherwise contribute. Applied
#: unconditionally by :func:`build_command`; there is deliberately no way to
#: switch them off.
#:
#: ``--setting-sources ""`` is the load-bearing one for settings, and it is not
#: the only load-bearing flag here. **Checked live on 2026-08-18 against
#: claude-code 2.1.159**: dropping ``--disable-slash-commands`` makes the CLI
#: declare thirteen skills, and dropping the two MCP flags makes it declare nine
#: pending connectors — on this machine, whose user configuration supplies them.
#: This comment previously said the others "close paths that are not currently
#: open", which invited a future reader to trim them as belt-and-braces. They
#: are open. See ``notebook/2026-08-18-memory-paths-is-not-a-gate.md`` for the
#: two calls, which are also the first known-good/known-bad pair ever run
#: against :meth:`InitReceipt.assert_isolated`'s ``skills`` branch.
ISOLATION_FLAGS: Final[tuple[str, ...]] = (
    "--setting-sources",
    "",
    "--tools",
    "",
    "--disable-slash-commands",
    "--strict-mcp-config",
    "--mcp-config",
    '{"mcpServers":{}}',
    "--no-session-persistence",
)


def isolated_cwd(prefix: str = "de-") -> tempfile.TemporaryDirectory[str]:
    """A throwaway working directory for one call, safe to clean up on Windows.

    Every call runs in a fresh directory because the CLI's auto-memory path is
    keyed on cwd, so a shared directory would let one call's state reach the
    next. That part is not optional.

    ``ignore_cleanup_errors=True`` is, and it is here because of a real loss.
    On 2026-08-12 a 365-call trigger run died at call 348 with

        PermissionError: [WinError 32] The process cannot access the file
        because it is being used by another process

    raised by ``TemporaryDirectory.__exit__``. Windows refuses to remove a
    directory a process still holds, and the CLI subprocess does not always
    release its cwd before the context manager returns. **The calls had all
    succeeded**; the run died tidying up after them.

    A leaked directory under the system temp folder costs nothing and the OS
    reclaims it. Losing a run to a cleanup race costs hours of quota. Only the
    checkpoint saved that one, and a script without a checkpoint would have lost
    everything.
    """
    return tempfile.TemporaryDirectory(prefix=prefix, ignore_cleanup_errors=True)


#: Text the CLI returns when the stored OAuth credential has been revoked. The
#: CLI reports ``loggedIn: true`` in this state, so the response body is the
#: only reliable signal.
_REVOKED_MARKER: Final = "authenticate"

#: Text the CLI returns when the prompt exceeds the model's context window.
#: Observed verbatim as "Prompt is too long" at a nominal 350k tokens.
_TOO_LONG_MARKER: Final = "prompt is too long"


class CliError(RuntimeError):
    """The CLI returned an error, or returned something unparseable."""


class IsolationError(CliError):
    """The CLI declared capabilities the experiment does not permit.

    Separate from :class:`CliError` because it is not a failed call. The call
    would have succeeded; what is wrong is that it would have been measuring a
    different venue, and that is a reason to stop a run rather than score it.
    """


class PromptTooLongError(CliError):
    """The assembled prompt did not fit the model's context window.

    Separated from :class:`CliError` because the two mean opposite things about
    the corpus. Infrastructure noise is a reason to retry an item; a prompt that
    overflows the window is a *construction defect* in the item, deterministic,
    and it will overflow every time. Scoring it as ``infrastructure`` would put a
    reproducible authoring mistake in the same bucket as a flaky network and hide
    it behind a retry.

    Measured: at a nominal 350k the CLI returns ``is_error`` with "Prompt is too
    long" and spends nothing. At 101,142 tokens it answers normally, so the
    ceiling is the model's window rather than anything in this harness.
    """


class AuthenticationError(CliError):
    """The CLI could not authenticate.

    Raised separately from :class:`CliError` because it is the one failure that
    must abort a whole run rather than scoring a single item. A revoked token
    yields a well-formed response with ``is_error`` set on every call, so
    without this distinction a credential that rotates mid-run is recorded as a
    few hundred model failures.
    """


@dataclass(frozen=True)
class CliResult:
    """One completed generation, with everything a run record needs."""

    text: str
    model: str
    cost_usd: float
    input_tokens: int
    output_tokens: int
    duration_ms: int
    session_id: str
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    context_window: int = 0
    #: Reasoning the model emitted separately from its answer, empty when the
    #: backend does not split the two. Measured 2026-08-19 against ``qwen3:4b``:
    #: 277 completion tokens for a one-character answer, of which 276 were in a
    #: ``reasoning`` field the parser was discarding. Recorded rather than
    #: dropped, because ``output_tokens`` counts it and the scorer never sees
    #: it, and an unexplained gap between those two is the shape of every
    #: instrument defect on record here. See
    #: :func:`decision_evals.providers.openai_compatible.parse_completion`.
    reasoning: str = ""

    @property
    def context_fraction(self) -> float:
        """How full the context window was. 0.0 when the CLI did not report one.

        Worth recording per item rather than assuming: the U-shaped degradation
        reported in the context-rot literature holds only while the window is
        below about half full, so which side of that line an item sits on is a
        covariate, not a constant.
        """
        if self.context_window <= 0:
            return 0.0
        return (self.input_tokens + self.output_tokens) / self.context_window


def build_command(
    *,
    system_prompt: str,
    model: str,
    in_situ: bool = False,
    json_schema: str | None = None,
    streaming: bool = False,
) -> list[str]:
    """Assemble a fully isolated ``claude -p`` invocation.

    **The prompt is not here.** It goes to the process on stdin, which is why
    this function does not take one. ``claude -p`` with the default
    ``--input-format text`` reads the prompt from stdin when no prompt argument
    is given, and ``-p`` is documented as "useful for pipes".

    The original version passed the rendered item as an argv element. That works
    for a 350-token item and cannot work for a long one: Windows caps a whole
    command line near 32 KB, and a 100k-token casefile is roughly 400 KB. Every
    call in the two longest strata would have died as a :class:`CliError` and
    been scored ``zero_cause="infrastructure"`` -- an entire arm of nulls that
    reads like a finding.

    There is deliberately no short-prompt fast path. A conditional argv/stdin
    split means the long path is the rarely-exercised one and the two can drift,
    which is exactly the harness variance this repository exists to measure.

    The system prompt stays on argv: skill bodies are 1-2 KB and there is only
    one of them per call.

    Args:
        system_prompt: Arm-specific system prompt.
        model: Model alias or id, passed through to ``--model``.
        in_situ: Append to the CLI's built-in system prompt rather than
            replacing it. This is the ecological-validity arm; it is still fully
            isolated, because isolation comes from ``--setting-sources ""``
            rather than from replacing the prompt.
        json_schema: Optional answer schema, passed to ``--json-schema``.
        streaming: Build the multi-turn form instead. Turns then arrive as
            JSON lines on stdin of one live process and the CLI answers with an
            event stream, which is how context carries across turns without
            ``--resume``. See :class:`Conversation`.

    Returns:
        Argument vector suitable for :func:`subprocess.run` without a shell.
        Pass the prompt separately as ``input=``.
    """
    prompt_flag = "--append-system-prompt" if in_situ else "--system-prompt"
    command = [
        "claude",
        "-p",
        prompt_flag,
        system_prompt,
        "--model",
        model,
        *ISOLATION_FLAGS,
    ]
    if streaming:
        # `--input-format stream-json` requires the streaming output form, and
        # `--verbose` is what makes the CLI emit the system/init event that
        # Track 0.6 asserts isolation from.
        command += [
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--verbose",
        ]
    else:
        command += ["--output-format", "json"]
    if json_schema is not None:
        command += ["--json-schema", json_schema]
    return command


def user_event(text: str) -> str:
    """One turn, as the JSON line the CLI expects on stdin."""
    return json.dumps(
        {
            "type": "user",
            "message": {"role": "user", "content": [{"type": "text", "text": text}]},
        }
    )


@dataclass(frozen=True)
class InitReceipt:
    """The ``system``/``init`` event: a machine-readable isolation receipt.

    Strictly better evidence than inferring isolation from a response. The CLI
    states, before any generation, exactly which tools, skills and agents it
    loaded and where it would write memory.

    **Two of these fields are latent rather than active, and the distinction
    matters.** Under ``--tools ""`` the CLI still *declares* its built-in
    subagents and an auto-memory path, but there is no Task tool to reach the
    agents and no memory tool to write the path — tested, nothing was created.
    Both go live the moment ``--tools`` is relaxed, which Track F plans. The
    memory path is keyed on the working directory, so it would become a
    cross-run state channel that a checkpointed record cannot see. Hence
    :meth:`assert_isolated` gates on ``tools`` and ``skills``, and the rest —
    ``agents``, ``memory_paths``, ``api_key_source``, ``model``, ``cwd``,
    ``session_id`` — is recorded rather than gated.

    **Why ``memory_paths`` specifically is recorded and not gated, checked
    live rather than assumed (2026-08-18, claude-code 2.1.159).** Unlike
    ``tools`` and ``skills`` — empty under a healthy isolated call, so a
    non-empty value is itself the anomaly — ``memory_paths`` reports
    ``{"auto": "<cwd-keyed-path>"}`` on *every* isolated call, planted
    ``CLAUDE.md`` or not: ``--setting-sources ""`` blocks that file from being
    read at all (see ``notebook/2026-08-10-isolation-canary.md``), so nothing
    a run does today can change what this field says. Refusing whenever it is
    non-empty would refuse every run this repository has ever made, not the
    contaminated ones; there is no currently-known shape of this field that
    distinguishes a clean isolated call from a compromised one. Gating
    ``assert_isolated`` on it would therefore not be a stricter check, it
    would be a broken one. See
    ``notebook/2026-08-18-memory-paths-is-not-a-gate.md`` for the calls this
    was checked against.
    """

    tools: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    memory_paths: tuple[str, ...] = ()
    api_key_source: str = ""
    model: str = ""
    cwd: str = ""
    session_id: str = ""

    @property
    def tools_disabled(self) -> bool:
        """Whether the CLI loaded no tools at all."""
        return not self.tools

    def assert_isolated(self) -> None:
        """Refuse a run whose declared capabilities exceed what was intended.

        Raises:
            IsolationError: Tools were loaded, or a skill was picked up from
                disk. Either one silently changes what is being measured, and
                both are invisible in a response body.
        """
        if self.tools:
            raise IsolationError(
                f"the CLI loaded {len(self.tools)} tool(s): {sorted(self.tools)}. "
                'Every measurement in this repository assumes `--tools ""`; a run with '
                "tools available is a different venue, not a noisier one."
            )
        if self.skills:
            raise IsolationError(
                f"the CLI loaded skill(s) from disk: {sorted(self.skills)}. The arm's "
                "system prompt is supposed to be the only skill content in context."
            )


def _memory_paths(event: dict[str, Any]) -> tuple[str, ...]:
    """Read ``memory_paths``, which is a mapping on the real CLI, not a list.

    Checked live against claude-code 2.1.159 on 2026-08-18: every ``system``/
    ``init`` event declares ``{"auto": "<cwd-keyed-path>"}``, never a bare
    list. A plain ``isinstance(value, list)`` check -- the shape every other
    field on this event actually has -- silently read this one as ``()``
    regardless of what the CLI said, on every call this harness has ever
    made. This is "recorded" being false in production while the class
    docstring claimed it, the same failure shape as the fields this repository
    has already found reading a whitelist that discarded everything it was
    supposed to accept. The list branch stays, since nothing pins the shape
    upstream and a future CLI could restore it.
    """
    value = event.get("memory_paths")
    if isinstance(value, dict):
        return tuple(str(item) for item in value.values())
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def parse_init_receipt(event: dict[str, Any]) -> InitReceipt:
    """Read a ``system``/``init`` event into an :class:`InitReceipt`.

    Absent keys become empty rather than raising: the event is the CLI's, its
    shape is not ours to require, and a missing field must not stop a run that
    is otherwise fine. What *is* enforced is :meth:`InitReceipt.assert_isolated`,
    and an absent ``tools`` key reads as no tools, which is the safe direction.
    """

    def strings(key: str) -> tuple[str, ...]:
        value = event.get(key)
        return tuple(str(item) for item in value) if isinstance(value, list) else ()

    return InitReceipt(
        tools=strings("tools"),
        skills=strings("skills"),
        agents=strings("agents"),
        memory_paths=_memory_paths(event),
        api_key_source=str(event.get("apiKeySource", "")),
        model=str(event.get("model", "")),
        cwd=str(event.get("cwd", "")),
        session_id=str(event.get("session_id", "")),
    )


def parse_result(payload: dict[str, Any]) -> CliResult:
    """Turn a ``--output-format json`` payload into a :class:`CliResult`.

    Raises:
        AuthenticationError: The failure was an authentication failure.
        CliError: Any other error, or a payload missing required fields.
    """
    if payload.get("is_error"):
        message = str(payload.get("result", "")) or "unknown CLI error"
        status = payload.get("api_error_status")
        if status == 401 or _REVOKED_MARKER in message.lower():
            raise AuthenticationError(
                f"{message} -- run `claude auth login`. Note that "
                "`claude auth status` reports loggedIn:true in this state."
            )
        if _TOO_LONG_MARKER in message.lower():
            raise PromptTooLongError(message)
        raise CliError(message)

    text = payload.get("result")
    if not isinstance(text, str):
        raise CliError(f"payload has no string `result` field: {payload!r}")

    # The resolved model id is the sole key of `modelUsage` for a single-turn
    # call. Recording the resolved id rather than the requested alias is what
    # makes the run record reproducible -- `haiku` is not a version.
    model_usage = payload.get("modelUsage") or {}
    if len(model_usage) != 1:
        raise CliError(f"expected exactly one resolved model, got {sorted(model_usage)}")
    model = next(iter(model_usage))

    usage = payload.get("usage") or {}
    cache_creation = int(_number(usage.get("cache_creation_input_tokens")))
    cache_read = int(_number(usage.get("cache_read_input_tokens")))

    # `usage.input_tokens` is the *uncached remainder*, not the prompt. On a
    # 380 KB casefile it reads 10 while `cache_creation_input_tokens` carries the
    # other 24,285, and the reported cost tracks the real figure. Recording
    # `input_tokens` alone would have put ~10 in the token column of every long
    # item -- and the token column is what `docs/HARNESS_DISCLOSURE.md` commits
    # to reporting at p90/p99, so the disclosure would have been backwards
    # precisely in the stratum it exists to describe.
    #
    # The three add up to the prompt the model actually read, which is the number
    # this field is supposed to mean. The split is kept alongside because it is
    # not noise: on the second repeat of an item the same prompt arrives as
    # `cache_read`, which changes cost without changing what was sampled.
    prompt_tokens = int(_number(usage.get("input_tokens"))) + cache_creation + cache_read

    return CliResult(
        text=text,
        model=model,
        cost_usd=_number(payload.get("total_cost_usd")),
        input_tokens=prompt_tokens,
        output_tokens=int(_number(usage.get("output_tokens"))),
        duration_ms=int(_number(payload.get("duration_ms"))),
        session_id=str(payload.get("session_id", "")),
        cache_creation_tokens=cache_creation,
        cache_read_tokens=cache_read,
        context_window=int(_number((model_usage[model] or {}).get("contextWindow"))),
    )


def _number(value: Any) -> float:
    """Coerce a possibly-absent, possibly-null CLI field to a number.

    ``dict.get(key, default)`` is not enough here: the CLI emits keys with
    explicit ``null`` values (``api_error_status`` is ``null`` on every success),
    so the default never fires and ``float(None)`` raises.
    """
    return 0.0 if value is None else float(value)


def run(
    prompt: str,
    *,
    system_prompt: str,
    model: str,
    cwd: str,
    in_situ: bool = False,
    json_schema: str | None = None,
    timeout: float = 900.0,
) -> CliResult:
    """Run one item and return its result.

    ``cwd`` is required rather than defaulted. The working directory determines
    which ``CLAUDE.md`` files are discoverable, so letting it default to
    wherever the runner happens to start is how a confound gets in. Callers pass
    a scratch directory outside the source tree; the canary test in
    ``tests/integration/`` proves the arrangement works rather than assuming it.

    The prompt goes in on stdin -- see :func:`build_command` for why. The default
    timeout is 900 s rather than 300 s because a 100k-token prompt spends most of
    it in prefill, and a run that times out is scored as infrastructure failure
    rather than being retried.
    """
    command = build_command(
        system_prompt=system_prompt,
        model=model,
        in_situ=in_situ,
        json_schema=json_schema,
    )
    # Fixed argv, no shell: `command` is assembled by build_command and contains
    # no item text at all. The prompt arrives on stdin, which removes the OS
    # command-line limit as a ceiling on item length and removes any question of
    # argv quoting.
    #
    # `encoding` is explicit and not optional. `text=True` alone decodes with
    # the locale codec, which on Windows is cp1252: the first curly quote or
    # dash the model emits raises UnicodeDecodeError *inside subprocess's reader
    # thread*, where it cannot propagate. `subprocess.run` then returns normally
    # with `stdout` set to None, and the failure surfaces several frames away as
    # a TypeError about NoneType. It took 280 clean items before one response
    # contained a byte cp1252 could not decode.
    #
    # `errors="replace"` on top: a run that has already spent its quota should
    # not be lost to one undecodable byte, and a mangled character in a response
    # is visible in the record while a dead run is not.
    completed = subprocess.run(
        command,
        input=prompt,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if completed.stdout is None:
        raise CliError(
            f"CLI produced no stdout (exit {completed.returncode}); "
            f"stderr {(completed.stderr or '')[:200]!r}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CliError(
            f"CLI did not emit JSON (exit {completed.returncode}): "
            f"{completed.stdout[:200]!r} / stderr {completed.stderr[:200]!r}"
        ) from exc
    if not isinstance(payload, dict):
        raise CliError(f"CLI emitted non-object JSON: {payload!r}")
    return parse_result(payload)


class Conversation:
    """A live multi-turn session against one CLI subprocess.

    **This is the whole V2 venue, and it needed no flag relaxed.** Track 0's
    original reading was that ``--no-session-persistence`` blocked multi-turn.
    It does not: that flag blocks ``--resume``, which is *cross-process*. With
    ``--input-format stream-json`` the turns go to one live process's stdin and
    context carries in-process, under the full isolation stack.

    The falsifier written for this was also wrong and is worth keeping visible.
    It required ``cache_read`` to climb turn over turn; measured, ``cache_read``
    stayed at **0** on every turn while turn 3 recalled a codeword from turn 1.
    Caching is a billing optimisation, not a transcript mechanism. Run as
    written, that gate would have declared a healthy venue dead. The corrected
    signal is ``input_tokens`` climbing monotonically *plus* a behavioural
    recall check — two independent signals, because a longer question explains
    the first and a lucky guess explains the second.

    Usage::

        with Conversation(system_prompt=..., model="haiku", cwd=tmp) as chat:
            chat.receipt.assert_isolated()
            first = chat.send("Remember MARMALADE-7.")
            third = chat.send("What was the codeword?")

    Args:
        spawn: Injected process factory, so the transport is testable without a
            model. Defaults to :func:`subprocess.Popen`.
    """

    def __init__(
        self,
        *,
        system_prompt: str,
        model: str,
        cwd: str,
        in_situ: bool = False,
        timeout: float = 900.0,
        spawn: Callable[[list[str], str], Any] | None = None,
    ) -> None:
        self._timeout = timeout
        self._turn_index = 0
        command = build_command(
            system_prompt=system_prompt, model=model, in_situ=in_situ, streaming=True
        )
        factory = spawn if spawn is not None else _spawn
        self._process = factory(command, cwd)
        if self._process.stdin is None or self._process.stdout is None:
            raise CliError("the CLI subprocess exposed no stdin/stdout pipe")
        self._receipt: InitReceipt | None = None

    @property
    def turn_index(self) -> int:
        """How many turns have completed. 0 before the first :meth:`send`."""
        return self._turn_index

    @property
    def receipt(self) -> InitReceipt:
        """The isolation receipt, available once the first turn has been sent.

        Raises:
            CliError: No ``system``/``init`` event has arrived yet.
        """
        if self._receipt is None:
            raise CliError("no system/init event has been seen yet; send a turn first")
        return self._receipt

    def send(self, text: str) -> CliResult:
        """Deliver one turn and read until the CLI reports a result.

        Blocks until a ``result`` event arrives or the stream ends. Events other
        than ``result`` and ``system``/``init`` are ignored rather than
        collected: this transport exists to carry turns, and a partial-message
        stream is the CLI's business.

        Raises:
            CliError: The stream ended without a result, which means the process
                died mid-turn.
            AuthenticationError: Via :func:`parse_result`.
        """
        assert self._process.stdin is not None  # narrowed in __init__
        assert self._process.stdout is not None
        self._process.stdin.write(user_event(text) + "\n")
        self._process.stdin.flush()

        for line in self._process.stdout:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError:
                # The CLI interleaves human-readable lines under --verbose.
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                self._receipt = parse_init_receipt(event)
            if event.get("type") == "result":
                self._turn_index += 1
                return parse_result(event)

        raise CliError(
            f"the CLI stream ended without a result on turn {self._turn_index + 1}; "
            "the process died mid-turn"
        )

    def close(self) -> None:
        """Close stdin and wait for the process to exit."""
        if self._process.stdin is not None and not self._process.stdin.closed:
            self._process.stdin.close()
        self._process.wait(timeout=self._timeout)

    def __enter__(self) -> Conversation:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _spawn(command: list[str], cwd: str) -> Any:
    """Start the CLI with pipes, decoding explicitly.

    ``encoding`` and ``errors`` are set for the same reason as in :func:`run`:
    ``text=True`` alone decodes with the locale codec, and on Windows that is
    cp1252, where one curly quote raises inside subprocess's reader thread.
    """
    return subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )


def preflight(*, model: str, cwd: str) -> CliResult:
    """Make one throwaway call so a bad credential aborts before item 1.

    A confirmation run is checkpointed and resumable across days, which means a
    token can rotate *between* sessions of a single run. Without this check the
    resulting 401s are indistinguishable, in the results, from a model that got
    every item wrong.
    """
    return run(
        "Reply with the single word: ready",
        system_prompt="Reply with exactly one word.",
        model=model,
        cwd=cwd,
    )
