"""Evaluation harness for measuring whether agent decision skills actually work.

The package is deliberately layered so that the parts producing published numbers
carry no dependency on a model backend:

``decision_evals.stats``
    Every number that reaches the scorecard or the paper passes through here.
    Pure functions over arrays, no I/O, 100% line and branch coverage required.

``decision_evals.generators``
    Seeded instantiation of parameterised scenario templates with *computed*
    ground truth.

``decision_evals.scorers``
    Programmatic verification of a structured answer against that ground truth.

``decision_evals.providers``
    The only layer that talks to a model. Everything above it is testable offline.
"""

__version__ = "0.1.0"
