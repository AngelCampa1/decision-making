# 2026-08-13 — pre-registration for N6, the confirmatory run on corpus v3

**Written before any arm has been run on version 3.** Track N phase 7. The
confirmatory run is `full`, `stakes-shown`, `opener-only` × 120 items × 2
repeats = **720 calls**, on Haiku, and the descriptive run (N7, the remaining
five arms) is a further **1,200**.

Every band below names its **estimator**, its **denominator** and the **function**
that computes it, per the rule four pre-registration slips on 2026-08-12
produced. Where a question cannot be answered at this sample size, that is said
here rather than discovered afterwards.

---

## The instrument, stated before it is used

120 items, 40 triples. One positive and two negatives per triple, sharing a body.

| band | items | triples | positives | routed positives |
|---|---|---|---|---|
| s | 42 | 14 | 14 | 11 |
| m | 30 | 10 | 10 | 8 |
| l | 27 | 9 | 9 | 8 |
| xl | 21 | 7 | 7 | 6 |
| **all** | **120** | **40** | **40** | **33** |

**Majority-class baseline 0.667.** Every accuracy below is read against that and
not against 0.5. The best shortcut available is a depth-2 stump at **0.750**
(lift 0.083), which is the number an arm has to beat to have measured anything —
on v2 the equivalent was a word-count ruler at 0.890 against a best arm of 0.956.

**The clustering unit is `triple`, not item.** Three items sharing a body are
correlated and a per-item bootstrap gives standard errors that are wrong in the
anti-conservative direction.

---

## Power, computed first, and it kills one of the four questions

`stats/power.minimum_detectable_effect`, McNemar, α=0.05, 80% power, one-sided:

| stratum | pairs | p_d=0.10 | p_d=0.15 | p_d=0.20 | p_d=0.30 |
|---|---|---|---|---|---|
| whole set | 120 | **0.071** | 0.087 | 0.101 | 0.123 |
| v2, for comparison | 73 | 0.091 | 0.111 | 0.128 | 0.157 |
| S band | 42 | n/a | 0.145 | 0.167 | 0.205 |
| routed positives | 33 | n/a | n/a | 0.188 | 0.230 |
| XL band | 21 | **n/a** | **n/a** | **n/a** | 0.283 |

`n/a` means **no effect of any size is detectable** at that discordance.

Two things follow and both are registered as limits rather than discovered as
disappointments:

- **A paired arm comparison inside the XL band is not available.** 21 items
  detects nothing below a discordance of 0.30. Any per-band arm difference is
  reported descriptively, with an interval and no p-value.
- **The whole-set comparison is better than v2's and not by much** — 0.071
  against 0.091. Going from 73 items to 120 bought two points of MDE. What v3
  actually bought is a corpus a ruler cannot solve, which is a different and
  larger thing.

For Q1 the contrast is **between** bands rather than paired, so McNemar does not
apply. Two-proportion, α=0.05 two-sided, 80% power, against a reference of 0.95:

| drop to detect | items needed per group |
|---|---|
| 0.05 (0.95 → 0.90) | 435 |
| 0.10 (0.95 → 0.85) | 141 |
| 0.15 (0.95 → 0.80) | 76 |
| **0.20 (0.95 → 0.75)** | **49** |

Pooling gives **S+M = 72 items / 24 triples** against **L+XL = 48 items / 16
triples**, before any design effect from clustering. **So Q1 can see a 20-point
drop and cannot see a 10-point one**, and the per-band table (S vs M vs L vs XL
separately) is descriptive only.

That is the honest MDE for the question this whole track was built to ask, and
it is written down before the run because the alternative is a flat result that
reads as a finding.

---

## The four questions, with bands

### Q1 — does firing accuracy fall on the long bands? **This is the experiment.**

*Estimator:* firing accuracy = (true positives + true negatives) / parsed
records in the stratum, pooled over both repeats, via
`trigger_arms.summarise(...).accuracy`.
*Denominator:* parsed records in the stratum. Unparseable rows are dropped, not
scored as non-fires.
*Clustering:* bootstrap over `triple`.

**Registered band: `full` arm, accuracy(S+M) − accuracy(L+XL) is between −0.05
and +0.10.**

Prediction: **a small fall, 0 to 5 points, not significant at this n.** The
reasoning: v2's turns were all short and scored 0.956, and the long bands are
harder to read but their negatives are also *more* obviously non-decisions once
read — an 1,100-word body ending in "work out our share of the roof at the
bottom, the middle and the top of the range" is a less ambiguous negative than
"should I use postgres or mysql". Those two effects partly cancel.

**Where I expect to be wrong:** if the fall is real and large it will be in
**recall on XL, not in accuracy**, because the long positives end in short asks
buried under a thousand words of context, and that is exactly the shape a
description scanning for "should I" would miss. Accuracy pools that away against
80 negatives.

**What each outcome licenses.**
- Flat, and the arm beats 0.750: the six-point-ceiling reading of the five Track
  L/M nulls is **not** supported, and those nulls keep their original reading.
- Falls by more than 0.10: five nulls were measured at a ceiling, Tracks L and M
  are re-openable, and the corpus v2 results become uninterpretable rather than
  merely capped.
- Flat and the arm does **not** beat 0.750: the instrument has no resolution and
  Q2–Q4 are not worth reading.

### Q2 — do the arm orderings survive the corpus change?

*Estimator:* per-arm precision = TP / (TP + FP), and firing accuracy, both from
`trigger_arms.summarise`.
*Denominator:* precision over records where the arm fired; accuracy over parsed
records. **Both are reported, because M5's `covers` band named a measure without
naming what it divided by and got away with it on luck.**

On v2, `stakes-shown` beat `full` on precision. **Registered band: the sign of
(precision(`stakes-shown`) − precision(`full`)) is the same on v3 as on v2.**

Prediction: **it holds.** This is the cheapest replication available and the
only one that tests whether any v2 result was about the description rather than
about the corpus.

**This comparison is across corpus versions and `label_versions_comparable`
refuses it as a paired test — correctly.** So the v2 and v3 numbers are never
subtracted. What is compared is the *ordering within each corpus*, which is a
weaker and legitimate claim.

### Q3 — how does `ledger` route now that the corpus contains piles?

*Estimator:* routing accuracy = correct / labelled-and-answered, where correct
means the named procedure is in the case's `routes` tuple.
*Denominator:* **stated twice**, because this is where M5 slipped — over all 33
routed positives, and over the subset where the arm fired and named a procedure.
Both go in the write-up.

**Registered band: `ledger` is the worst-routed of the four procedures on the
`full` arm, over the 10 `ledger`-labelled positives.**

Prediction: **`ledger` routes worst.** It has never been tested on its own case;
every previous `ledger` number was measured on turns that were not piles. The
router row says "a pile of context" and never says what a pile can be made of,
which is the diagnosed defect behind `p03`.

**This band is descriptive and carries no p-value.** Ten items detects nothing.
Registered so the prediction is on record before the data, not because it can be
tested.

### Q4 — do twinned negatives fire more than hand-written ones?

*Estimator:* false-positive rate = FP / (FP + TN).
*Denominator:* the 80 v3 negatives, and separately the 56 v2 negatives.

**No band is registered and no test is run.** The two negative sets are
different items from different corpus versions scored against different label
revisions, and `label_versions_comparable` refuses the comparison. Reporting a
difference here would be exactly the cross-version subtraction that guard
exists to prevent.

What *is* available and is registered: **FPR by `kind` within v3**, over the
seven negative kinds (lookup 27, summarise 15, generate 13, compute 12, settled
5, diagnose 4, meta 4). **Registered band: `settled` has the highest FPR of the
seven.** A negative whose decision has been made and stated is the one that
still looks like a decision, and it is the kind v2 barely had.

Prediction: `settled` highest, `lookup` lowest. At n=5 for `settled` this is a
descriptive statement about five items and is labelled as one.

---

## What would void the run

- **Parse rate below 0.95 in any arm**, or parse rates differing by more than
  0.05 between arms. A skill that wins on accuracy while breaking the output
  contract has not won.
- **Any isolation receipt failing.** `assert_isolated` raises; the run stops.
- **Adjudication (N3) moving more than 20% of labels.** Then the corpus is
  retired and this pre-registration is void along with it — which is why N3 runs
  first and is already running as this is written.

## What this cannot show

The corpus is model-authored. N4's human holdout does not exist yet, so every
number this run produces is a statement about model-authored text, and the
`full` arm's accuracy is **not** an estimate of how the shipped description
behaves on real user messages. That sentence is not available from v2 either and
was never available.
