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

## Result

Nine blind re-adjudications, 3 judges over the 3 rewritten turns, 0 unparseable,
`haiku`.

```
cases                 3
unanimous with key    1.000
contested (2-1 kept)  0
moved (2-1 against)   0
movement rate         0.000
```

All three came back 3-0 with the key. Over the 72 items as they now stand,
unanimity with the key is 0.917 and movement is 0.000, with Fleiss kappa 0.877.

**Cumulative disagreement over the 72 stays at 3/72 = 0.042**, which is the
figure the pre-registration said would be reported beside the post-rewrite one
and would not be reset by it. A round that rewrites until the judges agree can
always report 0.000, so the number that means something is the one counting
every disagreement these items have ever produced.

### The prediction, scored

| registered | actual |
|---|---|
| 2 or 3 of 3 agreeing, point estimate 3 | 3 of 3 |
| 0 labels moving, 1 inside the band | 0 |
| 9 calls | 9 |

**The "where I expect to be wrong" section was wrong, and wrong in the way that
was worth writing down.** It named `l24n1` as the item expected to survive the
rewrite still disputed, on the reasoning that a 241-word body about three people
who must agree before a deadline exerts decision pressure no closing sentence
can undo. `l24n1` came back unanimous.

The reasoning was sound and the conclusion drawn from it was not. The agent that
rewrote it, which never saw a judge's verdict, reported independently that no
arithmetic ask it could construct stayed clear of the decision reading, and that
what carried the item was a sentence conceding the choice: *I have given in and
said I will back my sister. The roof is going on and it is being let, so I am not
asking you to reopen that.* That is the shipped definition's own negative branch,
a task whose decision has already been made and stated. So the prediction was
right that the ask alone could not fix it, and wrong that nothing could.

### What the round changed beside the labels

Nothing moved a `should_fire`. The corpus text moved, so the answer key moves
with it, 5 to 6, and `datasets/triggers/corrections.jsonl` carries the line. The
reasoning is in the register entry and the bump is recorded as a choice rather
than a derivation, because no record on disk carries `set_version: 5` and
leaving it alone would have made nothing incomparable.

`matched:ask:type_token_ratio` fell from 3.03 to 2.91 null standard errors and
came off `corpus-baseline.txt`, which may only shrink. Three asks out of 330
items moved it. That is disclosed here and in the register, and it is not a
merit of the round: a corpus edit that turns a gate green is the mechanism this
repository has named as the source of four generations of leak, and the only
defence is that the rewrites were written to the shipped definition by agents
that never saw a judge's verdict or that file.

### One improvement on the 2026-08-18 method

That round replaced the disputed items' records in
`results/triggers/adjudication.jsonl`. This one appended the new verdicts and
left the originals in place, so the file now carries both what the judges said
about the turn as authored and what they said about the turn as rewritten. Both
readers of that file resolve a repeated `(case, judge)` slot last-wins, so the
appended verdicts are the live ones and the evidence for the rewrite is still
on disk rather than overwritten by it.
