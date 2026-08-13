# The corpus is 89% solved by counting words

**2026-08-13.** Not a run. A property of the trigger set, found because the
maintainer said the turns looked too short:

> *"these questions seem very simple and short. i believe users will do much
> bigger questions. like paragraphs. we need to account for that"*

That is right, and checking it turned up something worse than a coverage gap.

## What the set actually contains

| | n | median words | max words |
|---|---|---|---|
| positives | 17 | **18** | 23 |
| negatives | 56 | **8** | 17 |

**No turn in the set exceeds 25 words.** 46 of 73 are ten words or fewer. The
longest thing in a corpus built to test *"a pile of context ending in a question
about what to do"* is one sentence long:

> *"Here's the whole thread with the landlord, the inspection report, and my last
> three bank statements. Do I sign the renewal?"*

That **describes** a pile of context. It is not one. The `ledger` procedure
exists for piles of context and **the corpus has never contained a single one.**

## The part that is not a gap but a confound

Positives run at 18 words and negatives at 8, and those distributions barely
overlap. So length is a *cue*, and a cue is measurable:

| classifier | score |
|---|---|
| turn length, as an AUC | **0.850** |
| *"fire if the turn is ≥ 18 words"*, accuracy | **0.890** |
| best model arm measured, accuracy | 0.956 |

**A ruler gets 89%.** The whole movable range above counting words is about six
points, and every arm in Tracks L and M has been competing inside it.

The long-context plan already set this gate — *"a trivial classifier gets
AUC > 0.70 → a model can do it too, re-author"* — for padding documents. It was
never pointed at the trigger set. Pointed at it now, the set fails by 15 points.

## What this does and does not invalidate

**It does not invalidate the arm comparisons.** Every arm saw the same 73 turns,
so M4, M5, M6, M6b and L5 are internally valid and their differences are real.

**It caps what any of them could have found**, and that reframes the M track's
headline. Five manipulations moved firing accuracy nowhere, and the standing
interpretation was *"nothing about a description changes how well it
discriminates"*. A second reading now has to be carried alongside it:
**there was about six points of room above a word count, so five nulls is what a
ceiling looks like.** Neither reading is established. Both must be reported.

**And it makes one absolute claim unusable.** *"The shipped description fires
correctly 95.6% of the time"* is a sentence this repository could have written
and it would have been misleading, because the reader would assume the hard part
was the deciding.

## The fix is not "add long turns"

Adding long positives makes the confound worse. The set needs the length↔label
correlation **broken**, which means the additions are:

- **long negatives** — a paragraph of context ending in a lookup, a debugging
  request, a request for information rather than a recommendation;
- **short positives** — a genuine high-stakes decision in eight words;
- and only then long positives, including turns that **are** a pile of context
  rather than a description of one.

The target is `length_separability` at or below 0.60, checked rather than
intended. Below 0.55 would be better and may not be reachable without writing
negatives nobody would send.

## What now exists

- `triggers.length_separability` computes the AUC directly, as the concordance
  form of the Mann-Whitney statistic. Not from scikit-learn, which is not a
  dependency and must not become one for a five-line rank statistic.
- `MAX_LENGTH_SEPARABILITY = 0.70`, the long-context plan's own number.
- The shipped set is **0.850** and is recorded as failing its own gate, rather
  than the gate being softened to fit it.

## For the maintainer

The next trigger-set version is a corpus job, not a code job, and it is larger
than the label edits: roughly 20 long negatives and a handful of short
positives, authored, then the whole arm menu re-run because a set change is a
key change and v2 numbers will not compare to v3.

**Every result in `results/` should be read with this attached.** It is going
into STATUS.md and into each README rather than only here.
