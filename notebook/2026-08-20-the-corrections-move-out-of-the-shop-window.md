# The corrections move out of the shop window

**2026-08-20.** Four of this repository's documents opened by correcting
themselves. `README.md` did it twice: once about a pre-registration mechanism
it had described in the present tense and did not have, once about a
publishing step nothing checked. `SCORECARD.md` spent its opening paragraph on
a claim its own first line used to make and could not support. A reader's
first thirty seconds went to a confession.

Each of those corrections is evidence, and evidence belongs in a dated record.
So it is here. `SCORECARD.md` now opens with what it is and points at this
entry for its own history.

The four passages below are verbatim. Nothing in them is reworded or
rewrapped, and the paths inside them are relative to the file each came from,
so some will not resolve from `notebook/`. Three were recovered with `git show
origin/main:README.md`, the working copy having already been rewritten.

## 1. The pre-registration mechanism written in the wrong tense

`README.md` at `origin/main`, lines 240 to 258. It corrects a paragraph that
told readers to run `de screen` and `de confirm`, neither of which is a
command, and pointed at a `preregistration/` directory that has never existed.

> ### Pre-registration: two mechanisms, and only one of them has ever run
>
> This section used to describe the second as though it were the first. It read
> *"a confirmation run refuses to start unless the pre-registration file is
> committed, predates the results, and its recorded hash still matches the skill
> on disk"*, in the present tense, and it pointed at a `preregistration/`
> directory that has never existed. It also told you to run `de screen` and
> `de confirm`, neither of which is a command. The correction is
> [`docs/PROTOCOL.md`](docs/PROTOCOL.md) §3, split in two:
>
> - The standing mechanism, the one every run on record actually used, is a dated
>   prediction committed to [`notebook/`](notebook/) *before* the run. `de check`
>   enforces it, and refuses a published run whose README does not name a
>   prediction whose first commit is an ancestor of the run's commit.
> - The hash-locked refusal is built, tested, and has never run. It is scoped to
>   the `confirm` arena, and no confirmation run has happened. The module carries
>   a 100% branch floor and no caller, which is why it is declared in
>   `[tool.decision-evals.unwired]`. A tested refusal that nothing calls is
>   inert, and the gate reports green either way.

## 2. The gate that had only ever been asked about one machine

`README.md` at `origin/main`, lines 283 to 305, from the `## Development`
section. The four red places on CI's first run, and what simulating a clean
clone turned up.

> **The gate runs locally, and from now on in CI as well.** `de check` is bound to
> `pre-commit` (fast subset) and `pre-push` (everything), so a red tree can't be
> pushed, and it runs on a machine where you can watch it. It makes no model
> calls; model-backed evaluation is run explicitly from [`scripts/`](scripts/).
> Because it is offline and deterministic, the same command runs unchanged in
> [`.github/workflows/check.yml`](.github/workflows/check.yml) on every push and
> pull request. Its first run went red on a tree whose local gate was green, in
> four places, none of which a working directory can show -- a CLI the runner had
> no reason to have, and an assertion that was reading an error message Rich had
> wrapped to eighty columns. It has been green since `ada7b4a`. That is what the
> workflow is for: a gate that has only ever run on the machine it was written on
> has only ever been asked about that machine.
>
> **Simulating a clean clone is what found the reason to want that.** Checking out
> the committed tree on its own showed the gate had only ever been asked about a
> working directory, never about a commit. The tip of `main` imported a module
> that had never been committed. Two living documents linked paths that
> `.gitignore` excludes by design, so those links cannot resolve for anyone who
> clones this. The site manifest recorded a build from a file that is not in the
> repository. A test asserting that published checkpoints exist found one where it
> wanted two, because the second is under an ignored path. Every one of those is
> the gate working correctly on a tree it had never been shown. Written up in
> [`notebook/2026-08-19-the-gate-had-never-run-on-a-clean-clone.md`](notebook/2026-08-19-the-gate-had-never-run-on-a-clean-clone.md).

## 3. The scorecard that said it was generated

`SCORECARD.md`, lines 3 to 18 as they stood this morning. The file called
itself a generated artifact rebuilt by `de report` from
`results/**/summary.json`, with `de check` failing on a stale copy. There is
no such command, no such file, and no such step.

> Hand-maintained, and this line used to claim otherwise. It called the file a
> *"generated artifact"* that you should *"not edit by hand"*, rebuilt by
> `de report` from `results/**/summary.json`, with `de check` failing the build if
> the committed copy differed. None of that was true: there is no `de report`
> command, no `summary.json` under `results/`, and no scorecard step in
> `de check`. The file had not changed since the initial commit, so nothing ever
> tested the promise.
>
> Correcting it rather than building the generator, because the table is still
> empty. A generator written now would be written against a results schema no run
> has produced. When the first confirmatory run lands, `de report` gets built and
> this paragraph gets replaced by the guarantee it describes.
>
> What *is* enforced today is the promotion gate: `de lint` refuses to let a skill
> carrying `UNTESTED` or `WITHDRAWN` sit in `plugin/skills/`, and `de check` runs
> it. That check is real and has teeth. The table below does not.

## 4. Six days of a hand-written page

`README.md` at `origin/main`, lines 314 to 329. The site gate proved the
committed build matched the tree and never proved anyone was serving it.

> This section used to admit a step it could not check, and that step is gone.
> The site gate proves the committed build matches the current tree; it never
> proved the build was pushed, and for six days in August 2026 the live site was
> a hand-written page nothing here had ever touched. Publishing is now a function
> of `main` instead of a function of who remembered. `de check` is still offline
> on purpose and still cannot see the live site, so the question is answered on
> demand by a separate command:
>
> ```bash
> uv run de deployed
> ```
>
> It fetches what the site says about its own origin and compares that against
> `origin/main`. Exit 0 means the live site is a build of the current `main`,
> 1 means it is behind, and 2 means the question could not be answered. That last
> one is deliberately not the same as 0.

## What this changes

Nothing mechanical. `[tool.decision-evals.docs-absent-commands]` in
`pyproject.toml` refuses a declared command named nowhere in the scanned
documentation, and `notebook/` sits outside that scan. `de screen`, `de
confirm` and `de report` are all three named in
[`docs/WHY_THESE_RULES.md`](../docs/WHY_THESE_RULES.md), which is what holds
the register up now that they have left the documents that used to carry them.
The gate was green before this move and is green after it. What moved is which
document a stranger reads first.
