"""The citation gate.

The cases that matter are the ones the real failures took: a real paper, a real
identifier, and a wrong number beside it. A test suite that only proves missing
entries are caught would pass while the gate misses everything it was built for.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from decision_evals.citations import (
    BASELINE_PATH,
    BIB_PATH,
    asserts_a_number,
    blocks,
    census,
    check_citations,
    check_percent_escaping,
    governed_files,
    load_baseline,
    parse_bib,
    scan_text,
)

_ENTRY = r"""
@article{example,
  title   = {A Paper},
  journal = {arXiv preprint arXiv:2605.24050},
  year    = {2026},
  quote   = {up to 21\% when scaling to a 202-skill library}
}
"""

#: The same entry with the percent left bare, which is how 33 of them sat in
#: `paper/refs.bib` until 2026-08-13. BibTeX would compile the quote as
#: ``up to 21`` and drop the rest of the line.
_ENTRY_BARE_PERCENT = _ENTRY.replace(r"21\%", "21%")

_ENTRY_NO_QUOTE = """
@article{example,
  title   = {A Paper},
  journal = {arXiv preprint arXiv:2605.24050},
  year    = {2026}
}
"""

#: Two papers, **neither carrying a quote**, so a known-good case can put two
#: citations near each other without the missing-entry rule firing. The absence
#: of a quote is deliberate: the only thing that may make a known-good case pass
#: is the window. A fixture carrying a quote would pass every case for the wrong
#: reason and prove nothing about the window at all.
_TWO_ENTRIES = (
    _ENTRY_NO_QUOTE
    + """
@article{other,
  title   = {Another Paper},
  journal = {arXiv preprint arXiv:2602.12670},
  year    = {2026}
}
"""
)


def test_bib_entry_is_indexed_by_arxiv_id() -> None:
    bib = parse_bib(_ENTRY)
    assert set(bib) == {"2605.24050"}
    assert bib["2605.24050"].has_quote


def test_entry_without_a_quote_is_recorded_as_such() -> None:
    assert not parse_bib(_ENTRY_NO_QUOTE)["2605.24050"].has_quote


def test_commented_out_identifiers_do_not_count_as_entries() -> None:
    """A `% VERIFY` banner is not a bibliography entry.

    Without comment stripping, an identifier mentioned in a note above an entry
    would satisfy the gate for a paper nobody recorded.
    """
    text = "% see arXiv:2505.06120 for context\n" + _ENTRY
    assert set(parse_bib(text)) == {"2605.24050"}


def test_a_quote_field_inside_a_comment_does_not_count() -> None:
    text = _ENTRY_NO_QUOTE.replace("  year    = {2026}", "  year = {2026}\n%  quote = {nope}")
    assert not parse_bib(text)["2605.24050"].has_quote


def test_missing_entry_is_an_issue() -> None:
    issues = scan_text("docs/x.md", "See arXiv:2505.06120 for the design.", {})
    assert len(issues) == 1
    assert issues[0].arxiv_id == "2505.06120"
    assert BIB_PATH in issues[0].message


def test_a_bare_citation_needs_no_quote() -> None:
    """The rule is narrow on purpose. Citing a paper is not asserting a figure."""
    bib = parse_bib(_ENTRY_NO_QUOTE)
    assert scan_text("docs/x.md", "The approach follows arXiv:2605.24050.", bib) == []


def test_a_number_beside_a_citation_requires_a_quote() -> None:
    """The failure this gate exists for: real paper, real id, wrong number."""
    bib = parse_bib(_ENTRY_NO_QUOTE)
    issues = scan_text("docs/x.md", "Degrades 21% (arXiv:2605.24050).", bib)
    assert len(issues) == 1
    assert "quote" in issues[0].message


def test_a_number_beside_a_quoted_citation_is_fine() -> None:
    bib = parse_bib(_ENTRY)
    assert scan_text("docs/x.md", "Degrades 21% (arXiv:2605.24050).", bib) == []


@pytest.mark.parametrize(
    "line",
    [
        "presence is worth +18 to +36pp",
        "the drop was 39%",
        "inter-annotator kappa = 0.88",
        "AUC 0.679 against a ceiling",
        "self-generated skills are -1.3pp",
    ],
)
def test_claim_numbers_are_detected(line: str) -> None:
    assert asserts_a_number(line)


@pytest.mark.parametrize(
    "line",
    [
        "see arXiv:2605.24050",
        "https://arxiv.org/abs/2602.12670 is the source",
        "version 0.2.0 of the skill",
        "published in 2026",
        "87 tasks across 8 domains",
    ],
)
def test_non_claim_numbers_are_not_flagged(line: str) -> None:
    """Identifiers, URLs, versions, years and counts are not empirical claims.

    The identifier itself is the important case: `2605.24050` is four digits,
    a dot and five digits, so a naive number rule fires on every citation in
    the repository and the gate gets switched off within a day.
    """
    assert not asserts_a_number(line)


def test_the_identifier_alone_does_not_trigger_the_quote_rule() -> None:
    bib = parse_bib(_ENTRY_NO_QUOTE)
    assert scan_text("docs/x.md", "See https://arxiv.org/abs/2605.24050 here.", bib) == []


def test_one_line_citing_twice_reports_each_once() -> None:
    issues = scan_text("docs/x.md", "arXiv:2505.06120 and arXiv:2505.06120 again.", {})
    assert len(issues) == 1


def _repo(tmp_path: Path, *, doc: str, bib: str, baseline: str | None = None) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text(doc, encoding="utf-8")
    (tmp_path / "paper").mkdir()
    (tmp_path / BIB_PATH).write_text(bib, encoding="utf-8")
    if baseline is not None:
        (tmp_path / BASELINE_PATH).write_text(baseline, encoding="utf-8")
    return tmp_path


def test_a_missing_bibliography_is_itself_an_issue(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text("arXiv:2505.06120", encoding="utf-8")
    issues = check_citations(tmp_path)
    assert len(issues) == 1
    assert "missing" in issues[0].message


def test_baseline_exempts_a_legacy_identifier(tmp_path: Path) -> None:
    root = _repo(tmp_path, doc="See arXiv:2505.06120.", bib=_ENTRY, baseline="2505.06120\n")
    assert check_citations(root) == []


def test_baseline_comments_and_blank_lines_are_ignored(tmp_path: Path) -> None:
    baseline = "# legacy, seeded 2026-08-11\n\n2505.06120  # re-read me\n"
    root = _repo(tmp_path, doc="See arXiv:2505.06120.", bib=_ENTRY, baseline=baseline)
    assert load_baseline(root) == {"2505.06120"}
    assert check_citations(root) == []


def test_a_baseline_entry_that_is_no_longer_broken_fails_the_gate(tmp_path: Path) -> None:
    """The property that makes a baseline a backlog rather than a dustbin.

    Without this, resolved entries accumulate and the baseline stops reporting
    anything about how much work is left.
    """
    root = _repo(tmp_path, doc="No citations here.", bib=_ENTRY, baseline="2505.06120\n")
    issues = check_citations(root)
    assert len(issues) == 1
    assert "baselined but has no outstanding issue" in issues[0].message


def test_baseline_does_not_exempt_a_second_unrelated_identifier(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        doc="arXiv:2505.06120 and arXiv:2606.29251.",
        bib=_ENTRY,
        baseline="2505.06120\n",
    )
    issues = check_citations(root)
    assert [issue.arxiv_id for issue in issues] == ["2606.29251"]


def test_absent_baseline_file_is_an_empty_baseline(tmp_path: Path) -> None:
    root = _repo(tmp_path, doc="arXiv:2505.06120", bib=_ENTRY)
    assert load_baseline(root) == set()
    assert len(check_citations(root)) == 1


def test_census_counts_cited_and_bibliography_and_missing(tmp_path: Path) -> None:
    root = _repo(tmp_path, doc="arXiv:2505.06120 and arXiv:2605.24050.", bib=_ENTRY)
    assert census(root) == (2, 1, 1)


def test_governed_files_are_deduplicated(tmp_path: Path) -> None:
    root = _repo(tmp_path, doc="x", bib=_ENTRY)
    (root / "AGENTS.md").write_text("y", encoding="utf-8")
    found = governed_files(root)
    assert len(found) == len(set(found))
    assert (root / "docs" / "x.md") in found


def test_the_repository_itself_passes_the_gate() -> None:
    """The gate is only meaningful if it is actually satisfied here."""
    assert check_citations(Path(__file__).resolve().parents[2]) == []


# ---------------------------------------------------------------------------
# The block window, widened 2026-08-13.
#
# Standing rule 2: a falsifier must be run against a known-good case before it
# may fail anything. These are those cases, kept in the suite rather than in
# somebody's scratchpad, because the rule is about every future widening of
# this gate and not only the one that happened to prompt it.
# ---------------------------------------------------------------------------

#: Constructions a careful author would write, where the number does NOT belong
#: to the citation. A flag on any of these means the gate has become a dragnet,
#: which is as useless as one that fires on nothing — this repository has
#: shipped both.
KNOWN_GOOD: Final = {
    "toc: identifier in one list entry, number in the next": """
- [Availability](docs/RELATED_WORK.md) — arXiv:2605.24050
- [Granularity](docs/PROTOCOL.md) — the +16.6pp result
""",
    "two unrelated citations in adjacent paragraphs": """
The curator architecture is arXiv:2605.24050 and we adopt its split unchanged.

A separate line of work reports a 21% degradation as libraries grow, which is
a different claim about a different intervention entirely.
""",
    "number in the paragraph before the break, identifier after": """
Presence effects run to +36pp on the two models tested.

The taxonomy comes from arXiv:2605.24050 and is held constant across arms.
""",
    "heading carrying a number, identifier in the body below": """
## The 23.8-point swing

The ontology used throughout is arXiv:2605.24050, adopted without change.
""",
    "table: number in one row, identifier in another": """
| Xu & Wu (arXiv:2605.24050) | 30 tasks | qualitative only |
| Li et al. | 87 tasks | **+16.6pp** |
""",
    "identifiers listed under a heading that carries a figure": """
### Calibration, and the 50% ECE reduction

- arXiv:2605.24050
- arXiv:2602.12670
""",
    "number and identifier separated by a horizontal rule": """
Removing the option menu moved every model by 14-40 pp.

---

The taxonomy itself is arXiv:2605.24050 and is unchanged across versions.
""",
    "versions, years and task counts are not claims": """
Version 0.2.0, published in 2026, follows arXiv:2605.24050 across all 87 tasks.
""",
    # Everything below was found by an adversarial review on 2026-08-13, which
    # was given the splitter and told to break it. Each one flagged before the
    # fix; the first is the only one that had a live instance in the corpus.
    "blockquoted table: the rows split even behind a `>`": """
> | Xu & Wu (arXiv:2605.24050) | 30 tasks | qualitative only |
> | Li et al. | 87 tasks | **+16.6pp** |
""",
    "blockquote paragraphs are separated by their own blank line": """
> The taxonomy is arXiv:2605.24050 and we adopt it unchanged.
>
> A different line of work reports 21% degradation as libraries grow.
""",
    "GFM table without leading pipes": """
Paper | Scale | Effect
--- | --- | ---
arXiv:2605.24050 | 30 tasks | qualitative only
Li et al. | 87 tasks | +16.6pp
""",
    "setext `===` underline splits, exactly as `---` does": """
Xu and Wu, arXiv:2605.24050
===========================
An unrelated rerun of our own corpus scored 45% on 20 items.
""",
    "consecutive footnote definitions are separate units": """
[^1]: Xu and Wu, arXiv:2605.24050.
[^2]: Our own replication, 45% on 20 items, unpublished.
""",
    "a page range is not percentage points": """
The method is set out in Smith and Jones, chapter 3
pp. 14-19, and is applied by arXiv:2605.24050.
""",
    "a mismatched fence marker must not desync the parser": """
```text
A line about the other fence style:
~~~
still inside the code block
```

arXiv:2605.24050 is discussed here.

Elsewhere we measured 45%.
""",
    "an unterminated fence must not pool the rest of the file": """
```text
opened and never closed

arXiv:2605.24050

45% measured on our own corpus
""",
}

#: The other half of rule 2, and of "an estimator that cannot return a non-zero
#: value is not a measurement". A gate that passes everything measures nothing.
MUST_FIRE: Final = {
    "the CLAUDE.md wrap that motivated this: claim, then identifier": """
The wording is deliberate. Trust-framed prompts surfaced 59% more hidden
issues than unframed ones in a controlled comparison (arXiv:2605.24050).
""",
    "regression: same line, which the line-scoped gate did catch": "Degrades 21% (arXiv:2605.24050).",
    "one table row carrying both its figure and its citation": (
        "| Xu & Wu (arXiv:2605.24050) | 30 tasks | **+18 to +36pp** |"
    ),
    "one list item carrying both": """
- **AbstentionBench** — arXiv:2605.24050. Reasoning-tuned models are ~24% worse
  at abstaining than their base counterparts.
""",
    # The other half of the same review: a boundary rule added to stop
    # over-firing must not become a way to wrap out of the gate's sight.
    "a wrapped line starting with an ordinal is prose, not a list": """
Degradation reached 21% only at the top of a range running from four to
202. That is the figure reported in arXiv:2605.24050.
""",
    "one blockquoted paragraph carrying both": """
> Trust framing surfaced 59% more hidden issues than unframed ones
> in a controlled comparison (arXiv:2605.24050).
""",
    "one row of a table written without leading pipes": """
Paper | Scale | Effect
--- | --- | ---
arXiv:2605.24050 | 30 tasks | +18 to +36pp
""",
}


@pytest.mark.parametrize("doc", KNOWN_GOOD.values(), ids=list(KNOWN_GOOD))
def test_the_widened_window_passes_known_good_documents(doc: str) -> None:
    """Rule 2, in the direction people forget: what must NOT be flagged.

    Every case here is one the line-scoped gate accepted and a reader would
    too. The block splits — heading, rule, table row, list item, blank line —
    are what keep the window from reaching across into an unrelated claim.
    """
    assert scan_text("docs/x.md", doc, parse_bib(_TWO_ENTRIES)) == []


@pytest.mark.parametrize("doc", MUST_FIRE.values(), ids=list(MUST_FIRE))
def test_the_widened_window_still_fires_where_it_must(doc: str) -> None:
    assert scan_text("docs/x.md", doc, parse_bib(_ENTRY_NO_QUOTE)) != []


def test_a_hard_wrapped_claim_reaches_its_citation() -> None:
    """The defect this widening exists for, stated as directly as possible.

    ``CLAUDE.md`` put "59% more hidden issues" on one line and the identifier
    on the next, because the paragraph reflowed there. For as long as the scan
    was line-scoped, the gate enforcing standing rule 5 had never checked the
    product file's own load-bearing citation.
    """
    wrapped = "Trust framing surfaced 59% more hidden\nissues (arXiv:2605.24050) than baseline."
    assert scan_text("CLAUDE.md", wrapped, parse_bib(_ENTRY_NO_QUOTE)) != []
    assert scan_text("CLAUDE.md", wrapped, parse_bib(_ENTRY)) == []


def test_an_issue_is_reported_at_the_identifier_not_the_number() -> None:
    """Block-scoped detection, line-scoped reporting: fix it without searching."""
    issues = scan_text(
        "docs/x.md",
        "A claim of 21% appears here\nand the citation arXiv:2605.24050 is here.",
        parse_bib(_ENTRY_NO_QUOTE),
    )
    assert [issue.line for issue in issues] == [2]


def test_a_fenced_block_is_one_block() -> None:
    """A fence is verbatim shipped text; its contents are not reflowed prose."""
    found = blocks("before\n\n```\none\n\ntwo\n```\n\nafter")
    assert [block.first_line for block in found] == [1, 3, 9]


def test_an_unterminated_fence_does_not_swallow_the_rest_of_the_document() -> None:
    """A malformed document must not silently widen the window to the whole file.

    An earlier version of this test asserted only that *a* block came back from
    a two-line input, which a splitter that pooled everything into one block
    passes trivially. An adversarial review pointed that out, so the assertion
    is now about separation.
    """
    text = "```text\nopened, never closed\n\narXiv:2605.24050\n\n45% measured here\n"
    assert len(blocks(text)) > 1


def test_line_numbers_survive_the_unbalanced_fence_fallback() -> None:
    """The fallback re-reads the document; it must not renumber it."""
    text = "```text\nopener\n\nclaim of 21% here\n\narXiv:2605.24050 is cited here\n"
    assert blocks(text)[-1].first_line == 6


def test_a_mismatched_fence_marker_does_not_close_a_fence() -> None:
    """`~~~` inside a backtick fence used to desync the parser to end of file."""
    text = "```text\n~~~\n```\n\narXiv:2605.24050\n\n45% elsewhere\n"
    assert [block.first_line for block in blocks(text)] == [1, 5, 7]


def test_blocks_survive_crlf_line_endings() -> None:
    """This repository is developed on Windows."""
    assert len(blocks("one\r\n\r\ntwo\r\n")) == 2


# ---------------------------------------------------------------------------
# Percent escaping in quote fields.
# ---------------------------------------------------------------------------


def test_a_bare_percent_in_a_quote_is_an_issue() -> None:
    """It reaches the .bbl, and LaTeX comments the rest of the line out."""
    issues = check_percent_escaping(_ENTRY_BARE_PERCENT)
    assert len(issues) == 1
    assert issues[0].arxiv_id == "2605.24050"
    assert "quote" in issues[0].message


def test_an_escaped_percent_in_a_quote_is_fine() -> None:
    assert check_percent_escaping(_ENTRY) == []


def test_a_bare_percent_in_a_note_field_is_also_an_issue() -> None:
    """The check began at `quote` and that was the safe half.

    `quote` is a non-standard field no standard style prints, so a bare `%` in
    one cannot break a build. `note` is printed by `plain`, `plainnat` and
    `abbrv` alike, and held 35 of the 36 bare signs in this bibliography — the
    worst inside a retraction, where truncating at the `%` leaves text saying
    the opposite of what was meant. Found by an independent check, not the
    author, which is why the rule is now about the file rather than one field.
    """
    entry = _ENTRY_NO_QUOTE.replace("  year    = {2026}", "  note = {found 59% more issues}")
    issues = check_percent_escaping(entry)
    assert len(issues) == 1
    assert "note" in issues[0].message


def test_a_percent_outside_any_field_is_not_this_check_s_business() -> None:
    """`%` is a legitimate BibTeX comment between entries."""
    assert check_percent_escaping("% a banner comment\n" + _ENTRY_NO_QUOTE) == []


def test_the_bibliography_has_no_unescaped_percent() -> None:
    root = Path(__file__).resolve().parents[2]
    assert check_percent_escaping((root / BIB_PATH).read_text(encoding="utf-8")) == []
