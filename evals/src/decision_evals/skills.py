"""Skill validation.

Enforces three things the ecosystem does not enforce for you.

**Portability.** The Agent Skills standard defines exactly six frontmatter
fields. Vendor extensions -- ``context: fork``, ``disable-model-invocation`` --
are hard errors in Codex, Cursor and the rest, so the canonical skill carries
only the six and any vendor keys live in an overlay. A skill that works in one
tool and errors in six others is not portable, it is Claude-Code-shaped.

**Trigger quality, as far as static text allows.** Skill *availability* is worth
+18 to +36pp; prose granularity is worth +0.7pp with intervals crossing zero. So
the description does the work, and it needs negative clauses as well as positive
ones -- a description saying only when to fire is a description that fires on
everything adjacent. Measuring firing precision needs a run; requiring the
negative clause does not, so it is required here.

**Evidence.** A skill may not be *shipped* carrying ``UNTESTED``. Note the
distinction: developing a skill with no verdict is the normal state and is fine,
which is why the check applies to the plugin directory rather than the source
tree. This is the rule that keeps the repository from becoming another
unvalidated prompt library.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import yaml

from decision_evals.solvers.arms import check_placebo_match

#: The complete set of portable frontmatter fields. Anything else is a
#: portability defect in the canonical source.
STANDARD_FIELDS: Final[frozenset[str]] = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)

REQUIRED_FIELDS: Final[frozenset[str]] = frozenset({"name", "description"})

#: Verdicts from SCORECARD.md. A verdict outside this set is a typo, and a typo
#: in a verdict is a false claim.
VERDICTS: Final[frozenset[str]] = frozenset({"SHIP", "PROVISIONAL", "NULL", "HARMFUL", "UNTESTED"})

#: Phrases that mark a description's negative clause. Crude, and deliberately
#: so: the check is that the author wrote one at all.
_NEGATIVE_MARKERS: Final = ("do not use", "don't use", "not for", "skip when", "avoid when")


@dataclass(frozen=True)
class SkillIssue:
    """One validation failure."""

    skill: str
    message: str

    def __str__(self) -> str:
        return f"{self.skill}: {self.message}"


@dataclass
class SkillDocument:
    """A parsed SKILL.md."""

    path: Path
    frontmatter: dict[str, Any]
    body: str
    issues: list[SkillIssue] = field(default_factory=list)

    @property
    def name(self) -> str:
        raw = self.frontmatter.get("name")
        return raw if isinstance(raw, str) else self.path.parent.name


def parse_skill(path: Path) -> SkillDocument:
    """Read a SKILL.md into frontmatter and body.

    A malformed document returns a :class:`SkillDocument` carrying its issues
    rather than raising, so one broken skill does not hide the others' problems.
    """
    text = path.read_text(encoding="utf-8")
    document = SkillDocument(path=path, frontmatter={}, body=text)

    if not text.startswith("---"):
        document.issues.append(SkillIssue(path.parent.name, "missing YAML frontmatter"))
        return document

    parts = text.split("---", 2)
    if len(parts) < 3:
        document.issues.append(SkillIssue(path.parent.name, "unterminated YAML frontmatter"))
        return document

    try:
        loaded = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        document.issues.append(SkillIssue(path.parent.name, f"unparseable frontmatter: {exc}"))
        return document

    if not isinstance(loaded, dict):
        document.issues.append(SkillIssue(path.parent.name, "frontmatter is not a mapping"))
        return document

    document.frontmatter = loaded
    document.body = parts[2]
    return document


def validate_skill(path: Path, *, shipped: bool = False) -> list[SkillIssue]:
    """Validate one skill directory.

    Args:
        path: The ``SKILL.md`` file.
        shipped: True when validating a skill inside the plugin directory, where
            the evidence rule applies.
    """
    document = parse_skill(path)
    if document.issues:
        return document.issues

    issues: list[SkillIssue] = []
    name = document.name
    front = document.frontmatter

    issues += _check_fields(name, front, path)
    issues += _check_description(name, front)
    issues += _check_metadata(name, front, shipped=shipped)
    issues += _check_placebo(name, path.parent, document.body)
    return issues


def _check_fields(name: str, front: dict[str, Any], path: Path) -> list[SkillIssue]:
    issues = []
    extra = sorted(set(front) - STANDARD_FIELDS)
    if extra:
        issues.append(
            SkillIssue(
                name,
                f"non-standard frontmatter {extra}. The open standard defines exactly "
                f"{sorted(STANDARD_FIELDS)}; vendor keys are hard errors in other tools "
                "and belong in an overlay.",
            )
        )
    missing = sorted(REQUIRED_FIELDS - set(front))
    if missing:
        issues.append(SkillIssue(name, f"missing required frontmatter {missing}"))
    if front.get("name") != path.parent.name:
        issues.append(
            SkillIssue(
                name,
                f"name {front.get('name')!r} does not match directory "
                f"{path.parent.name!r}; discovery uses the directory",
            )
        )
    return issues


def _check_description(name: str, front: dict[str, Any]) -> list[SkillIssue]:
    description = front.get("description")
    if not isinstance(description, str) or not description.strip():
        return [SkillIssue(name, "description is empty; it is the only always-resident text")]
    lowered = description.casefold()
    if not any(marker in lowered for marker in _NEGATIVE_MARKERS):
        return [
            SkillIssue(
                name,
                "description has no negative clause. Availability is the dominant term in "
                "skill effectiveness, so a description that says only when to fire will "
                "fire on everything adjacent.",
            )
        ]
    return []


def _check_metadata(name: str, front: dict[str, Any], *, shipped: bool) -> list[SkillIssue]:
    metadata = front.get("metadata")
    if not isinstance(metadata, dict):
        return [SkillIssue(name, "metadata must be a mapping carrying the evidence record")]

    issues = []
    verdict = metadata.get("verdict")
    if verdict not in VERDICTS:
        issues.append(SkillIssue(name, f"verdict {verdict!r} is not one of {sorted(VERDICTS)}"))
    elif shipped and verdict == "UNTESTED":
        issues.append(
            SkillIssue(
                name,
                "an UNTESTED skill may not ship. Develop it in skills/ for as long as you "
                "like; carrying no verdict into the plugin is what makes a badge meaningless.",
            )
        )

    claims = metadata.get("claims")
    if not isinstance(claims, list) or not claims:
        issues.append(SkillIssue(name, "metadata.claims must list what the skill asserts"))
        return issues

    ids = []
    for claim in claims:
        if not isinstance(claim, dict) or "id" not in claim or "text" not in claim:
            issues.append(SkillIssue(name, f"malformed claim {claim!r}; needs `id` and `text`"))
            continue
        ids.append(claim["id"])
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        issues.append(SkillIssue(name, f"duplicate claim ids {duplicates}"))
    return issues


def _check_placebo(name: str, directory: Path, body: str) -> list[SkillIssue]:
    """A skill without a matched placebo cannot be placebo-controlled.

    Required at authoring time rather than at run time, because writing a
    length-matched placebo after seeing the treatment's results is exactly the
    degree of freedom the arm exists to remove.
    """
    placebo = directory / "placebo.md"
    if not placebo.exists():
        return [
            SkillIssue(
                name,
                "no placebo.md. No SHIP verdict is issued without a passing placebo arm, "
                "and writing the placebo after seeing results is the degree of freedom "
                "that arm exists to remove.",
            )
        ]
    match = check_placebo_match(body, placebo.read_text(encoding="utf-8"))
    if not match.ok:
        return [
            SkillIssue(
                name,
                f"placebo is not matched: {match.skill_words}w/{match.skill_sections}h skill "
                f"vs {match.placebo_words}w/{match.placebo_sections}h placebo "
                f"(ratio {match.word_ratio:.2f}, tolerance {match.tolerance})",
            )
        ]
    return []


def validate_all(skills_root: Path, *, shipped: bool = False) -> list[SkillIssue]:
    """Validate every skill under a root, in directory order."""
    issues: list[SkillIssue] = []
    for path in sorted(skills_root.glob("*/SKILL.md")):
        issues += validate_skill(path, shipped=shipped)
    return issues


# ---------------------------------------------------------------------------
# Mirrors
#
# The same content has to exist at more than one path: `.agents/skills/` is the
# convergent discovery path across Codex, Cursor, Copilot, Gemini CLI, Cline,
# Amp and OpenCode, and CLAUDE.md is what Claude Code reads where everything
# else reads AGENTS.md. Symlinks would express this exactly and do not survive
# a Windows checkout, so the copies are generated and their agreement is a
# gate rather than a habit.
# ---------------------------------------------------------------------------


def verdict_of(skill_dir: Path) -> str | None:
    """The verdict recorded in a skill's frontmatter, or None if unreadable."""
    path = skill_dir / "SKILL.md"
    if not path.is_file():
        return None
    metadata = parse_skill(path).frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        return None
    recorded = metadata.get("verdict")
    return recorded if isinstance(recorded, str) and recorded in VERDICTS else None


def promotable(skills_root: Path) -> list[Path]:
    """Skill directories whose recorded verdict permits shipping.

    The promotion gate, and the reason it is a gate rather than a lint: an
    UNTESTED skill is never copied into the plugin in the first place, so the
    "no unproven skill ships" rule cannot be violated by forgetting to run a
    check. Demotion works the same way in reverse -- a skill whose verdict
    reverts stops being promotable, and the copy it left behind is reported as
    an orphan rather than quietly continuing to ship.
    """
    if not skills_root.is_dir():
        return []
    return [
        path.parent
        for path in sorted(skills_root.glob("*/SKILL.md"))
        if (verdict_of(path.parent) or "UNTESTED") != "UNTESTED"
    ]


def mirror_plan(repo_root: Path) -> list[tuple[Path, Path]]:
    """Every (source, mirror) pair that must hold identical bytes."""
    pairs: list[tuple[Path, Path]] = []

    agents = repo_root / "AGENTS.md"
    if agents.exists():
        pairs.append((agents, repo_root / "CLAUDE.md"))

    skills_root = repo_root / "skills"
    if skills_root.is_dir():
        for source in sorted(skills_root.rglob("*")):
            if source.is_file():
                relative = source.relative_to(skills_root)
                pairs.append((source, repo_root / ".agents" / "skills" / relative))

    for skill_dir in promotable(skills_root):
        for source in sorted(skill_dir.rglob("*")):
            if source.is_file():
                relative = source.relative_to(skills_root)
                pairs.append((source, repo_root / "plugin" / "skills" / relative))
    return pairs


def orphaned_promotions(repo_root: Path) -> list[Path]:
    """Plugin skill directories with no promotable source behind them.

    Left unchecked this is the failure the whole evidence rule exists to
    prevent: a skill that was promoted on a verdict, then demoted when a
    replication came back worse, still sitting in the shipped directory with a
    badge it no longer earns. ``mirror_plan`` cannot catch it, because a
    demoted skill contributes no pairs at all.
    """
    plugin_skills = repo_root / "plugin" / "skills"
    if not plugin_skills.is_dir():
        return []
    promoted = {path.name for path in promotable(repo_root / "skills")}
    return [
        path
        for path in sorted(plugin_skills.iterdir())
        if path.is_dir() and path.name not in promoted
    ]


def sync_mirrors(repo_root: Path) -> list[Path]:
    """Write every mirror from its source, and prune demoted promotions.

    Returns the paths that changed. ``plugin/skills/`` is a generated directory
    in its entirety, so removing a demoted skill from it is a regeneration
    rather than a deletion of anything authored.
    """
    changed: list[Path] = []
    for source, mirror in mirror_plan(repo_root):
        content = source.read_bytes()
        if mirror.exists() and mirror.read_bytes() == content:
            continue
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_bytes(content)
        changed.append(mirror)

    for orphan in orphaned_promotions(repo_root):
        shutil.rmtree(orphan)
        changed.append(orphan)
    return changed


def check_mirrors(repo_root: Path) -> list[SkillIssue]:
    """Report mirrors that are missing or stale.

    Stale rather than merely absent matters more: an out-of-date
    ``.agents/skills/`` copy is worse than none, because it silently serves an
    old skill to every tool that is not Claude Code, and the difference would
    show up as unexplained variance between platforms rather than as an error.
    """
    issues: list[SkillIssue] = []
    for source, mirror in mirror_plan(repo_root):
        label = str(mirror.relative_to(repo_root)).replace("\\", "/")
        if not mirror.exists():
            issues.append(SkillIssue("mirror", f"{label} is missing; run `de mirror`"))
        elif mirror.read_bytes() != source.read_bytes():
            issues.append(SkillIssue("mirror", f"{label} is stale; run `de mirror`"))

    for orphan in orphaned_promotions(repo_root):
        recorded = verdict_of(repo_root / "skills" / orphan.name) or "no source skill"
        issues.append(
            SkillIssue(
                "mirror",
                f"plugin/skills/{orphan.name} is promoted but its source now records "
                f"{recorded}; run `de mirror` to withdraw it",
            )
        )
    return issues
