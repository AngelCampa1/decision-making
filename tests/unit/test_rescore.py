"""The checkpoint reconciliation gate, and the arithmetic under it.

Standing rule 2: a falsifier is run against a case it should pass before it is
allowed to fail anything. :func:`test_known_good_directory_passes` is that case
and it is deliberately the first test in the file — a directory where every
checkpoint declares its key and the one older arm carries a bridge must produce
no issues at all, or the gate is wrong rather than the repository.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from decision_evals import cli
from decision_evals.rescore import (
    CHECKPOINT_DIR,
    NOT_A_CHECKPOINT,
    RESCORE_KIND,
    CheckpointIssue,
    RescoreError,
    check_checkpoints,
    key_for,
    load_declared_versions,
    load_keys,
    read_jsonl,
    reconcile,
    rescore,
    rescored_name,
    stamp,
    write_jsonl,
)
from decision_evals.triggers import load_trigger_set

V1 = """
skill: decision-making
version: 1
positive:
  - id: p01
    turn: should I take the offer or stay
    why: two options
    route: ledger
  - id: p02
    turn: the disk is at 99 percent do we need to act
    why: provisional
negative:
  - id: n01
    turn: what is the current version of pytest
    why: a lookup
"""

V2 = """
skill: decision-making
version: 2
positive:
  - id: p01
    turn: should I take the offer or stay
    why: two options
    route: [ledger, fit]
negative:
  - id: p02
    turn: the disk is at 99 percent do we need to act
    why: moved to the negatives on 2026-08-13
  - id: n01
    turn: what is the current version of pytest
    why: a lookup
"""


def _repo(tmp_path: Path, key: str = V2) -> Path:
    (tmp_path / "datasets" / "triggers").mkdir(parents=True)
    (tmp_path / "datasets" / "triggers" / "decision-making.yaml").write_text(key, encoding="utf-8")
    (tmp_path / CHECKPOINT_DIR).mkdir(parents=True)
    return tmp_path


def _row(case: str, *, fired: bool, should_fire: bool, **extra: object) -> dict[str, object]:
    return {
        "case": case,
        "repeat": 0,
        "fired": fired,
        "procedure": "ledger" if fired else None,
        "covers": None,
        "should_fire": should_fire,
        "route": "ledger" if case == "p01" else None,
        **extra,
    }


def _v1_rows() -> list[dict[str, object]]:
    return [
        _row("p01", fired=True, should_fire=True),
        _row("p02", fired=False, should_fire=True),
        _row("n01", fired=False, should_fire=False),
    ]


def _v2_rows() -> list[dict[str, object]]:
    return [
        _row("p01", fired=True, should_fire=True, set_version=2, route="ledger"),
        _row("p02", fired=False, should_fire=False, set_version=2),
        _row("n01", fired=False, should_fire=False, set_version=2),
    ]


# --------------------------------------------------------------------------- #
# Standing rule 2 first: the gate must pass a directory that is correct.
# --------------------------------------------------------------------------- #


def test_known_good_directory_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", stamp(_v1_rows(), 1))
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts-new.jsonl", _v2_rows())
    reconcile(repo, {})
    assert check_checkpoints(repo) == []


def test_a_directory_of_one_version_needs_no_bridge(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", _v2_rows())
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts-four.jsonl", _v2_rows())
    assert check_checkpoints(repo) == []


def test_no_checkpoint_directory_is_not_an_issue(tmp_path: Path) -> None:
    assert check_checkpoints(tmp_path) == []


# --------------------------------------------------------------------------- #
# stamp / rescore
# --------------------------------------------------------------------------- #


def test_stamp_writes_the_version_onto_unstamped_rows() -> None:
    assert [row["set_version"] for row in stamp(_v1_rows(), 1)] == [1, 1, 1]


def test_stamp_leaves_an_agreeing_row_alone() -> None:
    assert stamp([{"case": "p01", "set_version": 2}], 2)[0]["set_version"] == 2


def test_stamp_refuses_to_overwrite_a_different_version() -> None:
    with pytest.raises(RescoreError, match="already declares set_version 1"):
        stamp([{"case": "p01", "set_version": 1}], 2)


def test_rescore_moves_the_label_and_leaves_the_verdict(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    key = load_trigger_set(repo / "datasets" / "triggers" / "decision-making.yaml")
    rows = rescore(stamp(_v1_rows(), 1), key, source="verdicts.jsonl")

    moved = next(row for row in rows if row["case"] == "p02")
    assert moved["should_fire"] is False
    assert moved["fired"] is False
    assert moved["set_version"] == 2
    assert moved["record_kind"] == RESCORE_KIND
    assert moved["rescored_from"] == "verdicts.jsonl"
    assert moved["rescored_from_set_version"] == 1


def test_rescore_refuses_a_case_the_key_does_not_have(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    key = load_trigger_set(repo / "datasets" / "triggers" / "decision-making.yaml")
    with pytest.raises(RescoreError, match="not in the decision-making set"):
        rescore([{"case": "x-n99", "set_version": 1}], key, source="verdicts.jsonl")


def test_rescore_keeps_covers_where_the_routes_did_not_move(tmp_path: Path) -> None:
    repo = _repo(tmp_path, key=V1)
    key = load_trigger_set(repo / "datasets" / "triggers" / "decision-making.yaml")
    rows = rescore(
        [_row("p01", fired=True, should_fire=True, covers=True, set_version=1)],
        key,
        source="verdicts.jsonl",
    )
    assert rows[0]["covers"] is True
    assert "covers_stale" not in rows[0]


def test_rescore_nulls_covers_where_the_routes_moved(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    key = load_trigger_set(repo / "datasets" / "triggers" / "decision-making.yaml")
    rows = rescore(
        [_row("p01", fired=True, should_fire=True, covers=True, set_version=1)],
        key,
        source="verdicts.jsonl",
    )
    assert rows[0]["covers"] is None
    assert "entry partition" in str(rows[0]["covers_stale"])


def test_rescored_name_carries_the_target_version() -> None:
    assert rescored_name("verdicts.jsonl", 2) == "rescored-verdicts-v2.jsonl"


def test_read_jsonl_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text('{"case": "p01"}\n\n{"case": "n01"}\n', encoding="utf-8")
    assert [row["case"] for row in read_jsonl(path)] == ["p01", "n01"]


# --------------------------------------------------------------------------- #
# keys
# --------------------------------------------------------------------------- #


def test_load_keys_skips_a_set_that_will_not_load(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "datasets" / "triggers" / "broken.yaml").write_text("not a mapping", encoding="utf-8")
    assert [key.version for key in load_keys(repo)] == [2]


def test_load_keys_reads_a_banded_corpus_directory(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    folder = repo / "datasets" / "triggers" / "decision-making"
    folder.mkdir()
    (folder / "index.yaml").write_text(V1.replace("version: 1", "version: 3"), encoding="utf-8")
    assert sorted(key.version for key in load_keys(repo)) == [2, 3]


def test_key_for_returns_none_when_a_case_is_missing(tmp_path: Path) -> None:
    keys = load_keys(_repo(tmp_path))
    assert key_for(keys, 2, {"p01"}) is not None
    assert key_for(keys, 2, {"p01", "x-n99"}) is None
    assert key_for(keys, 9, {"p01"}) is None


# --------------------------------------------------------------------------- #
# the per-file rules
# --------------------------------------------------------------------------- #


def _messages(repo: Path) -> list[str]:
    return [str(issue) for issue in check_checkpoints(repo)]


def test_an_unstamped_checkpoint_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", _v1_rows())
    assert "3 of 3 row(s) carry no `set_version`" in _messages(repo)[0]


def test_an_empty_checkpoint_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / CHECKPOINT_DIR / "verdicts.jsonl").write_text("", encoding="utf-8")
    assert _messages(repo) == ["verdicts.jsonl: is empty"]


def test_a_checkpoint_mixing_versions_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    rows = [*stamp(_v1_rows(), 1), *_v2_rows()]
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", rows)
    assert "mixes label revisions [1, 2]" in _messages(repo)[0]


def test_the_adjudication_ledger_is_not_a_checkpoint(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "adjudication.jsonl", [{"case": "p01"}])
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", _v2_rows())
    assert check_checkpoints(repo) == []


def test_a_rescored_row_in_the_run_directory_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    rows = [{**row, "record_kind": RESCORE_KIND} for row in _v2_rows()]
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", rows)
    assert "is named as a run and holds re-scored rows" in _messages(repo)[0]


# --------------------------------------------------------------------------- #
# the bridge
# --------------------------------------------------------------------------- #


def _unbridged(tmp_path: Path) -> Path:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", stamp(_v1_rows(), 1))
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts-new.jsonl", _v2_rows())
    return repo


def test_a_version_boundary_with_no_bridge_is_refused(tmp_path: Path) -> None:
    repo = _unbridged(tmp_path)
    assert "shares 3 case(s) with verdicts-new.jsonl at version 2" in _messages(repo)[0]


def test_checkpoints_that_share_no_cases_need_no_bridge(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(
        repo / CHECKPOINT_DIR / "verdicts.jsonl",
        [{**row, "case": f"other-{row['case']}", "set_version": 1} for row in _v1_rows()],
    )
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts-new.jsonl", _v2_rows())
    assert check_checkpoints(repo) == []


def test_a_bridge_without_the_rescore_marker_is_refused(tmp_path: Path) -> None:
    repo = _unbridged(tmp_path)
    reconcile(repo, {})
    path = repo / CHECKPOINT_DIR / "rescored-verdicts-v2.jsonl"
    write_jsonl(path, [{**row, "record_kind": "run"} for row in read_jsonl(path)])
    assert any("without `record_kind: 'rescore'`" in message for message in _messages(repo))


def test_a_bridge_naming_no_run_checkpoint_is_refused(tmp_path: Path) -> None:
    repo = _unbridged(tmp_path)
    reconcile(repo, {})
    path = repo / CHECKPOINT_DIR / "rescored-verdicts-v2.jsonl"
    write_jsonl(path, [{**row, "rescored_from": "ghost.jsonl"} for row in read_jsonl(path)])
    assert any("is not one run checkpoint" in message for message in _messages(repo))


def test_a_misnamed_bridge_is_refused(tmp_path: Path) -> None:
    repo = _unbridged(tmp_path)
    reconcile(repo, {})
    folder = repo / CHECKPOINT_DIR
    (folder / "rescored-verdicts-v2.jsonl").rename(folder / "rescored-verdicts-v9.jsonl")
    assert any("is not named rescored-verdicts-v2.jsonl" in m for m in _messages(repo))


def test_a_bridge_to_a_version_with_no_key_is_refused(tmp_path: Path) -> None:
    repo = _unbridged(tmp_path)
    reconcile(repo, {})
    folder = repo / CHECKPOINT_DIR
    rows = [{**row, "set_version": 7} for row in read_jsonl(folder / "rescored-verdicts-v2.jsonl")]
    (folder / "rescored-verdicts-v2.jsonl").unlink()
    write_jsonl(folder / "rescored-verdicts-v7.jsonl", rows)
    assert any("no trigger set on disk at that version" in message for message in _messages(repo))


def test_a_stale_bridge_is_refused(tmp_path: Path) -> None:
    repo = _unbridged(tmp_path)
    reconcile(repo, {})
    path = repo / CHECKPOINT_DIR / "rescored-verdicts-v2.jsonl"
    rows = read_jsonl(path)
    rows[1]["should_fire"] = True
    write_jsonl(path, rows)
    assert any("disagrees with decision-making v2 on 1 case(s)" in m for m in _messages(repo))


def test_an_unstamped_bridge_is_refused(tmp_path: Path) -> None:
    repo = _unbridged(tmp_path)
    reconcile(repo, {})
    path = repo / CHECKPOINT_DIR / "rescored-verdicts-v2.jsonl"
    rows = [
        {key: value for key, value in row.items() if key != "set_version"}
        for row in read_jsonl(path)
    ]
    write_jsonl(path, rows)
    assert any("carry no `set_version`" in message for message in _messages(repo))


# --------------------------------------------------------------------------- #
# reconcile
# --------------------------------------------------------------------------- #


def test_reconcile_stamps_and_bridges(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", _v1_rows())
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts-new.jsonl", _v2_rows())

    written = reconcile(repo, {"verdicts.jsonl": 1})

    assert written == [
        f"{CHECKPOINT_DIR}/verdicts.jsonl",
        f"{CHECKPOINT_DIR}/rescored-verdicts-v2.jsonl",
    ]
    assert check_checkpoints(repo) == []
    original = read_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl")
    assert {row["set_version"] for row in original} == {1}
    assert all(row["should_fire"] is True for row in original if row["case"] == "p02")


def test_reconcile_refuses_to_guess_a_version(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", _v1_rows())
    with pytest.raises(RescoreError, match="declares no `set_version` and none was supplied"):
        reconcile(repo, {})


def test_reconcile_refuses_a_bridge_it_has_no_key_for(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(
        repo / CHECKPOINT_DIR / "verdicts.jsonl",
        [{**row, "case": f"other-{row['case']}", "set_version": 1} for row in _v1_rows()],
    )
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts-new.jsonl", _v2_rows())
    with pytest.raises(RescoreError, match="cannot be bridged"):
        reconcile(repo, {})


def test_reconcile_ignores_the_adjudication_ledger(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "adjudication.jsonl", [{"case": "p01"}])
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", _v2_rows())
    assert reconcile(repo, {}) == []


def test_checkpoint_issue_reads_as_path_then_message() -> None:
    assert str(CheckpointIssue("verdicts.jsonl", "is empty")) == "verdicts.jsonl: is empty"


def test_write_jsonl_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "rows.jsonl"
    write_jsonl(path, [{"case": "p01"}])
    assert json.loads(path.read_text(encoding="utf-8")) == {"case": "p01"}


# --------------------------------------------------------------------------- #
# the register of pre-versioning checkpoints
# --------------------------------------------------------------------------- #


def test_declared_versions_are_empty_without_a_pyproject(tmp_path: Path) -> None:
    assert load_declared_versions(tmp_path) == {}


def test_declared_versions_are_empty_when_the_table_is_absent(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    assert load_declared_versions(tmp_path) == {}


def test_declared_versions_are_empty_when_the_path_is_not_a_table(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[tool]\n"decision-evals" = 1\n', encoding="utf-8")
    assert load_declared_versions(tmp_path) == {}


def test_declared_versions_read_the_register(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.decision-evals.unstamped-checkpoints]\n"verdicts.jsonl" = 1\n', encoding="utf-8"
    )
    assert load_declared_versions(tmp_path) == {"verdicts.jsonl": 1}


def test_the_repository_declares_a_version_for_every_unstamped_checkpoint() -> None:
    """The register covers what is on disk, or `de rescore` cannot run here.

    Not a tautology once the stamping has happened: it fails the moment a
    checkpoint arrives with no version and no derivation written down.
    """
    repo = Path(__file__).resolve().parents[2]
    declared = load_declared_versions(repo)
    for path in sorted((repo / CHECKPOINT_DIR).glob("*.jsonl")):
        if path.name in NOT_A_CHECKPOINT:
            continue
        rows = read_jsonl(path)
        if rows and all(row.get("set_version") is None for row in rows):
            assert path.name in declared


# --------------------------------------------------------------------------- #
# the gate, through the CLI
# --------------------------------------------------------------------------- #


def test_the_step_passes_a_reconciled_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _unbridged(tmp_path)
    reconcile(repo, {})
    monkeypatch.setattr(cli, "REPO_ROOT", repo)
    assert cli.check_checkpoints_step().passed


def test_the_step_fails_an_unreconciled_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "REPO_ROOT", _unbridged(tmp_path))
    result = cli.check_checkpoints_step()
    assert not result.passed
    assert "1 issue(s)" in result.detail


def test_the_repository_passes_its_own_checkpoint_gate() -> None:
    """No monkeypatching. The checkpoints on disk must satisfy the shipped gate."""
    assert cli.check_checkpoints_step().passed


def test_the_command_writes_the_bridges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _unbridged(tmp_path)
    monkeypatch.setattr(cli, "REPO_ROOT", repo)
    monkeypatch.setattr(cli, "load_declared_versions", lambda _: {})
    result = CliRunner().invoke(cli.app, ["rescore"])
    assert result.exit_code == 0
    assert "No model call was made." in result.stdout
    assert (repo / CHECKPOINT_DIR / "rescored-verdicts-v2.jsonl").is_file()


def test_the_command_refuses_to_guess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path)
    write_jsonl(repo / CHECKPOINT_DIR / "verdicts.jsonl", _v1_rows())
    monkeypatch.setattr(cli, "REPO_ROOT", repo)
    monkeypatch.setattr(cli, "load_declared_versions", lambda _: {})
    result = CliRunner().invoke(cli.app, ["rescore"])
    assert result.exit_code == 1
    assert "none was supplied" in result.stdout
