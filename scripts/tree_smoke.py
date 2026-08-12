"""Track 0.2/0.3: one live 4-node tree, with the isolation canary at every node.

The tree runs twice on the same task -- once with every report passed through,
once with one report ablated -- because a tree that runs is not evidence that
the *seam* works. If the orchestrator's answer is identical with and without a
sub-agent's report, either the report carried nothing or the substitution never
reached the prompt, and neither is distinguishable from success on a control run
alone.

**The second run pins the surviving reports to the first run's text, and the
first version of this script did not.** That version was confounded and the run
proved it: `customer-impact` answered on the control pass and declined on the
ablation pass from the identical prompt, so two things differed between the arms
and the orchestrator's changed answer could not be attributed to either. This is
Track I's finding arriving in a new place -- most of the variance in a repeated
model call is scatter -- and it means **every ablation in Tracks B through F must
hold the surviving reports fixed**, or it measures resampling.

Pinning costs nothing extra to build: it is the same ``transform`` seam, handed
a constant. The sub-agent is still called and still recorded, so the record
shows both what it said on this pass and what the orchestrator was actually
given.

Rule 3: nothing here is scored. It reports what each node said and what the
orchestrator read.

Usage:
    python scripts/tree_smoke.py [--model haiku]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decision_evals.budget import BudgetLedger  # noqa: E402
from decision_evals.orchestrator import (  # noqa: E402
    ROOT,
    Dispatch,
    append_records,
    run_tree,
    summarise,
)
from decision_evals.providers.claude_code import IsolationError  # noqa: E402

CHECKPOINT = REPO_ROOT / "results" / "track-0" / "tree_smoke.jsonl"

TASK = (
    "A team must choose between shipping a feature on Friday or waiting until "
    "Monday. Recommend one and say why in under 80 words."
)

#: Each sub-agent sees one slice and nothing else. The split is scripted rather
#: than model-chosen, because a model-chosen split varies between arms and would
#: confound every comparison drawn across it.
#:
#: "Everything you need is in the question" is load-bearing. Without it the
#: sub-agents replied "I don't have access to your team's on-call scheduling
#: data" to a question that stated the on-call hours, and a node that declines
#: is not a node reporting a finding.
SUB_SYSTEM = (
    "You are one analyst on a team. Everything you need is stated in the "
    "question; there is no other source to consult and no data to request. "
    "Answer only the question you are given, from the facts in it, in under 60 "
    "words. Do not recommend an overall course of action -- that is someone "
    "else's job."
)

ROOT_SYSTEM = (
    "You are deciding on behalf of a team, using reports from analysts who each "
    "saw one part of the picture. Give one recommendation in under 80 words."
)

ROOT_TEMPLATE = "{task}\n\nYour analysts reported:\n\n{reports}"

QUESTIONS = {
    "release-risk": (
        "The deploy pipeline has no automatic rollback and the on-call engineer "
        "is away this weekend. What is the release risk?"
    ),
    "customer-impact": (
        "Three enterprise customers have asked for this feature and one has a "
        "renewal decision next Wednesday. What is the customer impact of waiting?"
    ),
    "team-load": (
        "Two of the four engineers are already past their on-call hours this "
        "month. What is the team-load picture?"
    ),
}


def _dispatches(ablate: str | None = None, pinned: dict[str, str] | None = None) -> list[Dispatch]:
    """Build the fan-out, optionally ablating one node and pinning the rest.

    ``pinned`` holds the surviving reports at the control run's text. Without it
    the ablation arm differs from the control arm in every sub-agent's output at
    once, and the orchestrator's answer cannot be attributed to the ablation.
    """
    dispatches = []
    for name, question in QUESTIONS.items():
        if name == ablate:
            transform: object = lambda _: None  # noqa: E731
        elif pinned is not None:
            # Default-arg binding, not closure capture: a bare `lambda _: text`
            # in a loop captures the variable and every dispatch would receive
            # the last report.
            transform = lambda _, text=pinned[name]: text  # noqa: E731
        else:
            transform = None
        dispatches.append(
            Dispatch(
                name=name,
                system_prompt=SUB_SYSTEM,
                prompt=question,
                transform=transform,  # type: ignore[arg-type]
            )
        )
    return dispatches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--ablate", default="release-risk", help="which report to drop in run 2")
    args = parser.parse_args()

    ledger = BudgetLedger(limit_usd=2.0)
    results = []
    pinned: dict[str, str] | None = None

    for label, ablate in (("control", None), (f"ablate:{args.ablate}", args.ablate)):
        print(f"\n{'=' * 72}\n{label}\n{'=' * 72}")
        try:
            result = run_tree(
                task=TASK,
                orchestrator_system_prompt=ROOT_SYSTEM,
                orchestrator_template=ROOT_TEMPLATE,
                dispatches=_dispatches(ablate, pinned),
                conversation_id=f"smoke-{label}",
                ledger=ledger,
                model=args.model,
            )
        except IsolationError as error:
            print(f"ISOLATION FAILURE, stopping: {error}")
            return 1

        if pinned is None:
            # Hold the surviving reports at what the control run produced, so
            # the ablation arm differs in exactly one place.
            pinned = {
                record.node_name: record.response
                for record in result.records
                if record.node_name != ROOT
            }

        ledger = result.ledger
        results.append(result)
        append_records(CHECKPOINT, result)

        print(f"nodes {result.n_nodes}   receipts asserted {result.receipts_asserted}")
        for record in result.records:
            if record.node_name == ROOT:
                continue
            read = record.report_seen_by_parent
            state = "passed through" if read == record.response else f"REWRITTEN -> {read!r}"
            print(f"\n  [{record.node_name}] {state}")
            print(f"      said: {record.response.strip()[:160]}")
        print(f"\n  [{ROOT}] {result.final_response.strip()[:400]}")

    control, ablated = (r.final_response.strip() for r in results)
    print(f"\n{'=' * 72}\nSEAM CHECK\n{'=' * 72}")
    if control == ablated:
        print("*** The two orchestrator answers are byte-identical.")
        print("*** Either the dropped report carried nothing, or the ablation never")
        print("*** reached the prompt. Both are instrument failures and neither is")
        print("*** distinguishable from success on a control run alone.")
    else:
        print("the answers differ, so the ablation reached the orchestrator")

    report = summarise(results)
    print(f"\nnodes {report.n_nodes} across {report.n_trees} trees")
    print(f"notional cost ${report.total_cost_usd:.3f}  (subscription; nothing is billed)")
    print(f"wall clock {report.total_duration_ms / 1000:.0f}s (summed; the tree runs serially)")
    print("cost by node: " + ", ".join(f"{k} ${v:.3f}" for k, v in sorted(report.by_node.items())))
    print(f"checkpoint: {CHECKPOINT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
