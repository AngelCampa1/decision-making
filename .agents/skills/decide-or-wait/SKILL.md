---
name: decide-or-wait
description: >-
  Use when the question is about timing rather than direction — should I commit
  now, hold off, accept the offer today, sign, quit, tell them yet — or when a
  decision feels urgent and it is not clear whether the urgency is real.
  Produces whether the move is reversible and at what cost, which deadline is
  real, what waiting buys and what it costs, and often a split into the part to
  do now and the part to defer. Do not use when the choice itself is unresolved
  rather than its timing, when a hard external deadline has already passed, or
  for scheduling and calendar questions.
license: Apache-2.0
compatibility: ">=1.0"
metadata:
  version: 0.1.0
  status: experimental
  verdict: UNTESTED
  primary_metric: timing_admissibility
  claims:
    - id: dw-1
      text: Reversibility is stated as a cost to undo rather than as a yes or no.
    - id: dw-2
      text: Each deadline is marked real or imagined, and a real one names what enforces it.
    - id: dw-3
      text: What waiting buys is named as specific information arriving at a specific time, not as general clarity.
    - id: dw-4
      text: The cost of waiting is stated even when the recommendation is to wait.
    - id: dw-5
      text: The decision is split into its reversible and irreversible parts wherever the parts can move separately.
allowed-tools: []
---

# Decide or wait

Cheap, reversible decisions get agonised over. Expensive, irreversible ones get
made fast, because they are the ones that feel urgent. That inversion costs more
than picking wrong does.

Timing is a separate question from direction, and it is answerable even while
the direction is still open.

## Abort if

- What to do is still unresolved. Settle direction first; this is about when.
- The deadline has passed and the choice is now forced.
- It is scheduling — a calendar has no option value.

## Step 1 — Price the undo

Not *is this reversible* but **what does undoing it cost**, in time, money,
relationships, and what it forecloses. "Reversible" is rarely binary.

Resigning is reversible for about a week and effectively not after that.
Accepting a counter-offer is reversible and leaves a mark. Telling someone
something is never reversible at all. Say which of these you are looking at.

## Step 2 — Separate the real deadline from the felt one

Every urgent decision has a date attached. Ask what enforces it.

**Real:** an offer that expires in writing, a lease that renews, a visa, a
filing window, a flight. Something outside the decision imposes it.

**Felt:** wanting the discomfort to stop, someone else's impatience, a round
number on a calendar. These are worth naming precisely because they do not
appear as deadlines from the inside — they appear as urgency.

## Step 3 — Say what waiting buys, and what it costs

**Buys:** name the information and when it arrives. "In three weeks I will know
whether the funding closed" is a reason to wait. "Things will be clearer" is not
— nothing arrives on that date.

**Costs:** the offer weakens, the option decays, the other party moves, the
decision gets made for you. Waiting is a choice with a price, and a
recommendation to wait that does not state the price is incomplete.

Then look for the split. Often part of the move is reversible and can happen
now, and only a smaller part has to be committed to later. Taking the call,
running the numbers, telling one person — these usually cost nothing and buy
information.

## Output

```
UNDO COSTS
  <what it takes to reverse, and for how long that stays possible>

DEADLINE
  real:   <date — and what enforces it>
  felt:   <what feels urgent and is not>

WAITING
  buys:  <what you learn, and when>
  costs: <what decays meanwhile>

THEREFORE
  <decide now / wait until X / do the reversible part now, commit by X>
```
