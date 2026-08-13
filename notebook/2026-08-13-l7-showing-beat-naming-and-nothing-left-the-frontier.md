# L7: showing beat naming, and nothing left the frontier

**2026-08-13.** Outcome for
[the prediction](2026-08-13-l7-prediction-eager-without-deleting-what-works.md),
committed at `1cfd90b` before either arm ran. 73 cases × 2 repeats × 2 arms =
**292 isolated `claude -p` calls**, Haiku, **0 unparseable**, 0 isolation
failures. Scored against **trigger set v2**.

## The bands, as registered

| # | Band | Result | |
|---|---|---|---|
| 1 | parseable ≥ 98% | 146/146 both arms, 0 unparseable | ✅ |
| 2 | both arms beat `opener-only` on FPR (< 0.129) | 0.018 and 0.000 | ✅ |
| 3 | at least one arm reaches recall ≥ 0.94 | best 0.912 | ❌ |
| 4 | **at least one arm at FPR ≤ 0.06 *and* recall ≥ 0.94** | neither | ❌ |
| 5 | the two arms differ on FPR (descriptive) | 0.018 against 0.000 | ✅ |
| 6 | neither fires on the two lowest-stakes negatives | **0/2 on both, in both arms** | ✅ |

Two failed, and one of the two was a badly set band rather than a result. See
below.

## What the arms did

Every figure re-scored under v2 labels.

| arm | FPR | recall | precision | accuracy | never fired |
|---|---|---|---|---|---|
| `opener-only` | 0.1286 | **0.9529** | 0.735 | — | — |
| `no-exclusions` | 0.0571 | **0.9529** | 0.845 | — | — |
| `full` (shipped) | 0.0179 | 0.9294 | 0.941 | — | `x-n22` |
| **`stakes-shown`** | **0.0000** | 0.9118 | **1.0000** | **0.9795** | `x-n22` |
| `stakes-named` | 0.0179 | 0.8824 | 0.9375 | 0.9589 | `x-n03`, `x-n22` |
| `no-opener` | 0.0036 | 0.9059 | — | — | `x-n20` |

**Showing beat naming**, and I had no prior either way — which is why both ran
rather than my asking the maintainer a question the instrument could answer for
146 calls an arm.

`stakes-shown` has **precision 1.000**: across 110 negative observations it did
not fire once. It **dominates `no-opener`** on both axes — lower FPR *and*
higher recall — which is the first Pareto improvement of one arm over another in
this repository. It does **not** dominate `full`: it buys 1.8 points of FPR for
1.8 points of recall, which is a trade and not a win.

**Paired Wilcoxon, `stakes-shown` against `stakes-named`: p = 0.257**, 4 of 73
items differing, 3 favouring `shown`. The two openers are not distinguishable at
this n and the write-up may not say otherwise.

## Band 4 was the experiment and it failed

> *"Everything this repository has measured moves along the frontier and cancels.
> A point at FPR ≤ 0.06 with recall ≥ 0.94 sits above the line through `full`
> and `opener-only` and would be the first arm that is better rather than
> differently placed."*

No arm landed there. The frontier is intact after seven arms. Whatever a
description does, it moves *where on the line* the skill sits and not the line.

## Band 3 was unsettable and I set it anyway

Recall ≥ 0.94 over 17 positives needs 16 of 17. **`x-n22` has never fired in
any arm on any version** — a fact recorded in the prediction itself, in the
section headed *"where I expect to be wrong"*. So the ceiling was 16/17 = 0.941
and the band demanded a perfect score on everything else.

Writing a band whose own document explains why it cannot be met is not a
near-miss, it is a badly constructed band, and it goes in the working rules:
**a recall band must be set against the observed per-item ceiling, not against a
round number.** This is the fifth pre-registration defect on record and the
first that was visible before the run rather than after.

## Band 6 passed, and it was the one I expected to fail

> *"6 is the mechanism check, and it is the one I most expect to fail. 'Should I
> use tabs or spaces' has the grammar of a decision and none of the stakes."*

| negative | `stakes-named` | `stakes-shown` | `full` | `opener-only` |
|---|---|---|---|---|
| `x-n01` tabs vs spaces | 0/2 | 0/2 | 0/5 | **5/5** |
| `x-n02` variable naming | 0/2 | 0/2 | 0/5 | **5/5** |
| `n01` list vs set | 0/2 | 0/2 | 0/5 | **5/5** |
| `n04` plot twist | 0/2 | 0/2 | 0/5 | **5/5** |

Both stakes openers read the *content* and not the sentence shape. `opener-only`
fires on all four, every time — so the four turns are genuinely tempting, and a
description without exclusions takes the bait unanimously.

That is the clearest mechanism result in the run and it was not the one the run
was designed to get.

## The item that separates the two openers

Four items differ between the arms, and one of them carries the story:

| item | label | `stakes-shown` | `stakes-named` |
|---|---|---|---|
| `x-n03` *"Should I learn Rust?"* | positive | **2/2** | **0/2** |
| `x-n20` *"tests failing, fix before merging?"* | positive | 1/2 | 2/2 |
| `n07` *"how couples usually decide"* | negative | 0/2 | 1/2 |
| `n11` *"convert this to async?"* | negative | 0/2 | 1/2 |

**Naming stakes as a criterion makes the model apply it, and it applies it
strictly.** *"Should I learn Rust"* is a real decision about a person's own time
that does not look expensive, so an arm told to check for stakes declines. An
arm shown four examples matches the shape and fires.

That is exactly the tension the maintainer created by choosing **eager** while
keeping `x-n03` and `x-n22` as positives. `stakes-named` refuses precisely the
two positives that were kept on a maintainer's judgement, and it does so
unanimously. It is the most coherent behaviour in the run and it disagrees with
the answer key.

## An instrument defect found while scoring this

`summarise(records)` reads `should_fire` **from the record**, so calling it on a
v1 checkpoint silently reports v1 numbers. Every older arm on disk carries
`set_version: 1`; the L7 arms carry 2. The first scoring pass for this entry
therefore produced `full` at recall 0.878 — a v1 figure — beside `stakes-shown`
at 0.912, and the table would have been wrong by five points in the shipped
arm's disfavour.

`label_versions_comparable` **did** refuse the cross-arm comparison, which is
the guard working. But nothing refuses a *single-arm* report, and a single-arm
report is what goes in a README. **The guard protects comparisons and not
statements.** Recorded as the seventh measurement defect in
[`docs/STATUS.md`](../docs/STATUS.md); the fix is that re-scoring under current
labels must be explicit at the call site, which is how the table above was
produced.

## And all of it sits on a corpus a ruler solves at 0.890

`stakes-shown` at 0.9795 accuracy is **nine points above a word count** and the
best arm ever measured here is 0.956 by the same accounting. Whether *showing*
beats *naming* on turns a real person would send is not established by this run
and cannot be, on this corpus. See **Track N**.

The honest summary is that L7 produced the best-behaved arm on record, on an
instrument that was measuring something narrower than anybody had checked.
