"""Model backends.

Only one for now: the Claude Code CLI driven as a subprocess. See
``docs/HARNESS_DISCLOSURE.md`` for why this backend rather than
``inspect_swe``'s ``claude_code()`` solver, and
``notebook/2026-08-10-inspect-swe-spike-verdict.md`` for the spike that decided
it.
"""

from decision_evals.providers.claude_code import (
    ISOLATION_FLAGS,
    AuthenticationError,
    CliError,
    CliResult,
    build_command,
    parse_result,
)

__all__ = [
    "ISOLATION_FLAGS",
    "AuthenticationError",
    "CliError",
    "CliResult",
    "build_command",
    "parse_result",
]
