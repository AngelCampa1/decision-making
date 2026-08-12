# `cascade` and `timing` collide in the router's own table

**2026-08-12.** Follow-up to
[the five-repeat run](2026-08-12-five-repeats-firing-is-stable-routing-is-not.md),
which found two items the router gets stably wrong. This reads them instead of
counting them.

## The two items

**`p07`** — *"I want to resign. I was also going to raise the safety complaint
with HR, and I haven't yet. Should I go ahead?"* Labelled `cascade`. Routed to
`timing` four times in five.

**`p06`** — *"Is it a mistake to take a pay cut for a smaller company? I'm 54 and
my pension vests in three years."* Labelled `fit`. Routed to `cascade` twice and
`timing` three times. Never right.

## `p07` exposes a defect in the table, and it is visible without the data

Here are the two rows, as `SKILL.md` ships them:

| What is hard | Read | What it produces |
|---|---|---|
| The action looks fine and the worry is what it starts, or what it spends | `cascade.md` | the chain, what it forecloses, **and the order** |
| The direction is settled and the question is **when** | `timing.md` | the undo price, the real deadline, what waiting buys |

**`cascade` claims "the order" and `timing` claims "when".** In ordinary use those
are the same idea. A model told that one procedure handles ordering and another
handles timing has been given a distinction that does not exist in the language,
and `p07` is exactly the case that lands on the seam: resigning before raising
the complaint destroys the protection, so it is a question about *sequence*,
which the table files under both.

This is worth stating carefully. **It is not a conclusion drawn from the failure
rate** — the collision is legible in the table's own two sentences and would have
been legible before any run. The run is what made me read them.

The distinction the table is reaching for is real: `cascade` is about *what an
action sets off*, `timing` is about *whether to act now or later on an action
already chosen*. `p07` is a cascade question because the direction is not settled
— they are asking whether to go ahead at all. The table does not say that
crisply, and `timing`'s own row nearly does ("the direction is settled") while
`cascade`'s row does not mention that the direction is still open.

## `p06` is an ambiguous item, and I am not the one who should relabel it

Read against the table, **two routes are defensible**:

- `fit` — the generic answer (*a pay cut for a smaller company is fine if the
  upside is there*) is wrong for a 54-year-old three years from vesting. That is
  the fit row exactly.
- `cascade` — the pension is *what the move spends*. That is the cascade row
  exactly.

The model chose `cascade` twice and `timing` three times. `timing` is wrong by the
table — the direction is not settled — but `cascade` is arguably as good as my
label.

**So this is at least partly a trigger-set defect, and it must not be fixed by
me, now.** Relabelling the item I just watched fail is selection on the outcome,
the same mistake I caught myself making with `x-n21`/`x-n22` this morning. If the
set is to allow multiple acceptable routes per case, that decision has to cover
**all fourteen** routed cases and be made by someone who has not seen which two
failed.

## What I am not doing

**Not editing the router table.** The collision is real and the fix is obvious —
give `cascade` the "direction not yet settled" clause that `timing` already
carries — and making that edit today would be tuning the skill against the
measurement that motivated it. That is what Track L exists for: author variants,
pre-register the comparison, and replicate the winner on a holdout the variant
never saw.

Writing the fix down here without applying it is the point. It is a hypothesis
with a mechanism, which is a better input to Track L than a number.

## For the maintainer

1. **`p06`'s label.** `fit` or `cascade` — both read correctly off the table.
   Needs a set-wide re-audit, not a patch to one item.
2. **The table's `order`/`when` overlap.** A Track L variant, not an edit.
3. `p03` (routed `ledger`, went `fit` three times of five) is the third case
   worth reading and has not been read yet.
