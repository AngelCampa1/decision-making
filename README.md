# decision-making-skills

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange.svg)](docs/STATUS.md)
[![Verdict](https://img.shields.io/badge/verdict-UNTESTED-lightgrey.svg)](SCORECARD.md)

Agent skills for making better decisions under uncertainty — and an evaluation
harness that measures whether they actually work.

> **Status: pre-alpha. No skill in this repository has been validated yet.**
> The harness is being built first, deliberately. Until a skill carries a
> verdict in [`SCORECARD.md`](SCORECARD.md), treat it as an untested hypothesis.
>
> **[`docs/STATUS.md`](docs/STATUS.md) is the ledger** — every run on record,
> what it showed, which measurements turned out to be broken, and which tracks
> are still untouched.

## The skill

One skill, `decision-making`, that routes to one of four procedures depending on
what is actually hard about the decision — and reads only that one.

| What is hard | Procedure | What it produces |
| --- | --- | --- |
| A pile of context arrived and it is unclear what the answer turns on | [`ledger.md`](skills/decision-making/ledger.md) | what bears on it, what was set aside, and why |
| The advice may be generically right and wrong for this person | [`fit.md`](skills/decision-making/fit.md) | the generic answer, and the facts that would overturn it |
| The action looks fine and the worry is what it starts, or what it spends | [`cascade.md`](skills/decision-making/cascade.md) | the chain, what it forecloses, and the order |
| The direction is settled and the question is when | [`timing.md`](skills/decision-making/timing.md) | the undo price, the real deadline, what waiting buys |

Where more than one applies they run in the order **ledger → fit → cascade →
timing**, because each supplies an input to the next. A fifth file,
[`placebo.md`](skills/decision-making/placebo.md), is the token- and
structure-matched control arm; it ships alongside because a skill that only
beats nothing has not been measured against the thing that would fake it.

### Installing

The skills use only the six portable frontmatter fields defined by the
[Agent Skills standard](https://agentskills.io), so they need no conversion.

```bash
# Cross-tool: Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
cp -r .agents/skills/* ~/.agents/skills/
```

```bash
# Claude Code, project-scoped
cp -r skills/* .claude/skills/
```

There is also a Claude Code plugin, and **it currently ships nothing**.
`plugin/skills/` is empty because a skill is copied there only once a
confirmation run gives it a verdict — see
[`plugin/skills/README.md`](plugin/skills/README.md). Copying from `skills/` is
the way to use this today.

Nothing here is proven, and that is not a reason to avoid it. A verdict governs
the *public claim*, not whether a skill is usable.

## Why this exists

Agents fail at decisions in three separable ways:

1. **Unranked context.** Everything retrieved is weighted roughly equally. Tell
   an agent it's raining in Paraguay while planning a trip to Lisbon and it will
   suggest a raincoat — the information arrived, so it must be used somehow.
2. **Uncalibrated probability.** Stated confidence doesn't track observed
   frequency, and RLHF makes this worse rather than better.
3. **Uniform deliberation budget.** A one-way door and a trivially reversible
   choice get the same amount of thought.

Plenty of prompt libraries claim to fix this. The closest prior art ships 28
thinking skills and states in its own README that none is proven to improve
model accuracy. That is not an argument against skills — the published evidence
says having the right skill available is worth a great deal — it is an argument
for building the feedback loop that tells you *which* ones help, and by how much.

## What's actually here

| Component | Purpose |
| --- | --- |
| `skills/` | The skills, authored to the [Agent Skills](https://agentskills.io) 6-field standard so they work in Claude Code, Codex, Cursor, Copilot, Gemini CLI, Cline, Amp and OpenCode without conversion. Mirrored byte-for-byte to `.agents/skills/` by `de mirror` |
| `plugin/` | The Claude Code plugin. A skill is copied here only once a confirmation run gives it a verdict, so the directory is currently empty on purpose |
| `evals/` | `decision_evals` — the harness. Paired experiments, exact tests, cluster-aware resampling |
| `datasets/` | The answer key: parameterised scenario templates with *computed* ground truth, and the trigger corpus |
| `results/` | Published run records — raw transcripts and a README per run |
| `notebook/` | Append-only research log. Predictions go in *before* runs |
| `docs/` | Protocol, status, the research programme, related work, limitations, and what was rejected. Start at [`docs/README.md`](docs/README.md) |
| `paper/` | The write-up, in LaTeX. A draft; see [`paper/CHECKLIST.md`](paper/CHECKLIST.md) |
| `scripts/` | Standalone analysis and runners, including `run_triggers.py` — the script behind every model call on record |
| `tests/` | Unit, integration, property and golden tests |

## What has been measured

**Nothing about whether a decision skill improves a decision.** Every number on
record measures something upstream of that: whether a skill *fires* when it
should, which is the question that decides whether it is worth having installed
at all.

About 4,240 model calls, of which 2,555 are the trigger instrument. Seven
results are in — [`docs/STATUS.md`](docs/STATUS.md) has all of them with links
to the data. The through-line:

> Five independent manipulations of a skill description — structure, content,
> entry count, composition twice — and **not one moved how well it
> discriminates.** Every one moved only where it sits on the precision/recall
> frontier.

Two findings worth naming here because they cut against what this repository
originally claimed:

- **Skill shadowing did not appear at four entries.** One entry and four
  separate entries were indistinguishable on firing accuracy (0.956 vs 0.951,
  paired Wilcoxon p = 0.83). The
  [202-skill shadowing result](https://arxiv.org/abs/2605.24050) may no longer
  be cited as though it reached down to four.
- **The corpus behind every one of those numbers is 89% solvable by counting
  words.** Turn length alone separates the labels at AUC 0.850, and a bare
  *"fire if ≥ 18 words"* rule scores 0.890 with no model at all — against a best
  measured arm of 0.956. So every result above was competing for about six
  points over a ruler, and five nulls is also what a ceiling looks like. Both
  readings must be reported until the corpus is rebuilt, which is
  [Track N](docs/RESEARCH_PROGRAMME.md).

## How claims are made

Every skill is measured against four arms on the same items — **off**,
**on**, **placebo** (token- and structure-matched filler), and **cot** (plain
"think step by step"). A skill that beats *off* but not *placebo* is a length
effect. A skill that doesn't beat *cot* is an expensive way to say "think."

The statistics are exact and resampling-based rather than CLT-based, because at
our item counts the normal approximation isn't reliable. Templates rather than
items are the resampling unit, since items from one template are correlated.
Calibration is reported with the Murphy decomposition, so a "skill" that
improves Brier by hedging every forecast toward the base rate is caught by the
resolution term instead of being scored as a win.

### Pre-registration: two mechanisms, and only one of them has ever run

**This section used to describe the second as though it were the first.** It
read *"a confirmation run refuses to start unless the pre-registration file is
committed, predates the results, and its recorded hash still matches the skill
on disk"* — present tense, and pointed at a `preregistration/` directory that
has never existed. It also told you to run `de screen` and `de confirm`, neither
of which is a command. The correction is
[`docs/PROTOCOL.md`](docs/PROTOCOL.md) §3, split in two:

- **The standing mechanism, which every run on record actually used:** a dated
  prediction committed to [`notebook/`](notebook/) *before* the run. This is
  enforced — `de check` refuses a published run whose README does not name a
  prediction whose first commit is an ancestor of the run's commit.
- **The hash-locked refusal, which is built, tested, and has never run.** It is
  scoped to the `confirm` arena, and no confirmation run has happened. The
  module carries a 100% branch floor and no caller, which is why it is declared
  in `[tool.decision-evals.unwired]` — a tested refusal that nothing calls is
  inert, and the gate reports green either way.

The model calls on record were made by [`scripts/run_triggers.py`](scripts/run_triggers.py).

Verdicts govern the *public claim*, not your ability to use something. A skill
that comes back `NULL` goes back to the workbench and ships as `experimental` —
available, just not claimed as proven.

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
```

Run the full local gate — lint, types, tests, coverage floors, and the
repository-integrity checks:

```bash
uv run de check
```

There is no cloud CI. `de check` is bound to `pre-commit` (fast subset) and
`pre-push` (everything), so a red tree can't be pushed. It makes no model calls;
model-backed evaluation is run explicitly from [`scripts/`](scripts/).

Five of its steps check the method rather than the code, each one added after
the failure it prevents had already happened here:

| Step | Refuses |
| --- | --- |
| trigger sets | a skill with no trigger set, or a trigger set naming a skill that no longer exists |
| run provenance | a published run that does not state its answer-key version, or whose prediction cannot be shown to predate its data |
| integrity wiring | a module with a coverage floor that no entry point can reach |
| decision register | a change to the answer key or the shipped skill with no entry in [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| documentation | a `de` command, path, or component that this README names and the repository does not have |

The other commands: `de index` regenerates
[`docs/RUN_INDEX.md`](docs/RUN_INDEX.md), `de mirror` regenerates the cross-tool
skill copies, `de lint` checks skill frontmatter and the promotion gate,
`de power` prints a minimum-detectable-effect table, and `de fetch` downloads
the hash-pinned third-party corpora.

> **Note:** if `uv` was installed with `pip install uv`, its executable may not be
> on `PATH`. On Windows it lands in
> `%APPDATA%\Python\Python313\Scripts`. Add that directory to `PATH`, or invoke
> it as `python -m uv`.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The short version: run `de check`
before believing anything works, put predictions in the notebook before runs,
and never edit a notebook entry after the fact — append a correction instead.

## License

Apache-2.0. See [LICENSE](LICENSE).
