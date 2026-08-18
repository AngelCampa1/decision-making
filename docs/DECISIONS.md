# Decision register

**Every change to `datasets/triggers/` or `skills/` needs an entry here, and
`de check` refuses one that does not have it.**

Those two paths are the answer key and the product. A change to either moves
numbers that are already published: on 2026-08-13 one turn moved from the
positives to the negatives, recall rose 3 to 5 points on every arm on disk, and
**not one call was re-made**. That was a correct maintainer decision, and in a
JSONL file it is indistinguishable from a model result. The reasoning has to
live somewhere a reader of the numbers can reach.

The reasoning already existed — in commit bodies, and they are good ones. But
`git log` is not greppable by topic and is invisible to anyone reading `docs/`.
Commit trailers were considered as the store and rejected: commit messages here
cannot be amended, because the history *is* the pre-registration evidence, so a
trailer somebody forgot would be permanently unfixable. A file can be amended.

**Entries below the first heading are backfilled** from the commit bodies that
already carried the reasoning. They are transcriptions and point at the commit
for the full argument; nothing here was reconstructed from memory.

Format: `## <date> — <title>`, a `**Commits:**` line, then why.

---

## 2026-08-18 — Twelve disputed asks rewritten, one triple retired, and the key still has not moved

**Commits:** `08eda89`

**Twelve turns change and no label does.** N3's blind adjudication left 12 items
where the judges' majority disagreed with the key. Applying those moves is
impossible: all 12 land in triples that would end up with two positives or none,
because in each of the ten negative → positive cases the same adjudication
**unanimously** reconfirmed that triple's existing positive. So the disagreement
was never evidence that a label was wrong — it was evidence that **the authored
contrast did not land**, which the v3 plan's rule sends to *rewrite the turn*.

**The rule the rewrites were written to:** an inert ask asks about one thing. It
may share every noun with the positive; it may not put two options in a frame
that invites ranking them. Diagnosed from `s02n2` and applied to all twelve
without the rewriters being shown any judge's rationale — a rewrite aimed at a
stated objection is tuned to that judge.

**Result: 11 of 12 now agree with the key** on blind re-adjudication (36 calls,
0 unparseable), against a registered band of 8. Judge agreement on those twelve
went from 0.611 pairwise to 1.000, and corpus-wide movement from 12/261 = 0.046
to **1/261 = 0.004**.

**`l15` is retired whole** — `l15n2` still moves unanimously after its rewrite,
and the registered rule is one round only. The plan's rule that a retired body
retires its triple applies, and retiring one member would leave a structure the
corpus forbids. **The corpus goes from 261 items / 87 triples to 258 / 86** —
s 24, m 24, l 21, xl 17.

**No gate crossed and no baseline entry was orphaned**, which took a correction
mid-round. Three initial rewrites changed their turn's sentence count and pushed
a corpus-wide habit sitting at 3.01–3.11σ under its 3.0 gate, which would have
had a label fix quietly closing two open shortcut findings — the pattern this
register has already named four times. Rephrased to preserve sentence counts;
the two `sentence_count` findings now read **3.18σ**, stronger than before the
round. `datasets/triggers/corpus-baseline.txt` is unchanged: same three entries,
same keys.

**The answer key still has not moved and no version has been bumped.** Nothing
in this change alters a `should_fire`, so no published number is affected and
`set_version` stays where it was. The freeze — if one is still wanted — now has
one disputed item instead of twelve, and that item is gone.

Protocol registered before the round in
[`notebook/2026-08-18-prediction-the-rewrite-round-and-its-stopping-rule.md`](../notebook/2026-08-18-prediction-the-rewrite-round-and-its-stopping-rule.md);
outcome, including a registered prediction that turned out wrong, in
[`notebook/2026-08-18-the-rewrite-round-eleven-of-twelve-and-one-retirement.md`](../notebook/2026-08-18-the-rewrite-round-eleven-of-twelve-and-one-retirement.md).

---

## 2026-08-14 — The opener leak closed by touching both sides, not one

**Commits:** `cee9329`

A 20,000-draw permutation sweep of the full 4-band x 4-view x 11-feature
family (`notebook/2026-08-14-the-battery-searches-176-cells-and-nobody-had-
costed-that.md`) found `question_marks`/`terminal_question` on the `open`
view as the strongest survivors of Benjamini-Hochberg correction across all
176 cells: AUC 0.779 in `xl`/`open`, 0.716 in `l`/`open`, p < 0.001 both.
Measured directly before any edit: in `l`, 10 of 22 positives opened their
ask with a question against 1 of 44 negatives; in `xl`, 10 of 17 against 1
of 34 — whichever triple member led with a question scored as the positive
nineteen times out of twenty in the long bands.

**The fix is variety, not a direction.** Every earlier generation of this
defect (`word_count`, closed 2026-08-14 earlier the same day) came from a
rule pushed one way — this one touches both sides of the label instead: 4
positives per band (5 in `xl`) had their opener reordered, or given a
one-clause statement lead-in where the whole ask was a single question, so
the question no longer opens the ask; 10 `l` and 9 `xl` negatives — drawn
from `lookup`/`compute` kinds whose asks are already determinate questions —
had their existing question moved to the front instead. Every edit is a
reordering or small addition strictly after each triple's true shared
prefix; `corpus._shared_body` recomputed on every touched triple returns the
same length as before the edit. Resulting rates: `l` 6/22 positives vs
10/44 negatives (27.3% vs 22.7%), `xl` 5/17 vs 9/34 (29.4% vs 26.5%) — not
exact, because three items that would have made it exact were reverted (next
paragraph) rather than kept for the sake of a round number.

**Three items moved label under re-adjudication and were reverted, not
accepted.** A first pass touched 29 items (11 `l` and 10 `xl` negatives).
Blind re-adjudication on all 29 — 3 judges, `scripts/adjudicate.py` — found
3 moved 2-of-3 or 3-of-3 against the original label, all negative-to-positive:
`l12n1`, `l17n2`, `xl15n2`. Investigated rather than accepted, because
accepting would have put two positives in a one-positive-per-triple design.
In all three, moving the existing question to the front of the ask also
pushed a short framing clause ("One process question, separate from the
above." and similar) from leading to trailing — that clause was decoupling
a determinate lookup from an emotionally loaded shared body, and losing it
made the same question read as part of the decision rather than apart from
it. All three reverted to original text (confirmed byte-identical via
`git diff`) and dropped from the touched set; re-adjudication on the
remaining 26 items: 0 moved. Fresh adjudication records for the reverted
three's flawed text were excluded from the merge into
`results/triggers/adjudication.jsonl` rather than appended.

**Verified against the full family, not just the targeted cells.** Re-ran
the 176-cell sweep after the final edit (post-revert): all four target cells
clear BH by a wide margin (AUC 0.523/0.515, q = 1.0, was q <= 0.0044).
`l/close/type_token_ratio` and `xl/open/type_token_ratio`, named by the same
notebook as adjacent leaks, both improved without being touched directly.
Two cells newly cross BH (`l/ask/type_token_ratio`, `xl/ask/sentence_count`);
both checked and are pre-existing signal exposed by removing larger leaks
that were absorbing the correction budget, not the leak relocated by an
unbalanced push — see the notebook entry for the per-cell reasoning.
Independently, the task-giver re-ran the same test with a different
implementation against the corpus after the first (pre-revert) pass: 18
cells crossing p<0.05 before (8.8 expected) and 7 BH survivors (5 this leak)
against 10 crossing / 0 surviving after.

**The corpus's own gate.** `matched:open:question_marks` and
`matched:open:terminal_question` no longer reproduce and are removed from
`corpus-baseline.txt` (may-only-shrink). One gate finding,
`cancel:close:type_token_ratio`, briefly crossed 3.0 (to 3.04) during the
first pass — two of the three reverted items' reordering shifted a couple of
closing sentences by a clause — and closed the same day when those three
were reverted (measured after: 2.985, under the gate). The underlying skew
is real, corpus-wide (positive is the highest/lowest vocabulary-diversity
triple member in 66 of 87 triples, every band), predates this session at
~2.9 null SE, and needs a length/complexity-neutral rewrite of closing
sentences corpus-wide to actually close — out of scope here, and not added
to the baseline because it never shipped as a crossing finding on the
committed corpus.

**A claim raised and refuted.** The task-giver's read of the near-exact
pre-revert opener rates was that `matched_attainable` on these cells must now
be degenerate by construction (every permutation gives 0.500, the
`_shared_body`-bug signature). Checked directly against `corpus.py`'s own
functions rather than transcribed: only 8 of 22 `l` triples and 8 of 17 `xl`
triples have all three members agreeing on opener form; `null_se` is nonzero
and `matched_attainable`'s reach from 0.5 clears `MATCHED_Z * null_se` on
both bands (`Check.inert` is `False`, both axes, both bands, verified on the
final corpus). The band-level rate came from mixing which triples lean which
way, not from flattening each triple, so the check that closed this leak
stays capable of catching a regression.

**Two tests re-pinned in the same commit.** `test_corpus_battery.py` pinned
the shipped baseline's deferred-finding count at 5 and one per-band figure at
`xl 0.235` for `sentence_count`'s `cancel:` finding on `turn`. Both are
data-driven pins against the live corpus rather than assertions about
mechanism: the count drops to 3 as the two `question_marks`/
`terminal_question` findings above close, and `xl 0.235` moves to `xl 0.309`
because several `xl` positives gained a lead-in sentence, which shifts
`sentence_count`'s distribution. The reporting format itself (one
`band value` pair per band) is unchanged — checked before re-pinning rather
than assumed, since a changed message would have meant something broke
rather than moved.

Full derivation, before/after opener counts, the three-item investigation,
and the complete 176-cell before/after table:
`notebook/2026-08-14-the-opener-leak-closed-by-touching-both-sides.md`.

## 2026-08-14 — The ask cut stopped one word short of every shared body's newline

**Commits:** `6707c38`

`_shared_body` cut the raw byte-identical prefix of a triple's three turns
back to the last SPACE so the remainder starts at a whole word. Every
authored body ends with a NEWLINE before the ask, and a newline is not a
space — the cut landed one word short of where the newline actually was, and
that word ("believed." in the shipped XL band) leaked into every derived
`ask` and `open` as their shared, constant opening word. A regression test
was confirmed to fail against the pre-fix code before the fix landed.

**What the bug had been hiding.** A feature reading a constant leaked word
across an affected triple cannot separate anything and reads exactly 0.500 —
indistinguishable from a clean pass. Once the leak stopped being constant,
two matched within-triple findings crossed the z = 3.0 gate for the first
time: `matched:open:question_marks` and `matched:open:terminal_question`,
0.566 at 3.47 null SE pre-merge, baselined in `corpus-baseline.txt` with a
`CLOSED BY` condition. `matched:turn:word_count` and `matched:ask:word_count`
read bit-identically before and after this fix (0.66015625 both times) — the
leaked word was present in all three members of an affected triple, so
removing it shifts all three equally and a within-triple rank statistic
cannot see a shift common to the whole triple. Both findings closed the same
day, but by the concurrent long-band merge (`a38d2d8`, see the entry below),
not by this fix.

**The guard, checked against the day's other additions.** `sentence_count`
(added earlier the same day alongside the `open` view) was inert in every
view of the known-good fixture — its three fixed shapes all produced two
sentences, so the feature could not move regardless of label. Fixed by giving
one shape a third short sentence. The planted closing-leak fixture turned out
to leak on `open` as well as `close`, symmetrically — reversing a
two-sentence tail swaps which sentence is first exactly as much as which is
last, and a constant sentence placed in front of the swap does not shield
`open` because `_shared_body` folds anything that never varies into the body
regardless of position. The baseline-narrowness test's helper was widened to
capture every finding the fixture currently produces rather than a
hand-picked subset that predated the `open` view.

Full account, including the per-finding numbers before and after the
concurrent merge: `notebook/2026-08-14-the-ask-derivation-bug-and-two-checks-it-had-been-hiding.md`.

---

## 2026-08-14 — Twenty-three long-band triples, and a leak that closed sideways

**Commits:** `a38d2d8`

`l.yaml` gains `l10`–`l22` (13 triples) and `xl.yaml` gains `xl08`–`xl17` (10),
the rebuild that was "mid-rebuild and unmerged" in the entry below. The corpus
goes from 192 items (64 triples) to 261 (87). **No label on an existing item
changes here.** The three moves N3's adjudication found (`s02n2`, `s12p`,
`xl05n2`) are still not applied — this change merges the authored triples only
and does not touch that backlog, so "the freeze" the entry below anticipated is
still open on that point.

**Both `word_count` findings closed, but not by the condition the previous entry
named.** That entry called for a rank roughly uniform across longest, middle and
shortest. Measured on the 23 new triples: 16 positive-shortest, 5 positive-middle,
2 positive-longest — the mirror image of the 49-of-64 positive-longest bias
projected against, not a uniform split. `word_count` closed anyway, from matched
0.660 (3.24 null SE) to 0.546 (1.09), because `l` and `xl` swung from
positive-longest bias (0.778, 0.393) to positive-shortest bias (0.455, 0.294),
which happened to average against `s` and `m`'s unchanged positive-longest bias
and land the pooled/matched figure under the gate.

**The same swing opened two findings the previous corpus did not have.**
`sentence_count`, which tracks `word_count` closely, crosses the *dispersion*
gate on both `turn` and `ask` views (3.82 null SE, `cancel:` not `matched:` — the
mean stays near chance at 0.480 but the positive sits at an extreme of its triple
far more often than chance). `type_token_ratio` on the `ask` view crosses the
*matched* gate outright (0.316, 4.27 SE, below chance in all four bands). Not
retuned to close them: three features reading the same closing-sentence habit
through different rulers, and per-item retuning against whichever one is
currently over the line is the mechanism `docs/DECISIONS.md`'s own entries have
already named four times.

**`datasets/triggers/corpus-baseline.txt`:** the two `word_count` entries are
deleted; three replace them —
`cancel:turn:sentence_count`, `cancel:ask:sentence_count`,
`matched:ask:type_token_ratio` — with the same rank-uniformity condition named as
what would close them, corpus-wide. A concurrent session's `matched:open:
question_marks` / `matched:open:terminal_question` entries, added the same day
for an unrelated `_shared_body` measurement fix, are left as that session wrote
them; this merge shifts their numbers too (0.566→0.629 matched, 3.47→6.12 SE)
but the key still matches, so the gate still reads them as open and baselined.

Full battery, before/after per-band figures, and the rank-count measurement are
in `notebook/2026-08-14-the-long-band-merge-closed-one-leak-and-opened-two.md`.

## 2026-08-13 — Twenty-four short-band triples, and a statistic the design had always deserved

**Commits:** `e07c5ef`

`s.yaml` gains ten triples (`s15`–`s24`) and `m.yaml` fourteen. The corpus goes
from 120 items to 192. **No label on an existing item changes here** — the three
moves N3's adjudication found (`s02n2`, `s12p`, `xl05n2`) are recorded in the
notebook and are deliberately *not* applied, because the key must move once, at
the freeze, with the long-band rebuild in the same version bump. Two bumps means
two sets of incomparable records.

**Why the short bands and not the long ones.** A power analysis nobody had run
before the corpus was authored: at the measured design effect of 1.63 the short
arm is the binding constraint, and Fisher-exact confirms it — with `n_short`
held at 24 triples, taking `n_long` to 400 still reaches only 0.798. Widening
the long bands first would have bought nothing.

**The extension closed both seeded entries in `datasets/triggers/corpus-baseline.txt`,
and neither was closed by moving a threshold.** `paste_cues` is no longer inert
in every view; the four-feature `close`-view leak no longer holds with that
feature set. They are deleted rather than kept, which is the may-only-shrink
rule working in the direction it was written for.

**And it opened two, which is the exceptional case for that file.** The battery
gained a matched within-triple check — a positive against its own two negatives,
over the body they share, which is the only comparison a matched design actually
controls. `word_count` sits above both its negatives in 0.660 of comparisons,
3.24 null standard errors from chance, on both the `turn` and `ask` views. The
pooled AUC over the same corpus is 0.517 and 0.502.

**Read those two numbers together, because that is the finding.** A pooled AUC
ranks positives against negatives from *other* triples, where body variation
swamps the ask, so it is structurally blind to a rank held inside a triple. The
corpus was built as a matched design and evaluated as an unmatched one, and
every "the corpus is ruler-proof" claim on record rests on the wrong statistic.
Four separate pooled-cancellations were found by four separate people over one
day, each after the fact; the matched check found all of them in one run.

**What it does not license.** An arm sees one turn and never sees the other two
members of its triple, so it cannot use a within-triple rank directly. This is a
defect in the *construction*, not a demonstrated exploit, and per-band pooled AUC
remains the exploitability measure. Both are baselined and printed on every run
rather than treated as either fatal or fine.

**Not fixable in this change.** 23 long-band triples are mid-rebuild and
unmerged. An assignment rule pairing close rank with ask form was tried and
*measured to make it worse*: only 15 of 64 positives are `embedded` and can carry
shortest or middle rank, so 49 of 64 would be forced to positive-longest, which
projects ~0.766 against the observed 0.660. The close condition is a roughly
uniform rank distribution reached by assignment at authoring time, never by
editing negatives toward a target — four generations of leak on 2026-08-13 came
from per-item bounds pushed in one direction.

## 2026-08-13 — The XL band, and two rulers that cancelled

**Commits:** `74b7f5f`

Seven triples of 900–1,500 words completes the corpus at 120 items. `ledger` has
for the first time been shown a pile of context; version 2's longest positive
was one sentence describing one.

**The gates written for this corpus had never read it.** `check_trigger_sets`
globs `datasets/triggers/*.yaml` and the bands are one directory down, so 99
authored items sat outside the battery, the stump and the balance rules while
`de check` reported green. Third instance of a tested check with no caller, and
the first caught before anything was published from it. A draft-corpus step now
holds it to the live rules **without making it live** — the entry point may not
move before adjudication has run its 20% kill.

**A pooled AUC of 0.5 did not mean the bands were clean.** `word_count` read
0.511 across the set while L was at 0.769 and XL at 0.301 — a `ledger` positive
ends in four words and a `compute` negative in ninety, so the same habit pointed
opposite ways in the two bands and cancelled. Length inside a band is available
at inference, so it was a real shortcut. The depth-2 stump caught it at a lift
of 0.117; the per-feature battery could not. Mixing the ask lengths took it to
0.083 against a 0.100 cap.

Per-band separability is reported and not gated: 98 pairs in the XL band gives a
null SE around 0.137, so a [0.40, 0.60] gate would fire on a clean corpus about
half the time.

## 2026-08-13 — The L band, and a scale error in the gate rather than in the corpus

**Commits:** `bf88664`

Nine shared bodies, 27 turns. All eight single-feature shortcuts landed inside
[0.40, 0.60] on 33 triples. `first_person_rate` had read 0.680 after S and M —
ten S-band negatives sat at exactly zero against the positives' 0.10 — and was
fixed by asking the identical question in the first person. A shared body needs
no such repair, which is the argument for the construction.

The stump found a defect in the gate. `MAX_STUMP_ACCURACY = 0.70` was borrowed
from the AUC target, and accuracy does not transfer across base rates: version 2
was 77% negative so "never fire" scored 0.767 there, against 0.667 here. One
flat threshold asked v3 for 3.3 points of headroom and v2 for 13.3. It became a
**lift over the majority-class baseline** capped at 0.10.

On that gate the corpus **failed at 0.101 against a cap of 0.100** and the
commit says so rather than rounding it. `majority_baseline` became a function,
because an arm that never fires scores 0.667 and looks like caution.

## 2026-08-13 — The S and M bands, and a battery that checks more than length

**Commits:** `ee96088`

24 triples, 72 turns, two of four bands. Each triple is one positive and two
negatives written to the same length, so **the label cannot come from a word
count**. Band M is the band version 2 skipped entirely: a paragraph of situation
with the question inside it rather than as the whole turn.

The shortcut battery earned its keep on the first measurement — `word_count`
fell to 0.531 from version 2's 0.850, and `first_person_rate` came out at 0.680
and failed the gate. A battery that only checked length would have passed the
corpus and missed the next ruler.

## 2026-08-13 — The corpus is 89% solved by counting words

**Commits:** `fffa4a2`

The maintainer observed that real users write paragraphs. Checking it found a
confound rather than only a gap: positives run at a median of 18 words against
the negatives' 8, no turn exceeds 25 words, and **"fire if the turn is at least
18 words" scores 0.890 with no model involved** against a best measured arm of
0.956. Separability is AUC 0.850 where the long-context plan had already set a
0.70 gate — a gate never pointed at this set.

This does not invalidate the arm comparisons; every arm saw the same 73 turns.
It caps what any of them could have shown, and it gives Track M's headline a
second reading: five manipulations moved firing accuracy nowhere, and there were
about six points of room above a word count.

**Correction, 2026-08-13, appended rather than rewritten.** The two numbers in
the paragraphs above are at different label versions and comparing them is the
move `trigger_arms.label_versions_comparable` refuses. 0.890 is the ruler on the
**version 2** key; 0.956 is the `full` arm on the **version 1** key, where the
same ruler scores 0.877. Within a version the headroom is about **nine** points
either way: v2 ruler 0.890 against 0.9795 (`stakes-shown`) to 0.9863
(`confidence`), v1 ruler 0.877 against 0.967 (`no-opener`) to 0.973
(`confidence`). 0.956 was also never the best arm at either
version — `no-opener` and `confidence` both beat it at v1 and no document had computed it, because L5
published precision, recall, FPR and routing and no accuracy column. The
six-point figure is withdrawn; the decision it supported, that the corpus needs
rebuilding, is unaffected and if anything better supported.

## 2026-08-13 — Version the answer key

**Commits:** `903169c`

Re-scoring the arms on disk against the new labels raised recall 3 to 5 points
on almost all of them with no call re-made. It has every property the three
earlier defects had — valid checkpoints, every instrument check passing, 100%
parse rate, the number moving the way an author would like — and one they did
not: **it is not a bug.** The new labels are better. The improvement is real as
a label correction and would be a fabrication as a model result.

So the set carries `version: 2`, every record carries `set_version`, and
`trigger_arms` refuses a comparison spanning revisions.

## 2026-08-13 — Four label decisions, and a turn may have two acceptable routes

**Commits:** `d43c490`

`x-n21` *"the disk is at 99%, do we need to act"* moves to the negatives: the
question asked has an obvious answer, so there is no trade-off to weigh, and the
nuance is in how to act — which the turn does not ask.

`x-n22` *"the build is green, can I deploy"* stays a positive against four
versions that all declined to fire. A green build answers whether the code
compiles, not whether to ship; dependencies, prerequisites, who needs telling
and the maintenance window are all still open. That reasoning is also why it
gains `cascade` as a second route.

The line between them is written into both `why` fields: `x-n21` looks settled
and is, `x-n22` looks settled and is not.

## 2026-08-12 — The two cases that disagreed with me stay in the set

**Commits:** `0438306`

Removing `x-n21` and `x-n22` as "contested" because they failed to fire would
have been **selection on the outcome**. All five `x-n*` cases have the same
provenance — one sitting, one author, promotion argument and label together — so
pulling only the two that disagreed with that judgement would have deleted the
evidence against it and raised recall by doing so.

They are scored like everything else. The `x-` prefix is the reader's escape
hatch, and any recall figure leaning on them should be given both ways.

## 2026-08-12 — Fired but routed nowhere is an abort condition

**Commits:** `94da7cf`

Both runs that day produced cases where the model fired and returned
`procedure: null` — the skill's own *Abort if* clause arriving one step late,
after it had committed to running. The router table said what to do when several
procedures apply and nothing about when none does, leaving "pile is usually the
problem → ledger.md" as the only fallback. That is the wrong one: it turns a
lookup into a decision procedure instead of sending it back to *Abort if*.

Skill version 0.2.0 → 0.2.1.

## 2026-08-12 — Repairing p07 and p08, and what the repair showed

**Commits:** `88995e5`

Both cases were rewritten to carry no time word: temporal language had been put
into the two cases meant to test consequence reasoning, so the cascade/timing
confusion was partly an authoring defect.

The repair worked on its own terms — `p08` now routes correctly — and **routing
accuracy was identical to three decimal places with a different set of errors**.
That is the finding, not the repair.

## 2026-08-12 — A trigger set that described a skill which had stopped existing

**Commits:** `8541d46`

`datasets/triggers/evidence-ledger.yaml` named a skill retired the previous day
when the four procedures were consolidated behind one router, and the skill that
actually ships had no trigger set at all. Neither surfaced for a day, because
`load_trigger_set` was written, tested to 100%, and **called by nothing**.

`de check` gained the trigger-sets step. The same shape recurred later with
`prereg.py`, which is why `de check` now also refuses an unreachable integrity
lock.

## 2026-08-11 — One entry, four procedures behind it

**Commits:** `ca6b669`

Four separate decision skills would carry four descriptions that all read as
"help me decide", and overlapping descriptions are the documented mechanism by
which agents pick the wrong skill. Progressive disclosure reconciles the two
findings that look opposed: one description resident in context, one procedure
file read when it fires.

**Superseded in part by M4** (2026-08-12), which measured four entries against
one and found shadowing did not appear at four. The structure stands; the
citation that justified it no longer reaches down to this scale. See
`notebook/2026-08-12-m4-shadowing-did-not-appear-at-four.md`.

## 2026-08-11 — Three skills you can install today, and the review that was skipped

**Commits:** `9a16b18`

Re-reading the founding prompt rather than a twice-compacted summary of it
surfaced two things asked for on day one and absent from everything built. The
first: research on decision-making itself, before picking a direction. The
programme had eleven tracks on LLM failure modes and none on decision
frameworks — the "skills based on really nothing" the brief warned against.
That became Track K, and it runs first.

## 2026-08-11 — A placebo must match the skill's output template

**Commits:** `220cfa2`

Includes a correction: the plan claimed `evidence-ledger`'s placebo failed the
repo's own guard at a word ratio of 0.71. It did not — `check_placebo_match`
compares against the skill's *body*, and 421w vs 445w is 1.057, inside
tolerance. The 0.71 counted YAML frontmatter as skill prose, which the model
never sees.

What survived was sharper and invisible to both existing checks: matching length
is not matching structure, and a placebo that omits the output template lets the
treatment arm win on format alone.

## 2026-08-10 — Positive/negative trigger sets, and no F-score

**Commits:** `488331e`

Trigger quality is measured and reported separately from task accuracy, never
blended. **There is deliberately no F-score**: a single number would let a
description trade away precision, which is the property that degrades daily use.
A suite that lifts accuracy 10pp while firing on 60% of ordinary turns is a net
loss to whoever installed it, and an accuracy-only evaluation reports it as a
win.

## 2026-08-10 — The runner, the first skill, and a real validator

**Commits:** `a602794`

The runner is checkpointed and resumable because rate limits rather than dollars
are the budget and a confirmation run may span days. Records append to JSONL and
a resumed run skips item/arm pairs already present, so a crash costs the current
call and nothing else. A truncated final line is ignored rather than fatal —
refusing to resume over a partial write would throw away a whole checkpoint to
avoid re-running one item.
