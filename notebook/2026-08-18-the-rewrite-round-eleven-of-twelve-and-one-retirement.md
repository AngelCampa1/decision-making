# 2026-08-18 — the rewrite round: eleven of twelve, and one retirement

Outcome of the round registered in
[the stopping rule](2026-08-18-prediction-the-rewrite-round-and-its-stopping-rule.md),
which was committed before any ask was rewritten and before any call was made.
**36 calls**, 12 cases × 3 blind judges, 0 unparseable.

## Result

| | before | after |
|---|---|---|
| of the 12 disputed items, agreeing with the key | 0 | **11** |
| pairwise judge agreement, on those 12 | 0.611 | **1.000** |
| Fleiss kappa, on those 12 | 0.084 | **1.000** |
| corpus-wide movement | 12/261 = 0.046 | **1/261 = 0.004** |
| corpus-wide Fleiss kappa | 0.862 | **0.898** |

**The registered band was "at least 8 of the 12". It came in at 11**, and the
diagnosis it was testing held: every disputed negative had been putting two
options in a frame that invites ranking them, and rewriting each to ask about
one thing was enough. The clearest case is `s02n2`, which went from *"Is there a
tax difference between paying down my interest-free family loan and putting that
money into my pension?"* to *"My family loan is interest-free, and I get a 4%
pension match. Is the match on the pension treated as taxable income this
year?"* — same nouns, same situation, one question.

The defect generalised further than the rule as written. `xl16n1` asked *"where
would you have me look first?"*, which is the same shape moved from *choosing
between* options to *prioritising among* them, and `m16n2` asked *"what should I
be writing down for him, and in what order?"* — a sequencing judgement wearing a
task. Neither is a comparison of two options in the literal sense. Both were
fixed by the same move.

## The prediction that was wrong

**I registered that the two positive → negative items would be harder and that I
would not be surprised if both retired.** `m18p` and `s12p` are both among the
eleven that fixed, on the first attempt. The reasoning behind the prediction —
that strengthening an ask is harder than defusing one — was simply not borne
out: both turns had ended on a bare fact with no signal that the writer wanted
help, and saying so plainly was enough. `m18p` gained *"with no idea which of
the three to land the room on"* and `s12p` gained *"and now I must pick one to
book against"*.

## The one retirement

**`l15n2` still moves, unanimously, on the rewritten text.** Under the
registered rule — one round, exactly one, and whatever is still disputed is
retired — the `l15` triple is retired whole, because the plan's own rule is that
a retired body retires its triple and because retiring one member would leave a
structure the corpus forbids.

The corpus is now **258 items, 86 triples** — s 24, m 24, **l 21**, xl 17.

What `l15n2` asks after the rewrite is whether an *n* = 11 sample supports any
conclusion, which is a determinate question about a quoted email. Three readers
still say a decision skill should fire on it. The most likely reading, and it is
a reading rather than a finding: over a long enough body about the reader's own
situation, no question is inert, because the reason to want any of it is
visible. The XL agent working this round reached the same conclusion
independently while authoring — *"when the body is 1,200 words of a loaded
situation, almost any question over it can be read as serving a decision"*.
If that is right, it is a limit on how many negatives the long bands can carry,
and it belongs to N6's interpretation rather than to this round.

## What did not happen, which was the thing to watch

**No gate crossed and no baseline entry was orphaned.** The battery reads three
findings — the same three keys, no fourth — and the stump sits at 0.705 against
a majority baseline of 0.667, lift 0.038 against a 0.10 cap.

The specific risk was that rewriting several negatives into *"Restate…"* asks
would trade the comparison-framing leak for an `imperative_opener` one. It did
not: `imperative_opener` produced no finding.

**And the two `sentence_count` findings ended up *stronger*, 3.11σ → 3.18σ.**
That is worth stating because the opposite happened first. Three of the initial
rewrites changed their turn's sentence count, which pushed a corpus-wide habit
sitting at 3.01–3.11σ below its 3.0 gate and orphaned two baseline lines — a
label fix quietly closing two open shortcut findings, which is precisely what
the adversarial review warned would be indistinguishable from tuning the corpus
until its gates go green. The XL agent caught this unprompted and rephrased to
preserve its sentence counts; the M and L bands were corrected to match. The
skew is real and unfixed and it stays visible.

## Two things about the instrument, found by using it

**The adjudicator has no re-run path for a *changed* item, and the first attempt
to make one produced a clean run that measured nothing.** Running
`adjudicate.py --only <the 12>` against the live ledger printed *"0 calls
remaining after resume"*, re-emitted the pre-rewrite votes, and reported
**movement 1.000 and `CORPUS RETIRED: movement above the pre-registered
threshold`** — an alarming, well-formed number produced by zero model calls, on
a subset selected to be exactly the items that had moved. Nothing crashed. It is
the sixth instance of the shape this repository keeps cataloguing, and the tell
was one line of output above the result.

`--missing-only` covers items with *no* records. A rewrite round produces items
with *stale* records, and there is no flag for that. The workaround — a fresh
checkpoint file — then trips the label-version gate, whose exemption
(`rescore.NOT_A_CHECKPOINT`) is the exact string `adjudication.jsonl`. Both are
defensible individually and together they leave the documented workflow
unsupported.

**The dead retirement branch was already known to the code.** The commit that
opened this round said the plan's *"split 3 ways → retire"* branch is
unreachable with three binary judges. `adjudicate.py`'s own docstring had said
so all along: *"3-way split is impossible on a binary question, so its analogue
here is a 2-1 split agreeing with me, which keeps the label and is recorded as
contested."* So the implementation had resolved it and the plan text had not,
and neither says what to do when the majority disagrees **and** the label cannot
move — which is the case that actually arose, twelve times.

## The limit, restated because the numbers are flattering

Perfect inter-rater agreement on twelve previously-contested items is a good
result and it is also the shape a tuned corpus would produce. The guard is that
the rewriters were never shown the judges' rationales — they were given the
authoring rule and the body, and nothing about what any judge had said — so the
rewrites cannot have been fitted to particular objections. That guard is real
but it is not a proof.

The author was a model, the rewriters were models, the judges are models. This
round made the corpus internally consistent. It did not make it right, and
nothing in it bears on whether these labels match what a person would say.
**That is N4's job**, and N4 now has four licence-cleared sources to draw on.
