# 2026-08-11 — The venue was in the wrong cell

No model calls. A redirection, and a literature check that should have happened
in week one.

## What prompted it

The maintainer, unprompted by anything in the repository:

> i also feel like agentic systems fall in the trap of "the last message" they
> weight a ton on the last message or the last finding without weighting
> everything. not sure if we're sending the entire corpus at once at the agent
> or we're having a conversation like this inside claude code

The answer to the second half is: the entire corpus at once. Every call in this
repository is one `claude -p` with the whole prompt on stdin. There are no turns.
So the effect described in the first half **cannot occur in any corpus built
here**, because nothing arrives at different times.

## The repository had already written this down

`docs/ACCUMULATION_VENUE.md`, written before the casefiles existed:

> accumulation is *rendered* rather than lived … What it does not share is error
> compounding across the model's own steps, which this venue cannot measure and
> should not claim to.

`docs/FAILURE_TAXONOMY.md`, from the other direction: four of Harness-Bench's
five failure categories are structurally unreachable in a single-turn, no-tool
venue. Tool failures, grounding gaps, state and continuation issues cannot
happen.

Both documents name the limitation precisely. Three corpora were then built
inside it. **Writing down a limitation is not the same as acting on it**, and
nothing in `de check` enforces the difference.

## What the literature says, checked today

| Finding | Number |
|---|---|
| Single-turn → multi-turn accuracy drop ([2505.06120](https://arxiv.org/abs/2505.06120), ICLR 2026) | **−39% average**, 15 models, 200k conversations |
| That drop is increased *unreliability*, not lost aptitude | same model, same question, answers scatter |
| Multi-agent failure taxonomy ([MAST](https://arxiv.org/abs/2503.13657)) | 14 modes, κ=0.88; 36.9% inter-agent misalignment |
| Summarisation moves decisions ([2606.29251](https://arxiv.org/html/2606.29251)) | different summarisers, opposite directions, same evidence |
| Curated skills ([SkillsBench](https://arxiv.org/abs/2602.12670)) | +16.6pp; self-generated ≈0 or negative |

The largest single effect in this table is 39%, from a variable this repository
has held constant across every corpus it has built.

## Two things I had wrong

**Repeats.** The long-context plan argues repeats are near-worthless because
between-item variance dominates within-item sampling variance. That is correct
for estimating a mean and exactly wrong for estimating reliability — and the
multi-turn result says the degradation *is* the reliability. A design that
maximises cores and minimises repeats is optimal for the wrong estimand. Track I.

**The SkillsBench figure.** `CLAUDE.md` and `AGENTS.md` cite "+18 to +36pp". The
paper's headline is +16.6pp average (33.9 → 50.5). Not yet verified against the
paper itself; logged as a correction task rather than silently changed, because
the range may be a per-domain figure I read once and compressed badly.

## The instrument blocker, again

`ISOLATION_FLAGS` hard-codes `--tools ""` and `--no-session-persistence`. The
first blocks sub-agent dispatch, the second blocks session resume. Neither the
multi-turn venue nor the sub-agent venue can run at all today.

This is the third time the instrument has been found unable to produce the
phenomenon — after the argv length cap and the cached-token accounting — and the
first two were both found by a canary rather than by reading. The lesson is
holding: **build the smallest thing that would fail, before authoring anything.**

And the flags are load-bearing. `2026-08-10-isolation-canary.md` records that a
planted `CLAUDE.md` is injected even when the system prompt is fully replaced;
`--setting-sources ""` is what stops it. Opening `--tools` reopens a path that
was closed for a measured reason, so every relaxation needs its own canary.

## What changed

`docs/RESEARCH_PROGRAMME.md`, eleven tracks. The long-context experiment becomes
Track G — an interaction term rather than the headline — and its ~960k characters
of pilot-library authoring is on hold until Track A reports whether turn
structure dominates volume.

Track A is the correction to the repository's cardinal error: three corpora were
built to fix a failure never shown to exist here. It reuses the 12 existing
casefiles, costs roughly 1,200 calls, and can redirect or kill everything
downstream before a single new document is written.

**Prediction, logged before Track A runs.** On the 12 casefiles, sharded across
~6 turns against delivered whole, on Haiku 4.5: admissibility falls from 0.917
to **0.70 ± 0.10**, and within-item scatter at least doubles. I am recording it
because my last five predictions were wrong in the same direction — toward the
experiment working — and the record should keep saying so.
