# 2026-08-19 — Prediction: making the runner concurrent must not change what it measures

Written before the concurrent path exists, and before any of it runs. The
ordering is the point: a band chosen after seeing the numbers is not a band.

## Why this needs a falsifier at all

N10 is 3,096 calls. Track H's Phase 0 is 498. At roughly 8 s per CLI call a grid
of that size is days of serial wall-clock, and `stats/power.py`'s own tables
push future grids higher. So the runner is going concurrent.

The hazard is specific. Concurrency changes call ordering, changes what else the
GPU or the API is doing while a call is in flight, and on a local server changes
the batch a request lands in. If any of that changes the *response*, every number
produced after the change is incomparable with every number before it, and
nothing in a checkpoint would say so. This repository has published two
estimators that produced a clean run, a full checkpoint and a meaningless
number; a third would not be an accident.

So: before any published run uses the concurrent path, it has to be shown that
concurrency does not move the result.

## The measurement

Free, on the `dev` arena, which is why that arena was built first.

- **Corpus**: the first 40 cases of `datasets/triggers/decision-making/index.yaml`
  in file order. Deterministic, real prompts, no sampling of items.
- **Model**: `ollama/qwen3:4b`, `temperature=0`, local.
- **Arms**, in this order:
  - `S1` — serial, concurrency 1.
  - `S2` — serial, concurrency 1, an independent repeat.
  - `C` — concurrent, concurrency 8.

`S2` is not padding. It is the known-good case standing rule 2 demands: without
it, a low `S1`-vs-`C` agreement is uninterpretable, because it could be
concurrency or it could be that this model is not reproducible against itself.
The floor has to be measured, not assumed.

## Estimator, denominator, function

Named in advance, because four pre-registration slips on 2026-08-12 came from
not doing that.

- Per item *i*, two binary indicators against `S1`:
  `b_i = 1[text_S2[i] == text_S1[i]]` and `c_i = 1[text_C[i] == text_S1[i]]`.
  Exact string equality on the scored `text` field, not on `reasoning`.
- `agree_S2 = mean(b)`, `agree_C = mean(c)`.
- **Denominator: 40 for both.** All items, whatever their parse status. Every
  call returns text or raises, and a raise is a failed run rather than a scored
  zero.
- **Test**: `decision_evals.stats.paired.mcnemar_exact` on the 40 paired
  `(b_i, c_i)`.

## Registered band

**`agree_C >= agree_S2 - 0.10`.**

Concurrency may cost at most ten points of agreement relative to the
serial-repeat floor. Stated against the floor rather than against 1.0
deliberately: Track L7 registered a recall band against a round number when the
observed per-item ceiling was 0.941, and demanded perfection on everything else
without noticing. A band above an unmeasured ceiling is not a prediction.

## Kill condition, declared now

**If `agree_S2 < 0.50`, the primary outcome is abandoned before `agree_C` is
looked at.** That would mean exact text match cannot distinguish anything at
this model and temperature, so a comparison built on it measures the instrument
rather than the arms.

**Pre-declared secondary, used only if the kill fires**: per-item
`input_tokens`, which must match exactly across all three arms. Tokenisation of
a fixed prompt is deterministic, so this is a property concurrency genuinely
must not change, and it survives a model that will not reproduce its own prose.

## What I expect, and where I expect to be wrong

I expect `agree_C` to sit inside the band, because nothing in the design should
make a stateless HTTP completion depend on what else is in flight.

Where I expect to be wrong: **`agree_S2` itself.** `qwen3:4b` is a reasoning
model, and `temperature=0` is not a determinism guarantee — it fixes the
sampling rule, not the floating-point reduction order, and GPU kernels commonly
select different reductions by batch size. A long reasoning chain gives that
divergence hundreds of tokens to compound in before it reaches `content`. So
`agree_S2` may well be far below 1.0, and could plausibly trip the kill. That is
the outcome I think is most likely to be surprising, and it is why the secondary
is declared here rather than invented afterwards.

If the kill fires, the honest report is that this venue cannot answer the
question by text identity, and the concurrency claim rests on the token
secondary alone. That is a weaker result and it will be written as one.

## What a failure would mean

If `agree_C` falls outside the band while `agree_S2` is high, concurrency
changes results, and the concurrent path may not be used for any published run
until that is understood. The serial path stays.
