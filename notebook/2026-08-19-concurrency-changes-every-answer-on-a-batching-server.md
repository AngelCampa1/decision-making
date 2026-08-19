# 2026-08-19 — Concurrency changed every answer, and the prompts were byte-identical

Outcome of the falsifier registered in
[`2026-08-19-prediction-concurrency-must-not-change-results.md`](2026-08-19-prediction-concurrency-must-not-change-results.md),
which was committed before `run_arm` had a concurrent path at all.

120 calls, 40 items, three arms, `ollama/qwen3:4b` at `temperature=0` on the
`dev` arena. Free, which is the whole reason that arena was built first.

## The registered outcome

| | |
|---|---|
| `agree_S2`, the serial-against-serial floor | **0.7750** (31 of 40) |
| `agree_C`, concurrent against serial | **0.0000** (0 of 40) |
| registered band, `agree_C >= agree_S2 - 0.10` | `>= 0.6750` |
| verdict | **outside the band** |
| McNemar exact, two-sided, 40 pairs | 31 discordant, 31 of 31 favouring the serial repeat, p < 0.0001 |

The kill condition did not fire. It was declared as `agree_S2 < 0.50`, and the
floor came in at 0.775, so exact text match was a live instrument here and the
primary outcome stands as registered.

The registered consequence, quoted from the prediction: *"If `agree_C` falls
outside the band while `agree_S2` is high, concurrency changes results, and the
concurrent path may not be used for any published run until that is understood.
The serial path stays."* That is what happened, so that is what applies.

## The request did not change. The answer did.

`input_tokens` matched exactly across all three arms on every item that ran, so
the concurrent path sent the same bytes as the serial one. That was the
pre-declared secondary, and it passes. The scored `parsed` answer agreed with
serial on 0.974 of items for the serial repeat and 0.846 for the concurrent arm.

So the effect is not a bug in what the runner assembles. It is the server. A
backend that batches concurrent requests multiplies different matrix shapes,
which selects different reduction orders, which flips a token; and these are
reasoning outputs of 1,500 to 4,800 tokens, which is a long way for one flipped
token to propagate before it reaches `content`.

**Six of 39 items landed on a different decision**, not merely different prose.
That is the number that matters, because `parsed` is what enters a published
result and prose is not.

## Where the prediction was wrong

It said, under *where I expect to be wrong*: "`agree_S2` itself... `temperature=0`
is not a determinism guarantee... So `agree_S2` may well be far below 1.0, and
could plausibly trip the kill."

The mechanism was right and the arm was wrong. Batch-size-dependent reduction
order is exactly what happened, but it did not touch the serial repeat, which
holds batch size fixed at 1 and reproduced 31 of 40. It landed entirely on the
concurrent arm, and it took it to zero rather than to something degraded. A
prediction that named the right physics and the wrong arm is still a wrong
prediction, and it is recorded rather than edited.

## Two defects found while it ran

**An inert health check, the third here.** The script counted infrastructure
failures with `parse_status == "infrastructure_error"`. `ParseStatus` is
`Literal["parsed", "no_answer_line", "unlisted_option", "ambiguous"]`, so that
count could never have risen above zero. It surfaced because a CUDA OOM on
`m01p` in S1 wrote a record with `duration_ms=0` and the server's 500 body in
the `response` field, and the check called it healthy. The field that carries it
is `zero_cause`. Same standing rule broken as the previous two: check that some
possible response would have scored non-zero before believing an outcome.

**A false premise in the registered denominator.** The prediction justified
"denominator 40, all items" with "every call returns text or raises, and a raise
is a failed run rather than a scored zero". That is not this harness. `_run_one`
catches `CliError` and writes an infrastructure zero with the exception text as
the response, which then gets string-compared as though it were an answer. The
registered number is reported as registered; the clean-set rate over the 39
items with no infrastructure zero in any arm is reported beside it and labelled
unregistered. It moves nothing: 0.7949 against 0.0000.

Sixth pre-registration defect on record, and the second visible before scoring
rather than after.

## What this licenses

`runner.CONCURRENCY_UNSAFE` now refuses `concurrency > 1` for the `ollama`
prefix, with a `measuring_concurrency` escape that only this falsifier uses,
because the run that would clear the entry is itself a concurrent run on
`ollama`. The register may only shrink and it shrinks by measurement.

**It is a statement about a venue, not about concurrency.** The Claude CLI
backend, which produced every published number in this repository, has not been
measured, and unmeasured is a different thing from safe. Nothing published is
affected: `concurrency` defaults to 1 and no run has used anything else.

The speedup was 2.00x, 678.4 s against 1354.2 s, at `concurrency=8` against a
server started with `OLLAMA_NUM_PARALLEL=4`. Worth stating only because it is
the thing that would have been tempting.

## Replication

Running as `DE_CONC_PREFIX=rep1`, independently rather than resuming, because a
resumed pass returns the same records by construction. No finding here is
believed until the run reproduces. Its wall-clock will be measured on a machine
also running the gate, so its timing is not comparable with the numbers above;
its agreement rates are.
