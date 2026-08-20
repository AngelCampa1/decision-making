# 2026-08-20 — Prediction: the concurrency falsifier has never run on the backend every published number came from

Written before the run, before the script that runs it, and before any call is
made. Companion to
[`2026-08-19-prediction-concurrency-must-not-change-results.md`](2026-08-19-prediction-concurrency-must-not-change-results.md),
which registered the same question on the free `dev` arena.

## Why this is a gap and not a tidy-up

`runner.CONCURRENCY_UNSAFE` refuses `concurrency > 1` on the model prefixes it
names, and it names exactly one: `ollama/`. Every other prefix is permitted, and
the Claude CLI backend is every other prefix. So the register's silence about
`haiku` reads as a clearance, and nothing was ever measured to earn it. The
2026-08-19 run that produced the `ollama/` entry ran three arms on a local
batching server and nowhere else.

Two things found while scoping this, both of which change what the run is for,
and both recorded here rather than discovered afterwards:

- **`scripts/run_triggers.py` does not use `run_arm`.** `collect()` is its own
  serial loop, one call at a time, checkpointing after each. Every trigger
  number this repository has published was produced serially, by a function the
  concurrency work never touched.
- **No caller passes `concurrency > 1` on the CLI backend today.**
  `scripts/calibrate.py` is `run_arm`'s only production caller there and it
  passes no `concurrency` at all, so it takes the default of 1.

So this run does not clear a latent defect that is currently firing. It clears a
door that is unlocked and unused, before Wave 1.3 walks through it with several
thousand calls.

## The measurement

- **Corpus**: the generated corpus, `load_all()` with `generate(template,
  seed=1)`. 280 items over 10 templates, the same corpus and seed
  `scripts/calibrate.py` uses. Every item carries an answer key, which is why
  this corpus rather than the trigger turns: the quantity that reaches a
  published number here is a scored answer, and this corpus has one.
- **Model**: `haiku`, screening arena, asserted rather than assumed.
- **Arms, in this order**: `S1` serial, then `C` concurrent at 8, then `S2`
  serial.

**The order is a design choice and it is the one thing here not copied from the
earlier entry.** That run put `C` last and was then unable to separate
concurrency from drift, because its own replication found two serial passes an
hour apart agreeing on the text of nothing. Running `C` *between* the two serial
passes makes the floor conservative in the right direction: `S1` against `S2`
spans the whole session, while `C` sits nearer in time to each of them. If
elapsed time is what moves answers, the pair separated by the most time is the
pair that should agree least, and that pair is the floor.

## Estimator, denominator, function

- Per item *i*, on the `parsed` field of the record, which is the extracted
  answer rather than the prose around it:
  - `b_i = 1[parsed_S2[i] == parsed_S1[i]]`
  - `c1_i = 1[parsed_C[i] == parsed_S1[i]]`
  - `c2_i = 1[parsed_C[i] == parsed_S2[i]]`
- `agree_serial = mean(b)`, `agree_C1 = mean(c1)`, `agree_C2 = mean(c2)`.
- **Denominator: the items carrying a record in all three arms**, expected to be
  280. An item with an infrastructure zero stays in it and is also counted and
  reported per arm. The earlier entry's denominator rested on the premise that
  "a raise is a failed run rather than a scored zero", which is false about this
  harness, since `_run_one` catches `CliError` and writes a zero. The premise is
  dropped here rather than repeated.
- **Test**: `decision_evals.stats.paired.mcnemar_exact` on the paired
  `(b_i, c1_i)`, two-sided.

## Registered band

**`min(agree_C1, agree_C2) >= agree_serial - 0.05`.**

Five points rather than the earlier entry's ten, and the reason is `n`. At 280
items a rate near 0.9 carries a standard error near 0.018, so five points is
about 2.8 standard errors; at 40 items it would have been under one, which is
what made ten the right number there. The band is stated against the measured
floor rather than against 1.0, for the reason that entry gives and Track L7 paid
for.

## Kill condition, declared now

**If `agree_serial < 0.60`, the primary is abandoned before either concurrent
rate is looked at.**

The chance floor is 0.50 here rather than 0.00, because `parsed` takes one of
two values on every item in this corpus and two independent coin flips agree
half the time. A serial floor at 0.60 is a model barely distinguishable from a
coin against itself, and a band computed under it would be measuring the
instrument. This is a different number from the earlier entry's 0.50 because it
is a different estimator with a different chance floor, not because anyone
changed their mind.

**Pre-declared secondary, used only if the kill fires**: per-item `input_tokens`
identical across all three arms. A fixed prompt tokenises deterministically, so
that is something concurrency genuinely must not change, and it survives a model
that will not reproduce its own answers.

## Secondaries, registered so that a zero is not read afterwards as a discovery

- **Exact text agreement, predicted to be near zero in every pair, including
  `S1` against `S2`.** These are sampled calls through `claude -p` with no
  temperature control. The `dev` arena entry found cross-invocation serial text
  agreement of 0 of 40 on a local model at `temperature=0`, so there is less
  reason to expect identity here, not more. It is reported because it is free,
  and it is registered because an unregistered zero cannot be told apart from a
  broken estimator, which this repository has shipped three times.
- **Accuracy per arm, with a band and no confirmatory weight**:
  `|acc_C - acc_S1| <= 0.05`. This is the quantity that reaches a published
  number, so it is worth a band. 280 items is not enough to treat a three-way
  accuracy comparison as confirmatory, so it does not get to be the primary.
- **Infrastructure zeros per arm, and the number of backpressure trips.**
  Reported, no band.
- **Wall-clock per arm and the `S1` over `C` ratio.** Reported, no band. It is
  the reason the concurrent path exists and it is not evidence about
  equivalence.

## What I expect, and where I expect to be wrong

I expect the primary inside the band. Each `claude -p` call is its own
subprocess against a stateless API, and the batching mechanism that broke the
local server has no counterpart here.

Where I expect to be wrong, in order:

1. **Rate limits at concurrency 8.** This repository has never issued parallel
   calls to this backend. The backpressure that would absorb a 429 landed today
   and has never met a real one; its message markers are labelled a guess in
   their own source, because no record here carries any of them. If the window
   closes mid-run the wall-clock secondary is meaningless, and the run may take
   longer than serial while still being correct.
2. **`agree_serial` itself.** A two-option answer from a sampled model is not
   deterministic, and the earlier entry was wrong in exactly this place. If the
   floor lands near 0.6 the kill fires, and the honest report is that this venue
   cannot answer the question by answer identity either.
3. **The order fix not being enough.** Putting `C` in the middle bounds drift, it
   does not remove it. If all three rates come back close to each other and low,
   that is drift, and it is a statement about the backend rather than about
   concurrency.

## What a failure would mean

If a concurrent rate falls outside the band while the floor is healthy, `haiku`
joins `ollama/` in `CONCURRENCY_UNSAFE`, Wave 1.3 runs serially, and the
throughput problem stays open. The register may only shrink, so the addition is
the cheap outcome here and the clearance is the one that has to be earned.
