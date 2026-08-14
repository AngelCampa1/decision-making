# 2026-08-13 — N5: what a realism probe without a comparison set can say

**Written before the run. 40 calls, not yet made.** The instrument is
[`scripts/realism_probe.py`](../scripts/realism_probe.py); the maintainer
launches it.

Track N5 asks whether the model-authored trigger corpus reads as text a person
sent or as text written for a benchmark. This entry records the design, the
parameters I chose rather than derived, and — more usefully — the two confounds
that were found *before* any call was made, both of which would have produced a
clean, plausible, publishable number.

---

## The thing this cannot do, stated first

There is **no human-written comparison set in this repository.** Track N4, the
holdout, does not exist. So there is no known-good case: nothing here is known to
be a real message, and therefore nothing can show that a judge calling a turn
"composed" is right about it.

That has three consequences and they are not softenable.

1. **It is descriptive and it must never become a gate.** Standing rule 2 says a
   falsifier must be run against a known-good case before it may fail anything.
   There is no known-good case, so there is no falsifier. The script prints a
   rate with an interval and has no `passes` property, no threshold and no exit
   code keyed on a number.
2. **The base rate is unmeasurable.** If the probe returns "composed" on 45% of
   turns, nobody here can say whether a judge would also return 45% on a set of
   genuine messages. The number is a statement about one model's prior over
   message text.
3. **A forced choice — the sharper instrument — is unavailable.** It cancels the
   base rate, which is exactly the quantity missing, but it needs real messages
   to pair against. The tempting substitute, pairing two *corpus* items, is an
   estimator that cannot answer the question: both sides are model-authored, so
   it sits at 0.5 by construction however authored the whole set reads, and it
   prints a clean number while doing so. That is the 2026-08-12 defect shape, and
   it was rejected for that reason rather than on taste.

**This deviates from the written plan.**
[`docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md`](../docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md)
specifies a mixed sample judged comparatively — "which turns look like a real
message and which look authored". That framing assumes two populations this
repository does not have. The deviation is recorded here rather than made
quietly, and the plan document still says the other thing.

---

## Sample design

**40 calls, one item per matched triple.** The corpus is 40 triples of three
turns, and in the L and XL bands a triple's three turns share a byte-identical
body and differ only in the closing ask. Two items from one triple are one text
shown twice. One per triple makes the track's 40-call budget fall out of the
corpus structure rather than being chosen.

**Stratified by band and by domain, label alternating inside each domain group.**
This gives 21 positives and 19 negatives — balanced rather than the corpus's 1:2,
because balanced allocation minimises the wider of the two per-label standard
errors. The corpus-weighted rate is reported alongside as a point estimate.

**What the sample costs, which is the matched-triple design itself.** With one
item per triple the label contrast is *between* clusters, so it carries anything
that varies across triples. A within-triple design — 20 triples × 2 items — is
the same 40 calls and would answer the label question properly, at the cost of
covering half the corpus. Breadth was chosen because N5 is a coverage question;
that is a choice and this is where it is recorded.

### Parameters I chose rather than derived

| Parameter | Value | What would settle it instead |
|---|---|---|
| Judge model tier | `haiku` | Matches `adjudicate.py` so both passes over this corpus are one tier. Running both tiers is 80 calls and is the measurement. |
| Judges per turn | 1 | Adjudication needs a majority because it moves labels; this moves nothing. Three judges would buy precision on a descriptive number at a third of the coverage. |
| Interval level | 95% | Convention. Unadjusted across ~16 printed rows, and the report says so. |
| Audit allocation | 3 per band, equal | Proportional would give XL two items, and XL is the band most open to question. A human audit large enough to allocate by variance would settle it. |
| Audit sample | subset of the probe sample | Deliberate: it is the only anchor the machine's base rate has. The cost is that the human inherits every confound below. |

---

## Two confounds found before the run, by adversarial review

Both would have produced a clean number. Neither was visible from reading the
script.

### 1. Em-dashes are perfectly aliased with the long bands

Em and en dashes appear in **every** L and XL item of the sample and in **none**
of the S and M items:

```
band            em/en dash
l                      9/9
m                     0/10
s                     0/14
xl                     7/7
```

A judge keying on a mark a phone keyboard does not produce would therefore return
`{s 0.0, m 0.0, l 1.0, xl 1.0}` — a perfect, clean band effect that is about
punctuation. It would have been narrated as "the long bands read as composed."

The prompt's one debiasing sentence is about *length*, which is the dimension the
artefact is confounded with, not the artefact. Rather than strip the marks — that
would be tuning the corpus to a judge — the prevalence is now **printed beside
the band table**, so the sentence cannot be written without somebody having seen
the column that also separates those bands perfectly.

### 2. The label was a function of triple parity, and the corpus rotates domain with the triple index

The first draft alternated positive/negative on the triple index, so every
positive came from an odd-numbered triple and every negative from an even one.
The corpus cycles domain through the triple index, so the sample inherited it:
six relationship positives against three, and a stakes skew.

Demonstrated rather than argued: a stub responding **only to the band** — exactly
label-blind — still printed a six-point label gap.

Two fixes, and the second is the one that matters:

* Alternation now runs inside each domain group, which removes that alias.
* The report prints a **band-adjusted** label gap beside the raw one. The
  label-blind stub scores `+0.000` on the adjusted line and `+0.060` on the raw
  one, which is the known-good case the raw gap fails. The band arithmetic is
  unavoidable — L and XL have odd triple counts — so the raw gap could not be
  fixed, only measured around.

The residual caveat stands and is printed in the report: band-adjustment removes
band, not stakes, authoring order, or typography.

---

## What I expect, and where I expect to be wrong

No registered bands, because there is no comparison and nothing to be inside or
outside of. Qualitative expectations, recorded so they can be wrong:

1. **The composed rate will be high — I would guess above 0.5.** These turns were
   written to order by a model in one sitting. If it comes back near 0.1 my first
   suspicion is the prompt, not the corpus.
2. **The band column will show the long bands as more composed**, and I expect
   that to be *unreadable* because of the dash alias above. This is the
   prediction I most expect to be unable to interpret, which is why the
   typography column was added before rather than after.
3. **The band-adjusted label gap will be near zero.** The positive and its two
   negatives share a body in L and XL, so there is little for a realism judge to
   separate. A large adjusted gap would be more surprising than a null and would
   point at the closing ask being where the authored register lives.
4. **Where I expect to be wrong:** that the `kind` table will say anything. It is
   negatives-only, seven kinds over 19 items, cells of one to nine. It is printed
   for completeness and I do not expect to be able to read it.

---

## What no outcome of this run licenses

- It does not retire the corpus. Nothing here can.
- It does not validate the corpus either. A low composed rate would mean one
  judge's prior does not flag this text, which is not the same as a person having
  written it.
- It says nothing about the *other 80 items*, about another model tier, or about
  the author. The interval covers the judge's stochasticity over these 40 items
  and nothing else — the cluster-level sampling fraction is 1.0, so there is no
  population left to have sampled from.

The 12-item human audit is the part with ground truth and it needs a person. The
sheet is emitted blind — opaque keys, hash-ordered, no band and no label — and it
carries its own caveat at the top: **the only auditor available authored this
corpus**, so it is a self-assessment. An outside reader is Track N4's job.
