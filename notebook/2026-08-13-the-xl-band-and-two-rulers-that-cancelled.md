# 2026-08-13 — the XL band, and two rulers that cancelled each other out

Track N2, phase 3. Seven triples, 21 turns, 900–1,500 words each. The corpus is
complete at **120 items, 40 positives, 80 negatives** across four bands, and it
is the first time the `ledger` procedure has been shown a pile of context.

Not a run. No model was called and nothing here is a prediction. Two findings,
and both are about the gate rather than about the corpus.

---

## 1. The gates were reading nothing

`check_trigger_sets` globs `datasets/triggers/*.yaml`. The version 3 bands live
in `datasets/triggers/decision-making/`, one directory down. So the shortcut
battery, the stump, the balance rules and the band-width rules — all four gates
this track exists to install — **could not see any of the 99 items that were
already authored**, and `de check` reported green on every commit that added
them.

The numbers in `bf88664`'s commit body were real; they were computed by hand at
the terminal, the way I computed them again today. Nothing in the repository was
computing them.

That is the third instance of this exact shape:

| | tested | called by |
|---|---|---|
| `triggers` (2026-08-12) | 100% | nothing |
| `prereg.py` (2026-08-13) | every refusal in PROTOCOL §3 | nothing |
| the v3 corpus gates (today) | four gates, full battery | nothing |

The first two were found after something had been published. This one was found
while the corpus was still being written, which is the only reason it cost
nothing — and it was found by asking "what actually loads this file?", which is
the question that would have found the other two as well.

Fixed by `datasets/triggers/decision-making/index.yaml` plus `_check_drafts`,
which holds a corpus under construction to the same rules as a live one without
making it live. **It stays a draft**: swapping the entry point before blind
adjudication (N3) would publish on an answer key whose pre-registered kill has
not been run.

The check is asserted in both directions — a broken triple is reported, and the
draft that passes is asserted to contain 120 items in four bands, because a
green gate is worth nothing unless it read something.

## 2. The pooled AUC was 0.511 and both halves of it were rulers

The battery reports one AUC per feature over the whole set. On word count that
number was **0.511**, which is as clean as it gets. Per band:

| feature | S | M | L | XL | pooled |
|---|---|---|---|---|---|
| **word_count** | 0.503 | 0.547 | **0.769** | **0.301** | **0.511** |
| char_count | 0.358 | 0.425 | 0.660 | 0.337 | 0.481 |
| first_person_rate | 0.452 | 0.700 | 0.602 | 0.633 | 0.554 |

In the L band the positive is the **longest** member of its triple in 7 of 9
cases. In the XL band, as first written, it was the **shortest** in 7 of 7. Both
are the same authoring habit seen from two sides — a `ledger` positive ends in
four words (*"What do I do?"*) while a `compute` negative ends in ninety — and
the two directions cancel in the pool almost exactly.

This is not a within-triple artefact that a model could never exploit. Length
inside a band is available at inference: *"long, and near the bottom of the XL
range"* is a rule a classifier can implement, and it would have scored well.

**The stump caught it and the battery did not.** A depth-2 tree can split on
length and then on length again, which is exactly the cancellation, and it read
a lift of **0.117** against a cap of 0.100. `bf88664` had already recorded a
failure at 0.101 and predicted that XL was where the last thousandth had to come
from; the true figure was larger than that, because XL made it worse before it
made it better.

Fixed by mixing the ask lengths so the positive is the shortest member in four
triples, the middle in one and the longest in two. Final state, 120 items:

```
says_should_i     0.575    first_person_rate 0.554    word_count  0.511
question_marks    0.500    imperative_opener 0.494    paste_cues  0.489
char_count        0.481    type_token_ratio  0.471
stump 0.750 against a majority baseline of 0.667 — lift 0.083, cap 0.100
```

### Why per-band separability is reported and not gated

The tempting fix is to run the battery per band. The arithmetic says not yet.
Under independent sampling the null standard error of an AUC is
`sqrt((n_p + n_n + 1) / (12 · n_p · n_n))`:

| band | positives | negatives | pairs | null SE | ±0.10 is |
|---|---|---|---|---|---|
| S | 14 | 28 | 392 | 0.096 | ±1.05 SE |
| M | 10 | 20 | 200 | 0.114 | ±0.88 SE |
| L | 9 | 18 | 162 | 0.120 | ±0.83 SE |
| XL | 7 | 14 | 98 | 0.137 | ±0.73 SE |
| pooled | 40 | 80 | 3,200 | 0.056 | ±1.78 SE |

A [0.40, 0.60] gate on the XL band alone would fire on a *perfectly clean*
corpus something like half the time, and there would be eight of them per band.
A gate that fails at random is a gate somebody turns off, which is the argument
`_check_separability` already makes for the ratchet.

**The caveat runs the other way and I do not know its size.** That formula
assumes independent draws, and a matched triple is not one — the three members
share a body, so the true null variance is *smaller* than the table says by an
unknown amount. So this is an upper bound on the noise, not a measurement of it,
and whether a per-band gate is affordable is **open rather than settled**. What
is settled is that a pooled AUC of 0.511 is not evidence that a band is clean,
and the per-band table now has to be read beside it.

## What this does not fix

The corpus is authored by a model, which N4's human holdout is the only control
for. Adjudication (N3, 360 calls, 20% kill) has not run. Nothing here licenses
any claim about the corpus being a fair test — it licenses the claim that the
gates written for it now run.
