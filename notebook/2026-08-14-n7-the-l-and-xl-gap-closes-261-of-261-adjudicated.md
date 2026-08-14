# 2026-08-14 — N7: the L/XL gap closes, 261 of 261 now blind-adjudicated

N3 (2026-08-13, 120 items) and the same-day continuation (72 S/M items) left
the L and XL bands unadjudicated on purpose: a separate session was mid-edit
on `l.yaml`/`xl.yaml` to close the opener-leak found by the 176-cell
permutation sweep (`cee9329`), and any verdict against text still moving
would be void. That edit landed the same day, closed with **0 label moves**
across the 26 items whose text changed, plus 3 items (`l12n1`, `l17n2`,
`xl15n2`) reverted to byte-identical original text after blind
re-adjudication caught that a reordering had changed what the ask meant. That
work is not repeated here; it is the reason this run's text is stable.

## Inventory, verified rather than assumed

Loaded `datasets/triggers/decision-making/index.yaml` directly (261 cases:
s 72, m 72, l 66, xl 51) and diffed case ids against
`results/triggers/adjudication.jsonl` (822 raw lines; 783 unique
`(case, judge)` pairs after the checkpoint's own dedup-by-overwrite — 39 stale
duplicate lines from earlier re-runs sit in the file and cost nothing, since
`load_done` keys on `(case, judge)` and the last line for a key wins; flagged
here rather than fixed, since cleaning them is not this task).

- 205 cases already carried full 3-judge records before this run: all 72 s,
  all 72 m, 34 of 66 l, 27 of 51 xl.
- **56 L/XL cases had zero records**: 32 l (`l10n2`, `l11n1/n2`, `l12n1/n2`,
  `l13n1/n2`, `l14n1/p`, `l15n1/n2/p`, `l16n1/n2/p`, `l17n1/n2/p`,
  `l18n1/n2`, `l19n1/n2/p`, `l20n2/p`, `l21n1/n2/p`, `l22n1/n2`) and 24 xl
  (`xl08n2/p`, `xl09n2/p`, `xl10n1/n2`, `xl11n1/p`, `xl12n1/n2`, `xl13n1/n2/p`,
  `xl14n1/n2/p`, `xl15n1/n2/p`, `xl16n1/n2`, `xl17n1/n2/p`) — not the ~69 the
  task brief estimated; the opener-leak session had already covered 13 more
  l/xl cases than N3 left behind.
- Call count stated before running: **56 cases x 3 judges = 168 calls**,
  `--model haiku` to match N3 and the continuation's own instrument.

## Blindness, checked in code before spending a call

Read `scripts/adjudicate.py`'s `SYSTEM` constant (lines 73-88) and `ask()`
(line 116) directly rather than trusting the docstring. The judge's entire
context is the fixed decision-labelling instructions plus the skill's own
`Abort if` clauses via `abort_clauses()`, and the per-turn prompt is
`f"## Message\n\n{case.turn}"` — nothing else. No label, case id, band,
triple, or skill description reaches the prompt. Confirmed, not assumed.

## The run

```
scripts/adjudicate.py --model haiku --missing-only
```

`--missing-only` excludes any case with an existing record from the whole
261-item set, which selected exactly the 56 L/XL cases above (S and M were
already complete, so nothing there was touched). 168 calls, 0 unparseable.

```
selected 56 cases x 3 judges on haiku
  = 168 calls remaining after resume
  ...
  168/168
```

## Results: this batch alone (56 L/XL cases)

```
cases                56
unanimous with key   0.839
contested (2-1 kept)   4
moved (2-1 against)    5
movement rate        0.089   (pre-registered kill above 0.20)

inter-rater agreement, key not involved:
  pairwise agreement  0.917
  unanimous judges    0.875
  Fleiss kappa        0.821
  Krippendorff alpha  0.822

movement by band:
  l     3/32   0.094
  xl    2/24   0.083
```

Well under the kill on this batch alone, and the two previously-clean L/XL
bands (0/34 l, 1/27 xl from N3's coverage) both picked up movement once the
remaining half was checked — the gap left by N3's original partial coverage
was not a random hole.

## Results: the whole corpus, 261 of 261, for the first time

```
cases                261
unanimous with key   0.885
contested (2-1 kept)  18
moved (2-1 against)   12
movement rate        0.046   (pre-registered kill above 0.20)

inter-rater agreement, key not involved:
  pairwise agreement  0.936
  unanimous judges    0.904
  Fleiss kappa        0.862
  Krippendorff alpha  0.862

movement by band:
  l     3/66   0.045
  m     3/72   0.042
  s     3/72   0.042
  xl    3/51   0.059
```

**Every band now sits within a narrow 0.042-0.059 band of movement.** There
is no longer a length effect visible in movement rate — the concern N3 opened
with, that a 1,200-word turn has fifty times the label surface area of a
short one, does not show up as more movement in the long bands once they are
actually checked. The corpus survives the pre-registered 0.20 kill by roughly
a factor of four.

## The twelve labels adjudicated to move, still unapplied

| case | direction | votes | adjudicated |
|---|---|---|---|
| `s02n2` | negative → positive | (False, True, True) | 2026-08-13 (N3) |
| `s12p` | positive → negative | (True, False, False) | 2026-08-13 (N3) |
| `xl05n2` | negative → positive | (True, True, True) | 2026-08-13 (N3) |
| `m14n2` | negative → positive | (True, True, True) | 2026-08-14 (continuation) |
| `m16n2` | negative → positive | (True, True, False) | 2026-08-14 (continuation) |
| `m18p` | positive → negative | (False, False, False) | 2026-08-14 (continuation) |
| `s19n2` | negative → positive | (True, True, False) | 2026-08-14 (continuation) |
| `l15n2` | negative → positive | (True, True, True) | 2026-08-14 (N7, this run) |
| `l17n2` | negative → positive | (True, True, False) | 2026-08-14 (N7, this run) |
| `l21n1` | negative → positive | (True, True, False) | 2026-08-14 (N7, this run) |
| `xl13n2` | negative → positive | (True, True, True) | 2026-08-14 (N7, this run) |
| `xl16n1` | negative → positive | (False, True, True) | 2026-08-14 (N7, this run) |

Eleven of twelve move negative → positive; only `s12p` and `m18p` move the
other way, and only `m18p` is unanimous in that direction. Not investigated
further here — a directional skew this small (10 of 12) on a corpus that is
itself imbalanced toward negatives is not obviously more than what a slightly
conservative labelling pass toward "no" would produce, but it is worth
somebody's attention at the freeze rather than mine asserting a cause now.

**None of these twelve is applied.** Per the mechanical rule this script
enforces and N3/the continuation both held to: the answer key moves once, at
the freeze, carrying every adjudicated move from N3 through N7 at once — not
once per batch. Applying now would be an eighth version bump on top of the
seven reasons this repository already has on record to avoid stacking them.

## The caveat, carried forward verbatim a third time

**κ = 0.862 (combined 261) must not be read as evidence the labels are
right.** Three adjudicators are three independent instances of the same model
given the same prompt, not three independent human raters in the sense
Fleiss' κ assumes. A high κ shows the question is well-specified enough for
one model's reading of it to reproduce three times running — the
instrument's reliability, not the corpus's validity. N3's own N4 (a human
holdout, ~20 turns, never seen by the author before authoring closes) is
still the only thing in this repository's plan that would separate the two,
and it has not run. This is repeated a third time in as many days rather than
cross-referenced, so a reader who lands on only this entry gets the same
warning N3 and the continuation gave.

## What this closes and what it does not

**Closes:** the L/XL adjudication gap. All 261 items in the corpus now carry
3-judge blind adjudication records, for the first time since the corpus grew
past 120 items on 2026-08-13. The corpus survives the pre-registered kill at
every scope checked: this batch (0.089), the full 261 (0.046), and every
individual band (0.042-0.059).

**Does not close:** the freeze itself. Twelve moves are on record and
unapplied; applying them, bumping the answer-key version, and re-running
every arm comparison that used the old key is separate work this entry does
not do. N4 (human holdout) has still not run, so the caveat above still
holds without qualification.

## Process note

`docs/STATUS.md` is not touched in this change, on explicit instruction —
it was reverted once already this week by a concurrent session's git
operation and had to be reconstructed from memory. Updating it belongs to
whoever next has a clean read of the working tree.

`results/triggers/adjudication.jsonl` is gitignored
(`results/triggers/` in `.gitignore`, with `verdicts.jsonl` force-tracked as
the one exception) — it is the live, resumable checkpoint, not a published
artefact, and N3 and the continuation both left it uncommitted for the same
reason. This entry is the durable record of what the checkpoint shows as of
this run; the checkpoint itself remains local and re-derivable by re-running
`scripts/adjudicate.py --report-only`.

**A gap in the checkpoint's own schema, found late and worth naming rather
than fixing quietly.** A row is `case, judge, adjudicated, label, band,
triple, kind, model, raw` — a verdict about a turn, with no record of *which
version of that turn's text* was judged. The 26 L/XL items whose wording
changed under `cee9329`'s opener-leak fix were re-adjudicated the same day,
and `load_done` resolves duplicate `(case, judge)` keys last-write-wins in
file order — so the newer verdict happened to win because it was appended
later, not because anything in the record says it is the newer one. Nothing
in this run depended on that ordering holding (the 56 cases here had zero
prior records, so there was nothing to be shadowed), but the general
mechanism is unsafe: a checkpoint replayed out of append order, or merged
from two files, would silently prefer whichever verdict happened to sort
last. This is the same shape as two defects already on this repository's
record — a model tier that lived only in prose, and labels that moved
without a version stamp — and belongs on the list of things to fix before
the next corpus edit that touches already-adjudicated text, not carried
forward from memory.
