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

**Which models go where lives in :data:`MODELS`, one row per family.** That is a
registry, not a gate on what may be run: ``--model`` still takes any string and
the arena check fires only where a caller asks for it. What the registry decides
is which runs may become *evidence*, and it keys that on the model **and the
backend it is reached through**, because those are two different facts and only
the pair identifies a venue. See :class:`ModelEntry`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

Arena = Literal["dev", "screen", "confirm"]

Split = Literal["public", "holdout"]

Backend = Literal["claude_code", "antigravity", "openai_compatible"]


class ArenaError(ValueError):
    """An operation was attempted that the arena does not permit."""


@dataclass(frozen=True)
class ModelEntry:
    """One model, and the venue it is reached through.

    **An arena is a property of the pair, not of the model.** That is the whole
    lesson of ``docs/HARNESS_DISCLOSURE.md`` written as a type, and it stopped
    being hypothetical on 2026-08-21, when ``agy`` turned out to serve
    ``claude-sonnet-4-6``: the same weights this repository calls ``confirm``
    tier through ``claude -p`` also arrive through a backend that wraps every
    call in fourteen thousand tokens of somebody else's agent scaffold with 57
    tools enabled. Pooling those two under one arena because the vendor matches
    would be the precise error the disclosure document exists to prevent.

    ``prefix`` rather than an exact id so a pinned dated model
    (``claude-haiku-4-5-20251001``) matches its family without editing this table
    on every release. :func:`resolve_model` takes the **longest** matching
    prefix.

    Where two backends serve the same vendor, the id is namespaced by backend --
    ``agy/claude-opus-4-6`` against the Claude CLI's ``claude-opus-4-6``. Making
    the ids disjoint is what lets a bare prefix match stay correct; without it
    the registry would have to guess, and it would have guessed wrong.
    """

    prefix: str
    vendor: str
    backend: Backend
    arena: Arena


#: Every model this repository knows how to run, and where each one may be run.
#: Adding a model is a row here; nothing else needs to change. Adding one to
#: ``confirm`` is a decision with a ``docs/DECISIONS.md`` entry, because that is
#: the only arena whose results are evidence.
MODELS: Final[tuple[ModelEntry, ...]] = (
    # Local and fixture backends. Free, unmetered, and unable to emit a verdict.
    ModelEntry("mockllm", "fixture", "openai_compatible", "dev"),
    ModelEntry("ollama", "local", "openai_compatible", "dev"),
    # The Claude Code CLI: every number this repository has published.
    ModelEntry("haiku", "anthropic", "claude_code", "screen"),
    ModelEntry("claude-haiku", "anthropic", "claude_code", "screen"),
    ModelEntry("sonnet", "anthropic", "claude_code", "confirm"),
    ModelEntry("opus", "anthropic", "claude_code", "confirm"),
    ModelEntry("claude-sonnet", "anthropic", "claude_code", "confirm"),
    ModelEntry("claude-opus", "anthropic", "claude_code", "confirm"),
    # The Antigravity CLI, namespaced under ``agy/`` for the same reason
    # ``openai_compatible`` namespaces under ``ollama/``: the bare ids are **not**
    # disjoint from the Claude CLI's. ``agy`` serves a model it calls
    # ``claude-opus-4-6``, and ``claude -p`` accepts that id too -- one is a
    # confirm-tier venue and the other is a coding agent with 57 tools, so a bare
    # id cannot say which ran. The label is stripped before the request and kept
    # in the record, where it makes `models_comparable` refuse the pooling by
    # itself.
    #
    # Every vendor lands in ``screen`` regardless of how capable the weights are,
    # because the venue cannot support a verdict: the scaffold is in context on
    # every call and no flag removes it. The tier is not the question --
    # ``agy/gemini-3.1-pro-high`` is a frontier model and still sits here.
    ModelEntry("agy/gemini-", "google", "antigravity", "screen"),
    ModelEntry("agy/gpt-oss", "openai", "antigravity", "screen"),
    ModelEntry("agy/claude-", "anthropic", "antigravity", "screen"),
)

#: Aliases that name a family rather than a set of weights. Refused outright.
#:
#: ``agy`` defaults to ``--model auto`` and accepts ``pro``, ``flash`` and
#: ``flash-lite``; the Gemini CLI does the same. A record naming one of these
#: cannot say which weights answered, so a run made under an alias is not
#: reproducible even by the person who made it, and the failure is silent --
#: the run completes, the checkpoint fills, and the number describes an unknown.
UNPINNED_ALIASES: Final[frozenset[str]] = frozenset(
    {"auto", "pro", "flash", "flash-lite", "default", "latest"}
)


@dataclass(frozen=True)
class ArenaPolicy:
    """What an arena is allowed to do."""

    name: Arena
    split: Split
    may_revise_skill: bool
    emits_verdict: bool
    requires_preregistration: bool

    @property
    def model_prefixes(self) -> tuple[str, ...]:
        """The model prefixes this arena accepts, derived from :data:`MODELS`.

        Derived rather than stored so the registry is the single place a model's
        arena is written down. Two copies of that fact would eventually disagree,
        and the disagreement would be invisible.
        """
        return tuple(sorted(entry.prefix for entry in MODELS if entry.arena == self.name))


ARENAS: Final[dict[Arena, ArenaPolicy]] = {
    "dev": ArenaPolicy(
        name="dev",
        split="public",
        may_revise_skill=True,
        emits_verdict=False,
        requires_preregistration=False,
    ),
    "screen": ArenaPolicy(
        name="screen",
        split="public",
        may_revise_skill=True,
        emits_verdict=False,
        requires_preregistration=False,
    ),
    "confirm": ArenaPolicy(
        name="confirm",
        split="holdout",
        may_revise_skill=False,
        emits_verdict=True,
        requires_preregistration=True,
    ),
}


def resolve_model(model: str) -> ModelEntry:
    """Find the registry row for a model id.

    Raises:
        ArenaError: The id is an unpinned alias, or no row matches it. Both
            messages name this file and the row to add, because "unknown model"
            without that is a dead end for whoever hits it.
    """
    if model.strip().lower() in UNPINNED_ALIASES:
        raise ArenaError(
            f"{model!r} names a family, not a set of weights, and this repository "
            "refuses to run one. Pin the resolved id instead -- `agy models` lists "
            "them -- so the record can say what answered."
        )
    matches = [entry for entry in MODELS if model.startswith(entry.prefix)]
    if not matches:
        raise ArenaError(
            f"model {model!r} is not in the registry. Add a `ModelEntry` to `MODELS` in "
            "`decision_evals/arenas.py` naming its vendor, its backend and its arena. "
            "Guessing an arena for an unknown model is how a screening result becomes "
            "a verdict."
        )
    return max(matches, key=lambda entry: len(entry.prefix))


def policy_for(arena: str) -> ArenaPolicy:
    """Look up an arena's policy.

    Raises:
        ArenaError: Unknown arena.
    """
    if arena not in ARENAS:
        raise ArenaError(f"unknown arena {arena!r}; expected one of {sorted(ARENAS)}")
    return ARENAS[arena]


def assert_model_allowed(arena: str, model: str, *, backend: str | None = None) -> ArenaPolicy:
    """Refuse a model that does not belong to the arena.

    This is the load-bearing check in both directions. Running a frontier model
    in ``dev`` would spend quota on a run that cannot produce a verdict; running
    a local model in ``confirm`` would produce a verdict about the wrong model
    entirely. Neither is caught by any downstream analysis.

    Args:
        arena: The arena the caller intends to run in.
        model: The pinned model id.
        backend: The backend the caller is about to drive, when it knows. Checked
            against the registry rather than trusted, because the id space is
            only *nearly* disjoint -- see :class:`ModelEntry` on
            ``claude-sonnet-4-6``.

    Raises:
        ArenaError: The model is unknown, unpinned, belongs to another arena, or
            is about to be driven through a backend that does not serve it.
    """
    policy = policy_for(arena)
    entry = resolve_model(model)
    if entry.arena != arena:
        raise ArenaError(
            f"model {model!r} belongs to the {entry.arena!r} arena, not {arena!r}. It is "
            f"served by {entry.backend!r}, and running the wrong tier here produces a "
            "number that describes a different experiment from the one being reported."
        )
    if backend is not None and backend != entry.backend:
        raise ArenaError(
            f"model {model!r} is served by {entry.backend!r}, but {backend!r} was about "
            "to run it. The same weights reached through a different harness are a "
            "different venue, not the same measurement with a different label."
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
