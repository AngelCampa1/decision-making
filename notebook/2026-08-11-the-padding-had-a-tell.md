# 2026-08-11 — The padding had a tell, and so did the cores

No model calls. The separability gate runs on regexes.

## What the gate is for

Padding written to *not matter* has a register: fewer hard numerals, fewer
deadlines, fewer citations, more hedging, flatter sentences. The core is dense in
exactly those things **because that is what makes it the core**. On-topic-ness
fixes *topical* separability and does nothing about *register* separability.

If padding is separable on surface features, a model doing salience-weighted
attention finds the core in constant time however long the file gets. The dose
curve then comes out flat and gets written up as "no context rot at this scale",
when the retrieval difficulty was never manipulated at all.

That is the worst failure available to this experiment, and it is why the gate
runs before any long call is made.

## Three iterations

| Pass | Pooled AUC | Top feature | Direction | What it was |
|---|---|---|---|---|
| 1 | 0.776 | `type_token_ratio` | core higher | **the gate's own defect** |
| 2 | 0.750 | `dates` | padding higher | **the cores' defect** |
| 3 | 0.758 | `numerals` | core higher | **my defect** |
| 4 | **0.679** | `type_token_ratio` | core higher | passes |

Ceiling is 0.70, pre-registered.

### Pass 1 — raw TTR is a length measure in disguise

The first run's top feature was raw type-token ratio, and the obvious reading was
"my padding repeats itself". Half of it was artefact: TTR falls mechanically with
document length, so a 200-word note beats a 2,000-word schedule on vocabulary
variety whatever either of them says.

That is the exact confound every other feature is divided per-hundred-words to
avoid, and I did not apply it to the one feature that is not a count. Standardised
over 100-word windows the figure drops to 0.698.

**A gate can have the defect it exists to detect.** This one nearly reported my
padding as findable for a reason that was about file size.

### Pass 2 — the cores have no dates at all

Next up was `dates` at 0.750, with the direction reading *padding higher*. I had
loaded the high-salience padding with deadlines precisely because the docstring
says padding needs them.

Then the diagnostic: **all 82 core documents score exactly zero.**

The twelve probe casefiles are written entirely in relative time — *"within six
months of the date the understatement was discovered"*, *"four years after the
date of the notice of assessment"* — and never once name a date. So any padding
written the way professional correspondence is actually written is a perfect
tell. Every document with a date is padding.

This is not a padding defect. It is a **core** defect, and the padding was the
more realistic of the two.

For the pilot I matched the cores' register, because internal validity is what
Phase 0 is buying and the alternative is rewriting twelve casefiles to answer a
question that has not been asked yet. The real fix is recorded for Milestone F:
professional documents have dates, the 30 cores should carry them, and a corpus
where only the padding does is a corpus with a tell. Noted against the
ecological-validity limitations already recorded for the fictional jurisdiction.

### Pass 3 — I wrote the failure mode I had documented

`numerals` rose to 0.758, direction *core higher*. Core median 5.24 per hundred
words; my six low-salience documents had **zero**.

The first draft equated "does not bear on the decision" with "says nothing
specific". Every routine document came out vague — no reference codes, no counts,
no amounts, no durations. That is the register tell the module docstring warns
about, written straight into the corpus it warns about it in, by the person who
wrote the warning.

Real routine correspondence is full of numbers. *"Our reference AB/4471/02"*,
*"340 items were delayed last quarter"*, *"2.4 hours against a budget of 3.0"*.
What makes a document non-governing is that **none of its numbers bear on the
question**, not that it has none.

Rewritten with figures throughout, numerals falls to 0.554 and the pooled figure
to 0.679.

## What this changes about the estimate

Padding is nearly as expensive to author as core, and now there is a number
behind that claim rather than an assertion: twelve documents took three revisions
driven by a gate, and two of the three revisions were mine to make.

The plan's Milestone F library sizing survives — 250 per domain is roughly right
for a 100k draw under the 30% domination cap, which needs 333. The **pilot**
sizing did not: 25 per domain is a tenfold under-estimate, and the cap is now a
parameter so a run computing no standard errors can relax it deliberately rather
than by having the constant lowered.

## Caveats on the number itself

- **82 "core" documents is not 82 governing documents.** It is every document in
  every probe casefile, including the non-governing ones already in them. The
  comparison is closer to "casefile prose vs library prose" than to "core vs
  padding", and it flatters the gate slightly: casefile padding drags the core
  distribution toward the library's.
- **Twelve padding documents is a small sample** for a Mann-Whitney statistic.
  The AUC has a wide interval and 0.679 against a 0.70 ceiling is not a
  comfortable margin.
- **Six features are not all the features.** A model has more than regexes. The
  gate rules out the easy tells; the core-detection probe in Task 12 is what asks
  a model directly, and it is the one that counts.

Employment library not yet authored.
