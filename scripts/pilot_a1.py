"""Track A1 pilot: 30 pairs, to measure the one parameter the MDE is missing.

The full A1 grid is 1,964 generations. Its minimum detectable effect is a
*range* (5.4-9.9pp) rather than a number, because ``p_discordant`` is unknown --
and ``stats/power.required_pairs`` says in its own docstring to take that from a
screening run rather than to invent it. This is the screening run.

**It records and does not score.** Standing rule 3: you may run experiments and
record raw outputs; you may not decide that a response is wrong. Twenty-one of
twenty-one scored failures across three corpora were the answer key. So this
writes ``ShardedRecord`` lines, which have no ``correct`` field by construction,
and adjudication is a separate act by a human who can read the traces.

Usage:
    python scripts/pilot_a1.py [--per-family 10] [--model haiku]
"""

from __future__ import annotations

import argparse
import random
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

from decision_evals.corpora import ShardedInstruction, load_corpus  # noqa: E402
from decision_evals.providers.claude_code import (  # noqa: E402
    CliError,
    Conversation,
    IsolationError,
)
from decision_evals.providers.claude_code import run as cli_run  # noqa: E402
from decision_evals.sharded import (  # noqa: E402
    FULL_INSTRUCTION_FIELD,
    append_record,
    completed_keys,
    pairable,
    plan_run,
    run_full,
    run_sharded,
)

CHECKPOINT = REPO_ROOT / "results" / "track-a" / "pilot.jsonl"

#: Identical in both conditions. Anything that differs between them is a
#: confound with the thing under test, so the system prompt must not.
SYSTEM_PROMPT = (
    "You are answering a user's request. Work from everything they have told you "
    "so far. When you have enough to answer, give your best final answer."
)

#: Fixed so the pilot is reproducible and so nobody can reselect until the
#: numbers look better.
SEED = 20260811


def select(instructions: list[ShardedInstruction], per_family: int) -> list[ShardedInstruction]:
    """A stratified, seeded sample: equal counts from each pairable family."""
    rng = random.Random(SEED)
    chosen: list[ShardedInstruction] = []
    for family in sorted(FULL_INSTRUCTION_FIELD):
        pool = sorted(
            (item for item in instructions if item.task == family), key=lambda i: i.task_id
        )
        chosen.extend(rng.sample(pool, min(per_family, len(pool))))
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-family", type=int, default=10)
    parser.add_argument("--model", default="haiku")
    args = parser.parse_args()

    corpus = load_corpus(REPO_ROOT, check_hash=False)
    items = select(pairable(corpus), args.per_family)
    plan = plan_run(items)
    print(plan.describe())
    print(f"checkpoint: {CHECKPOINT.relative_to(REPO_ROOT)}\n")

    done = completed_keys(CHECKPOINT)
    started = time.time()
    failures = 0

    for index, item in enumerate(items, start=1):
        conversation_id = f"pilot-{item.task_id}"

        with tempfile.TemporaryDirectory() as cwd:
            # -- full: the fully-specified question, one call ------------------
            if (item.task_id, "full") not in done:
                try:
                    record = run_full(
                        item,
                        system_prompt=SYSTEM_PROMPT,
                        call=lambda prompt, system: cli_run(
                            prompt, system_prompt=system, model=args.model, cwd=cwd
                        ),
                        conversation_id=conversation_id,
                    )
                    append_record(CHECKPOINT, record)
                except CliError as exc:
                    failures += 1
                    print(f"  [{index}] full FAILED {item.task_id}: {exc}")

            # -- sharded: one shard per turn, one live process -----------------
            if (item.task_id, "sharded") not in done:
                try:
                    with Conversation(
                        system_prompt=SYSTEM_PROMPT, model=args.model, cwd=cwd
                    ) as chat:
                        record = run_sharded(
                            item,
                            system_prompt=SYSTEM_PROMPT,
                            conversation=chat,
                            conversation_id=conversation_id,
                        )
                        # Isolation is asserted per conversation, not per run:
                        # a receipt that changed mid-run is exactly the silent
                        # confound the gate exists for.
                        chat.receipt.assert_isolated()
                    append_record(CHECKPOINT, record)
                    if not record.prompt_tokens_climb:
                        print(f"  [{index}] WARNING {item.task_id}: prompt tokens did not climb")
                except IsolationError as exc:
                    print(f"  [{index}] ISOLATION FAILURE, stopping: {exc}")
                    return 1
                except CliError as exc:
                    failures += 1
                    print(f"  [{index}] sharded FAILED {item.task_id}: {exc}")

        elapsed = time.time() - started
        print(f"  [{index}/{len(items)}] {item.task:<9} {item.task_id:<34} {elapsed:6.0f}s")

    print(f"\ndone in {time.time() - started:.0f}s, {failures} call failure(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
