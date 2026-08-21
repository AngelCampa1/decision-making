"""Tests for the blind-adjudication coverage gate.

The failure this exists to catch has happened here: answer key v5 added 72 items
on 2026-08-20, the register said no number may be published against it until
they had been adjudicated, and the full gate passed green for a day on a tree
whose live answer key was 78% covered.

Every refusal below is asserted to fire, because a gate whose refusals nothing
exercises is the shape this repository has now shipped twice.
"""

from __future__ import annotations

import json
from pathlib import Path

from decision_evals.adjudication import (
    ADJUDICATORS,
    BASELINE_PATH,
    CHECKPOINT_PATH,
    adjudicated_cases,
    census,
    check_adjudication,
    load_baseline,
    panels,
    record_cases,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_KEY = "datasets/triggers/decision-making/index.yaml"


def _row(case: str, judge: object, **overrides: object) -> str:
    return json.dumps({"case": case, "judge": judge, "adjudicated": True, **overrides})


def _repo(tmp_path: Path, rows: list[str], *, baseline: str | None = None) -> Path:
    (tmp_path / "results" / "triggers").mkdir(parents=True)
    (tmp_path / CHECKPOINT_PATH).write_text("\n".join(rows), encoding="utf-8")
    if baseline is not None:
        (tmp_path / "datasets" / "triggers").mkdir(parents=True)
        (tmp_path / BASELINE_PATH).write_text(baseline, encoding="utf-8")
    return tmp_path


def _panel(case: str, **overrides: object) -> list[str]:
    """A full readable panel for one case."""
    return [_row(case, judge, **overrides) for judge in range(ADJUDICATORS)]


def _corpora(*ids: str, version: int = 5, key: str = _KEY) -> dict[str, tuple[int, frozenset[str]]]:
    return {key: (version, frozenset(ids))}


class TestReadingTheLedger:
    def test_a_full_panel_counts_as_covered(self, tmp_path: Path) -> None:
        assert adjudicated_cases(_repo(tmp_path, _panel("s01p"))) == {"s01p"}

    def test_a_no_verdict_is_a_verdict(self, tmp_path: Path) -> None:
        """556 of the 858 rows on disk are `false`. Dropping them loses 176 cases."""
        repo = _repo(tmp_path, _panel("s01p", adjudicated=False))
        assert adjudicated_cases(repo) == {"s01p"}

    def test_a_partial_panel_does_not_count(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, [_row("s01p", 0), _row("s01p", 1)])
        assert adjudicated_cases(repo) == set()

    def test_an_unreadable_reply_is_not_a_verdict(self, tmp_path: Path) -> None:
        rows = [_row("s01p", judge, adjudicated=None) for judge in range(ADJUDICATORS)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == set()

    def test_a_row_with_no_verdict_field_fills_no_slot(self, tmp_path: Path) -> None:
        rows = [json.dumps({"case": "s01p", "judge": judge}) for judge in range(ADJUDICATORS)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == set()

    def test_a_repeated_slot_is_resolved_last_wins(self, tmp_path: Path) -> None:
        """A retry that failed to parse empties the slot its first attempt filled."""
        rows = [*_panel("s01p"), _row("s01p", 2, adjudicated=None)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == set()

    def test_a_retry_that_parsed_refills_the_slot(self, tmp_path: Path) -> None:
        rows = [*_panel("s01p"), _row("s01p", 2, adjudicated=None), _row("s01p", 2)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == {"s01p"}

    def test_a_repeated_judge_does_not_fill_the_panel(self, tmp_path: Path) -> None:
        rows = [_row("s01p", 0), _row("s01p", 0), _row("s01p", 1)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == set()

    def test_more_judges_than_the_panel_still_counts(self, tmp_path: Path) -> None:
        rows = [_row("s01p", judge) for judge in range(5)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == {"s01p"}

    def test_blank_and_unparseable_lines_are_skipped(self, tmp_path: Path) -> None:
        rows = ["", "   ", "not json", json.dumps([1, 2]), *_panel("s01p")]
        assert adjudicated_cases(_repo(tmp_path, rows)) == {"s01p"}

    def test_a_non_string_case_is_skipped(self, tmp_path: Path) -> None:
        rows = [_row("s01p", 0), json.dumps({"case": 7, "judge": 1, "adjudicated": True})]
        assert adjudicated_cases(_repo(tmp_path, rows)) == set()

    def test_a_missing_checkpoint_covers_nothing(self, tmp_path: Path) -> None:
        assert panels(tmp_path) == {}
        assert adjudicated_cases(tmp_path) == set()


class TestTheJudgeSlot:
    def test_a_slot_written_as_a_string_is_the_same_slot(self, tmp_path: Path) -> None:
        """`load_done` coerces with `int()`, so the two readers must agree."""
        rows = [_row("s01p", "0"), _row("s01p", 1.0), _row("s01p", 2)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == {"s01p"}

    def test_a_boolean_is_not_a_judge_slot(self, tmp_path: Path) -> None:
        rows = [_row("s01p", True), _row("s01p", False), _row("s01p", 2)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == set()

    def test_an_uncoercible_slot_is_skipped(self, tmp_path: Path) -> None:
        rows = [_row("s01p", "left"), _row("s01p", None), _row("s01p", 2)]
        assert adjudicated_cases(_repo(tmp_path, rows)) == set()


class TestRecordCases:
    def test_it_reads_the_case_ids_a_run_names(self, tmp_path: Path) -> None:
        path = tmp_path / "verdicts.jsonl"
        path.write_text(
            "\n".join([json.dumps({"case": "s01p"}), "", json.dumps({"case": "s02p"})]),
            encoding="utf-8",
        )
        assert record_cases(path) == {"s01p", "s02p"}

    def test_an_unreadable_file_names_nothing(self, tmp_path: Path) -> None:
        assert record_cases(tmp_path / "absent.jsonl") == set()

    def test_unparseable_and_shapeless_rows_are_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "verdicts.jsonl"
        path.write_text(
            "\n".join(["not json", json.dumps([1]), json.dumps({"case": 7}), json.dumps({})]),
            encoding="utf-8",
        )
        assert record_cases(path) == set()


class TestBaseline:
    def test_comments_and_blanks_are_stripped(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, [], baseline=f"# a reason\n\n{_KEY}  # trailing\n")
        assert load_baseline(repo) == {_KEY}

    def test_a_missing_baseline_exempts_nothing(self, tmp_path: Path) -> None:
        assert load_baseline(tmp_path) == set()


class TestCoverage:
    def test_a_fully_covered_key_passes(self, tmp_path: Path) -> None:
        assert check_adjudication(_repo(tmp_path, _panel("s01p")), _corpora("s01p")) == []

    def test_an_uncovered_item_is_refused(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, _panel("s01p"))
        issues = check_adjudication(repo, _corpora("s01p", "s25p"))
        assert len(issues) == 1
        assert issues[0].where == _KEY
        assert "1 of 2 item(s)" in issues[0].message
        assert "s25p" in issues[0].message

    def test_the_message_locates_the_key_and_reads_as_one_line(self, tmp_path: Path) -> None:
        issue = check_adjudication(_repo(tmp_path, []), _corpora("s25p"))[0]
        assert str(issue) == f"{_KEY}: {issue.message}"

    def test_a_long_list_of_missing_ids_is_truncated_with_a_count(self, tmp_path: Path) -> None:
        missing = tuple(f"s{n:02d}p" for n in range(1, 21))
        issues = check_adjudication(_repo(tmp_path, []), _corpora(*missing))
        assert "and 14 more" in issues[0].message

    def test_a_short_list_is_not_truncated(self, tmp_path: Path) -> None:
        issues = check_adjudication(_repo(tmp_path, []), _corpora("s01p", "s02p"))
        assert "more" not in issues[0].message

    def test_a_stale_ledger_id_covers_nothing(self, tmp_path: Path) -> None:
        """`l15p` and its negatives outlived the triple they belonged to."""
        issues = check_adjudication(_repo(tmp_path, _panel("l15p")), _corpora("s25p"))
        assert len(issues) == 1
        assert "1 of 1 item(s)" in issues[0].message

    def test_an_empty_corpus_set_is_refused_by_nothing(self, tmp_path: Path) -> None:
        assert check_adjudication(_repo(tmp_path, []), {}) == []

    def test_every_uncovered_key_is_reported(self, tmp_path: Path) -> None:
        corpora = {**_corpora("s25p"), **_corpora("p04", key="other.yaml", version=2)}
        issues = check_adjudication(_repo(tmp_path, []), corpora)
        assert [issue.where for issue in issues] == [_KEY, "other.yaml"]


class TestTheRemedy:
    def test_a_case_with_no_record_is_sent_to_missing_only(self, tmp_path: Path) -> None:
        issues = check_adjudication(_repo(tmp_path, []), _corpora("s25p"))
        assert "--missing-only" in issues[0].message

    def test_a_case_with_a_partial_panel_is_not(self, tmp_path: Path) -> None:
        """`--missing-only` skips a case holding one row, which is the trap."""
        repo = _repo(tmp_path, [_row("s25p", 0)])
        message = check_adjudication(repo, _corpora("s25p"))[0].message
        assert "`--missing-only` will skip them" in message
        assert "--only <the ids>" in message


class TestPublishedRuns:
    def test_a_run_whose_cases_are_covered_passes(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, _panel("s01p"))
        runs = {"results/x/2026-08-19-abc1234": (_KEY, frozenset({"s01p"}))}
        assert check_adjudication(repo, _corpora("s01p"), runs) == []

    def test_a_run_naming_an_unadjudicated_case_is_refused(self, tmp_path: Path) -> None:
        """The live key can be made clean by retiring the item; the run cannot."""
        repo = _repo(tmp_path, _panel("s01p"))
        runs = {"results/x/2026-08-19-abc1234": (_KEY, frozenset({"s01p", "s25p"}))}
        issues = check_adjudication(repo, _corpora("s01p"), runs)
        assert len(issues) == 1
        assert issues[0].where == "results/x/2026-08-19-abc1234"
        assert "s25p" in issues[0].message
        assert _KEY in issues[0].message

    def test_a_run_declaring_a_baselined_key_is_exempt(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, [], baseline="datasets/triggers/decision-making.yaml\n")
        runs = {
            "results/x/2026-08-12-abc1234": (
                "datasets/triggers/decision-making.yaml",
                frozenset({"p04"}),
            )
        }
        assert (
            check_adjudication(
                repo, {"datasets/triggers/decision-making.yaml": (2, frozenset({"p04"}))}, runs
            )
            == []
        )

    def test_runs_are_reported_after_keys_and_in_order(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, [])
        runs = {
            "results/x/b": (_KEY, frozenset({"s25p"})),
            "results/x/a": (_KEY, frozenset({"s25p"})),
        }
        issues = check_adjudication(repo, _corpora("s25p"), runs)
        assert [issue.where for issue in issues] == [_KEY, "results/x/a", "results/x/b"]

    def test_no_runs_is_the_same_as_none(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, _panel("s01p"))
        assert check_adjudication(repo, _corpora("s01p"), {}) == []


class TestBaselineMayOnlyShrink:
    def test_a_baselined_key_is_exempt_while_it_is_uncovered(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, [], baseline=f"{_KEY}\n")
        assert check_adjudication(repo, _corpora("s25p")) == []

    def test_a_baselined_key_that_is_now_covered_is_refused(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, _panel("s01p"), baseline=f"{_KEY}\n")
        issues = check_adjudication(repo, _corpora("s01p"))
        assert len(issues) == 1
        assert issues[0].where == BASELINE_PATH
        assert "Remove the line" in issues[0].message

    def test_a_baselined_key_naming_no_loaded_set_is_refused(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, [], baseline="datasets/triggers/gone.yaml\n")
        issues = check_adjudication(repo, {})
        assert len(issues) == 1
        assert "names no trigger set that loaded" in issues[0].message

    def test_uncovered_keys_are_reported_before_baseline_defects(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, _panel("s01p"), baseline=f"{_KEY}\ndatasets/triggers/gone.yaml\n")
        corpora = {**_corpora("s01p"), **_corpora("s25p", key="other.yaml", version=2)}
        issues = check_adjudication(repo, corpora)
        assert [issue.where for issue in issues] == ["other.yaml", BASELINE_PATH, BASELINE_PATH]


class TestCensus:
    def test_baselined_items_are_outside_the_denominator(self, tmp_path: Path) -> None:
        """A total the header can never reach stops meaning anything."""
        repo = _repo(tmp_path, _panel("s01p"), baseline="datasets/triggers/decision-making.yaml\n")
        corpora = {
            **_corpora("s01p", "s25p"),
            "datasets/triggers/decision-making.yaml": (2, frozenset({"p04"})),
        }
        assert census(repo, corpora) == (2, 1, 1)

    def test_an_item_shared_between_keys_is_counted_once(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path, _panel("s01p"))
        corpora = {**_corpora("s01p"), **_corpora("s01p", key="other.yaml", version=2)}
        assert census(repo, corpora) == (1, 1, 0)


class TestTheRealRepository:
    def test_the_live_answer_keys_are_adjudicated_or_baselined(self) -> None:
        """The gate this module exists to be, run against the tree it ships in."""
        from decision_evals.triggers import TRIGGERS_DIR, TriggerSetError, load_trigger_set

        triggers_dir = REPO_ROOT / TRIGGERS_DIR
        corpora: dict[str, tuple[int, frozenset[str]]] = {}
        paths = (*sorted(triggers_dir.glob("*.yaml")), *sorted(triggers_dir.glob("*/index.yaml")))
        for path in paths:
            try:
                trigger_set = load_trigger_set(path)
            except TriggerSetError:
                continue
            key = path.relative_to(REPO_ROOT).as_posix()
            corpora[key] = (trigger_set.version, frozenset(c.id for c in trigger_set.cases))

        assert check_adjudication(REPO_ROOT, corpora) == []
