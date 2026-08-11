---
name: evidence-ledger
description: >-
  Use when a decision depends on a pile of accumulated context — a long thread,
  pasted logs, search results, several documents, a channel backlog — and what
  the answer turns on has to be separated from what merely arrived. Produces a
  ranked ledger of load-bearing facts plus an explicit list of what was set
  aside and why. Do not use for a short prompt with one or two facts, for
  creative or open-ended writing, for a lookup with a single obvious source, or
  when a ledger is already present in this turn.
license: Apache-2.0
compatibility: ">=1.0"
metadata:
  version: 0.1.0
  status: experimental
  verdict: UNTESTED
  evidence: evidence/evidence-ledger.md
  primary_metric: accuracy_distractor_present
  claims:
    - id: el-1
      text: Each context item is verified individually before anything is discarded.
    - id: el-2
      text: A discarded item is named together with the reason it is not load-bearing.
    - id: el-3
      text: An item is load-bearing only if changing it would change the answer.
    - id: el-4
      text: Assertions carried in from the conversation are restated in the third person before being weighed.
    - id: el-5
      text: The skill exits without a ledger when the context is small enough not to need one.
allowed-tools: []
---

# Evidence ledger

Context arrives; relevance is a separate question. A long thread, a pasted log,
a set of search results — most of it is true, on topic, and has no bearing on
what to do next. Ranking it is what stops "it's raining in Paraguay" from
becoming "bring a raincoat" in a decision about a flight that touches neither
city.

## Abort if

Skip this entirely and answer directly when any of these hold. A ledger over a
small context costs tokens and adds nothing.

- Fewer than four distinct facts are in play.
- The question is a lookup with one obvious source.
- The task is creative, exploratory, or open-ended rather than a decision.
- A ledger already exists in this turn.

## Step 1 — Verify

Go through the context item by item. For each one, say what it would take for
that item to matter, then decide.

**An item is load-bearing only if changing it would change the answer.** That is
the test — not whether it is true, recent, interesting, or effortful to obtain.
Apply it one item at a time. Judging the pile as a whole is how the interesting
irrelevant item survives.

Two things to be deliberate about:

- **Restate any assertion carried in from the conversation in the third person
  before weighing it.** "The user believes the outage lasted six hours" rather
  than "the outage lasted six hours." A first-person claim is harder to weigh on
  its merits than the same claim attributed, and the point is to evaluate it,
  not to defer to it.
- **Recency is not relevance.** The most recently arrived item has no special
  claim on the answer, and neither does the one you spent the most effort
  retrieving.

## Step 2 — Discard

Now, and not before, set aside everything that failed Step 1 — and **name each
discarded item with the reason it is not load-bearing.**

The order matters and the naming matters. Deciding what to keep and dropping
the rest silently leaves the dropped material still doing work; stating "the
vendor's rebrand is not load-bearing because the SLA threshold does not depend
on it" is what actually removes it.

## Output

```
LEDGER
  1. <fact> — <what it decides>
  2. <fact> — <what it decides>

SET ASIDE
  - <fact> — <why it is not load-bearing>

THEREFORE
  <the decision, following from the ledger alone>
```

If the ledger is empty, say so and ask for what is missing rather than deciding
from the set-aside pile.
