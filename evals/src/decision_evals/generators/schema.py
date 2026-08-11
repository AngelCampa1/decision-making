"""Template schema.

A template is a parameterised scenario whose answer is *computed*, not written.
Auditing ~50 rules is tractable; auditing 300 authored answers is not, and the
difference is what makes a self-generated benchmark trustworthy rather than
merely uncontaminated.

**Naming note.** The plan called the distractor-count and position axes ``arms``.
They are renamed ``strata`` here, because "arm" already means something specific
and load-bearing in this project — ``off`` / ``on`` / ``placebo`` / ``cot``.
Strata partition the *items*; arms partition the *treatment*. Every item appears
in every arm, which is the whole point of a paired design, so collapsing the two
words would have made the analysis code read as if it were doing something it
must never do.

Validation is deliberately strict and happens at load time. A template that
references an undefined variable, or declares a load-bearing fact that does not
exist, is a silent benchmark defect — the generator would happily produce items
and the error would surface as inexplicable model failures weeks later.
"""

from __future__ import annotations

from string import Formatter
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from decision_evals.generators.safe_eval import referenced_names, validate

#: Distractor strength, in the sense used by the context-rot literature: how
#: semantically related the irrelevant fact is to the question. Strong
#: distractors hurt more than weak ones, and one strong distractor hurts more
#: than several weak ones, so strength is a stratifying variable rather than
#: flavour text.
Strength = Literal["low", "medium", "high"]

Position = Literal["early", "middle", "late"]

TemplateId = Annotated[str, Field(pattern=r"^[a-z]+-\d{3}-[a-z0-9-]+$")]


class _Strict(BaseModel):
    """Reject unknown keys everywhere.

    A typo in a template key would otherwise be silently ignored, which is the
    failure mode this whole schema exists to prevent.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class Variable(_Strict):
    """One sampled variable. Exactly one sampling mode must be given."""

    choice: list[Any] | None = None
    int_range: tuple[int, int] | None = Field(default=None, alias="int")

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    @model_validator(mode="after")
    def _exactly_one_mode(self) -> Variable:
        modes = [self.choice is not None, self.int_range is not None]
        if sum(modes) != 1:
            raise ValueError("a variable needs exactly one of `choice` or `int`")
        if self.choice is not None and not self.choice:
            raise ValueError("`choice` must not be empty")
        if self.int_range is not None and self.int_range[0] > self.int_range[1]:
            raise ValueError(f"`int` range is inverted: {self.int_range}")
        return self


class Fact(_Strict):
    """A statement presented to the model."""

    id: str = Field(pattern=r"^[rd]\d+$")
    text: str = Field(min_length=1)


class Distractor(Fact):
    """A fact that must not change the answer.

    ``collides_with`` names a variable the solution expression reads, and
    asserts that this distractor states a quantity of the *same kind and units*
    — distinguished from the real one only by a qualifier a careful reader has
    to notice.

    That field exists because the first control run came back at ceiling, and
    reading the transcripts showed why: the original distractors were unrelated
    to the decision rule in type, not merely in topic, so nothing competed and
    only 13 of 93 loaded responses acknowledged them at all. ``strength`` ranks
    topical proximity, which turned out to be the wrong axis. A number in the
    units of the computation is the right one.

    The cliff on the other side is the GSM-NoOp re-audit's: a distractor placed
    *too* close is one a reasonable solver folds in, and a model that "fails" it
    is defensibly right. The qualifier requirement is what keeps a colliding
    distractor irrelevant rather than ambiguous, and the two-auditor filter
    still runs on top of it.
    """

    strength: Strength
    collides_with: str | None = None


class Solution(_Strict):
    """The computed answer, and which facts it depends on."""

    expr: str = Field(min_length=1)
    load_bearing: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _expression_is_safe(self) -> Solution:
        validate(self.expr)
        return self


class Strata(_Strict):
    """How items are partitioned within a template.

    ``distractors`` must include ``0``. The zero-distractor stratum is the
    clean-room split, and the protocol's first dataset gate is defined on it —
    an item missed *without* distractors is ambiguous, not hard. A template that
    cannot produce clean items cannot be difficulty-calibrated, so this is
    required rather than conventional.
    """

    distractors: list[int] = Field(min_length=1)
    position: list[Position] = Field(min_length=1)

    @model_validator(mode="after")
    def _has_a_clean_stratum(self) -> Strata:
        if 0 not in self.distractors:
            raise ValueError("`distractors` must include 0 (the clean-room stratum)")
        if any(count < 0 for count in self.distractors):
            raise ValueError("`distractors` counts must be non-negative")
        return self


class Template(_Strict):
    """A parameterised scenario."""

    template_id: TemplateId
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2)
    variables: dict[str, Variable]
    relevant_facts: list[Fact] = Field(min_length=1)
    distractor_facts: list[Distractor]
    solution: Solution
    strata: Strata
    variants: int = Field(default=6, ge=1, le=64)

    @model_validator(mode="after")
    def _cross_references_resolve(self) -> Template:
        self._check_fact_ids()
        self._check_load_bearing()
        self._check_placeholders()
        self._check_solution_names()
        self._check_distractor_supply()
        self._check_collisions()
        return self

    # -- individual checks, split out so each failure names its own cause ----

    def _check_fact_ids(self) -> None:
        ids = [fact.id for fact in self.all_facts]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"duplicate fact ids: {duplicates}")
        for fact in self.relevant_facts:
            if not fact.id.startswith("r"):
                raise ValueError(f"relevant fact {fact.id!r} must have an `r` prefix")
        for fact in self.distractor_facts:
            if not fact.id.startswith("d"):
                raise ValueError(f"distractor {fact.id!r} must have a `d` prefix")

    def _check_load_bearing(self) -> None:
        relevant = {fact.id for fact in self.relevant_facts}
        missing = sorted(set(self.solution.load_bearing) - relevant)
        if missing:
            raise ValueError(f"load_bearing names facts that are not relevant facts: {missing}")

    def _check_placeholders(self) -> None:
        """Every ``{name}`` must be a declared variable.

        Caught here because the alternative is a ``KeyError`` from
        ``str.format`` midway through generation, by which point the template
        that caused it is several frames away.
        """
        known = set(self.variables)
        for label, text in self._formattable():
            for _, field, _, _ in Formatter().parse(text):
                if field is not None and field not in known:
                    raise ValueError(
                        f"{label} references undeclared variable {field!r}; "
                        f"declared: {sorted(known)}"
                    )

    def _check_solution_names(self) -> None:
        unknown = sorted(referenced_names(self.solution.expr) - set(self.variables))
        if unknown:
            raise ValueError(f"solution expression references undeclared variables: {unknown}")

    def _check_distractor_supply(self) -> None:
        wanted = max(self.strata.distractors)
        if wanted > len(self.distractor_facts):
            raise ValueError(
                f"strata ask for {wanted} distractors but only "
                f"{len(self.distractor_facts)} are defined"
            )

    def _check_collisions(self) -> None:
        """Require at least one distractor that can actually compete.

        A template whose distractors are all type-incompatible with the decision
        rule cannot exert ranking pressure, and will read as a null result about
        the skill when it is really a null result about the item. Measured
        rather than assumed: the first control run scored 110/110 on exactly
        such a corpus.

        Resolving the pairing here rather than at generation time means an
        ambiguous collision is a load-time error naming the template, instead of
        a type error thrown from inside the sampler several frames away.
        """
        if not any(d.collides_with is not None for d in self.distractor_facts):
            raise ValueError(
                "no distractor declares `collides_with`. At least one must state a "
                "quantity in the units of the decision rule, or nothing competes for "
                "the model's attention and the template measures nothing."
            )
        self.collision_pairs()

    def collision_pairs(self) -> list[tuple[str, str]]:
        """``(solution variable, competing variable)`` for each colliding distractor.

        The competing variable is the one the distractor carries that the
        solution does not read, matched on declared kind — an ``int`` threshold
        competes with an ``int``, never with a ``choice`` of vendor names that
        happens to appear in the same sentence.
        """
        solution_vars = referenced_names(self.solution.expr)
        pairs: list[tuple[str, str]] = []

        for distractor in self.distractor_facts:
            target = distractor.collides_with
            if target is None:
                continue
            if target not in solution_vars:
                raise ValueError(
                    f"distractor {distractor.id!r} collides_with {target!r}, which the "
                    f"solution does not read; it reads {sorted(solution_vars)}"
                )
            kind = self._kind_of(target)
            candidates = sorted(
                name
                for name in self._variables_in(distractor.text) - solution_vars
                if self._kind_of(name) == kind
            )
            if len(candidates) != 1:
                raise ValueError(
                    f"distractor {distractor.id!r} collides_with {target!r} (kind "
                    f"{kind!r}) but carries {len(candidates)} competing variable(s) of "
                    f"that kind {candidates}; it needs exactly one"
                )
            pairs.append((target, candidates[0]))
        return pairs

    def _kind_of(self, name: str) -> str:
        # Indexed rather than guarded: `_check_placeholders` and
        # `_check_solution_names` both run first, so every name reaching here is
        # declared. A KeyError would mean those checks were reordered, which is
        # worth failing loudly rather than papering over.
        return "int" if self.variables[name].int_range is not None else "choice"

    @staticmethod
    def _variables_in(text: str) -> set[str]:
        return {field for _, field, _, _ in Formatter().parse(text) if field}

    # -- derived views ------------------------------------------------------

    @property
    def all_facts(self) -> list[Fact]:
        return [*self.relevant_facts, *self.distractor_facts]

    def _formattable(self) -> list[tuple[str, str]]:
        pairs = [("question", self.question)]
        pairs += [(f"fact {fact.id}", fact.text) for fact in self.all_facts]
        return pairs
