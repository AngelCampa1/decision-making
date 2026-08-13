"""Reachability of the integrity locks.

A coverage floor says *this module's failure would corrupt a published number
rather than crash it*. It does not say the module runs. Those are different
claims, and this repository has now conflated them twice:

- ``decision_evals.triggers`` was written and tested to 100% and called by
  nothing. A trigger set went on describing a skill that no longer existed and
  the skill that did ship had no trigger set at all, because **there was no run
  in which the mismatch could surface**. The docstring on
  ``cli.check_triggers_step`` records it.
- ``decision_evals.prereg`` carries a 100% line-and-branch floor under the
  heading "Integrity locks: every refusal branch needs a test asserting it
  refuses", and no caller anywhere reaches it. Meanwhile ``CLAUDE.md`` records
  four pre-registration slips in a single day — including a 365-call run
  launched with no bands — every one of which those refusal branches exist to
  prevent.

The second case is the sharper one, because ``docs/PROTOCOL.md`` describes the
gate in the present indicative: *"A confirmation run refuses to start unless…"*.
A refusal branch with 100% test coverage and no caller is **tested, proven, and
inert**. The tests pass, the floor is met, the gate reports green, and the run
it would have refused proceeds.

So the rule: every module carrying a coverage floor must be reachable by import
from an entry point — the console script, or something in ``scripts/``. A
module that cannot be reached is either dead or waiting for a caller that does
not exist yet, and **which of those it is has to be written down**. That is the
``[tool.decision-evals.unwired]`` register: module path to the reason it is
unreachable and the condition that would wire it. Like the citations baseline
it may only shrink, and a register entry that becomes reachable is itself an
error — otherwise the note outlives the situation it describes.

Reachability is computed statically over the import graph, so a module reached
only by a runtime string lookup reads as unreachable here. That is deliberate:
this repository has no dynamic import registry, and a rule that quietly
tolerated one would stop detecting the failure it was written for.
"""

from __future__ import annotations

import ast
import tomllib
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: The installed package. Imports outside it are third-party and not graphed.
PACKAGE: Final = "decision_evals"

#: Where the package lives, relative to the repository root.
SOURCE_ROOT: Final = "evals/src"

#: Entry points. ``cli`` is the console script declared in ``pyproject.toml``;
#: everything in ``scripts/`` is invoked directly with ``python``.
ENTRY_MODULE: Final = f"{PACKAGE}.cli"
ENTRY_SCRIPTS: Final = "scripts"

#: ``pyproject.toml`` tables this module reads.
FLOORS_TABLE: Final = ("tool", "decision-evals", "coverage-floors")
UNWIRED_TABLE: Final = ("tool", "decision-evals", "unwired")


@dataclass(frozen=True)
class WiringIssue:
    """One reachability defect."""

    module: str
    message: str

    def __str__(self) -> str:
        return f"{self.module}: {self.message}"


def _table(data: dict[str, object], path: tuple[str, ...]) -> dict[str, object]:
    """Walk a nested TOML table, returning an empty mapping if absent."""
    node: object = data
    for key in path:
        if not isinstance(node, dict):
            return {}
        node = node.get(key, {})
    return node if isinstance(node, dict) else {}


def module_name(path: Path, source_root: Path) -> str:
    """The dotted name a file is importable as."""
    parts = list(path.relative_to(source_root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imports_of(path: Path, name: str) -> set[str]:
    """First-party modules and attributes referenced by one file's imports.

    Relative imports resolve against the *containing package*, which for an
    ``__init__.py`` is the module's own name and for anything else is its
    parent. Getting that backwards resolves ``.power`` inside
    ``stats/__init__.py`` to ``decision_evals.power`` and silently hides an
    entire subtree as unreachable.

    Attribute targets (``from x import y`` yields ``x.y``) are returned
    alongside module targets because the caller cannot tell which is which
    without the file listing, and a name that is not a module is simply absent
    from it.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()

    container = name if path.name == "__init__.py" else name.rpartition(".")[0] or name
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = container.split(".")
                if node.level > 1:
                    base = base[: len(base) - (node.level - 1)]
                target = ".".join([*base, node.module] if node.module else base)
            else:
                target = node.module or ""
            found.add(target)
            found.update(f"{target}.{alias.name}" for alias in node.names)
    return {found_name for found_name in found if found_name.startswith(PACKAGE)}


def reachable_modules(repo_root: Path) -> set[str]:
    """Every first-party module reachable by import from an entry point.

    Importing ``decision_evals.stats.paired`` also loads the packages above it,
    so an ancestor of a reached module is reached. Without that, every
    ``__init__.py`` in the tree reads as dead.
    """
    source_root = repo_root / SOURCE_ROOT
    modules = {module_name(p, source_root): p for p in sorted(source_root.rglob("*.py"))}

    queue: deque[Path] = deque()
    if (entry := modules.get(ENTRY_MODULE)) is not None:
        queue.append(entry)
    queue.extend(sorted((repo_root / ENTRY_SCRIPTS).glob("*.py")))

    reached: set[str] = set()
    visited: set[str] = set()
    while queue:
        path = queue.popleft()
        name = _name_for(path, source_root)
        if name in visited:
            continue
        visited.add(name)
        reached.add(name)
        for target in imports_of(path, name):
            parts = target.split(".")
            for depth in range(1, len(parts) + 1):
                ancestor = ".".join(parts[:depth])
                if ancestor in modules:
                    reached.add(ancestor)
                    if ancestor not in visited:
                        queue.append(modules[ancestor])
    return reached


def _name_for(path: Path, source_root: Path) -> str:
    """Dotted name for a package file, or a stable pseudo-name for a script.

    Scripts are not importable modules and never appear in the floored set, so
    they only need a name distinct enough to keep the visited set honest.
    """
    if path.is_relative_to(source_root):
        return module_name(path, source_root)
    return f"<script:{path.name}>"


def floored_modules(repo_root: Path) -> list[str]:
    """Every module a coverage floor applies to.

    Floors are substring matches on the path, the same rule
    ``scripts/check_coverage_floors.py`` applies, so ``decision_evals/stats``
    covers the whole subpackage.
    """
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return []
    patterns = list(_table(tomllib.loads(pyproject.read_text(encoding="utf-8")), FLOORS_TABLE))
    source_root = repo_root / SOURCE_ROOT

    covered: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        relative = str(path.relative_to(source_root)).replace("\\", "/")
        if any(relative.startswith(pattern) for pattern in patterns):
            covered.append(module_name(path, source_root))
    return covered


def load_unwired(repo_root: Path) -> dict[str, str]:
    """Modules declared unreachable on purpose, mapped to the stated reason."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    table = _table(tomllib.loads(pyproject.read_text(encoding="utf-8")), UNWIRED_TABLE)
    return {key: str(value) for key, value in table.items()}


def check_wiring(repo_root: Path) -> list[WiringIssue]:
    """Every floored module is reachable, or declared unreachable with a reason."""
    reached = reachable_modules(repo_root)
    declared = load_unwired(repo_root)

    issues = [
        WiringIssue(
            name,
            "carries a coverage floor but is not reachable by import from any entry "
            "point. A refusal branch with 100% coverage and no caller is tested, "
            "proven and inert — the gate reports green and the run it would have "
            "refused proceeds. Wire it, or declare it under "
            "`[tool.decision-evals.unwired]` with the condition that would wire it.",
        )
        for name in floored_modules(repo_root)
        if name not in reached and name not in declared
    ]

    issues += [
        WiringIssue(
            name,
            "is declared unwired but is now reachable. Delete the entry — a note that "
            "outlives the situation it describes is how the last two dead integrity "
            "modules stayed invisible.",
        )
        for name in sorted(declared)
        if name in reached
    ]
    return issues


def census(repo_root: Path) -> tuple[int, int, int]:
    """``(floored, reachable, declared_unwired)``."""
    reached = reachable_modules(repo_root)
    floored = floored_modules(repo_root)
    return len(floored), sum(1 for name in floored if name in reached), len(load_unwired(repo_root))
