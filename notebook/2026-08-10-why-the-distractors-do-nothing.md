# 2026-08-10 — The distractors do nothing, and reading the traces says why

Written while the control run is still going, at 110 of 280 records, so that the
diagnosis is on the record before the final number is. The prediction in
[the previous entry](2026-08-10-first-calibration-and-a-defective-item.md) is
going to be confirmed and then some.

## The number so far

110 of 110 correct. Every template, every stratum, including four distractors in
every position. Not "above the [0.35, 0.75] band" — at the ceiling.

## The interesting part is not the accuracy

A ceiling on its own says "make it harder", which is not actionable. So I read
the transcripts. Here is a four-distractor item in full:

> The Tailspin contract SLA requires **downtime exceeding 15 continuous hours**
> to trigger penalties. Yesterday's incident caused **10 continuous hours** of
> downtime. Filing a claim costs nothing and has no effect on renewal terms.
>
> The incident does not meet the SLA threshold. […] ANSWER: wait

Four distractors were in that prompt. The response does not mention any of them.

That is not a one-off. Across all 93 distractor-present records, only **13**
contain any acknowledgement that something was irrelevant — no "unrelated", no
"does not affect", no naming-and-discarding of any kind. Output length tells the
same story: 483 tokens at zero distractors, 658 at one, 710 at four. The jump is
in *reading* them, and then almost nothing for adding three more.

The model is not ranking the context and getting the ranking right. It is not
ranking the context at all.

## Why, concretely

Look at what a distractor in `rel-001` actually is, against a rule of
`outage_h > sla_h`:

```
d1  {vendor} redesigned its public status page last quarter.
d2  The {region} region accounts for the largest share of {vendor} customers.
d3  The support organisation has {headcount} people across all products.
d4  {vendor} moved its head office to a new building in March.
d5  The office coffee machine was serviced on Tuesday.
```

There is no mechanism by which any of these could enter a comparison of two
durations. `d3` at least carries a number, and it is a headcount. The `strength`
labels I attached rank them by *topical proximity to the vendor*, which is not
the axis that matters — it is a bag-of-words notion of relatedness, and the model
is not a bag of words.

Compare what GSM-NoOp's distractors were: numbers **in the units of the
computation**, sitting right next to the numbers you need. "Five of them were
smaller than average" is dangerous because it is a plausible input to the
subtraction. "The coffee machine was serviced on Tuesday" is not a plausible
input to anything.

So the failure mode I built the corpus to elicit was never available to elicit.
This is the same lesson as the knife-edge item two entries ago, arriving from
the opposite direction: that time I made an item unfairly hard by being
imprecise, this time I made 280 of them trivially easy by being irrelevant in
the wrong way.

## What a distractor has to be

A distractor earns its place only if it is a **plausible input to the same
computation** — same type, same units as something the solution reads — and is
excluded only by a qualifier a careful reader has to notice:

```
d1  A separate degraded-performance window lasted {degraded_h} hours.
d2  The {vendor} support contract promises a {response_h}-hour first response.
```

Both are durations in hours. Neither is *continuous unavailability*, and neither
is the *penalty threshold*. A reader who tracks which quantity is which gets the
right answer; one who grabs the nearest number in the right units does not.

That is the failure mode the flagship claims to fix, and it is finally in the
item.

## The line I have to stay on

There is a narrow band here and it has a cliff on each side.

Too far away and you get what I have now: no effect, because nothing competes.
Too close and you get the thing the 2026 GSM-NoOp re-audit dissolved — an
"irrelevant" fact a reasonable solver would fold in, where the model that
"fails" is defensibly right and I have measured my own ambiguity. The re-audit
kept 117 of 945. I should expect to throw away most of what I write.

The rule I am adopting, because it is checkable rather than a matter of taste: a
colliding distractor must state its quantity with an **explicit qualifier that
distinguishes it** from the load-bearing one, in the same sentence. "Degraded
performance" against "unavailable". "First response" against "downtime". If I
cannot write that qualifier, the fact is ambiguous rather than irrelevant, and it
goes in the bin rather than in the template.

The two-auditor filter still applies on top. This narrows what gets *submitted*
to it; it does not replace it.

## Two defects, not one

Type-incompatibility is the one I can fix today. The other is unchanged from the
prediction and is not fixed by better distractors:

**Nine short facts in a 328-token single-turn prompt is not context
accumulation.** The whole pile fits comfortably in attention, in one turn, with
nothing to displace and nothing to forget. arXiv:2606.29718 documents 30–50%
degradation in long-horizon agentic search, not in short prompts, and the
short-horizon case is roughly what the re-audit dissolved. I have been testing
the venue where the effect is known to be absent.

So the corpus needs both: distractors that can actually compete, and a venue
where there is enough context for ranking to matter. The first is a schema
change and a rewrite. The second is a new item format, and is the larger piece
of work.

## Recorded before doing either

Fixing type-compatibility alone will move the number, and I do not expect it to
move it to the band. My guess is somewhere in the high 0.8s rather than 1.0 —
enough to prove the mechanism is real, not enough to make a single-turn
nine-fact item a usable venue. If that is right, the accumulation format is
required rather than optional, and the single-turn corpus survives only as the
clean-room and no-harm stratum, which is a job it is genuinely good at.

If it lands inside [0.35, 0.75] I will have been wrong about the venue and the
single-turn corpus stands. Recording the number I expect so that either outcome
costs me something.
