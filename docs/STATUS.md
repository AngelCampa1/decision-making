# Status: what has been run, what it showed, what is left

**Hand-maintained. Last updated 2026-08-13.** There is no generator behind this
file and it does not pretend otherwise — see the note at the top of
[`SCORECARD.md`](../SCORECARD.md) about a status file that claimed to be
generated and was not.

[`SCORECARD.md`](../SCORECARD.md) answers *what may be publicly claimed about a
skill* and is empty on purpose.
[`RESEARCH_PROGRAMME.md`](RESEARCH_PROGRAMME.md) answers *what the tracks are*.
**This file answers *where the work actually is*.**

---

## The one-line version

**Six results are in, five measurements were caught being broken, no skill has
been evaluated end-to-end — and the instrument that produced every trigger
result turns out to be solvable at 0.890 by counting words, which is now
[Track N](RESEARCH_PROGRAMME.md).**

---

## Model calls on record

| family | calls | status |
|---|---|---|
| trigger arms (M4, M5, M6, M6b, L5, confidence, baseline) | **2,555** | the working instrument |
| **L7** (`stakes-named`, `stakes-shown`) | **292** | **run and scored, not published** — see below |
| M5 first attempt, voided by a parser defect | 365 | kept as evidence |
| Track A pilots (`math`, `actions`) | 420 | both venues closed |
| calibration + `evidence-ledger` corpora | 560 | ceiling, closed |
| casefile probe | 44 | clean negative, closed |
| Track 0 instrument checks | 8 | passed |
| **total** | **~4,240** | |

Notional cost only — everything runs on a Claude Max subscription, nothing is
billed per call. See [`CLAUDE.md`](../CLAUDE.md).

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
| **L7** | can the description be eager without deleting the parts that work? | **Showing beat naming.** `stakes-shown` reaches **FPR 0.000 / recall 0.912**, precision 1.000, and dominates the previous best-precision arm on both axes. Bands 3 and 4 failed — no arm reached recall 0.94, and band 3 was unsettable because `x-n22` never fires anywhere, capping recall at 0.941. Band 6 passed unexpectedly: neither arm fires on tabs-vs-spaces or variable naming, so the stakes criterion reads content rather than sentence shape. **Run and scored; the write-up and `results/` directory do not exist yet.** |

**The through-line:** five independent manipulations of a skill description —
structure, content, count, composition twice — and **not one moved how well it
discriminates.** Every one moved only where it sits on the precision/recall
frontier.

**And a second reading of that through-line, added 2026-08-13.** The trigger
corpus is separable by **turn length alone at AUC 0.850**, and a bare
*"fire if ≥ 18 words"* rule scores **0.890** with no model. The best arm ever
measured scores 0.956, so every result above was competing for about **six
points over a ruler**. Five nulls is what a ceiling looks like. Neither reading
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
| the corpus itself, never audited | five arm comparisons | a ruler solves it at 0.890; the movable range was ~6 points → **Track N** |
| the model tier is not in any record | every trigger number | `--model` is a CLI default and the tier survives only as prose in a hand-written README → **N8** |

Each of the first five has a guard and tests: `final_responses_comparable`,
`decision(text, allowed)`, `routing_is_by_name`, `trigger_arms.covers_rates`.
The last two are open and are Track N's job.

**The pattern is the finding.** Not one of these was caught by a run failing.
Every one was caught by somebody asking a question the instrument was not set up
to answer — and two of the seven were the maintainer asking, not the tooling.

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
| **N** — the trigger corpus | 🟡 **started.** N1 shortcut battery done; N2 half authored (24 of 40 triples, S and M bands); N3–N8 open. Blocks every future L and M claim and retro-qualifies every past one. |
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

| what | where it is | what is missing |
|---|---|---|
| **L7**, 292 calls, both arms | `results/triggers/verdicts-stakes-{named,shown}.jsonl`, tracked in git | the notebook outcome entry scoring the six registered bands, and a `results/decision-making/` directory with a README |

Everything else in `results/triggers/` corresponds to a published directory
under `results/decision-making/`. `de index` and the provenance gate — built in
a parallel session, see `evals/src/decision_evals/provenance.py` — check that a
published run has a prediction that predates it; neither catches a run that was
never published at all, which is what this table is for.

---

## What is proven

**Nothing.** Every skill carries `verdict: UNTESTED` and `de lint` refuses to let
one into the shipped plugin. That is enforced, not aspirational, and it is the
point of the repository: *"we have not shown this works"* and *"this works"* are
different statements.
