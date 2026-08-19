# H1 does not need twenty, and τ drifts with n

**2026-08-19.** Track H's H1 row costs 498 calls off **20 triplets**. Two
authoring passes have produced two usable ones, so twenty triplets is on the
order of a hundred authored — the authoring bill that already closed Track G,
arriving at Track H by another route.

Nobody had asked whether twenty was the right number. This is that question,
answered by simulation rather than by authoring ninety more.
`scripts/size_track_h_phase0.py`, 174 cells × 2,000 replicates × 10,000
bootstrap resamples. **No model calls.**

## The answer

**On the registered rule, ten to fifteen.** `Phase0Result.kill` is a *point*
rule — `j >= 0.70` — and against it:

| | n=5 | n=10 | n=15 | n=20 |
|---|---|---|---|---|
| P(false kill) at true J = 0.50 | 0.23 | 0.10 | 0.04 | 0.02 |
| P(kill) at true J = 0.85 | 0.94 | 0.97 | 0.99 | 0.99 |

Going from ten to twenty buys about **eight points of false-kill protection for
fifty more authored triplets** — roughly 350,000 characters at the observed
one-in-five yield. The marginal triplets past ten to fifteen are not buying the
primary anything.

**Choose n as a multiple of five, and this is not aesthetics.** Bootstrap
replicate means live on the lattice `k/(2n)`, and 0.70 is an exact atom at
n = 5, 10, 15, 20 but *not* at 8 or 12. At n = 8 the smallest attainable
`ci_low >= 0.70` is 0.75, and 25.7% of replicates land in [0.65, 0.70) — mass
that would have closed the venue had 0.70 been representable. **P(indeterminate)
is not monotone in n**: going from five triplets to eight makes it 26 points
*worse*. Found in the grid, then confirmed by direct enumeration, and found
independently by the adversarial reviewer.

## The defect that no n fixes, and the reason this entry exists

**τ is defined as a maximum over the n base pairs, so the estimand is a function
of the sample size.** A bigger corpus produces a larger maximum base-versus-base
excursion, a higher threshold, and therefore a *different true J*. On the
reviewer's reconstruction, true J runs **0.843 → 0.915 → 0.956 → 0.977** as n
goes 5 → 10 → 20 → 40 at one parameterisation.

So no two rows of any power table above are the same venue, and the direction is
*toward the kill*: adding triplets mechanically pushes H1 toward closing Track H.

This also corrects the registered prediction. It says τ biases conservatively,
against the kill and toward the venue looking alive. That is half the story —
**the bias changes size with n**, which the prediction does not say and which
nobody had noticed.

A τ defined as a quantile, or as a pooled noise estimate, rather than a max over
n would remove the drift. **That should be settled before H1 authors anything
further**, because it is not a power problem and choosing a larger corpus makes
it worse rather than better.

Second-order but the same shape: τ is a single draw shared by every triplet, so
the clusters are not independent. Measured across-cluster correlation 0.07–0.10,
which `cluster_bootstrap_diff` resamples i.i.d. and cannot see. Realised SD runs
×1.23 to ×2.31 the closed form and **coverage does not improve with n** —
0.61–0.85 against a nominal 0.95.

## What the two decision rules do to the recommendation

The first version of this analysis scored a confidence-**interval** rule. H1
registered a **point** rule. They give opposite answers:

- **Point rule:** ten triplets is defensible, twenty is generous.
- **Interval rule:** *no* n between 5 and 20 works. Only J ≤ 0.30 and J ≥ 0.85
  are resolvable at all; the band 0.40–0.80 is unreachable at every n and every
  heterogeneity level run.

A reader would have taken "Track H is unaffordable" from a table whose rule was
not the one registered. The substitution was load-bearing, not cosmetic, and it
was caught by the reviewer rather than by the author.

The interval finding still matters on its own terms: if H1 wants to *state* that
the venue has headroom rather than merely observe a point estimate under the
kill, twenty triplets does not deliver that and neither would forty.

## Heterogeneity: the parameter with no data, bounded rather than guessed

**Two repeats caps the damage.** With `REPEATS = 2` the design effect is exactly
`1 + icc`, bounded by 2, so heterogeneity can widen the interval by at most √2
whatever its true value. Measured 1.220 against a predicted 1.225 at ICC = 0.50.
That is the answer to "you have no data for this": it cannot rescue or ruin the
design.

What it does move is the smallest usable n at J = 0.30: **12 → 12 → 15 → 20 → 20**
across ICC 0, 0.05, 0.20, 0.50, 0.83. The 0.83 run happened because the reviewer
pointed out that Track I's measured repeat ICC is 0.83–0.85 and that with two
repeats this *is* that quantity — the sweep had stopped at 0.50 while the
docstring cited 0.83 as directly comparable.

## Standing rule 2, and one check that was passing for the wrong reason

Nine checks pass, including the one that outranks every number: **discrimination
between J = 0.30 and J = 0.85 on 30 of 30 cells.** It is wired as a gate, not a
report — `main` exits non-zero and prints no recommendation if it fails, and a
test feeds it a fabricated grid where the two coincide to confirm it catches
that.

The anchor at n = 50 gives false positives 0.0290 against nominal 0.025 and
coverage 0.9530 against 0.95. That anchor is what separates "simulator broken"
from "small-sample behaviour" — and the small-sample behaviour is real: **at
n = 5 the bootstrap is anti-conservative at nearly 3× nominal α**, calibrating
only from about n = 12.

Two checks were passing for the wrong reason and are fixed. The J = 1 ceiling
check was satisfied *by* degenerate zero-width intervals rather than by
detection — at n = 5, J = 0.85, 38% of `p_closes` was zero-width — and now
asserts the mean estimate too. The discrimination check keyed on `(n, icc)`
without `shape`, silently grading 24 pairs where 30 exist.

## What is not settled

- **Whether the real elicited-quantity pipeline behaves like the reviewer's
  log-normal reconstruction.** Neither of us has data, because **no quantity has
  ever been elicited in this harness.** Every number above about τ's effect rests
  on a reconstruction, not a measurement.
- **`INDETERMINATE_CEILING = 0.20`** is now declared as a choice rather than a
  bare default, and it moves the answer — J = 0.30 gives n = 8, 12 or 15 at
  ceilings 0.25, 0.20, 0.15. What would measure it is a cost ratio between
  authoring a triplet and spending a run that resolves nothing, which nobody here
  has written down.
- **The recommendation is conditional on the τ fix.** Ten to fifteen is the
  answer to the question as asked; it is not a licence to author ten triplets
  while the estimand still moves with the corpus size.

## For the maintainer

The useful half is that H1's twenty is not load-bearing and the venue is
cheaper than its row claims. The important half is that the τ rule has a defect
that a bigger corpus makes worse, and it was found before H1 ran rather than
after — the sixth time this repository has caught an instrument defect in source
rather than in a result.
