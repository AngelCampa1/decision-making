# 2026-08-10 — The baseline number, scored against the prediction

The full control run finished. 280 items, Haiku, $1.24, zero parse failures.

## The prediction, and what happened

From [two entries ago](2026-08-10-first-calibration-and-a-defective-item.md),
recorded at n=54 before any of this was known:

> The full control run comes in above the difficulty band, with a
> clean-versus-loaded gap under 5pp and confidence intervals comfortably
> including zero.

| | predicted | actual |
| --- | --- | --- |
| difficulty gate | above [0.35, 0.75] | **0.946** |
| clean − loaded | under 5pp | **0.4pp** (0.950 vs 0.946) |

Correct, and by a wide margin. Distractor count did nothing: 0.950 at zero
distractors, 0.942 at one, 0.950 at four. Position did nothing either — early
0.938, middle 0.950, late 0.950. There is no signal in this corpus to find.

The response is the one recorded in advance: not to relax the band. The
diagnosis and the rebuild are in
[the entry before this](2026-08-10-why-the-distractors-do-nothing.md), written
while the run was still going so it could not be retrofitted to the result.

## The more useful finding is in the 15 wrong answers

They are not spread out. Fourteen of fifteen come from two variants of one
template, and the remaining one is its own separate defect.

### rel-009 v1 and v3: I never wrote down the rule

Seven failures each, in *every* stratum including zero distractors. A uniform
per-variant failure is a clean-room signature, not a distractor one.

```
The inbound aircraft is running 76 minutes late.
The traveller has 96 minutes of slack before the onward connection.
The later flight has seats available and no rebooking fee.

expected: wait_at_gate     model: rebook_now
```

The model's reasoning: 96 − 76 leaves 20 minutes, which has to cover deplaning,
walking to the gate and any luggage transfer; rebooking is free and seats are
available; therefore rebook.

**That is a better answer than mine.** My ground truth is `delay > slack`, which
assumes any positive margin means the connection is made. Nothing in the item
says that. Every other template in the corpus states its decision rule as a fact
— "policy forbids starting a deploy that cannot complete its smoke test inside
the window", "policy is to reorder whenever stock would run out" — and rel-009
stated two quantities and left the actual question to the reader's judgement
about how real airports work.

So it now carries the missing fact: the transfer airport protects any connection
with slack remaining, and rebooking forfeits that protection. That also removes
the free-rebooking asymmetry the model correctly exploited.

### rel-008 v2: a scenario the rule does not govern

One failure. 155 seats in active use against a renewal quote covering 116.

The utilisation rule says renew — usage is 134% of paid seats, far above the 95%
floor. The model said renegotiate, and explained why: the quote does not cover
the team. The policy addresses *under*-use and is silent about a shortfall, so
the model was reasoning past a gap in the scenario rather than failing to read
it.

No amount of rewording the policy fixes this, because the problem is not the
wording — it is that a coherent-on-paper sampling produced a situation the rule
was never written for. Templates can now declare `constraints`, and rel-008
declares `seats_used <= seats_paid`. The scenario is excluded at the point where
it is built.

## Three of these now, and they share a shape

The knife-edge tie, the missing policy fact, the ungoverned scenario. Every one
was a case where the model's answer was defensible and my ground truth was not,
and every one was found by a real run rather than by a test.

They also have different fixes, which is the part worth noticing: a sampling
margin, a missing fact, and a cross-variable constraint. There is no single
guard that catches this class. What catches it is running the control arm and
reading the failures — which is exactly the job the clean-room gate has, and
exactly why it is computed on the control arm only.

## The gate that nearly did not fire

Clean-room accuracy was **0.950** against a floor of **0.95**. Passed.

Meanwhile rel-009 was sitting at 0.50 clean. Nine templates at 1.00 and one at
0.50 pooled to exactly the floor, and one more unlucky item anywhere in the
corpus would have taken it under — which is to say the gate reported PASS by
luck rather than by measurement.

A clean-room failure is a property of an *item*: it means that item is
ambiguous. Pooling that across templates lets a broken template hide behind
working ones, which is precisely what happened. The gate is now per-template, and
the same run would have failed it loudly and named rel-009.

That is a better outcome than the fix to rel-009 itself. The template defect
cost one template; the pooling defect would have kept costing on every future
corpus.

## Next

Re-run the control arm on the rebuilt corpus. Prediction from the previous entry
stands unchanged and unedited: high 0.8s rather than 1.0 — enough to show the
collision mechanism is real, not enough to make a single-turn nine-fact item a
usable venue.

The baseline run is archived under
`results/evidence-ledger/2026-08-10-baseline-corpus/` with the commit of the
corpus that produced it. It cannot be regenerated from main, and it is the
control-arm number the paper's distractor section reports against.
