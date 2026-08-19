"""Model backends.

Two. The Claude Code CLI driven as a subprocess, which is every call this
repository has published; see ``docs/HARNESS_DISCLOSURE.md`` for why this
backend rather than ``inspect_swe``'s ``claude_code()`` solver, and
``notebook/2026-08-10-inspect-swe-spike-verdict.md`` for the spike that decided
it. And an OpenAI-compatible HTTP server, which is the ``dev`` arena
``docs/PROTOCOL.md`` §2 has declared since it was written.

They are not interchangeable and :mod:`decision_evals.arenas` is what stops them
being treated as though they were. A local model is free, unmetered and cannot
emit a verdict; the CLI is the only backend that reaches ``screen`` and
``confirm``. The shared surface is :class:`CliResult` and the two error types
:mod:`decision_evals.runner` catches, so a runner does not know which one it is
driving -- which is the point, and also the reason the arena gate is in code
rather than in a convention.
"""

from decision_evals.providers.claude_code import (
    ISOLATION_FLAGS,
    AuthenticationError,
    CliError,
    CliResult,
    IsolationError,
    PromptTooLongError,
    build_command,
    parse_result,
)
from decision_evals.providers.openai_compatible import (
    Endpoint,
    ModelCard,
    assert_isolated,
    ollama,
    show,
)

__all__ = [
    "ISOLATION_FLAGS",
    "AuthenticationError",
    "CliError",
    "CliResult",
    "Endpoint",
    "IsolationError",
    "ModelCard",
    "PromptTooLongError",
    "assert_isolated",
    "build_command",
    "ollama",
    "parse_result",
    "show",
]
