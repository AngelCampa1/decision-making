# Status: what has been run, what it showed, what is left

**Hand-maintained. Last updated 2026-08-14.** There is no generator behind this
file and it does not pretend otherwise — see the note at the top of
[`SCORECARD.md`](../SCORECARD.md) about a status file that claimed to be
generated and was not.

[`SCORECARD.md`](../SCORECARD.md) answers *what may be publicly claimed about a
skill* and is empty on purpose.
[`RESEARCH_PROGRAMME.md`](RESEARCH_PROGRAMME.md) answers *what the tracks are*.
**This file answers *where the work actually is*.**

---

## The one-line version

**Seven results are in, eight measurements were caught being broken, no skill
has been evaluated end-to-end — and the instrument that produced every trigger
result turns out to be solvable at 0.890 by counting words, which is now
[Track N](RESEARCH_PROGRAMME.md).**

*The counts above read "six" and "five" until 2026-08-13, when both tables below
had already grown past them. A summary line that is not recomputed from the
table under it is a hand-maintained number like any other.*

---

## Model calls on record

| family | calls | status |
|---|---|---|
| trigger arms (M4, M5, M6, M6b, L5, confidence, baseline) | **2,555** | the working instrument |
| **L7** (`stakes-named`, `stakes-shown`) | **292** | run, scored and **published** 2026-08-13 |
| M5 first attempt, voided by a parser defect | 365 | kept as evidence |
| Track A pilots (`math`, `actions`) | 420 | both venues closed |
| calibration + `evidence-ledger` corpora | 560 | ceiling, closed |
| casefile probe | 44 | clean negative, closed |
| Track 0 instrument checks | 8 | passed |
| **total** | **~4,240** | |

Notional cost only — everything runs on a Claude Max subscription, nothing is
billed per call. See [`CLAUDE.md`](../CLAUDE.md).

**Correction, 2026-08-13, appended. A whole run is missing from the table
above.** N3's blind label adjudication ran on 2026-08-13 — 3 judges × 120 turns,
**360 calls**, 0 unparseable — and this file did not mention it anywhere. The
total was therefore **~4,600**, not ~4,240, counted from
`results/triggers/adjudication.jsonl`.

It is the largest single omission the ledger has had, and it is instructive
about *which* runs go missing: N3 produced no arm comparison and no accuracy
number, so it never passed through the reporting path that puts a family in
this table. **A run that measures the instrument rather than the skill is
exactly the run nobody records**, and N3 was the run that decided whether the
corpus could be used at all.

**Correction, 2026-08-14, appended.** The corpus grew to 261 items the same day
(two merges, 24 short-band and 23 long-band triples), leaving 141 items with no
adjudication record at all. `s` and `m` are now **fully adjudicated** — 216 more
calls, 3 judges × 72 turns, 0 unparseable, `--only` scoped so `l`/`xl` (mid-edit
by another session closing an `open`-view leak) were not touched. The total is
therefore **~4,816**, not ~4,600. See
[`2026-08-14-n3-continued-the-72-s-and-m-items-n3-left-unadjudicated.md`](../notebook/2026-08-14-n3-continued-the-72-s-and-m-items-n3-left-unadjudicated.md).

---

## Venues built, and what happened to each

| venue | verdict | why |
|---|---|---|
| `rel-*` single-turn relevance | **closed — ceiling** | 0.946, and 15 of 15 zeros were the answer key |
| `rel-*` rebuilt with colliding distractors | **closed — ceiling** | 0.971; collisions bought 2.9pp |
| `probe-*` casefiles | **closed — clean negative** | 27 trap opportunities, **zero taken** |
| `math` sharded conversations | **closed — real null** | `p_discordant` = 0.000 |
| `actions` tool-use | **closed — no measurement exists** | no object is comparable across the arms |
| **trigger instrument** | **working** | 2,555 calls, 0 unparseable, 0 isolation failures |

---

## Results in hand

| run | question | answer |
|---|---|---|
| **M4** | one entry or four separate skills? | **Indistinguishable on firing** (0.956 vs 0.951, p = 0.83). Four are more conservative. The 202-skill shadowing citation no longer reaches down to four. |
| **L5** | which part of a description does the work? | Routing summary **−5.8pp** false firing, exclusions **−3.7pp**, opener **+1.8pp — it costs**. Not a length effect. |
| **M5** | two entries? | Conservatism floor already at two. Firing unmoved (p = 0.50). |
| **M6 + M6b** | which two procedures share an entry? | **`covers` spans 28.6 points across the three partitions** of identical vocabulary. A merged entry does not inherit its parts' pull. |
| **Track I** | how many repeats are needed? | ICC 0.83–0.85. **Two, not five.** Cut every later arm by 60%. |
| **Track K** | does the decision literature support any of this? | 4 of 11 popular frameworks have **no located controlled evaluation**. Patient decision aids have 209 RCTs. LLM assistance moves process measures and did not move the one outcome measure tested. |
| **L7** | can the description be eager without deleting the parts that work? | **Showing beat naming.** `stakes-shown` reaches **FPR 0.000 / recall 0.912 / precision 1.000** and **dominates `no-opener` on both axes** — the first Pareto improvement of one arm over another here. The two openers are not distinguishable (p = 0.257). Band 4, the experiment, failed: **the precision/recall frontier is intact after seven arms.** Band 6 passed against expectation — both stakes openers score 0/2 on tabs-vs-spaces while `opener-only` fires 5/5, so the criterion reads content and not sentence shape. |

**The through-line:** five independent manipulations of a skill description —
structure, content, count, composition twice — and **not one moved how well it
discriminates.** Every one moved only where it sits on the precision/recall
frontier.

**And a second reading of that through-line, added 2026-08-13.** The trigger
corpus is separable by **turn length alone at AUC 0.850**, and a bare
*"fire if ≥ 18 words"* rule scores **0.890** with no model on the **version 2**
key, against the best arm measured on that key — **0.9795** for the best
description arm (`stakes-shown`) and **0.9863** for `confidence`.
So every result above was competing for about **nine points over a ruler**.
Five nulls is what a ceiling looks like.

**Correction, 2026-08-13, appended.** This read "0.956 … about six points"
until the checkpoints were reconciled. 0.956 is the `full` arm on the
**version 1** key, where the same ruler scores 0.877, so the six-point figure
was arithmetic across two answer keys — and 0.956 was not the best arm at
either version, because `no-opener` reached 0.967 and `confidence` 0.973 at v1,
and L5 published no accuracy column for anyone to notice. Neither reading
is established and both must be reported until the corpus is rebuilt —
[`the v3 plan`](superpowers/plans/2026-08-13-trigger-corpus-v3.md),
[`the finding`](../notebook/2026-08-13-the-corpus-is-89-percent-solved-by-counting-words.md).

---

## Measurements caught being broken

Recorded because every one of them produced a clean run, a full checkpoint and a
plausible number. **None crashed.**

| defect | what it read | what was true |
|---|---|---|
| scorer read `final_response` across arms with different turn counts | 45/50 vs 23/50, "clean replication" | an artefact; crediting the whole conversation reversed it |
| parser whitelist dropped every entry name an n=2 arm offers | routing 0.000 over 365 calls | nothing had failed |
| routing graded against names the arm never offered | routing 0.000 again | no answer could have matched |
| `covers` quoted without its denominator | 0.743 | or 0.895, depending |
| `covers` compared across partitions | 0.743 vs 0.857 | 28.6-point range; the measure is retired |
| the corpus itself, never audited | five arm comparisons | a ruler solves it at 0.890; the movable range is ~9 points, not the ~6 quoted here until 2026-08-13, which compared a v2 ruler with a v1 arm → **Track N** |
| the model tier is not in any record | every trigger number | `--model` is a CLI default and the tier survived only as prose in a hand-written README. **Closed 2026-08-13 (N8)**: `run_triggers.py` stamps `model`, and `models_comparable` refuses a comparison spanning tiers |
| `summarise()` read `should_fire` from the record, so a single-arm report on a v1 checkpoint silently emitted v1 numbers | `full` at recall 0.878 beside `stakes-shown` at 0.912 | a v2 re-score puts `full` five points higher; the L7 table would have been wrong in the shipped arm's disfavour |

Six of the eight have a guard and tests: `final_responses_comparable`,
`decision(text, allowed)`, `routing_is_by_name`, `trigger_arms.covers_rates`,
and — since N8 closed on 2026-08-13 — `models_comparable`. **Row six is the
open one**, and it is Track N's whole job: nothing can guard a corpus against
admitting a shortcut except rebuilding it.

**The eighth is still open, and it is the sharpest, because a guard was already
there and did not cover it.** `label_versions_comparable` refused the cross-arm comparison,
which is the guard working. Nothing refuses a *single-arm* report — and a
single-arm report is what goes in a README. The guard protects comparisons and
not statements. Found while scoring L7; see
[the entry](../notebook/2026-08-13-l7-showing-beat-naming-and-nothing-left-the-frontier.md).

**The pattern is the finding.** Not one of these was caught by a run failing.
Every one was caught by somebody asking a question the instrument was not set up
to answer — and two of the eight were the maintainer asking, not the tooling.

---

## Where the corpus is, 2026-08-14

**261 items, 87 triples** — s 24, m 24, l 22, xl 17. Grown from 120 items / 40
triples by two same-day merges (24 short-band triples, 23 long-band ones). A
separate session's own notebook entry has the merge detail and the battery
before/after; not reproduced here.

**192 of 261 items are now blind-adjudicated (N3 + this continuation), and
seven adjudicated label moves are on record and unapplied:**

| case | direction | votes | adjudicated |
|---|---|---|---|
| `s02n2` | negative → positive | (False, True, True) | 2026-08-13 (N3) |
| `s12p` | positive → negative | (True, False, False) | 2026-08-13 (N3) |
| `xl05n2` | negative → positive | (True, True, True) | 2026-08-13 (N3) |
| `m14n2` | negative → positive | (True, True, True) | 2026-08-14 |
| `m16n2` | negative → positive | (True, True, False) | 2026-08-14 |
| `m18p` | positive → negative | (False, False, False) | 2026-08-14 |
| `s19n2` | negative → positive | (True, True, False) | 2026-08-14 |

None applied yet: moving a label bumps the answer-key version and invalidates
every comparison across the boundary, so the key moves **once**, at the
freeze, carrying all seven plus whatever N4–N7 still finds. Movement over the
192 adjudicated so far is 7/192 = 0.036 against the pre-registered 0.20 kill —
the corpus continues to survive it by a wide margin. Detail, per-band
breakdown and inter-rater agreement:
[`2026-08-14-n3-continued-the-72-s-and-m-items-n3-left-unadjudicated.md`](../notebook/2026-08-14-n3-continued-the-72-s-and-m-items-n3-left-unadjudicated.md).

L and XL (69 of the 261 items) remain at N3's original coverage. A separate
session is mid-edit on `l.yaml`/`xl.yaml`/`corpus-baseline.txt` closing an
`open`-view leak, so their text is not stable enough to adjudicate against yet.

---

## Open decisions that belong to the maintainer

| decision | status |
|---|---|
| **Eager or cautious?** | **Answered 2026-08-13 — eager, provisionally.** See [the notebook entry](../notebook/2026-08-13-the-maintainer-picked-eager.md). |
| `x-n21` / `x-n22` labels | open — worth 11 points of recall |
| `x-n03`, `x-n20` labels | open — largest per-item regressions |
| `p06` label (`fit` or `cascade`) | open — the model answers timing-ish in every arm |
| Should routing allow several acceptable routes? | open — must be decided blind to which items failed |
| Vendor the spider databases? | open — needs explicit permission, third-party download |
| **Write the N4 holdout turns** | **open, and it is the only Track N item that is not mine to do.** ~20 turns you author, ideally real messages rather than turns written to order, never seen by me before authoring closes. It is the control on "a model is writing the corpus that will evaluate a model", which no other gate touches. |

Trigger corpus v3 is no longer on this list — it stopped being a decision and
became **[Track N](RESEARCH_PROGRAMME.md)** on 2026-08-13.

---

## Tracks

| track | state |
|---|---|
| **0** — instrument (transport) | ✅ done |
| **I** — reliability | ✅ done |
| **N** — the trigger corpus | 🟡 **started.** N1 shortcut battery done; **N2 done** — grown by two merges to 87 triples, 261 items (S 24, M 24, L 22, XL 17); **N8 done** — the model tier is in the record and a comparison spanning tiers is refused; **N3 partial** — S and M fully adjudicated (192 of 261 items total, 7 moves unapplied — see below), L/XL blocked on an in-progress `open`-view leak fix; N4–N7 open. Blocks every future L and M claim and retro-qualifies every past one. |
| **K** — frameworks review | 🟡 three passes; K4 waits on Track A |
| **M** — skill design | 🟡 M1–M6b done; M3 has no estimator on a merged arm; **all of it now carries the Track N caveat** |
| **L** — skill variants | 🟡 L5 and **L7 run**; L7 unpublished; **same Track N caveat** |
| **S** — ship the skills | 🔴 not started |
| **A** — replication | 🔴 A1 closed both families; A2 needs harder items |
| **B** — attribution | 🔴 not started |
| **C** — evidence aggregation | 🔴 not started |
| **D** — delegation quality | 🔴 not started |
| **E** — handoff fidelity | 🔴 not started |
| **F** — end-to-end | 🔴 not started |
| **G** — volume / long context | 🔴 demoted; harness fixed and canary-verified to 101k tokens, no corpus |
| **H** — tailoring, life decisions | 🔴 not started; construct and its evidence now identified |
| **J** — write-up and release | 🔴 not started |

---

## Run but not written up

The one category this file exists to stop growing quietly.

**Empty.** L7 was the only entry and was published on 2026-08-13 —
[`results/decision-making/2026-08-13-abb6862-l7-stakes/`](../results/decision-making/2026-08-13-abb6862-l7-stakes/).

Every checkpoint in `results/triggers/` now corresponds to a published directory
under `results/decision-making/`. `de index` and the provenance gate — see
`evals/src/decision_evals/provenance.py` — check that a published run has a
prediction that predates it. Neither can see a run that was never published at
all, which is what this table is for, and it is the reason to keep it here
empty rather than delete it.

---

## What is proven

**Nothing.** Every skill carries `verdict: UNTESTED` and `de lint` refuses to let
one into the shipped plugin. That is enforced, not aspirational, and it is the
point of the repository: *"we have not shown this works"* and *"this works"* are
different statements.
