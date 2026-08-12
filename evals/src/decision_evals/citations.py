"""Citation validation.

Three misattributed numbers were written into this repository in a single
morning on 2026-08-11, all of them citing **real papers that existed and said
something adjacent**:

- ``+18 to +36pp`` was "corrected" to ``+16.6pp`` on the assumption that a
  search result describing "SkillsBench" was the paper already cited. Two
  different papers, both real.
- ``90% -> 13.6%`` was attributed to arXiv:2605.24050. That paper is *quoting*
  other authors, about **tool** selection, at **11,100** candidates. Its own
  number is 21% at 202 skills. The figure was then used to justify a design
  decision made at four skills.
- MAST's category percentages were reported as ``41.8 / 36.9 / 21.3``. Those
  numbers are not in the paper.

**A presence check would have caught none of them.** Every identifier resolved
and every paper was real. What was wrong was the number sitting next to the
identifier, so the check has to bind the two together: an assertion of the form
"*this figure*, per *this paper*" is only admissible when the bibliography
carries the sentence it came from.

Hence :data:`QUOTE_FIELD`. A ``quote`` field is a promise that someone opened
the paper, and it is checkable by a reader in a way that a bare identifier is
not. Adding one is a few seconds' work; the three errors above each survived
review and reached a file this repository calls the product.

The rule is deliberately narrow. An identifier cited in passing needs a
bibliography entry and nothing more. It is only when a **number** appears
alongside it that a verbatim quote becomes mandatory, because that is the only
construction in which the citation is doing arithmetic work.

**The baseline is where the known-unchecked claims are, and it is not neutral.**
On 2026-08-12 the eight baselined identifiers that assert a number were fetched
and read. Two were wrong: one paper's scale was another paper's, and one figure
was in no version of the paper it was attributed to. Six of eight is a better
rate than the morning that motivated this module, and it is not a rate anyone
should be comfortable exempting from a check. See
``notebook/2026-08-12-the-baseline-was-where-the-errors-were.md``.

**A ``quote`` field is not read against the number beside it**, and cannot be.
The gate checks that someone opened the paper; whether the sentence they copied
supports the figure is a judgement no regex makes. Resolving a baseline entry
therefore means reading what the identifier was cited *for*, not only what it is
— on 2026-08-12 that distinction was the difference between fixing a retracted
percentage and giving it a green tick.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: Files whose citations are governed. ``paper/`` is excluded: it is generated
#: from the bibliography rather than citing into it.
GOVERNED: Final[tuple[str, ...]] = (
    "docs/**/*.md",
    "notebook/*.md",
    "skills/**/*.md",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "SCORECARD.md",
)

#: The bibliography every governed citation must resolve into.
BIB_PATH: Final = "paper/refs.bib"

#: Identifiers cited before this gate existed, exempt until re-read. May only
#: shrink; see :func:`load_baseline`.
BASELINE_PATH: Final = "paper/citations-baseline.txt"

#: The field a bib entry must carry before a number may be asserted beside it.
QUOTE_FIELD: Final = "quote"

_ARXIV: Final = re.compile(r"\b(\d{4}\.\d{4,5})\b")

#: A number doing claim work. Percentages, percentage points, and the bare
#: decimals that agreement statistics are reported in (``kappa = 0.88``).
#:
#: Deliberately not "any digit": a version number, a task count or a year is not
#: an empirical claim, and a rule that fires on those would be turned off.
_CLAIM_NUMBER: Final = re.compile(
    r"""
    [+-]?\d+(?:\.\d+)?\s*(?:pp\b|%)      # +16.6pp, 39%, -1.3pp
    | \b(?:kappa|κ)\s*[=:]\s*\d?\.\d+    # kappa = 0.88
    | \bAUC\s*[=:]?\s*\d?\.\d+           # AUC 0.679
    """,
    re.VERBOSE | re.IGNORECASE,
)

#: Stripped before scanning a line for claim numbers, so that the digits inside
#: an identifier or a URL cannot be mistaken for the claim they accompany.
_MASK: Final = re.compile(r"https?://\S+|arxiv[:/]\S+|\b\d{4}\.\d{4,5}\b", re.IGNORECASE)


@dataclass(frozen=True)
class CitationIssue:
    """One citation defect, located precisely enough to fix without searching."""

    path: str
    line: int
    arxiv_id: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.arxiv_id} — {self.message}"


@dataclass(frozen=True)
class BibEntry:
    """One bibliography entry, reduced to what the gate cares about."""

    arxiv_id: str
    has_quote: bool


def parse_bib(text: str) -> dict[str, BibEntry]:
    """Index a BibTeX file by arXiv identifier.

    Entries are split on ``@`` at the start of a line, which is where BibTeX
    entries begin and where the ``%`` comment banners in this file do not.
    """
    entries: dict[str, BibEntry] = {}
    for chunk in re.split(r"^@", text, flags=re.M)[1:]:
        body = _strip_comments(chunk)
        found = _ARXIV.search(body)
        if found is None:
            continue
        arxiv_id = found.group(1)
        has_quote = re.search(rf"^\s*{QUOTE_FIELD}\s*=", body, re.M | re.IGNORECASE) is not None
        # First entry wins. A duplicated identifier is reported separately
        # rather than silently resolving to whichever came last.
        entries.setdefault(arxiv_id, BibEntry(arxiv_id=arxiv_id, has_quote=has_quote))
    return entries


def _strip_comments(text: str) -> str:
    """Drop whole-line ``%`` comments.

    A ``% VERIFY`` banner above an entry must not be read as part of it, and an
    identifier mentioned in a comment must not register as a bibliography entry.
    """
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("%"))


def asserts_a_number(line: str) -> bool:
    """Whether this line puts a claim number next to a citation.

    The identifier and any URL are masked first: ``arXiv:2605.24050`` contains
    digits, and a rule that read them as a claim would fire on every citation.
    """
    return _CLAIM_NUMBER.search(_MASK.sub(" ", line)) is not None


def scan_text(path: str, text: str, bib: dict[str, BibEntry]) -> list[CitationIssue]:
    """Check one document's citations against the bibliography."""
    issues: list[CitationIssue] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for arxiv_id in dict.fromkeys(_ARXIV.findall(line)):
            entry = bib.get(arxiv_id)
            if entry is None:
                issues.append(
                    CitationIssue(
                        path,
                        number,
                        arxiv_id,
                        f"not in {BIB_PATH}. Every cited identifier needs an entry, so that a "
                        "reader can check what was cited without re-deriving it from prose.",
                    )
                )
                continue
            if asserts_a_number(line) and not entry.has_quote:
                issues.append(
                    CitationIssue(
                        path,
                        number,
                        arxiv_id,
                        f"a number is asserted beside this citation, but its {BIB_PATH} entry has "
                        f"no `{QUOTE_FIELD}` field. Add the verbatim sentence the figure comes "
                        "from. Three misattributions on 2026-08-11 all cited real papers; the "
                        "number beside the identifier was what was wrong.",
                    )
                )
    return issues


def governed_files(repo_root: Path) -> list[Path]:
    """Every file whose citations this gate governs, deduplicated and sorted."""
    found: set[Path] = set()
    for pattern in GOVERNED:
        found.update(path for path in repo_root.glob(pattern) if path.is_file())
    return sorted(found)


def load_baseline(repo_root: Path) -> set[str]:
    """Identifiers exempted from the gate, one per line, ``#`` for comments.

    A baseline rather than a warning, and the distinction is the whole design.
    The backlog on the day this gate was written was 36 issues across citations
    made before it existed. Gating those retroactively would have blocked every
    commit until 19 papers were re-read; reporting them as warnings would have
    made the gate advisory, and an advisory gate is one somebody stops reading.

    So the baseline is exempt, **and it may only shrink** — see
    :func:`check_citations`, which fails when a listed identifier no longer has
    an issue. Without that, a baseline is just a place errors go to be forgotten.
    """
    path = repo_root / BASELINE_PATH
    if not path.is_file():
        return set()
    return {
        stripped
        for line in path.read_text(encoding="utf-8").splitlines()
        if (stripped := line.split("#", 1)[0].strip())
    }


def check_citations(repo_root: Path) -> list[CitationIssue]:
    """Validate every governed document against the bibliography.

    Returns the issues that should fail the build: everything not covered by
    the baseline, plus a report of any baseline entry that has become stale.
    """
    bib_path = repo_root / BIB_PATH
    if not bib_path.is_file():
        return [CitationIssue(BIB_PATH, 0, "-", "bibliography is missing")]

    bib = parse_bib(bib_path.read_text(encoding="utf-8"))
    found: list[CitationIssue] = []
    for path in governed_files(repo_root):
        relative = str(path.relative_to(repo_root)).replace("\\", "/")
        found += scan_text(relative, path.read_text(encoding="utf-8"), bib)

    baseline = load_baseline(repo_root)
    issues = [issue for issue in found if issue.arxiv_id not in baseline]

    # A baseline entry that no longer corresponds to a real issue is a lie about
    # the size of the backlog, so removing it is mandatory rather than tidy.
    resolved = baseline - {issue.arxiv_id for issue in found}
    issues += [
        CitationIssue(
            BASELINE_PATH,
            0,
            arxiv_id,
            "is baselined but has no outstanding issue. Delete the line — a baseline that "
            "does not shrink when work is done stops measuring anything.",
        )
        for arxiv_id in sorted(resolved)
    ]
    return issues


def census(repo_root: Path) -> tuple[int, int, int]:
    """``(cited, in_bib, missing)``.

    Reported by the gate rather than asserted in prose. Two drafts of the
    programme carried hand-counted totals and both were wrong, because the
    number moves with which directories you happen to glob.
    """
    bib_path = repo_root / BIB_PATH
    bib = parse_bib(bib_path.read_text(encoding="utf-8")) if bib_path.is_file() else {}
    cited: set[str] = set()
    for path in governed_files(repo_root):
        cited.update(_ARXIV.findall(path.read_text(encoding="utf-8")))
    return len(cited), len(bib), len(cited - set(bib))
