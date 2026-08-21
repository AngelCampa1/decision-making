# Why these rules

**Audience:** an agent or contributor who wants the reasoning behind a rule in AGENTS.md.

This is the incident record behind `AGENTS.md`. It is not read per turn, which
is the point: the rules stay one line each and the evidence for them lives here,
where it costs nothing to keep. Every section below is the history that produced
a single rule, and that rule links to it.

**How to read this.** The passages are verbatim from `AGENTS.md`. They are dated
records of what was true when they were written, so leave them alone: do not
rewrite the prose, and do not repair a reference that has gone stale since. The
only edit made in moving them was rebasing relative links one directory down,
because this file sits in `docs/`.


## Why the skill block is one entry


### Skill availability and presentation granularity

**It is also the product.** Skill *availability* is the dominant term in whether
a skill helps at all. Two independent benchmarks agree on the direction:

| Source | Scale | Presence effect | On form |
|---|---|---|---|
| Xu & Wu, *Skill Availability and Presentation Granularity* (arXiv:2605.31408) | 30 tasks, 2 models | **+18 to +36pp** | granularity effects minimal, uncertain, model-dependent (+0.7pp, intervals crossing zero) |
| Li et al., *SkillsBench* (arXiv:2602.12670) | 87 tasks, 8 domains | **+16.6pp** (33.9 → 50.5) | focused bundles beat larger ones; self-generated skills ≈0 or negative |

So the block below is not documentation about the skills. It is the part that
makes them fire, and it is meant to be copied into your own project.

### The shadowing bet, and why it was an extrapolation

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
[`docs/RESEARCH_PROGRAMME.md`](RESEARCH_PROGRAMME.md) is the experiment that
would settle it, and until it runs, one-entry-not-four is a judgement call
wearing a citation.

### M4: shadowing did not appear at four

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

### M5, and the floor at two

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
[`notebook/2026-08-12-m4-shadowing-did-not-appear-at-four.md`](../notebook/2026-08-12-m4-shadowing-did-not-appear-at-four.md).

### Why the wording is trust-framed

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

## Why a verdict is not a usability claim

That is not false modesty and it is not a reason to avoid it — use it if it
helps you. A verdict governs the *public claim*, not whether a skill is usable:
`UNTESTED` blocks entry to the shipped plugin, not `cp -r skills/*
.claude/skills/`. The distinction is the whole point of the repository — "we
have not shown this works" and "this works" are different statements, and
keeping them apart is the job. `de check` enforces the promotion rule rather
than trusting anyone to remember it.

## Why there are no dollars

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

In the paper and in `results/`, this is reported as *notional cost*, with the
subscription stated. Writing "we spent $250" would be false.

## Why sessions do not share a working tree


### The two 2026-08-13 incidents

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

### Three failures, one cause, 2026-08-19

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

### Nothing in the index is safe

  **Nothing in the index is safe, and the gate cannot see the difference.**
  `f12b444` committed `from decision_evals.claims import ...` into `cli.py`
  without committing `claims.py`, which existed only in the index. `main`'s tip
  did not import at all — `de` was unrunnable on a fresh checkout — while four
  sessions tried to push to it and read the failure as somebody else's mess.
  Every gate passed locally because every tree had the file on disk. **A gate
  that runs in the working tree cannot see what the commit is missing.** So:
  commit, do not stage, and if you want to know what you actually committed,
  check it out somewhere clean.

### Unpushed branches

  Push the branch even when the work is unfinished. An unpushed branch is one
  `git worktree remove` from gone, and a branch that has not touched `main` in a
  week is a merge nobody volunteers for — `feat/toolchain` sat 22 commits behind
  `main` on 2026-08-19 with nothing of its own committed anywhere. Rebasing
  daily also means you find out that `main` is broken on the day it breaks,
  rather than on the day you try to land.

### Why pushing a topic branch onto main is not a shortcut

  The reason this needs saying is that the obvious way to land does not do it.
  Pushing a topic branch straight onto the remote branch —
  `git push origin <topic>:main` — moves `origin/main` and leaves the local ref
  exactly where it was. Nothing warns you: `git status` in a worktree on another
  branch has nothing to report, and the next session to read local `main`
  reads a commit that is no longer the tip.

  Do **not** reach for `git update-ref refs/heads/main`. It bypasses the
  checked-out protection rather than satisfying it, and the worktree holding
  `main` is then left with a HEAD pointing somewhere its index and working tree
  do not match — which presents to that session as a working tree full of
  deletions it did not make. That is the failure this whole worktree section
  exists to stop, reintroduced by the command that looked like a shortcut.

## Why the gate runs in CI too

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

  **What that gate cannot see, stated so nobody mistakes green for correct.** It
  proves the site was *built* from the current tree. It does not prove anyone is
  serving that build: `de check` is offline and deterministic by design, so it
  cannot look at the live site, and a green gate beside a page nobody is serving
  is exactly as green as a deployed one.

## Why de site --deploy was removed

  **Publishing itself is no longer yours to remember.** Merging to `main` runs
  `.github/workflows/deploy-site.yml`, which builds the site and deploys it to
  Pages. There is no `gh-pages` branch and no local publish command; the
  `de site --deploy` flag was removed on 2026-08-19 after it published a build
  of a work-in-progress commit from a feature branch, because it force-pushed
  whatever local `HEAD` happened to be. What is left for you is asking whether
  it landed: `python -m uv run de deployed` fetches the live site's own record
  of which commit produced it and compares that against `origin/main`. It exits
  2 when it cannot tell, which is deliberately not the same as 0.

## Why a coverage floor is not a wiring check

- **A coverage floor does not mean a module runs.** `de check` refuses a floored
  module that no entry point can reach, because this repository has now shipped
  two of them: `triggers` was tested to 100% and called by nothing while a
  trigger set described a skill that no longer existed, and `prereg.py` carries
  every refusal `docs/PROTOCOL.md` §3 promised while nothing calls it. A tested
  refusal with no caller is inert, and the gate reports green either way.
  Intentional gaps go in `[tool.decision-evals.unwired]` with the condition that
  would close them.

## Why an unadjudicated answer key is refused

- **The rule was written down and nothing read it.** On 2026-08-20 answer key
  v5 gained 24 triples, 72 items, so that `council` and `hinge` had positives to
  be correct about. The register entry that introduced them says the labels are
  the author's and that no number may be published against version 5 until blind
  three-judge adjudication has run. It was true when written and stayed true for
  a day, during which all nineteen steps of `de check` reported green on a tree
  whose live answer key was 78% adjudicated. A run could have been published
  against those labels and the gate would have passed it.

  The stakes are the reason the rule exists at all: 21 of 21 scored failures
  across three corpora turned out to be the answer key rather than the model, and
  the method is in `METHODS.md` section 2. A label nobody but its author has read
  is the failure mode this repository has measured most often.

  So `de check` now refuses a trigger set on disk carrying an item with no
  three-judge record, joined on the case id. It is keyed to the live answer key
  and not to published runs, because a run declares a version and the corpus file
  moves on: four runs on disk declare v4 and the file is at v5, so checking them
  would mean resolving each past version out of git. `corrections.py` declined
  that same archaeology for the same reason. Keying to the live set buys the one
  property the run-keyed version could not have, which is that the check cannot
  quietly stop noticing.

  Authoring items now turns the gate red until they are adjudicated. That cost
  is the mechanism, not a side effect of it.

## Why documentation is gated mechanically


### The 2026-08-13 audit

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

### What the gate cannot see

  **What the gate cannot see is the failure that motivated it.**
  `docs/PROTOCOL.md` §3 described a refusal that has never run, in the present
  indicative, with every path in it correct. So: *prose describing a mechanism
  must name the arena it runs in and the tense it runs in.* If a gate is scoped
  to `confirm` and `confirm` has never run, the sentence says **will refuse**,
  not *refuses*. That one is on you; nothing checks it.

### Why the corrections-in-place are not enforced

  - **Delete a correction-in-place, and do not expect a gate to stop you.** The
    corrections that name `de screen`, `de confirm` and `de report` are held up by
    `[tool.decision-evals.docs-absent-commands]`, which refuses a declared command
    named nowhere in the scanned documentation. That register is **already
    satisfied by this file**, which names all three in the bullet above. Cutting
    the `README.md` and `SCORECARD.md` corrections therefore passes `de check`
    green, and the reason to keep them is that they are the record, not that
    anything enforces them.

### Why skills/ is excluded from the writing pass

  `skills/` is excluded and it is the sharpest case: the description in
  `skills/decision-making/SKILL.md` is the artefact Tracks L, M and N are measured
  on — `scripts/run_triggers.py` reads that frontmatter field and nothing else —
  so rewriting it for style would make every published number incomparable, and
  would need an entry in `docs/DECISIONS.md`. The copy in the fenced block above
  is a paraphrase for readers and is not what any run has measured.

## Why STATUS.md and the drift sweep exist

- **A published run updates `docs/STATUS.md` in the same change.** It is the
  ledger and it is hand-maintained, so it is the one file that drifts silently:
  on 2026-08-13 its summary line read "six results, five measurements" while the
  two tables underneath it listed seven and eight. A count in prose that is not
  recomputed from the table below it is a hand-maintained number like any other.
  Corrections there are appended, not rewritten.

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

## Pre-registration defects, in order


### The recall band above the ceiling

- **A recall band is set against the observed per-item ceiling, not a round
  number.** Track L7 registered "at least one arm reaches recall >= 0.94" over
  17 positives, which needs 16 of 17 — and `x-n22` "has never fired in any arm
  on any version", a fact stated flatly in that same prediction's *"where I
  expect to be wrong"* section. Read it as scoped to the version 2 corpus that
  prediction was scored against; the qualifier is added here, not quoted. The ceiling
  was 0.941 and the band demanded perfection on everything else. This is the
  fifth pre-registration defect on record and the first that was visible
  **before** the run rather than after, which makes it the cheapest one to have
  avoided. Compute the ceiling from the per-item history, then set the band
  under it.

### The item that was not the item

  **And compute it against the item you are about to run, which is not always
  the item the history is about.** `x-n22`'s successor in version 4 is `s13p`,
  and the v3/v4 rebuild did not carry it over intact: *"The build is green. Can
  I deploy?"* became *"The build is green and the release notes are written. Can
  I deploy, or is there something I'm missing?"*, where the closing clause asks
  for help rather than for a go/no-go. It fires in 11 of the 14 v4 rows on
  disk. The item's own annotation still said "otherwise unchanged" and "It has
  never fired in any arm on any version" until 2026-08-19, so a ceiling computed from
  the per-item history would have been computed for the wrong turn — the
  failure this rule is meant to prevent, arriving through the door the rule
  leaves open. Nothing caught it because descent from a v2 item was recorded
  only as prose inside `why`, and prose cannot be diffed. The `ancestry:` block
  in `datasets/triggers/decision-making/index.yaml` now maps each carried-over
  v4 id to its v2 ancestor and says whether the text is verbatim, edited or
  rewritten; check it before quoting a per-item fact across versions.

### Four slips in one day

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

### The answer-key move that earned five points

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

### Estimators that cannot return a non-zero value

- **An estimator that cannot return a non-zero value is not a measurement, and
  it does not announce itself.** Two defects in the trigger instrument on
  2026-08-12 each produced a clean run, a full checkpoint and a plausible zero:
  a parser whitelist that discarded every tool name an n=2 arm could offer, and a
  routing report that graded those names against names the arm never offered.
  Nothing crashed and firing was correct in both. **Before believing an outcome,
  check that some possible response would have scored above zero for this arm.**

### Estimators that are turn-count proxies

- **And the estimator must be checked against the arm structure, not only against
  the records.** On 2026-08-12 a 50-pair run produced 45/50 against 23/50 with
  discordance 24-to-2 in the predicted direction — a clean replication, and
  entirely an artefact of a scorer reading `final_response` when one arm had a
  single turn and the other had six. Crediting the whole conversation reversed
  the direction. Before a run: does the scorer read the *same object* in every
  arm? A measure that is legitimate for one arm can be a turn-count proxy for
  another.

## A new document is listed, declares an audience, and is reachable

**2026-08-21.** The documentation gate had been reading root `*.md` and
`docs/*.md` since 2026-08-13. One level deep, so `docs/reviews/` and
`docs/superpowers/` were rendered by the site, linked from `docs/README.md`, and
read by nothing. Widening the glob to `docs/**/*.md` found 23 unresolvable
references in one dated plan, which is a record and now sits in
`EXCLUDED_PREFIXES` as a class.

Three things were true at once and none of them was checked. `docs/README.md`
listed every document under `docs/` because somebody had kept it that way by
hand. `docs/STATUS.md`, one of the most linked files here, carried no
`**Audience:**` line. And `docs/superpowers/drafts/s9-ledger-replacement/`
held 315 lines describing a candidate procedure that nothing had ever linked
to, reachable only by listing the directory.

`check_docs_index` and `check_audience_lines` close all three, and they are the
two-directional comparison `check_component_table` already made for the README's
map of the repository, one level down. The same run that added them caught two
`de` commands and a deleted path in the prose of the documents announcing them,
which is the argument for the gate rather than the convention.

`docs/RESEARCH_PROGRAMME.md` was split in the same change: 2,550 lines and 66
commits, the most-edited file in this history, became a map and eight parts
under `docs/programme/`. The split went by exact line boundaries. Rewrapping
during a split can move a claim number into a markdown block whose identifier
carries no quote in `paper/refs.bib`, which turns a green citation gate red.

The map, the classes and the placement rule are
[`docs/DOCUMENTATION_MAP.md`](DOCUMENTATION_MAP.md).
