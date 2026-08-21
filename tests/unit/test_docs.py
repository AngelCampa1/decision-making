"""The documentation gate.

The failure this guards is the one every other integrity rule here already had
a gate for. On 2026-08-13 the README told readers to run ``de screen`` and
``de confirm``, neither a command, and advertised a ``preregistration/``
directory that has never existed, while omitting ``paper/`` and ``scripts/``.
``SCORECARD.md`` had already corrected a fourth of the same shape, ``de
report``. Four instances, one file each, none caught by anything.

Two tests exist because the first implementation was wrong in ways that read as
plausible. Resolving a backticked repository path against the *linking file*
rather than the repository root reported every correct path in ``docs/`` as
broken — 40 confident false positives. And scanning ``docs/DECISIONS.md``
demanded an edit to a dated register whose entry for ``8541d46`` names the file
that commit deleted, which is correct history.
"""

from __future__ import annotations

from pathlib import Path

from decision_evals.docs import (
    DocIssue,
    census,
    check_audience_lines,
    check_command_references,
    check_component_table,
    check_docs,
    check_docs_index,
    check_path_references,
    code_fragments,
    component_entries,
    index_entries,
    link_targets,
    linked_paths,
    load_absent_commands,
    load_external_paths,
    load_ignored_paths,
    repo_paths,
    scanned_files,
)

COMMANDS = {"check", "index", "mirror"}


def _repo(tmp_path: Path, files: dict[str, str], dirs: tuple[str, ...] = ()) -> Path:
    """A repository with documentation files and top-level directories."""
    for relative, body in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    for name in dirs:
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    return tmp_path


AUDIENCE = "**Audience:** the evaluating reader."


def _index(entries: tuple[str, ...] = (), extra: str = "") -> str:
    """A ``docs/README.md`` listing the documents beside it."""
    rows = "\n".join(f"| [`{name}`]({name}) | answers something |" for name in entries)
    return (
        f"# Documentation index\n\n{AUDIENCE}\n\n"
        f"| Document | Answers |\n| --- | --- |\n{rows}\n\n{extra}"
    )


def _readme(components: tuple[str, ...] = (), extra: str = "") -> str:
    rows = "\n".join(f"| `{name}/` | purpose |" for name in components)
    return (
        "# title\n\n"
        f"{AUDIENCE}\n\n"
        "## What's actually here\n\n"
        "| Component | Purpose |\n| --- | --- |\n"
        f"{rows}\n\n{extra}"
    )


# --------------------------------------------------------------------------- #
# Which files are read
# --------------------------------------------------------------------------- #


def test_scans_the_root_and_docs_but_not_the_notebook(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": "x",
            "docs/PROTOCOL.md": "x",
            "notebook/2026-08-11-an-entry.md": "`de report` was fine then",
            "results/decision-making/run/README.md": "x",
        },
    )
    names = [path.name for path in scanned_files(repo)]
    assert names == ["README.md", "PROTOCOL.md"]


def test_the_decision_register_is_excluded(tmp_path: Path) -> None:
    """A decision that removed a file necessarily names the file it removed."""
    repo = _repo(
        tmp_path,
        {
            "docs/DECISIONS.md": "`datasets/triggers/evidence-ledger.yaml` was deleted",
            "docs/STATUS.md": "x",
        },
        dirs=("datasets",),
    )
    assert [path.name for path in scanned_files(repo)] == ["STATUS.md"]
    assert check_path_references(repo) == []


def test_a_directory_named_like_a_document_is_not_read(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "x"}, dirs=("weird.md",))
    assert [path.name for path in scanned_files(repo)] == ["README.md"]


# --------------------------------------------------------------------------- #
# Code fragments
# --------------------------------------------------------------------------- #


def test_reads_both_inline_spans_and_fenced_blocks() -> None:
    text = "Run `de check` first.\n\n```bash\nuv run de index\n```\n"
    fragments = code_fragments(text)
    assert "uv run de index\n" in fragments
    assert "de check" in fragments


def test_a_fenced_block_is_not_also_read_as_inline_spans() -> None:
    """Backticks inside a fence would otherwise be re-parsed as span delimiters."""
    assert code_fragments("```\na `b` c\n```\n") == ["a `b` c\n"]


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def test_a_real_command_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme(extra="Run `uv run de check`.")})
    assert check_command_references(repo, COMMANDS) == []


def test_a_command_that_does_not_exist_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme(extra="Run `de confirm`.")})
    issues = check_command_references(repo, COMMANDS)
    assert [issue.where for issue in issues] == ["README.md"]
    assert "`de confirm` is not a command" in issues[0].message


def test_the_same_bad_command_twice_in_one_file_reports_once(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme(extra="`de confirm` and `de confirm`.")})
    assert len(check_command_references(repo, COMMANDS)) == 1


def test_a_declared_absent_command_may_be_named(tmp_path: Path) -> None:
    """`SCORECARD.md` has to be able to say that `de report` never existed."""
    repo = _repo(
        tmp_path,
        {
            "README.md": _readme(extra="There is no `de report`."),
            "pyproject.toml": '[tool.decision-evals.docs-absent-commands]\n"report" = "never built"\n',
        },
    )
    assert check_command_references(repo, COMMANDS) == []


def test_a_declared_absent_command_that_becomes_real_is_refused(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": _readme(extra="Run `de index`."),
            "pyproject.toml": '[tool.decision-evals.docs-absent-commands]\n"index" = "not built"\n',
        },
    )
    issues = check_command_references(repo, COMMANDS)
    assert issues == [
        DocIssue(
            "pyproject.toml",
            "`de index` is declared absent and is now a real command. Delete the entry "
            "— a note that outlives the situation it describes is how the last two "
            "dead integrity modules stayed invisible.",
        )
    ]


def test_a_declared_absent_command_nobody_mentions_is_refused(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": _readme(),
            "pyproject.toml": '[tool.decision-evals.docs-absent-commands]\n"ghost" = "why"\n',
        },
    )
    issues = check_command_references(repo, COMMANDS)
    assert "named nowhere in the documentation" in issues[0].message


# --------------------------------------------------------------------------- #
# The absent register
# --------------------------------------------------------------------------- #


def test_no_pyproject_means_no_declarations(tmp_path: Path) -> None:
    assert load_absent_commands(tmp_path) == {}


def test_a_non_table_on_the_way_down_is_tolerated(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"pyproject.toml": 'tool = "not a table"\n'})
    assert load_absent_commands(repo) == {}


def test_a_non_table_at_the_leaf_is_tolerated(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {"pyproject.toml": '[tool.decision-evals]\ndocs-absent-commands = "nope"\n'},
    )
    assert load_absent_commands(repo) == {}


# --------------------------------------------------------------------------- #
# The external-paths register
#
# `repo_paths` resolves any backticked fragment whose first segment is a real
# top-level directory against this root. `docs/DECISION_FRAMEWORKS.md` reviews a
# prompt library that keeps twenty files in `.claude/commands/`; `.claude/` is a
# directory here and that one is not, so a true sentence about another project's
# layout was reported as a broken link.
# --------------------------------------------------------------------------- #

CLAUDE_COMMANDS_EXTERNAL = """[tool.decision-evals.docs-external-paths]
".claude/commands/" = "another repository"
"""


def test_an_external_path_may_be_named(tmp_path: Path) -> None:
    """A path inside another repository is not a broken reference in this one."""
    repo = _repo(
        tmp_path,
        {
            "README.md": _readme(extra="It keeps 20 files in `.claude/commands/`."),
            "pyproject.toml": CLAUDE_COMMANDS_EXTERNAL,
        },
        dirs=(".claude",),
    )
    assert check_path_references(repo) == []


def test_an_external_path_that_now_exists_here_is_refused(tmp_path: Path) -> None:
    """An excuse that outlives its situation stops a real reference being checked."""
    repo = _repo(
        tmp_path,
        {
            "README.md": _readme(extra="See `.claude/commands/`."),
            "pyproject.toml": CLAUDE_COMMANDS_EXTERNAL,
        },
        dirs=(".claude/commands",),
    )
    assert check_path_references(repo) == [
        DocIssue(
            "pyproject.toml",
            "`.claude/commands/` is declared external and now exists here. Delete "
            "the entry — an excuse that outlives the situation it describes "
            "stops a real reference from being checked.",
        )
    ]


def test_an_external_path_nobody_mentions_is_refused(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {"README.md": _readme(), "pyproject.toml": CLAUDE_COMMANDS_EXTERNAL},
        dirs=(".claude",),
    )
    issues = check_path_references(repo)
    assert "named nowhere in the documentation" in issues[0].message


def test_the_register_does_not_excuse_a_markdown_link(tmp_path: Path) -> None:
    """A link is an offer to follow it; a cross-repo one is written as a URL."""
    repo = _repo(
        tmp_path,
        {
            "README.md": _readme(
                extra="`.claude/commands/` there, and [commands](.claude/commands/) here."
            ),
            "pyproject.toml": CLAUDE_COMMANDS_EXTERNAL,
        },
        dirs=(".claude",),
    )
    issues = check_path_references(repo)
    assert len(issues) == 1
    assert "`.claude/commands/` does not exist" in issues[0].message


def test_no_pyproject_means_no_external_paths(tmp_path: Path) -> None:
    assert load_external_paths(tmp_path) == {}


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #


def test_absolute_and_anchor_links_are_not_paths() -> None:
    text = "[a](https://example.com) [b](#section) [c](mailto:x@y.z) [d](docs/STATUS.md)"
    assert link_targets(text) == {"docs/STATUS.md"}


def test_a_link_resolves_against_the_linking_file(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"docs/A.md": "[b](B.md)", "docs/B.md": "x"})
    assert check_path_references(repo) == []


def test_a_backticked_repo_path_resolves_against_the_root(tmp_path: Path) -> None:
    """Resolving this against `docs/` is the bug that produced 40 false positives."""
    repo = _repo(tmp_path, {"docs/A.md": "see `skills/decision-making/`"}, dirs=("skills",))
    (repo / "skills" / "decision-making").mkdir()
    assert check_path_references(repo) == []


def test_a_link_that_does_not_resolve_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"docs/A.md": "[b](GONE.md)"})
    issues = check_path_references(repo)
    assert "`GONE.md` does not exist" in issues[0].message


def test_an_anchor_is_stripped_before_resolving(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"docs/A.md": "[b](B.md#part)", "docs/B.md": "x"})
    assert check_path_references(repo) == []


def test_only_paths_under_a_real_top_level_directory_are_resolved() -> None:
    top = {"docs", "skills"}
    assert repo_paths(["decision_evals.triggers"], top) == set()
    assert repo_paths(["vendor/thing.yaml"], top) == set()
    assert repo_paths(["docs/STATUS.md"], top) == {"docs/STATUS.md"}


def test_illustrative_paths_are_not_resolved() -> None:
    top = {"results"}
    assert repo_paths(["results/<skill>/<date>/README.md"], top) == set()
    assert repo_paths(["results/**/summary.json"], top) == set()
    assert repo_paths(["uv run de check"], top) == set()


# --------------------------------------------------------------------------- #
# The untracked-path register
# --------------------------------------------------------------------------- #


def test_a_declared_untracked_path_may_be_named(tmp_path: Path) -> None:
    """`docs/STATUS.md` has to name the checkpoint its claim rests on.

    `.gitignore` excludes `results/triggers/` because an append-only run file
    cannot be committed mid-run, so the reference cannot resolve on a clean
    clone and the gate was right to refuse it before this register existed.
    """
    repo = _repo(
        tmp_path,
        {
            "docs/A.md": "adjudicated into `results/triggers/adjudication.jsonl`.",
            "pyproject.toml": (
                "[tool.decision-evals.docs-ignored-paths]\n"
                '"results/triggers/adjudication.jsonl" = "append-only, ignored"\n'
            ),
        },
        dirs=("results",),
    )
    assert check_path_references(repo) == []


def test_a_declared_untracked_path_nobody_mentions_is_refused(tmp_path: Path) -> None:
    """The register may only shrink, same as the absent-command one."""
    repo = _repo(
        tmp_path,
        {
            "docs/A.md": "nothing to see",
            "pyproject.toml": (
                '[tool.decision-evals.docs-ignored-paths]\n"results/gone.jsonl" = "why"\n'
            ),
        },
        dirs=("results",),
    )
    issues = check_path_references(repo)
    assert issues == [
        DocIssue(
            "pyproject.toml",
            "`results/gone.jsonl` is declared untracked and is named nowhere in the "
            "documentation. Delete the line.",
        )
    ]


def test_an_undeclared_missing_path_still_names_the_register(tmp_path: Path) -> None:
    """The refusal has to say how to declare a deliberate absence."""
    repo = _repo(tmp_path, {"docs/A.md": "[b](GONE.md)"})
    issues = check_path_references(repo)
    assert "docs-ignored-paths" in issues[0].message


def test_no_pyproject_means_no_untracked_declarations(tmp_path: Path) -> None:
    assert load_ignored_paths(tmp_path) == {}


# --------------------------------------------------------------------------- #
# The component table
# --------------------------------------------------------------------------- #


def test_a_table_matching_the_tree_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme(("docs", "skills"))}, dirs=("docs", "skills"))
    assert check_component_table(repo) == []


def test_a_listed_component_that_does_not_exist_is_refused(tmp_path: Path) -> None:
    """The defect the check was written for."""
    repo = _repo(
        tmp_path,
        {"README.md": _readme(("docs", "preregistration"))},
        dirs=("docs",),
    )
    issues = check_component_table(repo)
    assert "lists `preregistration/`, which is not a directory" in issues[0].message


def test_an_existing_component_that_is_not_listed_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme(("docs",))}, dirs=("docs", "paper"))
    issues = check_component_table(repo)
    assert "`paper/` exists and the component table does not list it" in issues[0].message


def test_dot_directories_are_not_components(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme(("docs",))}, dirs=("docs", ".github", ".venv"))
    assert check_component_table(repo) == []


def test_a_missing_readme_is_refused(tmp_path: Path) -> None:
    assert check_component_table(tmp_path) == [DocIssue("README.md", "the README is missing")]
    assert component_entries(tmp_path) == []


def test_a_readme_without_the_section_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "# title\n\nno table here\n"})
    issues = check_component_table(repo)
    assert "has no `## What's actually here` section" in issues[0].message
    assert component_entries(repo) == []


def test_the_table_ends_at_the_next_heading(tmp_path: Path) -> None:
    """A directory named in a later section is not a component."""
    repo = _repo(
        tmp_path,
        {"README.md": _readme(("docs",), extra="## Later\n\n| `notthis/` | no |\n")},
        dirs=("docs",),
    )
    assert component_entries(repo) == ["docs"]


def test_the_table_may_be_the_last_section(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme(("docs",))}, dirs=("docs",))
    assert component_entries(repo) == ["docs"]


def test_a_cell_without_a_trailing_slash_is_not_a_component(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {"README.md": "## What's actually here\n\n| `de check` | not a directory |\n"},
    )
    assert component_entries(repo) == []


# --------------------------------------------------------------------------- #
# Composition
# --------------------------------------------------------------------------- #


def test_check_docs_runs_every_check(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": _readme(("docs", "gone"), extra="Run `de nope`.\n\n[x](MISSING.md)"),
            "docs/README.md": _index(),
            "docs/STATUS.md": "no audience here",
        },
        dirs=("docs",),
    )
    messages = " ".join(issue.message for issue in check_docs(repo, COMMANDS))
    assert "is not a command" in messages
    assert "does not exist" in messages
    assert "is not a directory" in messages
    assert "the index does not list it" in messages
    assert "carries no `**Audience:**` line" in messages


def test_census_counts_files_components_index_and_declarations(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": _readme(("docs",)),
            "docs/README.md": _index(("STATUS.md",)),
            "docs/STATUS.md": "x",
            "pyproject.toml": '[tool.decision-evals.docs-absent-commands]\n"report" = "why"\n',
        },
        dirs=("docs",),
    )
    assert census(repo) == (3, 1, 1, 1, 0)


def test_an_issue_reads_as_a_line() -> None:
    assert str(DocIssue("README.md", "broken")) == "README.md: broken"


# --------------------------------------------------------------------------- #
# The documentation index
# --------------------------------------------------------------------------- #


def test_an_index_matching_the_directory_passes(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": _index(("STATUS.md", "VOICE.md")),
            "docs/STATUS.md": AUDIENCE,
            "docs/VOICE.md": AUDIENCE,
        },
    )
    assert check_docs_index(repo) == []


def test_a_document_the_index_omits_is_refused(tmp_path: Path) -> None:
    """The failure the gate exists for: a file nobody remembered to list."""
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": _index(("STATUS.md",)),
            "docs/STATUS.md": AUDIENCE,
            "docs/ARCHITECTURE.md": AUDIENCE,
        },
    )
    issues = check_docs_index(repo)
    assert len(issues) == 1
    assert "`docs/ARCHITECTURE.md` exists and the index does not list it" in issues[0].message


def test_an_index_row_pointing_at_nothing_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"docs/README.md": _index(("GONE.md",))})
    issues = check_docs_index(repo)
    assert len(issues) == 1
    assert "which is not a file under `docs/`" in issues[0].message


def test_a_subdirectory_the_index_never_names_is_refused(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": _index(),
            "docs/programme/part-1.md": AUDIENCE + "\n\n[back](../README.md)",
        },
    )
    messages = " ".join(issue.message for issue in check_docs_index(repo))
    assert "`docs/programme/` exists and the index never names it" in messages


def test_naming_a_subdirectory_satisfies_the_rule(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": _index(extra="[the parts](programme/part-1.md)"),
            "docs/programme/part-1.md": AUDIENCE,
        },
    )
    assert check_docs_index(repo) == []


def test_a_document_in_a_subdirectory_nothing_links_to_is_refused(tmp_path: Path) -> None:
    """Found on the first run: a 315-line draft reachable only by `ls`."""
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": _index(extra="[the drafts](drafts/one.md)"),
            "docs/drafts/one.md": AUDIENCE,
            "docs/drafts/two.md": AUDIENCE,
        },
    )
    issues = check_docs_index(repo)
    assert len(issues) == 1
    assert issues[0].where == "docs/drafts/two.md"
    assert "nothing links to this document" in issues[0].message


def test_a_link_from_any_living_document_counts(tmp_path: Path) -> None:
    """Reachability is repository-wide, not index-only."""
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": _index(("VOICE.md",), extra="[drafts](drafts/one.md)"),
            "docs/VOICE.md": AUDIENCE + "\n\n[two](drafts/two.md)",
            "docs/drafts/one.md": AUDIENCE,
            "docs/drafts/two.md": AUDIENCE,
        },
    )
    assert check_docs_index(repo) == []


def test_an_anchor_does_not_stop_a_link_from_counting(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": _index(extra="[a part](programme/part-1.md#the-tracks)"),
            "docs/programme/part-1.md": AUDIENCE,
        },
    )
    assert check_docs_index(repo) == []


def test_a_missing_index_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme()})
    assert [issue.message for issue in check_docs_index(repo)] == [
        "the documentation index is missing"
    ]


def test_index_entries_ignores_targets_carrying_a_slash(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {"docs/README.md": _index(("STATUS.md",), extra="[s](../SCORECARD.md) [h](reviews/H.md)")},
    )
    assert index_entries(repo) == {"STATUS.md"}


def test_no_index_means_no_entries(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _readme()})
    assert index_entries(repo) == set()


def test_linked_paths_skips_a_target_that_does_not_exist(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"docs/README.md": _index(extra="[gone](nowhere.md)")})
    assert linked_paths(repo) == set()


# --------------------------------------------------------------------------- #
# The audience declaration
# --------------------------------------------------------------------------- #


def test_a_declared_audience_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"docs/VOICE.md": "# Voice\n\n" + AUDIENCE + "\n"})
    assert check_audience_lines(repo) == []


def test_a_document_without_an_audience_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"docs/VOICE.md": "# Voice\n\nno declaration\n"})
    issues = check_audience_lines(repo)
    assert len(issues) == 1
    assert issues[0].where == "docs/VOICE.md"


def test_the_decision_register_needs_no_audience(tmp_path: Path) -> None:
    """It is excluded from the scan, so every rule keyed on the scan skips it."""
    repo = _repo(tmp_path, {"docs/DECISIONS.md": "2026-08-11 - a decision"})
    assert check_audience_lines(repo) == []


# --------------------------------------------------------------------------- #
# Scan scope
# --------------------------------------------------------------------------- #


def test_the_scan_reaches_into_subdirectories(tmp_path: Path) -> None:
    """One level deep for eight days, which is how `docs/reviews/` went unread."""
    repo = _repo(
        tmp_path,
        {"docs/README.md": "x", "docs/reviews/HOUSE_STYLE.md": "x"},
    )
    assert [path.name for path in scanned_files(repo)] == ["README.md", "HOUSE_STYLE.md"]


def test_dated_plans_are_excluded_as_records(tmp_path: Path) -> None:
    """A plan names what it intended to build, which is often not what exists."""
    repo = _repo(
        tmp_path,
        {
            "docs/README.md": "x",
            "docs/superpowers/plans/2026-08-11-a-plan.md": "`scripts/detect_core.py` will do it",
        },
        dirs=("scripts",),
    )
    assert [path.name for path in scanned_files(repo)] == ["README.md"]
    assert check_path_references(repo) == []
