---
name: decision-making
description: >-
  Use when someone is trying to decide something and wants help deciding it —
  "help me think this through", "should I take it", "what would you do", or a
  pile of context ending in a question about what to do. Routes to one of four
  procedures depending on what is actually hard about the decision: too much
  context, advice that may not fit this person, downstream consequences, or
  timing. Do not use for factual lookups, for creative or exploratory work, for
  code review and debugging, or when the person wants information rather than a
  recommendation.
license: Apache-2.0
compatibility: ">=1.0"
metadata:
  version: 0.2.0
  status: experimental
  verdict: UNTESTED
  primary_metric: decision_admissibility
  claims:
    - id: dm-1
      text: One procedure is selected and run, rather than all four being applied to every question.
    - id: dm-2
      text: The procedure is chosen from what is hard about the decision, not from its subject matter.
    - id: dm-3
      text: A decision is produced; the procedure is working, not output.
    - id: dm-4
      text: Where several procedures apply, they run in the stated order and the reason for the order is that each supplies an input to the next.
    - id: dm-5
      text: The skill exits without a procedure when the question is not a decision.
allowed-tools: []
---

# Decision making

Four procedures. **Read one.** Which one depends on what is hard about this
particular decision — not on its subject.

| What is hard | Read | What it produces |
|---|---|---|
| A pile of context arrived and it is unclear what the answer turns on | `ledger.md` | what bears on it, what was set aside, and why |
| The advice may be generically right and wrong for this person | `fit.md` | the generic answer, and the facts that would overturn it |
| The action looks fine and the worry is what it starts, or what it spends | `cascade.md` | the chain, what it forecloses, and the order |
| The direction is settled and the question is when | `timing.md` | the undo price, the real deadline, what waiting buys |

## Abort if

- It is a lookup, a calculation, or a technical diagnosis.
- The work is creative or exploratory rather than a decision.
- They want information, not a recommendation. Give them the information.

## Choosing

Ask what would most change the answer if you got it wrong. That names the
procedure. If nothing obvious separates them, the pile is usually the problem —
start with `ledger.md`.

More than one can apply. When they do, run them in this order, because each one
feeds the next: **ledger → fit → cascade → timing.** You cannot tell what fits a
person until you know what is on the table; you cannot follow consequences until
you know which action you are considering; timing is last because it is a
question about an action already chosen.

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
