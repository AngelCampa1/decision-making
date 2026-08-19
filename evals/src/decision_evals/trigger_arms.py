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

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
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
    if (reason := venue_comparable(rows_a, rows_b)) is not None:
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
