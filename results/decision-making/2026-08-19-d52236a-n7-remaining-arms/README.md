# Track N7 — the remaining three description arms, and a band I substituted

**2026-08-19.** 3 arms × 258 items × 2 repeats = **1,548 isolated `claude -p`
calls**, `haiku`, **0 unparseable**, 0 isolation failures. Code at `d52236a`.

**Answer key:** `datasets/triggers/decision-making/index.yaml` v4

Prediction: [`notebook/2026-08-18-prediction-n7-the-remaining-description-arms.md`](../../../notebook/2026-08-18-prediction-n7-the-remaining-description-arms.md),
committed before the launch rather than during the run.

With [N6](../2026-08-18-e632659-n6-confirmatory/README.md), all six
`--description` arms now sit on one corpus at one key and one tier.

| arm | accuracy | precision | recall | FPR | run |
|---|---|---|---|---|---|
| `no-opener` | 0.9496 | 0.8687 | **1.0000** | 0.0756 | N7 |
| `stakes-shown` | 0.9477 | 0.8680 | 0.9942 | 0.0756 | N6 |
| `full` | 0.9360 | 0.8601 | 0.9651 | 0.0785 | N6 |
| `stakes-named` | 0.9341 | 0.8350 | **1.0000** | 0.0988 | N7 |
| `no-exclusions` | 0.8314 | 0.6641 | **1.0000** | 0.2529 | N7 |
| `opener-only` | 0.8295 | 0.6641 | 0.9884 | 0.2500 | N6 |

## The five registered predictions: one met cleanly, one met, three falsified

| # | registered | outcome |
|---|---|---|
| 1 | `no-exclusions` FPR > 0.0785 | **met** — 0.2529 |
| 2 | `no-opener` recall < 0.9651 | **falsified** — 1.0000 |
| 3 | `stakes-named` recall < 0.9942 | **falsified** — 1.0000 |
| 4 | `no-exclusions` over-fires on `l`/`xl` | **met** — s 0.073, m 0.104, l 0.476, xl 0.441 |
| 5 | no arm beats both `stakes-shown` recall and `full` FPR | **falsified — and the band was mine, not L7's** |

## The table's ordering is not a result

`no-opener` tops it and does not survive the paired test.

| comparison | discordant | split | p |
|---|---|---|---|
| `no-opener` vs `stakes-shown` | 26 | 13–13 | 0.86 |
| `no-opener` vs `full` | 32 | 19–13 | 0.35 |

FPRs equal to full float precision (0.07558139…), accuracy gap 0.0019. **The top
three arms are not distinguishable at n = 258.** What is distinguishable is the
bottom pair, 11 points down at three times the FPR.

`no-exclusions` and `opener-only` share a precision of 0.6641 and **disagree on
33 of 258 items**, split 16–17. The matching aggregates are cancellation, not
equivalence.

## Prediction 5 was not the band it claimed to be

L7's registered band 4 was **FPR ≤ 0.06 and recall ≥ 0.94**. What was registered
here re-derived both thresholds from N6's observed numbers — recall 0.9942, FPR
0.0785 — while citing L7 by name. The substitution flips the verdict:
`no-opener` clears the substituted band and **fails L7's**, since 0.0756 > 0.06.

**L7's band 4 still fails on N7 data.** No arm of six reaches FPR ≤ 0.06. The
frontier is intact after ten arms, and this run's own prediction would have
reported it broken. Recorded as the fifth pre-registration defect, with a
mechanism not previously catalogued: re-deriving a prior band's thresholds from a
later run's results while naming the prior band.

## Recall has no unreachable item on v4, which is worth having and weakens one axis

Three arms miss nothing. `full` misses five (`l20p`, `m11p`, `s13p`, `s17p`,
`s21p`), `opener-only` two, `stakes-shown` one. **No positive is unfireable in
every arm** — unlike v2/v3, where `x-n22` fired in no arm on any version and
capped every recall band set against a round number.

The cost: with half the field tied at recall 1.0000, a two-axis claim is mostly
an FPR contest, and the two leaders are tied there too.

## Provenance

- 516 records per arm, 258 distinct cases × exactly 2 repeats, every row stamped
  `set_version: 4` and `model: haiku`, case sets identical across all six arms.
- Parse rate 1.000 in all three arms; the registered void conditions (below 0.95
  in any arm, or a spread above 0.05) are not approached.
- `label_versions_comparable` **refuses** comparing L5's v1 `no-opener` (0.9671,
  73 items × 5 repeats, ruler 0.890) against this one (0.9496, 258 × 2, ruler
  0.7054), and is right to. A second instance of the same qualitative pattern on
  a differently-built corpus is not a replication.
- Every figure re-derived through the repository's own estimators by an
  independent agent briefed to break the interpretation, and again by hand. No
  arithmetic disagreement; three of its objections are adopted above.

**Venue caveat.** Every number here was measured with the description as the
entire system prompt and the turn under test as the only message — the proxy
`run_triggers.py`'s docstring names. That is **N9**, added to the programme on
2026-08-18, and it has not run.

Working:
[`notebook/2026-08-19-n7-four-of-five-predictions-wrong-and-a-band-i-substituted.md`](../../../notebook/2026-08-19-n7-four-of-five-predictions-wrong-and-a-band-i-substituted.md).
