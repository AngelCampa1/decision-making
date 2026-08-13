# One label moved and every arm improved

**2026-08-13.** Not a run. A consequence of the maintainer's label decisions,
recorded because it is the fourth defect of the same shape and the first one
caught before it produced a number.

## What happened

`x-n21` — *"The disk is at 99%. Do we need to act?"* — moved from the positives
to the negatives. `x-n22` stayed a positive. Both decisions are the
maintainer's.

Then every arm already on disk was re-scored against the new labels. **No call
was re-made.**

| arm | FPR v1 → v2 | recall v1 → v2 |
|---|---|---|
| bundle (shipped) | 0.018 → 0.018 | 0.878 → **0.929** |
| four entries | 0.000 → 0.004 | 0.800 → **0.835** |
| `opener-only` | 0.113 → 0.129 | 0.956 → 0.953 |
| `no-opener` | 0.000 → 0.004 | 0.867 → **0.906** |
| `no-exclusions` | 0.055 → 0.057 | 0.911 → **0.953** |

**The shipped skill gained five points of recall this afternoon and did nothing
to earn them.**

## Why this is the dangerous kind

It has every property the three earlier defects had:

- the checkpoint is unchanged and valid
- every instrument check passes
- the parse rate is 100%
- the number moves in the direction the author would like

And it has one they did not: **it is not a bug.** The new labels are better than
the old ones. `x-n21` really does have an obvious answer. The improvement is
real *as a label correction* and would be a fabrication *as a model result*, and
nothing in a JSONL file distinguishes those two readings.

## What now exists

- The trigger set carries `version: 2`, and the header says in bold that v1 and
  v2 numbers are not comparable.
- Every record the runner writes carries `set_version`.
- `trigger_arms.label_versions_comparable` refuses a comparison spanning
  revisions and names both. Records predating the field are read as version 1,
  which is what they are — a guard that never fires on the runs it was written
  for is decoration.

## The published results are all v1

`results/decision-making/*` is untouched and stays untouched. Those READMEs
describe runs made against version 1 and their numbers were correct for it.
**Nothing in them may be compared against a v2 run**, and the guard is what
enforces that rather than anyone's memory.

Re-scoring the old arms under v2 is free — the records carry case ids — and the
table above is that re-score. It is *not* published as a result, because
publishing it would put five improved numbers in `results/` with no run behind
them.

## The rule this adds

The working rules already say an estimator must be checked against the arm
structure and that a band must name its denominator. This adds the third:

**A change to the answer key is a change to every number ever computed from it.
Version the key, stamp the version into the records, and refuse across
versions.** The alternative is remembering, and four for four says nobody does.
