"""A scripted call tree: one orchestrator, N sub-agents, per-node records.

Track 0.2-0.4. This is the instrument for Tracks B through F, and it is
deliberately **not** the real Task tool.

**Why scripted.** The Task tool is ecologically truer and experimentally
useless: we could not hold anything fixed, could not ablate a sub-agent's
report, and could not keep ``--tools ""`` at every node. Here the tree is our
Python code driving separate isolated CLI calls, so every edge is something we
choose. The real Task tool returns in Track F as a validity check against this,
never as the instrument.

**Fan out once, aggregate once.** Sub-agents run first on their assigned
sub-tasks; the orchestrator then sees their reports and produces the answer.
The split is scripted rather than decided by the model, because a model-chosen
split varies between arms and would confound every comparison drawn across it.

**The substitution hook is the whole point.** :attr:`Dispatch.transform` sits
between a sub-agent's report and what the orchestrator reads. Passing a report
through unchanged is the control; dropping it is an ablation; replacing it with
a known-wrong one is how Track B attributes a failure to a node rather than to
the system. Without that seam this module would be an expensive way to make four
calls.

**Nothing here is scored.** :class:`NodeRecord` has no correctness field, for
the same reason :class:`~decision_evals.sharded.ShardedRecord` does not: 21 of 21
scored failures across three corpora were the answer key.

**Every node runs on the streaming transport, including single-turn ones.** That
is not incidental. The isolation receipt is the CLI's ``system``/``init`` event,
which only ``--output-format stream-json`` emits -- the single-shot JSON form
gives no receipt at all. Asserting isolation *at every node* (0.3) therefore
forces the streaming transport everywhere, and the alternative would have been to
assert it at the root and assume it for the leaves, which is the assumption a
sub-agent experiment least deserves.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Final

from decision_evals.budget import BudgetLedger, estimate_cost_usd
from decision_evals.providers.claude_code import CliResult, Conversation
from decision_evals.telemetry import (
    OP_INVOKE_AGENT,
    OP_INVOKE_WORKFLOW,
    RECORD_SCHEMA_VERSION,
    NodeIdentity,
)

#: The orchestrator's node name and id. Fixed so a record can be found without
#: knowing how the tree was built.
ROOT: Final = "orchestrator"

#: What a dropped report is replaced with. Stated rather than silently omitted:
#: an orchestrator given three headings and two reports can notice, and one given
#: two headings cannot, and those are different experiments.
ABLATED: Final = "[no report was returned by this sub-agent]"


class OrchestratorError(RuntimeError):
    """The tree could not be run as specified."""


#: Rewrites a sub-agent's report before the orchestrator reads it. Returning
#: ``None`` ablates the report.
ReportTransform = Callable[[str], str | None]


@dataclass(frozen=True)
class Dispatch:
    """One sub-agent: what it is asked, and what the orchestrator then sees.

    Attributes:
        name: Node name, unique within the tree.
        system_prompt: This node's full system-prompt replacement.
        prompt: What this node is asked. Scripted, not model-chosen.
        transform: Applied to the report before the orchestrator reads it.
            ``None`` return ablates it. Defaults to passing it through, which is
            the control condition.
    """

    name: str
    system_prompt: str
    prompt: str
    transform: ReportTransform | None = None


@dataclass(frozen=True)
class NodeRecord:
    """What one node did. Raw outputs only -- nothing scored.

    Attributes:
        report_seen_by_parent: What the orchestrator actually read, after
            :attr:`Dispatch.transform`. Stored separately from ``response``
            because when the two differ that difference *is* the manipulation,
            and a record holding only one of them cannot describe the run.
        prompt_tokens: ``input + cache_creation + cache_read``. The CLI's
            ``input_tokens`` alone is the uncached remainder.
    """

    conversation_id: str
    node_name: str
    node_id: str
    parent_node_id: str | None
    operation: str
    model: str
    prompt: str
    response: str
    report_seen_by_parent: str | None
    prompt_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    schema_version: int = RECORD_SCHEMA_VERSION

    @property
    def was_transformed(self) -> bool:
        """Whether the parent read something other than what this node said."""
        return (
            self.report_seen_by_parent is not None and self.report_seen_by_parent != self.response
        )


@dataclass(frozen=True)
class TreeResult:
    """One complete run of the tree.

    Attributes:
        ledger: The budget after the whole tree. Accounting is over the *tree*
            rather than the call: a per-call limit cannot stop a run that makes
            four calls per item, which is the shape every track from B onward
            has.
    """

    conversation_id: str
    records: tuple[NodeRecord, ...]
    ledger: BudgetLedger
    receipts_asserted: int = 0

    @property
    def final_response(self) -> str:
        """What the orchestrator concluded."""
        for record in self.records:
            if record.node_name == ROOT:
                return record.response
        raise OrchestratorError("the tree produced no orchestrator record")

    @property
    def total_cost_usd(self) -> float:
        return sum(record.cost_usd for record in self.records)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(record.prompt_tokens for record in self.records)

    @property
    def n_nodes(self) -> int:
        return len(self.records)


def render_reports(dispatches: Sequence[Dispatch], reports: Sequence[str | None]) -> str:
    """Lay the sub-agent reports out for the orchestrator.

    The heading for an ablated report is still emitted, carrying
    :data:`ABLATED`. An orchestrator that can see a sub-agent returned nothing
    and one that cannot even see it was dispatched are different conditions, and
    silently dropping the heading would make the ablation arm secretly also a
    fan-out-width manipulation.
    """
    if len(dispatches) != len(reports):
        raise OrchestratorError(
            f"{len(dispatches)} dispatches but {len(reports)} reports; "
            "these are zipped positionally and a mismatch would misattribute one"
        )
    blocks = [
        f"## Report from {dispatch.name}\n\n{report if report is not None else ABLATED}"
        for dispatch, report in zip(dispatches, reports, strict=True)
    ]
    return "\n\n".join(blocks)


#: How one isolated node is run. Injected so the tree is testable without a
#: model, and so Track F can swap in the real Task tool behind the same seam.
NodeRunner = Callable[[str, str, str], CliResult]


def _default_runner(model: str) -> tuple[NodeRunner, Callable[[], int]]:
    """A runner that opens one isolated conversation per node.

    Each node gets a **fresh working directory**. The CLI's auto-memory path is
    keyed on the cwd, so a shared directory would be a cross-node state channel
    that a checkpointed run could not see -- latent under ``--tools ""`` today
    and live the moment Track F relaxes it.
    """
    asserted = 0

    def run_node(system_prompt: str, prompt: str, node_name: str) -> CliResult:
        nonlocal asserted
        with (
            tempfile.TemporaryDirectory() as cwd,
            Conversation(system_prompt=system_prompt, model=model, cwd=cwd) as chat,
        ):
            result = chat.send(prompt)
            # Asserted per node, not once per tree. A sub-agent that loaded a
            # skill off disk while the root did not is exactly the confound a
            # delegation experiment cannot survive, and it is invisible in the
            # response text.
            chat.receipt.assert_isolated()
            asserted += 1
        return result

    return run_node, lambda: asserted


def run_tree(
    *,
    task: str,
    orchestrator_system_prompt: str,
    orchestrator_template: str,
    dispatches: Sequence[Dispatch],
    conversation_id: str,
    ledger: BudgetLedger,
    model: str = "haiku",
    runner: NodeRunner | None = None,
    receipts: Callable[[], int] | None = None,
) -> TreeResult:
    """Fan out to every dispatch, then aggregate in the orchestrator.

    Args:
        orchestrator_template: Must contain ``{task}`` and ``{reports}``. Checked
            before any call is made, because discovering it after the sub-agents
            have run wastes their quota and produces a half-tree.
        ledger: Authorises each node *before* it runs, using the length of that
            node's prompt. A tree that cannot afford its orchestrator must fail
            before its sub-agents burn quota, so the orchestrator's cost is
            reserved up front.

    Raises:
        OrchestratorError: The template is malformed, the dispatch names are not
            unique, or there are no dispatches.
        BudgetError: Via the ledger, before the offending call.
    """
    if not dispatches:
        raise OrchestratorError("a tree with no sub-agents is a single call; use `providers.run`")
    names = [dispatch.name for dispatch in dispatches]
    if len(set(names)) != len(names):
        raise OrchestratorError(f"dispatch names must be unique, got {names}")
    if ROOT in names:
        raise OrchestratorError(f"{ROOT!r} is reserved for the aggregating node")
    for placeholder in ("{task}", "{reports}"):
        if placeholder not in orchestrator_template:
            raise OrchestratorError(
                f"orchestrator_template is missing {placeholder}. Checked before any "
                "call, because finding out afterwards costs the sub-agents' quota "
                "and leaves half a tree in the records."
            )

    if runner is None:
        runner, receipts = _default_runner(model)

    records: list[NodeRecord] = []
    reports: list[str | None] = []

    for index, dispatch in enumerate(dispatches):
        ledger.assert_can_afford(estimate_cost_usd(prompt_chars=len(dispatch.prompt)))
        result = runner(dispatch.system_prompt, dispatch.prompt, dispatch.name)
        ledger = ledger.record(result.cost_usd)

        seen = dispatch.transform(result.text) if dispatch.transform else result.text
        reports.append(seen)
        records.append(
            _record(
                identity=NodeIdentity(
                    conversation_id=conversation_id,
                    node_name=dispatch.name,
                    node_id=f"{conversation_id}/{index}",
                    parent_node_id=f"{conversation_id}/{ROOT}",
                    operation=OP_INVOKE_AGENT,
                ),
                prompt=dispatch.prompt,
                result=result,
                report_seen_by_parent=seen,
            )
        )

    aggregate_prompt = orchestrator_template.format(
        task=task, reports=render_reports(dispatches, reports)
    )
    ledger.assert_can_afford(estimate_cost_usd(prompt_chars=len(aggregate_prompt)))
    root_result = runner(orchestrator_system_prompt, aggregate_prompt, ROOT)
    ledger = ledger.record(root_result.cost_usd)
    records.append(
        _record(
            identity=NodeIdentity(
                conversation_id=conversation_id,
                node_name=ROOT,
                node_id=f"{conversation_id}/{ROOT}",
                parent_node_id=None,
                operation=OP_INVOKE_WORKFLOW,
            ),
            prompt=aggregate_prompt,
            result=root_result,
            report_seen_by_parent=None,
        )
    )

    return TreeResult(
        conversation_id=conversation_id,
        records=tuple(records),
        ledger=ledger,
        receipts_asserted=receipts() if receipts else 0,
    )


def _record(
    *,
    identity: NodeIdentity,
    prompt: str,
    result: CliResult,
    report_seen_by_parent: str | None,
) -> NodeRecord:
    return NodeRecord(
        conversation_id=identity.conversation_id,
        node_name=identity.node_name,
        node_id=identity.node_id,
        parent_node_id=identity.parent_node_id,
        operation=identity.operation,
        model=result.model,
        prompt=prompt,
        response=result.text,
        report_seen_by_parent=report_seen_by_parent,
        prompt_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        duration_ms=result.duration_ms,
    )


def append_records(path: Path, result: TreeResult) -> None:
    """Append every node of one tree to a JSONL checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in result.records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def load_records(path: Path) -> list[NodeRecord]:
    """Read a checkpoint back, refusing anything it does not understand.

    An unknown column raises rather than being dropped. A loader that swallows
    ``TypeError`` makes every earlier checkpoint line vanish the moment a field
    is added, and the run looks empty rather than incompatible.
    """
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(NodeRecord(**json.loads(line)))
        except TypeError as error:
            raise OrchestratorError(
                f"{path}:{number}: record does not match NodeRecord: {error}"
            ) from error
    return records


@dataclass(frozen=True)
class TreeBudgetReport:
    """Cost and wall-clock over a call tree rather than a call.

    Track 0.4. ``duration_ms`` is **summed, not maximised**: the tree runs
    serially, so the wall clock a maintainer waits through is the sum. If
    dispatch is ever parallelised this becomes wrong, which is why it says so
    here rather than being inferred from the number.
    """

    n_trees: int
    n_nodes: int
    total_cost_usd: float
    total_prompt_tokens: int
    total_duration_ms: int
    by_node: dict[str, float] = field(default_factory=dict)

    @property
    def usd_per_tree(self) -> float:
        return self.total_cost_usd / self.n_trees if self.n_trees else 0.0


def summarise(results: Sequence[TreeResult]) -> TreeBudgetReport:
    """Aggregate cost and wall-clock across trees, and per node name.

    ``by_node`` is what makes this worth having over a single total: a tree
    whose orchestrator costs eight times each sub-agent is a different design
    problem from one where the sub-agents dominate, and the total cannot tell
    them apart.
    """
    by_node: dict[str, float] = {}
    nodes = tokens = duration = 0
    cost = 0.0
    for result in results:
        for record in result.records:
            nodes += 1
            cost += record.cost_usd
            tokens += record.prompt_tokens
            duration += record.duration_ms
            by_node[record.node_name] = by_node.get(record.node_name, 0.0) + record.cost_usd
    return TreeBudgetReport(
        n_trees=len(results),
        n_nodes=nodes,
        total_cost_usd=cost,
        total_prompt_tokens=tokens,
        total_duration_ms=duration,
        by_node=by_node,
    )
