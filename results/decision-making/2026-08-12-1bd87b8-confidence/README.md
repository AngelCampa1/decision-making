# Elicited confidence — decision-making v0.2.1, 1 repeat

**2026-08-12.** 73 cases × 1 repeat = 73 isolated `claude -p` calls, Haiku,
0 unparseable, 0 isolation failures. Code at `1bd87b8`.

Each case is asked for `p_fire` — **the model's probability that the tool should
be invoked** — alongside the hard fire/don't-fire decision. Scored against the
case's membership label, which is why the trigger set can carry a forecast
without anyone ruling a response wrong.

A confidence run and a plain run are **two runs**, on separate checkpoints. This
is not the 5-repeat file in
[`../2026-08-12-40b6ba5/`](../2026-08-12-40b6ba5/) with a column added.

## The forecast

Base rate 18/73 = 0.247.

| | |
|---|---|
| forecasts returned | 73/73 |
| distinct values used | 17 |
| **resolution** | **0.1687** — higher is better; this is the one to read |
| uncertainty | 0.1858 — a property of the question set, not the model |
| reliability | 0.0149 — lower is better |
| Brier | 0.0320 |
| Brier skill score | +0.8278 vs always answering the base rate |
| smoothed calibration error | 0.0579 |
| binned ECE (10) | 0.0673 |

**Resolution against uncertainty is the headline: 0.1687 of a possible 0.1858, so
the forecast captured 91% of the discriminable variance.** Brier alone would look
equally good for a forecaster that hedged everything at the base rate; resolution
is what separates them, which is why the Murphy decomposition is reported rather
than a single score.

### Reliability curve

| stated | n | observed |
|---|---|---|
| [0.0, 0.1) | 45 | 0.000 |
| [0.1, 0.2) | 6 | 0.167 |
| [0.2, 0.3) | 5 | 0.200 |
| [0.3, 0.4) | 1 | 0.000 |
| [0.6, 0.7) | 1 | 1.000 |
| [0.7, 0.8) | 1 | 1.000 |
| [0.8, 0.9) | 10 | 1.000 |
| [0.9, 1.0) | 4 | 1.000 |

**67% of forecasts fall outside [0.1, 0.9] and the middle is nearly empty.** The
distribution has 17 distinct values but it is bimodal — the spread is *within*
the two modes. Read it as a confident binary with fine-grained hedging inside
each mode, not as a graded belief.

## Firing and routing, at one repeat

| | this run | 5-repeat baseline |
|---|---|---|
| precision | 1.000 | 0.942 (range 0.889–1.000) |
| recall | 0.889 | 0.878 (range 0.833–0.889) |
| false-positive rate | 0.000 | 0.018 (range 0.000–0.036) |
| routing accuracy | 0.714 | 0.686 (sd 0.108) |

Every figure sits inside the baseline's observed range. **This is not evidence
that asking for a forecast improved firing** — one draw cannot say that, and
routing at 14 items cannot say it at any number of draws (see
[`notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md`](../../../notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md)).

Misses: `x-n21`, `x-n22` — the same two as every other run. **Recall is 0.889
with them and 1.000 without.** Any recall figure from this file should be given
both ways.

## Caveats

- **No skill was in context.** This is a baseline for elicited confidence and
  nothing else. Whether a decision procedure moves the forecast is Track L.
- **The set may be too easy.** Firing is near-perfect on these 73 items, and a
  well-resolved forecast about a question you can already answer is the easy
  case. Watch whether resolution survives where firing is nearer 0.7.
- **Still a proxy.** The model is shown one skill description and asked whether
  it would fire; in the real harness that description sits among others, in a
  longer context, mid-task.

## Columns

`case`, `repeat` (0), `fired`, `procedure`, `p_fire`, `should_fire`, `route`.

## Reproducing

```bash
python scripts/run_triggers.py --confidence
```

Labels: [`datasets/triggers/decision-making.yaml`](../../../datasets/triggers/decision-making.yaml).
Prediction: [`notebook/2026-08-12-first-forecast-prediction.md`](../../../notebook/2026-08-12-first-forecast-prediction.md).
Outcome: [`notebook/2026-08-12-the-first-forecast-outcome.md`](../../../notebook/2026-08-12-the-first-forecast-outcome.md).
