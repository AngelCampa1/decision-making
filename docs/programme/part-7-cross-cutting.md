# Part 7: cross-cutting

**Audience:** the evaluating reader, and in particular anyone picking up a track.

Tracks G, H and I. Volume, tailoring and life decisions, and reliability treated
as an outcome in its own right. Each runs inside the tracks above.

Part 7 of eight. The tracks table, the venue map, the sequencing and the
claim ladder are in [`RESEARCH_PROGRAMME.md`](../RESEARCH_PROGRAMME.md).
Headings below start at `###`, carried over from the split so that a track's
anchor is the one it had in the monolith.

---

Not phases. Each one runs inside the tracks above.

### Track G: volume (demoted)

The long-context experiment, reframed. It is no longer the headline; it is one
interaction term: does context length make the turn and handoff effects worse?
All the machinery survives, including `pad.py`, `separability.py`, the tax
library at AUC 0.679, the domination cap, the depth band and the ablation gate.

Full detail remains in
[`docs/superpowers/plans/2026-08-11-long-context-experiment.md`](../superpowers/plans/2026-08-11-long-context-experiment.md).

On hold: the ~960k characters of pilot library authoring. Track A tells us
whether volume matters at all relative to turn structure. If turns dominate, the
library is sized for the interaction rather than for a main effect, which is a
different and probably smaller corpus.

Two findings from that plan carry forward regardless:

- The 2k casefile venue now fails both gates: admissibility 0.917 against a
  0.85 ceiling, trap rate 0.000. No headroom and no trap bite.
- The separability gate found a defect in the cores, not the padding: all 82
  probe-casefile documents contain zero dates, so realistically-dated padding is
  a perfect tell. Any corpus authored from here on puts dates in both.

### Track H: tailoring, and life decisions

The design brief this repository exists for: *any decision AI helps a human make
needs to be tailored to that human's context.* Not a separate venue, but a task
family that runs inside C, D, E and F, where the accumulated context is a
person's life rather than a client file.

The triplet design survives intact and is the identified version of the metric:

1. Base.
2. Governing fact changed: the recommendation *should* move.
3. Matched non-governing fact changed, of equal salience; nothing should move.

`d = P(change | governing) − P(change | matched non-governing)`, reported as
sensitivity and specificity separately plus Youden's J. Without the third file
the metric is unidentified: a model that flips on any perturbation whatsoever
scores a perfect 1.0.

> Non-negotiable, and here is why, so that a future editor cannot remove it
> without reading the reason. The matched non-governing arm is the third of
> three files and it will look like the cheapest thing to cut when the grid is
> too large. It is the arm where, by design, *nothing is supposed to happen*.
> Cutting it does not shrink the metric, it destroys it, and what remains is a
> flip-rate that reports a perfect score for a model that flips on everything.
> The failure is silent: the number still computes and still looks reasonable.
> The same applies to the elicited-quantity primary below. Neither may be
> dropped "to save a stratum" or "to trim the grid".

The primary is an elicited quantity (months of runway, a threshold, a notice
period), not a flip, because flip-rate scores conditional advice, the best
available answer, as failure.

The construct has a name and a literature, and Track H should use them. Found
2026-08-12, Track K second pass. What the triplet measures is informed
values-congruent choice: does the choice match what *this person* actually
values, given that they understand the options. That is not a coinage here. It
is a validated outcome in the patient decision aids literature, where a 2024
Cochrane review of 209 RCTs and 107,698 participants reports RR 1.75
(CI 1.44 to 2.13) across 21 trials, moderate certainty, alongside high-certainty
effects on knowledge, accurate risk perception and decisional conflict. See
[`DECISION_FRAMEWORKS.md`](../DECISION_FRAMEWORKS.md) row 12.

So: adopt the name and the construct, do not import the effect size. Those are
health treatment and screening decisions, delivered to patients around a
clinical consultation by a static tool; nothing licenses transferring RR 1.75 to
an LLM answering a question about a job offer. What it buys is that Track H's
primary stops being a metric invented here to escape flip-rate, and becomes an
operationalisation of a construct with thirty years of instrument development
behind it, including the *decisional conflict* scale, which measures whether
someone feels able to choose and is the nearest published thing to what a
decision skill is actually for.

In a sub-agent system this gets a second question the single-call venue could
not ask: does the personal context survive the handoff? A sub-agent that
summarises a life into a report is exactly where tailoring dies.

No real personal data. Every persona invented; the datasheet says so.

The authoring gate: for each life core, could a licensed professional state in
one sentence why the generic answer is wrong here, citing only the governing
fact? If not, it is a preference survey and it is cut.

| # | Experiment | Cost | State |
|---|---|---|---|
| H1 | **Phase 0: the control arm, before a corpus.** 20 invented life cores × 3 files (base / governing fact changed / matched non-governing fact changed) = **60 files**, ~35,000 newly authored characters (~1,200 per base core, ~150 per variant delta, ~1,500 per triplet × 20, plus ~5,000 for the falsifier battery); the on-disk corpus would be some 180,000 characters, because each variant is a whole file repeating its base and the eight triplets authored so far measure 72,358, about 9,000 each, so this row's original ~72,000 estimate for twenty was the cost of eight, and the two figures are not interchangeable. **Control arm only, no skill arm**: the question is not *does `fit.md` help* but *is there anything here for it to help with*. 20 × 3 × 2 repeats = **120 generation calls**; 3 judges × 120 responses = **360 blind extraction calls** (`ADJUDICATORS = 3` in `scripts/adjudicate.py`); 2 planted triplets × 3 hand-written responses × 3 judges = **18 falsifier calls**. Two repeats, not five, derived from Track I's ICC 0.83 to 0.85 exactly as N6, N7 and N9 derived it rather than chosen here. Primary: Youden's J, which is identically the programme's `d` (see below), over **40 sensitivity and 40 specificity events, clustered on the 20 triplets and never pooled over the 60 files**, by `stats.cluster.cluster_bootstrap_diff` with the triplet id as the cluster label. Pre-registered kill: **unaided J ≥ 0.70 closes the venue**, the value reached at sensitivity 0.85 and specificity 0.85, and 0.85 is `ADMISSIBILITY_CEILING` in `scripts/probe_casefile.py`. Prediction registered before authoring: [`notebook/2026-08-19-prediction-track-h-phase-0.md`](../../notebook/2026-08-19-prediction-track-h-phase-0.md). | 498 calls | **corpus authoring blocked; see below** |

#### H1: Phase 0, and the deviation it commits

**Authoring status, 2026-08-19: two passes run, two usable triplets against the
twenty this row costs.** The 498-call figure above and every number feeding it
assume twenty triplets exist. They do not, and the observed yield is the reason
this row now says *blocked* rather than *not started*.

| pass | authored | clean | blocked | cut |
|---|---|---|---|---|
| one | 3 | 0 | 0 | 3 |
| two | 5 | 1 (`t03`) | 1 (`t04`) | 3 (`t01`, `t02`, `t05`) |

Pass one failed both of its checks: two of three matched facts governed, and a
single register feature separated all six inserts
([entry](../../notebook/2026-08-19-the-h1-form-failed-and-the-two-dials-are-one-dial.md)).
Pass two changed the neutralisation from *margin* to *categorical* and removed
both failure modes completely, but the failure moved rather than disappearing:
one triplet over-neutralised into triviality and two bought their difficulty by
making the **governing** fact ambiguous
([entry](../../notebook/2026-08-19-h1-pass-two-five-authored-one-clean.md)).

**The registered kill did not fire and Track H survives**, since the kill closes
the track only if passes two *and* three fail. That is a weaker statement than it
sounds, and two things must be read with it. The corpus **cannot be merged**: a
causal-rule-overlap feature reaches pooled AUC 0.740, and 0.800 with proper nouns
dropped, against `SEPARABILITY_BAND` of [0.40, 0.60]. And that feature is **not**
in `tailoring.FEATURES`, so the battery does not currently compute it: it was
found by two readers, not by the gate.

**What this does to the cost line.** At one clean triplet per five authored in
pass two, or two usable of eight across both passes, which is the figure
`docs/STATUS.md` carries and the one to quote for a whole-corpus estimate,
twenty triplets is on the order of a hundred authored: some 700,000 characters
of authored prose before a single generation call. That is the same authoring
bill that closed Track G, arriving at a different track by a different route,
and it is the open question about this venue rather than a detail of it. Nothing here has costed a
smaller H1: whether the primary is estimable at ten triplets, or five, is a power
question nobody has asked, and asking it is cheaper than authoring ninety more.

**τ has a registered rule and no derived number, and those are different.** The
threshold is defined below as the maximum relative difference between two repeats
of the same **base** prompt, which carry no perturbation: a noise floor,
computed before any contrast is examined. It cannot be derived without the run's
own base arm, so it does not exist yet, which is why `t04` is *blocked* rather
than cut: its relative movement is 0.333, and any τ above 1/3 would make its
governing arm a structural false negative. A τ that high would also mean some
base swung more than a third between identical repeats, which would be its own
finding, so the block is standing rule 1 being obeyed, not a coin flip.

**The deviation, named as one.** This section says Track H is *"Not a separate
venue, but a task family that runs inside C, D, E and F"*. C, D, E and F have not
started. H1 promotes Track H to a standalone Phase-0 venue and runs it **before**
them. That is a change to the programme and it is recorded here rather than
absorbed: what it gives up is the two questions the sub-agent setting adds (does
the personal context survive a handoff, and does a summariser destroy tailoring),
neither of which H1 can ask and both of which stay with C through F. What it
buys is that the founding construct stops being gated behind four unstarted
tracks. The section already refers to *"the single-call venue"* as a thing Track H
can inhabit, so the deviation is narrower than promotion usually is; it is still
a deviation.

**Why it goes first, and the argument is structural.** Four of the five *closed*
venues in `docs/STATUS.md`'s *Venues built* table (seven rows now, the other two
being the working trigger instrument and Track H's own blocked `tailoring`
corpus) closed on a verifier-backed **accuracy**: relevance labels, trap-taking,
arithmetic, admissibility, with the unaided model at 0.917 to 0.971 on every
one. Track H's primary is not an accuracy. It is a difference of two rates
inside a matched triplet, so competence at reading the item raises `P(change | governing)` and
says nothing about `P(change | matched non-governing)`. The mechanism that closed
the other four therefore cannot ceiling this one by construction. It can still
ceiling it by a *different* mechanism, and the registered prediction names the
one to worry about: noticing that the matched fact is *not* governing may be the
same reading act performed twice.

**An identity worth stating, because it removes an apparent second estimator.**
This section reports `d = P(change | governing) − P(change | matched
non-governing)` *and* Youden's J. They are the same number:
`J = sens + spec − 1 = P(change | gov) + (1 − P(change | matched)) − 1 =
P(change | gov) − P(change | matched) = d`. So there is one primary with a
two-part decomposition, and, usefully, `d` is a **paired mean difference of two
indicator vectors**, which is exactly the shape
`stats.cluster.cluster_bootstrap_diff` takes
(`evals/src/decision_evals/stats/cluster.py`, line 139).

**The denominator is the load-bearing half, and getting it wrong is a defect this
repository has already recorded.** Each `(triplet, repeat)` pair contributes one
sensitivity event and one specificity event: 40 of each, over 20 triplets. The
rate denominator is 40; the **inference denominator is 20 clusters**, and the
cluster is the **triplet, not the file**. Defect nine on `docs/STATUS.md`'s
broken-measurement list is *"pooled AUC used on a matched corpus"*, where a
pooled statistic ranks positives against negatives drawn from *other* triples and
is structurally blind to the rank held inside one. Track H is a matched design of
precisely that shape. Pooling its 60 files would repeat, in the venue built to
escape the other five, the defect those five already paid for.

**A parameter the existing spec does not supply, and standing rule 1 forbids
inventing.** This section states the primary as an elicited quantity *"not a
flip"* and states the metric as a difference of two **probabilities of change**.
Both are right and together they leave a hole: binarising a continuous quantity
into `change` / `no change` needs a threshold, and no number for one exists
anywhere in this repository. H1 registers the *rule* and derives the *number*
from the run's own base arm: movement is relative, `|q_variant − q_base| /
|q_base|`, and the threshold is the maximum of the 20 base repeat-0 vs repeat-1
relative differences, which carry no perturbation at all. That threshold is
computed before any governing or matched contrast is examined. The prediction
entry records that this rule is a choice and states which way it biases the
result: conservatively, toward under-reporting movement, which pushes J down and
so runs *against* the kill.

**That last sentence is half the story, and the missing half is a defect no
corpus size fixes.** τ is a *maximum* over the n base pairs, so it grows with the
corpus, and with it the estimand. Reconstructed on 2026-08-19, true J runs
**0.843 → 0.915 → 0.956 → 0.977** as n goes 5 → 10 → 20 → 40 at one
parameterisation. So the direction the prediction names is right and its size is
not fixed: **the bias changes with n**, no two corpus sizes measure the same
venue, and the drift runs *toward* the kill. Adding triplets makes this worse.

A second consequence of the same rule: τ is one draw shared by every triplet, so
the clusters are not independent. Measured across-cluster correlation of
indicators from different triplets is 0.07–0.10, which `cluster_bootstrap_diff`
resamples i.i.d. and cannot see; realised SD runs ×1.23 to ×2.31 the closed form
and coverage does **not** improve with n.

**Settle τ before authoring further.** A quantile, or a pooled noise estimate,
rather than a max over n would remove the drift. This was found in
source before H1 ran, and that every figure behind it rests on a reconstruction
rather than a measurement: **no quantity has ever been elicited in this
harness**. Full account:
[`notebook/2026-08-19-h1-does-not-need-twenty-and-tau-drifts-with-n.md`](../../notebook/2026-08-19-h1-does-not-need-twenty-and-tau-drifts-with-n.md).

**And twenty triplets is not load-bearing.** Simulating the registered *point*
rule (`Phase0Result.kill` is `j >= 0.70`, not an interval) over 174 cells:

| | n=5 | n=10 | n=15 | n=20 |
|---|---|---|---|---|
| P(false kill) at true J = 0.50 | 0.23 | 0.10 | 0.04 | 0.02 |
| P(kill) at true J = 0.85 | 0.94 | 0.97 | 0.99 | 0.99 |

Both rows are the symmetric, ICC = 0, rho = 0 cells of the grid, which the table
did not say. Heterogeneity moves them: the smallest usable n at J = 0.30 runs
12, 12, 15, 20, 20 across ICC 0, 0.05, 0.20, 0.50, 0.83.

**Ten is defensible and fifteen comfortable**; ten to twenty buys about eight
points of false-kill protection for fifty more authored triplets, which at the
observed yield is some 450,000 characters at the measured ~9,000 characters a
triplet. Pick n as a multiple of five and not for tidiness: bootstrap replicate
means live on the `k/(2n)` lattice and 0.70 is an atom at 5, 10, 15 and 20 but
not at 8 or 12. **That penalty is one cell, not a rule.** At true J = 0.85 going
from five triplets to eight makes the indeterminate rate 26 points worse; at
true J = 0.30 it makes it about 36 points *better*, and n=8 beats both 5 and 10
there. The lattice argument is a reason to prefer a representable threshold, not
a monotone cost in n.

An interval reading of the same grid says no n between 5 and 20 works at all,
which is a different question from the one H1 registered, and it is the reading
the first version of this analysis scored by mistake. Both are reported because
the gap between them is the finding: if H1 ever wants to *state* headroom rather
than observe a point estimate under the kill, twenty triplets does not deliver
it and neither would forty.

**Both non-negotiables hold, and Phase 0 is where they would be cut.** The
matched non-governing arm is a third of the generation bill and it is the arm
where nothing is supposed to happen, which is what makes it look free to drop
when a grid is too large. It is not free: without it J is a flip-rate and a model
that flips on everything scores 1.0, silently and with a number that still
computes. The elicited-quantity primary stays for the reason this section already
gives: flip-rate scores conditional advice, the best available answer, as
failure. Neither is cut in H1 and neither may be cut to size a later grid.

**What must pass before any J exists.** Standing rule 2: two planted triplets
with hand-written responses, one that obviously must move and one that obviously
must not, scored by the same three extractors. The battery must return
sensitivity 1.0 and specificity 1.0. **If it does not, the extractor is the
finding and no J is reported**: not a caveat on a number, no number. The raw
per-arm movement counts will be printed beside J in every case, because
`docs/STATUS.md` records five separate inert-estimator instances and a plausible
zero does not announce itself.

**What H1 does not settle.** A pass, J < 0.70, authorises the skill arm and
nothing else. It licenses no claim that any skill works; every skill here carries
`UNTESTED`. The *n* for any confirmatory grid is deliberately not chosen in this
row: it is an MDE, `stats/power.py`'s `minimum_detectable_effect` **will** be run
against Phase 0's observed J and its within-triplet variance, and N6's triple ICC
of 0.00–0.06 may not be reused as a planning figure any more than the 0.315 it
displaced.

### Track I: reliability as a first-class outcome

Cross-cutting, and a direct consequence of the multi-turn result: the
degradation is increased unreliability rather than lost aptitude. A mean-only
metric will under-detect it, and binary admissibility is already nearly a
constant in our data.

How lopsided, now that the numbers have been read first-hand.
Aptitude falls 16% and the source calls that non-significant; unreliability
rises 112%. Roughly seven-eighths of the headline −39% lives in the spread.
Every measurement this repository has taken is a mean, so a mean-only design was
pointed at the smaller and less significant component. That does not explain the
three nulls on its own, since the corpora were also short, single-turn and
underpowered, but it is the first account that predicts *which* number comes
back flat.

| # | Work | Status |
|---|---|---|
| I1 | `stats/reliability.py`: the §4.2 estimators (`aptitude_unreliability`), a per-item extension whose `scatter` array feeds a paired test directly (`per_item_reliability`), and the two repeat-count questions (`repeats_for_reliability`, `repeats_for_scatter_precision`). 100% line+branch, 7 property tests. | done |
| I2 | Every experiment reports scatter alongside its mean. ~~Nothing calls the module yet; I1 is a tool, not a result.~~ Half true, corrected 2026-08-13. `per_item_reliability` and `repeats_for_reliability` are called by `run_triggers.report_stability` and have already produced published numbers and a design change: ICC 0.833 (M5) and 0.852 (M6), and the resulting "future trigger arms run 2 repeats, not 5". `aptitude_unreliability`, the §4.2 estimator, the one the multi-turn finding actually lives in, still has no caller, and cannot have one until a venue produces per-item score distributions under two conditions. That is Track A, not a wiring job. | partly done |
| I3 | Power re-derived for a reliability outcome. | see below |
| I4 | A skill that reduces variance without moving the mean is a result, not a null. Pre-register it as a primary-eligible outcome so it cannot be discovered post hoc. | pending |

I3, stated sharply enough to act on. The long-context plan argues repeats are
near-worthless because between-item variance dominates within-item sampling
variance. That is right for a mean and wrong for a spread: at one repeat the
within-item scatter is not imprecise, it is *undefined*, and
`per_item_reliability` refuses `n_repeats=1` rather than returning a silent
zero. The two questions have different answers. At ICC 0.6 a mean outcome
reaches reliability 0.8 in 2 repeats, while estimating a per-item spread to a
relative standard error of 0.25 takes 9. A 4.5× difference in run count follows
from the choice of outcome alone, so it has to be settled before a grid is
sized.
