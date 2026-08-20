"""Tests for rate-limit backpressure in the runner.

Nothing sleeps here. `Backpressure` takes its clock and its jitter as
arguments, so what is exercised is the schedule rather than the wall time it
would cost.

The property that needs a test rather than an argument is the *shared* pause.
Per-call retry is the obvious fix and it is not enough once the pool has several
calls in flight: concurrency does not create quota, every worker meets the same
wall in the same instant, and independent backoff sends the same burst back at
the same instant too.
"""

from __future__ import annotations

import threading

import pytest

from decision_evals.providers.claude_code import (
    AuthenticationError,
    CliError,
    PromptTooLongError,
    RateLimitedError,
    parse_result,
)
from decision_evals.runner import Backoff, Backpressure, RunError


def _payload(**extra: object) -> dict[str, object]:
    return {"is_error": True, "result": "something went wrong", **extra}


class TestClassification:
    def test_429_and_529_are_rate_limits(self) -> None:
        """The load-bearing signal, and an HTTP semantic rather than a guess."""
        for status in (429, 529):
            with pytest.raises(RateLimitedError):
                parse_result(_payload(api_error_status=status))

    @pytest.mark.parametrize(
        "message",
        ["Rate limit exceeded", "Claude usage limit reached", "Overloaded"],
    )
    def test_the_message_markers_are_the_fallback(self, message: str) -> None:
        """Unobserved strings, kept so a missing status is not scored as failure.

        No record in this repository carries any of them. They are labelled as
        a guess where they are defined, and they are a superset on purpose: the
        cost of a false positive is one wait, and the cost of a false negative
        is an item burned and a model failure on the record that never happened.
        """
        with pytest.raises(RateLimitedError):
            parse_result({"is_error": True, "result": message})

    def test_an_ordinary_error_is_still_an_ordinary_error(self) -> None:
        with pytest.raises(CliError) as caught:
            parse_result(_payload())
        assert not isinstance(caught.value, RateLimitedError)

    def test_authentication_still_wins(self) -> None:
        """It aborts the run; a rate limit waits. The order matters."""
        with pytest.raises(AuthenticationError):
            parse_result(
                {"is_error": True, "result": "please authenticate", "api_error_status": 429}
            )

    def test_a_prompt_that_does_not_fit_is_not_a_rate_limit(self) -> None:
        """Deterministic and reproducible: waiting would never help."""
        with pytest.raises(PromptTooLongError):
            parse_result(
                {"is_error": True, "result": "Prompt is too long", "api_error_status": 429}
            )

    def test_retry_after_is_read_and_never_invented(self) -> None:
        with pytest.raises(RateLimitedError) as caught:
            parse_result(_payload(api_error_status=429, retry_after=17))
        assert caught.value.retry_after == 17.0

        with pytest.raises(RateLimitedError) as caught:
            parse_result(_payload(api_error_status=429))
        assert caught.value.retry_after is None

    @pytest.mark.parametrize("value", [True, "30", 0, -1])
    def test_a_retry_after_that_is_not_a_positive_number_is_absent(self, value: object) -> None:
        """`True` is an `int` in Python, and a one-second wait is not what it meant."""
        with pytest.raises(RateLimitedError) as caught:
            parse_result(_payload(api_error_status=429, retryAfter=value))
        assert caught.value.retry_after is None


class TestTheSchedule:
    def test_the_delay_doubles_and_is_capped(self) -> None:
        drawn: list[float] = []

        def uniform(low: float, high: float) -> float:
            drawn.append(high)
            return high

        pressure = Backpressure(
            Backoff(base_delay=2.0, max_delay=10.0),
            sleep=lambda _: None,
            uniform=uniform,
        )
        for attempt in range(5):
            pressure.trip(attempt)
        assert drawn == [2.0, 4.0, 8.0, 10.0, 10.0]

    def test_the_jitter_is_full_rather_than_none(self) -> None:
        """Every worker meets the wall at once, so a fixed delay re-synchronises them."""
        seen: list[tuple[float, float]] = []

        def uniform(low: float, high: float) -> float:
            seen.append((low, high))
            return low

        Backpressure(Backoff(base_delay=4.0), sleep=lambda _: None, uniform=uniform).trip(0)
        assert seen == [(0.0, 4.0)]

    def test_what_the_server_asked_for_beats_what_we_computed(self) -> None:
        slept: list[float] = []
        pressure = Backpressure(
            Backoff(base_delay=1.0, max_delay=2.0),
            sleep=slept.append,
            uniform=lambda low, high: high,
        )
        assert pressure.trip(0, retry_after=45.0) == 45.0
        assert slept == [45.0]


class TestTheBreaker:
    def test_it_aborts_after_enough_consecutive_refusals(self) -> None:
        """A wall that does not move is a window that closed, not one that narrowed.

        The run is checkpointed, so stopping costs nothing and resuming re-runs
        nothing. Waiting again costs the rest of the run.
        """
        pressure = Backpressure(
            Backoff(breaker_trips=3), sleep=lambda _: None, uniform=lambda low, high: 0.0
        )
        for attempt in range(3):
            pressure.trip(attempt)
        with pytest.raises(RunError, match="consecutive rate-limited"):
            pressure.trip(3)

    def test_a_call_getting_through_resets_it(self) -> None:
        pressure = Backpressure(
            Backoff(breaker_trips=2), sleep=lambda _: None, uniform=lambda low, high: 0.0
        )
        pressure.trip(0)
        pressure.trip(1)
        pressure.succeeded()
        pressure.trip(0)
        pressure.trip(1)
        assert pressure.trips == 4


class TestThePauseIsShared:
    def test_a_worker_serving_a_pause_holds_every_other_worker(self) -> None:
        """The property per-call retry does not have.

        One thread trips and is inside its sleep. A second thread calling
        `wait()` must not proceed until the first is done, or the pool goes
        straight back at a wall it already knows about.
        """
        inside = threading.Event()
        release = threading.Event()
        passed = threading.Event()

        def sleep(_: float) -> None:
            inside.set()
            assert release.wait(timeout=5.0)

        pressure = Backpressure(sleep=sleep, uniform=lambda low, high: 0.0)

        tripper = threading.Thread(target=lambda: pressure.trip(0))
        tripper.start()
        assert inside.wait(timeout=5.0)

        waiter = threading.Thread(target=lambda: (pressure.wait(), passed.set()))
        waiter.start()
        assert not passed.wait(timeout=0.2), "the second worker went through an open pause"

        release.set()
        tripper.join(timeout=5.0)
        assert passed.wait(timeout=5.0)
        waiter.join(timeout=5.0)

    def test_the_pause_reopens_even_when_the_breaker_fires_mid_sleep(self) -> None:
        """A raise inside the sleep must not leave every worker parked forever."""

        def sleep(_: float) -> None:
            raise KeyboardInterrupt

        pressure = Backpressure(sleep=sleep, uniform=lambda low, high: 0.0)
        with pytest.raises(KeyboardInterrupt):
            pressure.trip(0)
        pressure.wait()

    def test_nothing_is_waited_before_the_first_call(self) -> None:
        pressure = Backpressure(sleep=lambda _: None, uniform=lambda low, high: 0.0)
        pressure.wait()
        assert pressure.trips == 0
        assert pressure.slept == 0.0


class TestAScheduleThatCannotBeRun:
    """`Backoff` is a plain record, so a nonsense field reaches the run loop.

    Each of these turns into silence rather than an error: zero attempts is an
    arm making no calls at all, a negative delay is a negative sleep, and a
    breaker at zero trips before the first rate limit and stops every run at the
    first wall.
    """

    def test_a_call_is_made_at_least_once(self) -> None:
        with pytest.raises(ValueError, match="attempts is 0"):
            Backoff(attempts=0)

    @pytest.mark.parametrize("field", ["base_delay", "max_delay"])
    def test_a_delay_cannot_be_negative(self, field: str) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            Backoff(**{field: -1.0})

    def test_a_breaker_below_one_trips_before_anything_happens(self) -> None:
        with pytest.raises(ValueError, match="breaker_trips is 0"):
            Backoff(breaker_trips=0)

    def test_the_defaults_are_a_runnable_schedule(self) -> None:
        assert Backoff().attempts >= 1
