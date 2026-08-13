# Track M6b — the third and final partition

**2026-08-13.** 73 cases × 2 repeats = **146 isolated `claude -p` calls**, Haiku,
0 unparseable, 0 isolation failures. Code at `5ccedb9`.

There are exactly three ways to split four procedures into two entries of two.
This is the third, so the set is now complete:

| partition | run | `covers` | firing accuracy | FPR |
|---|---|---|---|---|
| `ledger-fit` / `cascade-timing` | [M5](../2026-08-12-c2673c5-m5-two-entries/) | 0.743 | 0.940 | 0.000 |
| `ledger-cascade` / `fit-timing` | [M6](../2026-08-13-82b4ab8-m6-pairing/) | **0.857** | 0.952 | 0.000 |
| **`ledger-timing` / `fit-cascade`** | **this** | **0.571** | 0.945 | 0.009 |

All three arms are **word-multiset identical** to each other — the same four
conditions and four products merged three ways, the shared opener and exclusions
unchanged, `or` the only connective any of them adds. Asserted by test.

## The routing measure has a 28.6-point range across partitions

That is larger than any effect the M track has gone looking for, and it is
produced entirely by which two procedures share a box.

Firing, meanwhile, does not move: paired Wilcoxon **p = 0.893** against M5 and
**p = 0.564** against M6, over 73 items each.

## A merged entry does not inherit its parts' pull

`p01` and `p02` are both labelled `ledger` and are the cleanest positives in the
set:

| item | M5 (`ledger-fit`) | M6 (`ledger-cascade`) | this run (`ledger-timing`) |
|---|---|---|---|
| `p01` | `ledger-fit` ×5 | `ledger-cascade` ×2 | **`fit-cascade` ×2** |
| `p02` | `ledger-fit` ×5 | `ledger-cascade` ×2 | **`fit-cascade` ×2** |

In the third partition the model unanimously picks **the entry that does not
contain `ledger`**. Joining `ledger`'s condition — *"a pile of context arrived
and it is unclear what the answer turns on"* — to `timing`'s — *"the direction is
settled and the question is when"* — produces a sentence that stops attracting
pile-of-context messages.

So the model reads each merged sentence and picks whichever reads more like the
message, rather than locating the procedure and reporting its box. **`covers` is
retired as a routing statistic**, and routing on a merged arm has no estimator.

## The n=2 false-positive floor is low, not absolute

M5 and M6 both read 0.000 and M5's write-up called the floor "reached at two
entries". This arm reads **0.009** — `n07` false-fires in one repeat of two. The
earlier phrasing was stronger than two arms licensed and is corrected in place.

## Caveats

- **One model tier, one instrument.** Haiku, and a proxy.
- **Two repeats**, justified by ICC 0.833/0.852 on the previous arms. It coarsens
  per-item rates to {0, 0.5, 1}; `p06`'s registered band was consequently a
  two-in-three band and it is not claimed as a strong test.
- The partition set is complete **at n=2 only**. n=3 partitions are unrun.

## Columns

`case`, `repeat` (0–1), `fired`, `procedure` (the entry named), `covers`,
`p_fire` (null), `should_fire`, `route`, `raw`.

## Reproducing

```bash
python scripts/run_triggers.py --pairing "ledger+timing,fit+cascade" --repeats 2
```

**Answer key:** [`datasets/triggers/decision-making.yaml`](../../../datasets/triggers/decision-making.yaml) **v1**. Not comparable with a v2 run: on 2026-08-13 one turn moved from the positives to the negatives and recall rose on every arm on disk with no call re-made.
Prediction: [`notebook/2026-08-13-m6b-prediction-the-third-partition-and-a-mechanism-that-names-one-item.md`](../../../notebook/2026-08-13-m6b-prediction-the-third-partition-and-a-mechanism-that-names-one-item.md).
Outcome: [`notebook/2026-08-13-m6b-the-merged-entry-is-not-the-union-of-its-parts.md`](../../../notebook/2026-08-13-m6b-the-merged-entry-is-not-the-union-of-its-parts.md).
