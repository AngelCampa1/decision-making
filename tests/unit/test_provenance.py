"""The run-provenance gate.

The cases that matter are the ones the real failures took. A suite proving that
a missing README is caught would pass while missing every defect this gate was
built for: a prediction written after its run, a README claiming one answer key
beside records stamped with another, and a baseline that quietly stopped
shrinking.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from decision_evals.provenance import (
    BASELINE_PATH,
    INDEX_PATH,
    GitFacts,
    ProvenanceError,
    ProvenanceIssue,
    census,
    check_provenance,
    check_run,
    discover_runs,
    index_is_current,
    load_baseline,
    outcome_links,
    prediction_links,
    record_versions,
    render_index,
)

_STAMP = (
    "**Answer key:** [`datasets/triggers/decision-making.yaml`]"
    "(../../../datasets/triggers/decision-making.yaml) **v1**.\n"
)
_PREDICTION = "Prediction: [`notebook/2026-08-12-a-prediction.md`](../../../notebook/2026-08-12-a-prediction.md).\n"

_NO_GIT = GitFacts(available=False, first_commit={}, ancestry=frozenset())


def _repo(
    tmp_path: Path,
    *,
    run: str = "2026-08-12-abc1234-arm",
    readme: str | None = None,
    records: list[dict[str, object]] | None = None,
    prediction: str | None = "notebook/2026-08-12-a-prediction.md",
) -> Path:
    """A minimal repository containing one published run."""
    run_dir = tmp_path / "results" / "decision-making" / run
    run_dir.mkdir(parents=True)
    if readme is not None:
        (run_dir / "README.md").write_text(readme, encoding="utf-8")
    if records is not None:
        (run_dir / "verdicts.jsonl").write_text(
            "\n".join(json.dumps(row) for row in records), encoding="utf-8"
        )
    if prediction is not None:
        note = tmp_path / prediction
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# a prediction\n", encoding="utf-8")
    return tmp_path


def _issues(repo: Path, git: GitFacts = _NO_GIT) -> list[str]:
    return [issue.message for issue in check_provenance(repo, git)]


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #


def test_runs_are_discovered_by_position_not_by_contents(tmp_path: Path) -> None:
    """A run cannot escape the gate by omitting the file the gate checks."""
    repo = _repo(tmp_path, readme=None, prediction=None)
    found = discover_runs(repo)
    assert [run.name for run in found] == ["2026-08-12-abc1234-arm"]
    assert not found[0].readme.is_file()


def test_no_results_directory_yields_no_runs(tmp_path: Path) -> None:
    assert discover_runs(tmp_path) == []


def test_run_exposes_the_commit_in_its_name(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert discover_runs(repo)[0].commit == "abc1234"


def test_a_malformed_name_has_no_commit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, run="baseline-corpus")
    assert discover_runs(repo)[0].commit is None


# --------------------------------------------------------------------------- #
# Shape
# --------------------------------------------------------------------------- #


def test_a_run_without_a_readme_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=None)
    assert any("no README.md" in message for message in _issues(repo))


def test_a_name_without_a_commit_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, run="2026-08-12-arm", readme=_STAMP + _PREDICTION)
    assert any("must be `<YYYY-MM-DD>-<sha7>" in message for message in _issues(repo))


def test_a_well_formed_run_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    assert _issues(repo) == []


def test_a_slugless_name_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, run="2026-08-12-abc1234", readme=_STAMP + _PREDICTION)
    assert _issues(repo) == []


# --------------------------------------------------------------------------- #
# The answer key: prose bound to data
# --------------------------------------------------------------------------- #


def test_a_readme_without_an_answer_key_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_PREDICTION)
    assert any("`**Answer key:**`" in message for message in _issues(repo))


def test_records_stamped_with_another_version_are_refused(tmp_path: Path) -> None:
    """The defect of 2026-08-13: prose and data disagreeing about the labels."""
    repo = _repo(
        tmp_path,
        readme=_STAMP + _PREDICTION,
        records=[{"case": "p01", "set_version": 2}],
    )
    assert any("carries [2]" in message for message in _issues(repo))


def test_records_without_a_version_are_read_as_v1(tmp_path: Path) -> None:
    """Matches ``label_versions_comparable``; the two must agree."""
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION, records=[{"case": "p01"}])
    assert _issues(repo) == []


def test_matching_versions_pass(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        readme=_STAMP + _PREDICTION,
        records=[{"case": "p01", "set_version": 1}],
    )
    assert _issues(repo) == []


def test_unparseable_and_blank_lines_are_skipped(tmp_path: Path) -> None:
    """A malformed record must not hide the version mismatch beside it."""
    path = tmp_path / "verdicts.jsonl"
    path.write_text('\n{"set_version": 2}\nnot json\n[1, 2]\n', encoding="utf-8")
    assert record_versions(path) == {2}


def test_an_unreadable_records_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ProvenanceError):
        record_versions(tmp_path / "missing.jsonl")


def test_a_non_integer_version_is_ignored(tmp_path: Path) -> None:
    """A string version is a malformed record, not a second revision.

    Treating ``"2"`` as version 2 would let a stringly-typed field trip the
    mismatch rule; treating it as absent leaves the defect to the schema check
    that owns it.
    """
    path = tmp_path / "verdicts.jsonl"
    path.write_text('{"set_version": "2"}\n{"set_version": 1}\n', encoding="utf-8")
    assert record_versions(path) == {1}


def test_an_issue_renders_as_run_then_message() -> None:
    assert str(ProvenanceIssue("results/x", "broken")) == "results/x: broken"


# --------------------------------------------------------------------------- #
# The prediction, and the commit graph that dates it
# --------------------------------------------------------------------------- #


def test_only_the_labelled_prediction_line_counts() -> None:
    """A passing citation is not a registration.

    Reading the first notebook link instead would pass a run that never
    registered anything — wrong in the direction that matters.
    """
    text = "see [notebook/2026-08-12-other.md](x)\n" + _PREDICTION
    assert prediction_links(text) == ["notebook/2026-08-12-a-prediction.md"]


def test_a_run_without_a_prediction_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP)
    assert any("no `Prediction:` line" in message for message in _issues(repo))


def test_a_prediction_that_does_not_exist_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION, prediction=None)
    assert any("does not exist" in message for message in _issues(repo))


def test_an_uncommitted_prediction_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    git = GitFacts(available=True, first_commit={}, ancestry=frozenset())
    assert any("is not committed" in message for message in _issues(repo, git))


def test_a_prediction_that_postdates_its_run_is_refused(tmp_path: Path) -> None:
    """The second recorded slip: an entry written after its run had started."""
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    git = GitFacts(
        available=True,
        first_commit={"notebook/2026-08-12-a-prediction.md": "def5678"},
        ancestry=frozenset(),
    )
    assert any("does not predate the run" in message for message in _issues(repo, git))


def test_a_prediction_committed_with_its_run_passes(tmp_path: Path) -> None:
    """A commit is its own ancestor: registering in the running commit is fine."""
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    git = GitFacts(
        available=True,
        first_commit={"notebook/2026-08-12-a-prediction.md": "abc1234"},
        ancestry=frozenset({("abc1234", "abc1234")}),
    )
    assert _issues(repo, git) == []


def test_without_git_the_commit_rule_is_skipped(tmp_path: Path) -> None:
    """A source tarball is not a defective run record."""
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    assert _issues(repo) == []


def test_a_malformed_name_skips_the_commit_rule(tmp_path: Path) -> None:
    """The name defect is already reported; it must not also fire as a git one."""
    repo = _repo(tmp_path, run="2026-08-12-arm", readme=_STAMP + _PREDICTION)
    git = GitFacts(available=True, first_commit={}, ancestry=frozenset())
    messages = _issues(repo, git)
    assert not any("is not committed" in message for message in messages)


# --------------------------------------------------------------------------- #
# Dead links
# --------------------------------------------------------------------------- #


def test_a_dead_notebook_link_is_refused(tmp_path: Path) -> None:
    readme = _STAMP + _PREDICTION + "Outcome: [x](../../../notebook/2026-08-12-gone.md).\n"
    repo = _repo(tmp_path, readme=readme)
    assert any("2026-08-12-gone.md" in message for message in _issues(repo))


# --------------------------------------------------------------------------- #
# The baseline, which may only shrink
# --------------------------------------------------------------------------- #


def test_a_baselined_run_is_exempt(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=None)
    (repo / BASELINE_PATH).parent.mkdir(parents=True, exist_ok=True)
    (repo / BASELINE_PATH).write_text("# why\n2026-08-12-abc1234-arm\n", encoding="utf-8")
    assert _issues(repo) == []


def test_a_stale_baseline_entry_is_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    (repo / BASELINE_PATH).write_text("2026-08-12-abc1234-arm\n", encoding="utf-8")
    assert any("has no outstanding issue" in message for message in _issues(repo))


def test_a_baseline_entry_naming_no_run_is_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    (repo / BASELINE_PATH).write_text("2026-01-01-deleted\n", encoding="utf-8")
    assert any("names no run directory" in message for message in _issues(repo))


def test_a_missing_baseline_file_is_an_empty_baseline(tmp_path: Path) -> None:
    assert load_baseline(tmp_path) == set()


def test_census_counts_runs_and_baselined(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    (repo / BASELINE_PATH).write_text("# comment only\n\n", encoding="utf-8")
    assert census(repo) == (1, 0)


# --------------------------------------------------------------------------- #
# The generated index
# --------------------------------------------------------------------------- #


def test_the_index_links_notebook_entries_back_to_their_run(tmp_path: Path) -> None:
    """The direction nobody could travel before: finding to data."""
    readme = _STAMP + _PREDICTION + "Outcome: [x](../../../notebook/2026-08-12-a-prediction.md).\n"
    repo = _repo(tmp_path, readme=readme)
    rendered = render_index(repo)
    assert "## Notebook entry to run" in rendered
    assert "2026-08-12-a-prediction.md" in rendered.split("## Notebook entry to run")[1]


def test_the_index_marks_baselined_runs(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    (repo / BASELINE_PATH).write_text("2026-08-12-abc1234-arm\n", encoding="utf-8")
    assert "*(baselined)*" in render_index(repo)


def test_the_index_names_a_run_with_no_prediction(tmp_path: Path) -> None:
    """A gap has to be visible in the index, not absent from it."""
    repo = _repo(tmp_path, readme=_STAMP)
    assert "**none**" in render_index(repo)


def test_the_index_handles_a_run_with_no_readme(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=None, prediction=None)
    assert "—" in render_index(repo)


def test_a_missing_index_is_not_current(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    assert not index_is_current(repo)


def test_a_written_index_is_current(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    path = repo / INDEX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_index(repo), encoding="utf-8", newline="\n")
    assert index_is_current(repo)


def test_a_stale_index_is_detected(tmp_path: Path) -> None:
    repo = _repo(tmp_path, readme=_STAMP + _PREDICTION)
    path = repo / INDEX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Run index\n", encoding="utf-8")
    assert not index_is_current(repo)


def test_outcome_and_write_up_both_count() -> None:
    assert outcome_links("Outcome: [a](x/notebook/2026-01-01-a.md).\n") == [
        "notebook/2026-01-01-a.md"
    ]
    assert outcome_links("Write-up: [b](x/notebook/2026-01-01-b.md).\n") == [
        "notebook/2026-01-01-b.md"
    ]


# --------------------------------------------------------------------------- #
# The real repository
# --------------------------------------------------------------------------- #


def test_the_committed_index_is_current() -> None:
    """A run published without appearing in the index is a failing build."""
    assert index_is_current(Path(__file__).resolve().parents[2])


def test_the_repository_passes_its_own_gate() -> None:
    """The gate is only worth having if it holds on the tree it ships with."""
    repo_root = Path(__file__).resolve().parents[2]
    assert check_provenance(repo_root, _NO_GIT) == []


def test_every_published_run_is_checked(tmp_path: Path) -> None:
    """check_run is total: it returns a list for any directory shape."""
    repo = _repo(tmp_path, readme=None, prediction=None)
    assert isinstance(check_run(discover_runs(repo)[0], repo, _NO_GIT), list)
