# Prediction: what each part of a description actually buys

**2026-08-12**, written and committed **before the run starts**. Track L5.

## Why this one, and why now

L5 is a **primary** axis in Track L — skill availability dominates whether a
skill helps at all, +18 to 36pp ([arXiv:2605.31408](https://arxiv.org/abs/2605.31408)),
and availability is decided by the description.

It is also **the only skill-variant axis this repository can currently power.**
Firing has 73 items and 70 of 73 identical across five repeats. Routing has 14
and [cannot reject at any useful effect size](2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).
L1 draws its candidates from Track K6 and L6's first candidate is a router-table
edit — both of those land on routing. L5 lands on firing.

## The arms, and every one is a deletion

The shipped description has three parts. Each arm removes one or two, and
**nothing is rewritten** — a test asserts no variant contains a word the shipped
description does not.

| arm | what it is | length |
|---|---|---|
| `full` | as shipped. Control | 549 ch |
| `no-exclusions` | *"Do not use for…"* deleted | 385 ch |
| `opener-only` | the *when to use it* sentence alone | 206 ch |
| `no-opener` | routing summary + exclusions, opener deleted | 342 ch |

Three fresh descriptions would answer *which prose did I like*. Three deletions
answer *what does that part buy*, which is the question.

## Predictions

Base rate 18/73 = 0.247. Control is the existing five-repeat baseline:
**precision 0.942, recall 0.878, FPR 0.018.** 5 repeats per arm.

| # | Prediction | Band |
|---|---|---|
| 1 | Parseable verdicts, all arms | ≥ 98% |
| 2 | **`no-exclusions` false-positive rate rises** | **> 0.04** (control 0.018) |
| 3 | `no-exclusions` recall | ≥ 0.85 — deleting a *negative* clause should not cost positives |
| 4 | `opener-only` FPR | **> 0.06** — the largest of the three |
| 5 | `opener-only` recall | 0.85–1.00 |
| 6 | `no-opener` recall **falls** | < 0.80 (control 0.878) |
| 7 | Ordering on FPR | `opener-only` ≥ `no-exclusions` > `full` |

**2 is the one worth running for.** The exclusion list is the part of a
description authors spend the most time on and the part no published result
measures separately. **If FPR does not move when it is deleted, it is decoration
— on this instrument, at this model tier — and that is worth knowing before
anyone writes another one.**

**6 is the mirror test and it is what makes 2 interpretable.** If deleting the
opener costs recall while deleting the exclusions costs precision, the
description has two parts doing two jobs and both earn their place. If deleting
*either* changes nothing, the model is reading the skill's name and the user's
message and the description is theatre.

## Where I expect to be wrong

**3.** I have said deleting the exclusions should not cost recall, because the
clause only ever says *don't*. But a shorter description is a different object,
not the same object minus a sentence — the model may read a 385-character
description as a smaller claim on its attention and fire less overall. If recall
drops alongside FPR rising, the effect is length rather than content, which is
**L2's** question and would say this run measured the wrong thing.

And a caution I have now earned three times today: **every band I set today about
an arm that was not the control was wrong.** The reason each time was predicting
a measurement's behaviour rather than a model's. This design at least reads the
same object in every arm — same 73 labels, same JSON field, same one-turn call —
which is the check that was missing.

## Cost

Three new arms × 73 cases × 5 repeats = **1,095 isolated calls**, roughly 90
minutes of wall clock. The `full` control already exists at
`results/decision-making/2026-08-12-40b6ba5/` and is not re-run.

Each arm gets its own checkpoint. Varying the trigger text and varying the
response contract in one run measures neither, so `--description` refuses to
combine with `--arm four` or `--confidence`.
