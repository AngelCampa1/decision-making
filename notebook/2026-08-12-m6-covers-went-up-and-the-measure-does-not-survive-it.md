# M6: `covers` went the wrong way, and the measure does not survive finding out why

**2026-08-13**, scoring the run. Outcome for
[the prediction](2026-08-12-m6-prediction-the-collision-was-inside-the-entry.md),
committed at `82b4ab8` before any calls were made. Track M6. **146 isolated
calls** (73 cases × 2 repeats), Haiku, **0 unparseable, 0 isolation failures**.

Two repeats rather than five, on M5's reliability finding. ICC on this run is
**0.852** with **1 of 73** items showing any scatter, so that was the right call.

## Scored as registered

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | Parseable verdicts | ≥ 98% | **100%** (146/146) | ✅ |
| 2 | **`covers` falls under the split pairing** | < 0.743 | **0.857** | ❌ |
| 3 | `covers` stays above chance | > 0.500 | 0.857 | ✅ |
| 4 | Firing accuracy unmoved | 0.90–0.97 | **0.952** | ✅ |
| 5 | FPR at the floor | ≤ 0.018 | **0.000** | ✅ |
| 6 | No firing difference from the contiguous arm | p ≥ 0.05 | **p = 0.273**, 4 of 73 differ | ✅ |

**Five of six, and the miss is the one that was the experiment.** I predicted
`covers` would fall when the colliding pair was split. It rose, 0.743 → 0.857,
and conditional on the arm having fired it is **24/24 = 1.000**.

The control bands did exactly what the design said they would. Same words, same
four procedures, firing indistinguishable — precision 1.000, recall 0.806
against 0.756, the same four misses (`x-n20`, `x-n21`, `x-n22`, `x-n03`), FPR
0.000 in both repeats. So the arm is clean and band 2 can be read.

## The diagnostic I named in advance showed nothing

The prediction said: *"The diagnostic is `p07` specifically — the item the
collision was diagnosed on. If `covers` falls and `p07` is where it falls, that
is the collision."*

`p07` is **1.0 in both arms**. It did not move, in either direction.

That is itself informative. `p07` fires at 1/5 in the **one-entry** arm and 5/5
in the four-entry arm, and now 2/2 and 5/5 in the two n=2 arms. Every arm that
does *not* show the model the router table gets `p07` right. **The
`cascade`/`timing` collision is a defect of the table, not of the descriptions**,
which is what M4 suggested and what this confirms from a second direction.

## What actually moved, and it is worse for the measure than a fall would have been

Five items changed. The raw answers say why:

| item | label | named at M5 (`ledger-fit` / `cascade-timing`) | named at M6 (`ledger-cascade` / `fit-timing`) |
|---|---|---|---|
| `p06` | `fit` | `cascade-timing` ×4, `ledger-fit` ×1 → **0.2** | `fit-timing` ×2 → **1.0** |
| `p04` | `fit` | `cascade-timing` ×1, `ledger-fit` ×4 → 0.8 | `fit-timing` ×2 → **1.0** |
| `p09` | `cascade` | `cascade-timing` ×4, `ledger-fit` ×1 → 0.8 | `ledger-cascade` ×2 → **1.0** |
| `p03` | `ledger` | `ledger-fit` ×3, none ×2 → 0.6 | `ledger-cascade` ×2 → **1.0** |
| `x-n23` | `timing` | `cascade-timing` ×4, none ×1 → 0.8 | `fit-timing` ×2 → **1.0** |

**The model did not change its mind. The entry boundaries moved underneath it.**

`p06` is the clearest case. It is labelled `fit`, and in both arms the model
reaches for something *timing*-flavoured. Under M5's grouping, `timing` sat with
`cascade`, so that answer landed outside the entry covering `fit` and scored 0.
Under M6's grouping, `timing` sits with `fit`, so the identical instinct lands
inside the covering entry and scores 1. Nothing about the model's judgement
improved; the partition forgave a different confusion.

## So the measure is grouping-dependent, and neither number means what it looked like

`covers` reads as *"did the model find the right procedure, allowing for the
merge"*. It is actually *"did the model's answer happen to fall inside whichever
entry contains the label"* — and **which confusions that forgives is a property
of the partition, not of the model.**

M5's contiguous grouping forgives `cascade`↔`timing` confusion. M6's grouping
forgives `fit`↔`timing` confusion. The two arms have **identical vocabulary,
identical entry count, and identical firing behaviour**, and their routing
numbers differ by 11.4pp for that reason alone.

The registered caveat said `covers` is not comparable across `n`, because chance
moves with the number of entries. **That was too weak. It is not comparable
across *groupings at the same n* either**, and this run is the demonstration.

The prediction's stated reason for caring was right even though its direction was
wrong — *"no routing number at n=2 can be quoted without naming its pairing"* —
and it is now right much more strongly than I meant it.

## What this costs, concretely

- **M5's `covers` 0.743 stands as measured and loses its interpretation.** It is
  not an estimate of how well a two-entry arm routes. It is that number *for the
  contiguous partition*, and the same skill under a different partition of the
  same four procedures reads 0.857. The published M5 result needs this attached,
  and the results README is amended rather than rewritten.
- **The instrument now prints the warning.** `run_triggers.py` reports both
  denominators and states that the figure is not comparable across pairings.
- **This is the third measure in two days to survive its run and fail its
  interpretation** — after `final_response` on `actions`, and exact-name routing
  accuracy on any merged arm. In none of the three did anything crash.

## The one thing that is solid

**Firing is unmoved by grouping, and that is a real null with a clean design.**
Two arms, word-multiset identical, four procedures offered either way, 73 paired
items: 4 differ, p = 0.273. Combined with M4 (structure, p = 0.83), M5 (count,
p = 0.50) and L5 (content), **nothing this repository has varied about a skill's
description changes how well it discriminates.** Four independent manipulations
now say so.

## For the maintainer

1. **Routing at merged entries needs a different measure or none.** The
   candidates are: score only at n=4 where names are labels; or ask the model to
   name a procedure *inside* the entry it picked, which adds a response-contract
   change and its own confound. Neither is free, and `covers` should not be
   quoted in the write-up as a routing accuracy in the meantime.
2. **`p06`'s label is now doing real work and is still unsettled.** It was
   already flagged as *"two routes defensible off the table"*. The model answers
   timing-ish on it in every arm; the key says `fit`. Under standing rule 3 I do
   not get to decide the model is wrong.
3. **`x-n03` joins `x-n20`, `x-n21` and `x-n22`** as a positive that no n=2 arm
   fires on.
