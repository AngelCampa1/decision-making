"""The blind-adjudication ledger, and the gate that keeps the answer key covered.

Twenty-one of twenty-one scored failures across three corpora turned out to be
the answer key rather than the model. The rule this repository drew from that is
in ``docs/METHODS.md`` section 2: the labels are relabelled by three independent
model instances per item, each blind to the label, the case id, the band, the
triple, the other judges and the skill description, and more than 20% of labels
moving retires the corpus. ``scripts/adjudicate.py`` runs it.

**The rule held by discipline until this module existed.** On 2026-08-20 answer
key v5 added 24 triples, 72 items, so that ``council`` and ``hinge`` had
positives to be correct about. The register said plainly that no number may be
published against version 5 until those labels had been through adjudication.
Nothing checked it. The full gate passed green on a tree whose live answer key
was 78% adjudicated, and it would have passed green on a run scored against it.

**What the gate checks, stated in the tense it runs in.** Two refusals, joined
on the case id, because either one alone has a hole the other closes.

The first reads the answer keys on disk and refuses a trigger set carrying an
item with no adjudication record. It re-reads them on every ``de check``, so it
cannot quietly stop noticing.

The second reads the published runs and refuses one whose records name a case
with no adjudication record. Run records carry ``case`` and ``set_version``
already, so this needs no git archaeology and no past version resolved out of
history. It exists because the first refusal is computed against whatever the
corpus holds *now*: retiring an item deletes the evidence that a published
number stood on an unadjudicated label. Three ids in the ledger today,
``l15p`` and its two negatives, name a triple that was retired at v4, which is
that erasure having already happened in the harmless direction.

A case counts as covered when three readable judge verdicts name it. That is
the panel size the kill threshold was pre-registered against, and the shape
every one of the 258 covered items in the live key already has. The ledger
holds three more, left behind when ``l15`` was retired. ``scripts/adjudicate.py``
imports :data:`ADJUDICATORS` from here so the run and the gate cannot drift.

The cost is deliberate. Authoring items turns the gate red until they are
adjudicated. That is the state the 72 items sat in for a day while every step
reported green.

**What it does not check, and cannot.**

It does not know whether the record it found adjudicated *this* text. The ledger
stores no corpus version and no date, and it has been rewritten in place at
least once, so an item whose wording changed under a stable id reads as covered.
That is the drift the ``ancestry:`` block in the trigger index was added to
catch, and it is a different gate's job.

For the same reason it cannot tell two corpora apart. Coverage is a flat set of
case ids, so a new answer key that reuses ``s01p`` for a different turn reads as
covered on the strength of a record about the old one. Version 3 rebuilt the
corpus with fresh ids and that is what makes the join safe today; a future
corpus that recycles them would need the ledger to carry the set it judged.

It does not check the route. The adjudicator answers one binary question,
whether the person is asking for help deciding something, and never sees which
of the six procedures the key says should run. A fully covered corpus has
adjudicated ``should_fire`` and nothing else.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from decision_evals.corpus import load_baseline_file

#: Written by ``scripts/adjudicate.py``, one row per ``(case, judge)``.
#: ``results/triggers/`` is gitignored and this file is force-tracked, so
#: whoever clones this gets the evidence the rule rests on.
CHECKPOINT_PATH: Final = "results/triggers/adjudication.jsonl"

#: Trigger sets exempt from coverage, one answer-key path per line. A run that
#: declares an exempt key is exempt with it, so the two refusals cannot
#: disagree about the same corpus.
BASELINE_PATH: Final = "datasets/triggers/adjudication-baseline.txt"

#: Independent instances per turn. Odd, so a binary question always resolves.
#: Pre-registered before the first adjudication run and unchanged since; the
#: kill threshold is stated against a panel of this size, and
#: ``scripts/adjudicate.py`` reads it from here rather than declaring its own.
ADJUDICATORS: Final = 3

#: How many missing ids an issue names before it stops listing them. A gate
#: message that prints 72 case ids buries the count that matters.
_SAMPLE: Final = 6


@dataclass(frozen=True)
class AdjudicationIssue:
    """One gap between an answer key and the ledger that is supposed to cover it."""

    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


def _judge_index(value: Any) -> int | None:
    """One row's judge slot, read the way ``adjudicate.load_done`` reads it.

    ``load_done`` coerces with ``int()``, so a slot written as ``"1"`` or ``1.0``
    is a resumable record there. Type-checking it here instead would make the
    two readers of one file disagree about what is on a line, and a case the
    runner believes is finished would be a case this gate believes is missing.

    ``True`` is an ``int`` in Python and is not a judge slot in any record.
    """
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def panels(repo_root: Path) -> dict[str, set[int]]:
    """Judge slots holding a readable verdict, per case id.

    A slot whose ``adjudicated`` is ``None`` is a reply the parser could not
    read, and it stays empty. Treating an unreadable reply as a verdict is the
    defect shape the adjudication run exists to find, so it must not be the
    defect shape this gate has. ``False`` is a verdict and fills its slot: 556
    of the 858 rows on disk are one, and dropping them would take coverage from
    261 cases to 85.

    **A repeated slot is resolved last-wins**, which is how
    ``adjudicate.load_done`` reads the same file. Twenty-five cases carry six
    rows each after the 2026-08-18 re-run. Taking the union instead would let a
    case whose retry failed to parse keep the slot its first attempt filled, so
    the runner would call the case unfinished while this gate called it covered.

    Unparseable lines are skipped. A malformed checkpoint row is a defect this
    gate is not the right place to report, and refusing to read the file would
    hide the coverage gap it *is* the right place to report.
    """
    path = repo_root / CHECKPOINT_PATH
    if not path.is_file():
        return {}
    slots: dict[str, dict[int, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        case, judge = row.get("case"), _judge_index(row.get("judge"))
        if isinstance(case, str) and judge is not None:
            slots.setdefault(case, {})[judge] = row.get("adjudicated")
    return {
        case: {judge for judge, verdict in found.items() if verdict is not None}
        for case, found in slots.items()
    }


def record_cases(path: Path) -> set[str]:
    """The case ids one published run's JSONL file names.

    Unreadable files and unparseable lines are skipped. A run whose records
    cannot be read is `check_provenance`'s finding, and refusing to read them
    here would hide the coverage gap this module is the right place to report.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    found: set[str] = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and isinstance(case := row.get("case"), str):
            found.add(case)
    return found


def adjudicated_cases(repo_root: Path) -> set[str]:
    """Case ids carrying a full panel of readable judge verdicts."""
    return {case for case, judges in panels(repo_root).items() if len(judges) >= ADJUDICATORS}


def load_baseline(repo_root: Path) -> set[str]:
    """Answer-key paths exempted from coverage.

    Exempt, **and it may only shrink**; see :func:`check_adjudication`. The
    exemption is a fact about a corpus, so it is stated once here rather than
    once per run scored against it.
    """
    return load_baseline_file(repo_root, BASELINE_PATH)


def _remedy(repo_root: Path, key: str, missing: list[str]) -> str:
    """The command that would actually close this gap.

    ``--missing-only`` selects cases with *no* record at all. A case holding one
    unreadable row is excluded by it and skipped by a plain resume too, because
    ``collect`` treats any stored row as done. Naming the wrong flag here would
    send a reader round a loop that cannot terminate.
    """
    started = set(panels(repo_root))
    if any(case in started for case in missing):
        return (
            f"Some of these carry a partial panel, so `--missing-only` will skip them: run "
            f"`scripts/adjudicate.py --set {key} --only <the ids>` to fill the empty slots"
        )
    return f"Run `scripts/adjudicate.py --set {key} --missing-only`"


def _uncovered(
    repo_root: Path, where: str, key: str, items: frozenset[str], covered: set[str], subject: str
) -> AdjudicationIssue:
    missing = sorted(items - covered)
    shown = ", ".join(missing[:_SAMPLE])
    more = "" if len(missing) <= _SAMPLE else f", and {len(missing) - _SAMPLE} more"
    return AdjudicationIssue(
        where,
        f"{subject} {len(missing)} of {len(items)} item(s) with no {ADJUDICATORS}-judge "
        f"adjudication record: {shown}{more}. The labels on those items are the author's, and "
        f"21 of 21 scored failures across three corpora were the answer key. "
        f"{_remedy(repo_root, key, missing)}, or baseline the answer key in {BASELINE_PATH} "
        "with the reason it stays uncovered.",
    )


def check_adjudication(
    repo_root: Path,
    corpora: dict[str, tuple[int, frozenset[str]]],
    runs: dict[str, tuple[str, frozenset[str]]] | None = None,
) -> list[AdjudicationIssue]:
    """Every live answer key is covered, every published run is, and the baseline still earns its lines.

    Args:
        repo_root: Repository root.
        corpora: Answer-key path to ``(version, item ids)``, for every trigger
            set that loaded. A set that will not load contributes no entry:
            that is `check_trigger_sets`'s finding, and reporting it here would
            send a reader to the wrong step.
        runs: Published run path to ``(declared answer-key path, case ids in its
            records)``. A run whose README declares no answer key contributes no
            entry, because `check_provenance` refuses that one and two steps
            reporting it name one defect twice.

    Returns:
        The uncovered answer keys, then the uncovered runs, then the baseline
        lines that have stopped naming a defect.
    """
    covered = adjudicated_cases(repo_root)
    baseline = load_baseline(repo_root)

    issues: list[AdjudicationIssue] = []
    exempt_and_clean: set[str] = set()
    for key in sorted(corpora):
        version, items = corpora[key]
        if key in baseline:
            if not items - covered:
                exempt_and_clean.add(key)
            continue
        if items - covered:
            issues.append(_uncovered(repo_root, key, key, items, covered, f"version {version} has"))

    for run in sorted(runs or {}):
        key, cases = (runs or {})[run]
        if key in baseline or not cases - covered:
            continue
        issues.append(
            _uncovered(
                repo_root,
                run,
                key,
                cases,
                covered,
                f"its records were scored against `{key}` and name",
            )
        )

    for key in sorted(exempt_and_clean):
        issues.append(
            AdjudicationIssue(
                BASELINE_PATH,
                f"`{key}` is baselined and every item in it is now adjudicated. Remove the "
                "line. A baseline that does not shrink when the work is done has stopped "
                "measuring anything.",
            )
        )
    for key in sorted(baseline - set(corpora)):
        issues.append(
            AdjudicationIssue(
                BASELINE_PATH,
                f"`{key}` is baselined and names no trigger set that loaded. Remove the line, "
                "or check the path.",
            )
        )
    return issues


def census(repo_root: Path, corpora: dict[str, tuple[int, frozenset[str]]]) -> tuple[int, int, int]:
    """``(items under the gate, items covered, keys baselined)``, for the gate's header.

    Baselined keys are outside the denominator. Counting their items would give
    the header a total it can never reach, which is a number that stops meaning
    anything the moment the work is done.
    """
    baseline = load_baseline(repo_root)
    covered = adjudicated_cases(repo_root)
    items = {item for key, (_v, ids) in corpora.items() if key not in baseline for item in ids}
    return (len(items), len(items & covered), len(baseline))
