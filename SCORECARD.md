# Scorecard

**Audience:** the evaluating reader.

**What this is.** The register of what may be publicly claimed about each skill
here, and the gate that decides when a claim is allowed. A verdict governs the
public claim and says nothing about whether the skill is usable.

## What is enforced

The promotion gate has teeth. `de lint` refuses to let a skill carrying
`UNTESTED` or `WITHDRAWN` sit in `plugin/skills/`, and `de check` runs it. No
skill reaches the shipped plugin on an author's say-so.

Five further checks govern the method rather than the product. Four were added
on 2026-08-13 and the fifth on 2026-08-21, each after the failure it prevents
had already happened here, and each runs inside `de check` today.

| Check | What it refuses |
| --- | --- |
| Run provenance | A published run that does not state its answer-key version, or whose prediction cannot be shown by git ancestry to predate its data |
| Integrity wiring | A module carrying a coverage floor that no entry point reaches |
| Decision register | A change to the answer key or to the shipped skill with no written reason |
| Documentation | A `de` command or a repository path this repository does not have |
| Label adjudication | An answer key on disk, or a published run, naming an item with no three-judge blind adjudication record (`docs/METHODS.md` §2: one model sampled three times, 1.10 effective raters) |

Between them they decide whether a number is traceable. Whether it is *good* is
the confirmation run's job, and none of them can put a row in the table below.

## Verdict vocabulary

| Verdict | Meaning |
| --- | --- |
| `SHIP` | Beat control at q < 0.10 with every guard passing, placebo-controlled, and replicated on a freshly generated holdout |
| `PROVISIONAL` | Same, but not yet replicated |
| `NULL` | Confidence interval includes zero, or the effect is smaller than the pre-registered minimum detectable effect. Back to the workbench; ships as `experimental` |
| `HARMFUL` | Significantly worse, or a guard was violated. Off by default pending redesign |
| `UNTESTED` | No confirmation run. Cannot carry a proven badge |
| `WITHDRAWN` | The maintainer stopped using it. See the retirement rule below |

`NULL` means we have not shown it works, which is a different statement from
showing it does not.

## The retirement rule

The maintainer's daily use is the fastest signal this project has, and until now
it could only come out positive. A procedure that fires when it should not, or
that produces a worse answer than thinking directly, had no way of being
recorded as such. Evidence that cannot come out negative is not evidence, so
here is the failure condition.

**A procedure disabled for 14 consecutive days is marked `WITHDRAWN`.**

- The clock starts at a dated line in [`notebook/`](notebook/) saying the
  procedure was turned off and why. Turning it back on is another dated line.
- Fourteen days is chosen to survive a holiday and not to survive disinterest.
  It is a judgement, not a measurement, and it is written down before any
  procedure is near it so that it cannot be chosen to spare one.
- `WITHDRAWN` blocks the plugin exactly as `UNTESTED` does, and `de lint`
  enforces that rather than intention.
- It is reversible. A withdrawn procedure that is rewritten and used again
  returns to `UNTESTED`, and the notebook keeps both entries.

This is not a public claim about the procedure. It says the person who wrote it
stopped reaching for it, which is worth exactly as much as that sounds, and
considerably more than an evidence channel that only ever agrees with itself.

## Skills

| Skill | Verdict | Primary metric | Effect | 95% CI | p | q (BH) | N | Model | Run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _none yet_ | | | | | | | | | |

**proven: 0 / shipped: 0**

The table is empty because no confirmation run has happened. The harness is
being built first, deliberately. [`docs/PROTOCOL.md`](docs/PROTOCOL.md) carries
the standing methodology, and [`notebook/`](notebook/) the running research log.

## The caveat that used to qualify every number on record

Every trigger measurement made before 2026-08-18 ran on a corpus that is 89%
solvable by counting words (AUC 0.850 on turn length alone; a bare "fire if
≥ 18 words" rule scores 0.890 on the version 2 key, against the best arm on
that key, 0.9795 to 0.9863). That has not changed and does not get to change:
it still applies, in full, to every number computed on trigger corpus versions
1 through 3, which is every published Track L and Track M result. The paired
comparisons between arms on those versions remain valid; the absolute numbers
still do not travel, and "nothing moved discrimination" still has the second
reading that a corpus with nowhere to move explains a null as well as a real
effect does.

It can no longer be said of every number on record. Track N6 (2026-08-18) ran
on trigger corpus v4, 258 items in
`datasets/triggers/decision-making/index.yaml`, whose best depth-2 stump over
eight trivial features reads 0.7054 against a majority baseline of 0.6667. That
is a corpus a trivial feature can barely nudge, not one it solves. All three
arms N6 ran, `full`, `stakes-shown` and `opener-only`, cleared the stump by 12
to 24 points (accuracy 0.8295, 0.9360, 0.9477 against the 0.7054 bar).
[Run](results/decision-making/2026-08-18-e632659-n6-confirmatory/README.md).

What that is worth, stated so it is not overclaimed: one confirmatory run,
three arms, one corpus revision. It says this instrument, on this corpus, is
not solved by a trivial feature. It does not say the skill works, does not
touch `verdict: UNTESTED`, and does not fill in the table above. A trigger
measurement is about whether the skill fires, not about whether firing
produces a better decision, and nothing has measured the second question yet.

The rebuild is Track N; N7 is running as this is written, and the corpus's own gates
(Track N1) still apply to v4 going forward exactly as they applied to v1
through v3. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

None of this touches the table above, which is empty for a different and simpler
reason: no skill has been measured on whether it improves a decision at all.

## Corrections

The corrections this file has made to itself are recorded in
[`notebook/2026-08-20-the-corrections-move-out-of-the-shop-window.md`](notebook/2026-08-20-the-corrections-move-out-of-the-shop-window.md).
