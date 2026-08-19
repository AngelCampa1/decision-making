# 2026-08-19 — prediction: Track H Phase 0, is there anything for tailoring to help with?

Registered **before any Track H item is authored**, before the extractor is
written, and before the first call. Nothing in Track H has ever run:
`docs/STATUS.md:397` reads *"**H** — tailoring, life decisions | 🔴 not started"*,
and no Track H item exists anywhere in this tree. Every sentence below about what
Phase 0 does is in the future tense on purpose.

This entry registers **H1**, the row added to
[`docs/RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md) in the same change.

## Why this is registered now rather than after C/D/E/F

The programme specifies Track H as *"Not a separate venue, but a task family that
runs inside C, D, E and F"*. C, D, E and F have not started. **Running Track H
standalone is a deviation from the programme and it is named as one** in the H1
subsection; this entry does not re-argue it, it registers what the deviation will
measure.

The reason it is worth deviating for, stated so it can be falsified: four of the
five closed venues (`docs/STATUS.md`, *Venues built*) measure verifier-backed
**accuracy** — 0.946, 0.971, 0.917, `p_discordant` 0.000 — and closed because the
unaided model was already at ceiling. Track H's primary is not an accuracy. It is
a **within-triplet contrast**, so reading the item well raises one of its two
terms and says nothing about the other. That is a structural argument and it may
be wrong; *Where I expect to be wrong* says how.

## What will run

- **20 triplets.** 20 invented life cores × 3 files each — base, governing fact
  changed, matched non-governing fact changed of equal salience. 60 files.
- **Control arm only. No skill arm.** The question Phase 0 asks is not *does
  `fit.md` help* — it is *is there anything here for `fit.md` to help with*.
- **2 repeats.** Derived, not chosen: Track I measured ICC 0.83–0.85 and
  `docs/STATUS.md:100` records the conclusion as *"**Two, not five.** Cut every
  later arm by 60%."* N6, N7 and N9 each used that derivation rather than a fresh
  choice, and so does this.
- **Both non-negotiables held.** The matched non-governing arm is not cut and the
  elicited-quantity primary is not cut. The programme has a boxed warning about
  exactly this and it is right: cutting the third arm does not shrink the metric,
  it destroys it, silently.
- **Dates in both cores and any padding**, in one of the two formats
  `scripts/separability.py` actually matches. Track G's carry-forward finding is
  free and applies to anything authored from here.
- **No real personal data.** Every persona invented.

### Calls, with arithmetic

| call type | count | derivation |
|---|---|---|
| control generation | 20 × 3 × 2 = **120** | 20 triplets × 3 files × 2 repeats |
| blind quantity extraction | 3 × 120 = **360** | `ADJUDICATORS = 3`, `scripts/adjudicate.py:96`, over every generated response |
| falsifier battery | 2 × 3 × 3 = **18** | 2 planted triplets × 3 hand-written responses × 3 judges. Responses are hand-written, so no generation calls |
| **total** | **498** | |

**This corrects a count I was handed.** The prior analysis put Phase 0 at 318
calls by adjudicating 60 responses. There are 120 responses, not 60 — the repeat
dimension was present on the generation line of that table and absent from the
adjudication line directly beneath it. 3 × 120 = 360, and the total is 498.

Notional cost: prompts land at ~1,500–2,500 characters, so `estimate_cost_usd`
(`evals/src/decision_evals/budget.py:84`, `max(tokens * 2.5e-6, _FLOOR_USD)` with
`_FLOOR_USD = 0.005` at line 60) returns the floor on every call.
**498 × $0.005 ≈ $2.49 notional.** Nothing is billed; this is a burn meter for
quota, not money, and nothing is purchased — the corpus is authored in-tree from
invented personas, so the outside-data rule does not engage at all.

## What will be computed, from which records, over which denominator, by which function

`CLAUDE.md` requires this to be writable before a run is called ready. It is four
paragraphs because one of them would otherwise hide the denominator.

**First, an identity, because it collapses two of the programme's quantities into
one.** Track H's stated primary is
`d = P(change | governing) − P(change | matched non-governing)`, reported
alongside Youden's J. These are the *same number*:

```
J = sens + spec − 1
  = P(change | governing) + (1 − P(change | matched)) − 1
  = P(change | governing) − P(change | matched)
  = d
```

So there is one primary, not two, and the sensitivity/specificity pair is its
decomposition rather than a second estimator. Both will be printed.

**Second, the unit.** Each `(triplet, repeat)` pair contributes exactly one
sensitivity event (did the elicited quantity move when the governing fact
changed?) and exactly one specificity event (did it hold when the matched
non-governing fact changed?). That is **40 sensitivity events and 40 specificity
events over 20 triplets**. The rate denominator is 40; the **inference
denominator is 20 clusters**.

**Third, the function.** `d` is a *paired* mean difference of two indicator
vectors sharing an item order, which is precisely
`stats.cluster.cluster_bootstrap_diff(control, treatment, clusters)`
(`evals/src/decision_evals/stats/cluster.py:139`) with `control` the matched-arm
change indicators, `treatment` the governing-arm change indicators, and
`clusters` **the triplet id**. Its own docstring states why the cluster argument
is the load-bearing one: whole clusters are drawn with replacement so that
within-cluster correlation reaches the interval, *"which is exactly what an
item-level bootstrap fails to do."*

**Fourth, and this is the half that has already gone wrong here.** Nothing in
this analysis may be pooled over the 60 files or the 120 responses. Defect nine
on `docs/STATUS.md`'s broken-measurement list (line 173) is *"pooled AUC used on
a matched corpus"*, where the pooled statistic *"ranks positives against
negatives from other triples"* and was structurally blind to the rank held
**inside** a triple. Track H is a matched design of exactly that shape. Pooling
its files would repeat, in the venue built to escape the other five, a defect
those five already recorded.

Agreement among the three extractors will be reported with `stats/agreement.py`'s
`fleiss_kappa` and `krippendorff_alpha` over the same 120 responses. That is a
health check on the instrument, not a result.

### The movement threshold, which the programme does not supply

The programme says the primary is an elicited quantity *"not a flip"*, and in the
same section states the metric as a difference of two **probabilities of change**.
Both halves are reasonable and together they leave a hole: turning a continuous
quantity into `change` / `no change` needs a threshold, and **no number for it
exists anywhere in this repository.** Standing rule 1 forbids inventing one.

So the *rule* is registered here and the *number* is derived from the run's own
base arm, before any governing or matched contrast is looked at:

> Movement is relative: `|q_variant − q_base| / |q_base|`. The threshold is the
> **maximum** of the 20 base-vs-base relative differences — repeat 0 against
> repeat 1 of the *same* base file, which is pure instrument noise and carries no
> perturbation at all. A contrast counts as `change` only if it exceeds the
> largest excursion the instrument produced when nothing was changed.

Two consequences, stated before the fact. With n = 20 the maximum is an upper
extreme and one noisy base pair sets the bar for all twenty; that is conservative
in the direction of *under*-reporting movement, which pushes sensitivity down and
J down — **against the kill and toward the venue looking alive**, so it is a bias
in the direction I would prefer, and it is recorded here rather than discovered
later. And if base-vs-base noise is large enough to swallow every real
perturbation, the result is sensitivity ≈ 0 with specificity ≈ 1, which is the
inert-estimator signature the guard below exists to catch and is not a finding.

## The kill criterion, and its arithmetic

> **Kill: if the unaided control arm reaches Youden's J ≥ 0.70 over the 20
> triplets, Track H Phase 0 closes and the venue joins the other five.**

**The arithmetic, checked rather than asserted.** J = sensitivity + specificity −
1. At sensitivity 0.85 and specificity 0.85, J = 0.85 + 0.85 − 1 = **0.70**,
exactly. And 0.85 is `ADMISSIBILITY_CEILING` — `scripts/probe_casefile.py:49`,
`ADMISSIBILITY_CEILING: Final = 0.85` — the one adequacy constant this repository
has already pre-registered and already used to close a venue, since Track G's 2k
casefile rung failed against it at 0.917. The correspondence holds, so the band
comes from the constant rather than from a round number, and the kill reads: *if
the unaided model is already at this repository's own registered adequacy level
on both arms at once, there is nothing for a skill to add.*

It is also exactly reachable at this resolution. Each arm moves in steps of
1/40 = 0.025, and 0.85 × 40 = **34 events out of 40** on each arm, an integer, so
the band names a state the instrument can actually occupy.

**One thing the round number hides, registered rather than glossed.** J ≥ 0.70 is
*implied by* both arms at 0.85 but is **not equivalent to it**: J is a difference,
so (1.00, 0.70) and (0.70, 1.00) reach it too. The symmetric point is what
motivates the constant, not what the kill tests. Therefore
`min(sensitivity, specificity)` **will be printed beside J**, and if J ≥ 0.70
arrives with one arm below 0.85 the disposition will say so in those words rather
than reporting "both arms adequate".

### Standing rule 2: the falsifier battery runs first, and no J is reported before it passes

A gate may not fail anything until it has passed a case it should pass. Two
falsifiers were wrong here on 2026-08-11 and both would have killed healthy
venues.

**Before any J is computed**, two planted triplets will be authored with
**hand-written** responses: one where the elicited quantity obviously *must* move
between base and governing, one where it obviously *must not* move between base
and matched. The three extractors will be run over those six responses — 18
calls — and the battery must score **sensitivity 1.0 and specificity 1.0**.

**If it does not, the extractor is the finding and no J is reported at all.** Not
a caveat attached to a number: no number.

A second guard, because a plausible zero does not announce itself. `docs/STATUS.md`
records five separate inert-estimator instances, one of them inside the module
whose job was hunting inert estimators. **The raw per-arm movement counts will be
printed beside J, never J alone.** If specificity = 1.000 while sensitivity =
0.000, the first hypothesis is an extractor answering "no movement" to everything,
not a model that never tailors.

## Predictions

Each names its estimator and its denominator. All are about the **unaided control
arm**; there is no skill arm in Phase 0.

1. **Sensitivity will be high: ≥ 0.85, i.e. ≥ 34 of 40.** Estimator: proportion of
   `(triplet, repeat)` governing contrasts exceeding the registered movement
   threshold. Denominator 40 events, clustered on 20 triplets. *Direction: high.*
   The authoring gate requires a professional to be able to state the governing
   fact in one sentence, and detecting a plainly stated fact is the reading task
   that scored 0.946 and 0.971 in the closed venues.

2. **Specificity will be the lower of the two, and below 0.85: < 34 of 40.** Same
   estimator on the matched contrasts, same denominator, same clustering.
   *Direction: low.* This is the whole bet. Holding still on a salient but
   non-governing change is not the same act as noticing a governing one.

3. **J will land below 0.70 and the venue will survive.** Estimator:
   `cluster_bootstrap_diff` over the paired indicator vectors, clustered on
   triplet, 20 clusters, 95% percentile interval. *Direction: J < 0.70.* This is
   predictions 1 and 2 combined and it is the registered pass condition, so it is
   the prediction most exposed to my wanting the venue to live.

4. **The 95% cluster-bootstrapped interval on J will be wide: width ≥ 0.30.** Same
   estimator, same 20 clusters. *Direction: wide.* Twenty clusters is very few, and
   if N6's near-zero triple ICC transfers, the clustered interval will not be much
   narrower than an item-level one. Registering the width now stops a wide interval
   later from being read as a surprise.

5. **The base-vs-base movement threshold will be non-trivial: > 0.05 relative.**
   Estimator: maximum of the 20 base repeat-0 vs repeat-1 relative differences.
   Denominator 20. *Direction: above 0.05.* An elicited quantity asked twice on
   identical input will not come back identical. If it does — threshold ≈ 0 — then
   nearly every contrast counts as movement, both rates go extreme, and prediction
   5 failing low is a **warning about predictions 1 through 3**, not an
   independent result.

6. **Fleiss kappa across the three extractors will be ≥ 0.70.** Estimator:
   `stats/agreement.py`'s `fleiss_kappa`; denominator 120 responses × 3 raters.
   *Direction: high.* Extracting a stated quantity is much closer to parsing than
   to the label judgements that scored 0.862 in N3. Below 0.70 the instrument is
   the finding.

## Where I expect to be wrong

**The strongest in-tree objection is N6's triple ICC, and it points the wrong
way.** N6 measured the ICC of matched triples at **0.00–0.06**, against the 0.315
its own power arithmetic had assumed, and `docs/STATUS.md:104` says in terms that
*"that planning figure may not be reused."* That is **this repository's only
measurement of how much signal a matched triple actually carries here, and it was
near zero.** Track H is a matched-triple design. If matched triples carry almost
no shared signal in this tree, clustering on 20 triplets buys nothing, prediction
4's interval is wide for a worse reason than I gave, and the premise that a
*within-triplet* contrast is more informative than a pooled rate is weaker than
the opening section claims.

The honest weakening, which does not dispose of the objection: N6's ICC is over
**trigger-firing judgements**, on a different corpus, with a different construct
and a binary outcome, so it constrains a *planning figure* rather than the
construct. But it is a real measurement, on disk, against the exact structure
being registered here. It will not be quietly omitted from the write-up if Phase
0 lands badly.

**Second: the authoring gate's difficulty dial and its validity dial may be the
same dial.** The gate requires that a licensed professional could state in one
sentence why the generic answer is wrong here, citing only the governing fact. An
item that clears that bar has a governing fact plain enough to state in one
sentence — and *noticing that the matched fact is not that fact is the same
reading act performed a second time*. If so, prediction 2 fails: specificity goes
high alongside sensitivity, J clears 0.70, and this is the sixth closure.
Loosening the gate so the governing fact is implicit makes the item harder and
simultaneously makes "which answer is concordant for this person" a judgement
call — which puts the result back on the answer key, the failure mode that
accounts for **21 of 21** scored failures across three corpora, twice with the
model producing a better answer than the key allowed.

I do not have an answer to this. What I have is that Phase 0 costs 498 calls and
~35,000 characters of authoring, which is the cheapest available way to find out,
and that the correct response to *"this venue might ceiling too"* is to buy the
measurement rather than to reason about it further.

**Third: the movement threshold is a rule I registered, not a number anyone
measured.** Deriving it from the run's own base arm is better than inventing a
constant, but it is still a decision made today with no prior evidence about how
an elicited quantity spreads across repeats in this harness — because no such
quantity has ever been elicited here. Prediction 5 is the check on it, and if
prediction 5 fails, predictions 1 through 3 are uninterpretable rather than merely
wrong.

**Fourth, and it is about my reasoning rather than about the run.** Five
consecutive predictions in this notebook have been wrong in the same direction,
toward the experiment working. Predictions 2 and 3 are both of that shape. If J
comes back at 0.72, the entry that follows says so, and does not discover a reason
the band should have been 0.75.

## Parameters chosen rather than derived, recorded as choices

Standing rule 1, listed rather than scattered through the entry:

- **20 triplets.** Chosen. It is a screening size, not a powered one: no MDE has
  been computed for this venue, because computing one needs a variance estimate
  from a Track H run and none exists. `stats/power.py`'s
  `minimum_detectable_effect` (line 144) **will** be run against Phase 0's
  observed J and its within-triplet variance to size any confirmatory grid.
  N6's 0.00–0.06 is explicitly not reused as a planning figure, and neither is
  0.315.
- **~1,200 characters per base core.** Chosen, anchored rather than derived: the
  only authored library on disk with a measured per-document size is
  `datasets/library/tax/` — 12 documents totalling **11,471 bytes** by `wc -c`,
  mean ~956. A life core carrying a persona, a situation and a question eliciting
  a quantity is somewhat longer than a tax document, so ~1,200 is that figure
  rounded up, and it is a choice.
- **~150 characters per variant delta**, giving ~1,500 newly authored characters
  per triplet and **~30,000 for 20**, plus ~5,000 for the two planted falsifier
  triplets and their hand-written responses: **~35,000 characters**. Chosen. The
  *on-disk* corpus is larger, ~72,000 characters, because each variant is a whole
  file that repeats its base. The two figures must not be quoted interchangeably.
- **The movement threshold rule**, above. The rule is registered; the number is
  derived from the base arm at analysis time and is not known now.

## What a pass licenses, stated narrowly

J < 0.70 authorises the **skill arm** and nothing else. It does not license any
claim that a skill works: every skill in this repository carries `UNTESTED`, and
`SCORECARD.md` governs what may be said. Phase 0 answers one question — is there
room — and the answer to that question is not an answer about `fit.md`.
