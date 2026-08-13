# Prediction: eager without deleting the parts that work

**2026-08-13**, written and committed **before the run starts**. Track L7.

## Why this arm exists

The maintainer chose eagerness and said what the skill should key on: **stakes,
real consequences, complexity, nuance.**

The only eager arm on record is `opener-only`, which reaches recall 0.956 by
**deleting** the routing summary and the exclusion list — the two clauses
[L5](2026-08-12-l5-the-boilerplate-does-the-work.md) measured at −5.8pp and
−3.7pp of false firing. That is eagerness by subtraction, and it costs 11.3% of
ordinary turns.

L7 asks whether eagerness is reachable **by widening the opener while keeping
both clauses verbatim.**

## Two arms, because I could not answer a design question and should not have asked

I asked the maintainer whether the new opener should *name* the criteria or
*show* them by example. That was a bad question to put to a person: it is
empirical, and the instrument answers it for 146 calls an arm. So both run.

| arm | opener | length |
|---|---|---|
| `stakes-named` | *"…and the choice has stakes — it is costly to undo, several things pull against each other, or it lands on someone else."* | 263 ch |
| `stakes-shown` | *"…'should I take the offer', 'do I raise this now or wait', 'is it worth the risk', 'what does this commit us to'…"* | 248 ch |

Both keep the routing summary and the exclusions **verbatim**, so the two arms
differ from each other and from `full` in the opener alone. Tests enforce that,
the length match (within 10%, observed 6%), and that `named` states a criterion
while `shown` does not.

## The cost this arm is honest about

**These openers are authored.** Every previous arm in Tracks L and M was derived
— L5 by deletion, M4/M5/M6 by mechanical partition — precisely so that no result
could be "the prose I happened to write". L7 gives that up, because no deletion
of the shipped description produces a stakes criterion.

What replaces derivation is constraint: same middle, same exclusions, matched
length, one opener each, both written before any of them ran. **It is weaker and
the write-up must say so.**

## The mechanism being tested

The seven ordinary turns `opener-only` interrupts are, with one exception,
**low-stakes**: tabs versus spaces, a variable name, list versus set, a plot
twist. If the opener keys on stakes rather than on the *shape* of a "should I"
question, those should stay quiet while the genuine decisions still fire.

**If that is right, L7 breaks the frontier rather than moving along it** — the
first result in this repository that would.

## Predictions

73 cases × 2 repeats × 2 arms = **292 calls**. Scored against **trigger set
version 2**; the `full` control must be re-scored under v2 before any
comparison, and `label_versions_comparable` refuses otherwise.

Reference points, both v2, both re-scored not re-run:

| | FPR | recall |
|---|---|---|
| `full` (shipped) | 0.018 | 0.929 |
| `opener-only` | 0.129 | 0.953 |

| # | Prediction | Band | Estimator |
|---|---|---|---|
| 1 | Parseable verdicts | ≥ 98% | share of records with non-null `fired`, both arms |
| 2 | **Both arms beat `opener-only` on FPR** | < 0.129 each | false fires ÷ negatives, v2 labels |
| 3 | **At least one arm reaches recall ≥ 0.94** | ≥ 0.94 | true positives ÷ positives, v2 labels |
| 4 | **At least one arm lands outside the frontier** | FPR ≤ 0.06 **and** recall ≥ 0.94 | both of the above, same arm |
| 5 | `stakes-named` and `stakes-shown` differ on FPR | either direction, descriptive | no p-value; 2 arms × 55 negatives cannot reject |
| 6 | Neither arm fires on the two lowest-stakes negatives | `x-n01` tabs, `x-n02` variable name, rate ≤ 0.5 | per-item fire rate |

**4 is the experiment.** Everything this repository has measured moves along the
frontier and cancels. A point at FPR ≤ 0.06 with recall ≥ 0.94 sits above the
line through `full` and `opener-only` and would be the first arm that is better
rather than differently placed.

**6 is the mechanism check**, and it is the one I most expect to fail. *"Should I
use tabs or spaces"* has the grammar of a decision and none of the stakes. If a
stakes-keyed opener still fires on it, the model is reading the sentence shape
and not the content, and predictions 2 through 4 will have been luck if they hit.

## Where I expect to be wrong

**5 is nearly free and I am registering it as such.** Two authored sentences
will differ on something. The band has no direction and no threshold, so it
cannot fail; it is there to make me write the number down rather than notice it
afterwards.

**And band 3 may be unreachable for a reason that is not about the opener.**
`x-n03`, `x-n20`, `x-n21`, `x-n22` are the maintainer-written positives, and
`x-n22` has never fired in any arm on any version. Recall ≥ 0.94 needs 16 of 17.

## Cost

292 isolated calls across two arms, own checkpoints.
