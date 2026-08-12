# The repaired pilot, and math is a ceiling

**2026-08-12.** Outcome of [the prediction registered before it](2026-08-12-repaired-pilot-prediction.md).
30 pairs, 180 generations, 1,038s, $1.45 notional, 0 call failures, 0 isolation
failures, 30/30 conversations accumulating.

## Scoreboard

| # | Prediction | Result | Outcome |
|---|---|---|---|
| 1 | Every pair completes | 0 failures of either kind | held |
| 2 | Prompt tokens climb in every sharded conversation | 30/30 | held |
| 3 | `math` within ±2 items of 9/10 | **10/10 both conditions** | held |
| 4 | `math` per-item agreement with the first pilot | **19/20** | held |
| 5 | `database` full responses contain SQL | **10/10** | held |
| 6 | `actions` full responses name the required function | **10/10** | held |
| 7 | `p_discordant` on the repaired families ≥ 0.15 | — | **unscoreable** |

Six held. The seventh is the interesting one and it is my fault.

## The repair worked, and it is visible in one number

`database` went from answering *"I don't have access to real-time TV
broadcasting schedules"* to **10/10 producing SQL in both conditions**. Same
items, same model, same seed. The only change is that the schema is now in the
system prompt.

The system prompt lengths say the rest: `math` 144 characters in every record,
`database` 678–1,580, `actions` 627–1,056. `math` was byte-identical to the
first pilot, which is what made prediction 4 a free measurement.

## Prediction 7 could not be scored, and it should not have been written

It asked for `p_discordant` on `actions` and `database`. Those families have no
correctness measure available here — spider grades by execution and the
databases are not vendored, BFCL by an AST match on a call nobody asked for. I
knew that when I wrote the prediction, and I wrote it anyway, naming a statistic
the run could not produce.

Registering a band is worth nothing if the band is on a quantity the instrument
does not measure. **A pre-registered prediction needs the estimator named, not
just the number**, and this one did not have one.

The nearest mechanical statistics, which are *not* correctness:

| Measure | Discordant | full | sharded |
|---|---|---|---|
| `database` produced SQL | 0/10 | 10 | 10 |
| `database` string match | 1/10 | 1 | 0 |
| `actions` named every required function | **2/10** | 10 | 8 |

## math is at a ceiling and the grid cannot be sized on it

**`p_discordant` = 0.000.** Ten pairs, both conditions correct on all ten.

The first pilot measured 0.10 on this family. That was **one item**, and the
repeat — identical prompt, identical items — got it right the second time. So
the entire discordance signal on `math` in the first pilot was a single response
that changed on rerun.

This is the third place the aptitude-versus-unreliability split
([arXiv:2505.06120](https://arxiv.org/abs/2505.06120)) has turned up here, and
the cleanest instance: the aggregate barely moved (19/20 agreement) while the
one non-agreeing item was the whole result.

**Arithmetically this closes `math` as an A1 venue.** McNemar's effect is bounded
by the discordant share, so at `p_discordant` ≈ 0 the family has no power at any
sample size. What `required_pairs` says at plausible values:

| `p_discordant` | pairs for a 5pp effect | for 10pp |
|---|---|---|
| 0.10 | 246 | 60 |
| 0.15 | 369 | 91 |
| 0.20 | 493 | 122 |

All of which assume there is discordance to find. On `math` there is none.

## So where is the signal? `actions`, and I had it backwards

Two of ten `actions` pairs are discordant on *did it name the function the
reference answer calls for*, **both in the paper's direction** — the full
condition named it, the sharded condition did not. `parallel_132` and
`parallel_157`, both cleanly: `full` named it, `sharded` returned nothing.

n = 10 and two same-direction discordant pairs is p = 0.25 exact. Nowhere near
significant, and it is the only non-zero discordance the pilot produced.

Which inverts this morning's reading. `math` was treated as the family to build
on because it was the one that looked scorable. It looked scorable because it was
the only family whose task was fully delivered — and now that the other two are
delivered too, `math` is the family with nothing left to measure and `actions` is
the one with a signal.

**Function-naming is a floor, not a correctness score**, and that is why it can
be used: the names come off the vendored reference and no key is authored. A
response that names `create_histogram` and gets every argument wrong counts as a
hit here. But it is mechanical, it is available, and it has a non-zero discordant
rate — which is three properties `math` cannot offer any more.

## What this means for Track A

A1 was going to be sized from `math`. It cannot be. The options are:

1. **Size it on `actions` function-naming**, accepting that the outcome is a
   floor on capability rather than task success. Needs a `p_discordant` estimate
   from more than ten pairs before any grid is priced.
2. **Add a family whose published metric is runnable here.** That is a corpus
   decision — vendoring the spider databases would make execution accuracy
   available and turn `database` into a real venue.
3. **Harder items within `math`.** GSM8K at 10/10 is not the hard end of
   anything.

Nothing here says the multi-turn effect is absent. It says **this venue cannot
currently see it**, which is an instrument result and belongs in the Phase 0
column, not the findings column.

## The string match is worthless and the run proves it

1/10 and 0/10, against 20/20 responses that produced valid-looking SQL. The
mismatches are things like `NOT IN (SELECT …)` against `LEFT JOIN … IS NULL` —
different text, and for `spider-val-409` arguably different NULL semantics, which
is exactly the judgement call the metric was built to avoid making.

It is labelled a lower bound and it prints every mismatch, so it did its job. But
it should never be summarised without those traces, and it should not appear in
any table that a reader could mistake for accuracy.
