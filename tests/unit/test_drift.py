"""The review record, and how far a document's subject has moved without it.

This is the one gate here that refuses on reading rather than on a defect, so
what these tests pin down is mostly the shape of the refusal: which documents
are in scope, which are exempt by rule, and that the register may only shrink.

None of it proves a description is true. Nothing can.
"""

from __future__ import annotations

from pathlib import Path

from decision_evals.drift import (
    CEILING,
    DriftIssue,
    Movement,
    census,
    check_drift,
    dependencies,
    living_documents,
    load_reviewed,
    worklist,
)

SHA = "650dcbc"


def _repo(tmp_path: Path, files: dict[str, str], reviewed: dict[str, str] | None = None) -> Path:
    for relative, body in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    if reviewed is not None:
        rows = "\n".join(f'"{name}" = "{sha}"' for name, sha in reviewed.items())
        (tmp_path / "pyproject.toml").write_text(
            f"[tool.decision-evals.reviewed]\n{rows}\n", encoding="utf-8"
        )
    return tmp_path


def _moved(document: str, commits: int | None, paths: tuple[str, ...] = ("x.py",)) -> Movement:
    return Movement(document, SHA, commits, paths)


# --------------------------------------------------------------------------- #
# What a document depends on
# --------------------------------------------------------------------------- #


def test_a_document_depends_on_the_code_it_names(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "docs/ARCHITECTURE.md": (
                "It reads `evals/src/decision_evals/cli.py` and links to "
                "[the arms](../evals/src/decision_evals/solvers/arms.py).\n"
            ),
            "evals/src/decision_evals/cli.py": "",
            "evals/src/decision_evals/solvers/arms.py": "",
        },
    )
    assert dependencies(repo, repo / "docs/ARCHITECTURE.md") == (
        "evals/src/decision_evals/cli.py",
        "evals/src/decision_evals/solvers/arms.py",
    )


def test_another_document_is_not_a_dependency(tmp_path: Path) -> None:
    """An index linking to what it indexes is an index, not a stale description."""
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": "See [`STATUS.md`](STATUS.md) and `docs/VOICE.md`.\n",
            "docs/STATUS.md": "x",
            "docs/VOICE.md": "x",
        },
    )
    assert dependencies(repo, repo / "docs/README.md") == ()


def test_a_directory_is_a_place_and_not_a_dependency(tmp_path: Path) -> None:
    """Counting them put `docs/README.md` thirteen commits behind on other people's work."""
    repo = _repo(
        tmp_path,
        {
            "docs/ARCHITECTURE.md": "It reads `notebook/` and `evals/src/cli.py`.\n",
            "notebook/keep.txt": "",
            "evals/src/cli.py": "",
        },
    )
    assert dependencies(repo, repo / "docs/ARCHITECTURE.md") == ("evals/src/cli.py",)


def test_a_path_outside_the_repository_is_not_a_dependency(tmp_path: Path) -> None:
    """`.venv` exists on a laptop and never in CI, so counting it splits the two."""
    repo = _repo(
        tmp_path,
        {
            "docs/ARCHITECTURE.md": (
                "Invoke `.venv/Scripts/de.exe` and read `evals/src/cli.py`.\n"
            ),
            ".venv/Scripts/de.exe": "",
            "evals/src/cli.py": "",
        },
    )
    assert dependencies(repo, repo / "docs/ARCHITECTURE.md") == ("evals/src/cli.py",)


def test_a_path_that_does_not_exist_is_not_a_dependency(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "It reads `evals/gone.py`.\n"})
    (repo / "evals").mkdir()
    assert dependencies(repo, repo / "README.md") == ()


def test_a_link_leaving_the_repository_is_skipped(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "See [elsewhere](../outside.py).\n"})
    (tmp_path.parent / "outside.py").write_text("", encoding="utf-8")
    assert dependencies(repo, repo / "README.md") == ()


def test_a_document_does_not_depend_on_itself(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"scripts/notes.md": "`scripts/notes.md` is this file.\n"})
    assert dependencies(repo, repo / "scripts/notes.md") == ()


# --------------------------------------------------------------------------- #
# Who is in scope
# --------------------------------------------------------------------------- #


def test_generated_documents_are_exempt_by_rule(tmp_path: Path) -> None:
    """Reviewing a generated document means reviewing its generator, which is code."""
    repo = _repo(
        tmp_path,
        {
            "README.md": "x",
            "CLAUDE.md": "x",
            "AGENTS.md": "x",
            "docs/RUN_INDEX.md": "x",
            "docs/STATUS.md": "x",
        },
    )
    assert living_documents(repo) == {"README.md", "AGENTS.md", "docs/STATUS.md"}


def test_no_register_is_no_reviews(tmp_path: Path) -> None:
    assert load_reviewed(tmp_path) == {}


def test_the_census_counts_what_is_covered(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {"README.md": "x", "docs/STATUS.md": "x"},
        reviewed={"README.md": SHA},
    )
    assert census(repo) == (2, 1)


# --------------------------------------------------------------------------- #
# Refusing
# --------------------------------------------------------------------------- #


def test_a_document_with_no_review_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "x", "docs/STATUS.md": "x"}, reviewed={"README.md": SHA})
    issues = check_drift(repo, {})
    assert [issue.where for issue in issues] == ["docs/STATUS.md"]
    assert "no review on record" in issues[0].message


def test_a_review_of_nothing_is_refused(tmp_path: Path) -> None:
    """Shrink-only, the same discipline as `unwired` and `docs-absent-commands`."""
    repo = _repo(tmp_path, {"README.md": "x"}, reviewed={"README.md": SHA, "docs/GONE.md": SHA})
    issues = check_drift(repo, {})
    assert [issue.where for issue in issues] == ["pyproject.toml"]
    assert "may only shrink" in issues[0].message


def test_a_review_at_a_commit_git_does_not_know_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "x"}, reviewed={"README.md": SHA})
    issues = check_drift(repo, {"README.md": _moved("README.md", None)})
    assert [issue.where for issue in issues] == ["pyproject.toml"]
    assert "git does not know" in issues[0].message


def test_a_document_past_the_ceiling_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "x"}, reviewed={"README.md": SHA})
    movement = _moved("README.md", CEILING + 1, ("a.py", "b.py"))
    issues = check_drift(repo, {"README.md": movement})
    assert [issue.where for issue in issues] == ["README.md"]
    assert f"{CEILING + 1} commit(s)" in issues[0].message
    assert "git log 650dcbc..HEAD -- a.py b.py" in issues[0].message


def test_a_document_at_the_ceiling_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "x"}, reviewed={"README.md": SHA})
    assert check_drift(repo, {"README.md": _moved("README.md", CEILING)}) == []


def test_a_document_with_no_movement_recorded_is_not_guessed_at(tmp_path: Path) -> None:
    """Git unavailable is a no-op, not a refusal, so a source tarball still passes."""
    repo = _repo(tmp_path, {"README.md": "x"}, reviewed={"README.md": SHA})
    assert check_drift(repo, {}) == []


def test_the_ceiling_can_be_tightened(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "x"}, reviewed={"README.md": SHA})
    assert check_drift(repo, {"README.md": _moved("README.md", 2)}, ceiling=1)


# --------------------------------------------------------------------------- #
# The worklist
# --------------------------------------------------------------------------- #


def test_the_worklist_puts_the_furthest_behind_first() -> None:
    movements = {
        "a.md": _moved("a.md", 3),
        "b.md": _moved("b.md", 0),
        "c.md": _moved("c.md", 9),
        "d.md": _moved("d.md", None),
    }
    assert [movement.document for movement in worklist(movements)] == ["c.md", "a.md", "d.md"]


def test_an_issue_reads_as_one_line() -> None:
    assert str(DriftIssue("README.md", "is stale")) == "README.md: is stale"
