# 2026-08-13 — an adversarial review of the XL band, and the fourth inert estimator

An adversarial sub-agent was given `datasets/triggers/decision-making/xl.yaml` and
the standard it claims to meet, and was not told what the author concluded. It
returned fourteen objections and a verdict that **nine of twenty-one items should
not ship**.

Per the work order, one agent's result is a hypothesis. Seven of its claims are
mechanically decidable, so they were checked here rather than believed. **Six
confirmed exactly. One is wrong.** The rest are label judgements and are
deliberately left open below.

---

## Confirmed by independent recomputation

| claim | verdict |
|---|---|
| XL word range is 923–1,059 against a declared band of 900–1,500 | confirmed; 0 of 21 items reach 1,200 words |
| terminal `?` separates: 2/7 positives, 0/14 negatives, AUC 0.643 | confirmed to three decimals |
| the first word is constant within every triple | ~~confirmed, all 40 triples~~ **this line was wrong — see the correction below** |
| `xl07`'s opening line is present verbatim in all three members | confirmed byte-for-byte |
| 4 October 2025 is a Saturday, inside Priya's stated 1st–4th close window | confirmed |
| the 20-business-day anchor requires today to be Sunday 7 September, which the body's own "8 Sept" item contradicts | confirmed |

## Correction, same day, before this entry was committed

**Two claims above are wrong and both are mine.** A later agent measured them and I
had not.

**1. "The first word is constant within every triple, all 40" is false.** It is
constant in **12 of 40** — all 7 XL triples, 3 of 9 L, 1 of 10 M, 1 of 14 S. My
verification script iterated the XL band and I wrote the result down as though it
covered the corpus. It sat under a heading reading *"confirmed by independent
recomputation"*, which is worse than an unchecked claim, because it tells the next
reader not to check.

`imperative_opener`'s real AUC is **0.494, not exactly 0.500**. The conclusion
survives by a different and better route: its *attainable* interval over the label
assignments the matched design permits is **[0.475, 0.525]**, so no label
assignment could ever have pushed it outside the (0.40, 0.60) band. The check
still could not fail. It could not fail for a reason I had not identified.

**2. "Every whole-turn feature is diluted by identical text" is not how AUC
works.** A byte-identical body contributes *nothing* to a rank statistic —
demonstrated: an identical body plus a seven-word difference in the ask gives a
turn-level AUC of **1.000**, not 0.5. What actually hides an ask-level ruler is
body variation *across* triples swamping the within-triple difference. That is a
sharper claim than mine and it has a different consequence: **the leak can hide in
S, M and L too, not only where a body is shared.**

**3. And the premise under both of them does not hold.** The corpus does not have
the construction its documentation claims. Measured shared-body fraction per
triple:

| band | triples sharing ≥90% of the body |
|---|---|
| s | **0 of 14** |
| m | **0 of 10** |
| l | 3 of 9 |
| xl | 5 of 7 (84–99%) |

`datasets/triggers/decision-making/l.yaml`'s header states the pasted material *"is
byte-identical across the positive and its two negatives"*. For six of its nine
triples the members share **zero characters**. `corpus.py`'s docstring says "three
of nine" and is right; the band file's header is wrong.

**So "matched triples kill the length shortcut by construction" is a claim this
corpus cannot make.** It is true of XL, partly true of L, and false of S and M —
which is 72 of 120 items. The battery still finds no length ruler on the turn view
(`word_count` pooled 0.511), so the corpus does appear ruler-proof; it is just not
ruler-proof *by construction*. It is ruler-proof by careful authoring, which is a
much weaker guarantee and one that does not extend to items authored later.

## Refuted

The review offered a "minor corroborating tell" that `xl03n1` says *"Assume
England bank holidays"* over a window containing none. **The string is not in the
body.** The surrounding finding survives on the arithmetic alone; the tell does
not. It is recorded because a review that is right about six things and wrong
about a seventh is exactly what confirmation is for, and dropping the miss would
make the process look better than it was.

---

## The finding that outlives the band

`_imperative_opener` is `words[0] in _IMPERATIVES` — the first word of the whole
turn. The three members of a triple share a byte-identical body **and opening
line**, so the first word is constant within every triple by construction.

**Its AUC is 0.500 for structural reasons. No corpus could ever have made it
fail.** It has been reported as one of eight features sitting comfortably inside
the separability band, and it was measuring nothing.

This is the **fourth** instance of the defect `CLAUDE.md` names — "an estimator
that cannot return a non-zero value is not a measurement, and it does not
announce itself". The previous three were a parser whitelist that discarded every
tool name an n=2 arm could offer, a routing report grading names the arm never
offered, and a scorer reading `final_response` across arms with different turn
counts. All four produced clean runs and plausible numbers.

And the general form is worse than the one feature. **In a matched-triple design
the body is constant across the label, so every whole-turn feature is diluted by
identical text.** The discriminating span can be as little as 18 characters
against a 4,846-character body. A turn-level AUC of 0.5 is close to uninformative
about whether an ask-level ruler exists. The battery has been asking the wrong
question of the right corpus.

Terminal `?` is the demonstration: 0.643 within XL, **0.569 pooled over all 120**
— inside the (0.40, 0.60) band, so the pooled gate never sees it. That is the
second instance of the pooled-versus-per-band problem recorded yesterday, and the
first where pooling hides a leak rather than a cancellation.

Fix in flight: refuse any feature with zero variance across the corpus or
constant within every triple; run the battery on the derived ask as well as the
turn; add terminal-position features. Under standing rule 2 the new guard must
pass a known-good case before it is allowed to fail anything.

---

## Deliberately left open: the label judgements

The review argues `xl07n1`, `xl07n2` and `xl05n2` are mislabelled, and that
`xl04n2`, `xl05n1` and `xl06n2` survive only under an ask-only reading their
bodies fight. Those are readings, not arithmetic, and **the author of a reading
is the worst available judge of it — including this one.**

The blind adjudication (N3) is running on this exact text as this is written: 3
independent instances per turn, given the turn and the shipped `Abort if`
clauses and **not** the label. It is the confirmation route for precisely these
six items, it did not share the reviewer's context, and it was launched before
the review returned.

**Prediction, recorded before the adjudication result is read:** the three
`settled` negatives the review attacks — `xl04n2`, `xl05n1`, `xl06n2` — draw the
most adjudicator disagreement in the band, because each announces a settlement
the retained body denies in the present tense. If adjudication moves those and
leaves the rest, the review is confirmed by a second route and the fix is to the
items. **If adjudication does not move them, the review is one reading and the
items stand** — and that outcome goes in the record too.

The pre-registered kill is 20% of labels moving. The review predicts far more
than that on this band; XL is 21 of 120 items, so it can supply at most 17.5
points on its own.

## What is not being done

The band is **not** being patched while adjudication runs on it. Editing the
text under a blind labelling run would void the run, and rewriting items to
satisfy a reviewer before an independent check is authoring toward a conclusion.
The order is: adjudicate, then act on what two routes agree about.
