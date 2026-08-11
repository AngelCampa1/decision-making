"""Shared pytest configuration.

Defines ``--bless``, the escape hatch for regenerating golden files.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--bless",
        action="store_true",
        default=False,
        help=(
            "Rewrite golden files instead of asserting against them. "
            "Requires committing the diff, which is the point: a benchmark that "
            "can change silently makes every number computed before the change "
            "incomparable with every number after it."
        ),
    )


@pytest.fixture(scope="session")
def bless(request: pytest.FixtureRequest) -> bool:
    value = request.config.getoption("--bless")
    assert isinstance(value, bool)
    return value


@pytest.fixture
def template_dict() -> Callable[..., dict[str, Any]]:
    """Build a minimal valid template, with overrides.

    Kept as a factory rather than a constant so a test that mutates one field
    cannot leak that mutation into the next test, and so each test's deviation
    from valid is visible at its call site.
    """

    def build(**overrides: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "template_id": "tst-001-example",
            "question": "Should the team act on {thing}?",
            "options": ["act", "hold"],
            "variables": {
                "thing": {"choice": ["alpha", "beta"]},
                "value": {"int": [1, 10]},
                "limit": {"int": [1, 10]},
                "colour": {"choice": ["red", "blue"]},
            },
            "relevant_facts": [
                {"id": "r1", "text": "The limit is {limit}."},
                {"id": "r2", "text": "The value is {value}."},
            ],
            "distractor_facts": [
                {"id": "d1", "text": "The {thing} is {colour}.", "strength": "high"},
                {"id": "d2", "text": "The office is open.", "strength": "low"},
            ],
            "solution": {
                "expr": "'act' if value > limit else 'hold'",
                "load_bearing": ["r1", "r2"],
            },
            "strata": {"distractors": [0, 2], "position": ["early", "late"]},
            "variants": 2,
        }
        base.update(overrides)
        return base

    return build
