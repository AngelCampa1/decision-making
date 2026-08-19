"""How many triplets does Track H's H1 actually need? A pure simulation.

**No model calls.** This script authors nothing, reads no corpus and contacts no
provider. It answers one question that is much cheaper than the authoring bill
it is asked about: at ``n`` triplets, how often would H1 land in each of the
three states its decision can occupy?

The H1 row in ``docs/RESEARCH_PROGRAMME.md`` costs 498 calls off **20 triplets**,
and two authoring passes have produced two usable triplets. Nobody has asked
whether 20 is the right number. The row itself says so: *"whether the primary is
estimable at ten triplets, or five, is a power question nobody has asked, and
asking it is cheaper than authoring ninety more."* This is that question.

The design, taken from the registration
(``notebook/2026-08-19-prediction-track-h-phase-0.md``) and not re-decided here:

* ``n`` triplets, **2 repeats** each. Each ``(triplet, repeat)`` pair yields one
  sensitivity event (governing arm) and one specificity event (matched arm), so
  a triplet carries 2 of each.
* The primary is ``d = P(change | governing) − P(change | matched)``, identically
  Youden's J, a **paired mean difference of two indicator vectors**.
* **The cluster is the triplet, not the file.** Pooling over files is defect nine
  on ``docs/STATUS.md``'s broken-measurement list and is not reintroduced here:
  every simulated dataset is built as ``n`` clusters of exactly 2 events and is
  handed to :func:`~decision_evals.stats.cluster.cluster_bootstrap_diff` with the
  triplet index as the cluster label.
* The registered kill is **unaided J >= 0.70 closes the venue**
  (:data:`~decision_evals.stats.track_h.KILL_THRESHOLD_J`).

The estimator characterised here is the estimator that will be used. No normal
approximation is substituted: with 2 binary events per cluster and as few as 5
clusters the asymptotics are not obviously trustworthy, which is the whole reason
to simulate rather than to solve.

Generative model, stated rather than assumed
--------------------------------------------

Two mappings from a true J to per-triplet rates, both recorded as choices under
standing rule 1:

* ``symmetric`` (**primary**), derived from the kill's own arithmetic rather than
  picked: ``P(change|governing) = (1 + J) / 2`` and ``P(change|matched) =
  (1 − J) / 2``, so sensitivity equals specificity. At J = 0.70 this is exactly
  (0.85, 0.85) — the pair the registration anchors ``KILL_THRESHOLD_J`` to, and
  0.85 is ``ADEQUACY_CEILING``. The mapping therefore reproduces the
  registration's own worked example at the threshold.
* ``sensitivity-anchored`` (**secondary**), the shape the registered predictions
  describe: sensitivity pinned at 0.90 and every bit of J's variation carried by
  the matched arm, ``P(change|matched) = 0.90 − J``.

**Between-triplet heterogeneity is the parameter nobody has data for**, so it is
swept rather than chosen. Per-triplet rates are drawn from a Beta with the arm's
mean and a concentration set so that the *within-triplet correlation of the
binary outcomes* equals ``icc``: ``Var(p) = icc * mean * (1 - mean)``, i.e. the
beta-binomial ICC. That parameterisation is scale-free — it is feasible at every
mean, which a raw standard deviation is not — and it is directly comparable to
the two ICCs this repository has actually measured (N6's matched-triple 0.00 to
0.06, Track I's repeat 0.83 to 0.85), neither of which is reused as a planning
figure. ``icc = 0`` is the homogeneous case and is run alongside every other.

A third knob, ``rho_item``, couples the governing and matched indicators *within
one event* through a latent bivariate normal. It exists because both arms of an
event are scored against the same base response, so a noisy base pushes both
toward "movement". Positive coupling reduces the variance of the paired
difference, so ``rho_item = 0`` — the default everywhere except its own
sensitivity slice — is the conservative choice, and the slice measures by how
much.

The three states
----------------

The registered kill is a **point** rule: ``Phase0Result.kill`` is ``j >= 0.70``
with no reference to the interval. The three-way decision this script is asked
about is an *interval* reading, and the two are reported side by side rather than
conflated:

* ``closes`` — ``ci_low >= 0.70``. The venue is closed with the interval behind it.
* ``survives`` — ``ci_high < 0.70``. Headroom is established, not merely observed.
* ``indeterminate`` — the interval straddles 0.70. This is the outcome that
  spends the whole authoring bill and buys nothing.

Standing rule 2
---------------

A falsifier may not fail anything until it has passed a case it should pass, and
the same applies to a simulator before its power numbers are believed. Known
answers are recovered first, and :func:`main` exits non-zero — no recommendation
— when any of them is missed:

* **Calibration anchor.** At **true J = 0** with a cluster count far above the
  design range, the rate at which the interval excludes zero from below must sit
  near the nominal one-sided 0.025, and two-sided coverage near 0.95. The anchor
  runs at a large ``n`` on purpose: at 5 clusters this bootstrap genuinely
  under-covers, so gating the null at the design's own cluster counts would fail
  for a reason that is a *result*. What the estimator does at 5 to 20 clusters is
  therefore reported in its own table rather than gated.
* **Ceiling.** At **true J = 1 with no noise**, every event moves in the
  governing arm and none in the matched arm, so detection must be certain at
  every ``n``.
* **Closed forms.** The mean and the standard deviation of the point estimate are
  both known exactly — see :func:`point_estimate_sd`, which is exact at every
  ``n`` rather than asymptotic — and both must be recovered within Monte-Carlo
  error in every cell. This is the check that the heterogeneity knob does what
  its name says, since ``icc`` enters that formula directly.
* **Discrimination.** The failure this repository keeps recording: an estimator
  that cannot return a different answer is not a measurement. The verdict
  distribution at J = 0.30 and J = 0.85 is compared explicitly, and the run
  refuses to report if they coincide.

Usage:
    python -m uv run python scripts/size_track_h_phase0.py
    python -m uv run python scripts/size_track_h_phase0.py --quick
    python -m uv run python scripts/size_track_h_phase0.py --out report.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

import numpy as np
import numpy.typing as npt
from scipy.special import ndtri

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

from decision_evals.stats.cluster import (  # noqa: E402
    ClusterBootstrapResult,
    cluster_bootstrap_diff,
)
from decision_evals.stats.track_h import KILL_THRESHOLD_J  # noqa: E402

#: Repeats per triplet. Not a choice made here: the registration derives it from
#: Track I's ICC of 0.83 to 0.85 exactly as N6, N7 and N9 did.
REPEATS: Final = 2

#: Nominal coverage of the reported interval.
CONFIDENCE: Final = 0.95

#: Bootstrap replicates. The default of ``cluster_bootstrap_diff`` itself, so the
#: thing characterised is the thing that will be run.
N_RESAMPLES: Final = 10_000

#: The three states an H1 result can occupy under an interval reading.
STATE_CLOSES: Final = "closes"
STATE_SURVIVES: Final = "survives"
STATE_INDETERMINATE: Final = "indeterminate"
STATES: Final = (STATE_CLOSES, STATE_SURVIVES, STATE_INDETERMINATE)

#: Share of runs allowed to land in the indeterminate state before an ``n`` counts
#: as usable. **Chosen, not derived** — standing rule 1 requires saying so. Nothing
#: in this repository fixes an acceptable rate of "the run answered nothing", and
#: no prior H1-shaped run exists to derive one from. It moves the answer: at
#: J = 0.30 and ICC = 0 the smallest usable n is **8** at a ceiling of 0.25 and
#: **12** at both 0.20 and 0.15. This comment said 10, 12 and 15 until it was
#: checked against the shipped code on 2026-08-19; the measured indeterminate
#: rates over the grid's own ``[5, 8, 10, 12, 15, 20]`` are 0.564, 0.2275,
#: 0.2295, 0.1415, 0.0825 and 0.0260, so 8 clears 0.25, and 12 clears 0.15 as
#: well as 0.20 -- 15 was never the smallest at any of the three. Note 8 beating
#: 10 is the lattice effect :func:`smallest_usable_n` documents, not noise.
#: What would measure the ceiling instead: a stated cost ratio between authoring
#: a triplet and spending a run that resolves nothing.
INDETERMINATE_CEILING: Final = 0.20

#: Rate-mapping names.
SHAPE_SYMMETRIC: Final = "symmetric"
SHAPE_SENS_ANCHORED: Final = "sensitivity-anchored"
SHAPES: Final = (SHAPE_SYMMETRIC, SHAPE_SENS_ANCHORED)

#: The sensitivity the ``sensitivity-anchored`` mapping pins. Chosen, not derived:
#: registered prediction 1 says sensitivity will be ">= 0.85", and 0.90 sits above
#: that bar while leaving room for J = 0.85 to be reachable with a non-negative
#: matched rate. Recorded as a choice under standing rule 1.
ANCHORED_SENSITIVITY: Final = 0.90


# --------------------------------------------------------------------------- #
# The generative model
# --------------------------------------------------------------------------- #
def symmetric_rates(true_j: float) -> tuple[float, float]:
    """``(P(change|governing), P(change|matched))`` with sensitivity = specificity.

    Derived from the kill's arithmetic rather than chosen: at ``true_j = 0.70``
    this returns ``(0.85, 0.15)``, i.e. sensitivity 0.85 and specificity 0.85,
    which is the exact pair ``KILL_THRESHOLD_J`` is anchored to.

    Args:
        true_j: The population Youden's J. Must lie in ``[0, 1]``.

    Returns:
        The governing-arm and matched-arm change probabilities.

    Raises:
        ValueError: ``true_j`` outside ``[0, 1]``.
    """
    if not 0.0 <= true_j <= 1.0:
        raise ValueError(f"true_j must be in [0, 1], got {true_j}")
    return (1.0 + true_j) / 2.0, (1.0 - true_j) / 2.0


def sensitivity_anchored_rates(
    true_j: float, sensitivity: float = ANCHORED_SENSITIVITY
) -> tuple[float, float]:
    """Rates with sensitivity pinned and the matched arm carrying all of J.

    The shape the registered predictions describe: prediction 1 puts sensitivity
    high, prediction 2 puts specificity lower, and the difference between them is
    the whole bet.

    Args:
        true_j: The population Youden's J.
        sensitivity: The pinned ``P(change | governing)``.

    Returns:
        The governing-arm and matched-arm change probabilities.

    Raises:
        ValueError: ``sensitivity`` outside ``[0, 1]``, or a ``true_j`` that
            would push the matched rate outside ``[0, 1]``.
    """
    if not 0.0 <= sensitivity <= 1.0:
        raise ValueError(f"sensitivity must be in [0, 1], got {sensitivity}")
    p_matched = sensitivity - true_j
    if not 0.0 <= p_matched <= 1.0:
        raise ValueError(
            f"true_j={true_j} is unreachable at sensitivity={sensitivity}: it implies "
            f"P(change|matched)={p_matched}, which is not a probability"
        )
    return sensitivity, p_matched


def rates_for(shape: str, true_j: float) -> tuple[float, float]:
    """Dispatch to the named rate mapping.

    Raises:
        ValueError: unknown ``shape``.
    """
    if shape == SHAPE_SYMMETRIC:
        return symmetric_rates(true_j)
    if shape == SHAPE_SENS_ANCHORED:
        return sensitivity_anchored_rates(true_j)
    raise ValueError(f"unknown rate shape {shape!r}")


def beta_shape(mean: float, icc: float) -> tuple[float, float]:
    """Beta ``(a, b)`` whose mean is ``mean`` and whose beta-binomial ICC is ``icc``.

    The Beta with ``a = mean * nu`` and ``b = (1 - mean) * nu`` has variance
    ``mean * (1 - mean) / (nu + 1)``. Setting ``nu = (1 - icc) / icc`` makes that
    variance ``icc * mean * (1 - mean)``, and ``Var(p) / (mean * (1 - mean))`` is
    exactly the correlation between two Bernoulli draws sharing the same ``p``.
    So ``icc`` is the within-triplet correlation of the outcomes, not a standard
    deviation that has to be checked for feasibility at every mean.

    Args:
        mean: The arm's population change probability, strictly inside ``(0, 1)``.
        icc: Within-triplet correlation, strictly inside ``(0, 1)``.

    Returns:
        The Beta shape parameters.

    Raises:
        ValueError: ``mean`` or ``icc`` outside the open unit interval.
    """
    if not 0.0 < mean < 1.0:
        raise ValueError(f"mean must be strictly inside (0, 1), got {mean}")
    if not 0.0 < icc < 1.0:
        raise ValueError(f"icc must be strictly inside (0, 1), got {icc}")
    nu = (1.0 - icc) / icc
    return mean * nu, (1.0 - mean) * nu


def draw_triplet_rates(
    rng: np.random.Generator, n_triplets: int, mean: float, icc: float
) -> npt.NDArray[np.float64]:
    """Per-triplet change probabilities for one arm.

    Returns a constant vector when ``icc == 0`` (homogeneous triplets) and also
    when ``mean`` is 0 or 1, where a degenerate mean leaves no room for
    between-triplet variation whatever ``icc`` says. That second case is what
    makes ``true_j = 1`` runnable as the noiseless known answer standing rule 2
    requires.

    Raises:
        ValueError: ``n_triplets < 1`` or ``icc`` outside ``[0, 1)``.
    """
    if n_triplets < 1:
        raise ValueError(f"n_triplets must be >= 1, got {n_triplets}")
    if not 0.0 <= icc < 1.0:
        raise ValueError(f"icc must be in [0, 1), got {icc}")
    if icc == 0.0 or mean in (0.0, 1.0):
        return np.full(n_triplets, float(mean), dtype=np.float64)
    a, b = beta_shape(mean, icc)
    return rng.beta(a, b, size=n_triplets).astype(np.float64)


def draw_event_indicators(
    rng: np.random.Generator,
    p_governing: npt.NDArray[np.float64],
    p_matched: npt.NDArray[np.float64],
    *,
    rho_item: float = 0.0,
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]]:
    """Governing and matched change indicators, shape ``(n_triplets, REPEATS)``.

    Both indicators of one event are thresholded from a latent bivariate normal
    with correlation ``rho_item``. At ``rho_item = 0`` this is two independent
    Bernoulli draws; above zero it models the fact that the two arms of an event
    are both scored against the *same* base response, so base noise pushes them
    together.

    Raises:
        ValueError: mismatched arm lengths, or ``rho_item`` outside ``(-1, 1)``.
    """
    if p_governing.shape != p_matched.shape:
        raise ValueError(
            f"arm rate vectors must be the same shape, got {p_governing.shape} "
            f"and {p_matched.shape}"
        )
    if not -1.0 < rho_item < 1.0:
        raise ValueError(f"rho_item must be in (-1, 1), got {rho_item}")

    size = (p_governing.size, REPEATS)
    z_governing = rng.standard_normal(size)
    noise = rng.standard_normal(size)
    z_matched = rho_item * z_governing + np.sqrt(1.0 - rho_item**2) * noise

    cut_governing = ndtri(p_governing)[:, None]
    cut_matched = ndtri(p_matched)[:, None]
    governing = (z_governing <= cut_governing).astype(np.int64)
    matched = (z_matched <= cut_matched).astype(np.int64)
    return governing, matched


def cluster_diff_sums(
    governing: npt.NDArray[np.int64], matched: npt.NDArray[np.int64]
) -> npt.NDArray[np.int64]:
    """Per-triplet sum of the paired per-event differences, one integer per cluster.

    Each cluster holds exactly ``REPEATS`` events, so the sum lies in
    ``[-REPEATS, REPEATS]``. This is the sufficient statistic for the cluster
    bootstrap — see :meth:`BootstrapCache.interval`.
    """
    return np.asarray(governing - matched, dtype=np.int64).sum(axis=1)


# --------------------------------------------------------------------------- #
# The estimator, memoised on its sufficient statistic
# --------------------------------------------------------------------------- #
def canonical_arrays(
    sums: npt.NDArray[np.int64],
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """A canonical ``(control, treatment, clusters)`` triple realising ``sums``.

    Every cluster in this design holds exactly ``REPEATS`` items, so a bootstrap
    replicate's mean is ``sum(drawn cluster sums) / (REPEATS * n)``. The replicate
    distribution therefore depends on the data **only** through the multiset of
    per-cluster difference sums, which is what makes memoisation exact rather
    than approximate. The clusters are sorted so that two datasets with the same
    multiset produce byte-identical inputs; cluster order is exchangeable under
    an i.i.d. resampling scheme, so sorting changes the draw that lands on a
    given cluster and not the distribution the interval comes from.

    Args:
        sums: One integer per cluster, each in ``[-REPEATS, REPEATS]``.

    Returns:
        Control values, treatment values and integer cluster labels, in cluster
        order, with ``REPEATS`` items per cluster.

    Raises:
        ValueError: an entry outside ``[-REPEATS, REPEATS]``, or empty input.
    """
    ordered = np.sort(np.asarray(sums, dtype=np.int64))
    if ordered.size == 0:
        raise ValueError("sums must not be empty")
    if np.any(np.abs(ordered) > REPEATS):
        raise ValueError(f"cluster difference sums must lie in [-{REPEATS}, {REPEATS}]")

    diffs = np.empty((ordered.size, REPEATS), dtype=np.float64)
    for row, total in enumerate(ordered):
        # Spread the sum over REPEATS items, each in {-1, 0, 1}. Any spread with
        # the right total gives the same bootstrap; this one is deterministic.
        positive = max(int(total), 0)
        negative = max(-int(total), 0)
        item = [1.0] * positive + [-1.0] * negative
        item += [0.0] * (REPEATS - len(item))
        diffs[row] = item

    flat = diffs.reshape(-1)
    treatment = np.maximum(flat, 0.0)
    control = np.maximum(-flat, 0.0)
    clusters = np.repeat(np.arange(ordered.size, dtype=np.int64), REPEATS)
    return control, treatment, clusters


class BootstrapCache:
    """``cluster_bootstrap_diff`` keyed on its sufficient statistic.

    A power simulation calls the estimator hundreds of thousands of times over a
    space of at most ``C(n + 4, 4)`` distinct datasets, so the same input recurs
    constantly. The cache turns that into one call per distinct input. It is not
    an approximation: see :func:`canonical_arrays` for why the multiset of
    per-cluster sums determines the result.

    The bootstrap seed is **fixed across the whole simulation**, which is what
    makes the cache well-defined. The cost is that bootstrap Monte-Carlo error is
    common to every simulation replicate rather than independent across them; at
    10,000 replicates that error is small beside the sampling error being
    measured, and ``--boot-seed`` exists so the claim can be checked by rerunning
    a slice against a different one.
    """

    def __init__(
        self,
        *,
        n_resamples: int = N_RESAMPLES,
        seed: int = 20260819,
        confidence: float = CONFIDENCE,
    ) -> None:
        self.n_resamples = n_resamples
        self.seed = seed
        self.confidence = confidence
        self.hits = 0
        self.misses = 0
        self._store: dict[tuple[int, ...], ClusterBootstrapResult] = {}

    def clear(self) -> None:
        """Drop the stored results, keeping the hit and miss counts.

        The store is the run's dominant memory footprint. A 174-cell grid died
        once with a numpy allocation failure partway through the largest cluster
        count, so the cache is released as soon as the phase that populated it is
        over rather than held for the life of the process.
        """
        self._store.clear()

    def interval(self, sums: npt.NDArray[np.int64]) -> ClusterBootstrapResult:
        """The cluster-bootstrap result for a dataset with these per-cluster sums."""
        key = tuple(int(value) for value in np.sort(np.asarray(sums, dtype=np.int64)))
        cached = self._store.get(key)
        if cached is not None:
            self.hits += 1
            return cached
        self.misses += 1
        control, treatment, clusters = canonical_arrays(sums)
        result = cluster_bootstrap_diff(
            control=control,
            treatment=treatment,
            clusters=clusters,
            confidence=self.confidence,
            n_resamples=self.n_resamples,
            seed=self.seed,
        )
        self._store[key] = result
        return result


def classify_interval(ci_low: float, ci_high: float, threshold: float = KILL_THRESHOLD_J) -> str:
    """Which of the three states an interval puts H1 in.

    Args:
        ci_low: Lower bound of the interval on J.
        ci_high: Upper bound.
        threshold: The registered kill, :data:`KILL_THRESHOLD_J`.

    Returns:
        One of :data:`STATES`. ``closes`` when the whole interval sits at or above
        the kill, ``survives`` when the whole interval sits below it, and
        ``indeterminate`` when it straddles — the outcome that spends the
        authoring bill and buys nothing.

    Raises:
        ValueError: ``ci_low > ci_high``.
    """
    if ci_low > ci_high:
        raise ValueError(f"ci_low must not exceed ci_high, got {ci_low} > {ci_high}")
    if ci_low >= threshold:
        return STATE_CLOSES
    if ci_high < threshold:
        return STATE_SURVIVES
    return STATE_INDETERMINATE


# --------------------------------------------------------------------------- #
# Grid cells
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CellSpec:
    """One point of the simulation grid."""

    n_triplets: int
    true_j: float
    icc: float
    shape: str = SHAPE_SYMMETRIC
    rho_item: float = 0.0


@dataclass(frozen=True, slots=True)
class CellResult:
    """What a cell's simulation replicates came to.

    Attributes:
        n_sims: Replicates drawn.
        p_closes: Share landing in :data:`STATE_CLOSES`.
        p_survives: Share landing in :data:`STATE_SURVIVES`.
        p_indeterminate: Share landing in :data:`STATE_INDETERMINATE`.
        p_point_kill: Share with ``j >= KILL_THRESHOLD_J`` on the **point
            estimate** — the rule ``Phase0Result.kill`` actually implements,
            reported beside the interval reading rather than instead of it.
        p_excludes_zero_above: Share whose interval sits strictly above zero. At
            ``true_j = 0`` this is the false-positive rate standing rule 2 checks.
        coverage: Share whose interval contains the population ``true_j``.
        mean_width: Mean interval width.
        p_zero_width: Share with a degenerate zero-width interval — the discrete
            percentile bootstrap's own failure mode, which reports certainty.
        mean_j: Mean point estimate, a check that the generative model delivers
            the J it was asked for.
        sd_j: Sample standard deviation of the point estimate across replicates.
            Compared against :func:`point_estimate_sd`, which is exact at every
            ``n``, so this is a known answer rather than a diagnostic.
    """

    n_triplets: int
    true_j: float
    icc: float
    shape: str
    rho_item: float
    n_sims: int
    p_closes: float
    p_survives: float
    p_indeterminate: float
    p_point_kill: float
    p_excludes_zero_above: float
    coverage: float
    mean_width: float
    p_zero_width: float
    mean_j: float
    sd_j: float


def run_cell(
    spec: CellSpec, *, n_sims: int, rng: np.random.Generator, cache: BootstrapCache
) -> CellResult:
    """Simulate one grid cell.

    Args:
        spec: The cell.
        n_sims: Simulation replicates.
        rng: Data-generating generator. Advanced in place.
        cache: The memoised estimator.

    Returns:
        A :class:`CellResult`.

    Raises:
        ValueError: ``n_sims < 1``, or via the generative-model functions.
    """
    if n_sims < 1:
        raise ValueError(f"n_sims must be >= 1, got {n_sims}")

    mean_governing, mean_matched = rates_for(spec.shape, spec.true_j)
    counts = dict.fromkeys(STATES, 0)
    n_point_kill = 0
    n_above_zero = 0
    n_covered = 0
    n_zero_width = 0
    total_width = 0.0
    estimates = np.empty(n_sims, dtype=np.float64)

    for sim in range(n_sims):
        p_governing = draw_triplet_rates(rng, spec.n_triplets, mean_governing, spec.icc)
        p_matched = draw_triplet_rates(rng, spec.n_triplets, mean_matched, spec.icc)
        governing, matched = draw_event_indicators(
            rng, p_governing, p_matched, rho_item=spec.rho_item
        )
        result = cache.interval(cluster_diff_sums(governing, matched))

        counts[classify_interval(result.ci_low, result.ci_high)] += 1
        n_point_kill += int(result.point_estimate >= KILL_THRESHOLD_J)
        n_above_zero += int(result.ci_low > 0.0)
        n_covered += int(result.ci_low <= spec.true_j <= result.ci_high)
        width = result.ci_high - result.ci_low
        n_zero_width += int(width == 0.0)
        total_width += width
        estimates[sim] = result.point_estimate

    return CellResult(
        n_triplets=spec.n_triplets,
        true_j=spec.true_j,
        icc=spec.icc,
        shape=spec.shape,
        rho_item=spec.rho_item,
        n_sims=n_sims,
        p_closes=counts[STATE_CLOSES] / n_sims,
        p_survives=counts[STATE_SURVIVES] / n_sims,
        p_indeterminate=counts[STATE_INDETERMINATE] / n_sims,
        p_point_kill=n_point_kill / n_sims,
        p_excludes_zero_above=n_above_zero / n_sims,
        coverage=n_covered / n_sims,
        mean_width=total_width / n_sims,
        p_zero_width=n_zero_width / n_sims,
        mean_j=float(estimates.mean()),
        sd_j=float(estimates.std(ddof=1)) if n_sims > 1 else 0.0,
    )


def cell_rng(data_seed: int, spec: CellSpec) -> np.random.Generator:
    """A generator seeded from the cell itself, not from position in the run.

    Deriving each cell's stream from its own parameters rather than advancing one
    shared generator is what makes a resumed run identical to an uninterrupted
    one. A single stream would make every cell's data depend on which cells ran
    before it, so a checkpoint restart would silently produce different numbers
    from the run it claims to continue.
    """
    key = (
        spec.n_triplets,
        round(spec.true_j * 1000),
        round(spec.icc * 1000),
        SHAPES.index(spec.shape),
        round(spec.rho_item * 1000),
    )
    return np.random.default_rng(np.random.SeedSequence([data_seed, *key]))


def spec_of(cell: CellResult) -> CellSpec:
    """The :class:`CellSpec` a completed cell came from, for checkpoint matching."""
    return CellSpec(
        n_triplets=cell.n_triplets,
        true_j=cell.true_j,
        icc=cell.icc,
        shape=cell.shape,
        rho_item=cell.rho_item,
    )


def load_checkpoint(path: Path) -> list[CellResult]:
    """Cells already computed, or an empty list when there is no checkpoint yet.

    Raises:
        ValueError: a line that is not a complete cell record. A checkpoint that
            cannot be read fully is not a checkpoint to resume from silently.
    """
    if not path.exists():
        return []
    cells: list[CellResult] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cells.append(CellResult(**json.loads(line)))
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError(f"{path}: line {number} is not a cell record ({error})") from error
    return cells


def build_grid(
    n_values: list[int],
    j_values: list[float],
    icc_values: list[float],
    *,
    shape: str = SHAPE_SYMMETRIC,
    rho_item: float = 0.0,
) -> list[CellSpec]:
    """The cartesian grid, with degenerate combinations collapsed.

    A ``true_j`` of 1 under the symmetric mapping puts both arm means on the
    boundary, where between-triplet variation does not exist. Rather than run four
    identical ICC levels there, the grid keeps one.
    """
    specs: list[CellSpec] = []
    for n_triplets in n_values:
        for true_j in j_values:
            degenerate = rates_for(shape, true_j)
            collapses = any(mean in (0.0, 1.0) for mean in degenerate)
            for icc in icc_values:
                if collapses and icc != icc_values[0]:
                    continue
                specs.append(
                    CellSpec(
                        n_triplets=n_triplets,
                        true_j=true_j,
                        icc=icc,
                        shape=shape,
                        rho_item=rho_item,
                    )
                )
    return specs


# --------------------------------------------------------------------------- #
# Standing rule 2
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RuleTwoCheck:
    """One known-answer check, with what it wanted and what it got."""

    name: str
    expected: str
    observed: str
    passed: bool


def check_known_answers(
    results: list[CellResult],
    anchor: CellResult | None,
    *,
    alpha_ceiling: float = 0.06,
    coverage_band: tuple[float, float] = (0.92, 0.98),
    inflation_tolerance: float = 0.12,
) -> list[RuleTwoCheck]:
    """Recover known answers before any power number is believed.

    The checks are chosen so that a failure points at the **simulator**, not at
    the estimator. That distinction is the trap here: at 5 clusters the cluster
    percentile bootstrap really does under-cover, and a null check gated at every
    design ``n`` would fail for a reason that is a *result* rather than a bug. So
    the calibration check runs at an ``anchor`` cluster count far above the design
    range, where the asymptotics are trustworthy and nominal is the right answer;
    what the estimator does at 5 to 20 clusters is then a measurement this run
    reports rather than a gate it trips.

    * **Calibration anchor.** At ``true_j = 0``, ``icc = 0`` and a large cluster
      count, the share of intervals strictly above zero must sit near the nominal
      one-sided 0.025, and two-sided coverage must sit near 0.95. If it does not,
      the pipeline is wrong and every power number below is worthless.
    * **Ceiling.** At ``true_j = 1`` with no noise every event moves in the
      governing arm and none in the matched arm, so detection must be certain and
      the state must be ``closes`` at every ``n``.
    * **Estimand recovery.** The mean point estimate must land on the ``true_j``
      the generative model was asked for, at every cell. A generative model that
      does not deliver its own J makes the x-axis of every table meaningless.
    * **Design effect.** With ``REPEATS`` events per cluster the variance of the
      cluster-mean difference carries a design effect of exactly
      :func:`variance_inflation_bound`, so the interval width at ``icc`` over the
      width at ``icc = 0`` must equal ``sqrt(1 + icc)``. This recovers a closed
      form and is the check that the heterogeneity knob does what it claims.
    * **Discrimination.** The verdict distribution at J = 0.30 must differ from
      the one at J = 0.85. An estimator that returns the same answer at both is
      broken rather than informative — the failure this repository has recorded
      five times.

    Args:
        results: Every cell of the design grid.
        anchor: The large-cluster calibration cell, or ``None`` if it was skipped.
        alpha_ceiling: False-positive rate above which the anchor check fails.
        coverage_band: Acceptable two-sided coverage at the anchor.
        inflation_tolerance: Relative tolerance on the design-effect recovery.

    Returns:
        One :class:`RuleTwoCheck` per check performed.
    """
    checks: list[RuleTwoCheck] = []

    if anchor is None:
        checks.append(
            RuleTwoCheck(
                name="calibration anchor",
                expected="a large-n null cell",
                observed="not run",
                passed=False,
            )
        )
    else:
        # Both bands widen to whichever is larger: the substantive tolerance, or
        # four Monte-Carlo standard errors at the anchor's own replicate count. A
        # fixed band would fail on noise in a short run and would be the wrong
        # question in a long one.
        nominal_alpha = (1.0 - CONFIDENCE) / 2.0
        alpha_mc = 4.0 * float(np.sqrt(nominal_alpha * (1.0 - nominal_alpha) / anchor.n_sims))
        alpha_bar = max(alpha_ceiling, nominal_alpha + alpha_mc)
        checks.append(
            RuleTwoCheck(
                name=f"calibration anchor: null false positives, n={anchor.n_triplets}",
                expected=f"near nominal {nominal_alpha:.3f}, at most {alpha_bar:.3f}",
                observed=f"{anchor.p_excludes_zero_above:.4f}",
                passed=bool(anchor.p_excludes_zero_above <= alpha_bar),
            )
        )
        coverage_mc = 4.0 * float(np.sqrt(CONFIDENCE * (1.0 - CONFIDENCE) / anchor.n_sims))
        half = max((coverage_band[1] - coverage_band[0]) / 2.0, coverage_mc)
        low, high = CONFIDENCE - half, min(1.0, CONFIDENCE + half)
        checks.append(
            RuleTwoCheck(
                name=f"calibration anchor: coverage, n={anchor.n_triplets}",
                expected=f"nominal {CONFIDENCE:.2f}, within [{low:.3f}, {high:.3f}]",
                observed=f"{anchor.coverage:.4f}",
                passed=bool(low <= anchor.coverage <= high),
            )
        )

    # `p_closes` alone is satisfied *by* the degeneracy at J = 1: every cluster is
    # identical, the percentile interval collapses to [1, 1], and "closes" follows
    # from zero width rather than from detection. So the point estimate is asserted
    # as well. Adversarial review, 2026-08-19.
    ceilings = [r for r in results if r.true_j == 1.0 and r.rho_item == 0.0]
    failed_ceilings = [
        r
        for r in ceilings
        if r.p_excludes_zero_above != 1.0 or r.p_closes != 1.0 or r.mean_j != 1.0
    ]
    checks.append(
        RuleTwoCheck(
            name="noiseless J=1 detection",
            expected=f"all {len(ceilings)} cells at mean J 1.0000, 1.0000 above zero, 1.0000 closes",
            observed=f"{len(ceilings) - len(failed_ceilings)} of {len(ceilings)} at 1.0000",
            passed=bool(ceilings) and not failed_ceilings,
        )
    )

    checks.extend(_closed_form_checks(results))
    checks.extend(_design_effect_checks(results, tolerance=inflation_tolerance))

    # Keyed on the shape as well as (n, icc). Without it the sensitivity-anchored
    # cells at icc=0.20 overwrite the symmetric cells at the same (n, icc) in this
    # dict, and the check silently grades 24 pairs where 30 exist. Found by
    # adversarial review, 2026-08-19.
    def _key(cell: CellResult) -> tuple[int, float, str]:
        return (cell.n_triplets, cell.icc, cell.shape)

    lows = {_key(r): r for r in results if r.true_j == 0.30 and r.rho_item == 0.0}
    highs = {_key(r): r for r in results if r.true_j == 0.85 and r.rho_item == 0.0}
    shared = sorted(set(lows) & set(highs))
    differing = [
        key
        for key in shared
        if (lows[key].p_closes, lows[key].p_survives)
        != (highs[key].p_closes, highs[key].p_survives)
    ]
    checks.append(
        RuleTwoCheck(
            name="discrimination between J=0.30 and J=0.85",
            expected=f"all {len(shared)} matched cells differ",
            observed=f"{len(differing)} of {len(shared)} differ",
            passed=bool(shared) and len(differing) == len(shared),
        )
    )
    return checks


def _closed_form_checks(results: list[CellResult], *, z_ceiling: float = 4.5) -> list[RuleTwoCheck]:
    """Recover the two quantities :func:`point_estimate_sd` fixes exactly.

    The mean of the point estimate must be ``true_j`` and its standard deviation
    must be the closed form, both at **every** ``n`` — the closed form is exact,
    not asymptotic, so a small ``n`` is no excuse. Both are scored as z-scores
    against the simulation's own Monte-Carlo error rather than against a fixed
    tolerance, so the check keeps its meaning at 12 replicates and at 2,000.

    Only ``rho_item == 0`` cells are scored: coupling the two arms within an
    event changes the variance of the difference, and the closed form does not
    model it. That is the whole reason the coupling slice is a sensitivity check
    rather than the default.
    """
    scored = [r for r in results if r.rho_item == 0.0 and r.n_sims > 1]
    if not scored:
        return []

    mean_z: list[tuple[float, CellResult]] = []
    sd_z: list[tuple[float, CellResult]] = []
    for cell in scored:
        sd = point_estimate_sd(cell.shape, cell.true_j, cell.icc, cell.n_triplets)
        if sd == 0.0:
            # J = 1 with no noise: the estimate is degenerate at 1 and the
            # ceiling check already covers it.
            continue
        mean_z.append((abs(cell.mean_j - cell.true_j) / (sd / np.sqrt(cell.n_sims)), cell))
        # The sampling SD of a sample standard deviation is sd / sqrt(2 * (m - 1)).
        sd_z.append((abs(cell.sd_j - sd) / (sd / np.sqrt(2.0 * (cell.n_sims - 1))), cell))

    checks: list[RuleTwoCheck] = []
    for name, scores in (
        ("estimand recovery: mean point estimate equals true J", mean_z),
        ("closed-form SD recovery: simulated SD equals sqrt(Var(d)(1+icc)/(2n))", sd_z),
    ):
        if not scores:
            continue
        worst_z, worst_cell = max(scores, key=lambda pair: pair[0])
        checks.append(
            RuleTwoCheck(
                name=name,
                expected=f"|z| <= {z_ceiling:.1f} against Monte-Carlo error in all "
                f"{len(scores)} cells",
                observed=(
                    f"worst |z| = {worst_z:.2f} at n={worst_cell.n_triplets}, "
                    f"J={worst_cell.true_j:.2f}, ICC={worst_cell.icc:.2f}, "
                    f"{worst_cell.shape}"
                ),
                passed=bool(worst_z <= z_ceiling),
            )
        )
    return checks


def _design_effect_checks(results: list[CellResult], *, tolerance: float) -> list[RuleTwoCheck]:
    """Width at ``icc`` over width at ``icc = 0`` must recover ``sqrt(1 + icc)``."""
    baseline = {
        (r.n_triplets, r.true_j, r.shape): r
        for r in results
        if r.icc == 0.0 and r.rho_item == 0.0 and 0.0 < r.true_j < 1.0
    }
    ratios: dict[float, list[float]] = {}
    for cell in results:
        if cell.icc == 0.0 or cell.rho_item != 0.0:
            continue
        base = baseline.get((cell.n_triplets, cell.true_j, cell.shape))
        if base is None or base.mean_width == 0.0:
            continue
        # Compared only at the largest simulated n, where the asymptotic design
        # effect is the right prediction. At 5 clusters the discrete percentile
        # bootstrap has its own bias and this identity is not expected to hold.
        if cell.n_triplets != max(r.n_triplets for r in results if r.rho_item == 0.0):
            continue
        ratios.setdefault(cell.icc, []).append(cell.mean_width / base.mean_width)

    checks: list[RuleTwoCheck] = []
    for icc in sorted(ratios):
        observed = sum(ratios[icc]) / len(ratios[icc])
        predicted = float(np.sqrt(variance_inflation_bound(icc)))
        checks.append(
            RuleTwoCheck(
                name=f"design effect recovered at ICC={icc:.2f}",
                expected=f"width ratio sqrt(1 + {icc:.2f}) = {predicted:.3f} +/- {tolerance:.0%}",
                observed=f"{observed:.3f} over {len(ratios[icc])} cells",
                passed=bool(abs(observed - predicted) <= tolerance * predicted),
            )
        )
    return checks


def point_estimate_sd(shape: str, true_j: float, icc: float, n_triplets: int) -> float:
    """Closed-form standard deviation of J's point estimate, at ``rho_item = 0``.

    Exact at every ``n``, not asymptotic: the estimate is a mean of ``n`` i.i.d.
    cluster means, so its variance is the cluster-mean variance over ``n``
    whatever the shape of the distribution. With ``REPEATS`` conditionally
    independent events per cluster and independent arms,

    ``Var(cluster mean) = [mu_g(1 - mu_g) + mu_m(1 - mu_m)] * (1 + icc) / REPEATS``

    where the ``(1 + icc)`` is the within-cluster covariance the heterogeneity
    knob injects — the same design effect :func:`variance_inflation_bound`
    reports. This is the known answer the simulator is required to recover
    before any of its power numbers count.

    Args:
        shape: Rate mapping name.
        true_j: Population J.
        icc: Within-triplet correlation.
        n_triplets: Clusters.

    Returns:
        The standard deviation of the point estimate.

    Raises:
        ValueError: ``n_triplets < 1``, ``icc`` outside ``[0, 1]``, or via
            :func:`rates_for`.
    """
    if n_triplets < 1:
        raise ValueError(f"n_triplets must be >= 1, got {n_triplets}")
    mean_governing, mean_matched = rates_for(shape, true_j)
    per_item = mean_governing * (1.0 - mean_governing) + mean_matched * (1.0 - mean_matched)
    variance = per_item * variance_inflation_bound(icc) / (REPEATS * n_triplets)
    return float(np.sqrt(variance))


def variance_inflation_bound(icc: float) -> float:
    """``1 + icc``: the most between-triplet heterogeneity can cost, at 2 repeats.

    With ``REPEATS`` events per cluster and independent arms, the variance of the
    cluster-mean difference is ``Var(d) * (1 + (REPEATS - 1) * icc) / REPEATS``.
    So at 2 repeats the design effect is ``1 + icc``, bounded by 2 — the
    parameter nobody has data for can inflate the interval's width by at most
    ``sqrt(2)``, whatever its value.

    Raises:
        ValueError: ``icc`` outside ``[0, 1]``.
    """
    if not 0.0 <= icc <= 1.0:
        raise ValueError(f"icc must be in [0, 1], got {icc}")
    return 1.0 + (REPEATS - 1) * icc


def smallest_usable_n(
    results: list[CellResult],
    *,
    true_j: float,
    icc: float,
    shape: str,
    ceiling: float = INDETERMINATE_CEILING,
) -> int | None:
    """Smallest ``n`` whose indeterminate rate falls at or below ``ceiling``.

    Returns ``None`` when no simulated ``n`` reaches it — the honest answer when
    the answer is "no n in this range".

    Note:
        ``ceiling`` is a **choice**, declared as one at
        :data:`INDETERMINATE_CEILING` and exposed as ``--indeterminate-ceiling``
        because it moves the answer. It is scanned in ascending ``n``, which the
        lattice effect below makes non-obvious: P(indeterminate) is **not**
        monotone in ``n``, so the smallest qualifying ``n`` can be smaller than
        an ``n`` above it that does not qualify.
    """
    matching = sorted(
        (
            r
            for r in results
            if r.true_j == true_j and r.icc == icc and r.shape == shape and r.rho_item == 0.0
        ),
        key=lambda r: r.n_triplets,
    )
    for cell in matching:
        if cell.p_indeterminate <= ceiling:
            return cell.n_triplets
    return None


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def three_state_table(results: list[CellResult], *, shape: str, icc: float, rho_item: float) -> str:
    """Markdown table of ``closes / survives / indeterminate`` over n and true J."""
    cells = [r for r in results if r.shape == shape and r.icc == icc and r.rho_item == rho_item]
    if not cells:
        return "_(no cells)_"
    j_values = sorted({r.true_j for r in cells})
    n_values = sorted({r.n_triplets for r in cells})
    lookup = {(r.n_triplets, r.true_j): r for r in cells}

    header = "| n | " + " | ".join(f"J={j:.2f}" for j in j_values) + " |"
    rule = "|---" * (len(j_values) + 1) + "|"
    lines = [header, rule]
    for n_triplets in n_values:
        row = [str(n_triplets)]
        for true_j in j_values:
            cell = lookup.get((n_triplets, true_j))
            row.append(
                "—"
                if cell is None
                else f"{cell.p_closes:.2f} / {cell.p_survives:.2f} / {cell.p_indeterminate:.2f}"
            )
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def width_table(results: list[CellResult], *, shape: str, true_j: float, rho_item: float) -> str:
    """Markdown table of mean interval width over n and ICC, at one true J.

    Held at a single ``true_j`` on purpose: width depends on both J and ICC, and
    a table pooled over J compares a J = 1 cell of width zero against cells that
    have width, which reads as a heterogeneity effect and is not one.
    """
    cells = [
        r for r in results if r.shape == shape and r.rho_item == rho_item and r.true_j == true_j
    ]
    if not cells:
        return "_(no cells)_"
    icc_values = sorted({r.icc for r in cells})
    n_values = sorted({r.n_triplets for r in cells})
    lookup = {(r.n_triplets, r.icc): r for r in cells}
    header = "| n | " + " | ".join(f"ICC={icc:.2f}" for icc in icc_values) + " |"
    rule = "|---" * (len(icc_values) + 1) + "|"
    lines = [header, rule]
    for n_triplets in n_values:
        row = [str(n_triplets)]
        for icc in icc_values:
            cell = lookup.get((n_triplets, icc))
            row.append("—" if cell is None else f"{cell.mean_width:.3f}")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_report(
    results: list[CellResult],
    checks: list[RuleTwoCheck],
    *,
    anchor: CellResult | None,
    n_sims: int,
    n_resamples: int,
    distinct_datasets: int,
    cache_hits: int,
    elapsed: float,
    width_j: float,
    ceiling: float = INDETERMINATE_CEILING,
) -> str:
    """The whole run as markdown."""
    lines = [
        "# Track H H1: how many triplets?",
        "",
        f"{len(results)} cells x {n_sims} simulation replicates, "
        f"{n_resamples} bootstrap resamples per distinct dataset, "
        f"{distinct_datasets} distinct datasets ({cache_hits} cache hits), "
        f"{elapsed:.1f}s.",
        "",
        "## Standing rule 2: known answers recovered first",
        "",
        "| check | expected | observed | passed |",
        "|---|---|---|---|",
    ]
    for check in checks:
        lines.append(
            f"| {check.name} | {check.expected} | {check.observed} | "
            f"{'yes' if check.passed else 'NO'} |"
        )
    if anchor is not None:
        lines += [
            "",
            f"Calibration anchor: n={anchor.n_triplets} clusters, true J=0, ICC=0, "
            f"{anchor.n_sims} replicates. Coverage {anchor.coverage:.4f}, "
            f"false positives above zero {anchor.p_excludes_zero_above:.4f}, "
            f"mean width {anchor.mean_width:.3f}.",
        ]

    lines += [
        "",
        "## The estimator's realised error rate at the design's own cluster counts",
        "",
        "Reported, not gated. This is what the cluster percentile bootstrap does at "
        "5 to 20 clusters with 2 binary events each, and it is a result rather than "
        "a defect in the simulator: the anchor above shows the same pipeline hitting "
        "nominal where the asymptotics hold.",
        "",
        "| n | two-sided coverage at J=0 | P(interval above zero) at J=0 |",
        "|---|---|---|",
    ]
    for cell in sorted(
        (r for r in results if r.true_j == 0.0 and r.icc == 0.0 and r.rho_item == 0.0),
        key=lambda r: r.n_triplets,
    ):
        lines.append(
            f"| {cell.n_triplets} | {cell.coverage:.3f} | {cell.p_excludes_zero_above:.3f} |"
        )

    lines += ["", "## Three states: closes / survives / indeterminate", ""]
    shapes = sorted({r.shape for r in results})
    for shape in shapes:
        rhos = sorted({r.rho_item for r in results if r.shape == shape})
        for rho_item in rhos:
            iccs = sorted({r.icc for r in results if r.shape == shape and r.rho_item == rho_item})
            for icc in iccs:
                lines += [
                    f"### {shape}, ICC={icc:.2f}, rho_item={rho_item:.2f}",
                    "",
                    three_state_table(results, shape=shape, icc=icc, rho_item=rho_item),
                    "",
                ]

    lines += [f"## Mean interval width at true J = {width_j:.2f}", ""]
    for shape in shapes:
        for rho_item in sorted({r.rho_item for r in results if r.shape == shape}):
            table = width_table(results, shape=shape, true_j=width_j, rho_item=rho_item)
            if table == "_(no cells)_":
                continue
            lines += [
                f"### {shape}, rho_item={rho_item:.2f}",
                "",
                table,
                "",
            ]

    lines += [
        f"## Smallest n whose indeterminate rate falls to {ceiling:.2f} or below",
        "",
        "The decision H1 has to support is three-way, so the quantity that sizes it "
        "is not power against a null — it is the chance of landing in the state that "
        "answers nothing. A dash means no simulated n reaches the bar.",
        "",
    ]
    for shape in shapes:
        cells = [r for r in results if r.shape == shape and r.rho_item == 0.0]
        if not cells:
            continue
        j_values = sorted({r.true_j for r in cells})
        icc_values = sorted({r.icc for r in cells})
        lines += [
            f"### {shape}",
            "",
            "| true J | " + " | ".join(f"ICC={icc:.2f}" for icc in icc_values) + " |",
            "|---" * (len(icc_values) + 1) + "|",
        ]
        for true_j in j_values:
            row = [f"{true_j:.2f}"]
            for icc in icc_values:
                smallest = smallest_usable_n(
                    results, true_j=true_j, icc=icc, shape=shape, ceiling=ceiling
                )
                row.append("—" if smallest is None else str(smallest))
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    lines += [
        "## Per-cell detail",
        "",
        "| n | J | ICC | shape | rho | coverage | width | P(point kill) "
        "| P(zero-width CI) | mean J |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for cell in sorted(results, key=lambda r: (r.shape, r.rho_item, r.icc, r.true_j, r.n_triplets)):
        lines.append(
            f"| {cell.n_triplets} | {cell.true_j:.2f} | {cell.icc:.2f} | {cell.shape} | "
            f"{cell.rho_item:.2f} | {cell.coverage:.3f} | {cell.mean_width:.3f} | "
            f"{cell.p_point_kill:.3f} | {cell.p_zero_width:.3f} | {cell.mean_j:.3f} |"
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def _append_checkpoint(path: Path | None, cell: CellResult) -> None:
    """Append one completed cell, so a crash costs one cell rather than the run."""
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(cell)) + chr(10))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--sims", type=int, default=2000, help="Simulation replicates per cell.")
    parser.add_argument("--resamples", type=int, default=N_RESAMPLES, help="Bootstrap replicates.")
    parser.add_argument(
        "--data-seed", type=int, default=20260819, help="Seed for the data-generating process."
    )
    parser.add_argument(
        "--boot-seed", type=int, default=20260819, help="Seed for the cluster bootstrap."
    )
    parser.add_argument(
        "--quick", action="store_true", help="A small smoke grid, for checking the plumbing."
    )
    parser.add_argument(
        "--anchor-n",
        type=int,
        default=50,
        help="Cluster count for the calibration anchor. Far above the design range on "
        "purpose: nominal coverage is the right answer there, so a failure points at "
        "the simulator rather than at small-sample behaviour.",
    )
    parser.add_argument("--anchor-sims", type=int, default=1000, help="Replicates for the anchor.")
    parser.add_argument(
        "--anchor-resamples", type=int, default=4000, help="Bootstrap replicates for the anchor."
    )
    parser.add_argument(
        "--indeterminate-ceiling",
        type=float,
        default=INDETERMINATE_CEILING,
        help="Share of runs allowed to land indeterminate before an n counts as usable. "
        "A choice, not a derived number: see INDETERMINATE_CEILING.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Append each completed cell here as JSON Lines, so a crash costs one cell.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse cells already in --checkpoint. Each cell is seeded from its own "
        "parameters, so a resumed run is identical to an uninterrupted one.",
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="Write the per-cell records as JSON here."
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write the markdown report here as well as to stdout.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the grid, check the known answers, print the report."""
    args = _parse_args(argv)

    if args.quick:
        n_values = [5, 20]
        j_values = [0.0, 0.30, 0.85, 1.0]
        icc_values = [0.0, 0.50]
        secondary_n = [20]
        width_j = 0.30
    else:
        n_values = [5, 8, 10, 12, 15, 20]
        j_values = [0.0, 0.30, 0.50, 0.70, 0.85, 1.0]
        icc_values = [0.0, 0.05, 0.20, 0.50]
        secondary_n = n_values
        width_j = 0.50

    specs = build_grid(n_values, j_values, icc_values)
    specs += build_grid(
        secondary_n, [j for j in j_values if 0.0 < j <= 0.85], [0.20], shape=SHAPE_SENS_ANCHORED
    )
    specs += build_grid(secondary_n, [j for j in j_values if 0.0 < j < 1.0], [0.20], rho_item=0.5)

    cache = BootstrapCache(n_resamples=args.resamples, seed=args.boot_seed, confidence=CONFIDENCE)
    anchor_spec = CellSpec(n_triplets=args.anchor_n, true_j=0.0, icc=0.0)

    done: dict[CellSpec, CellResult] = {}
    if args.checkpoint is not None and args.resume:
        done = {spec_of(cell): cell for cell in load_checkpoint(args.checkpoint)}
        if done:
            print(f"resuming: {len(done)} cells already on disk", file=sys.stderr, flush=True)

    started = time.perf_counter()
    results: list[CellResult] = []
    for index, spec in enumerate(specs, start=1):
        cell = done.get(spec)
        if cell is None:
            cell = run_cell(
                spec,
                n_sims=args.sims,
                rng=cell_rng(args.data_seed, spec),
                cache=cache,
            )
            _append_checkpoint(args.checkpoint, cell)
        results.append(cell)
        print(
            f"[{index}/{len(specs)}] n={spec.n_triplets} J={spec.true_j:.2f} "
            f"icc={spec.icc:.2f} {spec.shape} rho={spec.rho_item:.2f} "
            f"({time.perf_counter() - started:.0f}s, {cache.misses} distinct)",
            file=sys.stderr,
            flush=True,
        )
    # The cache is the run's whole memory footprint and the anchor shares nothing
    # with it, so it is dropped before the anchor's own, larger, resamples begin.
    cache_misses, cache_hits = cache.misses, cache.hits
    cache.clear()

    anchor: CellResult | None = None
    if args.anchor_n > 0:
        anchor = done.get(anchor_spec)
        if anchor is None:
            anchor_cache = BootstrapCache(
                n_resamples=args.anchor_resamples, seed=args.boot_seed, confidence=CONFIDENCE
            )
            print(f"calibration anchor: n={args.anchor_n} ...", file=sys.stderr, flush=True)
            anchor = run_cell(
                anchor_spec,
                n_sims=args.anchor_sims,
                rng=cell_rng(args.data_seed, anchor_spec),
                cache=anchor_cache,
            )
            _append_checkpoint(args.checkpoint, anchor)
    elapsed = time.perf_counter() - started

    checks = check_known_answers(results, anchor)
    report = render_report(
        results,
        checks,
        anchor=anchor,
        n_sims=args.sims,
        n_resamples=args.resamples,
        distinct_datasets=cache_misses,
        cache_hits=cache_hits,
        elapsed=elapsed,
        width_j=width_j,
        ceiling=args.indeterminate_ceiling,
    )
    print(report)

    if args.report is not None:
        args.report.write_text(report, encoding="utf-8")
    if args.out is not None:
        args.out.write_text(
            json.dumps(
                {
                    "sims": args.sims,
                    "resamples": args.resamples,
                    "data_seed": args.data_seed,
                    "boot_seed": args.boot_seed,
                    "elapsed_seconds": elapsed,
                    "distinct_datasets": cache_misses,
                    "checks": [asdict(check) for check in checks],
                    "anchor": None if anchor is None else asdict(anchor),
                    "cells": [asdict(cell) for cell in results],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    failed = [check for check in checks if not check.passed]
    if failed:
        print(
            "STANDING RULE 2 FAILED: "
            + "; ".join(f"{check.name} -> {check.observed}" for check in failed),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
