# 2026-08-13 — the spec made the leak arithmetically unavoidable

Four generations of one defect were found today, each individually, each after
the fact, each by a different person:

1. **Positives close short.** Median 11 words against 15 — four features
   separating the labels on the closing sentence, p = 0.002.
2. **Positives close longest.** The fix for (1) specified longer positive
   closings and produced the mirror leak: the positive was the longest of three
   closing sentences in **19 of 23** new triples. It *passed pooled* —
   `check_corpus` returned 0 issues and the stump lift fell from 0.083 to 0.048 —
   because S and M cancel L and XL. Per band, type-token ratio ran −3.80 SE in L
   and −3.30 SE in XL.
3. **First-person rate**, same view, found separately.
4. **Clipped negative openers.** The fix for (2) forced openers to collapse:
   *"Separately."*, *"Clause 9.2."*, *"Date aside."*, *"Arithmetic."*, *"One
   question."*, *"Numbers only."*, *"Lease signed."* The `close` view is
   structurally blind to it — it reads the last sentence only.

## The explanation, which is the actual finding

An author derived it while refusing an instruction as impossible.

**When a positive's ask is one sentence, X *is* the positive's closing
sentence.** A negative must then satisfy `close ≥ X+1` (to invert the rank) and
`total ≤ 1.15X` (§3's ±15% ask-total rule), while §3 separately requires
negatives to be two or three sentences. The opener budget is therefore
`0.15X − 1`:

| positive close (X) | 17–19 | 20–26 | 27 |
|---|---|---|---|
| opener budget | **1 word** | **2 words** | **3 words** |

So for every `implicit` and `explicit` positive in the corpus, the positive's
closing sentence is **forced** to sit at or within one word of the longest, and
rank inversion is purchasable only with a one-to-three-word fragment.

**This is not an authoring habit. It is the specification.** Generations 1, 2 and
4 are the same constraint expressing itself in whichever direction the last
instruction pushed. Nobody was being careless; the design space the spec permits
does not contain a clean corpus.

`embedded` positives are the exception, because X exceeds the close — one has a
**19-word** opener budget and needed no fix at all.

## How it was found

Six authors independently derived the same conflict, each while refusing a
different instruction as arithmetically impossible rather than approximating it:
a 26-word close needing a zero-word opener, a 29 leaving 0.90 words, a 23 out of
band at every arrangement, a 28 forcing ratio 1.16, a 30 at ratio 1.200.

**Each of them delivered the requested *rank* at the maximum legal length and
reported the shortfall, rather than silently breaking the constraint or silently
missing the target.** Three then proposed the same remedy without conferring.

Three of the coordinating unit's stated windows were also wrong — 22.6–28.2 where
±15% of 24 is 20.4–27.6; 23.5–30.6 where ±15% of 25 is 21.25–28.75; and a pair
of "totals" that implied a one-sentence negative, which §3 forbids. Every author
who caught it had re-derived the window instead of using the one they were given.

## The decision taken

1. **Relax the ask-total band to ±25%** for triples where the positive is
   assigned shortest or middle rank. ±15% stays where the positive is longest,
   since the conflict does not arise there.
2. **Prefer `embedded` positives** for new triples. Structure removes the
   conflict; widening a tolerance only buys room inside it. This is the better
   lever and it came from an author, not from the plan.

**With a condition attached**, because ±15% exists to stop ask *total* length
carrying the label: `word_count` on the `ask` view is 0.489 pooled today. If
relaxing to ±25% moves it outside (0.40, 0.60), the relaxation has bought a leak
one level up and only part 2 is taken. That number is to be reported before the
rank fix is called clean.

## The generalisation, in an author's words

> *"Any closing-sentence property the spec fixes in one direction becomes a label
> the battery can read without the body."*

Length, first-person rate, terminal `?`, and closing-construction family are four
instances. The fix in every case is **rank variety across the band**, never a
per-item bound.

**A battery that enumerates views will always be one view behind the next
unconscious habit.** Four views exist now — turn, ask, close, and an `open` view
being added. The class-level check, if it is tractable, is something like: flag
any feature whose per-triple *rank* of the positive is skewed away from uniform,
in any view. That has been asked for as a suggestion rather than a requirement,
because I do not know that it is the right shape.

## What this says about the method

The finding came from authors refusing instructions, not from the reviewer, not
from the gate, and not from me — I issued the instruction that caused generation
2 and endorsed the one that caused generation 4.

Nine sub-agents were given a spec and the freedom to say it could not be
satisfied. Six used it. **Every one of them was right**, and the arithmetic they
produced to justify refusing is what explains the original defect.

That is a different mechanism from adversarial review, and it may be worth more:
a reviewer checks whether the artefact meets the spec, and cannot see that the
spec is impossible. Only somebody trying to build to it finds that out.
