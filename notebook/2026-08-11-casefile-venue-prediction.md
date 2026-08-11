# 2026-08-11 — The casefile venue, and what I expect the probe to show

Recorded **before** any casefile has been put in front of a model. The plumbing
was validated on two hand-written fixtures — one admissible, one deliberately
trapped — and nothing else has run.

## Why the venue changed

Two control runs said the single-turn corpus cannot measure this. 0.946 against a
band of [0.35, 0.75]; 13 of 93 loaded responses acknowledging a distractor at all;
15 of 15 zeros turning out to be my defects rather than model failures. The
rebuild to type-compatible collisions is still finishing and the prediction on
record is high 0.8s — better, still unusable.

The diagnosis was never "too easy." A nine-fact, two-option puzzle has no room for
the failure. "It's raining in Paraguay, grab your raincoat" was an exaggeration,
and I built a benchmark around the exaggeration.

What replaces it is a **casefile**: 5–12 documents in a fictional jurisdiction
(Meridian), a numbered condition list, a menu of candidate actions, and a risk
question. Ground truth is a structure — governing conditions, required actions,
prohibited actions, an exposure band, and a deliberately withheld pivot fact —
rather than one label. The primary is **admissibility**: every required action
taken, no prohibited action taken, pivot named. Many different recommendations
pass, which is the point.

And it carries a second failure the old corpus could not express at all: an action
that is locally correct and **foreclosed downstream**. Filing the Year 3 amendment
is right on the Year 3 documents and reopens Year 1 under s.214(3), 61 days before
that window would have closed by itself.

## The predictions

Twelve casefiles, three at each trap order {none, 1, 2, 3}, control arm, Haiku.

| # | Quantity | Prediction |
|---|---|---|
| 1 | Overall admissibility | **0.10–0.30**, point estimate 0.17 |
| 2 | Trap rate at order ≥ 2 | **0.50–0.83**, point estimate 0.67 |
| 3 | Exposure answered at first order | **≥ 0.60** |
| 4 | Pivot named | **≈ 0.25** |
| 5 | Unjustified action taken (the raincoat) | **0.10–0.20** |
| 6 | All five blocks present | **≥ 0.90** |
| 7 | Gate 1 (headroom) and Gate 2 (trap bites) | both **PASS** |

**Prediction 3 is the one I care most about.** The risk question asks for the
exposure of a specific named counterfactual — filing this week — so its ground
truth does not depend on what the model recommends. A model that stops at the
Year 3 correction charge answers `moderate`; a model that propagates the look-back
answers `high`. It is the cleanest single reading of whether the path was played
forward, and it is readable even from a response that got everything else right.

**Prediction 5 is a prediction against my own flagship.** With an explicit action
menu and one obviously irrelevant option on it, I do not expect Haiku to pick the
storage-migration action. If that holds, the raincoat failure does not live in a
menu — it lives in free-text recommendation — and this venue will measure
`consequence-cascade` well and `evidence-ledger` poorly. That would be a real
problem for the discriminant-validity table, and I would rather have said so
first.

**Prediction 1 has a floor risk.** Admissibility is a conjunction over a required
set of four to six actions plus the pivot, and the most likely single failure is
dropping the boring one — the 21-day compliance response that has nothing to do
with the interesting trap. If it comes in at 0/12, the conjunction is too strict
rather than the venue too hard, and the fix is to score required-set coverage
before tightening anything else about the cases.

## What would make me wrong in a way that matters

- **Admissibility ≥ 0.85.** The venue has no headroom and the dials go up:
  document count, condition count, and how far apart an action sits from its
  consequence.
- **Trap rate at order ≥ 2 of zero.** Haiku plays the path forward reliably and
  `consequence-cascade` has nothing to fix here. That is a publishable negative
  about a specific hypothesis rather than a null about a corpus that could not
  test anything, which is the distinction the last month was spent learning.
- **Blocks below 0.90.** The five-block contract is the highest-risk edit in the
  repo. If the control arm cannot comply with it, no arm comparison built on it
  means anything, and the contract gets simplified before the corpus grows.

## Scoring

`python -m uv run python scripts/probe_casefile.py --model haiku`. Every trace
gets read. The automatic label is triage, not a result — the last corpus produced
fifteen zeros that were all mine, and reporting the automatic label would have
published a 5% agent error rate that did not exist.
