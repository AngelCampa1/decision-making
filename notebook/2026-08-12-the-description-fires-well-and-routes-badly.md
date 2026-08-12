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

## Next

- **Repair `p07` and `p08`** so they do not smuggle timing language into cascade
  cases, then re-run. The routing number should not be cited until then.
- **Put `x-n21`/`x-n22` to the maintainer.** Two defensible readings, and both
  the label and the description are mine.
- **Repeats.** One call per case. Track I says most of the variance in a repeated
  call is scatter, and every number above is n=1.
