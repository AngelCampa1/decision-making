"""The decision register, coupled to the paths where a silent decision costs something.

Maintainer rationale in this repository is genuinely recorded — in commit
bodies, and they are good ones. ``d43c490`` carries the full reasoning for
moving ``x-n21`` to the negatives. But ``git log`` is not greppable by topic and
is invisible to anyone reading ``docs/``, so the reasoning behind the numbers
lives somewhere the numbers do not point.

**Commit trailers were considered and rejected as the store.** Commit messages
here cannot be amended: :func:`~decision_evals.cli.check_git_identity` exists
because the history *is* the pre-registration evidence and rewriting it destroys
the timestamps the method relies on. A trailer somebody forgot would therefore
be permanently unfixable — the one medium in this repository that can never be
corrected. A file can be amended, which is why ``docs/REJECTED.md`` is a file.

**The coupling is the whole design.** A register nobody is obliged to write is a
register that stops being written, and there is no mechanical predicate for
"this commit made a decision" — gating all 131 commits would be noise, and noise
is what an advisory gate becomes before somebody turns it off. So the obligation
attaches to the two paths where an undocumented decision has already cost
something:

- ``datasets/triggers/`` — the answer key. On 2026-08-13 one turn moved from the
  positives to the negatives; recall rose 3 to 5 points on every arm on disk and
  **not one call was re-made**. That was a correct maintainer decision and it is
  indistinguishable, in a JSONL file, from a model result.
- ``skills/`` — the product. What ships is what the claims are about.

Roughly one commit in ten touches either, which is a volume a person can
actually sustain.

The trigger is *any* change to those paths rather than a ``version:`` bump,
because the defect that motivated this did not bump a version. A rule keyed to
version bumps would have let it through.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: Changes here oblige an entry. Prefixes, matched against repo-relative paths.
GOVERNED: Final[tuple[str, ...]] = ("datasets/triggers/", "skills/")

REGISTER_PATH: Final = "docs/DECISIONS.md"

#: Commits governed before the register existed, one sha per line, ``#`` comments.
BASELINE_PATH: Final = "docs/decisions-baseline.txt"

#: ``## 2026-08-13 — four label decisions``
_HEADING: Final = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s+—\s+(.+?)\s*$", re.MULTILINE)

#: ``**Commits:** `d43c490`, `903169c` ``
_COMMITS: Final = re.compile(r"^\*\*Commits:\*\*\s*(.+?)\s*$", re.MULTILINE)

_SHA: Final = re.compile(r"\b([0-9a-f]{7})\b")


@dataclass(frozen=True)
class DecisionIssue:
    """One register defect."""

    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


@dataclass(frozen=True)
class GovernedCommit:
    """A commit that touched a governed path, gathered by the caller."""

    sha: str
    date: str
    subject: str


@dataclass(frozen=True)
class Entry:
    """One register entry."""

    date: str
    title: str
    commits: tuple[str, ...]
    body: str


def touches_governed(paths: list[str]) -> bool:
    """Whether a changeset obliges a register entry."""
    return any(path.startswith(prefix) for path in paths for prefix in GOVERNED)


def parse_register(text: str) -> list[Entry]:
    """Split the register into entries.

    Tolerant of prose above the first heading, so the file can explain itself
    without the explanation parsing as an entry.
    """
    entries: list[Entry] = []
    matches = list(_HEADING.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        found = _COMMITS.search(body)
        commits = tuple(_SHA.findall(found.group(1))) if found else ()
        entries.append(
            Entry(
                date=match.group(1),
                title=match.group(2),
                commits=commits,
                body=_COMMITS.sub("", body).strip(),
            )
        )
    return entries


def load_baseline(repo_root: Path) -> set[str]:
    """Commits exempt from the rule. May only shrink; see :func:`check_decisions`."""
    path = repo_root / BASELINE_PATH
    if not path.is_file():
        return set()
    return {
        stripped
        for line in path.read_text(encoding="utf-8").splitlines()
        if (stripped := line.split("#", 1)[0].strip())
    }


def check_decisions(repo_root: Path, governed: list[GovernedCommit]) -> list[DecisionIssue]:
    """Every governed commit is explained, and every explanation names a real commit."""
    path = repo_root / REGISTER_PATH
    if not path.is_file():
        return [DecisionIssue(REGISTER_PATH, "the decision register is missing")]

    entries = parse_register(path.read_text(encoding="utf-8"))
    baseline = load_baseline(repo_root)
    known = {commit.sha for commit in governed}

    explained: set[str] = set()
    issues: list[DecisionIssue] = []
    for entry in entries:
        if not entry.commits:
            issues.append(
                DecisionIssue(
                    REGISTER_PATH,
                    f"entry {entry.date} '{entry.title}' has no `**Commits:**` line. An entry "
                    "that names no commit cannot be checked against anything.",
                )
            )
        if not entry.body:
            issues.append(
                DecisionIssue(
                    REGISTER_PATH,
                    f"entry {entry.date} '{entry.title}' has no body. The reasoning is the "
                    "point; a title is what the commit subject already gave you.",
                )
            )
        for sha in entry.commits:
            if sha not in known:
                issues.append(
                    DecisionIssue(
                        REGISTER_PATH,
                        f"entry {entry.date} names `{sha}`, which is not a commit that "
                        "touched a governed path. Check the sha.",
                    )
                )
            explained.add(sha)

    for commit in governed:
        if commit.sha in explained or commit.sha in baseline:
            continue
        issues.append(
            DecisionIssue(
                commit.sha,
                f"({commit.date}) '{commit.subject}' changed {' or '.join(GOVERNED)} with no "
                f"entry in {REGISTER_PATH}. A label move is invisible in a checkpoint and "
                "shifts every number computed from it, so the reasoning has to live somewhere "
                "a reader of the numbers can find.",
            )
        )

    for sha in sorted(baseline - known):
        issues.append(
            DecisionIssue(
                BASELINE_PATH,
                f"`{sha}` is baselined but touched no governed path. Delete the line.",
            )
        )
    for sha in sorted(baseline & explained):
        issues.append(
            DecisionIssue(
                BASELINE_PATH,
                f"`{sha}` is baselined and also explained. Delete the line — a baseline that "
                "does not shrink when work is done has stopped measuring anything.",
            )
        )
    return issues


def census(repo_root: Path, governed: list[GovernedCommit]) -> tuple[int, int, int]:
    """``(governed_commits, entries, baselined)``."""
    path = repo_root / REGISTER_PATH
    entries = parse_register(path.read_text(encoding="utf-8")) if path.is_file() else []
    return len(governed), len(entries), len(load_baseline(repo_root))
