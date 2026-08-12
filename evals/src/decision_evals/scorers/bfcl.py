"""BFCL's own AST match for the ``actions`` family, implemented from its key.

**Why this exists.** The A1 pilot could only report whether a response *named*
the required function, because nothing in the run asked for a parseable call and
inventing a parse would have measured compliance with a contract nobody stated.
Naming is a floor: a response that names ``create_histogram`` and gets both bin
counts wrong scores as a hit. The pilot's only non-zero discordance was on that
floor, so the family is worth grading properly.

**Standing rule 3 and why this is on the right side of it.** The rule is that a
model may run experiments and record raw outputs but may not decide a response is
wrong — 21 of 21 scored failures across three corpora were the answer key. It is
weaker for a *vendored* key than an authored one, which is how GSM8K's ``####``
line is used. This is the same situation: every acceptable value here is read off
``reference_answer`` as shipped, and nothing in this module encodes a judgement
about what a good answer looks like.

What *is* a judgement is the matching semantics, so they are stated rather than
assumed, and they come from the shape of the vendored data rather than from
taste. Measured across all 105 ``actions`` records:

* every record is ``test_category: "parallel"``;
* ``reference_answer`` is a list of 2, 3, 4 or 8 calls;
* every call is a single-key dict, keyed by function name;
* **every parameter value is a list**, and the list is the set of acceptable
  alternatives — all 776 of them.

So the rules are:

1. **Order does not matter.** ``parallel`` means the calls may be issued in any
   order, so matching is a bijection between response calls and reference calls.
2. **A parameter matches when the supplied value is in its acceptable list.**
3. **An empty string in the acceptable list means the parameter may be omitted.**
   ``{"face_value": [1000, ""]}`` is BFCL saying *1000, or leave it out*.
4. **An extra parameter the reference does not mention is a mismatch**, because
   the reference lists every parameter the call is allowed to carry.

Every failure is returned with the reason attached. A scorer that returns a bare
``False`` is one nobody can audit, and auditing scorers is the activity that
found all 21 key errors.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Final

#: In an acceptable-value list, this means "or omit this parameter entirely".
OPTIONAL: Final = ""

#: A fenced or bare JSON array anywhere in the response.
_ARRAY: Final = re.compile(r"\[\s*\{.*}\s*]", re.DOTALL)


class BfclParseError(ValueError):
    """The response did not contain a readable call list."""


@dataclass(frozen=True)
class Call:
    """One function call: a name and the arguments actually supplied."""

    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class MatchResult:
    """Whether a response's calls satisfy the reference, and why not.

    Attributes:
        matched: Every reference call was satisfied by a distinct response call.
        reasons: One line per unmatched reference call. Empty when ``matched``.
            Populated even on success paths that had to backtrack, so a reader
            can see what was tried.
    """

    matched: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)


def parse_reference(reference: object) -> list[Call]:
    """Read the vendored ``reference_answer`` into calls with acceptable values.

    Raises:
        BfclParseError: The reference is not the shape measured across all 105
            records. Guessing at a different shape is how a key silently starts
            grading something else.
    """
    if not isinstance(reference, list) or not reference:
        raise BfclParseError(f"reference_answer is {type(reference).__name__}, expected a list")
    calls: list[Call] = []
    for entry in reference:
        if not isinstance(entry, dict) or len(entry) != 1:
            raise BfclParseError(f"reference call is not a single-key dict: {entry!r}")
        ((name, params),) = entry.items()
        if not isinstance(params, dict):
            raise BfclParseError(f"parameters for {name!r} are {type(params).__name__}, not a dict")
        for key, accepted in params.items():
            if not isinstance(accepted, list):
                raise BfclParseError(
                    f"{name}.{key} holds {type(accepted).__name__}, not the list of acceptable "
                    "values every one of the 776 measured parameters holds"
                )
        calls.append(Call(name=str(name), arguments=dict(params)))
    return calls


def parse_response(text: str) -> list[Call]:
    """Read a model response into calls.

    Accepts the contract in :data:`CALL_FORMAT`: a JSON array of objects, each
    with ``name`` and ``arguments``. Fenced or bare, anywhere in the response,
    because requiring it to be the whole response would measure formatting.

    Raises:
        BfclParseError: No array was found, or it is not the declared shape. A
            parse failure is reported rather than scored as a wrong answer --
            they are different outcomes and only one is about the model's
            reasoning.
    """
    match = _ARRAY.search(text)
    if not match:
        raise BfclParseError("no JSON array of calls found in the response")
    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError as error:
        raise BfclParseError(f"call list is not valid JSON: {error}") from error
    if not isinstance(payload, list):
        raise BfclParseError(f"call list parsed as {type(payload).__name__}, not a list")

    calls: list[Call] = []
    for entry in payload:
        if not isinstance(entry, dict) or "name" not in entry:
            raise BfclParseError(f"call is missing a `name`: {entry!r}")
        arguments = entry.get("arguments", {})
        if not isinstance(arguments, dict):
            raise BfclParseError(f"`arguments` for {entry['name']!r} is not an object")
        calls.append(Call(name=str(entry["name"]), arguments=arguments))
    return calls


def _values_equal(supplied: object, accepted: object) -> bool:
    """Whether a supplied argument equals an accepted one.

    Numeric comparison is by value, so ``5`` and ``5.0`` are the same argument.
    Everything else is compared structurally. Strings are compared case- and
    whitespace-insensitively, because ``"data_random_forest"`` arriving as
    ``"Data_Random_Forest "`` is a formatting difference and grading it as a
    wrong call would report a presentation defect as a reasoning one.
    """
    if isinstance(supplied, bool) or isinstance(accepted, bool):
        return supplied is accepted
    if isinstance(supplied, int | float) and isinstance(accepted, int | float):
        return float(supplied) == float(accepted)
    if isinstance(supplied, str) and isinstance(accepted, str):
        return supplied.strip().casefold() == accepted.strip().casefold()
    if isinstance(supplied, list) and isinstance(accepted, list):
        return len(supplied) == len(accepted) and all(
            _values_equal(a, b) for a, b in zip(supplied, accepted, strict=True)
        )
    return bool(supplied == accepted)


def _satisfies(supplied: Call, reference: Call) -> str | None:
    """``None`` when this response call satisfies this reference call, else why not."""
    if supplied.name.strip() != reference.name.strip():
        return f"name {supplied.name!r} != {reference.name!r}"
    for key, accepted in reference.arguments.items():
        if key not in supplied.arguments:
            if any(value == OPTIONAL for value in accepted):
                continue
            return f"{reference.name}: missing required argument {key!r}"
        value = supplied.arguments[key]
        if not any(_values_equal(value, option) for option in accepted):
            return f"{reference.name}.{key}: {value!r} not in {accepted!r}"
    if extra := set(supplied.arguments) - set(reference.arguments):
        return f"{reference.name}: unexpected argument(s) {sorted(extra)}"
    return None


def match(response_calls: list[Call], reference_calls: list[Call]) -> MatchResult:
    """Whether the response's calls satisfy every reference call, one for one.

    A greedy bijection: each reference call claims the first unclaimed response
    call that satisfies it. Greedy is exact here rather than an approximation,
    because the reference's parallel calls differ in their argument values --
    that is what makes them separate calls -- so at most one response call
    satisfies each.

    Counts must be equal. A response issuing three calls where two were asked
    for has not done the task, and one issuing two where three were asked for
    plainly has not.
    """
    if len(response_calls) != len(reference_calls):
        return MatchResult(
            matched=False,
            reasons=(f"{len(response_calls)} call(s) issued, {len(reference_calls)} required",),
        )

    unclaimed = list(response_calls)
    reasons: list[str] = []
    for wanted in reference_calls:
        failures = []
        for candidate in unclaimed:
            reason = _satisfies(candidate, wanted)
            if reason is None:
                unclaimed.remove(candidate)
                break
            failures.append(reason)
        else:
            reasons.append(f"unsatisfied: {'; '.join(failures) or 'no calls left'}")
    return MatchResult(matched=not reasons, reasons=tuple(reasons))


#: Appended to the system prompt, identically in both conditions.
#:
#: It changes the task -- the pilot asked for prose and got prose -- so a run
#: made with it is not comparable with one made without, and both arms must
#: carry it or the manipulation is contaminated by a format difference.
#:
#: It asks for the call and nothing else about *how* to choose it, because the
#: point is to grade the choice rather than to coach it.
CALL_FORMAT: Final = (
    "When the task calls for using the available functions, end your reply with "
    "a JSON array of the calls to make, in this exact form and nothing after it:\n"
    '[{"name": "function_name", "arguments": {"parameter": "value"}}]\n'
    "Include one object per call. Include only parameters you are setting."
)
