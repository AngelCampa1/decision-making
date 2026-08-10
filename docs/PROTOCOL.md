# Protocol

**Version 1.** The standing methodology for every skill evaluated in this
repository. Changes get a new version number and a dated entry in
[`../notebook/`](../notebook/); they never silently amend a protocol a completed
run was conducted under.

## 1. The experiment

One skill, four arms, the same items in every arm, paired by item.

| Arm | System prompt | Purpose |
| --- | --- | --- |
| `off` | Task framing + response-format contract only | Control |
| `on` | Control + the skill body | Treatment |
| `placebo` | Control + token- and structure-matched filler | Isolates the length effect |
| `cot` | Control + "Think step by step" | Isolates the generic-reasoning effect |

Three rules make this a fair comparison rather than a demonstration:

**The response-format contract appears in every arm.** If only the treatment is
told to emit structured output, the experiment measures instruction-following,
not decision quality.

**The placebo is matched on tokens and structure** — same approximate length,
same headings, bullets, and a worked example — but contentless. A skill that
beats `off` and not `placebo` is a length effect, and no `SHIP` verdict is issued
without a passing placebo arm.

**Any option menus are held constant across arms.** AgentAtlas (arXiv:2605.20530)
found that removing explicit label menus from prompts moved trajectory accuracy
by 14–40pp across all eight models tested. That is larger than any effect we
expect to measure, so it cannot be allowed to vary.

A fifth `in-situ` arm, injecting the skill via `--append-system-prompt` on top of
the default system prompt rather than replacing it, tests ecological validity.
Disagreement between the isolated and in-situ arms is a reportable result.

## 2. Arenas

Three arenas with different permissions. The separation is enforced in code, not
by discipline.

| Arena | Models | Split | Skill may change | Emits a verdict |
| --- | --- | --- | --- | --- |
| `dev` | Local (Ollama, mock) | public | yes | **no** |
| `screen` | Cheap hosted (Haiku) | public | yes | **no** |
| `confirm` | Target (Sonnet, Opus) | private holdout | **no** | yes |

Why the separation matters: Prompting Inversion (arXiv:2510.22251) showed a
sculpted prompt helping GPT-4o (97% vs 93%) while *hurting* GPT-5 (94.00% vs
96.36% plain CoT). Scaffolding tuned against a weak model can become a handicap
on a strong one. Iterating freely in `dev` and `screen` is therefore fine and
expected; carrying that iteration into the verdict is not.

## 3. Pre-registration

Committed before any confirmation run, as `preregistration/<skill>-v<n>.yaml`:
hypothesis, primary metric, item count, minimum detectable effect, alpha, guards,
stopping rule, plus `skill_sha256` and `analysis_script_sha256`.

A confirmation run refuses to start unless:

1. the pre-registration file is committed and not dirty;
2. its commit is an ancestor of `HEAD` and predates everything in
   `results/<skill>/`;
3. `skill_sha256` matches the skill body on disk;
4. `analysis_script_sha256` matches the analysis code;
5. the recorded baseline accuracy falls inside the difficulty band;
6. the projected cost is within budget.

Editing one word of a skill after pre-registration aborts the run with a diff.
Proceeding requires writing `-v2.yaml`, which is a new, dated, visible commit.
The effect is to make prompt tuning an auditable event rather than an invisible
one. Locking the analysis script matters just as much: a pre-registered metric
means nothing if the code computing it can be rewritten after seeing the data.

**Stopping rule: fixed N, no interim analysis.** The screen/confirm split gives
cost control without alpha spending, because the two stages use disjoint items
and the screening result never enters the final p-value — it only decides whether
to spend.

## 4. Metrics

One primary metric per skill. Guards that can only veto. Secondaries that are
descriptive and explicitly labelled exploratory.

**Primary tests.** McNemar's exact test for paired binary outcomes; a paired
permutation test for continuous ones. Confidence intervals come from a cluster
bootstrap resampling *templates*, not items. The CLT is deliberately avoided:
arXiv:2503.01747 restricts its validity below a few hundred effectively
independent datapoints, and after a design effect of ~2.0 our counts sit in
exactly that range.

**Guards, all one-sided non-inferiority tests:**

| Guard | Threshold |
| --- | --- |
| No harm on the clean stratum | Δ ≥ −2pp |
| Beats placebo | CI on (on − placebo) excludes 0 |
| Beats plain CoT | CI lower bound on (on − cot) > −2pp |
| Format integrity | Parse-failure rate increase ≤ 1pp |
| Cost | Median output tokens ≤ 2.5× control |

Means are reported alongside **p90 and p99**. The AGENTS.md impact study
(arXiv:2601.20404) found the benefit of an instruction artifact concentrates in a
small number of expensive runs rather than spreading uniformly, so a mean-only
report can hide the effect entirely.

**Calibration** uses the Murphy decomposition with a hard floor on resolution
(Δ ≥ −0.005). A skill that improves Brier purely by shrinking every forecast
toward the base rate is hedging, and the resolution term is what catches it.
Calibration error is reported with a kernel-smoothed estimator rather than
binned ECE, which is bin-count dependent and biased at small n.

**Trigger quality is measured separately from task accuracy**, against a positive
set and a negative set of ~50 turns that superficially resemble triggers.
Precision and recall are reported. A suite that improves accuracy while firing on
most ordinary turns is a net loss in practice, and an accuracy-only evaluation
would not notice.

## 5. Multiplicity

Benjamini-Hochberg at **q = 0.10** across the primary tests of the
pre-registered skill set. Both raw p and adjusted q appear in the scorecard.

Guards are **not** corrected. They are conservative-direction non-inferiority
tests, so adjusting them would make it *easier* for a harmful skill to pass —
the correction would work against safety rather than for it.

## 6. Datasets

Parameterised YAML templates with **computed** ground truth, in the style of
GSM-Symbolic. Auditing ~50 template rules is tractable; auditing 300 authored
answers is not.

Three gates before a family is eligible for pre-registration, all run on the
**control arm only** so they cannot bias the treatment-minus-control difference:

1. **Distractor audit.** A distractor qualifies only if the computed solution is
   provably invariant to its removal *and* two independent passes agree it is
   genuinely irrelevant rather than plausibly foldable into the reasoning. The
   2026 GSM-Symbolic re-audit kept 12.4% of candidates; expect similar attrition.
2. **Clean-room check.** ≥95% control accuracy on distractor-free variants. Items
   missed *without* distractors are ambiguous, not hard.
3. **Difficulty calibration.** Control accuracy on distractor-present items in
   [0.35, 0.75]. Above that there is no headroom and the required N explodes.

Templates rather than items are the clustering unit, so the design favours **many
templates with few variants each**.

Public/screen items are committed and expected to become contaminated over time;
they only gate spending. The holdout is regenerated from a passphrase-derived
seed held outside the repository and published after the verdict, with fresh
seeds for the next run. Contamination is handled by regeneration, not secrecy.

## 7. Verifiers and judges

Verifiers are tested before they are trusted: fixtures of known-correct,
known-wrong, paraphrased, and boundary responses, run through the verifier first.
Every zero score is classified as agent failure, verifier defect, environment
leak, or infrastructure error rather than assumed to be the first.

Judges produce **secondary** metrics only; no primary metric is ever a judge
score. They emit a binary verdict plus a written critique rather than a Likert
rating, and are calibrated against a deliberately failure-heavy human-labelled
set with **TPR and TNR reported separately**. Blended accuracy hides the
agreeableness bias documented across this literature, where a judge can appear
>90% accurate while catching almost no real failures. Criteria drift
(arXiv:2404.12272) means recalibration is required whenever the pipeline or the
model changes.

Panels are small and heterogeneous. "Nine Judges, Two Effective Votes"
(arXiv:2605.29800) found nine judges from seven families yield an effective
sample size of ~2.18, so headcount is not the lever — diversity of failure mode
is. Aggregation uses a robust estimator rather than a mean, per RoPoLL
(arXiv:2606.30931), which shows mean aggregation carries unbounded bias under any
positive contamination.

## 8. Verdicts

See [`../SCORECARD.md`](../SCORECARD.md) for the vocabulary. Two commitments:

**Negative results are published.** A `NULL` or `HARMFUL` verdict gets a written
entry: hypothesis, N, observed effect, CI, why we expected otherwise, and what
would need to change. The badge reports honest denominators.

**A verdict is a claim about one model version at one point in time.** Skills
validated in one month can decay in the next. A periodic drift watch on shipped
skills is part of the protocol, not an optional extra.

## 9. Harness disclosure

Every run records its harness configuration against the ETCSOVG checklist —
Execution, Tool, Context, Scheduling, Observability, Verification, Governance.
This is not bureaucracy: in a controlled 3×3 factorial, harness variance exceeded
model variance by roughly 7.8× and produced six ranking reversals in nine
comparisons (arXiv:2605.23950). An agent result without its harness disclosed is
not reproducible, and most published ones are not.
