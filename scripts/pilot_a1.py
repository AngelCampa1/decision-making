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
from decision_evals.scorers.bfcl import CALL_FORMAT  # noqa: E402
from decision_evals.sharded import (  # noqa: E402
    FINAL_TURN,
    FULL_INSTRUCTION_FIELD,
    append_record,
    completed_keys,
    load_records,
    pairable,
    plan_run,
    run_full,
    run_sharded,
    task_context,
)

CHECKPOINT_DIR = REPO_ROOT / "results" / "track-a"


def checkpoint_for(tag: str) -> Path:
    """Where a run writes. ``--tag`` exists because the draw is not nested.

    ``rng.sample(pool, 40)`` is not a superset of ``rng.sample(pool, 10)`` from
    the same seed, so raising ``--per-family`` produces a *different* ten items
    rather than thirty more. Resuming into the same file would silently mix two
    draws, and every downstream count would be over a sample nobody chose.

    The system-prompt guard below would not catch that -- the prompts are
    identical, it is the items that differ -- so the separation has to be by
    path.
    """
    return CHECKPOINT_DIR / f"{tag}.jsonl"


#: Identical in both conditions. Anything that differs between them is a
#: confound with the thing under test, so the system prompt must not.
SYSTEM_PROMPT = (
    "You are answering a user's request. Work from everything they have told you "
    "so far. When you have enough to answer, give your best final answer."
)


def system_prompt_for(item: ShardedInstruction, *, call_format: bool = False) -> str:
    """The shared preamble plus whatever this family cannot be answered without.

    Still identical across the two conditions of a pair -- it is a function of
    the item, never of the condition.

    Args:
        call_format: Ask ``actions`` items for a parseable call, so BFCL's own
            AST match applies instead of the naming floor. It changes the task
            and both arms carry it. Restricted to ``actions`` because it names
            "the available functions": on a word problem it is noise, and noise
            added to one family and not another is a confound with family.
    """
    parts = [SYSTEM_PROMPT]
    if context := task_context(item):
        parts.append(context)
    if call_format and item.task == "actions":
        parts.append(CALL_FORMAT)
    return "\n\n".join(parts)


#: Fixed so the pilot is reproducible and so nobody can reselect until the
#: numbers look better.
SEED = 20260811


def select(
    instructions: list[ShardedInstruction],
    per_family: int,
    families: tuple[str, ...] | None = None,
) -> list[ShardedInstruction]:
    """A stratified, seeded sample: equal counts from each pairable family.

    ``families`` filters **after** the draw, never during it. One RNG walks the
    families in sorted order, so skipping one would shift what every later family
    draws -- and a run restricted to ``actions`` would then not be a subset of the
    full run it is meant to extend.
    """
    rng = random.Random(SEED)
    chosen: list[ShardedInstruction] = []
    for family in sorted(FULL_INSTRUCTION_FIELD):
        pool = sorted(
            (item for item in instructions if item.task == family), key=lambda i: i.task_id
        )
        chosen.extend(rng.sample(pool, min(per_family, len(pool))))
    if families is None:
        return chosen
    return [item for item in chosen if item.task in families]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-family", type=int, default=10)
    parser.add_argument("--model", default="haiku")
    parser.add_argument(
        "--final-turn",
        action="store_true",
        help="send the closing instruction to both conditions (one extra sharded turn)",
    )
    parser.add_argument(
        "--families",
        default="",
        help="comma-separated families to run; the draw is unchanged, only filtered",
    )
    parser.add_argument(
        "--call-format",
        action="store_true",
        help="ask actions items for a parseable call, enabling BFCL's own AST match",
    )
    parser.add_argument(
        "--tag",
        default="pilot",
        help="checkpoint name. Change it whenever --per-family or --families changes",
    )
    args = parser.parse_args()

    closing = FINAL_TURN if args.final_turn else None
    families = tuple(f.strip() for f in args.families.split(",") if f.strip()) or None
    if families and (unknown := set(families) - set(FULL_INSTRUCTION_FIELD)):
        print(f"unknown famil(ies): {sorted(unknown)}. Known: {sorted(FULL_INSTRUCTION_FIELD)}")
        return 1

    checkpoint = checkpoint_for(args.tag)
    corpus = load_corpus(REPO_ROOT, check_hash=False)
    items = select(pairable(corpus), args.per_family, families)
    if not items:
        print("no items selected")
        return 1
    plan = plan_run(items, final_turn=args.final_turn)
    print(plan.describe())
    print(f"closing instruction: {'yes' if closing else 'no'}")
    print(f"families: {', '.join(families) if families else 'all'}")
    print(f"call format: {'yes' if args.call_format else 'no'}")
    print(f"checkpoint: {checkpoint.relative_to(REPO_ROOT)}\n")

    # Resuming across a change to either prompt would append records made under
    # different conditions to the ones already there, and nothing downstream
    # would show it. That is how the first pilot ran forty pairs with no schema
    # and no function list; the second time it should refuse rather than resume.
    if checkpoint.exists():
        wanted = {system_prompt_for(item, call_format=args.call_format) for item in items}
        for record in load_records(checkpoint):
            mismatch = (
                "closing instruction"
                if record.final_turn != closing
                else "system prompt"
                if record.system_prompt not in wanted
                else None
            )
            if mismatch:
                print(
                    f"*** {checkpoint.name} holds records made with a different {mismatch} "
                    f"({record.task_id}). Resuming would pool two runs into one file. "
                    "Move it aside."
                )
                return 1

    done = completed_keys(checkpoint)
    started = time.time()
    failures = 0

    for index, item in enumerate(items, start=1):
        conversation_id = f"pilot-{item.task_id}"
        system = system_prompt_for(item, call_format=args.call_format)

        with tempfile.TemporaryDirectory() as cwd:
            # -- full: the fully-specified question, one call ------------------
            if (item.task_id, "full") not in done:
                try:
                    record = run_full(
                        item,
                        system_prompt=system,
                        call=lambda prompt, system: cli_run(
                            prompt, system_prompt=system, model=args.model, cwd=cwd
                        ),
                        conversation_id=conversation_id,
                        final_turn=closing,
                    )
                    append_record(checkpoint, record)
                except CliError as exc:
                    failures += 1
                    print(f"  [{index}] full FAILED {item.task_id}: {exc}")

            # -- sharded: one shard per turn, one live process -----------------
            if (item.task_id, "sharded") not in done:
                try:
                    with Conversation(system_prompt=system, model=args.model, cwd=cwd) as chat:
                        record = run_sharded(
                            item,
                            system_prompt=system,
                            conversation=chat,
                            conversation_id=conversation_id,
                            final_turn=closing,
                        )
                        # Isolation is asserted per conversation, not per run:
                        # a receipt that changed mid-run is exactly the silent
                        # confound the gate exists for.
                        chat.receipt.assert_isolated()
                    append_record(checkpoint, record)
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
