# K3 and K4 close: form can't explain an anecdote with no contrast, and the best-evidenced framework targets a failure five-sixths unconfirmed

**2026-08-14.** Not a run — a desk review, closing Track K3 (mine the public
prompt libraries for form) and Track K4 (map framework to LLM failure mode).
Full write-up in
[`docs/DECISION_FRAMEWORKS.md`](../docs/DECISION_FRAMEWORKS.md). K2 was being
worked concurrently in the same file by another session; the K1+K2 table and
this entry's WRAP-related claims were re-read and reconciled against their
edits before this was written, not before either session started.

## K3 — the form question the founding observation posed

CLAUDE.md records that the maintainer installed `cc-thinking-skills` (28
skills, autonomous description-triggering) and reports it did not help, and
frames that as "data about form, not about the frameworks." Two more public
libraries were read first-hand to see whether form predicts outcome:
`thinking-skills` (wanikua, 20 frameworks as **slash commands** — explicit
invocation only, no router, no autonomous triggering at all) and
`claude-skills-mental-models` (cyperx84, 98 "Munger-style" models bundled
into **one** autonomously-triggered skill, plus four parallel delivery
forms).

**The question cannot be answered from the public record, and that is the
finding, not a gap in the search.** None of the three libraries reports a
validated accuracy gain — cc-thinking-skills states one provisional number
*below its own bar*; the other two make no claim at all. There is no
"helped" library to set next to the maintainer's "didn't help" one, and an
outcome contrast needs two points.

What the survey does establish is a real, mechanical form split that maps
onto this repo's own M-track axis: wanikua's slash-command form has no
description-discrimination problem *by construction* (the human picks the
command), while cc-thinking-skills and cyperx84 both use the same
autonomous-triggering mechanism `decision-making` uses and so are exposed to
exactly what M2–M6 spent five experiments measuring.

**Prediction, stated so it can be checked later by whoever instruments
cc-thinking-skills.** If M4/M5/M6's own finding generalises past n=4 —
entry count moves the precision/recall frontier, not discrimination — a
28-separate-skill library should fail by **under-firing**, not by
mis-routing. Nobody has measured this. I also wrote down, and flagged as an
inference rather than a finding, that content is the more parsimonious
explanation for "didn't help" than shadowing: K1/K2 independently found that
most of what a 28-skill mental-models library reaches for (Kepner-Tregoe,
WRAP, OODA, satisficing) carries no located controlled evidence at all, and
this repo's own M-track already found entry count doesn't move
discrimination. Both readings stay open until someone actually instruments
one of these libraries.

## K4 — framework to failure mode, and what Track A actually contributes

Checked before writing anything: Track A (`docs/RESEARCH_PROGRAMME.md` Part
4) is not a test of any of the eleven catalogued frameworks. Its five
sub-experiments target multi-turn drop, recency, handoff loss, delegation
value and reliability — a different axis from anchoring, overconfidence,
sycophancy or base-rate neglect. Only two of A1's three families have
closed: `math` at `p_discordant` = 0.000 (ceiling/no-power, not a documented
absence of failure) and `actions` (unmeasurable — no comparable object
across arms, an instrument defect). `database`, A2–A5 have not run. **Track
A therefore contributes nothing to K4's documented/assumed column**, contrary
to what an agent under time pressure might have assumed given how much of
the programme leans on it.

Two papers were opened first-hand and grounded genuine LLM-side evidence
that did not exist in this document before today: anchoring bias in LLMs
(arXiv:2412.06593 — "the sensitivity of LLM responses to biased hints", CoT
and reflection found insufficient to mitigate it) and LLM overconfidence
(arXiv:2505.02151 — "all five LLMs we study are overconfident: they
overestimate the probability that their answer is correct between 20% and
60%"). Both are **pending a `paper/refs.bib` entry** — recorded instead in
`paper/citations-baseline.txt`, because another session was mid-edit on
`refs.bib`. A third paper (arXiv:2508.02087, sycophancy, directional only,
no rate) was already in the bibliography from earlier work and needed no new
entry — grounds Consider-the-opposite's target (anchoring on the user's own
framing).

**The finding worth stating plainly: three of the eleven frameworks fail the
excellent-evidence-wrong-target test, and the cleanest instance is not the
one I expected going in.** I expected OODA or satisficing to be the clean
case, since both fail on mechanism (no adversary tempo loop, no sustained
search-and-regret process, for a stateless single completion) independent of
evidence quality. They do fail that way. But the sharper instance is
**debiasing training (game/video)** — the single best-evidenced framework in
the entire K1/K2 catalogue, "supported," Cohen's *d* > 1, durable at two
months, not contested the way calibration is. Its target is a six-bias
battery, and only anchoring — one of six — has a located LLM study. The
other five (bias blind spot, confirmation bias, fundamental attribution
error, projection bias, representativeness) are validated against
constructs that presuppose an ongoing self-model or a model of *another*
agent's behaviour over time, which a stateless single-call model has no
clear counterpart for. The best human evidence in the table is evidenced
against a target that is at most one-sixth confirmed here.

A fourth case, pre-mortem, is excluded on different grounds — not a
literature gap but this repo's own casefile probe, which found the target
failure (under-weighting downstream failure paths) does not occur: 27 trap
opportunities across consequence-orders 1–3, none taken.

**One row moved while this was being written, from a concurrent K2 edit,
and is worth recording because it is the opposite pattern.** WRAP was split
into an integrated four-step process (still no human evidence) and a
"widen your options" component that the K2 pass found real trials for
(Basu & Savani 2017, Dow et al. 2010). The LLM-side target for that
component — does the model default to a narrow, single-option answer — is
still assumed, not documented. So WRAP's component is the inverse of
debiasing training: live human evidence, open LLM evidence, rather than the
other way round. Left in the table as a genuinely open row rather than
forced into either bucket.

## What is not closed

K4's documented/assumed column is provisional wherever it says DOCUMENTED
from outside literature (anchoring, overconfidence, sycophancy are all
general-purpose LLM findings, not measured on this repo's own decision
tasks) and wherever it says ASSUMED (reference-class/base-rate neglect in
LLMs specifically was searched for and not found — the located work tests
LLMs *assisting human* forecasters, not the model's own unaided reasoning,
and was not opened first-hand or cited here as a result). Re-read this
against Track A's later results once A2–A5 and `database` land.

## Sources

Full list with verbatim quotes in
[`docs/DECISION_FRAMEWORKS.md`](../docs/DECISION_FRAMEWORKS.md#sources-checked-on-2026-08-14-k3-and-k4-closing-pass).
