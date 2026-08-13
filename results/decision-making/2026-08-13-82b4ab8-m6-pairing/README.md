# Track M6 — which procedures share an entry, at fixed count

**2026-08-13.** 73 cases × 2 repeats = **146 isolated `claude -p` calls**, Haiku,
0 unparseable, 0 isolation failures. Code at `82b4ab8`.

Two repeats rather than five on M5's reliability finding (ICC 0.833). This run's
ICC is **0.852** with 1 of 73 items showing any scatter, which vindicates it.

The comparison arm is
[`../2026-08-12-c2673c5-m5-two-entries/`](../2026-08-12-c2673c5-m5-two-entries/)
— the same four procedures at the same entry count under the contiguous
partition. It was not re-run.

## What varied: the grouping, and nothing else

| arm | entries |
|---|---|
| M5 | `ledger-fit`, `cascade-timing` (contiguous in table order) |
| **M6** | `ledger-cascade`, `fit-timing` |

The two arms are **word-multiset identical** — the same four conditions and four
products merged two ways, the shared opener and exclusions unchanged, `or` the
only connective either adds. Clause order inside an entry stays table order
whatever the grouping. A test asserts the multiset equality.

## Results

| | M5 contiguous | **M6 split** |
|---|---|---|
| firing accuracy | 0.940 | **0.952** |
| precision | 1.000 | 1.000 |
| recall | 0.756 | 0.806 |
| false-positive rate | 0.000 | 0.000 |
| `covers`, all labelled calls | 0.743 | **0.857** |
| `covers`, calls that fired | 0.897 | **1.000** |

Firing, 73 paired items: **4 differ, paired Wilcoxon p = 0.273.**

## The routing number is a property of the partition, not of the model

**This is the run's result and it is a negative one about the measure.**

`covers` rose when the grouping changed, and the raw answers show the model did
not change its mind. `p06` is labelled `fit`; in both arms the model reaches for
something *timing*-flavoured. Under M5's grouping `timing` sits with `cascade`,
so that answer falls outside the entry covering `fit` and scores 0.2. Under M6's
grouping `timing` sits with `fit`, so the identical instinct scores 1.0.

| item | label | M5 | M6 |
|---|---|---|---|
| `p06` | `fit` | 0.2 | **1.0** |
| `p03` | `ledger` | 0.6 | **1.0** |
| `p04` | `fit` | 0.8 | **1.0** |
| `p09` | `cascade` | 0.8 | **1.0** |
| `x-n23` | `timing` | 0.8 | **1.0** |

So `covers` is *"did the answer fall inside whichever entry contains the
label"*, and **which confusions that forgives is a property of the partition.**
It is not comparable across `n` (chance moves) and — this run's finding — **not
comparable across groupings at the same `n` either.** M5's 0.743 stands as
measured and cannot be read as how well a two-entry arm routes.

> **Extended 2026-08-13 by [M6b](../2026-08-13-5ccedb9-m6b-third-partition/).**
> The third and final partition reads **0.571**, so the complete set at n=2 is
> 0.571 / 0.743 / 0.857 — a **28.6-point range** on identical vocabulary. And
> the mechanism is stronger than "boundaries forgive confusions": on `p01` and
> `p02`, both labelled `ledger`, the third arm unanimously names the entry that
> does **not** contain `ledger`. A merged entry does not inherit its parts'
> pull.

`p07`, the item the `cascade`/`timing` collision was diagnosed on and the
per-item diagnostic named before the run, is **1.0 in both arms**. Every arm
that does not show the model the router table gets it right. The collision is a
defect of the table, not of the descriptions.

## Caveats

- **One model tier, one instrument.** Haiku, and a proxy: the model is shown
  descriptions and asked whether it would fire.
- **Two repeats.** Justified by ICC, and it does coarsen per-item rates to
  {0, 0.5, 1} against the five-repeat arm's finer grid. The paired test is still
  exact; its resolution is lower.
- **One alternative pairing, not all three.** `ledger-timing`/`fit-cascade` was
  not run.
- Recall should be quoted both ways: `x-n03`, `x-n20`, `x-n21` and `x-n22` are
  maintainer-written positives that no n=2 arm fires on.

## Columns

`case`, `repeat` (0–1), `fired`, `procedure` (the entry named), `covers`,
`p_fire` (null), `should_fire`, `route`, `raw`.

## Reproducing

```bash
python scripts/run_triggers.py --pairing "ledger+cascade,fit+timing" --repeats 2
```

Prediction: [`notebook/2026-08-12-m6-prediction-the-collision-was-inside-the-entry.md`](../../../notebook/2026-08-12-m6-prediction-the-collision-was-inside-the-entry.md).
Outcome: [`notebook/2026-08-12-m6-covers-went-up-and-the-measure-does-not-survive-it.md`](../../../notebook/2026-08-12-m6-covers-went-up-and-the-measure-does-not-survive-it.md).
