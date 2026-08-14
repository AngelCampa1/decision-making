# 2026-08-14 — the battery searches 176 cells, and nobody had costed that

An adversarial review of the long-band merge confirmed all six of the merging
agent's numbers exactly, then went further than it was asked to and tested the
thing an *arm* can actually exploit: band-restricted plain AUC, positives against
all negatives inside one band, no pairing. It reported two findings —
`sentence_count` and `type_token_ratio` on the `ask` view, AUC 0.299–0.330,
p = 0.014–0.05 — and labelled them **uncorrected**, which is the honest thing to
do and left the question open.

This entry closes it. I ran the whole family rather than the two cells.

## The family is 176 cells and it had never been counted

```
4 bands x 4 views x 11 features = 176 band-level tests
24 of them are degenerate -- a single constant value, cannot fail
18 cross p < 0.05 uncorrected     expected by chance at m=176: 8.8
```

**Eighteen against an expectation of nearly nine.** There is real signal in
there, and about half of what a naive read would call findings is noise.

Benjamini–Hochberg at q < 0.05 leaves **seven**:

| band | view | feature | AUC | p | BH q |
|---|---|---|---|---|---|
| l | close | `type_token_ratio` | 0.217 | <0.0001 | 0.0088 |
| xl | open | `question_marks` | **0.779** | <0.0001 | 0.0044 |
| xl | open | `terminal_question` | **0.779** | <0.0001 | 0.0029 |
| l | open | `question_marks` | 0.716 | 0.0001 | 0.0044 |
| l | open | `terminal_question` | 0.716 | 0.0001 | 0.0053 |
| xl | open | `type_token_ratio` | 0.218 | 0.0005 | 0.0161 |
| xl | close | `type_token_ratio` | 0.230 | 0.0010 | 0.0264 |

`question_marks` and `terminal_question` return **identical** AUCs in both bands,
so they are one finding counted twice, and `word_count`/`char_count` pair the same
way further down the table. Seven rows is more like four distinct facts.

## The two findings that prompted this do not survive

```
xl / ask / sentence_count      p 0.0138   BH q 0.2024
l  / ask / type_token_ratio    p 0.0140   BH q 0.1902
```

**Neither clears correction**, and the reviewer's instinct to mark them
uncorrected was right. They sit at ranks 12 and 13 of 176 — comfortably inside
the range where eighteen crossings are expected to contain nine accidents.

This does not make the review wrong. It asked the right question — *is a
within-band leak exploitable in a way a pooled figure is not?* — and its finding
for `word_count` in XL stands: AUC 0.457, p = 0.63, not exploitable, because the
shared pasted body dilutes it. That was the claim the shippability of the corpus
turned on, and it held.

## The part worth keeping: the battery's own threshold is already about right

`MATCHED_Z = 3.0`. Two-sided, that is p = 0.0027. Across 176 cells the expected
number of false findings is **0.47** — under one per run.

So the battery is approximately multiplicity-safe already, and the two flagged
cells at p = 0.014 would never have crossed its gate in the first place. **Nobody
had computed that.** A fixed z chosen for a single comparison happened to land in
the right place for a family of 176, and it is worth writing down that it was
checked rather than leaving the next person to wonder.

My sweep used α = 0.05, which is the loose threshold, not the one the repository
gates on. That is why my sweep found eighteen and the battery reports a handful.

## What is actually leaking, and it is the newest view

The strongest surviving signal is not `word_count` and not the `ask` view. It is
**`question_marks` and `terminal_question` on the `open` view — AUC 0.779 in XL
and 0.716 in L.** Whether a turn's *first sentence* ends in a question mark
separates the labels in the long bands at close to four cases in five.

The `open` view was added today, and it fired immediately on the two bands where
nothing else does. That is the argument for enumerating views, and it is also the
standing warning: a battery that enumerates views will always be one view behind
the next unconscious habit. Four views exist. The next defect will be in the
fifth.

Those two are already baselined in `datasets/triggers/corpus-baseline.txt` by the
agent that added the view, which is the correct outcome — the finding was caught
by the instrument on the run that made it findable, not by somebody re-reading
the corpus afterwards.

## What I am not claiming

BH assumes a dependence structure this family does not have — `word_count` and
`char_count` are near-collinear, `question_marks` and `terminal_question` are the
same measurement twice, and the four views share text by construction. So the
seven survivors are an over-count of independent findings and the q-values are
approximate. The direction of the error is toward finding *too much*, which is
the safe direction for a corpus gate and the wrong one for a claim about the
corpus being clean.
