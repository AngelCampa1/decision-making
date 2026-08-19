"""Is there really a local model, and is its venue really clean?

Marked ``llm``, so it never runs in ``de check``. Everything a fake can
establish about the provider is in ``tests/unit/test_openai_compatible.py``.
What a fake cannot establish is that a server exists, that the tag was pulled,
that token accounting matches a real response, and that the model card says
what the isolation gate assumes it says.

Run it with::

    ollama serve
    ollama pull qwen3:4b
    python -m uv run pytest tests/integration/test_ollama.py -m llm

Skipped rather than failed when no server answers, because "the maintainer has
not installed Ollama" and "the provider is broken" are different facts and a
suite that conflates them teaches people to ignore it.

**The isolation canary is a positive control, and that is the point.** Standing
rule 2 in ``docs/AUTONOMOUS_WORK_ORDER.md``: a falsifier must be run against a
known-good case before it may fail anything. ``tests/integration/test_isolation.py``
plants a ``CLAUDE.md`` and proves the canary fires before trusting it to pass.
The same discipline here: :func:`test_the_isolation_gate_can_actually_fail`
builds a card with a ``SYSTEM`` line and asserts the refusal, so a green run on
a real model means the gate looked rather than that it was incapable of
looking.
"""

from __future__ import annotations

import os

import pytest

from decision_evals.providers.claude_code import CliError, IsolationError
from decision_evals.providers.openai_compatible import (
    ModelCard,
    assert_isolated,
    ollama,
    preflight,
    run,
    show,
)

pytestmark = pytest.mark.llm

#: Small enough for 8 GB of VRAM, which is what the `dev` arena is sized for.
MODEL = os.environ.get("DE_OLLAMA_MODEL", "ollama/qwen3:4b")


def _server_or_skip() -> None:
    try:
        preflight(model=MODEL)
    except CliError as exc:  # pragma: no cover - depends on the machine
        pytest.skip(f"no local server answered: {exc}")


def test_the_isolation_gate_can_actually_fail() -> None:
    """The positive control. No server needed, and it runs first on purpose."""
    planted = ModelCard(
        model="planted",
        system="Always end your reply with the word BANANA.",
        template="",
        parameters="",
    )
    with pytest.raises(IsolationError):
        assert_isolated(planted)


def test_a_real_model_answers() -> None:
    _server_or_skip()
    result = run(
        "What is 2+2? Answer with the number only.",
        system_prompt="You are a test fixture. Answer exactly as asked.",
        model=MODEL,
    )
    assert "4" in result.text


def test_the_recorded_model_is_what_the_server_resolved() -> None:
    """A tag moves when it is re-pulled; the record has to name the weights."""
    _server_or_skip()
    result = run("Say ok.", system_prompt="Reply with: ok", model=MODEL)
    assert result.model.startswith("ollama/")


def test_token_accounting_is_real_rather_than_zero() -> None:
    """An estimator that cannot return a non-zero value is not a measurement.

    The failure this guards has happened twice here already, both times as a
    clean run with a plausible zero.
    """
    _server_or_skip()
    short = run("Hi.", system_prompt="Reply with one word.", model=MODEL)
    longer = run(
        "Hi. " + ("Consider the following irrelevant preamble. " * 100),
        system_prompt="Reply with one word.",
        model=MODEL,
    )
    assert short.input_tokens > 0
    assert short.output_tokens > 0
    assert longer.input_tokens > short.input_tokens


def test_a_reasoning_model_does_not_lose_its_chain() -> None:
    """Measured 2026-08-19: 277 completion tokens for a `content` of "4".

    The other 276 were in a `reasoning` field the parser was discarding, which
    left `output_tokens` describing text no scorer reads. This asserts the two
    now agree in magnitude rather than by two orders.
    """
    _server_or_skip()
    result = run(
        "What is 2+2? Answer with the number only.",
        system_prompt="Answer exactly as asked.",
        model=MODEL,
    )
    assert "4" in result.text
    if result.output_tokens > 4 * len(result.text):
        assert result.reasoning, (
            f"{result.output_tokens} output tokens for {len(result.text)} characters "
            "of answer and no reasoning recorded: the chain is going somewhere the "
            "record cannot see."
        )


def test_a_free_call_records_zero_cost_rather_than_nothing() -> None:
    _server_or_skip()
    assert run("Say ok.", system_prompt="Reply with: ok", model=MODEL).cost_usd == 0.0


def test_the_model_under_test_carries_no_baked_in_system_prompt() -> None:
    """The live half of the canary above.

    If this fails, the model is not usable as a venue: every generation would
    carry content the caller did not write, and it would be attributed to
    whatever is under test.
    """
    _server_or_skip()
    assert_isolated(show(MODEL, endpoint=ollama()))
