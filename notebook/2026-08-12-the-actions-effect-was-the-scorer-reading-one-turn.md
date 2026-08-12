# The `actions` effect was the scorer reading one turn of seven

**2026-08-12.** Outcome for
[the 50-pair prediction](2026-08-12-actions-expansion-prediction.md). Track A1.
100 records, 0 errors, 0 isolation failures, 335 generations, Haiku.

**The headline result is void and the reason is an instrument defect I had
already written the fix for and did not switch on.** The numbers are below
anyway, scored as registered, because deleting a wrong measurement is worse than
publishing it with its correction.

## Scored as registered

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | Every pair completes | 0 failures | 0 errors, 0 isolation failures | ✅ |
| 2 | Prompt tokens climb in every sharded conversation | 50/50 | **50/50** | ✅ |
| 3 | `full` names every required function | ≥ 45/50 | **45/50** | ✅ |
| 4 | `sharded` names every required function | 38–47/50 | **23/50** | ❌ |
| 5 | `p_discordant` on function-naming | 0.08–0.25 | **0.520** | ❌ |
| 6 | Discordant pairs favouring `full` | ≥ 70% | **92.3%** (24/26) | ✅ |

Read at face value that is a large, clean replication of the sharded-context
effect: `full` 45/50 against `sharded` 23/50, discordance concentrated 24-to-2 in
the paper's direction. It is not real.

## What went wrong

`actions_report` in `scripts/analyse_pilot.py:355` scores naming against
`record.final_response`:

```python
hits = [name for name in dict.fromkeys(wanted) if name in record.final_response]
```

The `full` arm has **one turn**, so its final response is its whole answer. The
`sharded` arm has **four to ten** (median 6), and this run was launched with
**`--final-turn` off** — there was no closing instruction, so the sharded arm's
"final response" is its answer to the *last shard*, a sub-question with no reason
to restate function names it named three turns earlier.

Recompute, crediting a name anywhere in the conversation:

| measure | both | full only | sharded only | neither | `p_discordant` | favouring `full` |
|---|---|---|---|---|---|---|
| **final response only** | 21 | **24** | 2 | 3 | **0.520** | 24/26 |
| **anywhere in conversation** | 43 | 2 | **4** | 1 | **0.120** | 2/6 |

`full` 45 → 45. `sharded` **23 → 47**. **The direction reverses.** Twenty-four of
the twenty-six discordant pairs — every single one of the "full wins" cases — are
sharded records that named the function and then stopped repeating it.

## The fix existed and was not used

`FINAL_TURN` was added to `evals/src/decision_evals/sharded.py` earlier today for
exactly this: a closing turn asking for *"your final answer now, complete and
self-contained"*, sent to both conditions so their final responses are
comparable. The run plan even prints its state:

```
closing instruction: no
```

It printed that line and I did not read it. This is the same shape as the 40 void
records this morning — a run that completes cleanly, produces plausible numbers,
and measures something other than the thing.

## Neither number can be the fix

The tempting repair is to score "named anywhere". **It is biased the opposite
way and by roughly the same mechanism.** The sharded arm emits five to seven
turns of text against the full arm's one, so more surface for a substring to land
on. Final-response-only penalises `sharded` for not repeating itself; anywhere
rewards it for having more chances. Both are artefacts of turn count, which is
the independent variable.

The closing turn is the actual fix, because it makes both arms produce one
final, self-contained answer and the scorer then reads the same object in both.

## What is registered, and what is retired

**Bands 4, 5 and 6 are retired unscored.** They were computed on a measurement
that cannot support them, and the ✅ on 6 is worth no more than the ❌ on 5 — all
three are reading turn count. Bands 1, 2 and 3 stand: the harness ran clean,
context accumulated in every conversation, and `full` at 45/50 is unaffected
because the full arm has one turn either way.

**The re-run is 50 pairs with `--final-turn`: 50 single-turn calls plus 50
conversations totalling 335 turns, 385 generations in all** — 50 more than this
run, the closing turn on each conversation. New tag, new checkpoint, because
changing the closing instruction changes the item and the resume guard refuses to
mix them.

**Prediction for the re-run, registered here before it starts:**

| # | Prediction | Band |
|---|---|---|
| 1 | Every pair completes | 0 failures |
| 2 | `full` names every required function | 43–48 / 50 |
| 3 | `sharded` names every required function | **40–48 / 50** |
| 4 | `p_discordant` on naming | **0.04–0.20** |
| 5 | Discordant pairs favouring `full` | no band — the count will be too small to have a direction |

**3 and 4 are the run.** The corrected read of *this* run says 47/50 and 0.120,
and if the closing turn reproduces something near that, `actions` joins `math` as
a family with too little discordance to power anything and Track A1 needs a
corpus decision rather than more pairs. **I am predicting against my own
replication.**

Band 5 has no number on purpose. At `p_discordant` ≈ 0.12 the expected discordant
count is 6, and exact one-sided McNemar needs 5 all one way — the same arithmetic
that [closed routing at fourteen items](2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).
Fifty pairs is not obviously enough here either, and saying so before the run is
cheaper than discovering it after.

## Appended after committing: one trace, and why `actions` is the exposed family

`sharded-BFCL/parallel_62`, six turns, scored `full` names it / `sharded`
MISSING:

| turn | what the model did |
|---|---|
| 0 | asked for the equations — the first shard gave none |
| 1 | **emitted `algebra.quadratic_roots` with a=3, b=4, c=2** |
| 2 | **emitted `algebra.quadratic_roots` with a=5, b=-7, c=3** |
| 3 | *"You're right to clarify! I actually did use the correct coefficients…"* |
| 4 | *"Absolutely! You're correct, and I did use the right coefficients…"* |
| 5 | *"You're absolutely right! I used the correct definitions…"* |

**The work finished on turn 2 and the last three shards are restatements the
model answered with agreement.** The final response is a coefficient table with
no function name in it. Scored on the final response this is a total failure;
read as a conversation it is a clean success on turn 2.

That is why `actions` is the exposed family and `math` is not. **I re-checked
`math` under this defect and it is unaffected** — 10/10 both arms correct,
`p_discordant` still 0.000. GSM8K's last shard *is* the final question ("how many
did Rory retrieve?"), so the last turn's answer is the task's answer by
construction. BFCL's `parallel` shards split one multi-call request and then
trail off into confirmations, so the last turn is structurally uninformative.

**The defect is family-dependent, and that is the more useful statement than
"the scorer was wrong."** A run mixing families would have had one stratum
measuring reasoning and another measuring turn structure, with no sign in the
output that they were different.

## What this costs the day

Three registered bands retired and 335 generations spent on a measurement
artifact. The cheap check that would have caught it — *does the scorer read the
same object in both arms?* — takes one minute and was not run. Adding it to the
working rule from this morning: **a registered band names its estimator, and the
estimator must be checked against the arm structure, not only against the
records.**
