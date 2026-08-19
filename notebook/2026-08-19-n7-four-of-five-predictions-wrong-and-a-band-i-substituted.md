# 2026-08-19 — N7: four of five predictions wrong, and a band I substituted for the one I claimed to test

Outcome of the run registered in
[the prediction entry](2026-08-18-prediction-n7-the-remaining-description-arms.md),
committed **before** the launch. **1,548 calls**, three arms × 258 items × 2
repeats, `haiku`, key **v4**, **0 unparseable**. All six `--description` arms now
exist on the same corpus at the same key and tier.

Every figure re-derived independently through the repository's own estimators by
an agent briefed to break the interpretation, and again by me. No arithmetic
disagreement.

## All six arms

| arm | accuracy | precision | recall | FPR |
|---|---|---|---|---|
| `no-opener` | 0.9496 | 0.8687 | **1.0000** | 0.0756 |
| `stakes-shown` | 0.9477 | 0.8680 | 0.9942 | 0.0756 |
| `full` | 0.9360 | 0.8601 | 0.9651 | 0.0785 |
| `stakes-named` | 0.9341 | 0.8350 | **1.0000** | 0.0988 |
| `no-exclusions` | 0.8314 | 0.6641 | **1.0000** | 0.2529 |
| `opener-only` | 0.8295 | 0.6641 | 0.9884 | 0.2500 |

## The predictions

| # | registered | outcome |
|---|---|---|
| 1 | `no-exclusions` FPR > `full`'s 0.0785 | **met** — 0.2529 |
| 2 | `no-opener` recall < `full`'s 0.9651 | **falsified** — 1.0000 |
| 3 | `stakes-named` recall < `stakes-shown`'s 0.9942 | **falsified** — 1.0000 |
| 4 | `no-exclusions`' false firing concentrates in `l`/`xl` | **met** — s 0.073, m 0.104, l 0.476, xl 0.441 |
| 5 | no arm beats both `stakes-shown`'s recall and `full`'s FPR | **falsified** — and see below, because this one is my defect rather than a finding |

**One of five, and the two that held are the two that were easy.** Deleting the
exclusion list costs precision, and false firing lives in the long bands: both
were already visible in L5 and in N6.

## Prediction 5 is a pre-registration defect, and a new one

I wrote that prediction 5 tested L7's frontier finding. **It did not.** L7's band
4 was *"one arm at FPR ≤ 0.06 **and** recall ≥ 0.94"*. What I registered was
*"no arm beats both `stakes-shown`'s recall (0.9942) and `full`'s FPR
(0.0785)"* — thresholds I re-derived from N6's observed numbers instead of
reusing L7's.

The substitution moved both bars in opposite directions: **recall from 0.94 up to
0.9942, FPR from 0.06 down-loosened to 0.0785.** And it flips the verdict.
`no-opener` at recall 1.0000 / FPR 0.0756 clears my band and **fails L7's**,
because 0.0756 > 0.06.

**So L7's band 4 still fails on N7 data.** No arm of six reaches FPR ≤ 0.06; the
best is 0.0756. The precision/recall frontier L7 described is intact after ten
arms, and my entry would have reported it broken.

This is the fifth pre-registration defect on record and the mechanism is not one
of the four already catalogued: **re-deriving a band's thresholds from a later
run's observed values while citing the earlier band by name.** It is worse than
inventing a number, because it looks like continuity with the prior work. The
rule it needs: *when a run tests a previously registered band, quote that band's
numbers verbatim; a threshold that is re-derived is a new band and must say so.*

## The headline result is not a result

`no-opener` tops the table, and I was about to report that deleting the clause
which says what the skill is for produces the best arm. **It does not survive the
paired test.**

| comparison | discordant | split | p |
|---|---|---|---|
| `no-opener` vs `stakes-shown` | 26 | 13–13 | **0.86** |
| `no-opener` vs `full` | 32 | 19–13 | **0.35** |

Their FPRs are equal *to full float precision* — both 0.07558139… — and the
accuracy gap is 0.0019. **The top three arms are not distinguishable at n = 258.**
The ordering in the table is noise, and "`no-opener` is the best arm" is a
sentence about rounding.

What is distinguishable is the bottom pair from the top three: `no-exclusions`
and `opener-only` sit 11 points down with three times the FPR.

## Recall is at ceiling for half the field, which weakens the axis it sits on

Three arms miss **nothing at all**. `full` misses five positives (`l20p`,
`m11p`, `s13p`, `s17p`, `s21p`), `opener-only` two, `stakes-shown` one.

**No positive is unreachable** — unlike v2/v3, where `x-n22` fired in no arm on
any version and quietly capped every recall band that was set against a round
number. That is a property of the rebuilt corpus worth having.

But it means a two-axis claim is mostly a one-axis contest here: with half the
arms tied at recall 1.0000, "beats both axes" reduces to which of them has the
lower FPR, and the two leaders are tied there as well. My prediction 5 framed
itself as a frontier test when one of its two axes was flat across the field.

## L7's stakes mechanism does not appear

`stakes-named` was predicted to trail on recall, because L7 read it refusing
positives that `stakes-shown` accepted — `x-n03` at 0/2 against 2/2 — and
called that *"naming stakes as a criterion makes the model apply it strictly."*
On v4 `stakes-named` reaches recall 1.0000, the same as `stakes-shown`'s
neighbourhood, at a worse FPR (0.0988 against 0.0756).

**My own registered "where I expect to be wrong" called this**: L7's evidence was
two items, both positives kept on a maintainer's judgement, both on the old key.
The mechanism does not reproduce on a corpus built to resist a ruler. The
honest reading is that L7 found two idiosyncratic items.

## `no-opener` at v1 and at v4: suggestive, and not a replication

`docs/LIMITATIONS.md` records that at label version 1 the best description arm
was `no-opener` at 0.967, *"published without an accuracy column and therefore
never noticed."* It is again at or tied for the top on v4.

**`label_versions_comparable` refuses the comparison and it is right to.**
Checked directly: it raises *"these arms were scored against different label
revisions: [1] against [4]."* The two runs are not one corpus at two labels —
73 items × 5 repeats against 258 × 2, and rulers at 0.890 against 0.7054. Raw
accuracy is **lower** on v4 (0.9496 against 0.9671) while the margin over the
trivial-feature ceiling is far larger (+24.4pp against +7.7pp).

So: a second independent instance of the same qualitative pattern on a
differently-built corpus. Not a replication in any measurable sense, and both
halves of that sentence have to travel together.

## One coincidence worth not mistaking for a finding

`no-exclusions` and `opener-only` have precision identical to four decimals
(0.6641) and FPRs 0.0029 apart. **They disagree on 33 of 258 items** — 12.8% —
split 16–17. The matching aggregates are cancellation, not equivalence. Anyone
quoting the two as "the same arm" would be reading a coincidence.

## What N7 licenses

Narrow. On a corpus whose trivial-feature ceiling is 0.7054: **deleting the
exclusion list costs about 11 accuracy points and triples false firing;
everything else in the description is, at this n, not measurably load-bearing.**
Ten arms in, L7's frontier still holds — no description has reached FPR ≤ 0.06
at recall ≥ 0.94, and the descriptions that differ most differ mainly in how
much they over-fire on long turns.

And the venue caveat now has a row of its own: every number above was measured
with the description as the entire system prompt and the turn as the only
message. That is **N9**, and it has not run.
