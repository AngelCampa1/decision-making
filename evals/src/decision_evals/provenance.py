"""Provenance of published run records.

Every number this repository shows a reader lives in a
``results/<skill>/<date>-<sha7>[-slug]/README.md``. Those READMEs are the best
documentation in the repository and they were, until this module existed, the
only part of the method with **no gate at all**. Everything around them is
checked — lint, types, citations, trigger sets, coverage floors — while the
record of *what was run, against which labels, and what was predicted first*
was maintained entirely by remembering.

Remembering did not work. Three defects of exactly this shape are already on
the record:

- **A run with no registered bands.** ``results/decision-making/2026-08-12-40b6ba5/``
  is 365 calls published with a write-up and no prediction. It is the run
  ``CLAUDE.md`` describes as "launched with no bands at all", and it is the one
  run in ``results/`` this gate refuses.
- **A prediction written after its run had started.** Nothing in a file records
  when it was written, so the check is the commit graph: the prediction's
  first commit must be an ancestor of the commit the run was made at. A
  prediction that cannot be shown to predate its data is not evidence, it is a
  story with a date on it.
- **An answer key that moved under finished results.** On 2026-08-13 one turn
  moved from the positives to the negatives and recall rose on every arm on
  disk with **no call re-made**. :func:`~decision_evals.trigger_arms.label_versions_comparable`
  now guards the JSONL. It cannot guard the prose, and the prose is what gets
  quoted — so a README must state the answer-key version its numbers were
  computed under, and that statement must match the records in the same
  directory.

The last rule is the one worth stating plainly: **this module binds the prose
to the data.** A README claiming v1 beside records stamped v2 is the exact
construction that produced five unearned points of recall, and it is invisible
to every other check in the gate.

**The baseline is the citations baseline, with the same semantics.** Runs
published before the convention existed are exempt by name, each with a written
reason, and the list *may only shrink* — a baseline that does not shrink when
work is done has stopped measuring anything.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: Published run records live two levels under here: ``<skill>/<run>/``. The
#: live checkpoint directories (``results/triggers/``, ``results/track-a/``,
#: and friends) are files one level down and are gitignored, so this shape
#: excludes them without naming them.
RESULTS_ROOT: Final = "results"

#: Runs published before this gate existed, one per line, ``#`` for comments.
BASELINE_PATH: Final = "results/provenance-baseline.txt"

#: A run directory names the day it ran and the commit the code was at.
#: The commit is not decoration: it is what makes rule 6 checkable at all.
_RUN_DIR: Final = re.compile(r"^(\d{4}-\d{2}-\d{2})-([0-9a-f]{7})(?:-[a-z0-9-]+)?$")

#: ``**Answer key:** `datasets/triggers/decision-making.yaml` v1``
_ANSWER_KEY: Final = re.compile(
    r"^\*\*Answer key:\*\*\s*\[?`?(?P<path>[^`\]\s]+)`?\]?[^\n]*?\bv(?P<version>\d+)\b",
    re.MULTILINE,
)

#: ``Prediction: [`notebook/....md`](../../../notebook/....md).``
_PREDICTION: Final = re.compile(r"^Prediction:[^\n]*?(notebook/[a-z0-9-]+\.md)", re.MULTILINE)

#: ``Outcome:`` and ``Write-up:`` both name where the run was read.
_OUTCOME: Final = re.compile(
    r"^(?:Outcome|Write-up):[^\n]*?(notebook/[a-z0-9-]+\.md)", re.MULTILINE
)

#: The generated cross-reference. Hand-maintained indexes drift — ``STATUS.md``
#: says so about itself, and ``SCORECARD.md`` carries a note about a status file
#: that claimed to be generated and was not.
INDEX_PATH: Final = "docs/RUN_INDEX.md"

#: Any notebook path linked from a README, for the dead-link check.
_NOTEBOOK_LINK: Final = re.compile(r"notebook/[a-z0-9-]+\.md")

#: Records written before the field existed are version 1, which is what they
#: are. Matches :func:`~decision_evals.trigger_arms.label_versions_comparable`;
#: the two must agree or a run passes one check and fails the other.
DEFAULT_SET_VERSION: Final = 1


class ProvenanceError(ValueError):
    """A published run record could not be read."""


@dataclass(frozen=True)
class ProvenanceIssue:
    """One provenance defect, located precisely enough to fix without searching."""

    run: str
    message: str

    def __str__(self) -> str:
        return f"{self.run}: {self.message}"


@dataclass(frozen=True)
class RunRecord:
    """A published run directory, reduced to what the gate checks."""

    #: Repo-relative path, forward slashes on every platform.
    path: str
    #: The directory's own name, which is also its baseline key.
    name: str
    readme: Path
    jsonl: tuple[Path, ...]

    @property
    def commit(self) -> str | None:
        """The abbreviated commit in the directory name, if it is well-formed."""
        matched = _RUN_DIR.match(self.name)
        return matched.group(2) if matched else None


def prediction_links(text: str) -> list[str]:
    """Notebook entries a README registers as its prediction.

    Only the labelled ``Prediction:`` line counts. Taking the first notebook
    link in the file instead reads a passing citation as a registration, which
    is wrong in the direction that matters: it would pass a run that never
    registered anything.
    """
    return sorted(set(_PREDICTION.findall(text)))


@dataclass(frozen=True)
class GitFacts:
    """Git answers the gate needs, gathered by the caller.

    Passed in rather than shelled out for here, so every refusal branch is
    testable without a fixture repository — the same reason
    :class:`~decision_evals.prereg.RepoState` exists, and the reason this
    module can carry a branch-coverage floor.
    """

    #: Whether git was available and the repository readable at all. When
    #: false, the commit-order rule is skipped rather than failed: a source
    #: tarball is not a defective run record.
    available: bool
    #: Path -> abbreviated commit that first added it. Missing means untracked.
    first_commit: dict[str, str]
    #: ``(ancestor, descendant)`` pairs known to hold. A commit is its own
    #: ancestor, which is what lets a run register its prediction in the same
    #: commit that runs it.
    ancestry: frozenset[tuple[str, str]]


def discover_runs(repo_root: Path) -> list[RunRecord]:
    """Every published run directory, sorted.

    A directory qualifies by *position* — ``results/<skill>/<run>/`` — not by
    what it contains. Qualifying on "has a README" would let a run escape the
    gate by omitting the file the gate exists to check.
    """
    root = repo_root / RESULTS_ROOT
    if not root.is_dir():
        return []
    runs: list[RunRecord] = []
    for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for run_dir in sorted(p for p in skill_dir.iterdir() if p.is_dir()):
            runs.append(
                RunRecord(
                    path=f"{RESULTS_ROOT}/{skill_dir.name}/{run_dir.name}",
                    name=run_dir.name,
                    readme=run_dir / "README.md",
                    jsonl=tuple(sorted(run_dir.glob("*.jsonl"))),
                )
            )
    return runs


def record_versions(path: Path) -> set[int]:
    """The answer-key versions stamped into one JSONL file.

    Unparseable lines are skipped rather than raised on. A malformed record is
    a defect this gate is not the right place to report, and refusing to read
    the file would hide the version mismatch it *is* the right place to report.
    """
    versions: set[int] = set()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProvenanceError(f"{path}: {exc}") from exc
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            raw = row.get("set_version", DEFAULT_SET_VERSION)
            if isinstance(raw, int):
                versions.add(raw)
    return versions


def check_run(run: RunRecord, repo_root: Path, git: GitFacts) -> list[ProvenanceIssue]:
    """Apply every provenance rule to one run directory."""
    issues: list[ProvenanceIssue] = []

    matched = _RUN_DIR.match(run.name)
    if matched is None:
        issues.append(
            ProvenanceIssue(
                run.path,
                "directory name must be `<YYYY-MM-DD>-<sha7>[-slug]`. The commit is what "
                "lets a reader check that the prediction predates the data; without it "
                "the run's own claim to be pre-registered is unfalsifiable.",
            )
        )

    if not run.readme.is_file():
        issues.append(
            ProvenanceIssue(
                run.path,
                "has no README.md. A JSONL file with no record of what was run, against "
                "which labels, and what was predicted first is data nobody can read.",
            )
        )
        return issues

    text = run.readme.read_text(encoding="utf-8")
    issues += _check_answer_key(run, text)
    issues += _check_prediction(run, text, repo_root, git, matched)
    issues += _check_links(run, text, repo_root)
    return issues


def _check_answer_key(run: RunRecord, text: str) -> list[ProvenanceIssue]:
    """The README states its answer-key version, and the records agree."""
    declared = _ANSWER_KEY.search(text)
    if declared is None:
        return [
            ProvenanceIssue(
                run.path,
                "README has no `**Answer key:**` line naming the label set and its "
                "version. On 2026-08-13 one label moved and recall rose on every arm on "
                "disk with no call re-made; an unversioned number cannot be compared "
                "with anything, including a later version of itself.",
            )
        ]

    version = int(declared.group("version"))
    issues: list[ProvenanceIssue] = []
    for path in run.jsonl:
        found = record_versions(path)
        mismatched = found - {version}
        if mismatched:
            issues.append(
                ProvenanceIssue(
                    run.path,
                    f"README declares answer key v{version} but `{path.name}` carries "
                    f"{sorted(found)}. The prose and the data disagree about which labels "
                    "produced these numbers, which is the exact construction that put "
                    "five unearned points of recall on the shipped skill.",
                )
            )
    return issues


def _check_prediction(
    run: RunRecord,
    text: str,
    repo_root: Path,
    git: GitFacts,
    matched: re.Match[str] | None,
) -> list[ProvenanceIssue]:
    """A prediction exists, and its commit predates the run's code."""
    found = _PREDICTION.search(text)
    if found is None:
        return [
            ProvenanceIssue(
                run.path,
                "README has no `Prediction:` line linking a notebook entry. A prediction "
                "written before the data arrives is evidence; the same claim written "
                "afterwards is a story, and only the commit graph tells them apart.",
            )
        ]

    prediction = found.group(1)
    if not (repo_root / prediction).is_file():
        return [ProvenanceIssue(run.path, f"prediction `{prediction}` does not exist")]

    if not git.available or matched is None:
        return []

    run_commit = matched.group(2)
    prediction_commit = git.first_commit.get(prediction)
    if prediction_commit is None:
        return [
            ProvenanceIssue(
                run.path,
                f"prediction `{prediction}` is not committed, so nothing establishes that "
                "it predates the run. Commit it before publishing the result.",
            )
        ]
    if (prediction_commit, run_commit) not in git.ancestry:
        return [
            ProvenanceIssue(
                run.path,
                f"prediction `{prediction}` was first committed at {prediction_commit}, "
                f"which is not an ancestor of the run's commit {run_commit}. The "
                "prediction does not predate the run it claims to have registered.",
            )
        ]
    return []


def _check_links(run: RunRecord, text: str, repo_root: Path) -> list[ProvenanceIssue]:
    """Every notebook entry the README points at exists.

    Cheap, and it is the failure that makes an archive rot: a run record whose
    write-up has been renamed is a number with no reasoning attached.
    """
    return [
        ProvenanceIssue(run.path, f"links `{link}`, which does not exist")
        for link in sorted(set(_NOTEBOOK_LINK.findall(text)))
        if not (repo_root / link).is_file()
    ]


def load_baseline(repo_root: Path) -> set[str]:
    """Run directory names exempted from the gate.

    Exempt, **and it may only shrink** — see :func:`check_provenance`. The
    alternative considered and rejected was reporting legacy runs as warnings,
    which is how the citations backlog would have been handled if anyone had
    wanted it ignored.
    """
    path = repo_root / BASELINE_PATH
    if not path.is_file():
        return set()
    return {
        stripped
        for line in path.read_text(encoding="utf-8").splitlines()
        if (stripped := line.split("#", 1)[0].strip())
    }


def check_provenance(repo_root: Path, git: GitFacts) -> list[ProvenanceIssue]:
    """Validate every published run record.

    Returns the issues that should fail the build: everything not covered by
    the baseline, plus any baseline entry that has gone stale.
    """
    runs = discover_runs(repo_root)
    found: list[ProvenanceIssue] = []
    for run in runs:
        found += check_run(run, repo_root, git)

    baseline = load_baseline(repo_root)
    by_name = {run.path: run.name for run in runs}
    issues = [issue for issue in found if by_name.get(issue.run, issue.run) not in baseline]

    offending = {by_name.get(issue.run, issue.run) for issue in found}
    known = {run.name for run in runs}
    for name in sorted(baseline - offending):
        reason = (
            "is baselined but has no outstanding issue. Delete the line."
            if name in known
            else "is baselined but names no run directory. Delete the line."
        )
        issues.append(
            ProvenanceIssue(
                BASELINE_PATH,
                f"`{name}` {reason} A baseline that does not shrink when work is done has "
                "stopped measuring anything.",
            )
        )
    return issues


def outcome_links(text: str) -> list[str]:
    """Notebook entries a README names as where its result was read."""
    return sorted(set(_OUTCOME.findall(text)))


def render_index(repo_root: Path) -> str:
    """The run/notebook cross-reference, derived entirely from disk.

    Linkage in this repository runs one way. A run README names its prediction
    and its outcome; the notebook entries name no run, so **from a finding you
    cannot reach the data behind it** — which is the direction anyone re-reading
    a result actually travels, and the direction three scorer defects here were
    only caught by travelling.

    Generated rather than written, and checked for staleness by ``de check``.
    The alternative is another hand-maintained index, and this repository has
    already learned what those are worth: ``docs/STATUS.md`` carries a note
    saying it is maintained by hand, because an earlier status file claimed to
    be generated and was not.
    """
    runs = discover_runs(repo_root)
    baseline = load_baseline(repo_root)

    lines = [
        "# Run index",
        "",
        "**Audience:** the record.",
        "",
        "**Generated by `de index`. Do not edit.** `de check` fails when this file",
        "is stale, so a run that is published without appearing here is a failing",
        "build rather than a gap somebody notices later.",
        "",
        "Run READMEs link forward to their prediction and outcome. Nothing linked",
        "back, so from a finding you could not reach the data behind it. This is",
        "that direction.",
        "",
        "## Published runs",
        "",
        "| run | answer key | prediction | outcome |",
        "|---|---|---|---|",
    ]

    reverse: dict[str, list[str]] = {}
    for run in runs:
        text = run.readme.read_text(encoding="utf-8") if run.readme.is_file() else ""
        declared = _ANSWER_KEY.search(text)
        version = f"v{declared.group('version')}" if declared else "—"
        predictions = prediction_links(text)
        outcomes = outcome_links(text)
        note = " *(baselined)*" if run.name in baseline else ""
        lines.append(
            f"| [`{run.name}`](../{run.path}/){note} | {version} | "
            f"{_cell(predictions)} | {_cell(outcomes)} |"
        )
        for link in predictions + outcomes:
            reverse.setdefault(link, []).append(run.path)

    lines += [
        "",
        "## Notebook entry to run",
        "",
        "| notebook entry | run |",
        "|---|---|",
    ]
    for link in sorted(reverse):
        targets = " ".join(
            f"[`{Path(path).name}`](../{path}/)" for path in sorted(set(reverse[link]))
        )
        lines.append(f"| [`{Path(link).name}`](../{link}) | {targets} |")

    return "\n".join(lines) + "\n"


def _cell(links: list[str]) -> str:
    """Render a list of notebook links as one table cell."""
    if not links:
        return "**none**"
    return " ".join(f"[`{Path(link).name}`](../{link})" for link in links)


def index_is_current(repo_root: Path) -> bool:
    """Whether the committed index matches what the tree would generate."""
    path = repo_root / INDEX_PATH
    if not path.is_file():
        return False
    return path.read_text(encoding="utf-8").replace("\r\n", "\n") == render_index(repo_root)


def census(repo_root: Path) -> tuple[int, int]:
    """``(runs, baselined)``.

    Printed by the gate rather than asserted in prose, for the reason two
    hand-counted citation totals were both wrong: the figure moves with which
    directories you happen to glob.
    """
    return len(discover_runs(repo_root)), len(load_baseline(repo_root))
