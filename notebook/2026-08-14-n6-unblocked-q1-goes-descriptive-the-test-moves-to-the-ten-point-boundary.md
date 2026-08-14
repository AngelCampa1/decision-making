# 2026-08-14 — N6 unblocked: Q1 goes descriptive, the test moves to the ten-point boundary

This supersedes Q1's registered band in
[N6's 2026-08-13 pre-registration](2026-08-13-n6-prediction-does-accuracy-fall-on-the-long-bands.md),
which is not edited. That entry stays as written, including the band this one
replaces. The case for replacing it is
[2026-08-14's own analysis](2026-08-14-q1-cannot-reach-its-own-prediction-at-any-corpus-size-we-will-build.md):
Q1's registered band, `accuracy(S+M) − accuracy(L+XL)` in `[−0.05, +0.10]`, is
entered by the null 80.6% of the time and by the predicted 0–5-point fall 85.2%
of the time, at the 40-triple corpus the band was written against — and it gets
*worse*, not better, as the corpus grows: 92.4% for the null at the current
87 triples. A result inside a band nearly every hypothesis lands in is not
evidence for any of them. Every number in that analysis is re-derived below
from a clean process (`scipy.stats`, no cached constants) rather than trusted,
per standing rule 3 in `docs/AUTONOMOUS_WORK_ORDER.md`. All of it held.

**A note on the corpus while this was written.** Two other sessions are active
in this working tree right now: one editing `l.yaml`/`xl.yaml` to close the
`open`-view leak below, one adding case-subset selection to
`scripts/adjudicate.py` and adjudicating `s`/`m`. Nothing here edits
`datasets/triggers/`. The instrument counts below were read fresh at the end of
this session, not cached from its start, and `de check --fast` passed at that
moment — stated as a snapshot, not a guarantee, since the other sessions are
still working.

---

## 1. Every figure re-derived

### The two-proportion / clustering assumption behind the SEs

The 2026-08-14 analysis's `0.0518` and `0.0346` standard errors, and the
`0.577`/`0.823` power figures, are not printed by any function in `stats/` —
there is no two-proportion power function in this codebase, as the brief
anticipated, so this is worked by hand. Reverse-engineering the SEs shows the
assumption behind them: binomial variance at a reference accuracy of **0.95**,
inflated by a **constant design effect of 1.63**. That constant follows from
`design_effect(mean_cluster_size, icc) = 1 + (m − 1) × icc`
(`stats/cluster.py`) at `m = 3` (fixed — every triple is 1 positive + 2
negatives, so the mean cluster size cannot move as the corpus grows) and an
assumed **ICC of 0.315**. This ICC is a planning assumption, not a measurement
— N6 has not run, so there is no accuracy data to compute it from. That should
be stated plainly rather than left implicit, and the analysis entry did not say
so explicitly.

```
se(n1, n2) = sqrt(0.95 * 0.05 * (1/n1 + 1/n2) * 1.63)
```

| split | n(S+M) | n(L+XL) | SE | cited | match |
|---|---|---|---|---|---|
| as originally registered | 72 | 48 | 0.05185 | 0.0518 | yes |
| current corpus | 144 | 117 | 0.03463 | 0.0346 | yes |

Both reproduce to four significant figures. MDE at 80% power, two-sided
(`(z_0.975 + z_0.80) × SE`, `z`-sum = 2.8016):

| split | MDE |
|---|---|
| as registered (72 v 48) | 0.1453 — matches the "0.145" cell in the floor table |
| current (144 v 117) | 0.0970 — matches the cited "0.097" |

`P(estimate lands inside [−0.05, +0.10])`, `Φ` the normal CDF:

| true Δ | P(inside), 40 triples | cited | P(inside), 87 triples | cited |
|---|---|---|---|---|
| 0.000 (null) | 0.806 | 0.806 | 0.924 | 0.924 |
| 0.025 (predicted midpoint) | 0.852 | 0.852 | 0.970 | — |
| 0.050 (predicted upper edge) | 0.806 | — | 0.924 | — |
| 0.100 (consequential) | 0.498 | — | 0.500 | — |

All hold. **One correction to the analysis entry's "before merge" figure.**
The "before the merge (48 long items) 0.577" power figure does **not**
reproduce at `n1=72, n2=48` (that gives 0.488 two-sided) — it reproduces at
`n1=144, n2=48`:

```
se(144, 48) = 0.04638
power(two-sided, alpha=0.05, delta=0.10) = 0.5778   <- matches 0.577 exactly
se(144, 117) = 0.03463
power(two-sided, alpha=0.05, delta=0.10) = 0.8232   <- matches 0.823 exactly
```

This is not an error in the cited numbers, just an underspecified label. S+M
was already at 144 items (48 triples) before `a38d2d8` — that commit added 23
triples to the *long* bands only ("23 long-band triples merged", and
`39 − 16 = 23` triples added to L+XL), not to the short ones. "Before the
merge" means *L+XL still small, S+M already grown*, not *both sides at their
2026-08-13 sizes*. Both power figures reproduce exactly once that is read
correctly, so the 0.577 → 0.823 headline stands as written.

### Majority baseline and best-shortcut-stump, recomputed on the live corpus

Not copied from the brief — computed directly against
`datasets/triggers/decision-making/index.yaml` via
`decision_evals.corpus.majority_baseline` and `.stump_accuracy`:

```python
from decision_evals.triggers import load_trigger_set
from decision_evals.corpus import majority_baseline, stump_accuracy

ts = load_trigger_set(Path("datasets/triggers/decision-making/index.yaml"))
majority_baseline(ts)  # 0.6667
stump_accuracy(ts)  # 0.7011
```

**Majority baseline is unchanged at 0.667** — arithmetic necessity, since the
2-negatives-per-1-positive ratio is fixed by construction and majority baseline
is `2/3` regardless of corpus size. **The best-shortcut-stump figure has moved:
0.750 (120 items) → 0.701 (261 items), lift 0.083 → 0.034.** Against
`MAX_STUMP_LIFT = 0.1` (`corpus.py`) that is comfortably under gate.

**Two readings of that number point in opposite directions, and they need to
be told apart rather than collapsed into one "harder corpus" sentence.**
*Shortcut-resistance* went up: the 23 new triples give a depth-2 stump over
`FEATURES` less to work with than the original 120 items did, 3.4 points of
lift instead of 8.3 — a smaller ceiling than the original registration
assumed, and that part is good news for the corpus. But *the bar an arm has to
clear to prove it did more than pattern-match* went **down**, from 0.750 to
0.701, by the same arithmetic. The pre-registration's own phrase — "the number
an arm has to beat to have measured anything" — is a threshold, and the
threshold moved 4.9 points lower. An arm landing at, say, 0.72 would have
failed to clear the original bar and now clears the current one; that is not
the arm improving, it is the bar moving. **The reading this entry intends:
compare N6's accuracy against 0.701, not the stale 0.750, because 0.701 is
what a shortcut can actually reach on the corpus N6 will run against — but
report the margin over it as a weaker signal than the pre-registration's
original framing implied**, since the margin needed to be meaningful shrank
by the same 4.9 points. Any of the original decision-rule branches that name
"0.750" (`2026-08-13`'s Q1 section, "Flat, and the arm beats 0.750...") should
be read with 0.701 substituted, not with the sentence's conclusion left
unchanged.

### The weighting identity (item 4 of the brief)

Checked directly with synthetic records through `trigger_arms.summarise`,
not just read from the module's own claim:

```
3 items x 2 repeats, balanced           -> weight="record" == weight="item" (0.6667 both)
same records, repeats within one item
  flipped in order                      -> still equal (0.6667 both)
3rd item given a 3rd repeat (unbalanced) -> record=0.7143, item=0.7222 (differ)
```

Confirmed: identical under balanced repeats, part under unbalanced ones, and
order within a balanced case does not matter. **N6 runs 2 repeats per item.**
Stated once, per the brief: **`weight="item"` is the reported figure below.**
It is the right default for a new report per `Weight`'s own docstring, and
under N6's balanced design it is numerically identical to `"record"` anyway —
reporting both would be reporting one number twice, which is the exact M5
`covers` failure mode this repository has already caught once.

---

## 2. The instrument, recounted from the corpus, not from the brief

Read fresh from `datasets/triggers/decision-making/{s,m,l,xl}.yaml` at the end
of this session (re-verified after the coordinator's note that other sessions
are editing `l.yaml`/`xl.yaml` — the counts below are unchanged from the
first read, which is expected: the concurrent edit is fixing the `open`-view
leak by changing which triple member's opener carries the question mark, not
by adding or removing items).

| band | items | positives (=triples) | negatives | routed positives |
|---|---|---|---|---|
| s | 72 | 24 | 48 | 15 |
| m | 72 | 24 | 48 | 16 |
| l | 66 | 22 | 44 | 20 |
| xl | 51 | 17 | 34 | 15 |
| **all** | **261** | **87** | **174** | **66** |

Every positive's triple id has exactly 1 positive and 2 negatives — checked
programmatically, not assumed. "Routed positive" = positive whose `route`
field is non-empty (not the open router); computed the same way the original
table implicitly did.

**Majority-class baseline: 0.667 (unchanged, structural). Best depth-2-stump
accuracy: 0.701 (lift 0.034, was 0.750/0.083 at 120 items).** Both numbers
above.

---

## 3. Q1, superseding band

Two registrations replace the single band above, per the analysis entry's own
recommendation and the pre-registration's own unread power section
("Q1 can see a 20-point drop and cannot see a 10-point one").

### 3a. Descriptive — reported without a pass/fail verdict

*Estimator:* `trigger_arms.bootstrap_rate_difference(control=<L+XL full-arm
records>, treatment=<S+M full-arm records>, cluster_on="triple")`.
*Denominator:* per-item correctness rate (`weight="item"` in spirit — the
function's own per-item averaging), clustered on `triple`.
*Reported:* `.difference`, `.ci_low`, `.ci_high`, `.standard_error`, at the
function's default 95% confidence, alongside `n_items_control`,
`n_items_treatment`, `n_clusters_control`, `n_clusters_treatment`. No band, no
p-value — exactly the form Q3 already used in the original pre-registration.

### 3b. Testable — the consequential boundary, not the predicted one

*Estimator:* the same `bootstrap_rate_difference` call as 3a.
*Decision rule:* `result.excludes_zero and result.difference > 0` — the
two-sided 95% interval on `accuracy(S+M) − accuracy(L+XL)` excludes zero, in
the direction of a fall on the long bands.
*Denominator:* as in 3a.

This is a test of "no fall" against "some fall," not specifically against
"a 10-point fall" — but its *power* is stated against 0.10 because that is
the pre-registration's own consequential threshold, the branch where it says
v2's results "become uninterpretable rather than merely capped." Under the
planning assumption in §1 (0.95 reference accuracy, design effect 1.63):

| true fall | power to reject "no fall" |
|---|---|
| 0.000 | 0.050 (= alpha, by construction) |
| 0.025 (predicted midpoint) | 0.111 |
| 0.050 (predicted upper edge) | 0.303 |
| **0.100 (consequential)** | **0.823** |
| 0.150 | 0.991 |

**What this licenses and what it does not.** A reject (CI excludes zero,
positive direction) is interpretable evidence of *some* fall, with 82% power
to catch it if the true fall is 0.10 or larger — that is a properly powered
test now, where it was a coin toss before the long-band merge (0.577 → 0.823,
confirmed in §1). A **failure to reject is not evidence of "no fall."** At the
originally predicted 0–5 points, this test has 11%–30% power — a null here is
uninformative about the prediction the track was built to test, and that
prediction stays answerable only by 3a's descriptive interval, read as an
interval and not as a verdict.

**This registration is entered before the run, per standing rule.** N6 has
not been called.

---

## 4. Q2, Q3, Q4 — what moved and what did not

**Q2 (ordering: does `stakes-shown` beat `full` on precision, as on v2?) is
unaffected.** It is a sign comparison within one corpus version, not a power
claim tied to item counts, and `label_versions_comparable` already refuses the
cross-version subtraction correctly (confirmed in the analysis entry — not
re-litigated here). Nothing about the recount changes what is registered.

**Q3's denominator has grown, and materially.** Registered: "`ledger` is the
worst-routed of the four procedures, over the N `ledger`-labelled positives."
Recounted directly from the corpus (`route == "ledger"` under the runner's
`"first"` rule, matching what `covers` stamps):

| procedure | positives (first-route) | positives (any-route) |
|---|---|---|
| fit | 16 | 16 |
| cascade | 16 | 19 |
| timing | 15 | 16 |
| **ledger** | **19** | **19** |

**`ledger`'s denominator is 19, not the originally registered 10.** Under the
`"any"` rule the four groups do not partition (per `RoutingByProcedure`'s own
docstring) — `cascade` and `timing` each pick up items `ledger` does not,
which is why `ledger`'s count is identical under both rules: no dual-route
item names `ledger` as a second acceptable answer. The prediction itself
("`ledger` routes worst — it has never been tested on its own case") is
unchanged; only its denominator moves, and it moves toward more resolving
power, not less — 19 items is still descriptive-only by the pre-registration's
own standard (ten items detects nothing; nineteen is closer but still far
short of a McNemar-eligible n), so this stays registered as descriptive, as
before.

**Q4's `settled` band was registered at n=5. It is now n=20.** Full recount by
`kind` across all four bands, all negatives:

| kind | n (was, 120-item corpus) | n (now, 261-item corpus) |
|---|---|---|
| lookup | 27 | 49 |
| summarise | 15 | 29 |
| compute | 12 | 27 |
| generate | 13 | 27 |
| **settled** | **5** | **20** |
| diagnose | 4 | 14 |
| meta | 4 | 8 |
| **total** | **80** | **174** |

Every kind grew by roughly the corpus's own growth factor (261/120 ≈ 2.18),
which is what a uniform-band expansion should produce and is a weak check that
nothing was selectively added to one kind. At n=20, `settled`'s Wilson
interval is materially narrower than at n=5 — a `0.000` reading is no longer
indistinguishable from "no data," which was the entire caveat the original
registration carried. The prediction (`settled` highest, `lookup` lowest) is
unchanged; the label "a descriptive statement about five items" in the
original entry should now read **twenty**, and the finding is correspondingly
more able to say something.

---

## 5. Track I4 addendum — a variance outcome does not enter N6

Answering the coordinator's three questions directly, since they were the
third thing this brief asked for and are easy to lose under the Q1 rewrite.

**1. Does the aptitude/unreliability decomposition even apply to a binary
firing decision?** Yes, but not in the form that matters for a Bernoulli
population mean. `aptitude_unreliability` applied to a single Bernoulli(p)
process is not a useful decomposition — its variance is `p(1−p)`, fully
determined by its own mean, so "reduce variance without moving the mean" is
incoherent for one item's *population* firing rate. But that is not what
`per_item_reliability` measures. It measures **agreement across an item's own
repeats**, and items are not one Bernoulli process — they are 87 (or 174, for
negatives) *different* processes, each with its own latent firing probability
`p_item`, and `p_item` can be near 0, near 1, or near 0.5 independent of the
*pooled* accuracy. Two arms can have identical pooled accuracy while one
has all its `p_item` near 0 or 1 (deterministic per item — low within-item
scatter) and the other has many `p_item` near 0.5 (borderline — high
scatter). That is exactly what item-level ICC captures, and it is a coherent,
non-degenerate quantity for a binary outcome. So I4's concept is not
incoherent here; it needs to be read as a claim about the *distribution of
per-item firing probabilities*, not about the variance of a single scalar
Bernoulli trial. This is a different ICC from the triple-clustering one in §1
— that one is about correlation *across items sharing a body*, this one is
about agreement *across repeats of the same item* — and the two should not be
confused when both appear in the same report.

**2. Is 2 repeats enough to measure it?** No, and by a wide margin, confirmed
by direct call rather than by citation:

```python
from decision_evals.stats.reliability import repeats_for_reliability, repeats_for_scatter_precision

repeats_for_reliability(0.833, 0.8)  # 1  -- M5's measured ICC, mean-reliability target 0.8
repeats_for_reliability(0.852, 0.8)  # 1  -- M6's measured ICC, same target
repeats_for_scatter_precision(0.25)  # 9  -- relative SE 0.25 on the spread itself
repeats_for_scatter_precision(0.35)  # 6
repeats_for_scatter_precision(0.50)  # 3
```

At the ICCs already measured on this instrument (0.833 M5, 0.852 M6 — both
`docs/RESEARCH_PROGRAMME.md` line 1432, cross-checked here rather than
retyped), **2 repeats is more than sufficient to estimate the *mean* firing
rate reliably** (`repeats_for_reliability` returns 1 at a target of 0.8, and
returns 2 — matching N6's actual design — at the stricter target of 0.9 this
repository used when it set "2 repeats, not 5"). It is **not** sufficient to
estimate *scatter itself*: at `n_repeats=2`, `per_item_reliability`'s own
docstring states the mechanism directly — every percentile interpolates
between the same two values, so scatter degenerates to a fixed fraction
(`0.9 × |difference|` at the 10/90 split) of the absolute repeat-to-repeat
difference. It is not imprecise at 2 repeats, it is **structurally
uninformative** about anything beyond "did this item agree with itself once."
A relative standard error of even 0.50 on the spread estimate needs 3 repeats;
0.25 needs 9. N6 has 2.

**3. What follows for N6.** **N6 does not register a variance/reliability
outcome, and none of the bands in §3 or §4 should be read as one.** Any ICC
computed from N6's 2-repeat data is for the triple-clustering design effect
(§1, §3) — a nuisance parameter for a mean comparison — not a claim about
per-item consistency, and per-item scatter across N6's repeats will be
reported, if at all, as a raw descriptive count ("N items disagreed between
their two repeats") with the explicit caveat that it cannot distinguish a real
consistency difference between arms from sampling noise at this repeat count.
Registering an I4-shaped claim on N6 data would be exactly the "discovered
post hoc" failure I4 exists to prevent — a variance outcome earns its own
pre-registration and its own repeat budget (Track I3's own arithmetic: 6–9
repeats depending on target precision), not a repurposing of a run sized for
something else.

---

## 6. The outstanding blocker, stated honestly

**N6 does not start until the `open`-view leak is closed and the affected
items are re-adjudicated.** From the 176-cell battery report
([`2026-08-14-the-battery-searches-176-cells-and-nobody-had-costed-that.md`](2026-08-14-the-battery-searches-176-cells-and-nobody-had-costed-that.md))
and confirmed still open in `datasets/triggers/corpus-baseline.txt` as of this
session: `question_marks` and `terminal_question` on the `open` view read
**AUC 0.779 in XL and 0.716 in L** (post-merge numbers; the baseline file's own
prose is the pre-merge 0.566/3.47-SE snapshot, explicitly left unrewritten by
the session that owns that entry). Whether a case's first sentence ends in a
question mark separates the labels in the long bands at close to four cases in
five — a shortcut an arm could exploit without reading the turn, concentrated
exactly where Q1 is asking whether accuracy holds up.

That is the direct confound: **Q1 asks whether firing accuracy falls on the
long bands, and this leak can make the long bands look artificially easier
than they are** — high accuracy on L/XL would be uninterpretable as "the arm
reads long context fine" if it is partly "the arm can tell which sentence
poses the question." A flat or improving Q1 result collected before this
closes would not be usable evidence either way.

**Status at the time of this entry:** a separate session is actively editing
`l.yaml` and `xl.yaml` to close it — `git status` shows both files modified,
not committed, as this was written. This entry does not touch either file.
N6 is blocked on: (a) that fix landing, (b) the affected L/XL items being
re-adjudicated against the corrected corpus, and (c) `corpus-baseline.txt`
reflecting the closure (the entry currently there is explicit that it still
reads as open, more so post-merge than pre-merge). None of that is this
entry's work to do; this entry only registers what N6 measures once it runs.

---

## What this entry changes and what it does not

**Changes:** Q1's registered band (§3), the routing and FPR-by-kind
denominators for Q3 and Q4 (§4, numbers only — predictions unchanged), and
adds an explicit non-registration for any variance/reliability claim on N6
data (§5).

**Does not change:** the 2026-08-13 pre-registration itself (not edited, per
the brief), Q2, N6's call design, or anything in `datasets/triggers/`. N6
remains held until §6 clears.
