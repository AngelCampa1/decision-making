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
| **3. The instrument** | `0` | Instrument |
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

### Track M — Skill design: how a skill should be built

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
| M5 | Bundle-size curve: 2 procedures, 4, 8. Where does routing accuracy break? |

**Hypothesis falsifier.** If routing accuracy is at chance, the bundle is a
single long skill with extra steps, and the honest move is to merge the four
procedures into one body or split them back into separately-triggered skills.

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
| S7 | Re-derive each of the above from Track K's catalogue, or mark it invented | pending K |
| S8 | **A retirement rule.** "Daily use is evidence" currently has no failure condition — no threshold at which use retires a procedure. Define one: a procedure the maintainer disables for N consecutive days is marked `WITHDRAWN` in `SCORECARD.md`. Evidence that cannot come out negative is not evidence. | not written |

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
| 0.1 | ~~Session-resume canary~~ **Done.** Multi-turn canary passed under full isolation; falsifier corrected. Remaining work is to fold the `stream-json` transport into `providers/claude_code.py` beside the existing single-shot path. | done |
| 0.2 | Scripted orchestrator: 1 orchestrator + 3 sub-agents, per-node run records, end to end. | ~$1 |
| 0.3 | Isolation canary at every node, including sub-agents, with a planted `CLAUDE.md`. | ~$1 |
| 0.4 | Budget ledger and wall-clock accounting over a call *tree* rather than a call. | free |
| 0.5 | `RunRecord` gains node identity, parent, turn index, and a trace id — **using OpenTelemetry GenAI semantic-convention attribute names** (`gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.conversation.id`, `gen_ai.usage.*`, `gen_ai.evaluation.*`), with parent/child span nesting giving node parent and turn index for free. `opentelemetry-api` + `opentelemetry-sdk` is a 4-package pure-Python Apache-2.0 closure; `ConsoleSpanExporter(out=file)` opens **no socket**. Hand-rolling a trace schema when a vendor-neutral one exists is a real weakness, and MAST-style attribution needs structured traces regardless. **Adopt the names, not the package's constants**: the spec is status `Development`, zero releases, Schema URL `TODO`, and has already renamed `gen_ai.system` → `gen_ai.provider.name`. Hardcode the strings in one module, pin the SDK, record the semconv commit SHA per run. Old records must fail loudly, not silently vanish. | free |
| 0.6 | **Assert on the `system/init` event**, which `--output-format stream-json --verbose` emits as a free machine-readable isolation receipt: `tools`, `skills`, `agents`, `memory_paths`, `apiKeySource`. Strictly better evidence than inferring isolation from a response. Two channels it advertises are **latent, not active** — with `--tools ""` there is no Task tool to reach the six declared agents and no memory tool to write the auto-memory path (tested: nothing was created). **Both go live the moment `--tools` is relaxed, which Track F plans.** The auto-memory path is keyed on the working directory, so it would become a cross-run state channel that a checkpointed run cannot see. Mitigation: fresh cwd per run, plus an assertion on `memory_paths`. `--bare` would disable auto-memory and is unusable — it forces `ANTHROPIC_API_KEY` auth and never reads OAuth. | free |

**Depends on.** Nothing. This is the gate on everything else.

**Done when.** A canary trace shows turn-*n* context containing turn-1 content
by token accounting; a 4-node scripted run completes with per-node records; the
isolation canary passes at every node; `de check` green.

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
| A1 | **Multi-turn drop** | **Adopt the published instrument rather than authoring one.** arXiv:2505.06120 released its sharded corpus and simulator — `github.com/microsoft/lost_in_conversation` (MIT) and `sharded_instructions_600.json` (CDLA-Permissive-2.0): 600 pre-sharded instructions, 7 task families, plus the sharding prompts and simulated-user agent. This *is* the A1 design, peer-reviewed, and it removes the activity with this repo's worst track record — three discarded corpora, 21/21 key errors. Needs a `model_claude_code.py` shim against their `generate()` interface; their only backend is OpenAI. Skip the `code` task (Unix-only eval). **The "~6 turns" figure was mine and has no source** — the paper sweeps 2→8 and reports no mean; measure it from the JSON. | yes |
| A2 | **Recency over-weighting** | Decisive fact placed at first / middle / last turn, total turns fixed. Flat means no recency effect here and Track C changes shape. | yes |
| A3 | **Handoff loss** | Sub-agent reads the documents and reports; orchestrator decides from the report alone vs from raw documents. The gap is compression loss. Also: *which* facts survive. | yes |
| A4 | **Does delegating even help?** | One agent with everything vs orchestrator + sub-agents, same task. If single wins, the skill's job changes from "delegate better" to "know when not to delegate." | yes |
| A5 | **Reliability** | *k* repeats per item at each venue. Measure the scatter, not the mean. | yes |

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
| I2 | Every experiment reports scatter alongside its mean. **Nothing calls the module yet** — I1 is a tool, not a result. | pending |
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
  PART 4  A  replication                       |  revise against traces,
     |       ~1200 calls, hours not days       |  race frameworks, tune the
     |       can kill or redirect all of it    |  description
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

1. **Track A comes back flat *and the MDE was below the effect the literature
   reports*.** Both halves are required, and the second half was missing from an
   earlier draft — which made this the most dangerous sentence in the document.

   The arithmetic, using this repo's own `stats/power.required_pairs`: detecting
   a 12pp drop at 80% power needs roughly **127 pairs**, or ~254 once the stated
   design effect of ~2.0 is applied. **Track A has 12 items**, which are also the
   clustering unit, so the cluster bootstrap runs on 12 clusters. A flat Track A
   is therefore the *expected* result whether or not the effect is real.

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
| Track A | "These failure modes do / do not occur on frontier models in August 2026." |
| Track B | "We can attribute a system failure to a node, with reported agreement." |
| C / D / E | "A skill installed *here* changes *this* failure mode by *this much*." |
| Track F | "The system decides better end to end." |
| Track J | Any of the above, with an artifact someone else can re-run. |

Today we are entitled to the first row and not yet to it — Track 0 is not built.
