"""Measure the shipped skill's description: does it fire when it should?

Track M / Track S. Skill availability is the dominant term in whether a skill
helps at all, and availability is decided by the description. This has never
been measured here on any skill.

**It needs no answer key**, which is why it is worth running now. The labels are
trigger labels -- did it fire, and did the router pick the procedure its own
table names -- not judgements about answer quality. That sidesteps the failure
mode behind 21 of 21 scored errors in this repository.

**It is a proxy and says so.** The model is shown the description and asked
whether it would invoke the skill. The real harness decides differently: the
description sits among other skills, in a longer context, with the model
mid-task. This measures the description's discriminative content, not the
deployed firing rate.

Each case is one isolated call with a fresh working directory and the isolation
receipt asserted, so nothing on disk can influence the decision.

Usage:
    python scripts/run_triggers.py [--model haiku] [--skill decision-making]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decision_evals.providers.claude_code import (  # noqa: E402
    CliError,
    Conversation,
    IsolationError,
)
from decision_evals.skills import parse_skill  # noqa: E402
from decision_evals.triggers import (  # noqa: E402
    TRIGGERS_DIR,
    TriggerCase,
    evaluate,
    evaluate_routing,
    load_trigger_set,
)

PROCEDURES = ("ledger", "fit", "cascade", "timing")

#: The judge sees the skill's own description and router table and nothing else.
#: Not the procedure bodies: what the harness has in context when it decides
#: whether to fire is the frontmatter description, and giving it more would
#: measure a document that is never consulted at that moment.
SYSTEM = (
    "You decide whether a tool should be used. You are given one tool's "
    "description and one message a user sent. Answer with a single line of "
    "JSON and nothing else:\n"
    '{"fire": true|false, "procedure": "ledger"|"fit"|"cascade"|"timing"|null}\n'
    "`fire` is whether this tool should be invoked for this message. "
    "`procedure` is which of the tool's four procedures applies, or null if you "
    "would not invoke it or cannot tell."
)

_JSON = re.compile(r"\{[^{}]*\}")


def decision(text: str) -> tuple[bool | None, str | None]:
    """Parse the verdict, returning ``(None, None)`` when the format was ignored.

    Unparseable answers are counted and excluded rather than read as "did not
    fire". A model that will not answer in the format has told us about format
    compliance, and scoring that silence as a negative would flatter precision.
    """
    match = _JSON.search(text)
    if not match:
        return None, None
    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError:
        return None, None
    fired = payload.get("fire")
    if not isinstance(fired, bool):
        return None, None
    procedure = payload.get("procedure")
    return fired, procedure if procedure in PROCEDURES else None


def ask(description: str, case: TriggerCase, model: str) -> tuple[bool | None, str | None]:
    prompt = f"## Tool description\n\n{description}\n\n## User message\n\n{case.turn}"
    with (
        tempfile.TemporaryDirectory() as cwd,
        Conversation(system_prompt=SYSTEM, model=model, cwd=cwd) as chat,
    ):
        result = chat.send(prompt)
        chat.receipt.assert_isolated()
    return decision(result.text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--skill", default="decision-making")
    args = parser.parse_args()

    trigger_set = load_trigger_set(REPO_ROOT / TRIGGERS_DIR / f"{args.skill}.yaml")
    document = parse_skill(REPO_ROOT / "skills" / args.skill / "SKILL.md")
    description = str(document.frontmatter["description"]).strip()

    print(
        f"{args.skill}: {len(trigger_set.positives)} positive, {len(trigger_set.negatives)} negative"
    )
    print(f"description: {len(description)} chars\n")

    verdicts: dict[str, bool] = {}
    routes: dict[str, str | None] = {}
    unparseable: list[str] = []

    for index, case in enumerate(trigger_set.cases, start=1):
        try:
            fired, procedure = ask(description, case, args.model)
        except IsolationError as error:
            print(f"ISOLATION FAILURE at {case.id}, stopping: {error}")
            return 1
        except CliError as error:
            print(f"  {case.id}: call failed, excluded -- {error}")
            unparseable.append(case.id)
            continue

        if fired is None:
            unparseable.append(case.id)
            print(f"  {case.id}: unparseable, excluded")
            continue

        verdicts[case.turn] = fired
        routes[case.turn] = procedure
        wanted = "fire" if case.should_fire else "skip"
        got = "fire" if fired else "skip"
        mark = " " if wanted == got else "X"
        extra = f" -> {procedure}" if fired else ""
        print(
            f"  [{index:2}/{len(trigger_set.cases)}] {mark} {case.id:6} want {wanted} got {got}{extra}"
        )

    scored = tuple(c for c in trigger_set.cases if c.turn in verdicts)
    if len(scored) < 0.9 * len(trigger_set.cases):
        print(f"\n*** parse rate {len(scored) / len(trigger_set.cases):.0%}, below the 90% floor.")
        print("*** This measured format compliance rather than firing. Stopping.")
        return 1

    subset = type(trigger_set)(skill=trigger_set.skill, cases=scored)
    report = evaluate(subset, lambda turn: verdicts[turn])
    routing = evaluate_routing(subset, lambda turn: routes[turn])

    print(f"\n{'=' * 60}\nFIRING  (primary)\n{'=' * 60}")
    print(f"  precision            {report.precision:.3f}")
    print(f"  recall               {report.recall:.3f}")
    print(f"  false-positive rate  {report.false_positive_rate:.3f}   <- the daily-use cost")
    print(
        f"  tp {report.true_positives}  fp {report.false_positives}  "
        f"tn {report.true_negatives}  fn {report.false_negatives}"
    )
    if report.missed:
        print(f"  missed: {', '.join(report.missed)}")

    print(f"\n{'=' * 60}\nROUTING  (secondary -- the easier question)\n{'=' * 60}")
    print(
        f"  accuracy   {routing.accuracy:.3f} over {routing.n_scored} labelled "
        f"({routing.unlabelled} excluded as open)"
    )
    for case_id, wanted, got in routing.confusions:
        print(f"    {case_id}: wanted {wanted}, got {got}")

    print(f"\nexcluded {len(unparseable)}: {', '.join(unparseable) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
