"""Dataset generation.

Parameterised templates with computed ground truth, in the style of
GSM-Symbolic. See ``docs/PROTOCOL.md`` section 6 for the three gates a template
family must clear before it is eligible for pre-registration.
"""

from decision_evals.generators.generate import (
    GenerationError,
    Item,
    RenderedFact,
    derive_seed,
    generate,
    strata_combinations,
)
from decision_evals.generators.loader import (
    TEMPLATE_ROOT,
    TemplateLoadError,
    load_all,
    load_template,
)
from decision_evals.generators.safe_eval import (
    ExpressionError,
    UnsafeExpressionError,
    evaluate,
    referenced_names,
    validate,
)
from decision_evals.generators.schema import Distractor, Fact, Solution, Strata, Template

__all__ = [
    "TEMPLATE_ROOT",
    "Distractor",
    "ExpressionError",
    "Fact",
    "GenerationError",
    "Item",
    "RenderedFact",
    "Solution",
    "Strata",
    "Template",
    "TemplateLoadError",
    "UnsafeExpressionError",
    "derive_seed",
    "evaluate",
    "generate",
    "load_all",
    "load_template",
    "referenced_names",
    "strata_combinations",
    "validate",
]
