# Prediction: the pilot re-run, with the task actually set

**2026-08-12**, written before the run. Supersedes the A1 numbers in
[the pilot outcome](2026-08-12-a1-pilot-outcome.md) for `actions` and
`database`, which were void.

## What was wrong

The first pilot asked `database` for SQL without giving it a schema and asked
`actions` to call a function without giving it any functions. Both families
carry that material in the corpus — `schema_sql`, `function` — and the runner
never rendered it. Forty records, twenty items, all unanswerable.

It went unnoticed because the traces are *good*. Asked which countries' TV
channels air a Todd Casey cartoon, with no database in sight, the model said it
has no access to TV listings and suggested checking IMDb. That is the right
answer to the question it was asked. Nothing about it looks like a defect until
you go looking for the schema and find it was never sent.

`math` is unaffected — a word problem carries its own numbers. Which corrects
something I wrote this morning: `math` was not "the only family with a mechanical
key", it was the only family whose task was fully delivered.

## The re-run is two experiments at once

The system prompt for `math` is byte-identical to the first pilot's, and the
items are the same seeded sample. So those ten pairs are **a repeat of an
identical condition**, and the trigger runs have already shown that per-item
verdicts move between runs while aggregates hold. This gets a second data point
on that, for free, on a different instrument.

## Predictions

Bands fixed now.

| # | Prediction | Band |
|---|---|---|
| 1 | Every pair completes | 0 call failures, 0 isolation failures |
| 2 | Prompt tokens climb in every sharded conversation | 30/30 |
| 3 | `math`, both conditions, reproduces the first pilot's rate | within ±2 items of 9/10 |
| 4 | `math` per-item agreement with the first pilot | ≥ 16 of 20 records |
| 5 | `database` full-condition responses now contain SQL | ≥ 8/10 |
| 6 | `actions` full-condition responses now name the required function | ≥ 6/10 |
| 7 | `p_discordant` pooled over the two repaired families | ≥ 0.15 |

**5 and 6 are format-compliance predictions, not correctness ones**, and they are
the ones the run is for. If the repaired families still do not produce SQL and
function calls, the problem is the shared system prompt rather than the missing
context, and no amount of adjudication downstream will fix that.

**6 is lower than 5 on purpose.** The system prompt says "give your best final
answer" and says nothing about emitting a call. `database` has a strong
convention pulling towards SQL once a schema is present; `actions` has to be
inferred from the fact that functions were offered.

**7 is the number the whole pilot exists to produce.** On `math` it came out at
0.10 — near-ceiling, which arithmetically excludes the paper's 39% on that
family, because a paired difference cannot exceed the discordant share. If the
repaired families also land near zero, the A1 grid cannot detect the published
effect at any sample size and that is the finding, not a setback.

## Where I expect to be wrong

The last six prediction sets were wrong in the optimistic direction and the one
before this was not. The exposed guess here is **4**: I am predicting the repeat
agrees with the first run on at least 16 of 20, on the strength of `math` sitting
at ceiling. Ceilings are exactly where agreement is cheap, so a high number there
means less than it looks like, and I should not read it as the instrument being
stable.

No `--final-turn` on this run. Adding the closing instruction would make `math`
non-comparable with the first pilot, and the free repeat is worth more than
exercising a new flag.
