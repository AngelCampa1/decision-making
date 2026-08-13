"""Trigger quality, measured separately from task accuracy.

Skill *availability* is the dominant term in whether a skill helps — +18 to
+36pp in SkillsBench, against +0.7pp from prose polish with intervals crossing
zero. Availability is decided by the description firing at the right moments,
which is a different quantity from whether the skill helps once it fires, and
mixing them would hide the tradeoff between them.

The number that matters in daily use is **precision**. A suite that lifts
accuracy 10pp while firing on 60% of ordinary turns is a net loss to whoever
installed it, and an accuracy-only evaluation reports that as a win. So both are
reported, neither is blended into a single score, and the negative set is built
from turns that *look* like triggers rather than from turns that obviously are
not — precision against easy negatives is free and means nothing.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from decision_evals.skills import parse_skill
from decision_evals.unbundle import UnbundleError, router_rows

#: The four procedures the shipped router offers. The default whitelist for
#: :func:`decision`; an M5 arm overrides it with its own entry names.
PROCEDURES: Final = ("ledger", "fit", "cascade", "timing")


def routing_is_by_name(offered: Iterable[str]) -> bool:
    """Whether exact-name routing accuracy means anything for this arm.

    :func:`evaluate_routing` compares the tool the model named against the
    labelled procedure, string against string. That is a routing measure only
    when the arm *offers* the procedure names. An M5 arm at n=2 offers
    ``ledger-fit`` and ``cascade-timing``, so no answer can match and the report
    reads ``accuracy 0.000`` — not because routing failed but because nothing
    could have counted.

    This is the parser whitelist defect one layer out. On 2026-08-12 that bug
    discarded the offered names on the way *in* and voided 365 calls; this one
    grades them on the way *out* against names the arm never offered. Both
    produce a clean run and a zero. The outcome that survives a changing entry
    count is ``covers`` — did the named entry contain the labelled procedure —
    and its chance level moves with ``n``, so it is not comparable across arms.
    """
    return all(name in PROCEDURES for name in offered)


#: How separable a trigger set may be by turn length alone.
#:
#: The long-context plan set this gate at 0.70 for padding documents and never
#: applied it to the trigger set. On 2026-08-13, prompted by the observation
#: that real users write paragraphs, it was applied for the first time: the
#: shipped set scores **0.85**, and a bare word-count threshold at 18 words
#: classifies it at **0.890 accuracy with no model involved**.
#:
#: That does not invalidate the arm comparisons — every arm saw the same set —
#: but it caps what any of them could have shown. The best arm measured 0.956,
#: so **the whole movable range above a ruler is about six points**, and five
#: manipulations finding nothing is exactly what a ceiling looks like.
MAX_LENGTH_SEPARABILITY: Final = 0.70


def length_separability(trigger_set: TriggerSet) -> float:
    """How well turn length alone separates positives from negatives, as an AUC.

    0.5 means length carries no signal. 1.0 means a ruler solves the set.

    This is the concordance form of the Mann-Whitney statistic — the share of
    positive/negative pairs the positive is longer in, with ties at a half —
    computed directly rather than pulled from scikit-learn, which is not a
    dependency here and must not become one for a five-line rank statistic.
    """
    positives = [len(case.turn.split()) for case in trigger_set.positives]
    negatives = [len(case.turn.split()) for case in trigger_set.negatives]
    if not positives or not negatives:
        return 0.5
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


@dataclass(frozen=True)
class TriggerCase:
    """One turn, and whether the skill should fire on it.

    Attributes:
        routes: Which procedures inside the skill this turn may select. Empty
            where the skill's own router is genuinely open. A secondary label:
            firing at all is the primary quantity, and a report giving routing
            accuracy without precision has answered the easier question. Open
            cases are *excluded* from routing accuracy rather than guessed at,
            because a forced label on an ambiguous turn measures the author's
            taste.

            **More than one route is allowed, and that is a 2026-08-13 decision
            by the maintainer rather than a convenience.** Three of the fourteen
            labelled turns had a second defensible route, and scoring it as a
            fault measured the answer key. The rule attached to the decision is
            that a second route needs a written sentence defending it, in
            ``why``, and that the whole set is reviewed at once — not only the
            turns that failed.
    """

    id: str
    turn: str
    should_fire: bool
    why: str
    routes: tuple[str, ...] = ()
    #: Which length band this turn was authored into. ``None`` in version 2 and
    #: earlier, where every turn was under 25 words and there was nothing to
    #: band. See :mod:`decision_evals.corpus`.
    band: str | None = None
    #: The matched triple this turn belongs to: one positive and two negatives
    #: of the same length, sharing a body in the long bands. **This is the
    #: resampling cluster**, not the item -- three turns built from one body are
    #: correlated, and a per-item bootstrap over them gives standard errors that
    #: are wrong in the anti-conservative direction.
    triple: str | None = None
    #: What the decision is about. The corpus was overwhelmingly technical and
    #: work-shaped through version 2, and the founding brief for this repository
    #: is life decisions. Whether firing differs by subject is a hypothesis the
    #: set is now built to answer rather than a property it happens to have.
    domain: str | None = None
    #: ``high`` or ``low``. Track L7 made stakes the opener's criterion without
    #: the corpus ever labelling stakes, so the claim could not be checked.
    stakes: str | None = None
    #: How the decision is asked for: ``explicit`` ("should I ...?"),
    #: ``implicit`` (no question at all), or ``embedded`` (the question sits
    #: mid-paragraph). Version 2 was saturated with the explicit form.
    ask: str | None = None
    #: For negatives only: which kind of non-decision this is. Lets precision be
    #: read per kind instead of as one pooled number that hides which negatives
    #: were free.
    kind: str | None = None

    @property
    def route(self) -> str | None:
        """The first acceptable route, or ``None`` where the router is open.

        Kept because reports and confusion tables want one name to print. It is
        **not** the scoring rule: :func:`evaluate_routing` accepts any member of
        ``routes``.
        """
        return self.routes[0] if self.routes else None


@dataclass(frozen=True)
class TriggerSet:
    """The positive and negative cases for one skill.

    Attributes:
        version: Which revision of the labels these cases are. **Runs made
            against different versions are not comparable.** On 2026-08-13 one
            turn moved from the positives to the negatives, and recall rose by
            3 to 5 points on every arm already on disk without a single call
            being re-made. A label change is a silent effect of exactly the kind
            this repository keeps catching after the fact, so the version is
            written into every record and checked at comparison time.
    """

    skill: str
    cases: tuple[TriggerCase, ...]
    version: int = 1
    length_separability_ceiling: float | None = None

    @property
    def positives(self) -> tuple[TriggerCase, ...]:
        return tuple(case for case in self.cases if case.should_fire)

    @property
    def negatives(self) -> tuple[TriggerCase, ...]:
        return tuple(case for case in self.cases if not case.should_fire)


class TriggerSetError(ValueError):
    """The trigger set is missing or malformed."""


@dataclass(frozen=True)
class TriggerReport:
    """Firing behaviour over a trigger set.

    Precision and recall are kept apart deliberately. There is no F-score here:
    a single blended number would let a description trade away the property that
    actually degrades daily use.
    """

    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    fired_on: tuple[str, ...]
    missed: tuple[str, ...]

    @property
    def precision(self) -> float:
        fired = self.true_positives + self.false_positives
        return self.true_positives / fired if fired else 0.0

    @property
    def recall(self) -> float:
        actual = self.true_positives + self.false_negatives
        return self.true_positives / actual if actual else 0.0

    @property
    def false_positive_rate(self) -> float:
        """Share of ordinary turns the skill interrupts. The daily-use cost."""
        negatives = self.true_negatives + self.false_positives
        return self.false_positives / negatives if negatives else 0.0


def load_trigger_set(path: Path) -> TriggerSet:
    """Load a trigger set from YAML."""
    raw = _read_yaml(path)
    if not isinstance(raw, dict) or "skill" not in raw:
        raise TriggerSetError(f"{path}: expected a mapping with a `skill` key")

    # A set may be split across files. 120 items whose longest bodies run to
    # 1,500 words is not reviewable as one document, and a corpus nobody reads
    # is a corpus nobody checks. `includes` keeps the entry point at the path
    # every caller already uses while the cases live one file per length band.
    entries: dict[str, list[object]] = {"positive": [], "negative": []}
    for key in entries:
        entries[key].extend(raw.get(key) or [])
    for relative in raw.get("includes") or []:
        included = _read_yaml(path.parent / str(relative))
        if not isinstance(included, dict):
            raise TriggerSetError(f"{path}: include {relative!r} is not a mapping")
        for key in entries:
            entries[key].extend(included.get(key) or [])

    cases: list[TriggerCase] = []
    for should_fire, key in ((True, "positive"), (False, "negative")):
        for entry in entries[key]:
            if not isinstance(entry, dict) or not {"id", "turn", "why"} <= set(entry):
                raise TriggerSetError(f"{path}: malformed {key} case {entry!r}")
            route = entry.get("route")
            if route is not None and not should_fire:
                raise TriggerSetError(
                    f"{path}: negative case {entry['id']!r} carries route {route!r}. A turn "
                    "the skill should not fire on has no procedure to route to, and a route "
                    "here would be counted as a routing decision that never happens."
                )
            # A scalar and a list both work, so the older one-route form keeps
            # loading unchanged and a second route is an addition rather than a
            # migration of every case.
            if route is None:
                routes: tuple[str, ...] = ()
            elif isinstance(route, str):
                routes = (route,)
            elif isinstance(route, list) and route:
                routes = tuple(str(name) for name in route)
                if len(set(routes)) != len(routes):
                    raise TriggerSetError(
                        f"{path}: case {entry['id']!r} lists a route twice: {routes!r}"
                    )
            else:
                raise TriggerSetError(
                    f"{path}: case {entry['id']!r} has route {route!r}. Give one procedure "
                    "name, or a non-empty list of them, or omit the key."
                )
            kind = entry.get("kind")
            if kind is not None and should_fire:
                raise TriggerSetError(
                    f"{path}: positive case {entry['id']!r} carries kind {kind!r}. `kind` "
                    "names which sort of non-decision a negative is and has no meaning on a "
                    "turn the skill should fire on."
                )
            cases.append(
                TriggerCase(
                    id=str(entry["id"]),
                    turn=str(entry["turn"]),
                    should_fire=should_fire,
                    why=str(entry["why"]),
                    routes=routes,
                    band=_optional_str(entry, "band"),
                    triple=_optional_str(entry, "triple"),
                    domain=_optional_str(entry, "domain"),
                    stakes=_optional_str(entry, "stakes"),
                    ask=_optional_str(entry, "ask"),
                    kind=_optional_str(entry, "kind"),
                )
            )
    if not cases:
        raise TriggerSetError(f"{path}: no cases")

    ids = [case.id for case in cases]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise TriggerSetError(f"{path}: duplicate case ids {duplicates}")
    ceiling = raw.get("length_separability_ceiling")
    return TriggerSet(
        skill=str(raw["skill"]),
        cases=tuple(cases),
        version=int(raw.get("version", 1)),
        length_separability_ceiling=None if ceiling is None else float(ceiling),
    )


def _read_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TriggerSetError(f"{path}: {exc}") from exc


def _optional_str(entry: dict[str, object], key: str) -> str | None:
    """A stratum label, or ``None`` where the set predates strata.

    Deliberately permissive about *which* label: the vocabularies live in
    :mod:`decision_evals.corpus` and are checked there, so a typo is reported
    once with the whole set's shape rather than raised at load and hiding every
    later problem behind the first one.
    """
    value = entry.get(key)
    return None if value is None else str(value)


def evaluate(trigger_set: TriggerSet, fires: Callable[[str], bool]) -> TriggerReport:
    """Score a firing decision function over a trigger set.

    ``fires`` is injected rather than constructed here, so the same report can
    describe a real model deciding from the description or a stub in a test.
    """
    return _report(trigger_set.cases, fires)


def _report(cases: Sequence[TriggerCase], fires: Callable[[str], bool]) -> TriggerReport:
    tp = fp = tn = fn = 0
    fired_on: list[str] = []
    missed: list[str] = []
    for case in cases:
        fired = fires(case.turn)
        if fired:
            fired_on.append(case.id)
        if case.should_fire and fired:
            tp += 1
        elif case.should_fire:
            fn += 1
            missed.append(case.id)
        elif fired:
            fp += 1
        else:
            tn += 1
    return TriggerReport(
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        fired_on=tuple(fired_on),
        missed=tuple(missed),
    )


#: Where trigger sets live, one YAML per skill, named for the skill.
TRIGGERS_DIR: Final = "datasets/triggers"


@dataclass(frozen=True)
class RoutingReport:
    """Which procedure the skill picked, over the cases that declare one.

    Reported *beside* a :class:`TriggerReport` and never instead of it. Routing
    accuracy answers "given that it fired, did it read the right file", which is
    the easier question; a suite that routes perfectly and fires on every
    ordinary turn is still a net loss in daily use.

    Attributes:
        unlabelled: Positive cases carrying ``route: ~``. Excluded rather than
            guessed: forcing a label onto a turn where the skill's own router is
            open would measure the set author's taste.
    """

    correct: int
    incorrect: int
    unlabelled: int
    confusions: tuple[tuple[str, str, str], ...] = ()

    @property
    def n_scored(self) -> int:
        return self.correct + self.incorrect

    @property
    def accuracy(self) -> float:
        return self.correct / self.n_scored if self.n_scored else 0.0


def evaluate_routing(trigger_set: TriggerSet, route: Callable[[str], str | None]) -> RoutingReport:
    """Score a routing decision function over the positives that declare a route.

    ``route`` is injected for the same reason ``fires`` is: the same report has
    to describe a real model choosing from the skill's table and a stub in a
    test.
    """
    correct = incorrect = unlabelled = 0
    confusions: list[tuple[str, str, str]] = []
    for case in trigger_set.positives:
        if not case.routes:
            unlabelled += 1
            continue
        chosen = route(case.turn)
        # Any declared route counts. A turn with two defensible procedures is
        # easier to hit than a turn with one, and the accuracy is not comparable
        # against a run made before this rule -- which is why the rule was
        # applied to the whole set at once rather than to the turns that failed.
        if chosen is not None and chosen in case.routes:
            correct += 1
        else:
            incorrect += 1
            confusions.append((case.id, " or ".join(case.routes), chosen or "(none)"))
    return RoutingReport(
        correct=correct,
        incorrect=incorrect,
        unlabelled=unlabelled,
        confusions=tuple(confusions),
    )


def check_trigger_sets(repo_root: Path) -> list[str]:
    """Every skill has a trigger set, and every trigger set names a real skill.

    This exists because neither held. ``datasets/triggers/evidence-ledger.yaml``
    named a skill that stopped existing when the four procedures were
    consolidated behind one router on 2026-08-11, and the shipped skill had no
    trigger set at all. Nothing noticed for a day, because
    :func:`load_trigger_set` was not called by anything -- the machinery was
    written, tested to 100%, and wired to nothing.

    A dataset that describes a skill which no longer exists is worse than a
    missing one: it reports a measurement of something that is not shipping.
    """
    issues: list[str] = []
    skills_dir = repo_root / "skills"
    triggers_dir = repo_root / TRIGGERS_DIR

    skills = {path.parent.name for path in skills_dir.glob("*/SKILL.md")}
    sets = {path.stem: path for path in triggers_dir.glob("*.yaml")}

    for name in sorted(skills - set(sets)):
        issues.append(f"skill {name!r} has no trigger set at {TRIGGERS_DIR}/{name}.yaml")
    for name in sorted(set(sets) - skills):
        issues.append(
            f"{TRIGGERS_DIR}/{name}.yaml names skill {name!r}, which is not in skills/. "
            "A trigger set for a skill that does not exist reports a measurement of "
            "something that is not shipping."
        )
    for name, path in sorted(sets.items()):
        if name not in skills:
            continue
        try:
            trigger_set = load_trigger_set(path)
        except TriggerSetError as error:
            issues.append(str(error))
            continue
        if trigger_set.skill != name:
            issues.append(f"{path}: declares skill {trigger_set.skill!r} but is filed as {name!r}")
        if not trigger_set.negatives:
            issues.append(
                f"{path}: no negative cases. Precision cannot be measured without them, "
                "and precision is the number that decides whether a skill is worth "
                "having installed."
            )
        issues.extend(_check_separability(trigger_set, path))
        issues.extend(_check_routes(trigger_set, skills_dir / name / "SKILL.md", path))
        issues.extend(_check_corpus_rules(trigger_set, path))
    issues.extend(_check_drafts(triggers_dir, skills_dir, skills))
    return issues


def _check_corpus_rules(trigger_set: TriggerSet, path: Path) -> list[str]:
    # Imported here rather than at module scope: `corpus` reads TriggerSet from
    # this module, so a top-level import would close the cycle. The direction is
    # deliberate -- loading a set must not depend on the rules for building one.
    from decision_evals.corpus import check_corpus

    return check_corpus(trigger_set, path)


def _check_drafts(
    triggers_dir: Path, skills_dir: Path, skills: frozenset[str] | set[str]
) -> list[str]:
    """Hold a corpus under construction to the same rules as a live one.

    A version 3 corpus is a directory of band files, because 120 items whose
    longest bodies run to 1,500 words is not reviewable as one document. The
    scan above globs ``datasets/triggers/*.yaml`` and therefore could not see
    any of them: 120 authored turns and the entire shortcut battery sat outside
    the gate while ``de check`` reported green.

    That is the same failure as ``triggers`` at 100% coverage with no caller and
    ``prereg.py``'s refusals with no caller, and it is the one this repository
    keeps making. The difference this time is that it was found while the corpus
    was still being authored rather than after a number had been published from
    it, which is the only reason it costs nothing.

    A draft is checked and is deliberately **not** made live: the entry point
    every runner uses stays where it is until blind adjudication has run.
    """
    issues: list[str] = []
    for index in sorted(triggers_dir.glob("*/index.yaml")):
        try:
            draft = load_trigger_set(index)
        except TriggerSetError as error:
            issues.append(str(error))
            continue
        if draft.skill not in skills:
            issues.append(
                f"{index.relative_to(triggers_dir.parent.parent).as_posix()}: names skill "
                f"{draft.skill!r}, which is not in skills/. A corpus being built for a "
                "skill that does not exist is measuring something that will not ship."
            )
            continue
        issues.extend(_check_routes(draft, skills_dir / draft.skill / "SKILL.md", index))
        issues.extend(_check_corpus_rules(draft, index))
    return issues


def _check_separability(trigger_set: TriggerSet, path: Path) -> list[str]:
    """A ratchet on how much of the set a ruler can solve.

    The shipped set sits at 0.850 against a 0.70 target, found on 2026-08-13.
    Fixing it is a corpus job — roughly twenty long negatives and a few short
    positives — and a gate that fails every commit until then would be bypassed
    within the day, which is worse than no gate.

    So the threshold does **not** move. What the set declares instead is the
    value it is currently at, and the check fails if the real value goes
    *above* it. The set cannot get more separable by accident, improving it
    means lowering the declared number, and the distance from the target is
    printed on every run so nobody has to remember.

    Softening the gate to fit the data would have been the other option and it
    is the one this repository exists to avoid.
    """
    if any(case.band for case in trigger_set.cases):
        # A version 3 set is held to the two-sided band in `corpus`, which is
        # strictly stronger. Running the ratchet as well would let a set that
        # declared a ceiling in a previous life keep a weaker rule.
        return []
    actual = length_separability(trigger_set)
    ceiling = trigger_set.length_separability_ceiling
    if ceiling is None:
        return (
            []
            if actual <= MAX_LENGTH_SEPARABILITY
            else [
                f"{path}: turn length alone separates the labels at AUC {actual:.3f}, above "
                f"the {MAX_LENGTH_SEPARABILITY} target, and the set declares no ceiling. "
                "Add `length_separability_ceiling` with the current value and a reason, or "
                "add long negatives and short positives."
            ]
        )
    if actual > ceiling + 1e-9:
        return [
            f"{path}: turn length now separates the labels at AUC {actual:.3f}, above the "
            f"{ceiling:.3f} this set declared. The ratchet only turns down. New turns must "
            "not widen the length gap between the labels."
        ]
    return []


def _check_routes(trigger_set: TriggerSet, skill_path: Path, path: Path) -> list[str]:
    """Every declared route must name a procedure the skill's router table offers.

    Added 2026-08-12, after Tracks M4 and M5 made it load-bearing. Those arms are
    built by :func:`~decision_evals.unbundle.router_rows` reading the same table
    these labels point at, so a renamed procedure file would leave every routing
    label aimed at nothing **while every number kept computing** -- accuracy would
    simply fall, and it would look like a model result.

    A skill whose body carries no router table is not an error. Most skills will
    not have one; the check applies where there is something to check against.
    """
    try:
        rows = router_rows(parse_skill(skill_path).body)
    except (OSError, UnbundleError):
        return []
    known = {row.name for row in rows}
    return [
        f"{path}: case {case.id!r} routes to {name!r}, which is not a procedure in "
        f"{skill_path.parent.name}'s router table ({', '.join(sorted(known))}). "
        "A label pointing at a procedure that does not exist scores as a model failure."
        for case in trigger_set.cases
        for name in case.routes
        if name not in known
    ]


_JSON = re.compile(r"\{[^{}]*\}")


Verdict = tuple[bool | None, str | None, float | None]


def decision(text: str, allowed: tuple[str, ...] = PROCEDURES) -> Verdict:
    """Parse the verdict, returning ``(None, None, None)`` when format was ignored.

    Unparseable answers are counted and excluded rather than read as "did not
    fire". A model that will not answer in the format has told us about format
    compliance, and scoring that silence as a negative would flatter precision.

    ``p_fire`` is returned as ``None`` when absent or out of ``[0, 1]``, and its
    absence never invalidates the verdict: a run that asked for a probability and
    got a usable decision without one has produced a firing observation and no
    forecast, which is exactly what should be recorded.
    """
    match = _JSON.search(text)
    if not match:
        return None, None, None
    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError:
        return None, None, None
    fired = payload.get("fire")
    if not isinstance(fired, bool):
        return None, None, None
    # The four-skill arm names a tool where the one-entry arm names a procedure.
    # They are the same four strings and the same question, so they land in the
    # same column and the two arms stay comparable on one metric.
    procedure = payload.get("procedure", payload.get("tool"))
    raw = payload.get("p_fire")
    p_fire = float(raw) if isinstance(raw, int | float) and 0.0 <= raw <= 1.0 else None
    # ``allowed`` is a parameter because the offered names are not always the
    # four procedures. An M5 arm at n=2 offers ``ledger-fit`` and
    # ``cascade-timing``, and a hard-coded whitelist silently nulled all 365 of
    # them on 2026-08-12: the run finished clean, firing was unaffected, and
    # routing read 0.000 because every answer had been discarded rather than
    # because the model had failed.
    return fired, procedure if procedure in allowed else None, p_fire
