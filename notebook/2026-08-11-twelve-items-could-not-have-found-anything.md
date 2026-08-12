# Twelve items could not have found anything

**2026-08-11.** The MDE the programme kept promising to compute. No model calls.

## The sentence this fixes

The programme's first kill condition reads: *Track A comes back flat **and the
MDE was below the effect the literature reports***. It then says the second half
was missing from an earlier draft, and calls that "the most dangerous sentence in
the document" — because without it, an underpowered null reads as a finding.

The MDE was still not computed. It is now, by `de power`, and the table is
regenerated rather than transcribed.

## The table

```
  n_pairs |  p_d=0.15  p_d=0.20  p_d=0.30  p_d=0.40  p_d=0.50
       12 |     n/a     n/a     n/a     n/a    46.5
       30 |     n/a    19.6    24.0    27.7    31.0
      100 |     9.5    11.0    13.5    15.6    17.4
      233 |     6.3     7.3     8.9    10.3    11.5
      527 |     4.2     4.8     5.9     6.8     7.6
      627 |     3.8     4.4     5.4     6.3     7.0
```

Percentage points, α=0.05, power=0.80, one-sided. `p_d` is swept rather than
chosen: discordance is unknown before a screening run, and Rule 1 says do not
invent a missing parameter.

## What it says

**At 12 items, four of five columns are `n/a`.** Not "hard to detect" — *no
effect of any size is detectable*. The one finite cell is **46.5pp**, which is
larger than the entire −39% the multi-turn paper reports.

The probe corpus could not have detected the effect it was built to detect. That
is not a near miss; it is a corpus that was incapable of producing evidence, and
it produced a null, and the null was written up and interpreted.

I want to be careful about how much this explains. The probe's null was
**admissibility 0.917 with 27/27 traps untaken** — that is a ceiling effect, not
a wide interval, and a ceiling is a real observation about the task being too
easy. The power arithmetic does not retract that. What it does retract is any
reading of the three nulls as evidence *against* the effect existing. They were
never able to be.

Combined with yesterday's finding that seven-eighths of the multi-turn effect
lives in the *spread* rather than the mean, the picture of the three dead corpora
is: too short, too easy, too few, and measured on the wrong statistic. Four
independent reasons, any one sufficient.

## What it fixes

**A1 is now well-powered, and by the vendored corpus rather than by argument.**
627 records minus the Unix-only `code` family is **527 usable pairs**:

- MDE **4.2–7.6pp** depending on discordance
- **8.4pp** at the stated design effect of 2.0
- against a literature effect of **−39%**

That is roughly a fivefold margin. **A flat A1 would now be a real result.** It
is the first time in this repository that a null would mean something, and it
arrived from adopting somebody else's instrument rather than from any cleverness
here.

## What it does not fix

**A2 is not covered and I nearly let it ride on A1's number.** A2 holds total
turns fixed while moving a decisive fact between first, middle and last. The
vendored corpus runs 3–12 turns, so A2 cannot use all 527. Subsetting to the
largest single shard-count stratum — 6 shards — gives **233 records, MDE
6.3–11.5pp**. Still comfortable, still a different number, and it must be stated
as its own rather than inherited.

A3, A4 and A5 have no item count yet because they have no corpus yet. Their MDEs
are not computable and are deliberately left blank rather than filled with A1's.

## Prediction

Registered before A1 runs, per the standing rule: **A1 reproduces a drop of more
than 20pp** between the single-turn and sharded settings on Haiku, i.e. more than
half the published −39%.

That is my sixth consecutive prediction in the direction of the experiment
working. The record of the previous five being wrong in that same direction is
the reason to write this one down rather than to trust it.

---

## Correction, same day: 527 was wrong. A1 is 315.

Written above: *"627 records minus the Unix-only `code` family is **527 usable
pairs**."* That is arithmetic on the wrong quantity, and I found it an hour later
while building the runner.

527 counts records that are not `code`. A **pair** additionally needs a
*full-setting* instruction to put opposite the sharded one — and I had silently
assumed that joining the shards reconstructs it. It does not. For one `database`
record:

- full: *"which countries' tv channels are playing some cartoon written by Todd
  Casey?"*
- shards joined: *"tv channels airing cartoons determine which countries these tv
  channels belong to ensure the tv channels are actively playing…"*

Those are not the same instruction in two deliveries. They are two different
instructions. Pairing them would have measured sharded delivery against **a third
condition I wrote myself**, and reported it as the published design — the exact
failure the vendored corpus was adopted to avoid, reintroduced one layer down.

The full instruction has to come from a named field, and the field differs per
family:

| Family | n | Field | Usable |
|---|---|---|---|
| `actions` | 105 | `fully_specified_question` | yes |
| `database` | 107 | `fully_specified_question` | yes |
| `math` | 103 | `question` | yes |
| `summary` | 92 | `query`, but the task also carries `documents` | **undecided** |
| `data2text` | 120 | none — the input is a table | no |
| `code` | 100 | split `prompt`/`question_content` | excluded anyway |

**A1 is 315 pairs.** MDE 5.4–9.9pp, or 7.6–13.9pp at design effect 2.0. Against
−39% the conclusion is unchanged: A1 is well-powered and a flat A1 would mean
something. The conclusion survived; the number did not, and the number was in a
document for an hour.

`summary` stays undecided rather than being folded in to recover 92 pairs.
Deciding it means deciding what the full instruction *is* for that task, and that
is a parameter, not a preference.

**What this says about the method.** Rule 1 is written as "never invent a missing
parameter", and I did not think I was inventing one — I thought I was reading a
count off a file I had already verified by hash. The invention was upstream of
the arithmetic, in an unexamined assumption about what a pair is. Verifying the
corpus bytes proved the corpus was authentic and proved nothing about whether my
design fit it.
