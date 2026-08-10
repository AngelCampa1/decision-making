# 2026-08-10 — Positioning: what the prior art gets wrong, and the tension we can resolve

## The prior art

`tjboudreaux/cc-thinking-skills` ships 28 thinking skills. Its README says, with
unusual honesty:

> Zero skills currently hold a robust, replicated ELEVATE verdict... All 28
> shipped skills are manual-only; none is proven to improve model accuracy.

Its best candidate, `thinking-scientific-method`, reached +5.3pp at p=0.061 and
was correctly labelled as failing its own gate.

Worth being precise about what went wrong there, because it isn't laziness — the
project has an eval harness and a published scorecard, which is more than most.
Three things:

1. **All 28 skills are pure inline prompt text.** None uses `references/`,
   `scripts/`, or `assets/`. Nothing computes; the model is asked to do
   probability arithmetic in free text, which is the exact operation GSM-Symbolic
   says it is unreliable at.
2. **All 28 set `disable-model-invocation: true`**, so none auto-triggers. A user
   has to already know they need "pre-mortem" and type it. But the failure mode
   these skills target is *not knowing you need them* — the Paraguay raincoat is
   never fixed by someone who thinks to type `/relevance-gate`. This is an
   understandable defence against over-triggering that removes most of the value.
3. **The evals don't reach users.** A plugin install copies only the plugin
   directory, so `evals/`, the scorecard, and the audit never arrive. The
   evidence exists but isn't shipped.

Our counters, in order: put computation in `scripts/`; let cheap skills
auto-trigger and make false positives cheap rather than trying to eliminate them;
ship the *verdicts* (not the harness) inside the plugin as frontmatter metadata
plus an `evidence/` directory.

## The tension worth resolving

Two 2026 papers disagree about something central to this whole project, and both
are credible.

**SkillsBench** (arXiv:2605.31408), controlled, 86 tasks across 11 domains:
having a relevant skill available is worth **+18.0 to +36.0pp**. But varying the
*granularity and detail* of the skill's prose moved results only **+0.7pp** on
GPT-5.5 and **−6.7pp** on DeepSeek V4-Flash, confidence intervals crossing zero.
Worked examples added +0.7–1.3pp. Conclusion: presence matters enormously,
wordsmithing barely does.

**SkillOpt** (arXiv:2605.23904, Microsoft Research): treating `SKILL.md` as a
trainable parameter — bounded edits, a held-out validation gate, a rejected-edit
buffer — yields **+23.5pp average** on GPT-5.5 across 6 benchmarks, and it is
evaluated *inside Claude Code and Codex CLI harnesses*, i.e. the same setting we
care about. Conclusion: optimising that same prose is worth a great deal.

These cannot both be generally true. Either the prose matters or it doesn't.

## Why we're positioned to say something

Not because we're smarter, but because of what SkillOpt doesn't report. It has
**no confidence intervals, no significance tests, and no correction** for the
many implicit comparisons its accept-if-strictly-better gate performs. That gate
is a ratchet, not a hypothesis test: repeatedly accepting whatever improves a
single held-out split is precisely the procedure that manufactures apparent gains
through unadjusted multiple comparisons. Its own ablation also shows a
target-matched optimiser recovers only 56–74% of the gain versus a frontier
optimiser, which implies a distillation component the paper doesn't name as one.

Our optimisation ablation tests exactly this, with the SkillsBench null
**pre-registered as our prediction**. That pre-registration is the point — it is
what makes a null result informative rather than a failure to find something.

Also relevant: the benchmark-selection bias. SkillOpt's six benchmarks were
chosen because they admit crisp automatic scoring. That's a reasonable
constraint, but it makes "52/52 best-or-tied" a much weaker generality claim than
it sounds, and it isn't flagged as a limitation.

## Recorded prediction

Prose optimisation produces a null on our tasks (CI including zero), while skill
*presence* and *trigger quality* produce clear effects. If GEPA/ACE optimisation
does produce a real gain, I expect it to be concentrated in tasks with a crisp
procedural answer, and to transfer poorly from the small optimiser model to
Sonnet — the Prompting Inversion pattern (arXiv:2510.22251), where scaffolding
tuned for a weaker model becomes handcuffs on a stronger one.

## The thing this changes about where effort goes

If SkillsBench is right, then the highest-return engineering is **triggering**,
not wording. That reorders the work: sharp descriptions with explicit negative
clauses, a ready-to-paste `AGENTS.md` block, and a measured
positive/negative-trigger set with firing precision and recall reported
separately from task accuracy. A suite that improves accuracy 10pp while firing
on 60% of ordinary turns is a net loss in daily use, and no accuracy-only
evaluation would catch that.
