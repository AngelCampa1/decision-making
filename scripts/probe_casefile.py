"""Phase 0 probe for the casefile venue.

Deliberately outside ``decision_evals``. This exists to answer one question --
*can the control arm fail here at all* -- before any schema, generator, scorer or
golden file is built around the venue. The last two corpora were scaled, pinned
and fingerprinted before anyone checked that, and both turned out to measure
nothing. A throwaway script that answers it in a day is worth more than a correct
abstraction over a dead venue.

So the casefiles are hand-authored YAML with hand-written ground truth, the
parser is local, and none of it is reused. What survives Phase 0 is the *finding*,
not the code.

Two gates, both on the control arm:

1. **Admissibility below 0.85.** Above that there is no headroom.
2. **A non-zero trap rate at order >= 2.** A venue where the model never falls
   for a second-order trap cannot measure a forward-simulation skill, however
   hard it is in other respects.

Usage:
    python -m uv run python scripts/probe_casefile.py [--model haiku] [--case ID]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final

import yaml

from decision_evals.arenas import assert_model_allowed
from decision_evals.budget import BudgetError, BudgetLedger
from decision_evals.providers.claude_code import CliError
from decision_evals.providers.claude_code import preflight as cli_preflight
from decision_evals.providers.claude_code import run as cli_run

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_DIR = REPO_ROOT / "datasets" / "probe"
CHECKPOINT = REPO_ROOT / "results" / "probe" / "casefile-probe.jsonl"

ADMISSIBILITY_CEILING: Final = 0.85
BANDS: Final = ("negligible", "low", "moderate", "high", "severe")

#: The casefile framing. Every arm will share this; the probe runs `off` only.
BASE_FRAMING: Final = (
    "You are advising on a professional matter. You will be given a case file of "
    "documents, a question, a numbered list of conditions that may or may not "
    "bear on the decision, and a list of candidate actions identified by "
    "reference. Several conditions will not matter. Some candidate actions are "
    "wrong to take. There is no single correct set of actions -- there are "
    "recommendations that hold up and recommendations that do not."
)

#: Present in every arm without exception, exactly as FORMAT_CONTRACT is in the
#: single-turn venue. Block names deliberately avoid the evidence-ledger skill's
#: own LEDGER / SET ASIDE / THEREFORE vocabulary, so the `on` arm gets no lexical
#: head start on the contract.
FORMAT_CONTRACT: Final = (
    "Reason as much as you find useful, then end your reply with exactly these "
    "five blocks in this order and nothing after them:\n"
    "\n"
    "CONDITIONS\n"
    "  one line per condition, every condition listed, in the form\n"
    "  C1: governs\n"
    "  C2: does not govern\n"
    "CONSEQUENCES\n"
    "  free text -- for each action you recommend, what follows from it\n"
    "EXPOSURE\n"
    "  one word: negligible, low, moderate, high, or severe\n"
    "MISSING\n"
    "  the single fact that would most change your recommendation, or NONE\n"
    "ACTIONS\n"
    "  the actions you recommend, most urgent first, one per line, by\n"
    "  identifier only, in the form\n"
    "  1. A3\n"
    "  2. A7"
)

#: The menu-free contract. The first probe run scored 12/12 on avoiding
#: prohibited actions, which cannot be read as forward reasoning while the
#: candidate list spells the reasoning out -- "Defer the Year 3 amendment until
#: after the Year 1 assessment window closes" is the insight, printed on the
#: menu. AgentAtlas measured 14-40pp from menu presence alone with plain option
#: labels; this menu carries far more than a label. Removing it is the only way
#: to tell recognition from generation, and it is the difference between a
#: publishable negative and an artefact.
FORMAT_CONTRACT_FREE: Final = (
    "Reason as much as you find useful, then end your reply with exactly these "
    "five blocks in this order and nothing after them:\n"
    "\n"
    "CONDITIONS\n"
    "  one line per condition, every condition listed, in the form\n"
    "  C1: governs\n"
    "  C2: does not govern\n"
    "CONSEQUENCES\n"
    "  free text -- for each step you recommend, what follows from it\n"
    "EXPOSURE\n"
    "  one word: negligible, low, moderate, high, or severe\n"
    "MISSING\n"
    "  the single fact that would most change your recommendation, or NONE\n"
    "ACTIONS\n"
    "  the steps you recommend, most urgent first, one per line, each a single\n"
    "  short sentence naming a concrete step"
)

#: The bare contract: documents and a question, nothing else. The menu-free run
#: still handed the model a numbered list of the conditions in play, so a 0.97
#: condition recall measured *classification* of an extracted list, not
#: discovery. Real use supplies neither the list nor the risk question. This mode
#: removes the last of the scaffolding so the task is the one the skills are
#: actually for.
BARE_FRAMING: Final = (
    "You are advising on a professional matter. You will be given a case file of "
    "documents and a question. Work out what bears on the decision and what "
    "should be done. There is no single correct set of steps -- there are "
    "recommendations that hold up and recommendations that do not."
)

FORMAT_CONTRACT_BARE: Final = (
    "Reason as much as you find useful, then end your reply with exactly these "
    "three blocks in this order and nothing after them:\n"
    "\n"
    "CONSEQUENCES\n"
    "  free text -- for each step you recommend, what follows from it\n"
    "MISSING\n"
    "  the single fact that would most change your recommendation, or NONE\n"
    "ACTIONS\n"
    "  the steps you recommend, most urgent first, one per line, each a single\n"
    "  short sentence naming a concrete step"
)

_BLOCK_NAMES: Final = ("CONDITIONS", "CONSEQUENCES", "EXPOSURE", "MISSING", "ACTIONS")
_BLOCK_HEADER: Final = re.compile(
    r"^[\s>*\-#]*(?:\*\*|__|`)?\s*(" + "|".join(_BLOCK_NAMES) + r")\s*(?:\*\*|__|`)?\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_CONDITION_LINE: Final = re.compile(r"\b(c\d+)\b\s*[:\-—]\s*(.+)", re.IGNORECASE)
_ACTION_REF: Final = re.compile(r"\b(a\d+)\b", re.IGNORECASE)


# --------------------------------------------------------------------------
# casefiles


@dataclass(frozen=True)
class Casefile:
    """One hand-authored case, with its hand-written ground truth."""

    raw: dict[str, Any]

    @property
    def case_id(self) -> str:
        return str(self.raw["case_id"])

    @property
    def trap_order(self) -> Any:
        return self.raw["trap_order"]

    @property
    def trap_kind(self) -> str:
        return str(self.raw.get("trap_kind", "none"))

    @property
    def conditions(self) -> list[dict[str, Any]]:
        return list(self.raw["conditions"])

    @property
    def actions(self) -> list[dict[str, Any]]:
        return list(self.raw["actions"])

    def by_status(self, status: str) -> list[str]:
        return [a["id"].upper() for a in self.actions if a["status"] == status]

    def by_failure_kind(self, kind: str) -> list[str]:
        return [a["id"].upper() for a in self.actions if a.get("failure_kind") == kind]

    @property
    def governing(self) -> set[str]:
        return {c["id"].upper() for c in self.conditions if c["governs"]}


def load_casefiles(directory: Path = PROBE_DIR) -> list[Casefile]:
    """Read every probe casefile, in filename order."""
    cases = [
        Casefile(raw=yaml.safe_load(path.read_text(encoding="utf-8")))
        for path in sorted(directory.glob("*.yaml"))
    ]
    if not cases:
        raise SystemExit(f"no casefiles in {directory}")
    return cases


def validate(cases: list[Casefile]) -> list[str]:
    """Check the hand-written ground truth for the mistakes hand-writing makes.

    Twelve files of cross-referenced identifiers is exactly where a typo hides,
    and a dangling ``licensed_by`` silently changes what counts as the raincoat.
    Cheap to check, and a wrong answer key is indistinguishable from a model
    failure once the run is over.
    """
    problems: list[str] = []
    for case in cases:
        where = case.case_id
        doc_ids = {d["id"] for d in case.raw["documents"]}
        condition_ids = {c["id"] for c in case.conditions}
        action_ids = [a["id"] for a in case.actions]

        if case.trap_order not in ("none", 1, 2, 3):
            problems.append(f"{where}: trap_order {case.trap_order!r} is not none/1/2/3")
        if len(set(action_ids)) != len(action_ids):
            problems.append(f"{where}: duplicate action ids")
        if len(condition_ids) != len(case.conditions):
            problems.append(f"{where}: duplicate condition ids")
        if not case.by_status("required"):
            problems.append(f"{where}: no required actions, so admissibility is trivial")
        if not case.by_failure_kind("unjustified"):
            problems.append(f"{where}: no unjustified action, so the raincoat is unmeasurable")
        if not case.governing:
            problems.append(f"{where}: no governing conditions")

        for condition in case.conditions:
            if condition["source"] not in doc_ids:
                problems.append(
                    f"{where}: {condition['id']} cites unknown document {condition['source']}"
                )
        for action in case.actions:
            for cid in action.get("licensed_by", []):
                if cid not in condition_ids:
                    problems.append(f"{where}: {action['id']} licensed_by unknown condition {cid}")
            if action["status"] not in ("required", "prohibited", "optional"):
                problems.append(f"{where}: {action['id']} has status {action['status']!r}")
            if action["status"] == "prohibited" and "failure_kind" not in action:
                problems.append(f"{where}: {action['id']} is prohibited with no failure_kind")

        # An unjustified action licensed by a governing condition is not the
        # raincoat -- it has real support and would be arguable.
        for action_id in case.by_failure_kind("unjustified"):
            action = next(a for a in case.actions if a["id"] == action_id)
            if set(action.get("licensed_by", [])) & case.governing:
                problems.append(
                    f"{where}: {action_id} is called unjustified but a governing condition licenses it"
                )

        if case.raw["exposure"]["band"] not in BANDS:
            problems.append(
                f"{where}: exposure band {case.raw['exposure']['band']!r} is not a band"
            )
        first_order = case.raw["exposure"].get("first_order_wrong_answer")
        if first_order is not None and first_order == case.raw["exposure"]["band"]:
            problems.append(f"{where}: the first-order wrong answer equals the right one")
        if case.trap_order == "none" and case.by_failure_kind("trap"):
            problems.append(f"{where}: control stratum should have no trap actions")
        if case.trap_order != "none" and not case.by_failure_kind("trap"):
            problems.append(f"{where}: trap_order {case.trap_order} with no trap action")

        pivot = case.raw.get("pivot") or {}
        if pivot.get("present") and not pivot.get("accepts"):
            problems.append(f"{where}: pivot present with no accepted phrasings")
    return problems


def render(case: Casefile) -> str:
    """Render the user-facing case file.

    Arm-independent, exactly as ``render_item`` is in the single-turn venue: the
    action menu is the largest known scaffolding effect in the literature, so it
    cannot be allowed to vary between arms.
    """
    documents = "\n\n".join(
        f"[{doc['id']}] {doc['title']}\n{doc['body'].rstrip()}" for doc in case.raw["documents"]
    )
    conditions = "\n".join(f"  {c['id'].upper()}. {c['text']}" for c in case.conditions)
    actions = "\n".join(f"  {a['id'].upper()}. {a['text']}" for a in case.actions)
    return (
        f"CASE FILE — {len(case.raw['documents'])} documents\n\n"
        f"{documents}\n\n"
        f"{'=' * 60}\n\n"
        f"QUESTION: {case.raw['question'].strip()}\n\n"
        f"CONDITIONS IN PLAY\n{conditions}\n\n"
        f"CANDIDATE ACTIONS\n{actions}\n\n"
        f"RISK QUESTION: {case.raw['exposure_question'].strip()}"
    )


def render_no_menu(case: Casefile) -> str:
    """Render the same case file without the candidate action list.

    Identical in every other respect, so the menu is the only thing that varies
    between the two runs.
    """
    documents = "\n\n".join(
        f"[{doc['id']}] {doc['title']}\n{doc['body'].rstrip()}" for doc in case.raw["documents"]
    )
    conditions = "\n".join(f"  {c['id'].upper()}. {c['text']}" for c in case.conditions)
    return (
        f"CASE FILE — {len(case.raw['documents'])} documents\n\n"
        f"{documents}\n\n"
        f"{'=' * 60}\n\n"
        f"QUESTION: {case.raw['question'].strip()}\n\n"
        f"CONDITIONS IN PLAY\n{conditions}\n\n"
        f"RISK QUESTION: {case.raw['exposure_question'].strip()}"
    )


def render_bare(case: Casefile) -> str:
    """Documents and the question. No condition list, no menu, no risk question."""
    documents = "\n\n".join(
        f"[{doc['id']}] {doc['title']}\n{doc['body'].rstrip()}" for doc in case.raw["documents"]
    )
    return (
        f"CASE FILE — {len(case.raw['documents'])} documents\n\n"
        f"{documents}\n\n"
        f"{'=' * 60}\n\n"
        f"QUESTION: {case.raw['question'].strip()}"
    )


# --------------------------------------------------------------------------
# parsing


@dataclass(frozen=True)
class Parsed:
    """What could be read out of a response, block by block."""

    blocks_found: list[str]
    condition_votes: dict[str, bool]
    exposure: str | None
    missing: str
    actions: list[str]

    @property
    def complete(self) -> bool:
        return set(self.blocks_found) == set(_BLOCK_NAMES)


def split_blocks(response: str) -> dict[str, str]:
    """Split a response into its named blocks.

    The *last* occurrence of each header wins, matching ``parse_answer``'s
    last-answer-wins rule: a model that restates its blocks after further
    reasoning is standing behind the restatement.
    """
    matches = list(_BLOCK_HEADER.finditer(response))
    if not matches:
        return {}
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(response)
        blocks[match.group(1).upper()] = response[match.end() : end].strip()
    return blocks


def parse_response(response: str) -> Parsed:
    blocks = split_blocks(response)

    votes: dict[str, bool] = {}
    for line in blocks.get("CONDITIONS", "").splitlines():
        match = _CONDITION_LINE.search(line)
        if not match:
            continue
        verdict = match.group(2).casefold()
        # "does not govern" contains "govern", so the negative is tested first.
        if "not govern" in verdict or "does not" in verdict or verdict.strip() == "no":
            votes[match.group(1).upper()] = False
        elif "govern" in verdict or "yes" in verdict:
            votes[match.group(1).upper()] = True

    exposure_text = blocks.get("EXPOSURE", "").casefold()
    exposure = next((band for band in BANDS if band in exposure_text), None)

    seen: list[str] = []
    for ref in _ACTION_REF.findall(blocks.get("ACTIONS", "")):
        upper = ref.upper()
        if upper not in seen:
            seen.append(upper)

    return Parsed(
        blocks_found=sorted(blocks),
        condition_votes=votes,
        exposure=exposure,
        missing=blocks.get("MISSING", "").strip(),
        actions=seen,
    )


# --------------------------------------------------------------------------
# scoring


@dataclass(frozen=True)
class Scored:
    """One scored response. Admissibility is the conjunction; the rest diagnose it."""

    case_id: str
    trap_order: Any
    trap_kind: str
    admissible: bool
    missing_required: list[str] = field(default_factory=list)
    took_prohibited: list[str] = field(default_factory=list)
    trap_hit: bool = False
    unjustified_hit: bool = False
    pivot_ok: bool = False
    exposure_ok: bool = False
    exposure_said: str | None = None
    exposure_first_order: bool = False
    condition_precision: float = 0.0
    condition_recall: float = 0.0
    blocks_complete: bool = False
    blocks_found: list[str] = field(default_factory=list)


def score(case: Casefile, parsed: Parsed) -> Scored:
    recommended = set(parsed.actions)
    required = set(case.by_status("required"))
    prohibited = set(case.by_status("prohibited"))

    missing_required = sorted(required - recommended)
    took_prohibited = sorted(recommended & prohibited)

    pivot = case.raw.get("pivot") or {}
    if pivot.get("present"):
        haystack = parsed.missing.casefold()
        pivot_ok = any(phrase.casefold() in haystack for phrase in pivot.get("accepts", []))
    else:
        pivot_ok = parsed.missing.strip().upper().startswith("NONE")

    exposure_truth = str(case.raw["exposure"]["band"])
    first_order = case.raw["exposure"].get("first_order_wrong_answer")

    governing = case.governing
    voted_governing = {cid for cid, vote in parsed.condition_votes.items() if vote}
    hits = len(voted_governing & governing)
    precision = hits / len(voted_governing) if voted_governing else 0.0
    recall = hits / len(governing) if governing else 0.0

    # The primary. A response is admissible when it does everything the case
    # makes mandatory, nothing it makes prohibited (which already includes every
    # action foreclosed downstream and every action licensed only by a
    # non-governing condition), and names the pivot when the case has one.
    admissible = not missing_required and not took_prohibited and pivot_ok

    return Scored(
        case_id=case.case_id,
        trap_order=case.trap_order,
        trap_kind=case.trap_kind,
        admissible=admissible,
        missing_required=missing_required,
        took_prohibited=took_prohibited,
        trap_hit=bool(recommended & set(case.by_failure_kind("trap"))),
        unjustified_hit=bool(recommended & set(case.by_failure_kind("unjustified"))),
        pivot_ok=pivot_ok,
        exposure_ok=parsed.exposure == exposure_truth,
        exposure_said=parsed.exposure,
        exposure_first_order=parsed.exposure is not None and parsed.exposure == first_order,
        condition_precision=precision,
        condition_recall=recall,
        blocks_complete=parsed.complete,
        blocks_found=parsed.blocks_found,
    )


# --------------------------------------------------------------------------
# run loop


def completed(checkpoint: Path) -> set[str]:
    if not checkpoint.exists():
        return set()
    done = set()
    for line in checkpoint.read_text(encoding="utf-8").splitlines():
        try:
            done.add(json.loads(line)["case_id"])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--case", default="", help="run a single case id, for a smoke run")
    parser.add_argument("--budget", type=float, default=2.0)
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument(
        "--validate-only", action="store_true", help="check the answer key, spend nothing"
    )
    parser.add_argument(
        "--no-menu",
        action="store_true",
        help="withhold the candidate action list; recommendations are free text, read by hand",
    )
    parser.add_argument(
        "--bare",
        action="store_true",
        help="documents and the question only: no condition list, no menu, no risk question",
    )
    args = parser.parse_args()

    assert_model_allowed("screen", args.model)
    cases = load_casefiles()

    # Before anything is spent. A wrong answer key and a model failure are
    # indistinguishable once the run is over.
    problems = validate(cases)
    if problems:
        print(f"{len(problems)} problem(s) in the casefiles:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 2
    print(f"{len(cases)} casefiles validated", flush=True)
    if args.validate_only:
        return 0

    if args.case:
        cases = [c for c in cases if c.case_id == args.case]
        if not cases:
            raise SystemExit(f"no casefile with id {args.case!r}")

    if args.bare:
        checkpoint = CHECKPOINT.with_name("casefile-probe-bare.jsonl")
    elif args.no_menu:
        checkpoint = CHECKPOINT.with_name("casefile-probe-nomenu.jsonl")
    else:
        checkpoint = CHECKPOINT
    hand_read = args.bare or args.no_menu

    if not args.report_only:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        done = completed(checkpoint)
        ledger = BudgetLedger(limit_usd=args.budget)
        if args.bare:
            framing, contract = BARE_FRAMING, FORMAT_CONTRACT_BARE
        elif args.no_menu:
            framing = BASE_FRAMING.replace(
                "and a list of candidate actions identified by reference. ", ""
            ).replace(
                "Some candidate actions are wrong to take. ", "Some steps are wrong to take. "
            )
            contract = FORMAT_CONTRACT_FREE
        else:
            framing, contract = BASE_FRAMING, FORMAT_CONTRACT
        system_prompt = f"{framing}\n\n{contract}"

        with tempfile.TemporaryDirectory(prefix="de-probe-") as scratch:
            print(f"preflight against {args.model} ...", flush=True)
            cli_preflight(model=args.model, cwd=scratch)

            with checkpoint.open("a", encoding="utf-8") as handle:
                for case in cases:
                    if case.case_id in done:
                        continue
                    try:
                        ledger.assert_can_afford(0.05)
                    except BudgetError as exc:
                        print(f"\nstopping before {case.case_id}: {exc}", file=sys.stderr)
                        break
                    try:
                        result = cli_run(
                            render_bare(case)
                            if args.bare
                            else render_no_menu(case)
                            if args.no_menu
                            else render(case),
                            system_prompt=system_prompt,
                            model=args.model,
                            cwd=scratch,
                        )
                    except CliError as exc:
                        print(f"  {case.case_id}: call failed -- {exc}", file=sys.stderr)
                        continue
                    ledger = ledger.record(result.cost_usd)
                    scored = score(case, parse_response(result.text))
                    handle.write(
                        json.dumps(
                            {
                                **asdict(scored),
                                "model": result.model,
                                "cost_usd": result.cost_usd,
                                "response": result.text,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    handle.flush()
                    if hand_read:
                        # Action identifiers do not exist in these modes, so every
                        # automatic field except exposure is meaningless. Say so
                        # rather than print a scoreboard that reads as a result.
                        print(
                            f"  recorded {case.case_id}  order {scored.trap_order}  "
                            f"exposure={scored.exposure_said}",
                            flush=True,
                        )
                    else:
                        flag = "ok " if scored.admissible else "FAIL"
                        print(
                            f"  {flag} {case.case_id}  order {scored.trap_order}  "
                            f"trap_hit={scored.trap_hit}  exposure={scored.exposure_said}",
                            flush=True,
                        )

    if hand_read:
        mode = "bare" if args.bare else "no-menu"
        print(f"\n{mode} run complete -> {checkpoint}")
        print("Recommendations are free text. They are read by hand; there is no gate here.")
        return 0
    return report()


def report() -> int:
    if not CHECKPOINT.exists():
        print("no records", file=sys.stderr)
        return 2
    rows = [
        json.loads(line) for line in CHECKPOINT.read_text(encoding="utf-8").splitlines() if line
    ]
    if not rows:
        print("no records", file=sys.stderr)
        return 2

    admissible = sum(1 for r in rows if r["admissible"]) / len(rows)
    print(f"\n{'=' * 66}\ncasefile probe -- {len(rows)} cases")
    print(f"model: {sorted({r['model'] for r in rows})}")
    print(f"spend: ${sum(r['cost_usd'] for r in rows):.3f}")
    print("=" * 66)

    deep = [r for r in rows if isinstance(r["trap_order"], int) and r["trap_order"] >= 2]
    deep_trap_rate = sum(1 for r in deep if r["trap_hit"]) / len(deep) if deep else 0.0

    gate1 = admissible < ADMISSIBILITY_CEILING
    gate2 = deep_trap_rate > 0.0

    print(
        f"\nGATE 1 headroom       admissibility {admissible:.3f}   "
        f"need < {ADMISSIBILITY_CEILING}   {'PASS' if gate1 else 'FAIL'}"
    )
    print(
        f"GATE 2 trap bites     order>=2 trap rate {deep_trap_rate:.3f} (n={len(deep)})   "
        f"need > 0   {'PASS' if gate2 else 'FAIL'}"
    )

    print("\nby trap order:")
    by_order: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_order[row["trap_order"]].append(row)
    for order in sorted(by_order, key=str):
        group = by_order[order]
        adm = sum(1 for r in group if r["admissible"]) / len(group)
        trap = sum(1 for r in group if r["trap_hit"]) / len(group)
        print(f"  order {order!s:<5} admissible {adm:.2f}  trap_hit {trap:.2f}  (n={len(group)})")

    print("\ndiagnosis across all cases:")
    n = len(rows)
    print(f"  took a prohibited action    {sum(1 for r in rows if r['took_prohibited']) / n:.2f}")
    print(f"  missed a required action    {sum(1 for r in rows if r['missing_required']) / n:.2f}")
    print(f"  recommended the raincoat    {sum(1 for r in rows if r['unjustified_hit']) / n:.2f}")
    print(f"  named the pivot             {sum(1 for r in rows if r['pivot_ok']) / n:.2f}")
    print(f"  exposure band correct       {sum(1 for r in rows if r['exposure_ok']) / n:.2f}")
    print(
        f"  exposure stopped at order 1 {sum(1 for r in rows if r['exposure_first_order']) / n:.2f}"
    )
    print(f"  all five blocks present     {sum(1 for r in rows if r['blocks_complete']) / n:.2f}")
    print(
        f"  condition recall {sum(r['condition_recall'] for r in rows) / n:.2f}   "
        f"precision {sum(r['condition_precision'] for r in rows) / n:.2f}"
    )

    print("\n" + "=" * 66)
    if gate1 and gate2:
        print("both gates pass -- the venue can measure; build the schema")
        return 0
    print("at least one gate failed -- turn the dials before building anything")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
