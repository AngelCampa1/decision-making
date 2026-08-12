# `p03`, and the only row in the table that says "advice"

**2026-08-12.** The third item flagged in
[the cascade/timing entry](2026-08-12-cascade-and-timing-collide-in-the-table.md)
as worth reading rather than counting. Reading it changes the shape of the
problem: it is **not** the same defect as `p06`.

## The item

**`p03`** — *"Six people replied to my question in the group chat and they
disagree. What should I actually do?"* Labelled `ledger`.

| repeat | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| routed to | `ledger` | `fit` | *none* | `fit` | `fit` |

Fires 5/5. Routes right 1/5.

## This one is a real routing failure, and `p06` was not

The distinction matters because it changes who owns the fix.

`p06` (*pay cut, age 54, pension vests in three years*) had **two defensible
routes**: `fit` reads correctly and so does `cascade`, off the table's own
wording. That is a trigger-set defect and a maintainer decision.

`p03` does not. Read `fit`'s row against it:

> *The advice may be generically right and wrong for this person* → `fit.md`

**`fit` needs a fact about the person that would overturn the generic answer, and
`p03` states none.** There is no visa, no interest-free family loan, no vesting
date — nothing about the asker at all beyond that six people disagreed. So `fit`
is not a defensible reading here. Only `ledger` is:

> *A pile of context arrived and it is unclear what the answer turns on* →
> `ledger.md`

Six disagreeing replies is exactly a pile whose load-bearing part is unknown.

## The mechanism, and it is the same *kind* of defect as cascade/timing

`p03`'s pile is made of **advice**. And **"advice" appears in exactly one row of
the router table — `fit`'s.** `ledger`'s row says "a pile of context" and never
says what the pile can be made of.

So a salient content word in one row pulls a case that belongs to another. That
is structurally the same failure as `cascade`/`timing`, where "the order" and
"when" collide: in both, the router is matching on a surface term rather than on
the condition the row is actually stating.

**Stated but not applied**, on the same grounds as before — this is an L6 variant
candidate, and editing the table today would tune it against the run that found
the problem:

> `ledger`'s row should say what a pile can be made of — messages, documents,
> search results, **and advice** — so that "the pile is advice" stops being a
> reason to leave the row.

Note that `SKILL.md`'s own `description` field already lists pile *kinds* ("a
long thread, pasted logs, search results, several documents, a channel
backlog"), and the router table drops all of them. The description does the work
of firing; the table does the work of routing; only the first was written with
that list in it.

## What this does to the tally

Of the three items the router gets wrong most often, the causes are now three
different things:

| item | routed | cause |
|---|---|---|
| `p06` | never right | **trigger-set defect** — two routes defensible off the table |
| `p07` | 1/5 | **table defect** — `cascade`/`timing` collide on order/when |
| `p03` | 1/5 | **table defect** — "advice" appears only in `fit`'s row |

Two of three are the table, and both table defects are the same mechanism:
**a row is matched on a word it contains rather than on the condition it
states.** That is one hypothesis with two instances, which is a better L6 input
than three separate patches.

None of this is scoreable on the current set — see
[the power check](2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).
Fourteen routed items cannot reject at any effect size worth having, so these go
into Track L as authored variants awaiting a corpus, not as fixes awaiting a
re-run.

## `p04`, read in passing

**`p04`** — *"Everyone says build six months of runway before quitting. My visa
is tied to my employer. Should I still wait?"* Labelled `fit`, routed
`fit`/`cascade`/`fit`/`timing`/`fit`. **3/5 and the errors do not repeat**, which
is the signature of noise rather than of a defect. It contains "wait" and "still"
and drifted to `timing` once; it contains a consequence of quitting and drifted
to `cascade` once. Left alone.
