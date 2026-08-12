"""Assemble a long prompt without changing its answer.

This is where the independent variable is manufactured, so it is where the
experiment is most likely to fake itself. Three properties have to hold, and each
has a documented way of failing quietly:

**The draw is reproducible.** A cell that draws different padding on a resumed
run is a different item wearing the same id.

**The padding does not change the answer.** Padding is on-topic at the client
level and off-topic at the decision level -- a matter file full of documents
about the same client that have nothing to do with the question. That is the
GSM-NoOp lesson: a distractor a reasonable reader folds into the calculation is
not a distractor. But on-topic material about the same client is exactly the
material that changes a professional answer in real life, so the invariance rule
is mechanical and checked rather than asserted.

**No library document dominates.** A document drawn into many cells is a crossed
random effect: one that perturbs truth, or one that is stylistically loud,
contaminates many cells at once and the standard errors are wrong in the
anti-conservative direction.

The fourth threat has no code in it and is the largest. Prose written to
*not matter* has a register -- fewer hard numerals, fewer deadlines, fewer
citations, more hedging -- and the core is dense in exactly those things because
that is what makes it the core. On-topic-ness fixes topical separability and
does nothing for register separability. ``scripts/separability.py`` is the gate
for that, and it is the one most likely to fire.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Final

#: Characters per token, for turning a target length into a character budget.
#:
#: Deliberately *not* the 6.01 that ``scripts/canary_long.py`` measured. That
#: figure came from repetitive filler, which tokenises far better than varied
#: prose; the run labelled "100,000 tokens" there was really 63,313. Real
#: casefile prose lands nearer 4.
#:
#: This is an estimate and the achieved count is whatever the CLI reports back in
#: ``usage``. Every run records the achieved figure, and the nominal target is a
#: label rather than a measurement.
CHARS_PER_TOKEN: Final = 4.0

#: The proportional band the governing documents are held within.
#:
#: Volume is collinear with position: pad from 2k to 100k and place the core at
#: the front, and the governing facts end up 98k tokens from the question, which
#: traces the recency curve with a length label on it. Holding *relative*
#: position fixed makes absolute distance the thing that varies. The manipulation
#: is then absolute token count at fixed relative position, which is a narrower
#: claim than "length" and is the one the write-up has to make.
DEPTH_BAND: Final[tuple[float, float]] = (0.30, 0.60)

#: The largest share of cells any single library document may appear in.
#:
#: Enforced by refusing a draw the library is too small to serve, which is the
#: actionable form: it says author more documents rather than reporting a
#: standard error that is quietly wrong.
#:
#: The arithmetic is unforgiving and the plan under-estimated it by roughly
#: tenfold. A 100k-token prompt needs 400,000 characters of padding; at a
#: realistic 4,000 characters per document that is 100 documents drawn, so the
#: cap demands a library of 333. The pilot was scoped at 25 per domain.
#:
#: It is a parameter rather than a constant because the constraint is about
#: *standard errors across cells*, and the Phase 0 pilot computes none -- twelve
#: cells, read by hand, no inference. Relaxing it there is correct; relaxing it
#: for the confirmatory grid is not, and the default says which is which.
MAX_CELL_SHARE: Final = 0.30

#: Numerals of at least this many digits are treated as load-bearing figures.
#: Below it, collisions are inevitable and meaningless -- padding will contain
#: "14" whatever anyone does, and a rule that flags it is a rule nobody keeps.
_SIGNIFICANT_DIGITS: Final = 3

_NUMERAL: Final = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
_SECTION: Final = re.compile(r"\bs\.\s?\d+(?:\(\d+\))?", re.IGNORECASE)
_ISO_DATE: Final = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_PROSE_DATE: Final = re.compile(
    r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{4}\b"
)
_PROPER_NOUN: Final = re.compile(r"\b(?:[A-Z][a-z]{2,}\s+){1,3}(?:Ltd|Limited|plc|LLP|Inc|Group)\b")


class PaddingError(ValueError):
    """The draw cannot produce a valid prompt at this length."""


@dataclass(frozen=True)
class Document:
    """One artefact in a case file: an authority, a letter, a memo, a statement."""

    id: str
    title: str
    body: str

    @property
    def rendered(self) -> str:
        return f"--- {self.id}: {self.title} ---\n{self.body.strip()}\n"


@dataclass(frozen=True)
class Core:
    """The governing documents plus the question. What the answer turns on."""

    case_id: str
    documents: tuple[Document, ...]
    question: str

    @property
    def governing_text(self) -> str:
        """Everything the answer depends on, as one string, for the invariance check."""
        return "\n".join(document.body for document in self.documents)

    @property
    def chars(self) -> int:
        return sum(_size(document) for document in self.documents)


def core_from_casefile(raw: dict, governing_ids: set[str]) -> Core:
    """Adapt a probe casefile's YAML into a :class:`Core`.

    ``governing_ids`` names the documents the answer actually turns on. It is
    passed in rather than inferred because a casefile's document list includes
    material that is already non-governing, and guessing which is which here
    would put the answer key in two places.
    """
    documents = tuple(
        Document(id=doc["id"], title=doc.get("title", doc["id"]), body=doc["body"])
        for doc in raw["documents"]
        if doc["id"] in governing_ids
    )
    if not documents:
        raise PaddingError(f"{raw['case_id']}: none of {sorted(governing_ids)} are in the casefile")
    return Core(case_id=raw["case_id"], documents=documents, question=raw["question"])


def load_bearing_tokens(text: str) -> set[str]:
    """The figures, citations, dates and parties an answer can turn on.

    Used by the invariance check. Small numerals are excluded on purpose: a rule
    that flags every "14" is a rule that gets switched off, and the collisions
    that matter are amounts, section references, deadlines and party names.

    This is a filter, not a proof. The near-miss-authority mechanism deliberately
    reuses section references, so those items must relax it per-mechanism -- and
    they are therefore exactly where this check cannot protect the answer key,
    which is why they carry the heaviest share of the adversarial audit.
    """
    tokens = set(_SECTION.findall(text))
    tokens |= set(_ISO_DATE.findall(text))
    tokens |= set(_PROSE_DATE.findall(text))
    tokens |= {match.group(0) for match in _PROPER_NOUN.finditer(text)}
    for match in _NUMERAL.finditer(text):
        raw = match.group(0)
        if len(raw.replace(",", "").split(".")[0]) >= _SIGNIFICANT_DIGITS:
            tokens.add(raw)
    return tokens


def invariance_violations(core: Core, padding: list[Document]) -> list[str]:
    """Padding documents that repeat something the governing chain turns on."""
    governing = load_bearing_tokens(core.governing_text)
    violations = []
    for document in padding:
        collisions = sorted(token for token in governing if token in document.body)
        if collisions:
            violations.append(f"{document.id} repeats {', '.join(collisions)}")
    return violations


def draw(
    library: list[Document],
    *,
    target_tokens: int,
    seed: int,
    core_chars: int = 0,
    max_cell_share: float = MAX_CELL_SHARE,
) -> list[Document]:
    """Deterministically select padding summing to roughly ``target_tokens``.

    Shuffles a copy, never the caller's list, so a caller that reuses its library
    across cells does not get a draw order that depends on call sequence.

    Raises:
        PaddingError: The library cannot fill the target, or filling it would
            require so many of its documents that one of them would appear in
            more than :data:`MAX_CELL_SHARE` of cells.
    """
    budget = int(target_tokens * CHARS_PER_TOKEN) - core_chars
    if budget <= 0:
        return []

    if not library:
        raise PaddingError("the library is empty")

    shuffled = list(library)
    random.Random(seed).shuffle(shuffled)

    drawn: list[Document] = []
    used = 0
    for document in shuffled:
        if used >= budget:
            break
        drawn.append(document)
        used += len(document.rendered)

    if used < budget:
        raise PaddingError(
            f"the library is too small for {target_tokens:,} tokens: "
            f"{used:,} chars available against {budget:,} needed. "
            f"Author more documents rather than repeating them."
        )

    share = len(drawn) / len(library)
    if share > max_cell_share:
        raise PaddingError(
            f"a draw of {len(drawn)} from a library of {len(library)} puts every document "
            f"in {share:.0%} of cells, past the {max_cell_share:.0%} cap. One document that "
            f"perturbs truth would then contaminate that many cells at once and the "
            f"standard errors would be wrong in the anti-conservative direction. "
            f"The library needs at least {int(len(drawn) / max_cell_share)} documents, "
            f"or pass max_cell_share=1.0 if this run computes no standard errors."
        )
    return drawn


def assemble(
    core: Core,
    library: list[Document],
    *,
    target_tokens: int,
    seed: int,
    max_cell_share: float = MAX_CELL_SHARE,
) -> str:
    """Core plus a padding draw, rendered as one prompt.

    The governing documents are distributed inside :data:`DEPTH_BAND`, and the
    padding order is derived from ``seed`` so a single unlucky arrangement cannot
    drive a cell.

    Raises:
        PaddingError: The draw fails, or a padding document repeats something the
            governing chain turns on.
    """
    padding = draw(
        library,
        target_tokens=target_tokens,
        seed=seed,
        core_chars=core.chars,
        max_cell_share=max_cell_share,
    )

    violations = invariance_violations(core, padding)
    if violations:
        raise PaddingError(f"{core.case_id}: padding is not invariant -- " + "; ".join(violations))

    return _weave(core, padding) + f"\n\n{'=' * 60}\n\n{core.question}\n"


def ablate(
    core: Core,
    library: list[Document],
    *,
    target_tokens: int,
    seed: int,
    max_cell_share: float = MAX_CELL_SHARE,
) -> str:
    """The same prompt with every core document removed.

    Feeds the padding-only gate: ask the question anyway and see whether the
    model declines or answers confidently from padding alone. A confident answer
    means the padding carries signal, whatever the mechanical check said.
    """
    padding = draw(
        library,
        target_tokens=target_tokens,
        seed=seed,
        core_chars=core.chars,
        max_cell_share=max_cell_share,
    )
    body = "".join(document.rendered + "\n" for document in padding)
    return body + f"\n\n{'=' * 60}\n\n{core.question}\n"


def governing_depths(prompt: str, core: Core) -> list[float]:
    """Where each governing document starts, as a fraction of the prompt.

    Raises:
        PaddingError: A governing document is not in the prompt, which means the
            weave dropped it and the item has no answer.
    """
    depths = []
    for document in core.documents:
        marker = f"--- {document.id}: {document.title} ---"
        index = prompt.find(marker)
        if index < 0:
            raise PaddingError(f"{document.id} is not in the assembled prompt")
        depths.append(index / len(prompt))
    return depths


def within_band(prompt: str, core: Core, band: tuple[float, float] = DEPTH_BAND) -> bool:
    """Whether every governing document landed inside the depth band.

    False is not always a defect. At the 2k anchor the core *is* most of the
    prompt and cannot fit inside a band 30% of it wide, so the band is a property
    of the padded strata and the low anchor is reported as unbanded rather than
    as a failure.
    """
    low, high = band
    return all(low <= depth <= high for depth in governing_depths(prompt, core))


def _size(document: Document) -> int:
    """A document's contribution to the prompt, including its separating newline."""
    return len(document.rendered) + 1


def _weave(core: Core, padding: list[Document]) -> str:
    """Lay the core into the depth band with padding before, between and after.

    Each governing document is aimed at the centre of its own slice of the band,
    rather than at the slice boundary. Aiming at boundaries put the first
    document just below the band and the last just above it -- the first version
    of this landed a conjunct at depth 0.625 against a 0.60 ceiling, which is a
    quiet way to turn a length curve back into a position curve.

    Padding is added only while it fits *below* the target, so a document is
    never pushed past its slice by the last one that would not fit.
    """
    total = core.chars + sum(_size(document) for document in padding)
    low, high = DEPTH_BAND
    count = len(core.documents)
    span = (high - low) * total
    targets = [low * total + span * (position + 0.5) / count for position in range(count)]

    woven: list[Document] = []
    used = 0
    index = 0
    # Interleaving rather than blocking is what the distributed-conjunction
    # mechanism needs: the conjuncts have to be separated by real material.
    for document, target in zip(core.documents, targets, strict=True):
        while index < len(padding) and used + _size(padding[index]) <= target:
            woven.append(padding[index])
            used += _size(padding[index])
            index += 1
        woven.append(document)
        used += _size(document)

    woven.extend(padding[index:])
    return "".join(document.rendered + "\n" for document in woven)
