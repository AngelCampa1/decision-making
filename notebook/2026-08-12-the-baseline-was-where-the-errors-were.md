# The baseline was where the errors were

**2026-08-12.** Track K5. Eight papers fetched and read, first-hand, because
they were the eight baselined identifiers that assert a number.

## Result

| Paper | What we said | What it says |
|---|---|---|
| 2604.27891 | 11.5/24, 0.5/9, 5/17 | **exact** |
| 2606.08878 | 17.2% average, best 62.0%, Opus 4.8 weak | **exact** |
| 2503.13657 | 14 modes, 1600+ traces, κ=0.88 | **exact** |
| 2305.14975 | ~50% ECE reduction | relative 50% — fair |
| 2601.10338 | 26.1% of sampled skills | **exact** |
| 2601.20404 | −20.27% mean wall-clock | abstract gives **medians** (−28.64%); the means are unverified |
| 2605.31408 | 86 tasks, 11 domains | **30 tasks, 2 models** |
| 2606.29718 | context rot 30–50% | **the figure is not in the paper** |

Six survive. Two do not, and neither is the kind of error a presence check finds:
both identifiers resolve, both papers are real, both are on the subject they were
cited for.

## Xu & Wu is not the size we said it was

"86 tasks, 11 domains" is the scale of **SkillsBench**, roughly — and SkillsBench
is 87 tasks and 8 domains, so even the borrowed figure was wrong. Two papers
conflated, and the direction is the tell: it made the smaller paper look larger.

The number that actually matters survived. **+18 to +36pp** in `CLAUDE.md` and
`AGENTS.md` is the union of the two models' ranges (18.0–26.0 DeepSeek,
26.7–36.0 GPT-5.5) and is correct as stated.

One thing to carry forward: the granularity result is usually summarised here as
"+0.7pp, intervals crossing zero". The other model's figure is **−6.7pp**, which
is the larger of the two, and dropping it makes "minimal" sound better
established than it is. The paper's own word is *model-dependent*.

## The context-rot number does not exist

`arXiv:2606.29718` was cited three times for "context rot is documented at 30–50%
in long-horizon settings". It is not in the abstract, was not found in the PDF,
and appears in no secondary summary of the paper.

What the paper establishes is a mechanism, and a good one: **premature
termination** — models giving up, or answering uncertainly, long before the
context window is full, at a rate positively correlated with context length,
across four flagship models and three search benchmarks. Its own headline figure
is a 2.6–4.9% *gain* from behaviour-aware filtering.

**That citation was load-bearing.** It is the sentence in the long-context plan
that justifies volume as the variable worth manipulating, in a document whose
whole argument is that every corpus built here has been too small. The mechanism
still motivates the plan — arguably better than a percentage would, since
premature termination is a specific failure a decision procedure could interrupt
— but the plan was reading as though the size of the effect had been established
somewhere, and it had not.

## What this says about the gate

The gate did not catch these. It could not: both identifiers were on the
baseline, and the baseline is exactly the list of citations the gate agrees not
to look at.

That was the right trade when it was built — 36 issues predating the rule, and
gating them retroactively would have blocked every commit until nineteen papers
were re-read. But it means **the backlog is not neutral debt, it is where the
known-unchecked claims are**, and two of the first eight read were wrong. The
prior on the remaining nineteen should be set accordingly. They assert no
numbers, which is the only reason they are cheaper.

The other half of the design did work. `check_citations` fails when a baselined
identifier no longer has an outstanding issue, so the eight could not be quietly
resolved without deleting their lines. 27 → 19, enforced.

## One thing I nearly got wrong

Un-baselining `2503.13657` makes the gate pass on a notebook line reading
"36.9% inter-agent misalignment" — a figure `RESEARCH_PROGRAMME.md` had already
retracted as not being in the paper. Adding a `quote` field to the bib entry
satisfies the rule while leaving the wrong number in place, because the gate
checks that a quote *exists*, not that it supports the number beside it.

So resolving a baseline entry has to mean reading what it was cited *for*, not
just what it is. The notebook entry carries a correction now.
