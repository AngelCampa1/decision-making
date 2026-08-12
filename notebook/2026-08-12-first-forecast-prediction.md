# Prediction: the first forecast this repo has asked for

**2026-08-12**, written before the run. Track K6 / task #43.

`stats/calibration.py` was written in the first week, property-tested to 100%
line and branch coverage, and has never been called by anything. This is the run
that calls it.

## What is being asked

Each trigger case gets `p_fire` alongside the hard `fire` decision: **the
model's probability that the tool should be invoked**. Scored against the case's
own label, which is a membership label rather than a judgement about answer
quality — the reason the trigger set can carry a forecast without anyone ruling a
response wrong.

Base rate on the set is 18/73 = **0.247**. Separate checkpoint; a confidence run
and a plain run are two runs.

## Predictions

| # | Prediction | Band |
|---|---|---|
| 1 | The forecast discriminates | resolution ≥ 0.10 |
| 2 | It beats always answering the base rate | Brier skill score > 0 |
| 3 | Distinct values used | 5–12 |
| 4 | It is overconfident at the extremes | ≥ 60% of forecasts outside [0.1, 0.9] |
| 5 | Smoothed calibration error | 0.05–0.20 |
| 6 | Forecast returned when asked | ≥ 95% of calls |

**1 and 2 are the ones that matter, and 1 is the one that can embarrass the
metric.** A model answering 0.9 to everything it fires on and 0.05 to everything
else scores well on Brier and on calibration error while doing no forecasting at
all — it has re-encoded a binary decision as two constants. That is why
resolution leads the report and why the distinct-value count is printed. If
prediction 3 comes back as 2, predictions 1, 2 and 5 are uninterpretable
regardless of their values.

**4 is a prediction against the tool being useful.** Verbalized confidence from
RLHF-trained models is the citation behind this whole idea
([arXiv:2305.14975](https://arxiv.org/abs/2305.14975)) and it reports better
calibration than the conditional probabilities, not good calibration. If almost
everything lands at 0.05 or 0.95, then `p_fire` is a decision wearing a
probability's clothes, and *elicited confidence* as a skill candidate needs the
question changed rather than the prompt tuned.

## The thing this cannot tell us

Whether a decision *procedure* would improve the forecast. This is one call with
no skill in context, so it is a baseline and nothing else. Track L is where a
skill gets to move it.

## Where I expect to be wrong

**3.** I have said 5–12 distinct values because that is what a model asked for a
probability usually does. The firing decision on this set is close to perfect —
precision 1.000 in the second run — and a model that already knows the answer has
little reason to spread. Two-thirds of my exposure is on that one number, and if
it comes back at 3 the honest reading is that the set is too easy to elicit a
forecast from, not that the model cannot forecast.
