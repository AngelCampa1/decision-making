# Track M5 — the same four procedures across two entries, 5 repeats

**2026-08-12.** 73 cases × 5 repeats = **365 isolated `claude -p` calls**, Haiku,
0 unparseable, 0 isolation failures. Code at `c2673c5`.

The comparison arms are [`../2026-08-12-40b6ba5/`](../2026-08-12-40b6ba5/) (the
shipped one-entry bundle) and
[`../2026-08-12-615f7cb-four-arm/`](../2026-08-12-615f7cb-four-arm/) (four
entries), both at the same 73 cases and 5 repeats. Neither was re-run.

## What varied

`decision_evals.unbundle.entries()` partitions the router table **contiguously
and evenly**, so the arm is a function of `n` alone: at n=2 it produces
`ledger-fit` and `cascade-timing`. Conditions and products are the table's own,
joined by *"or"* — the single word this module adds, present in every
multi-procedure entry and therefore unable to differentiate them.

## Results

| | n=1 | **n=2** | n=4 |
|---|---|---|---|
| precision | 0.940 | **1.000 ± 0.000** | 1.000 |
| recall | 0.878 | **0.756 ± 0.030** | 0.800 |
| false-positive rate | 0.018 | **0.000 ± 0.000** | 0.000 |
| firing accuracy | 0.956 | **0.940 ± 0.008** | 0.951 |

Per-item correctness (`fired == should_fire`), 73 paired items against n=1:
**7 differ, 4 favour n=1 and 3 favour n=2, paired Wilcoxon p = 0.497.**

**The false-positive floor is reached at two entries.** M4 explained its zero
structurally — with separate entries, declining to name a tool *is* declining to
fire. That mechanism is not an artefact of four-way choice: it appears at two, at
0.000, in all five repeats.

**Recall is not monotone in entry count** (0.878 → 0.756 → 0.800) and this run
does not claim it is. n=2 is also the arm with the worst prose — mechanical
joining reads worse than a human would write, which was
[registered as a confound before the run](../../../notebook/2026-08-12-m5-prediction-where-the-curve-turns.md).
The clean contrast in this curve remains n=1 against n=4.

## Routing is reported as `covers`, and not on the same axis as the other arms

Exact-name routing accuracy is undefined for this arm: it offers `ledger-fit`
and the labels say `ledger`, so every comparison fails whatever the model does.
`routing_is_by_name` now refuses to print it.

| denominator | value |
|---|---|
| all labelled calls, non-answer counts as a miss | **0.743 ± 0.081** |
| labelled calls where the arm fired and named something | 0.895 ± 0.073 |

The first is reported, because it is the denominator the n=1 and n=4 arms use.
**Chance here is 0.500 against a four-way arm's 0.250, so this must not be
plotted on one curve with 0.686 and 0.786.**

> **Amended 2026-08-13 after [M6](../2026-08-13-82b4ab8-m6-pairing/).** This
> number stands as measured and **loses its interpretation.** M6 ran the same
> four procedures at the same entry count under a different partition —
> `ledger-cascade` / `fit-timing`, word-multiset identical to this arm — and
> `covers` read **0.857**. The model did not route better; the entry boundaries
> moved underneath it, so a different confusion was forgiven. `covers` is a
> property of the partition as much as of the model, and 0.743 is *this
> partition's* number rather than an estimate of how well a two-entry arm
> routes. Firing was unaffected (p = 0.273), so everything above this section is
> untouched.

## Reliability

ICC **0.833**; 3 of 73 items show any scatter across five repeats;
`repeats_for_reliability` asks for 1 repeat at r=0.8 and 2 at r=0.9. Separately,
a voided earlier run of this arm (parser defect, firing unaffected) agrees with
this one on **355 of 365 firing decisions — 97.3%**. Future arms can run 2
repeats rather than 5.

## Caveats

- **One model tier, one instrument.** Haiku, and a proxy: the model is shown
  descriptions and asked whether it would fire, not observed firing mid-task.
- **No bodies.** A real two-skill install also means two bodies and two sets of
  frontmatter. This measures the *selection* half only.
- **Which two procedures are paired is fixed, not chosen.** Pairing `cascade`
  with `timing` is a hypothesis about their overlap; M6 is where that varies.
- Recall on every arm should be quoted both ways: `x-n21` and `x-n22` are
  maintainer-written positives that essentially never fire in any arm.

## Columns

`case`, `repeat` (0–4), `fired`, `procedure` (the entry named), `covers`,
`p_fire` (null), `should_fire`, `route`, `raw`.

## Reproducing

```bash
python scripts/run_triggers.py --entries 2 --repeats 5
```

Prediction: [`notebook/2026-08-12-m5-prediction-where-the-curve-turns.md`](../../../notebook/2026-08-12-m5-prediction-where-the-curve-turns.md).
Outcome: [`notebook/2026-08-12-m5-the-floor-is-at-two-and-the-recall-curve-is-not-monotone.md`](../../../notebook/2026-08-12-m5-the-floor-is-at-two-and-the-recall-curve-is-not-monotone.md).
