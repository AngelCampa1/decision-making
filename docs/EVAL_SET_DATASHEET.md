# Eval-set datasheet

Following the *Datasheets for Datasets* convention. Written while the corpus is
still small, so the answers describe what exists rather than what was intended.

## Motivation

**Why was this created?** To measure whether a markdown decision skill changes
an agent's accuracy when a decision depends on a pile of accumulated context.
Public benchmarks are contaminated and, more importantly, do not isolate the
variable: we need items where the answer provably turns on a known subset of the
presented facts.

**Who created it?** Angel Campa (`AngelCampa1`). No external funding.

## Composition

**What do instances represent?** One decision scenario: a set of short factual
statements, a question, a fixed option menu, and a computed answer.

**How many?** At the time of writing, 10 templates producing 280 items at seed 1
— 4 variable samplings × 7 strata each. The strata are 0, 1 and 4 distractors
crossed with early, middle and late positions, with the zero-distractor stratum
appearing once rather than once per position.

**Is the ground truth reliable?** It is *computed*, never authored: each template
declares a solution expression evaluated against the sampled variables. Auditing
10 rules is tractable in a way that auditing 280 answers is not. The expression
is restricted to a whitelisted AST — no attribute access, subscripts, lambdas or
imports — so regenerating the corpus does not execute arbitrary code.

**What is missing?** Anything resembling a long horizon. Every item is a single
turn with six to nine short facts. If the surviving distractor effect lives in
long-horizon agentic accumulation, as arXiv:2606.29718 reports, this corpus
cannot see it. That is the most important limitation on this page.

**Are there labels?** Yes, and they are **exactly balanced by construction**.
Variants cycle through the option menu and resample until they hit their
assigned answer, so chance accuracy is exactly `1 / len(options)`. An early
draft sampled freely and produced two single-class templates out of ten.

**Are instances related?** Heavily, and it matters. Items sharing a template are
correlated, so **template id is the clustering key** in every score record and
the resampling unit in every confidence interval. The design deliberately favours
many templates with few variants each. Within a template, the strata of one
variant share their variable bindings, so clean and loaded items differ only in
irrelevant material and the larger distractor sets are supersets of the smaller.

**Is any content sensitive or personal?** No. Vendors, people and places are
invented; no real organisation is named.

## Collection

**How was the data collected?** It was generated. `generate(template, seed)` is a
pure function of its arguments, seeded from `sha256(template_id:seed:variant)`,
and the full output is pinned byte-exact by golden files that require an explicit
`pytest --bless` to change.

**Who wrote the templates?** Claude Opus 5, under direction, in a single session.
That is a real limitation: ten templates from one author in one sitting will
share idiom and structure in ways a broader corpus would not. **The mitigation
was a 10% human realism audit and it is retired as of 2026-08-18**, along with
every other step in these plans that waited on a person. It is not retired for
being unperformed: a single-item realism verdict cannot recover the judge's own
base rate, and the only reader available had authored the templates, so it was a
self-assessment either way. What replaces it is a **forced choice** — one
generated problem beside one human-written problem of the same shape, judged
blind, which was written by a person — because that cancels the base rate and
carries a ground truth the audit never had: which item is human is a fact on the
record. It needs a public human-written word-problem source that clears the
outside-data rule in [`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md), and
**no such source has been read, fetched or cleared** — so the mitigation is
currently unavailable rather than merely undone, and this limitation stands
open.

**What quality filters applied?**

1. **Distractor audit.** A distractor is admitted only if it shares no variables
   with the solution expression *and* two independent auditors agree it is
   genuinely inert rather than plausibly foldable. All 50 shipped distractors
   pass the structural half; **the semantic half has not run yet** and needs the
   local auditor models. Until it does, the audit is half-complete and should be
   described that way.
2. **Knife-edge rejection.** A sampling is rejected if its answer flips under a
   ±1 nudge to any integer the solution reads. Added after the first calibration
   run failed a clean-room item on a `outage_h == sla_h` tie against a fact
   reading "only after N continuous hours" — a sentence with two readings, which
   made the item defective rather than hard.
3. **Clean-room and difficulty gates**, both computed on the control arm only so
   they cannot bias the treatment-minus-control difference. See
   [`PROTOCOL.md`](PROTOCOL.md) §6.

## Preprocessing

Facts are rendered in the order the generator arranged them and are **not**
reordered downstream. Position is a stratum; reordering at render time would
destroy it.

The option menu is rendered identically in every arm. AgentAtlas
(arXiv:2605.20530**v1**) reported every model's trajectory accuracy dropping by
14–40 pp when the explicit label menu was removed, and two conditions travel with
that figure. First, **it is v1-only**: v2 (26 May 2026) deleted the sentence and
replaced the quantity with "mapped label agreement can change substantially" — no
number, and a different measure name — so the version has to be named wherever the
figure is used. Second, both versions disclaim the run as a demonstration on a
synthetic 1,342-item set rather than a benchmark release, v2 adding that it
"should not be read as a 'definitive model comparison'".

So the figure is used here only to justify holding the menu constant by
construction rather than by convention. It is **not** a magnitude to compare this
corpus's own effects against, and the earlier claim here that it was "larger than
any effect this corpus is designed to detect" has been withdrawn: that is exactly
the cross-study magnitude comparison v2 disclaims.

### Sampling is constrained, in two ways that make the corpus non-naturalistic

Both are deliberate, and both are the reason a number from this corpus is not a
number about how often models fail in the wild.

**Knife edges are rejected.** Every integer the solution reads is nudged by ±1;
if any nudge changes the answer, the sampling is discarded. Items sitting on a
threshold test how precisely a sentence is read, which is a different skill from
the one under test. This makes items *easier*.

**Collisions are required to discriminate.** At least one distractor per template
states a quantity of the same kind and units as something the answer depends on,
excluded only by a qualifier in its own sentence — a degraded-performance window
against continuous unavailability, a first-response target against a downtime
threshold. Sampling then rejects any binding where substituting the distractor's
number for the real one leaves the answer unchanged.

That second constraint is **stacking the deck, and it is the point**. A
naturalistic corpus would let the irrelevant number agree with the relevant one
roughly half the time; those items score identically whether the model ranked
the context or grabbed the nearest number, so they add dilution and no signal.
The reported effect from this corpus is therefore an *upper bound* on the
distractor effect a model would show against unconstrained material, and should
be read as a stress test rather than a prevalence estimate.

The alternative was measured, not assumed. The first control run used
distractors that were merely off-topic — a rebranding, a coffee machine — and
scored at ceiling with only 13 of 93 loaded responses acknowledging a distractor
at all. Type-incompatible distractors do not compete, and a corpus of them
measures nothing.

## Uses

**What is it for?** Measuring the effect of a decision skill on distractor
robustness, under [`PROTOCOL.md`](PROTOCOL.md).

**What should it not be used for?** Claims about long-horizon agentic behaviour;
claims about tasks whose quality is genuinely subjective; and any cross-paper
comparison, since prompt formatting differs and that alone moves results.

**Is contamination a risk?** Yes, and it is managed rather than prevented. The
public split is committed and expected to become contaminated; it only gates
spending and never enters a verdict. The holdout regenerates from a
seed kept in an uncommitted local file outside the repository — **a file, not a
passphrase somebody remembers**, since a secret only a person can produce is a
step that waits on a person — and is published after the verdict, with a fresh
seed for the next run.

## Distribution and maintenance

Apache-2.0, in the repository. Templates are the source of truth; items are
regenerated rather than distributed as a frozen file, and the golden corpus
exists to detect drift rather than to serve as the distribution format.

Maintained by the author. A template change re-blesses the goldens and the diff
goes through review, because a benchmark that can change silently makes every
number computed before the change incomparable with every number after it.

## Known problems

- **The first build of this corpus was far too easy, and the rebuild is
  unmeasured.** The original distractors were off-topic rather than
  type-compatible with the decision rule; the control arm scored at ceiling and
  the diagnosis is in
  [`notebook/2026-08-10-why-the-distractors-do-nothing.md`](../notebook/2026-08-10-why-the-distractors-do-nothing.md).
  Every distractor was rebuilt to collide. **Whether that lands inside
  [0.35, 0.75] has not yet been measured**, and the recorded prediction is that
  it will not — that a single-turn item of six to nine short facts is the wrong
  venue regardless of distractor quality.
- **The semantic half of the distractor audit has not run**, and it now matters
  much more than it did. Colliding distractors are built to sit near the line
  between irrelevant and ambiguous, which is exactly the class the 2026 GSM-NoOp
  re-audit found had produced most of the original effect. Structural invariance
  does not settle that; two independent auditors are required and none have run.
  This gate blocks pre-registration.
- **No realism measurement at all.** The 10% human audit that was the target is
  retired (see *Who wrote the templates?*), and the forced choice replacing it
  cannot run until a human-written comparison source clears the outside-data
  rule. Target and status are both now 0, and the honest reading is that this
  limitation got *more* open, not less.
- **Single author, single session, ten templates.** Idiom and structure are
  correlated across the corpus in ways that are hard to see from inside it.
