# 2026-08-10 — The flagship skill nearly had a fatal design flaw

## The worry

The flagship skill, `evidence-ledger`, asks the model to rank supplied context,
name what is irrelevant, and discard it — all **inline**, in the same context
window that then produces the answer.

The obvious objection: GSM-NoOp's finding is precisely that the generator *does
not* filter noise. We would be asking the same model, in the same window, to do
one step earlier the thing it demonstrably fails to do later. The distractor is
still sitting in the context when the answer is generated. Writing
"INERT: Paraguay rainfall — different continent" might not remove its influence;
it plausibly *increases* it by mentioning the distractor a second time.

I flagged this during planning as the single riskiest assumption in the design.

## What the literature says

Two 2026 findings, pointing the same direction:

**Bare negation doesn't work; verify-then-discard does.** The I³C line and
"Unable to Forget" (arXiv:2506.08184) find that instructing a model to ignore
something has marginal effect, and the effect degrades as the irrelevant item
becomes more semantically related to the task — which is exactly the regime we
care about, since our distractors are topically related by construction. What
does work is a two-step structure: explicitly verify *why* an item is irrelevant,
and only then discard it.

**Decoupled curation beats inline curation, measurably.** "Escaping the Context
Bottleneck" (arXiv:2604.11462) separates a context curator from a frozen task
executor: WebArena 36.4% → 41.2% with 8.8% *fewer* tokens, and an 8× token
reduction on DeepSearch. A 7B curator matched GPT-4o-level context management.
The framing that matters: context curation is a distinct, offloadable capability,
not something the answering model should be doing to itself mid-flight.

## Decision

**The forked variant becomes the primary design; inline becomes a comparison
arm.** A subagent reads the context pile and returns only the ledger, so the main
context never sees the raw distractors at all. That sidesteps the objection
entirely rather than hoping instruction-following overcomes it.

The skill body is also restructured so verification and discard are two visibly
separate steps, not one "ignore this" clause.

## Why keep inline as an arm at all

Because the forked design has a real limitation: it only works when the skill
owns retrieval, and usually it doesn't — context arrives in the conversation
before any skill fires. Inline is the degraded mode that has to work when
forking isn't available (no subagents, portable Skills-API deployment, small
context budget). Knowing how much is lost by degrading is a product question, not
just a research one.

So the experiment is three-way: **no-ledger / inline-ledger / forked-ledger**.

## Prediction, recorded before running

Forked > inline > none, with inline possibly indistinguishable from none. If
inline shows no effect, that is the interesting result, not the disappointing
one: it would mean a large fraction of published "tell the model to ignore
irrelevant context" advice does not survive measurement.

## The other thing that got worse

A 2026 re-audit of GSM-Symbolic found the original distractor effect largely
dissolves once distractors are filtered for *genuine* irrelevance — only 117 of
945 (12.4%) survived a two-auditor filter, and the remaining drop was
statistically indistinguishable from zero on GPT-4o, Claude Opus 4.6, and Haiku
4.5. (Source is a LessWrong re-analysis, not peer-reviewed; flagging the
confidence level rather than treating it as settled.)

Two consequences. First, our own dataset needs that same two-auditor filter, and
we should expect to discard most candidate distractors — this is now the most
important gate in the dataset build, not a formality. Second, the expected effect
size drops, which raises the required item count. The difficulty-calibration gate
(60 cheap items, run before scaling to 50 templates) exists to find this out in a
day rather than a month.

If frontier models genuinely no longer exhibit this failure at a measurable rate,
that is a publishable finding and it kills the skill honestly. But the failure
mode itself hasn't vanished — it relocated. Context rot is still documented at
30–50% degradation in long-horizon agentic search (arXiv:2606.29718), which is
where the skill should be aimed.

---

**Correction, 2026-08-12.** The 30–50% degradation figure attributed above to
arXiv:2606.29718 is not in that paper. Not in the abstract, not found in the
PDF, not in any secondary summary. What the paper shows is **premature
termination** — models giving up or answering uncertainly well before the
context window is full, at a rate rising with context length, over four models
and three search benchmarks. Its own headline number is a 2.6–4.9% *gain* from
behaviour-aware filtering.

The reasoning in this entry does not depend on the magnitude, only on the
direction, so what is argued above stands. The number should not be repeated.
