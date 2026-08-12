# The first forecast: five of six, and the miss is in the good direction

**2026-08-12.** Outcome for
[the prediction registered before the run](2026-08-12-first-forecast-prediction.md).
Track K6 / task #43. 73 cases, 1 repeat, Haiku, separate checkpoint from the
plain trigger runs. Base rate 18/73 = 0.247.

## Scoring the bands

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | The forecast discriminates | resolution ≥ 0.10 | **0.1687** | ✅ |
| 2 | Beats always answering the base rate | Brier skill score > 0 | **+0.8278** | ✅ |
| 3 | Distinct values used | 5–12 | **17** | ❌ |
| 4 | Overconfident at the extremes | ≥ 60% outside [0.1, 0.9] | **67.1%** (49/73) | ✅ |
| 5 | Smoothed calibration error | 0.05–0.20 | **0.0579** | ✅ |
| 6 | Forecast returned when asked | ≥ 95% | **100%** (73/73) | ✅ |

**Five of six.** Brier 0.0320, reliability 0.0149, uncertainty 0.1858, binned
ECE(10) 0.0673.

## The miss, and it is not the miss I predicted

I wrote that prediction 3 carried two-thirds of my exposure and that I expected
to be wrong *low* — a model that already knows the answer having little reason to
spread, coming back at 3 distinct values and rendering 1, 2 and 5
uninterpretable.

It came back at **17**, above the band, not below it:

```
0.0  0.01  0.02  0.05  0.1  0.15  0.2  0.25  0.35
0.7  0.75  0.8  0.85  0.88  0.92  0.93  0.95
```

So the failure mode the whole prediction was built around — *a binary decision
re-encoded as two constants* — did not happen, and predictions 1, 2 and 5 are
interpretable. **The band was wrong and the reasoning behind it was wrong in a
way that mattered less than the reasoning said it would.** Stating that plainly
is the point of writing the band down.

## What the numbers say

**Resolution 0.1687 against uncertainty 0.1858.** Resolution is bounded above by
uncertainty, so the forecast captured **91% of the discriminable variance in the
question set**. That is the number that says it is forecasting rather than
hedging, and it is the number I put first in the report for exactly this reason.

**The reliability curve is close to a step function, and it is honest about it:**

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

Every bin at or above 0.6 resolved to 1.000 and every bin below 0.3 resolved at
or under 0.2. **Prediction 4 was right and it was a prediction against the tool's
usefulness**: 67% of forecasts sit outside [0.1, 0.9], the middle is nearly
empty, and the one forecast at 0.35 was wrong. The distribution has 17 values but
it is bimodal — the spread is *within* the two modes, not between them.

So the honest reading is in between the two failure modes I described. It is not
two constants wearing a probability's clothes, and it is not a graded belief
either. **It is a confident binary with fine-grained hedging inside each mode**,
and the fine grain is where the calibration error of 0.0579 comes from being
small.

## What this does not license

**One repeat.** Firing on this run reads precision 1.000 / recall 0.889 / FPR
0.000, against the five-repeat baseline of 0.942 / 0.878 / 0.018 (precision range
0.889–1.000). Consistent, and **not evidence that asking for a forecast improved
firing** — a single draw cannot say that, which is the lesson from routing
earlier today. Routing here reads 0.714, one draw from a distribution measured at
0.686 ± 0.108.

**No skill was in context.** This is a baseline for elicited confidence and
nothing else. Whether a decision procedure moves the forecast is Track L.

**The set may be too easy for this to generalise.** The firing decision is nearly
perfect on these 73 items, and a well-resolved forecast about a question you can
already answer is the easy case. The number to watch is whether resolution
survives on a set where firing itself is closer to 0.7.

## For Track K6

`stats/calibration.py` was written in the first week, property-tested at 100%
line and branch coverage, and had **never been called by anything** until this
run. It is now called, and the Murphy decomposition earned its place in the
report: Brier alone (0.0320) would have looked equally good for a hedging
forecaster, and resolution is what separated them.

K6 ranks *elicited confidence* above `ledger.md` on published evidence — the only
candidate whose parent intervention has medium-to-large controlled effects in
humans. This run says the elicitation works mechanically on our stack. It says
nothing yet about whether it improves a decision.
