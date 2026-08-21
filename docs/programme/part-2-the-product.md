# Part 2: the product

**Audience:** the evaluating reader, and in particular anyone picking up a track.

Tracks S and L. Shipping the skills people install, and which formulation of a
skill is best. This lane ships continuously and is never gated on the research.

Part 2 of eight. The tracks table, the venue map, the sequencing and the
claim ladder are in [`RESEARCH_PROGRAMME.md`](../RESEARCH_PROGRAMME.md).
Headings below start at `###`, carried over from the split so that a track's
anchor is the one it had in the monolith.

---

Ships continuously and is never gated on the research. This is half the point of
the repository.

### Track S, ship the skills

The question: what can the maintainer, and anyone else, install and use today?

Why it matters. This project is dual-purpose: skills someone actually uses,
*and* a paper. The programme as first written was a research programme with a
skill attached. No skill improved until Track C/D/E, months out, and it produced
exactly one new skill almost by accident. That ratio is wrong and it is the
mistake this track corrects.

The decoupling that makes it possible. `SCORECARD.md` already says a verdict
governs the *public claim*, not whether a skill is usable. `UNTESTED` blocks
entry to `plugin/skills/`; it does not block `cp -r skills/* .claude/skills/`.
Shipping honestly-labelled unproven skills and shipping unproven skills *as
proven* are different acts, and only the second is the thing the evidence rule
exists to prevent.

Runs from day one, in parallel, never downstream. Every research finding is
harvested into a skill revision the week it arrives.

Shipped state as of 2026-08-11: one skill, `decision-making` v0.2.0,
`verdict: UNTESTED`, with four procedures behind a router. Not four skills:
they were consolidated the same day they were written (see Track M).

Superseded 2026-08-19: v0.3.0, six procedures, with `council` and `hinge` added
by Tracks S5 and S6. The paragraph above is left as the 2026-08-11 record it
says it is.

| # | Procedure / work | Status |
|---|---|---|
| S1 | `ledger.md`: a pile arrived and it is unclear what the answer turns on | in the bundle |
| S2 | `fit.md`: is this generic advice right for *this* person | in the bundle |
| S3 | `cascade.md`: what it sets in motion, and which option it spends | in the bundle |
| S4 | `timing.md`: the undo price, the real deadline, what waiting buys | in the bundle |
| S5 | a council / adversarial-review procedure: argue the positions before deciding | written 2026-08-19. `council.md`, for decisions where two or three positions are each defensible and whichever was argued first has the advantage. Ships `experimental` / `UNTESTED`; nothing has measured it |
| S6 | a clarify-or-decide procedure: ask for more, or decide under incomplete information | written 2026-08-19. `hinge.md`, whose test is whether the missing fact would change the answer rather than whether more information would help. Ships `experimental` / `UNTESTED`; nothing has measured it |
| S7 | Re-derive each of the above from Track K's catalogue, or mark it invented | done 2026-08-12. `cascade`, `timing` and `fit` trace to named frameworks; `ledger` is invented outright. None of the four traces to a framework with strong prescriptive evidence. See [`DECISION_FRAMEWORKS.md`](../DECISION_FRAMEWORKS.md) |
| S8 | A retirement rule. "Daily use is evidence" currently has no failure condition, no threshold at which use retires a procedure. Evidence that cannot come out negative is not evidence. | done 2026-08-12. 14 consecutive days disabled → `WITHDRAWN`, clocked from a dated `notebook/` line. Blocks the plugin through the existing promotion gate, not a second mechanism, so it operates rather than being written down |
| S9 | `ledger.md` is first in line for replacement. Three independent lines now name it: no framework trace (S7/K6), the top-ranked outside candidate is elicited confidence (K6), and it is worst-routed in all six description arms run to date (N6, N7). Only the first two bear on the procedure's *content*; the third is a router finding and does not by itself add weight to a content-replacement case. See below | router half done 2026-08-19, content question still open. The confusion pair was identified from all six arms' records and confirmed independently: `ledger` items land on `cascade` 77 times against `timing` 32 and `fit` 16, while only 5 records travel the other way, so the row had to pull its own items back, not repel tourists. The row now names the choice itself against what acting on it would set off. All six routing figures on record were measured against the old row, so nothing may be claimed about the new one until a fresh run scores it. `ledger.md`'s content is untouched |

The maintainer's daily use is evidence. Not publishable as a headline, and
the fastest signal available: a skill that fires when it should not, or produces
a worse answer than working directly, is worth knowing about in a day rather
than in a quarter. The copy-paste block in `AGENTS.md` closes on an explicit
invitation to report exactly that.

Honest caveat carried on all four: `consequence-cascade` has the weakest
prior of the set. The casefile probe found the model already doing order-1
through order-3 consequence reasoning unprompted: 27 trap opportunities, zero
taken, and it computed a leverage ratio nobody asked for. That was professional
casefiles with an option menu, not personal decisions, so the skill is still
worth having and worth testing. But if any of the four comes back `NULL`, this
is the one to bet on.

#### S9: three lines now name `ledger`, and only two of them bear on content (2026-08-19)

Line 1, framework provenance (Track S7 / K6, done 2026-08-12). `cascade`,
`timing` and `fit` each trace to a named decision framework; `ledger` traces to
nothing in the catalogue.
[`docs/DECISION_FRAMEWORKS.md`](../DECISION_FRAMEWORKS.md)'s audit table reads:
*"Invented. Diagnosticity and relevance ranking are real ideas, but no named
decision framework prescribes this procedure."* The sentence right after adds
the qualifier that matters: *"`ledger.md` is not thereby wrong. It is the
procedure with the least external support and the most exposure, and it should
be first in line behind any candidate that has a literature."*

Line 2, a ranked outside candidate (Track K6, done 2026-08-12).
`DECISION_FRAMEWORKS.md` ranks elicited confidence first among skill
candidates: *"This is the only candidate whose parent intervention has
medium-to-large controlled effects in humans, it needs no new corpus, and it
turns an unused, fully tested module into an outcome. It also fixes the
measurement problem the pre-mortem finding raises: a number can be scored for
accuracy, whereas a list of considerations can only be counted."* This ranks
what to build next; it is not a measurement of `ledger` in use.

Line 3, measured routing behaviour (Track N6 and N7, 2026-08-18/19, new).
`ledger` is the worst-routed of the four procedures, over the same 19
first-route-labelled positives, `rule="first"` (equality against
`routes[0]`), in every one of the six description arms run to date, not
only the three N6 registered:

| arm | run | cascade (n=16/32) | fit (n=15/30) | ledger (n=19/38) | timing (n=15/30) |
|---|---|---|---|---|---|
| `stakes-shown` | N6 | 1.000 | 0.733 | 0.579 | 0.833 |
| `full` | N6 | 0.875 | 0.833 | 0.474 | 0.767 |
| `stakes-named` | N7 | 0.906 | 0.700 | 0.474 | 0.867 |
| `no-exclusions` | N7 | 0.844 | 0.900 | 0.526 | 0.833 |
| `no-opener` | N7 | 0.906 | 0.800 | 0.395 | 0.767 |
| `opener-only` | N6 | 0.594 | 0.533 | 0.105 | 0.900 |

n counts are (distinct labelled items / parsed records across 2 repeats),
identical across all six arms, the same 65 labelled positives throughout.
N6's figures are quoted from its own README (0.474, 0.579, 0.105, its
registered Q3, "met"). N7's figures (0.526, 0.395, 0.474) were computed for
this update with `decision_evals.trigger_arms.routing_by_procedure(records,
rule="first")` against the committed checkpoints in
[`results/decision-making/2026-08-19-d52236a-n7-remaining-arms/`](../../results/decision-making/2026-08-19-d52236a-n7-remaining-arms/)
(`verdicts-no-exclusions.jsonl`, `verdicts-no-opener.jsonl`,
`verdicts-stakes-named.jsonl`). `results/triggers/` was not touched, per the
run that may be writing there. The method was checked against N6's own
checkpoints first and reproduced its published 0.474 / 0.579 / 0.105 exactly,
before being trusted on N7 data nobody had scored this way. N7 did not
pre-register a `ledger`-worst prediction of its own; this is a confirmatory
check this update requested, not a second pre-registration, and it is
reported here as descriptive for that reason.

The honest counter-argument, and it must not collapse into lines 1 to 2.
Lines 1 and 2 are about `ledger`'s *content*: what the procedure says to do,
and how that compares against the literature. Line 3 is about the *router*:
whether the model, given the current `SKILL.md` table and description, sends a
turn to the file matching its label. Those are different failures with
different remedies, and this repository has already mistaken one for the
other once. The M-track "router-table defect" diagnosis (Track M, 2026-08-12)
found `p06` and `p07` routed wrong not because their target procedures were
badly designed but because two table rows used colliding words:
`cascade` claimed "the order," `timing` claimed "when," and in ordinary use
those are one idea. Both were fixed, or queued for fixing (Track L6), by
editing the *table*, not the procedure.

`ledger` being worst-routed is the same shape of finding. A procedure the
router sends work to incorrectly may be a good procedure with a bad
description, and the corpus itself supplies a candidate explanation available
here too: `ledger`'s condition is "a pile of context ending in a question
about what to do", the broadest and least precisely stated of the four, and
it is labelled on the largest stratum, 19 of 65 positives against 15 to 16 for
the other three. A routing failure concentrated on the largest, vaguest-stated
bucket is at least as consistent with "the row is hard to write precisely" as
with "the underlying idea is worse." Nothing run so far distinguishes these
two readings. Line 3 does not, on its own, add weight to the case for
replacing `ledger`'s content. It adds weight to a *different* case, that
`ledger`'s row needs the same tightening `timing` and `cascade` already have
queued.

What each line licenses. Lines 1 and 2 license naming `ledger` first in
the replacement queue and naming elicited confidence as the specific
candidate. Line 3 licenses a routing fix (rewrite `ledger`'s condition to
be as narrow as `fit`'s or `timing`'s, the L6 edit class already queued) and,
at most, a lowered prior that a procedure this hard to route accurately may
also be one worth cutting. It does not license concluding `ledger`'s content
is worse than the other three's: routing accuracy has never been shown to
track content quality on this instrument.

What would settle it, and what it costs. Separating "bad description"
from "bad content" needs the same design M4/M5/M6 already used to separate
structure from content for firing: hold one fixed, vary the other. Rewrite
`ledger`'s router-table row and description to be as narrowly stated as
`fit`'s or `timing`'s, an L6-shaped edit with no new corpus, then re-run the
N6/N7 routing comparison. If `ledger` stops being worst, Line 3 was a
description artefact and Lines 1 to 2 stand alone as the content case. If
`ledger` is still worst-routed after a genuinely tightened description, that
is new evidence bearing on content, not just on the table. Cost: one rewrite,
free, plus a routing re-run at N6/N7's scale, 1,548 calls, already paid for
once and cheap to repeat on the checkpointed harness. Deciding what content
should replace `ledger`, if lines 1 to 2 carry the day regardless of line 3,
is separate work, and K6's Rank 1 (elicited confidence) is the standing
proposal for it.

A fourth thread, added 2026-08-18, complicates the elicited-confidence
replacement rather than confirming it, and it must not be smoothed over.
`paper/refs.bib`'s `sun2025overconfident` entry (arXiv:2505.02151, five LLMs,
algorithmically constructed reasoning problems with known ground truth) reads:
*"We find that all five LLMs we study are overconfident: they overestimate the
probability that their answer is correct between 20% and 60%. Humans have
accuracy similar to the more advanced LLMs, but far lower overconfidence."*
The entry's note adds two findings this repository carries nowhere else: LLM
overconfidence grows sharply relative to humans' as stated certainty falls,
and *showing a human an LLM's answer raises the human's accuracy while more
than doubling the human's own overconfidence.*

That cuts both ways, and both directions are reported. It
strengthens the case for building elicited confidence as a scored, internal
instrument. K6's own proposal is to score the number against
`stats/calibration.py`, and a model this badly calibrated is exactly the kind
of model whose calibration is worth measuring against a scorer that already
exists and is already wired to the `--confidence` arm, where it scores
*"P(this tool should be invoked)"*, a forecast with an outcome, rather than a
probability handed to a person. But it weakens the case
for elicited confidence as a user-facing replacement procedure shipped the
way `ledger.md` is. A probability handed to a person by a model that
overestimates its own correctness by 20 to 60 points is not obviously safer
than `ledger`'s qualitative pile-sorting, and the paper's own finding that
exposure to an LLM's stated answer more than doubles a human's overconfidence
suggests a naively shipped confidence number could leave the reader *more*
miscalibrated, not less. A model that is badly calibrated is a model whose
elicited confidence may not be worth eliciting on its own, only once
something scores and corrects it, which is what K6 named and nothing here has
built.

### Track L, skill variants: which formulation is best

> Every L result on disk was measured on a corpus a ruler solves at 0.890.
> L5 and L7 are internally valid, since all arms saw identical items, but the
> movable range above a word count was about nine points on the version 2 key,
> ruler 0.890 against 0.9795 to 0.9863 for the best arm, so an L null is
> ambiguous between "phrasing does not matter" and "there was nowhere to move".
> Track N is rebuilding the corpus; nothing here is retired and nothing here
> may be quoted without that sentence attached.

The question: for one target failure, which way of writing the skill works best?

Why it matters. The brief asked to test "different types of skills and
variations, finding the most optimal one." The current design compares one skill
against control, placebo and chain-of-thought. It never compares skill A
against skill B for the same job. Without that there is no basis for saying a
skill is good, only that it is better than nothing.

The axes are not equally worth running, and the priors say so. Attaching a
published prior to each one before spending anything is the difference between a
horse race and a fishing trip.

| # | Variant axis | Example | Published prior | Weight |
|---|---|---|---|---|
| L6 | Revision against failure traces: run it, read what went wrong, edit the skill, re-run | one skill, five rounds | +25.6pp (36.05 → 61.63), 3 benchmarks, 5 LLMs, [arXiv:2606.01139](https://arxiv.org/abs/2606.01139) | primary |
| L1 | Framework: genuinely different content for the same failure | a ledger vs a pre-mortem vs a reference class | curated vs no-skill +16.6pp (33.9→50.5); self-generated −1.3pp vs no-skill, [2602.12670](https://arxiv.org/abs/2602.12670). Two separate contrasts; an earlier draft merged them into one. | primary |
| L5 | Trigger breadth: the description, which controls whether it fires at all | narrow vs broad, scored on false-fire *and* miss rate | availability is the dominant term, +18 to 36pp, [2605.31408](https://arxiv.org/abs/2605.31408) | primary |
| L2 | Length | 150 vs 400 vs 1,200 words | ~+0.7pp, intervals crossing zero | confirm the null |
| L3 | Output shape | block template vs prose vs checklist | same | confirm the null |
| L4 | Framing | procedure vs diagnostic vs question list | same | confirm the null |

L2 to L4 are phrasing, and phrasing is the axis the evidence says does not move.
They are not dropped, since replicating a published null on our own stack is
cheap and is a legitimate result, but they are pre-registered *as* null
confirmations, run last, and they may not be reported as a search for an effect.
Spending a horse race on prose polish is how a project looks busy while
measuring nothing.

L6 now has its first real candidate, from measurement rather than invention,
2026-08-12. The five-repeat trigger run found two items the router gets
*stably* wrong, and reading them turned up a defect legible in `SKILL.md`'s own
table without any data: `cascade` claims "the order" and `timing` claims
"when", which in ordinary use are one idea. Only `timing`'s row carries the
clause that separates them, *the direction is settled*, and `cascade`'s does
not say that its own direction is still open.

The variant to test is therefore stated and not applied: give the `cascade`
row the direction-not-yet-settled clause. Editing it now would tune the skill
against the measurement that motivated it, which is the whole reason L6 has a
holdout. See
[`notebook/2026-08-12-cascade-and-timing-collide-in-the-table.md`](../../notebook/2026-08-12-cascade-and-timing-collide-in-the-table.md).

A second instance landed the same day, and two instances make it one
hypothesis. `p03` (*"six people replied in the group chat and they disagree.
What should I actually do?"*, labelled `ledger`) routes to `fit` three times in
five. `fit` needs a fact about the person that would overturn the generic answer
and `p03` states none, so unlike `p06` this is a genuine failure, and its cause
is that the pile is made of advice, and "advice" appears in exactly one row of
the table, `fit`'s. `ledger`'s row says "a pile of context" and never says what
a pile can be made of, though `SKILL.md`'s `description` field lists the kinds.

So both table defects are the same mechanism: a row matched on a word it
contains rather than on the condition it states. That is the L6 candidate:
one edit class, two instances, neither applied. See
[`notebook/2026-08-12-p03-and-the-only-row-that-says-advice.md`](../../notebook/2026-08-12-p03-and-the-only-row-that-says-advice.md).

One caution carried with it: `p06`, the other stably-wrong item, is at least
partly a trigger-set defect. `fit` and `cascade` both read correctly off the
table for that case, and the model picked `cascade`. Allowing multiple acceptable
routes is a set-wide decision over all fourteen routed cases, made by someone who
has not seen which two failed, and it must happen before any L6 round is scored
on routing.

And routing cannot be the outcome any of these are scored on, measured
2026-08-12, and it is an instrument falsifier. The
trigger set has 14 routed items. Pairwise across the five repeats, the
discordance floor from sampling noise alone is `p_discordant` = 0.157: about
2.2 items flip between two runs of the *identical* skill. `required_pairs` then
asks for 95 pairs to detect a 10pp routing effect, and refuses a 20pp one as
arithmetically impossible at that discordance.

The exact test is harsher than that approximation. One-sided McNemar needs 5
discordant pairs all one way; under the null the expected count is 2.2 and the
real size of the test is 0.0015 against a nominal 0.05. Ceiling check: a
*perfect* variant, one that routes all fourteen right and breaks nothing, clears
the bar in three of five draws, power ≈ 0.6 on the best intervention that could
exist.

So: score L5 on firing (73 items, precision 0.942 / recall 0.878 / FPR 0.018,
70 of 73 stable across five repeats, a real instrument, and trigger breadth is
about firing anyway), or grow the routed stratum to ~95 items and price that
before authoring item fifteen, or report routing descriptively with intervals
and no p-value. What may not happen is a Track L round scored on 14-item routing
and written up as a null: that null would be a property of the sample size and
would be indistinguishable from a finding about skills. Working:
[`notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md`](../../notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).

L6 is the one that changes what the skills are. SkillRevise describes
expert-authored skills as costly and misaligned with how models actually execute,
and one-shot LLM-generated skills as "syntactically correct but behaviorally
weak." Every skill in this repository is one-shot LLM-generated. The loop is:
run on held-out items → read every failure → make one execution-anchored edit →
re-run → keep it only if it verifies.

The overfitting guard is not optional here. Revising a skill against traces
from the items you then evaluate it on is fitting the test set, and it would
produce a large, real, meaningless number. Revision traces come from one item
pool and the verdict comes from another, drawn before revision starts and not
looked at until the end.

L1 draws its candidates from Track K6, not from invention. That is the whole
point of doing the frameworks review first.

Winner's curse is the standing threat, and `stats/` has nothing for it.
`stats/multiplicity.py` contains exactly one function, `benjamini_hochberg`. BH
controls the false discovery *rate* among rejections; it does nothing about the
magnitude bias of a selected maximum. There is no shrinkage, no selective or
conditional inference, and no holdout re-estimation helper anywhere in `stats/`.
An earlier draft cited the module here as though it addressed this, which
misrepresented readiness in the programme's most active track.

Holdout re-estimation is therefore the only control in this design, and the
number reported is the holdout estimate, not the discovery-set estimate.

Done when one target failure has ≥3 authored variants plus a revision loop, a
pre-registered comparison, and a winner replicated on a holdout it never saw.
