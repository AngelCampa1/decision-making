"""Run cost projection and the spend ledger.

Cost is a guard, not a metric. It exists so a run is stopped by arithmetic
rather than by noticing, and so a projection that was wrong is visible as a
refusal instead of as a quota exhausted three days into a confirmation run.

The unit is dollars because ``--output-format json`` reports
``total_cost_usd`` per call, even on a subscription where no dollars change
hands. It is a usable proxy for quota consumption and it is the only number the
CLI gives us; ``docs/LIMITATIONS.md`` says plainly that rate limits rather than
dollars are the real budget.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


class BudgetError(RuntimeError):
    """The run would exceed its budget."""


def project_cost(*, n_items: int, n_arms: int, repeats: int = 2, usd_per_item: float) -> float:
    """Project the cost of a run.

    Every factor is multiplied in explicitly, because each is a place a
    projection quietly goes wrong by an integer factor. ``repeats`` defaults to
    2 rather than 1: the harness-variance literature makes single-run point
    estimates uninterpretable, so a one-repeat run is not the cheap version of
    this experiment, it is a different and weaker one.

    Raises:
        BudgetError: A non-positive factor. A projection of zero would pass any
            budget check, which is the one wrong answer that fails silently.
    """
    if n_items < 1 or n_arms < 1 or repeats < 1:
        raise BudgetError(
            f"a run needs at least one item, arm and repeat; got items={n_items}, "
            f"arms={n_arms}, repeats={repeats}"
        )
    if usd_per_item <= 0:
        raise BudgetError(f"usd_per_item must be positive, got {usd_per_item}")
    return n_items * n_arms * repeats * usd_per_item


#: Notional dollars per prompt token, taken from the most expensive call the
#: long canary made ($0.2296 for 101,142 tokens = $2.27e-6) and rounded up. It
#: is an upper bound on purpose: this figure authorises a call *before* it is
#: made, and an authorisation that under-counts is not a budget.
_USD_PER_TOKEN: Final = 2.5e-6

#: Conservative chars-per-token. Canary filler measured 6.01; real casefile
#: prose tokenises worse and lands nearer 4. Assuming 4 over-estimates the token
#: count for anything more repetitive than prose, which is the direction an
#: authorisation should err in.
_CHARS_PER_TOKEN: Final = 4.0

#: Below this, per-call overhead dominates and the linear model under-reads.
_FLOOR_USD: Final = 0.005


def estimate_cost_usd(*, prompt_chars: int) -> float:
    """Project one call's notional cost from the length of its prompt.

    The ledger authorises before the call, so this must never read low. Every
    constant here is set to over-estimate, and the test suite pins that against
    the four real calls the long canary made.

    The figure it returns is notional -- an API-equivalent price on a
    subscription where nothing is billed per call -- so it is a burn meter for
    quota consumption rather than a spend cap. It has to scale with length all
    the same: the flat $0.05 it replaces under-counted a 100k-token prompt
    roughly fivefold, and the ledger would have authorised a run it could not
    finish.

    Raises:
        BudgetError: A negative length. Silently clamping would authorise a call
            at the floor when the caller's length arithmetic is broken.
    """
    if prompt_chars < 0:
        raise BudgetError(f"prompt_chars cannot be negative, got {prompt_chars}")
    tokens = prompt_chars / _CHARS_PER_TOKEN
    return max(tokens * _USD_PER_TOKEN, _FLOOR_USD)


@dataclass(frozen=True)
class BudgetLedger:
    """What a run is allowed to spend, and what it has spent.

    Frozen: :meth:`record` returns a new ledger rather than mutating this one,
    so a checkpointed run resumes from a value it can serialise instead of from
    whatever an object happened to accumulate.
    """

    limit_usd: float
    spent_usd: float = 0.0

    @property
    def remaining_usd(self) -> float:
        return max(self.limit_usd - self.spent_usd, 0.0)

    @property
    def exhausted(self) -> bool:
        return self.spent_usd >= self.limit_usd

    def record(self, cost_usd: float) -> BudgetLedger:
        """Return a ledger with ``cost_usd`` added.

        Raises:
            BudgetError: A negative cost. Refunds are not a thing that happens
                here, so a negative is a bug in the caller and would silently
                extend the budget.
        """
        if cost_usd < 0:
            raise BudgetError(f"cost cannot be negative, got {cost_usd}")
        return BudgetLedger(limit_usd=self.limit_usd, spent_usd=self.spent_usd + cost_usd)

    def assert_can_afford(self, cost_usd: float) -> None:
        """Refuse a call that would take the run past its limit.

        Checked *before* the call rather than after, so the limit is a limit
        rather than a report.
        """
        if self.spent_usd + cost_usd > self.limit_usd:
            raise BudgetError(
                f"this call would bring spend to ${self.spent_usd + cost_usd:.2f}, past the "
                f"${self.limit_usd:.2f} limit. The run is checkpointed: raise the limit "
                "deliberately and resume, rather than letting it drift."
            )
