# 2026-08-18 — every human gate comes out of the plans

Maintainer instruction, plainly: *remove any human gate there are in the plan on
any doc.* Not a run. A change to what the plans are allowed to depend on, and a
record of what each removal cost, because a gate deleted with nothing behind it
is a step the plan silently loses.

## What a human gate turned out to be worth here

Every one of these had been sitting open, and the interesting part is not that
they were open — it is how long, and how invisibly:

| gate | written down | supplied |
|---|---|---|
| N4's ~20 hand-authored holdout turns | 2026-08-13 | never — rerouted 2026-08-18 |
| the 10% realism audit, trigger corpus | before the corpus reached 120 items | never; 138 items were added under it and the sheet was never regenerated |
| the 10% realism audit, math eval set | at datasheet time | never |
| five `open` label decisions in `STATUS.md` | 2026-08-13 and earlier | never |
| "vendor the spider databases?" — *needs explicit permission* | 2026-08-13 | never |

**Nought for five, and the audit sheet is the sharp case.** It was addressed to
"12 items (10% of 120)" at answer key v3 while the corpus stood at 258 items and
v4. A gate that waits does not merely fail to fire; it goes stale pointing at a
corpus that no longer exists, and everything downstream keeps citing it as the
mitigation.

## The two conditions a removal had to meet

Written into [`AUTONOMOUS_WORK_ORDER.md`](../docs/AUTONOMOUS_WORK_ORDER.md) as a
standing section, beside the quota removal it structurally resembles.

**Name what now does the job.** Labels go to N3's three-instance blind
adjudication, answer key versioned and movement reported. Data-source decisions
go to the outside-data rule — executing it *is* the approval, and not one of its
four checks is dropped. A parameter with no derivation goes to standing rule 1:
record the choice as a choice, in a dated entry.

**Name what is lost.** In almost every case it is the last reader outside the
model loop, and no procedure buys that back. What the replacements do buy is
*checkability*: three blind judges leave a ledger, a pre-registered rule predates
its data, a licence check leaves a digest. One person's answer left none of
those, which is the argument — not that a person would judge worse.

## The realism audit was mislabelled, which is a better reason than unavailability

The sheet carried both of these, fifteen lines apart. **Quoted from the
generator rather than from the artefact**, because `results/triggers/` is
gitignored and both files were deleted with the code that wrote them — a
quotation nobody can retrieve is not evidence. These are
`scripts/realism_probe.py` at `90f1653`, lines 945-946 and 959-960:

> **Track N5, answer key v3. This is the part with ground truth, and it needs a
> person.**

> **Standing caveat.** The only auditor available authored this corpus, so these
> answers are a self-assessment.

A self-assessment by the author is not ground truth at any sample size. So the
audit is retired for being the wrong instrument, not for being inconvenient —
and that distinction is the whole of the justification, because "we removed the
check we kept failing to perform" is the other thing this could have been.

**What replaces it was already argued for in this repository, by the module that
declined to build it.** `scripts/realism_probe.py`'s docstring says a forced
choice is the sharper instrument because it cancels the judge's base rate — the
one quantity a single-item verdict cannot recover — and said it was unavailable
because *"There is no human-written comparison set in this repository"*
(`90f1653`; that docstring is rewritten in this same change). N4 no longer waits
for a person to write one. So the forced choice becomes reachable,
and with it the known-good case standing rule 2 has demanded all along: **which
turn is human is a fact on the record, not a taste.**

Nothing has been fetched and no licence is cleared. The probe is available in
plan, not on disk, and every doc touched today says so in the future tense.

## What was deliberately not removed, and why

- **`SCORECARD.md`'s retirement rule.** A procedure disabled for 14 consecutive
  days is `WITHDRAWN`, clocked from a dated line. That reads like a human gate
  and is the opposite of one: it is the only channel in this repository through
  which daily use can come out *negative*, and nothing waits on it. Removing a
  falsifier because it mentions a person would be the inverse of the
  instruction.
- **The outside-data rule's four checks**, the pre-registration requirement, the
  answer-key versioning, the promotion gate. A gate on evidence is not a gate on
  a person. What changed is that executing the rule is now the approval, rather
  than a person approving after the rule passes.
- **`AGENTS.md`'s reports of maintainer decisions.** Those are history. History
  is the pre-registration evidence here and is not rewritten.

## One judgement call, flagged because it is the least clear-cut

The holdout seed was *"passphrase-derived, held outside the repository"* in three
docs, a paper stub and a golden-file comment. A passphrase only a person can
produce is a step that waits on a person, so it is now a seed file, uncommitted,
outside the repository.

**It is not a free swap, and the first draft of this entry said it was.** An
adversarial review caught it: a file on this machine is readable by any agent
with filesystem access, and a passphrase in someone's head is not — so the
holdout got easier to *reconstruct*, not merely easier to regenerate. It stands,
because the seed has to reach the generator through an agent either way and
because `LIMITATIONS.md` already said secrecy was not the contamination
mechanism. But the exposure is now written into all three docs rather than
implied. Somebody may still reasonably think this one was not a gate at all.

## Corrected before this landed, by a review briefed to break it

Recorded because the confident wrong number is this repository's recurring
failure and it does not stop being one when it is caught:

- **"141 items were added under the audit sheet" was wrong; it is 138.** The
  same sentence carried 120 and 258, which disprove it. 141 was correct against
  a 261-item corpus and survived the retirement of `l15` without being
  recomputed — a stale derived number of exactly the kind the answer-key
  versioning rule exists for.
- **`STATUS.md` sent the rerouted label rows "against the 0.20 kill", and that
  is the wrong denominator.** The kill was pre-registered over a whole corpus
  adjudicated blind. These rows are selected *because* they already disagree, so
  movement over a hand-picked pair is not the quantity it calibrates — the same
  shape as this morning's re-adjudication, which reported `CORPUS RETIRED` from
  a subset chosen to be the items that had moved. The row now reports votes per
  item, and the kill stays with cumulative corpus-wide movement.
- **One present tense for a mechanism that has never run** ("a forced choice
  replaces it"), now future.
- **Two quotations were left pointing at text this change itself rewrote or
  deleted**, so neither was retrievable. Both now name the commit.

## Registered, before the consequences are observable

- **The forced-choice probe will land above 0.5 when it eventually runs** — the
  corpus will be distinguishable from human text. It was written to a grid, with
  matched triples sharing byte-identical bodies, which no real inbox produces.
  If it lands *at* 0.5 I will suspect the estimator before I believe the corpus.
  That order is not caution for its own sake: the most recent instrument finding
  here, [the rewrite round](2026-08-18-the-rewrite-round-eleven-of-twelve-and-one-retirement.md),
  called itself the sixth of exactly this shape — a clean run, a full checkpoint,
  and a plausible number from an estimator that could not have returned anything
  else.
- **The failure mode to watch is not a wrong decision. It is a quiet one.** Six
  rows moved off the maintainer's list today. Each is now supposed to end in a
  dated entry or an adjudication ledger. If, when they are actually decided,
  fewer than six carry one, then this change traded a slow gate for an invisible
  one — which is strictly worse, because a row marked `open` at least announces
  itself.
- **Where I expect to be wrong:** I have assumed the five `open` label rows are
  the kind of question blind adjudication can answer. `x-n21` and `x-n22` fire
  0/5 with nothing in between, and a stable disagreement may be one three model
  instances reproduce rather than resolve. If adjudication comes back split or
  unanimously against the key on both, the reroute did not decide them — it
  moved them.
