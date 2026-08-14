# 2026-08-13 — N3: the corpus survived, and four routes agreed on one item

360 blind adjudications, 3 judges × 120 turns, 0 unparseable. Judges saw the turn
and the shipped `Abort if` clauses; they did **not** see the label, and they did
not see the skill description, which is under test elsewhere.

```
cases                120
unanimous with key   0.917
contested (2-1 kept)   7
moved (2-1 against)    3
movement rate        0.025   (pre-registered kill above 0.20)

inter-rater agreement, key not involved:
  pairwise agreement  0.950
  unanimous judges    0.925
  Fleiss kappa        0.890
  Krippendorff alpha  0.890
```

**The corpus survives the pre-registered kill by a factor of eight.**

## The three labels that moved

| case | direction | votes |
|---|---|---|
| `s02n2` | negative → positive | (False, True, True) |
| `s12p` | positive → negative | (True, False, False) |
| `xl05n2` | negative → positive | **(True, True, True)** — unanimous |

**`xl05n2` is the item an adversarial reviewer independently called flat-out
mislabelled**, hours earlier, from the text alone and without seeing the
adjudication. Its argument was that the "meta" ask — *"it is telling me the two
consultants' recommendation is not the relevant fact, and I cannot see how that
can be right"* — is the `fit` procedure run on a live case, not an explanation of
a prior answer. Three blind judges reached the same verdict unanimously. A fourth
route reached part of it: the long-band unit's stance detector flagged `xl05`'s
shared body for present-tense indecision, from the text, with no knowledge of
either.

**Four routes, no shared context, same item.** That is the strongest confirmation
this repository has produced for anything, and it is worth noting that it is
confirmation of an *error*.

`s12p` is the other instructive one: *"Four people have now sent me spreadsheets
about the holiday budget and they don't agree with each other."* Eighteen words,
labelled a `ledger` positive, and **containing no ask at all.** Nothing is
requested. Two judges said so.

## Where the movement is, and where it is not

```
l     0/27   0.000
m     0/30   0.000
s     2/42   0.048
xl    1/21   0.048
```

**Zero movement in L and M.** The bands whose labels were most suspected — the
long ones, where the ask is buried under a thousand words — are the bands the
judges agreed with completely. The XL adversarial review predicted heavy movement
in XL and argued nine of its twenty-one items should not ship; adjudication moved
**one**.

Those two findings are not in conflict, and the distinction matters. The review
argued the items are *badly constructed* — bodies that deny their own asks, a
compute ask whose arithmetic is impossible, `why` fields describing a different
item. Adjudication asked only whether the **label** is right. An item can be
poorly built and correctly labelled, and most of the XL items the review attacked
are exactly that.

**A prediction recorded here yesterday was wrong.** It said the three `settled`
negatives the review attacked — `xl04n2`, `xl05n1`, `xl06n2` — would draw the most
adjudicator disagreement, because each announces a settlement the body denies in
the present tense. **None of the three moved.** The item that moved was the one
the review classed differently, as a `meta` ask that is really the `fit`
procedure. The reasoning behind the prediction was about body-versus-ask conflict;
the actual move was about an ask being a procedure in disguise. Right that the
review had found something, wrong about which thing.

## Inter-rater agreement is high, and that is not automatically good news

Fleiss κ = 0.890 over three judges. Judges agree with each other more than any of
them agrees with the key.

That is what a well-specified question looks like. It is **also** what a question
looks like when all three judges share a prior that the key does not — three
instances of the same model, given the same prompt, are not three independent
raters in the sense κ assumes. **κ = 0.890 measures the reproducibility of one
model's reading, not the objectivity of the labels.** Track N4's human holdout is
the only thing that separates those, and it does not exist.

Recorded so that 0.890 is never quoted as evidence the labels are right.

## What was checked and found not to hold

An exploratory hypothesis, tested and rejected: that disagreement would
concentrate on the eleven positives with no explicit interrogative or imperative
ask (`s12p` is one). Measured 2/27 against 2/76, Fisher exact p = 0.28. **Not
supported.** Post-hoc and underpowered, recorded because a hypothesis that was
checked and failed is worth as much in the record as one that held.

## What happens to the three labels

They are **not** being applied yet. Moving a label bumps the key version and
invalidates every comparison across the boundary — the defect with four instances
on record. The corpus is simultaneously being extended by 47 triples, so the key
should move **once**, at the freeze, with all three adjudicated moves and the
extension in a single version. Applying them now would mean two version bumps and
two sets of incomparable records.

The moves are recorded here, dated, with their votes, before that happens.
