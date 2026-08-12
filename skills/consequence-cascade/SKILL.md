---
name: consequence-cascade
description: >-
  Use when an action looks fine on its own and the worry is what it sets in
  motion — resigning before something is signed, telling one person before
  another, taking the money now, moving first and sorting the rest out later.
  Produces the chain of effects to the point where it stops being knowable, the
  options the action quietly spends, and the order the steps have to happen in.
  Do not use for contained one-off actions with no downstream, for reversible
  low-stakes choices, or for creative and exploratory work where following
  consequences is not the point.
license: Apache-2.0
compatibility: ">=1.0"
metadata:
  version: 0.1.0
  status: experimental
  verdict: UNTESTED
  primary_metric: foreclosure_recall
  claims:
    - id: cc-1
      text: The chain is followed only to the point where the next step stops being knowable, and that stopping point is stated.
    - id: cc-2
      text: Options the action removes are named separately from effects the action causes.
    - id: cc-3
      text: Where two steps can happen in either order, the orders are compared rather than assumed.
    - id: cc-4
      text: One chain is followed per action under consideration, rather than a branching tree of possibilities.
    - id: cc-5
      text: The skill exits when the action has no downstream worth tracing.
allowed-tools: []
---

# Consequence cascade

An action is usually judged on what it does. The trouble is rarely there. It is
in what the effect makes possible, and in what it quietly takes off the table.

Resigning gets you out. It also ends your standing to raise the thing you were
going to raise, and that second effect is the one that decides whether resigning
was right.

## Abort if

- The action is contained and has no downstream.
- It is small, reversible, and cheap to undo.
- The work is creative or exploratory rather than a decision.

## Step 1 — Follow the chain until it stops being knowable

First order: what happens directly. Second: what that makes true. Third: what
*that* makes true.

Stop when you can no longer say "and then" without inventing. That is usually
three steps, sometimes two. **Say where you stopped.** A chain that runs to six
steps is a story, and it will be more confident than the three-step version
while being worth less.

One chain per action. Branching into every possible world produces a tree nobody
can act on.

## Step 2 — Name what it forecloses

Separate from effects, and more important than them: **which choices does this
remove?**

Effects are things that happen. Foreclosures are things that stop being
available — leverage you spend, standing you lose, a door that closes behind
you, a fallback you were counting on without having counted it.

Effects announce themselves. Foreclosures do not, because nothing happens when
an option disappears. That asymmetry is the whole reason to look.

## Step 3 — Check the order

Where two steps could happen either way round, compare the orders explicitly.
Do not assume the obvious one.

Signing then negotiating is a different decision from negotiating then signing.
Telling A before B is different from telling B before A. Often one order keeps
everything open and the other spends the only leverage there was, and the two
look identical from a step away.

## Output

```
CHAIN
  1st  <what happens directly>
  2nd  <what that makes true>
  3rd  <what that makes true> — stops being knowable here

FORECLOSES
  - <option removed> — <how it goes, and whether it comes back>

ORDER
  <which steps are order-sensitive, and which order to take>

THEREFORE
  <do it, do it in this order, or do this other thing first>
```
