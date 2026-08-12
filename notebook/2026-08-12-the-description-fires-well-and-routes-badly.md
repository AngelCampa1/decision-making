# The description fires well and routes badly

**2026-08-12.** Outcome of [the prediction registered an hour ago](2026-08-12-trigger-run-prediction.md).
73 cases, one isolated call each, Haiku, 0 unparseable, 0 isolation failures.

## Scoreboard

| # | Prediction | Result | Outcome |
|---|---|---|---|
| 1 | Precision ≥ 0.80 | **0.941** (16/17) | held |
| 2 | Recall ≥ 0.85 | **0.889** (16/18) | held |
| 3 | False-positive rate ≤ 0.20 | **0.018** (1/55) | held, by a lot |
| 4 | Routing accuracy 0.55–0.80 | **0.643** (9/14) | held |
| 5 | The five promoted cases fire | **2 of 5 did not** | **WRONG** |

Four of five held. **That breaks a run of six consecutive prediction sets that
were wrong in the optimistic direction**, and it is worth noting *why*: these
predictions were about a description's discriminative behaviour, not about this
project's hypothesis being true. The optimism bias has been about the
hypothesis, and this run did not test it.

## The headline, stated carefully

**The shipped description fires almost exactly where it should.** One false
positive in fifty-five look-alike negatives — each of which was built to carry a
trigger's surface features — is a 1.8% interruption rate on ordinary turns. That
is the number that decides whether a skill is worth having installed, and it is
good.

**And this is a proxy.** The model was shown the description and asked whether
it would invoke the skill. The deployed harness decides differently: the
description sits among other skills, in a longer context, mid-task. This
measures the description's discriminative content. The gap to real firing
behaviour is not estimated here and should not be assumed small — skill
shadowing is precisely a claim that *other* descriptions change this number.

## The one false positive is a fair miss

`n11` — *"Should I convert this to async? Here's the function and its two
callers."* The skill fired. Its own **Abort if** says lookup, calculation or
technical diagnosis, and this is a technical judgement call with pasted context
and the words "should I". I would defend the negative label, and I can see the
firing.

Notably it returned `procedure: null` — it decided to fire and could not say
which procedure. That is a useful signal the harness could exploit: *fired but
routed nowhere* is a cheap abort condition, and nothing in `SKILL.md` currently
says so.

## Prediction 5 failed, and I cannot tell which way

Two of the five cases I promoted from `evidence-ledger`'s negatives did not fire:

- `x-n22` — *"The build is green. Can I deploy?"*
- `x-n21` — *"The disk is at 99%. Do we need to act?"*

I promoted them this morning arguing they match the router's timing row
("the direction is settled and the question is when"). Two readings, and **the
run cannot separate them**:

1. **The promotion was wrong.** These read as operational go/no-go checks with a
   determinate answer, not decisions someone wants help deciding.
2. **The description widened on paper but not in behaviour.** Consolidating four
   narrow skills behind one router was supposed to broaden the trigger surface,
   and here it did not.

The label is mine, which puts this squarely in the territory that produced 21 of
21 scored errors here. Recording the disagreement rather than resolving it, and
flagging it for the maintainer — this is the kind of call that should not be
made by the party who wrote both the label and the description.

## Routing is the weak half, and some of it is my authoring

0.643 over 14 labelled cases, against 0.25 chance. Better than chance, well short
of good. The confusions are not random:

| Case | Wanted | Got |
|---|---|---|
| `p07` | cascade | timing |
| `p08` | cascade | timing |
| `p03` | ledger | fit |
| `p06` | fit | cascade |

**Both cascade failures went to timing, and both of my cascade cases contain a
time word.** `p07` says *"resign on Friday"*; `p08` says *"now or not at all"*.
I wrote temporal language into the cases meant to test consequence reasoning, so
part of this is a defect in the trigger set rather than in the router. That is
fixable and should be fixed before the number is quoted anywhere.

What survives that correction is still a real finding: **`cascade` and `timing`
are the confusable pair**, which is exactly what the router's own table would
predict — one is about what an action sets in motion, the other about when to
take it, and a decision usually has both.

## What this means for the one-entry design

`CLAUDE.md` says the choice to ship one skill rather than four is "a judgement
call wearing a citation", because the published shadowing evidence sits at 202
skills and the decision was made at four. This run does not settle that, but it
gives the first local number on the half nobody had measured:

- **Availability is not the problem.** 0.941 precision, 0.018 FPR.
- **Selection within the bundle is.** 0.643.

If that holds up after the trigger set is repaired, it points somewhere specific:
the cost of consolidation is not that the skill fires wrongly, it is that having
fired, it reads the wrong file. Which is a *different* failure from shadowing,
and a cheaper one to fix — it lives in the router table, not in the description.

## Second run, same day — and it is the more useful one

`p07` and `p08` were repaired to carry no time word, and the whole set re-run.

| | Run 1 | Run 2 |
|---|---|---|
| precision | 0.941 | **1.000** |
| recall | 0.889 | 0.833 |
| false-positive rate | 0.018 | **0.000** |
| **routing accuracy** | **0.643** | **0.643** |
| routing confusions | p03, p06, p07, p08, x-n22 | p03, p06, p07, x-n20, x-n22 |

**Routing accuracy is identical to three decimal places and the errors are not
the same errors.** `p08` was fixed by the repair; `p06` moved from
cascade→timing; `x-n20` newly failed. The false positive `n11` also flipped to
correct without anything about it changing.

So the repair did what it was supposed to and **the aggregate did not move at
all.** The right reading is not that the repair failed. It is that

> **the per-item verdicts are unstable across runs while the aggregate is
> stable.**

That is the aptitude-versus-unreliability decomposition
([arXiv:2505.06120](https://arxiv.org/abs/2505.06120)) arriving in a third
place — after the multi-turn literature and after the orchestrator ablation this
morning. The mean is a real quantity; the individual confusions are close to
noise, and reading a story into "cascade confuses with timing" from one run
would have been reading noise.

**Every number in this entry is n=1 and should be treated as such.** The two
runs together are n=2, and they disagree on four of seventy-three items while
agreeing on the summary.

Which also means the thing I flagged for the maintainer needs restating more
carefully. Across the two runs the promoted cases fired like this: `x-n20` fired
once, `x-n21` never, `x-n22` never. That is not five cases with a verdict — it is
one stable non-firing pair, one coin flip, and two that fired both times.

## Next

- **Repeats, and they are now the priority.** Two runs already show the item
  verdicts moving. `repeats_for_reliability` in `stats/reliability.py` exists to
  size this; nothing here should be quoted until it has.
- **Put `x-n21`/`x-n22` to the maintainer.** Neither fired in either run. Both
  the label and the description are mine, and this is the class of call that
  produced 21 of 21 scored errors here.
- **`fired but routed nowhere`** showed up in both runs and is a cheap abort
  condition the skill does not currently name.

---

**Superseded, 2026-08-12.** Five repeats now exist:
[2026-08-12-five-repeats-firing-is-stable-routing-is-not.md](2026-08-12-five-repeats-firing-is-stable-routing-is-not.md).

Two claims above do not survive.

**"The per-item verdicts are unstable while the aggregate is stable."** True of
firing — 70 of 73 items return the identical verdict five times running. **False
of routing**, whose per-run accuracy has sd 0.108 over five repeats (mean 0.686,
range 0.571–0.857). The two runs recorded above both read 0.643, and I took that
agreement as the aggregate holding still. At that spread it was a coincidence.

**The confusion tables.** The specific per-run confusion lists above are mostly
noise. What survives repeats is narrower and more useful: `p06` is never routed
correctly in five attempts and `p07` almost never, both drifting to `timing`.
Those two are router-table defects. The rest of the lists are draws.

The `x-n21`/`x-n22` flag stands and is now firmer: 0/5 each, against 5/5 for the
other three promoted cases. A stable disagreement rather than a coin flip.
