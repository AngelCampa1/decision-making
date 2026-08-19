# Five venues closed, and what that is evidence of

**2026-08-19.** Every prior mention of this fact reads as a shrug on the way to
the next thing — "three corpora were built and all three measured nothing,"
one line in [`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md)'s "Where we
are, honestly" section. It deserves to be looked at directly instead, because
across five attempts, built by different people at different times against
different task families, the closures are not five different problems. Four of
them are the same problem wearing four costumes, and that is worth stating as a
finding rather than filing five times as an obstacle.

## What is closed

Quoted from [`docs/STATUS.md`](../docs/STATUS.md), "Venues built, and what
happened to each":

| venue | verdict | why |
|---|---|---|
| `rel-*` single-turn relevance | closed — ceiling | 0.946, and 15 of 15 zeros were the answer key |
| `rel-*` rebuilt with colliding distractors | closed — ceiling | 0.971; collisions bought 2.9pp |
| `probe-*` casefiles | closed — clean negative | 27 trap opportunities, zero taken |
| `math` sharded conversations | closed — real null | `p_discordant` = 0.000 |
| `actions` tool-use | closed — no measurement exists | no object is comparable across the arms |

Five for five. The sixth row of that table, the trigger instrument, is the one
venue on record marked **working** — and it is a different kind of instrument
entirely: it measures whether a description fires, not whether an answer is
correct, so it is out of scope for what follows.

## Four of five share a shape

State the claim so it can be checked rather than taken on faith: **the unaided
model was already good enough on these four that no improvement could be
visible**, and the reason is structural rather than incidental. All four score
an answer mechanically — a relevance label, a trap taken or not, a GSM8K
number, an admissibility conjunct. To grade an item without a human reading the
transcript, the item has to state the fact that decides it clearly enough for a
parser and a comparison function to check. That same fact, stated in the same
prompt, is available to the model reading it. A venue built to be verifier-scored
is, by the same construction step that makes it scorable, built to be readable —
and a model that can read clears it.

That is a mechanism claim, not a restatement of the closures, and it should be
tested against each of the four rather than asserted once and left standing.

## Testing it against each of the four

**`math`.** The governing rule is arithmetic itself — as explicit as a rule
gets. `p_discordant` = 0.000 across the corrected pilot: 10/10 correct in both
the full and sharded conditions, and re-running the identical condition on the
one item that had disagreed reproduced agreement, so the null is not noise
([`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md), the A1 pilot
write-up). This is the cleanest fit: the most explicit rule in the whole set
produced the flattest result.

**`rel-*` single-turn.** [`docs/FAILURE_TAXONOMY.md`](../docs/FAILURE_TAXONOMY.md)
read all fifteen zeros by hand and found three item-defect kinds, not one
model-failure kind: `ambiguous-threshold`, `unstated-rule`, and
`ungoverned-scenario`. The fix for the largest of the three, `unstated-rule`, is
stated in the taxonomy's own words: *"the item gives the quantities but never
states what decides the question... Fix: Add the policy fact. Every other
template had one."* Read plainly, that line says the templates that scored
correctly were exactly the ones where the governing fact had already been made
explicit enough to grade — which is the same fact that made them explicit
enough to answer.

**`rel-*` rebuilt with colliding distractors.** The rebuild varied something
else entirely — "type-compatible colliding distractors," per
[`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md)'s corpus table — while
leaving the governing rule exactly as explicit as before. If the mechanism is
rule-explicitness rather than distractor difficulty, a harder-to-spot distractor
should buy little, and it did: 0.971 against 0.946, a 2.9-point move
([`docs/STATUS.md`](../docs/STATUS.md)). That is what the mechanism predicts a
null on a different axis should look like, not silence.

**`probe-*` casefiles.** Traps are built against explicit consequence rules —
order-1 through order-3, the kind of thing a skill's own `Abort if` clauses
state outright, per the blind-adjudication procedure in
[`AUTONOMOUS_WORK_ORDER.md`](../docs/AUTONOMOUS_WORK_ORDER.md). The result:
*"The casefile probe found the model already doing order-1 through order-3
consequence reasoning unprompted: 27 trap opportunities, zero taken, and it
computed a leverage ratio nobody asked for"* — quoted from
[`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md)'s S9 discussion. Same
shape: the rule the trap needed the model to notice was explicit enough to
grade, and explicit enough to see.

Four for four, on the account this entry is testing.

## The fifth does not fit, and the record says so

`actions` did not close on a ceiling. It closed because "the scorer reads
`final_response`; `full` has one turn and `sharded` has five to eleven,"
producing four different verdicts on the same 100 responses depending on which
object was scored, and the number that ends it: *"of the 23 sharded
conversations whose last shard carried no parseable call, 23 had emitted one
earlier. No exceptions"* — [`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md).
That is a construction defect in what gets compared, not a model reading a rule
and clearing it. The account above covers four venues, not five, and saying
otherwise would be stretching a real pattern to cover a closure it does not
explain.

One loose end worth naming rather than smoothing over: before the incomparability
defect closed `actions` outright, the same pilot's function-naming check produced
the only non-zero discordance in the whole battery — 2 of 10 pairs, in the
predicted direction, p = 0.25 exact
([`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md)). Function-naming is
graded by whether a specific token appears, not by matching a governing fact
stated in the prompt, so it sits outside the mechanism this entry is testing
either way. It was never sized because the venue closed on the comparability
defect first. The one place any signal appeared in this whole record is
attached to the venue this account cannot explain, and that is recorded rather
than argued away.

## The unstated-rule wrinkle

There is a second way to read the `rel-*` item defects that cuts against a
comfortable version of this finding. `unstated-rule` items did not produce
agent failures when the rule was missing — they produced *defensible* answers
that disagreed with an arbitrary ground truth, which is why they were recoded
as `item_defect` rather than left as `agent_wrong`. `docs/FAILURE_TAXONOMY.md`:
*"Every one turned out, on reading, to be a case where the model's answer was
defensible and the ground truth was not."* So the two available knobs in this
record are: state the rule explicitly, and the model clears it; leave it
implicit, and the result is not a clean model failure either, it is a dispute
with the key that a human has to adjudicate away. Neither knob, on the evidence
here, produces a scoreable agent failure. That is consistent with the mechanism
as stated — a verifier-scored venue needs the first knob — but it also means
this record has not located a middle setting where the rule is implicit *and*
the disagreement is real. It has located two failure modes for the corpus
author, not a spectrum for the model.

## A confound this record cannot yet separate: length, not just explicitness

All four ceiling venues are also the shortest, single-turn, lowest-difficulty
items in the programme — 350 to 1,650 tokens, per
[`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md)'s corpus table. The
taxonomy's own general point cuts the same way: *"at low difficulty, benchmark
defects dominate the zeros. You cannot build a failure taxonomy for the agent
until the corpus is hard enough to produce agent failures"*
([`docs/FAILURE_TAXONOMY.md`](../docs/FAILURE_TAXONOMY.md)). That is a simpler
competing account than rule-explicitness — plain difficulty — and nothing in
this record separates the two, because every rule-explicit item tried so far
has also been short. `math` is both the shortest and the most explicit; nothing
disentangles which property is doing the work.

The direct test would be a verifier-scored venue that is long, and the record
already shows it is not available. Track G, the volume track built to move
length, hit its own ceiling the same day this entry was written: its padding
library tops out under 3,000 tokens against the 40k–100k it needs, and *"any
length rung above ~2.8k must be authored first"* — [the Track G
entry](2026-08-19-track-g-cannot-reach-length.md). That same entry says the
fallback is not a fallback at all: *"staying at 2k is not a fallback, it is the
fifth closed venue under another name."* So the one experiment that would
separate length from explicitness is blocked on the same authoring bill that
blocks Track G generally, and until it runs, "explicit rule" and "short and
easy" remain the same four data points read two ways.

## What this is not evidence of

This is a finding about instruments, not about the skill the instruments were
built to eventually test. [`SCORECARD.md`](../SCORECARD.md) is explicit that
*"no skill has been evaluated yet"* and its verdict vocabulary reserves `NULL`
for a confirmation run whose *"confidence interval includes zero, or the effect
is smaller than the pre-registered minimum detectable effect."* None of these
five venues ran a skill-on-versus-skill-off comparison to a null result — four
of them closed on a ceiling or a clean negative in the base measurement itself,
before any such comparison could be attempted, and the fifth closed because no
comparable object existed to run one on. `NULL` and `UNTESTED` are different
claims for a reason, and this entry is about a third thing again: five attempts
to build the substrate a skill comparison would run on, none of which produced
a substrate with headroom.

Nor does it close the construct decision skills are meant to serve. A construct
that has never been instrumented cannot be closed by five instruments that could
not see it either way. That is the argument for why Track H is being registered
now rather than as another accuracy venue: its primary,
`d = P(change | governing) − P(change | matched non-governing)`, is a
within-triplet contrast rather than an accuracy against a fixed key
([`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md), Track H). A
within-triplet design does not need the governing fact hidden from a scorer to
produce headroom — the comparison is between two perturbations of the same
item, not between an answer and a key — so it is not obviously subject to the
same mechanism this entry describes. Whether it actually escapes the mechanism
is untested and is exactly what running it would show.

## What would make this finding wrong

Stated so it can be checked against, not just believed:

- **A verifier-scored venue that states its governing rule explicitly and does
  not hit ceiling.** This is the direct falsifier and the record does not yet
  contain one — Track G's length rung is the design that would produce it, and
  it cannot currently be built at the token counts that would distinguish
  explicitness from difficulty.
- **A venue that hides its governing rule and produces a clean, scoreable agent
  failure rather than a key dispute.** The `unstated-rule` wrinkle above found
  the opposite once; a second instance either way would matter.
- **A closure among the four that turns out, on rereading, to trace to something
  other than the model reading an explicit rule** — a labelling bug, a
  degenerate distribution, an item-authoring shortcut that inflated the base
  rate the way the trigger corpus's word-count shortcut did. Nobody has gone
  back through `rel-*`, `probe-*`, or `math` with that specific question since
  each was closed; this entry has not done it either, and it is the most direct
  way this account could be wrong without any new venue at all.
- **`actions`' one non-zero pair turning out to replicate** on a corrected,
  comparable object. If function-naming holds up under Option 2 or 3 from
  [`RESEARCH_PROGRAMME.md`](../docs/RESEARCH_PROGRAMME.md)'s A1 discussion, it
  would be the first confirmed non-ceiling result in the whole record and would
  need explaining against, not folded into, the four-venue account above.

## For the maintainer

Nothing here is a new run, a new gate, or a new number — it is a rereading of
five closures already on record, checked against the files that closed each
one rather than against the summary lines that describe them. If the reread
holds up, the next venue this repository builds should be judged before it is
built by whether its scoring requires the governing fact to be stated in a way
the model can also read, because that is now a predictable way to spend a
corpus-authoring budget on a fourth ceiling.
