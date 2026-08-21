# 2026-08-21 — The 72 council and hinge items go through adjudication

**2026-08-21.** Answer key v5 carries 330 items in 110 triples. The blind
three-judge round has run on 258 of them. The 72 that have never been through it
are the 24 triples added on 2026-08-20 in `069df14`, twelve positives routed to
`council` and twelve to `hinge`, each with two length-matched negatives, three
triples per route per band.

Inventory against `results/triggers/adjudication.jsonl`, recomputed here rather
than carried from the entry that added the items:

```
corpus   330 items, version 5
ledger   261 distinct case ids
missing   72   s 18, m 18, l 18, xl 18
triples   s25-s30, m25-m30, l23-l28, xl18-xl23
```

The ledger also holds three case ids the corpus does not have, `l15p`, `l15n1`
and `l15n2`, left behind when that triple was retired on 2026-08-18. They are
recorded here because any inventory that assumes the ledger is a subset of the
corpus will be off by three, and because 858 lines in that file resolve to 783
unique `(case, judge)` records: 25 cases were adjudicated twice in the
2026-08-18 round.

`docs/DECISIONS.md:1332` states the block this run exists to clear: no number
may be published against version 5 until these labels have been through blind
adjudication, with a pre-registered kill at more than 20% of labels moving.

## What this run does not clear

The adjudicator answers one binary question, checked in `SYSTEM` before running:
is the person asking someone to help them decide something? It never sees the
route. So this run validates `should_fire` on all 72 items and says nothing
about whether the twelve `council` positives are `council` or the twelve `hinge`
positives are `hinge`.

That gap matters more here than in any earlier batch, because the reason these
items were authored at all was that `council` and `hinge` were the correct
answer for no positive in the corpus, and `evaluate_routing` scored
`chosen in case.routes` against a key that could only ever count a correct
`council` as wrong. Adjudication lifts the publishing block. The route labels
behind these 24 positives stay the author's, and something else has to check
them.

## Parameters, and which were chosen

`--model haiku` and three judges are derived: both match the instrument N3 ran
on, and a different model or panel size would make this batch incomparable with
the 258 items already on record. The denominator is 72, the items being
adjudicated, which is why the run is scoped with `--only` rather than
`--missing-only` alone: the end-of-run report scopes to `--only` and would
otherwise fold these into a whole-corpus figure.

```
scripts/adjudicate.py --only "@<72 ids, one per line>" --report-only   # dry run, returned "no adjudication records"
scripts/adjudicate.py --only "@<same file>"                            # the run, 216 calls
```

## Prediction, before running

Every movement rate this corpus has produced, by batch: N3's first 120 items
0.025, the 72 S and M items on 2026-08-14 0.056, the 56 L and XL items the same
day 0.089. Over all 261 items at once, 0.046, with every band inside 0.042 to
0.059 and no length effect left in it.

- Movement over the 72: **0.03 to 0.09**, point estimate 0.05, which is 2 to 6
  items. Well under the 0.20 kill.
- Unanimous with key: **0.84 to 0.92** (261-item figure: 0.885).
- Fleiss kappa and Krippendorff alpha: **0.80 to 0.88** (261-item figure:
  0.862). High values here measure reproducibility of one model's reading. Three
  instances of haiku are 1.10 effective raters, so this number is not evidence
  the labels are right, and it is repeated here so it does not get quoted from
  this entry as though it were.

**Where I expect to be wrong.** Every earlier batch was authored across bands
over several days. These 72 came from one pass on one afternoon, written to give
two named procedures positives to be correct about. A single sitting can carry a
consistent reading of what counts as a decision, and if that reading is off the
judges will disagree with it uniformly instead of item by item, which puts
movement above 0.09 without anything being randomly wrong.

If movement clusters, I expect it in the 48 negatives. They are length-matched
near-misses authored against their own positives, which is the shape most likely
to read as a decision to a judge who has the turn and no triple around it. A
result where the 24 positives move and the negatives hold would surprise me and
would point at the route labels rather than the fire labels.

## Result

216 blind adjudications, 3 judges x 72 turns, 0 unparseable, `--model haiku`
matching the instrument every earlier batch ran on. Judges saw the turn and the
shipped `Abort if` clauses and nothing else.

```
cases                72
unanimous with key   0.875
contested (2-1 kept)   6
moved (2-1 against)    3
movement rate        0.042   (pre-registered kill above 0.20)

inter-rater agreement, key not involved:
  pairwise agreement  0.926
  unanimous judges    0.889
  Fleiss kappa        0.839
  Krippendorff alpha  0.839
  effective raters    1.121

movement by band:
  l     1/18   0.056
  m     2/18   0.111
  s     0/18   0.000
  xl    0/18   0.000
```

**The corpus survives the pre-registered kill**, by a factor of nearly five, and
survives it in every band separately.

All three registered bands held. Movement 0.042 against a predicted 0.03 to
0.09. Unanimity with key 0.875 against a predicted 0.84 to 0.92. Fleiss kappa
0.839 against a predicted 0.80 to 0.88. The single-sitting authoring worry that
the prediction called its most likely failure did not materialise: one afternoon
of authoring produced the same movement rate as batches written across days.

Where the prediction was right for a weak reason: it expected movement to
cluster in the 48 negatives, and two of the three moves are negatives. Three
items is too few to call that anything but consistent.

**Correction to the prediction, appended.** The batch rates it quotes — 0.025,
0.056, 0.089 — cover 248 of the 261 items, not all of them. The remaining 13
were adjudicated in the opener-leak session, which never reported a batch rate.
The move counts still reconcile to the recorded total of 12, so only the
denominators were understated.

### The three moves cannot be applied, for the reason 2026-08-18 found

```
l24n1    negative -> positive   votes (True, True, False)
m25p     positive -> negative   votes (False, False, True)
m29n2    negative -> positive   votes (True, True, True)
```

Every one of the three breaks the one-positive-two-negative invariant
`corpus._check_triples` enforces, computed against the corpus and the ledger:

| triple | what the judges said | applying the move gives |
|---|---|---|
| `l24` | `l24p` confirmed positive 3-0, and `l24n1` also reads as fire 2-1 | two positives |
| `m29` | `m29p` confirmed positive 2-1, and `m29n2` reads as fire 3-0 | two positives |
| `m25` | `m25p` reads as no-fire 2-1, and both negatives unanimously no-fire | zero positives |

This is
[`2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md`](2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md)
happening again on the new items, at 3 of 3 where that round was 12 of 12. The
corpus is authored in triples and adjudicated in items: a judge sees one turn
and cannot know that two of the turns it just read share a body with a third and
compete for a single positive slot. So a 2-of-3 vote against the key says the
authored contrast did not land, and moving the label is not an available branch.

The plan's live remedy is to rewrite the disputed ask and re-adjudicate, which
is 3 items and 9 calls. Retirement is the remedy for a three-way split, and with
three binary judges a three-way split cannot occur, so that branch stays dead.

**What this settles and what it does not.** Every one of the 330 items in
version 5 now carries a three-judge blind record, and the movement rate over the
72 clears the kill. Three items carry a label three blind readers dispute, and
a number published against version 5 today is scored against those three as the
author wrote them.
