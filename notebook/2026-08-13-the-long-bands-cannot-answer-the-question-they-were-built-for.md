# 2026-08-13 — the long bands cannot answer the question they were built for

Track N built the `l` and `xl` bands to test one hypothesis: **a skill
description scanning for "should I" misses a short ask buried under a thousand
words of context.** Everything about corpus v3 — the matched triples, the
byte-identical bodies, the XL band's existence — is downstream of that.

The corpus cannot test it. This is arithmetic, computed today, and it was not
computed before the band was authored.

---

## Two measurements, neither of which was on record

**1. The design effect is 1.63, not 1.0.** The intraclass correlation over
triples on realistic records is 0.32–0.35. Every power figure previously written
for this corpus — including in the held N6 pre-registration — used an item count
with no design effect at all, in a document that *mandates* clustering three
paragraphs earlier.

**2. Clustering is a no-op on recall, by construction.** Each triple is one
positive and two negatives, so on the positives subset `n_clusters == n_items ==
40`, ICC 0.000, design effect exactly 1.000. Verified directly. The triple
structure — the corpus's central design idea — buys **nothing** for recall.
"Clustered interval on recall" is a vacuous phrase and it was about to be
written into a registration.

## What follows

At 80% power, two-sided, against a 0.95 reference:

| contrast | n | smallest detectable drop |
|---|---|---|
| accuracy, S+M vs L+XL | 72 vs 48 items, DE 1.63 | **0.240** |
| recall, S+M vs L+XL | 24 vs 16 positives, DE 1.00 | **0.360** |
| recall, XL alone | 24 vs 7 positives | power 0.22 at a 20-point drop |

The prediction on record was "a small fall, 0 to 5 points". The instrument
cannot see 24. **The gap between what was predicted and what is detectable is
roughly a factor of five, and nobody had computed either number until after the
corpus was built.**

A null result here would have been written up as "flat, the ceiling reading is
not supported". It would have carried no information whatsoever.

---

## Why the design causes it

Recall's denominator is the count of **positives**. The matched triple gives one
positive per three items. The 1:2 ratio is what kills the word-count shortcut —
it is the best thing about this corpus — and it is also what starves the
denominator of the measurement the corpus exists to make.

That trade was never written down. It is not obviously the wrong trade; it is
simply that one side of it was designed for and the other was not noticed.

Power is therefore bought only by whole new triples, at three items each:

| added L/XL triples | L+XL positives | recall MDE | accuracy MDE |
|---|---|---|---|
| +0 (today) | 16 | 0.360 | 0.240 |
| **+23** | **39** | **0.200** | **~0.14** |
| +44 | 60 | 0.150 | ~0.11 |
| +97 | 113 | 0.100 | ~0.09 |

**+23 is the registered target** — the knee of the curve. +44 nearly doubles the
authoring for five points, and a 10-point recall MDE would need +97 long-form
triples, which is not a sane single pass.

**A 10-point recall effect is out of reach at any corpus size this project will
build.** Saying so now is cheaper than discovering it in a write-up.

---

## The sequencing this changes

N6 was going to run next on the 120-item corpus. It is not going to.

Not because 720 calls are expensive — they are not, and quota is explicitly not
a reason to hold back — but because those calls would be spent at a
`set_version` that the corpus extension immediately supersedes.
`label_versions_comparable` would then refuse to compare the result against the
properly-powered run, so the first run could not even serve as a pilot for the
second. It would be 720 calls that can never be combined with anything.

New order:

1. Finish blind adjudication on the current 120. *(running; judge 0 complete at
   4 of 120 moved, 3.3%)*
2. Author +23 L/XL triples, to the failure taxonomy the XL adversarial review
   produced.
3. Adjudicate the new items.
4. Freeze the corpus, stamp the version.
5. Then run N6 **once**, on a corpus that can answer it.

## What was nearly published

Three separate things had to be true at once for this to be caught: someone
computed the design effect, someone noticed the positives are singleton
clusters, and someone asked what recall's denominator actually is. Each was
cheap. None was on the checklist, and the pre-registration had already passed
one adversarial review that found ten other defects **without finding this
one** — that reviewer worked the bands and the estimators and did not ask
whether the corpus had the items.

The rule this suggests, offered as a hypothesis and not yet a standing rule:
**compute the minimum detectable effect before authoring the corpus, not before
running it.** By the time a band exists, the sunk cost is the argument for
running it.
