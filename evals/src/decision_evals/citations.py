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

**Until 2026-08-13 the scan was line-scoped, and this repository hard-wraps at
~80 columns.** A claim and the identifier it rests on therefore land on
different lines routinely, and the check never fired on any of them. The worst
case was in the file this repository calls the product: ``CLAUDE.md`` put "59%
more hidden issues" on one line and ``arXiv:2603.14373`` on the next, so the
gate that enforces standing rule 5 had never checked the product file's own
load-bearing citation. ``docs/AUTONOMOUS_WORK_ORDER.md`` — the document that
*states* standing rule 5 — carried the same claim across the same wrap.

The window is now the **markdown block the author wrote**: see :func:`blocks`.
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
#: ``pp`` must not be followed by a full stop. ``pp. 14-19`` is a page range in
#: ordinary citation prose, not percentage points, and since the scan became
#: block-scoped a wrapped "chapter 3 / pp. 14-19" reads as a claim across the
#: line join. Percentage points are never written ``pp.``.
_CLAIM_NUMBER: Final = re.compile(
    r"""
    [+-]?\d+(?:\.\d+)?\s*(?:pp\b(?!\.)|%)  # +16.6pp, 39%, -1.3pp
    | \b(?:kappa|κ)\s*[=:]\s*\d?\.\d+      # kappa = 0.88
    | \bAUC\s*[=:]?\s*\d?\.\d+             # AUC 0.679
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


#: Structural boundaries that end a block. A block is the unit an author wrote;
#: these are the places markdown says one unit stops and the next begins.
#:
#: A fence records *which* marker opened it. Treating ``` and ``~~~`` as
#: interchangeable desynchronises the parser on the first document that
#: mentions one style inside the other, and because a blank line stops
#: separating anything while a fence is open, the desync runs to end of file
#: and pools every remaining citation into one block. CommonMark requires the
#: closer to use the same character, at least as many times, and nothing else
#: on the line.
_FENCE_OPEN: Final = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})")
_HEADING: Final = re.compile(r"^\s{0,3}#{1,6}\s")

#: ``---``/``***``/``___`` as a thematic break, and ``===`` as a setext
#: heading underline. Without the second, ``===`` and ``---`` split the same
#: document differently, which makes the gate's verdict depend on which
#: underline style an author happened to use.
_RULE: Final = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,}|={3,})\s*$")
_TABLE_ROW: Final = re.compile(r"^\s*\|")

#: A GFM delimiter row, with or without leading pipes: ``|---|---|`` and
#: ``--- | --- | ---`` are both legal and only the first used to be recognised.
_TABLE_DELIMITER: Final = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*$")

#: Footnote and link-reference definitions. Each is its own authored unit, and
#: consecutive ones carry unrelated claims.
_DEFINITION: Final = re.compile(r"^\s{0,3}\[[^\]]{1,200}\]:\s")

#: Blockquote markers, stripped before every structural test. Nothing inside a
#: blockquote used to split at all — not a table row, not a heading, not a list
#: item — because every pattern above is anchored at the line start and a ``>``
#: sits in front of it. That left a live 21-line block in this repository
#: holding a quoted comparison table whose rows carry two different papers and
#: two different figures.
_BLOCKQUOTE: Final = re.compile(r"^(?:\s{0,3}>\s?)+")

_BULLET: Final = re.compile(r"^\s*[-*+]\s+")

#: An ordered-list marker, captured so the ordinal can be read. Bounded on
#: purpose: at 80 columns a reflow drops figures at line starts, and
#: ``202. That is the figure ...`` is a wrapped sentence, not a list. CommonMark
#: only lets an ordered list interrupt a paragraph when it starts at 1, which is
#: exactly the distinction needed and is not a threshold anybody invented.
_ORDERED: Final = re.compile(r"^\s*(?P<ordinal>\d{1,9})[.)]\s+")


@dataclass(frozen=True)
class Block:
    """One authored unit of prose, and the line each of its lines came from."""

    first_line: int
    lines: tuple[tuple[int, str], ...]

    @property
    def text(self) -> str:
        return "\n".join(line for _, line in self.lines)


def blocks(text: str) -> list[Block]:
    """Split a markdown document into the units its author actually wrote.

    **Why a block and not a line.** The scan used to require the claim number
    and the identifier on the same physical line. That is not a rule about
    prose, it is a rule about where the paragraph reflow happened to fall, and
    in a repository hard-wrapped at ~80 columns it exempted almost everything —
    including ``CLAUDE.md``'s own justification for how it is worded.

    **Why not a fixed line count either.** ``±n`` lines would be a number
    nobody derived, and standing rule 1 forbids inventing one. It would also be
    wrong in both directions at once: it reaches *across* a blank line into an
    unrelated paragraph, and it stops short inside a long one.

    So the window is the author's own block. A block ends at a blank line and
    at every structural boundary markdown defines: a heading, a thematic break
    or setext underline, a table row, a list item, a footnote or link
    definition, and a fenced code block — each tested after any blockquote
    marker is stripped. Those splits are what keep the rule from becoming a
    dragnet. A table of contents is a run of list items, so an identifier in
    one entry does not reach a number in the next; a comparison table gives
    every row its own scope, which is exactly where the per-row figures in
    ``CLAUDE.md`` live.

    **How wide that actually is, measured on the rule as implemented.** Over
    the governed corpus the splitter yields 4,785 blocks, but the only ones
    whose size can change an outcome are the 138 that contain a citation:
    **mean 4.2 lines, median 4, p90 8, max 18**. So the effective window is
    about four hard-wrapped lines — one paragraph — and it is bounded above by
    a real number rather than by a hope.

    Those figures replace an earlier derivation that was wrong in the way this
    repository keeps being wrong. It quoted **blank-line** blocks (mean 3.3,
    median 3) to justify a splitter that also splits on structure, and it
    quoted the all-blocks distribution, which is dominated by thousands of
    one-line table rows and headings that can never contain a citation. Both
    numbers were real, neither described the thing being justified, and both
    made the window look tighter than it is. Found by adversarial review, not
    by the author. Standing rule 1 asks for a *derived* parameter, and a
    derivation of the wrong quantity satisfies it only in form.

    The residual over-firing is deliberate. Two sentences in one paragraph,
    one carrying a figure and the other a citation, will be flagged even when
    the figure belongs to neither. That is the conservative direction: the gate
    cannot read a quote against a number in any case (see the module
    docstring), so what it is really asking is whether somebody opened the
    paper being cited in the paragraph that asserts a figure. Answering that
    costs one ``quote`` field; the alternative cost is on record three times.

    The boundaries cut the other way too, and that is the real risk here: every
    rule added to stop over-firing is also a way to wrap out of the gate's
    sight. A blank line mid-sentence silences it, and so did a hard-wrapped
    line that happened to start with a number and a full stop, until the
    ordered-list rule was bounded the way CommonMark bounds it. Those cases are
    in the suite as must-fire, not as known-good.
    """
    return _split(text, fences=True)


def _split(text: str, *, fences: bool) -> list[Block]:
    """:func:`blocks`, with fence handling switchable for the unbalanced case."""
    found: list[Block] = []
    current: list[tuple[int, str]] = []
    fence: str | None = None
    in_table = False

    def flush() -> None:
        nonlocal current
        if current:
            found.append(Block(current[0][0], tuple(current)))
            current = []

    def alone(number: int, line: str) -> None:
        """Emit one line as its own block."""
        flush()
        found.append(Block(number, ((number, line),)))

    for number, line in enumerate(text.splitlines(), start=1):
        if fence is not None:
            current.append((number, line))
            closer = _FENCE_OPEN.match(line)
            if (
                closer is not None
                and closer.group("marker")[0] == fence[0]
                and len(closer.group("marker")) >= len(fence)
                and not line[closer.end() :].strip()
            ):
                fence = None
                flush()
            continue

        opener = _FENCE_OPEN.match(line) if fences else None
        if opener is not None:
            flush()
            current.append((number, line))
            fence = opener.group("marker")
            continue

        # Blockquote decoration is invisible to every rule below it, so it is
        # removed before they run. A `>` line with nothing after it is the
        # blockquote's own paragraph break and must behave like a blank line.
        bare = _BLOCKQUOTE.sub("", line)
        if not bare.strip():
            in_table = False
            flush()
            continue

        if _TABLE_DELIMITER.match(bare):
            # The header row sits in `current` already; give it its own scope
            # rather than leaving it joined to the paragraph above the table.
            if current:
                header = current.pop()
                flush()
                found.append(Block(header[0], (header,)))
            alone(number, line)
            in_table = True
            continue
        if _TABLE_ROW.match(bare) or (in_table and "|" in bare):
            alone(number, line)
            in_table = True
            continue
        in_table = False

        if _HEADING.match(bare) or _RULE.match(bare):
            alone(number, line)
            continue
        ordered = _ORDERED.match(bare)
        if (
            _BULLET.match(bare)
            or _DEFINITION.match(bare)
            or (ordered is not None and (not current or ordered.group("ordinal") == "1"))
        ):
            flush()
        current.append((number, line))

    if fence is not None:
        # An opener with no closer. CommonMark runs it to end of document, but
        # for this gate that means one unterminated fence pools every citation
        # after it into a single block, so the window silently becomes the rest
        # of the file — the exact unbounded scope this design exists to avoid.
        # A malformed document must not widen the rule, so it is re-read with
        # fence handling off. Line numbers are preserved, because an issue a
        # reader cannot locate is not much better than one nobody reported.
        return _split(text, fences=False)
    flush()
    return found


def scan_text(path: str, text: str, bib: dict[str, BibEntry]) -> list[CitationIssue]:
    """Check one document's citations against the bibliography.

    Scoped to :func:`blocks`. An issue is still reported at the line the
    identifier sits on, so it can be fixed without searching for it.
    """
    issues: list[CitationIssue] = []
    for block in blocks(text):
        block_asserts = asserts_a_number(block.text)
        seen: set[str] = set()
        for number, line in block.lines:
            for arxiv_id in dict.fromkeys(_ARXIV.findall(line)):
                if arxiv_id in seen:
                    continue
                seen.add(arxiv_id)
                entry = bib.get(arxiv_id)
                if entry is None:
                    issues.append(
                        CitationIssue(
                            path,
                            number,
                            arxiv_id,
                            f"not in {BIB_PATH}. Every cited identifier needs an entry, so that "
                            "a reader can check what was cited without re-deriving it from "
                            "prose.",
                        )
                    )
                    continue
                if block_asserts and not entry.has_quote:
                    issues.append(
                        CitationIssue(
                            path,
                            number,
                            arxiv_id,
                            f"a number is asserted in the same block as this citation, but its "
                            f"{BIB_PATH} entry has no `{QUOTE_FIELD}` field. Add the verbatim "
                            "sentence the figure comes from. Three misattributions on "
                            "2026-08-11 all cited real papers; the number beside the identifier "
                            "was what was wrong.",
                        )
                    )
    return issues


#: Any ``name = { ... }`` field, matched to its opening brace so the body can be
#: brace-balanced from there. **Every** field, not only ``quote`` — see
#: :func:`check_percent_escaping` for why that turned out to be the wrong scope.
_FIELD_OPEN: Final = re.compile(r"^[ \t]*(?P<name>[A-Za-z][A-Za-z0-9_-]*)\s*=\s*\{", re.M)


def _brace_body(text: str, open_brace: int) -> tuple[str, int]:
    """The contents of a brace group, and the index of its closing brace."""
    depth = 0
    index = open_brace
    while index < len(text):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                break
        index += 1
    return text[open_brace + 1 : index], index


def check_percent_escaping(text: str) -> list[CitationIssue]:
    """Every bibliography field must escape its percent signs.

    A bare ``%`` is copied through to the ``.bbl``, where **LaTeX** comments out
    the rest of the line. So ``found 59% more hidden issues`` typesets as
    ``found 59`` and the rest of the sentence is gone. It fails silently and it
    fails *invisibly*: what remains still looks like a quote, still sits in a
    ``quote`` field, and still satisfies every other check in this module. What
    gets cut is the figure — a percent sign is what truncates, so the prose
    survives and the number the citation was doing arithmetic work for does not.

    Found on 2026-08-13 in 33 places, none of which had ever been compiled:
    ``paper/`` has not been built. The check is written now rather than when the
    build is first run, because the day the build runs is the day 33 silent
    truncations become 33 wrong quotes.

    **The scope is every field, and it started as only ``quote``, which was the
    wrong half.** An independent check pointed out that ``quote`` and
    ``version`` are non-standard fields no standard style prints, so a bare
    ``%`` in them cannot break a build — while ``note``, which every standard
    style *does* typeset, held all 35 of the remaining bare signs. The audited
    field was the safe one. The worst of them is in a retraction:
    ``THE 63.7% IS NOT IN THIS PAPER`` truncates at the percent and the survivor
    reads as the opposite of what was meant. So the rule stopped being about
    ``quote`` and became about the file.
    """
    issues: list[CitationIssue] = []
    for match in _FIELD_OPEN.finditer(text):
        body, close = _brace_body(text, match.end() - 1)
        entry = text.rfind("\n@", 0, match.start())
        found = _ARXIV.search(text[entry:close]) if entry != -1 else None
        arxiv_id = found.group(1) if found else "-"
        line0 = text.count("\n", 0, match.start()) + 1
        for index, char in enumerate(body):
            if char == "%" and (index == 0 or body[index - 1] != "\\"):
                issues.append(
                    CitationIssue(
                        BIB_PATH,
                        line0 + body.count("\n", 0, index),
                        arxiv_id,
                        f"bare `%` in the `{match.group('name')}` field. It reaches the .bbl, "
                        "where LaTeX comments out the rest of the line — which is where the "
                        "figure is. Write `\\%`.",
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

    bib_text = bib_path.read_text(encoding="utf-8")
    bib = parse_bib(bib_text)
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

    # Not baselined and not exemptible. A truncated quote is a defect in the
    # evidence itself rather than in a claim resting on it, so there is nothing
    # for a baseline to defer: the fix is one backslash.
    issues += check_percent_escaping(bib_text)
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
