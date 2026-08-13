"""The integrity-wiring gate.

The failure this guards is specific and has happened twice: a module carrying a
100% line-and-branch coverage floor that **no entry point reaches**. Its tests
pass, its floor is met, the gate reports green, and the run its refusals would
have blocked proceeds. Nothing else in the gate can tell that apart from a
working lock.

Two of these tests exist because the first implementation got the graph wrong in
ways that both read as plausible: relative imports inside an ``__init__.py``
resolving one package too high, and a breadth-first search that marked modules
visited at enqueue time and so never parsed anything past the entry points. Each
bug reported a large, confident, wrong set of dead modules.
"""

from __future__ import annotations

from pathlib import Path

from decision_evals.wiring import (
    WiringIssue,
    census,
    check_wiring,
    floored_modules,
    imports_of,
    load_unwired,
    module_name,
    reachable_modules,
)


def _package(tmp_path: Path, files: dict[str, str]) -> Path:
    """A repository with a source tree, scripts directory and pyproject."""
    for relative, body in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (tmp_path / "scripts").mkdir(exist_ok=True)
    return tmp_path


def _pyproject(floors: list[str], unwired: dict[str, str] | None = None) -> str:
    lines = ["[tool.decision-evals.coverage-floors]"]
    lines += [f'"{pattern}" = {{ line = 100.0, branch = 100.0 }}' for pattern in floors]
    lines.append("[tool.decision-evals.unwired]")
    for module, reason in (unwired or {}).items():
        lines.append(f'"{module}" = "{reason}"')
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Naming and import parsing
# --------------------------------------------------------------------------- #


def test_module_name_drops_the_init_suffix(tmp_path: Path) -> None:
    root = tmp_path / "src"
    path = root / "decision_evals" / "stats" / "__init__.py"
    path.parent.mkdir(parents=True)
    path.touch()
    assert module_name(path, root) == "decision_evals.stats"


def test_module_name_of_a_plain_module(tmp_path: Path) -> None:
    root = tmp_path / "src"
    path = root / "decision_evals" / "prereg.py"
    path.parent.mkdir(parents=True)
    path.touch()
    assert module_name(path, root) == "decision_evals.prereg"


def test_relative_imports_in_a_package_init_resolve_to_that_package(tmp_path: Path) -> None:
    """`from .power import x` inside stats/__init__.py is stats.power.

    Resolving it to ``decision_evals.power`` instead reported the entire stats
    subpackage as dead — five modules, confidently, and wrongly.
    """
    path = tmp_path / "__init__.py"
    path.write_text("from .power import minimum_detectable_effect\n", encoding="utf-8")
    assert "decision_evals.stats.power" in imports_of(path, "decision_evals.stats")


def test_relative_imports_in_a_module_resolve_to_its_parent(tmp_path: Path) -> None:
    path = tmp_path / "paired.py"
    path.write_text("from .cluster import design_effect\n", encoding="utf-8")
    assert "decision_evals.stats.cluster" in imports_of(path, "decision_evals.stats.paired")


def test_a_double_dot_import_climbs_one_package(tmp_path: Path) -> None:
    path = tmp_path / "power.py"
    path.write_text("from ..arenas import policy_for\n", encoding="utf-8")
    assert "decision_evals.arenas" in imports_of(path, "decision_evals.stats.power")


def test_absolute_imports_are_captured(tmp_path: Path) -> None:
    path = tmp_path / "cli.py"
    path.write_text("import decision_evals.prereg\n", encoding="utf-8")
    assert "decision_evals.prereg" in imports_of(path, "decision_evals.cli")


def test_third_party_imports_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "cli.py"
    path.write_text("import typer\nfrom pathlib import Path\n", encoding="utf-8")
    assert imports_of(path, "decision_evals.cli") == set()


def test_an_unparseable_file_contributes_nothing(tmp_path: Path) -> None:
    path = tmp_path / "broken.py"
    path.write_text("def (\n", encoding="utf-8")
    assert imports_of(path, "decision_evals.broken") == set()


def test_a_missing_file_contributes_nothing(tmp_path: Path) -> None:
    assert imports_of(tmp_path / "gone.py", "decision_evals.gone") == set()


# --------------------------------------------------------------------------- #
# Reachability
# --------------------------------------------------------------------------- #


def test_a_module_imported_by_the_cli_is_reachable(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "from decision_evals.budget import x\n",
            "evals/src/decision_evals/budget.py": "x = 1\n",
        },
    )
    assert "decision_evals.budget" in reachable_modules(repo)


def test_reachability_is_transitive(tmp_path: Path) -> None:
    """The BFS must parse what it enqueues, not merely mark it seen."""
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "from decision_evals.a import x\n",
            "evals/src/decision_evals/a.py": "from decision_evals.b import y\n",
            "evals/src/decision_evals/b.py": "from decision_evals.c import z\n",
            "evals/src/decision_evals/c.py": "z = 1\n",
        },
    )
    reached = reachable_modules(repo)
    assert {"decision_evals.a", "decision_evals.b", "decision_evals.c"} <= reached


def test_importing_a_submodule_reaches_its_ancestor_packages(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "from decision_evals.stats.power import x\n",
            "evals/src/decision_evals/stats/__init__.py": "",
            "evals/src/decision_evals/stats/power.py": "x = 1\n",
        },
    )
    assert "decision_evals.stats" in reachable_modules(repo)


def test_a_module_reached_only_from_scripts_is_reachable(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "",
            "evals/src/decision_evals/triggers.py": "x = 1\n",
            "scripts/run_triggers.py": "from decision_evals.triggers import x\n",
        },
    )
    assert "decision_evals.triggers" in reachable_modules(repo)


def test_an_orphan_is_not_reachable(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "",
            "evals/src/decision_evals/prereg.py": "x = 1\n",
        },
    )
    assert "decision_evals.prereg" not in reachable_modules(repo)


def test_a_tree_without_a_cli_still_walks_scripts(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/triggers.py": "x = 1\n",
            "scripts/run.py": "from decision_evals.triggers import x\n",
        },
    )
    assert "decision_evals.triggers" in reachable_modules(repo)


# --------------------------------------------------------------------------- #
# The rule
# --------------------------------------------------------------------------- #


def test_an_unreachable_floored_module_is_refused(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "",
            "evals/src/decision_evals/prereg.py": "x = 1\n",
            "pyproject.toml": _pyproject(["decision_evals/prereg.py"]),
        },
    )
    issues = check_wiring(repo)
    assert [issue.module for issue in issues] == ["decision_evals.prereg"]
    assert "tested, proven and inert" in issues[0].message


def test_declaring_it_unwired_satisfies_the_rule(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "",
            "evals/src/decision_evals/prereg.py": "x = 1\n",
            "pyproject.toml": _pyproject(
                ["decision_evals/prereg.py"],
                {"decision_evals.prereg": "waiting for a confirmation runner"},
            ),
        },
    )
    assert check_wiring(repo) == []


def test_a_declaration_that_became_reachable_is_refused(tmp_path: Path) -> None:
    """A note that outlives its situation is how dead modules stay invisible."""
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "from decision_evals.prereg import x\n",
            "evals/src/decision_evals/prereg.py": "x = 1\n",
            "pyproject.toml": _pyproject(
                ["decision_evals/prereg.py"],
                {"decision_evals.prereg": "waiting for a confirmation runner"},
            ),
        },
    )
    issues = check_wiring(repo)
    assert any("now reachable" in issue.message for issue in issues)


def test_an_unfloored_orphan_is_not_the_gates_business(tmp_path: Path) -> None:
    """The rule is about integrity locks, not about dead code in general."""
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "",
            "evals/src/decision_evals/spare.py": "x = 1\n",
            "pyproject.toml": _pyproject(["decision_evals/prereg.py"]),
        },
    )
    assert check_wiring(repo) == []


def test_a_floor_pattern_covers_a_whole_subpackage(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "evals/src/decision_evals/cli.py": "",
            "evals/src/decision_evals/stats/__init__.py": "",
            "evals/src/decision_evals/stats/power.py": "x = 1\n",
            "pyproject.toml": _pyproject(["decision_evals/stats"]),
        },
    )
    assert set(floored_modules(repo)) == {"decision_evals.stats", "decision_evals.stats.power"}


# --------------------------------------------------------------------------- #
# Configuration edges
# --------------------------------------------------------------------------- #


def test_a_missing_pyproject_yields_no_floors_and_no_declarations(tmp_path: Path) -> None:
    repo = _package(tmp_path, {"evals/src/decision_evals/__init__.py": ""})
    assert floored_modules(repo) == []
    assert load_unwired(repo) == {}


def test_a_pyproject_without_the_tables_is_empty(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "pyproject.toml": '[project]\nname = "x"\n',
        },
    )
    assert floored_modules(repo) == []
    assert load_unwired(repo) == {}


def test_a_non_table_value_where_a_table_is_expected_is_empty(tmp_path: Path) -> None:
    repo = _package(
        tmp_path,
        {
            "evals/src/decision_evals/__init__.py": "",
            "pyproject.toml": '[tool]\n"decision-evals" = "not a table"\n',
        },
    )
    assert load_unwired(repo) == {}


# --------------------------------------------------------------------------- #
# The real repository
# --------------------------------------------------------------------------- #


def test_the_repository_passes_its_own_gate() -> None:
    assert check_wiring(Path(__file__).resolve().parents[2]) == []


def test_the_gate_governs_itself() -> None:
    """`provenance` and `wiring` carry floors, so they must be reachable too."""
    repo_root = Path(__file__).resolve().parents[2]
    reached = reachable_modules(repo_root)
    assert {"decision_evals.provenance", "decision_evals.wiring"} <= reached


def test_an_issue_renders_as_module_then_message() -> None:
    assert str(WiringIssue("decision_evals.prereg", "inert")) == "decision_evals.prereg: inert"


def test_census_reports_the_real_tree() -> None:
    floored, reachable, declared = census(Path(__file__).resolve().parents[2])
    assert floored > reachable >= 1
    assert declared >= 1
