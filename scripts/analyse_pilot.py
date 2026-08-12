"""Read the A1 pilot back: instrument checks first, then a provisional match.

Two halves, and the split is the point.

**The instrument checks are objective and pre-registered**
(``notebook/2026-08-12-a1-pilot-prediction.md``). Prompt tokens climbed or they
did not; the run had isolation failures or it did not. Nothing here decides
whether a response was any good.

**The match is provisional and only runs for ``math``.** Standing rule 3 says a
model may run experiments and record raw outputs but may not decide that a
response is wrong -- 21 of 21 scored failures across three corpora were the
answer key. The rule is weaker for a *vendored* key than for one authored here,
and GSM8K's is about as unambiguous as a key gets: the reference is the number
after ``####`` and nothing else. But the *extraction* is still a choice, so this
script prints every pair it scored alongside the text it scored, and the
agreement figure is labelled as needing adjudication until a human has read
them. It does not write anywhere.

Usage:
    python scripts/analyse_pilot.py [--show math] [--limit 8]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

# This script's entire job is printing model text back to a human, and model
# text contains check marks, em dashes and degree signs. Windows' console codec
# is cp1252 and raises on all of them, so a run would die partway through the
# traces it exists to show -- which is the moment the reader most needs it not to.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decision_evals.corpora import load_corpus  # noqa: E402
from decision_evals.sharded import FULL, SHARDED, ShardedRecord, load_records  # noqa: E402

CHECKPOINT = REPO_ROOT / "results" / "track-a" / "pilot.jsonl"

#: GSM8K states its reference answer after a `####` marker and nowhere else.
_GOLD = re.compile(r"####\s*(-?[\d,]+(?:\.\d+)?)")

#: A number in prose. Thousands separators and a currency prefix are stripped;
#: a trailing period is not part of the number.
_NUMBER = re.compile(r"-?\$?\d[\d,]*(?:\.\d+)?")


def parse_number(text: str) -> float | None:
    cleaned = text.replace(",", "").replace("$", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def gold_answer(answer_field: str) -> float | None:
    match = _GOLD.search(answer_field)
    return parse_number(match.group(1)) if match else None


def extracted_answer(response: str) -> tuple[float | None, str]:
    """The last number in the response, with the phrase it came from.

    Last-number extraction is the conventional GSM8K reading and is not invented
    here. It is still a choice, which is why the surrounding phrase comes back
    with it -- a number lifted out of a comparison table looks identical to one
    stated as the answer until you see its neighbours.
    """
    matches = list(_NUMBER.finditer(response))
    if not matches:
        return None, ""
    last = matches[-1]
    context = response[max(0, last.start() - 60) : last.end() + 20].replace("\n", " ")
    return parse_number(last.group()), context.strip()


def instrument_checks(records: list[ShardedRecord]) -> int:
    """The pre-registered checks. Returns the number that failed."""
    print("=" * 72)
    print("INSTRUMENT CHECKS  (pre-registered, objective)")
    print("=" * 72)

    by_condition = Counter(r.condition for r in records)
    families = Counter(r.task for r in records)
    pairs = {r.task_id for r in records if r.condition == FULL} & {
        r.task_id for r in records if r.condition == SHARDED
    }
    print(f"records          {len(records)}  ({dict(by_condition)})")
    print(f"complete pairs   {len(pairs)}")
    print(f"families         {dict(families)}")
    print(f"models           {sorted({r.model for r in records})}")

    failed = 0

    sharded = [r for r in records if r.condition == SHARDED]
    not_climbing = [r for r in sharded if not r.prompt_tokens_climb]
    print(f"\nprompt tokens climb  {len(sharded) - len(not_climbing)}/{len(sharded)} conversations")
    if not_climbing:
        failed += 1
        print("  *** PREDICTION 3 FAILED. The turns were not accumulating and the")
        print("  *** run is void rather than negative. Offending items:")
        for record in not_climbing:
            print(f"      {record.task_id}: {record.prompt_tokens_by_turn}")

    errored = [r for r in records if r.error]
    print(f"records carrying an error  {len(errored)}")
    if len(errored) > 5:
        failed += 1
        print("  *** PREDICTION 5 FAILED (>5 infrastructure failures).")

    if sharded:
        turns = [r.n_turns for r in sharded]
        print(f"turns per sharded item  min {min(turns)}  max {max(turns)}")
    total_cost = sum(r.cost_usd for r in records)
    print(f"notional cost  ${total_cost:.2f}  (subscription; nothing is billed per call)")
    return failed


def provisional_math_match(records: list[ShardedRecord], limit: int) -> None:
    corpus = {i.task_id: i for i in load_corpus(REPO_ROOT, check_hash=False)}
    by_key = {(r.task_id, r.condition): r for r in records}
    task_ids = sorted({r.task_id for r in records if r.task == "math"})

    print("\n" + "=" * 72)
    print("PROVISIONAL MATCH -- math only, NOT a result")
    print("=" * 72)
    print("Extraction is last-number-in-response. Every pair is printed so the")
    print("extraction can be checked before any figure is believed.\n")

    concordant = discordant = both_right = both_wrong = unextractable = 0
    shown = 0

    for task_id in task_ids:
        full = by_key.get((task_id, FULL))
        shard = by_key.get((task_id, SHARDED))
        if full is None or shard is None:
            continue
        gold = gold_answer(str(corpus[task_id].payload.get("answer", "")))
        full_value, full_context = extracted_answer(full.final_response)
        shard_value, shard_context = extracted_answer(shard.final_response)

        if gold is None or full_value is None or shard_value is None:
            unextractable += 1
            continue

        full_ok = abs(full_value - gold) < 1e-6
        shard_ok = abs(shard_value - gold) < 1e-6
        if full_ok and shard_ok:
            both_right += 1
        elif not full_ok and not shard_ok:
            both_wrong += 1
        if full_ok == shard_ok:
            concordant += 1
        else:
            discordant += 1

        if shown < limit or full_ok != shard_ok:
            shown += 1
            flag = "DISCORDANT" if full_ok != shard_ok else "concordant"
            print(f"--- {task_id}  [{flag}]  gold={gold:g}")
            print(f"    full    {'ok ' if full_ok else 'NO '} {full_value:g}   ...{full_context}")
            print(
                f"    sharded {'ok ' if shard_ok else 'NO '} {shard_value:g}   ...{shard_context}"
            )

    scored = concordant + discordant
    print(f"\nscored pairs      {scored}   (unextractable, skipped: {unextractable})")
    if scored:
        print(f"both right        {both_right}")
        print(f"both wrong        {both_wrong}")
        print(f"discordant        {discordant}")
        print(f"p_discordant      {discordant / scored:.3f}   <-- PROVISIONAL, needs adjudication")
    print("\nThis figure must not be written into docs/RESEARCH_PROGRAMME.md and the")
    print("full A1 grid must not be sized from it until the traces above are read.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=6, help="concordant pairs to print")
    args = parser.parse_args()

    if not CHECKPOINT.exists():
        print(f"no checkpoint at {CHECKPOINT}")
        return 1

    records = load_records(CHECKPOINT)
    failed = instrument_checks(records)
    provisional_math_match(records, args.limit)

    if failed:
        print(f"\n{failed} pre-registered instrument check(s) FAILED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
