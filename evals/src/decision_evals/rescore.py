"""Reading an old checkpoint under a newer answer key, and refusing to hide it.

On 2026-08-13 one turn moved from the positives to the negatives. Recall rose 3
to 5 points on every arm on disk, not one call was re-made, and
:func:`~decision_evals.trigger_arms.label_versions_comparable` was written the
same morning to refuse a comparison spanning the change.

**The guard was built and the records were never reconciled.** Nine checkpoints
in ``results/triggers/`` carried no ``set_version`` at all, two carried 2, and
the guard's "one stamped, one not" branch refuses every pair across that line —
including the pairing an unstarted pre-registration was about to use as its
replication baseline. A refusal nobody can satisfy is not a gate, it is a wall,
and the way through it is arithmetic rather than a run: the verdict a model
produced (``fired``, ``procedure``) does not depend on the label it was scored
against, so a checkpoint can be re-scored under a later key for free.

Two rules follow, and this module is both of them.

**A re-scored row must never be mistakable for a call.** The improvement from
re-scoring is real as a label correction and would be a fabrication as a model
result, and nothing in a JSONL record separated those two readings. So a
re-scored row carries ``record_kind: "rescore"``, the checkpoint it came from,
and the version it came from — per row, not per file name, because the unit a
script or a reader meets is one line. The file name says it too, with a
``rescored-`` prefix, so a path alone is enough to tell the two apart.

**Every unstamped row gets its version written down.** ``set_version`` defaulted
to 1 at comparison time, which told the truth but told it silently: an unstamped
record and a stamped one look the same to anything that is not the guard, and
the check below can therefore say nothing about a file that never declares
itself. The nine unstamped checkpoints were confirmed to be version 1 from the
labels baked into their own rows — every one of them carries ``x-n21`` as a
positive, which is the version 1 key and not the version 2 one — rather than
from their timestamps.

What is *not* re-scored is ``covers``. It is a function of the arm's entry
partition, which the record does not carry, as well as of the labelled route.
Where a case's acceptable routes are unchanged the stored value is still right
and is kept; where they changed it is set to ``None`` and the row says why, so
:func:`~decision_evals.trigger_arms.covers_rates` reports a smaller denominator
visibly instead of a wrong rate silently.
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Final

from decision_evals.triggers import TRIGGERS_DIR, TriggerSet, TriggerSetError, load_trigger_set

#: One checkpoint row. Deliberately a bare mapping: the runner writes whatever
#: the arm needed and this module must not silently drop a column it does not
#: know about.
Record = dict[str, Any]

#: Where run checkpoints live, relative to the repository root.
CHECKPOINT_DIR: Final = "results/triggers"

#: Re-scored copies, distinguished by a name prefix rather than a subdirectory.
#: ``provenance.discover_runs`` qualifies a published run **by position** —
#: anything at ``results/<skill>/<dir>/`` is a run and owes a dated name, a
#: README and a pre-registration — so a folder here would have been read as an
#: undated run with no prediction behind it. The prefix keeps the distinction in
#: the one place every reader of a path already looks.
RESCORED_PREFIX: Final = "rescored-"

#: The value in ``record_kind`` that means *no call was made for this row*.
RESCORE_KIND: Final = "rescore"

#: Not a checkpoint: the blind-adjudication ledger, which has no verdicts in it.
NOT_A_CHECKPOINT: Final = frozenset({"adjudication.jsonl"})

#: ``pyproject.toml`` table naming the version each pre-versioning checkpoint was
#: scored against. A register rather than an argument, and it may only shrink:
#: the fact is a derivation somebody performed once and it has to be written
#: where the derivation can be read, not passed on a command line.
VERSIONS_TABLE: Final = ("tool", "decision-evals", "unstamped-checkpoints")


class RescoreError(ValueError):
    """A checkpoint cannot be re-scored against the key it was given."""


@dataclass(frozen=True)
class CheckpointIssue:
    """One defect in the checkpoint directory."""

    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def stamp(rows: Iterable[Record], version: int) -> list[Record]:
    """Write ``set_version`` onto rows that carry none.

    Raises:
        RescoreError: if a row already declares a different version. Overwriting
            it would be the defect this module exists for, performed by the
            module written to prevent it.
    """
    stamped: list[Record] = []
    for row in rows:
        declared = row.get("set_version")
        if declared is not None and int(declared) != version:
            raise RescoreError(
                f"case {row.get('case')!r} already declares set_version {declared}, "
                f"and stamping it {version} would overwrite the one fact that says "
                "which answer key produced this verdict"
            )
        stamped.append({**row, "set_version": version})
    return stamped


def rescore(rows: Iterable[Record], trigger_set: TriggerSet, *, source: str) -> list[Record]:
    """The same verdicts, scored against ``trigger_set`` instead.

    No call is made and no verdict is touched: ``fired`` and ``procedure`` are
    what the model produced and do not depend on the key. What changes is
    ``should_fire``, ``route`` and ``set_version`` — the label columns — and
    every returned row is marked as a re-score.

    Args:
        rows: A run checkpoint, already stamped with the version it was scored
            against.
        trigger_set: The key to re-score against.
        source: The checkpoint's file name, written into every row so a reader
            who meets one line can find the calls behind it.

    Raises:
        RescoreError: if the key does not contain a case the checkpoint has a
            verdict for. Dropping it would shrink the denominator invisibly,
            which is this instrument's signature failure.
    """
    cases = {case.id: case for case in trigger_set.cases}
    out: list[Record] = []
    for row in rows:
        case_id = str(row.get("case"))
        case = cases.get(case_id)
        if case is None:
            raise RescoreError(
                f"{source}: case {case_id!r} is not in the {trigger_set.skill} set at "
                f"version {trigger_set.version}. A verdict with no label cannot be "
                "re-scored, and dropping it would shrink the denominator silently"
            )
        rescored: Record = {
            **row,
            "should_fire": case.should_fire,
            "route": case.route,
            "set_version": trigger_set.version,
            "record_kind": RESCORE_KIND,
            "rescored_from": source,
            "rescored_from_set_version": row.get("set_version"),
        }
        if row.get("covers") is not None and case.routes != (row.get("route"),):
            rescored["covers"] = None
            rescored["covers_stale"] = (
                "the acceptable routes for this case changed with the key, and `covers` "
                "depends on the arm's entry partition, which the record does not carry"
            )
        out.append(rescored)
    return out


def rescored_name(source: str, version: int) -> str:
    """File name for ``source`` re-scored to ``version``.

    The version is in the name as well as in every row because the obligation
    this module enforces is checked by looking for a file, and a name that did
    not say which key it targets would satisfy the check twice.
    """
    return f"{RESCORED_PREFIX}{Path(source).stem}-v{version}.jsonl"


def read_jsonl(path: Path) -> list[Record]:
    """Every record at ``path``, read as UTF-8.

    The encoding is explicit for the reason ``trigger_arms.load_arm`` gives:
    Windows defaults to cp1252 and a typographic dash in a stored reply raises
    ``UnicodeDecodeError`` halfway through scoring a finished run.
    """
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def write_jsonl(path: Path, rows: Sequence[Record]) -> None:
    """Write records, one per line, creating the directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def load_keys(repo_root: Path) -> list[TriggerSet]:
    """Every trigger set on disk, whatever version it declares.

    A set that will not load is not reported here — ``check_trigger_sets`` owns
    that message and would print it twice.
    """
    triggers = repo_root / TRIGGERS_DIR
    paths = [*sorted(triggers.glob("*.yaml")), *sorted(triggers.glob("*/index.yaml"))]
    sets: list[TriggerSet] = []
    for path in paths:
        try:
            sets.append(load_trigger_set(path))
        except TriggerSetError:
            continue
    return sets


def key_for(keys: Iterable[TriggerSet], version: int, ids: set[str]) -> TriggerSet | None:
    """The set at ``version`` containing every case in ``ids``, if one is on disk."""
    for candidate in keys:
        if candidate.version == version and ids <= {case.id for case in candidate.cases}:
            return candidate
    return None


def load_declared_versions(repo_root: Path) -> dict[str, int]:
    """The register of which key each pre-versioning checkpoint was scored against.

    Empty when the table is absent, which is the state the repository should
    reach: an entry exists only while some checkpoint on disk carries no
    ``set_version``, and stamping one is what deletes its line.
    """
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    node: object = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    for part in VERSIONS_TABLE:
        if not isinstance(node, dict):
            return {}
        node = node.get(part, {})
    return {str(key): int(value) for key, value in node.items()} if isinstance(node, dict) else {}


@dataclass(frozen=True)
class _Checkpoint:
    """A run checkpoint that passed the per-file rules."""

    name: str
    version: int
    ids: set[str]


def check_checkpoints(repo_root: Path) -> list[CheckpointIssue]:
    """Every checkpoint declares its answer key, and no pair spans one silently.

    Five rules, each of which the directory broke on 2026-08-13:

    1. **Every row carries ``set_version``.** The comparison guard defaults an
       absent one to 1, which is true and silent; nothing else can see it.
    2. **A file declares one version.** A checkpoint resumed across a label
       change would carry both, and every rate computed over it would be a
       weighted average of two answer keys.
    3. **A run checkpoint holds no re-scored rows**, so the calls stay
       separable from the arithmetic.
    4. **A re-scored file says so on every row**, names a run checkpoint that
       exists, and still agrees with the key it claims — a re-score goes stale
       the next time a label moves, which is the failure one turn later.
    5. **Two checkpoints that share case ids and disagree about the version
       need a bridge.** Without one the pair is refused by
       ``label_versions_comparable`` and nothing on disk says how to satisfy it.
    """
    directory = repo_root / CHECKPOINT_DIR
    if not directory.is_dir():
        return []
    keys = load_keys(repo_root)

    issues: list[CheckpointIssue] = []
    runs: list[_Checkpoint] = []
    for path in sorted(directory.glob("*.jsonl")):
        if path.name in NOT_A_CHECKPOINT or path.name.startswith(RESCORED_PREFIX):
            continue
        rows = read_jsonl(path)
        version = _single_version(path.name, rows, issues)
        if version is None:
            continue
        if any(row.get("record_kind") == RESCORE_KIND for row in rows):
            issues.append(
                CheckpointIssue(
                    path.name,
                    "is named as a run and holds re-scored rows. A re-score is arithmetic "
                    f"over calls already made; name it {RESCORED_PREFIX}... so nothing "
                    "reads it as a run",
                )
            )
            continue
        runs.append(_Checkpoint(path.name, version, {str(row.get("case")) for row in rows}))

    bridges = _check_rescored(directory, keys, {run.name for run in runs}, issues)
    issues.extend(_check_bridged(runs, bridges))
    return issues


def _single_version(name: str, rows: Sequence[Record], issues: list[CheckpointIssue]) -> int | None:
    """The one version this file declares, or ``None`` with an issue appended."""
    if not rows:
        issues.append(CheckpointIssue(name, "is empty"))
        return None
    unstamped = sum(1 for row in rows if row.get("set_version") is None)
    if unstamped:
        issues.append(
            CheckpointIssue(
                name,
                f"{unstamped} of {len(rows)} row(s) carry no `set_version`. An unstamped "
                "record reads as version 1 at comparison time and as nothing at all to "
                "everything else, which is how a v1 arm got compared with a v2 one. Run "
                "`de rescore`",
            )
        )
        return None
    versions = {int(row["set_version"]) for row in rows}
    if len(versions) > 1:
        issues.append(
            CheckpointIssue(
                name,
                f"mixes label revisions {sorted(versions)}. Every rate over this file is "
                "an average across two answer keys",
            )
        )
        return None
    return versions.pop()


def _check_rescored(
    directory: Path,
    keys: Sequence[TriggerSet],
    run_names: set[str],
    issues: list[CheckpointIssue],
) -> set[tuple[str, int]]:
    """Validate the bridges and return the ``(source, version)`` pairs they cover."""
    bridges: set[tuple[str, int]] = set()
    for path in sorted(directory.glob(f"{RESCORED_PREFIX}*.jsonl")):
        name = path.name
        rows = read_jsonl(path)
        version = _single_version(name, rows, issues)
        if version is None:
            continue
        if any(row.get("record_kind") != RESCORE_KIND for row in rows):
            issues.append(
                CheckpointIssue(
                    name,
                    f"has row(s) without `record_kind: {RESCORE_KIND!r}`. Every row here "
                    "must say that no call was made for it",
                )
            )
            continue
        sources = {str(row.get("rescored_from")) for row in rows}
        if len(sources) != 1 or not sources <= run_names:
            issues.append(
                CheckpointIssue(
                    name,
                    f"names {sorted(sources)} in `rescored_from`, which is not one run "
                    "checkpoint in this directory. A re-score with no calls behind it "
                    "cannot be checked against anything",
                )
            )
            continue
        source = sources.pop()
        if path.name != rescored_name(source, version):
            issues.append(
                CheckpointIssue(
                    name,
                    f"re-scores {source} to version {version} but is not named "
                    f"{rescored_name(source, version)}",
                )
            )
            continue
        issues.extend(_check_labels(name, rows, keys, version))
        bridges.add((source, version))
    return bridges


def _check_labels(
    name: str, rows: Sequence[Record], keys: Sequence[TriggerSet], version: int
) -> list[CheckpointIssue]:
    """The re-scored labels still match the key they claim.

    A re-score is correct on the afternoon it is written and wrong the next time
    a label moves, and it looks exactly the same either way.
    """
    ids = {str(row.get("case")) for row in rows}
    key = key_for(keys, version, ids)
    if key is None:
        return [
            CheckpointIssue(
                name,
                f"claims version {version}, and no trigger set on disk at that version "
                "contains all of its cases, so the labels in it cannot be checked",
            )
        ]
    cases = {case.id: case for case in key.cases}
    stale = sorted(
        {
            str(row["case"])
            for row in rows
            if bool(row.get("should_fire")) != cases[str(row["case"])].should_fire
            or row.get("route") != cases[str(row["case"])].route
        }
    )
    if not stale:
        return []
    return [
        CheckpointIssue(
            name,
            f"disagrees with {key.skill} v{version} on {len(stale)} case(s) "
            f"({', '.join(stale[:5])}). The key moved again after this was written. "
            "Run `de rescore`",
        )
    ]


def _check_bridged(
    runs: Sequence[_Checkpoint], bridges: set[tuple[str, int]]
) -> list[CheckpointIssue]:
    """Any two run checkpoints sharing cases across a version boundary need a bridge."""
    issues: list[CheckpointIssue] = []
    for left, right in combinations(runs, 2):
        if left.version == right.version or not (left.ids & right.ids):
            continue
        older, newer = sorted((left, right), key=lambda run: run.version)
        if (older.name, newer.version) in bridges:
            continue
        issues.append(
            CheckpointIssue(
                older.name,
                f"is version {older.version} and shares {len(left.ids & right.ids)} case(s) "
                f"with {newer.name} at version {newer.version}. `label_versions_comparable` "
                "refuses that pair, and nothing on disk offers a way to satisfy it. Run "
                f"`de rescore` to write {rescored_name(older.name, newer.version)}",
            )
        )
    return issues


def reconcile(repo_root: Path, versions: dict[str, int]) -> list[str]:
    """Stamp every run checkpoint and write the bridges its neighbours need.

    ``versions`` maps a checkpoint file name to the label revision it was scored
    against, for the files that declare none. It is a **required argument with
    no default** on purpose: which key an unstamped record was scored against is
    a fact to be derived from the labels baked into its own rows, and a function
    that guessed would be inventing the parameter that the guard exists to
    protect.

    Returns the paths written, relative to the repository root, in the order
    they were written.
    """
    directory = repo_root / CHECKPOINT_DIR
    keys = load_keys(repo_root)
    written: list[str] = []

    stamped: dict[str, tuple[Path, list[Record], int]] = {}
    for path in sorted(directory.glob("*.jsonl")):
        if path.name in NOT_A_CHECKPOINT or path.name.startswith(RESCORED_PREFIX):
            continue
        rows = read_jsonl(path)
        declared = {row.get("set_version") for row in rows}
        if declared == {None}:
            if path.name not in versions:
                raise RescoreError(
                    f"{path.name} declares no `set_version` and none was supplied. Derive "
                    "it from the labels the runner baked into its own rows and pass it; "
                    "do not let it default"
                )
            rows = stamp(rows, versions[path.name])
            write_jsonl(path, rows)
            written.append(f"{CHECKPOINT_DIR}/{path.name}")
        version = int(next(iter({row["set_version"] for row in rows})))
        stamped[path.name] = (path, rows, version)

    highest = max((version for _, _, version in stamped.values()), default=0)
    for name, (_, rows, version) in sorted(stamped.items()):
        if version >= highest:
            continue
        ids = {str(row["case"]) for row in rows}
        key = key_for(keys, highest, ids)
        if key is None:
            raise RescoreError(
                f"{name} is version {version} and no trigger set on disk at version "
                f"{highest} contains all of its cases, so it cannot be bridged"
            )
        target = directory / rescored_name(name, highest)
        write_jsonl(target, rescore(rows, key, source=name))
        written.append(f"{CHECKPOINT_DIR}/{target.name}")
    return written
