# Part 8: output

**Audience:** the evaluating reader, and in particular anyone picking up a track.

Track J. Paper, datasheet, harness disclosure, artifact, and where any of it
would be submitted. The artifact someone else can re-run.

Part 8 of eight. The tracks table, the venue map, the sequencing and the
claim ladder are in [`RESEARCH_PROGRAMME.md`](../RESEARCH_PROGRAMME.md).
Headings below start at `###`, carried over from the split so that a track's
anchor is the one it had in the monolith.

---

The artifact someone else can re-run.

### Track J: write-up and release

Paper, datasheet, harness disclosure, artifact. The verdict vocabulary and the
promotion gate carry over: no skill enters `plugin/skills/` while carrying
`UNTESTED`, and `de check` enforces it rather than trusting anyone to remember.

#### Where it would be submitted

The 2x2 near the top of this document is an *experiment* venue map: which cell
of the design space a run lives in. This is the other kind of venue, and the two
share a word by accident.

NeurIPS renamed its Datasets & Benchmarks track to
[Evaluations & Datasets](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)
for 2026, and the rename is the substance rather than a relabelling. The call
scopes evaluation as the processes, tools, datasets and practices used to test,
audit and interpret systems, and it asks in as many words for work that
presents "negative results, critical analyses, and use-case-inspired
evaluations". Read that against [`STATUS.md`](../STATUS.md) and it describes what
this repository has actually produced rather than what it hopes to: nulls
reported as nulls, a corpus a word counter solved before any model saw it, a run
published as void, and a citation withdrawn by the measurement that was supposed
to support it.

Four things the call asks for, read off it first-hand on 2026-08-20:

- Datasets documented in the Croissant machine-readable format, with "both core
  and Responsible AI (RAI) fields". **Nothing here emits Croissant**, and this
  is the only one of the four that is new work.
- Datasets and code "hosted on a dedicated ML hosting site (Dataverse, Kaggle,
  Hugging Face, or OpenML)". Publishing the corpus to the Hub is already
  scheduled for a different reason, so this arrives on its own.
- Reachable at submission time "without a personal request to the PI". A public
  Hub repository satisfies that; a link that needs an invitation does not.
- Abstract by 2026-05-04, paper by 2026-05-06.

**That last date has passed.** So the target is the 2027 call, which is not
published, and the deadlines above are recorded as what the 2026 call said
rather than as dates to work towards. Nothing in the programme is blocked on
this, and the runway is long enough that treating it as a constraint would be
inventing one. What it adds to work already planned is a Croissant emitter
beside [`EVAL_SET_DATASHEET.md`](../EVAL_SET_DATASHEET.md), generated from the
datasheet so the two cannot disagree, which is a serialiser rather than a
measurement.

What a venue does not change: the verdict vocabulary. Submitting a paper does
not promote a skill out of `UNTESTED`, and [`SCORECARD.md`](../../SCORECARD.md)
stays the record of what has been shown either way.
