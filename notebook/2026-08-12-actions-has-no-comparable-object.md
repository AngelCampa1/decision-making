# `actions` has no comparable object, and that closes it

**2026-08-12.** Outcome for the `--final-turn --call-format` prediction in
[the previous entry](2026-08-12-the-closing-turn-worked-and-made-the-measure-worse.md).
Track A1. 50 pairs, 385 generations, 0 call failures, 2010s. Third `actions` run
today; 1,105 generations across the three.

## Scored as registered

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | Every pair completes | 0 failures | 0 | ✅ |
| 2 | **Parse rate clears the guard** | ≥ 90% | **52%** | ❌ |
| 3 | `full` AST match | 30–45/50 | **47/50** | ❌ *(above)* |
| 4 | `sharded` AST match | 20–40/50 | **1/50** | ❌ |
| 5 | `p_discordant` on AST match | 0.10–0.35 | **0/50 computable** | ❌ |
| 6 | Naming stops discriminating | ≥45/50 each | full **50**, sharded **4** | ❌ |

**Band 2 was named as the gate and it failed, so 3, 4 and 5 are unreadable by
my own pre-registration.** That is the gate working. It is also the third
consecutive `actions` run whose headline numbers cannot be quoted.

The one thing band 3 does say: **the contract works.** `full` went from 45/50
named and 18/43 parsed to **50/50 named and 47/50 AST-matching** — better than
the band's top end, on BFCL's own published metric rather than a naming floor.
The instrument can grade this family. It cannot *pair* it.

## Four objects, four answers, one run

| what is scored | `full` | `sharded` | what the number is |
|---|---|---|---|
| final response (the closing turn) | 50 named / 47 AST | **4 / 1** | the closing turn is a summary |
| the **last shard's** reply | 50 / 47 | **27 / 13** | work is not at a fixed turn index |
| naming anywhere in the conversation | 50 | ~49 | six turns is six chances |
| the union of all calls emitted | — | — | breaks BFCL's bijection: 8 calls against a reference of 4 |

Every row is a different verdict on the same 100 responses.

## The number that ends the argument

Of the **23** sharded conversations whose last shard did not carry a parseable
call, **23 had emitted one in an earlier turn.** Twenty-three of twenty-three, no
exceptions.

So the sharded arm is not failing to make the calls. It makes them, correctly
formatted, and then keeps talking. `sharded-BFCL/parallel_98` is the whole thing
in one trace:

| turn | what it ended with |
|---|---|
| 0, 1 | asked for the charge and the medium |
| 2–5 | **one clean JSON call array each**, correct arguments |
| 6 | **all four calls in one array** — the complete answer |
| 7 *(closing instruction)* | *"Combined Total Strength: 1.124 × 10¹¹ N/C… the inverse square relationship…"* |

Turn 6 is a perfect response. Turn 7 is what the scorer reads.

## Why no wording fixes this

The closing instruction is *"give your final answer now, complete and
self-contained."* In the `full` arm nothing has been said yet, so the final
answer **is** the calls. In the `sharded` arm the calls were made four turns ago,
so the final answer is reasonably a **summary of what they produced**. Both arms
receive both instructions and resolve the conflict differently *because they are
in different states*, and the state difference is the independent variable.

There is no third instruction that escapes this. Demanding the calls be repeated
at the end measures whether a model restates finished work — a compliance test
wearing a reasoning test's clothes, which is the thing this run was supposed to
stop doing.

## Verdict: A1 `actions` is closed, for a different reason than `math`

| family | why it closed |
|---|---|
| `math` | `p_discordant` = 0.000 over 10 pairs. Real measurement, no effect to find at any n |
| `actions` | **no object is comparable across the arms.** The measurement does not exist |

These are not the same result and the write-up must not merge them. `math`
answers the question and says no. `actions` says the question cannot be put this
way.

**Both scoreable A1 families are now closed, and A1 needs a corpus decision
rather than more pairs.** The three options were listed after the repaired pilot
and one of them has moved:

1. **Size on `actions` naming** — dead. There is nothing to size.
2. **Vendor the spider databases** so `database` can be graded by execution
   accuracy, its published metric. This is now the leading option and it
   **requires the maintainer's permission** — it means downloading a third-party
   dataset.
3. **Harder `math` items.** GSM8K at 10/10 both arms is not the hard end of
   anything, but nothing suggests harder items produce discordance rather than
   symmetric failure.

## What was actually built today

Three void runs is a bad day's results and a good day's instrument:

- `--final-turn` exists and is now proven **necessary and not sufficient**.
- `--call-format` exists and is proven to work — 47/50 on BFCL's own AST match
  in the single-turn arm, from a standing start of "nothing in the run asks the
  model to emit a parseable call".
- `final_responses_comparable` refuses a run with no closing turn.
- `actions_report` refuses the paired naming comparison with no call contract.
- Neither guard existed this morning, and both encode a defect that had already
  produced a publishable-looking false replication.

**The one prediction that came out right was the one with no number on it.** I
declined to band the discordance direction on the second run because at
`p_discordant` ≈ 0.12 the expected count is too small to have a direction. Every
banded number about `sharded` was wrong, three runs running, and every one was
wrong because I was predicting the behaviour of a measurement rather than of a
model.
