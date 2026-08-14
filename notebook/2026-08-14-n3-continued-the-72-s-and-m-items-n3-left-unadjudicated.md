# 2026-08-14 — N3 continued: the 72 S and M items N3 left unadjudicated

N3 (2026-08-13) ran blind adjudication on 120 of the corpus's items — the first
120 authored, one length band at a time. The corpus has since grown to 261
items (the same-day long-band merge recorded in
[`2026-08-14-the-long-band-merge-closed-one-leak-and-opened-two.md`](2026-08-14-the-long-band-merge-closed-one-leak-and-opened-two.md)),
and inventory against `results/triggers/adjudication.jsonl` shows **141 items
with zero adjudication records**, split `m 42, l 39, s 30, xl 30`.

L and XL are excluded from this run: a separate session is editing
`l.yaml`/`xl.yaml`/`corpus-baseline.txt` right now to close an `open`-view leak
(`question_marks` / `terminal_question`, matched 0.629, 6.12 null SE — the same
merge entry above), so their text is not stable and any verdict against it
would be adjudicating turns that no longer exist by the time anyone reads the
record. This run covers only the 72 S+M items with no record: `s15`-`s24` and
`m11`-`m24`, three cases each (`n1`, `n2`, `p`) — 216 calls, `--model haiku` to
match N3's own instrument, via:

```
scripts/adjudicate.py --only "@<72 ids, one per line>" --report-only   # dry run, confirmed 0 existing records for these ids
scripts/adjudicate.py --only "@<same file>"                            # the run
```

using the `--only` flag added in `1e05384` for exactly this — N3's own script
had no way to touch a subset, so a re-run meant re-adjudicating all 120 items
already on record.

## Prediction, before running

N3's per-band movement on the first half of each band: `s 2/42 (0.048)`,
`m 0/30 (0.000)`. I expect the second half of each band to look similar, since
both halves were authored to the same rubric and by the same process — no
change of authorship or method separates `s01`-`s14`/`m01`-`m10` from
`s15`-`s24`/`m11`-`m24`. Concretely:

- Movement rate over the 72 new items: low, most likely **0-2 items moving**
  (rate 0.00-0.03), comfortably under the 0.20 kill.
- Unanimous-with-key: high, in the 0.85-0.95 range N3 measured overall (0.917).
- Fleiss kappa / Krippendorff alpha: high (N3: 0.890), for the same reason N3
  flagged — three instances of one model are not three independent raters, so
  a high value here is reproducibility of the reading, not proof the labels are
  right. Repeated below so it is not misquoted from this entry either.

**Where I expect to be wrong.** N3's S band was the *only* band with nonzero
movement in the first 42 items (M, L both sat at exactly 0.000). If S carries a
harder-to-write-correctly property that isn't a length effect — short turns
leave less room for an unambiguous ask, and shortness is a per-item authoring
choice, not something this second batch changes — S could plausibly clear one
or two more moves than M does again. I would not read a repeat of that
asymmetry as surprising; I would read a *reversal* (M moving, S staying at
zero) as worth a closer look at what changed between the two authoring passes.

## Result

216 blind adjudications, 3 judges × 72 turns, 0 unparseable, `--model haiku`
matching N3's own instrument. Judges saw the turn and the shipped `Abort if`
clauses (checked directly in `scripts/adjudicate.py`'s `SYSTEM` constant and
`abort_clauses()` before running — neither the label, the case id, the band,
nor the skill description under test elsewhere ever reaches the prompt).

```
cases                72
unanimous with key   0.875
contested (2-1 kept)   5
moved (2-1 against)    4
movement rate        0.056   (pre-registered kill above 0.20)

inter-rater agreement, key not involved:
  pairwise agreement  0.935
  unanimous judges    0.903
  Fleiss kappa        0.857
  Krippendorff alpha  0.858

movement by band:
  m     3/42   0.071
  s     1/30   0.033
```

**The corpus survives the pre-registered kill by a factor of over three (0.056
against the 0.20 threshold), and by a factor of nearly six on the combined
192-item figure below.** The prediction's numeric range (0.00-0.03 movement)
undershot the actual 0.056 — four items moved rather than zero to two — but the
qualitative call (low, nowhere near the kill) held.

**The one place the prediction was checked and found wrong, as flagged in
advance.** I wrote before running that a *reversal* of N3's S-moves/M-holds
asymmetry would be the surprising outcome. That is exactly what happened: `s`
moved 1/30 (0.033) this time, against N3's 2/42 (0.048) on the first half; `m`
moved 3/42 (0.071) this time, against N3's 0/30 (0.000) on the first half. Four
items and one item are both too few to support a claim about which band is
harder to label — this is recorded as a checked-and-reversed prediction, not as
a finding that M is now the harder band.

## The four labels that moved

| case | direction | votes |
|---|---|---|
| `m14n2` | negative → positive | **(True, True, True)** — unanimous |
| `m16n2` | negative → positive | (True, True, False) |
| `m18p` | positive → negative | **(False, False, False)** — unanimous |
| `s19n2` | negative → positive | (True, True, False) |

Combined with N3's three (`s02n2`, `s12p`, `xl05n2`), **seven adjudicated moves
are now on record and unapplied**, dated:

| case | direction | votes | adjudicated |
|---|---|---|---|
| `s02n2` | negative → positive | (False, True, True) | 2026-08-13 (N3) |
| `s12p` | positive → negative | (True, False, False) | 2026-08-13 (N3) |
| `xl05n2` | negative → positive | (True, True, True) | 2026-08-13 (N3) |
| `m14n2` | negative → positive | (True, True, True) | 2026-08-14 |
| `m16n2` | negative → positive | (True, True, False) | 2026-08-14 |
| `m18p` | positive → negative | (False, False, False) | 2026-08-14 |
| `s19n2` | negative → positive | (True, True, False) | 2026-08-14 |

**None of these seven is applied here.** Moving a label bumps the answer-key
version and invalidates every comparison across the boundary; the key moves
**once**, at the freeze, carrying all seven plus whatever N4-N7 add — not once
per adjudication batch. Applying now would mean an eighth version bump on top
of the seven this repository already has reasons to avoid stacking.

## The combined picture: N3 plus this run, 192 of 261 items

S and M are now **fully adjudicated** (72/72 each). L and XL remain at N3's
original coverage (27/66 and 21/51) — untouched here, on purpose, because a
separate session is mid-edit on `l.yaml`/`xl.yaml`/`corpus-baseline.txt` to
close the `open`-view leak (`question_marks`/`terminal_question`, matched
0.629, 6.12 null SE) and any verdict against text that changes under it would
be void. Scoping `--only` to exactly N3's original 120 ids plus this run's 72
(192 total, `scripts/adjudicate.py --only "@<192 ids>" --report-only`):

```
cases                192
unanimous with key   0.906
contested (2-1 kept)  11
moved (2-1 against)    7
movement rate        0.036   (pre-registered kill above 0.20)

inter-rater agreement, key not involved:
  pairwise agreement  0.948
  unanimous judges    0.922
  Fleiss kappa        0.885
  Krippendorff alpha  0.885

movement by band:
  l     0/27   0.000
  m     3/72   0.042
  s     3/72   0.042
  xl    1/21   0.048
```

**Not a finding distinct from the two runs above** — it is the same 192 records
folded together, reported because a reader is going to want the running total
rather than two separate small numbers. 0.885 sits almost exactly on N3's
own 0.890.

## The caveat N3 recorded, carried forward unchanged

**κ = 0.857 (this run) / 0.885 (combined) must not be read as evidence the
labels are right, for the same reason N3 gave and no additional reason this run
adds.** Three adjudicators are three independent instances of the same model
given the same prompt, not three independent human raters in the sense Fleiss'
κ assumes. What a high κ shows is that the question is well-specified enough
for one model's reading of it to reproduce three times running — the
instrument's reliability, not the corpus's validity. N3's own N4 (a human
holdout, ~20 turns, never seen by me before authoring closes) is still the only
thing in this repository's plan that would separate the two, and it has not
run. Repeating this every time the number is quoted is deliberate: N3's version
of this caveat is one entry away from this one, and a reader who finds only
this file should not have to chase the earlier one to get the same warning.

## Process note

While this ran, a check of the shared checkpoint showed 205 cases on record
rather than the 192 this entry accounts for (120 N3 + 72 here) — 13 more `l`
and `xl` cases (`l10p`, `l13p`, `l14n2`, `l18p`, `l20n1`, `l22p`,
`xl08n1`, `xl09n1`, `xl10p`, `xl11n2`, `xl12p`, `xl16p`, plus `xl01`-`xl07`
already counted) than N3 left behind. That is a different session adjudicating
some of the newly-merged long-band items concurrently with the leak fix
mentioned above — not this run, not counted in either table here, and not
touched by anything in this entry. `--only` kept this run's own numbers scoped
to exactly the 72 ids selected before it started, which is what makes them
readable independent of what else was landing in the same file at the same
time.
