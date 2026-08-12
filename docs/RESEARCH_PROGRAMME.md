# The research programme

**What we are trying to find out:** whether a written skill measurably improves
the decisions an agentic system makes, when that system accumulates context over
turns and delegates work to sub-agents.

That sentence has four load-bearing parts, and the repository has so far tested
none of them together:

| Part | Status |
|---|---|
| a written skill | `evidence-ledger` exists, `verdict: UNTESTED` |
| measurably improves decisions | three corpora, three nulls, 21/21 scored failures were answer-key errors |
| an agentic system | every call to date is one `claude -p`, no tools, no session |
| accumulates over turns | accumulation has been *rendered*, never *lived* |
| delegates to sub-agents | never attempted |

This document is the pointable index. Each track below states a question, what
would kill it, the experiments inside it, and what "done" means. Point at a
track and there is enough here to work for days without asking what next.

**This is bigger than one paper.** Tracks C, D and E could each carry one. The
programme is sequenced so that the cheapest disconfirming evidence arrives
first.

---

## Where we are, honestly

Three corpora were built and all three measured nothing:

| Corpus | Size | Varied | Result |
|---|---|---|---|
| `rel-*` single-turn | ~350 tok | distractor count, position | 0.946; 15/15 zeros were item defects |
| `rel-*` rebuilt | ~700 tok | type-compatible colliding distractors | 0.971 |
| `probe-*` casefiles | ~1,650 tok | trap order 1–3, four consequence kinds, three framings | **27 trap opportunities, zero taken**; admissibility 0.917 |

A fourth was planned — the same casefiles padded to 100k tokens. It is not
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
| Single-turn → multi-turn accuracy collapse | [LLMs Get Lost In Multi-Turn Conversation](https://arxiv.org/abs/2505.06120), ICLR 2026 | **−39% average**, 15 models, 200k conversations; Claude 3.7 Sonnet 85.4 → 70.0 |
| The collapse is *unreliability*, not lost aptitude | ibid. | same model, same question, answers scatter |
| Mechanism: anchor early, then over-weight the latest turn | ibid. | — |
| Multi-agent failure taxonomy | [MAST](https://arxiv.org/abs/2503.13657) | 14 modes, 1600+ traces, κ=0.88; **41.8%** design/spec, **36.9%** inter-agent misalignment, **21.3%** verification/termination |
| Summarisation is not neutral compression | [When Summaries Distort Decisions](https://arxiv.org/html/2606.29251) | different summarisers move identical evidence toward opposite decisions |
| Recency in ranking | [Do LLMs Favor Recent Content?](https://arxiv.org/abs/2509.11353) | 7 models; up to 95 rank positions |
| Skill *presence* is the dominant term; *form* is not | [Xu & Wu](https://arxiv.org/abs/2605.31408), 30 tasks, 2 models | **+18 to +36pp** from presence; granularity minimal and model-dependent |
| Curated skills help; self-generated ones do not | [SkillsBench](https://arxiv.org/abs/2602.12670), 87 tasks, 8 domains | **+16.6pp** (33.9 → 50.5); focused bundles beat larger ones |
| More skills makes agents worse | [Skill shadowing](https://arxiv.org/html/2605.24050) | selection accuracy >90% under 30 candidates → 13.6% at scale; mechanism is **description overlap** |
| Orchestration is not free | [In-Context Prompting Obsoletes Agent Orchestration](https://arxiv.org/pdf/2604.27891) | for procedural tasks a single well-prompted call matches multi-agent |
| Orchestrator prompting already shown to help | [PerspectiveGap](https://arxiv.org/pdf/2606.08878) | prior art — we must be sharper than "prompting the orchestrator helps" |

Two corrections to our own records follow from this and are tasks, not
footnotes:

- `CLAUDE.md` and `AGENTS.md` cite SkillsBench as "+18 to +36pp". The paper's
  headline is **+16.6pp** average. Verify against the paper and correct both
  files and any notebook entry that repeats it.
- The plan in `docs/superpowers/plans/2026-08-11-long-context-experiment.md`
  argues repeats are near-worthless because between-item variance dominates.
  That is correct for estimating a **mean** and exactly wrong for estimating
  **reliability**, which the multi-turn result says is where the effect lives.
  See Track I.

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

## Track K — Decision frameworks: the review this project skipped

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
| K5 | **Citation audit.** 65 arXiv identifiers are cited across `docs/` and `notebook/`; `paper/refs.bib` holds 39. Resolve every cited identifier against arxiv.org, add the 26 missing entries, and make `de check` fail when a markdown citation has no bib entry. A 2026-08-11 spot check already found one conflation of two real papers, caught only because the same claim carried two identifiers. |
| K6 | Output: `docs/DECISION_FRAMEWORKS.md` — the catalogue, with a shortlist of framework-derived skill candidates ranked by evidence strength. |

**Skill candidates already named in the brief and not yet written:** a council /
adversarial-review skill (multiple positions argued before deciding — which is
also the sub-agent architecture question), and a clarify-or-decide skill (when
to ask for more information versus decide under incomplete information).

**Done when** `docs/DECISION_FRAMEWORKS.md` exists and every current skill is
either traced to a documented framework or explicitly marked as invented.

---

## Track L — Skill variants: which formulation is best

**Question.** For one target failure, which way of writing the skill works best?

**Why it matters.** The brief asked to test "different types of skills and
variations, finding the most optimal one." The current design compares one skill
against control, placebo and chain-of-thought — it never compares **skill A
against skill B for the same job**. Without that there is no basis for saying a
skill is good, only that it is better than nothing.

SkillsBench gives a directional prior worth testing here: **focused 2–3 module
skills outperform comprehensive documentation.** Every skill in this repo is
already short, so that prediction is testable and cheap.

| # | Variant axis | Example |
|---|---|---|
| L1 | **Framework** | the same failure targeted via a ledger, a pre-mortem, or a reference class |
| L2 | **Length** | 400 words vs 1,200 vs 150 |
| L3 | **Output shape** | a fixed block template vs free prose vs a checklist |
| L4 | **Framing** | procedure ("do this") vs diagnostic ("check whether") vs question list |
| L5 | **Trigger breadth** | narrow description vs broad, measured on false-fire rate as well as on help |

**This is a horse race, and it needs the multiplicity machinery already built.**
`stats/multiplicity.py` exists and has never been used in anger. Winner's curse
is the standing threat: with five variants the best one is biased upward, so the
winner is re-run on a fresh holdout before it is called best.

**Done when** one target failure has ≥3 authored variants, a pre-registered
comparison, and a winner replicated on a holdout.

---

## Track M — Skill design: how a skill should be built

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
| M4 | Race one-entry-with-routing against four-separate-skills. The four-skill version is preserved in git at `9a16b18` and is the comparison arm. This is Track L applied to structure rather than to prose. |
| M5 | Bundle-size curve: 2 procedures, 4, 8. Where does routing accuracy break? |

**Hypothesis falsifier.** If routing accuracy is at chance, the bundle is a
single long skill with extra steps, and the honest move is to merge the four
procedures into one body or split them back into separately-triggered skills.

---

## Track S — Ship the skills

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

| # | Work | Status |
|---|---|---|
| S1 | `evidence-ledger` — the accumulated-context pile | written, `UNTESTED` |
| S2 | `switching-conditions` — is this generic advice right for *me* | written, `UNTESTED` |
| S3 | `consequence-cascade` — what this sets in motion, and what it spends | written, `UNTESTED` |
| S4 | `decide-or-wait` — timing, reversibility, real vs felt deadlines | written, `UNTESTED` |
| S5 | a council / adversarial-review skill — argue the positions before deciding | named in the brief, not written |
| S6 | a clarify-or-decide skill — ask for more, or decide under incomplete information | named in the brief, not written |
| S7 | Re-derive each of the above from Track K's catalogue, or mark it invented | pending K |

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

---

## Track 0 — Instrument

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

**Instrument falsifier.** If `--resume` does not actually place prior turns in
the model's context — verifiable by token accounting, `cache_read` must climb
turn over turn — the multi-turn venue is dead on this backend and we need a
different one before anything else proceeds.

| # | Experiment | Cost |
|---|---|---|
| 0.1 | Session-resume canary: state a constraint at turn 1, verify at turn *n* it is still in context *and* still honoured. Token accounting proves presence; behaviour is a separate measurement. | ~$1 |
| 0.2 | Scripted orchestrator: 1 orchestrator + 3 sub-agents, per-node run records, end to end. | ~$1 |
| 0.3 | Isolation canary at every node, including sub-agents, with a planted `CLAUDE.md`. | ~$1 |
| 0.4 | Budget ledger and wall-clock accounting over a call *tree* rather than a call. | free |
| 0.5 | `RunRecord` gains node identity, parent, turn index, and a trace id. Old records must fail loudly, not silently vanish. | free |

**Depends on.** Nothing. This is the gate on everything else.

**Done when.** A canary trace shows turn-*n* context containing turn-1 content
by token accounting; a 4-node scripted run completes with per-node records; the
isolation canary passes at every node; `de check` green.

---

## Track A — Replication

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
| A1 | **Multi-turn drop** | The 12 existing casefiles, delivered whole vs sharded across ~6 turns. Same content, same tokens, only delivery differs. | yes |
| A2 | **Recency over-weighting** | Decisive fact placed at first / middle / last turn, total turns fixed. Flat means no recency effect here and Track C changes shape. | yes |
| A3 | **Handoff loss** | Sub-agent reads the documents and reports; orchestrator decides from the report alone vs from raw documents. The gap is compression loss. Also: *which* facts survive. | yes |
| A4 | **Does delegating even help?** | One agent with everything vs orchestrator + sub-agents, same task. If single wins, the skill's job changes from "delegate better" to "know when not to delegate." | yes |
| A5 | **Reliability** | *k* repeats per item at each venue. Measure the scatter, not the mean. | yes |

**Depends on.** Track 0.

**Done when.** Five notebook entries, each with its numeric prediction written
*before* the run, and one table saying which effects reproduce and how big they
are on our stack.

---

## Track B — Attribution

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

## Track C — Evidence aggregation

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

---

## Track D — Delegation quality

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

---

## Track E — Handoff fidelity

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

## Track F — End-to-end

The daily-use claim. One score for the whole system, confirmatory only, run
**after** C/D/E have identified a mechanism worth confirming. Includes the real
Task tool as an ecological-validity check against the scripted orchestrator: if
the two disagree, the scripted result is internally valid and externally
suspect, and the write-up says so.

Underpowered by nature. Everything except the single pre-registered primary is
reported with effect sizes and intervals and no p-values.

**Depends on.** C, D, E.

---

## Track G — Volume (demoted)

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

---

## Track H — Tailoring, and life decisions

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

The primary is an elicited quantity (months of runway, a threshold, a notice
period), not a flip, because flip-rate scores conditional advice — the best
available answer — as failure.

In a sub-agent system this gets a second question the single-call venue could
not ask: **does the personal context survive the handoff?** A sub-agent that
summarises a life into a report is exactly where tailoring dies.

**No real personal data.** Every persona invented; the datasheet says so.

**Authoring gate.** For each life core: could a licensed professional state in
one sentence why the generic answer is wrong here, citing only the governing
fact? If not, it is a preference survey and it is cut.

---

## Track I — Reliability as a first-class outcome

Cross-cutting, and a direct consequence of the multi-turn result: the
degradation is **increased unreliability rather than lost aptitude**. A
mean-only metric will under-detect it, and binary admissibility is already
nearly a constant in our data.

| # | Work |
|---|---|
| I1 | `stats/reliability.py` — within-item scatter, at the repo's 100% line+branch floor with property tests, matching `paired.py`. |
| I2 | Every experiment reports scatter alongside its mean. |
| I3 | Power re-derived for a reliability outcome. Repeats are *not* worthless here, which reverses the argument in the long-context plan. |
| I4 | A skill that reduces variance without moving the mean is a **result**, not a null. Pre-register it as a primary-eligible outcome so it cannot be discovered post hoc. |

---

## Track J — Write-up and release

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

```text
  Track K  Decision frameworks   <- FIRST. Free, no instrument, and it changes
     |                              what every other track is testing.
     |                              The review the project skipped.
     |
  Track S  Ship the skills       <- parallel from day one, never downstream.
     |                              Write them, use them, label them honestly,
     |                              harvest each finding into a revision.
     |
  Track 0  Instrument            <- blocks the measurement, not the skills
     |
  Track A  Replication           <- ~1200 calls, hours not days
     |                              can kill or redirect the whole programme
     |
  Track L  Skill variants        <- the horse race the brief asked for:
     |                              which formulation wins, not just
     |                              whether one beats nothing
     |
  Track B  Attribution           <- runs on Track A's traces
     |
     +--> Track C  Evidence aggregation   \
     +--> Track D  Delegation quality      >  parallel, each pointable
     +--> Track E  Handoff fidelity       /
     |
  Track F  End-to-end            <- confirmatory, after a mechanism exists
     |
  Track J  Write-up

  Track G  Volume        woven into C/E as an interaction; library on hold
  Track H  Tailoring     a task family inside C/D/E/F
  Track I  Reliability   an outcome in every experiment
```

---

## What would kill the whole programme

Written down now so a null is a result rather than a fourth dead corpus.

1. **Track A comes back flat.** No multi-turn drop, no recency effect, no
   handoff loss on our stack. Then the 2026 models have fixed what the 2025
   models did, and that is publishable — but it is a different paper and this
   programme stops.
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
| Track A | "These failure modes do / do not occur on frontier models in August 2026." |
| Track B | "We can attribute a system failure to a node, with reported agreement." |
| C / D / E | "A skill installed *here* changes *this* failure mode by *this much*." |
| Track F | "The system decides better end to end." |
| Track J | Any of the above, with an artifact someone else can re-run. |

Today we are entitled to the first row and not yet to it — Track 0 is not built.
