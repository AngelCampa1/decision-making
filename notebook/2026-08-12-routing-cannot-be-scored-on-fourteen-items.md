# Routing cannot be scored on fourteen items

**2026-08-12.** Track L / Track M power check, computed from the
[five-repeat run](2026-08-12-five-repeats-firing-is-stable-routing-is-not.md).
No numeric band was registered for this — it is an **instrument measurement**,
not a hypothesis test, and nothing below scores a prediction. It is written down
because it decides whether a whole class of planned runs can answer anything.

## The question

Track L wants to compare skill variant A against skill variant B on the same
job. Three of its six axes (L1 framework, L5 trigger breadth, L6 revision) would
naturally be scored on **routing accuracy** — did the router send the case to the
right procedure. The trigger set has **14 routed items**. Is that enough?

## The measured input

Take the five repeats pairwise — same skill, same items, two independent draws —
and count the items whose correctness differs between the two. That is the
**discordance floor from sampling noise alone**, which any between-variant
comparison inherits on top of whatever the variant actually does.

| repeat pair | 0-1 | 0-2 | 0-3 | 0-4 | 1-2 | 1-3 | 1-4 | 2-3 | 2-4 | 3-4 |
|---|---|---|---|---|---|---|---|---|---|---|
| discordant share | .214 | .214 | .286 | .143 | .143 | .071 | .071 | .214 | .071 | .143 |

**mean `p_discordant` = 0.157**, i.e. about **2.2 of the 14 items flip on their
own** between any two runs of the identical skill.

## What that buys

`required_pairs` (`stats/power.py`), Connor's approximation, α=0.05, power 0.8,
one-sided:

| effect to detect | pairs needed |
|---|---|
| 10pp | **95** |
| 15pp | **41** |
| 20pp | *impossible* — an effect cannot exceed `p_discordant`, and the function refuses |

The set has 14.

## The exact test is worse than the approximation says, and this is the real finding

At n=14 the binomial is coarse enough that the normal approximation flatters it.
Exact one-sided McNemar needs **k ≥ 5 discordant pairs all pointing the same
way** (0.5⁵ = 0.031). Under the null, at `p_discordant` = 0.157:

- E[discordant] = **2.2**
- P(reject) = **0.0015** — the nominal α is 0.05 and the test's real size is a
  thirtieth of that. It is not underpowered so much as **nearly unable to fire**.

So ask the ceiling question instead: **how often would a *perfect* variant win?**
One that routes all fourteen correctly and breaks nothing. Then the discordant
count is exactly the number the baseline got wrong:

| repeat | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| baseline wrong | 2 | **5** | **5** | **6** | 4 |

**A flawless variant clears k ≥ 5 in three of five draws.** Its power is roughly
0.6 — against a target of 0.8, on the best possible intervention that could
exist. A variant that fixed half the errors would essentially never reject.

## What this means for the programme

**Routing is not a scoreable outcome at the current corpus size, for any Track L
axis, at any number of repeats.** Repeats shrink the noise on the *estimate* and
do not change the item count, and the item count is what the exact test is
counting.

Three ways out, and they are not equivalent:

1. **Score on firing, not routing.** 73 items, precision 0.942 / recall 0.878 /
   FPR 0.018, 70 of 73 identical across five repeats. This is a real instrument
   and L5 (trigger breadth) is *about* firing anyway. Cheapest and honest.
2. **Grow the routed stratum to ~95 items.** That is what a 10pp routing effect
   costs. It is a corpus decision, not a run decision, and it should be priced
   before anyone authors item fifteen.
3. **Report routing descriptively with intervals and no p-value**, as the
   programme already requires for anything beyond five secondaries.

**What must not happen** is a Track L round scored on 14-item routing and
reported as a null. That null would be a property of the sample size, and it
would look exactly like a finding about skills.

## Caveat on the number itself

`p_discordant` = 0.157 is estimated from **10 correlated pairs drawn from 5
repeats**, not 10 independent replications, so its own standard error is
understated. The direction of the conclusion does not depend on that — the exact
test's k ≥ 5 requirement against 14 items is arithmetic, and it holds whatever
`p_discordant` turns out to be.
