# 2026-08-13 — the sixth pre-registration defect, and the first one caught before the data

An adversarial sub-agent was given the draft N6 pre-registration
(`notebook/2026-08-13-n6-prediction-does-accuracy-fall-on-the-long-bands.md`),
the repository's standards, and no statement of what its author concluded. Its
verdict: **not safe to run as written.**

It is right, and the 720-call confirmatory run is held until the registration is
rebuilt. That is not a pause in the programme; the instrument is the work.

Five of its claims were recomputed here before any of them were acted on. **Four
confirmed. One is wrong.**

---

## Confirmed

**1. Three of four bands name no function that exists.**

The document's own opening promises that "every band below names its estimator,
its denominator and the **function** that computes it" — the rule written after
four slips on 2026-08-12. Then:

- **Q4** registers "`settled` has the highest FPR of the seven." There is no
  `summarise_by_kind` in the tree, and `summarise` cannot score a kind subgroup
  because a kind subgroup is all negatives.
- **Q3** registers routing accuracy per procedure. `covers_rates` computes the
  pooled rate only; `evaluate_routing` takes a `TriggerSet` and a callable, so it
  reads turns and cannot be pointed at a checkpoint.
- **Q1** mandates clustering over `triple`, then registers a difference between
  **disjoint** groups — S+M is 72 items in 24 triples, L+XL is 48 in 16.
  `cluster_bootstrap_diff` is a *paired* mean-difference bootstrap. Nothing here
  computes an unpaired two-group clustered difference, and subtracting two
  independent percentile intervals does not produce one.

The rule was written down, and then the very next registration broke it three
times. Writing the rule is not the control; **checking the band against the
function before the run is the control.**

**2. Q2's baseline is the cross-version comparison the guard exists to refuse.**

Verified from the checkpoints:

```
verdicts.jsonl          (full)          n=365  set_version=None
verdicts-stakes-shown.jsonl             n=146  set_version=2
```

`label_versions_comparable` has a "one stamped, one not" branch that returns a
refusal. The registration's replication baseline — "on v2, `stakes-shown` beat
`full` on precision" — **is refused by this repository's own code.** The guard was
built after the fourth defect of this kind; the records were never reconciled to
it, so the guard has been passing because nothing called it on these two arms.

Worse, the artefact runs the same way as the claimed effect. Moving a turn from
the positives to the negatives *adds a negative*, which can only lower precision
for an arm that fires on it. So the version gap flatters `stakes-shown`, which is
the direction the prediction wanted.

**3. "Q1 can see a 20-point drop" is false, by one item.**

The document's own table says 49 items per group. L+XL is **48**. The sentence
was written directly beneath the table that contradicts it. With the design
effect the same document mandates, the smallest detectable drop is 0.20–0.26, not
0.20.

This is the L7 defect again, verbatim — a band set without computing what it can
resolve. L7 registered recall ≥ 0.94 over 17 positives when the observed ceiling
was 0.941. The lesson was written into `CLAUDE.md`. It did not take.

**4. The runner does not stamp the estimator Q3 registered.**

`run_triggers.py` sets `covers` by equality against `case.route`, which is
`routes[0]`. `TriggerCase.route`'s own docstring says it is "**not** the scoring
rule: `evaluate_routing` accepts any member of `routes`." The registration named
membership. The corpus has three dual-route positives, so the denominators
differ by rule.

## Refuted

The review gave per-procedure denominators under the runner's rule as ledger 10,
cascade 10, fit 8, **timing 5**, and argued timing would come last by noise as
the smallest group. Measured:

| rule | fit | cascade | timing | ledger |
|---|---|---|---|---|
| `routes[0]` (what the runner stamps) | 8 | 8 | **7** | 10 |
| membership (what was registered) | 8 | 10 | 8 | 10 |

The divergence is real and the finding stands. The specific split is wrong and
the "smallest group at 5" argument does not survive it. Recorded because a
reviewer that is right about four things and wrong about a fifth is exactly what
independent confirmation is for.

---

## The band that would have confirmed itself

The sharpest objection is not any of the above. Q1 registered "accuracy(S+M) −
accuracy(L+XL) is between −0.05 and +0.10" against a standard error of ~0.041.
Simulated, the probability the result lands **inside** that band is:

| true difference | P(inside) |
|---|---|
| 0.00 — no fall at all | 0.88 |
| 0.05 — the prediction | 0.88 |
| 0.10 — Tracks L and M re-open | **0.50** |

The band assigns the same probability to the null and to the prediction. It
cannot make the one distinction Q1 exists to make, and it reports the
programme-changing outcome as "flat" on a coin flip.

**Run as written, the most likely result was: Q1 lands inside its band and is
written up as "flat, the ceiling reading is not supported"; Q3 confirms at ~27%
by chance; Q4 reads 0.000 across the board and is quietly dropped.** A clean,
confident, well-shaped result of exactly the kind this repository's history is
made of.

---

## What is different this time

The five previous pre-registration defects were all found **after** the run — in
one case after 365 calls. This one was found before a single call, by an agent
that did not write the document and was not told what it concluded.

That is the first evidence in this repository that the sub-agent-plus-adversarial-review
method does anything, and it is one observation, not a result. It cost roughly
128k tokens against 720 calls of a run that would have measured nothing.

**The counterfactual is not free either.** The review also produced a
confidently wrong denominator table that would have been believed had it not
been recomputed. Adversarial review moves the error from "confident and
unchecked" to "confident and checkable". It does not remove it.

## What happens next, in order

1. Write the three missing estimators — group-by-procedure, group-by-kind, and an
   unpaired clustered two-group difference. A band may not name a function that
   does not exist.
2. Re-score the v2 arms onto one label version and commit those records, so Q2's
   baseline is a within-version comparison.
3. Rebuild the registration: report Q1 as an interval rather than a containment
   test, drop or demote Q3 and Q4 to point estimates with stated denominators,
   register the bootstrap seed and resample count, and derive the 2-repeat choice
   from the measured ICC of 0.741 or record it as a choice.
4. Then run.

## Still open, and recorded as open

The review asserts the reference accuracy of 0.95 is imported from a corpus
whose ruler scored 0.890, while this corpus's best shortcut is 0.750 — so
assuming 0.95 on a corpus deliberately built to be harder is the optimistic end,
and it is the assumption that makes 48 items look nearly sufficient. That is a
judgement about an unmeasured quantity, not an arithmetic error, and it is not
resolvable before the run. It is registered here so that if the arm lands well
below 0.95, nobody gets to be surprised.
