"""Answer parsing and scoring.

Harbor's discipline, adopted wholesale: the verifier is tested against fixtures
of known-correct, known-wrong, paraphrased and boundary responses *before* it is
trusted, and every zero score is classified rather than assumed to be a model
failure. A verifier defect and a model failure look identical in the aggregate,
and only one of them is a finding.

Two parsing decisions are worth defending, because both cost us apparent
accuracy and both are deliberate.

**No fallback search.** When the ``ANSWER:`` line is missing, the response is a
parse failure even if an option is clearly named in the prose. Recovering it
would be easy and would corrupt the experiment: the format contract is in every
arm, so recovery rates would differ by arm in a way that has nothing to do with
decision quality, and the format-integrity guard would stop measuring anything.

**Ambiguity is a distinct outcome, not a coin flip.** A response naming two
options is not half correct. It is reported separately so it cannot be quietly
absorbed into either the numerator or the denominator.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

from decision_evals.generators.generate import Item

ParseStatus = Literal["parsed", "no_answer_line", "unlisted_option", "ambiguous"]

#: Why an item scored zero. The first three are assigned automatically; the last
#: two require a human reading the trace, and exist so that "we did not look" is
#: distinguishable from "we looked and it was the model".
ZeroCause = Literal[
    "agent_wrong",
    "format_violation",
    "infrastructure",
    "verifier_defect",
    "environment_leak",
]

#: Matches an answer line, tolerating the decorations models add: bold markers,
#: leading bullets, code ticks, trailing punctuation.
_ANSWER_LINE: Final = re.compile(
    r"^[\s>*\-]*(?:\*\*|__|`)?\s*ANSWER\s*(?:\*\*|__|`)?\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_DECORATION: Final = re.compile(r"^[\s*_`\"'\[]+|[\s*_`\"'\].,;:!]+$")


@dataclass(frozen=True)
class ParsedAnswer:
    """The result of reading a response's final answer."""

    status: ParseStatus
    value: str | None
    raw: str | None

    @property
    def ok(self) -> bool:
        return self.status == "parsed"


@dataclass(frozen=True)
class Score:
    """One scored item."""

    item_id: str
    template_id: str
    expected: str
    parsed: ParsedAnswer
    correct: bool
    zero_cause: ZeroCause | None

    @property
    def parse_failed(self) -> bool:
        """Feeds the format-integrity guard, which is about parsing, not accuracy."""
        return not self.parsed.ok


def _normalise(text: str) -> str:
    """Fold the differences that are presentation rather than content."""
    stripped = _DECORATION.sub("", text)
    return re.sub(r"[\s_\-]+", " ", stripped).strip().casefold()


def parse_answer(response: str, options: Sequence[str]) -> ParsedAnswer:
    """Extract the chosen option from a response.

    The *last* answer line wins. Models sometimes restate their answer after
    further reasoning, and the last statement is the one they are standing
    behind.
    """
    matches = _ANSWER_LINE.findall(response)
    if not matches:
        return ParsedAnswer(status="no_answer_line", value=None, raw=None)

    raw = matches[-1].strip()
    target = _normalise(raw)
    hits = [option for option in options if _normalise(option) == target]

    if len(hits) == 1:
        return ParsedAnswer(status="parsed", value=hits[0], raw=raw)
    if len(hits) > 1:
        # Only reachable from a template whose options normalise together, which
        # is a template defect. Surfaced rather than silently resolved.
        return ParsedAnswer(status="ambiguous", value=None, raw=raw)
    return ParsedAnswer(status="unlisted_option", value=None, raw=raw)


def score_item(item: Item, response: str, *, infrastructure_error: bool = False) -> Score:
    """Score one response against its item.

    Args:
        infrastructure_error: Set by the runner when the call itself failed --
            a timeout, a revoked credential, a transport error. Passed in rather
            than inferred, because a model that returns nothing and a call that
            never happened are indistinguishable from the response text alone,
            and conflating them would let a rate-limited run masquerade as a
            model that stopped answering.
    """
    parsed = parse_answer(response, item.options)
    correct = parsed.ok and parsed.value == item.answer
    return Score(
        item_id=item.item_id,
        template_id=item.template_id,
        expected=item.answer,
        parsed=parsed,
        correct=correct,
        zero_cause=_zero_cause(correct, parsed, infrastructure_error),
    )


def _zero_cause(
    correct: bool, parsed: ParsedAnswer, infrastructure_error: bool
) -> ZeroCause | None:
    if infrastructure_error:
        return "infrastructure"
    if correct:
        return None
    if not parsed.ok:
        return "format_violation"
    return "agent_wrong"


@dataclass(frozen=True)
class ScoreSummary:
    """Aggregates over a set of scores.

    Accuracy counts parse failures as incorrect, which is the honest
    denominator: a response that did not answer did not get it right. The
    parse-failure rate is reported alongside so the two can be told apart, and
    that separation is what the format-integrity guard needs -- a skill that
    improves accuracy while breaking the output contract has not improved
    anything usable.
    """

    total: int
    correct: int
    parse_failures: int

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def parse_failure_rate(self) -> float:
        return self.parse_failures / self.total if self.total else 0.0


def summarise(scores: Sequence[Score]) -> ScoreSummary:
    return ScoreSummary(
        total=len(scores),
        correct=sum(1 for score in scores if score.correct),
        parse_failures=sum(1 for score in scores if score.parse_failed),
    )
