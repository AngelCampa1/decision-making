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
from collections import Counter
from collections.abc import Callable, Sequence
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
}


def separability(trigger_set: TriggerSet, feature: Callable[[str], float]) -> float:
    """How well one feature alone separates positives from negatives, as an AUC.

    0.5 means the feature carries no signal. 1.0 means it solves the set and
    **0.0 means it solves the set backwards**, which is the same defect.

    This is the concordance form of the Mann-Whitney statistic -- the share of
    positive/negative pairs the positive scores higher in, with ties at a half --
    computed directly rather than pulled from scikit-learn, which is not a
    dependency here and must not become one for a five-line rank statistic.
    """
    positives = [feature(case.turn) for case in trigger_set.positives]
    negatives = [feature(case.turn) for case in trigger_set.negatives]
    if not positives or not negatives:
        return 0.5
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def separability_report(trigger_set: TriggerSet) -> dict[str, float]:
    """Every feature in the battery against the set, worst first."""
    scored = {name: separability(trigger_set, fn) for name, fn in FEATURES.items()}
    return dict(sorted(scored.items(), key=lambda item: -abs(item[1] - 0.5)))


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


def _band_of(case: TriggerCase) -> str | None:
    return case.band


def check_corpus(trigger_set: TriggerSet, path: Path) -> list[str]:
    """Every structural rule version 3 is built on, checked rather than intended.

    Returns an empty list for a set that predates the strata (version 2 and
    earlier declare no ``band``), because those sets are archived rather than
    fixed and re-checking them would only produce noise nobody can act on.
    """
    if not any(case.band for case in trigger_set.cases):
        return []
    return [
        *_check_vocabularies(trigger_set, path),
        *_check_bands(trigger_set, path),
        *_check_triples(trigger_set, path),
        *_check_ratio(trigger_set, path),
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


def _check_shortcuts(trigger_set: TriggerSet, path: Path) -> list[str]:
    low, high = SEPARABILITY_BAND
    issues = [
        f"{path}: {name!r} alone separates the labels at AUC {score:.3f}, outside "
        f"[{low:.2f}, {high:.2f}]. A corpus a single feature solves measures that feature."
        for name, score in separability_report(trigger_set).items()
        if not low <= score <= high
    ]
    stump = stump_accuracy(trigger_set)
    baseline = majority_baseline(trigger_set)
    if stump - baseline > MAX_STUMP_LIFT + 1e-9:
        issues.append(
            f"{path}: a depth-2 stump over the feature battery reaches {stump:.3f} accuracy "
            f"against a majority-class baseline of {baseline:.3f} -- a lift of "
            f"{stump - baseline:.3f}, above {MAX_STUMP_LIFT}. Two questions about punctuation "
            "and word counts should not get most of the way to the answer."
        )
    return issues


def majority_baseline(trigger_set: TriggerSet) -> float:
    """Accuracy of always guessing the commoner label.

    The number every other accuracy in a trigger report should be read against,
    and it is not 0.5. At two negatives per positive, "never fire" scores 0.667
    while looking like a model that has learnt caution.
    """
    positives = len(trigger_set.positives)
    total = len(trigger_set.cases)
    return max(positives, total - positives) / total if total else 0.0
