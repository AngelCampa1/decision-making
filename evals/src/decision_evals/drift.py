"""Which documents describe code that has moved since anyone read them.

Every other integrity check here asks whether a reference resolves. This one
asks a question no gate can answer -- is the description still true -- and does
the only useful thing a machine can do about it: narrow the reading.

`docs/PROTOCOL.md` once described, in the present indicative, a refusal that had
never run. Every path in it resolved. `de check` was green. The standing rule
that prose naming a mechanism must name its arena and its tense came out of
reading that, and the every-third-run sweep in ``AGENTS.md`` is where the rule
gets applied -- a sweep whose own bullet said, until this module existed,
"Nothing checks this".

**The signal.** A document's dependencies are the repository paths it names.
:mod:`decision_evals.docs` already extracts them, to prove they resolve. Here
the same paths answer a different question: ``docs/ARCHITECTURE.md`` names
``cli.py``, ``providers/claude_code.py`` and ``solvers/arms.py``, so if none of
those has moved since it was last read, it probably still holds, and if
``cli.py`` has moved twenty times, it probably does not.

Markdown dependencies are deliberately excluded. A document linking to another
document is the ordinary shape of an index, and counting those would make every
document stale every time ``docs/README.md`` gained a row. What is being tracked
is prose about a mechanism, which is the thing that goes wrong silently.

**What this does not prove.** Nothing stops a review that did not happen.
Recording a sha is a claim by a person that they read the document at that
commit, and it is exactly as trustworthy as the person. The claim is narrower
than it looks: an obligation nobody could see is now one that is visible, dated,
and refused when it is old. That is all.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from decision_evals.docs import GENERATED as GENERATED_DOCS
from decision_evals.docs import (
    code_fragments,
    link_targets,
    load_register,
    repo_paths,
    scanned_files,
)

#: Documents no person reads to check, because a generator writes them.
#: Reviewing one means reviewing its generator, which is source: covered by the
#: coverage floors and the wiring gate, not by a reading record.
#:
#: ``CLAUDE.md`` is here and not in ``docs.GENERATED`` because that set is
#: scoped to ``docs/`` and exists for the audience-line rule. This one is a
#: byte-exact mirror of ``AGENTS.md`` written by ``de mirror``, so a second
#: review record for it would be two entries that must move together, which is
#: the shape of drift rather than a defence against it.
GENERATED: Final[frozenset[str]] = GENERATED_DOCS | frozenset({"CLAUDE.md"})

#: Where the review record lives, beside the four registers ``docs.py`` reads,
#: in the same shape: a flat table of declaration to value. The value is the
#: commit the document was read at. The date is not stored, because git already
#: holds it and a second copy is a second thing to keep true.
REVIEWED_TABLE: Final[tuple[str, ...]] = ("tool", "decision-evals", "reviewed")

#: How far a document's subject may move before it has to be read again.
#:
#: Ten because ``AGENTS.md`` already asks a worktree to rejoin at least every
#: ten commits, and a reader holding two different cadences in their head keeps
#: neither.
#:
#: Measured on 2026-08-21, once directories stopped counting: the furthest
#: behind of the 36 was four. That is not a distribution worth tightening on,
#: because the register was a day old and every document was as freshly read as
#: it will ever be. Revisit when the spread is real.
CEILING: Final = 10

#: Extensions that are not evidence a description has gone stale. A document
#: linking to another document is an index doing its job.
_NOT_A_MECHANISM: Final[frozenset[str]] = frozenset({".md"})

#: Directories that exist on a developer machine and never in the repository.
#: Without this the answer differs between a laptop and CI, where they are
#: absent and the path drops out on its own.
_NOT_THE_REPOSITORY: Final[tuple[str, ...]] = (".venv/", "node_modules/", "site/dist/")


@dataclass(frozen=True)
class DriftIssue:
    """One document that has not been read recently enough to trust."""

    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


@dataclass(frozen=True)
class Movement:
    """How far one document's subject has moved since it was read.

    ``commits`` is ``None`` when git could not answer -- an unknown sha, most
    often, because the recorded commit was rebased away.
    """

    document: str
    sha: str
    commits: int | None
    paths: tuple[str, ...]


def _relative(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def dependencies(repo_root: Path, path: Path) -> tuple[str, ...]:
    """Every repository path a document names that is not another document.

    Both the backticked references ``docs.py`` proves exist and the markdown
    links it resolves, because a document points at code both ways and either
    one moving is a reason to read it again.

    A directory is a place, not a mechanism, so naming one is not a dependency
    on it. Measured on 2026-08-21 against the first register: counting
    directories put ``docs/README.md`` thirteen commits behind and
    ``docs/PROTOCOL.md`` eleven, on nothing but other people's work inside
    ``notebook/`` and ``results/``. Every one of those thirteen was noise. The
    files a document names are the signal, and they survive here.
    """
    text = path.read_text(encoding="utf-8")
    top_level = {child.name for child in repo_root.iterdir() if child.is_dir()}

    found: set[str] = set(repo_paths(code_fragments(text), top_level))
    for target in link_targets(text):
        resolved = (path.parent / target).resolve()
        try:
            found.add(resolved.relative_to(repo_root.resolve()).as_posix())
        except ValueError:
            continue

    here = _relative(path, repo_root)
    return tuple(
        sorted(
            reference
            for reference in found
            if reference != here
            and Path(reference).suffix not in _NOT_A_MECHANISM
            and not reference.startswith(_NOT_THE_REPOSITORY)
            and (repo_root / reference).is_file()
        )
    )


def living_documents(repo_root: Path) -> set[str]:
    """Every document a person is expected to have read."""
    return {
        _relative(path, repo_root)
        for path in scanned_files(repo_root)
        if _relative(path, repo_root) not in GENERATED
    }


def load_reviewed(repo_root: Path) -> dict[str, str]:
    """Document to the commit somebody recorded reading it at."""
    return load_register(repo_root, REVIEWED_TABLE)


def check_drift(
    repo_root: Path,
    movements: Mapping[str, Movement],
    *,
    ceiling: int = CEILING,
) -> list[DriftIssue]:
    """Both directions, and the ceiling.

    A living document with no entry is refused, so the register cannot be
    dodged by omission. An entry naming no document is refused, so it may only
    shrink. And a document whose subject has moved past the ceiling is refused,
    which is the whole point.
    """
    reviewed = load_reviewed(repo_root)
    living = living_documents(repo_root)

    issues = [
        DriftIssue(
            document,
            "is a living document with no review on record. Read it, then add it to "
            "`[tool.decision-evals.reviewed]` with the commit you read it at. A "
            "document nobody has claimed to read is not one this gate can say anything "
            "about.",
        )
        for document in sorted(living - set(reviewed))
    ]
    issues += [
        DriftIssue(
            "pyproject.toml",
            f"records a review of `{document}`, which is not a living document here. "
            "Delete the entry. Like every other register in this repository, this one "
            "may only shrink.",
        )
        for document in sorted(set(reviewed) - living)
    ]

    for document in sorted(living & set(reviewed)):
        movement = movements.get(document)
        if movement is None:
            continue
        if movement.commits is None:
            issues.append(
                DriftIssue(
                    "pyproject.toml",
                    f"records `{document}` as read at `{movement.sha}`, which git does "
                    "not know. A review recorded against a commit that no longer exists "
                    "pins nothing. Read the document and record the commit you read it "
                    "at.",
                )
            )
        elif movement.commits > ceiling:
            issues.append(
                DriftIssue(
                    document,
                    f"names {len(movement.paths)} path(s) that have moved in "
                    f"{movement.commits} commit(s) since it was last read at "
                    f"`{movement.sha}`, over a ceiling of {ceiling}. Read it against "
                    f"`git log {movement.sha}..HEAD -- {' '.join(movement.paths[:4])}`, "
                    "then record the commit you read it at.",
                )
            )
    return issues


def worklist(movements: Mapping[str, Movement]) -> list[Movement]:
    """Every document with something to re-read, the furthest behind first."""
    return sorted(
        (movement for movement in movements.values() if movement.commits != 0),
        key=lambda movement: (-(movement.commits or 0), movement.document),
    )


def census(repo_root: Path) -> tuple[int, int]:
    """Living documents, and how many carry a review."""
    living = living_documents(repo_root)
    reviewed = load_reviewed(repo_root)
    return len(living), len(living & set(reviewed))
