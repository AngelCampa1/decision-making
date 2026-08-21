"""The Antigravity CLI (``agy``) as a model backend.

**This backend is a venue, not a model.** That distinction is why the module is
separate from :mod:`decision_evals.providers.claude_code`, and it is measured
rather than asserted. On 2026-08-21 a six-word prompt cost **13,742 input
tokens** on ``gemini-3.7-flash-low`` and **15,750** on ``claude-sonnet-4-6``.
There is no ``--system-prompt``, no ``--tools`` and no ``--setting-sources``:
every call arrives wrapped in roughly fourteen thousand tokens of Antigravity's
own agent scaffold, with :data:`AGY_TOOLS` available.

So the arms this repository has published -- a bare description under a fully
replaced system prompt with ``--tools ""`` -- **cannot be run here**, and a
number from this backend compared against them would be comparing two different
constructs. :func:`decision_evals.trigger_arms.models_comparable` refuses that
pooling on the model stamp, which is the guard working rather than an obstacle
to route around.

What this backend *is* natively is the in-situ arm: a skill description offered
to a live coding agent that has tools, a persona and a job. That arm is void
today (``results/decision-making/2026-08-19-505b236-n9-in-situ-void/``, 516 calls
discarded at a 0.8566 parse rate), diagnosed as "prose -- the model answering as
Claude Code instead of emitting the contract".

**Why that void is fixable here.** Probed against a real trigger item on
2026-08-21, ``gemini-3.7-flash-low`` reproduced the N9 failure exactly: some five
hundred tokens of prose advice, then JSON. But ``--json-schema`` returned
``structured_output`` as a separate field regardless of the prose around it, so
the contract travels out of band and a parse failure stops being the failure mode
that ends a run. The prose is still recorded; it is no longer the channel the
verdict travels through.

**Three vendors, one binary.** ``agy models`` serves Gemini 3.1-3.7, Claude
Sonnet 4.6 and Opus 4.6, and GPT-OSS 120B. That is what makes this the first
backend able to support the claim ladder's sentence about *frontier models*,
plural (``docs/PROTOCOL.md``). It also means ``claude-sonnet-4-6`` reached
through ``agy`` and ``sonnet`` reached through ``claude -p`` are the same weights
in different venues, which is why :mod:`decision_evals.arenas` keys an arena on
the pair rather than on the model alone.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final

from decision_evals.providers.claude_code import (
    AuthenticationError,
    CliError,
    CliResult,
    IsolationError,
    PromptTooLongError,
    RateLimitedError,
)

#: The executable. A bare name so ``PATH`` resolves it, matching how the Claude
#: provider names ``claude``.
AGY_BIN: Final = "agy"

#: The namespace every model id carries in a record, exactly as
#: :attr:`~decision_evals.providers.openai_compatible.Endpoint.label` does for
#: ``ollama/``. Stripped before the request, because the CLI knows its models by
#: their bare names and has never heard of this.
#:
#: Not decoration. ``agy`` serves a model it calls ``claude-opus-4-6`` and
#: ``claude -p`` accepts that id too, so a bare record cannot say which venue
#: answered -- one is confirm-tier, the other is a coding agent with 57 tools.
#: The label is what makes
#: :func:`decision_evals.trigger_arms.models_comparable` refuse to pool them
#: without anyone having to remember to.
AGY_LABEL: Final = "agy"

#: Flags applied to every call, for the same reason
#: :data:`~decision_evals.providers.claude_code.ISOLATION_FLAGS` is: a call site
#: cannot forget them. This tuple is much shorter than that one, and the
#: difference is the finding rather than an oversight -- ``agy`` exposes no flag
#: that removes tools, settings or the system prompt.
#:
#: ``--disable-slash-commands`` is the one real isolation lever available. It
#: stops slash-command and *skill* expansion in print mode, which matters
#: directly here: this repository ships skills, and a skill picked up from disk
#: would be the arm's own content arriving through a second channel.
ISOLATION_FLAGS: Final[tuple[str, ...]] = ("--disable-slash-commands",)

#: The 57 tools ``agy`` declares on every call, pinned so that drift is loud.
#: Captured from the ``init`` event on 2026-08-21 and **identical across
#: gemini-3.7-flash-low and gpt-oss-120b-medium**, so the set is a property of
#: the harness rather than of the model.
#:
#: Pinned rather than merely recorded, because this list *is* the venue. A plugin
#: or an MCP server adding a fifty-eighth tool would make every subsequent call a
#: different experiment, and nothing else in the pipeline would notice.
AGY_TOOLS: Final[frozenset[str]] = frozenset(
    {
        "ask_custom_permission",
        "ask_permission",
        "ask_question",
        "browser_click_element",
        "browser_drag_pixel_to_pixel",
        "browser_get_dom",
        "browser_get_network_request",
        "browser_input",
        "browser_list_network_requests",
        "browser_mouse_down",
        "browser_mouse_up",
        "browser_move_mouse",
        "browser_press_key",
        "browser_refresh_page",
        "browser_resize_window",
        "browser_scroll",
        "browser_scroll_dom",
        "browser_select_option",
        "browser_subagent",
        "call_mcp_tool",
        "capture_browser_console_logs",
        "capture_browser_screenshot",
        "click_browser_pixel",
        "command_status",
        "define_subagent",
        "delete_knowledge",
        "execute_browser_javascript",
        "find_by_name",
        "finish",
        "generate_image",
        "grep_search",
        "invoke_subagent",
        "list_browser_pages",
        "list_dir",
        "list_permissions",
        "list_resources",
        "manage_inbox",
        "manage_subagents",
        "manage_task",
        "multi_replace_file_content",
        "notebook_edit",
        "notebook_execution",
        "open_browser_url",
        "read_browser_page",
        "read_resource",
        "read_url_content",
        "replace_file_content",
        "run_command",
        "schedule",
        "search_web",
        "sed_file",
        "send_command_input",
        "send_message",
        "view_file",
        "wait",
        "wait_5_seconds",
        "write_to_file",
    }
)

#: Windows' ``CreateProcess`` command line ceiling is 32,767 characters. The
#: prompt travels in argv because ``--print`` requires a value and a bare
#: ``--print`` with piped stdin is a usage error, so unlike the Claude provider
#: there is no stdin escape hatch. The longest turn in the v5 corpus is 8,363
#: characters, so the margin is real today; this constant exists so a longer
#: corpus fails with a sentence rather than an OS error.
_ARGV_CEILING: Final = 30_000

#: Text ``agy`` returns when the credential is missing or rejected.
#: **Unobserved**, like the two registers below it.
_AUTH_MARKERS: Final[tuple[str, ...]] = ("not logged in", "unauthenticated", "sign in")

#: Text treated as a quota refusal. **Unobserved.** No call made from this
#: repository has hit one; see
#: :class:`~decision_evals.providers.claude_code.RateLimitedError` for why a
#: superset is written down anyway, and what labelling it costs.
_RATE_LIMIT_MARKERS: Final[tuple[str, ...]] = (
    "rate limit",
    "rate_limit",
    "quota",
    "resource exhausted",
    "resource_exhausted",
    "too many requests",
)

#: Text treated as the prompt overflowing the window, on the same reasoning as
#: the Claude provider: a deterministic construction defect, never retried.
#: **Unobserved.**
_TOO_LONG_MARKERS: Final[tuple[str, ...]] = (
    "context length",
    "too long",
    "exceeds the maximum",
)


@dataclass(frozen=True)
class AgyReceipt:
    """What ``agy`` declared about the venue before it answered.

    The analogue of :class:`~decision_evals.providers.claude_code.InitReceipt`,
    read from the ``init`` event of an ``--output-format stream-json`` stream,
    and it exists for the same reason: strictly better evidence than inferring a
    clean venue from a response that looked clean.

    :meth:`assert_isolated` inverts its Claude counterpart. There, a non-empty
    ``tools`` list *is* the anomaly, because the harness asked for none. Here 57
    tools are the healthy state and the anomaly is any departure from them, in
    either direction. Asserting emptiness would refuse every call this backend
    can make, which is the shape of gate that gets switched off.
    """

    model: str = ""
    cwd: str = ""
    tools: tuple[str, ...] = ()
    permission_mode: str = ""

    def assert_isolated(self, *, model: str, cwd: str) -> None:
        """Refuse a call whose venue is not the one that was asked for.

        Args:
            model: The pinned model id the caller requested, with or without the
                :data:`AGY_LABEL` namespace. Compared bare, because the label is
                a recording convention and the CLI never sees it.
            cwd: The scratch directory the caller created for this call.

        Raises:
            IsolationError: The resolved model differs from the requested one,
                the working directory is not the scratch directory, or the tool
                set has drifted from :data:`AGY_TOOLS`.
        """
        requested = bare_model(model)
        if self.model != requested:
            raise IsolationError(
                f"asked for model {requested!r} and the CLI answered as {self.model!r}. "
                "A silent substitution puts two models' answers in one arm under one "
                "label, which no downstream analysis can separate."
            )
        if self.cwd != cwd:
            raise IsolationError(
                f"the CLI ran in {self.cwd!r}, not the scratch directory {cwd!r}. The "
                "working directory determines which project rules are discoverable, so "
                "a call outside it is a different venue."
            )
        declared = frozenset(self.tools)
        if declared != AGY_TOOLS:
            added = sorted(declared - AGY_TOOLS)
            removed = sorted(AGY_TOOLS - declared)
            raise IsolationError(
                f"the tool set drifted: {len(added)} added {added}, {len(removed)} "
                f"removed {removed}. This backend's 57 tools are the venue being "
                "measured, so a different set is a different experiment. Re-pinning "
                "AGY_TOOLS is a decision with a `docs/DECISIONS.md` entry, not a test "
                "fixture to update."
            )


def parse_init_receipt(event: dict[str, Any]) -> AgyReceipt:
    """Read an ``init`` event into an :class:`AgyReceipt`.

    Absent keys become empty rather than raising, matching
    :func:`~decision_evals.providers.claude_code.parse_init_receipt`: the event
    is the CLI's and its shape is not ours to require. What *is* enforced is
    :meth:`AgyReceipt.assert_isolated`, and an absent ``tools`` key reads as an
    empty set, which fails that check loudly rather than passing quietly.
    """
    init = event.get("init")
    if not isinstance(init, dict):
        init = {}
    tools = init.get("tools")
    return AgyReceipt(
        model=str(init.get("model", "")),
        cwd=str(init.get("cwd", "")),
        tools=tuple(str(item) for item in tools) if isinstance(tools, list) else (),
        permission_mode=str(init.get("permission_mode", "")),
    )


def nullable_enum(values: Sequence[str]) -> dict[str, Any]:
    """A "one of these, or nothing" property in the dialect this backend accepts.

    ``--json-schema`` is not full JSON Schema. Measured 2026-08-21 against
    ``gemini-3.7-flash-low``, the obvious spelling is **rejected outright**::

        {"type": ["string", "null"], "enum": [..., null]}   # status: ERROR

    while this one answers, and answered correctly::

        {"type": "string", "enum": [...], "nullable": true}

    The difference matters beyond tidiness. A schema the backend refuses fails
    the whole call, so writing the natural JSON Schema spelling would have turned
    every item in an arm into an infrastructure zero -- a clean run, a full
    checkpoint, and a number measuring nothing, which is the exact defect shape
    this repository has already published twice.

    ``null`` is the encoding for "would not fire, or cannot tell", so it has to
    be reachable; an enum that cannot express abstention would push the model
    into naming a procedure it does not believe in.
    """
    return {"type": "string", "enum": list(values), "nullable": True}


def build_command(
    *,
    prompt: str,
    model: str,
    json_schema: str | None = None,
    timeout: float = 900.0,
) -> list[str]:
    """Assemble one ``agy`` invocation.

    ``--output-format stream-json`` rather than ``json`` because only the stream
    carries the ``init`` event, and the ``init`` event is the receipt. Paying a
    little parsing for a venue check that is otherwise unavailable is the trade
    Track 0.3 already made when it forced the streaming transport onto every node.

    Raises:
        PromptTooLongError: The prompt would overflow the OS command line. Raised
            here rather than at the OS so the failure names the ceiling.
    """
    if len(prompt) > _ARGV_CEILING:
        raise PromptTooLongError(
            f"prompt is {len(prompt)} characters and the argv ceiling here is "
            f"{_ARGV_CEILING}. `agy --print` takes its prompt as an argument and "
            "rejects a bare `--print` with piped stdin, so there is no stdin path to "
            "fall back to."
        )
    command = [
        AGY_BIN,
        "--print",
        prompt,
        "--output-format",
        "stream-json",
        "--model",
        bare_model(model),
        *ISOLATION_FLAGS,
        "--print-timeout",
        f"{int(timeout)}s",
    ]
    if json_schema is not None:
        command += ["--json-schema", json_schema]
    return command


def bare_model(model: str) -> str:
    """Strip the :data:`AGY_LABEL` namespace, if the caller supplied it."""
    prefix = f"{AGY_LABEL}/"
    return model[len(prefix) :] if model.startswith(prefix) else model


def labelled_model(model: str) -> str:
    """Add the :data:`AGY_LABEL` namespace, if it is not already there."""
    prefix = f"{AGY_LABEL}/"
    return model if model.startswith(prefix) else f"{prefix}{model}"


def _number(value: Any) -> float:
    """Coerce a possibly-absent, possibly-null usage field to a number."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _classify(message: str) -> CliError:
    """Map an error message onto the taxonomy the runner already catches.

    The five error types are imported from the Claude provider rather than
    redefined, following :mod:`decision_evals.providers.openai_compatible`. A
    runner should not have to know which backend it is driving in order to know
    whether a failure is worth retrying.
    """
    lowered = message.lower()
    if any(marker in lowered for marker in _AUTH_MARKERS):
        return AuthenticationError(f"{message} -- run `agy` once and sign in.")
    if any(marker in lowered for marker in _TOO_LONG_MARKERS):
        return PromptTooLongError(message)
    if any(marker in lowered for marker in _RATE_LIMIT_MARKERS):
        return RateLimitedError(message)
    return CliError(message)


def parse_events(lines: Sequence[str], *, model: str) -> tuple[AgyReceipt, CliResult]:
    """Read a ``stream-json`` transcript into a receipt and a result.

    ``structured_output`` is preferred over ``response`` when present, and that
    preference is the point of using ``--json-schema`` at all: the prose the
    agent wrote around its answer stays in :attr:`CliResult.reasoning` where a
    reader can see it, while the verdict travels in a field that cannot be
    malformed. Under the N9 harness the prose *was* the channel, and 70 of 516
    calls were discarded because of it.

    Raises:
        CliError: The stream carried no ``result`` event, or the result was an
            error. Subclassed per :func:`_classify`.
    """
    receipt = AgyReceipt()
    result: dict[str, Any] | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            # A partial or non-JSON line is the CLI's business. The contract this
            # function needs is the `result` event, and its absence is what
            # raises below.
            continue
        if not isinstance(event, dict):
            continue
        if event.get("event") == "init":
            receipt = parse_init_receipt(event)
        elif event.get("event") == "result":
            payload = event.get("result")
            result = payload if isinstance(payload, dict) else {}

    if result is None:
        raise CliError(
            "the stream ended without a `result` event, which means the process died "
            "mid-call. Scored as infrastructure failure rather than as a model answer."
        )

    status = str(result.get("status", ""))
    text = result.get("response")
    structured = result.get("structured_output")

    # A failed status does not mean there is no answer, which was the surprise
    # here and is why `CliResult.status` exists. Measured 2026-08-21: a call came
    # back `status: "ERROR"` carrying `structured_output` of
    # `{"fire": true, "procedure": "timing"}`, because the agent reached for
    # `~/.gemini/antigravity-cli` after answering and the CLI's own protection
    # boundary refused it. Raising on the status would have thrown away a
    # complete verdict.
    #
    # So the question this branch asks is "is there an answer", not "did the call
    # end well". The status travels into the record either way, and **whether an
    # ERROR-status verdict may be scored is an analysis decision with a
    # `docs/DECISIONS.md` entry, not something to settle silently here.**
    if structured is None and not isinstance(text, str):
        raise CliError(f"result event has no string `response`: {result!r}")
    if structured is None and status and status != "SUCCESS":
        raise _classify(str(result.get("error") or text or status))

    if structured is not None:
        # Recorded as the answer, with the prose kept beside it rather than
        # dropped. `separators` and `sort_keys` are explicit so the text a scorer
        # reads is stable across runs and Python versions.
        answer = json.dumps(structured, separators=(",", ":"), sort_keys=True)
        reasoning = text if isinstance(text, str) else ""
    else:
        answer, reasoning = str(text), ""

    usage = result.get("usage") or {}
    return receipt, CliResult(
        text=answer,
        # The id the CLI resolved, namespaced, which `assert_isolated` has
        # already compared against the request. Falls back to the requested id
        # only when the stream carried no init event at all.
        model=labelled_model(receipt.model or bare_model(model)),
        # `agy` reports no cost. Recorded as an explicit 0.0 rather than omitted,
        # the same convention as `Endpoint.cost_usd`: a subscription call that
        # bills nothing is a fact about the run, not a missing field. See
        # `docs/HARNESS_DISCLOSURE.md` for the disclosure this obliges.
        cost_usd=0.0,
        input_tokens=int(_number(usage.get("input_tokens"))),
        output_tokens=int(_number(usage.get("output_tokens"))),
        duration_ms=int(_number(result.get("duration_seconds")) * 1000),
        session_id=str(result.get("conversation_id", "")),
        cache_read_tokens=int(_number(usage.get("cache_read_tokens"))),
        reasoning=reasoning,
        status=status,
        num_turns=int(_number(result.get("num_turns"))),
    )


def run(
    prompt: str,
    *,
    model: str,
    cwd: str,
    json_schema: str | None = None,
    timeout: float = 900.0,
) -> tuple[AgyReceipt, CliResult]:
    """Run one item and return its receipt alongside its result.

    Both, rather than the result alone, because the receipt is obtainable only
    from the same stream, and discarding it would leave the caller asserting a
    clean venue from a response that merely looked clean.

    There is no ``system_prompt`` parameter, and its absence is this backend's
    defining property: ``agy`` has no flag that replaces the system prompt, so
    the response contract travels either in ``json_schema`` or at the top of
    ``prompt``. See the module docstring.
    """
    command = build_command(prompt=prompt, model=model, json_schema=json_schema, timeout=timeout)
    # Fixed argv, no shell. `encoding` and `errors` are explicit for the reason
    # recorded in the Claude provider: `text=True` alone decodes with the locale
    # codec, which on Windows is cp1252, and the first character it cannot decode
    # raises inside subprocess's reader thread where it cannot propagate.
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        # A little past the CLI's own `--print-timeout`, so the CLI reports its
        # own timeout as a result event rather than being killed here with
        # nothing to record.
        timeout=timeout + 60.0,
        check=False,
    )
    if not completed.stdout:
        raise _classify(
            f"agy produced no stdout (exit {completed.returncode}); "
            f"stderr {(completed.stderr or '')[:300]!r}"
        )
    return parse_events(completed.stdout.splitlines(), model=model)


def preflight(*, model: str, cwd: str) -> tuple[AgyReceipt, CliResult]:
    """One throwaway call, to fail before item 1 rather than during it.

    The same role as the other two providers' preflights, against this backend's
    own failure: the credential is interactive-only, so a signed-out machine
    fails every call in a run rather than refusing to start one.
    """
    return run("Reply with exactly the word: ready", model=model, cwd=cwd, timeout=120.0)
