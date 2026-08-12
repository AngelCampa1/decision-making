# Agent instructions

This file is read by Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
and others. Claude Code reads `CLAUDE.md`; the two carry the same content here.

**It is also the product.** Skill *availability* is the dominant term in whether
a skill helps at all — SkillsBench measures a large gain from having the right
skill present against +0.7pp from polishing its prose, with intervals crossing
zero. So the block below is not documentation about the skills. It is the part
that makes them fire, and it is meant to be copied into your own project.

> The presence figure previously read "+18 to +36pp" here. A 2026-08-11
> literature check surfaced the paper's headline as **+16.6pp** average
> (33.9 → 50.5). Both are under re-check against arXiv:2602.12670 before either
> is asserted again — see Track K in
> [`docs/RESEARCH_PROGRAMME.md`](docs/RESEARCH_PROGRAMME.md).

---

## Copy this into your project's `AGENTS.md` or `CLAUDE.md`

```markdown
## Decision skills

Reach for these when the shape of the problem matches. They are cheap to enter
and cheap to leave — each one opens with the conditions under which it should
skip itself, so invoking one on a case it does not fit costs a few tokens rather
than a detour.

- **evidence-ledger** — when a decision depends on a pile of accumulated context
  (a long thread, pasted logs, search results, a channel backlog) and what the
  answer turns on has to be separated from what merely arrived. Skip it for a
  short prompt with one or two facts, or a lookup with one obvious source.

- **switching-conditions** — when someone asks what *they* should do and the
  right answer turns on facts about them: the offer, the move, the lease, the
  course, whether to tell them. Gives the generic answer first, then the facts
  that would overturn it and the threshold at which each one bites. Skip it when
  the answer is the same for everyone.

- **consequence-cascade** — when an action looks fine on its own and the worry is
  what it sets in motion, or which option it quietly spends. Follows the chain to
  the point where it stops being knowable, and checks whether the order of two
  steps matters. Skip it for contained, reversible, low-stakes moves.

- **decide-or-wait** — when the question is timing rather than direction, or when
  something feels urgent and it is not clear the urgency is real. Prices the
  undo, separates the real deadline from the felt one, and often splits the move
  into a part to do now and a part to defer. Skip it while what to do is still
  unsettled.

Trust your own read on when these apply. They are procedures, not policies:
if one of them is producing worse answers than working directly, that is worth
knowing and worth saying.
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

**Nothing yet.** All four skills carry `verdict: UNTESTED` and ship as
`experimental`. See [`SCORECARD.md`](SCORECARD.md) for the verdict vocabulary
and what each one licenses you to claim.

That is not false modesty and it is not a reason to avoid them — use them if
they help you. A verdict governs the *public claim*, not whether a skill is
usable, and `UNTESTED` blocks entry to the shipped plugin rather than blocking
`cp -r skills/* .claude/skills/`. It is the difference between "we have not shown this works" and
"this works", and the whole point of the repository is to keep those two
statements apart. A skill may not enter the shipped plugin while carrying
`UNTESTED`; `de check` enforces that rather than trusting anyone to remember it.

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
  the literature already settles, and fourteen tracks you can be pointed at.
  Start there before proposing experiment work. **Track K runs first** (the
  decision-frameworks review, free, no instrument), **Track S runs in parallel
  from day one** (the skills themselves), and Track 0 blocks the measurement
  but not the skills.
- The long-context experiment
  ([`docs/superpowers/plans/2026-08-11-long-context-experiment.md`](docs/superpowers/plans/2026-08-11-long-context-experiment.md))
  is now **Track G** and its pilot-library authoring is on hold. Read it for the
  gate machinery, not for the priority.
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
