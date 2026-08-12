"""Does context actually carry across turns? Only a real model can say.

Marked ``llm``, so it never runs in ``de check``. Everything a fake can
establish about :class:`Conversation` is in ``tests/unit/test_conversation.py``;
what a fake cannot establish is the one claim Track 0 rests on — that turns sent
to one live subprocess accumulate, **under the full isolation stack with no flag
relaxed**.

Run it with::

    python -m uv run pytest tests/integration/test_multiturn.py -m llm

Three short Haiku turns. The corrected falsifier is asserted here rather than
described: ``input_tokens`` climbing monotonically **and** a behavioural recall
check. Two independent signals, because a longer question explains the first and
a lucky guess explains the second.

``cache_read`` is deliberately *not* asserted on. Track 0's original falsifier
required it to climb turn over turn; measured, it stays at 0 on every turn while
context demonstrably carries, and run as written it would have declared a
healthy venue dead. The assertion below pins that observation so the wrong gate
cannot quietly return.
"""

from __future__ import annotations

import tempfile

import pytest

from decision_evals.providers.claude_code import Conversation

pytestmark = pytest.mark.llm

CODEWORD = "MARMALADE-7"
TURNS = (
    f"Remember this codeword: {CODEWORD}. Just acknowledge it.",
    "What is 2+2? Answer with the number only.",
    "What was the codeword I gave you? Answer with the codeword only.",
)


@pytest.fixture(scope="module")
def transcript() -> list[tuple[str, int, int]]:
    """Three turns against one live process. Returns (text, input, cache_read)."""
    with (
        tempfile.TemporaryDirectory() as cwd,
        Conversation(
            system_prompt="Answer in as few words as possible.", model="haiku", cwd=cwd
        ) as chat,
    ):
        rows = []
        for turn in TURNS:
            result = chat.send(turn)
            rows.append((result.text, result.input_tokens, result.cache_read_tokens))
        chat.receipt.assert_isolated()
        return rows


def test_input_tokens_climb_monotonically(transcript: list[tuple[str, int, int]]) -> None:
    """Half of the corrected falsifier: the transcript is growing."""
    tokens = [row[1] for row in transcript]
    assert tokens == sorted(tokens)
    assert tokens[-1] > tokens[0]


def test_the_last_turn_recalls_the_first(transcript: list[tuple[str, int, int]]) -> None:
    """The other half: it is a transcript, not just a longer prompt.

    An unrelated turn sits between the two, so a model answering only from the
    latest message cannot pass this.
    """
    assert CODEWORD in transcript[-1][0].upper()


def test_cache_read_is_not_evidence_of_accumulation(
    transcript: list[tuple[str, int, int]],
) -> None:
    """Pins the measurement that retired Track 0's original falsifier.

    Caching is a billing optimisation, not a transcript mechanism, and short
    turns never reach the threshold. If this ever starts failing, the finding
    changed -- which is worth knowing, but it must not be read as the falsifier
    having been right.
    """
    assert all(row[2] == 0 for row in transcript)


def test_the_isolation_receipt_passes_on_a_healthy_run() -> None:
    """Rule 2: a gate is run against a known-good case before it may fail anything.

    ``assert_isolated`` is called inside the fixture, so this asserting nothing
    further is the point -- the fixture would have raised.
    """
    with (
        tempfile.TemporaryDirectory() as cwd,
        Conversation(system_prompt="Reply with one word.", model="haiku", cwd=cwd) as chat,
    ):
        chat.send("Say: ready")
        receipt = chat.receipt
        receipt.assert_isolated()
        assert receipt.tools_disabled
        # Declared but unreachable under `--tools ""`. Recorded rather than
        # gated on, because relaxing --tools is what makes them live.
        assert receipt.agents
