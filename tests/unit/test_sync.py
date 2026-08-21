"""Generated regions, and the marker syntax that carries them.

Two of these tests exist because the first implementation was wrong in a way
that reads as harmless. An empty region — an author writing the two markers and
running ``de sync`` to fill them — did not match the block pattern at all, so
the opening marker paired with the *next* region's closing marker and one sync
overwrote two markers and the prose between them. Nothing raised. The document
looked plausible afterwards, which is the worst possible failure for a tool
whose job is keeping documents true.
"""

from __future__ import annotations

from pathlib import Path

from decision_evals.sync import (
    NEWLINE,
    REGIONS,
    Command,
    Facts,
    GateStep,
    Procedure,
    SyncIssue,
    apply_text,
    census,
    check_sync,
    collect_facts,
    facts_in,
    module_inventory,
    procedures,
    regions_in,
    render_arms,
    render_commands,
    render_modules,
    render_procedures,
    render_steps,
    scanned_files,
    sync,
    unbalanced,
)

FACTS = Facts(
    commands=(Command("check", "Run the gate."), Command("site", "Build the site.")),
    steps=(GateStep("mypy", True), GateStep("pytest", False)),
    modules=(("decision_evals/", ("cli", "docs")), ("decision_evals/stats/", ("power",))),
    procedures=(Procedure("ledger.md", True), Procedure("placebo.md", False)),
    arms=(("off", "The skill is absent."), ("on", "The skill is present.")),
    values={"corpus-solvability": "89%"},
)


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for relative, body in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return tmp_path


def _region(region_id: str, body: str = "") -> str:
    return f"<!-- de:generated {region_id} -->\n{body}<!-- /de:generated -->"


def _for(issues: list[SyncIssue], where: str) -> list[str]:
    """Issues raised against one document, so the unused-region check is out of the way."""
    return [issue.message for issue in issues if issue.where == where]


# --------------------------------------------------------------------------- #
# The marker
# --------------------------------------------------------------------------- #


def test_an_empty_region_is_a_region() -> None:
    """The failure that produced this module's only data loss.

    An author writes the markers and runs `de sync` to fill them. If that does
    not parse, the opener reaches forward to the next closer and the sync eats
    everything in between.
    """
    text = f"# doc\n\n{_region('arm-purposes')}\n"
    assert regions_in(text) == [("arm-purposes", "")]


def test_a_region_is_filled_in_place() -> None:
    text = f"before\n\n{_region('arm-purposes')}\n\nafter\n"
    updated = apply_text(text, FACTS)
    assert updated.startswith("before\n")
    assert updated.endswith("after\n")
    assert "| `off` | The skill is absent. |" in updated


def test_rendering_twice_changes_nothing() -> None:
    text = f"{_region('arm-purposes')}\n"
    once = apply_text(text, FACTS)
    assert apply_text(once, FACTS) == once


def test_two_regions_do_not_reach_into_each_other() -> None:
    text = f"{_region('arm-purposes')}\n\nmiddle\n\n{_region('de-commands')}\n"
    updated = apply_text(text, FACTS)
    assert "middle" in updated
    assert [region for region, _ in regions_in(updated)] == ["arm-purposes", "de-commands"]


def test_an_unknown_region_is_left_alone() -> None:
    text = f"{_region('not-a-region', 'hand written\n')}\n"
    assert apply_text(text, FACTS) == text


def test_an_unclosed_marker_is_refused() -> None:
    text = f"<!-- de:generated arm-purposes -->\n\n{_region('de-commands')}\n"
    assert unbalanced(text)


def test_balanced_markers_pass() -> None:
    assert unbalanced(f"{_region('arm-purposes')}\n") == []


def test_a_document_with_no_markers_passes() -> None:
    assert unbalanced("# just prose\n") == []


# --------------------------------------------------------------------------- #
# Inline facts
# --------------------------------------------------------------------------- #


def test_an_inline_fact_is_rewritten_from_the_register() -> None:
    text = "a corpus that is <!-- de:fact corpus-solvability -->12%<!-- /de:fact --> solvable\n"
    assert "-->89%<!--" in apply_text(text, FACTS)


def test_an_unregistered_fact_is_left_alone() -> None:
    text = "<!-- de:fact nobody-registered-this -->7<!-- /de:fact -->\n"
    assert apply_text(text, FACTS) == text


def test_facts_are_found() -> None:
    text = "x <!-- de:fact corpus-solvability -->89%<!-- /de:fact --> y\n"
    assert facts_in(text) == [("corpus-solvability", "89%")]


# --------------------------------------------------------------------------- #
# Gathering the facts
# --------------------------------------------------------------------------- #


def test_the_module_inventory_walks_the_package(tmp_path: Path) -> None:
    root = "evals/src/decision_evals"
    repo = _repo(
        tmp_path,
        {
            f"{root}/__init__.py": "",
            f"{root}/cli.py": "",
            f"{root}/docs.py": "",
            f"{root}/stats/__init__.py": "",
            f"{root}/stats/power.py": "",
            f"{root}/_private/hidden.py": "",
        },
    )
    (repo / root / "empty").mkdir()
    (repo / root / "notapackage").mkdir()
    (repo / root / "notapackage" / "README.md").write_text("x", encoding="utf-8")
    assert module_inventory(repo) == (
        ("decision_evals/", ("cli", "docs")),
        ("decision_evals/stats/", ("power",)),
    )


def test_no_package_means_no_inventory(tmp_path: Path) -> None:
    assert module_inventory(tmp_path) == ()


def test_the_procedures_record_what_the_router_names(tmp_path: Path) -> None:
    root = "skills/decision-making"
    repo = _repo(
        tmp_path,
        {
            f"{root}/SKILL.md": "Read [ledger.md](ledger.md) when there is too much context.",
            f"{root}/ledger.md": "x",
            f"{root}/placebo.md": "x",
        },
    )
    assert procedures(repo) == (Procedure("ledger.md", True), Procedure("placebo.md", False))


def test_no_skill_means_no_procedures(tmp_path: Path) -> None:
    assert procedures(tmp_path) == ()


def test_collecting_takes_the_live_values_and_reads_the_rest(tmp_path: Path) -> None:
    """The register is handed in, not imported.

    `claims.py` imports the marker from here, so this module importing the
    register back would be a cycle. It also means a test can hand this a
    directory and a dict.
    """
    root = "evals/src/decision_evals"
    repo = _repo(tmp_path, {f"{root}/cli.py": ""})
    facts = collect_facts(
        repo, commands=(), steps=(), arms=(), values={"corpus-solvability": "89%"}
    )
    assert facts.values == {"corpus-solvability": "89%"}
    assert facts.commands == ()
    assert facts.modules == (("decision_evals/", ("cli",)),)


# --------------------------------------------------------------------------- #
# What each region renders
# --------------------------------------------------------------------------- #


def test_commands_render_as_a_table() -> None:
    assert render_commands(FACTS).splitlines()[2] == "| `de check` | Run the gate. |"


def test_steps_render_numbered_and_say_what_fast_drops() -> None:
    lines = render_steps(FACTS).splitlines()
    assert lines[2] == "| 1 | mypy | runs |"
    assert lines[3] == "| 2 | pytest | skipped |"


def test_modules_render_one_row_per_package() -> None:
    assert "| `decision_evals/stats/` | `power` |" in render_modules(FACTS)


def test_procedures_say_whether_the_router_names_them() -> None:
    rendered = render_procedures(FACTS)
    assert "| `ledger.md` | yes |" in rendered
    assert "| `placebo.md` | no |" in rendered


def test_arms_render_their_purpose() -> None:
    assert "| `off` | The skill is absent. |" in render_arms(FACTS)


# --------------------------------------------------------------------------- #
# Writing
# --------------------------------------------------------------------------- #


def test_scanning_covers_the_root_and_docs_recursively(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": "x",
            "docs/STATUS.md": "x",
            "docs/programme/part-1.md": "x",
            "notebook/entry.md": "x",
        },
    )
    (repo / "docs" / "adirectory.md").mkdir()
    found = {path.relative_to(repo).as_posix() for path in scanned_files(repo)}
    assert found == {"README.md", "docs/STATUS.md", "docs/programme/part-1.md"}


def test_sync_writes_only_what_changed(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": f"{_region('arm-purposes')}\n",
            "docs/STATUS.md": "nothing derived here\n",
        },
    )
    assert sync(repo, FACTS) == ["README.md"]
    assert sync(repo, FACTS) == []


# --------------------------------------------------------------------------- #
# Refusing
# --------------------------------------------------------------------------- #


def _all_regions(extra: str = "") -> str:
    return "\n\n".join(_region(region_id) for region_id in sorted(REGIONS)) + f"\n{extra}"


def test_every_region_and_a_current_fact_pass(tmp_path: Path) -> None:
    text = _all_regions("solvable at <!-- de:fact corpus-solvability -->89%<!-- /de:fact -->")
    repo = _repo(tmp_path, {"README.md": text})
    sync(repo, FACTS)
    assert check_sync(repo, FACTS) == []


def test_a_region_nothing_uses_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "# nothing derived\n"})
    issues = check_sync(repo, FACTS)
    assert {issue.where for issue in issues} == {"decision_evals.sync"}
    assert len(issues) == len(REGIONS)


def test_a_stale_region_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _all_regions()})
    sync(repo, FACTS)
    text = (repo / "README.md").read_text(encoding="utf-8")
    (repo / "README.md").write_text(text.replace("Run the gate.", "Runs stuff."), "utf-8")
    messages = _for(check_sync(repo, FACTS), "README.md")
    assert len(messages) == 1
    assert "`de-commands` is not what it renders from" in messages[0]
    assert "Runs stuff." in messages[0]


def test_an_unknown_region_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": f"{_all_regions()}\n{_region('invented', 'x\n')}\n"})
    sync(repo, FACTS)
    messages = _for(check_sync(repo, FACTS), "README.md")
    assert len(messages) == 1
    assert "nothing renders" in messages[0]


def test_a_nested_marker_is_refused(tmp_path: Path) -> None:
    """An unclosed opener reaching forward, which is the shape that lost data."""
    text = (
        "<!-- de:generated de-commands -->\n"
        "<!-- de:generated arm-purposes -->\n"
        "<!-- /de:generated -->\n"
    )
    repo = _repo(tmp_path, {"README.md": text})
    messages = _for(check_sync(repo, FACTS), "README.md")
    assert any("another marker inside it" in message for message in messages)
    assert any("do not pair up" in message or "pair up" in message for message in messages)


def test_an_unregistered_inline_fact_is_left_to_the_register(tmp_path: Path) -> None:
    """One mistake, one refusal.

    `claims.py` owns whether a stated id exists, in both directions and across
    pages and documents alike. Refusing it here as well would be two messages
    for one fix, from two modules, neither of which owns the register.
    """
    text = _all_regions() + NEWLINE + "<!-- de:fact invented -->7<!-- /de:fact -->" + NEWLINE
    repo = _repo(tmp_path, {"README.md": text})
    sync(repo, FACTS)
    assert _for(check_sync(repo, FACTS), "README.md") == []


def test_a_stale_inline_fact_is_refused(tmp_path: Path) -> None:
    text = f"{_all_regions()}\n<!-- de:fact corpus-solvability -->12%<!-- /de:fact -->\n"
    repo = _repo(tmp_path, {"README.md": text})
    messages = _for(check_sync(repo, FACTS), "README.md")
    assert any("'12%'" in message and "'89%'" in message for message in messages)


# --------------------------------------------------------------------------- #
# Saying what differs
# --------------------------------------------------------------------------- #


def test_a_shortened_region_names_the_missing_line(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _all_regions()})
    sync(repo, FACTS)
    text = (repo / "README.md").read_text(encoding="utf-8")
    (repo / "README.md").write_text(
        text.replace("| `de site` | Build the site. |\n", ""), encoding="utf-8"
    )
    messages = _for(check_sync(repo, FACTS), "README.md")
    assert "missing 1 line(s)" in messages[0]


def test_a_lengthened_region_says_so(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": _all_regions()})
    sync(repo, FACTS)
    text = (repo / "README.md").read_text(encoding="utf-8")
    (repo / "README.md").write_text(
        text.replace(
            "| `de site` | Build the site. |\n",
            "| `de site` | Build the site. |\n| `de invented` | Nothing. |\n",
        ),
        encoding="utf-8",
    )
    messages = _for(check_sync(repo, FACTS), "README.md")
    assert "1 line(s) that nothing renders" in messages[0]


def test_a_region_differing_only_in_whitespace_says_so(tmp_path: Path) -> None:
    """The closing marker pulled onto the last rendered line.

    Every line matches and the region is still not what it renders, which read
    as "0 line(s) that nothing renders" until this test existed.
    """
    rendered = render_arms(FACTS)
    text = f"<!-- de:generated arm-purposes -->\n{rendered}<!-- /de:generated -->" + NEWLINE
    repo = _repo(tmp_path, {"README.md": _all_regions() + text})
    sync(repo, FACTS)
    (repo / "README.md").write_text(_all_regions() + text, encoding="utf-8")
    messages = _for(check_sync(repo, FACTS), "README.md")
    assert any("whitespace at an edge" in message for message in messages)


# --------------------------------------------------------------------------- #
# Counting
# --------------------------------------------------------------------------- #


def test_the_census_counts_documents_regions_and_facts(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": f"{_region('arm-purposes')}\n"
            "<!-- de:fact corpus-solvability -->89%<!-- /de:fact -->\n",
            "docs/STATUS.md": f"{_region('de-commands')}\n",
            "docs/VOICE.md": "prose only\n",
        },
    )
    assert census(repo) == (2, 2, 1)


def test_an_issue_reads_as_one_line() -> None:
    assert str(SyncIssue("README.md", "is wrong")) == "README.md: is wrong"
