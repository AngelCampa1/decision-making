# 2026-08-18 — N5's probe ran, and the prediction it was registered around was wrong

Outcome of the run registered in
[the prediction entry](2026-08-18-prediction-n5s-descriptive-probe-runs-at-last.md),
written before the first call. **86 calls**, one item per matched triple, 258
items / 86 triples at answer key **v4**, `haiku`, **0 unparseable**.

Every figure below was re-derived from the raw checkpoint by an independent
agent parsing the JSONL itself rather than reading the probe's report, and then
by me a third time. All three agree exactly.

## Result

| | |
|---|---|
| **`composed` rate** | **26/86 = 0.302**, 95% Wilson **[0.215, 0.406]** |
| corpus-weighted (1 positive : 2 negatives) | 0.321 |
| records / unparseable | 86 / **0** |
| distinct triples | 86 of 86, no triple twice |

## The registered prediction, and how wrong it was

**"The composed rate will exceed 0.50."** It is 0.302, and the interval's upper
bound is 0.406 — the prediction is not merely unmet, it is outside the interval.
The reasoning behind it was that a corpus written to a grid, with matched triples
and a fixed 1:2 ratio in every band, and with three authoring leaks already found
in it, should read as authored more often than not. **A blind judge disagrees:
it called roughly seven turns in ten a message a real person sent.**

One reading survives and is worth stating because it is not the one registered:
the *band-specific* upper bounds for `l` (0.635) and `xl` (0.690) do cross 0.50,
so a true rate above a half in the long bands alone is not excluded. The
registered band was aggregate. Read as written, it is falsified.

## The band prediction held, and the confound I registered in advance is total

| band | composed | | has em/en dash |
|---|---|---|---|
| xl | 8/17 = 0.471 | | 17/17 |
| l | 9/21 = 0.429 | | 21/21 |
| s | 5/24 = 0.208 | | 0/24 |
| m | 4/24 = 0.167 | | 0/24 |

**Band and dash-presence are the same partition of this sample.** Not
correlated — identical. Every `l` and `xl` item carries an em or en dash and no
`s` or `m` item carries one, so there is **zero within-band variance** in the
thing that would have to vary for the two to be told apart. The prediction entry
said "if the band gap appears *and* tracks that column, the finding is about
punctuation, not realism." It tracks it perfectly, and **this data cannot
separate them at all** — there is no contrast left to regress on.

What the free text says, which is suggestive and not decisive: **no cue names a
dash.** Twenty-one of 86 cues mention structure, formatting or polish —
*"formatting too perfect—real messages are messier even when organized"*,
*"footnote-style labeling"*, *"pedagogically structured"* — concentrated in `l`
and `xl` and mostly on `composed` verdicts. A judge can respond to a
dash-correlated register — tidy clause-linking, clean sentence structure —
without ever naming the mark, so this weakens the crude "it is pattern-matching a
glyph" story without touching the confound.

**The fix is cheap and belongs to whoever authors next**: put em dashes in some
short turns, or take them out of some long ones. Until then no band claim from
this instrument means anything.

## The label prediction, and a leak underneath it

Registered: *"the rate will not differ much by label."* Observed **0.250
positive against 0.357 negative**, a 10.7-point gap that does *not* shrink when
band is controlled (band-adjusted −0.114).

But `sample()`'s docstring already warns this row is the weakest printed: at one
item per triple, label is a **between-triple** contrast carrying whatever else
varies across triples. It does. **Positives skew high-stakes — 26 high / 18 low
against the negatives' 21 / 21 — and stakes has a larger effect than label
does:** 0.213 high against 0.410 low, a 19.7-point swing. Since high-stakes
reads as *less* composed and positives are disproportionately high-stakes, part
of the label gap is a stakes leak.

So "not much" is defensible only as *not resolved at this n* — the intervals
overlap, [0.146, 0.394] against [0.230, 0.508]. It is not defensible as *small*,
and it is not evidence about the label.

**The unregistered finding is the stakes gap itself**, which is nearly twice the
label gap and which nothing predicted. Low-stakes turns read as authored twice as
often as high-stakes ones. The obvious reading — that it is harder to write a
convincing low-stakes message because there is less to say — is a hypothesis this
run cannot test.

## What 0.302 does not license, which is most of what one would want from it

**It does not say the corpus reads real.** Nobody has shown what this judge, on
this prompt, says about 86 turns *known* to be human-written. Without that
anchor, 0.302 is equally consistent with a corpus that reads mostly like real
messages and with a judge that answers "real" about ambiguous text roughly 70% of
the time regardless of provenance. The prompt names `real` first and asks for a
cue on every reply, two biases the probe cannot measure on itself and says so.

What keeps it from being wholly uninformative: **the rate is not degenerate.** It
moves from 0.167 to 0.471 across bands and 0.213 to 0.410 across stakes, and both
verdicts appear in every stratum tested. That rules out the failure mode this
repository keeps finding — a clean number from an estimator that could not have
produced another — and shows the judge discriminates *something* in the text.
"Discriminates something" and "that something is realism" are different claims,
and only the first is supported.

**This is exactly the limit that motivated retiring the human audit and routing
N5's ground truth to a forced choice against N4's human turns.** Today's number
is the descriptive half doing its job: it is a rate with an interval, reported
and left alone.

## Two process failures, recorded because they are the second and third today

- **The prediction was authored before the first call and committed after it.**
  `0ee75d4` landed at 20:39:42; the run's last record was written at 20:43:13.
  The provenance gate checks *ancestry*, not timestamps, so it passes — but this
  repository's own rule is that a prediction which cannot be shown to predate its
  data is not evidence, and here only my word puts it there. **Commit the
  prediction before launching, not before the run finishes.**
- Earlier today an N6 readiness check computed three of four registered
  quantities as a side effect of proving the estimators could move, which is
  scoring under another name
  ([recorded here](2026-08-18-n6-two-arms-in-and-the-bands-were-checked-before-i-meant-to-look.md)).
  Both slips are about *ordering*, not about arithmetic, and both were caught
  only because somebody wrote down what happened in what sequence.
