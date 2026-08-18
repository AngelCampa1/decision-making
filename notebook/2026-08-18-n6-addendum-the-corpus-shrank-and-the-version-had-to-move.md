# 2026-08-18 — N6 addendum: the corpus shrank to 258/86, and the version had to move

Supersedes the item counts and power figures in
[N6's 2026-08-13 pre-registration](2026-08-13-n6-prediction-does-accuracy-fall-on-the-long-bands.md)
and [its 2026-08-14 update](2026-08-14-n6-unblocked-q1-goes-descriptive-the-test-moves-to-the-ten-point-boundary.md).
Neither is edited. **N6 has not run.** Everything here is conditional: what N6
would measure, once it is called, against the corpus as it stands.

## The version had to move, and finding out why corrected a decision made hours earlier

`docs/DECISIONS.md`'s earlier entry today reasoned that the rewrite round altered
no `should_fire`, so no published number was affected and `set_version` could
stay where it was. That is true about published numbers and **wrong about what
the version is for.**

Version 3 has named **four different corpora**: 120 items when authored, 192
after the short-band merge, 261 after the long-band merge, 258 after today's
retirement of `l15`. `label_versions_comparable` compares that integer and
nothing else, and the resume path in `run_triggers.py` keys on
`(case_id, repeat)` — it never hashes a case's text. So a version that moves
only when a label flips cannot see a corpus whose *text* changed underneath it,
which is exactly what happened today: eleven asks rewritten, three items
removed, every `should_fire` untouched.

**This has been harmless for one reason only: nothing has ever been scored
against any of the four.** Zero records on disk carry `set_version: 3` —
checked across every `*.jsonl` under `results/`, which reads 2,555 at version 1,
3,139 at version 2, 4,810 unstamped, and none at 3. N6 would be the first, and
it would stamp 1,548 records with a number that does not identify a corpus.

So `index.yaml` moves to **version 4** before the first call rather than after.
It costs nothing — there is nothing to be made incomparable — and it means the
version stamped into N6's records denotes exactly one corpus.

The literal `assert draft.version == 3` in `tests/unit/test_triggers.py` is what
made this a reviewed edit instead of a silent one. It is updated, not removed.

## Q1 — recomputed, and the band holds

S+M is untouched at 144 items / 48 triples; the rewrite round and the retirement
landed entirely in `l`. L+XL drops from 117/39 to **114 items / 38 triples**.
Using the 2026-08-14 entry's own formula and assumptions verbatim —
`se = sqrt(0.95 × 0.05 × (1/n1 + 1/n2) × 1.63)`, with
`design_effect(m=3, icc=0.315) = 1.63` and `m` fixed at 3 by construction:

| | registered (144/117) | current (144/114) |
|---|---|---|
| SE | 0.0346 | 0.0349 |
| MDE at 80% power | 0.0970 | 0.0977 |
| power at Δ = 0.025 | 0.111 | 0.111 |
| power at Δ = 0.050 | 0.303 | 0.300 |
| **power at Δ = 0.100** | **0.823** | **0.818** |
| power at Δ = 0.150 | 0.991 | 0.990 |

**N6 would still be adequately powered at the registered 0.10 consequential
threshold.** The drop is half a point, not a crossing, and it comes entirely
from L+XL losing one triple — S+M dominates the harmonic-sum SE and did not
move.

**The margin is worth naming rather than leaving implicit.** Solving for the
L+XL size at which power at Δ = 0.10 falls to exactly 0.80 gives
**n ≈ 105 items**. The current 114 sits about nine items above that line. One
more retirement round of today's size in the long bands would put this test
under 80% power, and whoever runs the next one should read that before assuming
the headroom is free.

3a (the descriptive interval) and 3b (`excludes_zero and difference > 0`) are
otherwise unchanged: same estimator, `trigger_arms.bootstrap_rate_difference`
on per-item correctness clustered on `triple`; same denominator, the per-item
rate over parsed records in each half; fewer L+XL items feeding it.

## Q3 and Q4 — the two denominators the bands actually rest on are unchanged

Recounted directly from the corpus, not from any document.

| procedure | first-route positives | | kind | negatives |
|---|---|---|---|---|
| **ledger** | **19** (unchanged) | | lookup | 49 (unchanged) |
| fit | 15 (was 16) | | summarise | 28 (was 29) |
| cascade | 16 (unchanged) | | compute | 27 (unchanged) |
| timing | 15 (unchanged) | | generate | 27 (unchanged) |
| | | | **settled** | **20** (unchanged) |
| | | | diagnose | 14 (unchanged) |
| | | | meta | 7 (was 8) |

Q3's band rests on `ledger`'s 19 and Q4's on `settled`'s 20; both are untouched.
The three items lost are `l15`'s — one positive labelled `fit`, and two
negatives of kinds `summarise` and `meta`.

## The bar N6 has to clear moved again

Majority baseline is unchanged at **0.6667**, which is structural — the 1:2
ratio is fixed by construction. The best depth-2 stump reads **0.7054**, lift
**0.0388** against a 0.10 cap, recomputed via `decision_evals.corpus`.

**N6's accuracy is compared against 0.705**, not the 0.701 of 261 items and not
the 0.750 the original registration named. The 2026-08-14 entry already flagged
this direction: shortcut-resistance improving and the bar an arm must clear both
move together, so the margin that means anything keeps shrinking by the same
amount it does.

## Unchanged, and stated so nobody re-derives it

Q2 is a within-corpus sign comparison, not a count-dependent power claim, and is
unaffected. N6's call design is unchanged. So is the 2026-08-14 entry's explicit
**non**-registration of any variance or reliability claim on N6 data: two
repeats can estimate a mean and cannot estimate scatter, and a claim of that
shape would need its own pre-registration and its own repeat budget.

## Before the first call

**1,548 calls** — 3 arms (`full`, `stakes-shown`, `opener-only`) × 258 items × 2
repeats. The tier is **Haiku**, which is what the 2026-08-13 pre-registration
names; it is stated here rather than left to a CLI default, because N8 made
`run_triggers.py` stamp `model` and `models_comparable` refuses a comparison
spanning tiers, so a tier arrived at by default is a parameter nobody chose.

Two checks were run before this entry, both passing, and both are the kind this
repository has been caught skipping:

- **No checkpoint exists at any of the three paths the run would write**
  (`verdicts-decision-making-v4.jsonl` and the two variant names), so every one
  of the 1,548 calls would be made fresh. This matters because today's other
  instrument finding was a run that reported a confident result from zero calls
  after silently resuming.
- **The estimator can return a non-zero value for these arms.** All three read
  the identical fields with the identical meaning — only the description text
  differs — unlike M4/M5, where the offered vocabulary itself changed between
  arms and the scorer graded one arm's answers against another's names.
  Synthetic records pushed through the real scoring path return interior rates
  and a non-zero clustered difference.
