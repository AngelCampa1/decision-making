# The accumulation venue

**Status: designed, not built.** This document exists so the design is on the
record before the number that motivates it arrives, and so the decision to build
it can be argued with rather than inferred from code.

## Why a second venue

The single-turn corpus asks a model to decide from six to nine short facts in
one prompt of roughly 350 tokens. That is not context accumulation. The whole
pile fits comfortably in attention, nothing is displaced, nothing is forgotten,
and the model can re-read every fact for free.

The literature is specific about where the surviving effect lives. The 2026
GSM-NoOp re-audit largely dissolved the short-horizon distractor effect once
ambiguous items were filtered out. Context rot (arXiv:2606.29718) documents
30–50% degradation *before* documented context limits, and its 2026 work targets
long-horizon agentic search. The flagship's premise — that ranking accumulated
context and naming what to discard improves decisions — is a claim about the
second setting, and the corpus was built in the first.

The first control run measured the consequence: 110 of 110 correct, with only 13
of 93 loaded responses acknowledging a distractor at all.

## What accumulation means here

The harness runs `claude -p` single-shot with no tools and no session, so an
item is one prompt. Accumulation is therefore *rendered* rather than lived: the
item is a transcript of prior turns — tool results, retrieved documents, user
messages — followed by the decision question.

That is a real limitation and it is the honest framing: the model reads an
accumulated context it did not itself produce. What it shares with the agentic
setting is the thing under test — a long, unranked, partly stale pile that has
to be reduced before a decision. What it does not share is error compounding
across the model's own steps, which this venue cannot measure and should not
claim to.

## The mechanism: supersession, not irrelevance

The single-turn corpus tests whether a model can *ignore* material. This venue
tests whether it can tell *current* material from *stale* material, which is a
different and more agentic failure.

An early turn states a value. A later turn revises it, explicitly. The answer is
computed from the revised value. A model that grabs the first number it finds —
or the most emphatic one, or the one nearest the question — gets a different
answer.

Three properties make this a better instrument than distractor irrelevance:

**Ground truth is not a judgement call.** "This figure was revised to 14 after
the audit" unambiguously supersedes "the figure is 9". There is no irrelevant-
versus-ambiguous line to walk, so the venue sidesteps the trap that dissolved
GSM-NoOp's effect entirely rather than trying to navigate it.

**It is what the skill actually claims.** `evidence-ledger` promises a ranked
ledger plus a *named discard list*. A superseded value is the clearest case of
something that must be named and discarded rather than silently dropped, and the
verify-then-discard split exists because bare "ignore X" instructions do not
work (arXiv:2506.08184).

**Depth becomes a real stratum.** With 20 to 60 turns there is somewhere to bury
things. Where the current value sits relative to the stale one, and how much
sits between them, are the dials — and the U-shaped position effect only applies
while context is under half full, which this venue can actually cross.

## Design sketch

A template gains:

- `turns` — an ordered pool of on-topic but inert transcript entries, used to pad
  to a target depth. On-topic matters: padding with unrelated chatter would
  reproduce the type-incompatibility mistake at a larger scale.
- `superseded` — each entry names a relevant fact it precedes and renders a
  stale value from its own variable, plus the revision language that supersedes
  it.
- A `depth` stratum replacing `position`: how many turns separate the stale
  value from its revision.

Sampling reuses the constraint the single-turn corpus already enforces:
substituting the stale value for the current one must change the answer.
Otherwise the careful reader and the first-number-grabber score identically and
the item contributes dilution.

## What this does not replace

The single-turn corpus keeps two jobs it is good at, and both are guards rather
than headline metrics:

- **The clean-room stratum.** Items with nothing to discard, where the answer
  should be reached every time. An accumulation item cannot be clean by
  construction.
- **The no-harm guard.** The flagship's claim is accuracy up on loaded items
  *and no regression on clean ones*, and the no-regression half is what kills a
  skill that ranks aggressively enough to throw away something it needed.

## What would make this the wrong move

Recorded so the decision stays falsifiable:

- If the rebuilt single-turn corpus lands inside [0.35, 0.75], the venue
  argument is weaker than stated and the single-turn corpus can carry the
  primary claim. This venue would then be a second experiment about a second
  failure mode, not a replacement.
- If accumulation items turn out to be *too* hard — control accuracy below 0.35 —
  the instrument is measuring reading stamina rather than ranking, and the dial
  is depth rather than the design.
- If a control model handles supersession near-perfectly at every depth, the
  premise is wrong in this venue too, and that is a publishable negative result
  about a specific, well-motivated hypothesis rather than a null about a corpus
  that could not test anything.
