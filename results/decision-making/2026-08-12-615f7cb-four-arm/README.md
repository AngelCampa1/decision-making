# Track M4 — four separate skills instead of one bundle, 5 repeats

**2026-08-12.** 73 cases × 5 repeats = 365 isolated `claude -p` calls, Haiku,
0 unparseable, 0 isolation failures. Code at `615f7cb`.

The comparison arm is [`../2026-08-12-40b6ba5/`](../2026-08-12-40b6ba5/), the
shipped one-entry bundle at the same 73 cases and the same 5 repeats. It was not
re-run.

## What varied, and what did not

The four descriptions were **derived, not written**, by
`decision_evals.unbundle`: condition and product verbatim from that procedure's
router-table row, opener and exclusions verbatim from the bundle's own
`description` field and given to all four unchanged. A test asserts that no word
appears in any composed description that is not already in the bundle, with one
declared exception — the connective *"Produces"*, identical across all four.

So the four descriptions are the one description's parts, redistributed, and the
only thing that varies is **how many entries the model chooses between**.

## Results

| | one entry | four entries |
|---|---|---|
| precision | 0.942 ± 0.039 | **1.000 ± 0.000** |
| recall | **0.878 ± 0.025** | 0.800 ± 0.063 |
| false-positive rate | 0.018 ± 0.013 | **0.000 ± 0.000** |
| routing accuracy | 0.686 ± 0.108 | **0.786 ± 0.051** |

Per-item correctness (`fired == should_fire`), 73 paired items:

| set | one | four | items differing | paired Wilcoxon |
|---|---|---|---|---|
| **all 73** | 0.956 | 0.951 | 8 — 4 each way | **p = 0.83** |
| 55 negatives | 0.982 | 1.000 | 2, both favour four | p = 0.18 |
| 18 positives | 0.878 | 0.800 | 6, 4 favour one | p = 0.21 |

**The arms are indistinguishable on firing accuracy.** The sub-splits point
opposite ways and cancel.

## Routing is reported descriptively and carries no p-value

Pre-registered that way: 14 labelled items cannot reject at any useful effect
size — `p_discordant` = 0.157 from sampling noise alone, and exact McNemar's real
size at n=14 is 0.0015. See
[`../../../notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md`](../../../notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).

The **item-level** pattern is the stronger evidence, because the items were named
in advance. Two router-table defects were diagnosed from traces that morning, and
both improve in the arm that has no table:

| item | defect | one | four |
|---|---|---|---|
| `p07` | `cascade`/`timing` collide on *order* vs *when* | 1/5 | **5/5** |
| `p03` | "advice" appears only in `fit`'s row | 1/5 | **3/5** |
| `p06` | two routes defensible off the table | 0/5 | **3/5** |
| `x-n20` | — | **4/5** | 0/5 |

`x-n20` is the largest per-item regression in the run and wants a maintainer's
eye, alongside `x-n21`/`x-n22`, whose labels were already in question.

## The trade is structural, not incidental

With four entries, **declining to name a tool is declining to fire** — the two
decisions are one act, where the one-entry arm can fire and then fail to route.
So the four-entry arm never fires on a message it cannot confidently route: its
false positives vanish (`n07` 2/5 → 0/5, `n11` 3/5 → 0/5) and its misses grow
(`x-n20` 5/5 → 1/5, `p03` and `p12` 5/5 → 3/5).

Neither arm dominates. Which is better depends on whether a **missed decision**
or an **unwanted interruption** is the more expensive error — a judgement this
repository has never written down.

## Caveats

- **Nothing here bears on n=202.** Four is four. The published shadowing result
  is not contradicted; the extrapolation from it down to four is not supported.
- **One model tier, one instrument.** Haiku, and a proxy: the model is shown
  descriptions and asked whether it would fire, not observed firing mid-task.
- **The four-entry arm has no bodies.** A real four-skill install also means four
  bodies and four sets of frontmatter. The trigger instrument never sees a body,
  so this measures the *selection* half of shadowing only.
- Recall on either arm should be quoted both ways: `x-n21` and `x-n22` are
  maintainer-written positives that essentially never fire in either arm.

## Columns

`case`, `repeat` (0–4), `fired`, `procedure` (the tool named), `p_fire` (null),
`should_fire`, `route`.

## Reproducing

```bash
python scripts/run_triggers.py --arm four --repeats 5
```

**Answer key:** [`datasets/triggers/decision-making.yaml`](../../../datasets/triggers/decision-making.yaml) **v1**. Not comparable with a v2 run: on 2026-08-13 one turn moved from the positives to the negatives and recall rose on every arm on disk with no call re-made.
Prediction: [`notebook/2026-08-12-m4-prediction-one-entry-against-four.md`](../../../notebook/2026-08-12-m4-prediction-one-entry-against-four.md).
Outcome: [`notebook/2026-08-12-m4-shadowing-did-not-appear-at-four.md`](../../../notebook/2026-08-12-m4-shadowing-did-not-appear-at-four.md).
