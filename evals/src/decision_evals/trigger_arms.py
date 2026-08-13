"""Scoring a trigger arm, and comparing two of them.

Every arm run so far — M4, M5, M6, L5, the confidence run — was scored by an
ad-hoc script written fresh at the keyboard, and **that practice has voided two
runs and invalidated the interpretation of a third**:

- a parser whitelist discarded every tool name an n=2 arm could offer, so 365
  calls reported routing 0.000 with nothing having failed;
- a routing report graded those names against names the arm never offered,
  reading 0.000 again;
- ``covers`` was quoted without its denominator, and the two denominators differ
  by 15pp.

None of the three crashed. All three produced a full checkpoint and a plausible
number. The common cause is that the scoring lived in a shell one-liner where
nothing could test it, so this module exists to move it somewhere that can be.

**It computes and does not judge.** Nothing here decides an answer is wrong;
labels come from the trigger set and the records come from the runner.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

#: One checkpoint row, as the runner writes it.
Record = Mapping[str, Any]


class ArmError(ValueError):
    """A set of records that cannot be scored as an arm."""


@dataclass(frozen=True, slots=True)
class ArmSummary:
    """What one arm did on firing.

    Attributes:
        n_records: Rows scored, across all repeats.
        unparseable: Rows whose ``fired`` is null. Reported rather than dropped
            silently: a parse rate is a property of the arm.
        accuracy: Share of rows where ``fired == should_fire``.
        precision: True positives over all fires.
        recall: True positives over all positives.
        false_positive_rate: False fires over all negatives — the daily-use cost.
        missed: Positive case ids that never fired in any repeat.
    """

    n_records: int
    unparseable: int
    accuracy: float
    precision: float
    recall: float
    false_positive_rate: float
    missed: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CoversRates:
    """``covers`` under both of its denominators.

    M5 registered a band naming this measure and not what it divided by, and the
    two answers differed by 15pp. Both are returned so a caller cannot pick one
    by accident.

    Attributes:
        over_labelled: Every labelled call, a non-answer counting as a miss.
            **This is the reported figure**, because it is the denominator
            ``evaluate_routing`` uses for arms whose entry names are labels.
        over_answered: Only the calls that fired and named an entry.
        n_labelled: Denominator of ``over_labelled``.
        n_answered: Denominator of ``over_answered``.
        chance: One over the number of entries offered, when known.
    """

    over_labelled: float
    over_answered: float
    n_labelled: int
    n_answered: int
    chance: float | None


@dataclass(frozen=True, slots=True)
class ArmComparison:
    """Two arms on the same cases, paired per item.

    Pairing is on the **case id**, not on the row: two arms may carry different
    repeat counts, and a run at 2 repeats against one at 5 is a legitimate
    comparison of per-item rates whose resolution differs. Comparing rows
    positionally would silently pair a case with a different case.
    """

    n_shared: int
    n_differing: int
    favouring_a: int
    favouring_b: int
    p_value: float
    accuracy_a: float
    accuracy_b: float
    moved: tuple[tuple[str, float, float], ...]


def _fired(record: Record) -> bool | None:
    value = record.get("fired")
    if value is None:
        return None
    return bool(value)


def summarise(records: Iterable[Record]) -> ArmSummary:
    """Firing precision, recall and false-positive rate for one arm.

    Unparseable rows are excluded from every rate and counted separately. They
    are not scored as failures to fire: a row with no verdict is a missing
    measurement, and treating it as a decline would turn a format problem into a
    recall result.

    Raises:
        ArmError: on an empty arm, or one with no positives or no negatives —
            precision and the false-positive rate are undefined there, and
            returning 0.0 would look like a measurement.
    """
    rows = list(records)
    if not rows:
        raise ArmError("no records")
    unparseable = sum(1 for row in rows if _fired(row) is None)
    scored = [row for row in rows if _fired(row) is not None]
    if not scored:
        raise ArmError(f"all {len(rows)} record(s) unparseable")

    positives = [row for row in scored if row["should_fire"]]
    negatives = [row for row in scored if not row["should_fire"]]
    if not positives or not negatives:
        raise ArmError(
            f"an arm needs both labels to score: {len(positives)} positive, "
            f"{len(negatives)} negative"
        )

    true_positives = sum(1 for row in positives if _fired(row))
    false_positives = sum(1 for row in negatives if _fired(row))
    fires = true_positives + false_positives

    ever_fired = {row["case"] for row in positives if _fired(row)}
    missed = tuple(sorted({row["case"] for row in positives} - ever_fired))

    return ArmSummary(
        n_records=len(rows),
        unparseable=unparseable,
        accuracy=sum(1 for row in scored if _fired(row) == bool(row["should_fire"])) / len(scored),
        precision=true_positives / fires if fires else 0.0,
        recall=true_positives / len(positives),
        false_positive_rate=false_positives / len(negatives),
        missed=missed,
    )


def covers_rates(records: Iterable[Record], *, n_entries: int | None = None) -> CoversRates:
    """``covers`` over both denominators.

    **This is not a routing accuracy and must not be quoted as one across arms.**
    M6 ran the same four procedures at the same entry count under two partitions
    and read 0.743 and 0.857 — the model's answers were unchanged and the entry
    boundaries moved, so a different confusion was forgiven. The number is a
    property of the partition as much as of the model.

    Raises:
        ArmError: if no record carries a ``covers`` value, which means the arm
            had no labelled routes and the measure does not apply.
    """
    labelled = [row for row in records if row.get("covers") is not None]
    if not labelled:
        raise ArmError("no record carries `covers`; this arm has no labelled routes")
    answered = [row for row in labelled if _fired(row)]
    return CoversRates(
        over_labelled=sum(1 for row in labelled if row["covers"]) / len(labelled),
        over_answered=(
            sum(1 for row in answered if row["covers"]) / len(answered) if answered else 0.0
        ),
        n_labelled=len(labelled),
        n_answered=len(answered),
        chance=1 / n_entries if n_entries else None,
    )


def label_versions_comparable(a: Iterable[Record], b: Iterable[Record]) -> str | None:
    """Whether two arms were scored against the same revision of the labels.

    On 2026-08-13 one turn moved from the positives to the negatives. **Recall
    rose 3 to 5 points on every arm already on disk and not one call was
    re-made.** A label change is invisible in a checkpoint, survives every
    instrument check, and produces a clean improvement — which is the exact
    failure shape this repository has now caught four times.

    Records written before the version existed carry no ``set_version``. Those
    are treated as version 1, which is what they are, rather than as unknown:
    the alternative is a guard that never fires on the runs it was written for.
    """
    versions_a = {int(row.get("set_version", 1)) for row in a}
    versions_b = {int(row.get("set_version", 1)) for row in b}
    if len(versions_a | versions_b) <= 1:
        return None
    return (
        f"these arms were scored against different label revisions: "
        f"{sorted(versions_a)} against {sorted(versions_b)}. Moving one turn between "
        f"the positives and the negatives changes recall on both arms with no call "
        f"re-made, so the difference would not be a model result. Re-score the older "
        f"arm against the current set first."
    )


def models_comparable(a: Iterable[Record], b: Iterable[Record]) -> str | None:
    """Whether two arms were produced by the same model tier.

    Same defect as :func:`label_versions_comparable`, one axis over. ``--model``
    is a command-line argument with a default, it changes every number in the
    run, and until 2026-08-13 the tier survived only as prose in a hand-written
    README while the verdict records carried ``case``, ``fired``, ``route``,
    ``repeat`` and no model at all. A run made at a different tier is not a
    result about a skill description, and nothing in a checkpoint said which
    tier produced it.

    **An absent ``model`` is unknown, not a default, and that is the difference
    from the label guard.** There, a record written before versioning genuinely
    *was* version 1, so defaulting told the truth. Here the tier could have been
    overridden on the command line and the record would look identical, so
    filling in ``haiku`` would be inventing a parameter — standing rule 1, and
    the rule exists because an invented figure is indistinguishable from a
    measured one three days later.

    So the three cases are decided separately:

    * **both unstamped** — allowed. Two records written before the stamp existed
      are exactly as comparable as they were yesterday; the guard knows nothing
      about them and pretends to know nothing. Refusing here would retroactively
      void every comparison already published, on no evidence.
    * **one stamped, one not** — refused. This is the transition where the risk
      is real: a new run whose tier is recorded, against an old one whose tier
      is a claim in prose.
    * **both stamped and different** — refused.
    """
    models_a = {row.get("model") for row in a}
    models_b = {row.get("model") for row in b}
    seen = models_a | models_b
    if seen <= {None} or len(seen) <= 1:
        return None
    named = sorted(str(model) for model in seen if model is not None)
    if None in seen:
        return (
            f"one of these arms records the model it ran on ({', '.join(named)}) and the "
            "other does not. An unstamped record does not mean the default tier -- "
            "`--model` could have been passed and the record would look the same -- so "
            "the two cannot be shown to have run on the same model, and a tier change "
            "moves every number in the run."
        )
    return (
        f"these arms ran on different models: {sorted(models_a, key=str)} against "
        f"{sorted(models_b, key=str)}. `--model` changes every number in a run, so the "
        "difference between them would not be a result about the description."
    )


def per_item_correctness(records: Iterable[Record]) -> dict[str, float]:
    """Per case id, the share of repeats where the arm's verdict matched its label.

    Unparseable rows are dropped, so a case whose every repeat failed to parse
    is absent rather than zero.
    """
    tallies: dict[str, list[int]] = {}
    for row in records:
        fired = _fired(row)
        if fired is None:
            continue
        tallies.setdefault(str(row["case"]), []).append(int(fired == bool(row["should_fire"])))
    return {case: sum(hits) / len(hits) for case, hits in tallies.items()}


def compare(a: Iterable[Record], b: Iterable[Record]) -> ArmComparison:
    """Two arms, paired on case id, tested on per-item correctness rates.

    **The estimator is the paired Wilcoxon signed-rank test over per-item
    correctness rates, with ``zero_method="wilcox"``, because that is what M4,
    M5, M6 and L5 each registered before their runs.** Substituting a different
    test here — exact McNemar on majority verdicts is the obvious candidate and
    is arguably better behaved — would silently stop reproducing four published
    numbers. Changing it is a decision that belongs in a notebook entry, not in
    a refactor.

    Pairing is on the **case id**. Rows are not paired positionally: two arms may
    carry different repeat counts, and position would pair a case with a
    different case.

    Raises:
        ArmError: if the two arms share no case ids.
    """
    from scipy.stats import wilcoxon

    rows_a, rows_b = list(a), list(b)
    if (reason := label_versions_comparable(rows_a, rows_b)) is not None:
        raise ArmError(reason)
    if (reason := models_comparable(rows_a, rows_b)) is not None:
        raise ArmError(reason)

    left, right = per_item_correctness(rows_a), per_item_correctness(rows_b)
    shared = sorted(set(left) & set(right))
    if not shared:
        raise ArmError("the two arms share no case ids")

    rates_a = [left[case] for case in shared]
    rates_b = [right[case] for case in shared]
    moved = tuple((case, left[case], right[case]) for case in shared if left[case] != right[case])

    # Every item identical means no discordance and nothing to test. `wilcoxon`
    # raises on an all-zero difference vector rather than returning 1.0, and an
    # arm compared against itself is a thing scripts do.
    p_value = float(wilcoxon(rates_a, rates_b, zero_method="wilcox").pvalue) if moved else 1.0

    return ArmComparison(
        n_shared=len(shared),
        n_differing=len(moved),
        favouring_a=sum(1 for _, x, y in moved if x > y),
        favouring_b=sum(1 for _, x, y in moved if y > x),
        p_value=p_value,
        accuracy_a=sum(rates_a) / len(shared),
        accuracy_b=sum(rates_b) / len(shared),
        moved=moved,
    )


def load_arm(path: Any) -> list[dict[str, Any]]:
    """Every JSONL record at ``path``, read as UTF-8.

    The encoding is explicit because it has bitten this repository: Windows
    defaults to cp1252 and a checkpoint containing a typographic dash raises
    ``UnicodeDecodeError`` halfway through scoring a completed run.
    """
    import json
    from pathlib import Path

    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def format_comparison(name_a: str, name_b: str, comparison: ArmComparison) -> Sequence[str]:
    """The comparison as lines, so a script prints it the same way every time."""
    lines = [
        f"  {name_a:24s} accuracy {comparison.accuracy_a:.4f}",
        f"  {name_b:24s} accuracy {comparison.accuracy_b:.4f}",
        f"  {comparison.n_differing} of {comparison.n_shared} item(s) differ -- "
        f"{comparison.favouring_a} favour {name_a}, "
        f"{comparison.favouring_b} favour {name_b}",
        f"  paired Wilcoxon over {comparison.n_shared} item(s): p = {comparison.p_value:.4f}",
    ]
    lines.extend(f"    {case}: {x:.2f} -> {y:.2f}" for case, x, y in comparison.moved)
    return lines
