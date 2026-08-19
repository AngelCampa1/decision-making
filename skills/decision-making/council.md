# Council

Most decisions have a position that occurred to you first, with an unfair
advantage: everything after it gets measured against a frame it did not choose.
When two or three positions are defensible, the risk is not missing the right
one — it is mistaking whichever got argued first for having decided.

Sell the company or keep building it. Both have a real case behind them.
Argue only the one you lean toward and the other never gets made — different
from having been considered and rejected.

## Abort if

- Only one position is defensible; the other would be invented to be knocked
  down.
- It is small, reversible, and one pass of judgement covers it.
- The work is creative or exploratory rather than a decision.

## Step 1 — Name the positions, before arguing any of them

State every position a reasonable, informed person could hold — not the one
you lean toward plus a foil built to lose. Two is normal, three the ceiling.
Name each in one sentence, as a claim about what to do.

If only one position survives, stop — the abort condition above, discovered
rather than assumed.

## Step 2 — Argue each on its own strongest terms

For every position, build the case the way the person who holds it would —
not a summary, the strongest version. State what has to be true for it to be
right, and what it prioritizes over the alternatives. A thin case for the
position you never meant to pick fails the same way as skipping it.

## Step 3 — Cross-examine

Put the positions against each other, one pair at a time. Name the fact or
priority the first needs and the second denies — the actual disagreement, not
a difference in tone. "Loyalty" is not one; "the acquirer's price beats last
year's valuation" is — it is checkable. Then ask which case stands once
contested.

## Output

```
POSITIONS
  A. <position> — the case for it, in one line
  B. <position> — the case for it, in one line

CROSS-EXAMINATION
  A needs / B denies: <the fact or priority actually in dispute>
  B needs / A denies: <the fact or priority actually in dispute>

SURVIVES
  <which case still stands once its premise was contested, and which did not>

THEREFORE
  <the decision, and the strongest objection to it that still stands>
```

If cross-examination does not separate them, say so — a tie that survived
argument is a finding, and silently picking one to fill the output is the
failure this exists to catch.
