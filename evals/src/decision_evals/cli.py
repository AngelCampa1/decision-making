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
from typing import Final

import typer

from decision_evals.citations import census, check_citations, load_baseline
from decision_evals.stats import minimum_detectable_effect

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
        check_triggers_step(),
        validate_manifests_step(),
        check_citations_step(),
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


def check_triggers_step() -> StepResult:
    """Every skill has a trigger set, and every trigger set names a real skill.

    Added 2026-08-12 because neither held and nothing noticed. The four
    procedures were consolidated behind one router the previous day;
    ``datasets/triggers/evidence-ledger.yaml`` went on describing a skill that
    no longer existed, and the skill that *did* ship had no trigger set at all.
    The module was written and tested to 100% and called by nothing, so there
    was no run in which the mismatch could surface.

    Firing precision is the number that decides whether a skill is worth having
    installed -- a suite that improves answers while interrupting ordinary turns
    is a net loss -- so a set with no negatives is refused too.
    """
    name = "trigger sets"
    _echo_header(name)

    from decision_evals.triggers import (
        TRIGGERS_DIR,
        TriggerSetError,
        check_trigger_sets,
        load_trigger_set,
    )

    triggers_dir = REPO_ROOT / TRIGGERS_DIR
    for path in sorted(triggers_dir.glob("*.yaml")):
        try:
            trigger_set = load_trigger_set(path)
        except TriggerSetError:
            # Reported with its reason by check_trigger_sets below; this loop
            # only prints the census.
            continue
        typer.echo(
            f"{path.stem}: {len(trigger_set.positives)} positive, "
            f"{len(trigger_set.negatives)} negative, "
            f"{sum(1 for c in trigger_set.positives if c.route)} routed"
        )

    issues = check_trigger_sets(REPO_ROOT)
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


def check_citations_step() -> StepResult:
    """Bind every cited arXiv identifier to the bibliography.

    Presence alone is not the check. Three numbers were misattributed here on
    2026-08-11 while citing real papers that existed and said something
    adjacent, so a number asserted beside an identifier additionally requires a
    verbatim ``quote`` in the bib entry. See
    :mod:`decision_evals.citations` for the three cases.

    The census is printed rather than asserted in prose: two drafts of the
    programme carried hand-counted totals and both were wrong, because the
    figure moves with which directories you happen to glob.
    """
    name = "citations"
    _echo_header(name)

    cited, in_bib, missing = census(REPO_ROOT)
    baselined = len(load_baseline(REPO_ROOT))
    typer.echo(
        f"{cited} identifier(s) cited, {in_bib} in the bibliography, "
        f"{missing} unresolved ({baselined} baselined)"
    )

    issues = check_citations(REPO_ROOT)
    if not issues:
        return StepResult(name, True)

    for issue in issues[:20]:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    if len(issues) > 20:
        typer.echo(f"  ... and {len(issues) - 20} more")
    return StepResult(name, False, f"{len(issues)} issue(s)")


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

    from decision_evals.skills import check_mirrors, validate_all

    # Source skills may carry UNTESTED -- that is the normal state during
    # development. The plugin directory is what ships, so the evidence rule
    # applies there.
    issues = validate_all(skills_dir)
    plugin_skills = REPO_ROOT / "plugin" / "skills"
    if plugin_skills.is_dir():
        issues += validate_all(plugin_skills, shipped=True)
    issues += check_mirrors(REPO_ROOT)

    for issue in issues:
        typer.echo(f"  {issue}")
    if issues:
        return StepResult(name, False, f"{len(issues)} issue(s)")

    typer.echo(f"{len(skill_files)} skill(s) valid")
    return StepResult(name, True)


def validate_manifests_step() -> StepResult:
    """Validate the plugin and marketplace manifests against Claude Code's schema.

    Makes no model calls -- it reads two JSON files. Run under ``--strict`` so
    an unrecognised field fails here rather than being tolerated locally and
    rejected by whoever installs it.
    """
    name = "plugin manifests"
    _echo_header(name)

    targets = [
        path for path in (REPO_ROOT / "plugin", REPO_ROOT) if (path / ".claude-plugin").is_dir()
    ]
    if not targets:
        typer.echo("no .claude-plugin/ manifests yet; nothing to validate")
        return StepResult(name, True, "no manifests")

    if shutil.which("claude") is None:
        return StepResult(name, False, "the `claude` CLI is not on PATH")

    failed = [
        target
        for target in targets
        if subprocess.run(
            ["claude", "plugin", "validate", str(target), "--strict"],
            cwd=REPO_ROOT,
            check=False,
        ).returncode
        != 0
    ]
    if failed:
        return StepResult(name, False, f"{len(failed)} manifest(s) rejected")
    return StepResult(name, True)


#: Item counts worth pricing. 12 is the old probe corpus, 30 the long-context
#: plan's core count, 233 the largest single shard-count stratum in the vendored
#: corpus, 527 that corpus minus the Unix-only `code` family, 627 all of it.
POWER_ROWS: Final[tuple[int, ...]] = (12, 30, 100, 233, 527, 627)

#: Discordance is the input people guess wrong, so it is swept rather than
#: chosen. Nothing here picks a value; the reader picks the column.
POWER_COLUMNS: Final[tuple[float, ...]] = (0.15, 0.20, 0.30, 0.40, 0.50)


@app.command()
def power(
    design_effect: float = typer.Option(
        1.0, "--design-effect", help="Clustering inflation. 2.0 is the stated design effect."
    ),
    alpha: float = typer.Option(0.05, help="Type I error rate."),
    target_power: float = typer.Option(0.80, "--power", help="Target power."),
) -> None:
    """Print the minimum detectable effect across item counts and discordance.

    A table rather than a number, and deliberately so. The MDE needs
    ``p_discordant``, which is not known before a screening run, and the first
    standing rule in the work order is that an invented parameter is
    indistinguishable from a measured one three days later. So the parameter is
    swept and the reader picks the column.

    This is what the Track A falsifier needs beside it. "Track A came back flat"
    only kills anything if the MDE was below the effect the literature reports;
    without that second half, an underpowered null reads as a finding.
    """
    _echo_header("minimum detectable effect")
    typer.echo(f"alpha={alpha}, power={target_power}, design_effect={design_effect}, one-sided\n")

    header = "  n_pairs |" + "".join(f"  p_d={p:.2f}" for p in POWER_COLUMNS)
    typer.echo(header)
    typer.echo("  " + "-" * (len(header) - 2))
    for n_pairs in POWER_ROWS:
        cells = ""
        for p_discordant in POWER_COLUMNS:
            try:
                result = minimum_detectable_effect(
                    n_pairs,
                    p_discordant,
                    alpha=alpha,
                    power=target_power,
                    design_effect=design_effect,
                )
            except ValueError:
                # Not an error: at this size no effect is detectable at all,
                # which is the useful answer and says do not run the study.
                cells += "     n/a"
            else:
                cells += f"   {100 * result.effect:5.1f}"
        typer.echo(f"  {n_pairs:>7} |{cells}")

    typer.echo("\n  values are percentage points; n/a = no effect is detectable at any size")


@app.command()
def fetch(
    force: bool = typer.Option(
        False, "--force", help="Re-download even if the local copy already verifies."
    ),
) -> None:
    """Download the vendored corpora and verify them against their locks.

    Deliberately not part of ``de check``: it makes network calls, and the gate
    is meant to be runnable offline and deterministic. The corpus is 28.9 MB and
    is fetched once.
    """
    import urllib.request

    from decision_evals.corpora import CORPUS_PATH, CorpusError, load_lock, verify

    _echo_header("fetch")
    lock = load_lock(REPO_ROOT)
    target = REPO_ROOT / CORPUS_PATH

    if not force:
        try:
            verify(target, lock)
        except CorpusError:
            pass
        else:
            typer.echo(f"{CORPUS_PATH} already matches the lock; nothing to do")
            raise typer.Exit(0)

    typer.echo(f"GET {lock.url}")
    typer.echo(f"  {lock.size_bytes:,} bytes, {lock.data_license}")
    target.parent.mkdir(parents=True, exist_ok=True)
    # The URL is built from the committed lock, never from user input, and the
    # payload is verified against a pinned hash immediately after it lands.
    with urllib.request.urlopen(lock.url) as response:
        target.write_bytes(response.read())

    verify(target, lock)
    typer.echo(f"verified {CORPUS_PATH} against {lock.repo}@{lock.commit[:7]}")


@app.command()
def mirror() -> None:
    """Regenerate the cross-tool mirrors (`.agents/skills/`, `CLAUDE.md`).

    Symlinks would express this better and do not survive a Windows checkout,
    so the copies are generated and `de check` gates their agreement.
    """
    from decision_evals.skills import sync_mirrors

    changed = sync_mirrors(REPO_ROOT)
    for path in changed:
        typer.echo(f"wrote {path.relative_to(REPO_ROOT)}")
    typer.echo(f"{len(changed)} mirror(s) updated")


@app.command()
def lint() -> None:
    """Validate skill frontmatter, evidence metadata, and claim coverage."""
    raise typer.Exit(_summarise([lint_skills_step()]))


if __name__ == "__main__":  # pragma: no cover
    app()
