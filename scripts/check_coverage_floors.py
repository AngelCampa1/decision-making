"""Enforce per-module coverage floors that a global threshold would hide.

``fail_under`` in coverage.py is global only. A repository can sit comfortably at
95% overall while the module that computes every published number sits at 40%,
because a large well-covered CLI averages it out. Since the statistics layer is
the part whose failure would silently corrupt results rather than crash, it
carries a stricter floor than the code around it, and that distinction has to be
checked explicitly.

Floors are declared in ``pyproject.toml`` under ``[tool.decision-evals]`` so they
live beside the rest of the tooling configuration rather than being buried here.

Usage:
    python scripts/check_coverage_floors.py [coverage.json]
"""

from __future__ import annotations

import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class Floor:
    """A coverage requirement for files matching a path prefix."""

    pattern: str
    line: float
    branch: float


@dataclass(frozen=True, slots=True)
class Violation:
    """A file that fell below its floor."""

    path: str
    pattern: str
    kind: str
    actual: float
    required: float

    def __str__(self) -> str:
        return (
            f"  {self.path}\n"
            f"      {self.kind} coverage {self.actual:.1f}% < {self.required:.1f}% "
            f"(floor '{self.pattern}')"
        )


def load_floors(pyproject: Path) -> list[Floor]:
    """Read floor declarations from pyproject.toml.

    Later entries win, so more specific patterns should be declared after the
    general ones they refine.
    """
    with pyproject.open("rb") as handle:
        config = tomllib.load(handle)
    declared = config.get("tool", {}).get("decision-evals", {}).get("coverage-floors", {})
    return [
        Floor(pattern=pattern, line=float(v["line"]), branch=float(v.get("branch", 0.0)))
        for pattern, v in declared.items()
    ]


def _normalise(path: str) -> str:
    """Make a coverage.py path comparable across platforms."""
    return path.replace("\\", "/")


def matching_floor(path: str, floors: list[Floor]) -> Floor | None:
    """Return the most specific floor for a path, or None if unconstrained."""
    normalised = _normalise(path)
    best: Floor | None = None
    for floor in floors:
        if floor.pattern in normalised and (
            best is None or len(floor.pattern) >= len(best.pattern)
        ):
            best = floor
    return best


def _percent(covered: int, total: int) -> float:
    """Percentage covered, treating 'nothing to cover' as fully covered."""
    return 100.0 if total == 0 else 100.0 * covered / total


def find_violations(report: dict, floors: list[Floor]) -> list[Violation]:
    """Check every measured file against its floor."""
    violations: list[Violation] = []
    for path, data in sorted(report.get("files", {}).items()):
        floor = matching_floor(path, floors)
        if floor is None:
            continue
        summary = data["summary"]

        line_pct = _percent(
            summary["covered_lines"], summary["covered_lines"] + summary["missing_lines"]
        )
        if line_pct + 1e-9 < floor.line:
            violations.append(
                Violation(_normalise(path), floor.pattern, "line", line_pct, floor.line)
            )

        branch_pct = _percent(summary.get("covered_branches", 0), summary.get("num_branches", 0))
        if branch_pct + 1e-9 < floor.branch:
            violations.append(
                Violation(_normalise(path), floor.pattern, "branch", branch_pct, floor.branch)
            )
    return violations


def main(argv: list[str]) -> int:
    """Entry point. Returns a process exit code."""
    report_path = Path(argv[1]) if len(argv) > 1 else REPO_ROOT / "coverage.json"
    if not report_path.exists():
        print(
            f"coverage report not found at {report_path}\n"
            "Run: uv run pytest --cov --cov-report=json",
            file=sys.stderr,
        )
        return 2

    floors = load_floors(REPO_ROOT / "pyproject.toml")
    if not floors:
        print("no coverage floors declared in pyproject.toml", file=sys.stderr)
        return 2

    with report_path.open(encoding="utf-8") as handle:
        report = json.load(handle)

    violations = find_violations(report, floors)
    if violations:
        print(f"coverage floors violated ({len(violations)}):", file=sys.stderr)
        for violation in violations:
            print(violation, file=sys.stderr)
        return 1

    measured = sum(1 for path in report.get("files", {}) if matching_floor(path, floors))
    print(f"coverage floors satisfied ({measured} files against {len(floors)} floors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
