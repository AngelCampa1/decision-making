# The first ablation measured resampling, and the fix is cheap

**2026-08-12.** Track 0.2/0.3/0.4. The scripted call tree runs, the isolation
receipt fires at every node, and the first version of the smoke test was
confounded in a way that would have quietly ruined Tracks B through F.

## What the done-when asked for, and what happened

| Requirement | Result |
|---|---|
| A 4-node scripted run completes with per-node records | 8 nodes across 2 trees |
| Isolation canary passes at every node | 8/8 receipts asserted |
| Budget and wall-clock over a call *tree* | $0.039 notional, 82 s summed |
| `de check` green | 9/9, 863 tests |

Cost by node is the number worth keeping: **orchestrator $0.023, sub-agents
$0.005–0.006 each.** The root costs about four times any leaf because it reads
all three reports. A single total would have hidden that, and it is the
difference between "delegation is expensive" and "aggregation is expensive",
which are different design problems.

## The confound

The smoke test runs the tree twice — once clean, once with one sub-agent's
report dropped — because a tree that merely *runs* is no evidence the
substitution seam reaches the model. Version one ran the second pass by simply
re-dispatching every sub-agent with one transform set to drop.

That is wrong, and the run said so. On the control pass `customer-impact`
produced a full report. On the ablation pass, from the **identical prompt**, it
replied *"I don't have sufficient information to assess customer impact."*

So two things differed between the arms: the dropped report, and the surviving
reports being resampled. The orchestrator's answer changed, and **nothing in the
run could say which cause did it.** A green "the answers differ" would have been
recorded as the seam working.

This is [Track I's finding](2026-08-11-seven-eighths-of-the-effect-is-scatter.md)
arriving somewhere new. Seven-eighths of the multi-turn effect is scatter rather
than aptitude; here scatter is large enough that a single resample of one node
swamps a whole-report ablation.

**The rule that follows, and it applies to every track from B onward: an
ablation must hold the surviving inputs fixed.** Otherwise it measures
resampling.

## The fix cost nothing, because the seam was already there

Pinning is the same `transform` hook handed a constant instead of a rewriter.
The sub-agent is still called and still recorded, so the record shows both what
it said on this pass and what the orchestrator was actually given —
`report_seen_by_parent` exists precisely for that gap.

## What the clean run showed

Control, all three reports live:

> **Recommend: Ship Monday.** Friday deployment risk is elevated due to missing
> automatic rollback and weekend on-call coverage […] Monday allows us to
> implement rollback capability while still delivering the feature 2 days before
> the enterprise customer's Wednesday renewal deadline.

Ablation, `release-risk` dropped, the other two pinned to the control text:

> **Ship Friday.** The enterprise customer renews Wednesday—only Friday delivery
> meets this deadline. **No release risk was flagged.** On-call constraints exist
> regardless of timing.

Exactly one input changed. The recommendation flipped, and the orchestrator
**named the absence** — "no release risk was flagged" — rather than silently
reasoning without it. That is Track B's mechanism working on the instrument
before Track B has a corpus.

It is one item on Haiku and is not a result. It is the demonstration that the
instrument can produce an attributable difference at all, which no venue in this
repository has previously been able to show.

## A prompt-design note that is not a footnote

In the first run, two of three sub-agents declined: *"I don't have access to your
team's on-call scheduling data"* — to a question that stated the on-call hours in
its second sentence. Adding *"everything you need is stated in the question;
there is no other source to consult"* to the sub-agent system prompt fixed it.

A node that declines is not a node reporting a finding, and a fan-out where a
third of the leaves abstain would have shown up downstream as a weak or absent
delegation effect. Worth checking the abstention rate per node in any real run
before reading anything into the orchestrator's answer.

## Open

- The ablation flipped the answer on **one** item. Whether that survives repeats
  is a Track B question and it needs the pinning rule above from the start.
- `render_reports` keeps the heading of an ablated node, so the orchestrator can
  see a sub-agent returned nothing. The alternative — dropping the heading — is
  a different experiment, and which one Track B wants is not decided.
