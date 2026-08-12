# Trigger run: what I expect, written before it runs

**2026-08-12.** 73 cases (18 positive, 55 negative), one isolated call each,
Haiku. Measures the shipped `decision-making` description, not its answers.

## Why this and not more answer-quality work

Skill *availability* is the dominant term in whether a skill helps at all —
+18 to +36pp from presence against roughly +0.7pp from prose form, with
intervals crossing zero ([arXiv:2605.31408](https://arxiv.org/abs/2605.31408)).
Availability is decided by the description firing at the right moments. That has
never been measured here, on any skill, despite `triggers.py` existing since
early on — it was written, tested to 100%, and called by nothing.

It also needs **no answer key**. The labels are trigger labels: did the skill
fire, and did the router pick the procedure its own table names. That sidesteps
the failure mode that has produced 21 of 21 scored errors in this repository.

## What is being measured

**Primary: precision.** Of the turns it fired on, how many should it have. A
skill that improves answers while interrupting ordinary turns is a net loss to
whoever installed it, and an accuracy-only evaluation records that as a win.

**Also: recall, false-positive rate, and routing accuracy.** Routing is reported
*beside* precision and never instead of it — it answers the easier question
("given that it fired, did it read the right file"), and 4 of 18 positives carry
`route: ~` and are excluded rather than guessed.

## What this is not

It is a **proxy**. It shows a model the description and asks whether it would
invoke the skill. The real harness decides differently — the description sits
among other skills, in a longer context, with the model mid-task. So this
measures the description's discriminative content, not the deployed firing rate,
and the gap between those is not estimated here.

## Predictions, registered now

1. **Precision ≥ 0.80.** The negatives were built to look like triggers, so this
   is not free.
2. **Recall ≥ 0.85.** Higher than precision, because the description's positive
   clauses are broad and its negative clause is one sentence.
3. **False-positive rate ≤ 0.20.**
4. **Routing accuracy between 0.55 and 0.80.** Four procedures, so chance is
   0.25. Below 0.55 would mean the router's table does not discriminate and the
   one-entry-four-procedures design is buying nothing.
5. **The five promoted cases** — the ones that were negatives for
   `evidence-ledger` and are positives here — **fire.** If they do not, the
   consolidation widened the description on paper but not in behaviour.

## The standing bias

That is now the eighth consecutive set of predictions in the direction of this
project's design working, and six of the previous seven were wrong that way. The
A1 pilot this morning was the most recent. Recording the pattern again rather
than pretending this time is different.

## What would make me stop

- Any isolation failure.
- A parse rate below 90%: if the model will not answer in the fixed format, the
  measurement is of format compliance rather than of firing.
