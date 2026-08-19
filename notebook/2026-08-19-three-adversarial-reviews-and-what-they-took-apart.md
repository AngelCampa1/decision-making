# 2026-08-19 — Three adversarial reviews, and the p-values did not survive them

Three reviewers were pointed at the concurrency work before it merged: one at the
runner, one at the evidence, one at CI and the documents. Each was briefed to
break the work rather than approve it, and told to demonstrate findings by
running code. Everything below marked confirmed was re-derived here, from the raw
records or by running the repro, before it was acted on.

The reviews found more than the work did.

## The evidence review: the numbers are right and the inference was not

Every headline figure reproduced exactly. What did not survive is what was built
on top of them.

**The agreement indicator is a block, not 40 draws.** Run-length encoding the
per-item indicator in dispatch order:

| | run-length encoding | sign changes | expected under iid |
|---|---|---|---|
| run 1 | `[0×8, 1×16, 0×1, 1×15]` | 3 | ~13.6 |
| run 2 | `[0×27, 1×13]` | **1** | ~17.1 |

Run 1 disagrees on positions 1–8 and agrees on 9–40. Run 2 disagrees on 1–27 and
agrees on 28–40. The single interior break in run 1 is `m01p`, the CUDA OOM.
Agreement is a property of *where in the run a call happened*, not of the item.

McNemar's exact test conditions on discordant pairs and requires them to be
independent. Run 2's thirteen discordant pairs are one contiguous block: one
event, not thirteen. Recomputed with blocks as the unit, the p-values go from
9.31e-10 and 2.44e-4 to **0.125 and 0.50**, and the `1.6e-7` I quoted for "0 of
40 under the serial rate" goes to about **0.46**. The arithmetic was right. The
null was refuted by the same records it was computed from.

Fourth instance here of one rule: the estimator was checked against the records
and never against the structure of the process generating them.

**The reload hypothesis is not just untested, the record disfavours it.** I wrote
that "roughly 8 minutes of idle" sat between the runs, against Ollama's 300 s
`keep_alive`. Reconstructed from file mtimes and each arm's recorded elapsed
time, the gap between run 1's last call and run 2's first is **165 seconds**. No
idle unload would have occurred. My premise was wrong by a factor of three, in
the direction that made my own hypothesis work.

The data also contain a counterexample to any idle-driven mechanism: `rep1-S1`
passes through three regimes back to back with no idle at all — positions 1–7
byte-identical to run 1's S2, positions 8–27 matching nothing, positions 28–40
byte-identical to its own S2. The state changes *during* an arm, between
consecutive calls.

**The registered secondary failed in run 1 and I reported it as passing.**
Registered: per-item `input_tokens` must match exactly across all three arms,
denominator 40. On `m01p` it is S1=0, S2=177, C=177. The instrument's own summary
records `input_tokens_identical: false`. I wrote "matched exactly across all
three arms on every item that ran" — a silent move to n=39, three paragraphs
after labelling exactly that move scrupulously for the agreement rate.

**The kill fired in run 2 and I then used the quantity it forbade.** The kill
says the primary is abandoned *before `agree_C` is looked at*. The entry says
that correctly once, then builds "0 of 40 twice, against 31 of 40 and 13 of 40"
and the 1.6e-7 on run 2's `agree_C` and run 2's floor. It cannot be both
abandoned and load-bearing. The surviving claim is a post-hoc analysis and is
labelled as one from here on.

**"Zero" was a pair-selection artefact.** I wrote that two serial runs an hour
apart agree on zero of forty, and propagated it into three other files. There are
two such pairs. The other one, run 1's S2 against run 2's S1, agrees on **7 of
40**. Corrected everywhere.

**The strongest evidence in the dataset was never reported.** Concurrency is
perfectly confounded with arm position — S1, S2, C ran in that order, twice, so
no serial arm ever ran third. But S2 and C are *adjacent*, with the same ~23
minute separation as S1 and S2, which controls elapsed time:

| pair | separation | text agreement |
|---|---|---|
| run 1 S1 vs S2 | ~23 min | 0.7750 |
| run 1 S2 vs C | ~23 min | **0.0000** |
| run 2 S1 vs S2 | ~24 min | 0.3250 |
| run 2 S2 vs C | ~23 min | **0.0000** |

At matched lag, serial-vs-serial is 0.775 and 0.325 and serial-vs-concurrent is
zero twice. That retires the elapsed-time explanation. It does not close the
position confound, which needs a serial arm run third. It is now in the
disclosure and the register comment.

**"Six of 39 landed on a different decision" was four.** Two of the six are
`no_answer_line` — format failures, not decisions. And the baseline I lacked at
the time: cross-invocation serial disagrees on five. Against that, four is not
an effect.

**`agree_S2` is a change-point, not a rate.** 0.775 and 0.325 are where the
regime switch fell, position 9 versus position 28. A ±0.10 band and a `< 0.50`
kill threshold defined on a change-point location are a category error, which is
why both behaved so oddly.

## The runner review: three real defects, all confirmed by running them

**The budget stopped being a limit.** `authorise` called `assert_can_afford` but
never charged, and the ledger only advanced when a record came back — so every
call in one window read the same balance. Six items at $0.02 against a $0.021
limit ran all six, burning 5.7x the limit and raising nothing, where serial
stopped after one. Reproduced here before fixing. Now reserved at dispatch and
released on completion; the same repro stops after one call at every
concurrency, and the docstring's "overshoot is bounded by the window" is gone
because the overshoot is zero.

**An abort discarded calls it had already paid for.** Returning on the first
failing future skipped the rest of that batch, including futures that had
*succeeded*, and which ones survived depended on set iteration order: twelve
trials, three different checkpoints, same inputs. Those calls were made and
billed, so the ledger under-read the real burn by up to `concurrency - 1` calls
on every abort — in a repository where `BudgetLedger` is described as the burn
meter. The batch is now drained before the error propagates.

**The register was evadable by typo.** `CONCURRENCY_UNSAFE` matches on the
requested model string, but `build_payload` tolerates a bare name and
`parse_completion` stamps the label back on. So `qwen3:4b` — which is exactly
what `ollama list` prints — reached the same server and wrote records reading
`ollama/qwen3:4b` while the guard never fired. `Ollama/` evaded it too. The
register may only shrink by measurement; this let it shrink by autocomplete.
`local_call` now refuses a model that does not name its venue, and the guard
case-folds.

**And the test that should have caught the first one made zero calls.**
`test_the_budget_still_stops_a_concurrent_run` used `limit_usd=0.0`, which
refuses the first item before anything is dispatched — the serial refusal path
with a `concurrency` argument attached. A mutant that removed the window bound
entirely passed all 38 tests. The test now authorises exactly one call and
asserts on the number actually made.

One more, smaller: `assert not any(prefix.startswith("haiku") for prefix in
CONCURRENCY_UNSAFE)` interrogates the register rather than the model and stays
true even when haiku is genuinely registered unsafe.

## What the reviews could not break

The single-writer checkpoint invariant held against a mutant writing one
character at a time from six threads. Exactly-once and no hang at concurrency 1,
2, 3, 5, 8, 64. The overshoot bound as originally claimed was accurate, just
unguarded. And the guard's own docstring — "a precaution rather than a
demonstration that concurrency moves decisions" — was checked and found correct.

## What actually survives all of this

One qualitative statement: **the concurrent arm never lands in the same output
state as any serial arm, in either run, on any of 40 items, at matched lag, while
serial arms share large contiguous blocks.** That is what the refusal rests on,
and it survives the collapse of every p-value built on top of it, because it does
not need one.

Everything quantitative around it was measuring a process whose structure the
estimator assumed away. The direction is what these data support. The p-value is
not, and the entries that quoted one are corrected here rather than edited there.
