"""Shortcut battery for the tailoring corpus (``datasets/tailoring/``).

**The finding that produced this module.** Track H's triplet design puts one
``governing`` fact and one ``matched`` (equal-salience, non-governing) fact into
otherwise-identical prompts, so a model has to read the fact rather than the
register it is written in. On the three triplets authored so far, a human
reader -- not a gate -- noticed that every governing insert names a penalty
attached to a status change (an event of default, a forfeiture, a coverage
exclusion) while every matched insert is procedural (a scope restriction, a
transfer restriction, a pre-authorisation requirement). That is a shortcut of
exactly the shape ``datasets/triggers/`` shipped once already -- see
``notebook/2026-08-13-the-corpus-is-89-percent-solved-by-counting-words.md``
-- and this corpus had no equivalent audit.

**Same instrument, different corpus.** :mod:`decision_evals.corpus` answers
"can a feature rank the positive against its negatives" for the trigger set.
Here the question is different: the two variants of a triplet differ from
``base`` by exactly one inserted sentence each, so the natural unit is the
**inserted delta**, not the whole prompt, and the comparison is paired within
a triplet rather than pooled against unrelated negatives. But the statistics
that answer both questions are the same statistics -- :func:`~decision_evals.
corpus.separability`, :func:`~decision_evals.corpus.matched_separability` and
its null standard error, :func:`~decision_evals.corpus.matched_dispersion_z`
-- because every one of them is already written generically over a
:class:`~decision_evals.triggers.TriggerSet` and a feature function, and takes
no trigger-specific assumption beyond "one positive, some negatives, grouped
into triples". A tailoring triplet has exactly one positive (the governing
delta) and one negative (the matched delta), which is a trigger triple with
``NEGATIVES_PER_POSITIVE = 1`` instead of 2 -- not a new shape. So this module
builds a synthetic :class:`~decision_evals.triggers.TriggerSet` out of the
derived deltas (governing arm scored ``should_fire=True``, matched arm scored
``should_fire=False``, ``triple`` set to the triplet id) and hands it to the
unmodified trigger-corpus functions, reusing :class:`~decision_evals.corpus.
Check` and the ``SEPARABILITY_BAND`` / ``MATCHED_Z`` conventions those
functions already carry rather than inventing a second battery style or a
second threshold.

**Derived, not declared.** The corpus files carry only ``prompt`` (the whole
document) and ``key`` (the answer key, which must never reach a model). There
is no ``delta:`` field, and adding one would be a corpus change needing a
``docs/DECISIONS.md`` entry for a fact the base file already implies. The base
arm is a sibling file in the same triplet, so the delta is recovered by
diffing ``base`` against ``governing`` and against ``matched`` -- see
:func:`extract_delta`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from decision_evals.corpus import (
    MATCHED_Z,
    SEPARABILITY_BAND,
    Check,
    Finding,
    attainable_auc,
    load_baseline_file,
    matched_attainable,
    matched_dispersion_z,
    matched_null_se,
    matched_separability,
    separability,
)
from decision_evals.triggers import TriggerCase, TriggerSet

#: Where the corpus and its manifest live.
TAILORING_DIR: Final = "datasets/tailoring"
INDEX_NAME: Final = "index.yaml"

#: The label this module gives the synthetic set. Not a real skill name --
#: nothing here is run through ``check_trigger_sets``, which is the check that
#: would reject a set naming a skill that does not exist in ``skills/``.
SET_LABEL: Final = "tailoring"

#: The corpus's baseline scope -- the identity a finding's key is combined
#: with to form a baseline entry (``<scope>|<key>``). One constant rather than
#: something derived from whatever ``Path`` a caller hands ``check_shortcuts``,
#: because there is exactly one index file for this corpus, unlike the trigger
#: corpus's one-file-per-skill layout that needs :func:`~decision_evals.
#: triggers._scope` to compute it per call.
CORPUS_SCOPE: Final = f"{TAILORING_DIR}/{INDEX_NAME}"

#: Same file format and the same may-only-shrink rule as
#: :data:`decision_evals.corpus.CORPUS_BASELINE_PATH`, for this corpus instead
#: of the trigger corpus's.
TAILORING_BASELINE_PATH: Final = "datasets/tailoring/corpus-baseline.txt"


def load_tailoring_baseline(repo_root: Path) -> set[str]:
    """Baselined tailoring-corpus finding keys, one per line, ``#`` for comments.

    Thin wrapper over :func:`decision_evals.corpus.load_baseline_file` for
    :data:`TAILORING_BASELINE_PATH`, mirroring
    :func:`decision_evals.corpus.load_corpus_baseline` for the trigger corpus.
    """
    return load_baseline_file(repo_root, TAILORING_BASELINE_PATH)


class TailoringSetError(ValueError):
    """The tailoring corpus is present but malformed in a way authoring must fix.

    Reserved for defects a triplet-level warning cannot express safely -- an
    unreadable or non-mapping ``index.yaml``. A malformed *triplet* (missing
    file, missing arm, bad YAML in one variant) is reported as a warning and
    that triplet is skipped instead, because the corpus is under active
    revision by another session as this module is written and a transient,
    single-triplet defect must not take the whole gate down with it.
    """


@dataclass(frozen=True)
class LoadResult:
    """What loading the corpus produced: the delta set, plus what was skipped.

    Attributes:
        trigger_set: The synthetic set, governing deltas positive, matched
            deltas negative, one triple per triplet id.
        warnings: One line per triplet that could not be loaded. Printed by
            the ``de check`` step whether or not the step passes, on the same
            principle as ``deferred_corpus_findings`` for the trigger corpus:
            a reader must be able to see that something was skipped, not only
            that the gate is green.
    """

    trigger_set: TriggerSet
    warnings: tuple[str, ...]


def extract_delta(base: str, variant: str) -> str:
    """The text inserted into ``variant`` relative to ``base``.

    ``variant`` is authored as ``base`` plus exactly one inserted bullet, so
    the shared prefix and shared suffix of the two strings bracket the
    insertion, and what neither can absorb is the delta. This is the same
    affix-scan idea as :func:`decision_evals.corpus._shared_body`, adapted
    from "recover what N members of a triple share" to "recover what one pair
    does not share" -- and it inherits that function's line-boundary lesson
    rather than repeating its bug: raw character-by-character affix matching
    can stop, or continue, mid-line by coincidence (a bullet marker, a shared
    word fragment), which either strands part of the neighbouring bullet
    inside the delta or eats part of the inserted one. The suffix is snapped
    forward to the next newline whenever it does not already start on a line
    boundary, which returns the stray fragment to the delta side; a stray
    leading bullet marker is stripped afterwards for the same reason.

    Requires ``len(base) <= len(variant)``, which holds by construction for
    every ``governing``/``matched`` file against its ``base`` sibling: the
    variant is the base plus an insertion, never a rewrite. Returns the
    stripped delta, or the full ``variant`` text if the two strings share no
    affix at all (a diagnostic degradation, not a silent wrong answer -- a
    battery run over a whole prompt instead of a delta reads far larger AUCs
    than one over a genuine six-line insertion, so a corpus authored outside
    the base-plus-one-bullet convention is loud rather than quiet about it).
    """
    limit = min(len(base), len(variant))
    prefix = 0
    while prefix < limit and base[prefix] == variant[prefix]:
        prefix += 1

    max_suffix = limit - prefix
    suffix = 0
    while (
        suffix < max_suffix and base[len(base) - 1 - suffix] == variant[len(variant) - 1 - suffix]
    ):
        suffix += 1

    boundary = len(variant) - suffix
    if suffix > 0 and boundary > prefix and variant[boundary - 1] != "\n":
        segment = variant[prefix:boundary]
        newline = segment.rfind("\n")
        if newline >= 0:
            suffix = len(variant) - (prefix + newline + 1)

    delta = variant[prefix : len(variant) - suffix].strip()
    return re.sub(r"^[-*]\s*", "", delta).strip()


def _load_variant(path: Path) -> tuple[str, str]:
    """``(arm, prompt)`` from one triplet-member file, or raise on any defect."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TailoringSetError(f"{path}: {exc}") from exc
    if not isinstance(raw, dict) or "arm" not in raw or "prompt" not in raw:
        raise TailoringSetError(f"{path}: expected a mapping with `arm` and `prompt`")
    return str(raw["arm"]), str(raw["prompt"])


def load_deltas(repo_root: Path) -> LoadResult:
    """Build the governing/matched delta set from ``datasets/tailoring/``.

    Returns an empty set, with no warnings, when ``index.yaml`` is absent or
    declares no triplets -- the corpus is 3 of a planned 20 triplets and under
    revision, and a shortcut battery with nothing to check is not a battery
    failure. Every other defect is reported as a warning and that triplet is
    skipped, per :class:`TailoringSetError`'s docstring.
    """
    tailoring_dir = repo_root / TAILORING_DIR
    index_path = tailoring_dir / INDEX_NAME
    if not index_path.is_file():
        return LoadResult(TriggerSet(skill=SET_LABEL, cases=()), ())

    try:
        raw = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TailoringSetError(f"{index_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise TailoringSetError(f"{index_path}: expected a mapping")

    warnings: list[str] = []
    cases: list[TriggerCase] = []
    for entry in raw.get("triplets") or []:
        result = _load_triplet(tailoring_dir, entry)
        if isinstance(result, str):
            warnings.append(result)
            continue
        cases.extend(result)
    return LoadResult(TriggerSet(skill=SET_LABEL, cases=tuple(cases)), tuple(warnings))


def _load_triplet(tailoring_dir: Path, entry: object) -> str | list[TriggerCase]:
    """One triplet's two cases, or the warning explaining why it has none."""
    if not isinstance(entry, dict) or "id" not in entry or "files" not in entry:
        return f"{tailoring_dir / INDEX_NAME}: malformed triplet entry {entry!r}, skipped"
    triplet_id = str(entry["id"])
    files = entry["files"]
    if not isinstance(files, list) or len(files) != 3:
        return f"triplet {triplet_id!r}: `files` is not a 3-element list, skipped"

    arms: dict[str, str] = {}
    for filename in files:
        path = tailoring_dir / str(filename)
        try:
            arm, prompt = _load_variant(path)
        except TailoringSetError as exc:
            return f"triplet {triplet_id!r}: {exc}, skipped"
        arms[arm] = prompt

    missing = {"base", "governing", "matched"} - set(arms)
    if missing:
        return f"triplet {triplet_id!r}: missing arm(s) {sorted(missing)}, skipped"

    base = arms["base"]
    return [
        TriggerCase(
            id=f"{triplet_id}-{arm}",
            turn=extract_delta(base, arms[arm]),
            should_fire=should_fire,
            why="derived: text inserted into the base prompt for this arm",
            triple=triplet_id,
        )
        for arm, should_fire in (("governing", True), ("matched", False))
    ]


_WORD: Final = re.compile(r"[A-Za-z']+")

#: A run of digits and thousands separators, with an optional decimal tail.
#: Counts "300,000" as one numeral and each of a date's three fields
#: separately -- ``has_date`` is the feature that reads a date as one unit.
_NUMERAL: Final = re.compile(r"\d[\d,]*(?:\.\d+)?")

_DATE: Final = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

#: Words for an outcome attached to a status change: a right lapsing, being
#: withheld, or being taken away once a condition is met.
#:
#: **What this can catch.** A delta that says the fact governs by naming its
#: own consequence in this vocabulary -- "forfeits", "breach ... default",
#: "excludes ... from cover" are all here as stems, not as the literal three
#: words from any one triplet. **What it cannot catch.** A governing fact
#: phrased without any consequence word at all ("the balance shown is net of
#: a $300,000 floor" -- true of h01's own base bullet) states the same
#: constraint with no verb this regex reads; a matched fact that happens to
#: use one of these words loosely also scores as if it were governing. It is
#: a lexical family, not a semantic parser, and it is reported as one
#: feature among several for exactly that reason -- the stump and the pooled
#: gate both make a single feature's False Positives on unseen items in a
#: matched fact only two of the shortcuts this instrument is built to weigh
#: as evidence, not to police them alone.
_PENALTY_CUES: Final = re.compile(
    r"\b(?:forfeit\w*|default\w*|breach\w*|exclud\w*|void\w*|terminat\w*|revok\w*|"
    r"rescind\w*|penal(?:t?y|ise\w*|ize\w*)|den(?:y|ies|ied)|ineligible\w*|lapse\w*|"
    r"los(?:e|es|t)|forgo\w*|cease\w*)\b",
    re.IGNORECASE,
)

#: Words for an administrative step: something to be requested, filed, or
#: cleared, with no stated penalty for skipping it.
#:
#: Shares the same catches-and-cannot-catch note as :data:`_PENALTY_CUES`: it
#: is a lexical family built from the corpus's authoring pattern ("restricts",
#: "requires pre-authorisation", "under a transfer restriction" are all here
#: as stems), not from those three literal phrases, and it will miss a
#: procedural fact phrased without any of these stems.
_PROCEDURAL_CUES: Final = re.compile(
    r"\b(?:requir\w*|restrict\w*|must|shall|submit\w*|obtain\w*|authoris\w*|"
    r"authoriz\w*|approv\w*|appl(?:y|ies|ied|ication\w*)|process\w*|notif\w*|"
    r"complet\w*|follow\w*|provide\w*|document\w*)\b",
    re.IGNORECASE,
)


def _penalty_lexicon_gap(text: str) -> float:
    """Penalty-family word count minus procedural-family word count.

    Positive when a delta leans on consequence vocabulary, negative when it
    leans on administrative vocabulary, zero when it uses neither or an equal
    count of both. Not normalised by delta length: the trigger battery's own
    counting features (``paste_cues``, ``question_marks``) are raw counts
    too, and these deltas are all short single-sentence insertions where a
    rate and a count carry the same ranking.
    """
    return float(len(_PENALTY_CUES.findall(text)) - len(_PROCEDURAL_CUES.findall(text)))


#: Every surface feature this battery tests, minimum set per the task brief:
#: delta length in characters and words, numeral count, date presence, and
#: the penalty-versus-procedural lexical family.
FEATURES: Final[dict[str, Callable[[str], float]]] = {
    "delta_char_count": lambda text: float(len(text)),
    "delta_word_count": lambda text: float(len(_WORD.findall(text))),
    "numeral_count": lambda text: float(len(_NUMERAL.findall(text))),
    "has_date": lambda text: float(bool(_DATE.search(text))),
    "penalty_lexicon_gap": _penalty_lexicon_gap,
}


def battery_report(trigger_set: TriggerSet) -> tuple[Check, ...]:
    """Every feature in :data:`FEATURES`, scored against the delta text directly.

    There is exactly one view here -- the delta -- where the trigger battery
    has four (``turn``, ``ask``, ``close``, ``open``), because the corpus
    files hand this module the substring the trigger corpus's view functions
    exist to recover. ``texts=None`` in every call below reads
    ``TriggerCase.turn``, which :func:`load_deltas` already set to the
    extracted delta.

    Reuses :class:`~decision_evals.corpus.Check` and the pooled/matched
    statistics unmodified -- ``Check.leaks``, ``Check.matched_leaks``,
    ``Check.cancels`` and ``Check.inert`` read :data:`~decision_evals.corpus.
    SEPARABILITY_BAND` and :data:`~decision_evals.corpus.MATCHED_Z` from
    :mod:`decision_evals.corpus`'s own module namespace regardless of which
    module constructed the ``Check``, so this function does not re-derive
    either threshold; it inherits them.
    """
    return tuple(
        Check(
            view="delta",
            feature=name,
            auc=separability(trigger_set, feature),
            attainable=attainable_auc(trigger_set, feature),
            per_band={},
            matched=matched_separability(trigger_set, feature),
            matched_attainable=matched_attainable(trigger_set, feature),
            matched_per_band={},
            null_se=matched_null_se(trigger_set, feature),
            dispersion_z=matched_dispersion_z(trigger_set, feature),
        )
        for name, feature in FEATURES.items()
    )


def inert_features(checks: tuple[Check, ...]) -> tuple[str, ...]:
    """Names of features no label assignment in this design could have failed.

    Reported rather than gated, the same treatment ``corpus._check_inert``
    gives the trigger battery: a feature that cannot move is not evidence the
    corpus is clean, and a reader needs to see it was never really tested.
    """
    return tuple(check.feature for check in checks if check.inert)


def check_shortcuts(trigger_set: TriggerSet, path: Path) -> list[Finding]:
    """Every shortcut this battery can see, as keyed :class:`~decision_evals.corpus.Finding`.

    Mirrors ``decision_evals.corpus._check_leaks`` and ``_check_matched``'s
    wording, structure **and key scheme**: the pooled statistic against
    :data:`~decision_evals.corpus.SEPARABILITY_BAND`, and the paired (matched)
    statistic against :data:`~decision_evals.corpus.MATCHED_Z` null standard
    errors. An empty ``trigger_set`` (no triplets loaded) produces no
    findings: every statistic below returns its chance value on no data, same
    as the trigger battery's own functions do.

    **The leak finding is combined across every leaking feature into one key,
    the same way ``_check_leaks`` keys a derived (non-``turn``) view rather
    than the gated one.** This corpus has exactly one view (``delta``, the
    inserted text -- see :func:`battery_report`), so there is no per-feature
    count gate to calibrate a threshold for; instead every feature that leaks
    at all is folded into a single ``leak:delta:<feature,feature,...>`` key,
    sorted and comma-joined. **That is what makes a baseline naming this
    finding safe rather than a blanket exemption**: the key names the whole
    set of features that went wrong, not any one of them or the corpus in
    general, so a fifth feature joining the set -- or a fourth dropping out --
    changes the key and the old baseline entry stops matching. See
    ``docs/DECISIONS.md`` and ``datasets/tailoring/corpus-baseline.txt`` for
    the entry this shipped with, and
    ``test_tailoring_battery.py::TestTheBaselineIsNarrowRatherThanBlanket``
    for the proof that a fifth feature is not deferred by a baseline naming
    four.

    The matched finding is left per-feature (``matched:delta:<feature>``),
    matching ``_check_matched``'s treatment of every view: its threshold is
    already a per-feature z rather than a count, so there is nothing to
    combine.

    **``Check.cancels`` is deliberately not read here, and that omission is
    itself checked rather than assumed.** ``matched_dispersion_z`` answers "is
    the positive's rank more extreme across its triple than chance", which is
    only a live question when a triple has more than two members to be
    extreme *among* -- the trigger corpus's one positive against two
    negatives. A tailoring triplet is one governing delta against exactly one
    matched delta, so ``_candidate_scores`` always hands back a two-element
    pair that sums to 1.0, both candidates carry the identical squared
    deviation from 0.5, and the observed statistic is always one of those two
    candidates. The excess-dispersion statistic is therefore identically
    ``0.0`` for every feature on every triplet this corpus can ever contain --
    confirmed on the real corpus and left as
    ``test_tailoring_battery.py::TestDispersionIsStructurallyInert`` rather
    than trusted from this paragraph. Gating on a statistic that cannot move
    is exactly the defect ``CLAUDE.md`` names: "an estimator that cannot
    return a non-zero value is not a measurement, and it does not announce
    itself" -- so the check is left out rather than shipped inert. If a future
    revision of the corpus design allows more than one matched fact per
    triplet, this reasoning stops holding and the check belongs back in.
    """
    findings: list[Finding] = []
    checks = battery_report(trigger_set)
    low, high = SEPARABILITY_BAND

    leaking = [check for check in checks if check.leaks]
    if leaking:
        detail = "; ".join(f"{check.feature} {check.auc:.3f}" for check in leaking)
        findings.append(
            Finding(
                f"leak:delta:{','.join(sorted(check.feature for check in leaking))}",
                f"{path}: {len(leaking)} feature(s) separate governing deltas from matched "
                f"deltas alone, outside [{low:.2f}, {high:.2f}] -- {detail}. A corpus a "
                "surface feature solves measures that feature, not the domain reasoning "
                "the triplet is meant to test.",
            )
        )

    for check in checks:
        if check.matched_leaks:
            direction = "above" if check.matched > 0.5 else "below"
            findings.append(
                Finding(
                    f"matched:delta:{check.feature}",
                    f"{path}: within its own triplet, the governing delta's {check.feature!r} "
                    f"sits {direction} the matched delta's in {check.matched:.3f} of "
                    f"comparisons -- {check.matched_z:.2f} null standard errors from chance, "
                    f"above {MATCHED_Z} (pooled AUC {check.auc:.3f}). A model can tell "
                    "governing from matched on this feature alone, whatever the underlying "
                    "reasoning.",
                )
            )
    return findings
