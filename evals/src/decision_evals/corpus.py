"""How a trigger corpus is allowed to be built, and the checks that enforce it.

Split out of :mod:`decision_evals.triggers` when the corpus went to version 3.
That module loads and scores a set; this one decides whether the set is a fair
test at all, which is a different question and was the one nobody was asking.

**The finding that produced this module.** On 2026-08-13 the version 2 corpus
was measured against a gate the long-context plan had written for padding
documents and never pointed at the trigger set. Positives ran at a median of 18
words and negatives at 8, so turn length alone separated the labels at **AUC
0.850**, and a bare *"fire if the turn has 18 words or more"* rule scored
**0.890 accuracy with no model involved**. The best arm ever measured scored
0.956. Five manipulations of the skill description had moved firing accuracy
nowhere, and the standing reading was that no description change affects
discrimination -- but there were only about six points of room above a ruler,
and five nulls is exactly what a ceiling looks like.

Version 3 is built so that cannot happen again, and so that several questions
can be asked of one corpus instead of one:

* **length** -- four bands from a single line to 1,500 words, because the
  ``ledger`` procedure exists for a pile of context and the corpus had never
  contained a pile;
* **domain** -- the founding brief for this repository is life decisions, and
  version 2 was overwhelmingly technical and work-shaped;
* **stakes** -- Track L7 made stakes the opener's criterion while the corpus
  carried no stakes label, so the claim could not be checked;
* **ask form** -- version 2 was saturated with "should I", which is a phrase and
  not a decision;
* **negative kind** -- one pooled precision figure hides which negatives were
  free.

Every one of those is a column on the case, so the same 120 calls answer all of
them instead of one.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from decision_evals.triggers import TriggerCase, TriggerSet

#: Length bands, and the word counts a turn in each must fall inside.
#:
#: ``s`` is deliberately *exactly* the version 2 range. The old corpus survives
#: as a stratum of the new one, so version 3 can be asked whether it reproduces
#: version 2 inside its own band -- which is a far better use of the old items
#: than deleting them.
BAND_WORDS: Final[dict[str, tuple[int, int]]] = {
    "s": (1, 25),
    "m": (40, 90),
    "l": (200, 400),
    "xl": (900, 1500),
}
BANDS: Final = tuple(BAND_WORDS)

#: What the decision is about.
DOMAINS: Final = ("career", "money", "health", "relationships", "technical")

#: Whether the choice is costly to undo, pulls several things against each
#: other, or lands on someone else.
STAKES: Final = ("high", "low")

#: How the decision is asked for. ``explicit`` is "should I ...?"; ``implicit``
#: has no question at all and ends in something like "I don't know what to do";
#: ``embedded`` buries the question mid-paragraph with text after it.
ASK_FORMS: Final = ("explicit", "implicit", "embedded")

#: Which sort of non-decision a negative is.
NEGATIVE_KINDS: Final = (
    "lookup",
    "compute",
    "diagnose",
    "generate",
    "summarise",
    "settled",
    "meta",
)

#: One positive to two negatives, in **every** band.
#:
#: Equal ratios per band is the condition that makes the length AUC 0.5 across
#: the whole set rather than only inside a band. A set that is balanced overall
#: but front-loads its positives into the long bands is separable by length
#: again, and the pooled figure would not show it.
NEGATIVES_PER_POSITIVE: Final = 2

#: How far from chance any trivial feature may separate the labels.
#:
#: **Two-sided, and the one-sided version it replaces was an instrument
#: defect.** A set at AUC 0.05 is solved by a ruler exactly as well as one at
#: 0.95 -- the classifier just points the other way -- and
#: ``MAX_LENGTH_SEPARABILITY = 0.70`` would have passed it.
SEPARABILITY_BAND: Final = (0.40, 0.60)

#: How far a depth-2 stump over :data:`FEATURES` may beat the majority class.
#:
#: A battery of single features misses interactions: "long **and** first-person"
#: could solve a corpus where neither alone does. The stump is fitted and scored
#: on the same data on purpose -- it is an upper bound on what a shortcut can
#: reach, so optimism is the conservative direction here.
#:
#: **Lift, not accuracy, and the absolute version this replaces was a scale
#: error I made and then measured.** The first form of this gate was a flat
#: ``MAX_STUMP_ACCURACY = 0.70``, borrowed from the AUC target. Accuracy is not
#: comparable across corpora with different base rates: version 2 was 77%
#: negative, so predicting "never fire" scored 0.767 there, while version 3 is
#: two negatives per positive and the same empty rule scores 0.667. A flat
#: threshold therefore asked version 3 for 3.3 points of headroom and version 2
#: for 13.3, which is not one gate.
#:
#: 0.10 is the accuracy analogue of the +/-0.10 the per-feature AUC band already
#: allows, so the two gates say the same thing on their own scales. For
#: reference, version 2's word-count ruler scored 0.890 against a 0.767 baseline
#: -- a lift of **0.123**, which is the defect this whole track exists to remove.
MAX_STUMP_LIFT: Final = 0.10

_WORD = re.compile(r"[A-Za-z']+")
_SHOULD = re.compile(r"\bshould (?:i|we)\b", re.IGNORECASE)
_FIRST_PERSON = frozenset({"i", "i'm", "i've", "i'd", "i'll", "me", "my", "mine", "we", "our"})
_PASTE_CUES = re.compile(
    r"\b(?:here'?s|below|attached|pasted|paste|forwarding|copying|thread|transcript)\b",
    re.IGNORECASE,
)
_IMPERATIVES = frozenset(
    {
        "add",
        "brainstorm",
        "check",
        "convert",
        "draft",
        "explain",
        "fix",
        "generate",
        "give",
        "implement",
        "list",
        "make",
        "rank",
        "reformat",
        "refactor",
        "rename",
        "review",
        "rewrite",
        "summarise",
        "summarize",
        "tell",
        "validate",
        "write",
    }
)


#: A turn that *ends* in a question mark, as opposed to containing one.
#:
#: ``question_marks`` counts occurrences anywhere and scores 0.500 on the whole
#: turn. Terminal position is a different quantity and it leaks: in the XL band
#: two of seven positives end in ``?`` and none of fourteen negatives do.
_TERMINAL_QUESTION = re.compile(r"\?\s*$")

#: The coda a negative uses to close the door on advice it does not want.
#:
#: Written after reading the lookup negatives rather than before, which is what
#: a shortcut battery is for -- it is an adversary's list, not an independent
#: test, and it is only evidence when it finds nothing.
_DECLINES_ADVICE = re.compile(
    r"\b(?:rather than|instead of|not a recommendation|not asking|just the rules|"
    r"don'?t need|no advice)\b",
    re.IGNORECASE,
)


def _words(turn: str) -> list[str]:
    return _WORD.findall(turn.lower())


def _first_person_rate(turn: str) -> float:
    words = _words(turn)
    return sum(1 for word in words if word in _FIRST_PERSON) / len(words) if words else 0.0


def _type_token_ratio(turn: str) -> float:
    words = _words(turn)
    return len(set(words)) / len(words) if words else 0.0


def _imperative_opener(turn: str) -> float:
    words = _words(turn)
    return 1.0 if words and words[0] in _IMPERATIVES else 0.0


#: Every way of solving the corpus without reading it that I could think of.
#:
#: It is a list of my own guesses about how a corpus can be cheated and it will
#: be incomplete. That is an argument for the stump below, not against the
#: battery: an unnamed shortcut that correlates with a named one still shows up.
FEATURES: Final[dict[str, Callable[[str], float]]] = {
    "word_count": lambda turn: float(len(turn.split())),
    "char_count": lambda turn: float(len(turn)),
    "says_should_i": lambda turn: float(bool(_SHOULD.search(turn))),
    "question_marks": lambda turn: float(turn.count("?")),
    "first_person_rate": _first_person_rate,
    "paste_cues": lambda turn: float(len(_PASTE_CUES.findall(turn))),
    "imperative_opener": _imperative_opener,
    "type_token_ratio": _type_token_ratio,
    "terminal_question": lambda turn: float(bool(_TERMINAL_QUESTION.search(turn))),
    "declines_advice": lambda turn: float(bool(_DECLINES_ADVICE.search(turn))),
    # The spec says a positive ask is one sentence and a negative ask is two or
    # three, so the battery has been missing the feature the corpus is written
    # to. Pooled it reads 0.504 -- as clean as this battery can print -- while
    # `m` sits at 0.625 and `xl` at 0.296, two rulers pointing opposite ways.
    "sentence_count": lambda turn: float(len(_sentences(turn))),
}

# A terminal full stop is not in the battery because it is not a second
# feature. Every turn in the corpus ends in `?` or `.`, so `terminal_period` is
# exactly `1 - terminal_question` and its AUC is exactly the reflection --
# 0.431 against 0.569 on the closing sentence. Two columns carrying one bit
# would double this feature's weight in the count gate below.


#: The parts of a turn the battery is run over.
#:
#: **A feature computed over the whole turn is diluted by whatever the turn
#: shares with its triple**, and in the XL band that is 85-90% of the
#: characters -- as much as 5,118 shared out of 5,776. The discriminating text
#: is the closing ask, so a whole-turn AUC of 0.5 is consistent with an ask that
#: gives the label away, and until 2026-08-13 nothing here looked.
#:
#: A view maps the set to one string per case id, because ``ask`` cannot be
#: computed from a turn alone -- it needs the other members of the triple.
View = Callable[[TriggerSet], dict[str, str]]

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _turn_view(trigger_set: TriggerSet) -> dict[str, str]:
    return {case.id: case.turn for case in trigger_set.cases}


def _shared_body(turns: Sequence[str]) -> str:
    """The opening every member of a triple has byte for byte, to a word boundary.

    Cut back to the last space so the remainder starts at a word: the raw
    common prefix of *"Should I tell her now"* and *"Should I take the offer"*
    ends mid-word at ``"Should I t"``, and a feature over ``"ell her now"``
    measures the cut rather than the ask.

    Called with at least one turn: its only caller walks a cluster, and a
    cluster with no members does not exist. There is no guard for the empty
    case because an unreachable branch is a branch nothing can test.
    """
    limit = min(len(turn) for turn in turns)
    length = 0
    while length < limit and len({turn[length] for turn in turns}) == 1:
        length += 1
    head = turns[0][:length]
    boundary = head.rfind(" ")
    return head[: boundary + 1] if boundary >= 0 else ""


def _ask_view(trigger_set: TriggerSet) -> dict[str, str]:
    """What is left of each turn once the body it shares with its triple is gone.

    Derived rather than declared. A ``ask:`` field on the case would be a
    corpus change -- a new column on the answer key, needing an entry in
    ``docs/DECISIONS.md`` and invalidating nothing but confusing everything --
    while the shared body is already recoverable by intersecting the members.

    **How much this recovers is a property of the corpus, not of the method,
    and on the shipped set it is much less than the design claims.** The
    matched triples share a byte-identical body only in XL (4,256-5,118
    characters) and in three of nine L triples. In S, M and the other six L
    triples the members share 0-2 characters, so the ask *is* the turn there and
    this view collapses onto :func:`_turn_view` for 30 of 40 triples. That is
    the honest answer and it is why :func:`_close_view` exists beside it.
    """
    members: dict[str | None, list[TriggerCase]] = defaultdict(list)
    for case in trigger_set.cases:
        members[case.triple].append(case)
    texts: dict[str, str] = {}
    for triple, cases in members.items():
        body = "" if triple is None else _shared_body([case.turn for case in cases])
        for case in cases:
            texts[case.id] = case.turn[len(body) :].strip() or case.turn
    return texts


def _close_view(trigger_set: TriggerSet) -> dict[str, str]:
    """The closing sentence, which is where every band puts the ask.

    The general form of :func:`_ask_view`: it needs no triple, it works in the
    30 triples whose members share no body, and it is the segment the corpus
    was authored to vary. It is also where the battery's blind spot was --
    ``imperative_opener`` reads the first word of the *turn*, and the imperative
    that matters is the one that opens *"Just the rules and where they are
    written down."*
    """
    return {case.id: _sentences(case.turn)[-1] for case in trigger_set.cases}


def _open_view(trigger_set: TriggerSet) -> dict[str, str]:
    """The first sentence of the ask, which is where a displaced leak lands next.

    Added 2026-08-13 for a defect that was **created by fixing the previous
    one**. The closing-length leak was corrected by specifying longer positive
    closings; because an ask is capped at +/-15% of the positive's length,
    buying closing words means spending opening words, and the negatives'
    openers collapsed into fragments -- *"Separately."*, *"Clause 9.2."*,
    *"Numbers only."*, *"Lease signed."* The closing view cannot see that, and
    neither can the whole turn.

    That is four generations of one defect: positives closing short, positives
    closing longest, first-person rate, clipped negative openers. Enumerating
    views will always be one generation behind, which is the argument for
    :func:`matched_separability` -- this view is the patch, that statistic is
    the fix.
    """
    asks = _ask_view(trigger_set)
    return {case.id: _sentences(asks[case.id])[0] for case in trigger_set.cases}


def _sentences(text: str) -> list[str]:
    parts = [part for part in _SENTENCE_END.split(text.strip()) if part.strip()]
    return parts or [text]


VIEWS: Final[dict[str, View]] = {
    "turn": _turn_view,
    "ask": _ask_view,
    "close": _close_view,
    "open": _open_view,
}

#: The view whose per-feature AUCs are gated one at a time.
#:
#: The published gate, unchanged. Its false-failure rate on a corpus carrying no
#: signal is measured rather than assumed -- see :data:`MIN_LEAKS_PER_VIEW`.
GATED_VIEW: Final = "turn"

#: How many features must leave the band in a *derived* view before it fails.
#:
#: **Derived, and here is the derivation.** Twenty thousand within-triple label
#: permutations of the shipped 120-item corpus -- the exact null the matched
#: design implies, and narrower than the independent-sampling formula in
#: ``notebook/2026-08-13-the-xl-band-and-two-rulers-that-cancelled.md`` because
#: three members of a triple are not three draws. Measured per-view chance of
#: failing a *clean* corpus:
#:
#: ===========  =======  =======  =======  =======
#: view         P(>=1)   P(>=2)   P(>=3)   P(>=4)
#: ===========  =======  =======  =======  =======
#: turn          0.032    0.008    0.001    0.000
#: ask           0.075    0.009    0.002    0.000
#: close         0.151    0.053    0.019    0.002
#: ===========  =======  =======  =======  =======
#:
#: Gating the derived views one feature at a time would fail a clean corpus on
#: one run in five (P(>=1) over all three views is 0.206), and a gate that
#: fails at random is a gate somebody turns off -- the argument
#: ``_check_separability`` already makes for the ratchet. At three, each derived
#: view fails a clean corpus at most as often as the per-feature gate that
#: already ships (0.019 and 0.002 against 0.032), and the shipped corpus's four
#: out-of-band closing features land at p = 0.002.
#:
#: **This is the first gate in this repository whose false-failure rate was
#: measured before it was switched on**, and that is the part worth copying
#: rather than the threshold. Every earlier gate here was given a round number
#: and found out afterwards: ``MAX_LENGTH_SEPARABILITY = 0.70`` was borrowed
#: from a plan about padding documents and never pointed at the trigger set
#: until the set scored 0.850; ``MAX_STUMP_ACCURACY = 0.70`` was a flat
#: threshold across corpora with different base rates and had to be re-derived
#: as a lift; two falsifiers were wrong the day they were written. The question
#: "how often does this fire on a corpus that is fine" is answerable in half a
#: second and nobody had asked it.
#:
#: :func:`null_leak_rate` recomputes this table, so the threshold is checkable
#: rather than remembered. It is calibrated on *this* corpus's shape -- 40
#: triples of three, ten features -- and a corpus of a different shape needs it
#: re-derived, not carried over.
MIN_LEAKS_PER_VIEW: Final = 3


def separability(
    trigger_set: TriggerSet,
    feature: Callable[[str], float],
    texts: Mapping[str, str] | None = None,
) -> float:
    """How well one feature alone separates positives from negatives, as an AUC.

    0.5 means the feature carries no signal. 1.0 means it solves the set and
    **0.0 means it solves the set backwards**, which is the same defect.

    This is the concordance form of the Mann-Whitney statistic -- the share of
    positive/negative pairs the positive scores higher in, with ties at a half --
    computed directly rather than pulled from scikit-learn, which is not a
    dependency here and must not become one for a five-line rank statistic.

    ``texts`` is the view: which string of each case the feature reads. It
    defaults to the whole turn, which is what every caller wanted until the
    whole turn turned out to be mostly shared body.
    """
    positives = [_score(case, feature, texts) for case in trigger_set.positives]
    negatives = [_score(case, feature, texts) for case in trigger_set.negatives]
    if not positives or not negatives:
        return 0.5
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def _score(
    case: TriggerCase, feature: Callable[[str], float], texts: Mapping[str, str] | None
) -> float:
    return feature(case.turn if texts is None else texts[case.id])


# `separability_report` stood here: every feature against the whole turn, worst
# first. `battery_report` subsumes it -- same numbers, plus the other two views,
# the per-band breakdown and the attainable interval -- and once `_check_shortcuts`
# moved across, nothing called it. Leaving a second entry point that reads only
# the view the corpus is *not* separable on is how the next reader concludes the
# battery is clean, so it is gone rather than deprecated.


def attainable_auc(
    trigger_set: TriggerSet,
    feature: Callable[[str], float],
    texts: Mapping[str, str] | None = None,
) -> tuple[float, float]:
    """Every AUC this feature could reach if the labels fell differently.

    **The question a passing check has to be able to answer.** The matched
    design fixes which turns exist and how many of each triple are positive; the
    only thing a corpus author chooses is *which* member of each triple is the
    positive. So the honest test of whether a check ran is whether any of those
    choices could have pushed it out of :data:`SEPARABILITY_BAND`. If none
    could, the check reported a pass it was structurally incapable of
    withholding, and that pass is not evidence about the corpus.

    The bound is exact in the direction that matters. A positive/negative pair
    drawn from two triples the feature is *constant across* contributes the same
    concordance whichever members are chosen, so it is fixed; every other pair
    is allowed its full range of ``[0, 1]``. Real assignments cannot reach every
    point in the returned interval, so this is an outer bound: an interval that
    lies inside the band proves the check cannot fail, while one that escapes it
    only suggests the check might.

    Returns ``(0.0, 1.0)`` -- everything is attainable, nothing is proven -- for
    a set that declares no triples, because without the clusters there is no
    design constraining the labels.
    """
    clusters: dict[str | None, list[TriggerCase]] = defaultdict(list)
    for case in trigger_set.cases:
        clusters[case.triple].append(case)
    if None in clusters:
        return 0.0, 1.0
    total = len(trigger_set.positives) * len(trigger_set.negatives)
    if not total:
        return 0.5, 0.5

    values = {
        name: {_score(case, feature, texts) for case in cases} for name, cases in clusters.items()
    }
    fixed = 0.0
    movable = 0
    for left, left_cases in clusters.items():
        n_positive = sum(1 for case in left_cases if case.should_fire)
        for right, right_cases in clusters.items():
            pairs = n_positive * sum(1 for case in right_cases if not case.should_fire)
            if len(values[left]) == 1 and len(values[right]) == 1:
                here, there = next(iter(values[left])), next(iter(values[right]))
                fixed += pairs * (1.0 if here > there else 0.5 if here == there else 0.0)
            else:
                movable += pairs
    return fixed / total, (fixed + movable) / total


#: How many null standard errors the matched statistic may sit from chance.
#:
#: **A z rather than a fixed band, and that is the same correction
#: :data:`MAX_STUMP_LIFT` already had to make once.** The matched statistic's
#: null standard error is known in closed form and moves with the corpus:
#: ``sqrt(Var/T)`` over ``T`` triples, so a fixed +/-0.10 means 1.17 SE at 23
#: triples and 1.96 SE at 64. That is not one gate, exactly as a flat accuracy
#: threshold was not one gate across two base rates.
#:
#: **Derived from the anchor this module already committed to** --- no derived
#: gate may fail a clean corpus more often than the per-feature gate on the
#: turn view already does --- and not from the leak it happens to catch.
#: Measured over 20,000 within-triple permutations at T=64, where the turn
#: view's pooled per-feature gate sits at 0.0094:
#:
#: =====  ======  ======  ======  ======
#: z      turn    ask     close   open
#: =====  ======  ======  ======  ======
#: 2.5    0.0423  0.0427  0.0286  0.0138
#: 3.0    0.0076  0.0072  0.0053  0.0021
#: 3.5    0.0014  0.0013  0.0008  0.0003
#: =====  ======  ======  ======  ======
#:
#: 3.0 is the smallest value on that grid at which **every** view clears the
#: anchor; 2.5 fails it in all four. The whole matched battery then costs
#: 0.0162 per run against a clean corpus.
#:
#: The analytic SE is used rather than a permuted one because ties can only
#: shrink the true null spread --- measured at 0.80 to 0.99 of the analytic
#: value across the forty checks --- so the gate errs toward not firing.
MATCHED_Z: Final = 3.0


def matched_separability(
    trigger_set: TriggerSet,
    feature: Callable[[str], float],
    texts: Mapping[str, str] | None = None,
) -> float:
    """The AUC computed **only** over the comparisons the design actually matched.

    Within each triple, how often the positive outscores its own two negatives,
    averaged over triples. 0.5 is chance, and it is chance *per triple*, so
    nothing cancels between bands.

    **This is the statistic the matched design was built to produce, and the
    pooled AUC drowns it.** At 64 triples there are 8,192 positive/negative
    pairs and only 128 of them are within-triple: the design's own comparisons
    are **1.6% of the pooled number**, and the other 98.4% compare a positive
    against negatives from unrelated triples -- exactly the comparisons the
    matching was supposed to make irrelevant. A habit that puts the positive
    top of its own triple every time therefore moves the pooled AUC by almost
    nothing while being perfectly learnable.

    Measured on the shipped corpus the day the ``open`` view was added: turn
    word_count reads **0.518 pooled and 0.656 matched**, which is 3.1 null
    standard errors and invisible to every gate that existed.

    **This is the answer to "a battery that enumerates views is one view behind
    the author's next habit".** It does not name a property. Any rule of the
    form *the positive's ask is the longest / shortest / most first-person of
    its three* is a skew in the positive's rank within its triple, whatever
    property is being ranked, and this reads that skew directly. It cannot
    catch a habit expressed in a feature the battery does not compute -- no
    statistic can -- but it catches every generation of a habit in a feature it
    does.
    """
    scores = [
        sum(
            1.0 if positive > negative else 0.5 if positive == negative else 0.0
            for negative in negatives
        )
        / len(negatives)
        for positive, negatives in _matched_groups(trigger_set, feature, texts)
    ]
    return sum(scores) / len(scores) if scores else 0.5


def _matched_groups(
    trigger_set: TriggerSet,
    feature: Callable[[str], float],
    texts: Mapping[str, str] | None = None,
) -> list[tuple[float, list[float]]]:
    """Per triple: the positive's score, and its own negatives' scores."""
    clusters: dict[str | None, list[TriggerCase]] = defaultdict(list)
    for case in trigger_set.cases:
        clusters[case.triple].append(case)
    groups = []
    for members in clusters.values():
        positives = [case for case in members if case.should_fire]
        negatives = [case for case in members if not case.should_fire]
        if len(positives) != 1 or not negatives:
            continue
        groups.append(
            (
                _score(positives[0], feature, texts),
                [_score(case, feature, texts) for case in negatives],
            )
        )
    return groups


def _candidate_scores(
    trigger_set: TriggerSet,
    feature: Callable[[str], float],
    texts: Mapping[str, str] | None = None,
) -> list[list[float]]:
    """Per triple, the concordance each member would score as the positive.

    The design's null in full, computed rather than simulated: the only thing
    the labels are free to choose is which member of a triple is the positive,
    so these three numbers *are* the null distribution for that triple.

    Their mean is exactly 0.5 for every triple, whatever the values and however
    many ties -- concordance is antisymmetric, so the three candidates' scores
    sum to 1.5. Which means the statistic's null centre needs no assumption and
    all that varies between features is the spread.
    """
    candidates = []
    for positive, negatives in _matched_groups(trigger_set, feature, texts):
        members = [positive, *negatives]
        candidates.append(
            [
                sum(
                    1.0 if chosen > other else 0.5 if chosen == other else 0.0
                    for position, other in enumerate(members)
                    if position != index
                )
                / (len(members) - 1)
                for index, chosen in enumerate(members)
            ]
        )
    return candidates


def matched_null_se(
    trigger_set: TriggerSet,
    feature: Callable[[str], float],
    texts: Mapping[str, str] | None = None,
) -> float:
    """Null standard error of :func:`matched_separability`, exactly.

    **Conditional on the values, so ties are handled rather than assumed away.**
    The closed form this replaces --- ``sqrt((m + 1) / (12 (m - 1) T))``, 0.0510
    at 64 triples --- assumes each triple's three candidate scores are distinct.
    ``sentence_count`` is the feature that makes that false: a triple of one,
    two and two sentences has two candidates scoring alike, and a triple where
    all three match has no spread at all. Measured against this exact form, the
    closed form ran 0.80 to 0.99 of the truth across forty checks --- close
    enough to have gone unnoticed, wrong in a direction that varies by feature.

    Returns ``0.0`` when no triple can move, which is the inert case: ``z`` is
    then undefined rather than infinite, and the check cannot fire.
    """
    candidates = _candidate_scores(trigger_set, feature, texts)
    if not candidates:
        return 0.0
    variance = float(
        sum(sum((score - 0.5) ** 2 for score in scores) / len(scores) for scores in candidates)
    )
    return float(variance**0.5) / len(candidates)


def matched_attainable(
    trigger_set: TriggerSet,
    feature: Callable[[str], float],
    texts: Mapping[str, str] | None = None,
) -> tuple[float, float]:
    """Every matched value the design's label choices could have produced.

    **Exact, not a bound.** Each triple contributes its own concordance and the
    choices are independent, so the extremes are reached by taking the best and
    the worst member in every triple at once. The pooled analogue in
    :func:`attainable_auc` can only manage an outer bound because cross-triple
    pairs couple the choices.
    """
    candidates = _candidate_scores(trigger_set, feature, texts)
    if not candidates:
        return 0.5, 0.5
    return (
        sum(min(scores) for scores in candidates) / len(candidates),
        sum(max(scores) for scores in candidates) / len(candidates),
    )


def matched_dispersion_z(
    trigger_set: TriggerSet,
    feature: Callable[[str], float],
    texts: Mapping[str, str] | None = None,
) -> float:
    """Are the per-triple ranks *spread* more than chance, with a mean of 0.5?

    **The pooled-cancellation problem, answered without splitting the corpus.**
    Three times in one day a feature has read clean pooled while separating
    inside a band: terminal ``?`` at 0.569 pooled and 0.643 in XL; the four
    closing features; and ``sentence_count`` at **0.504 pooled with m at 0.625
    and xl at 0.296**, two rulers pointing opposite ways and cancelling almost
    exactly. Every mean-based statistic has this hole, including
    :func:`matched_separability`, because opposite skews average out.

    Splitting into bands is the obvious fix and it is the wrong one: at 98 to
    392 pairs a band's null is wide enough that a clean corpus fails one
    regularly, which is the arithmetic in
    ``notebook/2026-08-13-the-xl-band-and-two-rulers-that-cancelled.md``.

    So test the *shape* instead of the location, at full sample size. If no
    habit exists, each triple's concordance is a draw from its own three
    candidate scores, and the spread of what was actually observed is
    predictable: ``sum (a_i - 0.5)^2`` has null mean ``sum v_i`` where ``v_i``
    is that triple's own candidate variance. Two opposite rulers put the
    positive at an extreme of its triple in both bands, so the observed sum of
    squares runs *high* while the mean sits exactly at chance. One ruler raises
    it too, so this does not replace the mean test; it covers the case the mean
    test is blind to by construction.

    Returns the standardised excess. Positive means more extreme ranks than
    chance; ``0.0`` when nothing can move.
    """
    candidates = _candidate_scores(trigger_set, feature, texts)
    observed = [
        sum(1.0 if p > n else 0.5 if p == n else 0.0 for n in negatives) / len(negatives)
        for p, negatives in _matched_groups(trigger_set, feature, texts)
    ]
    if not candidates:
        return 0.0
    statistic = sum((value - 0.5) ** 2 for value in observed)
    mean = 0.0
    variance = 0.0
    for scores in candidates:
        squares = [(score - 0.5) ** 2 for score in scores]
        expected = sum(squares) / len(squares)
        mean += expected
        variance += sum(square**2 for square in squares) / len(squares) - expected**2
    return (statistic - mean) / variance**0.5 if variance > 0 else 0.0


@dataclass(frozen=True)
class Check:
    """One feature, read through one view, and whether it could have failed.

    Attributes:
        per_band: The same AUC inside each length band. **Reported, never
            gated.** A pooled 0.511 hid a 0.769 in L against a 0.301 in XL once
            already; per-band numbers are how a reader sees a cancellation. They
            are not a gate because at 98 to 392 pairs a band's null is wide
            enough that a clean corpus would fail one regularly, and the
            arithmetic for that is in
            ``notebook/2026-08-13-the-xl-band-and-two-rulers-that-cancelled.md``.
    """

    view: str
    feature: str
    auc: float
    attainable: tuple[float, float]
    per_band: dict[str, float]
    matched: float = 0.5
    matched_attainable: tuple[float, float] = (0.5, 0.5)
    matched_per_band: dict[str, float] = field(default_factory=dict)
    null_se: float = 0.0
    dispersion_z: float = 0.0

    @property
    def matched_z(self) -> float:
        """Null standard errors between the matched value and chance."""
        return abs(self.matched - 0.5) / self.null_se if self.null_se else 0.0

    @property
    def inert(self) -> bool:
        """**Neither** statistic could have been pushed out by any label choice.

        Both, because they fail differently: a feature matched away inside every
        triple is pinned on the matched statistic and can still drift on the
        pooled one, and a feature the pooled statistic cannot move may be the
        one carrying a within-triple habit. Requiring both to be dead is what
        makes a pass mean the check was capable of failing.
        """
        low, high = SEPARABILITY_BAND
        pooled_dead = low <= self.attainable[0] and self.attainable[1] <= high
        reach = max(abs(value - 0.5) for value in self.matched_attainable)
        matched_dead = not self.null_se or reach <= MATCHED_Z * self.null_se
        return pooled_dead and matched_dead

    @property
    def leaks(self) -> bool:
        low, high = SEPARABILITY_BAND
        return not low <= self.auc <= high

    @property
    def matched_leaks(self) -> bool:
        return self.matched_z > MATCHED_Z

    @property
    def cancels(self) -> bool:
        """Ranks more extreme than chance while the mean says nothing.

        One-sided: only an *excess* of extreme ranks is evidence of a habit.
        A deficit means the positive sits mid-triple more often than chance,
        which no authoring rule of the observed family produces.
        """
        return self.dispersion_z > MATCHED_Z

    def describe_bands(self) -> str:
        return ", ".join(f"{band} {score:.3f}" for band, score in self.per_band.items())

    def describe_matched_bands(self) -> str:
        return ", ".join(f"{band} {score:.3f}" for band, score in self.matched_per_band.items())


def battery_report(trigger_set: TriggerSet) -> tuple[Check, ...]:
    """Every feature against every view, both statistics, pooled and per band."""
    bands = [band for band in BANDS if any(case.band == band for case in trigger_set.cases)]
    subsets = {band: _band_subset(trigger_set, band) for band in bands}
    checks: list[Check] = []
    for view_name, view in VIEWS.items():
        texts = view(trigger_set)
        for name, feature in FEATURES.items():
            checks.append(
                Check(
                    view=view_name,
                    feature=name,
                    auc=separability(trigger_set, feature, texts),
                    attainable=attainable_auc(trigger_set, feature, texts),
                    per_band={band: separability(subsets[band], feature, texts) for band in bands},
                    matched=matched_separability(trigger_set, feature, texts),
                    matched_attainable=matched_attainable(trigger_set, feature, texts),
                    matched_per_band={
                        band: matched_separability(subsets[band], feature, texts) for band in bands
                    },
                    null_se=matched_null_se(trigger_set, feature, texts),
                    dispersion_z=matched_dispersion_z(trigger_set, feature, texts),
                )
            )
    return tuple(checks)


def _band_subset(trigger_set: TriggerSet, band: str) -> TriggerSet:
    return TriggerSet(
        skill=trigger_set.skill,
        cases=tuple(case for case in trigger_set.cases if case.band == band),
        version=trigger_set.version,
    )


Row = tuple[tuple[float, ...], bool]

#: Candidate cut points per feature in the *outer* split of the stump search.
#:
#: The inner split is exact. Capping the outer grid makes the reported number a
#: **lower** bound on the best depth-2 stump, which is the lenient direction, so
#: the gate says a corpus that fails is certainly cheatable and a corpus that
#: passes is only not-obviously so. Stated rather than hidden: an exact outer
#: search is O(features^2 x n^2) and runs for seconds inside ``de check``.
_OUTER_CUTS: Final = 16


def _rows(trigger_set: TriggerSet) -> list[Row]:
    return [
        (tuple(fn(case.turn) for fn in FEATURES.values()), case.should_fire)
        for case in trigger_set.cases
    ]


def _leaf(rows: Sequence[Row]) -> int:
    """Correct predictions from one leaf voting its majority."""
    positives = sum(1 for _, label in rows if label)
    return max(positives, len(rows) - positives)


def _depth1(rows: Sequence[Row]) -> int:
    """Correct predictions from the best single threshold on any one feature."""
    total = len(rows)
    if total == 0:
        return 0
    positives = sum(1 for _, label in rows if label)
    best = max(positives, total - positives)
    for index in range(len(FEATURES)):
        order = sorted(rows, key=lambda row: row[0][index])
        left_positives = 0
        for cut in range(total - 1):
            left_positives += order[cut][1]
            if order[cut][0][index] == order[cut + 1][0][index]:
                continue
            left = cut + 1
            best = max(
                best,
                max(left_positives, left - left_positives)
                + max(positives - left_positives, total - left - positives + left_positives),
            )
    return best


def stump_accuracy(trigger_set: TriggerSet) -> float:
    """Best accuracy a depth-2 decision stump over :data:`FEATURES` reaches.

    The number to compare against a model arm. If a two-question flowchart over
    word counts and punctuation scores 0.89, an arm scoring 0.956 has bought six
    points, and that is the sentence a reader deserves next to any headline.

    **Over the whole turn only, and that is a measurement rather than an
    oversight.** Running the stump over all three views gives it thirty columns
    instead of ten, and a depth-2 tree fitted and scored on the same 120 rows
    overfits harder the more columns it is handed: across 200 within-triple
    permutations of *label-free* data the null lift rises from a mean of 0.056
    (p95 0.075) at ten columns to 0.077 (p95 0.100) at thirty, and the share of
    clean corpora exceeding :data:`MAX_STUMP_LIFT` rises from 0.020 to 0.060.
    The thirty-column stump reads 0.108 on the shipped corpus -- which would
    fail the cap while sitting on the null's 95th percentile, so it is not
    evidence of anything. Widening the columns without re-deriving the cap would
    repeat, exactly, the scale error :data:`MAX_STUMP_LIFT` was written to
    correct. The wide number is worth reporting; it is not worth gating.

    Adding ``terminal_question`` and ``declines_advice`` to the ten columns was
    checked the same way and moves neither the observed lift (0.083) nor the
    null (p95 0.075).
    """
    rows = _rows(trigger_set)
    if not rows:
        return 0.0
    best = _depth1(rows)
    for index in range(len(FEATURES)):
        order = sorted(rows, key=lambda row: row[0][index])
        step = max(1, len(order) // _OUTER_CUTS)
        for cut in range(step - 1, len(order) - 1, step):
            if order[cut][0][index] == order[cut + 1][0][index]:
                continue
            best = max(best, _depth1(order[: cut + 1]) + _depth1(order[cut + 1 :]))
    return best / len(rows)


def null_leak_rate(
    trigger_set: TriggerSet,
    view: str,
    *,
    leaks: int = MIN_LEAKS_PER_VIEW,
    draws: int = 2_000,
    seed: int = 20_260_813,
) -> float:
    """How often a corpus carrying **no signal at all** would fail this view.

    The null the matched design implies: hold every turn and every triple where
    it is, and re-draw which member of each triple is the positive. A corpus
    whose labels mean nothing is exactly that draw, so the share of draws in
    which ``leaks`` or more features leave the band *is* the gate's
    false-failure rate -- measured on the corpus in hand rather than taken from
    a formula that assumes 120 independent items when there are 40 clusters of
    three.

    This is what :data:`MIN_LEAKS_PER_VIEW` is derived from, and it is a
    function rather than a comment so the derivation can be re-run. It is not
    called by :func:`check_corpus`: twenty thousand draws is a minute of
    arithmetic and a gate may not cost that on every commit.

    Requires the one-positive-per-triple design :func:`_check_triples` enforces;
    returns ``0.0`` for anything else, since without the clusters there is no
    null to draw from.
    """
    import numpy as np

    clusters: dict[str | None, list[TriggerCase]] = defaultdict(list)
    for case in trigger_set.cases:
        clusters[case.triple].append(case)
    members = [clusters[name] for name in sorted(clusters, key=str)]
    sizes = {len(group) for group in members}
    if (
        None in clusters
        or len(sizes) != 1
        or any(sum(1 for case in group if case.should_fire) != 1 for group in members)
    ):
        return 0.0
    width = sizes.pop()

    texts = VIEWS[view](trigger_set)
    columns = [
        np.array([[feature(texts[case.id]) for case in group] for group in members], float)
        for feature in FEATURES.values()
    ]
    rng = np.random.default_rng(seed)
    choices = rng.integers(0, width, size=(draws, len(members)))
    rows = np.arange(len(members))
    low, high = SEPARABILITY_BAND
    leaked = np.zeros(draws, dtype=int)
    for values in columns:
        for start in range(0, draws, 500):
            chunk = choices[start : start + 500]
            taken = np.arange(chunk.shape[0])
            positives = values[rows[None, :], chunk]
            keep = np.ones((chunk.shape[0], len(members), width), dtype=bool)
            keep[taken[:, None], rows[None, :], chunk] = False
            negatives = (
                values[None, :, :]
                .repeat(chunk.shape[0], 0)[keep]
                .reshape(chunk.shape[0], len(members) * (width - 1))
            )
            gap = positives[:, :, None] - negatives[:, None, :]
            auc = ((gap > 0).sum(axis=(1, 2)) + 0.5 * (gap == 0).sum(axis=(1, 2))) / (
                positives.shape[1] * negatives.shape[1]
            )
            leaked[start : start + chunk.shape[0]] += (auc < low) | (auc > high)
    return float((leaked >= leaks).mean())


def _band_of(case: TriggerCase) -> str | None:
    return case.band


@dataclass(frozen=True)
class Finding:
    """One thing wrong with a corpus, and whether a baseline may defer it.

    Attributes:
        key: The finding's stable identity, or ``""`` for one that cannot be
            baselined. **Identity is the set of things that went wrong, not the
            wording**, so a fifth feature joining a leak is a different finding
            and lands outside any baseline naming the four. A message would
            have made the baseline match on prose and quietly cover the fifth.
        message: What a reader sees, including the per-band breakdown.
    """

    key: str
    message: str


#: Findings a baseline may never defer.
#:
#: A structural defect -- a case with no band, a triple that is not one
#: positive and two negatives, a band whose members are not the length it
#: claims -- is a corpus that cannot support the reading its results will be
#: given, and it is fixable by the person who wrote it in the time it takes to
#: read this sentence. There is no backlog to defer, so these carry no key and
#: :func:`corpus_baseline` cannot reach them.
_UNBASELINEABLE: Final = ""


def check_corpus(trigger_set: TriggerSet, path: Path) -> list[Finding]:
    """Every structural rule version 3 is built on, checked rather than intended.

    Returns an empty list for a set that predates the strata (version 2 and
    earlier declare no ``band``), because those sets are archived rather than
    fixed and re-checking them would only produce noise nobody can act on.
    """
    if not any(case.band for case in trigger_set.cases):
        return []
    structural = [
        *_check_vocabularies(trigger_set, path),
        *_check_bands(trigger_set, path),
        *_check_triples(trigger_set, path),
        *_check_ratio(trigger_set, path),
    ]
    return [
        *(Finding(_UNBASELINEABLE, message) for message in structural),
        *_check_shortcuts(trigger_set, path),
    ]


def _check_vocabularies(trigger_set: TriggerSet, path: Path) -> list[str]:
    issues: list[str] = []
    fields: tuple[tuple[str, Callable[[TriggerCase], str | None], tuple[str, ...]], ...] = (
        ("band", lambda case: case.band, BANDS),
        ("domain", lambda case: case.domain, DOMAINS),
        ("stakes", lambda case: case.stakes, STAKES),
        ("ask", lambda case: case.ask, ASK_FORMS),
    )
    for case in trigger_set.cases:
        for name, get, allowed in fields:
            value = get(case)
            if value is None:
                issues.append(f"{path}: case {case.id!r} declares no {name}")
            elif value not in allowed:
                issues.append(
                    f"{path}: case {case.id!r} has {name} {value!r}, not one of "
                    f"{', '.join(allowed)}"
                )
        if case.should_fire:
            continue
        if case.kind is None:
            issues.append(f"{path}: negative case {case.id!r} declares no kind")
        elif case.kind not in NEGATIVE_KINDS:
            issues.append(
                f"{path}: negative case {case.id!r} has kind {case.kind!r}, not one of "
                f"{', '.join(NEGATIVE_KINDS)}"
            )
    return issues


def _check_bands(trigger_set: TriggerSet, path: Path) -> list[str]:
    issues: list[str] = []
    for case in trigger_set.cases:
        limits = BAND_WORDS.get(case.band or "")
        if limits is None:
            continue
        words = len(case.turn.split())
        low, high = limits
        if not low <= words <= high:
            issues.append(
                f"{path}: case {case.id!r} is in band {case.band!r} at {words} words, outside "
                f"{low}-{high}. A band whose members are not the length it claims cannot "
                "support a per-band reading of the results."
            )
    return issues


def _check_triples(trigger_set: TriggerSet, path: Path) -> list[str]:
    """One positive and two negatives per triple, matched on length.

    The length match is what makes the whole design work. Two negatives written
    to be the same length as their positive are the reason the set is not
    solvable with a ruler, and a triple whose members drift apart quietly
    reintroduces the defect version 3 exists to remove.
    """
    issues: list[str] = []
    grouped: dict[str, list[TriggerCase]] = {}
    for case in trigger_set.cases:
        if case.triple is None:
            issues.append(f"{path}: case {case.id!r} belongs to no triple")
            continue
        grouped.setdefault(case.triple, []).append(case)

    for name, members in sorted(grouped.items()):
        positives = [case for case in members if case.should_fire]
        if len(members) != 1 + NEGATIVES_PER_POSITIVE or len(positives) != 1:
            issues.append(
                f"{path}: triple {name!r} has {len(positives)} positive(s) and "
                f"{len(members) - len(positives)} negative(s); every triple is one positive "
                f"and {NEGATIVES_PER_POSITIVE} negatives"
            )
        if len({case.band for case in members}) != 1:
            issues.append(f"{path}: triple {name!r} spans more than one band")
        counts = [len(case.turn.split()) for case in members]
        if counts and max(counts) - min(counts) > _tolerance(max(counts)):
            issues.append(
                f"{path}: triple {name!r} runs {min(counts)}-{max(counts)} words, wider than "
                f"the {_tolerance(max(counts))}-word tolerance. The members of a triple must "
                "be the same length, or length carries the label again."
            )
    return issues


def _tolerance(longest: int) -> int:
    """How far apart the members of a triple may be, in words.

    10%, with a floor of three words. The floor exists because 10% of a
    twenty-word turn is two words, which is finer than the difference between
    "Should I take it?" and "Should I take the offer?" -- a rule that strict
    would be met by padding rather than by matching. At 1,200 words the
    proportional term takes over and the floor never binds.
    """
    return max(3, round(0.1 * longest))


def _check_ratio(trigger_set: TriggerSet, path: Path) -> list[str]:
    issues: list[str] = []
    positives = Counter(case.band for case in trigger_set.positives)
    negatives = Counter(case.band for case in trigger_set.negatives)
    for band in sorted(set(positives) | set(negatives), key=str):
        wanted = positives[band] * NEGATIVES_PER_POSITIVE
        if negatives[band] != wanted:
            issues.append(
                f"{path}: band {band!r} has {positives[band]} positives and {negatives[band]} "
                f"negatives, not {wanted}. Equal ratios in every band is what makes the "
                "length AUC 0.5 across the set and not only inside a band."
            )
    return issues


def _check_shortcuts(trigger_set: TriggerSet, path: Path) -> list[Finding]:
    checks = battery_report(trigger_set)
    findings = [
        *_check_inert(checks, path),
        *_check_leaks(checks, path),
        *_check_matched(checks, path),
    ]
    stump = stump_accuracy(trigger_set)
    baseline = majority_baseline(trigger_set)
    if stump - baseline > MAX_STUMP_LIFT + 1e-9:
        findings.append(
            Finding(
                "stump",
                f"{path}: a depth-2 stump over the feature battery reaches {stump:.3f} "
                f"accuracy against a majority-class baseline of {baseline:.3f} -- a lift of "
                f"{stump - baseline:.3f}, above {MAX_STUMP_LIFT}. Two questions about "
                "punctuation and word counts should not get most of the way to the answer.",
            )
        )
    return findings


def _check_inert(checks: Sequence[Check], path: Path) -> list[Finding]:
    """A feature that could not have failed anywhere has not been tested.

    **The failure this exists for.** ``imperative_opener`` reads the first word
    of the whole turn, and the turn opens with the shared body, so on the
    shipped corpus its value moves in **one triple out of forty** and the widest
    AUC any label assignment could have produced is 0.525. It has been reported
    as a pass on every run and it was never able to be anything else. Same for
    ``paste_cues``: constant across 36 of 40 triples, attainable range
    [0.405, 0.595], a pass by construction.

    That is the estimator defect ``CLAUDE.md`` names -- "an estimator that
    cannot return a non-zero value is not a measurement, and it does not
    announce itself" -- for the fourth time in this repository, and the first
    time in a check rather than in a run.

    The unit is the **feature, not the check**. A feature that is pinned on the
    whole turn but live on the closing sentence has been tested, and that is the
    normal shape of a matched corpus: matching a feature within triples is how
    the design *removes* it as a confound, so pinning is a success there and
    only a failure when it happens in every view at once. The one-line
    consequence is that ``imperative_opener`` is rescued by ``close`` rather
    than deleted -- which is also the argument for the view mechanism.
    """
    findings: list[Finding] = []
    for name in FEATURES:
        family = [check for check in checks if check.feature == name]
        if not family or not all(check.inert for check in family):
            continue
        where = "; ".join(
            f"{check.view} could only reach [{check.attainable[0]:.3f}, {check.attainable[1]:.3f}]"
            for check in family
        )
        findings.append(
            Finding(
                f"inert:{name}",
                f"{path}: {name!r} is inert in every view -- {where}. No assignment of labels "
                f"this design allows could push it outside [{SEPARABILITY_BAND[0]:.2f}, "
                f"{SEPARABILITY_BAND[1]:.2f}], so its pass says nothing about the corpus. "
                "Give the feature a view it can move in, or retire it; a check that cannot "
                "fail is a check that did not run.",
            )
        )
    return findings


def _check_leaks(checks: Sequence[Check], path: Path) -> list[Finding]:
    """The band itself: per feature on the turn, by count on the derived views.

    The asymmetry is measured, not aesthetic. Gating every view one feature at a
    time fails a corpus that carries nothing on one run in five; the counts and
    the derivation are on :data:`MIN_LEAKS_PER_VIEW`.

    **A derived view's finding is keyed on the whole leaking set**, so a fifth
    feature joining is a different finding and no baseline naming four can
    cover it. The same rule closes the other direction: dropping to three is
    also a different finding, which fails until the baseline is shrunk to match.
    Progress a baseline does not record is progress the baseline has stopped
    measuring.
    """
    low, high = SEPARABILITY_BAND
    findings = [
        Finding(
            f"leak:{GATED_VIEW}:{check.feature}",
            f"{path}: {check.feature!r} alone separates the labels at AUC {check.auc:.3f}, "
            f"outside [{low:.2f}, {high:.2f}] (per band: {check.describe_bands()}). "
            "A corpus a single feature solves measures that feature.",
        )
        for check in checks
        if check.view == GATED_VIEW and check.leaks
    ]
    for view in VIEWS:
        if view == GATED_VIEW:
            continue
        leaking = [check for check in checks if check.view == view and check.leaks]
        if len(leaking) < MIN_LEAKS_PER_VIEW:
            continue
        detail = "; ".join(
            f"{check.feature} {check.auc:.3f} ({check.describe_bands()})" for check in leaking
        )
        findings.append(
            Finding(
                f"leak:{view}:{','.join(sorted(check.feature for check in leaking))}",
                f"{path}: {len(leaking)} features separate the labels on the {view!r} view, "
                f"outside [{low:.2f}, {high:.2f}] -- {detail}. A corpus carrying no signal "
                f"reaches {MIN_LEAKS_PER_VIEW} on this view about 2% of the time, so this is "
                "the closing text giving the label away while the whole turn looks clean.",
            )
        )
    return findings


#: Corpus findings that are on the record and deferred, one per line.
#:
#: Same file format and the same semantics as ``paper/citations-baseline.txt``
#: and ``results/provenance-baseline.txt``: exempt, **and it may only shrink**.
CORPUS_BASELINE_PATH: Final = "datasets/triggers/corpus-baseline.txt"


def load_corpus_baseline(repo_root: Path) -> set[str]:
    """Baselined finding keys, one per line, ``#`` for comments.

    Keys are ``<corpus path>|<finding key>`` -- scoped to the corpus, because
    ``inert:paste_cues`` is a different fact about a different set and a
    repository-wide key would exempt a corpus nobody has looked at yet.
    """
    path = repo_root / CORPUS_BASELINE_PATH
    if not path.is_file():
        return set()
    return {
        stripped
        for line in path.read_text(encoding="utf-8").splitlines()
        if (stripped := line.split("#", 1)[0].strip())
    }


def apply_corpus_baseline(
    findings: Sequence[tuple[str, Finding]], baseline: set[str]
) -> tuple[list[str], list[str]]:
    """Split findings into what fails the build and what is merely on the record.

    Returns ``(issues, deferred)``. ``issues`` is everything the baseline does
    not name, **plus a refusal for every baseline entry that no longer matches
    a real finding** -- without which a baseline is a place defects go to be
    forgotten, which is the sentence ``citations.py`` already had to write.

    ``deferred`` is printed on every run rather than swallowed. A reader who
    sees a green gate must still see that two findings are open; a build that
    says nothing has told them the corpus is clean, and it is not.
    """
    seen = {f"{scope}|{finding.key}" for scope, finding in findings if finding.key}
    issues = [
        finding.message
        for scope, finding in findings
        if not finding.key or f"{scope}|{finding.key}" not in baseline
    ]
    issues += [
        f"{CORPUS_BASELINE_PATH}: {entry!r} is baselined but matches no current finding. "
        "Delete the line -- a baseline that does not shrink when work is done stops "
        "measuring anything, and a finding that changed shape is a new finding."
        for entry in sorted(baseline - seen)
    ]
    deferred = [
        finding.message
        for scope, finding in findings
        if finding.key and f"{scope}|{finding.key}" in baseline
    ]
    return issues, deferred


def _check_matched(checks: Sequence[Check], path: Path) -> list[Finding]:
    """Is the positive systematically top or bottom of its own triple?

    **Per feature rather than by count, and that is the point of it.** The
    pooled gates are count gates because a fixed band at their sample size is a
    coin flip one feature at a time. This one is not: its null spread is known
    in closed form, so the threshold can be a z, and the defects it exists for
    show up as *one* feature strongly skewed rather than three weakly. Counting
    would have averaged away the only signal there was.

    The class, not the instance. A spec that fixes any ask property in one
    direction -- shortest closing, longest closing, most first-person, least
    clipped opener -- puts the positive at a predictable rank inside its own
    triple, and this reads that rank whatever property is being ranked.
    """
    findings = []
    for check in checks:
        if check.matched_leaks:
            direction = "above" if check.matched > 0.5 else "below"
            findings.append(
                Finding(
                    f"matched:{check.view}:{check.feature}",
                    f"{path}: within its own triple, the positive's {check.feature!r} on the "
                    f"{check.view!r} view sits {direction} its two negatives in "
                    f"{check.matched:.3f} of comparisons -- {check.matched_z:.2f} null "
                    f"standard errors from chance, above {MATCHED_Z} (per band: "
                    f"{check.describe_matched_bands()}; pooled AUC {check.auc:.3f}). "
                    "The matched comparisons are the ones this design controls, and a rank "
                    "the positive holds inside its own triple is learnable without the body.",
                )
            )
        elif check.cancels:
            findings.append(
                Finding(
                    f"cancel:{check.view}:{check.feature}",
                    f"{path}: {check.feature!r} on the {check.view!r} view puts the positive "
                    f"at an extreme of its own triple far more often than chance "
                    f"({check.dispersion_z:.2f} null standard errors, above {MATCHED_Z}) "
                    f"while the average says nothing -- matched {check.matched:.3f}, pooled "
                    f"AUC {check.auc:.3f}. Per band: {check.describe_matched_bands()}. "
                    "That is two rulers pointing opposite ways, which is what a pooled "
                    "number near 0.5 looks like on a banded corpus.",
                )
            )
    return findings


def majority_baseline(trigger_set: TriggerSet) -> float:
    """Accuracy of always guessing the commoner label.

    The number every other accuracy in a trigger report should be read against,
    and it is not 0.5. At two negatives per positive, "never fire" scores 0.667
    while looking like a model that has learnt caution.
    """
    positives = len(trigger_set.positives)
    total = len(trigger_set.cases)
    return max(positives, total - positives) / total if total else 0.0
