# Contributing

This repository is a research project with a product attached, and most of its
rules exist because the corresponding failure already happened here. Nearly all
of them are enforced by `de check` rather than by asking you to remember.

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
```

```bash
uv run de check
```

That is the whole local gate — lint, format, types, tests, coverage floors, and
six repository-integrity checks. There is no cloud CI, so `de check` is the only
thing standing between a mistake and the published record. It is bound to
`pre-commit` (fast subset) and `pre-push` (everything). Run it before you
believe anything works.

`de check` makes no model calls and is fully deterministic.

## What the gates will refuse

| If you | `de check` says |
| --- | --- |
| commit under an address other than the GitHub noreply one | the history *is* the pre-registration evidence, and a misattributed commit cannot be rewritten later without destroying the timestamps the method relies on |
| change `datasets/triggers/` or `skills/` without an entry in [`docs/DECISIONS.md`](docs/DECISIONS.md) | a label move is invisible in a checkpoint and shifts every number already computed from it |
| publish a run without an answer-key version, or with a prediction that cannot be shown to predate its data | a prediction that cannot be shown to predate its data is not evidence |
| give a module a coverage floor that no entry point reaches | a tested refusal with no caller is inert, and the gate reports green either way |
| name a `de` command, path, or component that does not exist | documentation was the last obligation here checked by reading it, and the README was found naming two commands that never existed |
| leave [`docs/RUN_INDEX.md`](docs/RUN_INDEX.md) stale | run `de index`; it is generated so it cannot drift the way a hand-maintained index does |
| regenerate a golden file without `pytest --bless` | a benchmark that changes silently makes every earlier number incomparable with every later one |

## The research rules

These are not enforceable by a gate, and they matter more than the ones that are.

- **Predictions go in [`notebook/`](notebook/) before runs.** Dated, one file
  per entry, `YYYY-MM-DD-a-sentence-about-what-happened.md`.
- **The notebook is append-only.** If a prediction turns out wrong, the entry
  says so — append a `Correction` block, never edit it away. This has been
  checked mechanically and is holding.
- **A registered band names its estimator and its denominator, not just its
  number.** If you cannot write the sentence "we will compute X from records Y
  over denominator Z using function W", the run is not ready.
- **A recall band is set against the observed per-item ceiling, not a round
  number.** Compute the ceiling from the per-item history first.
- **Before believing an outcome, check that some possible response would have
  scored above zero for that arm.** An estimator that cannot return a non-zero
  value is not a measurement, and it does not announce itself — this repository
  has shipped four of them, every one producing a clean run and a plausible
  number.

[`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md) has the rules
for running unattended. [`docs/PROTOCOL.md`](docs/PROTOCOL.md) is the standing
methodology.

## Changing a skill

`skills/` is the source. `.agents/skills/` and `CLAUDE.md` are generated
mirrors — edit [`AGENTS.md`](AGENTS.md) and the files under `skills/`, then:

```bash
uv run de mirror
```

`de check` gates their agreement, so a hand-edited mirror fails the build.

A skill may not enter `plugin/skills/` while it carries `UNTESTED` or
`WITHDRAWN`. That is the promotion gate and it is enforced by `de lint`.

## Reporting that a skill does not work

This is the most useful thing you can send. The verdict vocabulary in
[`SCORECARD.md`](SCORECARD.md) has room for `NULL` and `HARMFUL`, and the
retirement rule exists because evidence that cannot come out negative is not
evidence. If a procedure produced a worse answer than thinking directly, open an
issue and say so.

## Scope

Pull requests that add a skill without a way to measure it will be turned into a
discussion about how to measure it. That is not a rejection of the skill — it is
the entire premise of the repository. *"We have not shown this works"* and
*"this works"* are different statements, and keeping them apart is the job.
