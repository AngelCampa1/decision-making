"""Score Track H Phase 0 once the corpus and its extractions exist.

This script does not author the corpus, does not run the extractor, and does
not call a model. Phase 0's corpus (20 invented triplets) and the runner that
produces per-response extractions are built separately, per the split in
``notebook/2026-08-19-prediction-track-h-phase-0.md``. This is the scoring
half: it reads the record files that pipeline is expected to produce and
prints the Phase 0 report — the derived movement threshold, the falsifier
battery's verdict (a refusal, not a caveat, if it has not passed), and Youden's
J with sensitivity and specificity printed beside it, never alone.

Input schema (JSON Lines, one record per line):

``--base-repeats``
    One row per triplet's base-arm repeat-0/repeat-1 pair, used only to derive
    the movement threshold, before any governing or matched contrast is read::

        {"triplet_id": "t01", "repeat": 0, "quantity": 12.5}
        {"triplet_id": "t01", "repeat": 1, "quantity": 12.7}

    Exactly two rows per triplet id (repeats 0 and 1).

``--events``
    One row per ``(triplet, repeat)`` pair across all three arms — 40 rows in
    Phase 0::

        {"triplet_id": "t01", "repeat": 0, "q_base": 12.5, "q_governing": 40.0,
         "q_matched": 12.6}

``--falsifier``
    The two planted triplets' hand-written, hand-scored cases::

        {"name": "obvious-move", "q_base": 10.0, "q_governing": 50.0,
         "q_matched": 10.1, "expect_governing_change": true,
         "expect_matched_change": false}

Usage:
    python -m uv run python scripts/score_track_h.py \\
        --base-repeats results/track-h/base_repeats.jsonl \\
        --events results/track-h/events.jsonl \\
        --falsifier results/track-h/falsifier.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

from decision_evals.stats.track_h import (  # noqa: E402
    BaseRepeatPair,
    FalsifierBatteryFailedError,
    FalsifierCase,
    TripletEvent,
    compute_phase0_result,
    derive_movement_threshold,
    run_falsifier_battery,
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read newline-delimited JSON, skipping blank lines."""
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_base_pairs(path: Path) -> list[BaseRepeatPair]:
    """Pair up repeat-0/repeat-1 rows per triplet, refusing an incomplete pair."""
    by_triplet: dict[str, dict[int, float]] = {}
    for row in _read_jsonl(path):
        by_triplet.setdefault(str(row["triplet_id"]), {})[int(row["repeat"])] = float(
            row["quantity"]
        )
    pairs: list[BaseRepeatPair] = []
    for triplet_id, repeats in sorted(by_triplet.items()):
        if 0 not in repeats or 1 not in repeats:
            raise ValueError(f"{triplet_id} is missing repeat 0 or repeat 1 in {path}")
        pairs.append(
            BaseRepeatPair(triplet_id=triplet_id, q_repeat0=repeats[0], q_repeat1=repeats[1])
        )
    return pairs


def load_events(path: Path) -> list[TripletEvent]:
    """One :class:`TripletEvent` per row."""
    return [
        TripletEvent(
            triplet_id=str(row["triplet_id"]),
            repeat=int(row["repeat"]),
            q_base=float(row["q_base"]),
            q_governing=float(row["q_governing"]),
            q_matched=float(row["q_matched"]),
        )
        for row in _read_jsonl(path)
    ]


def load_falsifier_cases(path: Path) -> list[FalsifierCase]:
    """One :class:`FalsifierCase` per row."""
    return [
        FalsifierCase(
            name=str(row["name"]),
            q_base=float(row["q_base"]),
            q_governing=float(row["q_governing"]),
            q_matched=float(row["q_matched"]),
            expect_governing_change=bool(row["expect_governing_change"]),
            expect_matched_change=bool(row["expect_matched_change"]),
        )
        for row in _read_jsonl(path)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--base-repeats", type=Path, required=True, help="JSONL of base-arm repeat pairs"
    )
    parser.add_argument(
        "--events", type=Path, required=True, help="JSONL of (triplet, repeat) events"
    )
    parser.add_argument(
        "--falsifier", type=Path, required=True, help="JSONL of planted falsifier cases"
    )
    parser.add_argument("--seed", type=int, default=None, help="Bootstrap seed")
    args = parser.parse_args(argv)

    threshold = derive_movement_threshold(load_base_pairs(args.base_repeats))
    print(
        f"movement threshold: {threshold.value:.4f} relative "
        f"(from {threshold.n_base_pairs} base pairs, bound set by {threshold.max_triplet_id})"
    )

    battery = run_falsifier_battery(load_falsifier_cases(args.falsifier), threshold)
    print(
        f"falsifier battery: sensitivity {battery.sensitivity:.3f}, "
        f"specificity {battery.specificity:.3f}, over {battery.n_cases} planted cases"
    )

    try:
        result = compute_phase0_result(load_events(args.events), threshold, battery, seed=args.seed)
    except FalsifierBatteryFailedError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1

    print(result.disposition())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
