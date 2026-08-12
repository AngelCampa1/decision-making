# Trigger measurement — decision-making v0.2.1, 5 repeats

**2026-08-12.** 73 cases × 5 repeats = 365 isolated `claude -p` calls, Haiku,
0 unparseable, 0 isolation failures.

Published because the run is complete. `results/triggers/` is the live,
resumable checkpoint and is not committed; this is the copy the numbers were
computed from.

| | mean | sd | range |
|---|---|---|---|
| precision | 0.942 | 0.039 | 0.889–1.000 |
| recall | 0.878 | 0.025 | 0.833–0.889 |
| false-positive rate | 0.018 | 0.013 | 0.000–0.036 |
| routing accuracy | 0.686 | 0.108 | 0.571–0.857 |

**Recall is 0.878 with `x-n21` and `x-n22` in the set and 0.988 without them.**
Both are positives the maintainer wrote, both fire 0/5, and they are the set's
only misses. Any recall figure taken from this file should be given both ways.

**This is a proxy.** The model is shown one skill description and asked whether
it would fire. In the real harness that description sits among others, in a
longer context, mid-task.

## Columns

`case`, `repeat` (0–4), `fired`, `procedure`, `p_fire` (null — this run did
not elicit one), `should_fire`, `route`.

## Reproducing

```bash
python scripts/run_triggers.py --repeats 5
```

Labels: [`datasets/triggers/decision-making.yaml`](../../../datasets/triggers/decision-making.yaml).
Write-up: [`notebook/2026-08-12-five-repeats-firing-is-stable-routing-is-not.md`](../../../notebook/2026-08-12-five-repeats-firing-is-stable-routing-is-not.md).
