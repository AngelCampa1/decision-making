# Part 5: where a skill helps

**Audience:** the evaluating reader, and in particular anyone picking up a track.

Tracks C, D and E. Evidence aggregation, delegation quality, handoff fidelity.
They run in parallel once Part 4 reports, and each is independently pointable.

Part 5 of eight. The tracks table, the venue map, the sequencing and the
claim ladder are in [`RESEARCH_PROGRAMME.md`](../RESEARCH_PROGRAMME.md).
Headings below start at `###`, carried over from the split so that a track's
anchor is the one it had in the monolith.

---

Parallel once Part 4 reports. Each is independently pointable.

### Track C: evidence aggregation

This track is the orchestrator's judgment over what came back. Skill under test:
`evidence-ledger`. This is the user's "last message" complaint stated as a
measurable claim, and it is the failure the skill already claims to fix.

| # | Experiment | The failure it catches |
|---|---|---|
| C1 | Contradicting reports. Two sub-agents return conflicting findings, one early, one late. | Silently taking the later one instead of naming the conflict |
| C2 | Supersession, lived. An early turn states a value; a later turn revises it. The design in `ACCUMULATION_VENUE.md`, finally in a venue that can host it. | First-number-grabbing |
| C3 | Confident and wrong. A hedged report is right, a confident report is wrong. | Weighting confidence over evidence |
| C4 | Aggregation dose. 1 → 3 → 7 sub-agent reports. | Where aggregation breaks |
| C5 | Skill placement. Orchestrator on / off, crossed with Track E. | Where a skill has to be installed to work |

Hypothesis falsifier. Skill and control degrade identically → skills do not buy
robustness to accumulation. That is a *more* informative negative than "no
degradation exists" and is reported as one.

Depends on Tracks 0, A2, A3, B.

### Track D: delegation quality

What to ask, who to ask, and whether to believe the answer. This is MAST's
largest category (41.8% design and specification, 21.3% verification and
termination). `evidence-ledger` does not address this; a new skill is needed.
Working name: `scope-and-verify`, shipping `verdict: UNTESTED`.

| # | Experiment |
|---|---|
| D1 | Brief quality: score the orchestrator's briefs against a rubric, correlate with sub-agent output quality. Establishes that the brief is on the causal path before any skill is written. |
| D2 | Under-specification: tasks where a naive decomposition provably drops a constraint. |
| D3 | Verification: plant an internally contradictory sub-agent report. Does the orchestrator check? |
| D4 | Termination: does it stop too early, or never stop? MAST's 21.3%. |

Depends on Tracks 0, A4, B. D1 gates the rest: if brief quality does not predict
outcome, there is nothing for a delegation skill to improve.

### Track E: handoff fidelity

The unexplored cell is to install the skill on the *reporting* side. Every
design in this repository so far assumes the skill goes on the decider. If
compression is where the evidence dies, the skill belongs on the sub-agent.

| # | Experiment |
|---|---|
| E1 | What survives: plant *N* facts of known decisiveness in the sub-agent's material, measure which appear in its report. |
| E2 | Does a reporting skill change what survives? Skill on the sub-agent only. |
| E3 | Directional bias: replicate the summaries-distort-decisions result in our domain. Does the summariser's framing move the decision? |
| E4 | The placement factorial: orchestrator {on, off} × sub-agent {on, off}. |

E4 is the most useful result in the programme for anyone actually installing a
skill, and nobody has it. "Where do I put it" is a question every user of these
systems has, and it is answerable in four cells.

Depends on Tracks 0, A3, B.
