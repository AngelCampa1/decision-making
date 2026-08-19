# 2026-08-18 — N6: two arms in, and I saw the numbers during an instrument check

Written **while arm 3 is still running**, and written now rather than folded
into the analysis, because the order in which things were seen is the part that
cannot be reconstructed honestly later.

## What happened, stated in the order it happened

A sub-agent was dispatched to do a *readiness* check — name the function behind
each registered quantity, and show that each estimator can return a non-zero
value on this arm's structure, which is standing rule 2 and the direct lesson of
the two 2026-08-12 estimators that produced clean zeros while measuring nothing.
**Demonstrating that an estimator can move means running it on real records, and
running it on real records is scoring.** So Q1, Q3 and Q4 were computed on the
completed `full` arm as a side effect of checking they could be computed at all.

There is no way to un-see that, and the mitigation is not to pretend otherwise:

- **The bands were registered on 2026-08-13 and 2026-08-14, and amended once on
  2026-08-18 for item counts only.** All three entries are committed and their
  first commits precede every call in this run. Nothing below was chosen after
  the numbers were seen.
- **Every figure here was re-derived by me** from the checkpoints after reading
  the agent's report, not taken from it.
- **Arm 3 is unseen.** `opener-only` was at 244 of 516 when this was written.

The defensible design would have been a readiness check on *synthetic* records,
which is what the N6 addendum did four hours earlier and what I did not ask for
this time. That is the lesson and it belongs here rather than in a retrospective.

## Where the four registered questions stand on two arms of three

| | registered | observed | |
|---|---|---|---|
| **Q1** accuracy falls on the long bands | `excludes_zero and difference > 0` on `bootstrap_rate_difference(control=L+XL full-arm, treatment=S+M full-arm, cluster_on="triple")` | **+0.0976, 95% CI [0.0459, 0.1493]**, excludes zero | **met** |
| **Q2** `stakes-shown` beats `full` on precision, as on v2 | sign of the difference | **+0.0079** (0.8680 vs 0.8601) | **sign holds, thinly** |
| **Q3** `ledger` is the worst-routed of the four | descriptive, over 19 first-route positives | **ledger 0.474** vs cascade 0.875, fit 0.833, timing 0.767 | **met** |
| **Q4** `settled` has the highest FPR of the seven kinds | descriptive, over 20 negatives | **settled 0.000 — the *lowest***; `meta` highest at 0.357 | **falsified** |

## Q4 is the one worth reading, because it is wrong in a specific direction

The registered reasoning was: *"A negative whose decision has been made and
stated is the one that still looks like a decision, and it is the kind v2 barely
had."* Predicted `settled` highest, `lookup` lowest.

**`settled` fired on 0 of 40 records — not one of its 20 items, on either
repeat.** `lookup` is second-highest at 0.122. The prediction is not merely
unmet; both named ends are the wrong way round.

**The 2026-08-14 entry pre-empted the obvious objection to a zero**, which is
the only reason this reads as a result rather than as no data: *"At n = 20,
`settled`'s Wilson interval is materially narrower than at n = 5 — a `0.000`
reading is no longer indistinguishable from 'no data'."* The interval is
[0.000, 0.161].

What is highest instead is **`meta` at 0.357** over 7 items, CI [0.118, 0.697].
Seven items is seven items and that interval is nearly six-tenths wide; it is
reported because it is what the estimator says, not because it settles anything.

**The false positives are concentrated by band, not by kind.** Of the 21
distinct negatives that fired at all, **20 are `l` or `xl`** — 11 `l`, 9 `xl`,
one `s`, and no `m` item ever fired wrongly. Arm 1's FPR reads
0.010 on `s`, 0.000 on `m`, 0.190 on `l`, 0.147 on `xl` — so the "kind" story
Q4 asks about is largely a length story wearing a kind label, which is exactly
the confound Track N exists to remove and did not remove here.

## Two pre-registration defects, found by looking for functions rather than answers

Both are the shape this repository has now recorded five times, and both were
found before the analysis rather than after, which is the only cheap moment.

- **Q2 names a quantity nothing computes.** There is no ordering or precision-
  sign function in `trigger_arms`; `compare()` is a paired Wilcoxon over
  per-item **correctness**, not precision, and its docstring says so. Q2 is
  therefore a by-hand subtraction of two `summarise()` calls. Nothing would have
  announced a defect in it — there is no code to be wrong.
- **Q4's band names no arm.** "FPR by `kind` within v3" was registered without
  saying which of the three arms it is computed over, and the three arms have
  different firing behaviour by construction. The `full` arm is the natural
  reading and is what is reported above, but the reading was chosen after the
  run started. That is the M5 `covers` defect again — *the measure was named and
  the denominator was not* — and that one only cost nothing by luck.

## Also worth recording: the design effect was assumed 16× too large

The power arithmetic in all three N6 entries uses
`design_effect(m=3, icc=0.315) = 1.63`. **The observed ICC on the `full` arm is
0.0127, a design effect of 1.025**, and `clustering_is_inert` reads `False` — so
the clustering is real, just nearly weightless.

The registered figures were therefore **conservative, not optimistic**, which is
the harmless direction: effective n is 251.6 against the 158 the 1.63 assumption
implies, so Q1 is better powered than it was registered to be, not worse. The
0.315 is not thereby wrong — it came from a different corpus at a different
size — but it should not be carried into the next power calculation without
being recomputed against this one.

## What is not claimed here

**Nothing about N6 as a whole.** It is a three-arm run and one arm is unseen.
Q1's band is explicitly registered over `full`-arm records and is complete; Q2
needs `full` and `stakes-shown` and both are complete; Q3 and Q4 as reported are
`full`-arm only, per the reading declared above. The published run record waits
for `opener-only`, and if arm 3 changes any of this, it changes it in that
record and not by editing this entry.
