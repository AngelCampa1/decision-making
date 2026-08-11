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

import yaml


@dataclass(frozen=True)
class TriggerCase:
    """One turn, and whether the skill should fire on it."""

    id: str
    turn: str
    should_fire: bool
    why: str


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
            cases.append(
                TriggerCase(
                    id=str(entry["id"]),
                    turn=str(entry["turn"]),
                    should_fire=should_fire,
                    why=str(entry["why"]),
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
