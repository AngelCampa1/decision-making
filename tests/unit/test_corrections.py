"""Tests for the label-correction changelog gate.

The failure this exists to catch has happened here: the answer key moved, every
number computed from it moved with it, and what moved lived in a commit body.
`set_version` catches the *comparison*; nothing caught the *record*.

Every refusal below is asserted to fire, because a gate whose refusals nothing
exercises is the shape this repository has now shipped twice.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from decision_evals.corrections import (
    CORRECTIONS_PATH,
    census,
    check_corrections,
    parse_corrections,
    register_headings,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_MOVED = {
    "kind": "moved",
    "to_version": 2,
    "item": "x-n21",
    "old_label": True,
    "new_label": False,
    "date": "2026-08-13",
    "adjudicator": "maintainer",
    "decision": "a heading",
    "reason": "the question asked has an obvious answer",
}


def _line(**overrides: object) -> str:
    return json.dumps({**_MOVED, **overrides})


def _repo(tmp_path: Path, lines: list[str], *, register: str | None = "## a heading\n") -> Path:
    (tmp_path / "datasets" / "triggers").mkdir(parents=True)
    (tmp_path / CORRECTIONS_PATH).write_text("\n".join(lines), encoding="utf-8")
    if register is not None:
        (tmp_path / "docs").mkdir(parents=True)
        (tmp_path / "docs" / "DECISIONS.md").write_text(register, encoding="utf-8")
    return tmp_path


class TestParsing:
    def test_blank_lines_and_comments_are_skipped(self) -> None:
        corrections, issues = parse_corrections("\n# a comment\n   \n" + _line())
        assert issues == []
        assert len(corrections) == 1
        assert corrections[0].item == "x-n21"
        assert corrections[0].adjudicator == "maintainer"

    def test_a_line_that_is_not_json_reports_itself_without_hiding_the_rest(self) -> None:
        corrections, issues = parse_corrections("not json\n" + _line())
        assert len(corrections) == 1
        assert "not readable as JSON" in str(issues[0])
        assert ":1" in str(issues[0])

    def test_a_json_scalar_is_not_a_correction(self) -> None:
        _, issues = parse_corrections("42")
        assert "not a JSON object" in str(issues[0])

    @pytest.mark.parametrize("field", ["kind", "to_version", "date", "reason", "decision"])
    def test_every_required_field_is_required(self, field: str) -> None:
        row = dict(_MOVED)
        del row[field]
        _, issues = parse_corrections(json.dumps(row))
        assert f"has no `{field}`" in str(issues[0])

    def test_an_unknown_kind_is_refused(self) -> None:
        _, issues = parse_corrections(_line(kind="amended"))
        assert "not one of moved, none, rebuilt" in str(issues[0])

    def test_a_non_integer_version_is_refused(self) -> None:
        _, issues = parse_corrections(_line(to_version="2"))
        assert "not an integer" in str(issues[0])

    def test_a_boolean_version_is_refused_although_bool_is_an_int(self) -> None:
        """`True == 1` and `isinstance(True, int)`, so this needs its own branch."""
        _, issues = parse_corrections(_line(to_version=True))
        assert "not an integer" in str(issues[0])

    def test_nothing_moved_into_version_one(self) -> None:
        _, issues = parse_corrections(_line(to_version=1))
        assert "Version 1 is the first key" in str(issues[0])

    def test_a_date_that_is_not_iso_is_refused(self) -> None:
        _, issues = parse_corrections(_line(date="13 Aug 2026"))
        assert "not `YYYY-MM-DD`" in str(issues[0])

    def test_an_empty_reason_is_refused(self) -> None:
        _, issues = parse_corrections(_line(reason="   "))
        assert "The reason is the point" in str(issues[0])

    @pytest.mark.parametrize("field", ["item", "old_label", "new_label"])
    def test_a_moved_line_names_what_moved(self, field: str) -> None:
        row = dict(_MOVED)
        del row[field]
        _, issues = parse_corrections(json.dumps(row))
        assert f"no `{field}`" in str(issues[0])

    def test_a_label_that_is_not_a_boolean_is_refused(self) -> None:
        _, issues = parse_corrections(_line(old_label="positive"))
        assert "not a boolean" in str(issues[0])

    def test_a_label_that_did_not_change_is_not_a_move(self) -> None:
        _, issues = parse_corrections(_line(new_label=True))
        assert "which is not a move" in str(issues[0])

    def test_a_none_line_needs_no_item(self) -> None:
        """An identity bump has no item to name, and demanding one would invent it."""
        row = {k: v for k, v in _MOVED.items() if k not in ("item", "old_label", "new_label")}
        corrections, issues = parse_corrections(json.dumps({**row, "kind": "none"}))
        assert issues == []
        assert corrections[0].item is None
        assert corrections[0].old_label is None


class TestRegisterHeadings:
    def test_it_reads_second_level_headings_only(self) -> None:
        text = "# title\n\n## 2026-08-13 — a decision\n\n### a sub-heading\n"
        assert register_headings(text) == {"2026-08-13 — a decision"}


class TestTheGate:
    def test_a_clean_changelog_passes(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, [_line()])
        assert check_corrections(root, 2) == []

    def test_a_missing_changelog_is_the_first_thing_reported(self, tmp_path: Path) -> None:
        issues = check_corrections(tmp_path, 2)
        assert "changelog is missing" in str(issues[0])

    def test_an_undeclared_version_bump_is_refused(self, tmp_path: Path) -> None:
        """The failure the file exists for: the key moved and nothing says how."""
        root = _repo(tmp_path, [_line()])
        issues = check_corrections(root, 4)
        assert len(issues) == 2
        assert "reached version 3" in str(issues[0])
        assert "reached version 4" in str(issues[1])

    def test_a_decision_that_names_no_heading_is_refused(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, [_line(decision="a heading nobody wrote")])
        issues = check_corrections(root, 2)
        assert "is not a heading" in str(issues[0])

    def test_a_missing_register_refuses_every_line_rather_than_passing(
        self, tmp_path: Path
    ) -> None:
        """No register means no reasoning, not a free pass."""
        root = _repo(tmp_path, [_line()], register=None)
        issues = check_corrections(root, 2)
        assert "is not a heading" in str(issues[0])

    def test_a_line_ahead_of_the_corpus_is_refused(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, [_line(), _line(to_version=3)])
        issues = check_corrections(root, 2)
        assert "the corpus is at 2" in str(issues[0])

    def test_a_malformed_line_is_reported_before_the_transitions(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, ["{", _line()])
        issues = check_corrections(root, 2)
        assert "not readable as JSON" in str(issues[0])


class TestTheCommittedChangelog:
    """The real file, checked against the real register.

    A backfill written from git rather than from prose: the labels in
    `datasets/triggers/decision-making.yaml` were read out of the commits either
    side of each bump and diffed. Exactly one `should_fire` has ever changed on
    an item present before and after.
    """

    def test_it_accounts_for_every_version_the_corpus_has_reached(self) -> None:
        assert check_corrections(REPO_ROOT, 4) == []

    def test_the_one_label_that_ever_moved_is_x_n21(self) -> None:
        text = (REPO_ROOT / CORRECTIONS_PATH).read_text(encoding="utf-8")
        corrections, issues = parse_corrections(text)
        assert issues == []
        moves = [c for c in corrections if c.kind == "moved"]
        assert [(c.item, c.old_label, c.new_label, c.to_version) for c in moves] == [
            ("x-n21", True, False, 2)
        ]

    def test_the_census_counts_what_the_gate_prints(self) -> None:
        assert census(REPO_ROOT) == (3, 1, 3)

    def test_a_missing_file_censuses_to_zero_rather_than_raising(self, tmp_path: Path) -> None:
        assert census(tmp_path) == (0, 0, 0)
