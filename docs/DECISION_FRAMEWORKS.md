# Decision frameworks: the review this project skipped

**Track K1–K4, K6.** Status: **two passes, both 2026-08-12.** Every number below was
checked against a source on that date; every framework without a number is
marked with what was *not* found rather than left blank.

---

## Why this exists, and why it is late

The founding brief asked for research on how to make good decisions **before** a
direction was chosen. That did not happen. Four decision procedures were written
in this repository by a model reasoning from first principles, and only then did
anyone go looking for whether the field already had an answer.

That is the exact failure the brief warned about — "skills based on really
nothing" — and SkillsBench puts a number on it: curated skills gained +16.6pp
while self-generated ones came in at roughly zero or negative
([arXiv:2602.12670](https://arxiv.org/abs/2602.12670)).

So this document does two jobs. It catalogues what the decision literature
actually supports, and it audits the four procedures already shipped against
that catalogue. The audit's finding is at the bottom and it is mixed.

## The rule this document is written under

**No claim carries a number unless the number was read off a source on
2026-08-12.** Where a framework is popular and the evidence was not found, the
row says *none located* — which is a statement about the search, not about the
world, and is deliberately weaker than *none exists*.

This rule is not decoration. Three misattributed numbers were written into this
repository in a single morning on 2026-08-11, all citing real papers that said
something adjacent. `de check`'s citation gate binds arXiv identifiers to
verbatim quotes, but **almost nothing in the decision literature is on arXiv**,
so the gate cannot see this file's central claims. The discipline has to be
manual here, and saying so is part of the record.

One error was caught by this rule while writing: Morewedge et al. (2015) is in
*Policy Insights from the Behavioral and Brain Sciences*, not PNAS. From memory
it would have gone in as PNAS.

---

## K1 + K2 — the catalogue, graded by evidence

Two columns matter and they disagree constantly. **Popularity** is how often a
framework appears in business writing. **Prescriptive evidence** is whether
anyone has shown it improves decisions in a controlled setting. The gap between
them is the single most useful thing in this document.

| Framework | What it claims | Prescriptive evidence | Grade |
|---|---|---|---|
| Calibration / probability training | Short training improves forecast accuracy | GJP: ~6–11% Brier improvement over control, training under one hour. **Challenged in 2025** — see below | **contested** |
| Debiasing training (game/video) | One session reduces named biases, durably | Morewedge et al. 2015: medium-to-large effects, Cohen's *d* > 1, holding at two months; game beat video | **supported** |
| Consider-the-opposite | Explicitly generating opposing evidence reduces assimilation bias | Lord, Lepper & Preston 1984: beat "be fair and unbiased" instructions in two experiments. Later replication attempts moved in the predicted direction **without reaching significance** | **partial** |
| Reference-class forecasting | Take the outside view from a class of similar past cases | Adopted by the American Planning Association; case studies report improved accuracy. A 2025 review is titled *promises, problems, and a research agenda* and reports that little empirical evidence exists on RCF's accuracy versus other methods | **weak** |
| Pre-mortem | Imagine the failure has happened, then explain it | The famous "30%" is Mitchell, Russo & Pennington 1989 and it measures the **number of reasons generated**, not their quality or any decision outcome. The academic literature on the pre-mortem itself is thin | **misreported** |
| Kepner-Tregoe Rational Process | Situation appraisal → problem analysis → decision analysis → potential problem analysis | Widely deployed corporately (NASA, GM are the usual citations). **No independent controlled evaluation located** | *none located* |
| WRAP (Heath & Heath) | Widen options, reality-test, attain distance, prepare to be wrong | **No independent controlled evaluation located** | *none located* |
| OODA | Observe, orient, decide, act, faster than the adversary | Doctrinal and historical; **no controlled evaluation located** | *none located* |
| Decision analysis / MAUT | Decompose into attributes, weight, and score | Strong normative case. Evidence that decomposition improves *outcomes* rather than consistency is thin | **normative, not prescriptive** |
| Satisficing vs maximising | Stop at good-enough rather than search for best | Schwartz et al.'s work is **correlational** and its outcome is wellbeing and regret, not decision quality | **misfit for our purpose** |
| Option value / reversibility | Spend effort in proportion to how hard a choice is to undo | Grounded in real-options theory; the popular "one-way and two-way doors" form has **no controlled evaluation located** | **theory-backed, untested as advice** |
| **Patient decision aids** | A structured tool that states the options, their outcomes, and elicits what the person values, before the choice | **Stacey et al. 2024, Cochrane: 209 RCTs, 107,698 participants.** Knowledge MD +11.90/100 (CI 10.60–13.19; 107 trials), accurate risk perception RR 1.94 (CI 1.61–2.34; 25 trials), decisional conflict (uninformed) MD −10.02 (CI −12.31 to −7.74; 58 trials) — all **high-certainty**. Informed values-congruent choice RR 1.75 (CI 1.44–2.13; 21 trials), moderate-certainty | **strongly supported, in a different domain** |

### The four findings that change what this project should build

**1. The pre-mortem's headline number does not say what everyone says it says.**
Mitchell, Russo & Pennington found that imagining an event has already occurred
"increases the number of reasons generated for the potential future outcome by
approximately 30%" — and, in the reviewer's words, they "did not assess the
quality of the reasons." Klein's later framing of the same result as improving
the ability to *correctly identify* reasons is a stronger claim than the study
supports.

This matters here more than anywhere else in the table. **A procedure that makes
a model produce more considerations is not thereby a procedure that makes it
decide better**, and *more considerations* is exactly what a structured skill
most easily produces and what a careless metric most easily rewards. This
repository has already been bitten by the same conflation from the other side —
a hedged, branch-covering answer was praised in prose on probe-07 and would have
been scored *worse* by the metric proposed alongside it.

**2. The best-evidenced framework in the table is under active challenge.**
Mellers et al. (2014) is the Good Judgment Project result everyone cites for
calibration training. Hauenstein et al. (2025, *Psychological Science*)
re-analysed it under item response theory and concluded that "the conclusions
provided in Mellers et al. (2014) are not straightforward and raise the
possibility that both teaming and training did not improve forecasting ability."
The superforecaster findings partially survive; the *training* effect — the part
that would license a skill — is the part in question.

The honest reading is that calibration training remains the strongest candidate
in the table **and** that its strength is one contested re-analysis away from
the rest of the field.

**3. Four of eleven frameworks have no controlled evaluation this search could
find.** They are, without exception, the four most likely to be found in a
corporate deck. Kepner-Tregoe, WRAP, and OODA are the frameworks a model asked
to "use a decision framework" would most readily reach for, and they are the
ones with the least behind them.

**4. Added 2026-08-12: the strongest evidence in the whole table is in a
literature nobody in this field cites, and it is not a framework.** Patient
decision aids are the one form of structured decision support that has been
tested at scale: **209 randomised trials, 107,698 participants**, meta-analysed
in a 2024 Cochrane review, with three high-certainty effects and one
moderate-certainty one. Nothing else in the table is within two orders of
magnitude of that evidence base.

**The transfer is not automatic and must not be written as if it were.** These
are health treatment and screening decisions, delivered to patients, usually
around a clinical consultation, by a static tool rather than a conversational
model. None of that is a life-or-work decision handled by an LLM. The grade in
the table therefore says *strongly supported, **in a different domain***, and
that qualifier is load-bearing.

**What transfers regardless is the outcome vocabulary, and that is worth more
here than another framework.** This project has struggled to say what "decision
quality" even means, and has been reduced to admissibility conjuncts and
naming floors. This literature has spent thirty years answering exactly that
question and has validated instruments for it:

| construct | what it measures | Cochrane result |
|---|---|---|
| **knowledge** | does the person know the options and their outcomes | MD +11.90/100, high certainty |
| **accurate risk perception** | are their probability estimates right | RR 1.94, high certainty |
| **decisional conflict — uninformed subscale** | do they feel they lack the information to choose | MD −10.02, high certainty |
| **informed values-congruent choice** | does the choice match what *this person* actually values | RR 1.75, moderate certainty |

**The last row is the construct this repository was founded on.** The brief was
*"any decision ai helps the human make needs to be tailored to that human
context"*, and `fit.md` is the procedure for it. Values-congruent choice is that
idea, operationalised, measured across 21 trials, with a positive effect. That is
a far better target than "did the recommendation flip", which
[Track H's plan already rejected](../docs/superpowers/plans/) for punishing
conditional answers.

**Actionable, and small:** Track H should adopt *informed values-congruent
choice* as its named primary construct rather than inventing one, and cite where
it comes from. Track K6 should rank it alongside elicited confidence. Neither
requires believing the health effect size transfers — only that the construct is
better defined than anything authored here.

---

## K3 — what the existing prompt libraries encode

[`cc-thinking-skills`](https://github.com/tjboudreaux/cc-thinking-skills) is the
closest published comparator: **28 skills** across five groups (route/compose,
diagnose, decide, create, risk). It encodes Kepner-Tregoe, Cynefin, OODA,
pre-mortem, second-order thinking, reversibility, satisficing, first principles,
TRIZ, theory of constraints, and others — a superset of the frameworks in the
table above, including every one graded *none located*.

Two things about it are directly useful.

**Its own README does not claim an accuracy gain.** It states that the evidence
supports structured procedures rather than a guaranteed accuracy gain, and its
audit reports one provisional result — a `thinking-scientific-method` row at
**+4.0 percentage points**, which it flags as falling below its own **+5 point**
utility margin and as directional evidence rather than an accuracy claim. That
is an unusually honest README and it is a useful prior: the one measured number
in the nearest comparable library did not clear its author's own bar.

**The maintainer of this repository installed it and reports it did not help.**
That is one person's experience and is not evidence about the frameworks. It
*is* a data point about form, and it sits at n=28 skills — which is the
number this repository's own one-entry-not-four decision was extrapolating
towards from the published shadowing result at 202 skills
([arXiv:2605.24050](https://arxiv.org/abs/2605.24050)). A 28-skill library that
its installer abandoned is the closest thing to a mid-range observation anyone
has, and Track M4 should treat it as a target to reproduce rather than as
anecdote to discard.

---

## K4 — framework to failure mode

A framework is a skill candidate only if it targets a failure the model actually
makes. This mapping is provisional: the right-hand column is what Track A is
being run to establish, and **three corpora have so far produced three nulls**,
so most rows honestly read *unknown*.

| Framework | Failure it would target | Does this model make that failure? |
|---|---|---|
| Consider-the-opposite | Anchoring on the first framing offered | **Unknown.** Not yet isolated in any corpus here |
| Reference class / outside view | Reasoning from the specific case only | **Unknown** |
| Pre-mortem | Under-weighting failure paths | **Unknown**, and see the measurement warning above |
| Second-order / potential problem analysis | Judging an action on its first effect | **Measured, and absent.** The casefile probe offered 27 trap opportunities across orders 1–3 and none were taken |
| Reversibility / option value | Effort mismatched to irreversibility | **Unknown** |
| Relevance filtering | Folding on-topic but non-governing material into the answer | **Unknown at scale.** The single-turn corpora reached 0.946 and 0.971 and could not discriminate |
| Calibration | Overconfidence in a stated recommendation | **Not measured here at all.** No decision skill in this repository elicits a probability |

The last row is the gap worth naming. Calibration training is the
best-evidenced intervention in the human literature, and it is the only one with
**no counterpart at all** among the four procedures shipped here. Nothing in
`decision-making` asks the model to put a number on its own confidence, so
nothing can be scored for calibration — and `stats/calibration.py` exists,
is property-tested at 100% coverage, and has never been called by anything.

---

## K6 — skill candidates, ranked by evidence

**Rank 1 — elicited confidence, with scoring.** Add a required probability or
threshold to the response contract and score it with the calibration module that
already exists. This is the only candidate whose parent intervention has
medium-to-large controlled effects in humans, it needs no new corpus, and it
turns an unused, fully tested module into an outcome. It also fixes the
measurement problem the pre-mortem finding raises: a number can be scored for
accuracy, whereas a list of considerations can only be counted.

**Rank 2 — consider-the-opposite, as a procedure and not a prompt.** Partial
evidence, an unambiguous operationalisation, and it is the mechanism behind the
council / adversarial-review skill the brief already named. It is also the one
framework whose form maps cleanly onto sub-agents, which makes it the natural
content for Track D.

**Rank 3 — switching conditions.** Already shipped as `fit.md`. It is the
closest thing in the catalogue to *breakeven and value-of-information analysis*,
which is normatively solid even where prescriptive trials are missing, and it is
the procedure most aligned with the founding brief's actual subject — advice
that is correct in general and wrong for this person.

**Not recommended as skill content:** Kepner-Tregoe, WRAP, and OODA. Popular,
comprehensively encoded elsewhere, and carrying no located controlled evidence.
Encoding them would reproduce `cc-thinking-skills` and inherit its result.

**Recommended with a warning:** the pre-mortem. Worth having, but any evaluation
of it must score decision quality and **must not** score the number of risks
named, because that is the only thing its founding study measured.

---

## The audit: are the four shipped procedures traceable?

The programme's done-when condition is that every current skill is either traced
to a documented framework or explicitly marked as invented.

| Procedure | Traces to | Verdict |
|---|---|---|
| `cascade.md` — consequence cascade | Second-order thinking; Kepner-Tregoe's *potential problem analysis*; futures wheel | **Traced.** Named frameworks, no controlled evidence behind any of them |
| `timing.md` — decide or wait | Real-options / option value; reversibility; satisficing vs maximising | **Traced.** Theory-backed, untested as advice |
| `fit.md` — switching conditions | Breakeven analysis and value of information in decision analysis | **Traced**, and it is the strongest trace of the four |
| `ledger.md` — evidence ledger | Nothing in the catalogue | **Invented.** Diagnosticity and relevance ranking are real ideas, but no named decision framework prescribes this procedure |

So: three of four trace to documented frameworks, none of the four traces to a
framework with strong prescriptive evidence, and one is invented outright.

That is a better result than "all four invented" and a worse one than the
scorecard's `UNTESTED` verdict might suggest to a casual reader — `UNTESTED`
says nobody measured it here, and this table adds that for three of the four,
nobody has convincingly measured the underlying idea anywhere either.

`ledger.md` is not thereby wrong. It is the procedure with the least external
support and the most exposure, and it should be first in line behind any
candidate that has a literature.

---

## What is still open in Track K

- **K2 had a second pass on 2026-08-12 and nothing changed.** Kepner-Tregoe,
  WRAP and OODA were searched again with queries restricted to PubMed, PsycNET,
  ScienceDirect, SpringerLink, Wiley, Taylor & Francis, SAGE and Google Scholar.
  **No controlled evaluation of any of the three was found**, so all three rows
  stand at *none located*. What the pass returned instead was consultancy
  marketing for KT, book summaries for WRAP, and simulation/modelling papers for
  OODA (e.g. [arXiv:2203.15502](https://arxiv.org/abs/2203.15502), a red-vs-blue
  game analysis) — none of which evaluates the loop as advice to a human.

  **This is still not a systematic review and must not be described as one.**
  There is no full-text database access here, so the searches hit indexed
  abstracts and public landing pages only. *None located* remains a statement
  about the search. What it now means is *two sessions, the second
  domain-restricted*, which is stronger than it was and weaker than *none
  exists*.

  The productive result of the second pass was finding the **patient decision
  aids** literature, which is now row 12 of the catalogue and is the
  best-evidenced entry in it. Searching for evaluations of named frameworks kept
  returning nothing; searching for evaluations of *structured decision support*
  returned 209 trials. **The frameworks were the wrong search key**, and that is
  worth recording for whoever does the third pass.
- **K4's right-hand column is mostly `unknown`** and stays that way until Track A
  returns. This document should be re-read against those results rather than
  filed.
- **K5, the citation backlog**, is separate and tracked in
  `paper/citations-baseline.txt`.

## Sources checked on 2026-08-12

- Hauenstein, Thomas, Illingworth & Dougherty (2025), *Rethinking the Role of
  Teams and Training in Geopolitical Forecasting*, **Psychological Science** —
  <https://journals.sagepub.com/doi/10.1177/09567976241266481>
- Mellers et al. (2014), Good Judgment Project training results —
  <https://learnmoore.org/papers/Mellers%20et%20al%202014.pdf>
- Morewedge, Yoon, Scopelliti, Symborski, Korris & Kassam (2015), *Debiasing
  Decisions*, **Policy Insights from the Behavioral and Brain Sciences** 2(1)
  129–140 — <https://journals.sagepub.com/doi/abs/10.1177/2372732215600886>
- Mitchell, Russo & Pennington (1989), *Back to the future: temporal perspective
  in the explanation of events*, **JBDM** —
  <https://onlinelibrary.wiley.com/doi/abs/10.1002/bdm.3960020103>
- Collins, *The premortem*, course notes on behavioural economics and corporate
  decision making — <https://corporate.jcx.au/premortem>
- Lord, Lepper & Preston (1984), *Considering the Opposite* —
  <https://www.semanticscholar.org/paper/e71bbae72f8ad78e97c54f5ec88c9af2c70759f2>
- *Reference class forecasting: promises, problems, and a research agenda moving
  forward* (2025) —
  <https://www.tandfonline.com/doi/full/10.1080/09537287.2025.2578708>
  (abstract not retrievable — 403; the summary above is from search results and
  the row is graded accordingly)
- `cc-thinking-skills` — <https://github.com/tjboudreaux/cc-thinking-skills>

## Sources checked on 2026-08-12 (second pass)

- Stacey, Lewis, Smith et al. (2024), *Decision aids for people facing health
  treatment or screening decisions*, **Cochrane Database of Systematic Reviews**
  — 209 RCTs, 107,698 participants —
  <https://pubmed.ncbi.nlm.nih.gov/38284415/>
- Searched and **found nothing evaluative**: Kepner-Tregoe rational process,
  WRAP / Heath & Heath *Decisive* (2013), OODA loop. Queries restricted to
  PubMed, PsycNET, ScienceDirect, SpringerLink, Wiley, Taylor & Francis, SAGE
  and Google Scholar.
- Nearest OODA hit, and it is not an evaluation of the loop as advice:
  *Analysis of OODA Loop based on Adversarial for Complex Game Environments* —
  <https://arxiv.org/abs/2203.15502>
