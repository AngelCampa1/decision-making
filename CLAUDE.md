# Agent instructions

Read by Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode and others.
Claude Code reads `CLAUDE.md`, a byte-exact mirror written by `de mirror`.
**Edit this file only.** `de check` refuses a stale mirror.

Every rule here exists because that failure already happened. The dated
incidents, the measurements and the citations behind them are in
[`docs/WHY_THESE_RULES.md`](docs/WHY_THESE_RULES.md), which nothing loads per
turn. Read a section there when you want to know why a rule is worded the way it
is.

## Copy this into your project's `AGENTS.md` or `CLAUDE.md`

```markdown
## Decision skills

- **decision-making** — when someone is trying to decide something and wants help
  deciding it: "help me think this through", "should I take it", "what would you
  do", or a pile of context ending in a question about what to do. It routes to
  one of six procedures depending on what is actually hard — too much context,
  advice that may not fit this person, downstream consequences, timing, several
  positions that are each defensible, or a missing fact that may or may not
  matter — and reads only that one. Skip it for lookups, for creative or exploratory work, and
  when the person wants information rather than a recommendation.

One entry, not four. Four separate decision skills would have four descriptions
that all read as "help me decide", and overlapping descriptions are the
mechanism by which agents pick the wrong skill.

Trust your own read on when it applies. It is a procedure, not a policy: if it
is producing worse answers than thinking directly, that is worth knowing and
worth saying.
```

Do not reword that block. It is the install artefact and the measured wording.
Why it is one entry: [`docs/WHY_THESE_RULES.md`](docs/WHY_THESE_RULES.md).

## Installing the skills

```bash
# Cross-tool: Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
cp -r .agents/skills/* ~/.agents/skills/

# Claude Code, project-scoped
cp -r skills/* .claude/skills/
```

Canonical skills carry only the six portable frontmatter fields of the
[Agent Skills standard](https://agentskills.io). Vendor-only keys
(`context: fork`, `disable-model-invocation`) are a hard error in most of those
tools and live in the plugin overlay.

## What is proven

Nothing yet. `decision-making` and all six procedures carry `verdict: UNTESTED`
and ship as `experimental`. A verdict governs the public claim and says nothing
about whether the skill is usable. See [`SCORECARD.md`](SCORECARD.md).

## Cost

Every model call goes through the Claude Code CLI on a Claude Max subscription.
There is no API key and none may be added. `total_cost_usd` is a notional
API-equivalent price: a burn meter, never an expense and never a spend cap.
Report it as notional cost.

Never drop a model tier, trim a stratum or cut repeats to save money. The budget
is the rolling quota and wall-clock time, which is why the runner is
checkpointed and resumable. Nothing may be bought: no paid APIs, datasets or
tooling. "Vendoring" means checking a copy into `datasets/vendor/`.

---

# Working in this repository

Read [`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md) first. It
carries the five standing rules, the sub-agent and adversarial-review method,
where a worktree goes and what it needs, and the ordered landing sequence. What
follows is a summary of it, not a replacement.

## Other sessions

Several run here at once. Files you did not write, commits you did not author
and a tree dirty in places you never touched belong to another session. Do not
stop, do not narrate them, do not kill their processes. Prefer `Edit` over
`Write` on files you did not create this session, re-read before editing, stage
only your own paths, and speak up only on a real conflict. Never `git stash` in
a shared tree: `git show HEAD:<path>` and `git diff -- <path>` answer the same
question without touching anyone else's work.

## Worktrees

Any session running longer than a few minutes gets its own tree, its own
`.venv`, its own gate.

```bash
git worktree add -b <topic> .claude/worktrees/<topic> origin/main
cd .claude/worktrees/<topic>
python -m uv sync --group dev
python -m uv run de fetch
```

Never run a recursive delete or a forced clean at the repository root. Other
sessions' worktrees sit in that blast radius.

Rejoin at least daily and at least every ten commits, and push even when the
work is unfinished:

```bash
git fetch origin && git rebase origin/main && git push -u origin <topic>
```

Land by merging from a green worktree. `--no-verify` is not how a red gate gets
resolved. **Commit, do not stage:** a gate that runs in the working tree cannot
see what the commit is missing. Then prove it landed:

```bash
git fetch origin
git rev-parse main origin/main                             # two identical lines
git merge-base --is-ancestor <your-topic-sha> origin/main  # exit 0 means landed
```

Never `git push origin <topic>:main`, which moves the remote and leaves local
`main` where it was. Never `git update-ref refs/heads/main`, which bypasses the
checked-out protection and leaves that worktree showing deletions nobody made.
`main` is usually checked out somewhere, so read `git worktree list` first and
fast-forward it in place:

```bash
git -C <the-worktree-holding-main> merge --ff-only origin/main
```

The full order, deploy confirmation and cleanup are in
[Landing the work](docs/AUTONOMOUS_WORK_ORDER.md#landing-the-work).

## Method

Dispatch units of work to sub-agents and run the independent ones concurrently.
Give every artefact a different agent briefed to break it. Treat one agent's
result as a hypothesis until an independent agent re-derives it from the raw
records, the run reproduces, or the reviewer's specific objection is checked and
fails. A "looks good" review has not run.

Run continuously. Quota is not a reason to hold back: state a run's call count,
then start it.

## The gate

```bash
uv sync --group dev
python -m uv run de check              # the full local gate
python -m uv run de check --fast       # pre-commit subset: no tests, coverage or site
python -m uv run pytest tests/unit/test_claims.py
```

`uv` is not on `PATH` here, hence `python -m uv`. Run the full gate before
believing anything works. It also runs in CI (`.github/workflows/check.yml`) on
a clean checkout, which sees what a working directory cannot. A second workflow,
`deploy-site.yml`, publishes the site and checks nothing.

## Where the code is

`evals/src/decision_evals/` is the harness and the gates. `cli.py` wires every
`de check` step, and each step lives in the module it is named after: `docs.py`,
`citations.py`, `provenance.py`, `decisions.py`, `wiring.py`, `skills.py`.
`scripts/run_triggers.py` is the runner behind every model call on record.
`datasets/` is the answer key, `skills/` the product, `results/` and `notebook/`
the record. `README.md` carries the component table and
[`docs/RESEARCH_PROGRAMME.md`](docs/RESEARCH_PROGRAMME.md) carries the tracks.

## Standing obligations

- **Editing a document means rebuilding the site in the same change.** Run
  `python -m uv run de mirror` first if you touched `AGENTS.md` or `skills/`,
  because `CLAUDE.md` is itself a site input. Then `python -m uv run de site`.
  `de check` refuses a stale `site/build-manifest.json` and names the files that
  moved. Merging to `main` deploys; `python -m uv run de deployed` says whether
  it landed, and exit 2 means it could not tell.
- **A published run carries its own provenance.**
  `results/<skill>/<date>-<sha7>[-slug]/README.md` declares
  `**Answer key:** <label set> v<n>` matching the `set_version` in the records
  beside it, and a `Prediction:` line naming a notebook entry whose first commit
  is an ancestor of the run's commit. Two pre-convention runs are baselined in
  `results/provenance-baseline.txt`; that list may only shrink. Regenerate
  [`docs/RUN_INDEX.md`](docs/RUN_INDEX.md) with `de index`.
- **A published run updates [`docs/STATUS.md`](docs/STATUS.md) in the same
  change.** Corrections there are appended, never rewritten.
- **A change to `datasets/triggers/`, `datasets/tailoring/` or `skills/` needs
  an entry in [`docs/DECISIONS.md`](docs/DECISIONS.md).** Commit bodies are not
  the store.
- **Every third published run, sweep `README.md` and `docs/` for drift** and
  land the sweep as a dated `notebook/` entry. Count runs from
  [`docs/RUN_INDEX.md`](docs/RUN_INDEX.md), which is generated and cannot
  itself drift. Recompute every count stated in prose against the table beneath
  it, re-read [`docs/README.md`](docs/README.md) as an index, and read the
  living documents for a description that has stopped being true. Nothing checks
  this.
- **A coverage floor does not mean a module runs.** `de check` refuses a floored
  module that no entry point can reach. Intentional gaps go in
  `[tool.decision-evals.unwired]` with the condition that would close them.
- **The documentation gate catches a reference that does not resolve, never a
  description that is wrong.** Scope is root `*.md` and `docs/*.md`.
  `notebook/`, `results/**/README.md` and [`docs/DECISIONS.md`](docs/DECISIONS.md)
  are excluded as dated records, so do not "fix" a stale reference in them.
  Deliberately absent commands go in
  `[tool.decision-evals.docs-absent-commands]` and deliberately untracked paths
  in `[tool.decision-evals.docs-ignored-paths]`. Both may only shrink, and both
  refuse an entry named nowhere in the scanned documentation. Prose describing a
  mechanism names the arena and the tense it runs in: a gate scoped to an arena
  that has never run **will refuse**, it does not refuse.
- **All prose goes through [`docs/VOICE.md`](docs/VOICE.md) and the humanizer
  skill**, including comments and docstrings. Review with
  [`docs/reviews/HOUSE_STYLE.md`](docs/reviews/HOUSE_STYLE.md) and
  [`docs/reviews/POSITIONING.md`](docs/reviews/POSITIONING.md). Nothing checks
  this. Three things the pass may never do:
  - **Change a number, a confidence interval, a p-value, an arXiv identifier or
    a quoted sentence.** The rule that a `paper/refs.bib` entry must carry a
    quote before a number may be asserted beside it is scoped to the markdown
    **block**, so rewrapping alone can move a claim number into a block whose
    identifier has no quote behind it and turn a green gate red.
  - **Delete a correction that a register depends on.** Nothing stops you.
  - **Flatten a hedge that carries epistemic status.** Collapse stacked hedges
    and leave the load-bearing one.
- **`skills/decision-making/SKILL.md`'s description is the measured artefact.**
  `scripts/run_triggers.py` reads that field and nothing else, so rewriting it
  makes every published number incomparable. It changes only as a deliberate new
  arm with an entry in [`docs/DECISIONS.md`](docs/DECISIONS.md).
- Commits are attributed to the GitHub noreply address; `de check` refuses
  otherwise.
- Golden files pin the generated corpus byte-exact. Regenerating them needs
  `pytest --bless` and the diff belongs in review.
- `notebook/` is append-only and dated. Predictions go in before runs, and a
  prediction that turned out wrong stays and says so.

## Before any run

- Write down what will be computed, from which records, over which denominator,
  by which function. If that sentence cannot be written, the run is not ready. A
  registered band names its estimator and its denominator, not just its number.
- Set a recall band **under** the observed per-item ceiling, computed from the
  items you are about to run. Check the `ancestry:` block in
  `datasets/triggers/decision-making/index.yaml` before carrying a per-item fact
  across corpus versions.
- Check that some possible response would have scored above zero for this arm,
  and that the scorer reads the same object in every arm.
- Version the answer key, stamp the version into every record, and refuse
  comparisons across versions (`trigger_arms.label_versions_comparable`).
