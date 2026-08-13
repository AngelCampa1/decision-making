# The maintainer picked eager, provisionally

**2026-08-13.** A product decision, not a measurement. Recorded because five runs
have now ended with the same sentence — *"which point on the precision/recall
frontier is wanted is a decision nobody here has made"* — and it is made.

## What was asked

Every description variant tested lands somewhere on one trade. There is no arm
that is better at both ends.

| variant | interrupts you wrongly | catches the decisions |
|---|---|---|
| `opener-only` | **11.3%** of ordinary turns | **95.6%** |
| `no-exclusions` | 5.5% | 91.1% |
| **`full` (shipped)** | 1.8% | 87.8% |
| `no-opener` | **0.0%** | 86.7% |
| four separate entries | 0.0% | 80.0% |
| two entries, any partition | 0.0–0.9% | 75.6–80.6% |

## The answer

> *"i think i prefer it to be eager but we can experiment more"*

**Eager.** A missed decision costs more than an unwanted interruption.

**And it is provisional by the maintainer's own words**, so it is written here as
a working assumption rather than a settled preference. It can be revisited by
using the skill, which is the retirement rule's job.

## What this licenses, and what it does not

**It licenses ranking.** Until now `opener-only` and `no-opener` were both
"defensible skills" and nothing in the repository could prefer one. Now
`opener-only` is the better arm and `no-opener` is the worse one, on the same
numbers. That is the whole point of writing a loss function down.

**It does not license editing the shipped skill.** Two reasons, and the second
is the real one:

1. One run, one model tier, one proxy instrument.
2. **The direction of the L5 result is uncomfortable here.** `opener-only` is
   the arm that *keeps only the opener* — the friendly sentence with the
   illustrative quotes — and deletes the routing summary and the exclusion list.
   L5 measured those two clauses as buying −5.8pp and −3.7pp of false firing.
   Adopting eagerness by **deleting** the parts that do the work is not the same
   as adopting eagerness by design, and the first is what the current arm menu
   offers.

## So the next experiment is now well-posed, which it was not this morning

**L7: an eager description that keeps the boilerplate.** Take the shipped
description, keep the routing summary and the exclusions, and widen the opener
rather than removing anything. If FPR rises toward `opener-only`'s 11.3% while
recall rises toward 0.956, eagerness is available without giving up the clauses
that were measured to help. If it does not move, then eagerness lives in the
opener specifically and the trade is real rather than an artefact of deletion.

That is a sharper question than "which of the four arms do we ship", and it
exists only because the loss function got written down.

## The one number that should be watched

`opener-only` interrupts **one ordinary turn in nine**. That is the cost being
accepted, stated plainly so that nobody rediscovers it as a surprise. If daily
use makes that intolerable, the retirement rule in
[`SCORECARD.md`](../SCORECARD.md) is the mechanism, and this entry is the thing
it would contradict.
