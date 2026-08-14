# 2026-08-14 — the opener leak closed by touching both sides

[`notebook/2026-08-14-the-battery-searches-176-cells-and-nobody-had-costed-that.md`](2026-08-14-the-battery-searches-176-cells-and-nobody-had-costed-that.md)
named the strongest surviving finding in the 176-cell family: whether a turn's
**first sentence** ends in a question mark separates positives from negatives
in `l` and `xl` at AUC 0.716 and 0.779. This entry closes it, reports a
constructional side effect the fix produced and how it was resolved, and
records what else moved when it did.

## Re-derivation, independent of the numbers handed to me

Re-ran the 176-cell permutation sweep myself — pooled per-band AUC, positives
against all negatives inside one band, 20,000 within-triple label draws for the
null, Benjamini–Hochberg over all 176 cells — before touching anything. First
pass had a bug (the "observed" statistic was accidentally the *matched*
within-triple AUC while the null was pooled, comparing two different
statistics), caught by checking that AUC values matched the handed-down table
before trusting the p-values. Fixed, re-run:

All seven of the handed-down cells reproduced, AUC values exact to three
decimals: `xl/open/question_marks` 0.779, `xl/open/terminal_question` 0.779,
`l/open/question_marks` 0.716, `l/open/terminal_question` 0.716,
`l/close/type_token_ratio` 0.217, `xl/open/type_token_ratio` 0.218,
`xl/close/type_token_ratio` 0.230 — all matched. My sweep additionally crossed
BH on a handful of `ask`-view cells the handed-down table didn't list (16 total
survivors against 7), traced to Monte Carlo noise at the boundary for some and
to a genuine pre-existing `l`/`ask`/`type_token_ratio` signal (AUC 0.315,
essentially unmoved by anything below) for others — noted, not chased, since
the assignment was the opener leak specifically.

## The habit, measured before touching anything

|      | positives opening with `?` | negatives opening with `?` |
|---|---|---|
| `l`  | 10 / 22 (45.5%) | 1 / 44 (2.3%) |
| `xl` | 10 / 17 (58.8%) | 1 / 34 (2.9%) |

Whichever member of a triple carries the ask as a single leading question
scores as a positive nineteen times out of twenty in the long bands.

## The fix: variety, not a direction

Per `CLAUDE.md`'s own trap warning — every earlier generation of this defect
came from a rule pushed in one direction — the fix touches **both** sides of
the label:

- **4 positives per band** (`l10p l13p l18p l22p`, `xl04p xl07p xl10p xl12p
  xl16p` — 5 chosen in `xl`) had their opener reordered so the question is no
  longer the first sentence: where the ask already had a second sentence, the
  two were swapped; where the ask was a single short question with nothing
  else, a one-clause statement was prepended ("I keep starting this message
  and deleting it. Do I fight this? ...").
- **10 `l` and 9 `xl` negatives** — drawn from `lookup`/`compute` kinds, whose
  asks are already determinate questions — had their existing question moved
  to the front instead, or (twice, where no `?` existed anywhere in the ask) an
  imperative was reworded into an interrogative with the same request
  ("Do the arithmetic for me" → "What is the arithmetic"). (A first pass moved
  11 and 10 respectively; three were reverted after re-adjudication — see
  below.)

Every edit is a reordering or small addition **strictly after** each triple's
true shared prefix. Checked directly, not assumed: `corpus._shared_body`
recomputed on every touched triple after editing returns the same length as
before, for all touched triples.

**Result:**

|      | positives opening with `?` | negatives opening with `?` |
|---|---|---|
| `l`  | 6 / 22 (27.3%) | 10 / 44 (22.7%) |
| `xl` | 5 / 17 (29.4%) | 9 / 34 (26.5%) |

Not an exact match — a first pass reached an exact 27.3%/27.3% and
29.4%/29.4% by question-ifying 11 `l` and 10 `xl` negatives, but three of
those items (`l12n1`, `l17n2`, `xl15n2`) turned out to change the ask's
meaning, not just its dispersion, and were reverted (below) rather than kept
for the sake of a round number. What's left is still an eighteen-to-tenfold
reduction in the gap between the two rates, reached the same way: touching
which triples lean which way, not homogenizing every triple.

## Three items that moved label, and why they were not kept as new positives

Every item whose opener changed was sent to blind re-adjudication before
anything was assumed still valid, per the task's instruction that the label
rests on the ask. The first run — 29 items, 3 judges, `scripts/adjudicate.py`
on haiku — came back with 3 of 29 moved 2-of-3 or 3-of-3 against the original
label, movement rate 0.103 against a pre-registered kill of 0.2 (survives),
all three the same direction:

| id | original | adjudicators' votes | moved to |
|---|---|---|---|
| `l12n1` | negative (`lookup`) | True, True, True | positive |
| `l17n2` | negative (`lookup`) | True, True, True | positive |
| `xl15n2` | negative (`lookup`) | True, True, False | positive |

This was not treated as a discovery about the original corpus, for a
structural reason: these are matched triples, one positive and two negatives
by construction, and `_check_triples` enforces exactly that. Accepting the
move would have put two positives in each of three triples, which is not a
label correction, it is a broken invariant.

Investigated instead of either accepted or dismissed. Diffing what changed:
both `l12n1` and `l17n2` had a question moved to the front of the ask, and in
both cases doing that pushed a short framing clause — "One process question,
separate from the above." (`l12n1`), "Clause 9.2 is the part of the schedule
I cannot pin down." (`l17n2`) — from leading the ask to trailing it.
`xl15n2` is the same shape: "The leaflet says one thing about alcohol and
the forum says another." moved from leading to trailing. Read in isolation,
all three questions are determinate lookups regardless of order ("who runs
X", "who counts as Y", "which of these two sources is right"). What the
leading clause was doing, in each case, was decoupling that lookup from an
emotionally loaded shared body — `l12`'s body is about coming off medication
before a pregnancy attempt, `l17`'s about a safeguarding-inbox migration
decision, `xl15`'s about a drug-interaction judgment call — by naming the
question up front as separate, narrow, administrative. Moving the question
to the front and the decoupling clause to the end removed that framing, and
three adjudicators (out of the ones assigned to these three items) read the
now-undecoupled question as part of the surrounding decision rather than
apart from it. That is a real content change caused by construction, not a
mislabel in the original corpus surfacing.

**Resolution:** all three reverted to their original text — confirmed
byte-identical to the pre-session version via `git diff` on each region — and
dropped from the touched-item list rather than kept and independently
adjudicated as new positives. The 9 checkpoint records covering their
edited-but-reverted text (3 items × 3 judges) were excluded from the merge
into `results/triggers/adjudication.jsonl` rather than appended, since they
judged text that no longer exists on disk. Re-running the report on the
remaining 26 touched items confirms the fix: **0 of 26 moved**, 3 contested
(2-1 kept), same inter-rater agreement (pairwise 0.923, Krippendorff's alpha
0.840). The three reverted items are, by construction, back to whatever
their historical adjudication record already said, since their text is
unchanged from before this session.

Structural integrity re-checked after the revert (`_shared_body` length and
the 10%-of-longest word-count tolerance) for all touched triples: 0 problems.

## Before / after, full 176-cell family

Sweep re-run against the corpus as it stands after the revert above (not the
intermediate state with the flawed edit still in place):

| band | view | feature | AUC before | q before | AUC after | q after |
|---|---|---|---|---|---|---|
| `l` | open | terminal_question | 0.716 | 0.0000 | **0.523** | 1.0000 |
| `xl` | open | terminal_question | 0.779 | 0.0044 | **0.515** | 1.0000 |
| `xl` | open | question_marks | 0.779 | 0.0044 | **0.515** | 1.0000 |
| `l` | open | question_marks | 0.716 | 0.0044 | **0.523** | 1.0000 |
| `l` | ask | type_token_ratio | 0.315 | 0.3202 | 0.314 | 0.0088 |
| `xl` | open | type_token_ratio | 0.218 | 0.0106 | 0.324 | 0.1962 |
| `l` | close | type_token_ratio | 0.217 | 0.0279 | 0.297 | 0.1887 |
| `xl` | ask | sentence_count | 0.299 | 0.1856 | 0.354 | 0.0440 |

All four target cells clear BH by a wide margin (q = 1.0, was q ≤ 0.0044).
`l/close/type_token_ratio` and `xl/open/type_token_ratio` both improved
(moved toward 0.5, cleared BH) without being touched directly. Independently,
the task-giver re-ran the same test with a different implementation (band-
restricted plain unpaired AUC rather than my per-cell pooled version) against
the corpus as it stood after the *first* pass of the fix (before the revert
above): 18 cells crossing p < 0.05 before against 8.8 expected, 7 BH
survivors before (5 this leak) against 10 crossing / **0** surviving after.
`question_marks` and `terminal_question` did not appear anywhere in that
table either. The two implementations disagree on the pre-fix survivor count
(mine found 16, theirs 7 — Monte Carlo/pre-existing-signal, noted above, not
chased) but agree on direction and on the post-fix result, and my own
post-revert re-run above confirms the same shape survives the revert: 21
cells cross p < 0.05 uncorrected (was 18, expected 8.8 either way), 2 survive
BH, the same 2 pre-existing cells discussed next — not this leak reappearing
and not a new one.

Two cells newly cross BH: `l/ask/type_token_ratio` and `xl/ask/
sentence_count`. Checked whether either is the fix moving the leak sideways:

- `l/ask/type_token_ratio` moved 0.315 → 0.314 — **unchanged**. It sat at
  q = 0.32 before only because more numerous, stronger leaks were absorbing the
  Benjamini–Hochberg budget; removing those raised every remaining p-value's
  rank. Pre-existing, not created here.
- `xl/ask/sentence_count` moved 0.299 → 0.354, which is **closer to 0.5**, not
  farther — three of the five de-questioned XL positives needed a prepended
  lead-in sentence because their entire ask was one short question with
  nothing else, and that raised their `ask` sentence count from the shortest
  cluster toward the middle of the distribution. It crosses BH now for the
  same reason as the item above: less competition for the correction budget.

Neither is the failure mode the trap warns about (a leak relocated by an
unbalanced push); both are pre-existing signal made newly visible by removing
larger ones. Left as open findings rather than chased further under this
task's scope.

## The corpus's own gate, not just my ad hoc sweep

`corpus.py::check_corpus` runs a different, more sensitive statistic on the
same feature/view family — the *matched* within-triple rank and its
*dispersion*, gated at z = 3.0 rather than by pooled-AUC threshold. Before this
edit: `matched:open:question_marks` and `matched:open:terminal_question` were
both baselined findings (6.12 null SE). After: **neither reproduces** — both
keys now match no current finding, which `de check` requires be recorded by
deleting the baseline lines (may-only-shrink) rather than leaving them stale.

One gate finding briefly appeared and closed the same day: the first pass of
this fix (before the three-item revert above) nudged `cancel:close:
type_token_ratio` from ~2.9 to 3.04 null SE — just over the gate — because
two of the three reverted items' reordering also moved a trailing framing
clause and shifted a couple of closing sentences by a clause. Investigated
before baselining anything: the underlying skew is real and corpus-wide (the
positive is the highest- or lowest-diversity member of its own triple in
**66 of 87 triples**, `s` 17/24, `m` 14/24, `l` 21/22, `xl` 14/17), predates
this session, and is not something an opener-focused fix should be chasing —
fixing it needs a length/complexity-neutral rewrite of closing sentences
across most of the corpus, out of scope here and a straight shot at becoming
generation five of the per-item-nudge defect the `word_count` entry above it
in `corpus-baseline.txt` already names. It never shipped as a baseline entry:
reverting the three items for the label reason above incidentally reverted
the closing-sentence shift too, and the statistic is back at 2.985 null SE,
under the gate, on the corpus as committed.

Current gate state: 3 findings, all pre-existing and unrelated to this fix
(`cancel:turn:sentence_count`, `matched:ask:type_token_ratio`,
`cancel:ask:sentence_count`, all already baselined from the 2026-08-14
long-band merge). Checked directly: 0 unbaselined issues, 0 stale baseline
entries.

## A claim raised, checked, and refuted: is the fixed check still capable of failing

Balancing a band-level rate (27.3% vs 22.7% in `l`, 29.4% vs 26.5% in `xl`,
after the revert above; exactly matched in the pre-revert version) raises the
same question the `_shared_body` bug exposed: a check that reads near 0.500
can mean "no signal" or it can mean "cannot possibly read anything else," and
the battery can't tell those apart on the AUC number alone — that's what
`Check.inert` (`attainable_auc` / `matched_attainable` against `MATCHED_Z`)
exists to catch.

The task-giver's first read of the pre-revert exact-match rates was that
opener form must now be homogeneous *within every triple*, making
`matched_attainable` on these cells degenerate by construction (every
permutation the design allows gives exactly 0.500) — the same signature the
`_shared_body` bug produced, where a feature was inert because the splitter
was broken rather than because the corpus was clean. That would matter: a
check that cannot fail is not a check, whatever number it reports.

It didn't hold, and the repository's own rule — no finding believed until
confirmed, applied to a finding sent to me as much as one I produce myself —
is why this got checked before it went in the entry rather than transcribed.
Computed directly against `corpus.py`'s own functions, band-restricted,
`open` view, `question_marks`/`terminal_question` (identical values, so one
check covers both), re-run here on the final post-revert corpus:

|  | triples internally uniform | `matched_attainable` | `null_se` | `matched_dead`? | `pooled_att` | `inert`? |
|---|---|---|---|---|---|---|
| `l`  | 8 / 22  | (0.318, 0.795) | 0.060 | reach 0.295 > 0.180 → **False** | (0.066, 0.934) | **False** |
| `xl` | 8 / 17  | (0.338, 0.735) | 0.062 | reach 0.235 > 0.187 → **False** | (0.111, 0.889) | **False** |

Only 8 of 22 `l` triples and 8 of 17 `xl` triples have the positive and both
negatives agreeing on opener form; the other 14 and 9 still vary internally.
The band-level rate comes from mixing which *triples* lean which way, not
from flattening each triple. `null_se` is nonzero and `matched_attainable`'s
reach from 0.5 clears `MATCHED_Z * null_se` by a wide margin on both bands —
not the constant-feature signature the `_shared_body` bug produced, and
`Check.inert` returns `False` on both axes, both bands. The check that closed
this leak stays capable of catching a regression: the observed AUC sits near
0.5 because the real label assignment happens to balance, while a different
assignment on the same corpus could show up to 0.795 (`l`) or 0.735 (`xl`).

**Where the claim came from.** The task-giver independently re-ran the same
homogeneity count on the pre-revert corpus afterward and got 7/22 and 7/17,
matching exactly, and named the root cause in their own words: the 2:1 ratio
in the pre-revert counts follows from *any* label assignment where
question-opening negatives outnumber question-opening positives two to one —
it does not require within-triple homogeneity, and reading a coincidence of
aggregate counts as a structural fact was the error. Recorded here rather
than only in the exchange because a refuted claim is worth as much as a
confirmed one: it is the reason this check gets a table of its own instead
of a one-line "verified fine," and it is a second instance of the same
"inert for a derivation reason versus inert for a corpus reason" distinction
already on record from `_shared_body` — this time caught before it reached
a governed file rather than after.

**Why the real result is the better outcome anyway.** The majority of `l`
and `xl` triples still vary internally, which is what keeps
`matched_attainable`'s reach well above the dead-band requirement — the
check has room to move if a future edit reintroduces the habit. Balancing
the aggregate while leaving most triples' own mix alone is a direct instance
of "variety across the band, not a per-item rule": the fix did not need
every triple to change to close the leak, and not changing every triple is
exactly what left the check able to fail again if the leak comes back.

## What I am not claiming

The `close`-view `type_token_ratio` dispersion finding is real, corpus-wide,
and not closed by this session's work — it predates this session, sat under
the gate before and after, and would need a corpus-wide closing-sentence
rewrite to actually close, which is out of scope here. The two newly-crossing
`ask`-view cells above are genuine, pre-existing signal that this fix did not
create and did not fully explain; they are reported rather than adjudicated
away. And the three-item label episode above is not a claim that the
original corpus had a construction defect in `l12`, `l17`, or `xl15` — those
triples are back to their original, previously-adjudicated text, unchanged
by this session in any way that survives to the committed corpus.
