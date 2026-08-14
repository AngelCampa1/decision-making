# 2026-08-13 — the corpus fails its own battery, on the last sentence

The shortcut battery was rebuilt today after `imperative_opener` was found to be
inert. The rebuild added three things: an **attainable-AUC guard** that refuses a
feature no label assignment could move, **terminal-position features**, and two
**derived views** — the ask, and the closing sentence alone — alongside the whole
turn.

**Corpus v3 fails it, twice, and no threshold was touched to make that happen.**

---

## Failure 1 — a feature that has never been able to fail

`paste_cues` is inert in **all three views**. Its attainable interval is [0.405,
0.595] on turn and ask, and exactly [0.500, 0.500] on close. It has been reported
as one of eight features comfortably inside the separability band since it was
written, and it was measuring nothing the entire time.

That is the second inert feature found today and the fifth instance of the failure
`CLAUDE.md` names. The guard that caught it is new, which is the point: **the
defect was invisible to every check that existed, and it was invisible because the
check reported a pass.**

## Failure 2 — the closing sentence gives the label away

Four features separate the labels on the closing sentence while the whole turn
looks clean:

| feature | close | turn |
|---|---|---|
| word_count | **0.395** | 0.511 |
| char_count | **0.370** | 0.481 |
| first_person_rate | **0.627** | 0.554 |
| type_token_ratio | **0.602** | 0.471 |

**Positives close at a median of 11 words; negatives at 15.** Under the design's
own null — 20,000 within-triple label permutations, which is narrower than an
independent-sampling formula because three members of a triple are not three
draws — a clean corpus reaches three leaking features on this view about 2% of the
time. Four sits at **p = 0.002**.

This is an authoring habit, and it was visible in miniature a day earlier: the XL
positives were the shortest member in 7 of 7 triples because `ledger` positives
end in short asks. That was treated as an XL problem and fixed by rebalancing four
asks. **It was never an XL problem.** It is corpus-wide, it survived the fix, and
pooling over the whole turn hid it.

---

## The gate's power was derived before it was allowed to fail anything

Per-feature gating on all three views fails a **clean** corpus once in five runs
(0.206) — the repository's own argument against a gate that fires at random. So
the turn view keeps its per-feature gate (0.032) and the derived views fail only
on three or more features (0.019 and 0.002).

The same arithmetic stopped the stump being widened. Over 200 permutations the
null lift rises from mean 0.056 / p95 0.075 at ten columns to 0.077 / p95 0.100 at
thirty. The 30-column stump reads 0.108 on the real corpus — it would fail the cap
while sitting on the null's 95th percentile. Widening without re-deriving the cap
would have repeated the exact scale error `MAX_STUMP_LIFT` exists to correct.

**This is the first gate in this repository whose false-positive rate was computed
before it was switched on.** Standing rule 2 asks for a known-good case; this went
further and asked how often the gate fires on one.

---

## And the construction the corpus claims is not the construction it has

Measured shared-body fraction per triple:

| band | triples sharing ≥90% of the body |
|---|---|
| s | **0 of 14** |
| m | **0 of 10** |
| l | 3 of 9 |
| xl | 5 of 7 (84–99%) |

`l.yaml`'s header says the pasted material *"is byte-identical across the positive
and its two negatives"*. Six of its nine triples share **zero characters**.
`corpus.py`'s docstring says "three of nine" and is correct — so two files in this
repository disagree, and the one a reader meets first is the wrong one.

Three routes reached this independently today: a prefix measurement here, a
shared-body detector in the long-band authoring unit, and the battery rebuild's
own attempt to derive the ask by intersection (which recovers nothing in 30 of 40
triples, and is why there are two derived views rather than one).

**So "matched triples kill the length shortcut by construction" is a claim this
corpus cannot make.** True of XL, partly true of L, false of S and M — 72 of 120
items. The battery finds no length ruler on the turn view, so the corpus does
appear ruler-proof. It is simply not ruler-proof *by construction*; it is
ruler-proof by careful authoring. That is a much weaker guarantee, it was never
what was claimed, and — unlike a construction — it does not extend to items
authored later.

Which matters right now, because 47 new triples are being authored as this is
written.

---

## What this does not say

Adjudication has moved **2 of 120 labels (1.7%)** against a pre-registered kill of
20%. The labels are holding. Nothing here says the corpus is wrong about what a
decision is; it says the corpus leaks its answer through the shape of its last
sentence, and that its documentation describes a construction it only partly has.

Both are fixable by rebalancing closing-ask length without changing what is asked.
**Any item whose ask is edited must be re-adjudicated**, because the ask is what
the label rests on — that is the whole design.

## An estimator defect found inside a defect-finding instrument

The long-band unit's stance detector examines only text all three members share.
For six L triples that is the empty string, and a check reading an empty string
returns clean unconditionally. It reported 12 of 16 triples clean; five of those
verdicts could not have failed.

It reported this about itself. That is the sixth instance today of an estimator
that cannot return a non-zero value — and the first one caught by the instrument's
own author, before anybody quoted the number.
