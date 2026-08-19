"""The decision register.

The rule is a coupling: a change to the answer key or to the shipped skill
obliges an entry. What these tests pin down is that the coupling holds in both
directions — an unexplained commit fails, and an entry naming a commit that
touched nothing governed fails too, because a register that accumulates
untethered prose stops being checkable.
"""

from __future__ import annotations

from pathlib import Path

from decision_evals.decisions import (
    BASELINE_PATH,
    REGISTER_PATH,
    DecisionIssue,
    GovernedCommit,
    census,
    check_decisions,
    load_baseline,
    parse_register,
    touches_governed,
)

_COMMIT = GovernedCommit(sha="d43c490", date="2026-08-13", subject="four label decisions")

_ENTRY = """# Decision register

Prose above the first heading is not an entry.

## 2026-08-13 — four label decisions

**Commits:** `d43c490`

x-n21 moves to the negatives because the question has an obvious answer.
"""


def _repo(tmp_path: Path, register: str | None = _ENTRY) -> Path:
    if register is not None:
        path = tmp_path / REGISTER_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(register, encoding="utf-8")
    return tmp_path


def _messages(repo: Path, governed: list[GovernedCommit]) -> list[str]:
    return [issue.message for issue in check_decisions(repo, governed)]


# --------------------------------------------------------------------------- #
# What obliges an entry
# --------------------------------------------------------------------------- #


def test_the_answer_key_is_governed() -> None:
    assert touches_governed(["datasets/triggers/decision-making.yaml"])


def test_the_shipped_skill_is_governed() -> None:
    assert touches_governed(["skills/decision-making/SKILL.md"])


def test_ordinary_paths_are_not_governed() -> None:
    assert not touches_governed(["evals/src/decision_evals/cli.py", "notebook/x.md"])


def test_a_mixed_changeset_is_governed() -> None:
    assert touches_governed(["README.md", "skills/decision-making/SKILL.md"])


def test_the_tailoring_corpus_is_governed() -> None:
    """Track H's Phase 0 corpus carries labels (governing vs. matched
    non-governing), which is an answer key in exactly the sense this register
    exists for — see docs/DECISIONS.md, 2026-08-19. A change under
    datasets/tailoring/ must now be refused without an entry, the same as one
    under datasets/triggers/."""
    assert touches_governed(["datasets/tailoring/tri-001.yaml"])


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


def test_prose_above_the_first_heading_is_not_an_entry() -> None:
    entries = parse_register(_ENTRY)
    assert len(entries) == 1
    assert entries[0].title == "four label decisions"
    assert entries[0].commits == ("d43c490",)


def test_an_entry_body_excludes_the_commits_line() -> None:
    assert "Commits" not in parse_register(_ENTRY)[0].body


def test_several_commits_on_one_line_all_parse() -> None:
    text = "## 2026-08-13 — x\n\n**Commits:** `d43c490`, `903169c`\n\nwhy\n"
    assert parse_register(text)[0].commits == ("d43c490", "903169c")


def test_an_empty_register_has_no_entries() -> None:
    assert parse_register("# Decision register\n\nnothing yet.\n") == []


# --------------------------------------------------------------------------- #
# The rule
# --------------------------------------------------------------------------- #


def test_an_explained_commit_passes(tmp_path: Path) -> None:
    assert _messages(_repo(tmp_path), [_COMMIT]) == []


def test_an_unexplained_commit_is_refused(tmp_path: Path) -> None:
    """The 2026-08-13 failure: a label move with its reasoning only in a commit."""
    other = GovernedCommit(sha="fffa4a2", date="2026-08-13", subject="the turns were too short")
    assert any("no entry in" in message for message in _messages(_repo(tmp_path), [_COMMIT, other]))


def test_a_missing_register_is_refused(tmp_path: Path) -> None:
    assert any(
        "register is missing" in message for message in _messages(_repo(tmp_path, None), [_COMMIT])
    )


def test_an_entry_naming_an_ungoverned_commit_is_refused(tmp_path: Path) -> None:
    """A register that accumulates untethered prose stops being checkable."""
    assert any("not a commit that touched" in message for message in _messages(_repo(tmp_path), []))


def test_an_entry_without_commits_is_refused(tmp_path: Path) -> None:
    register = "## 2026-08-13 — x\n\nwhy but no commits line\n"
    assert any(
        "no `**Commits:**` line" in message
        for message in _messages(_repo(tmp_path, register), [_COMMIT])
    )


def test_an_entry_without_a_body_is_refused(tmp_path: Path) -> None:
    register = "## 2026-08-13 — x\n\n**Commits:** `d43c490`\n"
    assert any(
        "has no body" in message for message in _messages(_repo(tmp_path, register), [_COMMIT])
    )


# --------------------------------------------------------------------------- #
# The baseline
# --------------------------------------------------------------------------- #


def test_a_baselined_commit_is_exempt(tmp_path: Path) -> None:
    other = GovernedCommit(sha="fffa4a2", date="2026-08-13", subject="x")
    repo = _repo(tmp_path)
    (repo / BASELINE_PATH).write_text("# why\nfffa4a2\n", encoding="utf-8")
    assert _messages(repo, [_COMMIT, other]) == []


def test_a_baseline_entry_for_an_ungoverned_commit_is_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / BASELINE_PATH).write_text("aaaaaaa\n", encoding="utf-8")
    assert any("touched no governed path" in message for message in _messages(repo, [_COMMIT]))


def test_a_commit_both_baselined_and_explained_is_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / BASELINE_PATH).write_text("d43c490\n", encoding="utf-8")
    assert any("baselined and also explained" in message for message in _messages(repo, [_COMMIT]))


def test_a_missing_baseline_file_is_empty(tmp_path: Path) -> None:
    assert load_baseline(tmp_path) == set()


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def test_an_issue_renders_as_where_then_message() -> None:
    assert str(DecisionIssue("d43c490", "unexplained")) == "d43c490: unexplained"


def test_census_counts_commits_entries_and_baselined(tmp_path: Path) -> None:
    assert census(_repo(tmp_path), [_COMMIT]) == (1, 1, 0)


def test_census_without_a_register(tmp_path: Path) -> None:
    assert census(_repo(tmp_path, None), []) == (0, 0, 0)


# --------------------------------------------------------------------------- #
# The real repository
# --------------------------------------------------------------------------- #


def test_every_governed_commit_in_this_repository_is_explained() -> None:
    from decision_evals.cli import REPO_ROOT, _governed_commits

    governed = _governed_commits()
    assert governed, "expected the real history to contain governed commits"
    assert check_decisions(REPO_ROOT, governed) == []
