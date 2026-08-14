# The guard was built and the records were never reconciled

**2026-08-13.** Not a run. No model call was made for anything in this entry.

## What was wrong

`trigger_arms.label_versions_comparable` was written the morning of 2026-08-13
to refuse a comparison spanning the label move, and it works. It refused
**every** cross-arm pairing this repository publishes.

Nine checkpoints in `results/triggers/` carried no `set_version` at all and two
carried `2`. The guard's "one stamped, one not" branch fires on all eighteen
pairs, including `full` against `stakes-shown` — the pairing an unstarted
pre-registration was about to use as its replication baseline. A refusal with no
remedy on disk is a wall rather than a gate, and nothing said so: `de check` was
green throughout, because nothing looked at the checkpoint directory.

## How the version of the unstamped records was determined

**Not from their timestamps.** The runner bakes `should_fire` and `route` into
every row at write time, so a checkpoint carries the key it was scored against
inside itself. Loading the v1 key from `d43c490~1` and the current v2 key and
joining both to every row by case id:

| checkpoint | vs v1 | vs v2 |
|---|---|---|
| all nine unstamped files | 0 label mismatches | 1 mismatch, `x-n21` |
| `verdicts-stakes-named`, `verdicts-stakes-shown` | 1 mismatch, `x-n21` | 0 mismatches |

`x-n21` — *"The disk is at 99%. Do we need to act?"* — is the turn `d43c490`
moved from the positives to the negatives at 09:43. `903169c` added
`set_version` at 09:48. Nothing could have been scored against v2 without being
stamped, and the labels say so independently of the clock.

## What now exists

- Every row in `results/triggers/` carries `set_version`. The nine unstamped
  files were stamped `1`; nothing else in them changed, verified row by row.
- Nine `rescored-*-v2.jsonl` files re-score the v1 arms against the v2 key. Each
  row carries `record_kind: "rescore"`, `rescored_from` and
  `rescored_from_set_version`, **per row**, because the unit a script meets is a
  line and the improvement is real as a label correction and would be a
  fabrication as a model result.
- `covers` is not re-scored. It depends on the arm's entry partition, which the
  record does not carry. Where a case's routes changed it is set to `None` with
  `covers_stale` giving the reason, so the denominator shrinks visibly.
- `de rescore` writes all of it. `de check`'s new **checkpoint label versions**
  step refuses an unstamped row, a file mixing versions, a re-score in a run's
  clothing, a stale bridge, and a cross-version pair with no bridge.
- The register of which key each pre-versioning checkpoint used lives in
  `[tool.decision-evals.unstamped-checkpoints]`, with the derivation written
  above it. `de rescore` will not act on a default.

## The full re-score, per arm

Firing only. Verdicts unchanged; only the key moved.

| arm | acc v1 → v2 | prec v1 → v2 | recall v1 → v2 | FPR v1 → v2 |
|---|---|---|---|---|
| `full` (shipped) | 0.9562 → **0.9699** | 0.9405 → 0.9405 | 0.8778 → **0.9294** | 0.0182 → 0.0179 |
| `four` (M4) | 0.9507 → **0.9589** | 1.0000 → 0.9861 | 0.8000 → **0.8353** | 0.0000 → 0.0036 |
| `2-entries` (M5) | 0.9397 → **0.9534** | 1.0000 → 1.0000 | 0.7556 → **0.8000** | 0.0000 → 0.0000 |
| `opener-only` (L5) | 0.9041 → **0.8904** | 0.7350 → 0.6923 | 0.9556 → 0.9529 | 0.1127 → 0.1286 |
| `no-opener` (L5) | 0.9671 → **0.9753** | 1.0000 → 0.9872 | 0.8667 → **0.9059** | 0.0000 → 0.0036 |
| `no-exclusions` (L5) | 0.9370 → **0.9452** | 0.8454 → 0.8351 | 0.9111 → **0.9529** | 0.0545 → 0.0571 |
| `pairing ledger+cascade` (M6) | 0.9521 → **0.9658** | 1.0000 → 1.0000 | 0.8056 → **0.8529** | 0.0000 → 0.0000 |
| `pairing ledger+timing` (M6b) | 0.9452 → **0.9589** | 0.9667 → 0.9667 | 0.8056 → **0.8529** | 0.0091 → 0.0089 |
| `confidence` | 0.9726 → **0.9863** | 1.0000 → 1.0000 | 0.8889 → **0.9412** | 0.0000 → 0.0000 |
| `stakes-named` (L7) | *0.9452* → 0.9589 | 0.9375 → 0.9375 | *0.8333* → 0.8824 | 0.0182 → 0.0179 |
| `stakes-shown` (L7) | *0.9658* → 0.9795 | 1.0000 → 1.0000 | *0.8611* → 0.9118 | 0.0000 → 0.0000 |

Italics are counterfactual: the two L7 arms only ever ran under v2.

Routing accuracy, by name, over the arms whose `procedure` column holds
procedure names — a turn with two acceptable routes is easier to hit, so this
moves for a second reason as well:

| arm | v1 → v2 | n |
|---|---|---|
| `full` | 0.6857 → 0.7571 | 70 |
| `no-exclusions` | 0.7429 → 0.8286 | 70 |
| `no-opener` | 0.6714 → 0.7429 | 70 |
| `opener-only` | 0.4286 → 0.5000 | 70 |
| `stakes-named` | 0.6429 → 0.7143 | 28 |
| `stakes-shown` | 0.7143 → 0.7857 | 28 |
| `confidence` | 0.7143 → 0.7857 | 14 |

**This re-derives `notebook/2026-08-13-one-label-moved-and-every-arm-improved.md`
exactly** — five arms, FPR and recall, every figure.

**And the table above was itself confirmed**, per the working method: a second
agent, told not to read `notebook/` or `docs/` and given only the two YAML keys
and the raw JSONL, recomputed accuracy and the raw `(tp, fp, tn, fn)` for all
eleven files under both keys, plus the ruler sweep. Every cell matched. It
returned two things this entry had not: that the ruler ties at T=16 and T=18 on
both keys, and that the highest accuracy on record is the `confidence` arm
rather than any description arm — which corrected a sentence that had already
been written into five documents by the time it landed.

## What the re-score turned up that nobody had computed

**"The best arm ever measured scores 0.956" was wrong at both versions.**

0.956 is the `full` arm at **v1**. The ruler it was quoted against — 0.890 —
is a **v2** number: the same word-count rule scores 0.877 on the v1 key. So the
"about six points of headroom" figure in five documents was a comparison across
a label revision, which is the move the guard refuses.

It was also the wrong arm, twice over. At v1 the best *description* arm was
`no-opener` at **0.9671**, published in L5 on 2026-08-12 — and L5 reports FPR,
recall, precision and routing with **no accuracy column**, so the number existed
on disk and had never been computed. The one accuracy figure anybody had
published was M4's, and it was quoted as a maximum it never was.

And higher than either is the `confidence` arm — the shipped description with a
probability also elicited — at **0.9726** (v1) and **0.9863** (v2). That one is
one repeat over 73 cases against five for the 365-row arms, so it is the
thinnest estimate of the eleven, and `run_triggers.py` says in its own docstring
that a confidence run and a plain one stay comparable **on the firing axis and
only there**. It is therefore a legitimate entry in this column and the weakest
one. Reported rather than picked.

Within a version the headroom is about **nine points either way**, and the
figure does not depend on which of those readings is taken:

| key | word-count ruler | best description arm | highest on record | headroom |
|---|---|---|---|---|
| v1 | 0.877 (T=16 or T=18) | `no-opener` 0.9671 | `confidence` 0.9726 | 9.0–9.6 pts |
| v2 | 0.890 (T=16 or T=18) | `stakes-shown` 0.9795 | `confidence` 0.9863 | 8.9–9.6 pts |

Nine rather than six does not rescue Tracks L and M — a ceiling at nine points
is still a ceiling and **Track N** still has to run. But the sentence the
programme had written down was arithmetic across two answer keys, and the number
it produced was three points too small in the direction that made the nulls look
more forgivable.

## The rule

**A sentence of the form "the best arm ever measured scores X" cannot be written
without naming the arm and the label version.** X is not a property of the
skill. It is a property of a checkpoint, a key and an estimator, and two of
those three were missing every time this one was written.

The corollary is why the gate is in `de check` rather than in anyone's memory:
the defect was not that somebody compared across versions, it was that **nothing
on disk could tell you they had**. An unstamped record reads as v1 to the guard
and as nothing at all to every other reader.

## What was deliberately not done

`results/decision-making/*/README.md` was not edited. Those are the record and
how to correct them is the maintainer's call; the numbers that are now known to
be wrong are listed in the handover rather than fixed here. Two of them are in
the L7 README, which declares v2 and carries two v1 precision figures in its
results table.
