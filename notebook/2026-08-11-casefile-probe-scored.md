# 2026-08-11 — The casefile probe, scored

Three runs on the same twelve casefiles, in this order: with the candidate action
menu, without it, and with all scaffolding removed. Only the first was predicted
in advance. The second and third are follow-ups designed after reading the traces
from the first, which the dev arena permits and which is recorded here so nobody
has to reconstruct the order later.

## Run 1, against the prediction

Prediction is in
[`2026-08-11-casefile-venue-prediction.md`](2026-08-11-casefile-venue-prediction.md),
committed at `f0bd9be` before any casefile reached a model.

| # | Quantity | Predicted | Actual | |
|---|---|---|---|---|
| 1 | Admissibility | 0.10–0.30 | **0.500** | wrong |
| 2 | Trap rate, order ≥ 2 | 0.50–0.83 | **0.000** | wrong |
| 3 | Exposure at first order | ≥ 0.60 | **0.08** | wrong |
| 4 | Pivot named | ≈ 0.25 | **0.58** | wrong |
| 5 | Raincoat taken | 0.10–0.20 | **0.00** | close |
| 6 | Five blocks present | ≥ 0.90 | **1.00** | right |
| 7 | Both gates pass | yes | Gate 1 only | wrong |

Five of seven wrong, every one of them in the same direction. I underestimated
Haiku on this task, consistently and by a lot.

## All six admissibility failures were mine. Again.

Fifteen of fifteen last time; six of six this time. The automatic label is still
triage, not a result.

Five failed on the pivot conjunct alone. I declared "nothing determinative is
missing", the model named something, and the scorer demanded the literal word
`NONE`. What it named on probe-09 was:

> Evidence of a compliant written cure notice specifying at least a 21-day cure
> period, served before the protected concern was raised

That is exactly the fact s.46(3) turns on. It found a better pivot than I wrote.
On probe-11 it asked whether the Facility A Agent would in fact grant the waiver —
structurally identical to probe-12's pivot, which I *had* declared present. My
inconsistency, scored as its error.

The sixth, probe-06, missed a required action redundant with one it took: "wait
for the metallurgical report" is entailed by "serve the reservation of rights",
and its prose said so.

**The pivot conjunct as designed is not measuring anything.** A competent adviser
can nearly always name a useful unknown, and naming one is good behaviour. Scoring
it as failure inverts the thing being measured. Either it comes out of
admissibility, or it becomes "named a determinative unknown" with no requirement
that it match mine.

## What run 1 actually measured

Strip the pivot and the picture is a ceiling, not headroom:

```
prohibited actions taken     0 / 12
trap actions taken           0 / 12
raincoat taken               0 / 12
required actions             11 / 12
exposure band correct        11 / 12
condition recall 0.97, precision 0.93
five blocks present          12 / 12
```

Gate 1 "passed" at 0.500 entirely on the strength of a broken conjunct.

## Run 2 removed the menu, because run 1 could not distinguish two things

The candidate list spelled the reasoning out. "Defer the Year 3 amendment until
after the Year 1 assessment window closes, then file inside the s.216(2)
correction period" is not an option label — it is the insight, printed. AgentAtlas
measured 14–40pp from menu presence with plain labels; this menu carried far more.
Run 1 could not tell forward reasoning from recognising the right answer written
down, and the difference is whether there is a result here at all.

Same twelve casefiles, same conditions, same risk question, no menu, free-text
recommendations, read by hand.

**Nine of nine trap cases still correct.** Selected verbatim:

- **probe-08** (order 2): *"Notify the lender's Agent within ten business days …
  of the prior-period error, restatement, and resulting covenant breach at 4.12:1
  leverage."* It computed the ratio itself from doc2 and doc3.
- **probe-10** (order 3): *"File protective s.418(3) corresponding adjustment
  claim within 7 days of the disclosure to reserve the right to $1,680,000 relief
  before the claim window closes. Do not defer either filing; s.402(4) prohibits
  deferral and s.418(3) admits no extension."* probe-10 exists to check whether
  probe-07 taught a pattern rather than a method. It did not.
- **probe-11** (order 3): waiver obtained and documented *before* the authorising
  board meeting, then publication. The sequencing trap, sequenced correctly.
- **probe-12** (order 3): hold uncashed, notify the insurer inside cl. 8.1, obtain
  cl. 9.2 consent, require the s.19(5) agreement, *"Reject the payment if
  Marchetti refuses."* All three links.
- **probe-07** (order 2): *"Do not file the amended return until the Year 1 notice
  date is confirmed"*, then both branches presented to the client rather than one
  chosen. **That is better than my answer key**, which required a single course;
  presenting the branches is the correct professional posture and I had not
  allowed for it.

## The finding, stated plainly

**Haiku 4.5 performs order-1 through order-3 consequence reasoning reliably on
five-to-nine-document professional casefiles, without an action menu.** Zero
traps taken across nine trap cases in two independent framings.

That is the falsifier recorded in the prediction entry, and it says what to do
with it:

> **Trap rate at order ≥ 2 of zero.** Haiku plays the path forward reliably and
> `consequence-cascade` has nothing to fix here. That is a publishable negative
> about a specific, well-motivated hypothesis rather than a null about a corpus
> that could not test anything.

It is a negative result about a difficulty level, not about the hypothesis in
general. What it rules out is `consequence-cascade` earning a verdict on
casefiles of this size against this model.

## What run 2 still handed over, and run 3 removes

A **numbered list of the conditions in play**. Condition recall of 0.97 measures
classification of an extracted list, not discovery. I did the extraction — the
hardest and least visible part of the job — and then measured whether the model
could tick the right boxes.

Real use supplies no condition list, no risk question, and no menu. Run 3 is
documents and a question. If the failures live anywhere, they live there, and it
is also the only one of the three framings that resembles what the skills are
for.

## Run 3: documents and a question. Same answer.

**Nine of nine trap cases avoided again**, with no condition list, no menu, and no
risk question. The model found the governing conditions itself and reached the
same recommendations.

- **probe-09**: *"Whether a compliant s.44(1) cure notice was served before the
  protected concern was raised."* Unprompted, from seven documents, it named the
  exact fact s.46(3) turns on — and it served the cure notice **and** deferred
  past the presumption window, which is the both-prongs answer rather than the
  A7 half-answer I planted.
- **probe-12**: notify the insurer, obtain the s.19(5) agreement, *"Retain the
  payment pending receipt of both."* Three links, no scaffolding.
- **probe-11**: *"Request Facility A waiver from the Agent immediately, targeting
  execution before accounts publication."* The sequencing trap, sequenced right.
- **probe-02**: it added *"Verify the impairment does not breach any facility
  covenants before sign-off."* That case's notes flag the covenant certificate as
  a deliberate near-miss where inventing a breach would be over-reading. It did
  not invent one — it said verify. Correct on both counts.

Only probe-07 was weaker than run 2. It identified the whole look-back chain and
quantified it at $1.26M, then advised the client and left the timing to them
rather than volunteering the deferral. Defensible, and less useful than run 2's
answer, which laid out both branches.

## The finding, triangulated

**Three independent framings — full scaffolding, no menu, no scaffolding — and
Haiku 4.5 avoided every trap in all three.** Twenty-seven trap opportunities, zero
taken.

At this size the venue cannot measure a forward-simulation skill, and the reason
is not that the traps are weak. They are real, and the model traces them
explicitly and quantitatively, computing ratios and naming subsections that were
never handed to it.

## The variable never tested

Every corpus this project has built is **under 2,000 tokens**. The single-turn
items were ~350. These casefiles are ~1,650.

Context rot is documented at 30–50% degradation in long-horizon agentic settings
(arXiv:2606.29718). Nothing here is long-horizon. I have now built three corpora
that vary trap sophistication, distractor type-compatibility, and scaffolding, and
held the one variable the literature actually implicates roughly constant.

The next dial is **volume**, not cleverness: the same traps buried in tens of
thousands of tokens of genuinely irrelevant material, where the governing fact has
to be found rather than read. That is also the regime the skills are for — nobody
needs a decision procedure for nine documents they can hold in their head.

## Cost

$0.67 for run 1, comparable for runs 2 and 3. The whole phase is under $2 and
under a day, which was the entire argument for doing it before building a schema.
