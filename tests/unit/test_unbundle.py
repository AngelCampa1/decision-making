"""Track M4's arm builder: the four descriptions must be derived, never authored.

The point of every test here is the same. If any of them can be made to pass by
inventing prose, the M4 race stops being about structure and starts being about
whatever the prose happened to say — which is precisely why M4 refuses the
historical four-skill tree as an arm.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import ClassVar

import pytest

from decision_evals.skills import parse_skill
from decision_evals.unbundle import (
    _OPENER_NAMED,
    _OPENER_SHOWN,
    AUTHORED_VARIANTS,
    DELETION_VARIANTS,
    DESCRIPTION_VARIANTS,
    Procedure,
    UnbundleError,
    covering,
    description_variant,
    entries,
    entries_grouped,
    four_arm,
    router_rows,
    shared_scope,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _words(built: dict[str, str]) -> list[str]:
    """Every word across all entries, for the multiset comparison M6 rests on."""
    return re.findall(r"[a-z']+", " ".join(built.values()).lower())


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

    @pytest.mark.parametrize("variant", DELETION_VARIANTS)
    def test_no_deletion_variant_adds_a_word(self, variant: str) -> None:
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


class TestEntries:
    """Track M5's partition. Deterministic in n, and a superset of M4's arm."""

    FOUR = """
| What is hard | Read | What it produces |
|---|---|---|
| A pile arrived | `ledger.md` | a list |
| It may not fit | `fit.md` | the generic answer |
| It starts things | `cascade.md` | the chain |
| The question is when | `timing.md` | the undo price |
"""

    def test_n_equal_to_the_row_count_is_the_four_arm(self) -> None:
        assert entries(DESCRIPTION, self.FOUR, 4) == four_arm(DESCRIPTION, self.FOUR)

    def test_n_one_is_a_single_entry_covering_everything(self) -> None:
        out = entries(DESCRIPTION, self.FOUR, 1)
        assert list(out) == ["ledger-fit-cascade-timing"]

    def test_the_partition_is_contiguous_and_even(self) -> None:
        assert list(entries(DESCRIPTION, self.FOUR, 2)) == ["ledger-fit", "cascade-timing"]

    def test_an_uneven_split_front_loads_the_extra(self) -> None:
        assert list(entries(DESCRIPTION, self.FOUR, 3)) == ["ledger-fit", "cascade", "timing"]

    def test_every_procedure_appears_exactly_once_at_every_n(self) -> None:
        for n in range(1, 5):
            covered = [p for name in entries(DESCRIPTION, self.FOUR, n) for p in name.split("-")]
            assert sorted(covered) == ["cascade", "fit", "ledger", "timing"], n

    @pytest.mark.parametrize("n", [0, 5])
    def test_an_n_outside_the_table_raises(self, n: int) -> None:
        with pytest.raises(UnbundleError, match="n must be"):
            entries(DESCRIPTION, self.FOUR, n)

    def test_or_is_the_only_word_added(self) -> None:
        def words(text: str) -> set[str]:
            return {w.strip(".,`|") for w in text.lower().split()} - {""}

        allowed = words(DESCRIPTION + " " + self.FOUR) | {"produces", "or"}
        for n in range(1, 5):
            for text in entries(DESCRIPTION, self.FOUR, n).values():
                assert words(text) <= allowed, n

    def test_the_shipped_skill_partitions_at_every_n(self) -> None:
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        for n in range(1, 5):
            assert len(entries(description, document.body, n)) == n


class TestCovering:
    ENTRIES: ClassVar[dict[str, str]] = {"ledger-fit": "...", "cascade-timing": "..."}

    @pytest.mark.parametrize(
        ("procedure", "expected"),
        [
            ("ledger", "ledger-fit"),
            ("fit", "ledger-fit"),
            ("cascade", "cascade-timing"),
            ("timing", "cascade-timing"),
        ],
    )
    def test_finds_the_entry_holding_the_procedure(self, procedure: str, expected: str) -> None:
        assert covering(self.ENTRIES, procedure) == expected

    def test_an_uncovered_procedure_is_none(self) -> None:
        assert covering(self.ENTRIES, "premortem") is None

    def test_a_partial_name_does_not_match(self) -> None:
        """``fit`` must not match ``benefit``; the split is on the separator."""
        assert covering({"benefit-analysis": "..."}, "fit") is None


class TestEntriesGrouped:
    """M6: which procedures share an entry, at a count the grouping fixes.

    M5's partition is contiguous in table order, which is what makes its arm a
    function of ``n`` alone -- and which silently pairs ``cascade`` with
    ``timing``, the two rows diagnosed as colliding before any of it ran. A
    confusion inside one entry cannot be observed, so M5's routing number is
    partly the collision being hidden. This is how that gets varied.
    """

    SPLIT = (("ledger", "cascade"), ("fit", "timing"))

    def test_it_reproduces_the_contiguous_partition(self) -> None:
        """``entries`` is this function with the grouping table order gives."""
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        assert entries(description, document.body, 2) == entries_grouped(
            description, document.body, (("ledger", "fit"), ("cascade", "timing"))
        )

    def test_an_alternative_pairing_uses_the_same_words(self) -> None:
        """The manipulation is the grouping and nothing else.

        Both arms are the same four rows merged two ways, so the multiset of
        words across all entries must be identical. If it ever is not, the arm
        has started varying prose as well as grouping and cannot be read.
        """
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        contiguous = entries(description, document.body, 2)
        split = entries_grouped(description, document.body, self.SPLIT)
        assert list(split) == ["ledger-cascade", "fit-timing"]
        assert Counter(_words(contiguous)) == Counter(_words(split))

    def test_clause_order_stays_table_order(self) -> None:
        """Regrouping must not smuggle in a reordering of the merged sentence."""
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        built = entries_grouped(
            description, document.body, (("timing", "ledger"), ("fit",), ("cascade",))
        )
        assert "ledger-timing" in built

    def test_a_missing_procedure_is_rejected(self) -> None:
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        with pytest.raises(UnbundleError, match="must cover every procedure"):
            entries_grouped(description, document.body, (("ledger", "cascade"),))

    def test_a_repeated_procedure_is_rejected(self) -> None:
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        with pytest.raises(UnbundleError, match="more than one group"):
            entries_grouped(
                description, document.body, (("ledger", "cascade"), ("ledger", "fit", "timing"))
            )

    def test_a_name_the_table_lacks_is_rejected(self) -> None:
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        with pytest.raises(UnbundleError, match="not in the router table"):
            entries_grouped(
                description, document.body, (("ledger", "premortem"), ("fit", "cascade", "timing"))
            )

    def test_an_empty_group_is_rejected(self) -> None:
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        with pytest.raises(UnbundleError, match="empty group"):
            entries_grouped(
                description, document.body, ((), ("ledger", "fit", "cascade", "timing"))
            )


class TestAuthoredVariants:
    """L7's arms, and the constraints that stand in for derivation.

    These are the first arm texts in Tracks L and M that were *written*. That
    reintroduces the authoring problem those tracks avoid by construction, so
    what can be enforced is enforced here instead of promised in a docstring.
    """

    @pytest.mark.parametrize("variant", AUTHORED_VARIANTS)
    def test_the_routing_summary_and_exclusions_go_through_verbatim(self, variant: str) -> None:
        """The whole point of L7: eagerness without deleting what L5 measured."""
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        flat = " ".join(description.split())
        opener, exclusions = shared_scope(description)
        middle = flat[len(opener) : flat.find(exclusions)].strip()

        built = description_variant(description, variant)
        assert middle in built
        assert exclusions in built

    @pytest.mark.parametrize("variant", AUTHORED_VARIANTS)
    def test_the_shipped_opener_is_gone(self, variant: str) -> None:
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        opener, _ = shared_scope(description)
        assert opener not in description_variant(description, variant)

    def test_the_two_openers_are_matched_on_length(self) -> None:
        """Length is a live confound between two authored texts.

        L5 ruled it out across its own arms by deleting named parts. Nothing
        rules it out between two sentences someone wrote, so it is controlled.
        """
        ratio = len(_OPENER_NAMED) / len(_OPENER_SHOWN)
        assert abs(ratio - 1) <= 0.10, f"openers differ by {abs(ratio - 1):.0%}"

    def test_the_two_arms_differ_only_in_the_opener(self) -> None:
        document = parse_skill(SHIPPED)
        description = str(document.frontmatter["description"])
        named = description_variant(description, "stakes-named")
        shown = description_variant(description, "stakes-shown")
        assert named.replace(_OPENER_NAMED, "") == shown.replace(_OPENER_SHOWN, "")

    def test_named_states_a_criterion_and_shown_does_not(self) -> None:
        """The manipulation is tell against show, asserted rather than assumed."""
        assert "stakes" in _OPENER_NAMED
        assert "stakes" not in _OPENER_SHOWN
        assert _OPENER_SHOWN.count('"') >= 6, "shown carries example turns"
