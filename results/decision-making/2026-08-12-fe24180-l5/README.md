# Track L5 — what each part of a description buys

**2026-08-12.** 3 arms × 73 cases × 5 repeats = **1,095 isolated `claude -p`
calls**, Haiku, 0 unparseable, 0 isolation failures. Code at `fe24180`.

The `full` control is [`../2026-08-12-40b6ba5/`](../2026-08-12-40b6ba5/), the
shipped description at the same cases and repeats. It was not re-run.

## The arms are deletions, not rewrites

The shipped description has three parts: an **opener** (*"Use when someone is
trying to decide something…"*), a **routing summary** (*"Routes to one of four
procedures depending on what is actually hard…"*), and **exclusions** (*"Do not
use for factual lookups…"*). Each arm deletes one or two. A parametrised test
asserts no arm contains a word the shipped description does not.

## Results

| arm | parts | length | FPR | recall | precision | routing |
|---|---|---|---|---|---|---|
| `opener-only` | O | 206 ch | **0.113** ± 0.008 | **0.956** ± 0.025 | 0.735 | 0.429 |
| `no-exclusions` | O + R | 385 ch | 0.055 ± 0.013 | 0.911 ± 0.030 | 0.846 | 0.743 |
| `full` *(shipped)* | O + R + E | 549 ch | 0.018 ± 0.013 | 0.878 ± 0.025 | 0.942 | 0.686 |
| `no-opener` | R + E | 342 ch | **0.000** ± 0.000 | 0.867 ± 0.050 | **1.000** | 0.671 |

Each adjacent pair differs in exactly one part, so each part's contribution to
false-firing reads off directly:

| part | contribution to FPR |
|---|---|
| routing summary | **−5.8pp** |
| exclusions | **−3.7pp** |
| opener | **+1.8pp** — it costs |

**The exclusion list is not decoration**: deleting it triples the false-positive
rate. **The opener — the sentence with all the illustrative quotes — is the only
part that makes the skill worse**, and deleting it gives precision 1.000 for one
point of recall.

## It is content, not length

FPR is **not monotone in length**: 342 characters (`no-opener`) gives 0.000 and
385 (`no-exclusions`) gives 0.055. The design deletes named parts rather than
truncating, so the length explanation is ruled out by the two mid-length arms.

## Statistics

Paired Wilcoxon over per-item fire rates:

| contrast | 55 negatives | 18 positives |
|---|---|---|
| `opener-only` vs `full` | 7 differ, **7 up, 0 down, p = 0.016** | 3 differ, p = 0.11 |
| `no-exclusions` vs `full` | 4 differ, **4 up, 0 down**, p = 0.068 | 3 differ, p = 0.10 |
| `no-opener` vs `full` | 2 differ, **0 up, 2 down**, p = 0.18 | 4 differ, p = 0.72 |

**Only one contrast clears 0.05, and every contrast is perfectly one-directional
on the negatives** — no item in any arm moves against the trend. That unanimity
across three independent contrasts is the evidence; the p-values are what 55
items at a 0.018 base rate can buy.

**Do not quote combined accuracy.** FPR and recall move oppositely and cancel. A
description change here does not make the skill better — it **moves it along a
precision/recall frontier**, and which point is wanted is an open product
decision.

## Routing is descriptive and carries no p-value

Pre-registered that way: 14 labelled items cannot reject. One sanity check is
worth reading — `opener-only` routes at **0.429** against the control's 0.686,
because its description does not list the four procedures. Strip what routing
depends on and routing collapses while firing *improves*, so the two outcomes are
not one measurement under two names.

## Caveats

- One model tier (Haiku), one instrument. The model is shown a description and
  asked whether it would fire — not observed firing mid-task among other skills.
- Recall should be quoted both ways on every arm: `x-n21` and `x-n22` are
  maintainer-written positives that essentially never fire.
- **No arm is being adopted.** One run does not license editing the shipped
  skill; these are Track L variant candidates.

## Columns

`case`, `repeat` (0–4), `fired`, `procedure`, `covers`, `p_fire` (null),
`should_fire`, `route`.

## Reproducing

```bash
python scripts/run_triggers.py --description no-opener --repeats 5
```

Prediction: [`notebook/2026-08-12-l5-prediction-what-each-part-of-a-description-buys.md`](../../../notebook/2026-08-12-l5-prediction-what-each-part-of-a-description-buys.md).
Outcome: [`notebook/2026-08-12-l5-the-boilerplate-does-the-work.md`](../../../notebook/2026-08-12-l5-the-boilerplate-does-the-work.md).
