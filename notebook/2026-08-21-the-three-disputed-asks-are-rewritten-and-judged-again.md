# 2026-08-21 — The three disputed asks are rewritten and judged again

**2026-08-21, second entry of the day.** The adjudication of answer key v5's 72
new items ran this afternoon and the corpus survived the kill at movement 0.042.
Three labels moved, and
[the entry that reports it](2026-08-21-the-72-council-and-hinge-items-go-through-adjudication.md)
records why none of the three can be applied: each breaks the
one-positive-two-negative invariant `corpus._check_triples` enforces.

That is 2026-08-18's finding repeating on the new items, and the remedy it
settled on is the plan's live branch: rewrite the disputed ask and re-adjudicate
blind. This entry pre-registers that round.

## What is being rewritten, and to what budget

| item | key says | what the rewrite has to make the closing ask do | words now | must land in |
|---|---|---|---|---|
| `l24n1` | negative | ask for something with a determinate answer | 241 | 234-260 |
| `m25p` | positive | ask for a recommendation or a judgement | 68 | 65-72 |
| `m29n2` | negative | ask for something with a determinate answer | 65 | 59-66 |

The budgets are the triple's own length tolerance, 10% of the longest member
with a floor of three words. `m29` already sits at its limit, 59 to 66 against a
tolerance of 7, so that rewrite has no slack in either direction.

**Only the closing ask changes.** The body of each turn stays byte-identical, so
the triple keeps sharing one body and the contrast stays where the design puts
it.

## Blinding

The rewrites are done by sub-agents that see the turn, the item's intended
polarity, the shipped definition of what firing means, and the word budget.
They do not see the judges' verdicts, the vote counts, or any judge's `why`.
That is the same discipline the 2026-08-18 round used, and the reason for it is
that an author shown the reasoning writes to the judge instead of to the
definition.

## Prediction, before the rewrites are written

The 2026-08-18 round rewrote twelve asks and eleven of the twelve then agreed
with the key, with corpus movement falling to 0.004 and no label moving.

- **Agreement on the three rewritten items: 2 or 3 of 3.** Point estimate 3.
  Against the earlier round's 11/12 that is the same rate, and three items is
  too few for anything finer.
- **Labels moving after the rewrite: 0**, most likely, with 1 inside the band.
- The re-adjudication is 3 items x 3 judges = **9 calls**, `haiku`, same
  instrument.

**Where I expect to be wrong.** `l24n1` is the one I expect to survive the
rewrite still disputed. Its ask is already arithmetic, explicitly so — it asks
for ten-year figures and for the assumptions behind them — and three judges read
the turn as a decision request anyway. That points at the *body* rather than the
ask: 241 words establishing that three people must agree before probate
completes will read as a decision whatever the last sentence requests. If that
is right, no rewrite of the ask alone fixes `l24n1`, and the honest conclusion
is that the triple's body cannot carry an inert member at that length.

`m25p` is the one I expect to be easiest. "Can you put both cases properly?"
asks for the cases to be made, which is a produced artefact under the shipped
definition, so the label and the ask genuinely disagree and a rewrite has
somewhere to go.

## What gets reported, and over which denominator

Two figures, because one of them can be gamed and the other cannot.

- **Post-rewrite movement over the 3 rewritten items.** This is the figure the
  earlier round reported as 0.004.
- **Cumulative disagreement over the 72**, counting every disagreement ever
  found on these items rather than resetting against the rewritten base. It
  stays at 3/72 = 0.042 whatever this round returns.

The second exists because the first can be driven to zero by rewriting until the
judges agree. 2026-08-18 recorded that hazard about retirement, and it applies
in the same shape to rewriting: if the base resets each round, the 20% kill can
never fire again.
