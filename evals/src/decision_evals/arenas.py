"""Arena separation.

Three arenas with different permissions, enforced in code rather than by
discipline. The reason is Prompting Inversion (arXiv:2510.22251): a sculpted
prompt helped GPT-4o (97% vs 93%) and *hurt* GPT-5 (94.00% vs 96.36% plain CoT).
Scaffolding tuned against a weak model can become a handicap on a strong one.

So iterating freely against cheap models is fine and expected -- it is where a
skill actually gets good -- and carrying that iteration into a verdict is not.
The separation exists to make the second thing impossible rather than
discouraged, which is exactly the discipline SkillOpt's accept-if-strictly-better
ratchet lacks.

``dev`` and ``screen`` may revise a skill as often as they like. ``confirm`` may
not, runs on the private holdout, and is the only arena that emits a verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

Arena = Literal["dev", "screen", "confirm"]

Split = Literal["public", "holdout"]


class ArenaError(ValueError):
    """An operation was attempted that the arena does not permit."""


@dataclass(frozen=True)
class ArenaPolicy:
    """What an arena is allowed to do."""

    name: Arena
    #: Model identifiers must start with one of these. Prefixes rather than an
    #: exact list so a pinned dated model id (``claude-haiku-4-5-20251001``)
    #: still matches its family without editing this table on every release.
    model_prefixes: tuple[str, ...]
    split: Split
    may_revise_skill: bool
    emits_verdict: bool
    requires_preregistration: bool


ARENAS: Final[dict[Arena, ArenaPolicy]] = {
    "dev": ArenaPolicy(
        name="dev",
        model_prefixes=("mockllm", "ollama"),
        split="public",
        may_revise_skill=True,
        emits_verdict=False,
        requires_preregistration=False,
    ),
    "screen": ArenaPolicy(
        name="screen",
        model_prefixes=("haiku", "claude-haiku"),
        split="public",
        may_revise_skill=True,
        emits_verdict=False,
        requires_preregistration=False,
    ),
    "confirm": ArenaPolicy(
        name="confirm",
        model_prefixes=("sonnet", "opus", "claude-sonnet", "claude-opus"),
        split="holdout",
        may_revise_skill=False,
        emits_verdict=True,
        requires_preregistration=True,
    ),
}


def policy_for(arena: str) -> ArenaPolicy:
    """Look up an arena's policy.

    Raises:
        ArenaError: Unknown arena.
    """
    if arena not in ARENAS:
        raise ArenaError(f"unknown arena {arena!r}; expected one of {sorted(ARENAS)}")
    return ARENAS[arena]


def assert_model_allowed(arena: str, model: str) -> ArenaPolicy:
    """Refuse a model that does not belong to the arena.

    This is the load-bearing check in both directions. Running a frontier model
    in ``dev`` would spend quota on a run that cannot produce a verdict; running
    a local model in ``confirm`` would produce a verdict about the wrong model
    entirely. Neither is caught by any downstream analysis.
    """
    policy = policy_for(arena)
    if not any(model.startswith(prefix) for prefix in policy.model_prefixes):
        raise ArenaError(
            f"model {model!r} is not permitted in the {arena!r} arena, which accepts "
            f"{list(policy.model_prefixes)}. Running the wrong tier here produces a "
            "number that describes a different experiment from the one being reported."
        )
    return policy


def assert_may_revise_skill(arena: str) -> None:
    """Refuse a skill edit in a hash-locked arena."""
    policy = policy_for(arena)
    if not policy.may_revise_skill:
        raise ArenaError(
            f"the {arena!r} arena is hash-locked and may not revise a skill. Iterate in "
            "'dev' or 'screen', then pre-register a new version."
        )


def assert_may_emit_verdict(arena: str) -> None:
    """Refuse a verdict from an arena that cannot support one."""
    policy = policy_for(arena)
    if not policy.emits_verdict:
        raise ArenaError(
            f"the {arena!r} arena does not emit verdicts. Its results guide iteration and "
            "decide whether to spend on a confirmation run; they are not evidence."
        )


def assert_split_allowed(arena: str, split: str) -> None:
    """Refuse a run against the wrong split.

    The holdout is the only uncontaminated data we have, and spending it on a
    screening run cannot be undone within a seed.
    """
    policy = policy_for(arena)
    if split != policy.split:
        raise ArenaError(f"the {arena!r} arena runs on the {policy.split!r} split, not {split!r}.")
