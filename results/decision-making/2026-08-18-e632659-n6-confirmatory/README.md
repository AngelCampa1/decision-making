# Track N6 — the confirmatory grid, on a corpus that is not a word-count ruler

**2026-08-18.** 3 arms × 258 items × 2 repeats = **1,548 isolated `claude -p`
calls**, `haiku`, **0 unparseable in any arm**, 0 isolation failures. Code at
`e632659`.

**Answer key:** `datasets/triggers/decision-making/index.yaml` v4

Prediction: [`notebook/2026-08-18-n6-addendum-the-corpus-shrank-and-the-version-had-to-move.md`](../../../notebook/2026-08-18-n6-addendum-the-corpus-shrank-and-the-version-had-to-move.md),
which supersedes the counts and power figures in the
[2026-08-13 registration](../../../notebook/2026-08-13-n6-prediction-does-accuracy-fall-on-the-long-bands.md)
and its [2026-08-14 amendment](../../../notebook/2026-08-14-n6-unblocked-q1-goes-descriptive-the-test-moves-to-the-ten-point-boundary.md).

**Why this run is different from every trigger number before it.** Every earlier
measurement here ran on a corpus **89% solvable by counting words** — AUC 0.850
on turn length alone. This one runs on trigger corpus v4, whose best depth-2
stump over eight trivial features reads **0.7054** against a majority baseline of
0.6667. The bar an arm has to clear to have measured anything is 0.7054.

| arm | accuracy | precision | recall | FPR | clears 0.7054 |
|---|---|---|---|---|---|
| `stakes-shown` | **0.9477** | 0.8680 | **0.9942** | 0.0756 | +0.242 |
| `full` | 0.9360 | 0.8601 | 0.9651 | 0.0785 | +0.231 |
| `opener-only` | 0.8295 | 0.6641 | 0.9884 | **0.2500** | +0.124 |

## The four registered questions

| | registered | observed | |
|---|---|---|---|
| **Q1** | `excludes_zero and difference > 0` on `bootstrap_rate_difference(control=L+XL, treatment=S+M, cluster_on="triple")`, over **`full`**-arm records | **+0.0976, 95% CI [+0.0459, +0.1493]** (seed 17) | **met** |
| **Q2** | sign of precision(`stakes-shown`) − precision(`full`), as on v2 | **+0.0079** | **sign holds, thinly** |
| **Q3** | `ledger` is the worst-routed of the four procedures, over 19 first-route positives — descriptive | **worst in all three arms**: 0.474, 0.579, 0.105 | **met** |
| **Q4** | **`settled` has the highest FPR of the seven negative kinds** | **`settled` is at the bottom of the ranking in all three arms** — 0.000, 0.025, 0.050 | **falsified** |

**Q1 holds in every arm**, not only the registered one: `full` +0.0976,
`stakes-shown` +0.0948, `opener-only` +0.2367, each excluding zero. The point
estimate is the raw sample difference and does not move with the seed; the
interval bounds move by 0.003–0.010 across seeds, which is why the seed is
stated rather than left to a default.

**Q3 holds more robustly than it was registered.** `ledger` is worst under three
independent descriptions, and in `opener-only` it collapses to 0.105. The
registered reasoning — `ledger` has never been tested on its own case — is not
an artefact of one description.

## Q4 is falsified, and the falsification is narrower than "settled is lowest"

Registered reasoning: *"A negative whose decision has been made and stated is the
one that still looks like a decision."* Predicted `settled` highest, `lookup`
lowest.

**What is robust:** `settled` is nowhere near the top. n = 20, point estimates
0.000 / 0.025 / 0.050 across three arms, and `lookup` — predicted lowest — ranks
fifth or sixth of seven in every arm. The 2026-08-14 amendment had already
established that at n = 20 a 0.000 reading is no longer indistinguishable from
no data, which is why this reads as a result rather than an empty cell.

**What is not robust, and must not ride on it:** *which* kind is actually
highest. It is `meta` (n = 7) in `full` and `stakes-shown` and `compute` (n = 27)
in `opener-only`. In `full`, `meta`'s 0.357 is three of seven items firing.
Checked with `NegativeKindRate.separated_from`, `settled`'s interval is
**separated from `meta` only** in `full`, from **nothing at all** in
`stakes-shown`, and from four kinds in `opener-only`. So "settled is lowest" is a
point-estimate ranking, not a separation, in two arms of three.

## `opener-only` buys recall by collapsing on one band

The pooled FPR of 0.2500 is a blend, and quoting it alone understates what
happened.

| arm | s | m | l | xl |
|---|---|---|---|---|
| `full` | 0.010 | 0.000 | 0.190 | 0.147 |
| `stakes-shown` | 0.021 | 0.000 | 0.179 | 0.132 |
| `opener-only` | 0.073 | 0.104 | **0.524** | 0.368 |

**More than half of `l`-band negatives fire in `opener-only`** — worse than `xl`,
despite `xl` being the longer band — with `compute` negatives firing 6 of 6 and
`lookup` 6 of 11. That is a band-localised qualitative failure at n = 63, not
noise, and it means `opener-only`'s Q1 figure of +0.2367 is not "the same effect,
larger." It is disproportionately one band breaking. Reading the three Q1 numbers
as points on one scale would read a difference in kind as a difference in degree.

## The design effect was assumed roughly 5–25× too large

Registered power used `design_effect(m=3, icc=0.315) = 1.63`, an assumption with
no data behind it, which the 2026-08-14 entry says in its own words. Observed:

| arm | ICC | design effect | effective n |
|---|---|---|---|
| registered assumption | 0.315 | 1.63 | 158.3 |
| `full` | 0.0127 | 1.03 | 251.6 |
| `stakes-shown` | 0.0566 | 1.11 | 231.8 |
| `opener-only` | 0.0000 | 1.00 | 258.0 |

**Conservative, not optimistic** — the registered 0.818 power at Δ = 0.10 was an
understatement. It invalidates nothing, and it must not be reused: 0.315 is now
measured wrong for this instrument.

## Provenance and integrity

- **The answer key and the skill are byte-identical across the whole run**:
  `git diff 19a44c2 e632659 -- skills/ datasets/triggers/` is empty. The run
  spanned three commits, none of which touched either.
- 516 records per arm, 258 distinct cases × exactly 2 repeats, no duplicate
  `(case, repeat)`, every row stamped `set_version: 4` and `model: haiku`,
  identical case sets across arms.
- **Neither void condition fired.** Parse rate is 1.000 in all three arms, so the
  registered floor (below 0.95 in any arm, or a spread above 0.05) is not
  approached.
- The three arms offer the **identical** procedure vocabulary and an identical
  record schema, so the 2026-08-12 defect — scoring one arm's answers against
  names another arm never offered — is absent by construction here.

## Confirmation

Every figure was derived twice by me and once by an independent agent parsing the
JSONL with its own loading and counting code. All agree to four decimal places.
That agent was briefed to find a reason not to publish; three of its objections
are adopted above — the `separated_from` qualification on Q4, the band split on
`opener-only`, and the instruction not to carry `icc = 0.315` forward.

**One weakness the gate cannot see.** An earlier readiness check computed Q1, Q3
and Q4 on the completed `full` arm as a side effect of proving the estimators
could return a non-zero value, which is scoring under another name. The bands
were registered days earlier and are unaltered, and `opener-only` was unseen at
that point — but the sequence is recorded rather than left for a reader to
reconstruct:
[`notebook/2026-08-18-n6-two-arms-in-and-the-bands-were-checked-before-i-meant-to-look.md`](../../../notebook/2026-08-18-n6-two-arms-in-and-the-bands-were-checked-before-i-meant-to-look.md).
