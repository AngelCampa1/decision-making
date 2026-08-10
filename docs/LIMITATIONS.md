# Limitations

Written before any results exist, so it cannot be tuned to flatter them. Updated
as new limitations are discovered, never trimmed as they become inconvenient.

## The harness

**No temperature control.** The Claude Code CLI exposes no sampling parameters.
The response is to run ≥2 independent repeats per cell and report run-to-run
variance rather than to claim determinism. This is less of a loss than it sounds:
temperature 0 is not deterministic on hosted inference anyway, and a stated
variance is more honest than an assumed constant.

**Rate limits, not dollars, are the budget.** Subscription auth means the binding
constraint is a rolling quota rather than a spend cap. Runs are therefore
checkpointed and resumable across days, and a confirmation run may span multiple
sessions. Wall-clock timing is not comparable across runs and is not reported as
a metric.

**`--system-prompt` measures a clean injection, not daily use.** Replacing the
system prompt removes the confounds — tools, other skills, settings, MCP — but
the result describes a model that has *only* the skill, which is not the model
anyone runs. The `in-situ` arm using `--append-system-prompt` tests the realistic
case. Where the two disagree, the disagreement is the finding, and the in-situ
number is the one that describes daily use.

**Model identity is pinned only as far as the CLI reports it.** `--output-format
json` returns a resolved model id, which is recorded in every run config. It does
not protect against a silent server-side change within the same id. A verdict is
a claim about a model at a point in time, and the drift watch exists because of
this.

**Claude Code is both the harness under study and the instrument.** The
harness-variance literature says the scaffold dominates, and we are one specific
scaffold. Results should not be assumed to transfer to a different agent harness
without re-measurement — which is precisely the claim arXiv:2605.23950 makes
about everyone else's results too.

## The statistics

**N is small by ML standards.** Subscription throughput caps the item count, and
the cluster design effect (~2.0 at 6 variants per template with ICC 0.2) cuts the
effective N roughly in half again. Exact and resampling methods are used
throughout rather than the CLT for exactly this reason (arXiv:2503.01747), but no
method recovers power that was never purchased. Underpowered comparisons are
reported as `UNTESTED` or with an explicit minimum detectable effect rather than
as nulls.

**Multiplicity is controlled across pre-registered primaries only.** Benjamini-
Hochberg at q = 0.10 covers the primary test of each pre-registered skill.
Secondary and exploratory analyses are labelled as such and are not corrected;
they generate hypotheses and are not evidence.

**Guards are uncorrected by design.** They are one-sided non-inferiority tests in
the conservative direction, and correcting them would make it easier for a
harmful skill to pass. This is a deliberate asymmetry, stated so it is not
mistaken for an oversight.

**The cluster bootstrap assumes templates are exchangeable.** If template
difficulty is systematically related to template authorship or to the order in
which templates were written, the interval is optimistic. Templates are generated
in mixed batches to reduce this, but it is not eliminated.

## The datasets

**We generate our own items, so we also own their biases.** Public benchmarks are
contaminated, which is why we generate. The cost is that item realism rests on a
10% human audit, and a template family that is subtly easier in the treatment's
favour would not be caught by any automatic gate. The distractor audit runs on
the control arm only, which prevents the most direct version of this leak but not
all of it.

**The distractor premise may be weaker than the design assumes.** The 2026
GSM-Symbolic re-audit reduced the expected effect substantially, and its source is
a re-analysis rather than a peer-reviewed paper. If our own two-auditor filter
keeps a similarly small fraction, the flagship's effect may be too small to
detect at the N the budget supports. That outcome is a legitimate result and is
pre-registered as a possibility, not a failure to be worked around.

**Holdout secrecy is temporary and partial.** The holdout regenerates from a
passphrase-derived seed held outside the repository, and is published after the
verdict. Anyone who can run the generator with a guessed seed could reconstruct
items. Contamination is managed by regeneration between runs, not by secrecy.

## The judges

**Judge panels have a low effective sample size.** Nine judges from seven
families yield n_eff ≈ 2.18 (arXiv:2605.29800). Our three-judge panel should be
assumed to carry roughly two independent votes, and it reports its measured n_eff
rather than its headcount. No primary metric is ever a judge score.

**Judges drift.** Criteria drift (arXiv:2404.12272) means a judge calibrated once
does not stay calibrated. Recalibration is required whenever the pipeline or the
model changes, and a stale calibration blocks score emission — but between
recalibrations, judge-derived secondaries carry unquantified drift.

**Local judge models are weaker.** Ollama models supply genuine provider
diversity at zero cost, which is the active ingredient per RoPoLL, but they are
small. Diversity of failure mode is bought at the price of individual judge
quality, and that trade is a design choice rather than a free win.

## Scope

**Five skills is what the budget supports, not what the space contains.** The
framework survey in [`REJECTED.md`](REJECTED.md) records what was left out and
why. Several of those decisions are defensible rather than certain, and the
document exists so a future run can overturn them cheaply.

**Findings are about decision-shaped tasks with computable ground truth.** That
is a real restriction, and it is the same restriction SkillOpt has without
flagging it. Tasks whose quality is genuinely subjective are outside what this
harness can adjudicate, and any claim about them would rest on judge scores —
which is why judge scores are secondary.

**A verdict is not a usability judgement.** `NULL` means we have not shown a
skill works, not that it does not. The scorecard governs the public claim; it
does not govern what anyone installs.
