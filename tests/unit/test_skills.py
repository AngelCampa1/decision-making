"""Tests for skill validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from decision_evals.generators.loader import REPO_ROOT
from decision_evals.skills import (
    STANDARD_FIELDS,
    VERDICTS,
    check_mirrors,
    mirror_plan,
    orphaned_promotions,
    parse_skill,
    promotable,
    sync_mirrors,
    validate_all,
    validate_skill,
    verdict_of,
)

BODY = "\n# Title\n\n## Abort if\nSkip when small.\n\n## Step\n" + ("word " * 60)
PLACEBO = "# Title\n\n## A\nGeneric.\n\n## B\n" + ("word " * 60)


def _frontmatter(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "name": "demo-skill",
        "description": "Use when deciding from a pile of context. Do not use for short prompts.",
        "license": "Apache-2.0",
        "compatibility": ">=1.0",
        "metadata": {
            "version": "0.1.0",
            "status": "experimental",
            "verdict": "UNTESTED",
            "claims": [{"id": "c1", "text": "Something falsifiable."}],
        },
        "allowed-tools": [],
    }
    base.update(overrides)
    return base


def _write(
    root: Path,
    *,
    name: str = "demo-skill",
    front: dict[str, Any] | None = None,
    body: str = BODY,
    placebo: str | None = PLACEBO,
    raw: str | None = None,
) -> Path:
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "SKILL.md"
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
    else:
        matter = yaml.safe_dump(front if front is not None else _frontmatter(), sort_keys=False)
        path.write_text(f"---\n{matter}---{body}", encoding="utf-8")
    if placebo is not None:
        (directory / "placebo.md").write_text(placebo, encoding="utf-8")
    return path


# -- the shipped skill ------------------------------------------------------


def test_the_shipped_skill_validates() -> None:
    """The real artifact, not a fixture. If this fails, the skill is broken."""
    assert validate_skill(REPO_ROOT / "skills" / "decision-making" / "SKILL.md") == []


def test_the_shipped_skill_uses_only_portable_fields() -> None:
    """A skill that errors in six tools is Claude-Code-shaped, not portable."""
    document = parse_skill(REPO_ROOT / "skills" / "decision-making" / "SKILL.md")
    assert set(document.frontmatter) <= STANDARD_FIELDS


def test_a_generated_baseline_validates(tmp_path: Path) -> None:
    """Guards the rest: each test below asserts a *deviation* is caught."""
    assert validate_skill(_write(tmp_path)) == []


# -- parsing ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "match"),
    [
        ("no frontmatter here", "missing YAML frontmatter"),
        ("---\nname: x\nstill going", "unterminated"),
        ("---\nname: [unclosed\n---\nbody", "unparseable"),
        ("---\n- a\n- b\n---\nbody", "not a mapping"),
    ],
)
def test_malformed_documents_report_rather_than_raise(tmp_path: Path, raw: str, match: str) -> None:
    """One broken skill must not hide the others' problems."""
    issues = validate_skill(_write(tmp_path, raw=raw))
    assert len(issues) == 1
    assert match in issues[0].message


# -- frontmatter ------------------------------------------------------------


def test_a_vendor_extension_is_rejected(tmp_path: Path) -> None:
    """`context: fork` is a hard error in Codex, Cursor and the rest."""
    front = _frontmatter()
    front["context"] = "fork"
    issues = validate_skill(_write(tmp_path, front=front))
    assert any("non-standard frontmatter" in str(i) for i in issues)


def test_a_missing_required_field_is_reported(tmp_path: Path) -> None:
    front = _frontmatter()
    del front["description"]
    issues = validate_skill(_write(tmp_path, front=front))
    assert any("missing required frontmatter" in str(i) for i in issues)


def test_the_name_must_match_the_directory(tmp_path: Path) -> None:
    """Discovery uses the directory, so a mismatch means the name is decoration."""
    issues = validate_skill(_write(tmp_path, front=_frontmatter(name="something-else")))
    assert any("does not match directory" in str(i) for i in issues)


# -- description ------------------------------------------------------------


@pytest.mark.parametrize("description", ["", "   ", None])
def test_an_empty_description_is_rejected(tmp_path: Path, description: Any) -> None:
    """It is the only text always resident in context."""
    issues = validate_skill(_write(tmp_path, front=_frontmatter(description=description)))
    assert any("description is empty" in str(i) for i in issues)


def test_a_description_without_a_negative_clause_is_rejected(tmp_path: Path) -> None:
    """Availability dominates; a description saying only when to fire fires on everything."""
    front = _frontmatter(description="Use whenever you are making any kind of decision.")
    issues = validate_skill(_write(tmp_path, front=front))
    assert any("no negative clause" in str(i) for i in issues)


@pytest.mark.parametrize(
    "description",
    [
        "Use for X. Do not use for Y.",
        "Use for X. Don't use for Y.",
        "Use for X. Not for Y.",
        "Use for X. Skip when Y.",
        "Use for X. Avoid when Y.",
    ],
)
def test_recognised_negative_phrasings(tmp_path: Path, description: str) -> None:
    assert validate_skill(_write(tmp_path, front=_frontmatter(description=description))) == []


# -- metadata and evidence --------------------------------------------------


def test_metadata_must_be_a_mapping(tmp_path: Path) -> None:
    issues = validate_skill(_write(tmp_path, front=_frontmatter(metadata="none")))
    assert any("must be a mapping" in str(i) for i in issues)


def test_an_unrecognised_verdict_is_rejected(tmp_path: Path) -> None:
    """A typo in a verdict is a false claim."""
    front = _frontmatter(
        metadata={"verdict": "PROBABLY_FINE", "claims": [{"id": "c", "text": "t"}]}
    )
    issues = validate_skill(_write(tmp_path, front=front))
    assert any("is not one of" in str(i) for i in issues)


def test_an_untested_skill_may_be_developed_but_not_shipped(tmp_path: Path) -> None:
    """The distinction the rule turns on."""
    path = _write(tmp_path)
    assert validate_skill(path, shipped=False) == []
    issues = validate_skill(path, shipped=True)
    assert any("may not ship" in str(i) for i in issues)


@pytest.mark.parametrize("verdict", sorted(VERDICTS - {"UNTESTED"}))
def test_a_skill_with_a_verdict_may_ship(tmp_path: Path, verdict: str) -> None:
    front = _frontmatter(metadata={"verdict": verdict, "claims": [{"id": "c1", "text": "t"}]})
    assert validate_skill(_write(tmp_path, front=front), shipped=True) == []


@pytest.mark.parametrize("claims", [None, [], "not a list"])
def test_claims_must_be_declared(tmp_path: Path, claims: Any) -> None:
    front = _frontmatter(metadata={"verdict": "UNTESTED", "claims": claims})
    issues = validate_skill(_write(tmp_path, front=front))
    assert any("metadata.claims" in str(i) for i in issues)


@pytest.mark.parametrize("claim", [{"id": "c1"}, {"text": "t"}, "a string"])
def test_a_malformed_claim_is_reported(tmp_path: Path, claim: Any) -> None:
    front = _frontmatter(metadata={"verdict": "UNTESTED", "claims": [claim]})
    issues = validate_skill(_write(tmp_path, front=front))
    assert any("malformed claim" in str(i) for i in issues)


def test_duplicate_claim_ids_are_reported(tmp_path: Path) -> None:
    front = _frontmatter(
        metadata={
            "verdict": "UNTESTED",
            "claims": [{"id": "c1", "text": "a"}, {"id": "c1", "text": "b"}],
        }
    )
    issues = validate_skill(_write(tmp_path, front=front))
    assert any("duplicate claim ids" in str(i) for i in issues)


# -- placebo ----------------------------------------------------------------


def test_a_missing_placebo_is_rejected(tmp_path: Path) -> None:
    """Writing it after seeing results is the degree of freedom the arm removes."""
    issues = validate_skill(_write(tmp_path, placebo=None))
    assert any("no placebo.md" in str(i) for i in issues)


def test_an_unmatched_placebo_is_rejected(tmp_path: Path) -> None:
    issues = validate_skill(_write(tmp_path, placebo="# Tiny\n\n## A\nShort."))
    assert any("not matched" in str(i) for i in issues)


# -- batch ------------------------------------------------------------------


def test_validate_all_covers_every_skill(tmp_path: Path) -> None:
    _write(tmp_path, name="good-one", front=_frontmatter(name="good-one"))
    _write(tmp_path, name="bad-one", front=_frontmatter(name="mismatch"), placebo=None)
    issues = validate_all(tmp_path)
    assert {i.skill for i in issues} == {"mismatch"}
    assert len(issues) == 2


def test_validate_all_on_an_empty_root(tmp_path: Path) -> None:
    assert validate_all(tmp_path) == []


# -- mirrors ----------------------------------------------------------------


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "AGENTS.md").write_text("# Agents\nwiring block\n", encoding="utf-8")
    _write(tmp_path / "skills", name="demo-skill")
    return tmp_path


def test_the_real_repository_mirrors_are_current() -> None:
    """A stale `.agents/skills/` silently serves an old skill to every non-Claude tool."""
    assert check_mirrors(REPO_ROOT) == []


def test_mirror_plan_pairs_agents_with_claude(tmp_path: Path) -> None:
    pairs = mirror_plan(_repo(tmp_path))
    assert (tmp_path / "AGENTS.md", tmp_path / "CLAUDE.md") in pairs


def test_mirror_plan_skips_an_absent_agents_file(tmp_path: Path) -> None:
    _write(tmp_path / "skills", name="demo-skill")
    assert all(source.name != "AGENTS.md" for source, _ in mirror_plan(tmp_path))


def test_mirror_plan_covers_every_skill_file(tmp_path: Path) -> None:
    """Not just SKILL.md: the placebo has to reach the mirror too."""
    mirrors = {mirror.name for _, mirror in mirror_plan(_repo(tmp_path))}
    assert {"SKILL.md", "placebo.md", "CLAUDE.md"} <= mirrors


def test_mirror_plan_on_a_bare_directory(tmp_path: Path) -> None:
    assert mirror_plan(tmp_path) == []


def test_sync_writes_then_becomes_a_no_op(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    first = sync_mirrors(repo)
    assert first
    assert sync_mirrors(repo) == []
    assert (repo / "CLAUDE.md").read_text(encoding="utf-8") == (repo / "AGENTS.md").read_text(
        encoding="utf-8"
    )


def test_a_missing_mirror_is_reported(tmp_path: Path) -> None:
    issues = check_mirrors(_repo(tmp_path))
    assert issues
    assert all("is missing" in str(i) for i in issues)


def test_a_stale_mirror_is_reported(tmp_path: Path) -> None:
    """Worse than a missing one: it serves old content without erroring."""
    repo = _repo(tmp_path)
    sync_mirrors(repo)
    (repo / "AGENTS.md").write_text("# Agents\nrevised wiring\n", encoding="utf-8")
    issues = check_mirrors(repo)
    assert any("CLAUDE.md is stale" in str(i) for i in issues)


def test_sync_repairs_a_stale_mirror(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    sync_mirrors(repo)
    (repo / "CLAUDE.md").write_text("tampered", encoding="utf-8")
    assert sync_mirrors(repo) == [repo / "CLAUDE.md"]
    assert check_mirrors(repo) == []


# -- promotion --------------------------------------------------------------


def _promote(repo: Path, verdict: str, *, name: str = "demo-skill") -> Path:
    """Rewrite a source skill's verdict, as a confirmation run would."""
    front = _frontmatter(
        name=name,
        metadata={"verdict": verdict, "claims": [{"id": "c1", "text": "t"}]},
    )
    _write(repo / "skills", name=name, front=front)
    return repo


def test_an_untested_skill_is_not_promotable(tmp_path: Path) -> None:
    """The gate. Nothing reaches the plugin on good intentions."""
    assert promotable(_repo(tmp_path) / "skills") == []


@pytest.mark.parametrize("verdict", sorted(VERDICTS - {"UNTESTED"}))
def test_any_recorded_verdict_makes_a_skill_promotable(tmp_path: Path, verdict: str) -> None:
    """Including HARMFUL: shipping it off-by-default with its evidence is the point."""
    repo = _promote(_repo(tmp_path), verdict)
    assert [path.name for path in promotable(repo / "skills")] == ["demo-skill"]


def test_a_skill_with_unreadable_metadata_is_not_promotable(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write(repo / "skills", name="demo-skill", front=_frontmatter(metadata="none"))
    assert promotable(repo / "skills") == []


def test_verdict_of_a_directory_without_a_skill_file(tmp_path: Path) -> None:
    assert verdict_of(tmp_path / "absent") is None


def test_promotable_on_a_missing_skills_root(tmp_path: Path) -> None:
    assert promotable(tmp_path / "nothing") == []


def test_an_untested_skill_never_reaches_the_plugin(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    sync_mirrors(repo)
    assert not (repo / "plugin" / "skills" / "demo-skill").exists()
    assert check_mirrors(repo) == []


def test_promotion_copies_the_whole_skill_directory(tmp_path: Path) -> None:
    """Everything travels, not just SKILL.md.

    The placebo, because evidence includes what the skill was tested against;
    and nested `references/` or `scripts/`, because a skill that loses them on
    promotion ships broken to every installer while validating locally.
    """
    repo = _promote(_repo(tmp_path), "SHIP")
    nested = repo / "skills" / "demo-skill" / "references"
    nested.mkdir()
    (nested / "worked-example.md").write_text("example", encoding="utf-8")

    sync_mirrors(repo)
    promoted = repo / "plugin" / "skills" / "demo-skill"
    assert (promoted / "SKILL.md").exists()
    assert (promoted / "placebo.md").exists()
    assert (promoted / "references" / "worked-example.md").read_text(encoding="utf-8") == "example"
    assert check_mirrors(repo) == []


def test_a_promoted_skill_that_is_demoted_is_reported(tmp_path: Path) -> None:
    """The failure the evidence rule exists to prevent, and the one mirror_plan misses.

    A demoted skill contributes no source/mirror pairs at all, so a staleness
    check sees nothing wrong while the plugin keeps shipping a withdrawn badge.
    """
    repo = _promote(_repo(tmp_path), "SHIP")
    sync_mirrors(repo)
    _promote(repo, "UNTESTED")
    issues = check_mirrors(repo)
    assert any("promoted but its source now records UNTESTED" in str(i) for i in issues)


def test_sync_withdraws_a_demoted_skill(tmp_path: Path) -> None:
    repo = _promote(_repo(tmp_path), "SHIP")
    sync_mirrors(repo)
    _promote(repo, "UNTESTED")
    assert repo / "plugin" / "skills" / "demo-skill" in sync_mirrors(repo)
    assert not (repo / "plugin" / "skills" / "demo-skill").exists()
    assert check_mirrors(repo) == []


def test_a_plugin_skill_with_no_source_at_all_is_reported(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "plugin" / "skills" / "ghost").mkdir(parents=True)
    assert any("no source skill" in str(i) for i in check_mirrors(repo))


def test_a_file_beside_the_promotions_is_not_an_orphan(tmp_path: Path) -> None:
    """`plugin/skills/README.md` explains the empty directory; it is not a skill."""
    repo = _repo(tmp_path)
    plugin_skills = repo / "plugin" / "skills"
    plugin_skills.mkdir(parents=True)
    (plugin_skills / "README.md").write_text("why this is empty", encoding="utf-8")
    assert orphaned_promotions(repo) == []


def test_orphan_detection_without_a_plugin_directory(tmp_path: Path) -> None:
    assert orphaned_promotions(tmp_path) == []


# -- the real repository ----------------------------------------------------


def test_the_shipped_plugin_promotes_nothing_yet() -> None:
    """Guards the README badge. `proven: 0` has to mean the directory is empty."""
    assert promotable(REPO_ROOT / "skills") == []
    assert orphaned_promotions(REPO_ROOT) == []
