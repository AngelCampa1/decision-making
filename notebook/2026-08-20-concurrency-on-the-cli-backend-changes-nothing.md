# 2026-08-20 — Concurrency on the CLI backend changes nothing, and is 7.7× faster

Outcome of
[`2026-08-20-prediction-concurrency-on-the-cli-backend.md`](2026-08-20-prediction-concurrency-on-the-cli-backend.md),
which was committed before the run and before the script that ran it. Same shape
as [`2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md`](2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md),
which is the entry this one is a companion to, and the opposite result.

840 calls, `haiku`, seed 1, 280 generated items, three arms in the registered
order S1 → C(8) → S2. Records in the gitignored `results/track-0/`, summary in
`concurrency-cli-summary.json`.

## The primary is inside the band

| | |
| --- | --- |
| `agree_serial`, S1 vs S2, the floor | 0.9643 |
| `agree_C1`, S1 vs C | 0.9750 |
| `agree_C2`, S2 vs C | 0.9679 |
| registered band, `min(agree_C1, agree_C2) >= agree_serial - 0.05` | ≥ 0.9143 |
| kill, `agree_serial < 0.60` | did not fire |

**Concurrency agrees with serial at least as well as serial agrees with itself.**
Both concurrent comparisons sit *above* the serial floor rather than merely
inside the band, which is more than the prediction asked for. McNemar exact,
two-sided, on the 280 pairs: 9 discordant, 6 the concurrent arm only and 3 the
second serial arm only, p = 0.5078. Nothing to see, and the test says so rather
than the eye.

Every secondary landed where it was registered:

- **Text agreement is 0.0000 in all three pairs**, including serial against
  serial. Predicted "near zero" because this is a sampled backend and two
  identical prompts do not return identical strings. The estimator was chosen to
  be `parsed` for exactly this reason, and the number confirms the reason rather
  than embarrassing it.
- **`input_tokens` identical across all three arms.** The prompts were the same
  prompts.
- **Accuracy** S1 0.9821, C 0.9857, S2 0.9750. `|acc_C − acc_S1| = 0.0036`
  against a registered band of 0.05.
- **Zero infrastructure zeros in any arm.** No rate limit was hit, so the
  backpressure that landed the day before was never exercised here. That is not
  evidence it works.

Wall clock: S1 2959.9s, C 385.1s, S2 3069.0s. **7.69× on eight workers.**

## What this changes

`CONCURRENCY_UNSAFE` still names exactly one prefix, `ollama/`, and now that
silence is earned for the backend every published trigger number came from
rather than merely inherited. The register does not move, which is the outcome a
falsifier is allowed to have.

Two limits, both of them the prediction's and neither of them discovered
afterwards:

- **This measures `run_arm`, and `scripts/run_triggers.py` does not use it.**
  `collect()` is its own serial loop. Every trigger number on record was
  produced serially by a function this run did not touch, and making the
  published path concurrent is a separate change with its own evidence to
  gather.
- **One model, one tier, one day.** `haiku` at eight workers. Nothing here
  licenses `sonnet`, `opus`, or a higher worker count, and the free `dev` arena
  result from 2026-08-19 is the standing proof that a backend can fail this
  badly.

Cost is notional and not tracked per arm here; 840 calls on a Max subscription
against the rolling quota.
