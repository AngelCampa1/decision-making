"""Control-arm difficulty calibration.

The plan's stated response to its own biggest risk: run this on cheap items
*before* scaling templates, so a dead premise costs a day rather than a month.

Two gates, both computed on the control arm only so they cannot bias the
treatment-minus-control difference:

1. **Clean-room** -- at least 95% accuracy on distractor-free items. An item
   missed *without* distractors is ambiguous, not hard, and belongs in neither
   stratum.
2. **Difficulty** -- accuracy on distractor-present items inside [0.35, 0.75].
   Above the band there is no headroom and the required N explodes; below it,
   something other than distractor sensitivity is going on.

Usage:
    python -m uv run python scripts/calibrate.py [--model haiku] [--limit N]
"""

from __future__ import annotations

import argparse
import statistics
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from decision_evals.arenas import assert_model_allowed
from decision_evals.budget import BudgetLedger
from decision_evals.generators import generate, load_all
from decision_evals.runner import RunError, default_call, load_records, preflight, run_arm
from decision_evals.solvers.arms import build_arm

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = REPO_ROOT / "results" / "calibration" / "off-arm.jsonl"

CLEAN_ROOM_FLOOR = 0.95
DIFFICULTY_BAND = (0.35, 0.75)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--limit", type=int, default=0, help="cap items, for a smoke run")
    parser.add_argument("--budget", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    # Screening arena: public split, cheap model, no verdict. Asserted rather
    # than assumed, so a typo'd model cannot quietly turn this into a run whose
    # numbers describe a different experiment.
    assert_model_allowed("screen", args.model)

    items = [item for template in load_all() for item in generate(template, args.seed)]
    if args.limit:
        items = items[: args.limit]

    # Scratch cwd outside the source tree: this is the first isolation guard,
    # and the reason a planted CLAUDE.md cannot reach the run.
    with tempfile.TemporaryDirectory(prefix="de-calibrate-") as scratch:
        print(f"preflight against {args.model} ...", flush=True)
        preflight(model=args.model, cwd=scratch)

        arm = build_arm("off")
        print(f"running {len(items)} items, checkpoint {CHECKPOINT}", flush=True)
        try:
            produced = run_arm(
                items,
                arm,
                model=args.model,
                checkpoint=CHECKPOINT,
                call=default_call(args.model, scratch),
                ledger=BudgetLedger(limit_usd=args.budget),
            )
        except RunError as exc:
            print(f"\nrun stopped: {exc}", file=sys.stderr)
            print("checkpoint is intact; rerun to resume", file=sys.stderr)
            return 2
        print(f"  {len(produced)} new records this invocation", flush=True)

    return report()


def report() -> int:
    records = load_records(CHECKPOINT)
    if not records:
        print("no records", file=sys.stderr)
        return 2

    clean = [r for r in records if r.n_distractors == 0]
    loaded = [r for r in records if r.n_distractors > 0]

    print(f"\n{'=' * 66}\ncontrol-arm calibration -- {len(records)} records")
    print(f"model: {sorted({r.model for r in records})}")
    print(f"spend: ${sum(r.cost_usd for r in records):.3f}")
    print("=" * 66)

    clean_acc = _accuracy(clean)
    loaded_acc = _accuracy(loaded)
    parse_rate = sum(1 for r in records if r.parse_status != "parsed") / len(records)

    gate1 = clean_acc >= CLEAN_ROOM_FLOOR
    gate2 = DIFFICULTY_BAND[0] <= loaded_acc <= DIFFICULTY_BAND[1]

    print(
        f"\nGATE 1 clean-room     {clean_acc:.3f} (n={len(clean)})   "
        f"need >= {CLEAN_ROOM_FLOOR}   {'PASS' if gate1 else 'FAIL'}"
    )
    print(
        f"GATE 2 difficulty     {loaded_acc:.3f} (n={len(loaded)})   "
        f"need in {DIFFICULTY_BAND}   {'PASS' if gate2 else 'FAIL'}"
    )
    print(f"       parse failures {parse_rate:.3f}")

    print("\nby distractor count:")
    for count, group in sorted(_group(records, lambda r: r.n_distractors).items()):
        print(f"  {count:>2} distractors  acc {_accuracy(group):.3f}  (n={len(group)})")

    print("\nby position (loaded items only):")
    for position, group in sorted(_group(loaded, lambda r: r.position).items()):
        print(f"  {position:>6}  acc {_accuracy(group):.3f}  (n={len(group)})")

    print("\nby template:")
    per_template = _group(records, lambda r: r.template_id)
    for template_id, group in sorted(per_template.items()):
        c = [r for r in group if r.n_distractors == 0]
        d = [r for r in group if r.n_distractors > 0]
        print(f"  {template_id:<26} clean {_accuracy(c):.2f}  loaded {_accuracy(d):.2f}")

    accuracies = [_accuracy(g) for g in per_template.values()]
    if len(accuracies) > 1:
        print(f"\nbetween-template spread: sd {statistics.stdev(accuracies):.3f}")

    print("\n" + "=" * 66)
    if gate1 and gate2:
        print("both gates pass -- the corpus is eligible for pre-registration")
        return 0
    print("at least one gate failed -- see notebook for the diagnosis")
    return 1


def _accuracy(records: list) -> float:  # type: ignore[type-arg]
    return sum(1 for r in records if r.correct) / len(records) if records else 0.0


def _group(records: list, key) -> dict:  # type: ignore[type-arg, no-untyped-def]
    out = defaultdict(list)
    for record in records:
        out[key(record)].append(record)
    return dict(out)


if __name__ == "__main__":
    raise SystemExit(main())
