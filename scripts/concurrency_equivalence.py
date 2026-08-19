"""Does making the runner concurrent change what it measures?

The falsifier registered in
``notebook/2026-08-19-prediction-concurrency-must-not-change-results.md``,
committed before any of this ran.

The entry is named by path rather than by commit deliberately. ``provenance.py``
establishes the ordering from the *first commit touching that path*, so the path
is what carries the evidence; a sha7 written into prose is invalidated by the
first rebase, and ``CLAUDE.md`` now asks every branch to rebase onto
``origin/main`` daily. A run directory's sha7 is different -- it names a pushed
commit and is checked against the graph.

Three arms over the same 40 items, on the free ``dev`` arena:

    S1  serial, concurrency 1
    S2  serial, concurrency 1, an independent repeat
    C   concurrent, concurrency 8

``S2`` is the known-good case standing rule 2 demands. Without a measured
serial-against-itself floor, a low ``S1``-vs-``C`` agreement cannot be told from
a model that will not reproduce itself, and the whole comparison would be
uninterpretable in the direction that flatters the change.

Run it::

    python -m uv run python scripts/concurrency_equivalence.py

Nothing here may emit a verdict: ``dev`` does not, and ``arenas.py`` enforces
that on the model prefix.

**Flat files under ``results/track-0/``, not a subdirectory, and that is not a
style choice.** ``provenance.discover_runs`` qualifies a published run by
*position* -- any ``results/<skill>/<run>/`` directory -- and it walks the
filesystem rather than the git index. ``results/track-0/`` is gitignored whole,
so a run-shaped subdirectory there would be demanded to carry a run README and a
``Prediction:`` line on the machine that ran it, and would not exist at all in
CI. That is the same red-here-green-there asymmetry that
``[tool.decision-evals.docs-ignored-paths]`` was written to avoid. Flat files
sidestep it, which is why the checkpoints already in that directory are flat.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from decision_evals.budget import BudgetLedger
from decision_evals.generators.generate import Item
from decision_evals.providers.openai_compatible import assert_isolated, ollama, show
from decision_evals.runner import RunRecord, load_records, local_call, run_arm
from decision_evals.scorers.answer import ZeroCause
from decision_evals.solvers.arms import build_arm
from decision_evals.stats.paired import mcnemar_exact
from decision_evals.triggers import load_trigger_set

REPO_ROOT = Path(__file__).resolve().parents[1]
TRIGGERS = REPO_ROOT / "datasets" / "triggers" / "decision-making" / "index.yaml"
OUT = REPO_ROOT / "results" / "track-0"
#: Set `DE_CONC_PREFIX` to run an independent replication into its own files
#: rather than resuming the first one. No finding here is believed until the
#: run reproduces, and a resumed pass returns the same records by construction.
PREFIX = os.environ.get("DE_CONC_PREFIX", "concurrency")

#: Registered in the prediction and not to be changed here.
N_ITEMS = 40
MODEL = "ollama/qwen3:4b"
CONCURRENCY = 8

#: The band, and the kill. Both registered.
BAND = 0.10
KILL_FLOOR = 0.50


def items() -> list[Item]:
    """The first 40 trigger turns, in file order, as runnable items.

    The turn is the whole varying content; the wrapper around it is constant
    across all three arms, which is all the comparison needs. Options are a
    fixed pair rather than a real menu because nothing here is scored for
    correctness -- the outcome is whether two runs of the same prompt return the
    same text.
    """
    trigger_set = load_trigger_set(TRIGGERS)
    return [
        Item(
            item_id=case.id,
            template_id="concurrency-equivalence",
            seed=0,
            variant=0,
            n_distractors=0,
            position="none",
            variables={},
            question=case.turn,
            options=["wait", "act"],
            facts=[],
            answer="wait",
            load_bearing=[],
            distractor_ids=[],
        )
        for case in trigger_set.cases[:N_ITEMS]
    ]


def run(label: str, pool: list[Item], concurrency: int) -> tuple[list[RunRecord], float]:
    """One arm, into its own checkpoint. Returns records and wall-clock seconds."""
    checkpoint = OUT / f"{PREFIX}-{label}.jsonl"
    timing = OUT / f"{PREFIX}-{label}-timing.json"

    started = time.monotonic()
    produced = run_arm(
        pool,
        build_arm("off"),
        model=MODEL,
        checkpoint=checkpoint,
        call=local_call(MODEL),
        ledger=BudgetLedger(limit_usd=1.0),
        expected_cost_usd=0.0,
        concurrency=concurrency,
        # This script is why `runner.CONCURRENCY_UNSAFE` has an `ollama` entry,
        # and it is the only caller allowed past it. The register may only
        # shrink, and it shrinks when this run comes back inside the band --
        # so the job that would clear it has to be able to make the calls.
        measuring_concurrency=True,
    )
    elapsed = time.monotonic() - started

    if produced:
        timing.write_text(
            json.dumps({"elapsed_s": elapsed, "n_called": len(produced)}, indent=2),
            encoding="utf-8",
        )
    if not timing.is_file():
        raise SystemExit(
            f"{timing.name} is missing and this pass made no calls, so the wall-clock "
            f"for {label} is not recoverable. Delete {checkpoint.name} and run again."
        )
    stored = json.loads(timing.read_text(encoding="utf-8"))

    # Read back rather than using the return value: a resumed arm returns only
    # what this invocation produced, and the comparison needs all of it.
    return load_records(checkpoint), float(stored["elapsed_s"])


def by_id(records: list[RunRecord]) -> dict[str, RunRecord]:
    return {record.item_id: record for record in records}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    card = show(MODEL, endpoint=ollama())
    assert_isolated(card)
    print(f"model card: system={len(card.system)} chars, template={len(card.template)} chars\n")

    pool = items()
    print(f"{len(pool)} items from {TRIGGERS.relative_to(REPO_ROOT)}\n")

    arms: dict[str, tuple[dict[str, RunRecord], float]] = {}
    for label, concurrency in (("S1", 1), ("S2", 1), ("C", CONCURRENCY)):
        records, elapsed = run(label, pool, concurrency)
        arms[label] = (by_id(records), elapsed)
        print(f"{label}: {len(records)} records, {elapsed:.1f}s wall-clock")

    s1, s2, c = arms["S1"][0], arms["S2"][0], arms["C"][0]
    ids = sorted(set(s1) & set(s2) & set(c))
    print(f"\n{len(ids)} items present in all three arms")

    # An infrastructure zero has the exception text in `response`, so it would
    # be compared as though it were an answer. Counted and reported rather than
    # silently folded into the agreement rate.
    #
    # The field is `zero_cause`. The first version of this line read
    # `parse_status == "infrastructure_error"`, a value `ParseStatus` does not
    # contain, so the count could never have risen above zero. It was caught
    # because a CUDA OOM on `m01p` wrote a record with `duration_ms=0` that this
    # check called healthy. Third inert estimator on record here, same standing
    # rule broken: before believing an outcome, check that some possible response
    # would have scored non-zero. The annotation makes a rename a type error
    # rather than a silent revival.
    infrastructure: ZeroCause = "infrastructure"
    failures = {
        label: sum(1 for i in ids if arm[i].zero_cause == infrastructure)
        for label, (arm, _) in arms.items()
    }
    print(f"infrastructure failures: {failures}")

    # A failed call is not a disagreement about anything. It stays in the
    # registered denominator, because the prediction registered "all items,
    # whatever their parse status". But that same paragraph said "every call
    # returns text or raises, and a raise is a failed run rather than a scored
    # zero", and that is false about this harness: `_run_one` catches `CliError`
    # and writes an infrastructure zero. The registered denominator therefore
    # rests on a premise about the runner that does not hold, so the clean-set
    # rate below is reported beside the registered number and never instead of
    # it. Sixth pre-registration defect on record, second one visible before
    # scoring rather than after.
    clean = [i for i in ids if all(arm[i].zero_cause != infrastructure for arm, _ in arms.values())]

    agree_s2 = [int(s2[i].response == s1[i].response) for i in ids]
    agree_c = [int(c[i].response == s1[i].response) for i in ids]
    rate_s2 = sum(agree_s2) / len(ids)
    rate_c = sum(agree_c) / len(ids)

    tokens_match = all(s1[i].input_tokens == s2[i].input_tokens == c[i].input_tokens for i in ids)

    print(f"\nagree_S2 (the floor): {rate_s2:.4f}")
    print(f"agree_C:              {rate_c:.4f}")
    print(f"band: agree_C >= {rate_s2 - BAND:.4f}")

    killed = rate_s2 < KILL_FLOOR
    if killed:
        print(
            f"\nKILL FIRED: agree_S2 {rate_s2:.4f} < {KILL_FLOOR}. Exact text match "
            "cannot distinguish anything here, so the primary is abandoned and the "
            "pre-declared secondary is the result."
        )
    else:
        verdict = "INSIDE" if rate_c >= rate_s2 - BAND else "OUTSIDE"
        print(f"\nprimary: {verdict} the registered band")

    # Two-sided. The registered question is whether concurrency *changes* the
    # result, and a directional test would decline to see a change in the
    # direction that flatters it.
    test = mcnemar_exact(agree_s2, agree_c, alternative="two-sided")
    print(
        f"McNemar exact, two-sided: discordant={test.n_discordant} "
        f"(C-only {test.treatment_wins}, S2-only {test.control_wins}) "
        f"p={test.p_value:.4f}"
    )
    print(f"\nsecondary -- input_tokens identical across all three arms: {tokens_match}")

    # Unregistered, and labelled as such everywhere it appears.
    rate_s2_clean = (
        sum(int(s2[i].response == s1[i].response) for i in clean) / len(clean) if clean else 0.0
    )
    rate_c_clean = (
        sum(int(c[i].response == s1[i].response) for i in clean) / len(clean) if clean else 0.0
    )
    print(
        f"UNREGISTERED sensitivity, {len(clean)} items with no infrastructure zero "
        f"in any arm: agree_S2 {rate_s2_clean:.4f}, agree_C {rate_c_clean:.4f}"
    )

    speedup = arms["S1"][1] / arms["C"][1] if arms["C"][1] else 0.0
    print(f"speedup, S1 / C wall-clock: {speedup:.2f}x")

    summary: dict[str, Any] = {
        "n_items": len(ids),
        "model": MODEL,
        "concurrency": CONCURRENCY,
        "agree_S2": rate_s2,
        "agree_C": rate_c,
        "band_floor": rate_s2 - BAND,
        "kill_fired": killed,
        "inside_band": bool(rate_c >= rate_s2 - BAND),
        "input_tokens_identical": tokens_match,
        "infrastructure_failures": failures,
        "unregistered_sensitivity": {
            "n_clean": len(clean),
            "agree_S2": rate_s2_clean,
            "agree_C": rate_c_clean,
        },
        "wall_clock_s": {label: elapsed for label, (_, elapsed) in arms.items()},
        "speedup": speedup,
        "mcnemar": {
            "n_pairs": test.n_pairs,
            "n_discordant": test.n_discordant,
            "agree_C_only": test.treatment_wins,
            "agree_S2_only": test.control_wins,
            "p_value": test.p_value,
            "alternative": test.alternative,
        },
    }
    written = OUT / f"{PREFIX}-summary.json"
    written.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nwrote {written.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
