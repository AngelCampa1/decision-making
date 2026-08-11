# 2026-08-11 — The collision rebuild, scored against the prediction

The rebuilt corpus finished. 280 items, Haiku, control arm, zero parse failures.

## The prediction, and what happened

From [`2026-08-10-why-the-distractors-do-nothing.md`](2026-08-10-why-the-distractors-do-nothing.md),
written before the rebuild and unedited since:

> Fixing type-compatibility alone will move the number, and I do not expect it to
> move it to the band. My guess is somewhere in the high 0.8s rather than 1.0 —
> enough to prove the mechanism is real, not enough to make a single-turn
> nine-fact item a usable venue.

| | predicted | actual |
| --- | --- | --- |
| loaded accuracy | high 0.8s | **0.971** |
| difficulty gate | FAIL | **FAIL** |
| clean-room gate | — | **PASS, 1.000, every template** |

The direction was right and the magnitude was wrong by about four times. I called
the conclusion correctly for a reason that was not correct.

## What the collision rebuild actually bought

The comparison against the 0.946 baseline is not the right one, because 15 of
those 280 items were defective and all 15 were mine. Correcting for them:

| | valid loaded items | wrong | accuracy |
| --- | --- | --- | --- |
| pre-rebuild, defects excluded | 227 | 0 | **1.000** |
| post-rebuild | 240 | 7 | **0.971** |

So the mechanism is real and it is worth **2.9 percentage points**. I predicted
something like twelve. Making a distractor state the same kind of quantity in the
same units as a solution variable — the thing the GSM-NoOp re-audit says is the
only kind of distractor worth counting — moves Haiku by under three points on a
nine-fact item.

## The shape of the remaining failures says it is not a distractor effect at all

**By distractor count**, the effect is not monotone:

```
 0 distractors  1.000  (n=40)
 1 distractor   0.967  (n=120)
 4 distractors  0.975  (n=120)
```

Four collisions are *easier* than one. If this were distraction load, that
ordering could not happen.

**By position**, early 0.963 against middle and late at 0.975 — a 1.2pp spread,
and pointing the opposite way from any recency story.

**Between templates**, sd 0.029, with rel-001 and rel-006 at 0.92 loaded and four
templates at 1.00.

Seven wrong answers spread over 240 items, non-monotone in the dose, flat in
position, and concentrated in two templates. That is not a mechanism responding
to a dial. That is a handful of individually hard items, and it would take a
corpus several times the size to say anything about them with a confidence
interval that excluded zero.

## What this settles

**The single-turn venue is finished as a flagship, by measurement rather than by
assumption.** Two rebuilds, two ceilings. The premise was never wrong — context
rot is documented at 30–50% in long-horizon agentic settings — but a
one-paragraph nine-fact item is the wrong place to look for it, and I have now
spent two corpora establishing that.

**The corpus is, however, an excellent clean-room and no-harm guard.** Clean-room
came in at 1.000 on every template, up from a pooled 0.950 that concealed rel-009
sitting at 0.50. Both item defects are fixed, the per-template gate confirms it,
and zero parse failures across 280 items in the control arm means the format
contract is not a source of noise. That is exactly the job
[`ACCUMULATION_VENUE.md`](../docs/ACCUMULATION_VENUE.md) assigns it, and it is now
qualified for that job with a number rather than a hope.

Gate 2 fails and that is not a problem to fix. The corpus is no longer applying
for the flagship role.

## What I got wrong, specifically

I assumed the ceiling was caused by the distractors being off-topic, because that
was the visible defect. It was a real defect and fixing it produced a real, small
effect. But the dominant cause was never distractor quality — it was that the
item is too short for anything to be displaced, and a fact that stays on screen is
not a fact that has to be ranked.

The tell was in the trace read and I underweighted it: only 13 of 93 loaded
responses acknowledged a distractor at all. A model that does not mention the
distractor is not resisting it. It is not seeing a decision there.

## Next

The casefile venue, whose own prediction is recorded in
[`2026-08-11-casefile-venue-prediction.md`](2026-08-11-casefile-venue-prediction.md)
and predates every casefile call. If that probe also comes back at ceiling, the
problem is not the venue and I should say so rather than build a third one.
