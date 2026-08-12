# 2026-08-11 — What the probe scores were actually measuring

No model calls. Every response was already on disk; only the scorer changed.

## The metric as it was

```python
admissible = not missing_required and not took_prohibited and pivot_ok
```

Three conjuncts. The first two are properties of the model's answer. The third
is a property of my agreement with it: `pivot_ok` required the response to name
the determinative unknown *I* had written into the key, or the literal string
`NONE` where I had decided nothing was missing.

Five of the six scored failures were that conjunct alone. On probe-09 the model
wrote, in the `MISSING` block:

> evidence of a compliant written cure notice … served before the protected
> concern was raised

That is the exact fact `s.46(3)` turns on. It is a better pivot than the one I
wrote. It was scored zero.

## The corrected metric

```python
admissible = not missing_required and not took_prohibited and not unjustified_hit
```

Three conjuncts, all objective. The third is promoted from diagnostic: an action
licensed only by a non-governing condition is a real failure, and a metric that
claims to measure whether an answer was *licensed* cannot ignore it.

Pivot recall stays as a secondary. `named_an_unknown` joins it — "named a
determinative unknown", with no requirement that it match mine.

## Before and after

Only `casefile-probe.jsonl` is machine-scoreable. The no-menu and bare runs
produce free-text recommendations with no action identifiers, so every required
action parses as missing and admissibility is 0.000 by construction. Those runs
were always read by hand, and `--rescore` now refuses to print a scoreboard for
them.

| Run | Was | Now | Δ |
|---|---|---|---|
| `casefile-probe` (menu) | 0.500 | **0.917** | +0.417 |
| `casefile-probe-nomenu` | — | — | hand-read, no ids |
| `casefile-probe-bare` | — | — | hand-read, no ids |

Five cases changed verdict, all in the same direction:

| Case | Change | `pivot_ok` |
|---|---|---|
| probe-05-late-accounts-cliff | FAIL → ok | False |
| probe-08-restatement-covenant | FAIL → ok | False |
| probe-09-cure-notice | FAIL → ok | False |
| probe-10-voluntary-disclosure | FAIL → ok | False |
| probe-11-writeoff-cross-default | FAIL → ok | False |

Every one of them was failing on the pivot and nothing else.

**One genuine failure survives.** probe-06 missed required action A2. That is the
single real defect in twelve responses, and it is the only case where the model
did something the case makes mandatory and did not do it.

## The uncomfortable part

`ADMISSIBILITY_CEILING` is 0.85. The corrected number is **0.917**.

**Gate 1 now fails.** The 2k casefile venue has no headroom. It was reported as
passing at 0.500, and that 0.500 was mostly me.

This does not weaken the probe's negative result. It strengthens it, and it
makes it worse than reported:

- The headline finding was *27 trap opportunities, zero taken*. That was already
  true and is untouched — `trap_hit` never involved the pivot.
- What was wrong is the surrounding claim that there was *some* headroom to work
  with. There is essentially none. Both gates now fail: no headroom **and** no
  trap bite.
- So the venue was worse than the write-up said, and the write-up was hedged
  because a metric was manufacturing failures that made it look better than it
  was. The error flattered the venue. That is the fifth prediction in three days
  wrong in the direction that flattered the experiment, and the pattern is now
  too consistent to keep calling a coincidence.

`report()` now scores from the stored responses rather than reading back the
`admissible` field the run recorded. A stored verdict is a verdict under
whichever rules were in force that day, and leaving it in place would have left
the repository reporting 0.500 and 0.917 for the same run depending on which
command was typed.

## Does the graded outcome have enough variance to be a primary?

**At 2k, no.** This is the more useful finding of the two.

Mean graded admissibility is **0.981**, and the distribution is:

| Graded | Cases |
|---|---|
| 1.000 | 9 |
| 0.952 | 1 (probe-09, condition recall 0.86) |
| 0.933 | 1 (probe-04, condition recall 0.80) |
| 0.889 | 1 (probe-06, missed A2) |

Nine of twelve are exactly 1.000. Four distinct values across twelve cases, and
three of them are one case each. The graded outcome was added because binary
admissibility carries about one bit once the pivot comes out — and at this
length the graded version carries barely more. Both terms that could vary
(`required_taken`, `forbidden_avoided`) are at ceiling in eleven of twelve
cases; all the movement is condition recall, which is a *classification* score on
a list the prompt hands over.

Two consequences, both of which belong in the Milestone C prediction before any
long run happens:

1. **A numeric prediction for graded admissibility at 100k has to be written down
   in advance**, and the honest prior is that it is near ceiling there too. The
   gate band [0.25, 0.70] is on binary admissibility; if graded also has to clear
   a variance floor, that floor should be stated now rather than discovered.
2. **If both metrics are near-constant at 100k, the venue has no dependent
   variable and no amount of corpus fixes that.** That is an instrument
   falsifier, it fires before authoring, and it is cheaper to find at $8 than
   after 750 documents.

The counter-consideration is that 0.981 at 2k is exactly what a dose-response
design wants at its low anchor: the whole hypothesis is that the number falls
with length. A ceiling at 2k is only fatal if it is still a ceiling at 100k.
That is the measurement, and it has not been made.

## What this cost

Nothing. Twelve responses, already paid for, re-read under different rules.

The reason it was free is that every run writes the model's full response next to
its score. That was not obviously worth the disk when it was written. It is the
only reason a scorer defect found three weeks later did not cost a re-run.
