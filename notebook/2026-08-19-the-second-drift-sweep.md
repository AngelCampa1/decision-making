# The second drift sweep

**2026-08-19.** The standing rule is that every third published run,
`README.md` and `docs/` get swept for drift and the sweep lands here, so the
next one can see when the last one ran and what it already checked. The first
sweep found four defects at once. This is the second.

It was triggered off-schedule, by the two changes that landed today: the router
grew from four procedures to six, and Track H's H1 authoring reached its second
pass. Both are the kind of change that leaves counts stale in files nobody
opened.

## What moved

Three defects, all in [`docs/README.md`](../docs/README.md), all the same shape
— a count stated in prose that was never recomputed against the thing under it.

| was | is | why |
|---|---|---|
| "Fifteen documents" | Sixteen | `TAILORING_CORPUS_SPEC.md` landed earlier today and was never counted |
| index table: 15 `docs/` rows | 16 | the same file was never added to the map |
| "fifteen tracks in eight parts" | sixteen | `RESEARCH_PROGRAMME.md` line 26 already said *Sixteen*; the index did not follow |

The third is the interesting one. The programme corrected its own count and the
document whose job is to describe the programme did not, so the two disagreed
about the thing one of them exists to summarise. Nothing checks that, and
nothing will: `de check` refuses a reference that does not resolve and declines
to judge whether the sentence around it is true.

**And the sweep reproduced the defect while fixing it.** The new index row was
written as "seven salience dimensions, fifteen disqualifiers." The spec has had
**eight** dimensions since dimension 8 was added a few hours earlier, in this
same session, by the person writing the row. Counted mechanically, it is 8 and
15. That is the fourth instance today of a number being written from memory when
the file was one command away, and it is worth recording precisely because the
author had every reason to know better.

## What did not move, and was checked rather than assumed

Recorded so the next sweep can skip it or re-test it deliberately:

- **Root [`README.md`](../README.md)** — says the skill routes to "one of six
  procedures" and names all six; "Thirteen runs published… one void" checks out
  against [`docs/RUN_INDEX.md`](../docs/RUN_INDEX.md), which is generated and
  cannot itself drift.
- **[`docs/DECISION_FRAMEWORKS.md`](../docs/DECISION_FRAMEWORKS.md)** — its
  "four shipped procedures" audit self-scopes to when it was written and says in
  the same breath that `council` and `hinge` are unaudited. Correct as written;
  not stale.
- **[`docs/METHODS.md`](../docs/METHODS.md)** — already states that no number on
  record measures the six-procedure description.
- **[`docs/STATUS.md`](../docs/STATUS.md)**'s venues table — five closed and one
  working, matching the programme's "four of the five… closed on accuracy".
- **`causal_rule_overlap`** — the present-indicative trap, and the one place a
  fresh claim could have been made about a mechanism that has never run. Both
  the spec and the programme say it is *not* in `tailoring.FEATURES` and that
  the battery does not compute it. Correctly negated in both.

## One left alone on purpose

[`docs/TAILORING_CORPUS_SPEC.md`](../docs/TAILORING_CORPUS_SPEC.md) opens with
"Three triplets… authored. The remaining seventeen follow this document." Pass
two authored five more under that same document and three were cut, so the
sentence is arguably stale. It is left because it describes the document's
*charge* rather than a live count, and because the seventeen it names is the
figure the H1 row costs — which is itself now under question on yield grounds.
Rewriting it before that question is answered would replace one stale number
with another.

## What this sweep did not do

It read the living documents for counts and for claims that have stopped being
true. It did **not** re-read them as prose, and it did not check whether the
`humanizer` pass has ever been run over `CONTRIBUTING.md`, `SCORECARD.md` or the
documents under `docs/` — a standing obligation that nothing enforces and that,
as of the rule being written, had never been done for any of them. That is a
larger job than a count sweep and is not what this entry is.
