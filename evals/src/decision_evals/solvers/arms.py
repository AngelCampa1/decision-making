"""The experimental arms.

Four arms plus an ecological-validity fifth. The whole design rests on three
rules, and each is enforced here rather than left to whoever assembles a run.

**The response-format contract appears in every arm.** If only the treatment is
told to emit a structured answer, the experiment measures instruction-following
rather than decision quality, and the treatment wins for a reason that has
nothing to do with the skill. :data:`FORMAT_CONTRACT` is concatenated into every
arm's system prompt with no way to omit it.

**The option menu is held constant.** AgentAtlas found that removing explicit
option menus moved trajectory accuracy by 14-40pp across all eight models
tested -- larger than any effect we expect to measure. The menu lives in
:func:`render_item`, which is arm-independent, so it cannot vary by construction.

**The placebo is matched on tokens and structure.** A skill that beats ``off``
but not ``placebo`` is a length effect. :func:`check_placebo_match` refuses a
placebo that is not the right size, because an unmatched placebo is worse than
none: it looks like a control while silently failing to control for the thing it
exists to control for.

Wording follows the trust-framing result (arXiv:2603.14373), where trust-framed
system prompts surfaced 59% more hidden issues while fear-framing showed no gain
over unframed. Nothing here threatens the model with consequences.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from decision_evals.generators.generate import Item

ArmName = Literal["off", "on", "placebo", "cot", "in_situ"]

#: Every arm, in reporting order. ``in_situ`` is last because it answers a
#: different question from the other four: not "does the skill help" but "does
#: it still help when it is not the only thing in the prompt".
ARM_NAMES: Final[tuple[ArmName, ...]] = ("off", "on", "placebo", "cot", "in_situ")

#: Present in every arm without exception.
FORMAT_CONTRACT: Final = (
    "Give your reasoning if it helps you, then end your reply with a final line "
    "in exactly this form:\n"
    "ANSWER: <one of the listed options>\n"
    "Use the option text exactly as written in the list."
)

#: The task framing. Shared by every arm, so no arm is better oriented than
#: another before the skill is introduced.
BASE_FRAMING: Final = (
    "You are helping someone make a decision. You will be given some background "
    "facts, a question, and a fixed list of options. Choose the option the facts "
    "support."
)

#: The `cot` arm. Deliberately the plainest common phrasing rather than a tuned
#: one -- it is the tripwire for "is this skill an expensive way to say think",
#: and a sculpted CoT prompt would be a different experiment.
COT_INSTRUCTION: Final = "Think step by step before you answer."


class ArmError(ValueError):
    """An arm was requested that cannot be constructed as specified."""


@dataclass(frozen=True)
class ArmPrompt:
    """A rendered arm: what to send, and how to send it."""

    arm: ArmName
    system_prompt: str
    #: True when the prompt should be *appended* to the CLI's built-in system
    #: prompt rather than replacing it. Only ``in_situ`` sets this.
    append: bool


def build_arm(
    arm: ArmName,
    *,
    skill_body: str | None = None,
    placebo_body: str | None = None,
) -> ArmPrompt:
    """Render one arm's system prompt.

    Args:
        arm: Which arm.
        skill_body: The skill under test. Required by ``on`` and ``in_situ``.
        placebo_body: Token- and structure-matched filler. Required by
            ``placebo``.

    Raises:
        ArmError: An unknown arm, or a required body was not supplied. Missing
            bodies are an error rather than a silent fallback to the control:
            an arm that quietly degrades into ``off`` produces a null result
            that looks like evidence.
    """
    if arm not in ARM_NAMES:
        raise ArmError(f"unknown arm {arm!r}; expected one of {list(ARM_NAMES)}")

    sections = [BASE_FRAMING]

    if arm in ("on", "in_situ"):
        if not skill_body:
            raise ArmError(f"the {arm!r} arm needs a skill body")
        sections.append(skill_body.strip())
    elif arm == "placebo":
        if not placebo_body:
            raise ArmError("the 'placebo' arm needs a placebo body")
        sections.append(placebo_body.strip())
    elif arm == "cot":
        sections.append(COT_INSTRUCTION)

    sections.append(FORMAT_CONTRACT)
    return ArmPrompt(arm=arm, system_prompt="\n\n".join(sections), append=arm == "in_situ")


def render_item(item: Item) -> str:
    """Render the user-facing item text.

    Arm-independent by construction. Everything that varies between arms lives
    in the system prompt, so the option menu -- the single largest known
    scaffolding effect in the literature -- is identical in all five.

    Facts are presented in the order the generator arranged them, because
    position is a stratum and reordering here would destroy it.
    """
    facts = "\n".join(f"- {fact.text}" for fact in item.facts)
    options = "\n".join(f"- {option}" for option in item.options)
    return f"Background:\n{facts}\n\nQuestion: {item.question}\n\nOptions:\n{options}"


@dataclass(frozen=True)
class PlaceboMatch:
    """How closely a placebo matches the skill it stands in for."""

    skill_words: int
    placebo_words: int
    skill_sections: int
    placebo_sections: int
    tolerance: float
    skill_templates: int = 0
    placebo_templates: int = 0

    @property
    def word_ratio(self) -> float:
        return self.placebo_words / self.skill_words if self.skill_words else 0.0

    @property
    def words_match(self) -> bool:
        return abs(self.word_ratio - 1.0) <= self.tolerance

    @property
    def structure_matches(self) -> bool:
        return self.skill_sections == self.placebo_sections

    @property
    def templates_match(self) -> bool:
        """Whether both documents request the same number of output templates.

        A fenced block in a skill is almost always an output contract, and the
        two checks above cannot see one: ``evidence-ledger`` ends with a
        LEDGER / SET ASIDE / THEREFORE block while its placebo ends with a
        paragraph, and that pair passes on both word count and heading count.

        The venue imposes a five-block contract of its own, so the ``on`` arm
        would arrive carrying a second format instruction that the ``placebo``
        arm does not. An arm that emits more structure because it was told to,
        scored on a structured contract, is a format effect wearing a decision
        effect's clothes.
        """
        return self.skill_templates == self.placebo_templates

    @property
    def ok(self) -> bool:
        return self.words_match and self.structure_matches and self.templates_match


def check_placebo_match(
    skill_body: str, placebo_body: str, *, tolerance: float = 0.15
) -> PlaceboMatch:
    """Measure whether a placebo is a fair control for a skill.

    Length and section count, not content. Both are crude proxies, and the
    honest description is that they rule out the *obvious* failure -- a
    two-line placebo standing in for a two-page skill -- rather than
    establishing equivalence. Content matching is what the human review of the
    placebo text is for, and there is no automating that.

    ``tolerance`` is a fraction of the skill's word count; 15% is tight enough
    that a placebo cannot be half the length and loose enough that prose does
    not have to be padded to an exact count.
    """
    return PlaceboMatch(
        skill_words=len(skill_body.split()),
        placebo_words=len(placebo_body.split()),
        skill_sections=_count_headings(skill_body),
        placebo_sections=_count_headings(placebo_body),
        tolerance=tolerance,
        skill_templates=_count_fences(skill_body),
        placebo_templates=_count_fences(placebo_body),
    )


def _count_headings(body: str) -> int:
    return sum(1 for line in body.splitlines() if line.lstrip().startswith("#"))


def _count_fences(body: str) -> int:
    """Fenced blocks, counted as opening/closing pairs."""
    return sum(1 for line in body.splitlines() if line.lstrip().startswith("```")) // 2
