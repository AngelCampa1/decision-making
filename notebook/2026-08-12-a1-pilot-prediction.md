# A1 pilot: what I expect, written before the run

**2026-08-12.** 30 pairs, seeded, 10 each from `actions`, `database`, `math`.
~190 generations on Haiku.

## Why a pilot rather than the full grid

The full A1 grid is 1,964 generations and its MDE is a *range* — 5.4 to 9.9pp —
because `p_discordant` is unknown. `stats/power.required_pairs` says in its own
docstring that this is the input people most often guess wrong and that it should
come from a screening run. So the screening run comes first, and the full grid is
sized from what it returns rather than from my sweep.

## What is being measured, and what is not

**Recorded:** raw responses in both conditions, per-turn prompt and output
tokens, cost, duration, every intermediate turn.

**Not recorded:** whether any answer is correct. `ShardedRecord` has no `correct`
field and a test asserts its absence. Standing rule 3, and 21/21 scored failures
across three corpora are the reason.

So this pilot **cannot by itself produce `p_discordant`.** It produces the traces
from which a human can. Any figure I compute afterwards is provisional and
labelled as needing adjudication.

## Predictions, registered now

1. **`p_discordant` lands in 0.15–0.35.** This is the number the pilot exists for.
2. **The sharded condition scores lower than full.** Direction only; the pilot is
   30 pairs and its own MDE is ~20–30pp, so it cannot establish magnitude and
   will not be reported as if it could.
3. **Prompt tokens climb monotonically in every sharded conversation.** If this
   fails anywhere, the turns were not accumulating and the run is void rather
   than negative.
4. **Zero isolation failures.** The receipt is asserted per conversation, not
   once per run, because a receipt that changed mid-run is precisely the silent
   confound the gate exists for.
5. **Under 5 infrastructure failures** across ~190 generations.

## The standing bias

Predictions 1 and 2 are both in the direction of the experiment working. That is
now the seventh consecutive time, and the previous five were wrong in that same
direction. Writing it here rather than trusting it.

## What would make me stop

- Any isolation failure — stop immediately, do not continue to the full grid.
- Prompt tokens not climbing — the transport is broken and every multi-turn
  number in this repository is suspect.
- More than ~20% infrastructure failures — the harness, not the model.
