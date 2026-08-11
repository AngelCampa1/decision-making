"""Deterministic item generation.

``generate(template, seed)`` is a pure function of its arguments. That is
enforced by golden-file tests rather than asserted in a docstring, because the
nastiest bug an eval harness can have is a benchmark that drifts silently
between runs: every number computed before the drift becomes incomparable with
every number after it, and nothing in the analysis would notice.

Two design choices are worth reading before the code.

**Variable samplings are shared across strata.** ``variants`` counts *variable
samplings*, not items. Each sampling is then instantiated at every
(distractor-count, position) combination, so the clean item and the loaded items
carry identical variable bindings and differ only in the irrelevant material.
The clean-room check and the difficulty gate are therefore computed on matched
content rather than on independently sampled scenarios — the comparison the
protocol actually wants to make.

**Seeds are derived by hash, not by mutation.** Each item's RNG is seeded from
``sha256(template_id:seed:variant)``. That makes an item's content depend on its
own coordinates and nothing else, so generating item 7 alone produces exactly
what generating items 0-20 produces at index 7. A shared, sequentially advanced
RNG would make every item depend on how many items happened to precede it.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence
from itertools import product
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from decision_evals.generators.safe_eval import evaluate
from decision_evals.generators.schema import Fact, Position, Strength, Template

#: Position label used when a stratum has no distractors to position.
NO_POSITION = "none"

#: How many draws a variant may take to hit its assigned answer before the
#: template is declared defective. Generous: a balanced binary template needs
#: about two draws on average, so reaching this bound means an option is
#: effectively unreachable rather than merely uncommon.
_MAX_SAMPLING_ATTEMPTS = 500


class RenderedFact(BaseModel):
    """One fact as presented, with its provenance retained for scoring."""

    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    role: Literal["relevant", "distractor"]
    strength: Strength | None = None


class Item(BaseModel):
    """One generated scenario, ready to render into a prompt."""

    model_config = ConfigDict(frozen=True)

    item_id: str
    template_id: str
    seed: int
    variant: int
    n_distractors: int
    position: str
    variables: dict[str, Any]
    question: str
    options: list[str]
    facts: list[RenderedFact]
    answer: str
    load_bearing: list[str]
    distractor_ids: list[str]


class GenerationError(ValueError):
    """A template produced an item that cannot be scored."""


def derive_seed(template_id: str, seed: int, variant: int) -> int:
    """Derive a stable per-variant seed.

    Uses SHA-256 rather than :func:`hash`, which is randomised per process and
    would make generation irreproducible across runs on the same machine.
    """
    digest = hashlib.sha256(f"{template_id}:{seed}:{variant}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def strata_combinations(
    distractor_counts: list[int], positions: list[Position]
) -> list[tuple[int, str]]:
    """Enumerate the (count, position) strata, deduplicating the clean stratum.

    Position is meaningless with zero distractors, so the clean stratum appears
    once rather than once per position. Without this the clean split would be
    over-represented by a factor of ``len(positions)`` and would quietly
    dominate any pooled estimate.
    """
    combos: list[tuple[int, str]] = []
    for count, position in product(sorted(set(distractor_counts)), positions):
        combo = (count, NO_POSITION if count == 0 else position)
        if combo not in combos:
            combos.append(combo)
    return combos


def sample_variables(template: Template, rng: random.Random) -> dict[str, Any]:
    """Sample one binding for every declared variable."""
    values: dict[str, Any] = {}
    for name, spec in sorted(template.variables.items()):
        if spec.choice is not None:
            values[name] = rng.choice(spec.choice)
        else:
            assert spec.int_range is not None  # guaranteed by the schema
            low, high = spec.int_range
            values[name] = rng.randint(low, high)
    return values


def arrange(relevant: Sequence[Fact], distractors: Sequence[Fact], position: str) -> list[Fact]:
    """Interleave distractors with relevant facts at the requested position.

    Position is a first-class stratum because of the U-shaped position
    sensitivity documented in the long-context literature: the same distractor
    costs differently depending on where it sits. Pooling over positions would
    average that away.
    """
    if not distractors:
        return list(relevant)
    if position == "early":
        return [*distractors, *relevant]
    if position == "late":
        return [*relevant, *distractors]
    if position == "middle":
        midpoint = len(relevant) // 2
        return [*relevant[:midpoint], *distractors, *relevant[midpoint:]]
    raise GenerationError(f"unknown position {position!r}")


def generate(template: Template, seed: int) -> list[Item]:
    """Generate every item for a template at a given seed.

    Returns:
        ``variants x len(strata_combinations(...))`` items, in a stable order.
    """
    combos = strata_combinations(template.strata.distractors, template.strata.position)
    items: list[Item] = []

    for variant in range(template.variants):
        rng = random.Random(derive_seed(template.template_id, seed, variant))
        variables, answer = _sample_for_target(template, rng, _target(template, variant))

        # Drawn once per variant, before the stratum loop, so the loaded strata
        # of a given variant share the same distractor pool. A larger stratum is
        # then a superset of a smaller one rather than an unrelated draw, which
        # makes the distractor-count effect a within-variant contrast.
        pool = rng.sample(template.distractor_facts, k=max(count for count, _ in combos))

        for count, position in combos:
            chosen = list(pool[:count])
            ordered = arrange(template.relevant_facts, chosen, position)
            items.append(
                Item(
                    item_id=f"{template.template_id}#v{variant}-d{count}-{position}",
                    template_id=template.template_id,
                    seed=seed,
                    variant=variant,
                    n_distractors=count,
                    position=position,
                    variables=variables,
                    question=template.question.format(**variables),
                    options=list(template.options),
                    facts=[_render(fact, variables) for fact in ordered],
                    answer=answer,
                    load_bearing=list(template.solution.load_bearing),
                    distractor_ids=[fact.id for fact in chosen],
                )
            )
    return items


def _target(template: Template, variant: int) -> str:
    """The answer this variant is required to have.

    Cycling through the options makes the label distribution exactly uniform
    whenever ``variants`` is a multiple of ``len(options)``, which every shipped
    template arranges.
    """
    return template.options[variant % len(template.options)]


def _sample_for_target(
    template: Template, rng: random.Random, target: str
) -> tuple[dict[str, Any], str]:
    """Resample variables until the computed answer is ``target``.

    Label balance is enforced by construction rather than left to chance. An
    early draft sampled freely, and at four variants two of the ten templates
    came out entirely single-class -- solvable by always guessing the majority
    label, and worthless as evidence about anything.

    Balancing also fixes the meaning of the difficulty gate. Chance accuracy is
    now exactly ``1 / len(options)``, so the protocol's [0.35, 0.75] band sits
    around a known 0.5 for a binary template instead of around whatever the
    sampler happened to produce.

    Rejection sampling is used rather than solving the constraint because the
    solution expression is arbitrary within the whitelist. It is cheap: the
    bound below is generous, and a template that reaches it has a real defect --
    an option it can rarely or never produce -- which should stop the build
    rather than quietly skew the dataset.
    """
    for _ in range(_MAX_SAMPLING_ATTEMPTS):
        variables = sample_variables(template, rng)
        answer = _compute_answer(template, variables)
        if answer == target:
            return variables, answer
    raise GenerationError(
        f"{template.template_id}: could not produce answer {target!r} in "
        f"{_MAX_SAMPLING_ATTEMPTS} attempts. The variable ranges make this option "
        f"unreachable or very rare, which would leave the template unbalanced."
    )


def _compute_answer(template: Template, variables: dict[str, Any]) -> str:
    answer = evaluate(template.solution.expr, variables)
    if not isinstance(answer, str):
        raise GenerationError(
            f"{template.template_id}: solution returned {type(answer).__name__}, expected str"
        )
    if answer not in template.options:
        raise GenerationError(
            f"{template.template_id}: solution returned {answer!r}, "
            f"which is not one of the options {template.options}"
        )
    return answer


def _render(fact: Fact, variables: dict[str, Any]) -> RenderedFact:
    from decision_evals.generators.schema import Distractor

    is_distractor = isinstance(fact, Distractor)
    return RenderedFact(
        id=fact.id,
        text=fact.text.format(**variables),
        role="distractor" if is_distractor else "relevant",
        strength=fact.strength if isinstance(fact, Distractor) else None,
    )
