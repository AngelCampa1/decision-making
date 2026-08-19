# 2026-08-19 — N9 is void, and the way it broke is the finding

The in-situ arm ran all 516 calls and the runner refused the result: **parse
rate below its 90% floor.** So N9 does not answer the question it registered,
and none of its three predictions are scored. That is the disposition, and
everything below is exploratory.

The prediction entry
([`2026-08-19-prediction-n9-does-position-move-firing.md`](2026-08-19-prediction-n9-does-position-move-firing.md))
named this outcome in advance: *"a parse rate below 0.95 voids the run rather
than producing a finding, and the first thing to check on a large drop is the
unparseable count, not the interpretation."* That is the order it was checked
in. It is the first registered void condition in this repository to actually
fire — **not the only one that exists**: `RESEARCH_PROGRAMME.md`'s Track A
falsifier list carries *"parse rates diverge by arm. The run is void"*, which
has never had the chance to trigger because A2–A5 have not run.

## Three numbers, and they are not the same number

This is the part the first draft of this entry got wrong, and an adversarial
review caught it.

| | over | value |
|---|---|---|
| what the runner's gate computes (`run_triggers.py:918`) | **repeat 0 only**, 258 items | **0.8566** |
| repeat 1 alone | 258 items | 0.8721 |
| the aggregate over every call made | 516 calls | 0.8643 |

The first draft quoted 0.8643 and cited line 918 for it. **Line 918 does not
compute that.** `row = done.get((case.id, 0))` reads repeat 0 and nothing else,
so the gate is blind to repeat 1 entirely. The two round to the same displayed
`86%`, which is how it went unnoticed.

**So the 0.95-vs-0.90 discrepancy is not the interesting defect and calling it
benign was the wrong call.** The real one is underneath: a run where repeat 0
cleared 0.90 while repeat 1 dragged the true rate below it would **exit zero and
be published**, and nothing would say so. Here every reading is below every
floor, so the disposition is right — by luck, not by the gate. That is a
standing instrument gap and it is not fixed by this entry.

## What the 70 unparseable responses are

Not malformed JSON. **Not one of the 70 contains a `"fire"` key** — and,
checked harder on review, not one contains the substring "fire" in any casing,
or any parseable embedded JSON of any shape. They are prose: the model
answering as Claude Code rather than emitting the contract.

**How they divide up is much less certain than the first draft implied.** The
counts below come from regexes written *after* reading the data, where one
category is the residual bucket everything unmatched falls into. An independent
reviewer hand-read all 70 and formally classified a random 30, blind to these
labels:

| | regex, all 70 | independent hand read, n=30 |
|---|---|---|
| answers the question in prose | 54.3% | 40.0% |
| scope refusal, on host identity | 27.1% | 26.7% |
| declines the tool, answers anyway | 14.3% | 20.0% |
| clarifying question | 4.3% | 13.3% |

Only the scope-refusal row agrees. The residual bucket is inflated by roughly
fourteen points and the clarifying-question row by nine, and the boundary cases
are real rather than sloppy — a response declining the decision framing without
using the word "tool", a partial answer ending in a question, an
information-refusal that is not an answer. **No fine-grained count from this
table should be quoted.** Two claims survive an independent read and those are
the only two this entry stands behind: no `fire` key anywhere in the 70, and
the identity-refusal language is absent from `technical` and `career`.

## Two clusters, not a gradient

The first draft called this a gradient falling monotonically from `technical`
to `health`. **Sorting five domains by the outcome being described and then
calling the ordering a finding is circular**, and testing it does not support
five distinguishable steps:

| adjacent pair | Fisher exact |
|---|---|
| technical vs money | p = 0.287 |
| money vs career | p = 0.654 |
| career vs relationships | p = 0.135 |
| relationships vs health | p = 0.607 |

Not one adjacent step is distinguishable. The split that is:

| | parse rate | |
|---|---|---|
| `technical`, `money`, `career` | **0.9135** (285/312) | |
| `relationships`, `health` | **0.7892** (161/204) | Fisher **p = 0.00011** |

A χ² across all five domains is significant (χ² = 18.86, df = 4, p = 0.00084)
and is driven entirely by that one break. **It is a step function with a single
edge, not a slope** — which is the sharper claim, because a step is what a
categorical trigger looks like and a slope is what a difficulty confound looks
like.

Consistent with that, the identity-refusal language appears in `relationships`,
`health` and once in `money`, and **never in `technical` or `career`**.

## The confound hunt, which failed to find one

Turn length does not explain it: median 376 chars unparseable against 405.5
parseable, Mann-Whitney p = 0.155. Band does not — `m` is worst at 0.819 and
`l` best at 0.921, with no monotone relationship. Stakes does not — `health` is
majority low-stakes and has the worst rate. **A simpler variable was looked for
and not found**, which is evidence for the topic-sensitivity account rather
than proof of it.

`--system-prompt` replaces the host identity; `--append-system-prompt` leaves it
in place. The description is byte-identical across the two arms.

## Why this is not scored, and must not be

Recovering decisions by re-reading prose would be **post-hoc scoring of a voided
run against a rule invented after seeing it**, which is the shape of defect this
repository has recorded four times. The run is void. **Prediction 2 said the
loss would be in recall rather than precision**; the identity-refused positives
are consistent with that and are *not* evidence for it, because the arm that
would have shown it never produced scoreable output.

## The instrument is not what failed

446 of 516 calls parsed and scored normally, so a response existed that would
have scored above zero for this arm — the standing check before believing any
outcome. Item-level coverage was 0.957: 11 of 258 items lost every repeat.

**One claim from the first draft is withdrawn as unverifiable.** "0 isolation
failures" was carried over from the run console; there is no isolation field in
the checkpoint and no log was kept beside it, so nothing on disk supports it.

## What N9 needs to become answerable

The venue question is still open. Answering it needs an in-situ arm whose output
contract survives the host prompt — a change to how the arm asks, not to what it
asks, and therefore a new pre-registration rather than a re-score of this one.
**No such arm has been built or run**, and until one is, this repository has no
measurement of how the shipped description behaves in the venue anybody uses.

**And the gate needs fixing before that run**, or it will grade the next one on
half its data.
