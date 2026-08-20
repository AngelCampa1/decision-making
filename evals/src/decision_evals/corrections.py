"""The label-correction changelog, and the gate that keeps it complete.

A versioned answer key says *that* the labels changed. It does not say *which*
label changed, or to what, or why. On 2026-08-13 one turn moved from the
positives to the negatives; recall rose 3 to 5 points on every arm already on
disk and not one call was re-made. ``set_version`` was added that afternoon and
it does the job it was built for -- ``label_versions_comparable`` refuses a
comparison that straddles the boundary. What it cannot do is tell a reader of
the numbers *what moved*, and the reasoning lives in ``docs/DECISIONS.md`` as
prose that cannot be joined against a record.

**This file is the join.** One line per label that moved, machine-readable,
carrying the item, both labels, the version it moved into, the date, who moved
it, and the register entry that argued for it.

**It is not a common artefact, and that is the reason to have one.** A survey of
eval practice on 2026-08-19 found no benchmark publishing a per-item,
machine-readable label-correction changelog: MMLU-Redux ships a new dataset
repository, HLE ran a time-boxed bug bounty, and OpenAI published a retraction
essay about SWE-bench Verified long after 93 developers and three independent
annotators per sample had signed it off. What generalises from that is not
*annotate harder*. It is that answer keys rot and the re-audit needs a record
with a shape. Two of the three hard parts already exist here: a versioned key,
and ``rescore.py``, which re-scores without re-calling and marks the result so a
re-score cannot be mistaken for a run.

**What the gate checks, stated in the tense it runs in.** It refuses a version
bump that no line accounts for. Every transition into a version the corpus has
reached must be declared -- as one or more moved labels, as an explicit
statement that the bump moved none, or as a statement that the corpus was
rebuilt and item identity does not carry across. It also refuses a line whose
``decision`` names no heading in ``docs/DECISIONS.md``, because a reason nobody
wrote down is the condition this file exists to end.

**What it does not check, and cannot.** It does not diff the corpus against its
own history to find moves the author failed to declare. That would need the
previous version's file resolved out of git for every bump, and the version 2 to
version 3 transition replaced the corpus wholesale, so there is no item-level
diff to take across it. A *missing* line inside a declared bump is therefore
invisible here. What is caught is the whole undeclared bump, which is the
failure that has actually happened: the key moved and the record of what moved
was a commit body.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

CORRECTIONS_PATH: Final = "datasets/triggers/corrections.jsonl"
REGISTER_PATH: Final = "docs/DECISIONS.md"

#: How a transition is accounted for.
#:
#: ``moved`` -- one item's ``should_fire`` changed, and both labels are named.
#: ``none`` -- the bump moved no label; an identity or metadata change.
#: ``rebuilt`` -- the corpus was replaced and item ids do not carry across, so a
#: per-item correction is not defined for this transition.
KINDS: Final[frozenset[str]] = frozenset({"moved", "none", "rebuilt"})

_HEADING: Final = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_DATE: Final = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class CorrectionIssue:
    """One defect in the changelog."""

    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


@dataclass(frozen=True)
class Correction:
    """One accounted-for change to the answer key."""

    kind: str
    to_version: int
    date: str
    reason: str
    decision: str
    item: str | None = None
    old_label: bool | None = None
    new_label: bool | None = None
    adjudicator: str | None = None


def _issue(line_no: int, message: str) -> CorrectionIssue:
    return CorrectionIssue(f"{CORRECTIONS_PATH}:{line_no}", message)


def _validate(row: dict[str, Any]) -> str | None:
    """The reason this row is not a correction, or ``None``."""
    for field in ("kind", "to_version", "date", "reason", "decision"):
        if field not in row:
            return f"has no `{field}`. Every line needs one."
    kind = row["kind"]
    if kind not in KINDS:
        return f"has kind {kind!r}, which is not one of {', '.join(sorted(KINDS))}."
    if not isinstance(row["to_version"], int) or isinstance(row["to_version"], bool):
        return "has a `to_version` that is not an integer."
    if row["to_version"] < 2:
        return (
            f"declares a move into version {row['to_version']}. Version 1 is the first key "
            "and nothing moved into it."
        )
    if not _DATE.match(str(row["date"])):
        return f"has date {row['date']!r}, which is not `YYYY-MM-DD`."
    if not str(row["reason"]).strip():
        return "has an empty `reason`. The reason is the point of the line."
    if kind != "moved":
        return None
    for field in ("item", "old_label", "new_label"):
        if row.get(field) is None:
            return f"is a `moved` line with no `{field}`. A move names what moved and to what."
    if not isinstance(row["old_label"], bool) or not isinstance(row["new_label"], bool):
        return "has a label that is not a boolean. `should_fire` is a boolean."
    if row["old_label"] == row["new_label"]:
        return (
            f"records {row['item']!r} moving from {row['old_label']} to {row['new_label']}, "
            "which is not a move. A line here is a label that changed."
        )
    return None


def parse_corrections(text: str) -> tuple[list[Correction], list[CorrectionIssue]]:
    """Read the changelog, returning what parsed and what did not.

    Both come back rather than raising on the first bad line, so one malformed
    entry reports itself instead of hiding every entry after it.
    """
    corrections: list[Correction] = []
    issues: list[CorrectionIssue] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            row: Any = json.loads(line)
        except json.JSONDecodeError as error:
            issues.append(_issue(line_no, f"is not readable as JSON -- {error}"))
            continue
        if not isinstance(row, dict):
            issues.append(_issue(line_no, "is not a JSON object"))
            continue
        problem = _validate(row)
        if problem is not None:
            issues.append(_issue(line_no, problem))
            continue
        corrections.append(
            Correction(
                kind=str(row["kind"]),
                to_version=int(row["to_version"]),
                date=str(row["date"]),
                reason=str(row["reason"]),
                decision=str(row["decision"]),
                item=None if row.get("item") is None else str(row["item"]),
                old_label=row.get("old_label"),
                new_label=row.get("new_label"),
                adjudicator=None if row.get("adjudicator") is None else str(row["adjudicator"]),
            )
        )
    return corrections, issues


def register_headings(text: str) -> set[str]:
    """Every ``## `` heading in the decision register."""
    return {match.group(1).strip() for match in _HEADING.finditer(text)}


def check_corrections(repo_root: Path, corpus_version: int | None) -> list[CorrectionIssue]:
    """Every version the corpus has reached is accounted for, and every line resolves.

    Args:
        repo_root: Repository root.
        corpus_version: ``version:`` from the live trigger set. Transitions into
            2 through this number must each be declared. **``None`` means the
            version could not be read, and the transition checks are then
            skipped rather than run against a default.** A corpus file that will
            not load is `check_triggers_step`'s finding; substituting 1 here
            would invent a parameter -- standing rule 1 -- and would report
            every line on disk as ahead of a corpus nobody could read, sending a
            reader to the wrong step with three errors that are not the problem.

    Returns:
        Every defect found: the malformed lines first, then the unresolved
        decisions, then the undeclared transitions.
    """
    path = repo_root / CORRECTIONS_PATH
    if not path.is_file():
        return [CorrectionIssue(CORRECTIONS_PATH, "the label-correction changelog is missing")]

    corrections, issues = parse_corrections(path.read_text(encoding="utf-8"))

    register = repo_root / REGISTER_PATH
    headings = set()
    if register.is_file():
        headings = register_headings(register.read_text(encoding="utf-8"))
    for correction in corrections:
        if correction.decision in headings:
            continue
        issues.append(
            CorrectionIssue(
                CORRECTIONS_PATH,
                f"the line for version {correction.to_version} names decision "
                f"{correction.decision!r}, which is not a heading in {REGISTER_PATH}. A "
                "correction whose reasoning cannot be reached is the state this file exists "
                "to end.",
            )
        )

    if corpus_version is None:
        return issues

    declared = {correction.to_version for correction in corrections}
    for version in range(2, corpus_version + 1):
        if version in declared:
            continue
        issues.append(
            CorrectionIssue(
                CORRECTIONS_PATH,
                f"the answer key reached version {version} and no line accounts for the move "
                "into it. Declare the label or labels that moved, or a `none` line saying the "
                "bump moved none, or a `rebuilt` line saying item identity does not carry "
                "across. A version that moves with no record of what moved is the defect the "
                "version number was added to catch, one level up.",
            )
        )

    for correction in corrections:
        if correction.to_version <= corpus_version:
            continue
        issues.append(
            CorrectionIssue(
                CORRECTIONS_PATH,
                f"a line declares a move into version {correction.to_version} and the corpus "
                f"is at {corpus_version}. Check the corpus, or check the line.",
            )
        )
    return issues


def census(repo_root: Path) -> tuple[int, int, int]:
    """``(lines, moved labels, versions accounted for)``, for the gate's header."""
    path = repo_root / CORRECTIONS_PATH
    if not path.is_file():
        return (0, 0, 0)
    corrections, _ = parse_corrections(path.read_text(encoding="utf-8"))
    moved = sum(1 for correction in corrections if correction.kind == "moved")
    return (len(corrections), moved, len({correction.to_version for correction in corrections}))
