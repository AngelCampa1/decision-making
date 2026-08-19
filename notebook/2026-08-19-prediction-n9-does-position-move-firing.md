# 2026-08-19 — prediction: N9, does prompt position move firing at all?

Registered **before the first call** and committed before the launch.

## What runs

One arm — the `full` description sent with `--append-system-prompt` instead of
`--system-prompt` — × 258 items × 2 repeats = **516 calls**, `haiku`, key **v4**.
The reference is [N6's `full` arm](../results/decision-making/2026-08-18-e632659-n6-confirmatory/README.md):
accuracy 0.9360, precision 0.8601, recall 0.9651, FPR 0.0785.

**Conversation length is held at one turn on both sides.** Only position moves.
The programme's N9 row says why: how many prior turns, discussing what, is an
unmeasured parameter and standing rule 1 forbids inventing one.

## What will be computed, from which records, over which denominator

- `trigger_arms.summarise` over 516 parsed records — accuracy, precision,
  recall, FPR — against N6's `full` arm on the identical 258 cases.
- `trigger_arms.compare` — paired Wilcoxon on per-item correctness, the
  estimator M4, M5, M6 and L5 each registered — for discordance and p.
- Per-band FPR, because every arm measured so far has put its false firing in
  the long bands.
- **`venue_comparable` will refuse the naive `compare()` call**, by design: it
  raises on an in-situ arm against an unstamped one. The comparison is made by
  passing both arms explicitly, which is the point of the guard — it forces the
  venue difference to be stated rather than absorbed.

## Predictions

1. **The in-situ arm's accuracy will be lower than 0.9360.** The shipped
   description is written to be the whole instruction; appended to the CLI's own
   system prompt it competes with everything already there, which is the
   condition Track G's `in_situ` arm exists to test and the reason `arms.py`
   orders it last.
2. **The loss will be in recall, not precision.** A description that has to
   compete for attention should miss turns it would otherwise catch, rather than
   start firing on turns it would otherwise refuse.
3. **The two arms will be distinguishable** — `compare()` p < 0.05 over 258
   paired items. N7 has just shown that the top three *description* arms are not
   distinguishable at this n (p = 0.86, p = 0.35), so this prediction says the
   venue matters more than the wording does.

## Where I expect to be wrong

**Prediction 3 is the one I would bet against myself on.** If descriptions that
differ by whole deleted clauses are indistinguishable at n = 258, a change of
prompt *position* that alters no word of the description may well be too. If
N9 comes back at p = 0.5 with a two-point accuracy difference, the honest
reading is not "position does not matter" — it is that this instrument cannot
resolve differences of this size, and that the six-arm table published
yesterday was measuring less than it appeared to.

**And prediction 1 has a failure mode that would look like success.** If the
in-situ arm scores *much* lower — say below the 0.7054 stump — that is more
likely a parsing or contract failure than a venue effect: appending to the
CLI's system prompt leaves its own output conventions in play, and the arm
must still return the single line the parser expects. **A parse rate below 0.95
voids the run** rather than producing a finding, and the first thing to check on
a large drop is the unparseable count, not the interpretation.
