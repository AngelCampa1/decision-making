# Agent instructions

This file is read by Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
and others. Claude Code reads `CLAUDE.md`; the two carry the same content here.

**It is also the product.** Skill *availability* is the dominant term in whether
a skill helps at all. Two independent benchmarks agree on the direction:

| Source | Scale | Presence effect | On form |
|---|---|---|---|
| Xu & Wu, *Skill Availability and Presentation Granularity* (arXiv:2605.31408) | 30 tasks, 2 models | **+18 to +36pp** | granularity effects minimal, uncertain, model-dependent (+0.7pp, intervals crossing zero) |
| Li et al., *SkillsBench* (arXiv:2602.12670) | 87 tasks, 8 domains | **+16.6pp** (33.9 → 50.5) | focused bundles beat larger ones; self-generated skills ≈0 or negative |

So the block below is not documentation about the skills. It is the part that
makes them fire, and it is meant to be copied into your own project.

**And the block stays short on purpose — but read this as a design bet, not as a
measured result.** Expanding a skill library causes *skill shadowing*:
performance degrades "by up to 21% when scaling from a small set of helpful
skills to a **202-skill library**"
([arXiv:2605.24050](https://arxiv.org/abs/2605.24050), its own abstract).

The decision procedures live behind **one** entry rather than four because four
descriptions that all read as "help me decide" look like the same failure. **That
is an extrapolation and it should be labelled as one.** The published evidence
sits at 202 skills; the choice here was made at four. Nobody has measured
shadowing at n=4, and this repository has not either. Track M4 in
[`docs/RESEARCH_PROGRAMME.md`](docs/RESEARCH_PROGRAMME.md) is the experiment that
would settle it, and until it runs, one-entry-not-four is a judgement call
wearing a citation.

**M4 ran on 2026-08-12 and the citation has been replaced by a measurement that
does not support it.** 365 calls, 73 cases × 5 repeats, both arms, with the
four-skill arm's descriptions *derived* from this bundle rather than written, so
that only structure varied:

| | one entry | four entries |
|---|---|---|
| firing accuracy, 73 paired items | 0.956 | 0.951 — **paired Wilcoxon p = 0.83** |
| false-positive rate | 0.018 | **0.000** |
| recall | **0.878** | 0.800 |
| routing accuracy | 0.686 ± 0.108 | **0.786 ± 0.051** |

**Shadowing did not appear at four.** The stated mechanism — four descriptions
that all read as "help me decide" colliding — was not observed, and these four
share an opener and an exclusion list by construction. Four entries also *routed
better*, most sharply on the two items diagnosed that morning as **router-table**
defects (`p07` 1/5 → 5/5, `p03` 1/5 → 3/5), which was predicted in writing before
the run.

The trade is structural: with four entries, declining to name a tool *is*
declining to fire, so the arm never fires on a message it cannot route — fewer
false positives, more misses. Neither arm dominates, and which one is better
depends on whether a missed decision or an unwanted interruption is the more
expensive error, which nobody here has written down.

**M5 then ran the same four procedures across two entries, and the floor is
already there at two** — FPR 0.000 in all five repeats, firing accuracy 0.940
against the bundle's 0.956 (paired Wilcoxon p = 0.50). So the effect is not a
four-way artefact. Recall is *not* monotone in entry count (0.878 → 0.756 →
0.800) and M5 does not claim to explain that; n=2 is also the arm with the worst
prose, a confound registered before the run.

**Across M4, M5 and L5: nothing moved how well this description discriminates.
Structure, content and entry count each moved only where on the
precision/recall frontier it sits.**

**So the block below stays, and its justification changes.** One entry is not
retired on one run at one model tier — that would be acting on the measurement
that motivated the question. But the 202-skill result may no longer be cited as
though it reached down to four.
[`notebook/2026-08-12-m4-shadowing-did-not-appear-at-four.md`](notebook/2026-08-12-m4-shadowing-did-not-appear-at-four.md).

---

## Copy this into your project's `AGENTS.md` or `CLAUDE.md`

```markdown
## Decision skills

- **decision-making** — when someone is trying to decide something and wants help
  deciding it: "help me think this through", "should I take it", "what would you
  do", or a pile of context ending in a question about what to do. It routes to
  one of four procedures depending on what is actually hard — too much context,
  advice that may not fit this person, downstream consequences, or timing — and
  reads only that one. Skip it for lookups, for creative or exploratory work, and
  when the person wants information rather than a recommendation.

One entry, not four. Four separate decision skills would have four descriptions
that all read as "help me decide", and overlapping descriptions are the
mechanism by which agents pick the wrong skill.

Trust your own read on when it applies. It is a procedure, not a policy: if it
is producing worse answers than thinking directly, that is worth knowing and
worth saying.
```

The wording is deliberate. Trust-framed system prompts surfaced 59% more hidden
issues than unframed ones in a controlled comparison (arXiv:2603.14373), while
fear-framing — threats, consequences, "you MUST" — showed no gain over saying
nothing. So nothing here threatens the model, and the closing line invites it to
report that a skill is not working.

---

## Installing the skills

The canonical skills use only the six portable frontmatter fields defined by the
[Agent Skills standard](https://agentskills.io), so they need no conversion.

```bash
# Cross-tool: Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
cp -r .agents/skills/* ~/.agents/skills/

# Claude Code, project-scoped
cp -r skills/* .claude/skills/
```

Vendor-only frontmatter (`context: fork`, `disable-model-invocation`) is a hard
error in most of those tools, so it never appears in the canonical source. Any
Claude-specific keys live in the plugin overlay.

---

## What is actually proven

**Nothing yet.** `decision-making` carries `verdict: UNTESTED` and ships as
`experimental`, and so do all four procedures inside it. See
[`SCORECARD.md`](SCORECARD.md) for the verdict vocabulary and what each one
licenses you to claim.

That is not false modesty and it is not a reason to avoid it — use it if it
helps you. A verdict governs the *public claim*, not whether a skill is usable:
`UNTESTED` blocks entry to the shipped plugin, not `cp -r skills/*
.claude/skills/`. The distinction is the whole point of the repository — "we
have not shown this works" and "this works" are different statements, and
keeping them apart is the job. `de check` enforces the promotion rule rather
than trusting anyone to remember it.

---

## How this runs: a Claude Max subscription, not an API key

Every model call in this repository goes through the Claude Code CLI on the
maintainer's **Claude Max subscription**. There is no API key here and none
should be added.

**So the dollar figures are not money.** `total_cost_usd` in the CLI's JSON
output is a *notional API-equivalent price*. Nothing is billed per call. When a
run record says $0.23, that is what the same tokens would have cost on the API —
it is a unit of account, never an expense.

Two things follow, and both have been got wrong here before:

- **Do not design around dollars.** Do not drop a model tier, trim a stratum, or
  cut repeats to save money. There is no money to save. If an experiment needs
  Opus at 100k tokens to answer the question, that is not a cost decision.
- **There is still a budget — it just is not denominated in dollars.** The
  binding constraints are the subscription's rolling usage quota and wall-clock
  time. A 101k-token call takes about 8 seconds, so a confirmatory grid of ~800
  long calls is hours of serial running spread across days and windows. That is
  why the runner is checkpointed and resumable, and why `--model` tiers exist:
  to stay inside a quota, not inside a price.

`BudgetLedger` stays, reinterpreted. Reported cost scales with tokens, so it is
the best available **burn meter** for quota consumption. It is not a spend cap
and must not be described as one.

In the paper and in `results/`, this is reported as *notional cost*, with the
subscription stated. Writing "we spent $250" would be false.

---

## Working in this repository

If you are an agent contributing here rather than a user installing the skills:

- **You are probably not the only session in this directory.** The maintainer
  runs several in parallel. Files you did not write, commits you did not author,
  and a working tree that is dirty in places you never touched are **another
  session**, not corruption and not something to raise. Do not stop work over
  them, do not narrate them as unexplained, and do not offer to kill background
  processes. Just avoid clobbering: prefer `Edit` over `Write` on files you did
  not create this session, re-read before editing anything that may have moved,
  stage only your own paths, and say something only when an edit actually
  conflicts. This rule exists because both failure modes have already happened
  here on 2026-08-13 — one unattributed commit reported as a mystery, and one
  task abandoned mid-corpus to report four files that were simply somebody
  else's work in progress.

- **Work is sub-agent driven, reviews are adversarial, and no finding is
  believed until it is confirmed.** Maintainer instruction, 2026-08-13. Dispatch
  units of work to sub-agents and run the independent ones concurrently; give
  every artefact a *different* agent whose brief is to break it rather than
  approve it; and treat one agent's result as a hypothesis until an independent
  agent re-derives it from the raw records, or the run reproduces, or the
  reviewer's specific objection is checked and fails. A "looks good" review has
  not run. The full rule, and the history that produced it, is in
  [`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md) — every
  confident wrong number this repository has produced was caught by somebody
  checking, never by somebody being careful.

- **Run continuously. Quota is not a reason to hold back.** The stop-for-quota
  rule was removed on 2026-08-13. There is no money here; state a run's call
  count and then start it. The runner is checkpointed and resumable so that a
  grid spanning quota windows is a scheduling detail, not a decision.

- **The experiment programme lives in
  [`docs/RESEARCH_PROGRAMME.md`](docs/RESEARCH_PROGRAMME.md)** — the goal, what
  the literature already settles, and fifteen tracks you can be pointed at.
  Start there before proposing experiment work. **Track K runs first** (the
  decision-frameworks review, free, no instrument), **Track S runs in parallel
  from day one** (the skills themselves), and Track 0 blocks the measurement
  but not the skills.
- The long-context experiment
  ([`docs/superpowers/plans/2026-08-11-long-context-experiment.md`](docs/superpowers/plans/2026-08-11-long-context-experiment.md))
  is now **Track G** and its pilot-library authoring is on hold. Read it for the
  gate machinery, not for the priority.
- **If you are running unattended for hours or days, read
  [`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md) first.** It
  says what may run without a human and what to stop for. Every rule in it
  exists because that failure already happened here.
- `python -m uv run de check` is the full local gate — lint, types, tests,
  coverage floors, skill validation, run provenance and integrity wiring. There
  is no cloud CI. Run it before you believe anything works.
- **A published run must carry its own provenance, and the gate enforces it.**
  `results/<skill>/<date>-<sha7>[-slug]/README.md` must declare
  `**Answer key:** <label set> v<n>` matching the `set_version` in the records
  beside it, and must carry a `Prediction:` line naming a notebook entry whose
  first commit is an ancestor of the run's commit. A prediction that cannot be
  shown to predate its data is not evidence. Two pre-convention runs are
  baselined by name in `results/provenance-baseline.txt`; that list may only
  shrink. Regenerate `docs/RUN_INDEX.md` with `de index` — `de check` fails when
  it is stale.
- **A change to `datasets/triggers/` or `skills/` needs an entry in
  [`docs/DECISIONS.md`](docs/DECISIONS.md).** Those are the answer key and the
  product; a change to either moves numbers that are already published, and a
  label move is invisible in a checkpoint. `de check` refuses a governed commit
  with no entry, and refuses an entry naming a commit that touched neither path.
  Commit bodies are not the store: the history is the pre-registration evidence
  and cannot be rewritten, so a trailer somebody forgot would be permanently
  unfixable.
- **A coverage floor does not mean a module runs.** `de check` refuses a floored
  module that no entry point can reach, because this repository has now shipped
  two of them: `triggers` was tested to 100% and called by nothing while a
  trigger set described a skill that no longer existed, and `prereg.py` carries
  every refusal `docs/PROTOCOL.md` §3 promised while nothing calls it. A tested
  refusal with no caller is inert, and the gate reports green either way.
  Intentional gaps go in `[tool.decision-evals.unwired]` with the condition that
  would close them.
- **The documentation is checked mechanically, and it catches a reference that
  does not resolve — not a description that is wrong.** `de check` refuses a
  `de <cmd>` naming a command that does not exist, a markdown link or repository
  path that does not exist, and a README component table that disagrees with the
  directory listing. It was added on 2026-08-13 after the README was found
  telling readers to run `de screen` and `de confirm` — neither a command — and
  advertising a `preregistration/` directory that has never existed, while
  omitting `paper/` and `scripts/`; `SCORECARD.md` had already corrected a
  fourth of the same shape, `de report`. Four instances, one file each, none
  caught by anything, because documentation was the last obligation here checked
  by reading it.

  **What the gate cannot see is the failure that motivated it.**
  `docs/PROTOCOL.md` §3 described a refusal that has never run, in the present
  indicative, with every path in it correct. So: *prose describing a mechanism
  must name the arena it runs in and the tense it runs in.* If a gate is scoped
  to `confirm` and `confirm` has never run, the sentence says **will refuse**,
  not *refuses*. That one is on you; nothing checks it.

  Scope is the living documentation — root `*.md` and `docs/*.md`. `notebook/`,
  `results/**/README.md` and `docs/DECISIONS.md` are excluded **on purpose**:
  they are dated records of what was true when written, and a decision that
  removed a file necessarily names the file it removed. Do not "fix" a stale
  reference in any of them. Deliberately absent commands go in
  `[tool.decision-evals.docs-absent-commands]`, which may only shrink.
- **A published run updates `docs/STATUS.md` in the same change.** It is the
  ledger and it is hand-maintained, so it is the one file that drifts silently:
  on 2026-08-13 its summary line read "six results, five measurements" while the
  two tables underneath it listed seven and eight. A count in prose that is not
  recomputed from the table below it is a hand-maintained number like any other.
  Corrections there are appended, not rewritten.
- Commits must be attributed to the GitHub noreply address; `de check` refuses
  otherwise.
- Golden files pin the generated corpus byte-exact. Regenerating them needs
  `pytest --bless` and the diff belongs in review — a benchmark that changes
  silently makes every earlier number incomparable with every later one.
- `notebook/` is append-only and dated. Predictions go in *before* runs. If a
  prediction turns out wrong, the entry says so rather than being edited.
- **A recall band is set against the observed per-item ceiling, not a round
  number.** Track L7 registered "at least one arm reaches recall >= 0.94" over
  17 positives, which needs 16 of 17 — and `x-n22` has never fired in any arm on
  any version, a fact stated in that same prediction's *"where I expect to be
  wrong"* section. The ceiling was 0.941 and the band demanded perfection on
  everything else. This is the fifth pre-registration defect on record and the
  first that was visible **before** the run rather than after, which makes it
  the cheapest one to have avoided. Compute the ceiling from the per-item
  history, then set the band under it.
- **A registered band names its estimator and its denominator, not just its
  number.** Four pre-registration slips happened here on 2026-08-12 alone: a band
  asking for `p_discordant` on two task families that have no correctness measure
  available, so it could not be scored at all; an entry written after its run had
  started; a 365-call run launched with no bands at all; and M5's `covers` band,
  which named the measure but not what it divided by — 0.743 over all labelled
  calls, 0.895 over the calls that fired. Both fell inside the band, so that one
  cost nothing, which is luck rather than method. Each was recorded rather than
  quietly dropped, which is the minimum — but the fix is upstream. Before
  starting a run, write down what will be computed, from which records, over
  which denominator, by which function. If that sentence cannot be written, the
  run is not ready.
- **A change to the answer key is a change to every number ever computed from
  it.** On 2026-08-13 one turn moved from the positives to the negatives, on a
  maintainer decision that was correct. Recall rose 3 to 5 points on every arm
  on disk and **not one call was re-made**; the shipped skill gained five points
  it did nothing to earn. The checkpoints were valid, every instrument check
  passed, the parse rate was 100%, and the number moved the way an author would
  like. Unlike the three earlier defects of this shape it was **not a bug** —
  which is what makes it worse, because nothing in a record distinguishes a
  label correction from a model result. Version the key, stamp the version into
  every record, and refuse to compare across versions
  (`trigger_arms.label_versions_comparable`). Remembering does not work; the
  count is four for four.
- **An estimator that cannot return a non-zero value is not a measurement, and
  it does not announce itself.** Two defects in the trigger instrument on
  2026-08-12 each produced a clean run, a full checkpoint and a plausible zero:
  a parser whitelist that discarded every tool name an n=2 arm could offer, and a
  routing report that graded those names against names the arm never offered.
  Nothing crashed and firing was correct in both. **Before believing an outcome,
  check that some possible response would have scored above zero for this arm.**
- **And the estimator must be checked against the arm structure, not only against
  the records.** On 2026-08-12 a 50-pair run produced 45/50 against 23/50 with
  discordance 24-to-2 in the predicted direction — a clean replication, and
  entirely an artefact of a scorer reading `final_response` when one arm had a
  single turn and the other had six. Crediting the whole conversation reversed
  the direction. Before a run: does the scorer read the *same object* in every
  arm? A measure that is legitimate for one arm can be a turn-count proxy for
  another.
