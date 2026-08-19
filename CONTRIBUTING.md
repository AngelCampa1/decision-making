# Contributing

This repository is a research project with a product attached, and most of its
rules exist because the corresponding failure already happened here. Nearly all
of them are enforced by `de check` rather than by asking you to remember.

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev
```

That is the whole install. Publishing the website needs nothing extra, because
publishing no longer happens here.

```bash
uv run de check
```

That is the whole local gate: lint, format, types, tests, coverage floors, and
seven repository-integrity checks. It is bound to `pre-commit` (fast subset) and
`pre-push` (everything), and the same command runs in CI on every push and pull
request. Run it before you believe anything works.

Run it locally anyway, even though CI will. The two are not redundant: local
tells you the tree in front of you passes, CI tells you the commit passes, and
the first time those were compared, on a locally simulated clean clone, they
disagreed in four places.

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
| edit a document the website renders without rebuilding it | run `de site`; the site reads this repository's markdown in place, so an edited document is a published page that disagrees with the repository until somebody notices |
| regenerate a golden file without `pytest --bless` | a benchmark that changes silently makes every earlier number incomparable with every later one |

## The research rules

These are not enforceable by a gate, and they matter more than the ones that are.

- Predictions go in [`notebook/`](notebook/) before runs. Dated, one file per
  entry, `YYYY-MM-DD-a-sentence-about-what-happened.md`.
- The notebook is append-only. If a prediction turns out wrong, the entry says
  so: append a `Correction` block, never edit it away. This has been checked
  mechanically and is holding.
- A registered band names its estimator and its denominator, not just its
  number. If you cannot write the sentence "we will compute X from records Y
  over denominator Z using function W", the run is not ready.
- A recall band is set against the observed per-item ceiling, not a round
  number. Compute the ceiling from the per-item history first.
- Before believing an outcome, check that some possible response would have
  scored above zero for that arm. An estimator that cannot return a non-zero
  value is not a measurement, and it does not announce itself. This repository
  has shipped four of them, every one producing a clean run and a plausible
  number.

[`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md) has the rules
for running unattended. [`docs/PROTOCOL.md`](docs/PROTOCOL.md) is the standing
methodology.

## Writing

Prose a person reads goes through the humanizer skill before it is committed.
That means [`README.md`](README.md), this file,
[`SCORECARD.md`](SCORECARD.md), and the living documents under
[`docs/`](docs/). Nothing enforces it. The documentation gate reads whether a
reference resolves, not whether the sentence is worth reading.

Three kinds of file are exempt, for three different reasons. Dated records say
what was true on the day somebody wrote them: [`notebook/`](notebook/),
[`results/`](results/), [`docs/DECISIONS.md`](docs/DECISIONS.md) and
[`docs/STATUS.md`](docs/STATUS.md). Generated files are rewritten by the next
build: [`docs/RUN_INDEX.md`](docs/RUN_INDEX.md) and `CLAUDE.md`. And
[`AGENTS.md`](AGENTS.md), `CLAUDE.md` and
[`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md) are written for
an agent working mid-task rather than for a person deciding whether to trust the
work. [`skills/`](skills/) is exempt too, and most sharply: the description
there is the thing the trigger experiments measure, so an edit for style makes
the published numbers incomparable.

The pass never touches a number, a citation, a correction left in place, or a
hedge that is carrying its own weight. *"We have not shown this works"* does not
get shortened into *"this does not work"*. [`AGENTS.md`](AGENTS.md) states the
rule in full, including why no gate catches a violation.

## Changing a skill

`skills/` is the source. `.agents/skills/` and `CLAUDE.md` are generated
mirrors, so edit [`AGENTS.md`](AGENTS.md) and the files under `skills/`, then:

```bash
uv run de mirror
```

`de check` gates their agreement, so a hand-edited mirror fails the build.

A skill may not enter `plugin/skills/` while it carries `UNTESTED` or
`WITHDRAWN`. That is the promotion gate and it is enforced by `de lint`.

## Changing a document the website renders

Every markdown file under `docs/`, `notebook/`, `results/`, `skills/` and the
repository root is rendered by the site *in place*. Nothing is copied, so no
second version of a document exists to disagree with the first. The price is
that each build is a snapshot with an expiry nobody can see. Rebuild in the
same change:

```bash
uv run de site
```

That writes `site/build-manifest.json`, which records a hash of every file the
site renders. Commit it with the document.

Publishing is not your job any more. Merging to `main` deploys the site through
[`.github/workflows/deploy-site.yml`](.github/workflows/deploy-site.yml), and
nothing on a laptop can publish. That gate still cannot see the live page,
because `de check` is offline by design, so the question is asked separately
when you want the answer:

```bash
uv run de deployed
```

## Reporting that a skill does not work

This is the most useful thing you can send. The verdict vocabulary in
[`SCORECARD.md`](SCORECARD.md) has room for `NULL` and `HARMFUL`, and the
retirement rule exists because evidence that cannot come out negative is not
evidence. If a procedure produced a worse answer than thinking directly, open an
issue and say so.

## Scope

Pull requests that add a skill without a way to measure it will be turned into a
discussion about how to measure it. That is not a rejection of the skill. It is
the entire premise of the repository. *"We have not shown this works"* and
*"this works"* are different statements, and keeping them apart is the job.
