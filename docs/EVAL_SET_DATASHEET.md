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
share idiom and structure in ways a broader corpus would not. The 10% human
realism audit is the mitigation and it has not been performed yet.

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

The option menu is rendered identically in every arm. AgentAtlas measured 14–40pp
of trajectory accuracy moving with the presence of an explicit menu, which is
larger than any effect this corpus is designed to detect, so it is held constant
by construction rather than by convention.

## Uses

**What is it for?** Measuring the effect of a decision skill on distractor
robustness, under [`PROTOCOL.md`](PROTOCOL.md).

**What should it not be used for?** Claims about long-horizon agentic behaviour;
claims about tasks whose quality is genuinely subjective; and any cross-paper
comparison, since prompt formatting differs and that alone moves results.

**Is contamination a risk?** Yes, and it is managed rather than prevented. The
public split is committed and expected to become contaminated; it only gates
spending and never enters a verdict. The holdout regenerates from a
passphrase-derived seed held outside the repository and is published after the
verdict, with fresh seeds for the next run.

## Distribution and maintenance

Apache-2.0, in the repository. Templates are the source of truth; items are
regenerated rather than distributed as a frozen file, and the golden corpus
exists to detect drift rather than to serve as the distribution format.

Maintained by the author. A template change re-blesses the goldens and the diff
goes through review, because a benchmark that can change silently makes every
number computed before the change incomparable with every number after it.

## Known problems

- **The corpus may be too easy.** Interim control accuracy on distractor-present
  items was 0.870 against a target band of [0.35, 0.75], with no meaningful gap
  between clean and loaded strata. If the full run confirms this, the corpus as
  built cannot test the flagship's premise.
- **The semantic half of the distractor audit has not run.** Structural
  invariance alone does not establish that a fact is irrelevant to a reader.
- **No human realism audit yet.** 10% is the target; 0% is the status.
- **Single author, single session, ten templates.** Idiom and structure are
  correlated across the corpus in ways that are hard to see from inside it.
