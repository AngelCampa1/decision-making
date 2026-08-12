# Prediction: 50 `actions` pairs, and a note about when this was written

**2026-08-12.** Track A1.

## The ordering, stated plainly

**This entry was written after the run started.** I meant to print the run plan
and ran the run. No results have been read — the output file has not been opened
and will not be until this is committed — but the rule in `CLAUDE.md` is that
predictions go in *before* runs, and "before I looked" is a weaker guarantee than
"before it started". Recorded as the weaker one.

## Why this run

[The repaired pilot](2026-08-12-the-repaired-pilot-and-a-ceiling.md) closed
`math`: `p_discordant` = 0.000 over ten pairs, so no sample size gives that
family power. The only non-zero discordance it produced was **`actions`, 2 of 10
pairs on function-naming, both in the paper's direction**.

Two pairs is not an estimate. This takes the same family to 50 pairs so
`required_pairs` has something real to work from.

The draw is filtered after sampling, never during, so this is a different
`rng.sample` draw than the pilot's ten — not a superset. Its own checkpoint
(`actions-50.jsonl`) for that reason.

## Predictions

| # | Prediction | Band |
|---|---|---|
| 1 | Every pair completes | 0 call failures, 0 isolation failures |
| 2 | Prompt tokens climb in every sharded conversation | 50/50 |
| 3 | `full` names every required function | ≥ 45/50 |
| 4 | `sharded` names every required function | 38–47 / 50 |
| 5 | `p_discordant` on function-naming | **0.08–0.25** |
| 6 | Discordant pairs favouring `full` | ≥ 70% of them |

**5 is the number the run exists for.** The pilot's 2/10 is 0.20 with a 95%
interval running roughly 0.03–0.56, which is why the band is wide. If it comes
back under 0.05, `actions` closes the same way `math` did and A1 needs a corpus
decision rather than more pairs.

**6 is the direction test and it is the one that would actually replicate the
paper.** Discordance alone is noise; discordance concentrated in one direction is
an effect. Both pilot discordants favoured `full`, which is 2 out of 2 and means
nothing on its own.

## Where I expect to be wrong

**4.** I have put `sharded` at 38–47 because the pilot gave 8/10 and I am
assuming the pilot's rate roughly holds. The pilot's `math` stratum has just
demonstrated that a single item's verdict is not stable across identical runs, so
a rate estimated from ten items is exactly the kind of number this repository has
been wrong about. The band is wide and could easily be wide in the wrong place.

Also worth saying: function-naming is a **floor on capability, not task success**.
A response naming `create_histogram` with both bin counts wrong scores as a hit.
An effect found here is an effect on whether the model reaches for the right tool
at all, which is a narrower claim than the paper's and should be written as one.
