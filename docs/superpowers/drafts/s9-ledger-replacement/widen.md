---
draft: true
not-shipped: true
candidate-for: ledger.md
status: hypothesis
---

# Widen (draft — not shipped, not wired into any router)

**Audience:** an agent mid-task, if this is ever promoted. Today, the record.

**This file is not a live procedure.** It sits outside `skills/decision-making/`
on purpose — see `docs/superpowers/drafts/s9-ledger-replacement/README.md` for
why it is a candidate and not a swap. If it is ever promoted, the frontmatter
above is deleted and it moves into `skills/decision-making/` under its own
`de check` gates.

---

A model asked to help decide tends to produce one answer and then improve it —
add a caveat, hedge a clause, reconsider a step — rather than putting up two or
three genuinely different answers and choosing between them. The improving
looks like rigor. What it cannot do is show you the option that never got
generated because the first one already had all the attention.

The fix is not "think harder about the option you have." It is to produce more
than one option **before** evaluating any of them, so that evaluation is a
comparison instead of a polish.

## Abort if

- Only one course of action is actually available — there is no second option
  to generate.
- The context already narrows the field to one defensible choice.
- The task is a lookup, a calculation, or a technical diagnosis rather than a
  choice among plausible actions.
- Options already exist, stated in full, and the work is comparing named
  options rather than generating unstated ones — that is a different problem
  and this procedure adds nothing to it.

## Step 1 — Generate before evaluating

Produce two or three candidate answers **independently** — each one reasoned
from the situation on its own terms, not as a variation on the first. Do not
rank, critique, or soften any of them while generating the others; evaluation
after all candidates exist is the whole point, and evaluating the first one
while writing the second is how it quietly becomes the anchor.

Where the harness allows it, this is a natural fan-out: generate each
candidate as an independent pass and only then bring them into the same
context to compare. Where it does not, generate them as clearly separated
blocks in one pass and resist revising an earlier block once a later one exists.

## Step 2 — State what would make each one right

For each candidate, name the situation in which it is the best of the set —
not a list of pros and cons, but the specific condition under which this
option, rather than the others, is what a careful person would pick.

An option with no such condition is not a real alternative. It is the first
option's shadow, restated.

## Step 3 — Compare, then choose

Now, and only now, weigh the candidates against what is actually known about
this situation. State which one the known facts favor, and what would have to
be true for a different one to win instead.

## Output

```
CANDIDATES
  1. <option> — right when <condition>
  2. <option> — right when <condition>
  3. <option> — right when <condition>

KNOWN
  <what the situation actually establishes>

THEREFORE
  <the candidate the known facts favor, and what would flip it>
```

If only one candidate survives Step 1 — every other attempt collapses back
into it — say so. That is itself informative: the field was narrower than it
looked, not that the procedure failed.
