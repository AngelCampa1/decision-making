# M6b: a merged entry is not the union of its parts

**2026-08-13.** Outcome for
[the prediction](2026-08-13-m6b-prediction-the-third-partition-and-a-mechanism-that-names-one-item.md),
committed at `5ccedb9` before any calls. Track M6, third and final partition.
**146 isolated calls** (73 × 2), Haiku, **0 unparseable, 0 isolation failures**.

Scored with `decision_evals.trigger_arms`, which reproduces the other two arms'
published numbers from their own checkpoints.

## Scored as registered

| # | Prediction | Band | Observed | |
|---|---|---|---|---|
| 1 | Parseable verdicts | ≥ 98% | **100%** (146/146) | ✅ |
| 2 | **`p06` falls back** | ≤ 0.5 | **0.5** | ✅ |
| 3 | `covers` between the other two | 0.74–0.86 | **0.571** | ❌ |
| 4 | Firing accuracy unmoved | 0.90–0.97 | **0.945** | ✅ |
| 5 | FPR at the floor | ≤ 0.018 | **0.009** | ✅ |
| 6 | No firing difference from either n=2 arm | both p ≥ 0.05 | **0.893** (M5), **0.564** (M6) | ✅ |

**Band 2 passed and I am not going to claim much for it.** At two repeats `p06`
can only take 0, 0.5 or 1, so "≤ 0.5" was a two-in-three band before the run
started. It landed on the boundary. The direction is right and the test was weak.

**Band 3 is the miss and it is the result.**

## The three partitions of one skill

| partition | `covers` | firing accuracy | FPR |
|---|---|---|---|
| `ledger-fit` / `cascade-timing` (M5) | 0.743 | 0.940 | 0.000 |
| `ledger-cascade` / `fit-timing` (M6) | **0.857** | 0.952 | 0.000 |
| **`ledger-timing` / `fit-cascade` (M6b)** | **0.571** | 0.945 | 0.009 |

**A 28.6-point range.** Same four procedures, same entry count, same words —
the three arms are word-multiset identical to each other by construction and by
test — and the routing number moves by more than a quarter of its scale
depending only on which two procedures were put in a box together.

Firing does not move at all: p = 0.89 against M5, p = 0.56 against M6.

## The mechanism is worse than M6 said

M6 concluded that the partition decides *which confusions are forgiven*. The
third partition shows something stronger, and `p01` and `p02` are where it is
visible. Both are labelled `ledger`:

| item | M5 (`ledger-fit`) | M6 (`ledger-cascade`) | **M6b (`ledger-timing`)** |
|---|---|---|---|
| `p01` | `ledger-fit` ×5 ✅ | `ledger-cascade` ×2 ✅ | **`fit-cascade` ×2 ❌** |
| `p02` | `ledger-fit` ×5 ✅ | `ledger-cascade` ×2 ✅ | **`fit-cascade` ×2 ❌** |

In two partitions the model picks the entry containing `ledger`. In the third it
picks **the entry that does not contain `ledger` at all** — and does so
unanimously, on both items, in both repeats.

So the model is not choosing "the entry that holds the right procedure, allowing
for the merge". It is reading each merged sentence and picking whichever *reads*
more like the message. When `ledger`'s clause — *"a pile of context arrived and
it is unclear what the answer turns on"* — is joined to `timing`'s — *"the
direction is settled and the question is when"* — the resulting sentence stops
attracting pile-of-context messages, and the other entry wins.

**A merged entry is not the union of its parts.** Joining two conditions with
*"or"* produces a description that does not reliably inherit either one's pull.
That is a fact about how descriptions are read, not about how procedures are
grouped, and nothing in M4 or M5 could have shown it because both of those
varied count rather than composition.

## What this does to the numbers already published

- **`covers` is dead as a routing statistic and this is the third and final
  nail.** It was already not comparable across `n` (chance moves) and not
  comparable across partitions (M6). It now has a measured range of 28.6 points
  across the complete set of partitions at fixed `n`, which is larger than any
  effect the M track has looked for. M5's 0.743 and M6's 0.857 keep their values
  and neither is an estimate of anything.
- **The n=2 false-positive floor is not structural.** M5 and M6 both read 0.000
  and M5's outcome entry called the floor "reached at two entries". M6b reads
  **0.009** — `n07` false-fires once. The floor is low, not absolute, and the
  M5 entry's phrasing was stronger than two arms licensed.
- **Firing survives everything.** Five manipulations now — structure (M4),
  content (L5), count (M5), and composition twice (M6, M6b) — and not one has
  moved how well this description discriminates. That is the M track's finding
  and it is much better supported than anything about routing.

## What I would tell the maintainer

1. **Routing cannot be measured on a merged arm at all.** Not with `covers`, not
   with exact names. The only honest options are to score routing solely at n=4,
   where entry names are labels, or to change the response contract so the model
   names a procedure inside the entry it chose — which is a new manipulation and
   needs its own arm. **M3's question is open and this instrument cannot close
   it.**
2. **The shipped skill has one entry, so none of this touches it directly** —
   but the `or`-joining result is a live warning for any future skill whose
   description covers several conditions in one sentence. The parts do not add.
3. **`p01` and `p02` are the two cleanest items in the set** and they went 5/5,
   2/2, 0/2. If any single observation in this repository deserves a second
   model tier, it is that one.
