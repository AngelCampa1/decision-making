# 2026-08-18 — prediction: the rewrite round, and the stopping rule that keeps it honest

Registered **before** any ask is rewritten and before any re-adjudication call
is made. It follows
[the freeze finding](2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md)
and its appended adversarial review, which established that the only live branch
of the v3 plan's own rule is *rewrite the turn*, since *move the label* is
structurally blocked on a matched-triple corpus and retirement is the remedy for
a three-way split that three binary judges cannot produce.

## The danger this entry exists to bound

**Rewrite, re-adjudicate, rewrite again is fitting the corpus to its own
adjudicator.** Nothing in the machinery would stop it, and the result would look
like a clean corpus with high inter-rater agreement — the most flattering
possible artefact and a worthless one. This repository has caught five estimators
that produced plausible numbers while measuring nothing; a corpus tuned until its
judges agree would be the sixth and the hardest to see, because every gate would
read green and the agreement statistic would *improve*.

So the round is bounded before it starts.

## The protocol

1. **One round. Exactly one.** Each of the 12 disputed asks is rewritten once.
2. **The rewriter does not see the judges' per-item rationales.** It is given the
   triple's shared body, the author's intent for that member (`kind`:
   `lookup`, `compute`, `summarise`, …), and the general principle in §3. It is
   *not* told what any judge said about that item. A rewrite aimed at a
   particular judge's stated objection is tuned to that judge; a rewrite aimed at
   the authoring rule is not.
3. **Re-adjudication is the unchanged N3 protocol** — three fresh instances, no
   access to the label, same prompt, same parser.
4. **Whatever is still disputed after one round is retired**, and the retirement
   is reported with the cumulative movement figure the review demanded, not with
   a denominator reset onto the survivors.
5. **The shortcut battery is re-run against `HEAD` afterwards.** No gate may
   cross. If one does, the rewrite is reverted rather than baselined — a new
   baseline entry earned by an edit that was supposed to fix labels is the
   fifth generation of the leak.

## The diagnosis the rewrites are aimed at

Read off `s02n2`, which is the cleanest instance. It was authored as a `lookup`:

> "Is there a tax difference for me between paying down my interest-free family
> loan and putting that money into my pension?"

The answer is determinate and factual, and two of three judges said it should
fire anyway. Their reasons agree with each other: it "presents two competing
financial options," it is "comparing two financial options."

**So the defect is comparison framing, not subject matter.** An ask that sets two
options side by side reads as a decision request even when its answer is a fact,
because the reason a person wants that fact is visibly to choose between them.
The negatives were built to wear the positive's subject matter — that was the
design — but several of them also inherited the positive's *shape*.

The rewrite rule that follows: **an inert ask asks about one thing.** It may
share every noun with the positive. It may not put two options in a frame that
invites ranking them.

## Predictions

- **At least 8 of the 12 rewritten asks reach a majority consistent with the key
  after one round.** Estimator: majority of 3 binary judges per item, from
  `results/triggers/adjudication.jsonl`, over a denominator of the 12 rewritten
  items. Fewer than 8 means the negatives' problem is not framing and the
  diagnosis in §3 is wrong.
- **The two positive → negative items behave differently from the ten.** `m18p`
  and `s12p` are positives the judges unanimously read as non-decisions, so the
  rewrite there strengthens an ask rather than defusing one. I expect these two
  to be *harder*, and I would not be surprised if both end up retired.
- **Corpus-wide movement, recomputed over all 261 items after the round, falls
  below 0.046.** It has to, arithmetically, if any rewrite works; the number
  worth watching is whether it falls to near zero, which would be the signature
  of tuning rather than fixing.
- **No gate crosses.** Stump lift stays under 0.10 and the three baselined
  findings do not gain a fourth.

## Where I expect to be wrong

**The comparison-framing diagnosis is drawn from one item read closely and
eleven read quickly.** It fits `s02n2` exactly. If the other eleven turn out to
have unrelated causes — an ask that is factual but high-stakes, an ask whose body
is so loaded that any question over it reads as a decision — then a single rule
applied twelve times will fix the ones it fits and damage the ones it does not,
and the 8-of-12 band will be met for the wrong reason.

**And the honest limit of the whole round:** the judges are a model, the
rewriter is a model, and the author was a model. Rewriting until a model agrees
with a model is exactly the circularity N4 exists to bound, and this round does
not bound it. It makes the corpus internally consistent. It does not make it
right.
