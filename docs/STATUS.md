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

**Eleven results are in, eleven measurements were caught being broken, no skill
has been evaluated end-to-end — and the instrument that produced every trigger
result was solvable at 0.890 by counting words, which is
[Track N](RESEARCH_PROGRAMME.md) and is now rebuilt: the best shortcut on the
**258**-item corpus is a stump at **0.7054** against a 0.6667 baseline, a lift
of **0.0387**. One of the eleven, **N9, is void** and answers nothing.**

*The counts above read "six" and "five" until 2026-08-13, and "eight" until
2026-08-14, each time because the tables below had already grown past them. A
summary line that is not recomputed from the table under it is a hand-maintained
number like any other — and it has now drifted twice, which says the lesson was
recorded and not learned.*

*Drifted a third time, corrected 2026-08-19. It read "seven" while the table
below had gained N5, N6 and N7 — three published runs that were in
`results/` and not in the ledger. The corpus figures in the same sentence
were stale by one revision: 261 items and a 0.701 stump are the **pre-shrink**
numbers, from before `l15` was retired. On v4 the stump is 0.7054 against
0.6667. Three drifts now, all of the same shape, and the count has never once
been wrong in the direction of claiming less than the tables held.*

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

**Correction, 2026-08-19, appended. Four runs since the table was last touched,
and none of them is in it.** Counted by line from the `.jsonl` beside each run's
`README.md`, so the arithmetic can be checked without trusting this paragraph:

| run | calls | from |
|---|---|---|
| N5 realism probe | 86 | `2026-08-18-0ee75d4-n5-realism-probe/realism.jsonl` |
| N6 confirmatory | 1,548 | `2026-08-18-e632659-n6-confirmatory/` (3 arms x 516) |
| N7 remaining arms | 1,548 | `2026-08-19-d52236a-n7-remaining-arms/` (3 arms x 516) |
| N9 in situ, **void** | 516 | `2026-08-19-505b236-n9-in-situ-void/verdicts-in-situ.jsonl` |
| **new total** | **~8,514** | 4,816 + 86 + 1,548 + 1,548 + 516 |

N9 is counted although the run is void, on the same rule that keeps M5's voided
365 in the table above: the ledger records calls made, not calls that produced a
usable number, and a void run is the more expensive kind to forget.

**A figure of 8,550 was briefly published on the site and is wrong.** It added
36 calls this file cannot account for. The 36 was almost certainly the three
casefile probes at 12 each, which are already inside the `casefile probe` row's
44 alongside the 8 canary rows, so it was double-counted. Recounting from
`results/` gives 8,514, and the site now quotes that.

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
| **N5** | are the generated turns realistic? | **Descriptive only, and the registered prediction failed.** `composed` 0.302 [0.215, 0.406] against a registered >0.50. Band is **perfectly confounded with em/en-dash presence** — all 38 `l`/`xl` items carry one, none of the 48 `s`/`m` items do — so band and punctuation cannot be told apart here. |
| **N6** | do the description findings survive the rebuilt corpus? | **Three of four bands met, Q4 falsified.** Q1 +0.0976 [0.0459, 0.1493]; `ledger` worst-routed in all three arms; `settled` is at the **bottom** of the routing table, not the top as registered. `opener-only`'s pooled FPR 0.250 is one band coming apart (`l` 0.524). Triple ICC **0.00–0.06** against the 0.315 the power arithmetic assumed, so that planning figure may not be reused. |
| **N7** | which description arm is best, all six on one corpus? | **One of five predictions met cleanly, and the top three arms are indistinguishable** — `no-opener` 0.9496, `stakes-shown` 0.9477, `full` 0.9360, p = 0.86 and p = 0.35. L7's precision/recall frontier is **intact after ten arms**. A pre-registration defect is recorded against this run. |
| **N9** | does the venue move firing? | **Void — no answer.** 516 calls made and refused on parse rate, no prediction scored. Reported here so the row is not mistaken for unrun. What broke is described in [the run record](../results/decision-making/2026-08-19-505b236-n9-in-situ-void/README.md) and is exploratory. |

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

**Correction, 2026-08-14, appended. The count is ten, and the ninth is the
largest of them**, because it is not a bug in a scorer — it is the wrong
statistic, used by every gate since the corpus was designed.

| defect | what it read | what was true |
|---|---|---|
| **the parse-rate gate reads repeat 0 only** | `run_triggers.py:918` prints one parse rate and voids the run on it, described everywhere as the run's parse rate | `row = done.get((case.id, 0))` — the gate never looks at repeat 1. On N9 that is 0.8566 against an aggregate of 0.8643; both are below the floor so the disposition held **by luck**. A run whose repeat 0 cleared 0.90 while repeat 1 dragged the aggregate under would exit zero and publish. Found by adversarial review 2026-08-19. **Fixed the same day** — `parse_rate_over_all_repeats()` counts every call the run was asked to make, and the gate runs before the repeat-0 report is built so a failing run never reaches a report describing half its calls. The falsifier was demonstrated against the old code first: a 20-item run with repeat 0 clean at 20/20 and repeat 1 at 6/20 — true rate 65% — returned 0 before the fix and voids after. The rejected denominator, *item parseable if any repeat parsed*, reads 0.957 on N9 against 0.8643 over all calls, and would have flipped N9 from void to published |
| **pooled AUC used on a matched corpus** | `word_count` at 0.517, "as clean as this battery can print" | the matched within-triple statistic read 0.660 at 3.24 null SE. A pooled AUC ranks positives against negatives from *other* triples, where body variation swamps the ask, so it is structurally blind to a rank held inside a triple — two-thirds of its comparisons are between items sharing nothing |
| `_shared_body` cut the common prefix back to the last **space**, and bodies end in a **newline** | opener features constant within every triple, reading exactly **0.500** | the body's final word leaked into every derived `ask` and became its first "sentence". Fifth inert-estimator instance, and it was in the module whose job is hunting inert estimators |

**The corpus was built as a matched design and evaluated as an unmatched one.**
Four separate pooled-cancellations were found by four separate people over
2026-08-13, each after the fact; the matched statistic found all of them in one
run. Row six above — "the corpus itself, never audited" — was the same failure
seen from the other side.

Neither statistic retires the other. Per-band pooled AUC is the *exploitability*
measure: an arm sees one turn and never sees the other two members of its
triple, so a within-triple rank is a defect in the construction rather than a
demonstrated exploit. Both are gated and both are printed.

**An eleventh is on record and is not counted here**, because it is a claim
rather than a measurement: `stats/multiplicity.py` implements
`benjamini_hochberg`, exports it, property-tests it, and **nothing calls it**,
while `paper/CHECKLIST.md` ticked "multiplicity controlled". Fourth instance of
a tested function with no caller. The wiring gate missed it because the module
is *import*-reachable via `stats/__init__.py`; importable is not used. The box is
now unticked.

---

## Where the corpus is, 2026-08-14

**258 items, 86 triples** — s 24, m 24, l 21, xl 17, after `l15` was retired on 2026-08-18. It read 261/87 until then, and 120/40 when authored. Grown from 120 items / 40
triples by two same-day merges (24 short-band triples, 23 long-band ones). A
separate session's own notebook entry has the merge detail and the battery
before/after; not reproduced here.

**A leak was found and closed the same day, and both halves are measured.** A
20,000-draw permutation test over the battery's full family — 4 bands × 4 views
× 11 features, 176 cells, band-restricted plain unpaired AUC, Benjamini–Hochberg
corrected — run before and against the committed fix:

| | cells crossing p<0.05 | expected by chance | surviving BH |
|---|---|---|---|
| before | 18 | 8.8 | **7** |
| after | 10 | 8.8 | **0** |

Five of the seven were one fact: `question_marks` and `terminal_question` on the
`open` view read AUC **0.779 in XL and 0.716 in L**. Whether a turn's *first
sentence* ends in a question mark separated the labels in the long bands at close
to four cases in five — plain unpaired AUC inside a single band, on text the arm
reads, with band membership self-evident from turn length. **Exploitable**,
unlike the within-triple findings, and it confounded N6's Q1 directly.

**By this test the corpus is now statistically indistinguishable from clean**,
and nothing moved in to replace what was removed — which is what happened to the
four previous generations of this defect. It was closed by moving *both* sides
and keeping per-triple variety, never by a per-item rule.

Two claims about the fix were raised and **refuted** by direct computation, both
recorded because a refuted claim is worth as much here as a confirmed one. The
target cells read AUC exactly 0.500, which is the signature of a *constant*
feature that ties every comparison and cannot fail — that is how the
`_shared_body` bug was caught. It is not that, and the check is not degenerate:
only 8 of 22 L triples and 8 of 17 XL triples are internally homogeneous, so
attainable AUC still reaches 0.807 in L against a dead-band requirement of 0.187.
**The check can still fail on a regression.**

**One discrepancy is open and is recorded rather than resolved.** Two independent
sweeps of the same pre-fix corpus disagreed on how many cells survive BH — 7 by
the measure above, 16 by another session's. It is not Monte Carlo noise (stable
across seeds) and it is not the degenerate-cell denominator (7 either way, at
m=176 and m=152). The likeliest explanation is that the two sweeps score
different statistics — matched within-triple versus plain unpaired — which is
precisely the distinction that produced defect nine. Unresolved.

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

**Correction, 2026-08-18, appended. The section above is stale by one commit,
and it is the third instance of this file lagging its own tables.** `30012d9`
closed the L/XL gap about an hour after the paragraph above was written, and
nothing came back to update it. Re-derived from
`results/triggers/adjudication.jsonl` by two independent agents and then by
hand, all three agreeing:

| | stated above | actual |
|---|---|---|
| adjudicated | 192 of 261 | **261 of 261**, 3 judges each, 0 unparseable |
| moves on record | 7 | **12** — 10 negative → positive, 2 positive → negative |
| movement | 7/192 = 0.036 | **12/261 = 0.046**, against the 0.20 kill |

The five further moves are `l15n2`, `l17n2`, `l21n1` (l), `xl13n2`, `xl16n1`
(xl). Per-band movement is 0.042 (s), 0.042 (m), 0.045 (l), 0.059 (xl) — no
band is individually near the kill, which the pooled figure alone would not
show. Fleiss kappa 0.862, Krippendorff alpha 0.862, unanimity 0.904.

**One number in `30012d9`'s own commit message is wrong and cannot be fixed
where it was written.** It reads "Eleven of the twelve move negative to
positive." It is **ten**: `m18p` and `s12p` both move positive → negative, and
this file's own table above already listed both correctly. History is the
pre-registration evidence and is not rewritten, so the correction lives here.

**And the freeze is now blocked on something nobody had costed.** All 12 moves
break the one-positive-per-triple invariant `corpus._check_triples` enforces —
the 10 negative → positive moves each land in a triple whose existing positive
the same adjudication **unanimously** reconfirmed, 10 of 10, giving two
positives; the 2 positive → negative moves land in triples whose other members
were unanimously negative, giving none. So "apply the adjudicated labels" is
not an executable instruction, and the freeze needs a design decision that the
v3 plan's *"rewrite the turn or move the label"* rule names but does not
resolve.

**Resolved the same day, and the answer was to rewrite rather than relabel.**
The plan sends a 2-of-3 disagreement to *rewrite the turn*, and reserves
retirement for a three-way split that three binary judges cannot produce. All
12 asks were rewritten to one rule — an inert ask asks about one thing, and may
not put two options in a frame that invites ranking them — by agents never shown
any judge's rationale. On blind re-adjudication, **36 calls, 11 of 12 now agree
with the key** against a registered band of 8; judge agreement on those twelve
went 0.611 → 1.000 pairwise, and corpus-wide movement **0.046 → 0.004**.

`l15` is retired whole, being the one item still disputed after the single
registered round. **The corpus is now 258 items, 86 triples — s 24, m 24, l 21,
xl 17.** No label moved, no version was bumped, no gate crossed, and the two
`sentence_count` findings ended *stronger* at 3.18σ. Detail:
[`the outcome`](../notebook/2026-08-18-the-rewrite-round-eleven-of-twelve-and-one-retirement.md).

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

**Correction, 2026-08-18, appended. The N4 row above is answered, and the answer
is no.** The maintainer will not author the ~20 holdout turns. It is off this
list — not done, *rerouted*: N4 will be built from a public human-written corpus
and labelled by N3's blind adjudicator. See
[Track N](RESEARCH_PROGRAMME.md#n4s-route-changed-on-2026-08-18-and-the-threat-it-controls-did-not).

**Correction, 2026-08-18, appended. This section is closed, and the heading
above is now wrong.** On a maintainer instruction — *remove every human gate from
the plans* — no row on this list waits on a person any longer. The heading stays
where it is because this file appends and does not rewrite; read it as *decisions
that used to belong to the maintainer*.

Each row is rerouted rather than deleted, because a gate deleted without a
replacement is a step the plan silently loses:

| row | where it goes now |
|---|---|
| `x-n21` / `x-n22` labels | **N3's three-instance blind adjudication**, answer key versioned, and the votes reported per item. **Not against the 0.20 kill** — that threshold was pre-registered over a whole corpus adjudicated blind, and these two are selected precisely because they already disagree stably, so movement over a hand-picked pair is not the quantity it calibrates. Cumulative corpus-wide movement is what carries the kill. These two are worth 11 points of recall and have been open since the day they were found, which is the argument against casting votes rather than for them |
| `x-n03`, `x-n20` labels | same procedure, same record |
| `p06` label (`fit` or `cascade`) | same procedure. A route label is a judgement about which file answers the turn, and three blind readers make it the same way they make a fire/no-fire call |
| Should routing allow several acceptable routes? | **pre-registered in `notebook/` before any per-item result is opened**, then applied mechanically. The requirement was that it be decided *blind to which items failed* — that is a property of the procedure, not of the decider, and a dated entry that predates the scoring proves it in a way a person's recollection cannot |
| Vendor the spider databases? | **the outside-data rule in [`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md)** — free, redistributable, licence read first-hand, a sample read for personal information, digest pinned. Executing the rule is the approval. Nothing about "explicit permission" is lost: the four checks stay, and a source failing any one of them is not vendored |
| Write the N4 holdout turns | already rerouted above — a public human-written corpus, labelled by N3's adjudicator |

**What this trades away, said plainly rather than buried.** Every one of these
rows now ends in a model's judgement about a corpus a model authored. The
casting vote was the last place a person was going to look at this data, and it
is gone. What replaces it is not better judgement — it is *checkable*
judgement: three blind readers leave a ledger, a pre-registered rule predates
its data, and a licence check leaves a digest. A maintainer's answer left none
of those, which is why five of these six rows sat open long enough to be
forgotten rather than decided.

**And a constraint that was never written down anywhere is now written down.**
This is a side project with no budget: nothing may be purchased — no paid data,
no paid APIs, no paid tooling. It had been true since the first commit and lived
only in the maintainer's head, which is the same defect shape as the model tier
that survived as prose in a README. It is now in
[`CLAUDE.md`](../CLAUDE.md) beside the subscription note, with the operational
half — licence read first-hand, redistribution checked, a sample actually read
for personal information, digest pinned — in
[`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md).

---

## Tracks

| track | state |
|---|---|
| **0** — instrument (transport) | ✅ done |
| **I** — reliability | ✅ done |
| **N** — the trigger corpus | 🟡 **started.** N1 shortcut battery done; **N2 done** — grown by two merges to 87 triples, 261 items (S 24, M 24, L 22, XL 17); **N8 done** — the model tier is in the record and a comparison spanning tiers is refused; **N3 done** — all items blind-adjudicated, and the 12 disputes resolved 2026-08-18 by rewriting the asks rather than moving labels: 11 of 12 now agree with the key, `l15` retired, corpus at **258 items / 86 triples**, movement 0.004, no label moved — the answer key nonetheless moved **3 → 4** later the same day, because version 3 had named four different corpora and N6 would have been the first run ever to stamp it; N4 rerouted to a public human-written source and [surveyed](../notebook/2026-08-18-n4-the-licence-survey-and-what-it-could-not-verify.md) — 4 of 8 candidates clear the redistribution bar, LMSYS-Chat-1M and ShareGPT are killed by it, and nothing may be fetched until the chosen source's licence is read directly, **N5's 10% human audit retired 2026-08-18** — its sheet was a self-assessment by the corpus's own author, still addressed to 120 items at key v3, and a forced choice against N4's human turns **will** replace it once N4's source is fetched, which it has not been; **N5's descriptive probe ran the same day for the first time** — 86 calls, `composed` 0.302 [0.215, 0.406], the registered >0.50 prediction falsified, and band inseparable from em-dash presence, **N6 done 2026-08-18** — 1,548 calls, 0 unparseable, three of four registered bands met and Q4 falsified in all three arms; `opener-only`'s pooled FPR of 0.250 is one band coming apart (`l` 0.524). The triple ICC is 0.00–0.06 against the 0.315 the power arithmetic assumed, so that planning figure may not be reused. **N7 done 2026-08-19** — 1,548 calls, 0 unparseable, all six description arms now on one corpus at one key and tier. One of five predictions met cleanly; the top three arms are statistically indistinguishable, and L7's precision/recall frontier is intact after ten arms. A pre-registration defect is recorded against this run: prediction 5 re-derived L7's band-4 thresholds from N6's observed numbers while citing L7, which flipped the verdict. **N9 ran 2026-08-19 and is void** — 516 calls refused on parse rate, no prediction scored; the first registered void condition here to actually fire. The 70 unparseable responses carry no `"fire"` key and no JSON at all: they are the model answering as Claude Code. Parse rate is **two clusters, not a gradient** — `technical`/`money`/`career` 0.9135 against `relationships`/`health` 0.7892, Fisher p = 0.00011 — and identity-refusal language never appears in `technical` or `career`. **An adversarial review found the gate reads repeat 0 only**, so it graded this run on half its calls; the disposition survives because every reading is below every floor, which is luck rather than verification. So the harness still has **no measurement of how the shipped description behaves in the venue anybody uses**, and closing that needs a new arm and a new pre-registration. Blocks every future L and M claim and retro-qualifies every past one. |
| **K** — frameworks review | 🟡 three passes; K4 waits on Track A |
| **M** — skill design | 🟡 M1–M6b done; M3 has no estimator on a merged arm; **all of it now carries the Track N caveat** |
| **L** — skill variants | 🟡 L5 and **L7 run**; L7 unpublished; **same Track N caveat** |
| **S** — ship the skills | 🟡 **started 2026-08-19.** S5 (`council.md`) and S6 (`hinge.md`) written, the last two procedures the founding brief named; S9's router half done — `ledger`'s row retargeted against its confusion pair (`cascade`, 77 records). **The shipped description now enumerates six procedures, which retires all ten description arms as measurements of what ships** — see [`DECISIONS.md`](DECISIONS.md). Nothing here is measured; all of it is `UNTESTED` |
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
