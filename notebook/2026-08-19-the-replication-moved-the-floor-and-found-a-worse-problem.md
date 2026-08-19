# 2026-08-19 — The replication moved the floor, and found something worse than the thing it was checking

Replication of
[`2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md`](2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md),
run independently rather than resumed, 120 more calls on the same 40 items.

It did not confirm that entry's primary. It found a larger problem underneath it.

## What the second run says

| | run 1 | run 2 |
|---|---|---|
| `agree_S2`, serial against serial | 0.7750 | **0.3250** |
| `agree_C`, concurrent against serial | 0.0000 | 0.0000 |
| kill (`agree_S2 < 0.50`) | did not fire | **fired** |
| secondary, `input_tokens` identical | on the clean set | yes, all 40 |

The kill fired, and it was declared in advance precisely for this: *"the primary
outcome is abandoned before `agree_C` is looked at."* So run 2 does not
independently confirm run 1's band violation. It declines to answer, and the
pre-declared secondary is what it returns: the prompts were byte-identical.

The serial floor moving from 0.775 to 0.325 between two measurements of the same
quantity is the headline. A floor that varies by 45 points is not a floor.

## The finding neither run was looking for

All six arms compared against each other, exact text and scored answer, on the
40 items common to every arm:

| pair | text | answer |
|---|---|---|
| run 1, serial vs serial, same invocation | 0.7750 | 0.9750 |
| run 2, serial vs serial, same invocation | 0.3250 | 0.9000 |
| run 1, serial vs concurrent, same invocation | 0.0000 | 0.8500 |
| run 2, serial vs concurrent, same invocation | 0.0000 | 0.8250 |
| **run 1 vs run 2, serial vs serial, across invocations** | **0.0000** | 0.8750 |
| run 1 vs run 2, concurrent vs concurrent, across invocations | 0.0000 | 0.9000 |

**Two serial runs of the same 40 prompts, an hour apart, agree on the exact text
of zero of them.** Spot-checked on `m03p`: identical 170-token prompt, entirely
different prose, same parsed answer. Nothing about concurrency is involved.

So exact text identity is meaningful on this backend only *within a single
process invocation against a server that has not moved*. Outside that, it is
zero regardless of arm, which means the registered primary was measuring the
instrument as much as it was measuring the arms. That is the third estimator
here to have that shape, and the first where the estimator was the
pre-registered one rather than a bug in the reporting.

## What survives, and what does not

**Survives.** Within a single invocation, concurrency destroys text agreement
where serial does not: 0 of 40 twice, against 31 of 40 and 13 of 40. Under a
null where batching does not matter, the concurrent arm should look like the
serial repeat; getting 0 of 40 twice when the comparable serial rate is 0.325 is
about 1.6e-7 on the worse of the two runs. The direction is robust even though
the floor is not.

**Does not survive.** "Concurrency changes results and serial is fine." Serial is
not fine across invocations. The previous entry's framing, and the commit
message that went with it, put the whole effect on concurrency because
cross-invocation serial had not been compared. It had been sitting in the data
and I did not look until the replication forced it.

**Never established, either way.** On the scored answer, which is the quantity
that reaches a published number, the concurrent arms land at 0.850 and 0.825
against a cross-invocation serial baseline of 0.875. At n=40 those are not
separable. So there is no evidence here that concurrency specifically moves the
*decision*, only that it moves the prose.

## A hypothesis, labelled as one

Ollama's default `keep_alive` is 5 minutes and roughly 8 minutes of idle sat
between the two runs, so the model was very likely unloaded and reloaded. A
reload changes the memory layout, which changes reduction order, which is the
same mechanism batching triggers. That would explain why within-invocation
serial reproduces and across-invocation serial does not.

It is untested. The experiment is cheap and free: 8 items, three serial passes,
one immediately after another and one after forcing an unload with
`keep_alive=0`. If the reload hypothesis holds, the first two agree and the
third does not. Nobody has run it.

## What changes

The `CONCURRENCY_UNSAFE` refusal stays. It is justified by the part that
replicated, and adding a second source of variation to a venue that is already
not reproducible across runs is not a thing to do on a default.

What has to change is every sentence that said serial was the safe path. It is
safe within an invocation and nowhere else, so no two runs on this backend may
be compared by text at all, and answer-level comparisons carry something like
ten points of run-to-run noise at n=40. Corrected in `runner.py` and
`docs/HARNESS_DISCLOSURE.md`; the previous notebook entry stands unedited, as
the record of what was believed before this ran.

Confirmation is why this repository has the rule. One run said something clean
and quotable and it was half wrong.
