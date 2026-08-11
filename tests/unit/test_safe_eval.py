"""Tests for the restricted expression evaluator.

The rejection tests matter more than the acceptance tests. A whitelist that
accepts what it should is convenient; a whitelist that rejects what it must is
the security property, and every entry below is a construct that would give a
template author arbitrary code execution in anyone who regenerates the dataset.
"""

from __future__ import annotations

import pytest

from decision_evals.generators.safe_eval import (
    ExpressionError,
    UnsafeExpressionError,
    evaluate,
    referenced_names,
    validate,
)


@pytest.mark.parametrize(
    ("expression", "variables", "expected"),
    [
        ("'act' if value > limit else 'hold'", {"value": 5, "limit": 3}, "act"),
        ("'act' if value > limit else 'hold'", {"value": 1, "limit": 3}, "hold"),
        ("'a' if x * (100 + y) > z * 100 else 'b'", {"x": 10, "y": 20, "z": 11}, "a"),
        ("'a' if min(p, q) >= 2 else 'b'", {"p": 5, "q": 2}, "a"),
        ("'a' if not flag else 'b'", {"flag": False}, "a"),
        ("'a' if x in (1, 2, 3) else 'b'", {"x": 2}, "a"),
        ("'a' if x >= 1 and y <= 9 else 'b'", {"x": 4, "y": 4}, "a"),
        ("str(round(abs(-x) / 2))", {"x": 7}, "4"),
    ],
)
def test_whitelisted_expressions_evaluate(
    expression: str, variables: dict[str, object], expected: object
) -> None:
    assert evaluate(expression, variables) == expected


@pytest.mark.parametrize(
    ("expression", "why"),
    [
        ("__import__('os').system('echo pwned')", "import"),
        ("().__class__.__bases__", "attribute access, the classic sandbox escape"),
        ("[x for x in range(3)]", "comprehension"),
        ("(lambda: 1)()", "lambda"),
        ("data[0]", "subscript"),
        ("open('secrets')", "a callable outside the whitelist"),
        ("min(*args)", "starred argument"),
        ("round(x, ndigits=2)", "keyword argument"),
        ("f(1)()", "calling the result of a call"),
        ("x := 3", "walrus"),
        ("{'a': 1}", "dict literal"),
        ("x if y", "syntax error"),
    ],
)
def test_unsafe_or_malformed_expressions_are_rejected(expression: str, why: str) -> None:
    with pytest.raises(UnsafeExpressionError):
        validate(expression)


def test_a_disallowed_function_names_what_is_allowed() -> None:
    """The error has to be actionable -- template authors read it, not the source."""
    with pytest.raises(UnsafeExpressionError, match="Allowed:"):
        validate("exec('x')")


def test_builtins_are_not_reachable_from_the_namespace() -> None:
    with pytest.raises(ExpressionError, match="references a name"):
        evaluate("eval", {})


def test_an_unbound_name_is_an_expression_error_not_a_crash() -> None:
    with pytest.raises(ExpressionError, match="does not define"):
        evaluate("'a' if missing > 1 else 'b'", {"present": 1})


def test_referenced_names_reports_variables_only() -> None:
    names = referenced_names("'a' if min(width, height) > margin else 'b'")
    assert names == frozenset({"width", "height", "margin"})


def test_referenced_names_is_empty_for_a_constant_expression() -> None:
    assert referenced_names("'always'") == frozenset()
