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
