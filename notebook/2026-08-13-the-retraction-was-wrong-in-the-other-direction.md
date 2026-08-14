# The retraction was wrong in the other direction

**2026-08-13.** A finding that did not replicate, recorded here because the
record of what did not survive is the part that makes the record worth anything.

## What was believed

Earlier the same day, the citation gate was widened from line-scoped to a
markdown-block window and caught 27 citations across 19 papers where the old one
caught 0. Verifying those, a unit reported that **arXiv:2605.23950** — the paper
`docs/RELATED_WORK.md` calls "the premise of the whole project" — is a position
paper whose abstract contains no numerals, and that four figures this repository
attributed to it were not in it:

- aggregate harness/model variance ratio ≈ 7.8×
- a 3×3 factorial on 100 SWE-bench Verified tasks
- harness moves of 8.5–13 points versus model moves of 2.5–5 points
- six ranking reversals in nine comparisons

The figures were withdrawn from `docs/RELATED_WORK.md` and `docs/PROTOCOL.md` §9.
The unit reported, against itself, that the retraction had not propagated to
three other files, and named them. A follow-up unit was dispatched to finish the
propagation.

## What replicated, and what did not

**The abstract claim replicated exactly.** arXiv:2605.23950 is a position paper
and its abstract carries no numerals. Both units that fetched it agree.

**The absence claim did not replicate, and it was never actually made.** The
original entry said the figures were "*unverified*, not shown absent" and that
"they may well be its body's numbers". That was correct and appropriately
hedged. What failed was the step after it: the hedge was dropped in transit, and
"not in the abstract" was propagated as "not in the paper".

`arxiv.org/html/2605.23950v1` was fetched by two agents that did not share
context. **All four figures are in the body, verbatim, in §4.2 and Table 2**:

> "Changing the harness moves GLM-5.1 by 13.0 percentage points and GPT-5.4 and
> Kimi K2.6 by 8.5 points each." … "Changing the model within a fixed harness
> moves scores by only 3.0, 2.5, and 5.0 points for H₁, H₂, H₃." … "Aggregate
> HV̄/MV̄ ratio: 7.80×." … "Ranking reversal pairs: 6 out of 9
> model-pair/harness-pair comparisons."

They are the output of an experiment the authors ran themselves — three models
"tightly clustered on the LLM Stats coding leaderboard" × three harness
configurations, "on a difficulty-stratified 100-task subset of SWE-bench
Verified", two runs per cell.

**So the defect was citation hygiene, not fabrication.** A body figure was cited
as though the abstract carried it, in a repository whose standing rule is to cite
nothing you have not opened. The abstract had been opened; the paper had not.
That is a real defect and standing rule 5 catches it. The correct fix is to name
the section, not to delete the number. The figures are restored.

## Two further claims in the retraction were also wrong

Both were carried into the follow-up brief as established:

- **n_eff ≈ 2.18 in `docs/LIMITATIONS.md` was described as "one of the withdrawn
  2605.23950 figures".** It is not a 2605.23950 figure at all. It is
  **arXiv:2605.29800**'s, where it appears as a Kish effective sample size of
  2.18, 95% CI [2.07, 2.31], for nine judges from seven families — exactly what
  that file already said. The only defect was quoting a body point estimate where
  the abstract states the result in rounded form.
- **The 23.8-point swing in `docs/HARNESS_DISCLOSURE.md`** is **arXiv:2605.27922**'s
  and is in its body. Not withdrawn, not misattributed. The wording was loose in
  two ways now fixed: it is a best-versus-worst gap between two configurable
  harnesses (76.2 against 52.4), not an isolated variance component, and it is
  computed over the 5,088-trajectory factorial rather than "across 5,194
  trajectories".

**One of the three findings in the brief survived intact.** arXiv:2306.05685 does
say "over 80% agreement, the same level of agreement between humans"; the
repository's old "~85%, above human-human ~81%" both invented the numbers and
reversed the inequality. That retraction had already propagated completely — a
repository-wide grep found the claim surviving only inside correction notices and
the `refs.bib` note, which is where it belongs.

## What this changes

**A retraction that propagates is as dangerous as one that stalls, and this
repository had only worried about the second.** The framing that motivated the
follow-up unit was "a retraction that reached two files and stopped". The actual
risk on display was the opposite: a correctly-hedged "unverified" became an
unhedged "absent" in one hop, and would have deleted four correct, verbatim
figures from a third file had the next unit not opened the paper.

**Verification must record its locus.** The whole failure is compressed into the
difference between "not in the abstract" and "not in the paper". Every claim of
absence should say what was searched. `refs.bib` now carries a `quote_body`
field on this entry for exactly that reason.

**And a caveat was missing from the figures the whole time, in both directions.**
Nobody — not the original prose, not the retraction — noted that 7.80× is one
estimate from one 3×3 design on one task distribution with two runs per cell. The
figures are back with that caveat attached, which is the one thing about this
episode that leaves the repository better than it started.

## Where the proposed gate was rejected

The follow-up brief proposed a withdrawn-figures blocklist: a may-only-shrink
list that fails when a retracted number reappears anywhere in the living
documentation. **It was not built, and this episode is the argument against it.**
Standing rule 2 says a falsifier must be run against a known-good case before it
may fail anything. Run against today's known-good case, it fails: a blocklist
built yesterday would have contained 7.8, 6-of-9, the 100-task subset and the
8.5–13 range, and would today be blocking the build until somebody deleted four
correct figures — automating exactly the error that had to be undone by hand.
