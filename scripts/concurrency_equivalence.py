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

**A second backend, added 2026-08-20.** ``--backend cli`` runs the same
falsifier against the Claude Code backend, which is where every published number
in this repository came from and which ``CONCURRENCY_UNSAFE`` has never been
asked about. Its constants, its arm order and its estimator are registered
separately in
``notebook/2026-08-20-prediction-concurrency-on-the-cli-backend.md`` and live in
their own ``CLI_*`` names, because the four ``dev`` constants are what a
published run was scored against and a flag that rebinds them is a flag that can
rescore it. Three differences are worth reading before the numbers:

- **The estimator is ``parsed``, not ``response``.** ``claude -p`` samples, so
  text identity is near zero for every pair including serial against serial. The
  quantity that reaches a published number is the extracted answer.
- **The kill floor is 0.60, not 0.50.** A two-valued answer agrees with itself
  half the time by chance, so a floor at 0.50 would be no floor.
- **The arms run S1, C, S2.** The concurrent arm sits between the two serial
  passes, so the floor spans more elapsed time than either comparison does. The
  ``dev`` ordering could not separate concurrency from drift and its own
  replication is what showed that.

Run it::

    python -m uv run python scripts/concurrency_equivalence.py
    python -m uv run python scripts/concurrency_equivalence.py --backend cli

Nothing in the ``dev`` path may emit a verdict: that arena does not, and
``arenas.py`` enforces it on the model prefix. The ``cli`` path asserts the
*screening* arena for the same reason and by the same function.

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

import argparse
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from decision_evals.arenas import assert_model_allowed
from decision_evals.budget import BudgetLedger
from decision_evals.generators.generate import Item
from decision_evals.providers.openai_compatible import assert_isolated, ollama, show
from decision_evals.runner import (
    CallFn,
    RunRecord,
    default_call,
    load_records,
    local_call,
    preflight,
    run_arm,
)
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

#: The CLI arena's own registered constants, from
#: ``notebook/2026-08-20-prediction-concurrency-on-the-cli-backend.md``. They are
#: separate names rather than overrides of the four above, because the ``dev``
#: numbers are what a published run was scored against and a flag that rebinds
#: them is a flag that can silently rescore it.
CLI_MODEL = "haiku"
CLI_SEED = 1
CLI_CONCURRENCY = 8
#: Five points, not ten: the denominator is 280 rather than 40.
CLI_BAND = 0.05
#: 0.60, not 0.50. The estimator is a two-valued answer, so chance agreement is
#: 0.50 and a floor at the chance level would be no floor at all.
CLI_KILL_FLOOR = 0.60
#: Serial, concurrent, serial. The concurrent arm sits *between* the two serial
#: passes so that the floor spans more elapsed time than either comparison does;
#: see the prediction for why the earlier ordering could not separate
#: concurrency from drift.
CLI_ARMS: tuple[tuple[str, int], ...] = (("S1", 1), ("C", CLI_CONCURRENCY), ("S2", 1))


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


def run(
    label: str,
    pool: list[Item],
    concurrency: int,
    *,
    prefix: str,
    model: str,
    call: CallFn,
    budget_usd: float = 1.0,
    expected_cost_usd: float = 0.0,
) -> tuple[list[RunRecord], float]:
    """One arm, into its own checkpoint. Returns records and wall-clock seconds.

    Parameterised over the backend on 2026-08-20 so that the CLI arena runs the
    *same* estimator rather than a second copy of it. The `dev` caller passes
    exactly what this function used to hardcode.
    """
    checkpoint = OUT / f"{prefix}-{label}.jsonl"
    timing = OUT / f"{prefix}-{label}-timing.json"

    started = time.monotonic()
    produced = run_arm(
        pool,
        build_arm("off"),
        model=model,
        checkpoint=checkpoint,
        call=call,
        ledger=BudgetLedger(limit_usd=budget_usd),
        expected_cost_usd=expected_cost_usd,
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
    parser = argparse.ArgumentParser(description="concurrency equivalence falsifier")
    parser.add_argument(
        "--backend",
        choices=("dev", "cli"),
        default="dev",
        help="dev: the free local arena, the 2026-08-19 run. cli: the Claude Code backend.",
    )
    parser.add_argument("--prefix", default=None, help="checkpoint stem; overrides DE_CONC_PREFIX")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    if args.backend == "cli":
        main_cli(args.prefix or os.environ.get("DE_CONC_PREFIX", "concurrency-cli"))
        return
    main_dev(args.prefix or PREFIX)


def main_dev(prefix: str) -> None:
    card = show(MODEL, endpoint=ollama())
    assert_isolated(card)
    print(f"model card: system={len(card.system)} chars, template={len(card.template)} chars\n")

    pool = items()
    print(f"{len(pool)} items from {TRIGGERS.relative_to(REPO_ROOT)}\n")

    arms: dict[str, tuple[dict[str, RunRecord], float]] = {}
    for label, concurrency in (("S1", 1), ("S2", 1), ("C", CONCURRENCY)):
        records, elapsed = run(
            label, pool, concurrency, prefix=prefix, model=MODEL, call=local_call(MODEL)
        )
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
    written = OUT / f"{prefix}-summary.json"
    written.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nwrote {written.relative_to(REPO_ROOT)}")


def cli_items() -> list[Item]:
    """The generated corpus, the same one `scripts/calibrate.py` runs.

    The trigger turns are not used here. This estimator reads the *parsed
    answer*, which is the quantity that reaches a published number, and only
    this corpus has an answer to parse.
    """
    from decision_evals.generators import generate, load_all

    return [item for template in load_all() for item in generate(template, CLI_SEED)]


def _agreement(
    left: dict[str, RunRecord], right: dict[str, RunRecord], ids: list[str]
) -> list[int]:
    return [int(left[i].parsed == right[i].parsed) for i in ids]


def _text_agreement(
    left: dict[str, RunRecord], right: dict[str, RunRecord], ids: list[str]
) -> float:
    return sum(int(left[i].response == right[i].response) for i in ids) / len(ids) if ids else 0.0


def main_cli(prefix: str) -> None:
    """The Claude Code backend, registered 2026-08-20.

    Everything below is the estimator the prediction names, and nothing here
    chooses a number the prediction did not. The `dev` path above is untouched.
    """
    assert_model_allowed("screen", CLI_MODEL)

    pool = cli_items()
    print(f"{len(pool)} items from the generated corpus at seed {CLI_SEED}")
    print(f"model {CLI_MODEL}, arms {[label for label, _ in CLI_ARMS]}\n")

    with tempfile.TemporaryDirectory(prefix="de-conc-") as scratch:
        print(f"preflight against {CLI_MODEL} ...", flush=True)
        preflight(model=CLI_MODEL, cwd=scratch)

        arms: dict[str, tuple[dict[str, RunRecord], float]] = {}
        for label, concurrency in CLI_ARMS:
            records, elapsed = run(
                label,
                pool,
                concurrency,
                prefix=prefix,
                model=CLI_MODEL,
                call=default_call(CLI_MODEL, scratch),
                budget_usd=50.0,
                expected_cost_usd=0.01,
            )
            arms[label] = (by_id(records), elapsed)
            print(f"{label}: {len(records)} records, {elapsed:.1f}s wall-clock", flush=True)

    s1, s2, c = arms["S1"][0], arms["S2"][0], arms["C"][0]
    ids = sorted(set(s1) & set(s2) & set(c))
    print(f"\n{len(ids)} items present in all three arms")

    infrastructure: ZeroCause = "infrastructure"
    failures = {
        label: sum(1 for i in ids if arm[i].zero_cause == infrastructure)
        for label, (arm, _) in arms.items()
    }
    print(f"infrastructure zeros: {failures}")

    # PRIMARY. `parsed`, not `response`: the prediction names the extracted
    # answer, and on this backend the prose is sampled and reproduces nothing.
    b = _agreement(s1, s2, ids)
    c1 = _agreement(s1, c, ids)
    c2 = _agreement(s2, c, ids)
    agree_serial = sum(b) / len(ids)
    agree_c1 = sum(c1) / len(ids)
    agree_c2 = sum(c2) / len(ids)

    print(f"\nagree_serial (the floor, S1 vs S2): {agree_serial:.4f}")
    print(f"agree_C1 (S1 vs C):                 {agree_c1:.4f}")
    print(f"agree_C2 (S2 vs C):                 {agree_c2:.4f}")
    print(f"band: min(agree_C1, agree_C2) >= {agree_serial - CLI_BAND:.4f}")

    killed = agree_serial < CLI_KILL_FLOOR
    if killed:
        print(
            f"\nKILL FIRED: agree_serial {agree_serial:.4f} < {CLI_KILL_FLOOR}. Two serial "
            "passes cannot agree with each other above the chance floor for a two-valued "
            "answer, so the primary is abandoned and the token secondary is the result."
        )
    else:
        inside = min(agree_c1, agree_c2) >= agree_serial - CLI_BAND
        print(f"\nprimary: {'INSIDE' if inside else 'OUTSIDE'} the registered band")

    test = mcnemar_exact(b, c1, alternative="two-sided")
    print(
        f"McNemar exact, two-sided, (b, c1): discordant={test.n_discordant} "
        f"(C-only {test.treatment_wins}, S2-only {test.control_wins}) "
        f"p={test.p_value:.4f}"
    )

    # SECONDARY, used only if the kill fires. A fixed prompt tokenises the same
    # way every time, so this is something concurrency must not change and a
    # sampled model cannot break.
    tokens_match = all(s1[i].input_tokens == s2[i].input_tokens == c[i].input_tokens for i in ids)
    print(f"\nsecondary -- input_tokens identical across all three arms: {tokens_match}")

    # SECONDARY, registered as expected-near-zero so that a zero here is not
    # read afterwards as a discovery.
    text_rates = {
        "S1_vs_S2": _text_agreement(s1, s2, ids),
        "S1_vs_C": _text_agreement(s1, c, ids),
        "S2_vs_C": _text_agreement(s2, c, ids),
    }
    print("secondary -- exact text agreement (predicted near zero in every pair):")
    for pair, rate in text_rates.items():
        print(f"    {pair}: {rate:.4f}")

    # SECONDARY with a band and no confirmatory weight.
    accuracy = {
        label: sum(arm[i].correct for i in ids) / len(ids) for label, (arm, _) in arms.items()
    }
    accuracy_gap = abs(accuracy["C"] - accuracy["S1"])
    print(
        "secondary -- accuracy per arm: " + ", ".join(f"{k} {v:.4f}" for k, v in accuracy.items())
    )
    print(f"    |acc_C - acc_S1| = {accuracy_gap:.4f}, band 0.05: {accuracy_gap <= 0.05}")

    speedup = arms["S1"][1] / arms["C"][1] if arms["C"][1] else 0.0
    print(f"\nspeedup, S1 / C wall-clock: {speedup:.2f}x")

    summary: dict[str, Any] = {
        "backend": "cli",
        "prediction": "notebook/2026-08-20-prediction-concurrency-on-the-cli-backend.md",
        "n_items": len(ids),
        "model": CLI_MODEL,
        "seed": CLI_SEED,
        "arms": [{"label": label, "concurrency": n} for label, n in CLI_ARMS],
        "primary_field": "parsed",
        "agree_serial": agree_serial,
        "agree_C1": agree_c1,
        "agree_C2": agree_c2,
        "band_floor": agree_serial - CLI_BAND,
        "kill_fired": killed,
        "inside_band": bool(min(agree_c1, agree_c2) >= agree_serial - CLI_BAND),
        "input_tokens_identical": tokens_match,
        "text_agreement": text_rates,
        "accuracy": accuracy,
        "accuracy_gap": accuracy_gap,
        "accuracy_gap_within_band": bool(accuracy_gap <= 0.05),
        "infrastructure_zeros": failures,
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
    written = OUT / f"{prefix}-summary.json"
    written.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nwrote {written.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
