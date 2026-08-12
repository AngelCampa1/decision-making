# Prediction: one entry against four

**2026-08-12**, written and committed **before the run starts**. Track M4.

## What is being raced

`decision-making` ships as **one** description with four procedures behind a
router table. `CLAUDE.md` says plainly that this is an extrapolation:

> The published evidence sits at 202 skills; the choice here was made at four.
> Nobody has measured shadowing at n=4, and this repository has not either.
> […] one-entry-not-four is a judgement call wearing a citation.

This is the run that stops it being one.

**Arm `one`** — the shipped description. The model decides `fire` and then names
a `procedure`.

**Arm `four`** — the same four procedures as four separate tools. The model
decides `fire` and names a `tool`.

## Nothing in the four-skill arm is authored, and that is the design

The obvious way to build arm `four` is to write four descriptions, which varies
structure **and my prose** at once. M4's own text already refuses the historical
four-skill tree at `9a16b18` for exactly this reason.

So `decision_evals.unbundle` composes each description mechanically:

- **condition** and **product**, verbatim from that procedure's router-table row;
- **opener** and **exclusions**, verbatim from the bundle's own `description`,
  given to all four unchanged.

The four descriptions are the one description's parts, redistributed. A test
asserts that **no word appears in any composed description that is not already in
the bundle**, with one declared exception — the connective *"Produces"*, which is
identical across all four and so cannot differentiate them. If that test ever
fails, prose has been invented and the race is uninterpretable.

## What is deliberately not modelled

A real four-skill install also means four bodies and four sets of frontmatter.
The trigger instrument never sees a body — what is in context when a model
decides whether to fire is the description. **This measures the selection half of
shadowing and nothing else.**

Also: in arm `four`, firing and routing collapse into one act, because declining
to name a tool *is* declining to fire. That is not a defect of the harness, it is
what having four entries means.

## Predictions

Base rate 18/73 = 0.247. Both arms 73 cases, 5 repeats — four is the minimum from
ICC 0.741 and five is what the existing baseline used.

| # | Prediction | Band |
|---|---|---|
| 1 | Every call returns a parseable verdict | ≥ 98% |
| 2 | Arm `four` **precision** | 0.80–0.95 |
| 3 | Arm `four` **recall** | 0.80–0.95 |
| 4 | **False-positive rate is where the cost lands** | arm `four` FPR **> arm `one`'s 0.018** |
| 5 | Arm `four` routing accuracy | 0.55–0.80 |
| 6 | `x-n21` and `x-n22` still miss | both fire ≤ 1/5 in arm `four` |

**4 is the prediction that matters and it is the one the repository's own design
choice rests on.** Four overlapping descriptions should each look plausible for
a wider set of messages than the single scoped description does, so the failure
should appear as *firing when it should not* rather than as bad routing. If FPR
does not rise, the one-entry choice bought nothing measurable at n=4 and
`CLAUDE.md`'s block should say so.

**5 is where I would most like to be surprised.** Routing in arm `one` is
0.686 ± 0.108. There is a real argument that four separate descriptions route
*better*, because each names its own condition in its own entry rather than as
one row of a table the model has to read past three others to reach — and today's
two table defects (`cascade`/`timing` colliding on order/when, and "advice"
appearing only in `fit`'s row) are both defects **of the table**, which arm `four`
does not have.

## What this cannot show

**Nothing about n=202.** Four is four. A null here is evidence that shadowing has
not begun at four descriptions on this instrument, not evidence against the
published result.

**And routing cannot carry a verdict either way.** 14 routed items, `p_discordant`
0.157 from noise alone; the arithmetic is in
[the power check](2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).
Band 5 is registered as a **descriptive** band and no p-value will be computed on
it. Firing, at 73 items with 70/73 stable across five repeats, is the outcome
this run is powered for.

## Cost

73 cases × 5 repeats = **365 isolated calls**, one arm. Arm `one`'s five-repeat
baseline already exists at `results/decision-making/2026-08-12-40b6ba5/`, so only
the new arm runs.

## Where I expect to be wrong

**2 and 3.** I have put both at 0.80–0.95 by assuming arm `four` degrades from
arm `one`'s 0.942 / 0.878 rather than collapsing or holding. Every band I set
about a *second* arm today was wrong, three runs running, and each time because I
was predicting a measurement's behaviour rather than a model's. This one at least
reads the same object in both arms — the same 73 labels, the same JSON field —
which is the check that was missing from all three.
