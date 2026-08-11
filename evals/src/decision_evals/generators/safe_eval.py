"""A restricted expression evaluator for template ground truth.

Templates compute their own answers, which is what makes ~50 rules auditable
where 300 authored answers would not be. That requires evaluating an expression
from a YAML file, and the obvious implementation — :func:`eval` — would make
every template a code-execution vector.

That is not a hypothetical concern for this ecosystem: a 2026 audit found 26.1%
of a sampled skills corpus carried at least one vulnerability, with supply-chain
injection among the categories. A dataset people are invited to regenerate from
our templates should not be the same kind of artifact.

So expressions are parsed to an AST and every node is checked against a
whitelist before anything runs. The whitelist is small on purpose: arithmetic,
comparison, boolean logic, a conditional, and a handful of pure builtins. There
are no attribute lookups, no subscripts, no comprehensions, no lambdas, and no
imports — an expression that needs any of those is a template that should be
simplified, not a whitelist that should be widened.
"""

from __future__ import annotations

import ast
from typing import Any, Final

#: Node types an expression may contain. Anything else is rejected.
#:
#: Notable omissions, all deliberate: ``ast.Attribute`` (``().__class__`` is the
#: classic sandbox escape), ``ast.Subscript``, ``ast.Lambda``, comprehensions,
#: ``ast.Starred``, and every statement type.
_ALLOWED_NODES: Final[tuple[type[ast.AST], ...]] = (
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.USub,
    ast.UAdd,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.IfExp,
    ast.Call,
    ast.List,
    ast.Tuple,
)

#: Callables an expression may invoke. All pure, all total on the inputs a
#: template can produce.
_ALLOWED_CALLS: Final[dict[str, Any]] = {
    "abs": abs,
    "float": float,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "round": round,
    "sorted": sorted,
    "str": str,
    "sum": sum,
}


class UnsafeExpressionError(ValueError):
    """The expression used a construct outside the whitelist."""


class ExpressionError(ValueError):
    """The expression was well-formed and safe, but did not evaluate."""


def validate(expression: str) -> ast.Expression:
    """Parse an expression and reject anything outside the whitelist.

    Separate from :func:`evaluate` so templates can be linted without being
    instantiated — a malformed rule should fail in ``de lint``, not halfway
    through generating a dataset.

    Raises:
        UnsafeExpressionError: A disallowed node type, or a call to something other
            than an allowed builtin.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"cannot parse {expression!r}: {exc}") from exc

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise UnsafeExpressionError(
                f"{type(node).__name__} is not allowed in a template expression: {expression!r}"
            )
        if isinstance(node, ast.Call):
            # Only bare names may be called. A call whose target is anything
            # else -- an attribute, another call's result -- is rejected before
            # the name check, so there is no path to an arbitrary callable.
            if not isinstance(node.func, ast.Name):
                raise UnsafeExpressionError(f"only named functions may be called: {expression!r}")
            if node.func.id not in _ALLOWED_CALLS:
                raise UnsafeExpressionError(
                    f"{node.func.id}() is not an allowed function. "
                    f"Allowed: {sorted(_ALLOWED_CALLS)}"
                )
            if node.keywords:
                raise UnsafeExpressionError(f"keyword arguments are not allowed: {expression!r}")
    return tree


def evaluate(expression: str, variables: dict[str, Any]) -> Any:
    """Evaluate a whitelisted expression against a template's variables.

    Args:
        expression: The template's ``solution.expr``.
        variables: The sampled variable bindings.

    Raises:
        UnsafeExpressionError: The expression failed :func:`validate`.
        ExpressionError: The expression referenced an unbound name, or raised.
    """
    tree = validate(expression)
    namespace: dict[str, Any] = {"__builtins__": {}, **_ALLOWED_CALLS, **variables}
    try:
        # Safe by construction: `tree` has already passed the node whitelist,
        # `__builtins__` is emptied, and the namespace holds only pure callables
        # plus the template's own sampled variables.
        return eval(compile(tree, "<template>", "eval"), namespace)
    except NameError as exc:
        raise ExpressionError(
            f"{expression!r} references a name the template does not define: {exc}"
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise ExpressionError(f"{expression!r} failed to evaluate: {exc}") from exc


def referenced_names(expression: str) -> frozenset[str]:
    """Return the variable names an expression reads.

    Used by the distractor audit to prove invariance structurally: a fact whose
    variables appear nowhere in the solution expression cannot affect the
    answer, whatever the sampled values happen to be.
    """
    tree = validate(expression)
    return frozenset(
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id not in _ALLOWED_CALLS
    )
