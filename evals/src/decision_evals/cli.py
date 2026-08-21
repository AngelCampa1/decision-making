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
from decision_evals.claims import census as claims_census
from decision_evals.claims import check_claims
from decision_evals.decisions import GOVERNED as DECISION_PATHS
from decision_evals.decisions import GovernedCommit, check_decisions
from decision_evals.decisions import census as decisions_census
from decision_evals.deployed import BEHIND as DEPLOY_BEHIND
from decision_evals.deployed import CURRENT as DEPLOY_CURRENT
from decision_evals.deployed import check_deployed
from decision_evals.docs import census as docs_census
from decision_evals.docs import check_docs
from decision_evals.provenance import (
    INDEX_PATH,
    GitFacts,
    ProvenanceIssue,
    check_provenance,
    discover_runs,
    index_is_current,
    prediction_links,
    render_index,
)
from decision_evals.provenance import RunRecord as ProvenanceRun
from decision_evals.provenance import census as provenance_census
from decision_evals.rescore import (
    CHECKPOINT_DIR,
    RescoreError,
    check_checkpoints,
    load_declared_versions,
    reconcile,
)
from decision_evals.site import (
    MANIFEST_PATH as SITE_MANIFEST_PATH,
)
from decision_evals.site import (
    SITE_DIR as SITE_DIR_NAME,
)
from decision_evals.site import census as site_census
from decision_evals.site import (
    check_site,
    render_manifest,
    site_present,
)
from decision_evals.stats import minimum_detectable_effect
from decision_evals.wiring import census as census_wiring
from decision_evals.wiring import check_wiring

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
        check_tailoring_step(),
        validate_manifests_step(),
        check_citations_step(),
        check_provenance_step(),
        check_wiring_step(),
        check_decisions_step(),
        check_corrections_step(),
        check_checkpoints_step(),
        check_docs_step(),
        check_claims_step(),
    ]

    if not fast:
        # Rebuilding the site takes a Node toolchain and a few seconds, so it
        # is demanded at `pre-push` rather than on every commit -- the same
        # treatment as the test suite, and for the same reason.
        results.append(check_site_step())
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
        deferred_corpus_findings,
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

    # Printed whether or not the step passes, and deliberately not in green. A
    # baselined finding is deferred, not resolved; a run that reported only the
    # census would let a reader take a passing gate for a clean corpus, and the
    # gap between "not shown to be wrong" and "shown to be right" is the thing
    # this repository exists to keep open.
    for deferred in deferred_corpus_findings(REPO_ROOT):
        typer.secho(f"  known-open (baselined): {deferred}", fg=typer.colors.YELLOW)

    issues = check_trigger_sets(REPO_ROOT)
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


def check_tailoring_step() -> StepResult:
    """The tailoring corpus's governing/matched split, checked for shortcuts.

    Added 2026-08-19 after a human reader, not a gate, noticed that all three
    authored triplets share one surface tell: every ``governing`` insert names
    a penalty attached to a status change and every ``matched`` insert is
    procedural. ``datasets/triggers/`` shipped an equivalent defect once
    already (see ``check_triggers_step``'s docstring) with no audit until every
    number computed on it had to be re-read; this closes the same gap for
    Track H before any model call is made against the corpus.

    The corpus is 3 of a planned 20 triplets and under active revision, so an
    empty or missing ``index.yaml`` passes with nothing to report rather than
    failing the gate -- see :func:`decision_evals.tailoring.load_deltas`.

    **Baselined findings are deferred rather than dropped, and printed on
    every run** -- the same treatment ``check_triggers_step`` gives the
    trigger corpus, for the same reason: the three triplets on disk are
    retained as evidence of a form that failed adversarial review (see
    ``datasets/tailoring/corpus-baseline.txt``), so this step must never read
    as "the corpus is clean" while it is still red by design.
    """
    name = "tailoring corpus"
    _echo_header(name)

    from decision_evals.corpus import apply_corpus_baseline
    from decision_evals.tailoring import (
        CORPUS_SCOPE,
        TAILORING_BASELINE_PATH,
        TAILORING_DIR,
        check_shortcuts,
        load_deltas,
        load_tailoring_baseline,
    )

    tailoring_dir = REPO_ROOT / TAILORING_DIR
    result = load_deltas(REPO_ROOT)
    for warning in result.warnings:
        typer.secho(f"  {warning}", fg=typer.colors.YELLOW)

    trigger_set = result.trigger_set
    typer.echo(
        f"{len(trigger_set.positives)} governing delta(s), "
        f"{len(trigger_set.negatives)} matched delta(s)"
    )

    findings = check_shortcuts(trigger_set, tailoring_dir / "index.yaml")
    baseline = load_tailoring_baseline(REPO_ROOT)
    issues, deferred = apply_corpus_baseline(
        [(CORPUS_SCOPE, finding) for finding in findings],
        baseline,
        baseline_path=TAILORING_BASELINE_PATH,
    )

    for item in deferred:
        typer.secho(f"  known-open (baselined): {item}", fg=typer.colors.YELLOW)

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


def _gather_git_facts(runs: list[ProvenanceRun]) -> GitFacts:
    """Collect the commit facts the provenance gate needs.

    Shelled out for here rather than inside :mod:`decision_evals.provenance`, so
    that every refusal branch in that module stays testable without a fixture
    repository — the same split :class:`~decision_evals.prereg.RepoState` uses.

    When git is unavailable the commit-order rule is skipped rather than
    failed. A source tarball is not a defective run record, and a gate that
    fails on unpacking is a gate somebody turns off.
    """
    if not (REPO_ROOT / ".git").exists() or _git_output(["rev-parse", "HEAD"]) is None:
        return GitFacts(available=False, first_commit={}, ancestry=frozenset())

    first_commit: dict[str, str] = {}
    pairs: set[tuple[str, str]] = set()
    for run in runs:
        if not run.readme.is_file():
            continue
        text = run.readme.read_text(encoding="utf-8")
        for link in prediction_links(text):
            if link not in first_commit:
                # --diff-filter=A lists the commits that *added* the path; the
                # last line is the earliest, which is when it was registered.
                log = _git_output(["log", "--diff-filter=A", "--format=%h", "--", link])
                if log:
                    first_commit[link] = log.splitlines()[-1].strip()
            added = first_commit.get(link)
            if added and run.commit and _is_ancestor(added, run.commit):
                pairs.add((added, run.commit))
    return GitFacts(available=True, first_commit=first_commit, ancestry=frozenset(pairs))


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    """Whether one commit is an ancestor of another, or the same commit.

    ``git merge-base --is-ancestor`` treats a commit as its own ancestor, which
    is what lets a run register its prediction in the very commit it runs at —
    the normal case here, and correct: the prediction is still in the tree
    before the data exists.
    """
    try:
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
    except OSError:
        return False
    return completed.returncode == 0


def check_provenance_step() -> StepResult:
    """Every published run states its answer key and registered its prediction.

    Added 2026-08-13. The run READMEs were the only part of the method with no
    gate: everything around them is checked while the record of what was run,
    against which labels, and what was predicted first was maintained by
    remembering. Three defects of that shape are already on the record, and the
    one this gate cannot repair is baselined by name.
    """
    name = "run provenance"
    _echo_header(name)

    runs, baselined = provenance_census(REPO_ROOT)
    typer.echo(f"{runs} published run(s), {baselined} baselined")

    issues = check_provenance(REPO_ROOT, _gather_git_facts(discover_runs(REPO_ROOT)))

    if not index_is_current(REPO_ROOT):
        typer.secho(
            f"  {INDEX_PATH} is stale. Run `de index`. It is generated so that it "
            "cannot drift the way a hand-maintained index does.",
            fg=typer.colors.RED,
        )
        issues = [*issues, ProvenanceIssue(INDEX_PATH, "stale")]

    if not issues:
        return StepResult(name, True)
    for issue in issues:
        if issue.run != INDEX_PATH:
            typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


def check_site_step() -> StepResult:
    """The published site is not older than the documents it publishes.

    The site renders the markdown in this repository in place rather than
    copying it, which is what stops a second copy of `STATUS.md` existing to
    disagree with the first -- and what makes every build a snapshot that goes
    stale silently. Same treatment as `docs/RUN_INDEX.md`: generated by a
    command, refused when it drifts.
    """
    name = "site"
    _echo_header(name)

    if not site_present(REPO_ROOT):
        typer.echo("no site/ directory yet; nothing to gate")
        return StepResult(name, True)

    inputs, changed = site_census(REPO_ROOT)
    typer.echo(f"{inputs} input file(s), {changed} changed since the last build")

    issues = check_site(REPO_ROOT)
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


@app.command()
def site() -> None:
    """Build the site and record what it was built from.

    The manifest is written **after** a successful build, never before: a
    manifest recorded against a build that failed is a green gate over a site
    that does not exist.
    """
    site_dir = REPO_ROOT / SITE_DIR_NAME
    if not site_dir.is_dir():
        typer.secho(f"{SITE_DIR_NAME}/ does not exist.", fg=typer.colors.RED)
        raise typer.Exit(1)

    npm = shutil.which("npm")
    if npm is None:
        typer.secho(
            "npm is not on PATH. The site is an Astro project, so building it "
            "needs Node. `de check` runs without it -- the staleness gate is "
            "pure Python -- but satisfying that gate after editing a document "
            "does not.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    if not (site_dir / "node_modules").is_dir():
        typer.echo("installing site dependencies")
        if subprocess.run([npm, "ci"], cwd=site_dir, check=False).returncode != 0:
            typer.secho("npm ci failed", fg=typer.colors.RED)
            raise typer.Exit(1)

    # Astro caches rendered markdown, and that cache does not notice a changed
    # remark plugin -- it will happily serve pages rendered by the previous
    # version of the link rewriter. Clear it, or the build is a guess.
    for stale in (site_dir / ".astro-cache", site_dir / ".astro", site_dir / "dist"):
        if stale.is_dir():
            shutil.rmtree(stale)

    typer.echo("building")
    if subprocess.run([npm, "run", "build"], cwd=site_dir, check=False).returncode != 0:
        typer.secho("the site build failed; the manifest is unchanged", fg=typer.colors.RED)
        raise typer.Exit(1)

    target = REPO_ROOT / SITE_MANIFEST_PATH
    target.write_text(render_manifest(REPO_ROOT), encoding="utf-8", newline="\n")
    typer.secho(f"wrote {SITE_MANIFEST_PATH}", fg=typer.colors.GREEN)
    typer.echo("not published. Publishing happens on push to `main`; see `de deployed`.")


@app.command()
def deployed() -> None:
    """Report whether the published site is a build of the current `main`.

    Online, and deliberately not a `de check` step. That gate is offline and
    deterministic by design; a step that reaches the network would fail on a
    plane and turn a refusal into a coin toss.
    """
    state = check_deployed(REPO_ROOT)
    colour = {
        DEPLOY_CURRENT: typer.colors.GREEN,
        DEPLOY_BEHIND: typer.colors.RED,
    }.get(state.status, typer.colors.YELLOW)
    typer.secho(str(state), fg=colour)
    if state.exit_code:
        raise typer.Exit(state.exit_code)


@app.command()
def index() -> None:
    """Regenerate `docs/RUN_INDEX.md` from the published run records."""
    target = REPO_ROOT / INDEX_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_index(REPO_ROOT), encoding="utf-8", newline="\n")
    typer.secho(f"wrote {INDEX_PATH}", fg=typer.colors.GREEN)


def _governed_commits() -> list[GovernedCommit]:
    """Commits that touched the answer key or the shipped skill.

    Empty outside a git repository, which makes the step a no-op rather than a
    failure — a source tarball has no history to check against.
    """
    log = _git_output(["log", "--format=%h|%ad|%s", "--date=short", "--", *DECISION_PATHS])
    if not log:
        return []
    commits: list[GovernedCommit] = []
    for line in log.splitlines():
        sha, _, rest = line.partition("|")
        date, _, subject = rest.partition("|")
        if sha and date:
            commits.append(GovernedCommit(sha=sha, date=date, subject=subject))
    return commits


def check_decisions_step() -> StepResult:
    """Every change to the answer key or the shipped skill is explained.

    Added 2026-08-13. Maintainer rationale was recorded in commit bodies, which
    are good and are not greppable by topic. A label move is invisible in a
    checkpoint and shifts every number computed from it, so the reasoning has to
    live somewhere a reader of the numbers can reach.
    """
    name = "decision register"
    _echo_header(name)

    governed = _governed_commits()
    commits, entries, baselined = decisions_census(REPO_ROOT, governed)
    typer.echo(f"{commits} governed commit(s), {entries} entries, {baselined} baselined")

    issues = check_decisions(REPO_ROOT, governed)
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


def check_corrections_step() -> StepResult:
    """Every version the answer key has reached says which labels moved into it.

    Added 2026-08-20. ``set_version`` says *that* the labels changed and
    ``label_versions_comparable`` refuses a comparison across the boundary;
    neither says *which* label moved. That lived in ``docs/DECISIONS.md`` as
    prose, which a reader of the numbers cannot join against a record, and in
    commit bodies, which cannot be amended here.

    The corpus version is the highest any trigger set on disk declares, because
    two sets live here -- the version 2 file every published Track L and Track M
    number was measured on, and the version 4 directory. A gate keyed to one of
    them would stop noticing the other.
    """
    name = "label corrections"
    _echo_header(name)

    from decision_evals.corrections import census, check_corrections
    from decision_evals.triggers import TRIGGERS_DIR, TriggerSetError, load_trigger_set

    triggers_dir = REPO_ROOT / TRIGGERS_DIR
    versions = []
    for path in (*sorted(triggers_dir.glob("*.yaml")), *sorted(triggers_dir.glob("*/index.yaml"))):
        try:
            versions.append(load_trigger_set(path).version)
        except TriggerSetError:
            # Reported with its reason by `check_triggers_step`. A set that will
            # not load contributes no version rather than failing this step too.
            continue
    # `None`, not 1, when nothing loaded. A corpus file that will not load is
    # the trigger-set step's finding; defaulting here would report every line
    # on disk as ahead of a corpus nobody could read.
    corpus_version = max(versions) if versions else None

    lines, moved, accounted = census(REPO_ROOT)
    at = "version unreadable" if corpus_version is None else f"at version {corpus_version}"
    typer.echo(
        f"corpus {at}; {lines} line(s), {moved} moved label(s), "
        f"{accounted} version(s) accounted for"
    )

    issues = check_corrections(REPO_ROOT, corpus_version)
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


def check_wiring_step() -> StepResult:
    """Every module with a coverage floor is reachable from an entry point.

    Added 2026-08-13, after ``prereg.py`` was found carrying a 100% line and
    branch floor under the heading "Integrity locks" with no caller anywhere,
    while ``CLAUDE.md`` recorded four pre-registration slips its refusal
    branches exist to prevent. A tested refusal that nothing calls is inert,
    and nothing in the gate distinguished it from a working one.
    """
    name = "integrity wiring"
    _echo_header(name)

    floored, reachable, declared = census_wiring(REPO_ROOT)
    typer.echo(f"{floored} floored module(s), {reachable} reachable, {declared} declared unwired")

    issues = check_wiring(REPO_ROOT)
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


def check_checkpoints_step() -> StepResult:
    """No two checkpoints disagree about the answer key without a way through.

    Added 2026-08-13. ``trigger_arms.label_versions_comparable`` was written
    that morning to refuse a comparison spanning the label move, and it works —
    it refuses **every** published cross-arm pairing, because nine checkpoints
    carried no ``set_version`` at all and two carried 2. The guard was built and
    the records were never reconciled, so the refusal had no remedy on disk and
    nothing said so.

    An unstamped record is the part to make loud. It reads as version 1 at
    comparison time, which is true, and as nothing at all to every other reader,
    which is how a v1 arm ends up in a table headed v2. So every row declares
    its key, and an older arm that shares cases with a newer one carries a
    re-scored bridge beside it.
    """
    name = "checkpoint label versions"
    _echo_header(name)

    checkpoints = sorted((REPO_ROOT / CHECKPOINT_DIR).glob("*.jsonl"))
    typer.echo(f"{len(checkpoints)} file(s) under {CHECKPOINT_DIR}/")

    issues = check_checkpoints(REPO_ROOT)
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


@app.command()
def rescore() -> None:
    """Stamp every checkpoint with its answer key, and bridge the older ones.

    Makes no model calls. Re-scoring reads the verdict a model already produced
    and joins it to a different label, so an arm can be brought onto the current
    key for nothing — and the rows it writes say on every line that no call was
    made for them.
    """
    try:
        written = reconcile(REPO_ROOT, load_declared_versions(REPO_ROOT))
    except RescoreError as error:
        typer.secho(str(error), fg=typer.colors.RED)
        raise typer.Exit(1) from error
    for path in written:
        typer.echo(f"wrote {path}")
    typer.secho(f"{len(written)} file(s) written. No model call was made.", fg=typer.colors.GREEN)


def check_docs_step() -> StepResult:
    """Every command and path the living documentation names actually exists.

    Added 2026-08-13, after an audit found the README telling readers to run
    ``de screen`` and ``de confirm`` -- neither a command -- and advertising a
    ``preregistration/`` directory that has never existed, while omitting
    ``paper/`` and ``scripts/``. ``SCORECARD.md`` had already corrected a
    fourth of the same shape, ``de report``. Four instances, none caught by
    anything, because documentation was the last obligation here checked by
    reading it.

    Registered limitation: this reads whether a reference resolves, never
    whether the sentence around it is true. ``docs/PROTOCOL.md`` §3 described a
    refusal that had never run, in the present indicative, with every path in
    it correct. That defect is invisible to this step.
    """
    name = "documentation"
    _echo_header(name)

    files, components, indexed, absent, external = docs_census(REPO_ROOT)
    typer.echo(
        f"{files} living doc(s), {components} component(s) listed, "
        f"{indexed} indexed under docs/, "
        f"{absent} command(s) declared absent, {external} path(s) declared external"
    )

    commands = {
        command.name or (command.callback.__name__ if command.callback else "")
        for command in app.registered_commands
    }
    issues = check_docs(REPO_ROOT, commands - {""})
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
    return StepResult(name, False, f"{len(issues)} issue(s)")


def check_claims_step() -> StepResult:
    """Every measured number the site publishes still says what its source says.

    Added 2026-08-19, after the landing page was found offering four procedures
    against a skill that routes to six, hardcoding thirteen published runs
    while another page on the same site derived twelve, and republishing an
    "about six points" figure that ``docs/STATUS.md`` had retracted six days
    earlier. None of it was catchable: ``docs.py`` scans ``*.md`` and
    ``docs/*.md`` and never opens an ``.astro`` file, and ``site.py`` hashes
    the page for staleness without reading a word of it. Worse, the existing
    gate laundered it -- editing ``SKILL.md`` made the manifest stale, ``de
    site`` rehashed, and the wrong page republished green.

    Runs in ``--fast``. Unlike the site step it needs no Node toolchain, and it
    is the check most likely to fire on a routine edit to ``docs/STATUS.md``,
    which is when the fix is cheapest.

    Registered limitation: this binds a number to a sentence and cannot tell
    whether that sentence is still the document's answer. ``docs/STATUS.md``
    corrects by appending and holds four true totals at once. ``latest``
    narrows that where a correction takes a recognisable numeric shape and does
    nothing where it is phrased in words. The ``retractions`` register is the
    manual remedy, so the hole closes one commit late.

    A second gap, found on the day this shipped: the register cannot tell a
    published claim from a comment describing one, so a page documenting a
    retraction is refused for naming it. There is no exemption table for that
    yet. Reword the comment; do not reprint the retracted phrase.
    """
    name = "published claims"
    _echo_header(name)

    claims, retractions, pages = claims_census(REPO_ROOT)
    typer.echo(f"{claims} claim(s), {retractions} retraction(s), {pages} page(s) scanned")

    issues = check_claims(REPO_ROOT)
    if not issues:
        return StepResult(name, True)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED)
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
#:
#: **233 and 527 do not exclude the same thing, and 233 is not A2's n.** 527
#: drops `code`; 233 does not, and every other line in Track A treats `code` as
#: ungradable on this stack. The 6-turn stratum without `code` is **212**, and
#: restricted to the three families A1 established as gradable it is **103** at
#: 4 turns. Recounted off `datasets/vendor/sharded_instructions_600.json` on
#: 2026-08-18; see the A-track table in `docs/RESEARCH_PROGRAMME.md`. The rows
#: are left as they are because `de power` prices item counts rather than
#: naming an experiment's n, and changing them would move a published table.
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
