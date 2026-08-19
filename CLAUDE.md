# Agent instructions

This file is read by Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
and others. Claude Code reads `CLAUDE.md`; the two carry the same content here.

**Edit this file, not `CLAUDE.md`.** `CLAUDE.md` is a byte-exact mirror written
by `de mirror`, and `de check` refuses a tree where it has fallen behind. An
edit made to `CLAUDE.md` is reverted by the next build.

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

The wording is deliberate. Trust-framed system prompts surfaced 59% more hidden
issues than unframed ones (arXiv:2603.14373), while fear-framing — threats,
consequences, "you MUST" — "showed no significant improvement over baseline on
any metric". So nothing here threatens the model, and the closing line invites
it to report that a skill is not working.

**The 59% is the smaller of the paper's two studies and the replication is
weaker.** Study 1 is a *manual* experiment over 9 debugging scenarios on a
single model: 59% more hidden issues, p = 0.002, d = 2.28. Study 2 automates
it over 135 scenario-level points and lands at **+25%** hidden issues
(p = 0.016) and +74% investigative steps. The fear-framing null is Study 2's
and is the robust half. Whichever number is quoted, the other travels with it —
and both were measured on debugging, so applying them to how reviewers are
briefed here is an extrapolation. Verified first-hand 2026-08-13.

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
`experimental`, and so do all six procedures inside it. See
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
- **And nothing may be bought.** This is a side project with no budget — no paid
  APIs, no paid datasets, no paid tooling, no subscription beyond the Claude Max
  one already here, nothing that bills. Maintainer instruction, 2026-08-18. If a
  track needs data this repository did not author, it uses data that is free to
  obtain *and* free to redistribute, or it does without and says which. Note
  that **"vendoring" here means checking a copy into `datasets/vendor/`** — it
  has never meant paying anyone, and the word has already been misread that way
  once, which is the reason this bullet names it.

`BudgetLedger` stays, reinterpreted. Reported cost scales with tokens, so it is
the best available **burn meter** for quota consumption. It is not a spend cap
and must not be described as one.

In the paper and in `results/`, this is reported as *notional cost*, with the
subscription stated. Writing "we spent $250" would be false.

---

## Working in this repository

If you are an agent contributing here rather than a user installing the skills:

- **Read [`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md)
  first — before this file's other bullets and before the programme.** It is
  not a document about long unattended runs any more; it is *how work is done
  here*, on a five-minute task as much as a five-day one. It carries the five
  standing rules, the sub-agent and adversarial-review method, the confirmation
  requirement, and the reason each exists — every one of them is a failure that
  has already happened in this repository, with the reference so you can check
  rather than take it on trust. The bullets below are pointers into it, not a
  substitute for it.

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

- **Work in your own worktree, and rejoin `main` on a schedule.** The bullet
  above says how to share one working tree politely. Stop sharing it. A session
  that will run longer than a few minutes gets its own:

  ```bash
  git worktree add -b <topic> .claude/worktrees/<topic> origin/main
  ```

  **Inside the repository, under `.claude/worktrees/`** — corrected 2026-08-19,
  having said the opposite here. `.gitignore` already carries `.claude/`, so a
  nested tree neither shows in `git status` nor can be staged. The other reason
  once given — that a nested tree is matched by `site/inputs.json` globs — was
  measured and is **false**: with three nested worktrees on disk,
  `input_files()` returns 192 inputs and zero under that directory. The cost of
  the location is that an ignored directory is easy to destroy; see
  [Starting the work](docs/AUTONOMOUS_WORK_ORDER.md#starting-the-work-which-directory-the-worktree-goes-in),
  which also lists the setup a fresh worktree needs before the gate will pass.
  Its own tree, its own `.venv`, its own gate.

  Three failures, one cause, all of them on 2026-08-19 in a single shared tree:

  - **`de check` is whole-repo and it is bound to `pre-commit` and
    `pre-push`.** So another session's half-written module fails *your* push.
    Four sessions each read "4 of 18 steps failed", each concluded it was
    blocked, and not one of the failures belonged to the session reading it.
    That is a hold-and-wait cycle: nobody can land until everybody is done, and
    nobody is done because they are all waiting.
  - **`.venv/Scripts/de.exe` is a shared lock.** `uv run` tries to reinstall it
    and gets `os error 32` while another session is mid-gate. `python -m uv run
    --no-sync` gets you past it; a worktree with its own `.venv` means it never
    happens. Do not kill the other session's processes.
  - **A failed `pre-commit` stashes and restores the whole tree**, which
    destroys uncommitted work belonging to sessions that were not committing.
    Eighteen files went that way and came back only from
    `~/.cache/pre-commit/patch*`, which is not a backup and is not guaranteed to
    be there next time.

  **Nothing in the index is safe, and the gate cannot see the difference.**
  `f12b444` committed `from decision_evals.claims import ...` into `cli.py`
  without committing `claims.py`, which existed only in the index. `main`'s tip
  did not import at all — `de` was unrunnable on a fresh checkout — while four
  sessions tried to push to it and read the failure as somebody else's mess.
  Every gate passed locally because every tree had the file on disk. **A gate
  that runs in the working tree cannot see what the commit is missing.** So:
  commit, do not stage, and if you want to know what you actually committed,
  check it out somewhere clean.

  **Rejoin often, and the interval is short.** A long-horizon branch is the case
  this rule exists for, not the exception to it. Fetch, rebase onto
  `origin/main`, and push your branch **at least daily and at least every ten
  commits**, whichever comes first:

  ```bash
  git fetch origin && git rebase origin/main && git push -u origin <topic>
  ```

  Push the branch even when the work is unfinished. An unpushed branch is one
  `git worktree remove` from gone, and a branch that has not touched `main` in a
  week is a merge nobody volunteers for — `feat/toolchain` sat 22 commits behind
  `main` on 2026-08-19 with nothing of its own committed anywhere. Rebasing
  daily also means you find out that `main` is broken on the day it breaks,
  rather than on the day you try to land.

  Landing is a merge to `main` from a green worktree, and `--no-verify` is not
  how a red gate gets resolved. If the gate is red on your own isolated tree,
  it is yours and it is real.

  **After landing, local `main` and `origin/main` must name the same commit.**
  Check it, do not assume it:

  ```bash
  git fetch origin && git rev-parse main origin/main   # two identical lines
  ```

  The reason this needs saying is that the obvious way to land does not do it.
  Pushing a topic branch straight onto the remote branch —
  `git push origin <topic>:main` — moves `origin/main` and leaves the local ref
  exactly where it was. Nothing warns you: `git status` in a worktree on another
  branch has nothing to report, and the next session to read local `main`
  reads a commit that is no longer the tip.

  Nor can you always fix it from where you are. `main` is usually checked out
  in *some* worktree — on 2026-08-19 it was not in `D:\code\decision-making` at
  all, which had a topic branch checked out, but in another session's
  scratchpad worktree — and git refuses to update a branch ref that is checked
  out anywhere. `git fetch origin main:main` is rejected. `git worktree list`
  tells you which path holds it. So either land from that worktree and push
  from there, or fast-forward it in place afterwards:

  ```bash
  git -C <the-worktree-holding-main> merge --ff-only origin/main
  ```

  Do **not** reach for `git update-ref refs/heads/main`. It bypasses the
  checked-out protection rather than satisfying it, and the worktree holding
  `main` is then left with a HEAD pointing somewhere its index and working tree
  do not match — which presents to that session as a working tree full of
  deletions it did not make. That is the failure this whole worktree section
  exists to stop, reintroduced by the command that looked like a shortcut.


  **Landing does not stop at the merge.** The ordered sequence — catch up,
  adversarial review, fix, regenerate, rebuild the site, commit, full `de
  check`, merge, deploy, fetch the deployed page, remove the worktree and
  branch — is
  [Landing the work](docs/AUTONOMOUS_WORK_ORDER.md#landing-the-work). Its last
  two steps are the ones nothing here can check: that the deployed page was
  *fetched and asserted against*, and that the worktree and branch were removed
  — unless another session is standing in them, which outranks the tidying.
  Deploying itself dropped off that list on 2026-08-19: it is a workflow now,
  and `de deployed` will say whether it landed.
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
  the literature already settles, and sixteen tracks you can be pointed at.
  Start there before proposing experiment work. **Track K runs first** (the
  decision-frameworks review, free, no instrument), **Track S runs in parallel
  from day one** (the skills themselves), and Track 0 blocks the measurement
  but not the skills.
- The long-context experiment
  ([`docs/superpowers/plans/2026-08-11-long-context-experiment.md`](docs/superpowers/plans/2026-08-11-long-context-experiment.md))
  is now **Track G** and its pilot-library authoring is on hold. Read it for the
  gate machinery, not for the priority.
- **[`docs/AUTONOMOUS_WORK_ORDER.md`](docs/AUTONOMOUS_WORK_ORDER.md) governs
  how the work runs**, and it is the first read above rather than a footnote
  here. It no longer says what to stop for, because there is nothing to stop
  for: it says how to keep going — derive the parameter or record the choice,
  adjudicate the failures blind, run the grid, confirm the finding.
- `python -m uv run de check` is the full local gate — lint, types, tests,
  coverage floors, skill validation, run provenance and integrity wiring. Run it
  before you believe anything works. It also runs in CI
  (`.github/workflows/check.yml`), which is not a convenience: checking out the
  committed tree on its own showed the gate had only ever been asked about a
  working directory, never about a commit. `main`'s tip imported an uncommitted
  module, two documents linked ignored paths, and the site manifest recorded a
  build from a file not in the repository. Green locally means green *here*;
  only a clean checkout can say green on a clean clone. The workflow's first run
  went red in four places a working directory cannot show, and has been green
  since `ada7b4a`. See
  `notebook/2026-08-19-the-gate-had-never-run-on-a-clean-clone.md`.
  A second workflow, `deploy-site.yml`, publishes the site and checks nothing.
- **Setup, and the loop underneath the gate.** `uv sync --group dev` installs
  it; add `--group docs` only to publish the site. `python -m uv run de check
  --fast` skips tests, coverage and the site rebuild — that is the pre-commit
  subset and the right loop while iterating, but it is not the gate, so run the
  whole thing before believing anything. A single file is `python -m uv run
  pytest tests/unit/test_claims.py`. `uv` is not on PATH here, hence `python -m
  uv`.
- **Where the code is.** `evals/src/decision_evals/` is the harness and the
  gates: `cli.py` wires every `de check` step, and each step lives in the module
  it is named after — `docs.py`, `provenance.py`, `decisions.py`, `wiring.py`,
  `skills.py`. `scripts/run_triggers.py` is the runner behind every model call on
  record. `datasets/` is the answer key, `skills/` the product, `results/` and
  `notebook/` the record. `README.md` carries the full component table.
- **Editing a document means rebuilding the site in the same change.** The site
  under `site/` renders this repository's markdown *in place* — `docs/`,
  `notebook/`, `results/`, `skills/` and the root are read by the build, never
  copied — so there is no second copy of `STATUS.md` to disagree with the first,
  and every build is a snapshot that goes stale invisibly. `python -m uv run de
  site` rebuilds it and writes `site/build-manifest.json`, a hash of every input;
  `de check` refuses a tree where that manifest has fallen behind, and names the
  files that moved. Notebook entries are this repository's highest-frequency
  action, so this will fire often. It is the price of not having two copies.

  **What that gate cannot see, stated so nobody mistakes green for correct.** It
  proves the site was *built* from the current tree. It does not prove anyone is
  serving that build: `de check` is offline and deterministic by design, so it
  cannot look at the live site, and a green gate beside a page nobody is serving
  is exactly as green as a deployed one.

  **Publishing itself is no longer yours to remember.** Merging to `main` runs
  `.github/workflows/deploy-site.yml`, which builds the site and deploys it to
  Pages. There is no `gh-pages` branch and no local publish command; the
  `de site --deploy` flag was removed on 2026-08-19 after it published a build
  of a work-in-progress commit from a feature branch, because it force-pushed
  whatever local `HEAD` happened to be. What is left for you is asking whether
  it landed: `python -m uv run de deployed` fetches the live site's own record
  of which commit produced it and compares that against `origin/main`. It exits
  2 when it cannot tell, which is deliberately not the same as 0.
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
- **Prose a human reads goes through the `humanizer` skill before it is
  committed.** `README.md` is the case that names the rule and it is not the only
  one: `CONTRIBUTING.md`, `SCORECARD.md` and the living documents under `docs/` are
  read by people deciding whether to trust this repository, and until 2026-08-19 not
  one of them had ever been through a writing pass. **Nothing checks this.** The
  documentation gate reads whether a reference resolves, never whether the sentence
  around it is worth reading, and `evals/src/decision_evals/docs.py` refuses to grow
  into a prose linter on purpose — "a gate that flags prose becomes noise, and noise
  is what an advisory gate becomes before somebody turns it off". So this one is on
  you.

  `third-grade-copy` does **not** apply here. The writing rule one directory up
  pairs the two for marketing copy and exempts technical docs; these are technical
  docs, and a third-grade reading level would strip the precision they exist to
  carry.

  Three things the pass may never do:

  - **Change a number, a confidence interval, a p-value, an arXiv identifier or a
    quoted sentence.** Identifiers are resolved against `paper/refs.bib` wherever
    they appear, but the rule that a bib entry must carry a `quote` before a number
    may be asserted beside it is scoped to the *markdown block*. So rewrapping
    alone can move a claim number into a block whose identifier has no quote behind
    it, and the gate that was green before the pass fails after it.
  - **Delete a correction-in-place, and do not expect a gate to stop you.** The
    corrections that name `de screen`, `de confirm` and `de report` are held up by
    `[tool.decision-evals.docs-absent-commands]`, which refuses a declared command
    named nowhere in the scanned documentation. That register is **already
    satisfied by this file**, which names all three in the bullet above. Cutting
    the `README.md` and `SCORECARD.md` corrections therefore passes `de check`
    green, and the reason to keep them is that they are the record, not that
    anything enforces them.
  - **Flatten a hedge that carries epistemic status.** *"We have not shown this
    works"* is not the same statement as *"this does not work"*, and keeping those
    apart is the whole job. Collapse stacked hedges; leave the load-bearing one.

  Excluded, and for three different reasons rather than one. `notebook/`,
  `results/`, `docs/DECISIONS.md` and `docs/STATUS.md` are dated records, and a
  record rewritten for style is a record destroyed. `docs/RUN_INDEX.md` is
  generated by `de index` and `CLAUDE.md` by `de mirror`, so editing either is
  reverted by the next build. `AGENTS.md`, `CLAUDE.md` and
  `docs/AUTONOMOUS_WORK_ORDER.md` are written to be read by an agent mid-task
  rather than by a person deciding whether to trust the work, which is the
  audience the rule is about; note that all three are still governed by the
  citation gate, so the block hazard above applies to them anyway.

  `skills/` is excluded and it is the sharpest case: the description in
  `skills/decision-making/SKILL.md` is the artefact Tracks L, M and N are measured
  on — `scripts/run_triggers.py` reads that frontmatter field and nothing else —
  so rewriting it for style would make every published number incomparable, and
  would need an entry in `docs/DECISIONS.md`. The copy in the fenced block above
  is a paraphrase for readers and is not what any run has measured.

- **A published run updates `docs/STATUS.md` in the same change.** It is the
  ledger and it is hand-maintained, so it is the one file that drifts silently:
  on 2026-08-13 its summary line read "six results, five measurements" while the
  two tables underneath it listed seven and eight. A count in prose that is not
  recomputed from the table below it is a hand-maintained number like any other.
  Corrections there are appended, not rewritten.
- **Every third published run, sweep `README.md` and `docs/` for drift, and land
  the sweep as a dated `notebook/` entry.** Count published runs from
  `docs/RUN_INDEX.md`, which is generated and cannot itself drift. The bullet
  above covers `docs/STATUS.md` on the day a run lands; this one covers
  everything a run does *not* touch, which is where the rot actually
  accumulates. A sweep does three things: recompute every count stated in prose
  against the table or directory underneath it; re-read `docs/README.md` as an
  index, since documents get added and never regrouped; and read the living
  documents for a description that has stopped being true. The notebook entry
  names what moved and what did not, so the next sweep can see when the last one
  ran.

  **Nothing checks this, and the reason is deliberate.** `de check` refuses a
  reference that does not resolve and will never judge whether the sentence
  around it is true — `evals/src/decision_evals/docs.py` declines to grow into a
  prose linter, because an advisory gate becomes noise before somebody turns it
  off. So the failure mode is silent by construction, and the first sweep found
  it in four places at once: `docs/README.md` counted fourteen documents over a
  directory holding sixteen, the site landing page offered four procedures when
  the skill routes to six, `README.md` reported seven published runs against
  thirteen in the generated index, and its call total predated four runs. Every
  one of those overstated or understated by drifting, not by anyone deciding
  anything.
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
