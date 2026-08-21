<div align="center">

<picture class="gh-only">
  <source media="(prefers-color-scheme: dark)" srcset="site/public/lockup-dark.png">
  <img src="site/public/lockup-light.png" alt="decision-making-skills" width="440">
</picture>

[![Check](https://github.com/AngelCampa1/decision-making-skills/actions/workflows/check.yml/badge.svg)](https://github.com/AngelCampa1/decision-making-skills/actions/workflows/check.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange.svg)](docs/STATUS.md)
[![Verdict](https://img.shields.io/badge/verdict-UNTESTED-lightgrey.svg)](SCORECARD.md)

</div>

**Audience:** anyone deciding whether this is worth their attention.

Two things live here.

**An agent skill for decisions.** It works out what is *hard* about the choice
before it answers, then runs one of six procedures built for that specific
difficulty. Paste in the whole thread and ask what to do about Tuesday:

```text
LEDGER
  1. the Lisbon forecast — decides what to pack
  2. the Tuesday flight — decides when

SET ASIDE
  - the rain in Paraguay — your trip does not touch it

THEREFORE
  pack for Lisbon
```

That is `ledger.md`, the one for when too much context arrived and you cannot
see which fact decides it. The other five handle advice that is generically
right and may be wrong for you, consequences you did not price, timing, several
positions that are each defensible, and a missing fact that may or may not
matter.

**And `decision_evals`, the harness built to find out whether any of that
helps.** It relabels its own answer key with a blind panel of three model
instances and reports their agreement chance-corrected. It stamps an answer-key
version into every record and refuses, in code, to compare arms across a version
boundary. It pins MCP empty at every call, because a connector present in one
arm and absent in another is a confound. And it refuses to publish a result
whose prediction cannot be shown by git ancestry to predate its data. Thirteen
runs are published under those rules, raw transcripts included.

What they have found so far is about *firing*: whether a skill switches on when
it should. Rewriting the skill's description five different ways changed which
mistakes it made, trading missed decisions against unwanted interruptions, and
never changed how well it told the two apart. Then the harness was pointed at
its own test set, and a rule as crude as *fire if the question is long* scored
close to the real thing. That finding retired the test set and paid for the
rebuilt one every result since has run on.

One of those runs was aimed at this repository's own argument. A published
result says that a large skill library crowds out the right skill, and this
README used to cite it as the reason the skill ships as one entry instead of
four. The run found nothing of the kind at four entries, so the citation was
retired from the claim it was supporting and the four-entry arm turned out to
route better.

No skill here carries a verdict yet, so [`SCORECARD.md`](SCORECARD.md) is empty
and [`docs/STATUS.md`](docs/STATUS.md) is the ledger of every run on record.
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) draws how the skill, the harness,
the datasets and the gate fit together.
The skill is free, installs in one line, and comes out again in one line.

## The skill

One skill, `decision-making`. Its router asks a single question, *what is hard
here?*, and the answer selects one of six procedures. It reads only that one.

| What is hard | Procedure | What it produces |
| --- | --- | --- |
| A pile of context arrived and it is unclear which fact decides it | [`ledger.md`](skills/decision-making/ledger.md) | what bears on it, what was set aside, and why |
| The advice may be generically right and wrong for this person | [`fit.md`](skills/decision-making/fit.md) | the generic answer, and the facts that would overturn it |
| The action looks fine and the worry is what it starts, or what it spends | [`cascade.md`](skills/decision-making/cascade.md) | the chain, what it forecloses, and the order |
| The direction is settled and the question is when | [`timing.md`](skills/decision-making/timing.md) | the undo price, the real deadline, what waiting buys |
| Several positions are each defensible, and whichever was argued first has the advantage | [`council.md`](skills/decision-making/council.md) | the case for each, argued fairly, and which one survives |
| Something needed to answer is missing, and it is unclear whether asking for it is worth the wait | [`hinge.md`](skills/decision-making/hinge.md) | which gaps would change the answer, and the answer now or the one question to ask |

The six exist because agents fail at decisions in separable ways. Everything
retrieved gets weighted roughly equally, so an agent told it is raining in
Paraguay while planning a trip to Lisbon will suggest a raincoat. Stated
confidence drifts from observed frequency. A one-way door and a trivially
reversible choice draw the same deliberation budget.

Where more than one applies they run in the order ledger, fit, cascade, timing,
because each supplies an input to the next. `council.md` and `hinge.md` sit
outside that chain and each runs alone. A seventh file,
[`placebo.md`](skills/decision-making/placebo.md), is the token- and
structure-matched control arm. It ships alongside because a skill that only
beats nothing has not been measured against the thing that would fake it.

### Install

The skills carry only the six portable frontmatter fields of the
[Agent Skills standard](https://agentskills.io), so they need no conversion.

```bash
# Cross-tool: Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
cp -r .agents/skills/* ~/.agents/skills/
```

```bash
# Claude Code, project-scoped
cp -r skills/* .claude/skills/
```

There is also a Claude Code plugin, and it currently ships nothing. A skill is
copied into `plugin/skills/` only once a confirmation run gives it a verdict.
Copying from `skills/` is the way to use this today.

## How it works

`decision_evals` does four things: it holds the answer key, it runs arms against
it, it scores them, and it refuses to publish what it cannot trace.

**The answer key.** [`datasets/`](datasets/) is the golden dataset:
parameterised scenario templates with *computed* ground truth, plus third-party
corpora pinned by SHA-256 and downloaded by `de fetch`. The key carries a
version stamped into every record, and `label_versions_comparable` refuses a
comparison that spans a version boundary. That guard exists because one correct
label move once raised recall on every arm on disk without a single call being
re-made.

**Relabelling it, blind.** The maintainer's labels do not get the last word on
themselves. [`scripts/adjudicate.py`](scripts/adjudicate.py) puts three blind
adjudicators on every turn, an LLM-as-a-judge panel of independent model
instances, none of which sees the maintainer's label or the other two, resolved
by majority against a kill threshold fixed before the run. Inter-rater
reliability is reported chance-corrected, with Fleiss' kappa and Krippendorff's
alpha beside raw agreement, because on this class balance two judges that have
learned nothing still agree most of the time. Primary metrics stay
deterministic and a judge never produces one.

**The arms.** A confirmation run is a within-item comparison with four arms on
the same items: **off** (the ablation), **on**, **placebo** (token- and
structure-matched filler), and **cot** (plain "think step by step"). The placebo
is what makes the design worth running. A skill that beats *off* and ties
*placebo* is a length effect, and a skill that ties *cot* is an expensive way to
say "think". [`scripts/run_triggers.py`](scripts/run_triggers.py) is the runner
behind every model call on record, and it pins MCP empty at every call with
`--strict-mcp-config`. The full lockdown is in
[`docs/HARNESS_DISCLOSURE.md`](docs/HARNESS_DISCLOSURE.md).

**The scorers.** Firing accuracy is the selection question, the same shape as
tool selection in a function-calling evaluation, and
[`evals/src/decision_evals/scorers/bfcl.py`](evals/src/decision_evals/scorers/bfcl.py)
scores a call the way BFCL's checker does, matching name and arguments after a
JSON parse. Calibration goes through the Murphy decomposition, so a skill that
improves Brier by hedging every forecast toward the base rate is caught by the
resolution term. The statistics are exact and resampling-based instead of
CLT-based, because at these item counts the normal approximation is unreliable,
and the resampling unit is the template, since items from one template are
correlated.

**The record each run leaves.**
[`evals/src/decision_evals/telemetry.py`](evals/src/decision_evals/telemetry.py)
pins the GenAI OpenTelemetry semantic-convention attribute names, adopted as
names without taking the dependency, so a record written here reads in a tool
that has never seen this repository.
[`evals/src/decision_evals/orchestrator.py`](evals/src/decision_evals/orchestrator.py)
runs a scripted fan-out of sub-agents with a per-node record. Every published
run ships its raw transcripts under [`results/`](results/) and is indexed with
its answer key and its prediction in
[`docs/RUN_INDEX.md`](docs/RUN_INDEX.md).

**Pre-registration.** A dated prediction goes into [`notebook/`](notebook/)
before the run. `de check` enforces it and refuses a published run whose README
does not name a prediction whose first commit is a git ancestor of the run's
commit. Two runs predate the rule and are baselined by name in
[`results/provenance-baseline.txt`](results/provenance-baseline.txt), a list
that may only shrink.

[`docs/METHODS.md`](docs/METHODS.md) is the full account: nine sections, each
naming the technique, the failure it defends against, the code that implements
it, and whether it has actually run.

## What's actually here

| Component | Purpose |
| --- | --- |
| `skills/` | The skills, authored to the [Agent Skills](https://agentskills.io) six-field standard so they work in Claude Code, Codex, Cursor, Copilot, Gemini CLI, Cline, Amp and OpenCode without conversion. Mirrored byte-for-byte by `de mirror` |
| `plugin/` | The Claude Code plugin. A skill is copied here once a confirmation run gives it a verdict |
| `evals/` | `decision_evals`, the evaluation harness. Paired experiments, exact tests, cluster-aware resampling, and chance-corrected inter-rater reliability |
| `datasets/` | The answer key: parameterised scenario templates with *computed* ground truth, the trigger corpus, and the SHA-256 lockfile for the third-party corpus `de fetch` downloads |
| `results/` | Published run records: raw transcripts and a README per run |
| `notebook/` | Append-only research log. Predictions go in *before* runs |
| `docs/` | Protocol, status, the research programme, related work, limitations, and what was rejected. Start at [`docs/README.md`](docs/README.md), or [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the pieces fit |
| `paper/` | The write-up, in LaTeX. A draft; see [`paper/CHECKLIST.md`](paper/CHECKLIST.md) |
| `scripts/` | Standalone analysis and runners, including `run_triggers.py`, the script behind every model call on record |
| `tests/` | Unit, integration, property and golden tests |
| `site/` | The website. It renders the markdown already in this repository in place, so no second copy of a document can disagree with the first |

## Where the evidence stands

Every caveat, in one place.

No skill here carries a verdict. `decision-making` and all six procedures are
`UNTESTED` and ship as `experimental`. [`SCORECARD.md`](SCORECARD.md) is the
file that changes that, and it is empty.

Every number on record measures whether a skill *fires*, which is upstream of
whether it helps. Firing decides whether a skill is worth having installed at
all, and it is the question this instrument was built for. Nothing here has yet
measured whether a decision procedure improves a decision.

No published run has used the placebo or cot arm. Every call on record compares
variants of the skill's *description*. The four-arm comparison is what a
confirmation run would do, and no confirmation run has happened.

One of the thirteen published runs is void. It was refused on parse rate before
any prediction was scored, which is the first registered void condition here to
fire on its own.

The description arms no longer measure what ships. The shipped description now
enumerates six procedures, so the ten arms that varied earlier wordings describe
something the skill has moved past. The harness therefore has no measurement of
how the shipped description behaves in the venue anybody uses, which qualifies
every finding above and needs a new arm and a new pre-registration to close.

The corpus behind the earlier results was largely solvable without a model, a
finding this harness produced about its own instrument. It scopes to answer-key
version 2 and the runs above it. The rebuilt version 4 corpus is far harder to
shortcut, the two keys are never mixed, and
[`SCORECARD.md`](SCORECARD.md) carries both figures with the arms measured
against them.

The hash-locked pre-registration refusal is built, tested, and has never run. It
is scoped to the `confirm` arena, no confirmation run has happened, and the
module is declared in `[tool.decision-evals.unwired]` because a tested refusal
that nothing calls is inert.

[`docs/STATUS.md`](docs/STATUS.md) is the ledger: every run, what it showed,
which measurements turned out to be broken, and which tracks are untouched.
[`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) covers what is wrong with the
harness, the statistics, the datasets and the judges.

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
```

That is the whole install. Run the full gate, which is lint, types, tests,
coverage floors and the repository-integrity checks:

```bash
uv run de check
```

`de check` makes no model calls and is fully deterministic, so the same command
runs unchanged in [`.github/workflows/check.yml`](.github/workflows/check.yml)
on every push and pull request. It is bound to `pre-commit` as a fast subset and
to `pre-push` in full. Running it in CI as well as locally is not redundant:
local tells you the working tree passes, CI tells you the *commit* passes, and a
gate that has only ever run on the machine it was written on has only ever been
asked about that machine.

Several of its steps check the method instead of the code:

| Step | Refuses |
| --- | --- |
| trigger sets | a skill with no trigger set, or a trigger set naming a skill that no longer exists |
| run provenance | a published run that does not state its answer-key version, or whose prediction cannot be shown to predate its data |
| integrity wiring | a module with a coverage floor that no entry point can reach |
| decision register | a change to the answer key or the shipped skill with no entry in [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| label corrections | a version the answer key has reached that no line of [`datasets/triggers/corrections.jsonl`](datasets/triggers/corrections.jsonl) accounts for |
| documentation | a `de` command, path, or component that this README names and the repository does not have, a document under `docs/` that [`docs/README.md`](docs/README.md) does not list, and a living document that names no audience |
| citations | a claim carrying an arXiv identifier whose entry in [`paper/refs.bib`](paper/refs.bib) has no quote behind it |
| generated regions | a table a document derives from the repository that is no longer what it derives from, and a renderer no document uses |
| document drift | a living document with no review on record, or one more than ten commits past the last one |
| published claims | a measured number, on the website or in a document, that no longer matches the sentence it came from |
| site | a published build older than the documents it publishes, naming the files that moved |

Merging to `main` publishes the site through
[`.github/workflows/deploy-site.yml`](.github/workflows/deploy-site.yml).
Nothing on a developer machine can publish. `de check` is offline by design and
cannot see the live site, so that question is answered on demand:

```bash
uv run de deployed
```

It fetches what the site says about its own origin and compares that against
`origin/main`. Exit 0 means the live site is a build of the current `main`, 1
means it is behind, and 2 means the question could not be answered, which is
deliberately distinct from 0.

Editing any document the site renders makes the published build stale, so the
loop is edit, rebuild, commit both:

```bash
uv run de sync && uv run de site
```

`de site` needs Node and npm on `PATH`, because the site is an Astro project.
The gate that demands you run it does not.

The other commands: `de sync` rewrites the tables and figures the documents
derive from the repository rather than restate by hand, `de drift` lists the
documents whose code has moved since anybody last read them, `de index`
regenerates [`docs/RUN_INDEX.md`](docs/RUN_INDEX.md), `de mirror` regenerates
the cross-tool skill copies, `de lint` checks skill frontmatter and the
promotion gate,
`de power` prints a minimum-detectable-effect table, `de rescore` re-grades an
existing checkpoint against a newer answer key without re-making a single call,
and `de fetch` downloads the hash-pinned third-party corpora.

> **Note:** if `uv` was installed with `pip install uv`, its executable may not
> be on `PATH`. On Windows it lands in
> `%APPDATA%\Python\Python313\Scripts`. Add that directory to `PATH`, or invoke
> it as `python -m uv`.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The short version: run `de check`
before believing anything works, put predictions in the notebook before runs,
and never edit a notebook entry after the fact. Append a correction instead.
Prose goes through the standard in [`docs/VOICE.md`](docs/VOICE.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
