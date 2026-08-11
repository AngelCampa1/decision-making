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
from dataclasses import dataclass
from typing import Any, Final

#: Flags that remove every confound the CLI would otherwise contribute. Applied
#: unconditionally by :func:`build_command`; there is deliberately no way to
#: switch them off.
#:
#: ``--setting-sources ""`` is the load-bearing one. The others close paths that
#: are not currently open but would be a confound if a future CLI version
#: changed a default.
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

#: Text the CLI returns when the stored OAuth credential has been revoked. The
#: CLI reports ``loggedIn: true`` in this state, so the response body is the
#: only reliable signal.
_REVOKED_MARKER: Final = "authenticate"


class CliError(RuntimeError):
    """The CLI returned an error, or returned something unparseable."""


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


def build_command(
    prompt: str,
    *,
    system_prompt: str,
    model: str,
    in_situ: bool = False,
    json_schema: str | None = None,
) -> list[str]:
    """Assemble a fully isolated ``claude -p`` invocation.

    Args:
        prompt: The rendered item.
        system_prompt: Arm-specific system prompt.
        model: Model alias or id, passed through to ``--model``.
        in_situ: Append to the CLI's built-in system prompt rather than
            replacing it. This is the ecological-validity arm; it is still fully
            isolated, because isolation comes from ``--setting-sources ""``
            rather than from replacing the prompt.
        json_schema: Optional answer schema, passed to ``--json-schema``.

    Returns:
        Argument vector suitable for :func:`subprocess.run` without a shell.
    """
    prompt_flag = "--append-system-prompt" if in_situ else "--system-prompt"
    command = [
        "claude",
        "-p",
        prompt,
        prompt_flag,
        system_prompt,
        "--model",
        model,
        *ISOLATION_FLAGS,
        "--output-format",
        "json",
    ]
    if json_schema is not None:
        command += ["--json-schema", json_schema]
    return command


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
    return CliResult(
        text=text,
        model=model,
        cost_usd=_number(payload.get("total_cost_usd")),
        input_tokens=int(_number(usage.get("input_tokens"))),
        output_tokens=int(_number(usage.get("output_tokens"))),
        duration_ms=int(_number(payload.get("duration_ms"))),
        session_id=str(payload.get("session_id", "")),
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
    timeout: float = 300.0,
) -> CliResult:
    """Run one item and return its result.

    ``cwd`` is required rather than defaulted. The working directory determines
    which ``CLAUDE.md`` files are discoverable, so letting it default to
    wherever the runner happens to start is how a confound gets in. Callers pass
    a scratch directory outside the source tree; the canary test in
    ``tests/integration/`` proves the arrangement works rather than assuming it.
    """
    command = build_command(
        prompt,
        system_prompt=system_prompt,
        model=model,
        in_situ=in_situ,
        json_schema=json_schema,
    )
    # Fixed argv, no shell: `command` is assembled by build_command, never
    # interpolated from item text.
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
