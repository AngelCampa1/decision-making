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
                                   [--repeats 5] [--confidence]

``--confidence`` additionally elicits a probability and scores it. It writes to
its own checkpoint: asking for a probability changes the response contract, so a
confidence run and a plain one are two runs, not one run with an extra column.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decision_evals.providers.claude_code import (  # noqa: E402
    CliError,
    Conversation,
    IsolationError,
    isolated_cwd,
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

#: The same task with a probability attached. Track K6 ranks *elicited
#: confidence* above every other framework-derived skill candidate on evidence
#: strength, and `stats/calibration.py` has been property-tested to 100% coverage
#: since the first week without ever being called by anything. This is the first
#: forecast this repository has asked a model for.
#:
#: It asks for **P(this tool should be invoked)**, not for confidence in the
#: model's own answer. The two are different quantities and only the first is a
#: forecast: it has an outcome -- the case's label -- so Brier, the Murphy
#: decomposition and a reliability diagram all apply directly. "How sure are you"
#: about one's own output has no outcome to score against without deciding the
#: output was wrong, which is the act this repository does not perform.
#:
#: `fire` stays a separate hard decision so the firing metrics keep their shape
#: and the two runs stay comparable on that axis -- but only on that axis. Asking
#: for a probability changes the response contract, which can change the decision,
#: so a confidence run gets its own checkpoint and must not be pooled with a
#: plain one.
SYSTEM_CONFIDENCE = (
    "You decide whether a tool should be used. You are given one tool's "
    "description and one message a user sent. Answer with a single line of "
    "JSON and nothing else:\n"
    '{"fire": true|false, "procedure": "ledger"|"fit"|"cascade"|"timing"|null, '
    '"p_fire": 0.0}\n'
    "`fire` is whether this tool should be invoked for this message. "
    "`procedure` is which of the tool's four procedures applies, or null if you "
    "would not invoke it or cannot tell. "
    "`p_fire` is your probability between 0 and 1 that this tool should be "
    "invoked -- not how confident you are in your own answer. Use the full range: "
    "0.5 means genuinely undecided, and a well-calibrated 0.7 is right about "
    "seven times in ten."
)

_JSON = re.compile(r"\{[^{}]*\}")


Verdict = tuple[bool | None, str | None, float | None]


def decision(text: str) -> Verdict:
    """Parse the verdict, returning ``(None, None, None)`` when format was ignored.

    Unparseable answers are counted and excluded rather than read as "did not
    fire". A model that will not answer in the format has told us about format
    compliance, and scoring that silence as a negative would flatter precision.

    ``p_fire`` is returned as ``None`` when absent or out of ``[0, 1]``, and its
    absence never invalidates the verdict: a run that asked for a probability and
    got a usable decision without one has produced a firing observation and no
    forecast, which is exactly what should be recorded.
    """
    match = _JSON.search(text)
    if not match:
        return None, None, None
    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError:
        return None, None, None
    fired = payload.get("fire")
    if not isinstance(fired, bool):
        return None, None, None
    procedure = payload.get("procedure")
    raw = payload.get("p_fire")
    p_fire = float(raw) if isinstance(raw, int | float) and 0.0 <= raw <= 1.0 else None
    return fired, procedure if procedure in PROCEDURES else None, p_fire


def ask(description: str, case: TriggerCase, model: str, system: str) -> Verdict:
    prompt = f"## Tool description\n\n{description}\n\n## User message\n\n{case.turn}"
    with (
        isolated_cwd("de-trigger-") as cwd,
        Conversation(system_prompt=system, model=model, cwd=cwd) as chat,
    ):
        result = chat.send(prompt)
        chat.receipt.assert_isolated()
    return decision(result.text)


CHECKPOINT = REPO_ROOT / "results" / "triggers" / "verdicts.jsonl"

#: A separate file, not a column. Asking for a probability changes the response
#: contract and can change the decision, so the two runs are not one run with an
#: extra field -- and a shared path plus a resume would have silently merged them.
CHECKPOINT_CONFIDENCE = REPO_ROOT / "results" / "triggers" / "verdicts-confidence.jsonl"


def load_done(path: Path) -> dict[tuple[str, int], dict[str, object]]:
    """Verdicts already collected, keyed by (case id, repeat)."""
    if not path.exists():
        return {}
    done = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            done[(str(row["case"]), int(row["repeat"]))] = row
    return done


def collect(
    trigger_set: object,
    description: str,
    model: str,
    repeats: int,
    *,
    system: str = SYSTEM,
    checkpoint: Path = CHECKPOINT,
) -> dict[tuple[str, int], dict[str, object]]:
    """Run every case `repeats` times, checkpointing after each call.

    Resumable, because two runs already showed the item verdicts moving and the
    honest number needs enough repeats that a lost run would be expensive to
    redo.
    """
    done = load_done(checkpoint)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    cases = trigger_set.cases  # type: ignore[attr-defined]
    total = len(cases) * repeats

    with checkpoint.open("a", encoding="utf-8") as handle:
        for repeat in range(repeats):
            for index, case in enumerate(cases):
                if (case.id, repeat) in done:
                    continue
                try:
                    fired, procedure, p_fire = ask(description, case, model, system)
                except IsolationError:
                    raise
                except CliError as error:
                    fired, procedure, p_fire = None, None, None
                    print(f"  r{repeat} {case.id}: call failed -- {error}")
                row = {
                    "case": case.id,
                    "repeat": repeat,
                    "fired": fired,
                    "procedure": procedure,
                    "p_fire": p_fire,
                    "should_fire": case.should_fire,
                    "route": case.route,
                }
                handle.write(json.dumps(row) + "\n")
                handle.flush()
                done[(case.id, repeat)] = row
                seen = repeat * len(cases) + index + 1
                if seen % 25 == 0 or seen == total:
                    print(f"  {seen}/{total}")
    return done


def report_stability(
    trigger_set: object, done: dict[tuple[str, int], dict[str, object]], repeats: int
) -> None:
    """Per-item stability, and how many repeats the aggregate actually needs."""
    import numpy as np

    from decision_evals.stats import per_item_reliability, repeats_for_reliability

    cases = trigger_set.cases  # type: ignore[attr-defined]
    rows = []
    unstable_fire: list[str] = []
    unstable_route: list[str] = []

    for case in cases:
        verdicts = [done.get((case.id, r)) for r in range(repeats)]
        if any(v is None or v["fired"] is None for v in verdicts):
            continue
        fired = [bool(v["fired"]) for v in verdicts]  # type: ignore[index]
        rows.append([1.0 if f == case.should_fire else 0.0 for f in fired])
        if len(set(fired)) > 1:
            unstable_fire.append(f"{case.id}({sum(fired)}/{repeats})")
        if case.should_fire and case.route:
            chosen = {v["procedure"] for v in verdicts}  # type: ignore[index]
            if len(chosen) > 1:
                unstable_route.append(
                    f"{case.id}({'/'.join(str(c) for c in sorted(chosen, key=str))})"
                )

    scores = np.array(rows, dtype=float)
    print(f"\n{'=' * 60}\nSTABILITY across {repeats} repeats\n{'=' * 60}")
    print(f"  items scored          {len(rows)}")
    print(f"  firing flipped on     {len(unstable_fire)} item(s)")
    for entry in unstable_fire:
        print(f"      {entry}")
    print(f"  routing varied on     {len(unstable_route)} labelled item(s)")
    for entry in unstable_route:
        print(f"      {entry}")

    result = per_item_reliability(scores)
    print(f"\n  ICC                   {result.icc:.3f}")
    print(f"  aptitude (p90)        {result.aptitude:.3f}")
    print(f"  scatter (p90-p10)     {result.scatter:.3f}")
    for target in (0.8, 0.9):
        try:
            k = repeats_for_reliability(result.icc, target)
            print(f"  repeats for r={target}   {k}")
        except ValueError as error:
            print(f"  repeats for r={target}   n/a ({error})")


def report_calibration(done: dict[tuple[str, int], dict[str, object]]) -> None:
    """Is the elicited probability worth anything?

    Reported as the Murphy decomposition rather than as a single Brier score,
    because Brier alone cannot tell a calibrated forecaster from a hedging one.
    A model that answers 0.74 to everything is perfectly reliable and completely
    useless: reliability near zero, **resolution** near zero. Resolution is the
    number that says the forecast discriminates at all, and it is the one to read
    first.

    Skipped silently below ten forecasts. Every estimator here is biased at small
    n, and a reliability diagram over six points is a decoration.
    """
    import numpy as np

    from decision_evals.stats.calibration import (
        expected_calibration_error,
        murphy_decomposition,
        reliability_curve,
        smooth_calibration_error,
    )

    rows = [
        row
        for row in done.values()
        if isinstance(row.get("p_fire"), int | float) and row.get("fired") is not None
    ]
    print(f"\n{'=' * 60}\nCALIBRATION of the elicited p_fire\n{'=' * 60}")
    print(f"  forecasts returned    {len(rows)}/{len(done)}")
    if len(rows) < 10:
        print("  too few to estimate anything; every measure here is biased at small n")
        return

    forecasts = np.array([float(row["p_fire"]) for row in rows])  # type: ignore[arg-type]
    outcomes = np.array([1.0 if row["should_fire"] else 0.0 for row in rows])

    murphy = murphy_decomposition(forecasts, outcomes)
    print(f"  distinct values used  {murphy.n_groups}   <- 1 or 2 means it is not forecasting")
    print(f"  base rate             {murphy.base_rate:.3f}")
    print(f"  Brier                 {murphy.brier:.4f}   (lower better)")
    print(f"  reliability           {murphy.reliability:.4f}   (lower better)")
    print(f"  resolution            {murphy.resolution:.4f}   (HIGHER better -- read this one)")
    print(f"  uncertainty           {murphy.uncertainty:.4f}   (the question set, not the model)")
    print(
        f"  Brier skill score     {murphy.skill_score:+.4f}   (vs always answering the base rate)"
    )
    print(f"  smoothed cal. error   {smooth_calibration_error(forecasts, outcomes):.4f}")
    print(f"  binned ECE (10)       {expected_calibration_error(forecasts, outcomes):.4f}")

    print("\n  stated    n     observed")
    for calibration_bin in reliability_curve(forecasts, outcomes):
        print(
            f"  [{calibration_bin.lower:.1f},{calibration_bin.upper:.1f})"
            f"  {calibration_bin.count:4d}   {calibration_bin.observed_frequency:.3f}"
            f"   (mean stated {calibration_bin.mean_forecast:.3f})"
        )

    if murphy.skill_score <= 0:
        print("\n  *** No skill over always answering the base rate. The forecast is not")
        print("  *** carrying information about these labels.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--skill", default="decision-making")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--confidence",
        action="store_true",
        help="also elicit p_fire and score it; writes a separate checkpoint",
    )
    args = parser.parse_args()

    trigger_set = load_trigger_set(REPO_ROOT / TRIGGERS_DIR / f"{args.skill}.yaml")
    document = parse_skill(REPO_ROOT / "skills" / args.skill / "SKILL.md")
    description = str(document.frontmatter["description"]).strip()

    print(
        f"{args.skill}: {len(trigger_set.positives)} positive, {len(trigger_set.negatives)} negative"
    )
    print(f"description: {len(description)} chars, {args.repeats} repeat(s)\n")

    system = SYSTEM_CONFIDENCE if args.confidence else SYSTEM
    checkpoint = CHECKPOINT_CONFIDENCE if args.confidence else CHECKPOINT
    try:
        done = collect(
            trigger_set,
            description,
            args.model,
            args.repeats,
            system=system,
            checkpoint=checkpoint,
        )
    except IsolationError as error:
        print(f"ISOLATION FAILURE, stopping: {error}")
        return 1

    if args.repeats > 1:
        report_stability(trigger_set, done, args.repeats)
    if args.confidence:
        report_calibration(done)

    # The single-run report below describes repeat 0, and is kept because
    # precision and recall are what the skill is judged on. With repeats > 1 the
    # stability block above is the one that says whether to believe it.
    verdicts: dict[str, bool] = {}
    routes: dict[str, str | None] = {}
    unparseable: list[str] = []
    for case in trigger_set.cases:
        row = done.get((case.id, 0))
        if row is None or row["fired"] is None:
            unparseable.append(case.id)
            continue
        verdicts[case.turn] = bool(row["fired"])
        routes[case.turn] = row["procedure"]  # type: ignore[assignment]

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
