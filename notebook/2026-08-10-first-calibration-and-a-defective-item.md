# 2026-08-10 — The first real run found a bug in my benchmark, not in the model

## What happened

First control-arm run against Haiku. At 54 records, every single failure came
from one variant of one template — and it failed at **zero distractors**, which
is the clean-room stratum.

That is the gate doing precisely its job. `docs/PROTOCOL.md` says an item missed
*without* distractors is ambiguous, not hard. Here is the item:

```
variables: outage_h=11, sla_h=11
- The Northwind contract credits SLA penalties only after 11 continuous hours of downtime.
- Yesterday's incident kept the service unavailable for 11 continuous hours.
- Filing a claim costs nothing and has no effect on renewal terms.

expected: wait          model: file_sla_claim
```

The rule is `outage_h > sla_h`, strictly greater, so ground truth is `wait`. The
model read "only after 11 continuous hours" as satisfied by exactly 11 hours and
filed the claim. Its reasoning was explicit about it: *"exactly 11 continuous
hours, which is the minimum required to trigger SLA penalties"*.

**The model is right, or at least defensibly so.** "After 11 hours" does not
have one reading. I wrote a sentence with two meanings and then scored one of
them as wrong.

## Why this is worth more than a one-line fix

Had this shipped, it would have contributed a per-template accuracy floor that
no arm could ever clear, in *every* stratum simultaneously. The paired design
would have cancelled most of it in the treatment-minus-control difference — so
the headline effect would have looked fine — while quietly making the clean-room
gate unpassable and the difficulty number meaningless. It is the shape of bug
that survives exactly the checks you would expect to catch it.

It is also the shape of bug the whole GSM-Symbolic re-audit is about, pointed at
myself. The re-audit's finding was that the original collapse came mostly from
*ambiguous* items rather than genuinely irrelevant distractors. I had spent a
notebook entry treating that as a fact about someone else's benchmark, and then
built the same defect into mine on the first attempt.

## The fix

Two, one narrow and one general.

**Narrow.** `rel-001`'s fact now reads "only when downtime **exceeds** {sla_h}
continuous hours", which is unambiguously strict.

**General.** Generation now rejects any sampling whose answer flips under a ±1
nudge to an integer the solution expression reads. An exact tie is the worst
case, but the neighbours are barely better: at `outage_h = 12, sla_h = 11` the
item is still mostly testing how precisely a threshold sentence is read, which
is a different skill from ranking irrelevant context out and adds noise to every
stratum at once.

Fixing only the wording would have been the cheaper move, and it would have left
nine other templates one unlucky sampling away from the same defect. Four of ten
goldens changed when the margin was applied, which is a reasonable estimate of
how often this was about to happen.

## The cost, stated plainly

**This makes items easier, and the corpus is already too easy.** Interim control
accuracy was 0.870 on distractor-present items against a target band of
[0.35, 0.75], with essentially no gap between clean (0.875) and loaded (0.870)
at either 1 or 4 distractors.

So I have just made a ceiling problem slightly worse. Doing it anyway, because
the alternative is keeping ambiguous items *because they lower the accuracy
number* — which is manufacturing difficulty out of my own imprecision and
calling it distractor sensitivity. The honest fix for a ceiling is stronger
distractors, and that is a separate problem being treated as one.

## The interim signal, and what I expect

At n=54 the distractor effect was approximately zero: 0.875 clean, 0.875 at one
distractor, 0.864 at four. Small sample, one template, no intervals — not a
result, and I am not going to treat it as one.

But it points the same direction as the 2026 re-audit, and it is worth recording
before the full run finishes so the reading cannot be retrofitted.

**Prediction, recorded now.** The full control run comes in above the difficulty
band, with a clean-versus-loaded gap under 5pp and confidence intervals
comfortably including zero. If that holds, the corpus as built cannot test the
flagship's premise, and the response is *not* to relax the band — it is that
these distractors are too weak, and single-turn scenarios of six to nine short
facts are the wrong venue. arXiv:2606.29718 relocated the surviving effect to
long-horizon agentic accumulation; this corpus is the short-horizon case the
re-audit largely dissolved.

If that is where this lands, the flagship gets re-aimed rather than the gate
loosened, and this entry is the record that the decision was made before the
number arrived rather than after.
