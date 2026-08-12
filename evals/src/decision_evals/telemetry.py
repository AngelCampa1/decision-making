"""OpenTelemetry GenAI attribute names, hardcoded on purpose.

Track 0.5. A multi-node run needs node identity, a parent, a turn index and a
trace id on every record, and there is a vendor-neutral vocabulary for exactly
that. Hand-rolling a trace schema when one exists is a real weakness, and
MAST-style attribution needs structured traces regardless.

**We adopt the names and not the package.** Every string below was read from
``open-telemetry/semantic-conventions-genai`` at commit :data:`SEMCONV_COMMIT`
and is pinned here. Three facts make importing the library's constants the wrong
call:

* the specification is status **Development**;
* the repository has **zero releases** — checked 2026-08-11, HEAD pushed the day
  before;
* it has already renamed a field in flight, ``gen_ai.system`` →
  ``gen_ai.provider.name``.

A rename upstream would silently change what our columns are called, and columns
that change name between runs are indistinguishable from columns that changed
meaning. Hardcoding costs one edit when the spec settles and buys a record
format that cannot move underneath a result. Nothing here imports
``opentelemetry``; there is no runtime dependency and no socket.

One correction worth recording, because it nearly went the other way. The
inference-span document does **not** list ``gen_ai.agent.name``, and on that
evidence the programme looked wrong to have named it. It is in the attribute
registry, at Development stability, along with ``gen_ai.agent.id`` and
``gen_ai.evaluation.*``. The first document checked is not the specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

#: Provenance of every string in this module. Recorded per run so a record can
#: be read years later against the vocabulary it was written under.
SEMCONV_REPO: Final = "open-telemetry/semantic-conventions-genai"
SEMCONV_COMMIT: Final = "8d3e4a0f3c34a46f6edb9c71e8666e02e6bf3958"
SEMCONV_STABILITY: Final = "development"

# --------------------------------------------------------------------------- #
# Attribute names. Verified in the registry at SEMCONV_COMMIT, 2026-08-11.
# --------------------------------------------------------------------------- #
OPERATION_NAME: Final = "gen_ai.operation.name"
PROVIDER_NAME: Final = "gen_ai.provider.name"
CONVERSATION_ID: Final = "gen_ai.conversation.id"
AGENT_NAME: Final = "gen_ai.agent.name"
AGENT_ID: Final = "gen_ai.agent.id"
REQUEST_MODEL: Final = "gen_ai.request.model"
RESPONSE_MODEL: Final = "gen_ai.response.model"
USAGE_INPUT_TOKENS: Final = "gen_ai.usage.input_tokens"
USAGE_OUTPUT_TOKENS: Final = "gen_ai.usage.output_tokens"
EVALUATION_NAME: Final = "gen_ai.evaluation.name"
EVALUATION_SCORE: Final = "gen_ai.evaluation.score.value"

#: Well-known ``gen_ai.operation.name`` values we actually emit. The registry
#: lists eighteen; these are the three this harness produces.
OP_CHAT: Final = "chat"
OP_INVOKE_AGENT: Final = "invoke_agent"
OP_INVOKE_WORKFLOW: Final = "invoke_workflow"

#: Well-known ``gen_ai.provider.name`` value. Note what this does *not* say: the
#: calls go through the Claude Code CLI on a subscription, not the Anthropic API,
#: and the registry has no value for a CLI. The provider of the model is
#: ``anthropic``; how we reach it is recorded separately in
#: ``docs/HARNESS_DISCLOSURE.md`` and must not be inferred from this field.
PROVIDER_ANTHROPIC: Final = "anthropic"

#: Attributes with no registry equivalent. Namespaced away from ``gen_ai.`` so
#: that ours and theirs are never confused, which is the whole reason for
#: adopting a vocabulary rather than inventing one.
NODE_PARENT_ID: Final = "decision_evals.node.parent_id"
TURN_INDEX: Final = "decision_evals.turn.index"
ARM: Final = "decision_evals.arm"
SCHEMA_VERSION: Final = "decision_evals.schema.version"

#: Bumped whenever ``RunRecord`` gains or loses a field. Version 1 is the
#: single-call schema every record in ``results/`` was written under.
RECORD_SCHEMA_VERSION: Final = 2


@dataclass(frozen=True, slots=True)
class NodeIdentity:
    """Where a call sits in a run tree.

    A single ``claude -p`` call — every record this repository has produced so
    far — is the degenerate case: no parent, no turn index. Those fields are
    ``None`` because that is *true* of a single call, not because the value is
    missing.

    Attributes:
        conversation_id: Groups every node and turn of one run. The
            ``gen_ai.conversation.id`` of the whole tree.
        node_name: Which agent this is, e.g. ``orchestrator`` or
            ``sub-agent-2``.
        node_id: Unique within the run.
        parent_node_id: The node that dispatched this one, or ``None`` at the
            root.
        turn_index: 0-based turn within this node's conversation, or ``None``
            for a single-shot call.
        operation: One of :data:`OP_CHAT`, :data:`OP_INVOKE_AGENT`,
            :data:`OP_INVOKE_WORKFLOW`.
    """

    conversation_id: str
    node_name: str = "root"
    node_id: str = "root"
    parent_node_id: str | None = None
    turn_index: int | None = None
    operation: str = OP_CHAT

    @property
    def is_root(self) -> bool:
        """Whether this node was dispatched by nothing."""
        return self.parent_node_id is None


def span_name(operation: str, model: str) -> str:
    """``{gen_ai.operation.name} {gen_ai.request.model}``, per the spec.

    Quoting the convention verbatim: *"Span name SHOULD be
    `{gen_ai.operation.name} {gen_ai.request.model}`"*.
    """
    return f"{operation} {model}"


def span_attributes(
    identity: NodeIdentity,
    *,
    request_model: str,
    response_model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    arm: str | None = None,
    evaluation_name: str | None = None,
    evaluation_score: float | None = None,
) -> dict[str, Any]:
    """Build a span-attribute mapping using the pinned vocabulary.

    Only attributes with a value are emitted. An absent attribute and an
    attribute set to ``None`` mean different things to every trace consumer, and
    a record full of nulls is harder to read than a short one.

    Args:
        identity: Where this call sits in the run tree.
        request_model: The model asked for.
        response_model: The model that answered. Worth recording separately: a
            subscription can serve a different build than the alias requested,
            and a silent substitution mid-run would otherwise be invisible.
        input_tokens: Prompt tokens. Callers must pass the *real* prompt size —
            ``input + cache_creation + cache_read`` — because the CLI's
            ``input_tokens`` alone is the uncached remainder and reported 10 for
            a 380 KB casefile.
        output_tokens: Completion tokens.
        arm: Experimental arm, ours rather than the spec's.
        evaluation_name: What was scored, e.g. ``admissibility``.
        evaluation_score: The score.

    Returns:
        A flat mapping ready to attach to a span or to serialise into a record.
    """
    attributes: dict[str, Any] = {
        OPERATION_NAME: identity.operation,
        PROVIDER_NAME: PROVIDER_ANTHROPIC,
        CONVERSATION_ID: identity.conversation_id,
        AGENT_NAME: identity.node_name,
        AGENT_ID: identity.node_id,
        REQUEST_MODEL: request_model,
        SCHEMA_VERSION: RECORD_SCHEMA_VERSION,
    }

    optional: dict[str, Any] = {
        RESPONSE_MODEL: response_model,
        USAGE_INPUT_TOKENS: input_tokens,
        USAGE_OUTPUT_TOKENS: output_tokens,
        NODE_PARENT_ID: identity.parent_node_id,
        TURN_INDEX: identity.turn_index,
        ARM: arm,
        EVALUATION_NAME: evaluation_name,
        EVALUATION_SCORE: evaluation_score,
    }
    attributes.update({key: value for key, value in optional.items() if value is not None})
    return attributes


def provenance() -> dict[str, str]:
    """What vocabulary this run's attribute names came from.

    Written into every run config. The spec is unreleased and moving, so a
    record that does not say which commit it was written against cannot be
    safely compared with one written a month later.
    """
    return {
        "semconv_repo": SEMCONV_REPO,
        "semconv_commit": SEMCONV_COMMIT,
        "semconv_stability": SEMCONV_STABILITY,
    }
