"""Tests for the integrity locks: arenas, pre-registration, budget.

These three modules carry a 100% branch-coverage floor, and the reason is
specific to what they are. A refusal branch that has never executed is a refusal
nobody has checked, and every one of them exists to stop a run that would
produce a dishonest number. A lock that silently fails open is worse than no
lock, because the run still completes and the number still looks fine.

So every ``raise`` below has a test asserting it fires.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from decision_evals.arenas import (
    ARENAS,
    MODELS,
    ArenaError,
    assert_may_emit_verdict,
    assert_may_revise_skill,
    assert_model_allowed,
    assert_split_allowed,
    policy_for,
    resolve_model,
)
from decision_evals.budget import BudgetError, BudgetLedger, estimate_cost_usd, project_cost
from decision_evals.prereg import (
    Preregistration,
    PreregistrationError,
    RepoState,
    assert_runnable,
    load_preregistration,
    sha256_text,
)

SKILL = "# Evidence ledger\nVerify, then discard."
ANALYSIS = "def analyse():\n    return 1\n"


# ===========================================================================
# Arenas
# ===========================================================================


def test_every_arena_is_self_consistent() -> None:
    """A verdict from a public split, or from a revisable skill, is not a verdict."""
    for policy in ARENAS.values():
        if policy.emits_verdict:
            assert policy.split == "holdout"
            assert not policy.may_revise_skill
            assert policy.requires_preregistration


def test_exactly_one_arena_emits_verdicts() -> None:
    assert [name for name, p in ARENAS.items() if p.emits_verdict] == ["confirm"]


def test_an_unknown_arena_is_refused() -> None:
    with pytest.raises(ArenaError, match="unknown arena"):
        policy_for("production")


@pytest.mark.parametrize(
    ("arena", "model"),
    [
        ("dev", "mockllm/model"),
        ("dev", "ollama/qwen3:8b"),
        ("screen", "haiku"),
        ("screen", "claude-haiku-4-5-20251001"),
        ("confirm", "sonnet"),
        ("confirm", "claude-opus-4-6"),
    ],
)
def test_permitted_models_are_accepted(arena: str, model: str) -> None:
    assert assert_model_allowed(arena, model).name == arena


def test_a_frontier_model_is_refused_in_dev() -> None:
    """Spends quota on a run that cannot produce a verdict."""
    with pytest.raises(ArenaError, match="belongs to the 'confirm' arena, not 'dev'"):
        assert_model_allowed("dev", "opus")


@pytest.mark.parametrize(
    ("model", "arena", "backend", "vendor"),
    [
        ("agy/gemini-3.7-flash-low", "screen", "antigravity", "google"),
        ("agy/gpt-oss-120b-medium", "screen", "antigravity", "openai"),
        ("agy/claude-sonnet-4-6", "screen", "antigravity", "anthropic"),
    ],
)
def test_antigravity_models_resolve_to_screen(
    model: str, arena: str, backend: str, vendor: str
) -> None:
    """Every model on this backend screens, however capable the weights are.

    The venue cannot support a verdict -- the agent scaffold and its 57 tools are
    in context on every call and no flag removes them -- so the tier of the model
    is not what decides this.
    """
    entry = resolve_model(model)
    assert (entry.arena, entry.backend, entry.vendor) == (arena, backend, vendor)


def test_the_same_weights_on_two_backends_are_two_venues() -> None:
    """The collision this registry exists to resolve.

    ``agy`` serves a model it calls ``claude-opus-4-6`` and ``claude -p`` accepts
    that id too. Reading them as one model would file a coding agent's answers
    under the arena whose results are evidence.
    """
    assert resolve_model("claude-opus-4-6").arena == "confirm"
    assert resolve_model("agy/claude-opus-4-6").arena == "screen"
    with pytest.raises(ArenaError, match="belongs to the 'screen' arena"):
        assert_model_allowed("confirm", "agy/claude-opus-4-6")


@pytest.mark.parametrize("alias", ["auto", "pro", "flash", "flash-lite", "default", "latest"])
def test_an_unpinned_alias_is_refused(alias: str) -> None:
    """A record naming a family cannot say which weights answered.

    ``agy`` defaults to ``--model auto``, so this is the refusal that stops a
    whole arm being run against an unknown.
    """
    with pytest.raises(ArenaError, match="names a family, not a set of weights"):
        resolve_model(alias)


def test_an_unknown_model_names_the_row_to_add() -> None:
    with pytest.raises(ArenaError, match="not in the registry"):
        resolve_model("llama-4-scout")


def test_a_backend_that_does_not_serve_the_model_is_refused() -> None:
    with pytest.raises(ArenaError, match="is served by 'antigravity'"):
        assert_model_allowed("screen", "agy/gemini-3.7-flash-low", backend="claude_code")


def test_arena_prefixes_are_derived_from_the_registry() -> None:
    """Two copies of a model's arena would eventually disagree, invisibly."""
    for name, policy in ARENAS.items():
        assert policy.model_prefixes == tuple(
            sorted(entry.prefix for entry in MODELS if entry.arena == name)
        )


def test_a_local_model_is_refused_in_confirm() -> None:
    """Would produce a verdict about an entirely different model."""
    with pytest.raises(ArenaError, match="different experiment"):
        assert_model_allowed("confirm", "ollama/qwen3:8b")


def test_screening_models_are_refused_in_confirm() -> None:
    with pytest.raises(ArenaError):
        assert_model_allowed("confirm", "haiku")


def test_revising_a_skill_is_refused_in_the_locked_arena() -> None:
    with pytest.raises(ArenaError, match="hash-locked"):
        assert_may_revise_skill("confirm")


@pytest.mark.parametrize("arena", ["dev", "screen"])
def test_revision_is_permitted_where_iteration_happens(arena: str) -> None:
    assert_may_revise_skill(arena)


@pytest.mark.parametrize("arena", ["dev", "screen"])
def test_a_verdict_is_refused_outside_confirm(arena: str) -> None:
    with pytest.raises(ArenaError, match="not evidence"):
        assert_may_emit_verdict(arena)


def test_confirm_may_emit_a_verdict() -> None:
    assert_may_emit_verdict("confirm")


def test_the_holdout_cannot_be_spent_on_screening() -> None:
    """Contamination cannot be undone within a seed."""
    with pytest.raises(ArenaError, match="runs on the 'public' split"):
        assert_split_allowed("screen", "holdout")


def test_confirm_refuses_the_public_split() -> None:
    with pytest.raises(ArenaError, match="runs on the 'holdout' split"):
        assert_split_allowed("confirm", "public")


def test_matching_splits_pass() -> None:
    assert_split_allowed("dev", "public")
    assert_split_allowed("confirm", "holdout")


# ===========================================================================
# Pre-registration
# ===========================================================================


def _prereg_dict(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "skill": "evidence-ledger",
        "version": 1,
        "hypothesis": "The ledger raises accuracy on distractor-present items.",
        "primary_metric": "accuracy_distractor_present",
        "n_items": 280,
        "minimum_detectable_effect": 0.08,
        "alpha": 0.05,
        "guards": ["no_harm_clean", "beats_placebo", "beats_cot", "format_integrity"],
        "stopping_rule": "fixed N, no interim analysis",
        "difficulty_band": [0.35, 0.75],
        "budget_usd": 40.0,
        "skill_sha256": sha256_text(SKILL),
        "analysis_script_sha256": sha256_text(ANALYSIS),
    }
    base.update(overrides)
    return base


def _prereg(**overrides: Any) -> Preregistration:
    return Preregistration.model_validate(_prereg_dict(**overrides))


CLEAN_REPO = RepoState(committed_and_clean=True, is_ancestor_of_head=True, precedes_results=True)


def _run(prereg: Preregistration | None = None, **overrides: Any) -> None:
    kwargs: dict[str, Any] = {
        "repo": CLEAN_REPO,
        "skill_body": SKILL,
        "analysis_source": ANALYSIS,
        "baseline_accuracy": 0.55,
        "projected_cost_usd": 12.0,
    }
    kwargs.update(overrides)
    assert_runnable(prereg or _prereg(), **kwargs)


def test_a_well_formed_run_is_permitted() -> None:
    """Guards the rest: each test below asserts a *deviation* is refused."""
    _run()


def test_line_endings_do_not_break_the_hash() -> None:
    """Otherwise a Windows checkout fails a lock over a difference that is not one."""
    assert sha256_text("a\r\nb") == sha256_text("a\nb") == sha256_text("a\rb")


def test_an_uncommitted_preregistration_is_refused() -> None:
    repo = RepoState(committed_and_clean=False, is_ancestor_of_head=True, precedes_results=True)
    with pytest.raises(PreregistrationError, match="entirely in its timestamp"):
        _run(repo=repo)


def test_a_preregistration_off_the_current_history_is_refused() -> None:
    repo = RepoState(committed_and_clean=True, is_ancestor_of_head=False, precedes_results=True)
    with pytest.raises(PreregistrationError, match="not an ancestor of HEAD"):
        _run(repo=repo)


def test_a_preregistration_written_after_the_results_is_refused() -> None:
    repo = RepoState(committed_and_clean=True, is_ancestor_of_head=True, precedes_results=False)
    with pytest.raises(PreregistrationError, match="postdiction"):
        _run(repo=repo)


def test_one_changed_character_in_the_skill_aborts_the_run() -> None:
    """The lock the whole design turns on."""
    with pytest.raises(PreregistrationError, match="skill hash mismatch"):
        _run(skill_body=SKILL + " ")


def test_the_abort_message_names_the_next_version() -> None:
    with pytest.raises(PreregistrationError, match=r"evidence-ledger-v2\.yaml"):
        _run(skill_body="different")


def test_editing_the_analysis_script_aborts_the_run() -> None:
    """A pre-registered metric means nothing if its code can be rewritten."""
    with pytest.raises(PreregistrationError, match="analysis script hash mismatch"):
        _run(analysis_source=ANALYSIS + "# tweak\n")


@pytest.mark.parametrize("accuracy", [0.20, 0.34, 0.76, 0.99])
def test_a_baseline_outside_the_difficulty_band_is_refused(accuracy: float) -> None:
    with pytest.raises(PreregistrationError, match="difficulty band"):
        _run(baseline_accuracy=accuracy)


@pytest.mark.parametrize("accuracy", [0.35, 0.55, 0.75])
def test_the_difficulty_band_is_inclusive(accuracy: float) -> None:
    _run(baseline_accuracy=accuracy)


def test_a_run_over_budget_is_refused() -> None:
    with pytest.raises(PreregistrationError, match="optional-stopping"):
        _run(projected_cost_usd=40.01)


def test_a_run_exactly_on_budget_is_permitted() -> None:
    _run(projected_cost_usd=40.0)


# -- loading ----------------------------------------------------------------


def test_a_preregistration_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "evidence-ledger-v1.yaml"
    path.write_text(yaml.safe_dump(_prereg_dict()), encoding="utf-8")
    assert load_preregistration(path).skill == "evidence-ledger"


def test_a_missing_preregistration_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(PreregistrationError):
        load_preregistration(tmp_path / "absent.yaml")


def test_a_non_mapping_preregistration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "listy.yaml"
    path.write_text(yaml.safe_dump(["not", "a", "mapping"]), encoding="utf-8")
    with pytest.raises(PreregistrationError, match="expected a mapping"):
        load_preregistration(path)


def test_malformed_yaml_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("key: [unclosed\n", encoding="utf-8")
    with pytest.raises(PreregistrationError):
        load_preregistration(path)


def test_an_invalid_preregistration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(_prereg_dict(alpha=1.5)), encoding="utf-8")
    with pytest.raises(PreregistrationError):
        load_preregistration(path)


def test_a_malformed_hash_is_rejected() -> None:
    """A truncated or uppercase hash would never match and would fail confusingly later."""
    with pytest.raises(Exception, match="skill_sha256"):
        _prereg(skill_sha256="abc123")


def test_a_preregistration_needs_at_least_one_guard() -> None:
    with pytest.raises(Exception, match="guards"):
        _prereg(guards=[])


# ===========================================================================
# Budget
# ===========================================================================


def test_cost_projection_multiplies_every_factor() -> None:
    assert project_cost(n_items=280, n_arms=4, repeats=2, usd_per_item=0.01) == pytest.approx(22.4)


def test_repeats_default_to_two() -> None:
    """A one-repeat run is not the cheap version of this experiment.

    Harness variance makes single-run point estimates uninterpretable, so the
    default is the design, not a convenience.
    """
    assert project_cost(n_items=10, n_arms=2, usd_per_item=1.0) == 40.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_items": 0, "n_arms": 4, "repeats": 2},
        {"n_items": 10, "n_arms": 0, "repeats": 2},
        {"n_items": 10, "n_arms": 4, "repeats": 0},
    ],
)
def test_a_degenerate_projection_is_refused(kwargs: dict[str, int]) -> None:
    """A projection of zero would pass any budget check -- the one silent wrong answer."""
    with pytest.raises(BudgetError, match="at least one item"):
        project_cost(usd_per_item=0.01, **kwargs)


@pytest.mark.parametrize("rate", [0.0, -1.0])
def test_a_non_positive_rate_is_refused(rate: float) -> None:
    with pytest.raises(BudgetError, match="must be positive"):
        project_cost(n_items=10, n_arms=4, usd_per_item=rate)


def test_the_ledger_is_immutable() -> None:
    """A checkpointed run resumes from a serialisable value, not an accumulator."""
    start = BudgetLedger(limit_usd=10.0)
    after = start.record(3.0)
    assert start.spent_usd == 0.0
    assert after.spent_usd == 3.0
    assert after.remaining_usd == 7.0


def test_remaining_never_goes_negative() -> None:
    assert BudgetLedger(limit_usd=10.0, spent_usd=12.0).remaining_usd == 0.0


def test_exhaustion_is_reported_at_the_limit() -> None:
    assert not BudgetLedger(limit_usd=10.0, spent_usd=9.99).exhausted
    assert BudgetLedger(limit_usd=10.0, spent_usd=10.0).exhausted


def test_a_negative_cost_is_refused() -> None:
    with pytest.raises(BudgetError, match="cannot be negative"):
        BudgetLedger(limit_usd=10.0).record(-1.0)


def test_an_affordable_call_passes() -> None:
    BudgetLedger(limit_usd=10.0, spent_usd=9.0).assert_can_afford(1.0)


def test_a_call_that_would_overrun_is_refused_before_it_happens() -> None:
    """Checked before the call, so the limit is a limit rather than a report."""
    with pytest.raises(BudgetError, match="past the"):
        BudgetLedger(limit_usd=10.0, spent_usd=9.0).assert_can_afford(1.01)


# -- cost estimation --------------------------------------------------------


def test_a_long_prompt_is_authorised_at_more_than_a_short_one() -> None:
    assert estimate_cost_usd(prompt_chars=400_000) > 20 * estimate_cost_usd(prompt_chars=1_500)


def test_the_estimate_never_falls_below_the_floor() -> None:
    assert estimate_cost_usd(prompt_chars=0) == pytest.approx(0.005)


@pytest.mark.parametrize(
    ("achieved_tokens", "observed_usd"),
    [(1_533, 0.0052), (25_489, 0.0298), (63_313, 0.0714), (101_142, 0.2296)],
)
def test_the_estimate_covers_every_call_the_canary_actually_made(
    achieved_tokens: int, observed_usd: float
) -> None:
    """An authorisation that under-counts is a budget that is not a budget.

    Canary filler measured 6.01 chars/token; the estimator assumes 4.0. The
    mismatch is deliberate and one-directional -- it over-estimates.
    """
    assert estimate_cost_usd(prompt_chars=int(achieved_tokens * 6.0)) >= observed_usd


def test_a_negative_length_is_a_bug_not_a_free_call() -> None:
    with pytest.raises(BudgetError, match="cannot be negative"):
        estimate_cost_usd(prompt_chars=-1)
