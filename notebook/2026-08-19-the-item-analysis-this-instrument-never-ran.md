# The item analysis this instrument never ran

2026-08-19.

Every number this repository has published about the trigger corpus is an
**arm** statistic: firing accuracy, recall, FPR, routing accuracy, each averaged
over 258 items. Not one is an **item** statistic. `RoutingGroup.per_item` is
computed and never printed. No point-biserial, no item-total correlation, no
difficulty register, and the only difficulty band in the codebase lives in
`prereg.py`, which is the declared-unwired module.

That gap has a cost with a number on it. BenchBench (arXiv:2603.20807) reports
Pearson **r ≈ 0.62** between item invalidity and item discrimination, negative
in direction — the abstract prints the magnitude and gives the sign in words,
so the minus is not a character in the source and is not written as one here. A
bad item does not add noise; it systematically flattens the measurement. ABA
(arXiv:2605.26079) audited 168 benchmarks and found **>25.7% of tasks critically
flawed**, and filtering those tasks out *raised* average performance on
SWE-bench Verified and Terminal-Bench 2 by 9.9% and 9.6%. And Anthropic's
own eval guidance names the cheapest screen there is — *a 0% pass rate across
many trials is most often a signal of a broken task, not an incapable agent* —
which this instrument has never run despite having the records to run it on.

This entry registers the estimators **before** they are computed. Nothing here
needs a model call; every number comes from records already on disk, which is
exactly why the pre-registration matters. A re-analysis of existing data is the
easiest place in this repository to fit an estimator to a result and not notice.

---

## What is computed, from which records, over which denominator, by which function

**Records.** `results/triggers/verdicts-{full,no-exclusions,no-opener,opener-only,stakes-named,stakes-shown}-decision-making-v4.jsonl`
— six description arms, 516 rows each, 258 items × 2 repeats, `set_version: 4`,
`model: haiku`.

**`verdicts-in-situ-decision-making-v4.jsonl` is excluded and this is a
decision, not an oversight.** That arm is the void N9 run: 70 of 516 responses
were unparseable, none containing a `"fire"` key, and its parse rate splits by
domain (`technical`/`money`/`career` 0.9135 against `relationships`/`health`
0.7892, Fisher p = 0.00011). Including it would put a domain-correlated missing-
data mechanism inside an item statistic, which is the one place it would do the
most damage. Twelve respondents become fourteen and the difficulty estimate for
every `relationships` and `health` item moves for a reason that has nothing to
do with the item.

**Respondent.** One `(arm, repeat)` pair. **n = 12.** This is the denominator
that limits everything below and it is small. Classical item analysis assumes
hundreds of respondents; twelve gives intervals wide enough that only large
effects will clear them. **Every statistic here is registered as descriptive.
None of it licenses a claim about any arm, and no band below is a kill.**

**Correctness.** A row is correct when `fired == should_fire`. Routing is not
scored here: `council` and `hinge` are offered to the model and are correct for
zero of 86 positives, so any routing statistic on this corpus is a six-way
choice against a four-way key and must not be folded into an item score.

Four estimators, each with its denominator stated:

1. **Item difficulty** `p_i` — correct rows for item *i* over rows for item *i*.
   Denominator 12 per item. Reported separately for positives and negatives,
   because a positive's difficulty is a miss rate and a negative's is a
   false-fire rate and averaging them means nothing.
2. **Item discrimination** `r_pb(i)` — point-biserial between item *i*'s
   correctness and the respondent's total score over the other 257 items.
   **Corrected item-total, not raw**: with 258 items the inflation is small, but
   the correction is free and its absence is the standard defect.
   Denominator 12 respondents.
3. **Broken-item screen** — items at `p_i == 0.0` across all 12 respondents.
   Anthropic's rule. Reported with the complementary set (`p_i == 1.0`), which
   is not a defect signal but is the ceiling term.
4. **Per-triple joint outcome** `J_t` — for triple *t*, the fraction of the 12
   respondents that got **all three** of its items right in that respondent's
   repeat. This is AgentAbstain's paired accuracy (arXiv:2607.10059) generalised
   from a pair to a triple, and it is the statistic the matched-triple design
   was built for and has never produced. Denominator 12 per triple, 86 triples.

Implementation goes in `evals/src/decision_evals/trigger_arms.py` beside the
existing `RoutingGroup.per_item`, and is called from `run_triggers.py`'s report
path so it cannot become the fifth tested-and-unreachable estimator here.

---

## Predictions

Written before computing. Two facts are **already observed** and are therefore
not predictions — they came out of the audit that motivated this entry, and
listing them as successes afterwards would be exactly the story-telling the
notebook exists to prevent:

- `m11p` fires in no repeat of the N6 `full` arm.
- Six negatives (`l01n1`, `l12n1`, `l14n2`, `l19n1`, `l20n1`, `xl17n2`) fire in
  every repeat of that arm.

Both were measured on **one** arm. Whether they hold across all six is open, and
that is prediction 1.

**P1 — the broken-item set is small and mostly negatives.** Across all 12
respondents, at most **4** positives sit at `p_i == 0.0`, and at least **8**
negatives do. Rationale: the over-calling result (arXiv:2605.18882) finds call
accuracy high and no-call accuracy much lower across six models in three
families, so a systematically failed item here should be a negative that always
fires rather than a positive that never does.

**P2 — median discrimination is positive but weak.** Median `r_pb` over the 258
items falls in **[0.05, 0.35]**. Rationale: with six description variants of one
skill measured at one model tier, between-respondent ability variance is small,
and discrimination cannot exceed what the spread allows. A median above 0.35
would mean the arms differ far more than N7 found (the top three arms are
indistinguishable at n=258, p=0.86 and p=0.35) and I would not believe it
without checking the estimator first.

**P3 — between 6 and 30 items have negative discrimination.** These are items
the *worse* arms get right and the better arms get wrong — Benchmark²'s
capability-alignment-deviation signal (arXiv:2601.03986) and the closest thing
this corpus has to a mislabelled-item detector. Zero would be surprising and
would suggest the estimator is not sensitive at n=12.

**P4 — joint triple accuracy lands in [0.55, 0.75], and above the independence
product.** N6's `full` arm reports firing accuracy 0.8566 at repeat 0. Under
independent errors a triple would clear at 0.8566³ ≈ 0.629. The triples share a
body, and `trigger_arms.py`'s own clustered bootstrap exists because they share
difficulty, so the joint rate should sit **above** 0.629. If it lands below,
either the negatives inside a triple are failing in an anti-correlated way — the
shared body making one negative easier exactly when the other is harder — or the
estimator is wrong. I expect above, and the interesting number is the margin.

**P5 — the XL band has the lowest joint accuracy.** Three chances to fail on a
1,200-word body, and N6 found the long bands hardest.

### Where I expect to be wrong

P2's interval is the one I would bet against myself on. Point-biserial at n=12
is noisy enough that the median could land anywhere in [0.0, 0.5] on
resampling, and I have not computed what its own sampling interval is. If the
observed median falls just outside [0.05, 0.35] that is weak evidence about the
corpus and strong evidence that the band was too tight for the denominator —
which is the fifth pre-registration defect of the shape this repository keeps
recording. The band stays as written, and if it misses on width rather than
direction, the entry that reports it will say so.

P3 is a count over a quantity with no interval attached, which is the weaker
half of the same problem.

---

## What this does not do

It does not audit whether an item is *sound* — only whether it discriminates.
An item every arm gets right may be trivially easy or may be a shortcut nobody
has found; the shortcut battery answers the second and nothing answers the
first. ABA-style item auditing is a separate pass and is not this one.

It does not touch labels. Discrimination is a signal that an item might be
mislabelled, never a licence to move a label — that is Track N3's blind
adjudication, and the answer key stays at v4 through all of this. Nothing
computed here may change a `should_fire` field without a `docs/DECISIONS.md`
entry and a fresh adjudication.

---

## Appended 2026-08-19 — the scoring, and what an adversarial re-derivation found

**Appended, not edited.** Every prediction above stands as it was written,
including the two this section falsifies and the one it shows could not have
been scored at all. Rewriting a band after seeing the data is the single thing
this directory exists to prevent, and a prediction improved after the fact is
worth less than a wrong one left standing.

### Scores

| | registered | observed | |
|---|---|---|---|
| P1 | ≤4 positives and ≥8 negatives at `p == 0` | 0 positives, **1** negative | **falsified** |
| P2 | median `r_pb` in [0.05, 0.35] | 0.5153 over 73, 0.0000 over 258 | **unscoreable** |
| P3 | 6–30 items with negative discrimination | 15 | met, weakly |
| P4 | joint in [0.55, 0.75], above independence | 0.7568, above a baseline that was wrong | **falsified** |
| P5 | XL has the lowest joint accuracy | `l` 0.5238 is lowest; `xl` 0.6176 | **falsified** |

Headline figures, for the record: mean difficulty 0.9913 over positives and
0.8614 over negatives; median `r_pb` 0.5153 over the 73 items where it is
defined; floor 0 positives and 1 negative (`l19n1`); ceiling 81 positives and
103 negatives; mean joint 0.7568 over 86 triples; 15 items discriminating
negatively. Both "already observed" facts held across all six arms.

### P4's anchor is factually wrong, and the error is instructive

The entry states that N6's `full` arm reports firing accuracy 0.8566 at repeat
0. **It does not.** N6 `full` at repeat 0 is 244/258 = **0.9457**. 0.8566 is the
*parse rate* at repeat 0 of the **N9 in-situ arm** — the void run this same
entry excludes by name, three sections above the prediction that anchors on it
(`results/decision-making/2026-08-19-505b236-n9-in-situ-void/README.md:20`).

So the independence baseline should have been about **0.74**, not 0.629: pooled
accuracy cubed is 0.7405, and the composition-aware product for one positive and
two negatives, `p_pos · p_neg²`, is 0.7356. Against the observed 0.7568 the real
margin over independence is **+0.008 to +0.021**, not the +0.128 the registered
anchor implies. P4 is falsified on its band — 0.7568 sits above the 0.75 ceiling
— and its direction claim survives only weakly: the triples do clear
independence, by about a fiftieth of what a reader of the prediction would
expect.

P4 also **failed to name its estimator**, which the standing rule requires. Mean
over 86 triples and pooled over all 1,032 respondent-triple cells both give
0.7568 here, and they agree only because every denominator is exactly 12. The
median over triples is **0.8750**. Three defensible readings, two numbers, one
of which would have been reported as the result.

### P2 was unreachable, not merely ambiguous

P2 registered the median `r_pb` "over the 258 items". `r_pb` is undefined for
the 185 constant items, so the real denominator is **73**. The two readings of
that one sentence straddle the band rather than sitting near each other: 0.5153
over the 73 defined, and exactly 0.0000 over 258 if the undefined items are
counted as zero. One reading falsifies the band from above; the other lands
inside it on an artefact of counting non-measurements.

Worse, the band could not have been hit. A margin-preserving null — curveball
swaps holding both the respondent totals and the item difficulties fixed, so
only the *pattern* of who got what right is destroyed — gives a null median
`r_pb` of **0.4450, 95% [0.4048, 0.5068]** over 300 draws at 5,000 swaps, with
`n_defined` = 73, matching the observed denominator exactly. That null sits
**above** P2's ceiling of 0.35. Given these margins, no arrangement of the data
consistent with them would have produced a median inside the registered band.

The observed 0.5153 clears the null's upper tail outright: 0 of 300 draws
reached it. A lower-precision run at 120 draws and 1,500 swaps agreed at 0.4463
and gave the more conservative p = 0.0083, so better mixing tightened the tail
rather than moving the conclusion. A bootstrap over the 12 respondents puts the
observed median in **[0.3893, 0.6969]** — an interval as wide as the band it is
being compared against, which is the noise the "where I expect to be wrong"
section predicted and underestimated.

This is the **sixth** pre-registration defect of the family this repository
keeps recording, and the first where the band could not have been hit at all.
The earlier five were bands set too tight, scored on the wrong denominator, or
written after the run. This one was arithmetically unreachable from the corpus's
own margins before a single number was computed.

P3 has the mirror-image problem and it is worth naming even though P3 was met:
**99.8% of bootstrap draws satisfy [6, 30]**, so the band is close to
unfalsifiable and "met" is barely evidence of anything.

P1's failure is a denominator error of the same family. The "at least 8
negatives" threshold came from an observation on **two** respondents and was
scored on **twelve**, where `p == 0` for a negative means firing in all twelve
rather than in both of two. One item survives that: `l19n1`.

### The arithmetic is sound

An independent scorer that imports nothing from `decision_evals` reproduced all
258 difficulties, all 258 discriminations including which are `None`, and all 86
joint outcomes, with **zero disagreements at 1e-12**. Every criticism above is
about what was registered and what is wired, not about what the estimators
compute.

That confirmation also caught one of its own: a `print` in the reviewer's scratch
script still carried a verdict label written against an earlier, weaker null — a
within-respondent shuffle that leaves item margins free, which lands at 0.272 and
does fall inside the band. The null was strengthened and the label was not
updated with it. The number governs, not the label, and the label is void.

### A live wiring defect, open

`run_triggers.py`'s wired caller passes **one arm**, which is n=2 respondents.
At n=2 every defined point-biserial is forced to ±1 by construction, and the
report prints `median_discrimination = 1.0` with no caveat; `format_item_analysis`
warns only at n < 2. That is this repository's plausible-zero failure mode
inverted into a **plausible one** — a number that looks like a strong result,
arrives through a clean run, and is an artefact of the denominator.

The registered 12-respondent analysis has **no wired entry point**. It is
reachable from the test suite and from an explicit call, and not from anything a
run does. Stated here as open rather than fixed.

---

## Appended 2026-08-19 (second) — what an adversarial review of the section above found

**A correction to a correction, appended for the reason the first one was
appended.** The section above was written by the same author as the
pre-registration it scores, and an independent reviewer was then briefed to
break it rather than approve it. It found twelve defects, and re-derived every
one from the records before reporting it. Editing them into the section above
would leave a clean-looking correction and destroy the thing this directory
exists for — so they are recorded here, in order of how much they matter, with
the two that run **in the author's favour** first.

Every number below was re-derived a second time for this section, by a scorer
that reads the six checkpoint files directly and imports nothing from
`decision_evals`.

### C1 — "held across all six arms" is false, and it flatters the audit

The section above ends its headline paragraph with: *"Both 'already observed'
facts held across all six arms."* **They did not.** They hold in the N6 `full`
arm exactly as the pre-registration stated them, and **neither survives the
six-arm grid**:

| already-observed fact | in N6 `full` | over all 12 respondents |
|---|---|---|
| `m11p` fires in no repeat | true | fires in **8 of 12** |
| six named negatives fire in every repeat | true | only `l19n1` does |

The other five: `l12n1` 11/12, `l20n1` 11/12, `l01n1` 8/12, `l14n2` 8/12,
`xl17n2` 6/12.

This is the worst defect in the section because of the direction it points. The
audit that motivated this whole entry was run on one arm; "held across all six
arms" is the sentence that promotes it to a property of the corpus, and it is
the one sentence in the section that was not checked.

It is also **self-contradicting**, which is what makes it cheap to have caught.
A positive that fires in no repeat sits at `p == 0`, and the floor row four
lines above says **0 positives** are there. A negative that fires in every
repeat also sits at `p == 0`, and the same row says **1 negative** is there, not
six. The P1 paragraph twelve lines below then says the same thing again — *"One
item survives that: `l19n1`"*. Three statements in one section, two of them
right.

**Read the first prediction as it was written and the record is fine**: the
pre-registration said both facts *"were measured on one arm. Whether they hold
across all six is open, and that is prediction 1."* The answer is that they do
not.

### C2 — P2 is falsified, not unscoreable

The score table grades P2 **unscoreable**, and the argument for that grade is
that the two readings of its denominator disagree: *"One reading falsifies the
band from above; the other lands inside it on an artefact of counting
non-measurements."*

The second half is arithmetic and it is wrong. P2's band is **[0.05, 0.35]**.
The two readings are 0.5153 and 0.0000. **0.0000 is not inside [0.05, 0.35]** —
it is below the floor by 0.05, the same way 0.5153 is above the ceiling by
0.165. Both readings falsify. The ambiguity decides *which side* P2 fails on and
decides nothing else.

So the score is **falsified under either reading**, and the "unscoreable" verdict
rested entirely on the sentence that is wrong. What survives, and is strengthened
rather than weakened: the denominator really was ambiguous, and the band really
was unreachable — the margin-preserving null sits above the ceiling and zero sits
below the floor, so no reading of that sentence could have landed inside.

The commit message for `97d9c5e` got this right and the file did not. It says
the readings *"straddle"* the band, which is the correct geometry. Two
descriptions of one pair of numbers were written the same afternoon and only one
of them is true; the one a reader of `notebook/` reaches is the false one, which
is why it is corrected here rather than left to the log.

### C3 — the margin over independence is +0.016 to +0.021

The section states *"the real margin over independence is **+0.008 to +0.021**"*.
The lower end is not a number anything here produces. Re-derived twice:

| | value | margin against observed 0.756783 |
|---|---|---|
| observed mean joint, 86 triples | 0.756783 | — |
| pooled accuracy cubed (0.904716³) | 0.740519 | **+0.016263** |
| composition-aware `p_pos · p_neg²` (0.991279 · 0.861434²) | 0.735597 | **+0.021186** |

The range is **+0.016 to +0.021**. Nothing named in that paragraph, and nothing
in the records, yields +0.008.

### C4 — "about a fiftieth" is about a seventh

The same paragraph closes: *"the triples do clear independence, by about a
fiftieth of what a reader of the prediction would expect."* The registered anchor
0.8566³ = 0.628542 implies a margin of **0.128241**. Against the real margins
that is a ratio of **6.05** and **7.89** — between a sixth and an eighth. Write
**about a seventh**.

A fiftieth would be a margin near 0.0026. The error overstates the shrinkage by
roughly sevenfold, in the direction that makes the correction sound more
dramatic than it is — which is the second of the two defects here that run the
author's way.

### C5 — the Records section names six files that have never existed

The pre-registration's *"What is computed, from which records"* section opens by
naming
`results/triggers/verdicts-{full,no-exclusions,no-opener,opener-only,stakes-named,stakes-shown}-decision-making-v4.jsonl`,
and excludes `verdicts-in-situ-decision-making-v4.jsonl` by name. **No file with
that name, and no file matching that naming pattern, has ever existed in this
repository.** `scripts/run_triggers.py:1048` writes `verdicts-<description>.jsonl`,
and no verdict file has ever been written under `results/triggers/` at all. The
seven real files are:

- `results/decision-making/2026-08-18-e632659-n6-confirmatory/verdicts-full.jsonl`
- the same directory's `verdicts-opener-only.jsonl`
- the same directory's `verdicts-stakes-shown.jsonl`
- `results/decision-making/2026-08-19-d52236a-n7-remaining-arms/verdicts-no-exclusions.jsonl`
- the same directory's `verdicts-no-opener.jsonl`
- the same directory's `verdicts-stakes-named.jsonl`
- `results/decision-making/2026-08-19-505b236-n9-in-situ-void/verdicts-in-situ.jsonl`

The first six are the analysis set; the seventh is the excluded one, and the
exclusion stands on its stated reason.

This one matters more than a typo because of what it is a section of. The
standing rule that this entry was written to satisfy demands *"what will be
computed, **from which records**, over which denominator, by which function"* —
and the records half was the half that pointed at nothing. Every number in the
entry is reproducible; the sentence telling a reader where to reproduce it from
was not.

The same wrong directory reached two other places on the same day.
`docs/DECISIONS.md` carried it and is **corrected in place** (it is not
append-only). `s13p`'s `why` in `datasets/triggers/decision-making/s.yaml`
carries it too, and that is a governed answer-key path needing its own commit
and its own register entry, so it is **outstanding**.

### C6 — a number-bearing citation with no quote behind it

P1's rationale cites arXiv:2605.18882 for *"call accuracy high and no-call
accuracy much lower across six models in three families"*. `shi2026overcalling`
in `paper/refs.bib` carried **no `quote` field**, so nothing in this repository
could check that sentence, and the citation gate passed it: `_CLAIM_NUMBER`
fires on digits beside a percent sign or `pp`, and "six" and "three" are spelled
as words.

**Checked against the abstract, and it holds.** The source says: *"On the
When2Call benchmark, six models from three families show high call accuracy but
much lower no-call accuracy, leaving overall accuracy in the 55%-70% range."*
That is now the `quote` field. Two limits travel with it and did not travel with
the citation: the asymmetry is measured on When2Call rather than on anything
resembling this corpus, and the paper's own subject is the mechanistic account —
sparse-autoencoder features for the call/no-call decision, an activation-margin
offset, and steering that cancels it — not the descriptive gap borrowed here.

### C7 — an italicised verbatim quotation with no source, and two unmarked cuts

The opening section italicises *"a 0% pass rate across many trials is most often
a signal of a broken task, not an incapable agent"* and attributes it to
Anthropic's eval guidance with no URL and no locator. It is load-bearing:
estimator 3, the broken-item screen, is justified by it and by nothing else.

The source is
<https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents>, and the
sentence there reads:

> With frontier models, a 0% pass rate across many trials (i.e. 0% pass@100) is
> most often a signal of a broken task, not an incapable agent, and a sign to
> double-check your task specification and graders.

So the italicised text is a substring, with **two unmarked cuts**, and the first
of them is a scope qualifier. *"With frontier models"* was dropped from a quote
used to license a screen run at the haiku tier. The parenthetical *"(i.e. 0%
pass@100)"* was dropped from the middle without an elision marker. Neither cut
changes the conclusion the estimator draws, and dropping a scope qualifier from
inside quotation marks is the kind of thing that eventually does.

### C8 — 300 draws do not license "no arrangement of the data"

The section writes: *"Given these margins, no arrangement of the data consistent
with them would have produced a median inside the registered band."* That is a
universal quantifier over a space the run sampled 300 points of. What was
actually shown, and it is enough:

> Not one of 300 margin-preserving draws produced a median `r_pb` inside
> [0.05, 0.35], and the null's 95% interval [0.4048, 0.5068] sits entirely above
> the band's ceiling of 0.35.

That supports "the band was unreachable" as an inference. It is not a proof, and
the sentence as written claims one.

### C9 — `n_defined` = 73 is forced by construction, not a check that passed

The null paragraph reports the null *"with `n_defined` = 73, matching the
observed denominator exactly"*, in a position where it reads as the null
validating itself against the data. It cannot fail. A curveball swap preserves
both margins, so an item every respondent scored the same on stays constant
under every draw, and the count of items where `r_pb` is defined is therefore
identical in the null and in the observation by construction. It is a useful
implementation assertion and it is zero evidence about the corpus.

### C10 — on this branch the registration commit follows the implementation

The seventh pre-registration defect of the family this repository keeps
recording, and the first that is about `git` rather than about a band.

The entry above says it registers the estimators *"**before** they are
computed"*. On this branch that is not visible: `81590cd` (13:46:38) adds
`trigger_arms.py`'s estimators, `run_triggers.py`'s caller and both test files,
and the pre-registration first appears **four minutes later** at `8cdeebd`
(13:50:37). A reader checking the claim against this history finds the code
first.

**The claim is nevertheless true, and here is the check that shows it.** Both
were written together in `f86269a` (13:15:15), thirty-one minutes before the
code landed here — but `f86269a` is **not an ancestor of HEAD**, so it is not
reachable from this branch and a reader cannot see it. The reviewer diffed the
two copies of the entry, `f86269a` against `8cdeebd`. **Only the three citation
corrections differ**: BenchBench's `r ≈ −0.62` losing its minus sign, ABA's
"removing them moved SWE-bench Verified by ~9.9%" becoming the correct
"filtering those tasks out raised average performance ... by 9.9% and 9.6%", and
AgentAbstain's "Paired Accuracy" lower-cased. **No band, no prediction, no
denominator and no estimator moved between them.**

The defect is that nothing on this branch proves that without a reviewer doing
it by hand. A pre-registration whose evidence is an unreachable commit is a
pre-registration on trust.

### C11 — four bibliography titles were guessed, and only the missing authors were disclosed

The four entries recorded for this notebook entry carried a banner disclosing
that their author lines were not captured. They also carried **short names in
the `title` field**, which was not disclosed and read as though the titles had
been recorded. `aba2026` contradicted itself outright: `title = {Automated
Benchmark Auditing}` beside a `note` saying ABA abbreviates *Auto Benchmark
Audit*, so the two fields disagreed and neither held the real title.

Fetched from the abstract pages and corrected, with author lists:

| key | recorded | actual |
|---|---|---|
| `benchbench2026` | BenchBench | BenchBench: Benchmarking Automated Benchmark Generation |
| `aba2026` | Automated Benchmark Auditing | Automated Benchmark Auditing for AI Agents and Large Language Models |
| `agentabstain2026` | AgentAbstain | AgentAbstain: Do LLM Agents Know When Not to Act? |
| `benchmarksquared2026` | Benchmark² | Benchmark²: Systematic Evaluation of LLM Benchmarks |

An omission disclosed in a banner is a known gap. A guess in the same field a
recorded value would occupy is not, and that is the difference this correction
is about.

### C12 — the wiring paragraph used the wrong tense on a path that had never run

*"the report prints `median_discrimination = 1.0` with no caveat"* — present
indicative, for a code path no published run had ever executed.
`report_item_analysis` was written the same afternoon. The standing rule is that
prose describing a mechanism names the tense it runs in: **would have printed**,
not *prints*.

The underlying defect was real and **the fix has landed**, at `080503e`, from
the unit working on the code while this section was being written.
`item_discrimination` now refuses a denominator under three respondents in the
estimator rather than in the formatter, so `ItemAnalysis.median_discrimination`
is `None` on the dataclass a scoring script reads rather than `1.0` on the page
only. The paragraph above is left standing and is read in the past tense.

**The other half of that paragraph is unaffected and stays open.** The wired
caller still passes one arm, and the registered twelve-respondent analysis still
has no entry point any run reaches.

### Still open, and not fixed by this section

- **`s13p`'s `why` in `datasets/triggers/decision-making/s.yaml`** locates its
  fourteen rows in `results/triggers/`. Governed path; needs its own commit and
  its own `docs/DECISIONS.md` entry.
- **`report_item_analysis`'s docstring in `scripts/run_triggers.py`** states the
  BenchBench correlation as `r = -0.62`. `benchbench2026`'s own `note` records
  that the abstract prints the magnitude and gives the direction in words, and
  that a citation writing the minus asserts a character the source does not
  print. The docstring is outside this unit's paths.
- **`9895d08`'s commit message** says the item-analysis unit "moved five of its
  inputs" and then lists four things, two of which are sections of one file, and
  names `paper/refs.bib` among them. `refs.bib` is not a site input and appears
  nowhere in `site/build-manifest.json`; the manifest diff moved exactly two
  entries, `docs/DECISIONS.md` and this file. Commit messages cannot be amended
  here, so it is recorded rather than fixed.

### Closed, 2026-08-20: the wired caller now assembles the registered twelve

`report_item_analysis` takes a `pool` argument and `run_triggers.py` exposes it
as a repeatable `--pool`. Each pooled checkpoint joins as an arm named by its
file stem, and nothing about comparability is decided at the call site:
`_respondent_grid` already applies the same four guards `compare` applies, and
pooling is the stronger claim of the two, so a refusal stops the whole table
rather than dropping one arm out of it. Dropping would move the denominator the
caller named and print a number anyway.

Pooling the six description arms this entry names reproduces every figure in the
section above from a clean checkout: **12 respondents, 258 items, 0
unparseable**, mean difficulty 0.9913 over positives and 0.8614 over negatives,
median `r_pb` 0.5153 over the 73 items where it is defined, 86 complete triples,
and a floor of exactly one item, `l19n1`. That is the re-derivation, not a
re-reading of the section.

Two of the three bullets above are therefore closed or were already closed. The
docstring bullet was stale when it was written: the text on disk states the
correlation as a magnitude with the direction in words, which is what
`benchbench2026`'s `note` asks for. `s13p`'s `why` is still open and is still a
governed path.

### What the review did not find

Nothing in the arithmetic. The independent re-derivation for this section
reproduced all 258 difficulties, the floor and ceiling counts, both mean
difficulties, all 86 joint outcomes and the mean and median over them, and both
independence baselines, agreeing with the section above everywhere except the
three places named in C1, C3 and C4 — and each of those three is a sentence
about the numbers, not a number. The estimators are sound. What kept failing is
the prose around them, in the direction of the author's argument.
