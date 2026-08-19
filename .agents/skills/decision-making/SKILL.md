---
name: decision-making
description: >-
  Use when someone is trying to decide something and wants help deciding it —
  "help me think this through", "should I take it", "what would you do", or a
  pile of context ending in a question about what to do. Routes to one of six
  procedures depending on what is actually hard about the decision: too much
  context, advice that may not fit this person, downstream consequences,
  timing, several positions that are each defensible, or a missing fact that
  may or may not matter. Do not use for factual lookups, for creative or exploratory work, for
  code review and debugging, or when the person wants information rather than a
  recommendation.
license: Apache-2.0
compatibility: ">=1.0"
metadata:
  version: 0.3.0
  status: experimental
  verdict: UNTESTED
  primary_metric: decision_admissibility
  claims:
    - id: dm-1
      text: One procedure is selected and run, rather than all of them being applied to every question.
    - id: dm-2
      text: The procedure is chosen from what is hard about the decision, not from its subject matter.
    - id: dm-3
      text: A decision is produced; the procedure is working, not output.
    - id: dm-4
      text: Where several of ledger, fit, cascade and timing apply, they run in that order and the reason for the order is that each supplies an input to the next. council and hinge are not in that chain; each runs alone.
    - id: dm-5
      text: The skill exits without a procedure when the question is not a decision.
allowed-tools: []
---

# Decision making

Six procedures. **Read one.** Which one depends on what is hard about this
particular decision — not on its subject.

| What is hard | Read | What it produces |
|---|---|---|
| A pile of context arrived and it is unclear which already-known fact decides it — the choice itself, not what acting on it would set off | `ledger.md` | what bears on it, what was set aside, and why |
| The advice may be generically right and wrong for this person | `fit.md` | the generic answer, and the facts that would overturn it |
| The action looks fine and the worry is what it starts, or what it spends | `cascade.md` | the chain, what it forecloses, and the order |
| The direction is settled and the question is when | `timing.md` | the undo price, the real deadline, what waiting buys |
| Several positions are each defensible, and whichever was argued first has the advantage | `council.md` | the case for each, argued fairly, and which one survives |
| The fact the decision actually turns on was never given, not just buried in what's already known, and it's unclear whether asking for it is worth the wait | `hinge.md` | which gaps would change the answer, and the answer now or the one question to ask |

## Abort if

- It is a lookup, a calculation, or a technical diagnosis.
- The work is creative or exploratory rather than a decision.
- They want information, not a recommendation. Give them the information.

## Choosing

Ask what would most change the answer if you got it wrong. That names the
procedure. If nothing obvious separates them, that ambiguity is itself
information: reread each candidate's *Abort if* list and take whichever one
nothing on it rules out, rather than defaulting to one procedure by habit.

**If no procedure fits, that is the answer.** Not being able to name one is
usually a sign this is a lookup, a technical judgement, or a request for
information wearing a decision's phrasing — go back to *Abort if* and answer
directly.

`council.md` and `hinge.md` sit outside the four-chain, and outside each other
— each runs alone. Both, when they apply, run before `ledger`, `fit`, `cascade`
and `timing`: until the positions are settled or the missing fact is asked for
or guessed at out loud, there is no single action or answer for the other four
to work on. Where both seem to apply, resolve the missing fact first — it can
collapse a disagreement `council.md` would otherwise have to argue out.

Within the four, more than one can apply. Run them in this order, because each
one feeds the next: **ledger → fit → cascade → timing.** You cannot tell what
fits a person until you know what is on the table; you cannot follow
consequences until you know which action you are considering; timing is last
because it is a question about an action already chosen.

Two is usually the most that earns its place. Three means the decision probably
needs breaking into two decisions.

## The point is the decision

These are working procedures, not an output format. **Do the procedure, then
answer.** A reply that hands back four labelled blocks and no recommendation has
turned someone's question into an audit of their question.

Show the working only where it changes what you would say, or where the person
would reasonably want to check it. The person asked what to do.

If a procedure is producing worse answers than thinking directly, say so. That
is worth more than politely using it.
