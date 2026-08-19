# The research programme

**What we are trying to find out:** whether a written skill measurably improves
the decisions an agentic system makes, when that system accumulates context over
turns and delegates work to sub-agents.

That sentence has four load-bearing parts, and the repository has so far tested
none of them together:

| Part | Status |
|---|---|
| a written skill | `decision-making` v0.2.0 ships, four procedures behind a router, `verdict: UNTESTED` |
| measurably improves decisions | three corpora, three nulls, 21/21 scored failures were answer-key errors |
| an agentic system | every call to date is one `claude -p`, no tools, no session |
| accumulates over turns | accumulation has been *rendered*, never *lived* |
| delegates to sub-agents | never attempted |

**Read two other files with this one, and read the first of them before this
one.** They are not appendices; the work is not doable without them.

| | |
|---|---|
| [`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md) | **How the work is done.** Five standing rules, the sub-agent and adversarial-review method, the confirmation requirement, what may run unattended. Every rule is a failure that already happened here. **Read it first.** |
| [`STATUS.md`](STATUS.md) | **Where the work actually stopped.** Track states, runs on record, and the ten measurements caught being broken. This programme says what a track *is*; that file says how far it got. |

**How to read this.** Fifteen tracks in eight parts. Each track states a
question, what would kill it, the experiments inside it, and what "done" means —
point at one and there is enough here to work for days without asking what next.
Track letters (`K`, `A`, `0`…) are **stable identifiers**, referenced from commit
messages and the task list; they are not an order. **The parts are the order**,
and [The tracks](#the-tracks) is the index.

**Two lanes, and they run in parallel.** The *product* lane (Part 2) ships skills
people install and use, and never waits on the research lane. The *research* lane
(Parts 3–6) validates them. A project where the second gates the first produces
a paper with a skill attached; this one is meant to be both. See
[Sequencing](#sequencing).

**This is bigger than one paper.** Tracks C, D and E could each carry one. The
programme is ordered so that the cheapest disconfirming evidence arrives first.

---

## Where we are, honestly

Three corpora were built and all three measured nothing:

| Corpus | Size | Varied | Result |
|---|---|---|---|
| `rel-*` single-turn | ~350 tok | distractor count, position | 0.946; 15/15 zeros were item defects |
| `rel-*` rebuilt | ~700 tok | type-compatible colliding distractors | 0.971 |
| `probe-*` casefiles | ~1,650 tok | trap order 1–3, four consequence kinds, three framings | **27 trap opportunities, zero taken**; admissibility 0.917 |

**A fourth corpus did produce results — and on 2026-08-13 it turned out to be
measuring something else.** The 73-turn trigger set behind every Track L and
Track M number is separable by **turn length alone at AUC 0.850**; a bare *"fire
if ≥ 18 words"* rule scores **0.890** on the version 2 key, against **0.9795**
for the best description arm on that key (`stakes-shown`) and **0.9863** for the
`confidence` arm. So the **nine-point** band
above a ruler is where five reported nulls were competing, and
the corpus never contained the pile of context its `ledger` procedure exists
for. **Track N** rebuilds it; the existing L and M comparisons stay valid
against each other and stop being quotable on their own.

A fifth was planned — the same casefiles padded to 100k tokens. It is not
cancelled, but it is demoted to Track G, and the ~960k characters of library
authoring it needs is **on hold** until Track A reports.

The reason is in the repository's own words. `docs/ACCUMULATION_VENUE.md` says
of the single-call design:

> accumulation is *rendered* rather than lived … What it does not share is error
> compounding across the model's own steps, which this venue cannot measure and
> should not claim to.

That was written before any of this was built, and then everything was built in
the venue it warns about. `docs/FAILURE_TAXONOMY.md` reaches the same place from
the other end: four of Harness-Bench's five failure categories are
**structurally unreachable** in a single-turn, no-tool venue. Tool failures,
grounding gaps, state and continuation issues cannot occur, so no taxonomy built
here generalises to a system that has them.

**What survives and gets reused:** the CLI provider and its isolation findings,
the checkpointed runner, the budget ledger, `stats/` (paired tests, power,
clustering, multiplicity), the calibration and clean-room gates, the placebo
structural guard, `pad.py`, `separability.py`, the 12 casefiles, the
pre-registration and verdict machinery, and `de check`. None of that is wasted.
It was pointed at the wrong axis, which is a different problem from being wrong.

---

## What the literature already settles

Measured elsewhere. We do not re-measure these; we check they hold on our stack
(Track A) and then build on them.

| Finding | Source | Number |
|---|---|---|
| Single-turn → multi-turn accuracy collapse | [LLMs Get Lost In Multi-Turn Conversation](https://arxiv.org/abs/2505.06120) | **−39% average across six generation tasks** (abstract, verbatim). Per-model figures are in Table 1 and are **not** quoted here until read from the table — an earlier draft carried 85.4 → 70.0 for Claude 3.7 Sonnet, which is reportedly the *Math task alone* against a six-task average of 78.0 → 65.6. Venue unverified. |
| The collapse is *unreliability*, not lost aptitude | ibid. | §4.2, read 2026-08-11: aptitude `A^90 = percentile_90(S)` drops **16%** and the paper calls that non-significant; unreliability `U^90_10 = percentile_90(S) − percentile_10(S)` rises **112%**. So roughly seven-eighths of the −39% is scatter. Implemented in `stats/reliability.py`; see Track I. |
| Mechanism: anchor early, then over-weight the latest turn | ibid. | — |
| Multi-agent failure taxonomy | [MAST](https://arxiv.org/abs/2503.13657) | 14 modes, 1600+ traces, κ=0.88 — all three verified. **The category percentages are not in the paper.** An earlier draft carried 41.8 / 36.9 / 21.3; aggregating the per-mode rates in Figure 1 gives roughly **44.3 / 32.4 / 23.5**, and any figure used must be labelled "our aggregation of MAST Figure 1". MAST's traces are 7 frameworks on coding and maths — transfer to a 4-node decision task is an assumption, not a finding. |
| Summarisation is not neutral compression | [When Summaries Distort Decisions](https://arxiv.org/html/2606.29251) | different summarisers move identical evidence toward opposite decisions |
| Recency in ranking | [Do LLMs Favor Recent Content?](https://arxiv.org/abs/2509.11353) | 7 models; up to 95 rank positions |
| Skill *presence* is the dominant term; *form* is not | [Xu & Wu](https://arxiv.org/abs/2605.31408), 30 tasks, 2 models | **+18 to +36pp** from presence; granularity minimal and model-dependent |
| Curated skills help; self-generated ones do not | [SkillsBench](https://arxiv.org/abs/2602.12670), 87 tasks, 8 domains | **+16.6pp** (33.9 → 50.5); focused bundles beat larger ones |
| More skills makes agents worse | [Skill shadowing](https://arxiv.org/abs/2605.24050) | **"up to 21% when scaling from a small set of helpful skills to a 202-skill library"** (abstract, verbatim). Shadowing dominates context overhead, which is "small and indistinguishable from zero". **Regime is 202 skills.** An earlier draft of this table carried "90% → 13.6%", which is this paper *quoting* Gan & Sun 2025 on **tool** selection at **11,100** candidates — not its own finding, and three orders of magnitude from any decision made here. |
| Orchestration is not free | [In-Context Prompting Obsoletes Agent Orchestration **for Procedural Tasks**](https://arxiv.org/abs/2604.27891) | the qualifier is the scope. Reported as *domination*, not parity — failure rates 11.5% vs 24%, 0.5% vs 9%, 5% vs 17%. This is a **stronger** threat to Track D than an earlier draft said. |
| Orchestration prompting is a measured *capability gap* | [PerspectiveGap](https://arxiv.org/abs/2606.08878) | 17.2% average combined pass rate; best model 62.0%; Opus 4.8 singled out for weakness despite strong coding. **It does not show that prompting the orchestrator helps** — it shows models are bad at orchestration prompting. So it is a baseline and an item source for Tracks D and E, not prior art to be out-sharpened. |

**A caution about this table, learned by getting it wrong.** The first draft
collapsed the two skills rows into one, on the assumption that a search result
describing "SkillsBench" was the paper already cited. They are two different real
papers with different scales and different numbers, and the merge turned a
correct figure into an incorrect one — in the product file, in this document, and
in a notebook entry. Both identifiers were resolved against arxiv.org before this
version. **A search-result summary is not the paper**, and two similarly-named
papers on one topic is the normal case. Track K5 makes `de check` enforce it.

One correction to our own records follows from this table and is a task, not a
footnote: the plan in
`docs/superpowers/plans/2026-08-11-long-context-experiment.md` argues repeats are
near-worthless because between-item variance dominates. That is correct for
estimating a **mean** and exactly wrong for estimating **reliability**, which the
multi-turn result says is where the effect lives. See Track I.

---

## The venue map

Two binary axes. The repository has lived entirely in one cell.

```text
                  single call            turns accumulate
                +--------------------+--------------------+
  no sub-agents |  V1                |  V2                |
                |  all work to date  |  the multi-turn    |
                |  3 corpora, 3 null |  venue             |
                +--------------------+--------------------+
  sub-agents    |  V3                |  V4                |
                |  fan out once,     |  the system the    |
                |  aggregate once    |  goal describes    |
                +--------------------+--------------------+
```

V1 is the cell the literature says is *least* likely to show anything. V4 is
what "agentic systems that rely on sub-agents" means. V2 and V3 are the
decompositions that make V4 attributable — without them a V4 result cannot say
whether the damage came from turns or from delegation.

---

## The tracks

| Part | Track | |
|---|---|---|
| **1. What is already known** | `K` | Decision frameworks: the review this project skipped |
|  | `M` | Skill design: how a skill should be built |
| **2. The product** | `S` | Ship the skills |
|  | `L` | Skill variants: which formulation is best |
| **3. The instrument** | `0` | Instrument: multi-turn and delegation |
|  | `N` | The trigger corpus: is the instrument behind `L` and `M` a fair test? |
| **4. Does the failure exist** | `A` | Replication |
|  | `B` | Attribution |
| **5. Where a skill helps** | `C` | Evidence aggregation |
|  | `D` | Delegation quality |
|  | `E` | Handoff fidelity |
| **6. Confirmation** | `F` | End-to-end |
| **7. Cross-cutting** | `G` | Volume (demoted) |
|  | `H` | Tailoring, and life decisions |
|  | `I` | Reliability as a first-class outcome |
| **8. Output** | `J` | Write-up and release |

Track letters are stable identifiers, not an order — they are referenced from
commit messages and the task list. **The parts are the order.**

---

# Part 1 — What is already known

Free, no instrument, and it changes what everything else is testing. Runs first.

### Track K — Decision frameworks: the review this project skipped

**Question.** What is already known about how to make good decisions, and which
of it can be written down as a skill?

**Why it matters.** The founding brief asked for research on *decision making*
before any direction was chosen — "how to make great decisions." Every skill in
this repository was instead invented from first principles by a model. That is
precisely the "skills based on really nothing" the brief warned against, and
SkillsBench's finding that **self-generated skills yield negligible or negative
gains while curated ones yield +16.6pp** is the same warning with a number on it.

This track runs **first**. It is free, it needs no instrument, and it changes
what every other track is testing.

| # | Work |
|---|---|
| K1 | Review the normative and applied decision literature: decision analysis and expected value, reference-class forecasting and base rates, calibration training, pre-mortems, Kepner-Tregoe, WRAP, OODA, satisficing vs maximising, option value and reversibility, dominance and elimination-by-aspects. One page each: what it claims, what evidence supports it, what it costs to run. |
| K2 | Review the *prescriptive* evidence — which of these actually improve human decisions in trials, not which are popular. Many are folklore with a book attached, and the write-up must say which. |
| K3 | Mine [cc-thinking-skills](https://github.com/tjboudreaux/cc-thinking-skills) and comparable prompt libraries: what frameworks are already encoded, in what form, with what evidence behind them. The maintainer installed it and reports it did not help — that is data about form, not about the frameworks. |
| K4 | Map framework → failure mode. A framework is only a skill candidate if it targets a failure an LLM actually makes. Cross against Track A's results. |
| K5 | **Citation audit, and it is worse than a coverage gap.** Counts drift with the glob, so `de check` computes them rather than prose asserting them — measured 2026-08-11: 67 unique identifiers cited across `docs/`, `notebook/`, `skills/` and the product files; `paper/refs.bib` holds 49 entries, 39 carrying arXiv ids. **Nine of the ten papers in the headline literature table are absent from the bibliography** — only 2605.31408 is present. So the bib and the programme cite disjoint literatures. Work: resolve every identifier against arxiv.org; add the missing entries; and make `de check` fail when a number is asserted beside an arXiv id **without a `quote:` field in the bib entry holding the verbatim source sentence.** Presence-checking alone would not have caught any of the three misattributions found on 2026-08-11 — all three cited real papers that existed and said something adjacent. |
| K6 | Output: `docs/DECISION_FRAMEWORKS.md` — the catalogue, with a shortlist of framework-derived skill candidates ranked by evidence strength. |

**Skill candidates already named in the brief and not yet written:** a council /
adversarial-review skill (multiple positions argued before deciding — which is
also the sub-agent architecture question), and a clarify-or-decide skill (when
to ask for more information versus decide under incomplete information).

**Done when** `docs/DECISION_FRAMEWORKS.md` exists and every current skill is
either traced to a documented framework or explicitly marked as invented.

#### First pass done, 2026-08-12 — [`docs/DECISION_FRAMEWORKS.md`](DECISION_FRAMEWORKS.md)

Eleven frameworks catalogued and graded on *prescriptive* evidence rather than
popularity. K2's *none located* rows still want a database search. Four results
bear on what the rest of the programme should build.

**K5 closed on 2026-08-12 and reopened on 2026-08-14, and this paragraph did not notice.** `paper/citations-baseline.txt` carries two identifiers again — `2412.06593` (anchoring) and `2505.02151` (overconfidence), added by the K3/K4 pass with their quotes recorded in [`DECISION_FRAMEWORKS.md`](DECISION_FRAMEWORKS.md) rather than in `paper/refs.bib`, because another session held that file at the time. Neither is in the bibliography today. **A backlog that may only shrink can still be added to**, and the sentence below was true when written and has been false since. What follows is the 2026-08-12 audit as it stood.

All 27 baselined
identifiers were fetched first-hand: 67 cited, 67 in the bibliography, 0
exempted. Of the eight that assert a number, six survive — In-Context Prompting's
three failure-rate pairs, PerspectiveGap's 17.2% and 62.0%, and MAST's 14 modes /
1600+ traces / κ=0.88 are exact. Two do not:

- **Xu & Wu is 30 tasks and 2 models, not "86 tasks, 11 domains".** That was
  SkillsBench's scale, misremembered — and SkillsBench is 87 tasks and 8 domains,
  so both halves were wrong, in the direction that made the smaller paper look
  larger. The **+18 to +36pp** in `CLAUDE.md` and `AGENTS.md` is correct: it is
  the union of the two models' ranges.
- **The 30–50% context-rot figure is not in arXiv:2606.29718.** Not in the
  abstract, not in the PDF, not in any secondary summary. That paper establishes
  *premature termination* — models giving up before the window is full, at a rate
  rising with context length — and its own headline number is a 2.6–4.9% gain
  from filtering. The figure was load-bearing for Track G's entire premise, which
  now says so.

Neither is a defect a presence check finds: both identifiers resolve and both
papers are on the subject they were cited for. And neither was caught by the
gate, because both were **baselined** — which is the finding about the gate. See
[`notebook/2026-08-12-the-baseline-was-where-the-errors-were.md`](../notebook/2026-08-12-the-baseline-was-where-the-errors-were.md).

**The pre-mortem's famous "30%" is a count of reasons generated, not a measure
of decision quality.** Mitchell, Russo & Pennington did not assess the quality
of the reasons. So *a procedure that makes a model produce more considerations
is not thereby a procedure that makes it decide better* — and more
considerations is precisely what a structured skill most easily produces and
what a careless metric most easily rewards. This is the same conflation that
already bit probe-07 from the other direction.

**The best-evidenced framework in the table is under active challenge.**
Hauenstein et al. (2025, *Psychological Science*) re-analysed the Good Judgment
Project under IRT and concluded the training and teaming effects may not be
real. Calibration training is still the strongest candidate *and* is one
re-analysis away from the rest.

**Calibration has no counterpart among the four shipped procedures.** Nothing in
`decision-making` elicits a probability, so nothing can be scored for
calibration — while `stats/calibration.py` is property-tested at 100% coverage
and has never been called. That makes **elicited confidence the top-ranked skill
candidate**: the only one whose parent intervention has medium-to-large
controlled effects in humans, it needs no new corpus, and it converts a list of
considerations into a number that can be scored.

**The audit:** `cascade`, `timing` and `fit` trace to documented frameworks;
`ledger` is invented outright. None of the four traces to a framework with
strong prescriptive evidence.

**And a mid-range shadowing observation fell out of K3.**
[`cc-thinking-skills`](https://github.com/tjboudreaux/cc-thinking-skills) is a
**28-skill** library whose own README declines to claim an accuracy gain and
reports one provisional result below its own utility margin. Track M4 is
extrapolating from 202 skills down towards four; 28 is the only point anyone has
in between, and it comes with an installer who abandoned it.

#### K2 closed, fourth pass, 2026-08-12 → 2026-08-14 — [`docs/DECISION_FRAMEWORKS.md`](DECISION_FRAMEWORKS.md#k1--k2--the-catalogue-graded-by-evidence)

The line above — *"K2's `none located` rows still want a database search"* —
is now stale; a fourth search pass on 2026-08-14 closed it. Kepner-Tregoe,
WRAP and OODA were the three rows still marked `none located` after the
second pass's domain-restricted queries and the third pass's pivot to
LLM-assisted-decision-making trials (neither of which targeted these three
directly). The fourth pass applied the second pass's own lesson —
search for the *construct* behind a brand name, not the name — to all three,
one component at a time rather than as a whole.

**It worked once.** WRAP's "widen your options" letter has real controlled
evidence: Basu & Savani (2017), seven lab experiments, ~2,892 participants,
simultaneous-vs-sequential option presentation raises optimal (dominating-
option) choice 7–16pp, every comparison p ≤ .02; and Dow et al. (2010),
n=33, parallel-vs-serial prototyping raises real click-through and expert
ratings, both p<.05. A correlational field study of 83 real executive
decisions (Hauschildt & Gemünden 1985 — the actual paper behind the
"University of Kiel" study *Decisive*'s own endnotes cite for this chapter)
points the same direction. **WRAP as an integrated four-step process still
has no trial of the whole**, and its other three letters stayed at *none
located* even under construct-level search. K6's ranking now lists "generate
options concurrently" as its own candidate, ahead of consider-the-opposite —
see `docs/DECISION_FRAMEWORKS.md`'s K6 section for why the evidence
comparison favours that order.

**Kepner-Tregoe did not get an equivalent win**, but the decomposition
exercise explains why the gap is not a literature nobody has searched: KT's
"decision analysis" step is the same construct as this table's own
**Decision analysis / MAUT** row, and its "potential problem analysis" step
is the same shape as the **Pre-mortem** row. KT-as-a-named-process has no
trial after four passes because its parts already have grades, not because
nobody has looked at the parts.

**OODA remains `none located` for the loop as advice to a human**, with one
addition: an academic (not consultancy) source, Bryant (2006, *Military
Psychology*), arguing the loop is no longer current with modern cognitive
science — a theoretical critique, not a trial, so the grade does not move.
One further source (Priyanath & Chaminda 2019, a Sri Lankan small-enterprise
survey regressing "business fog" on OODA-strategy use) was found but never
opened past a CAPTCHA wall on any fetch attempt, so no number from it appears
anywhere in this repository, per standing rule 5.

New bibliography entries: `dow2010parallel`, `basusavani2017`,
`hauschildtgemunden1985`, `bryant2006ooda` — all in `paper/refs.bib` with a
`quote` field read from the primary source. Full search log and a caught
near-miss (a fabricated-looking "Johnson et al., 2012" citation surfaced by a
WebSearch summary, never used) are in
`docs/DECISION_FRAMEWORKS.md`'s "What is still open in Track K" and "Sources
checked on 2026-08-14 (K2 fourth pass)" sections.

#### K3 and K4 closed, 2026-08-14 — [`docs/DECISION_FRAMEWORKS.md`](DECISION_FRAMEWORKS.md#k3--what-the-existing-prompt-libraries-encode-and-in-what-form)

**K3 read two more public libraries first-hand beyond `cc-thinking-skills`,
and the form question turned out to be unanswerable as posed, not merely
open.** `thinking-skills` (wanikua, 20 frameworks as slash commands — no
router, explicit invocation only) and `claude-skills-mental-models`
(cyperx84, 98 models bundled into one autonomously-triggered skill plus four
parallel delivery forms) both make **no accuracy claim at all**, joining
cc-thinking-skills' own provisional number that sits below its own bar. So
"is there a form difference between the libraries that help and the ones
that don't" has no library in it that helped — the question needs two
outcome points to compare and the public record supplies one. What the
survey does find is a genuine, checkable form split: explicit slash-command
invocation has no description-discrimination problem *by construction*,
while cc-thinking-skills and cyperx84 both use the same autonomous-
triggering mechanism `decision-making` does, and so are exposed to exactly
what Track M's five experiments spent their budget measuring. A specific,
stated-as-a-prediction reading of M4/M5/M6's own finding (entry count moves
the frontier, not discrimination) says a 28-skill library should fail by
under-firing rather than by mis-routing — untested against any real library,
flagged as a hypothesis rather than filed as a result.

**K4 mapped all eleven catalogued frameworks to a target LLM failure mode and
graded each documented or assumed**, after first checking what Track A has
actually produced rather than assuming coverage: A1's `math` and `actions`
sub-families are the only two closed, neither establishes a bias mechanism
(`math` is a ceiling/no-power null; `actions` is unmeasurable, an instrument
defect), and `database`/A2–A5 have not run. Two new LLM-bias papers were
opened first-hand and are **pending a `paper/refs.bib` entry** (in
`paper/citations-baseline.txt` instead, since K2's session was mid-edit on
`refs.bib`): anchoring (arXiv:2412.06593) and overconfidence
(arXiv:2505.02151). A third, sycophancy (arXiv:2508.02087), was already in
the bibliography.

**Three frameworks fail the excellent-evidence-wrong-target test, and the
sharpest is debiasing training (game/video)** — the single best-evidenced row
in the whole K1/K2 catalogue, evidenced against a six-bias battery of which
only anchoring (one-sixth) has a located LLM study; the other five presuppose
a self-model or social-attribution process a stateless completion has no
clear counterpart for. OODA and satisficing vs maximising fail on mechanism
rather than missing papers — a real-time adversarial tempo loop and a
sustained search-and-regret process both have no analogue in a single
completion, independent of whether anyone ran a trial. A fourth case,
pre-mortem, is excluded on this repo's own casefile-probe measurement (27
trap opportunities, zero taken) rather than an outside evidence gap.
Calibration and consider-the-opposite are the two rows where the human
evidence and the newly-found LLM evidence now agree, strengthening rather
than changing K6's existing top-two ranking.

Full write-up, tables and sources in `docs/DECISION_FRAMEWORKS.md`'s K3 and
K4 sections;
[`notebook/2026-08-14-k3-and-k4-close-form-cannot-explain-an-anecdote-with-no-contrast.md`](../notebook/2026-08-14-k3-and-k4-close-form-cannot-explain-an-anecdote-with-no-contrast.md)
has the full account.

### Track M — Skill design: how a skill should be built

> **The same caveat as Track L, and it lands harder here.** M4, M5, M6 and M6b
> each found no effect on firing accuracy, and the headline reading is that
> structure, count and composition do not change discrimination. On a corpus a
> ruler solves at 0.890 there were about nine points to move — the ruler and
> the best arm on the same key, 0.9795 to 0.9863. **Four nulls with
> nine points of headroom is not the same evidence as four nulls with fifty**,
> and this document reported it as though it were. **Track N** is the fix; the
> M results stand as internally valid comparisons and as nothing more until it
> lands.

**Question.** Given content worth having, what is the right *shape* to put it
in — one skill or several, how long, how bundled, how described?

**Why it matters.** This is a separate question from *what the skill says*, and
the evidence says it may matter more. The repository shipped four decision skills
on 2026-08-11 and consolidated them into one the same day, because the research
below says four overlapping descriptions is a known failure rather than a
richer offering.

| Finding | Source | Bearing |
|---|---|---|
| Skill **presence** dominates; presentation granularity is minimal and model-dependent | [arXiv:2605.31408](https://arxiv.org/abs/2605.31408) — 30 tasks, 2 models | +18–36pp from presence, ~+0.7pp from form |
| **Focused bundles beat larger ones**; self-generated skills ≈0 or negative | [arXiv:2602.12670](https://arxiv.org/abs/2602.12670) — 87 tasks, 8 domains | +16.6pp for curated |
| **Skill shadowing** — more skills makes agents worse | [arXiv:2605.24050](https://arxiv.org/html/2605.24050) | selection >90% under 30 candidates → 13.6% at scale; mechanism is description overlap |
| **Progressive disclosure** — metadata preloaded, body on activation, bundled files only when the body directs | Agent Skills specification | the mechanism that reconciles "one entry" with "focused content" |

Those first two look opposed and are not. *Focused* is about what loads; *one
entry* is about what the router has to choose between. Progressive disclosure
separates the two: one description in context at all times, one procedure file
read when it fires.

| # | Work |
|---|---|
| M1 | Read the Agent Skills specification properly and record what the three disclosure levels cost and buy. |
| M2 | Measure false-fire rate: how often does `decision-making` activate when it should not, and how often does it miss? This is the number the description controls and nothing in this repo measures it yet. |
| M3 | Measure whether routing works: given a decision, does the model read the *right* one of the four files? A router that always reads `ledger.md` is one skill wearing four. |
| M4 | Race one-entry-with-routing against four-separate-skills. **Build the four-skill arm from the *current* procedure files** — the four bodies verbatim, wrapped in four `SKILL.md` files with four descriptions — so that structure and description are the only things that vary. Do **not** use the historical four-skill tree at `9a16b18` as an arm: the prose has moved since, and a race against it would vary structure, content and description at once, which is uninterpretable for a question about structure. This is the experiment that would justify or overturn the one-entry choice, which is currently an extrapolation from a 202-skill regime down to four. |
| M5 | Bundle-size curve: 2 procedures, 4, 8. Where does routing accuracy break? **Run at n=2 on 2026-08-12** — see below. n=8 needs four procedures that do not exist. |
| M6 | **Which** procedures are paired, holding the count fixed. **All three partitions at n=2 run 2026-08-13** — see below. It retired `covers` as a routing measure and left M3 with no estimator on a merged arm. |

**Hypothesis falsifier.** If routing accuracy is at chance, the bundle is a
single long skill with extra steps, and the honest move is to merge the four
procedures into one body or split them back into separately-triggered skills.

#### M4, built and running — 2026-08-12

**The four-skill arm exists and nothing in it was written.**
`decision_evals.unbundle` composes each of the four descriptions mechanically
from the shipped bundle: **condition** and **product** verbatim from that
procedure's router-table row, **opener** and **exclusions** verbatim from the
bundle's own `description` and given to all four unchanged. The four
descriptions are the one description's parts, redistributed.

A test asserts that **no word appears in any composed description that is not
already in the bundle** — one declared exception, the connective *"Produces"*,
which is identical across all four and so cannot differentiate them. That test
is the operational form of M4's own instruction to vary structure and nothing
else, and it fails loudly if prose is ever invented.

`run_triggers.py --arm four` runs it, on its own checkpoint, and refuses
`--confidence` alongside: two changes to the response contract in one run
measure neither. The four-arm answer names a `tool` where the one-arm names a
`procedure`; they are the same four strings and land in the same column, so the
arms score on one metric.

**Scored on firing, not routing**, per
[the power check](../notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).
Routing at 14 items cannot reject at any effect size worth having, so its band
is registered as descriptive with no p-value. Firing has 73 items and 70 of 73
stable across five repeats.

**The band that matters is the false-positive rate.** Four overlapping
descriptions should each look plausible for a wider set of messages than one
scoped description, so shadowing at n=4 should appear as *firing when it should
not* — arm `four`'s FPR above arm `one`'s 0.018. **If it does not rise, the
one-entry choice bought nothing measurable at four descriptions**, and the
copy-paste block in `AGENTS.md` should say so rather than continuing to justify
itself with a 202-skill citation. Prediction registered before the run in
[`notebook/2026-08-12-m4-prediction-one-entry-against-four.md`](../notebook/2026-08-12-m4-prediction-one-entry-against-four.md).

**What it cannot show: anything about n=202.** Four is four. A null is evidence
that shadowing has not begun at four descriptions on this instrument, not
evidence against the published result.

#### M6b, the third partition, completing the set — 2026-08-13

146 calls. Results in
[`results/decision-making/2026-08-13-5ccedb9-m6b-third-partition/`](../results/decision-making/2026-08-13-5ccedb9-m6b-third-partition/),
outcome in
[`notebook/2026-08-13-m6b-the-merged-entry-is-not-the-union-of-its-parts.md`](../notebook/2026-08-13-m6b-the-merged-entry-is-not-the-union-of-its-parts.md).

There are exactly three ways to split four procedures into two entries of two,
and all three are now run. They are word-multiset identical to each other.

| partition | `covers` | firing accuracy | FPR |
|---|---|---|---|
| `ledger-fit` / `cascade-timing` | 0.743 | 0.940 | 0.000 |
| `ledger-cascade` / `fit-timing` | **0.857** | 0.952 | 0.000 |
| `ledger-timing` / `fit-cascade` | **0.571** | 0.945 | 0.009 |

**A 28.6-point range on identical vocabulary**, larger than any effect this
track has looked for, produced entirely by which two procedures share a box.
Firing does not move across any of it: p = 0.893 against M5, p = 0.564 against
M6.

**And the mechanism is stronger than M6 concluded.** `p01` and `p02` are the
cleanest positives in the set and both are labelled `ledger`. Under two
partitions the model names the entry containing `ledger`. Under
`ledger-timing` it unanimously names **`fit-cascade`** — the entry that does not
contain it. Joining `ledger`'s *"a pile of context arrived"* to `timing`'s *"the
direction is settled and the question is when"* produces a sentence that stops
attracting pile-of-context messages. **A merged entry does not inherit its
parts' pull**, which is a fact about how descriptions are read and which neither
M4 nor M5 could have shown, since both varied count rather than composition.

Two published claims are corrected in place as a result. **`covers` is retired**
and M3 — *does routing work* — has no estimator on a merged arm; the honest
options are to score routing only at n=4, or to add a response-contract arm
where the model names a procedure inside the entry it chose. And **the n=2
false-positive floor is low, not structural**: M5's write-up said "floor" on two
arms reading 0.000, and the third reads 0.009.

**Firing has now survived five manipulations** — structure (M4), content (L5),
count (M5), composition twice (M6, M6b) — without moving. That is the M track's
result and it is far better supported than anything about routing.

#### M6, run at n=2 under a second partition — 2026-08-13

146 calls, 73 cases × 2 repeats. Results in
[`results/decision-making/2026-08-13-82b4ab8-m6-pairing/`](../results/decision-making/2026-08-13-82b4ab8-m6-pairing/),
outcome in
[`notebook/2026-08-12-m6-covers-went-up-and-the-measure-does-not-survive-it.md`](../notebook/2026-08-12-m6-covers-went-up-and-the-measure-does-not-survive-it.md).

Same four procedures, same entry count, different partition:
`ledger-cascade` / `fit-timing` against M5's `ledger-fit` / `cascade-timing`. The
two arms are **word-multiset identical**, asserted by test. Five of six
registered bands hit.

**The band that failed was the experiment, and it failed upward.** `covers` was
predicted to drop when the colliding pair was split; it rose, 0.743 → 0.857. The
raw answers show the model did not change its mind — `p06` draws a
*timing*-flavoured answer in both arms, and only the entry boundary moved, so
under one partition it scores 0.2 and under the other 1.0.

**So `covers` is a property of the partition as much as of the model, and it is
retired as a cross-arm routing measure.** It is not comparable across `n`
(chance moves) and not comparable across groupings at the same `n`. M5's 0.743
stands as measured with its interpretation withdrawn; its results README is
amended in place. **M3's question — does routing work — has no surviving
estimator on any merged arm**, and the honest options are to score routing only
at n=4 where entry names are labels, or to change the response contract so the
model names a procedure inside the entry it picked. Neither is free.

**Firing, meanwhile, is a clean null with the best-identified design in the
repository.** 4 of 73 items differ, p = 0.273, on two arms that share every word.
With M4 (structure, p = 0.83), M5 (count, p = 0.50) and L5 (content),
**four independent manipulations of a skill description have now failed to move
how well it discriminates.**

And `p07` — the item the `cascade`/`timing` collision was diagnosed on, named as
the per-item diagnostic before the run — is 1.0 in both arms. Every arm that does
not show the model the router table gets it right. **The collision is a defect of
the table, not of the descriptions**, confirmed from a second direction.

#### M5, run at n=2 — 2026-08-12

365 calls, 73 cases × 5 repeats, one arm. Results in
[`results/decision-making/2026-08-12-c2673c5-m5-two-entries/`](../results/decision-making/2026-08-12-c2673c5-m5-two-entries/),
outcome in
[`notebook/2026-08-12-m5-the-floor-is-at-two-and-the-recall-curve-is-not-monotone.md`](../notebook/2026-08-12-m5-the-floor-is-at-two-and-the-recall-curve-is-not-monotone.md).

| | n=1 | **n=2** | n=4 |
|---|---|---|---|
| firing accuracy | 0.956 | **0.940** | 0.951 |
| false-positive rate | 0.018 | **0.000** | 0.000 |
| recall | 0.878 | **0.756** | 0.800 |

**The conservatism floor is reached at two entries.** M4's zero FPR was
explained structurally — with separate entries, declining to name a tool *is*
declining to fire — and that mechanism is not an artefact of a four-way choice.
Five of six registered bands hit; the miss is recall, and **recall is not
monotone in entry count**, which this run does not claim to explain. n=2 is also
the arm with the worst prose, a confound registered before the run, so the clean
contrast in the curve remains M4's n=1 against n=4.

**Together M4 and M5 say entry count does not change how well this description
selects — only how conservative the selection is.** Three runs on 2026-08-12
(M4 by structure, L5 by content, M5 by count) moved firing accuracy nowhere and
each moved the arm along a precision/recall frontier. **Which point on that
frontier is wanted is a product decision nobody has made**, and it now blocks the
interpretation of every arm this track has run.

**Two instrument defects, both of which produced a plausible number rather than
a crash.** The parser whitelist discarded the offered entry names on the way in
and voided 365 calls; the routing report then graded the offered names on the way
out against names the arm never offered, printing `accuracy 0.000`. Both are
fixed with tests (`decision(text, allowed)`, `routing_is_by_name`). **The lesson
for the rest of the programme is that this harness fails silently and correctly-
shaped**, so every new outcome needs a check that its estimator can, in
principle, return a non-zero value for this arm.

**Reliability, and a design change it earns.** ICC 0.833, 3 of 73 items with any
scatter, and the voided run agrees with the repaired one on 355 of 365 firing
decisions. `repeats_for_reliability` asks for 2 repeats at r=0.9. **Future
trigger arms run 2 repeats, not 5**, and spend the quota on more arms.

#### M2 and M3, first measurement — 2026-08-12

73 cases, two full runs, Haiku, 0 unparseable, 0 isolation failures. Details in
[`notebook/2026-08-12-the-description-fires-well-and-routes-badly.md`](../notebook/2026-08-12-the-description-fires-well-and-routes-badly.md).

| | Run 1 | Run 2 |
|---|---|---|
| precision | 0.941 | 1.000 |
| recall | 0.889 | 0.833 |
| false-positive rate | 0.018 | 0.000 |
| **routing accuracy** | **0.643** | **0.643** |

**M2 is answered and the answer is good.** The description interrupts between 0
and 2% of ordinary turns, across 55 negatives each built to carry a trigger's
surface features. Availability is not this skill's problem.

**M3 is answered less comfortably.** 0.643 against 0.25 chance — clear of the
falsifier above, well short of good. So the bundle is not a single skill wearing
four, and it is not routing reliably either.

#### M2 and M3, five repeats — 2026-08-12, and this supersedes the table above

365 calls (73 × 5), 0 unparseable, 0 isolation failures.
[`notebook/2026-08-12-five-repeats-firing-is-stable-routing-is-not.md`](../notebook/2026-08-12-five-repeats-firing-is-stable-routing-is-not.md).

| | mean | sd | range |
|---|---|---|---|
| precision | **0.942** | 0.039 | 0.889–1.000 |
| recall | **0.878** | 0.025 | 0.833–0.889 |
| false-positive rate | **0.018** | 0.013 | 0.000–0.036 |
| **routing accuracy** | **0.686** | **0.108** | 0.571–0.857 |

**Firing is stable: 70 of 73 items return the identical verdict five times
running.** ICC 0.741, so `repeats_for_reliability` asks for **4 repeats** at
r = 0.9. One is not enough for anything on this instrument.

**Routing is not stable, and the earlier reading was wrong.** The two single runs
above both landed on 0.643 and I took that agreement as the aggregate holding
still. At sd = 0.108 over five repeats it was a coincidence: repeat 0 of this run
alone reads 0.857. So *"per-item verdicts move while the aggregate is stable"* is
true of firing and false of routing.

**The cascade/timing confusion survives repeats, in two specific items.** Seven
of fourteen labelled items route correctly 5/5. Two are stably wrong: `p06` is
never routed to `fit` in five attempts and `p07` reaches `cascade` once, both
drifting to `timing` — and `p07` had already been repaired to remove its time
words, so the repair was not the issue. Those two are router-table defects. The
rest of any single run's confusion list is noise.

**Recall is 0.878 or 0.988 depending on two labels of mine.** `x-n21` (*"The disk
is at 99%. Do we need to act?"*) and `x-n22` (*"The build is green. Can I
deploy?"*) fire **0/5** each and are the set's only misses; excluding them takes
recall to 0.988 with precision and FPR unchanged. Of the five cases promoted out
of `evidence-ledger`'s negatives, three fire 5/5 and these two fire 0/5, with
nothing in between — so this is a **stable disagreement, not a coin flip**. Both
readings still stand (the promotion was wrong, or the router widened on paper and
not in behaviour) and repeats cannot separate them. It is a label decision, and it
goes where every other label in this repository goes: three-instance blind
adjudication under N3's protocol, with the answer key versioned and the movement
reported. **Not to a casting vote.** Routing a disputed label to a person is what
left these two unresolved from the day they were found, and a label one person
settles is a label no reader can check.

**What it points at.** The cost of consolidation is not that the skill fires
wrongly — it is that, having fired, it reads the wrong file. 0.942 against 0.686.
That is a different failure from shadowing and a cheaper one: it lives in the
router table, not in the description. **M4 should therefore be re-scoped**, since
racing one-entry against four-skills was framed around a firing-precision cost
that this measurement does not find.

`fired but routed nowhere` appeared in every run and is now named in `SKILL.md`
as an abort condition (v0.2.1).

---

# Part 2 — The product

Ships continuously and is never gated on the research. This is half the point of the repository.

### Track S — Ship the skills

**Question.** What can the maintainer, and anyone else, install and use today?

**Why it matters.** This project is dual-purpose: skills someone actually uses,
*and* a paper. The programme as first written was a research programme with a
skill attached — no skill improved until Track C/D/E, months out, and it produced
exactly one new skill almost by accident. That ratio is wrong and it is the
mistake this track corrects.

**The decoupling that makes it possible.** `SCORECARD.md` already says a verdict
governs the *public claim*, not whether a skill is usable. `UNTESTED` blocks
entry to `plugin/skills/`; it does not block `cp -r skills/* .claude/skills/`.
Shipping honestly-labelled unproven skills and shipping unproven skills *as
proven* are different acts, and only the second is the thing the evidence rule
exists to prevent.

**Runs from day one, in parallel, never downstream.** Every research finding is
harvested into a skill revision the week it arrives, not at the end.

**Shipped state as of 2026-08-11: one skill, `decision-making` v0.2.0,
`verdict: UNTESTED`**, with four procedures behind a router. Not four skills —
they were consolidated the same day they were written (see Track M).

| # | Procedure / work | Status |
|---|---|---|
| S1 | `ledger.md` — a pile arrived and it is unclear what the answer turns on | in the bundle |
| S2 | `fit.md` — is this generic advice right for *this* person | in the bundle |
| S3 | `cascade.md` — what it sets in motion, and which option it spends | in the bundle |
| S4 | `timing.md` — the undo price, the real deadline, what waiting buys | in the bundle |
| S5 | a council / adversarial-review procedure — argue the positions before deciding | named in the founding brief, not written |
| S6 | a clarify-or-decide procedure — ask for more, or decide under incomplete information | named in the founding brief, not written |
| S7 | Re-derive each of the above from Track K's catalogue, or mark it invented | **done 2026-08-12.** `cascade`, `timing` and `fit` trace to named frameworks; `ledger` is invented outright. None of the four traces to a framework with strong prescriptive evidence — see [`DECISION_FRAMEWORKS.md`](DECISION_FRAMEWORKS.md) |
| S8 | **A retirement rule.** "Daily use is evidence" currently has no failure condition — no threshold at which use retires a procedure. Evidence that cannot come out negative is not evidence. | **done 2026-08-12.** 14 consecutive days disabled → `WITHDRAWN`, clocked from a dated `notebook/` line. Blocks the plugin through the existing promotion gate, not a second mechanism, so it operates rather than being written down |
| S9 | **`ledger.md` is first in line for replacement.** It is the one procedure with no external support, and Track K6 ranks *elicited confidence* above it on evidence — the only candidate whose parent intervention has medium-to-large controlled effects in humans | opened by K |

**The maintainer's daily use is evidence.** Not publishable as a headline, and
the fastest signal available: a skill that fires when it should not, or produces
a worse answer than working directly, is worth knowing about in a day rather
than in a quarter. The copy-paste block in `AGENTS.md` closes on an explicit
invitation to report exactly that.

**Honest caveat carried on all four:** `consequence-cascade` has the weakest
prior of the set. The casefile probe found the model already doing order-1
through order-3 consequence reasoning unprompted — 27 trap opportunities, zero
taken, and it computed a leverage ratio nobody asked for. That was professional
casefiles with an option menu, not personal decisions, so the skill is still
worth having and worth testing. But if any of the four comes back `NULL`, this
is the one to bet on.

### Track L — Skill variants: which formulation is best

> **Every L result on disk was measured on a corpus a ruler solves at 0.890.**
> L5 and L7 are internally valid — all arms saw identical items — but the
> movable range above a word count was about nine points on the version 2 key,
> ruler 0.890 against 0.9795 to 0.9863 for the best arm, so an L null is
> ambiguous between "phrasing does not matter" and "there was nowhere to move".
> **Track N** is rebuilding the corpus; nothing here is retired and nothing here
> may be quoted without that sentence attached.

**Question.** For one target failure, which way of writing the skill works best?

**Why it matters.** The brief asked to test "different types of skills and
variations, finding the most optimal one." The current design compares one skill
against control, placebo and chain-of-thought — it never compares **skill A
against skill B for the same job**. Without that there is no basis for saying a
skill is good, only that it is better than nothing.

**The axes are not equally worth running, and the priors say so.** Attaching a
published prior to each one before spending anything is the difference between a
horse race and a fishing trip.

| # | Variant axis | Example | Published prior | Weight |
|---|---|---|---|---|
| **L6** | **Revision against failure traces** — run it, read what went wrong, edit the skill, re-run | one skill, five rounds | **+25.6pp** (36.05 → 61.63), 3 benchmarks, 5 LLMs — [arXiv:2606.01139](https://arxiv.org/abs/2606.01139) | **primary** |
| **L1** | **Framework** — genuinely different content for the same failure | a ledger vs a pre-mortem vs a reference class | curated vs **no-skill** +16.6pp (33.9→50.5); self-generated **−1.3pp vs no-skill** — [2602.12670](https://arxiv.org/abs/2602.12670). Two separate contrasts; an earlier draft merged them into one. | **primary** |
| **L5** | **Trigger breadth** — the description, which controls whether it fires at all | narrow vs broad, scored on false-fire *and* miss rate | availability is the dominant term, **+18–36pp** — [2605.31408](https://arxiv.org/abs/2605.31408) | **primary** |
| L2 | Length | 150 vs 400 vs 1,200 words | ~+0.7pp, intervals crossing zero | confirm the null |
| L3 | Output shape | block template vs prose vs checklist | same | confirm the null |
| L4 | Framing | procedure vs diagnostic vs question list | same | confirm the null |

**L2–L4 are phrasing, and phrasing is the axis the evidence says does not move.**
They are not dropped — replicating a published null on our own stack is cheap and
is a legitimate result — but they are pre-registered *as* null confirmations, run
last, and they may not be reported as a search for an effect. Spending a horse
race on prose polish is how a project looks busy while measuring nothing.

**L6 now has its first real candidate, from measurement rather than invention —
2026-08-12.** The five-repeat trigger run found two items the router gets
*stably* wrong, and reading them turned up a defect legible in `SKILL.md`'s own
table without any data: **`cascade` claims "the order" and `timing` claims
"when"**, which in ordinary use are one idea. Only `timing`'s row carries the
clause that separates them — *the direction is settled* — and `cascade`'s does
not say that its own direction is still open.

The variant to test is therefore stated and **not applied**: give the `cascade`
row the direction-not-yet-settled clause. Editing it now would tune the skill
against the measurement that motivated it, which is the whole reason L6 has a
holdout. See
[`notebook/2026-08-12-cascade-and-timing-collide-in-the-table.md`](../notebook/2026-08-12-cascade-and-timing-collide-in-the-table.md).

**A second instance landed the same day, and two instances make it one
hypothesis.** `p03` (*"six people replied in the group chat and they disagree —
what should I actually do?"*, labelled `ledger`) routes to `fit` three times in
five. `fit` needs a fact about the person that would overturn the generic answer
and `p03` states none, so unlike `p06` this is a genuine failure — and its cause
is that **the pile is made of advice, and "advice" appears in exactly one row of
the table, `fit`'s.** `ledger`'s row says "a pile of context" and never says what
a pile can be made of, though `SKILL.md`'s `description` field lists the kinds.

So both table defects are **the same mechanism: a row matched on a word it
contains rather than on the condition it states.** That is the L6 candidate —
one edit class, two instances, neither applied. See
[`notebook/2026-08-12-p03-and-the-only-row-that-says-advice.md`](../notebook/2026-08-12-p03-and-the-only-row-that-says-advice.md).

One caution carried with it: **`p06`, the other stably-wrong item, is at least
partly a trigger-set defect** — `fit` and `cascade` both read correctly off the
table for that case, and the model picked `cascade`. Allowing multiple acceptable
routes is a set-wide decision over all fourteen routed cases, made by someone who
has not seen which two failed, and it must happen before any L6 round is scored
on routing.

**And routing cannot be the outcome any of these are scored on — measured
2026-08-12, and it is an instrument falsifier, not a disappointment.** The
trigger set has **14 routed items**. Pairwise across the five repeats, the
discordance floor from sampling noise alone is `p_discordant` = **0.157** — about
2.2 items flip between two runs of the *identical* skill. `required_pairs` then
asks for **95 pairs** to detect a 10pp routing effect, and refuses a 20pp one as
arithmetically impossible at that discordance.

The exact test is harsher than that approximation. One-sided McNemar needs **5
discordant pairs all one way**; under the null the expected count is 2.2 and the
real size of the test is **0.0015** against a nominal 0.05. Ceiling check: a
*perfect* variant — routes all fourteen right, breaks nothing — clears the bar in
**three of five** draws, power ≈ 0.6 on the best intervention that could exist.

So: **score L5 on firing** (73 items, precision 0.942 / recall 0.878 / FPR 0.018,
70 of 73 stable across five repeats — a real instrument, and trigger breadth is
about firing anyway), **or grow the routed stratum to ~95 items and price that
before authoring item fifteen**, or report routing descriptively with intervals
and no p-value. What may not happen is a Track L round scored on 14-item routing
and written up as a null: that null would be a property of the sample size and
would be indistinguishable from a finding about skills. Working:
[`notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md`](../notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).

**L6 is the one that changes what the skills are.** SkillRevise describes
expert-authored skills as costly and misaligned with how models actually execute,
and one-shot LLM-generated skills as "syntactically correct but behaviorally
weak." Every skill in this repository is one-shot LLM-generated. The loop is:
run on held-out items → read every failure → make one execution-anchored edit →
re-run → keep it only if it verifies.

**The overfitting guard is not optional here.** Revising a skill against traces
from the items you then evaluate it on is fitting the test set, and it would
produce a large, real, meaningless number. Revision traces come from one item
pool and the verdict comes from another, drawn before revision starts and not
looked at until the end.

**L1 draws its candidates from Track K6**, not from invention. That is the whole
point of doing the frameworks review first.

**Winner's curse is the standing threat, and `stats/` has nothing for it.**
`stats/multiplicity.py` contains exactly one function, `benjamini_hochberg`. BH
controls the false discovery *rate* among rejections; it does nothing about the
magnitude bias of a selected maximum. There is no shrinkage, no selective or
conditional inference, and no holdout re-estimation helper anywhere in `stats/`.
An earlier draft cited the module here as though it addressed this, which
misrepresented readiness in the programme's most active track.

**Holdout re-estimation is therefore the only control in this design, and the
holdout estimate — not the discovery-set estimate — is the number reported.**

**Done when** one target failure has ≥3 authored variants plus a revision loop, a
pre-registered comparison, and a winner replicated on a holdout it never saw.

---

# Part 3 — The instrument

Blocks the measurement. Does not block the product.

**Two instruments, and only one of them was ever audited.** Track 0 is the
transport — can this stack run a multi-turn, delegating system under control.
Track N is the *corpus* that every Track L and Track M number was computed
from, and until 2026-08-13 nobody had asked whether it was a fair test. It was
not.

### Track 0 — Instrument

**Question.** Can this stack run a genuinely multi-turn, genuinely delegating
system under experimental control?

**Why it matters.** `ISOLATION_FLAGS` in
`evals/src/decision_evals/providers/claude_code.py` hard-codes `--tools ""` and
`--no-session-persistence`. The first blocks sub-agent dispatch; the second
blocks session resume. **Nothing in V2, V3 or V4 can run today.** This is the
same class of blocker as the argv-length defect: the instrument cannot produce
the phenomenon, and it would have been discovered after authoring the corpus.

And the flags are not incidental. `notebook/2026-08-10-isolation-canary.md`
records that a `CLAUDE.md` planted in the working directory is injected **even
when the system prompt is fully replaced**; `--setting-sources ""` is the flag
that actually stops it. Opening `--tools` reopens paths that were closed for a
measured reason. Every relaxation needs its own canary.

**The design call: scripted orchestration, not the real Task tool.** The
orchestrator is our Python code driving separate isolated `claude -p` calls, one
per node. We then control exactly what each node sees, can ablate or substitute
a sub-agent report, and keep `--tools ""` at every node. The real Task tool is
ecologically truer and experimentally useless — we could not hold anything
fixed. It returns in Track F as a validity check, not as the instrument.

> **Resolved 2026-08-11, before any of this ran — and the falsifier was wrong.**
> Multi-turn already works, **under the full isolation stack with no flag
> relaxed**. `--no-session-persistence` blocks `--resume`, which is
> cross-process; it does not block multi-turn, because with `--input-format
> stream-json` turns go to one live subprocess's stdin and context carries
> in-process. Reproduced: turn 3 recalled a codeword from turn 1 with an
> unrelated turn between, `input_tokens` 179 → 410 → 513.
>
> **The original falsifier read "`cache_read` must climb turn over turn".
> `cache_read` was 0 on every turn while context demonstrably carried** —
> caching is a billing optimisation, not a transcript mechanism, and short turns
> never reach the threshold. Run as written, 0.1 would have declared a healthy
> venue dead.
>
> So **Track 0 is not a hard gate for A1 and A2.** The transport is ~80 lines of
> `Popen` plus JSONL. Track A's real prerequisite is the MDE calculation, not
> the harness. Full record in
> [`notebook/2026-08-11-multi-turn-already-worked.md`](../notebook/2026-08-11-multi-turn-already-worked.md).

**Instrument falsifier, corrected.** Prior turns are in context iff
**`input_tokens` climbs monotonically** *and* a behavioural recall check passes.
Two independent signals, because the first can be explained by a longer question
and the second by a lucky guess. `cache_read` is not evidence either way.

| # | Experiment | Cost |
|---|---|---|
| 0.1 | ~~Session-resume canary~~ **Done, and folded in.** `Conversation` now lives in `providers/claude_code.py` beside the single-shot path, sharing `build_command` so the isolation flags cannot be forgotten on the streaming form either. Re-verified through the shipped class: `input_tokens` 179 → 334 → 422, turn 3 recalled the turn-1 codeword with an unrelated turn between, `cache_read` **0 on every turn**. The transport is unit-tested against a fake process at 100% line+branch, and `tests/integration/test_multiturn.py` (marked `llm`) asserts the corrected falsifier against a live model. | done |
| 0.2 | **Done 2026-08-12.** `decision_evals/orchestrator.py`, 100% line+branch. 1 orchestrator + 3 sub-agents, fan out once and aggregate once, per-node `NodeRecord`s carrying node/parent/operation. The split is scripted rather than model-chosen, because a model-chosen split varies between arms. `Dispatch.transform` is the seam the module exists for — pass through is the control, drop is an ablation, substitute is Track B's attribution — and the record stores *both* what the node said and what the parent read, because when they differ that difference is the manipulation. Ran live: 8 nodes across 2 trees, $0.039 notional. | done |
| 0.3 | **Done 2026-08-12, and it forced a design decision.** The isolation receipt is the `system`/`init` event, which only `--output-format stream-json` emits — the single-shot JSON form gives no receipt at all. So asserting isolation *at every node* forces the streaming transport everywhere, including single-turn nodes. The alternative was asserting at the root and assuming for the leaves, which is the assumption a delegation experiment least deserves. 8/8 receipts asserted; fresh cwd per node, because the auto-memory path is keyed on it. | done |
| 0.4 | **Done 2026-08-12.** `summarise()` reports cost, prompt tokens and wall-clock over a call *tree*, split **by node name**. Measured on the smoke run: orchestrator $0.023 against $0.005–0.006 per sub-agent — the root costs about four times any leaf because it reads all three reports. A single total cannot tell "delegation is expensive" from "aggregation is expensive", and those are different design problems. Wall-clock is summed, not maximised, and says so: the tree runs serially. | done |
| **0.7** | **New, and it is a rule rather than an experiment.** The first ablation this repository ran was confounded: the second pass re-dispatched every sub-agent, and `customer-impact` answered on the control pass and declined on the ablation pass *from the identical prompt*. Two things differed and nothing in the run could say which caused the orchestrator's change. **An ablation must hold the surviving inputs fixed**, or it measures resampling — Track I's scatter finding arriving somewhere new. Pinning is the same `transform` seam handed a constant. Applies to every track from B onward. See [`notebook/2026-08-12-the-ablation-that-measured-resampling.md`](../notebook/2026-08-12-the-ablation-that-measured-resampling.md). **Implemented 2026-08-13** — `pin`, `pinned_dispatches`, `ablation_is_identified` and `run_ablation`, at 100% line+branch. The rule had sat in this table for a day with nothing enforcing it, so the only thing standing between the next ablation and the last one was somebody remembering. Two things the implementation forced that the rule as written did not say: pinning takes **what the parent read**, not what the node said, or a control that was itself transforming would move two things at once; and the guard reads **node names**, not pinned reports, because an ablated node and a node that was never dispatched both drop out of the pinned set and those are different runs — the second is a fan-out manipulation wearing an ablation's name. | free |
| 0.5 | **Done.** `decision_evals/telemetry.py` pins the vocabulary at `open-telemetry/semantic-conventions-genai@8d3e4a0`, every name read from the registry at that commit; `RunRecord` gains `schema_version`, `conversation_id`, `node_name`, `node_id`, `parent_node_id`, `turn_index`. The fields **default** rather than being required — a single `claude -p` call genuinely has no parent and no turn index, so `None` is true of it, and `schema_version` defaults to 1 so an older record describes itself accurately. Every published `RunRecord` checkpoint still loads, asserted in the test suite; an unknown column still fails loudly. Two things the earlier note got right and one it did not: `gen_ai.agent.name` is **absent from the inference-span document** and present in the **registry**, so checking one page would have wrongly retired it. Original text follows. — `RunRecord` gains node identity, parent, turn index, and a trace id — **using OpenTelemetry GenAI semantic-convention attribute names** (`gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.conversation.id`, `gen_ai.usage.*`, `gen_ai.evaluation.*`), with parent/child span nesting giving node parent and turn index for free. `opentelemetry-api` + `opentelemetry-sdk` is a 4-package pure-Python Apache-2.0 closure; `ConsoleSpanExporter(out=file)` opens **no socket**. Hand-rolling a trace schema when a vendor-neutral one exists is a real weakness, and MAST-style attribution needs structured traces regardless. **Adopt the names, not the package's constants**: the spec is status `Development`, zero releases, Schema URL `TODO`, and has already renamed `gen_ai.system` → `gen_ai.provider.name`. Hardcode the strings in one module, pin the SDK, record the semconv commit SHA per run. Old records must fail loudly, not silently vanish. | free |
| 0.6 | **Done.** `InitReceipt` + `parse_init_receipt` + `assert_isolated()`, raising `IsolationError` when the CLI declares tools or picks a skill off disk. Rule 2 satisfied: run against a known-good live call first, where it passes — receipt reads `tools=()`, `skills=()`, `apiKeySource='none'`, **6 agents declared, 0 memory paths**. Declared agents deliberately do *not* fail the gate: they are latent under `--tools ""` and only go live when it is relaxed. Original text follows. — **Assert on the `system/init` event**, which `--output-format stream-json --verbose` emits as a free machine-readable isolation receipt: `tools`, `skills`, `agents`, `memory_paths`, `apiKeySource`. Strictly better evidence than inferring isolation from a response. Two channels it advertises are **latent, not active** — with `--tools ""` there is no Task tool to reach the six declared agents and no memory tool to write the auto-memory path (tested: nothing was created). **Both go live the moment `--tools` is relaxed, which Track F plans.** The auto-memory path is keyed on the working directory, so it would become a cross-run state channel that a checkpointed run cannot see. Mitigation: fresh cwd per run, plus an assertion on `memory_paths`. `--bare` would disable auto-memory and is unusable — it forces `ANTHROPIC_API_KEY` auth and never reads OAuth. | free |

**Depends on.** Nothing. This is the gate on everything else.

**Done when.** A canary trace shows turn-*n* context containing turn-1 content
by token accounting; a 4-node scripted run completes with per-node records; the
isolation canary passes at every node; `de check` green.

---

### Track N — The trigger corpus

**Full design:
[`docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md`](superpowers/plans/2026-08-13-trigger-corpus-v3.md).**

**Question.** Every Track L and Track M result was computed from one corpus of
73 turns. Is that corpus a test of the thing it claims to test?

**Why it matters — and this is not a hypothetical.** Asked for the first time
on 2026-08-13, prompted by the maintainer pointing out that nothing in the set
was longer than 25 words while real users write paragraphs. Two defects, and
they are different problems that arrived together:

- **Coverage.** No turn exceeded 23 words; 46 of 73 were ten words or fewer.
  The `ledger` procedure exists for *"a pile of context ending in a question
  about what to do"* and the corpus had never contained a pile — the longest
  positive was one sentence *describing* one.
- **A shortcut.** Positives ran at a median of 18 words and negatives at 8, so
  turn length alone separated the labels at **AUC 0.850** and a bare *"fire if
  ≥ 18 words"* rule scored **0.890 accuracy with no model involved** on the
  version 2 key. The best description arm on that key is `stakes-shown` at
  **0.9795** and the highest firing accuracy on record is `confidence` at
  **0.9863**; on the version 1 key the same ruler scores 0.877, against
  `no-opener` at 0.967 and `confidence` at 0.973. **Nine points either way, and
  the two pairs must not be crossed** — 0.956, the figure this paragraph carried until 2026-08-13, is
  the `full` arm at version 1 quoted against a version 2 ruler.

**So every result in Tracks L and M was competing for about nine points over a
ruler**, and the through-line those tracks report — five manipulations of a
description, none of which moved discrimination — now carries a second reading
that cannot be dismissed: **there was nine points of room, and five nulls is
what a ceiling looks like.** Neither reading is established. Both are reported
until this track closes.

Fixing coverage without fixing the shortcut makes the shortcut worse — adding
long positives to a set where long already means positive widens the gap — so
both are fixed by one construction, the **matched triple**: one positive and two
negatives written to the same length, sharing a body in the long bands and
differing only in what is asked of it.

Version 3 also stops being a single-question instrument. The same 120 calls per
arm answer length, domain, stakes, ask form and negative kind, because each is a
column on the case rather than a property the set happens to have.

| # | Experiment | Cost | State |
|---|---|---|---|
| **N1** | **The shortcut battery.** `corpus.py`: eight trivial features, each held to a **two-sided** [0.40, 0.60] — the one-sided `MAX_LENGTH_SEPARABILITY = 0.70` it replaces would have passed a set at AUC 0.05, which is solved by a ruler pointing the other way — plus a depth-2 stump over all eight capped at 0.70, because a battery of singles misses interactions. | free | **done** |
| **N2** | **Author the corpus.** 40 triples, 120 items, four bands (≤25 / 40–90 / 200–400 / 900–1500 words), 1:2 positive-to-negative in **every** band so the ratio holds across the set and not only inside it. ~11k words of authored bodies. | free | **done** — authored at 40 triples / 120 items and since grown by two merges to **87 triples, 261 items** (S 24, M 24, L 22, XL 17), every gate in N1 passing. See below |
| **N3** | **Blind label adjudication.** Three independent instances label each turn with no access to mine. **Pre-registered kill: >20% label movement retires the corpus.** 21 of 21 scored failures across three corpora were the answer key, and a 1,200-word turn has fifty times the surface for that. | 360 calls | **done 2026-08-14** across two continuations, 261 of 261 items, 3 judges each, 0 unparseable. **Movement 12/261 = 0.046 against the 0.20 kill — the corpus survives by a factor of four**, and no band is near it (0.042 s, 0.042 m, 0.045 l, 0.059 xl). Fleiss kappa 0.862. **The 12 moves are unapplied and cannot be applied as written** — see below |
| **N4** | **The human-authored holdout.** The threat no gate above touches: a model is authoring the corpus that will evaluate a model. Blind adjudication does not fix it — the adjudicator is also a model. **~20 turns are drawn from a public human-written corpus** that clears the outside-data rule; the labels stay with N3's blind adjudication. Every arm is reported twice. **Orderings agree → the threat is bounded by a measurement. Orderings disagree → the model-authored corpus is decoration, and we know it.** | ~120 calls | **source survey done 2026-08-18** — eight candidates, four clear redistribution, OASST1 recommended. No step waits on a person; see below |
| **N5** | **Realism.** The descriptive machine probe — do turns read as real, or as authored-for-a-benchmark — plus, once N4 lands, a **forced choice against N4's human turns**: one corpus turn beside one human turn, blind judge, which was sent by a person. That is the instrument `realism_probe.py`'s own docstring names as the sharper one and declines to build for want of real messages, and it carries the known-good case standing rule 2 demands, because which item is human is a fact rather than a taste. 0.5 will mean indistinguishable; above it, the corpus reads as authored and the probe will say by how much. **It will still not be a gate** — it retires nothing on its own, and it has not run. | 86 done + ~86 to come | **descriptive half done 2026-08-18** — 86 calls, 0 unparseable, `composed` rate **0.302 [0.215, 0.406]** against a registered prediction of >0.50, which is falsified. Band and em-dash presence are the same partition of the sample, so no band claim survives. [Run](../results/decision-making/2026-08-18-0ee75d4-n5-realism-probe/README.md). **The 10% human audit is retired** — its own sheet recorded that the only auditor available authored the corpus, so it was a self-assessment wearing the words *ground truth*. See below |
| **N6** | **Confirmatory re-run** — `full`, `stakes-shown`, `opener-only` × 258 × 2 repeats. Two repeats, not five: ICC 0.83–0.85 (Track I). | 1,548 calls | **done 2026-08-18**, 0 unparseable. Q1 **met** (+0.0976 [0.0459, 0.1493]), Q2's sign holds (+0.0079), Q3 **met** — `ledger` worst-routed in all three arms — **Q4 falsified**: `settled` is at the bottom, not the top. All three arms clear the 0.7054 stump. [Run](../results/decision-making/2026-08-18-e632659-n6-confirmatory/README.md) |
| **N7** | **Descriptive re-run** — the remaining three `--description` arms (`no-exclusions`, `no-opener`, `stakes-named`; N6 already ran `full`, `stakes-shown` and `opener-only`) × 258 × 2 repeats. | 1,548 calls | **done 2026-08-19**, 0 unparseable. All six arms now on one corpus. **Only 1 of 5 predictions met cleanly.** The top three arms — `no-opener`, `stakes-shown`, `full` — are **not distinguishable** at n=258 (p=0.86, p=0.35); deleting the exclusion list is the one change that measurably matters (−11pp accuracy, 3× FPR). **L7's band 4 still fails** — no arm reaches FPR ≤ 0.06 — and this run's own prediction 5 substituted thresholds and would have reported it broken. [Run](../results/decision-making/2026-08-19-d52236a-n7-remaining-arms/README.md) |
| **N8** | **Stamp the model into the record.** `--model` is a CLI argument with a default and the tier survives only as prose in a hand-written README; the verdict records carry `case`, `fired`, `route`, `repeat` and no model at all. Same shape as the label-versioning defect: a run parameter that changes every number, recoverable only from someone remembering to type it. Needs a comparability guard beside `label_versions_comparable`. | free | **done 2026-08-13.** `run_triggers.py` writes `model`; `models_comparable` refuses a comparison spanning tiers, and `compare` raises on it. **An absent `model` is unknown, not the default** — `--model` could have been passed and the record would look identical, so filling in `haiku` would be standing rule 1's invented parameter. Two unstamped arms therefore still compare (no published comparison is retroactively voided) and a stamped arm against an unstamped one is refused, which is the transition where the risk is real |
| **N9** | **Proxy validation.** `run_triggers.py`'s own module docstring names the gap and this table has never scheduled the measurement: the harness shows the model a description and one message and asks whether it would fire; deployment shows it a description *appended to* a longer system prompt, mid-session, after other turns. N9 takes the first, cheapest step — the same 258-item corpus, key v4, `haiku`, the `full` description, sent through `Conversation(in_situ=True)` (`--append-system-prompt`) instead of `--system-prompt`, one turn, against the existing **N6** `full` arm as the unmodified reference. Conversation length is held at one turn on both sides — see below for why. | 516 calls | |

#### N9 — the proxy the module docstring names, and the cheapest step toward closing it

**The gap, verified rather than taken on report.** `scripts/run_triggers.py`'s
module docstring says plainly what the instrument is not: *"The real harness
decides differently: the description sits among other skills, in a longer
context, with the model mid-task. This measures the description's
discriminative content, not the deployed firing rate."* The word "proxy"
appears nowhere else in this document — `grep -n "proxy"
docs/RESEARCH_PROGRAMME.md` matches only that docstring's own paraphrase above
— and no row before this one schedules the measurement that would bound the
gap. Every number in Track L, every number in Track M, and all three of N6's
arms were measured in a venue where the description **is** the entire system
prompt and the turn under test is the only message sent.

**What is compared.** The same four constants N6 already fixed — 258 items,
key v4, `haiku`, the `full` description — run once more with the description
appended rather than substituted, against N6's own `full` arm (accuracy
0.9360, precision 0.8601, recall 0.9651, FPR 0.0785;
[`results/decision-making/2026-08-18-e632659-n6-confirmatory/`](../results/decision-making/2026-08-18-e632659-n6-confirmatory/README.md))
as the reference. No new reference run is needed; N6 already paid for it.

**The two mechanisms this reuses already exist, checked by reading the code
rather than by trusting this description of it:**

1. **A secure multi-turn transport, already used by every trigger call.**
   `Conversation` (`evals/src/decision_evals/providers/claude_code.py`, line
   511). Its class docstring states the isolation finding directly:
   `--no-session-persistence` (one of `ISOLATION_FLAGS`, line 54) blocks
   `--resume`, which is cross-process, but does not block turns sent
   in-process over `--input-format stream-json` — multi-turn needed no
   isolation flag relaxed to work. `run_triggers.py`'s `ask()` function
   already opens a `Conversation` at line 212 and sends exactly one turn at
   line 214.
2. **An `in_situ` mechanism, already a first-class parameter.**
   `build_command` (same file, `def build_command` at line 163) sets
   `prompt_flag = "--append-system-prompt" if in_situ else "--system-prompt"`
   at line 209; `Conversation.__init__` (line 547) already accepts and
   threads through `in_situ: bool = False`. `evals/src/decision_evals/solvers/arms.py`
   already treats `in_situ` as a fifth named arm (`ARM_NAMES`, line 40) for
   Track G, deliberately ordered last because "it answers a different
   question from the other four: not 'does the skill help' but 'does it
   still help when it is not the only thing in the prompt'" (lines 37–39).
   `run_triggers.py` has no such arm and no `--in-situ` flag. Wiring one
   through is the only new code this row needs — both machines it calls
   already run.

**Call count, derived rather than invented.** One new arm (`full`, in_situ) ×
258 items × 2 repeats = **516 calls**. Two repeats, not five, for the reason
N6 and N7 already used rather than a fresh choice here: Track I measured ICC
0.83–0.85 for this instrument.

**The risk in the design, named rather than absorbed silently.** An `in_situ`
arm that *also* inserts turns before the one under test confounds two changes
in a single comparison — prompt **position** (appended vs substituted) and
conversation **length** (one turn vs several) — and a divergence from N6 could
then be credited to either. N9 holds conversation length fixed at one turn on
both sides and moves only position. That is a deliberate scope cut, not an
oversight: how many prior turns, what they should discuss, and how they
should be authored is exactly the kind of unmeasured parameter standing rule
1 forbids inventing. The docstring's "longer context, mid-task" clause names
a real second gap but supplies no number for turn count or content, and
authoring that corpus is separate work this row does not fund.

**What a large divergence would mean, and what it would not.** If N9's arm
lands outside N6's `full` arm's interval, every published trigger number —
all of Track L, all of Track M, N6's three arms — is a statement about a
venue nobody deploys in, measuring the description's discriminative content
in a position it never occupies at inference time. That is not a hypothetical
tacked on for effect; it is the stated reason this row exists. A null
result — N9 inside N6's interval — says position alone does not move firing
behaviour, which is one of the two gaps the docstring names, not both.

**What N9 does not settle.** It moves the venue one step closer to
deployment and no further. After it runs, the residual gap is exactly the
half of the docstring's sentence N9 does not touch: "the turn under test
arrives after other turns" — a real session has other skills present, a task
already under way, and a context this corpus does not supply. Closing that
half needs its own row, its own derived turn count, and its own check against
N9's position-only result so the two effects are not read as one.

#### N4's route changed on 2026-08-18, and the threat it controls did not

**The maintainer will not hand-author the ~20 holdout turns.** Recorded as a
decision rather than left as a blocked row, because a blocked row that nobody
retires is how a track stalls for weeks — N4 has sat on
[`STATUS.md`](STATUS.md)'s maintainer list since it was written and no turn has
ever been supplied.

So N4 **will** be built from a public human-written corpus instead. What it
controls for is the *provenance of the text* — the three leaks Track N has
closed so far were authoring habits (a word-count ruler at 0.890, an `open`-view
opener at 0.779, and `_shared_body` cutting at a space), all of them in text a
model wrote, all of them hunted by gates a model built. Human text breaks that
loop whether or not the human is the maintainer.

The labels **will** come from N3's three-judge blind adjudication, unchanged.
That is a real weakening and it is stated rather than argued away: the
adjudicator is still a model. But the contamination being controlled sits in the
*text*, not the key, so a model-labelled human corpus is materially less
circular than a model-authored one — and it is reachable without a person.

Two things this costs, both accepted:

- **The distribution shifts.** Forum posts are written for strangers and chat
  logs were sent to a different assistant. The holdout therefore asks *does this
  generalise off our own writing*, not *does this work on the maintainer's
  inbox*. The first is the question worth answering; the second was never quite
  what N4 asked either.
- **A source must clear the outside-data rule before anything is fetched** —
  free, redistributable, sampled and read, digest pinned. See
  [`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md). Nothing here has a
  budget, so a source that costs money is not a source.

**A label-free fallback exists if no corpus clears that bar.** N4's payload is
whether the arms *rank the same* on human text as on authored text; a weaker
version measures only how much the arms disagree **with each other** on
unlabelled human turns. Divergence on authored text and convergence on human
text would be a finding, and it needs no key at all.

#### N3 closed, and the freeze it feeds cannot be executed as written — 2026-08-18

**261 of 261 items blind-adjudicated, 3 judges each, 12 moves, movement
0.046 against the 0.20 kill.** Derived independently three times — two
sub-agents told nothing of each other, then by hand — and agreeing on every
figure. The corpus survives the kill by a factor of four and survives it in
every band separately (0.042 s, 0.042 m, 0.045 l, 0.059 xl), which is stated
because a pooled rate has hidden a per-stratum problem here before.

**All 12 moves break the one-positive-two-negative invariant, and that is a
fact about the design rather than about the labels.** In each of the 10
negative → positive moves, the same adjudication **unanimously** reconfirmed
that triple's *existing* positive — 10 of 10, all three judges — so the judges
say both members should fire, and applying the move yields two positives. The 2 positive → negative
moves land in triples whose other members were unanimously negative, yielding
none. `corpus._check_triples` reports this as **structural**, which carries the
`_UNBASELINEABLE` key by design: there is no version of the freeze that lands
and defers this.

**The mechanism: the corpus is authored in triples and adjudicated in items.**
A judge sees one turn and is asked whether that turn should fire. Nothing in
the protocol knows the turn shares a body with two others and is competing for
a single positive slot. So a 2-of-3 vote against the key does not say *this
label is wrong*; it says **the authored contrast did not land**. The v3 plan's
rule — *"2-of-3 against me → I rewrite the turn or move the label, and say
which"* — assumes both branches are always available. On a matched-triple
corpus **"move the label" sometimes is not**, and the plan does not say so
because the case had not arisen when it was written.

It had arisen once, and was read as a local accident. `docs/DECISIONS.md`'s
2026-08-14 entry reverted `l12n1`, `l17n2` and `xl15n2` rather than promoting
them, "because accepting would have put two positives in a one-positive-per-
triple design." That was the general case seen through one opener edit.

**The freeze is therefore open, and the choice is not neutral.** Retiring the
12 affected triples is mechanical and invents nothing, and it deletes exactly
the 36 items three blind readers found hardest — making the corpus easier
rather than better, and incidentally closing two of the three open shortcut
findings. A corpus edit that turns gates green is the mechanism this repository
has already named as the source of four generations of leak. Rewriting the
disputed ask and re-adjudicating preserves difficulty and costs authoring plus
another adjudication round. Demoting the existing positive is ruled out: no
judge supports it. Relaxing the invariant is a corpus redesign, not a version
bump.

**The remedy is rewrite-and-re-adjudicate, and an adversarial review settled
it against the cheaper option.** Retirement of the 12 triples was the obvious
move and is the wrong branch of the plan's own rule, which sends a 2-of-3
disagreement to *rewrite the turn or move the label* and reserves retirement
for a *three-way split*. All 12 disputes are clean 3-0 or 2-1 majorities, and
**with three binary judges a three-way split cannot occur at all** — so the
retirement branch has been unreachable since the protocol was written, which is
why it read as available. Moving the label is structurally blocked, so
rewriting is the only live branch. Three checks, each re-derived:

- **Retirement biases the survivors along the axes v3 exists to test.** It
  removes implicit asks at 18.5% and embedded at 18.2% against explicit at
  7.9% — the two forms added because v2 was saturated with *"should I"* — and
  23.5% of technical and 22.2% of money against **0%** of relationships.
- **It costs N6 the power the long-band merge just bought.** SE 0.0346 →
  0.0374, MDE **0.0970 → 0.1047**, power at the registered 0.10 threshold
  **0.823 → 0.763**. The MDE crosses the effect the test is built around.
- **It closes two of the three open shortcut findings, and that is a side
  effect rather than a reason.** The retired triples are in fact *less* extreme
  than the survivors on both features (0.229 vs 0.283, 0.292 vs 0.393), so this
  is not disguised feature-retuning — but citing a gate closure as a merit is
  the reasoning this repository has named as the source of four generations of
  leak.

Retirement is held for any of the 12 that still fails to reach a key-consistent
majority after a genuine rewrite. **And if it is ever used, movement must be
reported cumulatively over the corpus's whole history**, because pruning the
disputed items is otherwise a way of making the 20% kill structurally unable to
fire again.

**Resolved 2026-08-18, and the corpus survived it.** All 12 asks were rewritten
to one rule — *an inert ask asks about one thing, and may not put two options in
a frame that invites ranking them* — diagnosed from `s02n2` and applied by agents
never shown a judge's rationale, since a rewrite aimed at a stated objection is
tuned to that judge. On blind re-adjudication, **36 calls, 0 unparseable, 11 of
12 now agree with the key** against a registered band of 8. Judge agreement on
those twelve went **0.611 → 1.000** pairwise and corpus-wide movement **0.046 →
0.004**. `l15` is retired whole, being the one item still disputed after the
single round the protocol allowed, so the corpus stands at **258 items, 86
triples** — s 24, m 24, l 21, xl 17.

**No label moved and no version was bumped**, so no published number is
affected. No gate crossed, `imperative_opener` did not pick up the *"Restate…"*
rewrites, and the two `sentence_count` findings ended *stronger* at 3.18σ —
after a mid-round correction, because three rewrites had changed their turn's
sentence count and pushed that habit under its 3.0 gate, which would have had a
label fix quietly closing two open shortcut findings.

**One prediction registered before the round was wrong**: the two positive →
negative items were expected to be harder and possibly to retire. Both fixed on
the first attempt.

Working:
[`notebook/2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md`](../notebook/2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md).

#### N5's human audit is retired, and the plan has no step left that waits on a person — 2026-08-18

**The 10% audit was a gate on a person and it is removed**, on a maintainer
instruction to take every such gate out of the plans. It is not being removed
because nobody filled it in, and that distinction is the whole of the
justification. The audit sheet's own standing caveat said it: *"The only auditor
available authored this corpus, so these answers are a self-assessment."* A
self-assessment by the author is not the ground truth the sheet's header claimed
for it, so the audit was mislabelled from the day it was written, and **138
items were added under it** without the sheet ever being regenerated — it was
still addressed to a 120-item corpus at answer key v3, against 258 items at v4.

**What replaces it is stronger than what it replaced, and only because N4
moved.** `realism_probe.py`'s docstring already names the sharper instrument and
declined to build it: a forced choice cancels the judge's base rate, which is the
one quantity a single-item realism verdict cannot recover, and it was unavailable
because — in that docstring's words as they stood at `90f1653`, this morning's
commit — *"There is no human-written comparison set in this repository."* N4 no
longer waits for a person to write one — it draws on a public human-written
corpus — so the comparison set becomes reachable, and with it the known-good case
standing rule 2 demands before any falsifier may fail anything: **which turn is
human is a fact on the record, not a taste**. N5 therefore now depends on N4
rather than on anybody's calendar.

**What this costs, stated rather than glossed.** The retired audit was the only
place in the programme where a reader outside the model loop was ever going to
look at this corpus. Nothing replaces that, and the forced choice does not: its
judge is a model too. What it gains is a ground truth the audit never had. The
corpus remains model-authored, model-adjudicated and model-probed, and Track N4's
row is the only thing that moves the provenance of the *text* out of that loop.

**And no output from `scripts/realism_probe.py` exists on disk**, so the
descriptive half of N5 has not run either. That is a call budget, not a gate.

**And a naming collision worth fixing before it reaches a paper.** Commit
`30012d9` and its notebook entry call themselves "N7". They are a continuation
of **N3** — closing the L/XL adjudication gap — and not the N7 in the table
above, which is the descriptive re-run of the remaining three arms and has never
started.

---

**Depends on.** Nothing. Like Track 0, it is a gate rather than a question.

**Blocks.** Every *future* claim from Tracks L and M, and it retro-qualifies
every past one. It does **not** block Track S — the skill ships and is usable
either way, which is the distinction `SCORECARD.md` exists to draw.

**Falsifiers.**

1. **N1's gates cannot be met** without writing turns nobody would send. Then
   the length–label correlation is intrinsic to the task — long messages really
   are more often decisions — and that is a finding to report rather than
   engineer around. The corpus ships with the honest AUC and every claim is
   conditional on it.
2. **N3 moves more than 20% of labels.** Corpus retired, not reported.
3. **N4's orderings disagree.** Every trigger result in this repository becomes
   a statement about model-authored text and nothing else.
4. **Accuracy is flat across bands and the arms re-order anyway.** Then the
   trigger instrument does not have the resolution for the questions Tracks L
   and M have been asking it, which is a larger result than any of them.

**Done when.** All eight features and the stump are inside their gates on a
120-item set; adjudication is under the kill threshold; the holdout exists and
has been run; N6 is published with its bands registered first; and every
`results/**/README.md` carries the ruler caveat.

#### N2 closed, 2026-08-13 — and the gates it closed against had never run

**120 items, 40 positives, 80 negatives, four bands.** The XL band is 7 triples
of 900–1,500 words in which the positive and its two negatives share a
byte-identical body and differ only in the closing ask, so `ledger` has for the
first time been shown the pile of context it exists for. Working:
[`notebook/2026-08-13-the-xl-band-and-two-rulers-that-cancelled.md`](../notebook/2026-08-13-the-xl-band-and-two-rulers-that-cancelled.md).

**The corpus was outside every gate written for it.** `check_trigger_sets` globs
`datasets/triggers/*.yaml`; the bands are one directory down. The shortcut
battery, the stump and the balance rules could not see any of the 99 items
already authored, and `de check` was green on every commit that added them. That
is the **third** tested-with-no-caller defect on record — after `triggers` at
100% coverage and `prereg.py`'s unreachable refusals — and the first found
before anything had been published from it. A `_check_drafts` step now holds a
corpus under construction to the live rules **without making it live**, because
the entry point may not move before adjudication.

**And a pooled AUC of 0.5 is not evidence that a band is clean.** `word_count`
read 0.511 over the whole set while the L band sat at **0.769** and the XL band
at **0.301** — one authoring habit seen from two sides, cancelling in the pool.
Length inside a band is available at inference, so this was a real shortcut and
not a bookkeeping curiosity. The depth-2 stump caught it at a lift of 0.117
against a 0.100 cap; the per-feature battery could not, by construction. After
re-mixing the ask lengths the set reads:

| | | | |
|---|---|---|---|
| says_should_i 0.575 | first_person_rate 0.554 | word_count 0.511 | question_marks 0.500 |
| imperative_opener 0.494 | paste_cues 0.489 | char_count 0.481 | type_token_ratio 0.471 |

stump 0.750 against a majority baseline of 0.667 — **lift 0.083, cap 0.100.**

**Per-band separability is reported and not gated, and the reason is arithmetic
rather than convenience.** At 7 positives and 14 negatives an XL-band AUC rests
on 98 pairs, a null standard error of ~0.137 under independent sampling, so a
[0.40, 0.60] gate would fire on a clean corpus roughly half the time — eight
times per band. The matched-triple construction makes the true null variance
smaller than that by an unknown amount, so the figure bounds the noise rather
than measuring it, and whether a per-band gate is affordable is **open**. What
is not open is that the pooled number alone was hiding two rulers.

**Neighbouring work, not duplicated here.** `provenance.py`, `wiring.py` and
`de index` — gates on whether a published run has a prediction that predates it
— were built in a parallel session and are the same class of fix aimed at the
write-up rather than the corpus.

---

# Part 4 — Does the failure exist

Before asking whether a skill fixes a failure, show the failure happens here. Three corpora were built without this.

### Track A — Replication

**Question.** Do the failures the literature reports actually happen on our
stack, our models, our tasks?

**Why it matters.** This is the repository's cardinal error, stated plainly:
three corpora were built to fix a failure that was never shown to exist here. A
skill cannot help with a failure that does not occur. Track A is cheap — roughly
1,200 calls, a few hours of wall clock — and it can kill or redirect everything
downstream before a single document is authored.

**Run this first.** It is the highest-value work in the programme.

**Instrument falsifier.** If A1–A5 are all flat, the failures do not exist at
this scale on this stack, and the programme needs a harder task family before
any skill work. That is a real finding and it gets written up as one.

| # | Experiment | Design | Prediction registered before |
|---|---|---|---|
| A1 | **Multi-turn drop** | **Adopted, and now vendored.** `microsoft/lost_in_conversation` (MIT), corpus CDLA-Permissive-2.0, pinned at commit `c865793` with a SHA-256 in `datasets/vendor/lost_in_conversation.lock.json`; `de fetch` downloads it and the loader refuses anything that does not match. This removes the activity with this repo's worst record — three discarded corpora, 21/21 key errors. Still needed: a `model_claude_code.py` shim; their only backend is OpenAI. **Three things measured on retrieval, each contradicting something we had written down** — see below. | yes |
| A2 | **Recency over-weighting** | Decisive fact placed at first / middle / last turn, total turns fixed. Flat means no recency effect here and Track C changes shape. | yes |
| A3 | **Handoff loss** | Sub-agent reads the documents and reports; orchestrator decides from the report alone vs from raw documents. The gap is compression loss. Also: *which* facts survive. | yes |
| A4 | **Does delegating even help?** | One agent with everything vs orchestrator + sub-agents, same task. If single wins, the skill's job changes from "delegate better" to "know when not to delegate." | yes |
| A5 | **Reliability** | *k* repeats per item at each venue. Measure the scatter, not the mean. | yes |

**What the vendored corpus actually contains**, measured 2026-08-11 by
`decision_evals.corpora.shard_summary` rather than read off the paper:

| We had written | The file says |
|---|---|
| 600 instructions | **627 records** — the filename is wrong, not the count |
| 7 task families | **6 present**: actions, code, data2text, database, math, summary. The seventh, `translation`, is a separate file (`data/sharded_translation.json`) |
| sharded "across ~6 turns", flagged as invented | **mean 5.97, median 6, range 3–12.** The invented figure was *right* — and it was still invented. It is now measured |
| skip `code` (Unix-only eval) | leaves **527 records**, mean 5.78, median 6 |

The turn-count spread is the part that changes a design. A corpus running 3 to 12
turns is not a fixed-length instrument, so any per-item comparison has to carry
turn count as a covariate rather than assume it away — and A2, which holds total
turns fixed while moving a fact, cannot simply reuse A1's items.

**A1 pilot, 2026-08-12 — and forty of its sixty records were void.** The run
completed cleanly: 30 pairs, 190 generations, 0 failures, all 30 conversations
accumulating. But `database` was asked for SQL with no schema in the prompt and
`actions` was asked to call a function with none offered. Both families carry
that material in the corpus (`schema_sql`, `function`); the runner never rendered
it. Those twenty items were unanswerable, not hard.

It survived a first reading because the traces are good. Asked which countries'
TV channels air a Todd Casey cartoon, with no database, the model said it has no
access to TV listings and suggested IMDb — the right answer to the question it
was actually asked.

Three things follow, and they outlast the pilot:

- **`math` was not "the only family with a mechanical key".** It was the only
  family whose task was fully delivered; a word problem carries its own numbers.
  The `p_discordant` = 0.10 measured on it stands, and it is still near ceiling.
- **A run can be clean and void at once.** Every instrument check passed. What
  was missing was a check that the task arrived, which is now `TASK_CONTEXT_FIELD`
  — declared per family, no default, refusing to run an item that is declared to
  need context and does not carry it.
- **`ShardedRecord` stores the system prompt verbatim.** The defect lived there
  and nothing in the record showed it.

**Neither `database` nor `actions` can be graded here even repaired.** Spider's
metric is execution accuracy and the databases are not vendored; BFCL's is an AST
match on a parsed call, and nothing in the run asks for a parseable call.
Substituting for either is authoring a key while pointing at a vendored one, so
they report format compliance and, for `database`, a string match labelled as a
lower bound.

**Re-run 2026-08-12, and it closes `math` as an A1 venue.** 30 pairs, 180
generations, 0 failures, $1.45. The repair is visible in one number: `database`
went from prose about TV listings to **10/10 producing SQL in both conditions**.

| Family | Measure | Discordant | full | sharded |
|---|---|---|---|---|
| `math` | correct (GSM8K key) | **0/10** | 10 | 10 |
| `database` | produced SQL | 0/10 | 10 | 10 |
| `actions` | named the required function | **2/10** | 10 | 8 |

**`p_discordant` on `math` is 0.000, so the family has no power at any sample
size** — McNemar's effect is bounded by the discordant share. The first pilot's
0.10 was one item, and repeating the identical condition got that item right;
`math` per-item agreement across the two runs is 19/20, so the aggregate was
stable and the single disagreement *was* the entire signal. Third appearance of
the aptitude-versus-unreliability split ([arXiv:2505.06120](https://arxiv.org/abs/2505.06120)),
and the cleanest.

**The signal is in `actions`, which inverts the earlier reading.** Two of ten
pairs discordant on function-naming, both in the paper's direction (p = 0.25
exact at n=10, nowhere near significant, and the only non-zero discordance the
pilot produced). `math` looked like the family to build on only because it was
the one whose task had been delivered; with all three delivered it is the one
with nothing left to measure.

So A1 cannot be sized from `math`. Three options, and the choice is a corpus
decision: size on `actions` function-naming and accept a capability floor as the
outcome; vendor the spider databases so execution accuracy becomes available;
or find harder `math` items, since GSM8K at 10/10 is not the hard end of
anything. **None of this says the multi-turn effect is absent — it says this
venue cannot currently see it**, which is a Phase 0 result rather than a finding.

**`actions` closed too, later on 2026-08-12, after three runs and 1,105
generations. Option 1 above is dead.** Not for lack of an effect — because
**no object is comparable across the arms.** The scorer reads `final_response`;
`full` has one turn and `sharded` has five to eleven. Four different objects were
tried on the same 100 responses and each gave a different verdict:

| what is scored | `full` | `sharded` |
|---|---|---|
| final response, no closing turn | 45 named | 23 |
| final response, **with** closing turn | 50 named / 47 AST | **4 / 1** |
| the **last shard's** reply | 50 / 47 | 27 / 13 |
| naming anywhere in the conversation | 50 | ~49 |
| the union of all calls emitted | — | breaks BFCL's bijection: 8 calls against a reference of 4 |

**The number that ends it: of the 23 sharded conversations whose last shard
carried no parseable call, 23 had emitted one earlier.** No exceptions. The arm
is not failing to call — it calls, correctly formatted, and then keeps talking.

And **no wording escapes it.** *"Give your final answer now, complete and
self-contained"* means *the calls* in an arm that has said nothing yet and *a
summary of the results* in an arm that made them four turns ago. Both arms get
both instructions and resolve them differently because they are in different
states, and the state difference **is** the independent variable. An instruction
demanding the calls be repeated at the end would measure whether a model restates
finished work.

So the two closures are different and must not be merged in the write-up:
**`math` answers the question and says no** (`p_discordant` = 0.000, a real
measurement); **`actions` says the question cannot be put this way** (the
measurement does not exist).

**What survives is instrument, and it is not nothing.** `--call-format` took the
single-turn arm from 18/43 parsed to **50/50 named and 47/50 matching on BFCL's
own published AST metric**, so the harness can grade this family — it just cannot
pair it. Two guards now encode the defect rather than a memory of it:
`final_responses_comparable` refuses a run with no closing instruction, and
`actions_report` refuses the paired naming comparison without a call contract.
Both defects had already produced a publishable-looking false replication
(45/50 against 23/50, discordance 24-to-2 in the predicted direction).

**Option 2 is now the leading one and nothing in it waits on a person**:
vendoring the spider databases means downloading a third-party dataset, which is
precisely what [`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md)'s
outside-data rule is for — free, redistributable, licence read first-hand, a
sample read for personal information, a digest pinned in
`datasets/vendor/*.lock.json`. **The rule is the decision procedure, so
executing it is the approval.** Four steps, all free, and a source failing any
one of them is not vendored. Whether Spider's own terms clear that bar is not
asserted here, and reading them is the first of the four.

**One consequence for the rest of Track A, and it is good news.** A1 compares a
**one-turn** arm against a **six-turn** arm, which is why no object is
comparable. **A2 does not**: it holds total turns fixed and moves a decisive fact
between positions, so both arms have the same turn count, the same shards and the
same place for the answer to land. A2 is immune to the defect that closed A1 by
construction, and it is the next A-track experiment for that reason as well as
its own.

What A2 still needs is **headroom**, which is option 3 rather than option 2. A
position effect cannot be seen at 10/10, and `math` sits at 10/10 in both arms —
so A2 inherits A1's need for harder items even though it escapes A1's
measurement problem. Those are two separate blockers and only one of them has
been solved.

Also recorded: prediction 7 of that run was **unscoreable as written**. It asked
for `p_discordant` on families that have no correctness measure here, which was
known when it was registered. A pre-registered band needs the estimator named,
not only the number.

**Sample sizes and detectable effects, consolidated — 2026-08-18.** Three of
these numbers already exist, scattered across two notebook entries, a CLI
table (`de power`) and the prose above; two of the five experiments have never
had a pair count, a repeat count or a design effect written down anywhere in
this repository — grep of the whole tree comes up empty for both. The table
below calls `stats/power.required_pairs` and `minimum_detectable_effect`
directly rather than re-deriving the arithmetic by hand, and it counts the
corpus on disk rather than trusting the figures already written about it — the
same discipline the 527-to-315 correction above cost an hour to learn.

**The `design_effect ≈ 2.0` used throughout the A-track prose above is not
derived — it is `cluster.py`'s own worked-example number** (six variants per
template, ICC 0.2), carried in as a stand-in. Nothing in the vendored corpus
has the structure to compute an ICC from: the only groupable unit is task
family, and three to six families is too few groups for
`intraclass_correlation` to return anything stable. So it has never been
replaced with a measured value the way Track N replaced its own placeholder
with `design_effect(m=3, icc=0.315) = 1.63`. What would replace it: an ICC
computed from repeated draws within one task family, which needs the same
repeat measurements A5 is supposed to produce.

| # | Paired unit | Pairs available (counted off the corpus, not read from prose) | Repeats | Design effect | MDE @ 80% power | Status |
|---|---|---|---|---|---|---|
| **A1** | one instruction (`task_id`), full-condition response vs. sharded-condition response | **315** — `actions` 105 + `database` 107 + `math` 103, each carrying that family's own full-setting field (`fully_specified_question` or `question`). Counted directly off `sharded_instructions_600.json`; matches the pre-registered figure | **1.** No repeats were run; no ICC has ever been measured for this venue | **assumed 2.0** (see above) | **5.4–9.9pp** unadjusted, **7.6–13.9pp** at the assumed design effect, `p_discordant` swept 0.15–0.50 | **closed** — and not by reaching that MDE. `math`'s observed `p_discordant` is 0.000, so `minimum_detectable_effect` raises `ValueError`: no effect is detectable at any `n`. `database` and `actions` closed on instrument grounds (no gradable object, no comparable object across arms), so the run that actually closed them used 10 pairs per family, not 315 |
| **A2** | one instruction at a fixed shard count, decisive fact at first / middle / last turn | **212**, counted directly off `sharded_instructions_600.json` for the 6-turn stratum across the five non-`code` families. **Not 233** — the figure this document and `cli.py`'s `POWER_ROWS` both carry for "the largest shard-count stratum" still includes `code`, which every other line in Track A treats as ungradable on this stack. Restricted further to the three families A1 actually established as gradable (`actions` / `database` / `math`), the largest single-turn stratum is **103** (4 turns), not 212 and not 233 | **never written down** | assumed 2.0, same as A1, never computed | **6.6–12.0pp** unadjusted / **9.3–16.9pp** at DE=2.0, `n`=212; **9.4–17.1pp** / **13.1–24.0pp** at `n`=103 if restricted to gradable families | not yet run. Which of the three pairwise position comparisons is the primary registered test is also not stated anywhere |
| **A3** | undecided — provisionally, one document set handed to a sub-agent, orchestrator decides from the report vs. from the raw documents | **never written down.** No corpus exists; A3 needs Track 0's multi-agent transport, which needs `--tools ""` relaxed and has not run | never written down | never computed | **not computable** — there is no `n` to hand either power function | not run |
| **A4** | undecided — provisionally, one task, single agent with everything vs. orchestrator + sub-agents | **never written down**, same Track 0 dependency as A3 | never written down | never computed | **not computable** | not run |
| **A5** | *k* repeats per item, at whichever of A1–A4's venues it runs against | n/a — A5 is a repeat-count question, not a pair-count question | **never written down.** `stats/reliability.repeats_for_reliability(icc, target)` is exactly the function this needs, but it takes an ICC as input, and no venue in A1–A4 has ever had a repeat measured to compute one from | n/a | **not computable** — the repeat count needs the ICC and the ICC needs the pilot A5 itself would be | not run |

Confirmed against
[`notebook/2026-08-11-twelve-items-could-not-have-found-anything.md`](../notebook/2026-08-11-twelve-items-could-not-have-found-anything.md),
whose own line already said it: *"A3, A4 and A5 have no item count yet because
they have no corpus yet."* Nothing built since has changed that, and this table
is the first place it is said about repeats and the design effect too, not
only about item counts.

**Depends on.** Track 0.

**Done when.** Five notebook entries, each with its numeric prediction written
*before* the run, and one table saying which effects reproduce and how big they
are on our stack.

### Track B — Attribution

**Question.** When the system produces a bad decision, which node caused it?

**Why it matters.** Twenty-one of twenty-one scored failures so far were answer
key errors, not model errors. A multi-node trace multiplies the surface area for
that mistake. Nothing downstream can be believed without this.

MAST is the citable prior, confirmed or refuted against our traces — the same
bottom-up method `docs/FAILURE_TAXONOMY.md` already uses, which is what caught
the false "appeals to real-world considerations" signal.

| # | Experiment |
|---|---|
| B1 | Port MAST's 14 modes into a codebook mapped onto our trace schema; mark which are unreachable in each venue, as `FAILURE_TAXONOMY.md` already does. |
| B2 | Per-node scorer: a trace is scored at every node, not only at the final answer. |
| B3 | Blind adjudication extended to multi-node traces. The pre-registered **>20% key-amendment kill** carries over unchanged. |
| B4 | Inter-annotator agreement on our own coding, reported. MAST reports κ=0.88; a number below that is a result about our codebook. |

**Depends on.** Track 0 for trace structure; runs alongside Track A on its
traces.

**Done when.** Every Track A failure has been read and coded, agreement is
reported, and the amendment rate is under 20%.

---

# Part 5 — Where a skill helps

Parallel once Part 4 reports. Each is independently pointable.

### Track C — Evidence aggregation

**The orchestrator's judgment over what came back.** Skill under test:
`evidence-ledger`. This is the user's "last message" complaint stated as a
measurable claim, and it is the failure the skill already claims to fix.

| # | Experiment | The failure it catches |
|---|---|---|
| C1 | **Contradicting reports.** Two sub-agents return conflicting findings, one early, one late. | Silently taking the later one instead of naming the conflict |
| C2 | **Supersession, lived.** An early turn states a value; a later turn revises it. The design in `ACCUMULATION_VENUE.md`, finally in a venue that can host it. | First-number-grabbing |
| C3 | **Confident and wrong.** A hedged report is right, a confident report is wrong. | Weighting confidence over evidence |
| C4 | **Aggregation dose.** 1 → 3 → 7 sub-agent reports. | Where aggregation breaks |
| C5 | **Skill placement.** Orchestrator on / off, crossed with Track E. | Where a skill has to be installed to work |

**Hypothesis falsifier.** Skill and control degrade identically → skills do not
buy robustness to accumulation. That is a *more* informative negative than "no
degradation exists" and is reported as one.

**Depends on.** Tracks 0, A2, A3, B.

### Track D — Delegation quality

**What to ask, who to ask, and whether to believe the answer.** MAST's largest
category (41.8% design and specification, 21.3% verification and termination).
`evidence-ledger` does not address this; a new skill is needed. Working name:
`scope-and-verify`, shipping `verdict: UNTESTED`.

| # | Experiment |
|---|---|
| D1 | Brief quality: score the orchestrator's briefs against a rubric, correlate with sub-agent output quality. Establishes that the brief is on the causal path before any skill is written. |
| D2 | Under-specification: tasks where a naive decomposition provably drops a constraint. |
| D3 | Verification: plant an internally contradictory sub-agent report. Does the orchestrator check? |
| D4 | Termination: does it stop too early, or never stop? MAST's 21.3%. |

**Depends on.** Tracks 0, A4, B. **D1 gates the rest** — if brief quality does
not predict outcome, there is nothing for a delegation skill to improve.

### Track E — Handoff fidelity

**The unexplored cell: install the skill on the *reporting* side.** Every design
in this repository so far assumes the skill goes on the decider. If compression
is where the evidence dies, the skill belongs on the sub-agent.

| # | Experiment |
|---|---|
| E1 | What survives: plant *N* facts of known decisiveness in the sub-agent's material, measure which appear in its report. |
| E2 | Does a reporting skill change what survives? Skill on the sub-agent only. |
| E3 | Directional bias: replicate the summaries-distort-decisions result in our domain — does the summariser's framing move the decision? |
| E4 | **The placement factorial:** orchestrator {on, off} × sub-agent {on, off}. |

E4 is the most useful result in the programme for anyone actually installing a
skill, and nobody has it. "Where do I put it" is a question every user of these
systems has, and it is answerable in four cells.

**Depends on.** Tracks 0, A3, B.

---

# Part 6 — Confirmation

Runs only after Part 5 finds a mechanism worth confirming.

### Track F — End-to-end

The daily-use claim. One score for the whole system, confirmatory only, run
**after** C/D/E have identified a mechanism worth confirming. Includes the real
Task tool as an ecological-validity check against the scripted orchestrator: if
the two disagree, the scripted result is internally valid and externally
suspect, and the write-up says so.

Underpowered by nature. Everything except the single pre-registered primary is
reported with effect sizes and intervals and no p-values.

**Depends on.** C, D, E.

---

# Part 7 — Cross-cutting

Not phases. Each one runs inside the tracks above.

### Track G — Volume (demoted)

The long-context experiment, reframed. It is no longer the headline; it is one
interaction term: **does context length make the turn and handoff effects
worse?** All the machinery survives — `pad.py`, `separability.py`, the tax
library at AUC 0.679, the domination cap, the depth band, the ablation gate.

Full detail remains in
[`docs/superpowers/plans/2026-08-11-long-context-experiment.md`](superpowers/plans/2026-08-11-long-context-experiment.md).

**On hold: the ~960k characters of pilot library authoring.** Track A tells us
whether volume matters at all relative to turn structure. If turns dominate, the
library is sized for the interaction rather than for a main effect, which is a
different and probably smaller corpus.

Two findings from that plan carry forward regardless:

- The 2k casefile venue now **fails both gates** — admissibility 0.917 against a
  0.85 ceiling, trap rate 0.000. No headroom and no trap bite.
- The separability gate found a defect in the **cores**, not the padding: all 82
  probe-casefile documents contain zero dates, so realistically-dated padding is
  a perfect tell. Any corpus authored from here on puts dates in both.

### Track H — Tailoring, and life decisions

The design brief this repository exists for: *any decision AI helps a human make
needs to be tailored to that human's context.* Not a separate venue — a task
family that runs inside C, D, E and F, where the accumulated context is a
person's life rather than a client file.

The triplet design survives intact and is the identified version of the metric:

1. **Base.**
2. **Governing fact changed** — the recommendation *should* move.
3. **Matched non-governing fact changed** — of equal salience; nothing should move.

`d = P(change | governing) − P(change | matched non-governing)`, reported as
sensitivity and specificity separately plus Youden's J. **Without the third
file the metric is unidentified**: a model that flips on any perturbation
whatsoever scores a perfect 1.0.

> **Non-negotiable, and here is why, so that a future editor cannot remove it
> without reading the reason.** The matched non-governing arm is the third of
> three files and it will look like the cheapest thing to cut when the grid is
> too large — it is the arm where, by design, *nothing is supposed to happen*.
> Cutting it does not shrink the metric, it destroys it, and what remains is a
> flip-rate that reports a perfect score for a model that flips on everything.
> The failure is silent: the number still computes and still looks reasonable.
> The same applies to the elicited-quantity primary below. Neither may be
> dropped "to save a stratum" or "to trim the grid".

The primary is an elicited quantity (months of runway, a threshold, a notice
period), not a flip, because flip-rate scores conditional advice — the best
available answer — as failure.

**The construct has a name and a literature, and Track H should use them —
found 2026-08-12, Track K second pass.** What the triplet measures is
**informed values-congruent choice**: does the choice match what *this person*
actually values, given that they understand the options. That is not a coinage
here. It is a validated outcome in the patient decision aids literature, where a
2024 Cochrane review of **209 RCTs and 107,698 participants** reports **RR 1.75
(CI 1.44–2.13) across 21 trials**, moderate certainty — alongside high-certainty
effects on knowledge, accurate risk perception and decisional conflict. See
[`DECISION_FRAMEWORKS.md`](DECISION_FRAMEWORKS.md) row 12.

So: **adopt the name and the construct, do not import the effect size.** Those
are health treatment and screening decisions, delivered to patients around a
clinical consultation by a static tool; nothing licenses transferring RR 1.75 to
an LLM answering a question about a job offer. What it buys is that Track H's
primary stops being a metric invented here to escape flip-rate, and becomes an
operationalisation of a construct with thirty years of instrument development
behind it — including the *decisional conflict* scale, which measures whether
someone feels able to choose and is the nearest published thing to what a
decision skill is actually for.

In a sub-agent system this gets a second question the single-call venue could
not ask: **does the personal context survive the handoff?** A sub-agent that
summarises a life into a report is exactly where tailoring dies.

**No real personal data.** Every persona invented; the datasheet says so.

**Authoring gate.** For each life core: could a licensed professional state in
one sentence why the generic answer is wrong here, citing only the governing
fact? If not, it is a preference survey and it is cut.

### Track I — Reliability as a first-class outcome

Cross-cutting, and a direct consequence of the multi-turn result: the
degradation is **increased unreliability rather than lost aptitude**. A
mean-only metric will under-detect it, and binary admissibility is already
nearly a constant in our data.

**How lopsided, now that the numbers have been read rather than paraphrased.**
Aptitude falls **16%** and the source calls that non-significant; unreliability
rises **112%**. Roughly seven-eighths of the headline −39% lives in the spread.
Every measurement this repository has taken is a mean, so a mean-only design was
pointed at the smaller and less significant component. That does not explain the
three nulls on its own — the corpora were also short, single-turn and
underpowered — but it is the first account that predicts *which* number comes
back flat.

| # | Work | Status |
|---|---|---|
| I1 | `stats/reliability.py` — the §4.2 estimators (`aptitude_unreliability`), a per-item extension whose `scatter` array feeds a paired test directly (`per_item_reliability`), and the two repeat-count questions (`repeats_for_reliability`, `repeats_for_scatter_precision`). 100% line+branch, 7 property tests. | **done** |
| I2 | Every experiment reports scatter alongside its mean. ~~**Nothing calls the module yet** — I1 is a tool, not a result.~~ **Half true, corrected 2026-08-13.** `per_item_reliability` and `repeats_for_reliability` are called by `run_triggers.report_stability` and have already produced published numbers and a design change: ICC 0.833 (M5) and 0.852 (M6), and the resulting "future trigger arms run 2 repeats, not 5". `aptitude_unreliability` — the §4.2 estimator, the one the multi-turn finding actually lives in — still has **no caller**, and cannot have one until a venue produces per-item score distributions under two conditions. That is Track A, not a wiring job. | partly done |
| I3 | Power re-derived for a reliability outcome. | see below |
| I4 | A skill that reduces variance without moving the mean is a **result**, not a null. Pre-register it as a primary-eligible outcome so it cannot be discovered post hoc. | pending |

**I3, stated sharply enough to act on.** The long-context plan argues repeats are
near-worthless because between-item variance dominates within-item sampling
variance. That is right for a **mean** and wrong for a **spread**: at one repeat
the within-item scatter is not imprecise, it is *undefined*, and
`per_item_reliability` refuses `n_repeats=1` rather than returning a silent zero.
The two questions have different answers — at ICC 0.6 a mean outcome reaches
reliability 0.8 in **2** repeats, while estimating a per-item spread to a relative
standard error of 0.25 takes **9**. A 4.5× difference in run count follows from
the choice of outcome alone, so it has to be settled before a grid is sized.

---

# Part 8 — Output

The artifact someone else can re-run.

### Track J — Write-up and release

Paper, datasheet, harness disclosure, artifact. The verdict vocabulary and the
promotion gate carry over: no skill enters `plugin/skills/` while carrying
`UNTESTED`, and `de check` enforces it rather than trusting anyone to remember.

---

## Cross-cutting rules

Unchanged, and they apply to every track:

- **Predictions go in the notebook before runs.** Wrong predictions stay wrong
  in the record rather than being edited.
- **Blind adjudication of every scored failure**, with the pre-registered
  **>20% key-amendment kill**.
- **Instrument falsifiers before hypothesis falsifiers.** A gate that says "the
  venue cannot answer this" fires before spend.
- **No API keys.** Every call goes through the Claude Code CLI on a Claude Max
  subscription. `total_cost_usd` is a *notional* API-equivalent price and is
  never money spent — it is a burn meter for quota.
- **The budget is quota and wall-clock**, not dollars. Never drop a tier or trim
  a stratum to save money; there is no money to save.
- **`python -m uv run de check` is the gate.** No cloud CI.
- **Golden files pin the corpus byte-exact.** Regeneration needs `pytest
  --bless` and the diff belongs in review.
- **Commits attributed to the GitHub noreply address.**

---

## Sequencing

Two lanes. The product lane never waits on the research lane — that separation is
what makes this dual-purpose rather than a paper with a skill attached.

```text
  PART 1   K  frameworks      free, no instrument, changes what
           M  skill design    everything downstream is testing
              |
     +--------+--------------------------------+
     |                                         |
  RESEARCH LANE                          PRODUCT LANE  (PART 2)
     |                                         |
  PART 3  0  instrument                   S  ship the skills
     |       blocks measurement                |  install, use, label honestly
     |       not the product                   |
     |                                         L  variants + revision
     |  N  the trigger corpus                  |  revise against traces,
     |       the instrument L and M already    |  race frameworks, tune the
     |       ran on. a ruler solves it at      |  description
     |       0.890, so every L and M null      |
     |       has two readings until it lands   |
     |            |                            |
     |            +--- retro-qualifies --------+
     |            |    every L and M number on disk
  PART 4  A  replication                       |
     |       ~1200 calls, hours not days       |
     |       can kill or redirect all of it    |
     |                                         |
        B  attribution                         |
     |       runs on A's traces                |
     |                                         |
  PART 5  C  evidence aggregation  \           |
        D  delegation quality       > parallel |
        E  handoff fidelity        /           |
     |                                         |
  PART 6  F  end-to-end  <- only after a mechanism exists
     |                                         |
     +--------------------+--------------------+
                          |
  PART 8  J  write-up and artifact

  PART 7  cross-cutting, inside every track above
          G  volume       an interaction term; library authoring on hold
          H  tailoring    a task family, not a venue
          I  reliability  an outcome reported everywhere, not a track to finish
```

**Findings cross the lanes both ways.** Every research result is harvested into a
skill revision the week it lands, and every misfire the maintainer hits in daily
use is a candidate item for the corpus. A finding that never reaches the skill,
and a skill complaint that never reaches the corpus, both mean the lanes have
come apart.

---

## What would kill the whole programme

Written down now so a null is a result rather than a fourth dead corpus.

**0. The process measure moves and the outcome measure does not — and this has
already happened to someone else, at scale.** Agweyu et al. (2026, *Nature
Medicine*) cluster-randomized 103 clinical officers across 16 Kenyan primary care
facilities over 9,691 patients. LLM assistance raised note quality across every
domain and drove appropriate diagnosis to aOR 1.74 (p < 0.001). Treatment failure
was 2.2% against 2.0%, aOR 0.77, **p = 0.13**. The intervention visibly changed
how the work was written down and did not change what happened to the patients.

**That is the shape of every result this repository has produced.** M4, M5 and L5
each moved where the skill sits on a precision/recall frontier and none moved how
well it discriminates; the probe casefiles took 0 of 27 traps; `math` returned
`p_discordant` 0.000. Two independent lines of evidence now point the same way.

**And a competing explanation for the trigger half of that, found 2026-08-13.**
The corpus those nulls were measured on is solved to 0.890 by counting words on
the version 2 key, against 0.9795 to 0.9863 for the best arm on the same key. A flat
result is what a real null looks like *and*
what a nine-point ceiling looks like, and this document had no way to tell them
apart because nobody had measured the ceiling. **Track N** measures it. Until it
lands, "nothing about a description changes discrimination" is one of two live
readings rather than the finding — which is the more important correction,
because the sentence had already been written down as though it were settled.

So the rule for Tracks C through F: **name the outcome measure and the process
measure separately in the pre-registration, and state in advance that a process
gain with a flat outcome is a null for the skill, not a partial win.** Writing
that after the run is how "the model produced a more thorough answer" becomes a
finding. The counterweight is Goh et al. (2024) — +6.5pp on management reasoning,
+6.2pp on the case-specific domains — which is a process measure with an expert
rubric behind it and is the strongest located evidence for Track H. Both are in
[`docs/DECISION_FRAMEWORKS.md`](DECISION_FRAMEWORKS.md).

And the caveat that travels with both: clinicians **fully** adhered to the LLM's
advice in 19.5% of encounters. Advice given is not advice taken, and every
measurement in this repository is of advice given.

1. **Track A comes back flat *and the MDE was below the effect the literature
   reports*.** Both halves are required, and the second half was missing from an
   earlier draft — which made this the most dangerous sentence in the document.

   The arithmetic, using this repo's own `stats/power.required_pairs`: detecting
   a 12pp drop at 80% power needs roughly **127 pairs**, or ~254 once the stated
   design effect of ~2.0 is applied. **Track A had 12 items**, which are also the
   clustering unit, so the cluster bootstrap ran on 12 clusters. A flat Track A
   would therefore have been the *expected* result whether or not the effect was
   real.

   **Computed 2026-08-11, and it is worse than "underpowered".** Run
   `python -m uv run de power`; the table is regenerated rather than transcribed,
   because a hand-copied power figure is the same class of error as a hand-copied
   citation.

   | n_pairs | p_d=0.15 | p_d=0.20 | p_d=0.30 | p_d=0.40 | p_d=0.50 |
   |---|---|---|---|---|---|
   | **12** | n/a | n/a | n/a | n/a | **46.5** |
   | 30 | n/a | 19.6 | 24.0 | 27.7 | 31.0 |
   | 100 | 9.5 | 11.0 | 13.5 | 15.6 | 17.4 |
   | 233 | 6.3 | 7.3 | 8.9 | 10.3 | 11.5 |
   | **527** | **4.2** | **4.8** | **5.9** | **6.8** | **7.6** |
   | 627 | 3.8 | 4.4 | 5.4 | 6.3 | 7.0 |

   Percentage points. `n/a` means **no effect of any size is detectable** at that
   item count. At 12 items every column but the last is `n/a`, and the last is
   46.5pp — larger than the entire −39% the multi-turn paper reports. The 12-item
   corpus could not have detected the effect it was built to detect. `p_d` is
   swept rather than chosen, because discordance is unknown before a screening
   run and Rule 1 forbids inventing it.

   **This is now fixed for A1, and by the corpus rather than by argument** — but
   at a smaller item count than first written here, and the correction is the
   instructive part.

   > **Corrected the same day.** An earlier version of this paragraph said
   > **527 usable pairs**. That is the count of records that are not the
   > Unix-only `code` family, and it silently assumed the *full* condition could
   > be reconstructed by joining the shards. **It cannot.** Joined shards read as
   > a bulleted decomposition, not as the original question — for one `database`
   > record the full question is *"which countries' tv channels are playing some
   > cartoon written by Todd Casey?"* against joined shards beginning *"tv
   > channels airing cartoons determine which countries…"*. Pairing those would
   > have compared sharded delivery against **a third instruction we wrote**,
   > while calling it the published design. Caught by checking the field rather
   > than assuming it.

   A full-setting instruction has to come from a field, and the schema is
   per-family:

   | Family | n | Full-setting field | Usable for A1 |
   |---|---|---|---|
   | `actions` | 105 | `fully_specified_question` | **yes** |
   | `database` | 107 | `fully_specified_question` | **yes** |
   | `math` | 103 | `question` | **yes** |
   | `summary` | 92 | `query` — but the task also carries `documents`, so `query` alone may not be the instruction | **undecided** |
   | `data2text` | 120 | none; the input is a table | **no** |
   | `code` | 100 | split `prompt` (45) / `question_content` (55) | excluded anyway (Unix-only eval) |

   So **A1 is 315 pairs**, giving an MDE of **5.4–9.9pp**, or **7.6–13.9pp** at
   the stated design effect of 2.0. Against −39% that is still a wide margin and
   a flat A1 would still be a real result — the conclusion survives, the number
   did not. `summary` is left undecided rather than folded in, because deciding
   it is choosing what the full instruction *is*, and that is exactly the kind of
   parameter Rule 1 forbids inventing.

   A2 is *not* covered by any of this: it needs a fixed turn count, and the
   largest single shard-count stratum is 233 records (MDE 6–12pp) before the
   full-instruction constraint is even applied.

   As written, this falsifier turned an underpowered null into a
   programme-terminating decision — the same "build first, check the premise
   later" error as the three dead corpora, run in reverse. And the two biases do
   not cancel: the author's documented bias is toward the experiment working, the
   design's bias is toward a null, and what that produces is **a null that gets
   believed**.

   So: Track 0 computes the MDE per experiment before Track A runs, the notebook
   records the MDE beside the point prediction, and item count is sized from it.
   A flat result at a 30pp MDE kills nothing.
2. **Delegation never helps (A4).** If a single well-prompted call always beats
   the orchestrated system on our tasks, sub-agents are a handicap rather than
   an architecture here, and the honest deliverable is a skill about *when not
   to delegate*.
3. **Key amendment rate exceeds 20%.** The corpus is retired and the run is not
   reported as a result. Given 21/21, this is the falsifier most likely to fire.
4. **Placebo matches skill.** The effect is instruction bulk, not content.
5. **Chain-of-thought matches skill.** The skill is a verbose CoT prompt in a
   markdown file.
6. **Parse rates diverge by arm.** The run is void. A skill that wins on
   accuracy while breaking the output contract has not won.
7. **Scripted and real orchestration disagree (F).** Internal validity without
   external validity, and the write-up has to say so rather than reporting the
   convenient number.

---

## The claim ladder

What we may honestly say, at each stage, and not before.

| After | We may claim |
|---|---|
| Track 0 | "We can run this experiment." Nothing about decisions. |
| Track N | "A firing result is about the description and not about turn length." **Nothing above the ruler may be claimed before this row.** With `N4` on top: "and it holds on turns a human wrote." |
| Track A | "These failure modes do / do not occur on frontier models in August 2026." |
| Track B | "We can attribute a system failure to a node, with reported agreement." |
| C / D / E | "A skill installed *here* changes *this* failure mode by *this much*." |
| Track F | "The system decides better end to end." |
| Track J | Any of the above, with an artifact someone else can re-run. |

Today we are entitled to the first row and not yet to it — Track 0 is not built.
