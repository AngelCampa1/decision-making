# Track N5 — the realism probe, run for the first time

**2026-08-18.** 86 isolated `claude -p` calls, `haiku`, one item per matched
triple over 258 items / 86 triples. **0 unparseable, 0 call failures.** Code at
`0ee75d4`.

**Answer key:** `datasets/triggers/decision-making/index.yaml` v4

Prediction: [`notebook/2026-08-18-prediction-n5s-descriptive-probe-runs-at-last.md`](../../../notebook/2026-08-18-prediction-n5s-descriptive-probe-runs-at-last.md).

**Descriptive. No threshold here retires the corpus**, and none is offered. The
probe asks a blind judge one question about one turn — did a person send this —
with no label, no skill, and no mention that the corpus is about decisions.

## Result

| | |
|---|---|
| **`composed` rate** | **26/86 = 0.302**, 95% Wilson **[0.215, 0.406]** |
| corpus-weighted (1 positive : 2 negatives) | 0.321 |
| by band | xl 0.471, l 0.429, s 0.208, m 0.167 |
| by stakes | high 0.213, low 0.410 |
| by label | positive 0.250, negative 0.357 |
| prompt | `ad274b4d0416` |

**The registered prediction was that the rate would exceed 0.50. It did not**,
and the interval's upper bound does not reach it. The judge called roughly seven
turns in ten a message a real person sent.

## Three things that qualify every number above

**Band and dash-presence are the same partition.** All 38 `l`/`xl` items carry
an em or en dash; none of the 48 `s`/`m` items do. There is no within-band
variance in the confound, so the band effect and a punctuation effect are not
distinguishable in this sample — stated as a limit, not a suspicion. The
prediction entry registered this risk before the run.

**The label row is a between-triple contrast** at one item per triple, and it
leaks: positives skew high-stakes (26/18 against the negatives' 21/21), while
stakes moves the rate further than label does (19.7 points against 10.7).

**A rate without a comparison set is a statement about the judge.** Nothing here
establishes what this judge says about text known to be human-written, so 0.302
is consistent both with a corpus that reads real and with a generous prior. What
it does rule out is a degenerate estimator: the rate moves across every stratum
tested and both verdicts appear throughout.

## Provenance, including the part that is weaker than the gate can see

The probe and the corpus are **byte-identical at `cc5ea68` and `0ee75d4`** —
`git diff cc5ea68 0ee75d4 -- scripts/realism_probe.py datasets/triggers/` is
empty — so the run's inputs are the same at either commit, and the directory
names `0ee75d4` because that is the commit carrying the prediction.

**The prediction entry was authored before the first call and committed after
it.** `0ee75d4` landed at 20:39:42 and the run's last record was written at
20:43:13. The provenance gate checks ancestry rather than timestamps, so it
passes; the honest statement is that only the author's word places the entry
before the data. Recorded rather than left for a reader to reconstruct.

## Confirmation

Every figure was re-derived three times: by the probe's report path, by an
independent agent parsing `realism.jsonl` with its own code and its own Wilson
implementation, and by hand afterwards. All three agree exactly, including the
86-of-86 distinct-triple check.

Working:
[`notebook/2026-08-18-n5-the-probe-ran-and-the-headline-prediction-was-wrong.md`](../../../notebook/2026-08-18-n5-the-probe-ran-and-the-headline-prediction-was-wrong.md).
