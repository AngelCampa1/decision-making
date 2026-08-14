# 2026-08-14 — Q1 cannot reach its own prediction, at any corpus size we will build

N6 is the confirmatory run: 720 calls, three arms, the question this whole track
was built to ask. It is still held. This entry says what I checked, what held,
what I **refuted**, and the one thing that decides whether the run is worth
making.

The [N6 pre-registration](2026-08-13-n6-prediction-does-accuracy-fall-on-the-long-bands.md)
is not edited. It is a dated prediction and it stays as written.

---

## First, three criticisms I was carrying, and only one of them survives

I came to this holding three objections to N6. Two do not hold and I am recording
that before the one that does, because a criticism repeated without checking is
the failure mode this repository keeps finding in itself.

**"Three of four registered bands name functions that do not exist." — CLOSED.**
True when it was written, false now. All seven estimators the pre-registration
names are present in `trigger_arms` as of `e07c5ef`: `summarise`,
`summarise_by_band`, `routing_by_procedure`, `false_positive_rate_by_kind`,
`bootstrap_rate`, `bootstrap_rate_difference`, `label_versions_comparable`.

**"Q2's baseline is a cross-label-version comparison the guard refuses." —
REFUTED.** The pre-registration says so itself, in the entry, before the run:
that the v2 and v3 numbers are never subtracted, and that what is compared is
the *ordering within each corpus*, which is a weaker and legitimate claim. I was
criticising it for the thing it had already got right.

**"Q1's band assigns roughly the same probability to its null and its
prediction." — CONFIRMED**, and worse than the version I was carrying. Below.

## And the estimators refuse instead of returning zero, which is the point

Run against a version 2 checkpoint, three of them decline:

```
bootstrap_rate               no record carries 'triple', so there is nothing to
                             cluster on
summarise_by_band            no record carries a `band` ... neither can be read
                             per band
false_positive_rate_by_kind  no record carries a `kind` ... returning an empty
                             table would read as though the kinds agreed
```

That is the guard this repository has now written five times because it has
shipped five estimators that could not return a non-zero value. Here it fires on
the intended input.

## One parameter is equivalent rather than inert, and it matters for N6

`summarise(weight="item")` returned bit-identical numbers to `weight="record"` on
365 records, which is the exact shape of a dead parameter. It is not one. Under
**balanced** repeats the mean of per-case means equals the grand mean, so the two
coincide by arithmetic; forcing unequal repeat counts parts them
(0.9696 against 0.9699). Flipping three of five repeats on one case does **not**
part them, because that stays balanced.

**The consequence for N6 is concrete: it runs 2 repeats per item, balanced, so
the two weightings are guaranteed identical.** Reporting both is reporting one
number twice. Say which one is meant, once.

---

## Q1's band, checked rather than asserted

Registered: `full` arm, `accuracy(S+M) − accuracy(L+XL)` between **−0.05 and
+0.10**. Predicted: a small fall, **0 to 5 points**. The null is a fall of zero.

At 40 triples — S+M = 72 items, L+XL = 48, accuracy ≈ 0.95, design effect 1.63 —
the standard error of that difference is **0.0518**:

| what is true | Δ | P(result lands inside the registered band) |
|---|---|---|
| the null, no fall | +0.000 | **0.806** |
| the prediction, midpoint | +0.025 | **0.852** |
| the prediction, upper edge | +0.050 | 0.806 |
| the outcome that would matter | +0.100 | 0.498 |

**A result inside the band is evidence for neither hypothesis.** Both sit at four
chances in five of landing there. The band cannot be failed by the null and
cannot be passed distinctively by the prediction.

This is the seventh pre-registration defect on record and the second caught
**before** its run rather than after.

## The part that is not fixable by rewriting the band

The obvious repair is to narrow the band. It does not work, and the reason is
worth more than the defect.

Detectable effect at 80% power, two-sided, is 2.802 × SE. The **short side alone**
puts a floor under that which no amount of long-band authoring can cross:

| short side | floor, with an *infinite* long side |
|---|---|
| 72 items (40 triples, as registered) | 0.092 |
| 144 items (64 triples, today) | **0.065** |
| 300 items | 0.045 |

And with the long side at realistic sizes:

| | long 48 | long 100 | long 200 | long 400 |
|---|---|---|---|---|
| short 72 | 0.145 | 0.120 | 0.107 | 0.100 |
| **short 144 (today)** | 0.130 | **0.101** | 0.085 | 0.076 |
| short 300 | 0.121 | 0.090 | 0.071 | 0.060 |

**Q1 predicts an effect of 0.025 to 0.050. The best cell in that table is 0.060.**
Detecting a 5-point fall with both sides balanced needs about **82 triples per
side, ~163 triples in total** — against 64 today and 87 after the long-band
merge lands.

So the honest statement is: **N6's Q1 cannot reach its own prediction, and will
not be able to after the long-band merge either.**

## The merge landed while this was being written, and it is measured, not projected

`a38d2d8` took the corpus to 87 triples: **S+M = 144 items (48 triples), L+XL =
117 items (39 triples)**. The projection above said roughly 0.095. Measured:

```
SE of the difference        0.0346
detectable at 80% power     0.097     <- against a predicted 0.025-0.050
```

The prediction is still out of reach by a factor of two, and the registered band
gets *worse*, not better, as the corpus grows — a tighter SE puts **more** of both
hypotheses inside a fixed interval:

| what is true | P(inside band), 40 triples | P(inside band), 87 triples |
|---|---|---|
| the null | 0.806 | **0.924** |
| the prediction, midpoint | 0.852 | **0.970** |

**That is the clearest statement of the defect available.** A band that gets
harder to fail as you collect more data is not measuring the thing it names.

**But the merge bought the run something real, and it is not what was advertised.**
Power to reject "no fall" at the 0.10 decision boundary — the branch where v2's
results become uninterpretable rather than merely capped:

```
before the merge (48 long items)    0.577
after  the merge (117 long items)   0.823
```

The merge did not rescue Q1's prediction and nothing could. It moved the
*consequential* question from a coin toss to a properly powered test. That is
the argument for running N6, and it is a better argument than the one the
pre-registration made.

The pre-registration's own two-proportion table already said the neighbouring
thing — *"Q1 can see a 20-point drop and cannot see a 10-point one"* — and then
registered a band as though a test were available. **The power section was right
and the band section did not read it.** That is the actual defect: not a wrong
number, but two sections of one document disagreeing, with the optimistic one
carrying the registration.

## What I am proposing, and what I am not

Not deciding this alone — it changes what a 720-call run is for.

1. **Q1 is registered as descriptive**, with a cluster-bootstrap interval and no
   p-value, in exactly the form the pre-registration already chose for Q3. An
   interval that includes zero and includes 0.10 is reported as what it is.
2. **The band that is testable is the consequential one.** The pre-registration's
   own decision rule turns at a fall of 0.10 — *"corpus v2 results become
   uninterpretable rather than merely capped"*. At 64 triples the run has about
   even odds of resolving that boundary, and after the merge better than even.
   Register against **0.10**, which the instrument can nearly see, not against
   **0.025**, which it cannot.
3. **Recall on XL is the pre-registration's own stated place to expect the real
   effect** — *"if the fall is real and large it will be in recall on XL, not in
   accuracy"* — and it is the stratum with one positive per triple, where
   clustering is provably vacuous. That is where added long-band triples buy the
   most, and it is a reason to run the merge before the calls rather than after.

**What I am not proposing is cancelling N6.** Q2, Q3 and Q4 are unaffected by any
of this; Q2 is the cheapest replication available and Q4's FPR-by-kind table has
never been computed at all. A run that cannot settle its headline can still be
the only run that has ever asked the other three.

## Where I expect to be wrong

The 0.95 reference accuracy is taken from v2 and v3 is a harder corpus by
construction. If the arms land nearer 0.85 the variance is larger and every
number above is optimistic — the floors rise and Q1 gets *worse*, not better. I
have not modelled that, and the direction of the error is against the run.
