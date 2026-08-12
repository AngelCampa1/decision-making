# The closing turn worked, and made the measure worse

**2026-08-12.** Outcome for the re-run registered in
[the void entry](2026-08-12-the-actions-effect-was-the-scorer-reading-one-turn.md).
Track A1. 50 pairs, `--final-turn`, 385 generations, 0 call failures, 2110s.

## Scored as registered

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | Every pair completes | 0 failures | 0 | ✅ |
| 2 | `full` names every required function | 43–48/50 | **47/50** | ✅ |
| 3 | `sharded` names every required function | 40–48/50 | **3/50** | ❌ |
| 4 | `p_discordant` on naming | 0.04–0.20 | **0.880** | ❌ |
| 5 | direction | *no band, deliberately* | 44/44 favour `full` | — |

**`sharded` went from 23/50 to 3/50.** The fix made the number worse, and the
fix was correct.

## What the closing turn actually did

`sharded-BFCL/parallel_98`, eight turns:

| turn | what the model did |
|---|---|
| 0–2 | asked for the missing charge and distance |
| **3, 4, 5** | **emitted `calculate_electric_field_strength` three times, with arguments** |
| 6 | summarised the calculations in a table |
| 7 | *(the closing instruction)* **"Electric Field Strength Calculations — Final Summary"**, four results in N/C, a combined total |

The closing turn did exactly what it was written to do: a complete,
self-contained final answer, no further questions. **And a complete final answer
to a tool-use task is the results, not the name of the tool.** The function name
was in turns 3, 4 and 5 and had no business being in turn 7.

Meanwhile the `full` arm has **one** turn, which must both make the call and
report the answer, so the call text is necessarily in its final response. That is
why it reads 47/50 in both runs and is not moved by the flag at all.

## So the measure is structurally unable to read this family

Three configurations, one conclusion:

| run | measure | `full` | `sharded` | `p_discordant` |
|---|---|---|---|---|
| no closing turn | final response | 45/50 | 23/50 | 0.520 |
| **closing turn** | final response | **47/50** | **3/50** | **0.880** |
| no closing turn | anywhere in conversation | 45/50 | 47/50 | 0.120 |
| **closing turn** | anywhere in conversation | **47/50** | **49/50** | **0.080** |

Every final-response number tracks *how many turns the arm had to bury the name
in*. Every anywhere number says the two arms are within a couple of items of each
other. **Bands 3 and 4 are retired unscored for the second time today**, and the
`44/44 favour full` on the direction is worth nothing — I declined to put a band
on it, which was the one call I got right.

Two runs, 720 generations, and `actions` function-naming has produced no readable
comparison at any setting.

## The fix, and it was on the shelf the whole time

`CALL_FORMAT` in `evals/src/decision_evals/scorers/bfcl.py` asks the model to end
its reply with a JSON array of the calls to make. Combined with `--final-turn`
that puts the calls **in the final response by contract**, which:

1. makes the object the scorer reads the same in both arms, for a reason instead
   of by luck; and
2. enables **BFCL's own AST match** — the published metric — instead of a naming
   floor. This run parsed only 43 of 100 responses, below the 90% guard, so the
   AST half has been unreadable in every run so far.

**This is the run that was named as outstanding this morning and not done.** The
naming floor was adopted because "nothing in the run asks the model to emit a
parseable call", which was true and was fixable in one flag.

## Prediction for `--final-turn --call-format`, registered before it starts

50 pairs, 385 generations, new tag `actions-50-call`.

| # | Prediction | Band |
|---|---|---|
| 1 | Every pair completes | 0 call failures |
| 2 | **Parse rate clears the guard** | ≥ 90% of the 100 responses parse |
| 3 | `full` AST match | 30–45 / 50 |
| 4 | `sharded` AST match | **20–40 / 50** |
| 5 | `p_discordant` on AST match | **0.10–0.35** |
| 6 | Naming, final response, both arms | ≥ 45/50 each — the contract should make this stop discriminating |

**2 is the gate.** Below 90% the AST half is measuring format compliance again
and 3–5 are unreadable, exactly as they have been twice. If it comes back at 60%,
`actions` is not a venue this harness can grade and the corpus decision is forced.

**5 is the run.** The two families measured so far give `p_discordant` 0.000
(`math`) and 0.080–0.120 (`actions`, on the only measure that reads both arms).
At 0.08 over 50 pairs the expected discordant count is 4 and exact one-sided
McNemar needs 5 all one way — the arithmetic that
[closed routing at fourteen items](2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).
So I am predicting the band **and** predicting it will not be enough, which is a
corpus-size finding rather than an effect.

**Where I expect to be wrong: 4.** The AST match demands every argument, not just
the name, and the sharded arm has to carry argument values across six turns.
Naming said the arms were level; the full metric may not. If `sharded` comes back
under 15 while `full` is over 35, that is the first genuinely discordant signal
this track has produced and it should be treated with the suspicion the last two
earned.
