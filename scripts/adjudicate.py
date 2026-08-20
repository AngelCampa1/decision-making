"""Track N3: blind label adjudication for a trigger corpus.

**The check that has never run here.** Twenty-one of twenty-one scored failures
across three corpora were the answer key rather than the model, and version 3
multiplies the key's surface area by roughly fifty: a 1,200-word turn has fifty
times as many places to be wrong about what is being asked, and the error would
be *correlated with the independent variable*, so long items would look harder
because their labels are worse.

**Blind means blind.** Each adjudicator sees the turn and the skill's own
`Abort if` clauses. It does not see my label, my `why`, the case id, the band,
the triple, or the other adjudicators. Three independent instances per turn,
each in its own isolated conversation with a fresh working directory.

**The resolution rule is mechanical and is fixed before the run**, per the plan
in `docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md`:

* unanimous agreement with my label -> keep
* 2-of-3 against me -> the label moves, and the notebook says which and why
* 3-way split is impossible on a binary question, so its analogue here is a
  2-1 split *agreeing* with me, which keeps the label and is recorded as contested

**Pre-registered kill: more than 20% of labels moving retires the corpus.** That
is the falsifier most likely to fire, and it is checked by
:func:`adjudication_outcome` rather than by anybody's judgement after the fact.

This script scores nothing about model quality. It compares one set of labels
against another set of labels, which is the one comparison that does not require
deciding a response was wrong.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
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
from decision_evals.stats.agreement import (  # noqa: E402
    effective_raters,
    fleiss_kappa,
    krippendorff_alpha,
    percent_agreement,
    unanimity_rate,
)
from decision_evals.triggers import (  # noqa: E402
    TriggerCase,
    load_trigger_set,
    parse_only,
    select_cases,
)

#: The adjudicator's whole context. Deliberately *not* the skill description:
#: that is the thing under test in every other run, and an adjudicator shown it
#: would be reproducing the description's reading of the turn rather than
#: independently judging what the turn asks for. What it gets is the plain
#: question the label is supposed to answer, plus the shipped abort conditions,
#: which are the closest thing this repository has to a definition.
SYSTEM = (
    "You are labelling messages for a dataset. For each message, decide one "
    "thing: is the person asking someone to help them DECIDE something?\n\n"
    "Answer yes when the message puts an open choice in front of the reader and "
    "wants a recommendation, a judgement, or help working out what to do -- "
    "even if it is phrased as a statement, has no question mark, or buries the "
    "question in the middle.\n\n"
    "Answer no when the message asks for something with a determinate answer or "
    "a produced artefact: a lookup, a calculation, a diagnosis, a summary, a "
    "piece of writing, an explanation of a previous answer, or a task whose "
    "decision has already been made and stated.\n\n"
    "A long message full of pasted context is not automatically a decision, and "
    "a short one is not automatically not. Judge what is being asked for.\n\n"
    "Answer with a single line of JSON and nothing else:\n"
    '{"decision": true|false, "why": "<one short sentence>"}'
)

CHECKPOINT = REPO_ROOT / "results" / "triggers" / "adjudication.jsonl"

#: Pre-registered. More than this share of labels moving retires the corpus.
KILL_THRESHOLD = 0.20

#: Independent instances per turn. Odd, so a binary question always resolves.
ADJUDICATORS = 3


def abort_clauses(skill_path: Path) -> str:
    """The shipped `Abort if` block, verbatim, or empty if the skill has none."""
    body = parse_skill(skill_path).body
    lines: list[str] = []
    capturing = False
    for line in body.splitlines():
        if line.strip().lower().startswith(("**abort if", "## abort if", "abort if")):
            capturing = True
            lines.append(line)
            continue
        if capturing:
            if line.startswith("#") or (line.strip() == "" and lines and lines[-1].strip() == ""):
                break
            lines.append(line)
    return "\n".join(lines).strip()


def ask(case: TriggerCase, model: str, system: str) -> tuple[bool | None, str]:
    """One adjudicator's verdict on one turn, plus the raw reply."""
    prompt = f"## Message\n\n{case.turn}"
    with (
        isolated_cwd("de-adjudicate-") as cwd,
        Conversation(system_prompt=system, model=model, cwd=cwd) as chat,
    ):
        result = chat.send(prompt)
        chat.receipt.assert_isolated()
    return parse(result.text), result.text


def parse(text: str) -> bool | None:
    """`decision` out of the reply, or ``None`` when it cannot be read.

    ``None`` is a missing measurement rather than a "no". Scoring an unparseable
    reply as disagreement would turn a format problem into label movement, which
    is the exact shape of defect this run exists to detect.
    """
    for chunk in _json_candidates(text):
        try:
            loaded = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(loaded, dict) and isinstance(loaded.get("decision"), bool):
            return bool(loaded["decision"])
    return None


def _json_candidates(text: str) -> list[str]:
    stripped = text.strip()
    candidates = [stripped]
    start, end = stripped.find("{"), stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    return candidates


def load_done(path: Path) -> dict[tuple[str, int], dict[str, object]]:
    if not path.exists():
        return {}
    done: dict[tuple[str, int], dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            done[(str(row["case"]), int(row["judge"]))] = row
    return done


def collect(
    cases: tuple[TriggerCase, ...],
    model: str,
    system: str,
    *,
    checkpoint: Path = CHECKPOINT,
    judges: int = ADJUDICATORS,
) -> dict[tuple[str, int], dict[str, object]]:
    """Every case, `judges` times, checkpointing after each call."""
    done = load_done(checkpoint)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    total = len(cases) * judges
    with checkpoint.open("a", encoding="utf-8") as handle:
        for judge in range(judges):
            for index, case in enumerate(cases):
                if (case.id, judge) in done:
                    continue
                try:
                    verdict, raw = ask(case, model, system)
                except IsolationError:
                    raise
                except CliError as error:
                    verdict, raw = None, str(error)
                    print(f"  j{judge} {case.id}: call failed -- {error}")
                row = {
                    "case": case.id,
                    "judge": judge,
                    "adjudicated": verdict,
                    "label": case.should_fire,
                    "band": case.band,
                    "triple": case.triple,
                    "kind": case.kind,
                    "model": model,
                    "raw": raw,
                }
                handle.write(json.dumps(row) + "\n")
                handle.flush()
                done[(case.id, judge)] = row
                seen = judge * len(cases) + index + 1
                if seen % 20 == 0 or seen == total:
                    print(f"  {seen}/{total}", flush=True)
    return done


@dataclass(frozen=True)
class CaseOutcome:
    """What the three adjudicators said about one turn."""

    case: str
    label: bool
    votes: tuple[bool, ...]
    band: str | None

    @property
    def unparseable(self) -> int:
        return ADJUDICATORS - len(self.votes)

    @property
    def ratings(self) -> tuple[bool | None, ...]:
        """One slot per adjudicator, ``None`` where the reply could not be read.

        ``votes`` holds only the readable replies, which is what the resolution
        rule needs — a majority is a majority of the votes that exist. The
        agreement estimators need the *shape* instead: three judges of whom one
        produced nothing is not the same evidence as two judges who agreed, and
        collapsing them is how a formatting problem turns into a reliability
        claim.
        """
        return (*self.votes, *([None] * self.unparseable))

    @property
    def agreeing(self) -> int:
        return sum(1 for vote in self.votes if vote == self.label)

    @property
    def moves(self) -> bool:
        """A majority of *parseable* votes disagreeing with the label."""
        return bool(self.votes) and self.agreeing * 2 < len(self.votes)

    @property
    def contested(self) -> bool:
        """Kept, but not unanimously."""
        return not self.moves and self.agreeing != len(self.votes)


@dataclass(frozen=True)
class AdjudicationOutcome:
    """The whole run, and whether the corpus survives it."""

    outcomes: tuple[CaseOutcome, ...]
    panel: tuple[str, ...] = ()
    threshold: float = KILL_THRESHOLD

    @property
    def n_cases(self) -> int:
        return len(self.outcomes)

    @property
    def moved(self) -> tuple[CaseOutcome, ...]:
        return tuple(outcome for outcome in self.outcomes if outcome.moves)

    @property
    def contested(self) -> tuple[CaseOutcome, ...]:
        return tuple(outcome for outcome in self.outcomes if outcome.contested)

    @property
    def movement_rate(self) -> float:
        return len(self.moved) / self.n_cases if self.n_cases else 0.0

    @property
    def retired(self) -> bool:
        """The pre-registered kill, evaluated mechanically."""
        return self.movement_rate > self.threshold

    @property
    def unanimous_rate(self) -> float:
        """Cases where every adjudicator was readable *and* agreed with my label.

        The denominator is every case, including ones nobody could be read on:
        an unreadable reply is a missing rating, and a missing rating is not
        agreement. Computed by :func:`~decision_evals.stats.agreement.unanimity_rate`
        so that this repository carries one definition of unanimity rather than
        two — the inline version this replaced hard-coded the same rule and
        agreed with it case for case at three judges.

        Note that this is agreement *with the key*, not between the judges. The
        inter-rater block in :func:`report` is the one that says whether three
        judges agreeing means anything.
        """
        if not self.outcomes:
            return 0.0
        return unanimity_rate([(case.label, *case.ratings) for case in self.outcomes]).rate


def adjudication_outcome(
    done: dict[tuple[str, int], dict[str, object]],
) -> AdjudicationOutcome:
    """Fold the raw rows into per-case outcomes and the kill decision."""
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in done.values():
        grouped.setdefault(str(row["case"]), []).append(row)
    outcomes = []
    for case in sorted(grouped):
        rows = grouped[case]
        votes = tuple(bool(r["adjudicated"]) for r in rows if r["adjudicated"] is not None)
        outcomes.append(
            CaseOutcome(
                case=case,
                label=bool(rows[0]["label"]),
                votes=votes,
                band=rows[0]["band"] if rows[0]["band"] is None else str(rows[0]["band"]),
            )
        )
    # The panel's composition, kept because the reliability block cannot be
    # read without it. Every coefficient there measures how much these judges
    # agree; none of them measures how many judges this is, and three fresh
    # instances of one model at one tier is not three raters' worth of
    # evidence however high the coefficient comes out.
    #
    # One entry per *judge slot*, not per row. The slot is the rater the
    # coefficients count -- 783 rows here are three judges over 261 cases, and
    # a panel line reading "haiku x783" would describe the checkpoint rather
    # than the panel. A slot that somehow ran on two models is named as such
    # rather than collapsed to one of them.
    by_judge: dict[int, set[str]] = {}
    for row in done.values():
        if row.get("model"):
            by_judge.setdefault(int(row["judge"]), set()).add(str(row["model"]))  # type: ignore[call-overload]
    panel = tuple(sorted("+".join(sorted(models)) for models in by_judge.values() if models))
    return AdjudicationOutcome(outcomes=tuple(outcomes), panel=panel)


def _agreement_line(label: str, compute: Callable[[], float]) -> str:
    """One reported coefficient, or the reason there is not one.

    Every estimator refuses a degenerate input rather than returning a plausible
    zero, so a run where all three judges said the same thing about everything
    prints why alpha is unavailable instead of printing 0.000 and being believed.
    """
    try:
        return f"    {label:<20s} {compute():.3f}"
    except ValueError as error:
        return f"    {label:<20s} n/a -- {error}"


def report_reliability(outcome: AdjudicationOutcome) -> None:
    """Agreement *between the judges*, which the key is not involved in.

    ``unanimous with key`` above measures the judges against my labels and is
    therefore a statement about the corpus. This block measures the judges
    against each other and is a statement about the *instrument*: three blind
    adjudicators who disagree with one another cannot move a label on anyone's
    behalf, and until this ran there was no number here that would have said so.

    Fleiss' kappa is reported beside Krippendorff's alpha because they answer
    the same question differently under missing data — Fleiss refuses the run
    outright the moment one reply is unreadable, alpha drops the unpairable
    units and says how many. When both are available they differ only by the
    finite-sample factor ``(n - 1) / n``.

    **Every one of those coefficients answers how much these judges agree, not
    how many judges this is.** Kohli (arXiv:2605.29800) finds nine frontier
    judges from seven model families "effectively provide only about 2
    independent votes' worth of information". So the panel's composition is
    printed above the coefficients and its effective size below them: a high
    kappa over three fresh instances of one model at one tier is not three
    raters' worth of evidence, and the coefficient alone will be read as though
    it were.

    The effective size is the weaker statement and says so.
    :func:`~decision_evals.stats.agreement.effective_raters` divides the rater
    count by the design effect of the agreement observed here. It is **not**
    Kohli's cross-family figure and cannot be computed on this design —
    agreement driven by the item and agreement driven by the shared model are
    not separately identified from ratings one model produced.
    """
    ratings = [case.ratings for case in outcome.outcomes]
    print("\n  inter-rater agreement (judges against each other, key not involved):")
    print(f"    {'panel':<20s} {_panel_line(outcome.panel)}")
    for line in (
        _agreement_line("pairwise agreement", lambda: percent_agreement(ratings).agreement),
        _agreement_line("unanimous judges", lambda: unanimity_rate(ratings).rate),
        _agreement_line("Fleiss kappa", lambda: fleiss_kappa(ratings).kappa),
        _agreement_line("Krippendorff alpha", lambda: krippendorff_alpha(ratings).alpha),
        _agreement_line("effective raters", lambda: effective_raters(ratings).effective),
    ):
        print(line)
    print(
        "    ^ effective raters is the rater count over the design effect of the agreement "
        "above, and it is not Kohli's cross-family n_eff: one model resampled cannot "
        "separate agreeing about the item from sharing the model."
    )


def _panel_line(panel: tuple[str, ...]) -> str:
    """Who the judges were, as counts by model.

    Printed because a coefficient over three samples of one model reads exactly
    like a coefficient over three independent judges, and nothing else in the
    block distinguishes them.
    """
    if not panel:
        return "unrecorded -- these rows carry no `model`, so the panel cannot be described"
    counts = Counter(panel)
    named = ", ".join(f"{model} x{count}" for model, count in sorted(counts.items()))
    if len(counts) == 1:
        return f"{named} -- one model, sampled {sum(counts.values())} times"
    return f"{named} -- {len(counts)} distinct models"


def report(outcome: AdjudicationOutcome) -> None:
    print("\n=== adjudication ===")
    print(f"  cases                {outcome.n_cases}")
    print(f"  unanimous with key   {outcome.unanimous_rate:.3f}")
    print(f"  contested (2-1 kept) {len(outcome.contested)}")
    print(f"  moved (2-1 against)  {len(outcome.moved)}")
    print(f"  movement rate        {outcome.movement_rate:.3f}   (kill above {KILL_THRESHOLD})")
    report_reliability(outcome)
    per_band: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    for case in outcome.outcomes:
        totals[str(case.band)] += 1
        if case.moves:
            per_band[str(case.band)] += 1
    print("\n  movement by band:")
    for band in sorted(totals):
        n, d = per_band[band], totals[band]
        print(f"    {band:3s} {n:3d}/{d:3d}  {n / d:.3f}")
    if outcome.moved:
        print("\n  labels the adjudicators moved:")
        for case in outcome.moved:
            direction = "positive -> negative" if case.label else "negative -> positive"
            print(f"    {case.case:8s} {direction}  votes {case.votes}")
    print(
        "\n  CORPUS RETIRED: movement above the pre-registered threshold"
        if outcome.retired
        else "\n  corpus survives the pre-registered kill"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--judges", type=int, default=ADJUDICATORS)
    parser.add_argument(
        "--set",
        default=str(REPO_ROOT / "datasets" / "triggers" / "decision-making" / "index.yaml"),
    )
    parser.add_argument("--checkpoint", default=str(CHECKPOINT))
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument(
        "--only",
        default=None,
        help=(
            "Restrict to specific case ids: a comma-separated list, or "
            "@path/to/ids.txt (one id per line, # comments allowed). Unknown ids "
            "raise rather than silently selecting nothing. Combines with "
            "--missing-only."
        ),
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help=(
            "Restrict to cases with zero adjudication records in the checkpoint "
            "at all -- not cases with some judges done and others pending, which "
            "--report-only's own resume logic already fills in. For re-running "
            "after a corpus edit, where only the new or changed items need "
            "adjudicating and everything already on record must be left alone."
        ),
    )
    args = parser.parse_args()

    trigger_set = load_trigger_set(Path(args.set))
    checkpoint = Path(args.checkpoint)
    only = parse_only(args.only) if args.only else None
    exclude_ids = None
    if args.missing_only:
        exclude_ids = frozenset(case_id for case_id, _judge in load_done(checkpoint))
    cases = select_cases(trigger_set.cases, only=only, exclude_ids=exclude_ids)

    if not args.report_only:
        clauses = abort_clauses(REPO_ROOT / "skills" / trigger_set.skill / "SKILL.md")
        system = SYSTEM if not clauses else f"{SYSTEM}\n\nThe tool's own exclusions:\n{clauses}"
        done_before = load_done(checkpoint)
        remaining = sum(
            1
            for case in cases
            for judge in range(args.judges)
            if (case.id, judge) not in done_before
        )
        print(f"selected {len(cases)} cases x {args.judges} judges on {args.model}")
        print(f"  = {remaining} calls remaining after resume, checkpointed at {checkpoint}")
        collect(cases, args.model, system, checkpoint=checkpoint, judges=args.judges)

    done = load_done(checkpoint)
    if only is not None:
        # Scope the report to what was selected, not the whole checkpoint --
        # otherwise `--only` would narrow which calls get made but not which
        # ones get reported on, and a scoped run of an unrelated band would
        # silently fold its records into someone else's numbers.
        wanted = set(only)
        done = {key: row for key, row in done.items() if key[0] in wanted}
    if not done:
        print("no adjudication records")
        return 1
    unparseable = sum(1 for row in done.values() if row["adjudicated"] is None)
    print(f"\n  records {len(done)}, unparseable {unparseable}")
    report(adjudication_outcome(done))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
