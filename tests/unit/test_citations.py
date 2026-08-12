"""The citation gate.

The cases that matter are the ones the real failures took: a real paper, a real
identifier, and a wrong number beside it. A test suite that only proves missing
entries are caught would pass while the gate misses everything it was built for.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from decision_evals.citations import (
    BASELINE_PATH,
    BIB_PATH,
    asserts_a_number,
    census,
    check_citations,
    governed_files,
    load_baseline,
    parse_bib,
    scan_text,
)

_ENTRY = """
@article{example,
  title   = {A Paper},
  journal = {arXiv preprint arXiv:2605.24050},
  year    = {2026},
  quote   = {up to 21% when scaling to a 202-skill library}
}
"""

_ENTRY_NO_QUOTE = """
@article{example,
  title   = {A Paper},
  journal = {arXiv preprint arXiv:2605.24050},
  year    = {2026}
}
"""


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
