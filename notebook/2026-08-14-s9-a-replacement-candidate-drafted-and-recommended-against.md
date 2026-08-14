# S9: a replacement candidate for `ledger`, drafted, and recommended against on today's evidence

**2026-08-14.** Track S9. Draft only — nothing shipped, nothing in `skills/`
or `datasets/triggers/` touched. Full dossier at
[`docs/superpowers/drafts/s9-ledger-replacement/README.md`](../docs/superpowers/drafts/s9-ledger-replacement/README.md),
candidate procedure at
[`docs/superpowers/drafts/s9-ledger-replacement/widen.md`](../docs/superpowers/drafts/s9-ledger-replacement/widen.md).

## Prediction, written before opening `ledger.md` or drafting anything

Given the framing handed to this track — Track S7 found `ledger` invented,
Track K2 just promoted "generate options concurrently" to Rank 2 with real
human evidence — the naive expectation going in was that this would land as a
straightforward "yes, swap it" with a costed migration attached. Writing this
line first so the actual conclusion below is checkable against it rather than
looking inevitable in hindsight.

## What happened instead

Reading `ledger.md` and the corpus items that route to it first, before
drafting the candidate, changed the answer. `ledger` targets a glut of
disagreeing sources crowding out what is load-bearing. The evidence Track K2
found — Basu & Savani 2017, Dow et al. 2010, Hauschildt & Gemünden 1985 — is
about humans doing better when candidate *options* are generated or presented
concurrently rather than sequentially. Those are different failures. Three of
the nineteen `ledger`-routed positives in the draft v3 corpus (`l01p`,
`xl08p`, `xl14p`) already contain two or more fully specified options in the
turn itself; more options would not help there, correctly weighting the
pasted facts would.

**Recounted directly rather than trusted from the brief.** The task handed me
"10 ledger-labelled positives at 40 triples"; the live count, `grep`'d
against all four band files (`s.yaml`, `m.yaml`, `l.yaml`, `xl.yaml`), is 19
of 87 triples (57 items: 19 positives, 38 paired hard negatives). The live
governed corpus (`datasets/triggers/decision-making.yaml`, version 2) has 3
ledger positives out of 73 items — that one I did not need to recount against
a stale figure, but confirmed the same way.

**K4's own table, closed today by a different session, already says the
LLM-side half of this candidate's case is `assumed` rather than
`documented`** — no study tests whether a model's own unaided reasoning
defaults to a narrow, single-option answer. I looked for anything since that
would move it and found nothing; `widen.md`'s opening paragraph is written as
a hypothesis and labelled as one rather than smuggled in as a finding.

Two independent reasons, not one, so the recommendation does not rest on a
single failed check: the target failure is unmeasured in LLMs, and separately,
even granting it, it is not the failure `ledger` and its corpus were built to
catch.

## Recommendation

**Not on this evidence.** Drafted `widen.md` anyway, because a well-reasoned
"no" is worth less without the artifact it says no to — a reviewer can now
look at the actual candidate rather than a description of one. If this is
revisited, the dossier names two things that would change the answer: an
LLM-specific study of option-generation narrowness (parallel to Vu et al.,
arXiv:2412.06593, on anchoring), and — separately — a corpus authored for
option-scarcity rather than source-glut, since the existing 57-item v3 block
cannot be repurposed for a construct it was never testing.

## Migration cost, in case this is revisited later

Costed in full in the dossier's section 5. Short version: swapping `ledger`
for anything bumps the trigger-corpus answer-key version
(`trigger_arms.label_versions_comparable` then applies to every M4/M5/L5
number on record), orphans the 57-item v3 block built around the pile-of-
sources construct, and requires either relabelling or dropping the 3 live-
corpus `ledger` positives. Nothing in `SCORECARD.md` breaks today because
that table is still empty — no skill has an outcome-quality measurement yet,
only firing/routing numbers, and those are what would need re-running.

## What I did not do

Did not touch `skills/decision-making/ledger.md`, `SKILL.md`'s router table,
or any file under `datasets/triggers/`. Did not add a `docs/DECISIONS.md`
entry, because no governed path changed. Did not add new `paper/refs.bib`
entries — reused `basusavani2017`, `dow2010parallel`,
`hauschildtgemunden1985`, all already present with verbatim `quote` fields
from K2's fourth pass, and cited none of them beside a number I had not
already seen quoted in `docs/DECISION_FRAMEWORKS.md`.
