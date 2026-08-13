# decision-making

Agent skills for making better decisions under uncertainty — and an evaluation
harness that measures whether they actually work.

> **Status: pre-alpha. No skill in this repository has been validated yet.**
> The harness is being built first, deliberately. Until a skill carries a
> verdict in [`SCORECARD.md`](SCORECARD.md), treat it as an untested hypothesis.
>
> **[`docs/STATUS.md`](docs/STATUS.md) is the ledger** — every run on record,
> what it showed, which measurements turned out to be broken, and which tracks
> are still untouched.

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
| `skills/` | The skills, authored to the [Agent Skills](https://agentskills.io) 6-field standard so they work in Claude Code, Codex, Cursor, Copilot, Gemini CLI, Cline, Amp and OpenCode without conversion |
| `plugin/` | The Claude Code plugin. A skill is copied here only once a confirmation run gives it a verdict, so the directory is currently empty on purpose |
| `evals/` | `decision_evals` — the harness. Paired experiments, exact tests, cluster-aware resampling |
| `datasets/` | Parameterised scenario templates with *computed* ground truth |
| `preregistration/` | Hypotheses, committed and hash-locked before the run |
| `results/` | Raw run records and transcripts |
| `notebook/` | Append-only research log |
| `docs/` | Protocol, related work, limitations, and what was rejected |

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

Pre-registration is enforced by the tooling, not by good intentions: a
confirmation run refuses to start unless the pre-registration file is committed,
predates the results, and its recorded hash still matches the skill on disk.
Editing one word of a skill after pre-registration aborts the run with a diff.

Verdicts govern the *public claim*, not your ability to use something. A skill
that comes back `NULL` goes back to the workbench and ships as `experimental` —
available, just not claimed as proven.

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
```

Run the full local gate — lint, types, tests, coverage floors, golden files:

```bash
uv run de check
```

There is no cloud CI. `de check` is bound to `pre-commit` (fast subset) and
`pre-push` (everything), so a red tree can't be pushed. Model-backed evaluation
is never part of `de check`; it runs explicitly via `de screen` and `de confirm`.

> **Note:** if `uv` was installed with `pip install uv`, its executable may not be
> on `PATH`. On Windows it lands in
> `%APPDATA%\Python\Python313\Scripts`. Add that directory to `PATH`, or invoke
> it as `python -m uv`.

## License

Apache-2.0. See [LICENSE](LICENSE).
