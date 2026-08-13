# Trigger corpus v3: real length, and a set a ruler cannot solve

**This is Track N of
[`docs/RESEARCH_PROGRAMME.md`](../../RESEARCH_PROGRAMME.md)**, in Part 3 — the
instrument. It blocks the measurement and not the product, it retro-qualifies
every Track L and Track M number on disk, and its experiments are numbered
`N1`–`N8` there. This file is the design; the programme entry is the place it
sits in the order.

**2026-08-13. A plan, not a run.** Nothing here has been executed. It is written
down first because the corpus is the answer key, and
[`the last four pre-registration slips`](../../../CLAUDE.md) were all cases where
something got built before it got specified.

## The two problems, stated separately

They arrived together and they are not the same problem.

**Problem 1 — the corpus is not the thing it claims to test.** No turn exceeds
23 words. 46 of 73 are ten words or fewer. The `ledger` procedure exists for
*"a pile of context ending in a question about what to do"* and the corpus has
never contained a pile. The longest positive is one sentence *describing* one.
Real users write paragraphs. This is a coverage gap and it is the one the
maintainer named.

**Problem 2 — length is a shortcut, and it is most of the answer.** Positives
run at a median of 18 words, negatives at 8, and the distributions barely
overlap:

| | n | median | range |
|---|---|---|---|
| positives | 17 | 18 | 4–23 |
| negatives | 56 | 8 | 3–17 |

`length_separability` = **0.850**. A bare *"fire if ≥ 18 words"* rule scores
**0.890 accuracy** with no model. The best arm ever measured scores 0.956. So
every result in Tracks L and M was competing for about **six points above a
ruler**.

**Fixing 1 without fixing 2 makes 2 worse.** Adding long positives to a set
where long already means positive widens the gap. The two must be fixed by the
same construction.

---

## The construction: matched triples

The unit of the corpus stops being an item and becomes a **triple**:

> one positive, and two negatives matched to it on length,
> with the same surface features and a different ask.

In the long bands the three share a **body** — the same pasted thread,
statements and documents — and differ only in the sentence at the end:

| ending | label | why |
|---|---|---|
| *"Do I sign the renewal?"* | **positive** | a decision, on this pile |
| *"What's the total of the three deposits?"* | negative | a lookup, over the same pile |
| *"Summarise where this ended up."* | negative | a summary, over the same pile |

This does four things at once, which is why it is the whole design:

1. **It kills the length shortcut by construction, not by hope.** Within a
   triple the three turns are the same length. Across the set, positives and
   negatives therefore have the same length distribution, and
   `length_separability` goes to 0.5 mechanically. It is checked, not assumed.
2. **It makes the negatives hard in the only way that counts.** The current
   negatives are hard *by hand* — each was written to wear a trigger's surface
   feature. A twinned negative wears every surface feature of its positive
   because it is byte-identical up to the last sentence. Precision measured
   against these is precision.
3. **It cuts the authoring cost roughly threefold** in the expensive bands. One
   1,200-word body yields three items.
4. **It gives the statistics a cluster.** The triple is the resampling unit,
   the way templates already are for `rel-*`. Three items sharing a body are
   correlated, and a per-item bootstrap over them would produce standard errors
   that are wrong in the anti-conservative direction.

**The cost taken on knowingly:** one badly-written body damages three items
instead of one. Body defects are therefore adjudicated at the body level and a
retired body retires its whole triple.

---

## The grid

Four length bands. **S is exactly the v2 range**, so the old corpus survives as
a stratum and v3 can be asked whether it reproduces v2 inside it.

| Band | Words | Triples | Positives | Negatives | Shared body? |
|---|---|---|---|---|---|
| **S** | ≤ 25 | 14 | 14 | 28 | no — matched on word count ±2 |
| **M** | 40–90 | 10 | 10 | 20 | optional |
| **L** | 200–400 | 9 | 9 | 18 | **yes** |
| **XL** | 900–1500 | 7 | 7 | 14 | **yes** |
| | | **40** | **40** | **80** | |

**120 items, 40 positives, 80 negatives.**

Why these numbers:

- **1:2 in every band.** Equal ratios per band is the condition that makes the
  length AUC 0.5 across the whole set, not just inside a band.
- **40 positives, not 17.** Recall granularity goes from 5.9pp per item to
  2.5pp. This is why the L7 recall band was unsettable: at 17 positives, one
  item that never fires puts the ceiling at 0.941 and a band at 0.94 demands
  perfection everywhere else.
- **80 negatives.** Close to the current 56, enough that an FPR of 0.02 is
  distinguishable from 0.00 at all.
- **XL is only 7 triples** because 1,200 words × 7 is already 8,400 words of
  authored body and the marginal item there is expensive. It is the band that
  finally tests `ledger`, so it cannot be zero.

Authored volume: roughly **11,000 words of bodies** plus 120 endings.

---

## The four gates the corpus must pass before any model sees it

All four are code, all four are free, and all four run in `de check`.

### Gate 1 — length, two-sided

`MAX_LENGTH_SEPARABILITY = 0.70` is **one-sided and that is an instrument
defect**. A set at AUC 0.05 is solved by a ruler exactly as well as one at 0.95;
the classifier just points the other way. The gate becomes a band:

```
0.40 <= length_separability(set) <= 0.60
```

The existing ratchet on `length_separability_ceiling` stays for v2 and is
deleted when v3 lands, because v3 is required to be *inside* the band rather
than merely not getting worse.

### Gate 2 — the rest of the ruler drawer

Fixing length and then discovering that `"should I"` solves 80% would be the
same mistake twice. `length_separability` generalises to
`trivial_separability(feature)` over a declared battery:

| Feature | What it would mean if it separated |
|---|---|
| word count | the current defect |
| character count | word count wearing a hat |
| contains *"should I" / "should we"* | the label is a phrase match |
| question-mark count | the label is punctuation |
| first-person pronoun rate | positives are about the speaker and negatives are not |
| paste cues (*here's, below, attached, pasted*) | the label is a formatting habit |
| imperative-verb-initial (*draft, fix, rename, summarise*) | the negatives are all commands |
| type-token ratio | the two classes were written in different registers |

Each reports an AUC and each must land in **[0.40, 0.60]**.

**And a combined check, because a battery of singles misses interactions:** a
depth-2 decision stump fitted over the whole battery must not exceed **0.70
accuracy**. Fitted and scored on the same data, deliberately — this is an
upper bound on what a shortcut can reach, so optimism is the conservative
direction.

### Gate 3 — balance

Mechanical, and it is what makes gate 1 hold rather than being achieved by
accident:

- every band has exactly a 1:2 positive-to-negative ratio;
- inside a triple, the three word counts are within ±10% of each other;
- inside a band, the positive and negative median word counts are within 10%;
- every item declares its `band` and its `triple`, and every triple has exactly
  three members with exactly one positive.

### Gate 4 — realism

A 1,200-word turn that reads like an example written for a test is not a test.
The repo's realism audit has been at 0% since it was written down, and it
matters far more at 1,200 words than at 12.

- **Human audit, 10% of items**, which is 12 items and is not optional.
- **Machine probe, descriptive not blocking:** a fresh instance is shown a mixed
  sample and asked which turns look like a real message and which look authored
  for a benchmark. Reported as a rate. It is not a gate because *"looks
  authored"* has no ground truth, and a gate without ground truth is how a
  corpus gets tuned to a judge.

Bodies must carry real artefact texture — timestamps, copy-paste seams,
inconsistent formatting, sentences that trail off, numbers that appear twice in
different formats. Prose written to be *read* is the tell.

---

## Carry-over, and how items get retired

The S band takes 42 of v2's 73 items. **31 items are retired**, and retirement
is where a corpus rebuild can quietly launder a result, so the rule is
mechanical and stated before it is applied:

An item is retired if it is a **duplicate mechanism** — a second or later item
testing a failure mode already covered by an earlier one under the same `why`
category. v2 has clusters of these: `x-n24`–`x-n29` are six variants of
"meta or acknowledgement", `x-n46`–`x-n48` are three variants of
"underspecified", `x-n38`–`x-n41` are four variants of "mechanical task". One
survives from each cluster; the rest go.

**The rule does not read per-item outcomes, and I already know them, so the
rule alone is not enough.** After applying it, the plan publishes: *of the 31
retired items, how many did some arm get wrong?* If retired items are cleaner
than kept items, the rule was biased and the retirement is redone. The number
goes in the corpus header whatever it says.

The five provisional `x-` positives (`x-n03`, `x-n20`, `x-n22`, `x-n23`, and
`x-n21`, now a negative) **all carry over unchanged**, including `x-n22`, which
has never fired in any arm on any version. Dropping it would raise recall
across the board for free, which is the same move as the label change on
2026-08-13 that gave every arm five points it did not earn.

---

## The largest risk: the labels, not the turns

**Twenty-one of twenty-one scored failures across three corpora were the answer
key.** v3 multiplies the key's surface area by roughly fifty. A 1,200-word turn
has fifty times as many places for me to be wrong about what it is asking, and
the error would be **correlated with the independent variable** — long items
would look harder because their labels are worse.

Three defences, in order of cost:

1. **Every label carries a written `why`**, as now, and for twinned items the
   `why` must state *which sentence* makes the difference. If the difference
   cannot be named in one sentence, the triple is not built.
2. **Blind adjudication before the run, not after.** Three independent
   instances label each turn fire/no-fire, given the skill's own `Abort if`
   clauses and no access to my label. This is the check that has never run here.
   - unanimous agreement with my label → keep
   - 2-of-3 against me → I rewrite the turn or move the label, and say which
   - split 3 ways → the triple is retired as genuinely undecidable, the way
     `route: ~` already handles open routing
3. **Pre-registered kill: > 20% of items changing label at adjudication retires
   the corpus** and v3 is re-authored rather than reported. Given 21/21, this is
   the falsifier most likely to fire.

Routing labels get the same treatment, and the long bands are where `ledger`
becomes testable for the first time — it currently has three items, all of them
short, none of them an actual pile.

---

## The threat that no gate above touches: a model is writing it

The turns are hand-authored, one at a time, not generated from templates — the
`rel-*` corpus is template-generated with computed ground truth and this one
cannot be, because *"is this a decision"* has no computable answer.

**That is not the sharp version of the objection, and the sharp version stands.**
A model is authoring the corpus that will be used to evaluate a model of the
same family. I write a positive the way I would recognise a positive. Every
accuracy figure this corpus produces is inflated by that, in a direction nothing
inside the corpus can measure.

There is no evidence this is fine. The evidence available points the other way,
and some of it is first-hand and in this repository:

- **21 of 21 scored failures across three corpora were my answer key**, not the
  model. That is the strongest evidence here and it is about exactly this.
- The long-context plan already treats model-authored padding as a threat
  serious enough to gate on — the detectability probe — for this reason.
- `SkillsBench`, already cited in `CLAUDE.md`: self-generated skills score ≈0 or
  negative.
- There is published work on self-preference in LLM-as-judge setups (models
  scoring their own generations higher). It is **not cited here** because it has
  not been verified first-hand, which is a Track K job and the rule `de check`
  enforces.

**Blind adjudication does not fix this.** The adjudicator is also a model. It
catches a wrong label; it cannot catch a turn written in the register a model
finds legible.

### The fix is a control, not a disclaimer

**A human-authored holdout.** The maintainer writes — or supplies from real
messages — a set of turns under the same grid, labelled by them, never seen by
me before authoring is closed. Every arm is then reported twice:

| | model-authored items | human-authored holdout |
|---|---|---|
| firing accuracy per arm | | |
| arm ordering | | |

- **Orderings agree** → the authoring threat is bounded, and it is bounded by a
  measurement rather than by an argument.
- **Orderings disagree** → the model-authored corpus is decoration, and we know
  it rather than publishing on it.

Twenty turns is enough to see a reversal. The cheapest good source is real
messages that already exist rather than turns written to order, because a turn
written *for* a benchmark is the artefact under suspicion whoever writes it.

### What the corpus licenses until that holdout exists

It is a **relative** instrument. Every arm sees identical items, so comparisons
*between* arms are valid and that is what Tracks L and M ask for.

It licenses **no absolute claim** about behaviour on real user messages. A
sentence like *"the shipped description fires correctly 94% of the time"* is not
available from this corpus at any point, and was not available from version 2
either. That distinction is the same one `SCORECARD.md` draws between a verdict
and a usable skill, and it is the reason this repository exists.

---

## What must not change at the same time

A corpus change plus a description change plus a label change is three
manipulations and zero attributions. So in v3:

- the shipped `SKILL.md` description is **byte-identical**;
- the four procedures and the router table are **unchanged**;
- the arm menu (`full`, `opener-only`, `no-opener`, `no-exclusions`,
  `stakes-named`, `stakes-shown`, n=2, n=4) is **unchanged**;
- carried-over items keep their v2 route labels unless adjudication moves them.

The only thing that varies is the corpus. That is what makes "do the arm
orderings survive?" a real question.

---

## Instrument changes

| File | Change |
|---|---|
| `triggers.py` | `TriggerCase` gains `band` and `triple`; `TriggerSet` gains `bands`; `length_separability` → `trivial_separability(feature)` plus the battery and the stump; two-sided band replaces `MAX_LENGTH_SEPARABILITY`; `_check_balance` added |
| `run_triggers.py` | record `band`, `triple`, `set_version: 3`; `--band` to run one stratum; headline reports per band |
| `trigger_arms.py` | per-band summaries; cluster the bootstrap on `triple`, not on item |
| `datasets/triggers/` | `decision-making.yaml` → v3; v2 preserved at `decision-making-v2.yaml` so old records stay checkable |
| tests | balance, two-sided band, battery, stump, triple integrity, and a test that v2 still loads |

`label_versions_comparable` already refuses to compare across versions and
needs no change. That is the one piece of this that is already in place.

---

## Phasing and cost

**Standing rule 5: the call count is stated before anything starts.**

| Phase | What | Calls | Blocking? |
|---|---|---|---|
| 0 | instrument: bands, balance, battery, stump, clustering | **0** | yes |
| 1 | S band — carry-over, retirement, matched negatives authored | 0 | yes |
| 2 | M band authored | 0 | yes |
| 3 | L and XL bodies authored (~11k words) | 0 | yes |
| 4 | gates 1–3 run; re-author until they pass | 0 | yes |
| 5 | blind label adjudication, 120 items × 3 | **360** | yes — 20% kill |
| 6 | realism: 12 human, machine probe on 40 | **40** | no |
| 7 | pre-registration written and committed | 0 | yes |
| 8 | **confirmatory** re-run: `full`, `stakes-shown`, `opener-only` × 120 × 2 repeats | **720** | — |
| 9 | **descriptive** re-run: the remaining 5 arms | **1,200** | — |

**Total ≈ 2,320 calls.** For scale, everything this repository has run to date is
about 3,950. At roughly 4–6 seconds a call this is **three to four hours of
serial wall-clock**, spread across quota windows. The runner is checkpointed and
resumable, which is why this is a scheduling problem and not a budget one.

Phases 8 and 9 are separated so that a stop after phase 8 still leaves a
complete, pre-registered, three-arm result rather than a partial grid.

Two repeats, not five: ICC was 0.833 (M5) and 0.852 (M6), and
`repeats_for_reliability` returns 2.

---

## What gets pre-registered before phase 8

Written in `notebook/` with estimator **and denominator** named, per the rule
that four slips on 2026-08-12 produced.

| # | Question | Why it is worth asking |
|---|---|---|
| 1 | Does firing accuracy fall on the long bands? | Everything measured here sits on turns under 25 words. If accuracy is flat from S to XL, the six-point ceiling was real and the nulls stand. If it falls, five nulls were a ceiling artefact and Tracks L and M are re-openable. |
| 2 | Do the arm orderings survive the corpus change? | `stakes-shown` beat `full` on precision on v2. Reproducing that on a corpus built to different rules is far stronger evidence than any single v2 run. |
| 3 | How does `ledger` route once the corpus contains piles? | It has never been tested on its own case. Prediction to be written down: it is the worst-routed of the four. |
| 4 | Does a twinned negative fire more than a hand-written one? | If yes, the old negatives were easy and every precision figure on record is optimistic. |

**Question 1 is the experiment.** It is also the one that can retire the
repository's current headline, which is the reason to ask it.

---

## Falsifiers

- **Gates 1–3 cannot be met** without writing turns nobody would send. Then the
  length confound is intrinsic to the task — long messages really are more often
  decisions — and that is a finding to report, not to engineer around. The
  corpus ships with the honest AUC and every claim is stated as conditional on it.
- **Adjudication moves > 20% of labels.** Corpus retired, not reported.
- **Accuracy is flat across bands and the arms re-order anyway.** Then the
  measurement is noisier than any effect it has been used to detect, and the
  right conclusion is that the trigger instrument does not have the resolution
  for the questions Tracks L and M have been asking it.
- **The stump beats 0.70 on features I did not think of.** Expected, at least
  once. The battery is a list of my own guesses about how a corpus can be
  cheated, and it will be incomplete.

---

## What this does not fix

Firing is still measured separately from answer quality, and this plan touches
only firing. A description that fires perfectly on 120 turns and produces worse
advice than thinking directly would pass every gate here. That is Track S's
job and nothing in v3 brings it closer.
