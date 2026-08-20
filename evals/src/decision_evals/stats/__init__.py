"""Statistics for paired skill-vs-no-skill experiments.

Every published number flows through this subpackage, so it carries a 100% line
and branch coverage floor and is exercised by property-based tests rather than
example-based ones alone.

Three choices here are deliberate and worth stating up front:

*Exact and resampling methods, not the CLT.* Miller's "Adding Error Bars to
Evals" (arXiv:2411.00640) popularised CLT-based standard errors for evals, but
arXiv:2503.01747 shows the normal approximation is unreliable below a few
hundred effectively-independent datapoints. Our item counts sit in exactly that
range once the design effect is applied, so the primary tests are McNemar's
*exact* test and a cluster bootstrap.

*Clusters, not items, are the unit of resampling.* Items generated from one
template are correlated. Treating them as independent understates variance by
the design effect ``1 + (m - 1) * ICC``, which at m=6 and ICC=0.2 discards
roughly half the effective sample.

*The Murphy decomposition is exact, not approximate.* Grouping by unique
forecast value rather than by histogram bin makes ``Brier = Reliability −
Resolution + Uncertainty`` hold to floating-point precision, which turns it into
a property test that catches essentially every decomposition bug.
"""

from decision_evals.stats.agreement import (
    CohenKappaResult,
    DegenerateAgreementError,
    EffectiveRatersResult,
    FleissKappaResult,
    KrippendorffAlphaResult,
    PercentAgreementResult,
    UnanimityResult,
    cohen_kappa,
    effective_raters,
    fleiss_kappa,
    krippendorff_alpha,
    percent_agreement,
    unanimity_rate,
)
from decision_evals.stats.calibration import (
    CalibrationBin,
    MurphyDecomposition,
    brier_score,
    expected_calibration_error,
    log_score,
    murphy_decomposition,
    reliability_curve,
    smooth_calibration_error,
)
from decision_evals.stats.cluster import (
    ClusterBootstrapResult,
    TwoSampleClusterBootstrapResult,
    cluster_bootstrap_diff,
    cluster_bootstrap_two_sample,
    design_effect,
    effective_sample_size,
    intraclass_correlation,
)
from decision_evals.stats.multiplicity import BenjaminiHochbergResult, benjamini_hochberg
from decision_evals.stats.paired import (
    McNemarResult,
    PermutationResult,
    mcnemar_exact,
    paired_permutation_test,
)
from decision_evals.stats.power import PowerResult, minimum_detectable_effect, required_pairs
from decision_evals.stats.reliability import (
    PerItemReliability,
    ReliabilityResult,
    aptitude_unreliability,
    per_item_reliability,
    repeat_reliability,
    repeats_for_reliability,
    repeats_for_scatter_precision,
)

__all__ = [
    "BenjaminiHochbergResult",
    "CalibrationBin",
    "ClusterBootstrapResult",
    "CohenKappaResult",
    "DegenerateAgreementError",
    "EffectiveRatersResult",
    "FleissKappaResult",
    "KrippendorffAlphaResult",
    "McNemarResult",
    "MurphyDecomposition",
    "PerItemReliability",
    "PercentAgreementResult",
    "PermutationResult",
    "PowerResult",
    "ReliabilityResult",
    "TwoSampleClusterBootstrapResult",
    "UnanimityResult",
    "aptitude_unreliability",
    "benjamini_hochberg",
    "brier_score",
    "cluster_bootstrap_diff",
    "cluster_bootstrap_two_sample",
    "cohen_kappa",
    "design_effect",
    "effective_raters",
    "effective_sample_size",
    "expected_calibration_error",
    "fleiss_kappa",
    "intraclass_correlation",
    "krippendorff_alpha",
    "log_score",
    "mcnemar_exact",
    "minimum_detectable_effect",
    "murphy_decomposition",
    "paired_permutation_test",
    "per_item_reliability",
    "percent_agreement",
    "reliability_curve",
    "repeat_reliability",
    "repeats_for_reliability",
    "repeats_for_scatter_precision",
    "required_pairs",
    "smooth_calibration_error",
    "unanimity_rate",
]
