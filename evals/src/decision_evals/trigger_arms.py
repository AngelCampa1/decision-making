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

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Literal

#: One checkpoint row, as the runner writes it.
Record = Mapping[str, Any]

#: Which denominator a rate is taken over.
#:
#: ``"record"`` counts rows, so an item collected at three repeats outweighs one
#: collected at two. ``"item"`` averages each case's own rate first and then
#: averages those, so every authored turn carries one vote whatever its repeat
#: count.
#:
#: **Uneven repeats are the expected state here, not an edge case.** ``--band``
#: deliberately shares a checkpoint with the full run so the cheap bands can be
#: collected first, which leaves exactly this shape. On an interleaved file with
#: ``s`` at three repeats and the rest at two, the two weightings gave pooled
#: accuracy 0.8121 and 0.7958 — and the short band was carrying 45% of the rows
#: while holding 35% of the items, in the run whose whole question is whether the
#: long bands are worse. Record weighting biases that headline toward the answer
#: the experiment is testing for.
Weight = Literal["record", "item"]

#: The record fields that are legitimate resampling units.
#:
#: ``triple`` is the real one: one positive and two negatives built from one body.
#: ``case`` puts every item in its own cluster and reduces a clustered bootstrap
#: to the item-level one, which exists so the difference between them can be
#: shown rather than asserted.
#:
#: Everything else the runner stamps — ``band``, ``domain``, ``stakes``, ``ask``,
#: ``kind``, ``should_fire``, ``route`` — is a *stratum*, not a cluster, and each
#: is reachable from ``cluster_on`` by a one-word slip. A confirmation pass found
#: ``cluster_on="stakes"`` silently recollapsing 120 items into 2 clusters and
#: ``cluster_on="domain"`` returning an interval of width exactly 0.0000 over 3
#: clusters, which reads as certainty. A typo raises; a neighbouring field did
#: not, and that is the more likely slip of the two.
CLUSTER_FIELDS: tuple[str, ...] = ("triple", "case")


class ArmError(ValueError):
    """A set of records that cannot be scored as an arm."""


@dataclass(frozen=True, slots=True)
class ConfusionMatrix:
    """The 2x2 table behind an arm's rates, and the coefficient over it.

    Firing accuracy on this corpus has a majority baseline of 2/3 -- 86
    positives against 172 negatives -- so an arm that never fires scores 0.667
    and an arm that always fires scores 0.333, and the distance between those
    two numbers is the class balance rather than anything either arm did.
    Neither of them is reported as such anywhere, because the four cells were
    printed by `evaluate` per repeat and never assembled across an arm.

    Attributes:
        true_positives: Positives the arm fired on.
        false_positives: Negatives the arm fired on.
        true_negatives: Negatives the arm stayed silent on.
        false_negatives: Positives the arm stayed silent on.
        weight: Which denominator the cells were taken over, carried for the
            same reason :class:`ArmSummary` carries it.

    **The cells are floats and that is not a rounding convenience.** Under
    ``weight="item"`` a cell is the number of fires an item is expected to
    produce in *one* repeat, summed over items, so a case collected three times
    contributes once rather than three times -- the same arithmetic
    :func:`summarise` already does for precision under that weighting. Under
    ``weight="record"`` they are whole numbers carried as floats so that one
    dataclass serves both and a caller cannot read the type as a promise about
    the denominator.

    Raises:
        ArmError: on a negative cell, or on a table whose cells are all zero.
            Every property below divides by a margin, and an empty table is the
            one input for which there is no table to describe. Refusing at
            construction makes the properties total for every instance that
            exists.
    """

    true_positives: float
    false_positives: float
    true_negatives: float
    false_negatives: float
    weight: Weight

    def __post_init__(self) -> None:
        cells = (
            self.true_positives,
            self.false_positives,
            self.true_negatives,
            self.false_negatives,
        )
        if any(cell < 0 for cell in cells):
            raise ArmError(f"a confusion matrix cannot hold a negative cell: {cells}")
        if not any(cells):
            raise ArmError(
                "an all-zero confusion matrix describes no arm. Every rate below divides "
                "by a margin of this table, and an empty one has nothing to divide."
            )

    @property
    def n(self) -> float:
        """Everything in the table."""
        return (
            self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        )

    @property
    def base_rate(self) -> float:
        """Share of the table that is positive. The number accuracy hides."""
        return (self.true_positives + self.false_negatives) / self.n

    @property
    def majority_baseline(self) -> float:
        """Accuracy of always predicting whichever class is larger.

        The bar firing accuracy has to clear before it means anything, and it
        is a property of the corpus rather than of the arm.
        """
        return max(self.base_rate, 1.0 - self.base_rate)

    @property
    def mcc(self) -> float | None:
        """Matthews correlation over this table, or ``None`` where undefined.

        The correlation between the arm's answers and the labels. Both
        degenerate arms above sit at 0 whatever the class balance is, which is
        the property accuracy lacks and the reason this is worth reporting
        beside it rather than instead of it -- accuracy is what four published
        runs were scored on and stays quotable against them.

        **Undefined rather than zero when a margin is empty, and that departs
        from the usual convention** (`sklearn` substitutes 0.0). A zero margin
        means the arm answered one way for everything, or the table holds one
        label; the denominator has a zero factor and there is no correlation to
        report. Returning 0.0 would put *"this arm's answers are uncorrelated
        with the labels"* and *"this quantity has no value here"* into the same
        float, and this repository has twice published an estimator that could
        only return zero. The conventional substitution is stated by
        :func:`format_confusion`, where a reader can see it being made.
        """
        denominator = (
            (self.true_positives + self.false_positives)
            * (self.true_positives + self.false_negatives)
            * (self.true_negatives + self.false_positives)
            * (self.true_negatives + self.false_negatives)
        )
        if denominator <= 0:
            return None
        numerator = (
            self.true_positives * self.true_negatives - self.false_positives * self.false_negatives
        )
        return numerator / math.sqrt(denominator)


@dataclass(frozen=True, slots=True)
class ArmSummary:
    """What one arm did on firing.

    Attributes:
        n_records: Rows scored, across all repeats.
        n_items: Distinct case ids contributing at least one parsed row. The
            companion denominator to ``n_records``, and the pair is printed
            together because the two differ whenever repeats are uneven.
        unparseable: Rows whose ``fired`` is null. Reported rather than dropped
            silently: a parse rate is a property of the arm.
        accuracy: Share of rows where ``fired == should_fire``.
        precision: True positives over all fires.
        recall: True positives over all positives.
        false_positive_rate: False fires over all negatives — the daily-use cost.
        missed: Positive case ids that never fired in any repeat.
        weight: ``"record"`` or ``"item"`` — which denominator every rate above
            was taken over. **Carried in the result so a rate cannot be quoted
            without it**, because the two answers differ whenever repeats are
            uneven and nothing in the number says which one it is.
        confusion: The 2x2 table the four rates above are computed from, under
            the same weighting, carrying the base rate and Matthews
            correlation. Assembled here because ``evaluate`` prints the cells
            for one repeat and nothing has ever held them across an arm, so
            every reported accuracy sat beside a majority baseline nobody
            stated.
    """

    n_records: int
    n_items: int
    unparseable: int
    accuracy: float
    precision: float
    recall: float
    false_positive_rate: float
    missed: tuple[str, ...]
    weight: Weight
    confusion: ConfusionMatrix


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


def per_item_fire_rates(records: Iterable[Record]) -> dict[str, tuple[bool, float, int]]:
    """Per case id, ``(should_fire, share of repeats that fired, repeats parsed)``.

    The item-weighted counterpart of :func:`per_item_correctness`, which folds
    the label away. Keeping the label lets recall, specificity and precision all
    be taken over items rather than rows.

    Raises:
        ArmError: if one case id appears under both labels. That is the
            2026-08-13 defect — one turn moved between the positives and the
            negatives, recall rose on every arm on disk, and not one call was
            re-made — arriving in a single file rather than across two.
    """
    tallies: dict[str, list[int]] = {}
    labels: dict[str, bool] = {}
    for row in records:
        fired = _fired(row)
        if fired is None:
            continue
        case = str(row["case"])
        label = bool(row["should_fire"])
        if labels.setdefault(case, label) != label:
            raise ArmError(
                f"case {case!r} appears with both labels. A checkpoint holding one turn as "
                "a positive and as a negative is two label revisions appended to one file, "
                "and the difference between them is not a model result."
            )
        tallies.setdefault(case, []).append(int(fired))
    return {
        case: (labels[case], sum(hits) / len(hits), len(hits)) for case, hits in tallies.items()
    }


def summarise(records: Iterable[Record], *, weight: Weight = "record") -> ArmSummary:
    """Firing precision, recall and false-positive rate for one arm.

    Unparseable rows are excluded from every rate and counted separately. They
    are not scored as failures to fire: a row with no verdict is a missing
    measurement, and treating it as a decline would turn a format problem into a
    recall result.

    ``weight`` chooses the denominator and the result carries the choice. The
    default is ``"record"`` because that is what M4, M5, M6 and L5 were scored
    with and changing it would silently stop reproducing four published numbers.
    ``"item"`` is the right default for a *new* report and is what a caller
    should pass when repeats are uneven, which on a resumed ``--band`` run they
    routinely are — see :data:`Weight`. With equal repeats and no unparseable
    rows the two are identical, which is the check that says the item path is
    computing the same quantity rather than a different one.

    Raises:
        ArmError: on an empty arm, or one with no positives or no negatives —
            precision and the false-positive rate are undefined there, and
            returning 0.0 would look like a measurement. Also on a ``weight``
            that is neither ``"record"`` nor ``"item"``, and, via
            :func:`per_item_fire_rates`, on a case id carrying both labels.
    """
    if weight not in ("record", "item"):
        raise ArmError(f"weight must be 'record' or 'item', got {weight!r}")

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

    items = per_item_fire_rates(scored)
    ever_fired = {row["case"] for row in positives if _fired(row)}
    missed = tuple(sorted({row["case"] for row in positives} - ever_fired))

    if weight == "item":
        fired_positive = [share for label, share, _ in items.values() if label]
        fired_negative = [share for label, share, _ in items.values() if not label]
        # Precision over items is the ratio of the two summed shares: each item
        # contributes the fires it is expected to produce in one repeat, so a
        # case collected three times does not count one and a half times.
        expected_true = sum(fired_positive)
        expected_false = sum(fired_negative)
        expected_fires = expected_true + expected_false
        return ArmSummary(
            n_records=len(rows),
            n_items=len(items),
            unparseable=unparseable,
            accuracy=sum(share if label else 1.0 - share for label, share, _ in items.values())
            / len(items),
            precision=expected_true / expected_fires if expected_fires else 0.0,
            recall=sum(fired_positive) / len(fired_positive),
            false_positive_rate=sum(fired_negative) / len(fired_negative),
            missed=missed,
            weight=weight,
            # Expected fires per item in one repeat, so the cells sum to the
            # item count rather than the row count and a case collected three
            # times does not weigh three votes. Same arithmetic as `precision`
            # two lines up.
            confusion=ConfusionMatrix(
                true_positives=expected_true,
                false_negatives=len(fired_positive) - expected_true,
                false_positives=expected_false,
                true_negatives=len(fired_negative) - expected_false,
                weight=weight,
            ),
        )

    true_positives = sum(1 for row in positives if _fired(row))
    false_positives = sum(1 for row in negatives if _fired(row))
    fires = true_positives + false_positives

    return ArmSummary(
        n_records=len(rows),
        n_items=len(items),
        unparseable=unparseable,
        accuracy=sum(1 for row in scored if _fired(row) == bool(row["should_fire"])) / len(scored),
        precision=true_positives / fires if fires else 0.0,
        recall=true_positives / len(positives),
        false_positive_rate=false_positives / len(negatives),
        missed=missed,
        weight=weight,
        confusion=ConfusionMatrix(
            true_positives=true_positives,
            false_negatives=len(positives) - true_positives,
            false_positives=false_positives,
            true_negatives=len(negatives) - false_positives,
            weight=weight,
        ),
    )


def _in_band_order(bands: Iterable[str]) -> list[str]:
    """Band names shortest-first, with anything unrecognised sorted after.

    The order is read from :mod:`decision_evals.corpus` rather than repeated
    here, because a second copy of ``s, m, l, xl`` is a second place for the
    corpus and its report to disagree about what a band is. The import is local
    to keep this module's own imports to the standard library: ``corpus`` pulls
    in ``triggers``, which pulls in ``yaml``, and scoring a checkpoint must not
    need the loader for the set that produced it.
    """
    from decision_evals.corpus import BANDS

    rank = {name: index for index, name in enumerate(BANDS)}
    return sorted(bands, key=lambda name: (rank.get(name, len(rank)), name))


class BandTable(dict[str, ArmSummary]):
    """The per-band table, plus the bands that are missing from it and why.

    A ``dict`` subclass rather than a new type, so every existing caller —
    ``bands["xl"]``, ``list(bands)``, :func:`format_bands` — keeps working. What
    it adds is the part a bare mapping cannot carry: **which bands are absent**.
    A table that silently omits ``xl`` and a table where ``xl`` genuinely does
    not differ look identical to a reader, and the second is a finding while the
    first is an interrupted run.

    Attributes:
        unscoreable: ``(band, reason)`` for each band that could not be scored.
        unrecognised: Band names the corpus does not declare. Kept and reported
            rather than refused: a checkpoint may legitimately predate a band
            being renamed, and refusing here would make an old file unreadable
            to correct a typo. They sort last and :func:`format_bands` names
            them, so the typo is loud instead of silent.
    """

    __slots__ = ("unrecognised", "unscoreable")

    def __init__(
        self,
        summaries: Mapping[str, ArmSummary],
        *,
        unscoreable: Iterable[tuple[str, str]] = (),
        unrecognised: Iterable[str] = (),
    ) -> None:
        super().__init__(summaries)
        self.unscoreable: tuple[tuple[str, str], ...] = tuple(unscoreable)
        self.unrecognised: tuple[str, ...] = tuple(unrecognised)


def summarise_by_band(
    records: Iterable[Record],
    *,
    weight: Weight = "record",
    on_unscoreable: Literal["raise", "report"] = "raise",
) -> BandTable:
    """One :class:`ArmSummary` per length band, in the corpus's own band order.

    **This is the question version 3 of the corpus exists to ask.** Every number
    this repository has published sits on turns of 25 words or fewer, because
    that is all version 2 contained. Five description manipulations moved firing
    accuracy nowhere and the standing reading is that description structure does
    not affect discrimination — but a word-count ruler scored 0.890 on that set
    against a best arm of 0.956, so there were about six points of room, and
    five nulls is also exactly what a ceiling looks like.

    If accuracy is flat from ``s`` to ``xl``, the ceiling was real and those
    nulls stand. If it falls, they were an artefact of the band and Tracks L and
    M are re-openable. **A pooled figure cannot tell those two apart**, and a
    pooled figure is what every caller gets by default.

    ``on_unscoreable`` decides what a half-collected band costs. The default
    ``"raise"`` refuses the whole table, which is the safe answer for a caller
    that is about to compute something from it. ``"report"`` returns the bands
    that *can* be scored and names the rest in
    :attr:`BandTable.unscoreable` — which is what a run report wants, because
    ``collect`` iterates the positives before the negatives and a 720-call run
    designed to span quota windows will be interrupted mid-band as a matter of
    routine. Losing the table for ``s``, ``m`` and ``l`` because ``xl``'s
    negatives are not in yet is a real cost and no wrong number is avoided by
    paying it.

    Raises:
        ArmError: if no record carries a ``band`` — which is what a version 2
            checkpoint looks like, and what a version 3 run made before the
            runner stamped the strata looks like too. Returning ``{}`` there
            would be a plausible zero, and an empty table reads as "the bands do
            not differ" rather than as "this run cannot answer that". This
            instrument has already shipped two estimators that could only return
            zero and neither announced itself.
        ArmError: if only *some* records carry a ``band``. The unbanded rows
            would be dropped from every rate while the printed ``n`` gave no
            hint: on a four-row fixture that turned an accuracy of 0.500 into
            1.000. It is the M5 defect — a measure whose denominator moved
            without saying so — and :func:`bootstrap_rate` already refuses the
            same shape for cluster labels.
        ArmError: if a band label is blank, which is a phantom band rather than
            a band, or if one case id appears under two different band labels,
            which is two corpora appended to one checkpoint and would count that
            item at full weight in both.
        ArmError: if any band holds a single label, under ``"raise"``.
            :func:`summarise` refuses that pooled and the refusal matters more
            per band: a half-collected band is the shape a resumed or
            interrupted ``--band`` run leaves behind, and its precision would
            read 0.000 rather than undefined.
        ArmError: under ``"report"``, if *no* band can be scored. An empty table
            is the plausible zero this whole function exists to refuse.
    """
    if on_unscoreable not in ("raise", "report"):
        raise ArmError(f"on_unscoreable must be 'raise' or 'report', got {on_unscoreable!r}")

    rows = list(records)
    banded = [row for row in rows if row.get("band") is not None]
    if not banded:
        raise ArmError(
            "no record carries a `band`. This is a version 2 checkpoint, or a version 3 "
            "one made before the runner stamped the strata, and neither can be read per "
            "band. Re-run against a banded set rather than reading the pooled figure as "
            "though the bands agreed."
        )
    if len(banded) != len(rows):
        raise ArmError(
            f"{len(rows) - len(banded)} of {len(rows)} record(s) carry no `band`. Dropping "
            "them would change the denominator without saying so, which is how every "
            "voided run in this instrument's history reported a plausible number."
        )

    grouped: dict[str, list[Record]] = {}
    seen: dict[str, str] = {}
    for row in banded:
        band = str(row["band"])
        if not band.strip():
            raise ArmError(
                f"record for case {str(row['case'])!r} carries a blank `band`. An empty "
                "label is a phantom band, not a band: it would appear in the table with a "
                "name nobody can read and a rate nobody can attribute."
            )
        case = str(row["case"])
        if seen.setdefault(case, band) != band:
            raise ArmError(
                f"case {case!r} appears under two bands, {seen[case]!r} and {band!r}. Two "
                "runs against different corpora have been appended to one checkpoint, and "
                "the item would be counted at full weight in both."
            )
        grouped.setdefault(band, []).append(row)

    ordered = _in_band_order(grouped)
    summaries: dict[str, ArmSummary] = {}
    unscoreable: list[tuple[str, str]] = []
    for band in ordered:
        try:
            summaries[band] = summarise(grouped[band], weight=weight)
        except ArmError as error:
            if on_unscoreable == "raise":
                raise ArmError(f"band {band!r} cannot be scored: {error}") from error
            unscoreable.append((band, str(error)))

    if not summaries:
        raise ArmError(
            "no band could be scored: "
            + "; ".join(f"{band} ({reason})" for band, reason in unscoreable)
            + ". An empty table reads as though the bands agreed."
        )
    return BandTable(
        summaries,
        unscoreable=unscoreable,
        unrecognised=_unrecognised_bands(ordered),
    )


def _unrecognised_bands(bands: Iterable[str]) -> list[str]:
    """Band names the corpus does not declare. Local import, as in `_in_band_order`."""
    from decision_evals.corpus import BANDS

    return [band for band in bands if band not in BANDS]


@dataclass(frozen=True, slots=True)
class ClusteredRate:
    """A per-item rate whose interval resamples **triples**, not items.

    Three version 3 items sharing a body are one authored artefact seen three
    times. In the long bands they are byte-identical up to the last sentence, so
    a body that is confusing, badly punctuated or accidentally ambiguous moves
    all three together. Resampling items pretends those three are three
    independent draws, and the resulting interval is too narrow — wrong in the
    **anti-conservative** direction, which is the direction that publishes an
    effect that is not there.

    Attributes:
        point_estimate: Mean per-item correctness. Over every record this is
            accuracy; over the positives alone it is recall; over the negatives
            alone it is specificity, so ``1 - point_estimate`` is the
            false-positive rate. Which one it is depends on what the caller
            filtered, and the caller has to say so — this class does not know.
        ci_low: Lower percentile bound.
        ci_high: Upper percentile bound.
        standard_error: Standard deviation of the bootstrap distribution.
        confidence: Nominal coverage, e.g. 0.95.
        n_items: Distinct case ids that produced at least one parsed verdict.
        n_clusters: Distinct cluster labels — the resampling unit, and the
            number that governs the width.
        n_resamples: Replicates drawn.
        icc: Intraclass correlation of per-item correctness within a cluster.
            **This is the evidence that the clustering was needed at all.** At
            0.0 the triples carry no shared difficulty and the clustered
            interval matches the item-level one; above it, they do.
        design_effect: ``1 + (m - 1) * ICC``. How much variance the clustering
            adds over pretending the items are independent.
        effective_n: ``n_items`` divided by the design effect — how many
            independent items this corpus is actually worth.
    """

    point_estimate: float
    ci_low: float
    ci_high: float
    standard_error: float
    confidence: float
    n_items: int
    n_clusters: int
    n_resamples: int
    icc: float
    design_effect: float
    effective_n: float

    @property
    def width(self) -> float:
        """Interval width. The quantity a per-item bootstrap understates."""
        return self.ci_high - self.ci_low

    @property
    def clustering_is_inert(self) -> bool:
        """Whether every cluster holds one item, so clustering did nothing.

        **This is structural, not measured, and the distinction matters.** A
        design effect of 1.000 because the ICC came out at 0.000 is a finding:
        the triples were measured and carry no shared difficulty. A design
        effect of 1.000 because every cluster is a singleton is arithmetic —
        there was no within-cluster variance for the ICC to estimate and the
        interval is the item-level one wearing the word "clustered".

        Each version 3 triple is one positive and two negatives, so **on the
        positives alone every cluster is a singleton by construction**: 40
        items, 40 clusters, design effect exactly 1.000. Any band written on
        recall therefore gets nothing from the triple structure, and the held
        pre-registration expects the length effect to appear in recall on XL —
        7 positives, 7 clusters. Calling that interval clustered is a vacuous
        phrase, and it is one this class now refuses to let a caller print.
        """
        return self.n_items == self.n_clusters


def per_item_rates_and_clusters(
    records: Iterable[Record], *, cluster_on: str = "triple"
) -> tuple[list[str], list[float], list[str]]:
    """``(case ids, per-item rates, cluster labels)``, in one case-sorted order.

    The extraction every clustered estimator needs, in one place. It was inline
    in :func:`bootstrap_rate` until a second caller appeared, and the four
    refusals below are the reason it is not simply re-typed at each call site:
    each of them is a way for a plausible number to be produced over a
    denominator nobody stated, and three of the four have happened here.

    Raises:
        ArmError: if ``cluster_on`` is not one of :data:`CLUSTER_FIELDS`; if no
            record carries it — a version 2 checkpoint has no triples, and
            resampling its items is the right answer for that corpus and the
            wrong one for this call; if only some records do, because dropping
            the rest changes the denominator silently; if every record is
            unparseable, leaving no rate to resample; or if one case id appears
            under two cluster labels, which is what two runs against different
            corpora appended to one checkpoint looks like.
    """
    if cluster_on not in CLUSTER_FIELDS:
        raise ArmError(
            f"cluster_on={cluster_on!r} is not a resampling unit. The legitimate units are "
            f"{', '.join(repr(name) for name in CLUSTER_FIELDS)}; everything else the "
            "runner stamps is a stratum, and clustering on one silently returns a "
            "different interval rather than failing. `stakes` recollapses the whole corpus "
            "into two clusters and `domain` has returned a width of exactly 0.0000, which "
            "reads as certainty."
        )
    rows = list(records)
    clustered = [row for row in rows if row.get(cluster_on) is not None]
    if not clustered:
        raise ArmError(
            f"no record carries {cluster_on!r}, so there is nothing to cluster on. A "
            "version 2 checkpoint has no triples; resampling its items would be the "
            "right answer for that corpus and the wrong one for this call."
        )
    if len(clustered) != len(rows):
        raise ArmError(
            f"{len(rows) - len(clustered)} of {len(rows)} record(s) carry no {cluster_on!r}. "
            "Dropping them would change the denominator without saying so, which is how "
            "every voided run in this instrument's history reported a plausible number."
        )

    rates = per_item_correctness(clustered)
    if not rates:
        raise ArmError(f"all {len(rows)} record(s) unparseable; there is no rate to resample")

    labels: dict[str, str] = {}
    for row in clustered:
        case = str(row["case"])
        if case not in rates:
            continue
        cluster = str(row[cluster_on])
        if labels.setdefault(case, cluster) != cluster:
            raise ArmError(
                f"case {case!r} appears under two {cluster_on!r} labels, "
                f"{labels[case]!r} and {cluster!r}. Two runs against different corpora "
                "have been appended to one checkpoint."
            )

    cases = sorted(rates)
    return cases, [rates[case] for case in cases], [labels[case] for case in cases]


def bootstrap_rate(
    records: Iterable[Record],
    *,
    cluster_on: str = "triple",
    confidence: float = 0.95,
    n_resamples: int = 2_000,
    seed: int | None = None,
) -> ClusteredRate:
    """Percentile bootstrap of a per-item rate, resampling whole clusters.

    The unit of the version 3 corpus is the **triple** — one positive and two
    negatives built from one body, differing only in the sentence at the end.
    That is the construction that removes the length shortcut, and it is also
    the construction that makes the three items correlated. Miller's clustered
    standard errors (arXiv:2411.00640) apply to it exactly as they apply to the
    ``rel-*`` templates, and :mod:`decision_evals.stats.cluster` already
    implements the resampling; this function is the trigger instrument finally
    calling it.

    The estimate is the mean of **per-item** correctness rates, matching
    :func:`compare`, so an arm at two repeats and an arm at five are the same
    quantity at different resolutions rather than one arm weighted more heavily.

    ``cluster_on`` names the record field holding the cluster label. It defaults
    to ``"triple"`` and the one other value worth passing is ``"case"``, which
    puts every item in its own cluster and reduces this to the ordinary
    item-level bootstrap. That arm exists so the difference between the two can
    be *shown* on real records rather than asserted in a docstring.

    Args:
        records: Checkpoint rows for one arm.
        cluster_on: Record field carrying the resampling unit.
        confidence: Nominal coverage, passed through.
        n_resamples: Replicates. The default is lower than the stats module's
            because this is called inside a run report, not inside a paper.
        seed: For reproducibility. A report that moves between two readings of
            the same checkpoint is not a report.

    Raises:
        ArmError: if no record carries ``cluster_on``, if only some do — a
            partial cluster label silently changes the denominator, and a silent
            denominator is this instrument's signature failure — if every record
            is unparseable, or if fewer than two clusters survive, where the
            bootstrap would return a zero-width interval that looks like
            certainty.
        ValueError: from :func:`~decision_evals.stats.cluster_bootstrap_diff` on
            a ``confidence`` outside ``(0, 1)`` or ``n_resamples < 1``.
    """
    import numpy as np

    from decision_evals.stats import (
        cluster_bootstrap_diff,
        design_effect,
        effective_sample_size,
        intraclass_correlation,
    )

    cases, rate_list, clusters = per_item_rates_and_clusters(records, cluster_on=cluster_on)
    values = np.array(rate_list, dtype=float)
    n_clusters = len(set(clusters))
    if n_clusters < 2:
        raise ArmError(
            f"{len(cases)} item(s) fall in a single {cluster_on!r}. Resampling one cluster "
            "returns the same items every time and a zero-width interval, which reads as "
            "certainty rather than as one cluster."
        )

    # A one-sample bootstrap of the mean is the paired form against a control of
    # zeros: ``treatment - control`` is then the value itself, and the percentile
    # interval of its mean is the interval wanted here. Written this way so the
    # resampling lives in one place -- `stats.cluster` carries a 100% line and
    # branch floor and is property-tested, and a second implementation here would
    # be a second thing to keep right.
    drawn = cluster_bootstrap_diff(
        np.zeros_like(values),
        values,
        clusters,
        confidence=confidence,
        n_resamples=n_resamples,
        seed=seed,
    )
    icc = intraclass_correlation(values, clusters)
    mean_cluster_size = len(cases) / n_clusters
    return ClusteredRate(
        point_estimate=drawn.point_estimate,
        ci_low=drawn.ci_low,
        ci_high=drawn.ci_high,
        standard_error=drawn.standard_error,
        confidence=confidence,
        n_items=drawn.n_items,
        n_clusters=drawn.n_clusters,
        n_resamples=n_resamples,
        icc=icc,
        design_effect=design_effect(mean_cluster_size, icc),
        effective_n=effective_sample_size(len(cases), mean_cluster_size, icc),
    )


@dataclass(frozen=True, slots=True)
class ClusteredRateDifference:
    """A rate difference between two **disjoint** groups of items.

    Q1 of the held pre-registration — *does firing accuracy fall on the long
    bands?* — compares S+M, 72 items in 24 triples, against L+XL, 48 items in 16
    triples. Different items, different clusters, no pairing, so
    :func:`compare` and :func:`~decision_evals.stats.cluster_bootstrap_diff` do
    not apply: both require the treatment values in the same item order as the
    control.

    **And the interval cannot be recovered by subtracting two
    :class:`ClusteredRate` intervals.** That subtraction produces an interval on
    the difference of the bounds, which is a different quantity and is wrong in
    both directions depending on the correlation it assumes. The resampling has
    to happen jointly, which is what
    :func:`~decision_evals.stats.cluster_bootstrap_two_sample` does.

    Attributes:
        name_control: What the control group is, for the report.
        name_treatment: What the treatment group is.
        difference: ``rate_treatment − rate_control``, over items.
        rate_control: Mean per-item correctness in the control group.
        rate_treatment: Mean per-item correctness in the treatment group.
        accuracy_control_over_records: The same rate over *records* rather than
            items. Reported beside the item figure and never instead of it: the
            registered Q1 estimator is record-weighted, the two differ whenever
            repeats are uneven, and a resumed ``--band`` run makes them uneven
            as a matter of course.
        accuracy_treatment_over_records: As above, for the treatment group.
        clustering_is_inert: Whether every cluster in **both** groups holds one
            item, which makes "clustered" a word rather than a method. True on
            any positives-only split, by the corpus's construction.
    """

    name_control: str
    name_treatment: str
    difference: float
    ci_low: float
    ci_high: float
    standard_error: float
    confidence: float
    rate_control: float
    rate_treatment: float
    accuracy_control_over_records: float
    accuracy_treatment_over_records: float
    n_items_control: int
    n_items_treatment: int
    n_clusters_control: int
    n_clusters_treatment: int
    n_resamples: int
    icc: float
    design_effect: float
    effective_n: float
    clustering_is_inert: bool

    @property
    def width(self) -> float:
        """Interval width."""
        return self.ci_high - self.ci_low

    @property
    def excludes_zero(self) -> bool:
        """Whether the interval excludes zero in either direction."""
        return self.ci_low > 0.0 or self.ci_high < 0.0

    def within(self, low: float, high: float) -> bool:
        """Whether the point estimate falls inside a registered band."""
        return low <= self.difference <= high


def bootstrap_rate_difference(
    control: Iterable[Record],
    treatment: Iterable[Record],
    *,
    name_control: str = "control",
    name_treatment: str = "treatment",
    cluster_on: str = "triple",
    confidence: float = 0.95,
    n_resamples: int = 2_000,
    seed: int | None = None,
) -> ClusteredRateDifference:
    """Unpaired difference of two clustered per-item rates.

    Each group is resampled over its own clusters, independently, and the
    replicate is the difference of the two resampled means. That is the only way
    to get a valid interval on this difference: the two groups contain different
    items in different clusters, so nothing pairs them, and subtracting two
    percentile intervals answers a different question.

    Args:
        control: Checkpoint rows for the first group. For Q1 this is the long
            bands, so that the reported difference carries the registered sign.
        treatment: Checkpoint rows for the second group.
        name_control: Label for the control group in the report.
        name_treatment: Label for the treatment group.
        cluster_on: Record field carrying the resampling unit. One of
            :data:`CLUSTER_FIELDS`.
        confidence: Nominal coverage.
        n_resamples: Replicates.
        seed: For reproducibility.

    Raises:
        ArmError: from :func:`per_item_rates_and_clusters` on either group; if
            the two groups share a case id, which means the split is wrong and
            the comparison is neither paired nor unpaired; or, via
            :func:`~decision_evals.stats.cluster_bootstrap_two_sample`, if a
            group falls in a single cluster.
    """
    import numpy as np

    from decision_evals.stats import cluster_bootstrap_two_sample

    cases_c, rates_c, clusters_c = per_item_rates_and_clusters(control, cluster_on=cluster_on)
    cases_t, rates_t, clusters_t = per_item_rates_and_clusters(treatment, cluster_on=cluster_on)

    shared = sorted(set(cases_c) & set(cases_t))
    if shared:
        raise ArmError(
            f"the two groups share {len(shared)} case id(s): {', '.join(shared[:5])}"
            f"{'...' if len(shared) > 5 else ''}. An unpaired estimator on overlapping "
            "groups double-counts the shared items and resamples them independently in "
            "both, which is neither the paired answer nor the unpaired one."
        )

    try:
        drawn = cluster_bootstrap_two_sample(
            np.array(rates_c, dtype=float),
            clusters_c,
            np.array(rates_t, dtype=float),
            clusters_t,
            confidence=confidence,
            n_resamples=n_resamples,
            seed=seed,
        )
    except ValueError as error:
        raise ArmError(str(error)) from error

    return ClusteredRateDifference(
        name_control=name_control,
        name_treatment=name_treatment,
        difference=drawn.point_estimate,
        ci_low=drawn.ci_low,
        ci_high=drawn.ci_high,
        standard_error=drawn.standard_error,
        confidence=confidence,
        rate_control=drawn.mean_control,
        rate_treatment=drawn.mean_treatment,
        accuracy_control_over_records=_record_accuracy(control),
        accuracy_treatment_over_records=_record_accuracy(treatment),
        n_items_control=drawn.n_items_control,
        n_items_treatment=drawn.n_items_treatment,
        n_clusters_control=drawn.n_clusters_control,
        n_clusters_treatment=drawn.n_clusters_treatment,
        n_resamples=n_resamples,
        icc=drawn.icc,
        design_effect=drawn.design_effect,
        effective_n=drawn.effective_n,
        clustering_is_inert=(
            drawn.n_items_control == drawn.n_clusters_control
            and drawn.n_items_treatment == drawn.n_clusters_treatment
        ),
    )


def _record_accuracy(records: Iterable[Record]) -> float:
    """Correct rows over parsed rows. The registered Q1 denominator.

    Computed here rather than through :func:`summarise` because a group may hold
    one label — the positives-only split does, by construction — and
    :func:`summarise` refuses that, correctly, for precision and the
    false-positive rate. Accuracy is defined either way.

    There is deliberately **no empty-input refusal**. Every call site reaches
    this only after :func:`per_item_rates_and_clusters` has accepted the same
    records, and that function refuses an entirely unparseable group by name. A
    second guard here could not fire, and a refusal that cannot fire is the
    defect this repository has shipped twice: tested, proven and inert.
    """
    scored = [row for row in records if _fired(row) is not None]
    return sum(1 for row in scored if _fired(row) == bool(row["should_fire"])) / len(scored)


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


#: How a named procedure is scored against a case's ``routes`` tuple.
#:
#: ``"first"`` — equality against ``routes[0]``. That is what
#: :attr:`~decision_evals.triggers.TriggerCase.route` returns and what
#: ``scripts/run_triggers.py`` stamps into ``covers``.
#: ``"any"`` — membership in the whole tuple, which is what
#: :func:`~decision_evals.triggers.evaluate_routing` applies, and what the
#: 2026-08-13 maintainer decision on second routes intended.
#:
#: **The two disagree, and they disagree on the denominator as well as on the
#: verdict.** Three v3 positives carry two defensible routes, so the per-procedure
#: item counts are 8 / 8 / 7 / 10 under ``"first"`` and 8 / 10 / 8 / 10 under
#: ``"any"`` — a dual-route item belongs to *both* its groups. There is no
#: defensible default between them, so :func:`routing_by_procedure` has none.
RoutingRule = Literal["first", "any"]

#: The rules :func:`routing_by_procedure` accepts.
ROUTING_RULES: tuple[RoutingRule, ...] = ("first", "any")


@dataclass(frozen=True, slots=True)
class RoutingGroup:
    """Routing for one procedure, under one stated rule.

    Attributes:
        procedure: The labelled procedure this group is about.
        rule: Which scoring rule produced every number here. **Carried on the
            group and not only on the table**, so a figure lifted out of the
            table into a sentence keeps its rule with it.
        n_items: Distinct case ids labelled for this procedure.
        n_records: Parsed rows across all repeats.
        n_answered: Rows that fired *and* named a procedure — the
            pre-registration's second denominator, stated in those words.
        over_items: Mean of the per-item correctness rates. One vote per
            authored turn, whatever its repeat count.
        over_records: Correct rows over parsed rows.
        over_answered: Correct rows over answered rows, or ``None`` when nothing
            was answered. ``None`` rather than 0.0: an empty denominator is the
            absence of a rate, and this instrument has published a plausible
            zero four times.
        per_item: ``(case id, correctness rate)``, case-sorted.
    """

    procedure: str
    rule: RoutingRule
    n_items: int
    n_records: int
    n_answered: int
    over_items: float
    over_records: float
    over_answered: float | None
    per_item: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class RoutingByProcedure:
    """Routing accuracy split by the procedure the turn was labelled for.

    Attributes:
        rule: The rule the caller asked for.
        groups: Procedure name to :class:`RoutingGroup`, alphabetical.
        n_items: Distinct labelled items overall.
        n_records: Parsed labelled rows overall.

    Note:
        Under ``"any"`` the groups do **not** partition the items: a dual-route
        turn is scored in each of its groups, so ``sum(g.n_items)`` exceeds
        ``n_items``. That is the intended behaviour — the question "how well does
        ``timing`` get routed to" includes every turn ``timing`` was an
        acceptable answer for — but it means the group denominators cannot be
        added up, and :attr:`n_items` is the number that says so.
    """

    rule: RoutingRule
    groups: dict[str, RoutingGroup]
    n_items: int
    n_records: int


def _acceptable_routes(
    row: Record, routes: Mapping[str, Sequence[str]] | None, rule: RoutingRule
) -> tuple[str, ...]:
    """The procedures this row may name, under ``rule``.

    Three sources in precedence order, because a checkpoint may or may not carry
    the whole tuple: the caller's mapping, the row's own ``routes`` field, then
    the row's ``route`` — which is ``routes[0]`` and therefore cannot support
    the ``"any"`` rule at all.
    """
    case = str(row["case"])
    if routes is not None:
        if case not in routes:
            raise ArmError(
                f"case {case!r} is labelled in the records but absent from the supplied "
                "`routes` mapping. Scoring it against nothing would drop it from the "
                "denominator without saying so."
            )
        declared = tuple(str(name) for name in routes[case])
        if not declared:
            raise ArmError(
                f"case {case!r} maps to an empty route tuple. A positive with an open "
                "router is excluded by carrying no route at all, not by carrying none."
            )
    elif row.get("routes"):
        declared = tuple(str(name) for name in row["routes"])
    else:
        if rule == "any":
            raise ArmError(
                f"case {case!r} carries only `route`, which is `routes[0]`, and rule 'any' "
                "needs the whole tuple. Three v3 positives have a second defensible route "
                "and scoring them against the first alone is the rule this one is not. "
                "Pass `routes=` from the trigger set, or re-run so the records carry it."
            )
        declared = (str(row["route"]),)
    return declared[:1] if rule == "first" else declared


def routing_by_procedure(
    records: Iterable[Record],
    *,
    rule: RoutingRule,
    routes: Mapping[str, Sequence[str]] | None = None,
) -> RoutingByProcedure:
    """Routing accuracy, grouped by the procedure the turn was labelled for.

    Q3 of the held pre-registration: *how does ``ledger`` route now that the
    corpus contains piles?* — registered as "``ledger`` is the worst-routed of
    the four procedures", which a pooled routing accuracy cannot answer.

    **``rule`` is required and has no default.** Two scoring rules are live in
    this repository and they disagree: the runner stamps ``covers`` by equality
    against ``routes[0]`` while ``evaluate_routing`` accepts any member of
    ``routes``. Defaulting would mean a number could be quoted without its rule,
    and the whole reason this function exists is that the rule changes both the
    verdicts and the denominators. The chosen rule is written into the result and
    into every group inside it.

    Correctness is decided on the **named procedure**, whether or not the turn
    also fired — matching ``evaluate_routing`` and the ``covers`` stamp. Firing
    enters only through ``n_answered``, which is the pre-registration's second
    denominator, stated there as "the subset where the arm fired and named a
    procedure".

    Args:
        records: Checkpoint rows. Rows with no route label are ignored; rows
            whose ``fired`` is null are dropped as unparseable.
        rule: ``"first"`` or ``"any"``. See :data:`RoutingRule`.
        routes: Case id to its acceptable procedures, normally
            ``{case.id: case.routes for case in trigger_set.positives}``.
            Required for ``"any"`` unless the records carry their own ``routes``
            field, because ``route`` alone is ``routes[0]`` and cannot express a
            second acceptable answer.

    Raises:
        ArmError: on an unknown ``rule``; if no record carries a route label, so
            the arm has nothing to route and an empty table would read as a
            result; if a labelled case is missing from ``routes``; or if ``"any"``
            is asked for against records that carry only ``route``.
    """
    if rule not in ROUTING_RULES:
        raise ArmError(
            f"rule must be one of {', '.join(repr(name) for name in ROUTING_RULES)}, "
            f"got {rule!r}. There is no default: the runner's `covers` stamp uses 'first' "
            "and `evaluate_routing` uses 'any', they disagree on three v3 items, and a "
            "routing number quoted without its rule is not a measurement."
        )

    rows = [
        row
        for row in records
        if _fired(row) is not None and (row.get("routes") or row.get("route") is not None)
    ]
    if not rows:
        raise ArmError(
            "no parsed record carries a route label, so there is no routing to score. An "
            "arm with no labelled routes and an empty table look the same to a reader."
        )

    tallies: dict[str, dict[str, list[tuple[bool, bool]]]] = {}
    items: set[str] = set()
    for row in rows:
        acceptable = _acceptable_routes(row, routes, rule)
        case = str(row["case"])
        items.add(case)
        procedure = row.get("procedure")
        correct = procedure is not None and str(procedure) in acceptable
        answered = bool(_fired(row)) and procedure is not None
        for name in acceptable:
            tallies.setdefault(name, {}).setdefault(case, []).append((correct, answered))

    groups: dict[str, RoutingGroup] = {}
    for name in sorted(tallies):
        per_case = tallies[name]
        flat = [pair for pairs in per_case.values() for pair in pairs]
        answered_rows = [correct for correct, answered in flat if answered]
        per_item = tuple(
            (case, sum(1 for correct, _ in pairs if correct) / len(pairs))
            for case, pairs in sorted(per_case.items())
        )
        groups[name] = RoutingGroup(
            procedure=name,
            rule=rule,
            n_items=len(per_case),
            n_records=len(flat),
            n_answered=len(answered_rows),
            over_items=sum(rate for _, rate in per_item) / len(per_item),
            over_records=sum(1 for correct, _ in flat if correct) / len(flat),
            over_answered=(
                sum(1 for correct in answered_rows if correct) / len(answered_rows)
                if answered_rows
                else None
            ),
            per_item=per_item,
        )

    return RoutingByProcedure(
        rule=rule,
        groups=groups,
        n_items=len(items),
        n_records=len(rows),
    )


@dataclass(frozen=True, slots=True)
class NegativeKindRate:
    """False-positive rate for one kind of negative, with an interval.

    Attributes:
        kind: Which sort of non-decision these turns are.
        n_items: Distinct case ids. **The denominator that governs the
            interval**, and the one a reader has to see: ``settled`` is five
            items, so at any plausible false-positive rate it reads 0.000 most
            of the time and that is not evidence of anything.
        n_records: Parsed rows across all repeats.
        n_fires: Rows that fired.
        over_items: Mean per-item fire rate — one vote per authored turn.
        over_records: Fires over parsed rows.
        ci_low: Lower Wilson bound on ``over_items``.
        ci_high: Upper Wilson bound.
        confidence: Nominal coverage of the interval.
        fired_on: Case ids that fired in at least one repeat.
    """

    kind: str
    n_items: int
    n_records: int
    n_fires: int
    over_items: float
    over_records: float
    ci_low: float
    ci_high: float
    confidence: float
    fired_on: tuple[str, ...]

    @property
    def width(self) -> float:
        """Interval width. On a five-item group this is most of ``[0, 1]``."""
        return self.ci_high - self.ci_low

    def separated_from(self, other: NegativeKindRate) -> bool:
        """Whether this group's interval excludes the other's point estimate.

        The weakest honest reading of "these two kinds differ". It is offered
        instead of a verdict flag because the threshold for *uninformative* is
        not derivable from anything measured here, and standing rule 1 says an
        undermined parameter is recorded as a choice rather than invented into a
        function. What the caller gets is the interval and the count; what it
        does with them is its own registered band.
        """
        return not self.ci_low <= other.over_items <= self.ci_high


def _wilson(p_hat: float, n: int, confidence: float) -> tuple[float, float]:
    """Wilson score interval on a proportion.

    Chosen over a bootstrap because the groups that need it most are the
    smallest ones, and a bootstrap over five items whose every draw is zero
    returns ``[0.000, 0.000]`` — an interval of zero width, which reads as
    certainty and is exactly the failure this whole result type exists to
    prevent. Wilson is non-degenerate at ``p = 0``: five items with no fires
    gives roughly ``[0.000, 0.434]``, which says what it should.

    ``p_hat`` may be fractional, because it is a mean of per-item rates rather
    than a count of successes. The interval treats each *item* as one
    observation, which is the conservative unit: repeats of one turn are not
    independent evidence about that turn.
    """
    from scipy.stats import norm

    z = float(norm.ppf(1.0 - (1.0 - confidence) / 2.0))
    denominator = 1.0 + z * z / n
    centre = (p_hat + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p_hat * (1.0 - p_hat) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def false_positive_rate_by_kind(
    records: Iterable[Record], *, confidence: float = 0.95
) -> dict[str, NegativeKindRate]:
    """False-positive rate per kind of negative, largest group first.

    Q4 of the held pre-registration: **``settled`` has the highest FPR of the
    seven kinds.** A negative whose decision has been made and stated is the one
    that still looks like a decision, and it is the kind version 2 barely had.

    :func:`summarise` cannot answer this. It refuses a subgroup holding one
    label — correctly, because precision and recall are undefined there — and a
    ``kind`` subgroup is all negatives by definition. So this computes the one
    rate that *is* defined on an all-negative group and computes nothing else.

    Every group carries ``n_items`` and an interval, because five of the seven
    kinds are small and two are tiny. At n=5 and a true rate near 0.02 the
    ``settled`` group reads exactly 0.000 the large majority of the time; the
    rate alone is indistinguishable from evidence of a real floor, and
    ``[0.000, 0.434]`` beside it is not.

    Args:
        records: Checkpoint rows. Positives are ignored; they carry no ``kind``.
        confidence: Nominal coverage of the Wilson interval.

    Raises:
        ArmError: if no record carries a ``kind``, which is a version 2
            checkpoint and cannot answer this at all; if a record carries a
            ``kind`` while being labelled a positive, which the trigger loader
            forbids and which means two corpora have been appended to one file;
            if every row of some kind is unparseable, leaving that kind with a
            rate of 0.000 over nothing; or on a ``confidence`` outside ``(0, 1)``.
    """
    if not 0.0 < confidence < 1.0:
        raise ArmError(f"confidence must be in (0, 1), got {confidence}")

    rows = [row for row in records if row.get("kind") is not None]
    if not rows:
        raise ArmError(
            "no record carries a `kind`. This is a version 2 checkpoint, where the "
            "negatives were not typed, and a pooled false-positive rate is the only thing "
            "it can answer. Returning an empty table would read as though the kinds agreed."
        )

    grouped: dict[str, list[Record]] = {}
    for row in rows:
        if row["should_fire"]:
            raise ArmError(
                f"case {str(row['case'])!r} carries kind {str(row['kind'])!r} and is "
                "labelled a positive. `kind` names which sort of non-decision a negative "
                "is; the trigger loader refuses it on a positive, so this checkpoint holds "
                "two corpora."
            )
        grouped.setdefault(str(row["kind"]), []).append(row)

    rates: list[NegativeKindRate] = []
    for kind, group in grouped.items():
        items = per_item_fire_rates(group)
        if not items:
            raise ArmError(
                f"every record of kind {kind!r} is unparseable, so its false-positive rate "
                "would read 0.000 over nothing. A format failure is not a refusal to fire."
            )
        scored = [row for row in group if _fired(row) is not None]
        over_items = sum(share for _, share, _ in items.values()) / len(items)
        low, high = _wilson(over_items, len(items), confidence)
        rates.append(
            NegativeKindRate(
                kind=kind,
                n_items=len(items),
                n_records=len(scored),
                n_fires=sum(1 for row in scored if _fired(row)),
                over_items=over_items,
                over_records=sum(1 for row in scored if _fired(row)) / len(scored),
                ci_low=low,
                ci_high=high,
                confidence=confidence,
                fired_on=tuple(sorted(case for case, (_, share, _) in items.items() if share > 0)),
            )
        )

    # Largest group first, so a reader meets the kinds that can support a
    # statement before the ones that cannot, and the two four-item groups are
    # last rather than interleaved with the twenty-seven-item one.
    rates.sort(key=lambda rate: (-rate.n_items, rate.kind))
    return {rate.kind: rate for rate in rates}


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


def venue_comparable(a: Iterable[Record], b: Iterable[Record]) -> str | None:
    """Whether two arms sent the description through the same prompt venue.

    Track N9. ``run_triggers.py``'s own module docstring names the gap this
    guards against: every number in Track L, Track M and N6 was measured with
    the description as the *entire* system prompt (``--system-prompt``); N9
    sends the same description **appended to** the CLI's own system prompt
    (``--append-system-prompt``, ``Conversation(in_situ=True)``) instead. A
    comparison spanning the two would answer N9's own question by fiat -- by
    which arm happened to land in the diff -- rather than by measurement.

    **An absent ``in_situ`` is False, not unknown, and that is the opposite
    call from :func:`models_comparable` for a reason specific to this field.**
    There, ``--model`` already carried a default that could be silently
    overridden before the stamp existed, so an unstamped record's tier
    genuinely could have been anything -- filling in the default would be
    standing rule 1's invented parameter. ``in_situ`` has no such history:
    before this parameter existed, ``run_triggers.py``'s ``ask()`` built every
    ``Conversation`` with no ``in_situ`` argument at all, and
    ``Conversation.__init__``'s own default resolves that to
    ``in_situ=False``. There is no call this file has ever made that could
    have been in situ without the stamp saying so. So an absent value is read
    as False, the same way :func:`label_versions_comparable` reads an absent
    ``set_version`` as 1: it states what happened rather than declaring the
    past unrecoverable, and every arm published before this row existed
    remains comparable to every other one, none of it retroactively voided.
    """
    venues_a = {bool(row.get("in_situ", False)) for row in a}
    venues_b = {bool(row.get("in_situ", False)) for row in b}
    if len(venues_a | venues_b) <= 1:
        return None

    def _label(in_situ: bool) -> str:
        return "in situ (--append-system-prompt)" if in_situ else "substituted (--system-prompt)"

    named_a = sorted(_label(v) for v in venues_a)
    named_b = sorted(_label(v) for v in venues_b)
    return (
        f"these arms were sent through different prompt venues: {named_a} against "
        f"{named_b}. One appends the description to the CLI's own system prompt and "
        "the other replaces it outright -- exactly the position N9 exists to test, so "
        "comparing them would decide that question by which arm was in the diff rather "
        "than by measurement."
    )


def skill_versions_comparable(a: Iterable[Record], b: Iterable[Record]) -> str | None:
    """Whether two arms were scored against the same revision of the shipped skill.

    On 2026-08-19 the shipped skill went ``0.2.1`` -> ``0.3.0``: two procedures
    added, the router table grew from four rows to six, and the frontmatter
    ``description`` -- the text every arm in this file actually sends -- was
    rewritten with it (``docs/DECISIONS.md``, "the shipped description now
    enumerates six procedures, and that retires ten arms"). ``set_version``
    tracks the *corpus* label revision and says nothing about which
    ``SKILL.md`` produced the description being scored. Without this guard,
    ``compare()`` would take an arm run against the six-procedure description
    and one run against the four-procedure description, find none of the three
    existing guards objecting, and return a p-value for a difference between
    two products.

    **An absent ``skill_version`` is unknown, not a default -- the same call as
    :func:`models_comparable`, and the opposite of :func:`venue_comparable`,
    for the reason :func:`models_comparable` gives.** ``metadata.version`` in
    ``skills/decision-making/SKILL.md`` has moved three times on record --
    ``0.2.0`` -> ``0.2.1`` -> ``0.3.0`` -- and the description text changed
    alongside every one of those bumps. A record written before this stamp
    existed could have been produced against any of those revisions depending
    only on when the run happened to be made; nothing in the row says which,
    so filling one in would be standing rule 1's invented parameter -- exactly
    the situation ``--model`` was in before it was stamped.

    This is *not* :func:`venue_comparable`'s situation. There, ``in_situ`` had
    no revision to be silently at, because ``ask()`` never passed the argument
    at all before the stamp existed, so every historical call resolves to one
    fact (``False``) and reading an absent value that way states what
    happened. The skill version has no such single resolution -- it demonstrably
    took three different values across the runs already on disk -- so the two
    fields need opposite defaults even though they are stamped by the same
    function.

    So the three cases are decided the way :func:`models_comparable` decides
    them:

    * **both unstamped** -- allowed. Neither record says which revision
      produced it, and the guard says nothing about them either, rather than
      quietly deciding they must match.
    * **one stamped, one not** -- refused. The unstamped arm could have run
      against any prior revision; the stamped one names its revision exactly.
    * **both stamped and different** -- refused.
    """
    versions_a = {row.get("skill_version") for row in a}
    versions_b = {row.get("skill_version") for row in b}
    seen = versions_a | versions_b
    if seen <= {None} or len(seen) <= 1:
        return None
    named = sorted(str(version) for version in seen if version is not None)
    if None in seen:
        return (
            f"one of these arms records the skill revision it ran against ({', '.join(named)}) "
            "and the other does not. An unstamped record does not mean any particular "
            "revision -- `metadata.version` has moved three times on record and the "
            "description text changed with it each time -- so the two cannot be shown to "
            "have run against the same skill, and a revision bump moves the description "
            "every arm here actually sends."
        )
    return (
        f"these arms were scored against different skill revisions: {sorted(versions_a, key=str)} "
        f"against {sorted(versions_b, key=str)}. A revision bump rewrites the frontmatter "
        "description these arms are testing, so the difference between them would not be "
        "a result about one description."
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

    **The four stamp guards are not enough on their own.** They compare
    ``set_version``, ``model``, ``in_situ`` and ``skill_version``, which are
    four claims a file makes about itself; none of them looks at a label. Two
    arms stamped ``set_version: 4``, identical in every verdict, differing only
    in one case's ``should_fire``, compared 1.0000 against 0.6667 with an
    item-moved line under it -- because :func:`per_item_correctness` folds the
    label away into ``fired == should_fire`` before anything can pair on it.
    That is the 2026-08-13 "not one call was re-made" defect arriving *inside*
    one key version, so :func:`_labels_by_case` is the fifth guard and is the
    same function :func:`_respondent_grid` refuses on.

    Raises:
        ArmError: if the two arms share no case ids, if either fails one of the
            four comparability guards, or if one case id carries both labels
            across them.
    """
    from scipy.stats import wilcoxon

    rows_a, rows_b = list(a), list(b)
    if (reason := label_versions_comparable(rows_a, rows_b)) is not None:
        raise ArmError(reason)
    if (reason := models_comparable(rows_a, rows_b)) is not None:
        raise ArmError(reason)
    if (reason := venue_comparable(rows_a, rows_b)) is not None:
        raise ArmError(reason)
    if (reason := skill_versions_comparable(rows_a, rows_b)) is not None:
        raise ArmError(reason)
    _labels_by_case([*rows_a, *rows_b])

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


#: One respondent: an ``(arm, repeat)`` pair.
#:
#: The unit of the item analysis registered in
#: ``notebook/2026-08-19-the-item-analysis-this-instrument-never-ran.md``. An arm
#: is a description variant; a repeat is one pass of that variant over the whole
#: corpus. Twelve respondents -- six arms at two repeats -- is what the v4
#: records hold, and it is the denominator that limits every statistic below.
Respondent = tuple[str, int]


@dataclass(frozen=True, slots=True)
class ItemDifficulty:
    """How often one item was answered correctly, over the respondents.

    Attributes:
        case: The case id.
        should_fire: The item's label. **Carried so a difficulty cannot be
            averaged across the two.** A positive's difficulty is a miss rate
            and a negative's is a false-fire rate; pooling them produces a
            number about neither, which is why :class:`ItemAnalysis` reports the
            two means separately and never a third.
        p: Correct rows over parsed rows for this item, correct meaning
            ``fired == should_fire``. Routing is not in it: ``council`` and
            ``hinge`` are offered to the model and correct for zero of the 86
            positives, so a routing term here would be a six-way choice scored
            against a four-way key.
        n_respondents: Parsed rows for this item -- the denominator of ``p``,
            and 12 only when every respondent's row parsed.
    """

    case: str
    should_fire: bool
    p: float
    n_respondents: int


@dataclass(frozen=True, slots=True)
class ItemDiscrimination:
    """Corrected item-total point-biserial for one item.

    Attributes:
        case: The case id.
        should_fire: The item's label, carried for the same reason as on
            :class:`ItemDifficulty`.
        r_pb: Correlation between this item's per-respondent correctness and
            the respondent's score over **the other items**, or ``None`` when
            it does not exist. ``None`` rather than 0.0: a constant item has no
            correlation, and 0.0 would read as "measured, and flat" -- the
            plausible zero this instrument has published four times.
        n_respondents: Respondents whose row for this item parsed. The
            denominator of the correlation, and it must be at least three:
            two points determine a line, so a defined correlation over two
            respondents is +1.0 or -1.0 whatever the data say.
        undefined: Why ``r_pb`` is ``None``, or ``None`` when it is not. Every
            item at ``p == 0.0`` or ``p == 1.0`` lands here by construction,
            which is the arithmetic link between this estimator and the broken-
            item screen: an item nobody varies on cannot discriminate. So does
            every item under three respondents, which is the arithmetic link to
            the denominator: at two the value exists and carries no information
            beyond which repeat scored higher.
    """

    case: str
    should_fire: bool
    r_pb: float | None
    n_respondents: int
    undefined: str | None


@dataclass(frozen=True, slots=True)
class BrokenItemScreen:
    """Items every respondent got wrong, and items every respondent got right.

    Anthropic's eval guidance names the cheapest screen there is -- *a 0% pass
    rate across many trials is most often a signal of a broken task, not an
    incapable agent*. It is a screen and not a verdict: nothing here may move a
    label, which is Track N3's blind adjudication and needs a
    ``docs/DECISIONS.md`` entry.

    The floor is split by label because the two mean different things. A
    positive at ``p == 0.0`` never fired in any respondent; a negative at
    ``p == 0.0`` fired in every one.

    Attributes:
        n_respondents: Respondents in the analysis. **Read this first, and read
            it as the size of the set rather than as any item's denominator** --
            an item whose other rows were unparseable sits on the floor over its
            own handful of respondents, which is why
            :func:`format_item_analysis` prints each floor item's own count
            beside it. At one respondent every ``p`` is 0.0 or 1.0 by
            construction and both sets below are simply the items that
            respondent got wrong and right. At two, ``p`` can only be 0.0, 0.5
            or 1.0, so the floor and the ceiling still hold most of the corpus:
            the screen being borrowed is a 0% rate across *many* trials, and two
            is not many.
        floor_positives: Positives at ``p == 0.0``, case-sorted.
        floor_negatives: Negatives at ``p == 0.0``, case-sorted.
        ceiling_positives: Positives at ``p == 1.0``. Not a defect signal --
            the ceiling term, reported because an item nothing varies on
            contributes no discrimination either way.
        ceiling_negatives: Negatives at ``p == 1.0``.
    """

    n_respondents: int
    floor_positives: tuple[str, ...]
    floor_negatives: tuple[str, ...]
    ceiling_positives: tuple[str, ...]
    ceiling_negatives: tuple[str, ...]

    @property
    def floor(self) -> tuple[str, ...]:
        """Every item at ``p == 0.0``, both labels, case-sorted."""
        return tuple(sorted(self.floor_positives + self.floor_negatives))

    @property
    def ceiling(self) -> tuple[str, ...]:
        """Every item at ``p == 1.0``, both labels, case-sorted."""
        return tuple(sorted(self.ceiling_positives + self.ceiling_negatives))


@dataclass(frozen=True, slots=True)
class TripleJoint:
    """Whether a respondent got a whole triple right, over the respondents.

    AgentAbstain's Paired Accuracy generalised from a pair to a triple, and the
    statistic the matched-triple design was built for. A triple is one positive
    and two negatives written from one body: getting the positive right by
    firing on everything scores here exactly as badly as it should.

    Attributes:
        triple: The triple id.
        joint: Fraction of contributing respondents that got **all** the
            triple's items right within that respondent's own repeat, or
            ``None`` when no respondent observed the whole triple.
        n_respondents: Respondents that observed every item of the triple --
            the denominator of ``joint``. A respondent with one unparseable row
            in the triple has no joint outcome and is not counted as a failure.
        n_items: Items carrying this triple id. Three in the v4 corpus;
            anything else is named in :attr:`ItemAnalysis.incomplete_triples`,
            because "all three" over two items is a different statistic.
    """

    triple: str
    joint: float | None
    n_respondents: int
    n_items: int


@dataclass(frozen=True, slots=True)
class ItemAnalysis:
    """The four registered item-level estimators over one respondent set.

    Attributes:
        respondents: Every ``(arm, repeat)`` pair, sorted.
        n_items: Items with at least one parsed row.
        n_unparseable: Rows whose ``fired`` is null, across every arm. **Zero
            is what makes the rest-scores below comparable**: see
            :func:`item_discrimination` for what a non-zero value does to them.
        dropped: Items whose every row was unparseable, so they have no
            difficulty at all. Absent from ``difficulty`` rather than scored as
            zero, matching :func:`per_item_correctness`.
        difficulty: Case id to :class:`ItemDifficulty`, every item.
        discrimination: Case id to :class:`ItemDiscrimination`, every item.
        screen: The floor and ceiling sets.
        triples: Triple id to :class:`TripleJoint`, empty when the records
            carry no triples.
        triples_unavailable: Why ``triples`` is empty, or ``None``. Carried
            rather than raised so a v2 checkpoint still yields the other three
            estimators, and stated rather than left blank so an empty table
            cannot read as "no triple failed".
        incomplete_triples: Triple ids holding other than three items.
        mean_difficulty_positive: Mean ``p`` over the positives, or ``None``
            when there are none.
        mean_difficulty_negative: Mean ``p`` over the negatives, or ``None``.
        median_discrimination: Median ``r_pb`` over the items where it is
            defined, or ``None`` when it is defined nowhere.
        n_discriminating: How many items that median was taken over. The
            denominator, and it is not ``n_items``: every floor and ceiling
            item is excluded because its correlation does not exist.
    """

    respondents: tuple[Respondent, ...]
    n_items: int
    n_unparseable: int
    dropped: tuple[str, ...]
    difficulty: dict[str, ItemDifficulty]
    discrimination: dict[str, ItemDiscrimination]
    screen: BrokenItemScreen
    triples: dict[str, TripleJoint]
    triples_unavailable: str | None
    incomplete_triples: tuple[str, ...]
    mean_difficulty_positive: float | None
    mean_difficulty_negative: float | None
    median_discrimination: float | None
    n_discriminating: int

    @property
    def n_respondents(self) -> int:
        """Respondents. The denominator every statistic here is limited by."""
        return len(self.respondents)

    @property
    def complete(self) -> bool:
        """Whether every respondent has a parsed row for every item.

        The condition under which a rest-score is a count over the same 257
        items for every respondent. When it is False the rest-scores are counts
        over different numbers of items and partly measure parse rate.
        """
        return self.n_unparseable == 0


def _labels_by_case(rows: Iterable[Record]) -> dict[str, bool]:
    """Case id to ``should_fire``, refusing a case that appears under both labels.

    One place where a label map is built, because there are two callers and the
    consequence of them disagreeing is the defect this repository has already
    published once. On 2026-08-13 one turn moved from the positives to the
    negatives; recall rose three to five points on every arm on disk and **not
    one call was re-made**. `set_version` catches that across a key revision --
    and catches nothing when two files carry the same stamp and different
    labels, which is what a hand-edited checkpoint or a half-applied `de
    rescore` leaves behind.

    Correctness here is ``fired == should_fire`` and nothing else, so a label
    that differs between two arms silently regrades every row of one of them.
    :func:`compare` reads 33 points of difference out of two arms whose model
    behaviour is identical, and prints an item-moved line under it.

    Raises:
        ArmError: if one case id appears under both labels.
    """
    labels: dict[str, bool] = {}
    for row in rows:
        case = str(row["case"])
        label = bool(row["should_fire"])
        if labels.setdefault(case, label) != label:
            raise ArmError(
                f"case {case!r} appears with both labels. A respondent set holding one "
                "turn as a positive and as a negative is two label revisions read as "
                "one, and the difference between them is not a model result."
            )
    return labels


def _respondent_grid(
    arms: Mapping[str, Sequence[Record]],
) -> tuple[tuple[Respondent, ...], dict[str, bool], dict[str, dict[Respondent, bool]], int]:
    """``(respondents, labels, correctness, unparseable)`` over a set of arms.

    One place where the respondent set is built, so the four estimators cannot
    disagree about who is in it. Correctness is ``fired == should_fire`` and
    nothing else.

    Raises:
        ArmError: if no arm is supplied, or one holds no records -- an empty arm
            contributes no respondent and would silently shrink the denominator
            the caller named; if two arms fail any of the four comparability
            guards :func:`compare` applies, for the same reasons it applies
            them -- pooling two arms into one respondent set is a stronger claim
            about their comparability than testing one against the other, not a
            weaker one; if one case id appears under both labels; if one
            ``(arm, repeat, case)`` cell carries two verdicts, because there is
            no defensible rule for choosing between them; or if no row parsed
            anywhere.

            :func:`venue_comparable` is the guard that makes the registered
            exclusion mechanical rather than a matter of the caller's memory.
            The pre-registration excludes ``verdicts-in-situ`` on the grounds
            that 70 of its 516 responses are unparseable and its parse rate
            splits by domain (Fisher p = 0.00011), so pooling it would put a
            domain-correlated missing-data mechanism inside an item statistic --
            and every one of those rows is stamped ``in_situ: true``, so the
            guard catches the exact file the entry names. Without it the
            exclusion lived only in whichever list of paths a caller happened to
            type.
    """
    if not arms:
        raise ArmError(
            "no arm was supplied, so there is no respondent set. An item analysis over "
            "nothing would report an empty table, and an empty table and a corpus with no "
            "broken item look the same to a reader."
        )
    rows_by_arm = {name: list(records) for name, records in sorted(arms.items())}
    for name, rows in rows_by_arm.items():
        if not rows:
            raise ArmError(
                f"arm {name!r} holds no records. It contributes no respondent, so the "
                "denominator would be smaller than the one the caller asked for and "
                "nothing would say so."
            )

    reference = next(iter(rows_by_arm.values()))
    for name, rows in rows_by_arm.items():
        for guard in (
            label_versions_comparable,
            models_comparable,
            venue_comparable,
            skill_versions_comparable,
        ):
            if (reason := guard(rows, reference)) is not None:
                raise ArmError(f"arm {name!r} cannot join this respondent set: {reason}")

    labels = _labels_by_case(row for rows in rows_by_arm.values() for row in rows)
    correctness: dict[str, dict[Respondent, bool]] = {}
    respondents: set[Respondent] = set()
    seen: set[tuple[Respondent, str]] = set()
    unparseable = 0
    for name, rows in rows_by_arm.items():
        for row in rows:
            case = str(row["case"])
            label = labels[case]
            respondent: Respondent = (name, int(row["repeat"]))
            respondents.add(respondent)
            if (respondent, case) in seen:
                raise ArmError(
                    f"respondent {respondent} carries two verdicts for case {case!r}. One "
                    "cell of the respondent-by-item grid cannot hold two answers, and "
                    "there is no defensible rule for picking one -- de-duplicate the "
                    "checkpoint first."
                )
            seen.add((respondent, case))
            fired = _fired(row)
            if fired is None:
                unparseable += 1
                continue
            correctness.setdefault(case, {})[respondent] = fired == label

    if not correctness:
        raise ArmError(
            f"all {unparseable} row(s) across {len(rows_by_arm)} arm(s) are unparseable; "
            "there is no item to score."
        )
    return tuple(sorted(respondents)), labels, correctness, unparseable


def item_difficulty(arms: Mapping[str, Sequence[Record]]) -> dict[str, ItemDifficulty]:
    """Per item, correct rows over parsed rows across the respondents.

    Estimator 1 of the registered four. The denominator is the respondents whose
    row for that item parsed -- 12 in the v4 respondent set, and stated per item
    because it is 12 only when nothing failed to parse.

    Correct is ``fired == should_fire``. Nothing about routing enters, by
    registration: two of the six procedures the model is offered are correct for
    zero of the 86 positives, so a routing term would grade a six-way choice
    against a four-way key.

    The result is keyed by case and carries each item's label, because a
    positive's difficulty is a miss rate and a negative's is a false-fire rate.
    They are never averaged together here or anywhere below.

    Raises:
        ArmError: as :func:`_respondent_grid` raises it.
    """
    _, labels, correctness, _ = _respondent_grid(arms)
    return {
        case: ItemDifficulty(
            case=case,
            should_fire=labels[case],
            p=sum(1 for correct in scores.values() if correct) / len(scores),
            n_respondents=len(scores),
        )
        for case, scores in sorted(correctness.items())
    }


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Pearson correlation, or ``None`` when either side has no variance.

    ``None`` and not 0.0. A constant vector has no correlation with anything --
    the quantity does not exist rather than existing and being flat, and this
    module does not publish a plausible zero.
    """
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    deviations_x = [x - mean_x for x in xs]
    deviations_y = [y - mean_y for y in ys]
    sum_xx = sum(d * d for d in deviations_x)
    sum_yy = sum(d * d for d in deviations_y)
    if sum_xx <= 0.0 or sum_yy <= 0.0:
        return None
    covariance = sum(dx * dy for dx, dy in zip(deviations_x, deviations_y, strict=True))
    return covariance / math.sqrt(sum_xx * sum_yy)


def item_discrimination(arms: Mapping[str, Sequence[Record]]) -> dict[str, ItemDiscrimination]:
    """Per item, the **corrected** item-total point-biserial.

    Estimator 2 of the registered four: the correlation between item *i*'s
    per-respondent correctness and that respondent's score over the *other*
    items. Corrected item-total, not raw -- the item is removed from the total it
    is correlated against. At 258 items the inflation a raw correlation carries
    is small, but the correction costs nothing and its absence is the standard
    defect.

    The rest-score is the **count** of other items that respondent got right,
    which is what the pre-registration names. With a complete grid every
    respondent's count is taken over the same 257 items, and a count and a rate
    then differ by a constant factor a correlation is invariant to. With
    unparseable rows they are not the same thing: a count over fewer observed
    items partly measures how much of the corpus that respondent parsed. So
    :attr:`ItemAnalysis.complete` is reported beside the numbers and
    :func:`format_item_analysis` says so on the page when it is False.

    ``r_pb`` is ``None`` wherever the correlation does not exist **or exists
    only by construction** -- fewer than three respondents, an item every
    respondent scored the same on (every floor and ceiling item), or rest-scores
    that do not vary. The reason is carried in
    :attr:`ItemDiscrimination.undefined`, because "no discrimination" and "the
    correlation is undefined here" are different statements and 0.0 says the
    first while meaning the second.

    **Three, not two.** Pearson over two points is a line through two points:
    where it is defined at all it is exactly +1.0 or -1.0, and the standard
    ``--repeats 2`` single-arm run therefore reported ``median r_pb +1.000`` as
    though it were a measurement. n=2 admits exactly two values, n=3 nineteen and
    n=4 ninety-seven, so three is the smallest non-degenerate denominator and is
    the floor here. Refusing it in the estimator rather than in
    :func:`format_item_analysis` is deliberate: a formatter fix would leave
    :attr:`ItemAnalysis.median_discrimination` equal to 1.0 on the dataclass a
    scoring script reads, which is the right-on-the-page-wrong-in-the-record
    split this module exists to stop.

    Raises:
        ArmError: as :func:`_respondent_grid` raises it.
    """
    _, labels, correctness, _ = _respondent_grid(arms)
    totals: dict[Respondent, int] = {}
    for scores in correctness.values():
        for respondent, correct in scores.items():
            totals[respondent] = totals.get(respondent, 0) + int(correct)

    results: dict[str, ItemDiscrimination] = {}
    for case, scores in sorted(correctness.items()):
        respondents = sorted(scores)
        n = len(respondents)
        if n < 3:
            results[case] = ItemDiscrimination(
                case=case,
                should_fire=labels[case],
                r_pb=None,
                n_respondents=n,
                undefined=(
                    f"{n} respondent(s) scored this item; three is the smallest "
                    "denominator that can carry a correlation here. At two, a defined "
                    "point-biserial is two points and is therefore exactly +1.000 or "
                    "-1.000 by construction, saying only which repeat scored higher"
                ),
            )
            continue
        on_item = [float(scores[respondent]) for respondent in respondents]
        rest = [float(totals[respondent] - int(scores[respondent])) for respondent in respondents]
        r_pb = _pearson(on_item, rest)
        undefined: str | None = None
        if r_pb is None:
            undefined = (
                f"every respondent scored the same on this item (p = {sum(on_item) / n:.3f}); "
                "a constant has no correlation"
                if len(set(on_item)) == 1
                else "the rest-scores do not vary across these respondents"
            )
        results[case] = ItemDiscrimination(
            case=case,
            should_fire=labels[case],
            r_pb=r_pb,
            n_respondents=n,
            undefined=undefined,
        )
    return results


def broken_item_screen(arms: Mapping[str, Sequence[Record]]) -> BrokenItemScreen:
    """Items at ``p == 0.0``, and separately the items at ``p == 1.0``.

    Estimator 3 of the registered four, and the cheapest screen there is: a 0%
    pass rate across many trials is more often a broken task than an incapable
    agent. It reports; it does not judge. An item on the floor may be
    mislabelled, may be genuinely hard, or may be the one this description was
    never going to reach, and telling those apart is a blind adjudication rather
    than an arithmetic.

    The ceiling set comes back beside it because it is the complementary fact and
    it is **not** a defect signal -- an item everything gets right may be
    trivially easy or may hide a shortcut, and neither is decided here.

    Raises:
        ArmError: as :func:`_respondent_grid` raises it.
    """
    difficulty = item_difficulty(arms)
    respondents, _, _, _ = _respondent_grid(arms)

    def _at(value: float, *, should_fire: bool) -> tuple[str, ...]:
        return tuple(
            case
            for case, item in difficulty.items()
            if item.p == value and item.should_fire is should_fire
        )

    return BrokenItemScreen(
        n_respondents=len(respondents),
        floor_positives=_at(0.0, should_fire=True),
        floor_negatives=_at(0.0, should_fire=False),
        ceiling_positives=_at(1.0, should_fire=True),
        ceiling_negatives=_at(1.0, should_fire=False),
    )


def triple_joint_outcomes(arms: Mapping[str, Sequence[Record]]) -> dict[str, TripleJoint]:
    """Per triple, the fraction of respondents that got all of its items right.

    Estimator 4 of the registered four. The three items of a triple are one
    positive and two negatives written from one body, so a respondent scores here
    only by firing on the decision *and* declining both non-decisions -- within
    its own repeat, never pooled across repeats, because a triple answered right
    across three different passes was never answered right once.

    A respondent with an unparseable row anywhere in the triple has no joint
    outcome and is dropped from that triple's denominator rather than counted as
    a failure. The surviving count is on every row.

    Raises:
        ArmError: if no record carries ``triple`` -- a version 2 checkpoint has
            none, and an empty table would read as a result; if only some records
            do, because dropping the rest changes the denominator without saying
            so; if one case id appears under two triple ids, which is two corpora
            appended to one respondent set; or as :func:`_respondent_grid` raises
            it.
    """
    respondents, _, correctness, _ = _respondent_grid(arms)
    rows = [row for _, records in sorted(arms.items()) for row in records]

    carried = [row for row in rows if row.get("triple") is not None]
    if not carried:
        raise ArmError(
            "no record carries 'triple', so there is no triple to score jointly. A version "
            "2 checkpoint has none, and a per-triple table over a corpus with no triples "
            "would be an empty table rather than a refusal."
        )
    if len(carried) != len(rows):
        raise ArmError(
            f"{len(rows) - len(carried)} of {len(rows)} record(s) carry no 'triple'. "
            "Dropping them would change the denominator without saying so, which is how "
            "every voided run in this instrument's history reported a plausible number."
        )

    members: dict[str, set[str]] = {}
    triple_of: dict[str, str] = {}
    for row in carried:
        case = str(row["case"])
        triple = str(row["triple"])
        if triple_of.setdefault(case, triple) != triple:
            raise ArmError(
                f"case {case!r} appears under two 'triple' labels, {triple_of[case]!r} and "
                f"{triple!r}. Two runs against different corpora have been appended to one "
                "respondent set."
            )
        members.setdefault(triple, set()).add(case)

    results: dict[str, TripleJoint] = {}
    for triple, cases in sorted(members.items()):
        complete = [
            respondent
            for respondent in respondents
            if all(respondent in correctness.get(case, {}) for case in cases)
        ]
        joint = (
            sum(1 for r in complete if all(correctness[case][r] for case in cases)) / len(complete)
            if complete
            else None
        )
        results[triple] = TripleJoint(
            triple=triple,
            joint=joint,
            n_respondents=len(complete),
            n_items=len(cases),
        )
    return results


def item_analysis(arms: Mapping[str, Sequence[Record]]) -> ItemAnalysis:
    """The four registered item estimators over one respondent set.

    Registered in
    ``notebook/2026-08-19-the-item-analysis-this-instrument-never-ran.md``, which
    is the pre-registration this implements and does not extend. Every number
    there is **descriptive**: none of it licenses a claim about an arm, and the
    entry says so.

    ``arms`` maps an arm name to its records; a respondent is one ``(arm,
    repeat)`` pair, so six two-repeat arms give the registered twelve. Passing a
    single arm is legitimate and gives as many respondents as it has repeats --
    the numbers are then about that arm alone and the discrimination column is
    mostly undefined, which is a property of the denominator rather than of the
    corpus.

    The values are ``Sequence`` and not ``Iterable`` because this walks each one
    five or six times -- once per estimator, and :func:`broken_item_screen`
    twice on its own. A generator would be empty from the second walk onward and
    the diagnosis would be ``arm 'x' holds no records``, which names the caller's
    argument type as a corpus defect.

    Positives and negatives are never averaged together: two means come back and
    there is no third.

    The registered respondent set is the **six description arms** -- ``full``,
    ``no-exclusions``, ``no-opener``, ``opener-only``, ``stakes-named``,
    ``stakes-shown`` -- at two repeats each. ``verdicts-in-situ`` is excluded by
    that entry, and :func:`_respondent_grid` refuses it rather than trusting the
    caller to leave it out.

    Raises:
        ArmError: as :func:`_respondent_grid` raises it. A records set carrying
            no triples is *not* an error here -- ``triples`` comes back empty
            with :attr:`ItemAnalysis.triples_unavailable` naming the reason,
            because the other three estimators are still computable and losing
            them to a v2 checkpoint would be a worse answer than saying which
            table is missing.
    """
    respondents, labels, correctness, unparseable = _respondent_grid(arms)
    difficulty = item_difficulty(arms)
    discrimination = item_discrimination(arms)
    screen = broken_item_screen(arms)

    triples: dict[str, TripleJoint] = {}
    triples_unavailable: str | None = None
    try:
        triples = triple_joint_outcomes(arms)
    except ArmError as error:
        triples_unavailable = str(error)

    positives = [item.p for item in difficulty.values() if item.should_fire]
    negatives = [item.p for item in difficulty.values() if not item.should_fire]
    correlations = [item.r_pb for item in discrimination.values() if item.r_pb is not None]
    return ItemAnalysis(
        respondents=respondents,
        n_items=len(difficulty),
        n_unparseable=unparseable,
        dropped=tuple(sorted(set(labels) - set(correctness))),
        difficulty=difficulty,
        discrimination=discrimination,
        screen=screen,
        triples=triples,
        triples_unavailable=triples_unavailable,
        incomplete_triples=tuple(name for name, triple in triples.items() if triple.n_items != 3),
        mean_difficulty_positive=sum(positives) / len(positives) if positives else None,
        mean_difficulty_negative=sum(negatives) / len(negatives) if negatives else None,
        median_discrimination=median(correlations) if correlations else None,
        n_discriminating=len(correlations),
    )


def load_arm(path: Path | str) -> list[Record]:
    """Every JSONL record at ``path``, read as UTF-8.

    The encoding is explicit because it has bitten this repository: Windows
    defaults to cp1252 and a checkpoint containing a typographic dash raises
    ``UnicodeDecodeError`` halfway through scoring a completed run. That, and
    ``json.JSONDecodeError`` on a half-written line, are the two failures a
    caller has to handle, and **both are ``ValueError`` subclasses rather than
    ``OSError``** -- a caller catching only the second loses a completed run's
    report to a file it merely read.

    Raises:
        OSError: if ``path`` cannot be read.
        UnicodeDecodeError: if it is not UTF-8.
        json.JSONDecodeError: if a non-blank line is not one JSON object.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def format_bands(bands: Mapping[str, ArmSummary]) -> Sequence[str]:
    """The per-band table as lines, so every report prints it the same way.

    The rate columns carry their denominators in ``n``, because the one thing
    this instrument has repeatedly published is a plausible rate over a
    denominator nobody stated. ``items`` sits beside ``n`` for the same reason:
    a band collected at three repeats while its neighbours are at two carries
    more rows than items, which is invisible in a rate and is the routine state
    of a resumed run.

    Bands that could not be scored, and band names the corpus does not declare,
    are printed under the table when the caller passed a :class:`BandTable`. A
    table missing ``xl`` and a table where ``xl`` does not differ read the same
    otherwise.
    """
    header = (
        f"  {'band':4s} {'n':>5s} {'items':>6s} {'reps':>5s} {'acc':>7s} "
        f"{'prec':>7s} {'recall':>7s} {'FPR':>7s}"
    )
    weights = {arm.weight for arm in bands.values()}
    lines = [f"  weighted by {'/'.join(sorted(weights))}", header]
    for band, arm in bands.items():
        reps = arm.n_records / arm.n_items if arm.n_items else 0.0
        lines.append(
            f"  {band:4s} {arm.n_records:5d} {arm.n_items:6d} {reps:5.1f} "
            f"{arm.accuracy:7.3f} {arm.precision:7.3f} "
            f"{arm.recall:7.3f} {arm.false_positive_rate:7.3f}"
        )
        if arm.missed:
            lines.append(f"       never fired: {', '.join(arm.missed)}")
    if isinstance(bands, BandTable):
        lines.extend(f"  NOT SCORED  {band}: {reason}" for band, reason in bands.unscoreable)
        if bands.unrecognised:
            lines.append(
                f"  band name(s) the corpus does not declare: {', '.join(bands.unrecognised)}"
            )
    return lines


def format_confusion(matrix: ConfusionMatrix) -> Sequence[str]:
    """The 2x2 table, the base rate it is drawn from, and the coefficient.

    The base rate is printed above the coefficient rather than below it because
    it is what makes the coefficient worth reading: an arm scoring 0.667
    accuracy on this corpus has matched the majority baseline exactly and could
    have done it by never firing.

    Where `ConfusionMatrix.mcc` is undefined this says so, names the margin
    that is empty, and states the conventional substitution instead of
    performing it. A reader who wants `sklearn`'s 0.0 can see the step being
    taken; a reader who wants to know the arm answered one way for everything
    is told that instead of being handed a number that looks like a
    measurement.

    Cells print at one decimal because item weighting makes them expected
    counts rather than counts -- an integer format would round 85.5 to 86 and
    silently claim a whole item.
    """
    lines = [
        f"  weighted by {matrix.weight}",
        f"  {'':14s} {'fired':>9s} {'silent':>9s}",
        f"  {'should fire':14s} {matrix.true_positives:9.1f} {matrix.false_negatives:9.1f}",
        f"  {'should not':14s} {matrix.false_positives:9.1f} {matrix.true_negatives:9.1f}",
        f"  base rate {matrix.base_rate:.4f} over {matrix.n:.1f}; "
        f"always-answer-the-larger-class accuracy is {matrix.majority_baseline:.4f}",
    ]
    if (mcc := matrix.mcc) is None:
        empty = [
            name
            for name, margin in (
                ("fired", matrix.true_positives + matrix.false_positives),
                ("silent", matrix.true_negatives + matrix.false_negatives),
                ("should fire", matrix.true_positives + matrix.false_negatives),
                ("should not", matrix.true_negatives + matrix.false_positives),
            )
            if margin <= 0
        ]
        lines.append(
            f"  MCC undefined: the {', '.join(empty)} margin(s) of this table are empty, so "
            "the coefficient divides by zero. The usual convention substitutes 0.000; that "
            "is stated here rather than printed as a result."
        )
    else:
        lines.append(f"  MCC {mcc:+.4f}   <- 0 for both degenerate arms, whatever the balance")
    return lines


def format_difference(difference: ClusteredRateDifference) -> Sequence[str]:
    """An unpaired clustered difference as lines.

    Prints the item-weighted rates and the record-weighted ones together,
    because the registered estimator is record-weighted and the clustered
    interval is item-weighted, and the two differ exactly when a run has been
    resumed. Prints the cluster counts beside the item counts for the same
    reason the class carries ``clustering_is_inert``: an interval over 40
    singleton clusters is the item-level interval, and calling it clustered is
    a word rather than a method.
    """
    lines = [
        f"  {difference.name_treatment} − {difference.name_control}  "
        f"{difference.difference:+.3f}  "
        f"[{difference.ci_low:+.3f}, {difference.ci_high:+.3f}] at {difference.confidence:.0%}",
        f"    per item      {difference.name_control} {difference.rate_control:.3f} "
        f"({difference.n_items_control} item(s) in {difference.n_clusters_control} cluster(s)), "
        f"{difference.name_treatment} {difference.rate_treatment:.3f} "
        f"({difference.n_items_treatment} in {difference.n_clusters_treatment})",
        f"    per record    {difference.name_control} "
        f"{difference.accuracy_control_over_records:.3f}, {difference.name_treatment} "
        f"{difference.accuracy_treatment_over_records:.3f}   <- the registered denominator",
        f"    ICC {difference.icc:.3f}, design effect {difference.design_effect:.2f}, "
        f"effective n {difference.effective_n:.1f}, {difference.n_resamples} resample(s)",
    ]
    if difference.clustering_is_inert:
        lines.append(
            "    CLUSTERING DID NOTHING: every cluster holds one item, so this is the "
            "item-level interval. Do not describe it as clustered."
        )
    return lines


def format_routing(result: RoutingByProcedure) -> Sequence[str]:
    """Routing per procedure as lines, with the rule on every line that carries a rate."""
    lines = [
        f"  rule {result.rule!r}: "
        + (
            "equality against routes[0], the runner's `covers` stamp"
            if result.rule == "first"
            else "membership in the whole routes tuple, what `evaluate_routing` applies"
        ),
        f"  {'procedure':10s} {'items':>6s} {'n':>5s} {'answ':>5s} "
        f"{'/item':>7s} {'/rec':>7s} {'/answ':>7s}",
    ]
    for name, group in result.groups.items():
        answered = "     --" if group.over_answered is None else f"{group.over_answered:7.3f}"
        lines.append(
            f"  {name:10s} {group.n_items:6d} {group.n_records:5d} {group.n_answered:5d} "
            f"{group.over_items:7.3f} {group.over_records:7.3f} {answered}"
        )
    grouped_items = sum(group.n_items for group in result.groups.values())
    lines.append(f"  {result.n_items} labelled item(s); the groups above hold {grouped_items}")
    if grouped_items != result.n_items:
        lines.append(
            "  ^ they do not add up on purpose: a turn with two acceptable routes is "
            "scored in both groups under rule 'any'."
        )
    return lines


def format_negative_kinds(kinds: Mapping[str, NegativeKindRate]) -> Sequence[str]:
    """False-positive rate per kind as lines, interval always beside the rate.

    The interval is not decoration here. Two of the seven kinds hold four items
    and one holds five, so their point estimates read 0.000 at almost any true
    rate and a table of point estimates alone would invite a ranking that the
    data cannot support.
    """
    lines = [
        f"  {'kind':10s} {'items':>6s} {'n':>5s} {'fires':>6s} {'FPR/item':>9s} "
        f"{'FPR/rec':>8s}  interval"
    ]
    for kind, rate in kinds.items():
        lines.append(
            f"  {kind:10s} {rate.n_items:6d} {rate.n_records:5d} {rate.n_fires:6d} "
            f"{rate.over_items:9.3f} {rate.over_records:8.3f}  "
            f"[{rate.ci_low:.3f}, {rate.ci_high:.3f}] at {rate.confidence:.0%}"
        )
        if rate.fired_on:
            lines.append(f"       fired on: {', '.join(rate.fired_on)}")
    return lines


def format_rate(name: str, rate: ClusteredRate) -> Sequence[str]:
    """A clustered rate as lines, naming the cluster count and the design effect.

    Both are printed because the interval is only wider than an item-level one
    to the extent the ICC says the clusters are real, and a reader who cannot
    see that has to take the width on trust.
    """
    lines = [
        f"  {name:24s} {rate.point_estimate:.3f}  "
        f"[{rate.ci_low:.3f}, {rate.ci_high:.3f}] at {rate.confidence:.0%}",
        f"  {'':24s} {rate.n_items} item(s) in {rate.n_clusters} cluster(s), "
        f"ICC {rate.icc:.3f}, design effect {rate.design_effect:.2f}, "
        f"effective n {rate.effective_n:.1f}",
    ]
    if rate.clustering_is_inert:
        lines.append(
            f"  {'':24s} CLUSTERING DID NOTHING: every cluster holds one item, so this "
            "is the item-level interval under another name."
        )
    return lines


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


def format_item_analysis(analysis: ItemAnalysis, *, worst: int = 10) -> Sequence[str]:
    """The item analysis as lines, respondent count first.

    The respondent count leads because it governs every number underneath it and
    because it is small: twelve is what the v4 records hold, classical item
    analysis assumes hundreds, and a table of point estimates with no denominator
    on the page invites a reading the data cannot support. One respondent is
    printed with the sentence that says what the screen degenerates to.

    Positives and negatives get their own mean and there is no pooled one, for
    the reason :class:`ItemDifficulty` gives. ``worst`` bounds **every** item
    list here -- the lowest discriminators, the hardest triples and the two
    floor sets -- so a 258-item corpus does not print 258 rows into a run's
    report; the counts above each list are complete either way. The floor sets
    are bounded for the same reason as the others and it bites hardest there:
    at ``--repeats 1`` every item is at ``p`` 0.0 or 1.0, so the floor is half
    the corpus.

    Each floor item carries **its own** respondent count, not the set's. An
    item that parsed on 2 of 12 rows is on the floor over two, and Anthropic's
    screen is premised on a 0% rate across *many* trials.
    """
    lines = [
        f"  respondents           {analysis.n_respondents} "
        f"{', '.join(f'{arm}/r{repeat}' for arm, repeat in analysis.respondents)}",
        f"  items scored          {analysis.n_items}",
        f"  unparseable rows      {analysis.n_unparseable}",
    ]
    if analysis.dropped:
        lines.append(
            f"       no parsed row at all, so no difficulty: {', '.join(analysis.dropped)}"
        )
    if not analysis.complete:
        lines.append(
            "  ^ the grid has holes, so each respondent's rest-score is a count over a "
            "different number of items and partly measures its own parse rate."
        )
    if analysis.n_respondents < 3:
        lines.append(
            "  ^ under three respondents, so no discrimination is reported below. At one "
            "respondent every p is 0.000 or 1.000 by construction and the screen is just "
            "what it got wrong and right; at two, a defined correlation is exactly +1.000 "
            "or -1.000 whatever the data say."
        )

    positive = analysis.mean_difficulty_positive
    negative = analysis.mean_difficulty_negative
    lines.extend(
        [
            "",
            f"  DIFFICULTY   mean p over the positives  "
            f"{'--' if positive is None else f'{positive:.3f}'}"
            f"   (a miss rate; 1.000 is never missed)",
            f"               mean p over the negatives  "
            f"{'--' if negative is None else f'{negative:.3f}'}"
            f"   (a false-fire rate; 1.000 is never fired)",
            "               never pooled: the two mean different things.",
        ]
    )

    median_r = analysis.median_discrimination
    lines.extend(
        [
            "",
            f"  DISCRIMINATION  median corrected r_pb  "
            f"{'--' if median_r is None else f'{median_r:+.3f}'} over "
            f"{analysis.n_discriminating} of {analysis.n_items} item(s)",
            "                  the rest are undefined, not zero: an item every "
            "respondent scored the same on has no correlation.",
        ]
    )
    negatives_first = sorted(
        ((item.r_pb, item) for item in analysis.discrimination.values() if item.r_pb is not None),
        key=lambda pair: (pair[0], pair[1].case),
    )
    if negatives_first:
        lowest = negatives_first[:worst]
        lines.append(f"                  lowest {len(lowest)} of {len(negatives_first)}:")
        lines.extend(
            f"                    {item.case:10s} {r_pb:+.3f}  "
            f"p {analysis.difficulty[item.case].p:.3f}"
            for r_pb, item in lowest
        )

    screen = analysis.screen

    def _floor(cases: tuple[str, ...]) -> str:
        """Each floor item with **its own** denominator, capped at ``worst``.

        The set-wide respondent count is not this item's denominator. An item
        that parsed on 2 of 12 rows sits on the floor over two, and the screen
        being borrowed here -- a 0% pass rate *across many trials* -- is a claim
        about the trials that item actually got.
        """
        if not cases:
            return "none"
        shown = ", ".join(
            f"{case} (over {analysis.difficulty[case].n_respondents})" for case in cases[:worst]
        )
        return shown if len(cases) <= worst else f"{shown}, and {len(cases) - worst} more"

    lines.extend(
        [
            "",
            f"  SCREEN  p == 0.000 on {len(screen.floor_positives)} positive(s) and "
            f"{len(screen.floor_negatives)} negative(s); the set holds "
            f"{screen.n_respondents} respondent(s) and each item below carries its own",
            f"          positives: {_floor(screen.floor_positives)}",
            f"          negatives: {_floor(screen.floor_negatives)}",
            f"          p == 1.000 on {len(screen.ceiling_positives)} positive(s) and "
            f"{len(screen.ceiling_negatives)} negative(s) -- the ceiling term, "
            "not a defect signal",
            "          A screen, not a verdict. Nothing here moves a label.",
        ]
    )

    lines.append("")
    if analysis.triples_unavailable is not None:
        lines.append(f"  TRIPLES not available: {analysis.triples_unavailable}")
        return lines
    scored = [
        (triple.joint, triple) for triple in analysis.triples.values() if triple.joint is not None
    ]
    lines.append(
        f"  TRIPLES  {len(scored)} of {len(analysis.triples)} triple(s) have a joint outcome"
    )
    if scored:
        # The mean is over the *complete* triples only. A two-item triple is
        # cleared by getting two items right, so pooling it with the three-item
        # ones raises the mean in one direction -- and the line below already
        # says that "all three" over another count is a different statistic.
        complete = [(joint, triple) for joint, triple in scored if triple.n_items == 3]
        partial = [triple for _, triple in scored if triple.n_items != 3]
        if complete:
            mean_joint = sum(joint for joint, _ in complete) / len(complete)
            lines.append(
                f"           mean J_t  {mean_joint:.3f}   over the {len(complete)} triple(s) "
                "holding three items: all three right in one respondent's own repeat"
            )
        else:
            lines.append(
                "           mean J_t  --   no scored triple holds three items, and "
                "'all three' over another count is a different statistic"
            )
        if partial:
            lines.append(
                f"           {len(partial)} scored triple(s) hold other than three items and "
                "are out of that mean -- named under NOT THREE ITEMS below"
            )
        hardest = sorted(scored, key=lambda pair: (pair[0], pair[1].triple))[:worst]
        lines.append(f"           lowest {len(hardest)} of {len(scored)}:")
        lines.extend(
            f"             {triple.triple:10s} {joint:.3f} "
            f"over {triple.n_respondents} respondent(s)"
            + ("" if triple.n_items == 3 else f", {triple.n_items} item(s)")
            for joint, triple in hardest
        )
    unscored = [triple.triple for triple in analysis.triples.values() if triple.joint is None]
    if unscored:
        lines.append(
            f"           no respondent observed every item of: {', '.join(unscored)} "
            "-- absent, not 0.000"
        )
    if analysis.incomplete_triples:
        lines.append(
            f"           NOT THREE ITEMS: {', '.join(analysis.incomplete_triples)}. "
            "'All three' over another count is a different statistic."
        )
    return lines
