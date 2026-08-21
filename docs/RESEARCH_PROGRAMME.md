# The research programme

**Audience:** the evaluating reader, and in particular anyone picking up a track.

What we are trying to find out: whether a written skill measurably improves the
decisions an agentic system makes, when that system accumulates context over
turns and delegates work to sub-agents.

That sentence has four load-bearing parts, and the repository has so far tested
none of them together:

| Part | Status |
|---|---|
| a written skill | `decision-making` v0.3.0 ships, six procedures behind a router, `verdict: UNTESTED`. `council` and `hinge` were added 2026-08-19 and neither is measured or framework-audited |
| measurably improves decisions | three corpora, three nulls, 21/21 scored failures were answer-key errors |
| an agentic system | every call to date is one `claude -p`, no tools, no session |
| accumulates over turns | accumulation has been *rendered*, never *lived* |
| delegates to sub-agents | never attempted |

Read two other files with this one, and read the first of them before this one.
They are not appendices; the work is not doable without them.

| | |
|---|---|
| [`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md) | How the work is done. Five standing rules, the sub-agent and adversarial-review method, the confirmation requirement, what may run unattended. Every rule is a failure that already happened here. Read it first. |
| [`STATUS.md`](STATUS.md) | Where the work actually stopped. Track states, runs on record, and the <!-- de:fact broken-measurements -->eleven<!-- /de:fact --> measurements caught being broken. This programme says what a track *is*; that file says how far it got. |

How to read this. Sixteen tracks in eight parts, and each part is its own file
under [`programme/`](programme/part-1-what-is-already-known.md). This page is
the map: the tracks, the venue map, what has been measured, and the rules that
apply across every part. [The parts](#the-parts) lists all eight with what is
in each.

Two lanes, and they run in parallel. The *product* lane
([Part 2](programme/part-2-the-product.md)) ships skills people install and
use, and never waits on the research lane. The *research* lane
(Parts [3](programme/part-3-the-instrument.md) to
[6](programme/part-6-confirmation.md)) validates them. A project where the
second gates the first produces a paper with a skill attached; this one is
meant to be both. See [Sequencing](#sequencing).

This is bigger than one paper. Tracks C, D and E could each carry one. The
programme is ordered so that the cheapest disconfirming evidence arrives first.

---

## The tracks

| Part | Track | |
|---|---|---|
| **[1. What is already known](programme/part-1-what-is-already-known.md)** | `K` | Decision frameworks: the review this project skipped |
|  | `M` | Skill design: how a skill should be built |
| **[2. The product](programme/part-2-the-product.md)** | `S` | Ship the skills |
|  | `L` | Skill variants: which formulation is best |
| **[3. The instrument](programme/part-3-the-instrument.md)** | `0` | Instrument: multi-turn and delegation |
|  | `N` | The trigger corpus: is the instrument behind `L` and `M` a fair test? |
| **[4. Does the failure exist](programme/part-4-does-the-failure-exist.md)** | `A` | Replication |
|  | `B` | Attribution |
| **[5. Where a skill helps](programme/part-5-where-a-skill-helps.md)** | `C` | Evidence aggregation |
|  | `D` | Delegation quality |
|  | `E` | Handoff fidelity |
| **[6. Confirmation](programme/part-6-confirmation.md)** | `F` | End-to-end |
| **[7. Cross-cutting](programme/part-7-cross-cutting.md)** | `G` | Volume (demoted) |
|  | `H` | Tailoring, and life decisions |
|  | `I` | Reliability as a first-class outcome |
| **[8. Output](programme/part-8-output.md)** | `J` | Write-up and release |

Track letters (`K`, `A`, `0`…) are stable identifiers, referenced from commit
messages and the task list. The parts are the order, and each one is a file.

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
decompositions that make V4 attributable: without them a V4 result cannot say
whether the damage came from turns or from delegation.

---

## What has been measured so far

Three corpora were built and all three measured nothing:

| Corpus | Size | Varied | Result |
|---|---|---|---|
| `rel-*` single-turn | ~350 tok | distractor count, position | 0.946; 15/15 zeros were item defects |
| `rel-*` rebuilt | ~700 tok | type-compatible colliding distractors | 0.971 |
| `probe-*` casefiles | ~1,650 tok | trap order 1 to 3, four consequence kinds, three framings | 27 trap opportunities, zero taken; admissibility 0.917 |

A fourth corpus did produce results, and on 2026-08-13 it turned out to be
measuring something else. The 73-turn trigger set behind every Track L and
Track M number is separable by turn length alone at AUC 0.850; a bare *"fire
if ≥ 18 words"* rule scores 0.890 on the version 2 key, against 0.9795
for the best description arm on that key (`stakes-shown`) and 0.9863 for the
`confidence` arm. So the nine-point band
above a ruler is where five reported nulls were competing, and
the corpus never contained the pile of context its `ledger` procedure exists
for. Track N rebuilds it; the existing L and M comparisons stay valid
against each other and stop being quotable on their own.

A fifth was planned: the same casefiles padded to 100k tokens. It is not
cancelled, but it is demoted to Track G, and the ~960k characters of library
authoring it needs is on hold until Track A reports.

The reason is in the repository's own words. `docs/ACCUMULATION_VENUE.md` says
of the single-call design:

> accumulation is *rendered* rather than lived … What it does not share is error
> compounding across the model's own steps, which this venue cannot measure and
> should not claim to.

That was written before any of this was built, and then everything was built in
the venue it warns about. `docs/FAILURE_TAXONOMY.md` reaches the same place from
the other end: four of Harness-Bench's five failure categories are
structurally unreachable in a single-turn, no-tool venue. Tool failures,
grounding gaps, state and continuation issues cannot occur, so no taxonomy built
here generalises to a system that has them.

What survives and gets reused: the CLI provider and its isolation findings,
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
| Single-turn → multi-turn accuracy collapse | [LLMs Get Lost In Multi-Turn Conversation](https://arxiv.org/abs/2505.06120) | **−39% average across six generation tasks** (abstract, verbatim). Per-model figures are in Table 1 and are not quoted here until read from the table. An earlier draft carried 85.4 → 70.0 for Claude 3.7 Sonnet, which is reportedly the *Math task alone* against a six-task average of 78.0 → 65.6. Venue unverified. |
| The collapse is *unreliability*, not lost aptitude | ibid. | §4.2, read 2026-08-11: aptitude `A^90 = percentile_90(S)` drops 16% and the paper calls that non-significant; unreliability `U^90_10 = percentile_90(S) − percentile_10(S)` rises 112%. So roughly seven-eighths of the −39% is scatter. Implemented in `stats/reliability.py`; see Track I. |
| Mechanism: anchor early, then over-weight the latest turn | ibid. | n/a |
| Multi-agent failure taxonomy | [MAST](https://arxiv.org/abs/2503.13657) | 14 modes, 1600+ traces, κ=0.88, all three verified. The category percentages are not in the paper. An earlier draft carried 41.8 / 36.9 / 21.3; aggregating the per-mode rates in Figure 1 gives roughly 44.3 / 32.4 / 23.5, and any figure used must be labelled "our aggregation of MAST Figure 1". MAST's traces are 7 frameworks on coding and maths, so transfer to a 4-node decision task is an assumption, not a finding. |
| Summarisation is not neutral compression | [When Summaries Distort Decisions](https://arxiv.org/html/2606.29251) | different summarisers move identical evidence toward opposite decisions |
| Recency in ranking | [Do LLMs Favor Recent Content?](https://arxiv.org/abs/2509.11353) | 7 models; up to 95 rank positions |
| Skill *presence* is the dominant term; *form* is not | [Xu & Wu](https://arxiv.org/abs/2605.31408), 30 tasks, 2 models | +18 to +36pp from presence; granularity minimal and model-dependent |
| Curated skills help; self-generated ones do not | [SkillsBench](https://arxiv.org/abs/2602.12670), 87 tasks, 8 domains | +16.6pp (33.9 → 50.5); focused bundles beat larger ones |
| More skills makes agents worse | [Skill shadowing](https://arxiv.org/abs/2605.24050) | **"up to 21% when scaling from a small set of helpful skills to a 202-skill library"** (abstract, verbatim). Shadowing dominates context overhead, which is "small and indistinguishable from zero". The regime is 202 skills. An earlier draft of this table carried "90% → 13.6%", which is this paper *quoting* Gan & Sun 2025 on tool selection at 11,100 candidates, not its own finding, and three orders of magnitude from any decision made here. |
| Orchestration is not free | [In-Context Prompting Obsoletes Agent Orchestration **for Procedural Tasks**](https://arxiv.org/abs/2604.27891) | the qualifier is the scope. Reported as *domination*, not parity: failure rates 11.5% vs 24%, 0.5% vs 9%, 5% vs 17%. This is a stronger threat to Track D than an earlier draft said. |
| Orchestration prompting is a measured *capability gap* | [PerspectiveGap](https://arxiv.org/abs/2606.08878) | 17.2% average combined pass rate; best model 62.0%; Opus 4.8 singled out for weakness despite strong coding. It does not show that prompting the orchestrator helps; it shows models are bad at orchestration prompting. So it is a baseline and an item source for Tracks D and E, not prior art to be out-sharpened. |

A caution about this table, learned by getting it wrong. The first draft
collapsed the two skills rows into one, on the assumption that a search result
describing "SkillsBench" was the paper already cited. They are two different real
papers with different scales and different numbers, and the merge turned a
correct figure into an incorrect one, in the product file, in this document, and
in a notebook entry. Both identifiers were resolved against arxiv.org before this
version. A search-result summary is not the paper, and two similarly-named
papers on one topic is the normal case. Track K5 makes `de check` enforce it.

One correction to our own records follows from this table, and it is a task:
the plan in
`docs/superpowers/plans/2026-08-11-long-context-experiment.md` argues repeats are
near-worthless because between-item variance dominates. That is correct for
estimating a mean and exactly wrong for estimating reliability, which the
multi-turn result says is where the effect lives. See Track I.

## The parts

Each part states its tracks, what would kill each one, the experiments inside
it, and what "done" means. Every part is self-contained: point a session at one
and it has the falsifiers, the experiments and the done condition it needs.

| | Part | What is in it |
|---|---|---|
| 1 | [What is already known](programme/part-1-what-is-already-known.md) | Tracks K and M. The decision-framework review this project skipped, graded by evidence, and what the literature says about how a skill should be built. |
| 2 | [The product](programme/part-2-the-product.md) | Tracks S and L. Shipping the skills, and which formulation of a skill is best. |
| 3 | [The instrument](programme/part-3-the-instrument.md) | Tracks 0 and N. Multi-turn and delegation, and whether the trigger corpus behind every published number is a fair test. The longest part, because the instrument failed first. |
| 4 | [Does the failure exist](programme/part-4-does-the-failure-exist.md) | Tracks A and B. Replicating the context failure this whole programme assumes, and attributing it. |
| 5 | [Where a skill helps](programme/part-5-where-a-skill-helps.md) | Tracks C, D and E. Evidence aggregation, delegation quality, handoff fidelity. Any one of the three could carry a paper. |
| 6 | [Confirmation](programme/part-6-confirmation.md) | Track F, end-to-end. Sixteen lines, because confirmation gets specified once Part 5 names a mechanism worth confirming. |
| 7 | [Cross-cutting](programme/part-7-cross-cutting.md) | Tracks G, H and I. Volume, tailoring and life decisions, and reliability treated as an outcome in its own right. |
| 8 | [Output](programme/part-8-output.md) | Track J. Paper, datasheet, harness disclosure, artifact, and where any of it would be submitted. |

The rules below this line apply to every part.

---

## Cross-cutting rules

Unchanged, and they apply to every track:

- Predictions go in the notebook before runs. Wrong predictions stay wrong in
  the record rather than being edited.
- Blind adjudication of every scored failure, with the pre-registered >20%
  key-amendment kill.
- Instrument falsifiers before hypothesis falsifiers. A gate that says "the
  venue cannot answer this" fires before spend.
- No API keys. Every call goes through the Claude Code CLI on a Claude Max
  subscription. `total_cost_usd` is a *notional* API-equivalent price and is
  never money spent. It is a burn meter for quota.
- The budget is quota and wall-clock, not dollars. Never drop a tier or trim a
  stratum to save money; there is no money to save.
- `python -m uv run de check` is the gate, locally and in CI. Local says the
  tree passes; CI says the commit does. A separate workflow publishes the site
  and gates nothing.
- Golden files pin the corpus byte-exact. Regeneration needs `pytest --bless`
  and the diff belongs in review.
- Commits attributed to the GitHub noreply address.

---

## Sequencing

Two lanes. The product lane never waits on the research lane, and that
separation is what makes this dual-purpose rather than a paper with a skill
attached.

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

Findings cross the lanes both ways. Every research result is harvested into a
skill revision the week it lands, and every misfire the maintainer hits in daily
use is a candidate item for the corpus. A finding that never reaches the skill,
and a skill complaint that never reaches the corpus, both mean the lanes have
come apart.

---

## Queued, and stopped on purpose

A four-wave plan ran on 2026-08-20 and was stopped partway through the second
wave. The work that landed is in the tracks above, in the register, and in the
gate. The work that did not is written down in
[`the plan stops at wave 1`](../notebook/2026-08-20-the-plan-stops-at-wave-1-and-here-is-what-it-leaves.md),
which names every remaining item, says which of them are partly built rather
than unstarted, and reproduces the plan itself, because the plan file lives
outside this repository and will not survive.

Three items bind things stated elsewhere in this document, so they are repeated
here. One of the three closed after the stop and is kept for the same reason:
a reader who finds the constraint should find that it lifted.

- **The twenty-four version 5 triples are unadjudicated.** No number may be
  published against answer key v5 until the blind three-judge round has run on
  them. Every downstream run in Part 3 and after is scored against that key.
- **Concurrency on the Claude CLI backend was measured on 2026-08-20 and the
  register did not move.** 840 calls, concurrency 8 agreeing with serial better
  than serial agrees with itself, 7.69× wall-clock. `CONCURRENCY_UNSAFE` still
  names only `ollama/`, and now that silence is earned rather than inherited.
  What this does not cover: `scripts/run_triggers.py` runs its own serial loop
  and was not touched, so the published path is still serial. See
  [`the outcome`](../notebook/2026-08-20-concurrency-on-the-cli-backend-changes-nothing.md).
- **The `confirm` pathway does not exist.** `de screen`, `de confirm` and
  `de report` are registered as deliberately absent, and `decision_evals.prereg`
  is the last entry in `[tool.decision-evals.unwired]`. Until they exist no
  skill can leave `UNTESTED` and `SCORECARD.md` cannot have a row.

---

## What would kill the whole programme

Written down now so a null is a result rather than a fourth dead corpus.

**0.** The process measure moves and the outcome measure does not, and this has
already happened to someone else, at scale. Agweyu et al. (2026, *Nature
Medicine*) cluster-randomized 103 clinical officers across 16 Kenyan primary care
facilities over 9,691 patients. LLM assistance raised note quality across every
domain and drove appropriate diagnosis to aOR 1.74 (p < 0.001). Treatment failure
was 2.2% against 2.0%, aOR 0.77, p = 0.13. The intervention visibly changed how
the work was written down and did not change what happened to the patients.

That is the shape of every result this repository has produced. M4, M5 and L5
each moved where the skill sits on a precision/recall frontier and none moved how
well it discriminates; the probe casefiles took 0 of 27 traps; `math` returned
`p_discordant` 0.000. Two independent lines of evidence now point the same way.

There is a competing explanation for the trigger half of that, found 2026-08-13.
The corpus those nulls were measured on is solved to 0.890 by counting words on
the version 2 key, against 0.9795 to 0.9863 for the best arm on the same key. A
flat result is what a real null looks like *and*
what a nine-point ceiling looks like, and this document had no way to tell them
apart because nobody had measured the ceiling. Track N measures it. Until it
lands, "nothing about a description changes discrimination" is one of two live
readings rather than the finding. That is the more important correction, because
the sentence had already been written down as though it were settled.

So the rule for Tracks C through F: name the outcome measure and the process
measure separately in the pre-registration, and state in advance that a process
gain with a flat outcome is a null for the skill, not a partial win. Writing
that after the run is how "the model produced a more thorough answer" becomes a
finding. The counterweight is Goh et al. (2024), +6.5pp on management reasoning
and +6.2pp on the case-specific domains, which is a process measure with an
expert rubric behind it and is the strongest located evidence for Track H. Both
are in [`docs/DECISION_FRAMEWORKS.md`](DECISION_FRAMEWORKS.md).

And the caveat that travels with both: clinicians *fully* adhered to the LLM's
advice in 19.5% of encounters. Advice given is not advice taken, and every
measurement in this repository is of advice given.

1. Track A comes back flat *and the MDE was below the effect the literature
   reports*. Both halves are required, and the second half was missing from an
   earlier draft, which made this the most dangerous sentence in the document.

   The arithmetic, using this repo's own `stats/power.required_pairs`: detecting
   a 12pp drop at 80% power needs roughly 127 pairs, or ~254 once the stated
   design effect of ~2.0 is applied. Track A had 12 items, which are also the
   clustering unit, so the cluster bootstrap ran on 12 clusters. A flat Track A
   would therefore have been the *expected* result whether or not the effect was
   real.

   Computed 2026-08-11, and it is worse than "underpowered". Run
   `python -m uv run de power`; the table is regenerated rather than transcribed,
   because a hand-copied power figure is the same class of error as a hand-copied
   citation.

   | n_pairs | p_d=0.15 | p_d=0.20 | p_d=0.30 | p_d=0.40 | p_d=0.50 |
   |---|---|---|---|---|---|
   | 12 | n/a | n/a | n/a | n/a | 46.5 |
   | 30 | n/a | 19.6 | 24.0 | 27.7 | 31.0 |
   | 100 | 9.5 | 11.0 | 13.5 | 15.6 | 17.4 |
   | 233 | 6.3 | 7.3 | 8.9 | 10.3 | 11.5 |
   | 527 | 4.2 | 4.8 | 5.9 | 6.8 | 7.6 |
   | 627 | 3.8 | 4.4 | 5.4 | 6.3 | 7.0 |

   Percentage points. `n/a` means no effect of any size is detectable at that
   item count. At 12 items every column but the last is `n/a`, and the last is
   46.5pp, larger than the entire −39% the multi-turn paper reports. The 12-item
   corpus could not have detected the effect it was built to detect. `p_d` is
   swept rather than chosen, because discordance is unknown before a screening
   run and Rule 1 forbids inventing it.

   This is now fixed for A1, and by the corpus rather than by argument, but at a
   smaller item count than first written here, and the correction is the
   instructive part.

   > Corrected the same day. An earlier version of this paragraph said 527
   > usable pairs. That is the count of records that are not the Unix-only
   > `code` family, and it silently assumed the *full* condition could be
   > reconstructed by joining the shards. It cannot. Joined shards read as a
   > bulleted decomposition, not as the original question: for one `database`
   > record the full question is *"which countries' tv channels are playing some
   > cartoon written by Todd Casey?"* against joined shards beginning *"tv
   > channels airing cartoons determine which countries…"*. Pairing those would
   > have compared sharded delivery against a third instruction we wrote, while
   > calling it the published design. Caught by checking the field rather than
   > assuming it.

   A full-setting instruction has to come from a field, and the schema is
   per-family:

   | Family | n | Full-setting field | Usable for A1 |
   |---|---|---|---|
   | `actions` | 105 | `fully_specified_question` | yes |
   | `database` | 107 | `fully_specified_question` | yes |
   | `math` | 103 | `question` | yes |
   | `summary` | 92 | `query`, but the task also carries `documents`, so `query` alone may not be the instruction | undecided |
   | `data2text` | 120 | none; the input is a table | no |
   | `code` | 100 | split `prompt` (45) / `question_content` (55) | excluded anyway (Unix-only eval) |

   So A1 is 315 pairs, giving an MDE of 5.4 to 9.9pp, or 7.6 to 13.9pp at the
   stated design effect of 2.0. Against −39% that is still a wide margin and a
   flat A1 would still be a real result: the conclusion survives, the number did
   not. `summary` is left undecided rather than folded in, because deciding it
   is choosing what the full instruction *is*, and that is exactly the kind of
   parameter Rule 1 forbids inventing.

   A2 is *not* covered by any of this: it needs a fixed turn count, and the
   largest single shard-count stratum is 233 records (MDE 6 to 12pp) before the
   full-instruction constraint is even applied.

   As written, this falsifier turned an underpowered null into a
   programme-terminating decision, the same "build first, check the premise
   later" error as the three dead corpora, run in reverse. And the two biases do
   not cancel: the author's documented bias is toward the experiment working, the
   design's bias is toward a null, and what that produces is a null that gets
   believed.

   So: Track 0 computes the MDE per experiment before Track A runs, the notebook
   records the MDE beside the point prediction, and item count is sized from it.
   A flat result at a 30pp MDE kills nothing.
2. Delegation never helps (A4). If a single well-prompted call always beats
   the orchestrated system on our tasks, sub-agents are a handicap rather than
   an architecture here, and the honest deliverable is a skill about *when not
   to delegate*.
3. Key amendment rate exceeds 20%. The corpus is retired and the run is not
   reported as a result. Given 21/21, this is the falsifier most likely to fire.
4. Placebo matches skill. The effect is instruction bulk, not content.
5. Chain-of-thought matches skill. The skill is a verbose CoT prompt in a
   markdown file.
6. Parse rates diverge by arm. The run is void. A skill that wins on
   accuracy while breaking the output contract has not won.
7. Scripted and real orchestration disagree (F). Internal validity without
   external validity, and the write-up has to say so rather than reporting the
   convenient number.

---

## The claim ladder

What we may honestly say, at each stage, and not before.

| After | We may claim |
|---|---|
| Track 0 | "We can run this experiment." Nothing about decisions. |
| Track N | "A firing result is about the description and not about turn length." Nothing above the ruler may be claimed before this row. With `N4` on top: "and it holds on turns a human wrote." |
| Track A | "These failure modes do / do not occur on frontier models in August 2026." |
| Track B | "We can attribute a system failure to a node, with reported agreement." |
| C / D / E | "A skill installed *here* changes *this* failure mode by *this much*." |
| Track F | "The system decides better end to end." |
| Track J | Any of the above, with an artifact someone else can re-run. |

Today we are entitled to the first row and not yet to the rest. Track 0 *is* built, every row 0.1 to 0.7 is done, and this sentence said otherwise until 2026-08-19, having been written before it completed.
