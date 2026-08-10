# Scorecard

**Generated artifact — do not edit by hand.** `de report` rebuilds this from
`results/**/summary.json`, and `de check` fails the build if the committed copy
differs from what the results imply.

## Skills

| Skill | Verdict | Primary metric | Effect | 95% CI | p | q (BH) | N | Model | Run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _none yet_ | | | | | | | | | |

**proven: 0 / shipped: 0**

No skill has been evaluated yet. The harness is being built first, deliberately —
see [`docs/PROTOCOL.md`](docs/PROTOCOL.md) for the standing methodology and the
verdict vocabulary, and [`notebook/`](notebook/) for the running research log.

## Verdict vocabulary

| Verdict | Meaning |
| --- | --- |
| `SHIP` | Beat control at q < 0.10 with every guard passing, placebo-controlled, and replicated on a freshly generated holdout |
| `PROVISIONAL` | Same, but not yet replicated |
| `NULL` | Confidence interval includes zero, or the effect is smaller than the pre-registered minimum detectable effect. Back to the workbench; ships as `experimental` |
| `HARMFUL` | Significantly worse, or a guard was violated. Off by default pending redesign |
| `UNTESTED` | No confirmation run. Cannot carry a proven badge |

A verdict governs the *public claim*, not whether a skill is usable. `NULL` means
we have not shown it works, which is not the same as showing it does not.
