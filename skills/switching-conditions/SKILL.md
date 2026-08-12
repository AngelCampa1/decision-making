---
name: switching-conditions
description: >-
  Use when someone asks what they should do about their own life or work — take
  the offer, move, buy or keep renting, go back to study, leave, tell them — and
  the right answer turns on facts about that particular person. Produces the
  generic answer, the specific facts that would overturn it with the threshold
  at which each one bites, and an answer that stays conditional on whatever is
  still unknown. Do not use for factual lookups, for questions with the same
  answer for everyone, for debugging or code review, or when the person's
  situation is already fully specified.
license: Apache-2.0
compatibility: ">=1.0"
metadata:
  version: 0.1.0
  status: experimental
  verdict: UNTESTED
  primary_metric: switch_discrimination
  claims:
    - id: sc-1
      text: The generic answer is written down separately, before any tailoring, so that it is visible as generic.
    - id: sc-2
      text: Each switching condition names the threshold or state at which the recommendation changes, not merely the topic it concerns.
    - id: sc-3
      text: Only facts that would change the recommendation are asked for.
    - id: sc-4
      text: An answer left conditional on an unknown is a complete answer rather than a deferral.
    - id: sc-5
      text: The skill exits without switches when the question does not depend on who is asking.
allowed-tools: []
---

# Switching conditions

Most advice is correct in general and wrong for the person asking. *Build six
months of runway before you leave* is sound, and useless to someone whose visa
is tied to their employer. The failure is invisible from the inside: the advice
is true, well reasoned, and never touches the situation.

The fix is not to ask more questions. It is to work out which facts would
**overturn** the answer, and then ask only for those.

## Abort if

- The question has one answer regardless of who is asking.
- It is a lookup, a calculation, or a technical diagnosis.
- The context already settles every fact that would move the answer.

## Step 1 — Say the generic answer out loud

Write the answer you would give knowing nothing about this person. One or two
sentences. Do not skip this because it feels obvious.

Writing it down is what makes it inspectable. An unstated generic answer gets
quietly decorated with whatever the person mentioned and then presented as
though it were tailored.

## Step 2 — Find the switches

Ask: **what would have to be true about this person for that answer to be
wrong?** Each switch names a fact *and* the point at which it bites.

- "Runway" is not a switch. "Under about four months of runway, the answer
  becomes take the contract first" is.
- Put a number, a date, or a named state on it wherever the domain allows one.
- Three to five switches. If you have twelve, they are not switches, they are
  considerations, and considerations do not change answers.

A switch you cannot state a threshold for is usually a preference in disguise.
Say so rather than dressing it as a condition.

## Step 3 — Ask for the fewest facts that decide it

Sort the switches by how much they move the answer. Ask about the top one or
two. **Do not run an intake interview** — a person who wanted a form would have
filled one in.

Then answer. If something decisive is still unknown, give the conditional
answer: it is the complete answer, not a way of avoiding one.

## Output

```
GENERIC
  <the answer knowing nothing about them>

SWITCHES
  - <fact> — at <threshold> the answer becomes <X>
  - <fact> — if <state> the answer becomes <Y>

KNOWN / UNKNOWN
  known:   <what the context already settles>
  unknown: <the smallest set that would settle the rest>

THEREFORE
  <the answer, conditional where it has to be>
```

If nothing switches, say the generic answer is the answer here, and why.
