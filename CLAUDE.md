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
  coverage floors, skill validation. There is no cloud CI. Run it before you
  believe anything works.
- Commits must be attributed to the GitHub noreply address; `de check` refuses
  otherwise.
- Golden files pin the generated corpus byte-exact. Regenerating them needs
  `pytest --bless` and the diff belongs in review — a benchmark that changes
  silently makes every earlier number incomparable with every later one.
- `notebook/` is append-only and dated. Predictions go in *before* runs. If a
  prediction turns out wrong, the entry says so rather than being edited.
