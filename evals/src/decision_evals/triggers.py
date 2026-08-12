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

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml


@dataclass(frozen=True)
class TriggerCase:
    """One turn, and whether the skill should fire on it.

    Attributes:
        route: Which procedure inside the skill this turn should select, or
            ``None`` where the skill's own router is genuinely open. A secondary
            label: firing at all is the primary quantity, and a report giving
            routing accuracy without precision has answered the easier question.
            ``None`` cases are *excluded* from routing accuracy rather than
            guessed at, because a forced label on an ambiguous turn measures the
            author's taste.
    """

    id: str
    turn: str
    should_fire: bool
    why: str
    route: str | None = None


@dataclass(frozen=True)
class TriggerSet:
    """The positive and negative cases for one skill."""

    skill: str
    cases: tuple[TriggerCase, ...]

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
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TriggerSetError(f"{path}: {exc}") from exc
    if not isinstance(raw, dict) or "skill" not in raw:
        raise TriggerSetError(f"{path}: expected a mapping with a `skill` key")

    cases: list[TriggerCase] = []
    for should_fire, key in ((True, "positive"), (False, "negative")):
        for entry in raw.get(key) or []:
            if not isinstance(entry, dict) or not {"id", "turn", "why"} <= set(entry):
                raise TriggerSetError(f"{path}: malformed {key} case {entry!r}")
            route = entry.get("route")
            if route is not None and not should_fire:
                raise TriggerSetError(
                    f"{path}: negative case {entry['id']!r} carries route {route!r}. A turn "
                    "the skill should not fire on has no procedure to route to, and a route "
                    "here would be counted as a routing decision that never happens."
                )
            cases.append(
                TriggerCase(
                    id=str(entry["id"]),
                    turn=str(entry["turn"]),
                    should_fire=should_fire,
                    why=str(entry["why"]),
                    route=None if route is None else str(route),
                )
            )
    if not cases:
        raise TriggerSetError(f"{path}: no cases")

    ids = [case.id for case in cases]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise TriggerSetError(f"{path}: duplicate case ids {duplicates}")
    return TriggerSet(skill=str(raw["skill"]), cases=tuple(cases))


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
        if case.route is None:
            unlabelled += 1
            continue
        chosen = route(case.turn)
        if chosen == case.route:
            correct += 1
        else:
            incorrect += 1
            confusions.append((case.id, case.route, chosen or "(none)"))
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
    return issues
