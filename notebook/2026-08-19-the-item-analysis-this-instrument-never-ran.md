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
