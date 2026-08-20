# Voice

**Audience:** anyone writing prose in this repository, human or agent.

**What this is.** The house standard for how writing here reads. It covers every
document, every skill body, and every comment and docstring in the source. One
rule governs all of it: say what is true, in the order a reader needs it, in
sentences worth reading.

Nothing enforces this file. `de check` refuses a reference that does not resolve
and declines to judge the sentence around it, because an advisory gate that
flags prose becomes noise and then gets switched off. The guardrail is a writing
pass and a review, both described at the bottom of this page.

## Who reads what

Four audiences. Every document serves exactly one, and a document that tries to
serve two serves neither.

| Audience | Files | What they want |
| --- | --- | --- |
| **Cold reader** | `README.md`, the site landing page, the GitHub description and topics, `CITATION.cff` | Thirty seconds to decide whether this deserves their attention |
| **Evaluating reader** | `SCORECARD.md`, `CONTRIBUTING.md`, `docs/README.md`, `docs/METHODS.md`, `docs/PROTOCOL.md`, `docs/LIMITATIONS.md`, `docs/RELATED_WORK.md`, and the other living documents | To judge whether the method holds up |
| **Agent mid-task** | `AGENTS.md`, `CLAUDE.md`, `docs/AUTONOMOUS_WORK_ORDER.md` | The rule that applies right now, at the lowest context cost |
| **The record** | `notebook/`, `results/`, `docs/DECISIONS.md`, `docs/STATUS.md`, `docs/RUN_INDEX.md` | What was true on the day it was written |

Declare it. Every governed document carries one line under its title:

```markdown
**Audience:** the evaluating reader.
```

This is a convention. No gate checks it, and its value is that writing the line
forces the question.

## Register, by audience

**Cold reader.** Claim first. Evidence second. Caveats once, in one place, below
everything that earns trust. A reader who has not yet learned what this is
cannot evaluate a disclaimer about it.

**Evaluating reader.** Precision outranks brevity. Hedges that carry epistemic
status stay exactly as they are. This reader came to find the limits, so the
limits are the content and get stated plainly.

**Agent mid-task.** Imperative mood. One rule per bullet. Link out for the
reasoning. Every paragraph of justification in an agent-facing file is context
spent on every session forever, so it lives in `docs/WHY_THESE_RULES.md` and the
rule keeps a pointer.

**The record.** Unchanged, and never restyled after the fact. A record rewritten
for style is a record destroyed. New entries meet this standard and old entries
are left alone. Corrections are appended.

## What not to write

Each of these was found in this repository, and every example is real.

**Negative parallelism.** Defining a thing by what it is not. It reads as an
argument with an opponent who is not in the room, and at density it becomes the
only music in the prose. This repository carried fifty of them in two files.

> It is *we have not shown this works*, not *this does not work*.

Say the true thing once, in the affirmative. Keep the construction only where
the distinction between the two statements is itself the point, which is rare
and was previously claimed four times across four files.

**The apology opener.** Four documents here opened by confessing something.

> Hand-maintained, and this line used to claim otherwise.

Open with what the document is for. A correction is a record, and records have
their own address.

**Corrections in a shop window.** A confession belongs in `notebook/`, dated,
where it counts as evidence. Inside a document a stranger reads first, it is the
first impression.

**Pre-empting an objection nobody raised.**

> Nothing here is proven, and that is not a reason to avoid it.

The reader had not objected. Arguing with them teaches them to.

**Self-deprecation as a credibility move.** Admitting a fault to seem honest is
still a performance, and it spends the reader's goodwill on nothing. State what
is true and let the reader draw the conclusion.

**Em dash overuse.** This repository carried 277 of them across eight documents
and 393 more in the source. A comma, a colon, or a full stop is almost always
the better mark.

**The rule of three.** Three parallel clauses, three-item lists, three examples,
arriving because three sounds finished. Use the number of items there are.

**Announcing the writing.** "It is worth noting", "importantly", "in this
section we". Delete the announcement and keep the sentence.

## The positive frame

Write what was built and what was found. This is the rule the rest of the page
serves.

The mechanisms here are hard to build and most projects do not have them. That
makes them achievements, and an achievement gets written as one:

> The harness refuses to publish a result whose prediction cannot be shown by
> git ancestry to predate its data.

That sentence and "we cannot prove much yet" describe the same repository. The
first is true, specific, and earns trust. The second throws away the reason the
reader should give it.

A limitation found by your own instrument is a finding. The corpus here turned
out to be largely solvable by counting words, which the harness discovered, and
which paid for the rebuilt corpus every result since has run on. Written as an
achievement it becomes the most persuasive thing on the page. Written as an
apology it becomes a reason to close the tab.

None of this licenses overclaiming. Commit `8af6f38` in this history is titled
*"The keyword pass had written four claims the code does not support"*, and that
is the failure at the other end of this dial. Confidence applies to how a true
sentence is framed. It never applies to whether the sentence is true.

## Technical vocabulary and discoverability

Use the standard term for the standard thing. Write "LLM-as-a-judge",
"inter-rater reliability", "pre-registration", "ablation". They are precise, and
precision is why they exist.

Put them in sentences that describe what the code does. Search is served by the
GitHub topics, the repository description, and the per-page meta descriptions,
all of which already carry the vocabulary.

Two things this repository has done and will not do again. Do not build a
translation table mapping local names to industry names. Do not state an intent
to be found. A sentence explaining that you named something for discoverability
tells the reader you were thinking about being read instead of about being
right.

## Exemplars

The target voice already exists here. Read these before writing.

`docs/LIMITATIONS.md` opens:

> Written before any results exist, so it cannot be tuned to flatter them.

A caveat stated as a methodological strength, in fifteen words.

`docs/METHODS.md` opens with **What this is.** and then says what it is. Four
words of orientation, then content.

`site/src/pages/index.astro` is the best-written surface here: a headline, a
working demo, then the status. Read its ordering before restructuring anything.

## Three things a writing pass may never do

These are load-bearing and they outrank everything above.

1. **Never change a number, a confidence interval, a p-value, an arXiv
   identifier, or a quoted sentence.** Two published figures on the website are
   bound to verbatim sentences in `SCORECARD.md` through `site/claims.json`, and
   the citation gate binds numbers to quotes in `paper/refs.bib` by markdown
   block, so reflowing prose can move a figure into a block that cannot support
   it.
2. **Never delete a correction that a gate register depends on** unless the same
   commit shrinks the register. `[tool.decision-evals.docs-absent-commands]` in
   `pyproject.toml` refuses an entry named nowhere in the scanned documentation.
3. **Never flatten a hedge that carries epistemic status.** "We have not shown
   this works" and "this does not work" are different claims, and keeping them
   apart is what this repository is for. Collapse stacked hedges and leave the
   load-bearing one.

## How a writing pass runs

1. Read this file and the exemplars.
2. Run the `humanizer` skill. It applies to drafting as much as to editing, and
   to every file including source comments. There are no exempt files.
   `third-grade-copy` does not apply here: these are technical documents and a
   third-grade reading level would strip the precision they carry.
3. Rewrite.
4. Hand the result to a different agent for review, briefed with
   `docs/reviews/HOUSE_STYLE.md` and `docs/reviews/POSITIONING.md`. A
   cold-reader surface also gets `docs/reviews/COLD_READER.md`. A review that
   says "looks good" has not run.
5. Run `python -m uv run de check`. Editing a rendered document makes the site
   build stale, and `--fast` skips that step, so the full gate is the one that
   tells you.
