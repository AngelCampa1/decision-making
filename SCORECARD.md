# Scorecard

Hand-maintained, and this line used to claim otherwise. It called the file a
*"generated artifact"* that you should *"not edit by hand"*, rebuilt by
`de report` from `results/**/summary.json`, with `de check` failing the build if
the committed copy differed. None of that was true: there is no `de report`
command, no `summary.json` under `results/`, and no scorecard step in
`de check`. The file had not changed since the initial commit, so nothing ever
tested the promise.

Correcting it rather than building the generator, because the table is still
empty. A generator written now would be written against a results schema no run
has produced. When the first confirmatory run lands, `de report` gets built and
this paragraph gets replaced by the guarantee it describes.

What *is* enforced today is the promotion gate: `de lint` refuses to let a skill
carrying `UNTESTED` or `WITHDRAWN` sit in `plugin/skills/`, and `de check` runs
it. That check is real and has teeth. The table below does not.

Four more checks over the method itself were added on 2026-08-13, each after the
failure it prevents had already happened here. Run provenance: a published run
must state its answer-key version and name a prediction that can be shown to
predate its data. Integrity wiring: a module with a coverage floor that no entry
point reaches is refused. The decision register: a change to the answer key or
the shipped skill needs a written reason. Documentation: a `de` command or path
that this repository does not have is refused. None of them can put a row in the
table below. They govern whether a number is *traceable*, not whether it is
*good*.

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
touch `verdict: UNTESTED`, and does not fill in the table below. A trigger
measurement is about whether the skill fires, not about whether firing
produces a better decision, and nothing has measured the second question yet.

The rebuild is Track N; N7 is running as this is written, and the corpus's own gates
(Track N1) still apply to v4 going forward exactly as they applied to v1
through v3. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

None of this touches the table below, which is empty for a different and simpler
reason: no skill has been measured on whether it improves a decision at all.

## Skills

| Skill | Verdict | Primary metric | Effect | 95% CI | p | q (BH) | N | Model | Run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _none yet_ | | | | | | | | | |

**proven: 0 / shipped: 0**

No skill has been evaluated yet. The harness is being built first, deliberately.
See [`docs/PROTOCOL.md`](docs/PROTOCOL.md) for the standing methodology and the
verdict vocabulary, and [`notebook/`](notebook/) for the running research log.

## Verdict vocabulary

| Verdict | Meaning |
| --- | --- |
| `SHIP` | Beat control at q < 0.10 with every guard passing, placebo-controlled, and replicated on a freshly generated holdout |
| `PROVISIONAL` | Same, but not yet replicated |
| `NULL` | Confidence interval includes zero, or the effect is smaller than the pre-registered minimum detectable effect. Back to the workbench; ships as `experimental` |
| `HARMFUL` | Significantly worse, or a guard was violated. Off by default pending redesign |
| `UNTESTED` | No confirmation run. Cannot carry a proven badge |
| `WITHDRAWN` | The maintainer stopped using it. See the retirement rule below |

A verdict governs the *public claim*, not whether a skill is usable. `NULL` means
we have not shown it works, which is not the same as showing it does not.

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
