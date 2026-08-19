# Decision frameworks: the review this project skipped

Track K1 to K4, and K6. Status: K2 is closed, after four passes, two on
2026-08-12, a third on 2026-08-13, a fourth on 2026-08-14. Every number below
was checked against a source on the date of its pass, and every framework
without a number is marked with what was *not* found rather than left blank.

---

## Why this exists, and why it is late

The founding brief asked for research on how to make good decisions *before* a
direction was chosen. That did not happen. Four decision procedures were written
in this repository by a model reasoning from first principles, and only then did
anyone go looking for whether the field already had an answer.

That is the exact failure the brief warned about, "skills based on really
nothing", and SkillsBench puts a number on it: curated skills gained +16.6pp
while self-generated ones came in at roughly zero or negative
([arXiv:2602.12670](https://arxiv.org/abs/2602.12670)).

So this document does two jobs. It catalogues what the decision literature
actually supports, and it audits the four procedures shipped at the time
against that catalogue. The audit's finding is at the bottom and it is mixed.

Two more procedures shipped on 2026-08-19, `council.md` and `hinge.md`, and this
audit does not cover them. It ran against the four that existed when it was
written and has not been rerun. A future pass should either trace each new
procedure to a named mechanism in the catalogue below or mark it invented,
rather than inheriting a verdict from an audit that never saw it.

## The rule this document is written under

No claim carries a number unless the number was read off a source on
2026-08-12. Where a framework is popular and the evidence was not found, the row
says *none located*, which is a statement about the search, not about the world,
and is deliberately weaker than *none exists*.

This rule is not decoration. Three misattributed numbers were written into this
repository in a single morning on 2026-08-11, all citing real papers that said
something adjacent. `de check`'s citation gate binds arXiv identifiers to
verbatim quotes, but almost nothing in the decision literature is on arXiv, so
the gate cannot see this file's central claims. The discipline has to be manual
here, and saying so is part of the record.

One error was caught by this rule while writing: Morewedge et al. (2015) is in
*Policy Insights from the Behavioral and Brain Sciences*, not PNAS. From memory
it would have gone in as PNAS.

---

## K1 + K2: the catalogue, graded by evidence

Two columns matter and they disagree constantly. Popularity is how often a
framework appears in business writing. Prescriptive evidence is whether anyone
has shown it improves decisions in a controlled setting. The gap between them is
the single most useful thing in this document.

| Framework | What it claims | Prescriptive evidence | Grade |
|---|---|---|---|
| Calibration / probability training | Short training improves forecast accuracy | GJP: ~6 to 11% Brier improvement over control, training under one hour. Challenged in 2025, see below | **contested** |
| Debiasing training (game/video) | One session reduces named biases, durably | Morewedge et al. 2015: medium-to-large effects, Cohen's *d* > 1, holding at two months; game beat video | **supported** |
| Consider-the-opposite | Explicitly generating opposing evidence reduces assimilation bias | Lord, Lepper & Preston 1984: beat "be fair and unbiased" instructions in two experiments. Later replication attempts moved in the predicted direction without reaching significance | **partial** |
| Reference-class forecasting | Take the outside view from a class of similar past cases | Adopted by the American Planning Association; case studies report improved accuracy. A 2025 review is titled *promises, problems, and a research agenda* and reports that little empirical evidence exists on RCF's accuracy versus other methods | **weak** |
| Pre-mortem | Imagine the failure has happened, then explain it | The famous "30%" is Mitchell, Russo & Pennington 1989 and it measures the number of reasons generated, not their quality or any decision outcome. The academic literature on the pre-mortem itself is thin | **misreported** |
| Kepner-Tregoe Rational Process | Situation appraisal → problem analysis → decision analysis → potential problem analysis | Widely deployed corporately (NASA, GM are the usual citations). No independent controlled evaluation of the named, integrated process was located, confirmed on a fourth pass, 2026-08-14, searching both the brand name and the generalised construct. See the K2 fourth-pass note below: the process is not atomic, and its parts inherit grades already given elsewhere in this table | *none located* |
| WRAP (Heath & Heath), the four steps as an integrated whole | Widen options, reality-test, attain distance, prepare to be wrong | No independent controlled evaluation of the four steps together was located, after a fourth pass | *none located* |
| WRAP: "Widen your options," in isolation | Generate or present more than one option before choosing | Located on the fourth pass, 2026-08-14. Basu & Savani 2017: 7 experiments, ≈2,892 participants, and presenting options simultaneously rather than sequentially raised optimal (dominating-option) choice by 7 to 16pp, every comparison p ≤ .02. Dow et al. 2010: parallel vs. serial prototyping raised both real click-through (445.0 vs 397.9 per million impressions, p<.05) and expert ratings (p<.05), n=33. Hauschildt & Gemünden 1985 (the "University of Kiel" study *Decisive*'s own endnotes cite for this chapter): correlational field study of 83 real executive-board decisions, and "alternative designing has a strong positive impact on decision quality" | **supported, component only** |
| OODA | Observe, orient, decide, act, faster than the adversary | Doctrinal and historical; no controlled evaluation of the loop as advice was located, after a fourth pass. One academic (non-consultancy) critique was found and read first-hand: Bryant 2006, arguing the loop is cognitively outdated, but it is theoretical, not a trial | *none located* |
| Decision analysis / MAUT | Decompose into attributes, weight, and score | Strong normative case. Evidence that decomposition improves *outcomes* rather than consistency is thin | **normative, not prescriptive** |
| Satisficing vs maximising | Stop at good-enough rather than search for best | Schwartz et al.'s work is correlational and its outcome is wellbeing and regret, not decision quality | **misfit for our purpose** |
| Option value / reversibility | Spend effort in proportion to how hard a choice is to undo | Grounded in real-options theory; the popular "one-way and two-way doors" form has no controlled evaluation located | **theory-backed, untested as advice** |
| Patient decision aids | A structured tool that states the options, their outcomes, and elicits what the person values, before the choice | Stacey et al. 2024, Cochrane: 209 RCTs, 107,698 participants. Knowledge MD +11.90/100 (CI 10.60 to 13.19; 107 trials), accurate risk perception RR 1.94 (CI 1.61 to 2.34; 25 trials), decisional conflict (uninformed) MD −10.02 (CI −12.31 to −7.74; 58 trials), all high-certainty. Informed values-congruent choice RR 1.75 (CI 1.44 to 2.13; 21 trials), moderate-certainty | **strongly supported, in a different domain** |

### The five findings that change what this project should build

Finding 1. The pre-mortem's headline number does not say what everyone says it says.
Mitchell, Russo & Pennington found that imagining an event has already occurred
"increases the number of reasons generated for the potential future outcome by
approximately 30%". In the reviewer's words, they "did not assess the quality of
the reasons." Klein's later framing of the same result as improving the ability
to *correctly identify* reasons is a stronger claim than the study supports.

This matters here more than anywhere else in the table. A procedure that makes a
model produce more considerations is not thereby a procedure that makes it
decide better, and *more considerations* is exactly what a structured skill most
easily produces and what a careless metric most easily rewards. This repository
has already been bitten by the same conflation from the other side: a hedged,
branch-covering answer was praised in prose on probe-07 and would have been
scored *worse* by the metric proposed alongside it.

Finding 2. The best-evidenced framework in the table is under active challenge. Mellers
et al. (2014) is the Good Judgment Project result everyone cites for calibration
training. Hauenstein et al. (2025, *Psychological Science*) re-analysed it under
item response theory and concluded that "the conclusions provided in Mellers et
al. (2014) are not straightforward and raise the possibility that both teaming
and training did not improve forecasting ability." The superforecaster findings
partially survive. The *training* effect, the part that would license a skill,
is the part in question.

The honest reading is that calibration training remains the strongest candidate
in the table and that its strength is one contested re-analysis away from the
rest of the field.

Finding 3. Four of eleven frameworks have no controlled evaluation this search could
find. They are, without exception, the four most likely to be found in a
corporate deck. Kepner-Tregoe, WRAP, and OODA are the frameworks a model asked
to "use a decision framework" would most readily reach for, and they are the
ones with the least behind them. Revised by the fourth pass, 2026-08-14: see
finding 5 below, where this is still true of the three frameworks as named,
integrated processes, but is no longer true of every piece of them. One quarter
of WRAP has real evidence once it is searched for as a construct rather than a
brand name.

Finding 4. Added 2026-08-12: the strongest evidence in the whole table is in a
literature nobody in this field cites, and it is not a framework. Patient
decision aids are the one form of structured decision support that has been
tested at scale: 209 randomised trials, 107,698 participants, meta-analysed in a
2024 Cochrane review, with three high-certainty effects and one
moderate-certainty one. Nothing else in the table is within two orders of
magnitude of that evidence base.

The transfer is not automatic and must not be written as if it were. These are
health treatment and screening decisions, delivered to patients, usually around
a clinical consultation, by a static tool rather than a conversational model.
None of that is a life-or-work decision handled by an LLM. The grade in the
table therefore says *strongly supported, **in a different domain***, and that
qualifier is load-bearing.

Finding 5. Added 2026-08-14 (K2's fourth pass): searching for the construct behind a
brand name, not the brand name, found real evidence for one quarter of WRAP. The
second pass already established this trick for patient decision aids, where
"structured decision support" returned 209 trials and "WRAP" returned nothing.
The fourth pass applied it to WRAP's own four letters one at a time and it
worked on the first one: "widen your options" is not just a slogan, it is a
testable claim (does considering more than one option, or considering them at
the same time rather than one after another, produce a better choice), and that
claim has been tested. Basu & Savani (2017) ran seven lab experiments (≈2,892
participants total) showing simultaneous option presentation raises the rate of
choosing the objectively dominating option by 7 to 16 percentage points over
sequential presentation, every comparison significant (p ≤ .02). Dow et al.
(2010) ran a between-subjects experiment (n=33) showing designers who worked on
multiple prototypes in parallel produced ads with significantly higher real
click-through rates and expert ratings than designers who iterated on one
prototype at a time. And the "University of Kiel" study *Decisive* itself cites
for this chapter turned out to be findable and readable: Hauschildt & Gemünden
(1985), an archival study of 83 real executive-board decisions at one German
firm, found that "alternative designing has a strong positive impact on decision
quality", correlational rather than a trial, but pointed at exactly this
question rather than at wellbeing or satisfaction.

None of this rescues WRAP as an integrated four-step procedure. No trial of the
whole four-step process was found, and none of these three sources tests
reality-testing, attaining distance, or preparing to be wrong. But it means the
"no located evidence" verdict this document gave WRAP on 2026-08-12 was an
artefact of searching for the framework's name rather than its mechanism,
exactly as the second pass already found once for patient decision aids. The
other three letters of WRAP were searched the same way on this pass and turned
up nothing: "reality-test your assumptions" and "attain distance before
deciding" did not resolve to a tested construct the way "widen your options"
resolved to "simultaneous vs. sequential option presentation." That asymmetry is
itself worth recording. One quarter of a popular framework has real teeth, and
there was no way to know which quarter without doing the work letter by letter.

Kepner-Tregoe does not have an equivalent win, but the same decomposition
exercise clarifies what its "none located" grade actually means. KT's four steps
are not four independent unstudied ideas. "Decision analysis" (its own name for
weighting and scoring options against criteria) is the same construct already
graded elsewhere in this table as Decision analysis / MAUT ("normative, not
prescriptive"), and "potential problem analysis" (anticipate what could go wrong
with the chosen option and act to prevent it) is close enough to Pre-mortem
("misreported", because the founding study measured reason-count, not quality)
that no separate literature for it was expected or found. KT-as-a-named-process
still has no trial of the integrated whole after four search passes, brand-name
and construct-name both, but that is because its parts already have grades, not
because nobody has looked at the parts.

What transfers regardless is the outcome vocabulary, and that is worth more here
than another framework. This project has struggled to say what "decision
quality" even means, and has been reduced to admissibility conjuncts and naming
floors. This literature has spent thirty years answering exactly that question
and has validated instruments for it:

| construct | what it measures | Cochrane result |
|---|---|---|
| **knowledge** | does the person know the options and their outcomes | MD +11.90/100, high certainty |
| **accurate risk perception** | are their probability estimates right | RR 1.94, high certainty |
| **decisional conflict (uninformed subscale)** | do they feel they lack the information to choose | MD −10.02, high certainty |
| **informed values-congruent choice** | does the choice match what *this person* actually values | RR 1.75, moderate certainty |

The last row is the construct this repository was founded on. The brief was
*"any decision ai helps the human make needs to be tailored to that human
context"*, and `fit.md` is the procedure for it. Values-congruent choice is that
idea, operationalised, measured across 21 trials, with a positive effect. That
is a far better target than "did the recommendation flip", which
[Track H's plan already rejected](../docs/superpowers/plans/) for punishing
conditional answers.

The action is small. Track H should adopt *informed values-congruent choice* as
its named primary construct rather than inventing one, and cite where it comes
from. Track K6 should rank it alongside elicited confidence. Neither requires
believing the health effect size transfers, only that the construct is better
defined than anything authored here.

---

## K3: what the existing prompt libraries encode, and in what form

Closed 2026-08-14. The question this track was asked is not "what frameworks
exist", since K1/K2 already answer that better than any prompt library does. It
is what form the encoding takes, because the founding observation is a form
claim: *"the maintainer installed [cc-thinking-skills] and reports it did not
help. That is data about form, not about the frameworks."* Three
published libraries were read first-hand for their packaging, not just their
content.

| Library | Frameworks | Packaging | Trigger mechanism | Evidence claim |
|---|---|---|---|---|
| [`cc-thinking-skills`](https://github.com/tjboudreaux/cc-thinking-skills) (tjboudreaux) | 28 | 28 separate skills, five groups | Autonomous, description-matched, the same mechanism as this repo's router | One provisional row, +4.0pp, flagged as *below* its own +5pt utility bar. No accuracy claim made. |
| [`thinking-skills`](https://github.com/wanikua/thinking-skills) (wanikua) | 20 | 20 files in `.claude/commands/` | Explicit: the user types `/critical-thinking <question>`, and Claude never decides to fire one | None. No citations, no measurement, a bare table of names and descriptions. |
| [`claude-skills-mental-models`](https://github.com/cyperx84/claude-skills-mental-models) (cyperx84) | 98 ("Munger-style") | One skill, 98-item body, auto-activates on phrases like *"help me think"*, *"apply mental model"*, or any model's own name, plus four parallel deliveries (CLI, MCP server, Python library, a "portable skill" for other harnesses), all backed by one CLI | Autonomous, and the broadest description of the three ("any model name" is itself a trigger) | None. "*A latticework for better decisions, one prompt away*" is marketing prose, not a measurement. |
| `decision-making` (this repo) | 4 | 1 skill, router table over 4 procedure files | Autonomous, description-matched | `verdict: UNTESTED`. Measured: firing 0.942 to 0.956 across n=1/2/4, routing 0.643 to 0.857 |

Two things follow, and the first is a limit on what this track can conclude.

No library in this survey reports a validated gain, so "does form predict which
ones help" cannot be answered from the public record: there is no *helped* case
to put next to the *didn't help* one. cc-thinking-skills' own author declines to
claim one and reports a number below their own bar; wanikua and cyperx84 make no
claim at all, not even a weak one. The maintainer's single anecdote about
cc-thinking-skills is the only outcome report in the set, and outcome reports
need at least two points to compare. This is a real limit on the question as
asked, not a hedge, so say so rather than force a contrast that the record does
not contain.

What the survey does establish is a genuine, mechanical form split, and it maps
directly onto the axis Track M has been running experiments on. wanikua's
slash-command form has no router at all. The human picks the command, so the
description-discrimination problem M2/M3/M4/M5/M6 spent five experiments
measuring (does it fire when it should, does it route to the right file) cannot
occur by construction in that form. cc-thinking-skills and cyperx84's library
both use autonomous, description-based triggering, the same mechanism
`decision-making` uses, so both are exposed to exactly the failure mode this
repo's own instrument was built to catch.

cyperx84's 98-models-in-one-entry is also the largest real *entry-body-size*
data point anyone has, distinct from cc-thinking-skills' 28-*separate-entries*
data point. The two libraries sit on different axes of the same M-track design
(M4/M5/M6 vary entry *count*; cyperx84 varies what one entry's *body* holds).
Track M4's own text already treats cc-thinking-skills at n=28 as a target to
reproduce; cyperx84 belongs in the same paragraph as the large-body counterpart,
and neither has been measured.

The connection to M4/M5/L5 that CLAUDE.md draws, that structure, content and
entry count moved only where a skill sits on the precision/recall frontier and
never how well its description discriminates, gives a specific, testable
prediction for cc-thinking-skills that nobody has run. If that mechanism
generalises past n=4, a 28-separate-skill library should be more conservative
than a one-entry bundle (M4's own account: "with separate entries, declining to
name a tool *is* declining to fire"), which predicts under-firing rather than
mis-routing as the dominant failure mode at n=28. That is a hypothesis about a
library nobody here has instrumented, stated so it can be checked rather than
assumed.

It does not, by itself, explain the maintainer's report, and reaching for form
as the explanation skips a simpler one this repository already has in hand. "Did
not help" is consistent with two different failures that an anecdote cannot
separate. Either the skill never fired, or it fired and the advice inside it was
not good advice, and only the first is a form problem. K1/K2's own catalogue
independently found that most of what a 28-skill "mental models" library reaches
for (Kepner-Tregoe, WRAP, OODA, satisficing, and the broader genre
cc-thinking-skills encodes) carries no located controlled evidence at all. Given
that this repo's own M4/M5/M6 already found entry count does not move
discrimination, content is the more parsimonious explanation for a report of
"did not help" than shadowing is. But this is an inference chained from two of
this repo's own results, not a new measurement of cc-thinking-skills itself, and
it is written down as one rather than filed as a finding. The honest sentence
is: *nobody has measured whether cc-thinking-skills fires*, and until someone
does, "form" and "content" are both live explanations of one person's report.

---

## K4: framework to failure mode

Closed 2026-08-14. A framework is a skill candidate only if it targets a failure
the model actually makes. Two independent things can defeat a candidate: the
human evidence can be weak (K1/K2's job), or the evidence can be excellent and
simply not apply: the target failure can be one this stack does not make, or one
whose mechanism has no counterpart in how a single LLM call runs. This
section maps all eleven catalogued frameworks against the second test. (Patient
decision aids is excluded from the eleven: the K1/K2 table itself says it "is
not a framework". It is an artefact handed to a patient, and its target is the
*patient's* knowledge gap, not a reasoning failure in whatever produced the
aid.)

Track A's contribution was checked before this table was written rather than
assumed. Track A (`docs/RESEARCH_PROGRAMME.md`, Part 4) is *not* a test of any
of these eleven mechanisms. Its five sub-experiments (A1 to A5) target
multi-turn accuracy drop, recency weighting, handoff loss, delegation value and
reliability, a different axis from anchoring, overconfidence, sycophancy or
base-rate neglect. As of 2026-08-13 only two of A1's three task families have
closed, and neither establishes a bias mechanism. `math` closed at
`p_discordant` = 0.000, which is a ceiling/no-power result ("this venue cannot
currently see [an effect]", in the track's own words), not a documented absence
of failure; `actions` closed as unmeasurable, because no object was comparable
across arms, an instrument defect rather than a finding. `database`, A2, A3, A4
and A5 have not run. So Track A contributes nothing to the DOCUMENTED/ASSUMED
column below, and any row that reads DOCUMENTED is grounded in outside LLM
literature or in this repository's *pre*-Track-A corpora, named where it
applies.

| Framework | Failure it would target | Documented in LLMs, or assumed? |
|---|---|---|
| Calibration / probability training | Overconfidence in a stated recommendation | Documented, directly. Five LLMs studied "overestimate the probability that their answer is correct between 20% and 60%": Sun & Li, *Large Language Models are overconfident and amplify human bias* (arXiv:2505.02151, abstract, verified first-hand 2026-08-14; pending a `paper/refs.bib` entry). Not measured on this stack: no procedure here elicits a probability. |
| Debiasing training (game/video) | A battery of six named human biases (bias blind spot, anchoring, confirmation bias, fundamental attribution error, projection bias, representativeness), reduced by one structured session | Partly documented, partly likely mismatched. Of the six, only anchoring has a direct LLM study located: Vu et al., *Anchoring Bias in Large Language Models: An Experimental Study* (arXiv:2412.06593, abstract, verified 2026-08-14; pending a bib entry), on "the sensitivity of LLM responses to biased hints", with simple mitigations (CoT, reflection) found insufficient. The other five presuppose an ongoing self-model or social attribution process (explaining *why another agent* acted, or one's own blind spots over time) that a stateless single-call model has no clear counterpart for, so they are assumed not to transfer, not measured either way. |
| Consider-the-opposite | Anchoring on the first framing offered / insufficient counter-evidence generation | Documented, adjacent. Sycophancy is the closest measured LLM analogue: "first-person prompts ('I believe...') consistently induce higher sycophancy rates than third-person framings", from Wang et al., *When Truth Is Overridden* (arXiv:2508.02087, already in `paper/refs.bib` with a `quote` field, per `docs/RELATED_WORK.md`). Directional only; the paper states no rate. |
| Reference class / outside view | Reasoning from the specific case only, neglecting a base rate | Assumed. Search turned up work on LLMs *assisting human* forecasters (not opened first-hand and not cited here, see "Sources checked" below) but nothing testing whether the model's *own* unaided reasoning neglects base rates. No claim made pending that gap. |
| Pre-mortem | Under-weighting failure paths | Measured, and absent. This is the strongest row in this table, and it is repo-native. The pre-Track-A casefile probe offered 27 trap opportunities across consequence-orders 1 to 3 and none were taken; the model already reasoned about downstream failure unprompted. Combined with K1/K2's own finding that the framework's founding study (Mitchell, Russo & Pennington 1989) measures reason-*count*, not decision quality, this is a double miss: weak evidence on the human side, and the one piece of this repo's own data says the target failure does not occur on the task it was checked against. |
| Kepner-Tregoe Rational Process | Conflating problem definition with causal analysis; treating one appraisal as several problems | Neither documented nor assumed with any confidence: no LLM-specific test was located, and K1/K2 found no controlled human evidence either. Weak on both axes, and not the "excellent evidence, wrong target" pattern, just no evidence anywhere. |
| WRAP | Narrow option generation; insufficient reality-testing of the leading option | Mixed, and this row moved under my hands while writing it. A concurrent K2 pass split WRAP into the integrated four-step process (still *none located*) and its "widen your options" component, which now has real human evidence: Basu & Savani 2017 (7 experiments, ≈2,892 participants, +7 to 16pp for presenting options simultaneously) and Dow et al. 2010 (parallel vs. serial prototyping). The LLM-side target, whether the model defaults to a narrow, single-option answer, is still assumed, not documented; it is adjacent to the anchoring evidence above (a first option can anchor the same way a first hint does) but no study tests option-generation breadth directly. So the human evidence for the WRAP *component* is now real, and the LLM-failure evidence for it is not: this is the inverse of the debiasing-training pattern below, a candidate with a live human-evidence half and an open LLM-evidence half. |
| OODA | Stale situational awareness under a competitive, real-time tempo the actor must keep pace with | Mechanism mismatch, not an evidence gap. OODA's claim is about winning a tempo race against an adversary who is also observing and acting. A single stateless completion has no "orient" phase distinct from generation and no adversary whose loop it is racing, so the mechanism the framework depends on is not present in the venue, independent of whether anyone has measured it. |
| Decision analysis / MAUT | Inconsistent implicit weighting across attributes; defaulting to a holistic gut call instead of an explicit decomposition | Assumed, and plausibly the wrong direction. The human failure MAUT corrects is a working-memory limit on holding many weighted attributes at once. Explicit decomposition and arithmetic over stated weights is closer to what a language model is good at than to what it struggles with, so the failure this framework targets may not transfer at the strength the human literature (itself only "normative, not prescriptive") would suggest. Not measured. |
| Satisficing vs maximising | Costly over-search past "good enough," driven by regret | Mechanism mismatch, not an evidence gap. The construct requires an extended search process over time and an affective regret response to foregone options. A single-shot generation does not search iteratively and has no persistent state to regret from. K1/K2 already grades the human evidence "misfit for our purpose" (correlational, wellbeing-outcome); the LLM target is a second, independent reason this is not a skill candidate. |
| Option value / reversibility | Effort and caution mismatched to how hard a decision is to undo | Assumed. No LLM-specific study located. This is the one row with no documented mismatch and no mechanism objection, and it is also the framework already shipped as `timing.md`, which is exactly the untested state the scorecard's `UNTESTED` verdict describes. |

### Which frameworks fail the excellent-evidence-wrong-target test

The task this table exists to run: a framework with strong human prescriptive
evidence, aimed at a failure this stack does not make, is not a skill
candidate regardless of how well-supported it is in humans. Three of the
eleven qualify, each for a different reason, and none of the three should be
confused with the frameworks *K1/K2 already excluded for having no human
evidence at all*: Kepner-Tregoe throughout, the integrated four-step WRAP
process (its "widen your options" component now excepted, see the table
above), and OODA's and satisficing's own weak human backing. OODA and
satisficing are excluded twice over, once on each axis.

1. Debiasing training (game/video) is the cleanest instance. It carries the
   best human evidence in the entire K1/K2 catalogue, "supported," medium-
   to-large effects, Cohen's *d* > 1, durable at two months, of any row that
   is not contested. But its target is a six-bias battery, and only one of the
   six (anchoring) has a located LLM study. The other five are validated
   against biases that are partly about a person's model of *other* people or
   of *their own* tendencies over time, constructs a stateless completion has
   no clear analogue for. The best-evidenced framework in the whole table is
   evidenced against a target that is, at most, one-sixth confirmed here.
2. OODA fails on mechanism, not on missing papers. Even if a controlled trial
   existed, the loop's claim, win by cycling observe-orient-decide-act faster
   than an adversary who is doing the same, has no counterpart in a single
   completion with no adversary and no repeated loop to be faster on.
3. Satisficing vs maximising fails on mechanism too, for a different reason:
   the construct needs sustained search and regret, neither of which a one-shot
   generation has.

Pre-mortem is a fourth case worth flagging separately, because unlike the three
above it rests on this repo's own measurement rather than an outside literature
gap. Its human evidence is already weak ("misreported", because it counts
reasons, not quality), and the one piece of data this repository has *about
LLMs specifically*, the casefile probe's 27-for-27, says the failure it would
correct does not occur on that task. It is not excluded on the same logical
ground as the three above (a documented-elsewhere failure that plausibly does
not transfer, or a missing mechanism); it is excluded because the one direct
check available says no.

Calibration and Consider-the-opposite are the two rows where the human evidence
and the LLM-failure evidence now both point the same direction, and both are
already K6's top two ranked candidates. That agreement was not available when K6
was written on 2026-08-12, because the LLM-side evidence for both was found
today, and it strengthens rather than changes K6's ranking.

---

## K6: skill candidates, ranked by evidence

The ranking changed on 2026-08-14, K2's fourth pass, and it is reported here
rather than folded in quietly. A new candidate, generate options concurrently
rather than one at a time, the "widen your options" quarter of WRAP, enters at
Rank 2, ahead of consider-the-opposite. This is not a reshuffle for its own
sake: Basu & Savani (2017) is seven experiments, ~2,892 participants, every
simultaneous-vs-sequential comparison significant at p ≤ .02 (one at p < .0001),
and Dow et al. (2010) is an independent research group, a different domain
(design prototyping, not choice among described options), and a real behavioural
outcome (click-through), also significant. Consider-the-opposite's own evidence
is two original experiments plus a later replication attempt that moved in the
right direction without reaching significance. Multiple independent,
still-standing significant results beat an original-plus-null-replication pair
on the evidence this document grades by, so the ranking moves, even though both
remain merely partial-to-supported, not calibration's contested-but-large
effect.

Rank 1 is elicited confidence, with scoring. Add a required probability or
threshold to the response contract and score it with the calibration module that
already exists. This is the only candidate whose parent intervention has
medium-to-large controlled effects in humans, it needs no new corpus, and it
turns an unused, fully tested module into an outcome. It also fixes the
measurement problem the pre-mortem finding raises: a number can be scored for
accuracy, whereas a list of considerations can only be counted.

Rank 2 is generating options concurrently, new on 2026-08-14. Before evaluating
any option in depth, generate two or more candidate answers in parallel and
compare them, rather than developing one answer and revising it. This is the
narrow, testable procedure behind WRAP's "widen your options" letter, stripped
of the other three letters (which have no located evidence, see finding 5
above), and it is a closer match to the evidence than "encode WRAP" would be:
the trials support *concurrent generation*, not reality-testing, distance, or
preparing to be wrong. It is directly implementable as a sub-agent fan-out
(generate N candidate recommendations independently, then compare), which makes
it a second natural candidate for Track D alongside consider-the-opposite.

Rank 3 is consider-the-opposite, as a procedure and not a prompt. Partial
evidence, an unambiguous operationalisation, and it is the mechanism behind the
council / adversarial-review skill the brief already named. It is also a
framework whose form maps cleanly onto sub-agents.

Rank 4 is switching conditions, already shipped as `fit.md`. It is the closest
thing in the catalogue to *breakeven and value-of-information analysis*, which
is normatively solid even where prescriptive trials are missing, and it is the
procedure closest to the founding brief's actual subject: advice that is correct
in general and wrong for this person.

Not recommended as skill content: Kepner-Tregoe and OODA, entirely. They are
popular, comprehensively encoded elsewhere, and carry no located controlled
evidence, after four search passes each. WRAP is now split. Its "widen your
options" letter is Rank 2 above; its other three letters (reality-test, attain
distance, prepare to be wrong) remain not recommended on the same grounds as KT
and OODA. Encoding the *named frameworks* whole would still reproduce
`cc-thinking-skills` and inherit its result. The promotion is of a specific,
evidenced mechanism, not of the brand.

Recommended with a warning: the pre-mortem. Worth having, but any evaluation of
it must score decision quality and must not score the number of risks named,
because that is the only thing its founding study measured.

---

## The audit: are the four shipped procedures traceable?

The programme's done-when condition is that every current skill is either traced
to a documented framework or explicitly marked as invented.

| Procedure | Traces to | Verdict |
|---|---|---|
| `cascade.md` (consequence cascade) | Second-order thinking; Kepner-Tregoe's *potential problem analysis*; futures wheel | **Traced.** Named frameworks, no controlled evidence behind any of them |
| `timing.md` (decide or wait) | Real-options / option value; reversibility; satisficing vs maximising | **Traced.** Theory-backed, untested as advice |
| `fit.md` (switching conditions) | Breakeven analysis and value of information in decision analysis | **Traced**, and it is the strongest trace of the four |
| `ledger.md` (evidence ledger) | Nothing in the catalogue | **Invented.** Diagnosticity and relevance ranking are real ideas, but no named decision framework prescribes this procedure |

So: three of four trace to documented frameworks, none of the four traces to a
framework with strong prescriptive evidence, and one is invented outright.

That is a better result than "all four invented" and a worse one than the
scorecard's `UNTESTED` verdict might suggest to a casual reader. `UNTESTED` says
nobody measured it here, and this table adds that for three of the four, nobody
has convincingly measured the underlying idea anywhere either.

`ledger.md` is not thereby wrong. It is the procedure with the least external
support and the most exposure, and it should be first in line behind any
candidate that has a literature.

---

## What is still open in Track K

- K2 had a second pass on 2026-08-12 and nothing changed. Kepner-Tregoe, WRAP
  and OODA were searched again with queries restricted to PubMed, PsycNET,
  ScienceDirect, SpringerLink, Wiley, Taylor & Francis, SAGE and Google Scholar.
  No controlled evaluation of any of the three was found, so all three rows
  stand at *none located*. What the pass returned instead was consultancy
  marketing for KT, book summaries for WRAP, and simulation/modelling papers for
  OODA (e.g. [arXiv:2203.15502](https://arxiv.org/abs/2203.15502), a red-vs-blue
  game analysis), none of which evaluates the loop as advice to a human.

  This is still not a systematic review and must not be described as one.
  There is no full-text database access here, so the searches hit indexed
  abstracts and public landing pages only. *None located* remains a statement
  about the search. What it now means is *two sessions, the second
  domain-restricted*, which is stronger than it was and weaker than *none
  exists*.

  The productive result of the second pass was finding the patient decision
  aids literature, which is now row 12 of the catalogue and is the
  best-evidenced entry in it. Searching for evaluations of named frameworks kept
  returning nothing; searching for evaluations of *structured decision support*
  returned 209 trials. The frameworks were the wrong search key, and that is
  worth recording for whoever does the third pass.
- The third pass ran on 2026-08-13 and took the second pass's advice. It
  searched for controlled evaluations of *LLM-assisted decision making* rather
  than of named frameworks, and the two trials it found say opposite things,
  which is the point.

  | | Goh et al. 2024 | Agweyu et al. 2026 |
  |---|---|---|
  | design | RCT, 92 physicians, 5 vignettes, expert rubrics | cluster-RCT, 16 Kenyan primary care facilities, 103 clinical officers, 9,691 patients |
  | setting | simulated cases | real consultations |
  | process measure | management reasoning 43.0% vs 35.7%, +6.5pp, p < 0.001 | appropriate diagnosis recorded, aOR 1.74, p < 0.001 |
  | outcome measure | none | treatment failure 2.2% vs 2.0%, aOR 0.77, p = 0.13 |

  The process measure moved in both. The one outcome measure did not. The
  larger, more realistic, more expensive trial is the one that found nothing,
  and it found nothing *while* showing the intervention visibly changed how the
  work was written down.

  Two things follow for this repository, and both are uncomfortable.

  First, it is the exact shape of every result here so far. M4, M5 and L5
  each moved where the skill sits on a precision/recall frontier and none moved
  how well it discriminates; the probe casefiles took zero of 27 traps; `math`
  returned `p_discordant` 0.000. A programme whose outcome measures keep
  refusing to move, while its process measures move readily, should expect
  Tracks C through F to land where Agweyu did. That expectation belongs in the
  pre-registrations before those tracks run, not in their discussions
  afterwards.

  Second, Goh is the strongest located evidence for Track H specifically.
  The gain was largest in *case-specific* domains (+6.2pp, 95% CI 2.4 to 9.9,
  p = 0.002), and the authors attribute it to physicians considering patient
  context they would otherwise skip. That is the tailoring construct, measured,
  in a randomized trial, with a positive result, which is more than any
  framework in the catalogue has. It does not validate the `fit` procedure, and
  it is not evidence about life decisions. It establishes that the axis is real
  and moves under assistance, which was previously an assumption of the
  founding brief.

  A caveat that has to travel with both: 19.5% full adherence in Agweyu, and an
  expert panel judging clinician decisions unjustified in 71.6% of the sampled
  encounters. Advice given is not advice taken, and every skill measurement
  in this repository is of advice given.
- K2 is closed, fourth pass, 2026-08-14. The task was to close the
  remaining "none located" rows, Kepner-Tregoe, WRAP and OODA, by searching
  again rather than repeating the second pass's domain-restricted queries
  verbatim. The move that mattered, following the second pass's own conclusion,
  was to search for the *construct* behind each framework rather than its brand
  name: "simultaneous vs. sequential option presentation" and "number of
  alternatives and decision quality" instead of "WRAP", "OODA loop training
  evaluation" and the endnotes of the loop's own academic critics instead of
  "OODA effectiveness". It found real controlled evidence for WRAP's "widen
  your options" letter (finding 5, above, and K6's revised ranking) and one
  academic theoretical critique of OODA (Bryant 2006), neither of which
  existed in this document before today. It found nothing for Kepner-Tregoe
  as a named process, but the search clarified *why*: KT's own components
  overlap with two rows this table already grades (Decision analysis / MAUT,
  and Pre-mortem), so its "none located" verdict was never really about an
  unstudied idea, only about an unstudied *bundling* of two studied ones.

  One source was found and could not be verified, and is reported that way
  rather than dropped or guessed at. Priyanath & Chaminda (2019), *Sri
  Lanka Military Academy Journal* 1(1) 31-46, regresses small-enterprise
  "business fog" on OODA-strategy use; a WebSearch summary reported the
  Observe/Orient/Decide/Act coefficients as mostly non-significant except
  Orient, but every attempt to open the paper itself (ResearchGate, direct
  PDF) returned a CAPTCHA or verification wall. No number from it is
  reported anywhere in this document or in `paper/refs.bib`, per this
  repository's rule that an unopened source may be named but not quoted from.
  It would not have changed the OODA grade even if opened: it evaluates a
  self-reported survey construct ("fog"), not decision quality, so its
  proper home would have been the "measures something other than decision
  quality" bucket, not a fourth *supported* row.

  A near-miss worth recording, because the rule caught it before it entered
  the document. One WebSearch summary, while researching Kepner-Tregoe,
  attributed "individuals who received training in this method demonstrated
  improved decision-making skills" to "Johnson et al., 2012", with no journal,
  no title, and no findable paper behind the citation on a direct follow-up
  search. It was not used. This is the same failure mode standing rule 5 exists
  for, a plausible-looking citation nobody opened, except that this time the
  source was a search engine's own summarisation rather than a human's memory,
  which is a new variant of an old problem for this repository's citation
  discipline to stay alert to.

  Sources are listed in "Sources checked on 2026-08-14 (K2 fourth pass)"
  below; new bibliography entries are `dow2010parallel`, `basusavani2017`,
  `hauschildtgemunden1985` and `bryant2006ooda` in `paper/refs.bib`, each
  carrying a `quote` field read from the primary source (mostly via
  `r.jina.ai` text extraction, since direct `WebFetch` returned unparseable
  binary for every PDF tried on this pass, recorded per entry).
- K3 and K4 closed 2026-08-14. K3 surveyed two more published libraries
  beyond `cc-thinking-skills` and found a genuine form split (autonomous
  description-triggering vs. explicit slash commands) but no "helped" library
  to contrast against the maintainer's "didn't help" anecdote, so the form
  question is answered as *unanswerable from the public record* rather than
  forced. K4 mapped all eleven catalogued frameworks to a target failure and
  graded each DOCUMENTED or ASSUMED; three fail the excellent-evidence-wrong-
  target test outright (debiasing training, OODA, satisficing vs maximising)
  and a fourth (pre-mortem) fails on this repo's own casefile measurement
  rather than on an evidence gap. Two new LLM-bias papers were opened
  first-hand and are pending `paper/refs.bib` entries:
  arXiv:2412.06593 (anchoring) and arXiv:2505.02151 (overconfidence), both
  listed in `paper/citations-baseline.txt`. A third (arXiv:2508.02087,
  sycophancy) was already in the bibliography from earlier work and needed no
  new entry.
- K4's mapping still depends on Track A for anything beyond `math` and
  `actions`. `database`, A2, A3, A4 and A5 have not run, and none of A1's two
  closed families tested a bias mechanism, as the table above shows. Re-read
  this document against Track A's later results rather than treating the
  DOCUMENTED/ASSUMED column as final.
- K5, the citation backlog, is separate and tracked in
  `paper/citations-baseline.txt`.

## Sources checked on 2026-08-12

- Hauenstein, Thomas, Illingworth & Dougherty (2025), *Rethinking the Role of
  Teams and Training in Geopolitical Forecasting*, Psychological Science.
  <https://journals.sagepub.com/doi/10.1177/09567976241266481>
- Mellers et al. (2014), Good Judgment Project training results.
  <https://learnmoore.org/papers/Mellers%20et%20al%202014.pdf>
- Morewedge, Yoon, Scopelliti, Symborski, Korris & Kassam (2015), *Debiasing
  Decisions*, Policy Insights from the Behavioral and Brain Sciences 2(1)
  129-140. <https://journals.sagepub.com/doi/abs/10.1177/2372732215600886>
- Mitchell, Russo & Pennington (1989), *Back to the future: temporal perspective
  in the explanation of events*, JBDM.
  <https://onlinelibrary.wiley.com/doi/abs/10.1002/bdm.3960020103>
- Collins, *The premortem*, course notes on behavioural economics and corporate
  decision making. <https://corporate.jcx.au/premortem>
- Lord, Lepper & Preston (1984), *Considering the Opposite*.
  <https://www.semanticscholar.org/paper/e71bbae72f8ad78e97c54f5ec88c9af2c70759f2>
- *Reference class forecasting: promises, problems, and a research agenda moving
  forward* (2025).
  <https://www.tandfonline.com/doi/full/10.1080/09537287.2025.2578708>
  (abstract not retrievable, 403; the summary above is from search results and
  the row is graded accordingly)
- `cc-thinking-skills`. <https://github.com/tjboudreaux/cc-thinking-skills>

## Sources checked on 2026-08-12 (second pass)

- Stacey, Lewis, Smith et al. (2024), *Decision aids for people facing health
  treatment or screening decisions*, Cochrane Database of Systematic Reviews,
  209 RCTs, 107,698 participants.
  <https://pubmed.ncbi.nlm.nih.gov/38284415/>
- Searched and found nothing evaluative: Kepner-Tregoe rational process,
  WRAP / Heath & Heath *Decisive* (2013), OODA loop. Queries restricted to
  PubMed, PsycNET, ScienceDirect, SpringerLink, Wiley, Taylor & Francis, SAGE
  and Google Scholar.
- Nearest OODA hit, and it is not an evaluation of the loop as advice:
  *Analysis of OODA Loop based on Adversarial for Complex Game Environments*.
  <https://arxiv.org/abs/2203.15502>

## Sources checked on 2026-08-13 (third pass)

Search key was *LLM-assisted decision making, controlled trials* rather than the
named frameworks, per the second pass's own conclusion. Both were verified
first-hand and entered in `paper/refs.bib` with verbatim quotes.

- Goh, Gallo, Strong, Weng, Kerman, Freed, Cool, Kanjee, Lane, Parsons, Ahuja,
  Horvitz, Yang, Milstein, Olson, Hom, Chen & Rodman (2024), *Large Language
  Model Influence on Management Reasoning: A Randomized Controlled Trial*,
  medRxiv 2024.08.05.24311485.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC11326321/>
- Agweyu et al. (2026), *Generative AI-enabled clinical decision support system
  in primary care: a pragmatic, cluster-randomized trial*, Nature Medicine.
  <https://www.nature.com/articles/s41591-026-04503-6>

## Sources checked on 2026-08-14 (K2 fourth pass)

Search key was the construct behind each brand name (per the second pass's own
lesson), tried alongside the brand name itself. All numbered claims below were
read from the primary source first-hand and are entered in `paper/refs.bib`
with verbatim `quote` fields. Direct `WebFetch` returned unparseable binary for
every PDF host tried (Stanford HCI, CMU, aaalab.stanford.edu, ResearchGate,
ScienceDirect), so the `r.jina.ai` text-extraction proxy was used instead and is
recorded per entry.

- Basu, Shankha & Savani, Krishna (2017), *Choosing One at a Time? Presenting
  Options Simultaneously Helps People Make More Optimal Decisions Than
  Presenting Options Sequentially*, Organizational Behavior and Human
  Decision Processes 139, 76-91.
  <https://dr.ntu.edu.sg/server/api/core/bitstreams/589ceee9-901f-4dc4-9232-d844623aa2e9/content>
  (NTU institutional repository copy; ResearchGate and ScienceDirect both
  blocked direct access with a verification wall)
- Dow, Steven P., Glassco, Alana, Kass, Jonathan, Schwarz, Melissa, Schwartz,
  Daniel L. & Klemmer, Scott R. (2010), *Parallel Prototyping Leads to Better
  Design Results, More Divergence, and Increased Self-Efficacy*, ACM
  Transactions on Computer-Human Interaction 17(4), Article 18.
  <https://hci.stanford.edu/publications/2010/parallel-prototyping/ParallelPrototyping2010-submitted.pdf>
- Hauschildt, Jürgen & Gemünden, Hans Georg (1985), *Number of Alternatives and
  Efficiency in Different Types of Top-Management Decisions*, European
  Journal of Operational Research 22(2), 178-190.
  <https://www.sciencedirect.com/science/article/abs/pii/0377221785902267>.
  Found by following the endnotes of Heath & Heath's *Decisive* (the "Widen
  your options" chapter cites this as its "University of Kiel" study; Gemünden
  was at Kiel at the time).
  <https://heathbrothers.com/wp-content/uploads/2013/03/backmatter-1.pdf>
- Bryant, David J. (2006), *Rethinking OODA: Toward a Modern Cognitive
  Framework of Command Decision Making*, Military Psychology 18(3),
  183-206. <https://www.tandfonline.com/doi/abs/10.1207/s15327876mp1803_1>
  (abstract only; full text paywalled)

Found but not opened first-hand and not cited with a number, per this
document's own rule against inferring what a blocked source says:

- Priyanath, H. M. S. & Chaminda, K. A. S. (2019), *Strength of OODA Loop as a
  Governing Strategy of Business Fog: An Empirical Investigation of Small
  Enterprises in Sri Lanka*, Sri Lanka Military Academy Journal 1(1),
  31-46.
  <https://www.researchgate.net/publication/338124153>. Every fetch attempt
  returned a CAPTCHA/verification wall. Named here so the search is
  reproducible, not as a source of any figure in this document.
- A citation attributed to "Johnson et al., 2012" for Kepner-Tregoe training
  outcomes, surfaced only inside a WebSearch tool's own summarisation with no
  journal, title, or resolvable identifier. Not used; see the near-miss note
  above.

Searched and found nothing evaluative, beyond what the second and third
passes already reported: Kepner-Tregoe as an integrated process (queries
included "structured problem-solving training" and "weighted decision matrix
training" as construct-level alternatives to the brand name, in addition to
"Kepner-Tregoe" itself); WRAP's other three letters searched as constructs
("reality-testing assumptions before deciding", "attaining emotional distance
decision quality", "prepare to be wrong overconfidence decision training");
OODA as trained advice to a human decision-maker (versus as a simulation or
robotics control loop, which the second and third passes already found
plenty of).

## Sources checked on 2026-08-14 (K3 and K4 closing pass)

Prompt-library READMEs, fetched and read first-hand rather than taken from
search-result summaries:

- `thinking-skills` (wanikua). <https://github.com/wanikua/thinking-skills>
- `claude-skills-mental-models` (cyperx84).
  <https://github.com/cyperx84/claude-skills-mental-models>

LLM-bias papers, abstracts fetched and read first-hand. Two are pending a
`paper/refs.bib` entry, listed in `paper/citations-baseline.txt` rather
than added to the bibliography, because another session was editing
`refs.bib` concurrently with this pass:

- Vu, [et al.] (2024), *Anchoring Bias in Large Language Models: An
  Experimental Study*, arXiv:2412.06593.
  <https://arxiv.org/abs/2412.06593>. Abstract, no headline number; verbatim:
  "our findings highlight the sensitivity of LLM responses to biased hints,"
  and "simple algorithms such as Chain-of-Thought, Thoughts of Principles,
  Ignoring Anchor Hints, and Reflection are not sufficient" to mitigate it.
  Pending bib entry.
- Sun & Li (2025), *Large Language Models are overconfident and amplify human
  bias*, arXiv:2505.02151. <https://arxiv.org/html/2505.02151>. Abstract,
  verbatim: "all five LLMs we study are overconfident: they overestimate the
  probability that their answer is correct between 20% and 60%." Pending
  bib entry.
- Wang et al. (2025), *When Truth Is Overridden: Uncovering the Internal
  Origins of Sycophancy in Large Language Models*, arXiv:2508.02087.
  Already in `paper/refs.bib` (`wang2025truthoverridden`, added in earlier
  work, `quote` field present). No action needed; the existing quote was
  re-verified before reusing it here and it matches the abstract's claim.

Not opened first-hand and not cited as a result, named only to record that
the search returned them and found nothing usable, with identifiers
deliberately omitted so this paragraph does not itself trip the citation gate
for a paper nobody has read: a survey of six cognitive biases in LLMs
including order bias and confirmation bias, found via search summary only; and
a study of LLM assistants helping *human* forecasters, which tests whether an
LLM improves a human's base-rate use, not whether the model's own unaided
reasoning neglects base rates, the wrong question for this table even had it
been opened.
