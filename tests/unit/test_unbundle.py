"""Track M4's arm builder: the four descriptions must be derived, never authored.

The point of every test here is the same. If any of them can be made to pass by
inventing prose, the M4 race stops being about structure and starts being about
whatever the prose happened to say — which is precisely why M4 refuses the
historical four-skill tree as an arm.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from decision_evals.skills import parse_skill
from decision_evals.unbundle import (
    DESCRIPTION_VARIANTS,
    Procedure,
    UnbundleError,
    description_variant,
    four_arm,
    router_rows,
    shared_scope,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIPPED = REPO_ROOT / "skills" / "decision-making" / "SKILL.md"

BODY = """
| What is hard | Read | What it produces |
|---|---|---|
| A pile arrived | `ledger.md` | what bears on it |
| It may not fit | `fit.md` | the generic answer |
"""

DESCRIPTION = (
    "Use when someone is deciding something. Routes to one of four procedures. "
    "Do not use for lookups."
)


class TestRouterRows:
    def test_reads_every_row_in_table_order(self) -> None:
        rows = router_rows(BODY)
        assert [r.name for r in rows] == ["ledger", "fit"]

    def test_the_header_is_not_a_row(self) -> None:
        """The header's middle cell has no backticked filename, so it cannot match."""
        assert all(r.name not in {"Read", "What it produces"} for r in router_rows(BODY))

    def test_condition_and_product_are_verbatim(self) -> None:
        row = router_rows(BODY)[0]
        assert row.condition == "A pile arrived"
        assert row.product == "what bears on it"

    def test_a_table_that_moved_raises_rather_than_returning_nothing(self) -> None:
        with pytest.raises(UnbundleError, match="shape has changed"):
            router_rows("# Decision making\n\nNo table here.\n")


class TestSharedScope:
    def test_splits_on_the_markers(self) -> None:
        opener, exclusions = shared_scope(DESCRIPTION)
        assert opener == "Use when someone is deciding something."
        assert exclusions == "Do not use for lookups."

    def test_a_missing_opener_marker_raises(self) -> None:
        with pytest.raises(UnbundleError, match="opener marker"):
            shared_scope("Use when deciding. Do not use for lookups.")

    def test_a_missing_exclusions_marker_raises(self) -> None:
        with pytest.raises(UnbundleError, match="exclusions marker"):
            shared_scope("Use when deciding. Routes to one of four procedures.")

    def test_newlines_in_a_folded_yaml_scalar_are_flattened(self) -> None:
        folded = "Use when\ndeciding. Routes to one of four\nprocedures. Do not use for\nlookups."
        opener, exclusions = shared_scope(folded)
        assert "\n" not in opener
        assert "\n" not in exclusions
        assert opener == "Use when deciding."


class TestFourArm:
    def test_one_entry_per_row(self) -> None:
        assert list(four_arm(DESCRIPTION, BODY)) == ["ledger", "fit"]

    def test_every_arm_carries_the_shared_scope_unchanged(self) -> None:
        opener, exclusions = shared_scope(DESCRIPTION)
        for text in four_arm(DESCRIPTION, BODY).values():
            assert text.startswith(opener)
            assert text.endswith(exclusions)

    def test_the_arms_differ_only_in_their_own_row(self) -> None:
        """The whole design: shared scope, one distinct clause each."""
        opener, exclusions = shared_scope(DESCRIPTION)
        middles = {
            text.removeprefix(opener).removesuffix(exclusions).strip()
            for text in four_arm(DESCRIPTION, BODY).values()
        }
        assert len(middles) == 2

    def test_no_word_appears_that_is_not_in_the_bundle(self) -> None:
        """The falsifiable version of "nothing here is authored".

        Every word of every composed description must already occur in the
        bundle's description or its router table. If this test ever fails, some
        prose has been invented and the M4 race has become uninterpretable.
        """

        def words(text: str) -> set[str]:
            """Bare words. Sentence punctuation moves when clauses are joined."""
            return {w.strip(".,`|") for w in text.lower().split()} - {""}

        # ``produces`` is the one connective the composer adds, and it is
        # declared here rather than hidden -- it is identical across all four
        # arms, so it cannot differentiate them.
        allowed = words(DESCRIPTION + " " + BODY) | {"produces"}
        for text in four_arm(DESCRIPTION, BODY).values():
            assert words(text) <= allowed


class TestAgainstTheShippedSkill:
    """These run against the real file, so a skill edit that breaks M4 fails here."""

    def test_the_shipped_bundle_splits_into_four(self) -> None:
        document = parse_skill(SHIPPED)
        arms = four_arm(str(document.frontmatter["description"]), document.body)
        assert set(arms) == {"ledger", "fit", "cascade", "timing"}

    def test_each_shipped_arm_is_a_usable_description(self) -> None:
        document = parse_skill(SHIPPED)
        for name, text in four_arm(str(document.frontmatter["description"]), document.body).items():
            assert 100 < len(text) < 1024, name

    def test_a_procedure_composes_its_own_row(self) -> None:
        row = Procedure(name="x", condition="the pile is large", product="a list")
        assert row.description("Use when.", "Not for lookups.") == (
            "Use when. The pile is large. Produces a list. Not for lookups."
        )


class TestDescriptionVariants:
    """Track L5. Every arm must be a deletion, never a rewrite."""

    def test_full_is_the_description_flattened(self) -> None:
        assert description_variant(DESCRIPTION, "full") == " ".join(DESCRIPTION.split())

    def test_no_exclusions_drops_only_the_exclusions(self) -> None:
        text = description_variant(DESCRIPTION, "no-exclusions")
        assert "Do not use for" not in text
        assert text.startswith("Use when someone is deciding something.")
        assert "Routes to one of four procedures." in text

    def test_opener_only_is_the_opener(self) -> None:
        opener, _ = shared_scope(DESCRIPTION)
        assert description_variant(DESCRIPTION, "opener-only") == opener

    def test_no_opener_drops_only_the_opener(self) -> None:
        text = description_variant(DESCRIPTION, "no-opener")
        assert "Use when someone is deciding" not in text
        assert text.startswith("Routes to one of four procedures.")
        assert text.endswith("Do not use for lookups.")

    @pytest.mark.parametrize("variant", DESCRIPTION_VARIANTS)
    def test_no_variant_adds_a_word(self, variant: str) -> None:
        """The falsifiable form of "these are subtractions"."""

        def words(text: str) -> set[str]:
            return {w.strip(".,`|") for w in text.lower().split()} - {""}

        assert words(description_variant(DESCRIPTION, variant)) <= words(DESCRIPTION)

    @pytest.mark.parametrize("variant", DESCRIPTION_VARIANTS)
    def test_every_variant_builds_from_the_shipped_skill(self, variant: str) -> None:
        document = parse_skill(SHIPPED)
        text = description_variant(str(document.frontmatter["description"]), variant)
        assert 100 < len(text) < 1024, variant

    def test_an_unknown_variant_raises(self) -> None:
        with pytest.raises(UnbundleError, match="unknown variant"):
            description_variant(DESCRIPTION, "shorter")

    def test_a_moved_marker_raises_rather_than_guessing(self) -> None:
        with pytest.raises(UnbundleError, match="marker"):
            description_variant("Some description with no markers at all.", "opener-only")
