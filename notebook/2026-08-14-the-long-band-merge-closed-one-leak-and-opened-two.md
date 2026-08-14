# 2026-08-14 — the long-band merge closed one leak and opened two

**Prediction, before running anything.** The 23 long-band triples sitting
unmerged in scratchpad (`l10`-`l22`, `xl08`-`xl17`) were built to answer the
`word_count` finding baselined on 2026-08-13: matched 0.660, 3.24 null standard
errors, driven by `l` at 0.778 and (in the opposite direction) `xl` at 0.393. I
expected the merge to move both bands toward 0.5 and close the finding cleanly,
and I expected the merge to be a pure append with no id collisions, since the
fragments continue the existing `l01`-`l09` / `xl01`-`xl07` numbering rather than
reusing it. I did not expect it to be feature-neutral — CLAUDE.md's own warning
about "four generations of leak" from per-item retuning made me expect some
correlated feature to move if the fix wasn't genuinely uniform-rank.

## What was there

Nine files in the scratchpad: `l-a.yaml` through `l-d.yaml` (13 triples,
`l10`-`l22`) and `xl-a.yaml` through `xl-e.yaml` (10 triples, `xl08`-`xl17`), plus
a `fragments/` directory of four building-block files (`l-positive.yaml`,
`l-negative.yaml`, `xl-positive.yaml`, `xl-negative.yaml`) that were superseded
by the nine and not used. 13 + 10 = 23 triples, 69 items, matching the task's
count exactly. No duplicate ids inside the fragments, and no collision with the
live corpus: `l.yaml` topped out at `l09`, `xl.yaml` at `xl07`, so no renumbering
was needed. Schema matched the live corpus field-for-field (positives carry
`route`, including `route: ~` for one deliberately unroutable case, `l17`;
negatives carry `kind`), so this was a pure append.

## Rank distribution, measured before trusting the merge

The corpus-baseline note this was meant to close specifically warned against
tuning negatives to hit a target and called for "a rank distribution for the
positive that is roughly uniform across longest, middle and shortest." Measured
directly on the 23 new triples by word count:

```
positive-shortest: 16 of 23
positive-middle:    5 of 23
positive-longest:   2 of 23
```

That is not uniform. It is the mirror image of the defect the note projected
against (49 of 64 forced to positive-longest) — this batch over-corrected past
0.5 in the other direction rather than landing near it.

## The battery, before and after

Pre-merge (192 items, 64 triples) — from `corpus-baseline.txt`, reproduced here
by loading the pre-merge commit (`a1c171c`) directly rather than trusted from
memory:

```
word_count, matched: 0.660, 3.24 null SE (LEAK)
  per band: s 0.604, m 0.750, l 0.778, xl 0.393
  pooled AUC: 0.517 (turn), 0.503 (ask)

sentence_count, matched: 0.590, 2.17 null SE (quiet, second-highest of the
  battery), dispersion 1.64 (quiet)
  per band: s 0.552, m 0.625, l 0.778, xl 0.357

type_token_ratio, ask, matched: 0.414, 1.72 null SE (quiet)
  per band: s 0.375, m 0.417, l 0.444, xl 0.500
```

Post-merge (261 items, 87 triples), read from a live `de check --fast` run
against the merged corpus:

```
word_count, matched: 0.546, 1.09 null SE -- CLOSED, under the z=3.0 gate
  per band: s 0.604 (unchanged), m 0.750 (unchanged), l 0.455, xl 0.294
  pooled AUC: 0.509 (turn), 0.489 (ask)

sentence_count, turn+ask, matched: 0.480, 0.58 null SE (quiet) but
  dispersion: 3.82 null SE -- NEW `cancel:` finding, both views
  per band matched: s 0.552, m 0.625, l 0.432, xl 0.235
  pooled AUC: 0.517 (turn), 0.466 (ask)

type_token_ratio, ask, matched: 0.316, 4.27 null SE -- NEW `matched:` finding
  per band: s 0.375, m 0.417, l 0.205, xl 0.235
  pooled AUC: 0.389
  (turn view: 2.93 null SE -- under the gate, closest passing feature to it)
```

**`word_count` closed as predicted, but not by the mechanism the earlier note
called for.** `l` and `xl` did not move toward 0.5; they moved through it. `l`
went from 0.778 (positive-longest) to 0.455 (mildly positive-shortest), `xl`
from 0.393 to 0.294 (more strongly positive-shortest, in the same direction it
was already leaning). `s` and `m` are untouched — same triples, same numbers.
The pooled-and-matched figure landed under the gate because the new bands'
positive-shortest skew happened to average against the old bands'
positive-longest skew, which is the same cross-band cancellation mechanism this
corpus has now hit four separate times on four separate features, just run in
the direction that helps this time.

**And it did not cancel cleanly everywhere.** `sentence_count` correlates with
`word_count` closely enough that the same skew that closed one opened the
other, as a `cancel:` finding rather than a `matched:` one: the *direction*
still balances close to 0.5 pooled (0.480 matched), but the *dispersion* — how
often the positive sits at either extreme of its triple rather than the middle
— is 3.82 null standard errors, comfortably over the gate. `type_token_ratio`
on the `ask` view is worse: it does not cancel at all. All four bands sit below
chance (s 0.375, m 0.417, l 0.205, xl 0.235), strongest exactly where the new
triples landed.

## What I did about it

Nothing to the corpus content. CLAUDE.md is explicit that per-item retuning
against whichever feature is currently over threshold is how this corpus
already generated four leaks, and re-tuning the 23 new triples to flatten
`sentence_count` and lift `type_token_ratio` would push `word_count` back over
its own gate — the three features are reading the same closing-sentence habit
through different rulers, not three independent defects.

Instead: `corpus-baseline.txt` loses the two `word_count` entries (closed, with
the mechanism above written down rather than just "closed") and gains three —
`cancel:turn:sentence_count`, `cancel:ask:sentence_count`,
`matched:ask:type_token_ratio` — with the same rank-uniformity condition named
as what would close them, corpus-wide rather than per-band.

## A process note, not a corpus finding

While this merge was in progress, a different session was concurrently editing
`evals/src/decision_evals/corpus.py` (a `_shared_body` off-by-one that pinned
`open`-view opener features identical across ~20 of the original 64 triples)
and `corpus-baseline.txt` (adding `matched:open:question_marks` and
`matched:open:terminal_question`, unrelated to this merge). Two consequences
worth recording rather than being surprised by twice:

1. Two of my early `battery_report` runs, taken minutes apart with no edits of
   my own in between, printed different numbers for the same features. Both
   were real: the corpus and the measurement code were both moving under me.
   I stopped trusting any single run and re-derived from a `git show
   HEAD:<path>`-sourced clean base plus the extracted fragments, verified in
   the same process that wrote the file, before treating a count as fact.
2. My own working-tree edit to `l.yaml`/`xl.yaml` was clobbered back to the
   pre-merge commit at least once, most plausibly by the other session's `git`
   operations sharing this working tree. Re-applying from the saved extraction
   was safe because the merge is a deterministic append, but a merge built by
   hand-editing in place would not have survived this cleanly.

The `question_marks` / `terminal_question` baseline entries that session added
carry pre-merge numbers in their prose (0.566 matched, 3.47 SE, measured on the
64-triple corpus). This merge moves both to 0.629 matched, 6.12 SE — the key
still matches so the gate still treats them as open and baselined, but the
comment is now a pre-merge snapshot. Left as-is rather than rewritten; it is
recorded in `corpus-baseline.txt` itself and is that session's entry to update.

## Commits

- Corpus merge (`l.yaml`, `xl.yaml`, `corpus-baseline.txt`): see
  `docs/DECISIONS.md`, entry dated 2026-08-14, for the commit sha (recorded
  there rather than here because the decision register commit cannot name its
  own predecessor's sha until that commit exists).
