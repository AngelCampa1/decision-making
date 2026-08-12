# A1 pilot: the instrument works and the effect is not there

**2026-08-12.** Outcome of [the prediction registered this morning](2026-08-12-a1-pilot-prediction.md).
30 pairs, 190 generations, Haiku, 1,402 s, notional cost $1.78, 0 call failures.

## Scoreboard against the registered predictions

| # | Prediction | Outcome |
|---|---|---|
| 1 | `p_discordant` lands in 0.15–0.35 | **WRONG.** 0.10 on `math`, and 0.00 after the one discordant pair is read |
| 2 | The sharded condition scores lower than full | **Not supported.** 9 of 10 `math` pairs both correct; the tenth is an extraction artifact |
| 3 | Prompt tokens climb in every sharded conversation | **Held.** 30/30 |
| 4 | Zero isolation failures | **Held.** Receipt asserted per conversation |
| 5 | Under 5 infrastructure failures | **Held.** Zero |

**That is the seventh consecutive prediction in the direction of the experiment
working, and the sixth that was wrong that way.** The prediction entry said this
would probably happen and it did. The pattern is not getting weaker with
practice, so it should be treated as a standing bias rather than a run of bad
luck: predictions in this repository are systematically optimistic about its own
hypothesis, and the appropriate response is to keep registering them rather than
to keep believing them.

## The instrument is fine. This is the first clean result here.

Three corpora produced three nulls, and until today none of them could say
whether the venue was capable of showing anything. This one can.

- Prompt tokens climbed monotonically in all 30 conversations — the shortest ran
  3 turns, the longest 7. Turns accumulate.
- Not one call failed across 190 generations.
- The isolation receipt was asserted per conversation and never fired.
- Sharded items emit **1,655** median output tokens against **496** for full,
  which is the ~3.3× the turn count implies. Nothing is being truncated.

## The one discordant pair is not a wrong answer

`sharded-GSM8K/728`, gold 40. The full condition computed `(60 ÷ 150) × 100 =
40%`. The sharded condition finished its last turn with:

> **Total so far: 150 spools** / **Total blue spools: 60** / Does Candy have any
> other colours of thread spools beyond these, or is this her complete
> collection?

It did not answer. Last-number extraction lifted `60` out of an inventory list
and scored it wrong. **"Gave no answer" and "gave a wrong answer" are different
things**, and merging them would have manufactured the exact effect being looked
for — from a response that is arguably *better* behaviour than the full
condition's, since the model noticed the shards might be incomplete.

Adjudicated as "no answer given", `p_discordant` on `math` is **0.00**.

This is the same failure as probe-09 and probe-07, arriving through the scorer
rather than the key. Rule 3 caught it because the traces were printed rather
than summarised.

## What this does to the full grid, and it cuts both ways

The MDE table read low discordance as bad news. It is not, and the power module
says so plainly when asked:

| `p_discordant` | MDE at 100 pairs | at 315 | at 627 |
|---|---|---|---|
| 0.10 | 7.8pp | **4.4pp** | 3.1pp |
| 0.15 | 9.5pp | 5.4pp | 3.8pp |
| 0.20 | 11.0pp | 6.2pp | 4.4pp |

So 315 pairs at the measured discordance gives **4.4pp**, better than the
5.4–9.9pp the programme assumed. Sizing the grid is not the problem.

**The problem is the ceiling.** `required_pairs` refuses `effect > p_discordant`
with *"the difference of the discordant counts is bounded by their sum"*. At
`p_discordant = 0.10` the largest effect that can exist is **10pp**. The paper's
headline is a **39%** average drop across six generation tasks
([arXiv:2505.06120](https://arxiv.org/abs/2505.06120)). An effect of that size
is not merely undetected here — on this family it is **arithmetically excluded**.

## The caveat that matters most, and it is mine

`math` was scored because it is the only family with a mechanical key. **That is
selection on scorability, and scorability correlates with saturation.** GSM8K is
a solved benchmark; 9 of 10 pairs both correct in both conditions is a ceiling
effect, and a ceiling cannot show a decrement.

The 20 `actions` and 20 `database` pairs are recorded and unscored, and they are
the families where a difference would plausibly live. Concluding "the effect is
not there" from `math` alone would repeat the twelve-item error in a new costume:
measuring the stratum that could not have shown anything and reporting the
absence.

So the honest statement is narrower than it wants to be:

> On GSM8K items delivered as 3–7 shards to Haiku 4.5, with turns verified to
> accumulate, sharding cost nothing measurable — and the family was at ceiling in
> both conditions, so it could not have.

## What happens next, and what does not

**Does not:** no number from this run goes into `docs/RESEARCH_PROGRAMME.md`, and
the full A1 grid is not sized from it, until the maintainer has read the traces
above. Ten pairs is ten pairs.

**Open, and for the maintainer rather than for me:**

1. **Scoring `actions` and `database`.** Both need a key, both are
   judgement-laden, and both are where 21/21 came from. The pilot deliberately
   stopped short.
2. **Whether a non-answer counts.** The runner sends the shards and stops. The
   paper's own simulation classifies each response and continues until the model
   attempts an answer. Ours does not, and that is a design decision with a
   direction: it makes the sharded arm look worse for a reason unrelated to
   reasoning.
3. **Whether `math` should be in the grid at all.** At ceiling it contributes
   cost and no information.

---

## Correction, same day: forty of these sixty records were void

Not edited above, per the notebook rule. What is written there about `math`
stands. What is written about `actions` and `database` does not, and the reason
is not in this entry's data.

Both families were run without the material the task needs. `database` was asked
for SQL with no schema in the prompt; `actions` was asked to call a function with
none offered. The corpus carries both — `schema_sql`, `function` — and the runner
never rendered them. Twenty items, forty records, unanswerable rather than hard.

Everything this entry says about the instrument still holds: the conversations
accumulated, the receipts were clean, nothing failed. **That is the part worth
keeping.** A run can pass every instrument check and still measure nothing,
because no check asked whether the task had arrived.

And it corrects a sentence above. `math` was called the only family with a
mechanical key. It was the only family whose task was fully delivered, which is
why it was the only one that looked scorable — a word problem carries its own
numbers. The two claims point at the same ten items and are not the same claim.

Re-run prediction: [2026-08-12-repaired-pilot-prediction.md](2026-08-12-repaired-pilot-prediction.md).
