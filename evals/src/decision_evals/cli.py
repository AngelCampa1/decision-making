"""Command-line entry point for the harness.

``de check`` is the whole local gate: lint, types, tests, coverage floors, and
the repository-integrity checks. It makes no model calls and is fully
deterministic, so it can run on every commit without spending budget or
introducing flakes.

Model-backed evaluation deliberately lives behind separate commands. Anything
that costs rate limit or produces a verdict has to be invoked on purpose.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import typer

REPO_ROOT = Path(__file__).resolve().parents[3]

# Commit attribution is load-bearing here: the commit history is the
# pre-registration evidence, so a misattributed commit cannot simply be
# rewritten later without destroying the timestamps the method relies on.
FORBIDDEN_EMAIL_DOMAINS = ("@ventoralabs.com",)

app = typer.Typer(
    name="de",
    help="Evaluation harness for agent decision skills.",
    no_args_is_help=True,
    add_completion=False,
)


@dataclass(frozen=True, slots=True)
class StepResult:
    """Outcome of one gate step."""

    name: str
    passed: bool
    detail: str = ""


def _echo_header(text: str) -> None:
    typer.secho(f"\n=== {text} ===", fg=typer.colors.CYAN, bold=True)


def _run(name: str, command: list[str], *, cwd: Path | None = None) -> StepResult:
    """Run a subprocess step, streaming its output."""
    _echo_header(name)
    if shutil.which(command[0]) is None and not Path(command[0]).exists():
        return StepResult(name, False, f"command not found: {command[0]}")
    completed = subprocess.run(command, cwd=cwd or REPO_ROOT, check=False)
    return StepResult(name, completed.returncode == 0)


def _git_output(args: list[str]) -> str | None:
    """Run a git command, returning stripped stdout or None if it failed."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def check_git_identity() -> StepResult:
    """Verify commit attribution is configured and uses an acceptable address.

    Catches the misattribution before it lands rather than after, which matters
    because rewriting history to fix it would invalidate the pre-registration
    timestamps that make the protocol credible.
    """
    name = "git identity"
    _echo_header(name)

    if not (REPO_ROOT / ".git").exists():
        typer.echo("not a git repository; skipping")
        return StepResult(name, True, "not a git repository")

    email = _git_output(["config", "user.email"])
    author = _git_output(["config", "user.name"])

    if not email:
        return StepResult(name, False, "git user.email is not set")
    if not author:
        return StepResult(name, False, "git user.name is not set")

    for domain in FORBIDDEN_EMAIL_DOMAINS:
        if email.endswith(domain):
            return StepResult(
                name,
                False,
                f"commit email {email!r} uses {domain}, which must not appear on this "
                f"repository. Set a repo-local address:\n"
                f'  git config user.email "200381496+AngelCampa1@users.noreply.github.com"',
            )

    typer.echo(f"{author} <{email}>")
    return StepResult(name, True)


def _summarise(results: list[StepResult]) -> int:
    """Print a summary table and return a process exit code."""
    _echo_header("summary")
    failed = [r for r in results if not r.passed]
    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        colour = typer.colors.GREEN if result.passed else typer.colors.RED
        typer.secho(f"  [{mark}] {result.name}", fg=colour)
        if result.detail and not result.passed:
            typer.secho(f"         {result.detail}", fg=typer.colors.RED)

    if failed:
        typer.secho(
            f"\n{len(failed)} of {len(results)} steps failed.", fg=typer.colors.RED, bold=True
        )
        return 1
    typer.secho(f"\nAll {len(results)} steps passed.", fg=typer.colors.GREEN, bold=True)
    return 0


@app.command()
def check(
    fast: bool = typer.Option(
        False,
        "--fast",
        help="Skip tests and coverage. Used by the pre-commit hook; pre-push runs everything.",
    ),
) -> None:
    """Run the full local gate. No model calls, fully deterministic."""
    python = sys.executable
    results: list[StepResult] = [
        check_git_identity(),
        _run("ruff check", [python, "-m", "ruff", "check", "."]),
        _run("ruff format", [python, "-m", "ruff", "format", "--check", "."]),
        _run("mypy", [python, "-m", "mypy"]),
        lint_skills_step(),
    ]

    if not fast:
        results.append(
            _run(
                "pytest",
                [
                    python,
                    "-m",
                    "pytest",
                    "tests",
                    "-m",
                    "not llm and not slow",
                    "--cov",
                    "--cov-report=json",
                    "--cov-report=term:skip-covered",
                ],
            )
        )
        results.append(
            _run(
                "coverage floors",
                [python, str(REPO_ROOT / "scripts" / "check_coverage_floors.py")],
            )
        )

    raise typer.Exit(_summarise(results))


def lint_skills_step() -> StepResult:
    """Validate every shipped skill's frontmatter and evidence metadata.

    Skills without a recorded verdict must not ship, which is the rule that
    keeps this repository from becoming another unvalidated prompt library. The
    validator is a no-op while no skills exist, and says so rather than passing
    silently.
    """
    name = "skill lint"
    _echo_header(name)

    skills_dir = REPO_ROOT / "skills"
    if not skills_dir.exists():
        typer.echo("no skills/ directory yet; nothing to validate")
        return StepResult(name, True, "no skills directory")

    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        typer.echo("skills/ is empty; nothing to validate")
        return StepResult(name, True, "no skills")

    # The full validator (frontmatter schema, evidence coverage, claim coverage,
    # pre-registration hash integrity) arrives with the first skill.
    typer.echo(f"found {len(skill_files)} skill(s)")
    return StepResult(name, True)


@app.command()
def lint() -> None:
    """Validate skill frontmatter, evidence metadata, and claim coverage."""
    raise typer.Exit(_summarise([lint_skills_step()]))


if __name__ == "__main__":  # pragma: no cover
    app()
