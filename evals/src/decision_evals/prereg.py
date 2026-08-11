"""Pre-registration, enforced rather than promised.

A confirmation run refuses to start unless the pre-registration is committed,
predates the results, and both hash locks match. Editing one word of a skill
after pre-registration aborts the run.

**Locking the analysis script matters as much as locking the skill.** A
pre-registered metric means nothing if the code computing it can be rewritten
after seeing the data, and that is the gap most "pre-registered" ML work leaves
open. Both hashes are checked, and neither is optional.

The git facts arrive as a :class:`RepoState` rather than being shelled out for
here. That keeps every refusal branch testable without a fixture repository,
which matters because this module carries a 100% branch-coverage floor: a
refusal that has never been executed is a refusal nobody has checked.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class PreregistrationError(ValueError):
    """The run may not proceed as pre-registered."""


class Preregistration(BaseModel):
    """The committed contract for one confirmation run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    skill: str = Field(min_length=1)
    version: int = Field(ge=1)
    hypothesis: str = Field(min_length=1)
    primary_metric: str = Field(min_length=1)
    n_items: int = Field(ge=1)
    minimum_detectable_effect: float = Field(gt=0.0, lt=1.0)
    alpha: float = Field(gt=0.0, lt=1.0)
    guards: list[str] = Field(min_length=1)
    #: Fixed N, no interim analysis. Recorded as text so a deviation is visible
    #: in the diff rather than inferred from the code.
    stopping_rule: str = Field(min_length=1)
    difficulty_band: tuple[float, float] = (0.35, 0.75)
    budget_usd: float = Field(gt=0.0)
    skill_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    analysis_script_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RepoState:
    """Git facts about the pre-registration file, gathered by the caller."""

    #: The file is committed and the working copy is clean.
    committed_and_clean: bool
    #: Its commit is an ancestor of HEAD.
    is_ancestor_of_head: bool
    #: Its commit predates everything already in ``results/<skill>/``.
    precedes_results: bool


def sha256_text(text: str) -> str:
    """Hash a skill body or analysis source.

    Line endings are normalised first. Otherwise a checkout on Windows would
    hash differently from the same file on Linux, and the lock would fire on a
    difference that does not exist.
    """
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def load_preregistration(path: Path) -> Preregistration:
    """Load and validate a pre-registration file."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PreregistrationError(f"{path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PreregistrationError(f"{path}: expected a mapping, got {type(raw).__name__}")
    try:
        return Preregistration.model_validate(raw)
    except ValidationError as exc:
        raise PreregistrationError(f"{path}: {exc}") from exc


def assert_runnable(
    prereg: Preregistration,
    *,
    repo: RepoState,
    skill_body: str,
    analysis_source: str,
    baseline_accuracy: float,
    projected_cost_usd: float,
) -> None:
    """Refuse to start a confirmation run that would not be honest.

    Checks run in order of how cheaply they can be fixed, so the first failure
    reported is the most actionable one.

    Raises:
        PreregistrationError: Naming the check that failed and what to do.
    """
    _assert_committed(repo)
    _assert_hash(
        "skill",
        expected=prereg.skill_sha256,
        actual=sha256_text(skill_body),
        remedy=(
            f"The skill changed after pre-registration. Iterating is fine, but it needs a "
            f"new preregistration/{prereg.skill}-v{prereg.version + 1}.yaml -- a dated, "
            "visible commit rather than an invisible edit."
        ),
    )
    _assert_hash(
        "analysis script",
        expected=prereg.analysis_script_sha256,
        actual=sha256_text(analysis_source),
        remedy=(
            "The analysis code changed after pre-registration. A pre-registered metric "
            "means nothing if the code computing it can be rewritten after seeing the data."
        ),
    )
    _assert_difficulty(prereg, baseline_accuracy)
    _assert_budget(prereg, projected_cost_usd)


def _assert_committed(repo: RepoState) -> None:
    if not repo.committed_and_clean:
        raise PreregistrationError(
            "the pre-registration is uncommitted or has uncommitted edits. Its value is "
            "entirely in its timestamp, and an uncommitted file has none."
        )
    if not repo.is_ancestor_of_head:
        raise PreregistrationError(
            "the pre-registration's commit is not an ancestor of HEAD, so it cannot be "
            "shown to predate this run."
        )
    if not repo.precedes_results:
        raise PreregistrationError(
            "the pre-registration was committed after results already existed for this "
            "skill. That is a postdiction, whatever the file says."
        )


def _assert_hash(what: str, *, expected: str, actual: str, remedy: str) -> None:
    if expected != actual:
        raise PreregistrationError(
            f"{what} hash mismatch.\n  pre-registered: {expected}\n  on disk:        {actual}\n"
            f"{remedy}"
        )


def _assert_difficulty(prereg: Preregistration, baseline_accuracy: float) -> None:
    low, high = prereg.difficulty_band
    if not low <= baseline_accuracy <= high:
        raise PreregistrationError(
            f"control accuracy {baseline_accuracy:.3f} is outside the pre-registered "
            f"difficulty band [{low}, {high}]. Above the band there is no headroom to "
            "measure; below it, the items are ambiguous rather than hard."
        )


def _assert_budget(prereg: Preregistration, projected_cost_usd: float) -> None:
    if projected_cost_usd > prereg.budget_usd:
        raise PreregistrationError(
            f"projected cost ${projected_cost_usd:.2f} exceeds the pre-registered budget "
            f"${prereg.budget_usd:.2f}. Raising the budget mid-run is how a fixed-N design "
            "turns into an optional-stopping one."
        )
