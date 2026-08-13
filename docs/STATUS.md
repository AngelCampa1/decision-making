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

**One instrument works, five results are in, three measurements were caught
being broken, and no skill has been evaluated end-to-end.**

---

## Model calls on record

| family | calls | status |
|---|---|---|
| trigger arms (M4, M5, M6, M6b, L5, confidence, baseline) | **2,555** | the working instrument |
| M5 first attempt, voided by a parser defect | 365 | kept as evidence |
| Track A pilots (`math`, `actions`) | 420 | both venues closed |
| calibration + `evidence-ledger` corpora | 560 | ceiling, closed |
| casefile probe | 44 | clean negative, closed |
| Track 0 instrument checks | 8 | passed |
| **total** | **~3,950** | |

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

**The through-line:** five independent manipulations of a skill description —
structure, content, count, composition twice — and **not one moved how well it
discriminates.** Every one moved only where it sits on the precision/recall
frontier.

---

## Measurements caught being broken

Recorded because all three produced a clean run, a full checkpoint and a
plausible number. **None crashed.**

| defect | what it read | what was true |
|---|---|---|
| scorer read `final_response` across arms with different turn counts | 45/50 vs 23/50, "clean replication" | an artefact; crediting the whole conversation reversed it |
| parser whitelist dropped every entry name an n=2 arm offers | routing 0.000 over 365 calls | nothing had failed |
| routing graded against names the arm never offered | routing 0.000 again | no answer could have matched |
| `covers` quoted without its denominator | 0.743 | or 0.895, depending |
| `covers` compared across partitions | 0.743 vs 0.857 | 28.6-point range; the measure is retired |

Each now has a guard and tests: `final_responses_comparable`,
`decision(text, allowed)`, `routing_is_by_name`, `trigger_arms.covers_rates`.

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

---

## Tracks

| track | state |
|---|---|
| **0** — instrument | ✅ done |
| **I** — reliability | ✅ done |
| **K** — frameworks review | 🟡 three passes; K4 waits on Track A |
| **M** — skill design | 🟡 M1–M6b done; M3 has no estimator on a merged arm |
| **L** — skill variants | 🟡 L5 done; **L7 (eager, keeping the boilerplate) is now well-posed** |
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

## What is proven

**Nothing.** Every skill carries `verdict: UNTESTED` and `de lint` refuses to let
one into the shipped plugin. That is enforced, not aspirational, and it is the
point of the repository: *"we have not shown this works"* and *"this works"* are
different statements.
