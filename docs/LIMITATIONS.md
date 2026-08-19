# Limitations

Written before any results exist, so it cannot be tuned to flatter them. We add
limitations here as we find them, and never trim one because it turned
inconvenient.

## The harness

The Claude Code CLI exposes no sampling parameters, so there is no temperature
control. We run ≥2 independent repeats per cell and report run-to-run variance
instead of claiming determinism. That is less of a loss than it sounds:
temperature 0 is not deterministic on hosted inference anyway, and a stated
variance is more honest than an assumed constant.

The budget is rate limits, not dollars. Every call runs on a Claude Max
subscription; there is no API key. The binding constraint is a rolling quota
rather than a spend cap, so runs are checkpointed and resumable across days, and
a confirmation run may span several sessions. Wall-clock timing is not
comparable across runs, so we do not report it as a metric.

Every dollar figure in this repository is notional. `total_cost_usd` is what the
same tokens would have cost on the API, not money anyone was charged. We report
it as a unit of account and as a proxy for quota burn, never as spend. A reader
comparing our per-item cost against an API-billed study is comparing a price to
a price, not a price to an invoice.

`--system-prompt` measures a clean injection, not daily use. Replacing the
system prompt removes the confounds (tools, other skills, settings, MCP), but
the result describes a model that has *only* the skill, which is not the model
anyone runs. The `in-situ` arm, which uses `--append-system-prompt`, tests the
realistic case. Where the two disagree, the disagreement is the finding, and the
in-situ number is the one that describes daily use.

Model identity is pinned only as far as the CLI reports it. `--output-format
json` returns a resolved model id, and every run config records it. That does
not protect against a silent server-side change within the same id. A verdict is
a claim about a model at a point in time, which is why the drift watch exists.

Claude Code is both the harness under study and the instrument. The
harness-variance literature says the scaffold dominates, and we are one specific
scaffold. Do not assume a result here transfers to a different agent harness
without re-measurement. That is precisely the claim arXiv:2605.23950 makes about
everyone else's results too.

## The statistics

N is small by ML standards. Subscription throughput caps the item count, and the
cluster design effect (~2.0 at 6 variants per template with ICC 0.2) cuts the
effective N roughly in half again. We use exact and resampling methods
throughout rather than the CLT for that reason (arXiv:2503.01747), but no method
recovers power that was never purchased. An underpowered comparison is reported
as `UNTESTED` or with an explicit minimum detectable effect, never as a null.

Multiplicity is controlled across pre-registered primaries only.
Benjamini-Hochberg at q = 0.10 covers the primary test of each pre-registered
skill. We label secondary and exploratory analyses as such and do not correct
them; they generate hypotheses and are not evidence.

Guards are uncorrected by design. They are one-sided non-inferiority tests in
the conservative direction, and correcting them would make it easier for a
harmful skill to pass. The asymmetry is deliberate, and it is written down here
so nobody reads it as an oversight.

The cluster bootstrap assumes templates are exchangeable. If template difficulty
tracks who wrote a template, or the order the templates were written in, the
interval is optimistic. We generate templates in mixed batches to reduce that,
which does not eliminate it.

## The datasets

Trigger corpus versions 1 through 3 are 89% solvable by counting words, and
every Track L and Track M number sits on one of them. Turn length alone
separates the positives from the negatives at AUC 0.850; a bare *"fire if ≥ 18
words"* rule scores 0.890 with no model involved. Both figures are label version
2.

Version 4 is not that corpus, and as of 2026-08-18 not every published number
sits on the old one. v4's best depth-2 stump over eight trivial features reads
0.7054 against a majority baseline of 0.6667, a corpus a trivial feature can
nudge rather than solve, and Track N6's three arms cleared it by 12 to 24
points. None of that retroactively rescues anything. Every figure in the rest of
this paragraph, and every L- and M-track conclusion drawn from them, still sits
on v1 through v3 and still carries the caveat in full. What changed is that the
sentence may no longer be written about *every* number here. The best
*description* arm on that key is `stakes-shown` at 0.9795, and the highest
firing accuracy on record at all is the `confidence` arm at 0.9863: the shipped
description with a probability also elicited, at one repeat rather than five. So
the range any arm was competing over is about nine points above a ruler, either
way.

This paragraph used to say six points, against a best arm of 0.956, and that was
wrong twice. 0.956 is the `full` arm at version 1, where the same ruler scores
0.877, so the comparison spanned a label revision, which is the move
`trigger_arms.label_versions_comparable` refuses. It was also the wrong arm. At
version 1 the best description arm was `no-opener` at 0.967, published without
an accuracy column and therefore never noticed, and `confidence` reached 0.973.
The rule this leaves behind is that *"the best arm ever measured scores X"*
cannot be written without naming the arm and the label version, because X is not
a property of the skill.

Two consequences, and both must be reported until the corpus is rebuilt:

- Internal validity survives. Every arm saw the same 73 turns, so the paired
  comparisons between arms are still the comparisons they claim to be.
- The absolute numbers do not travel, and the standing interpretation has a
  second reading. "Five independent manipulations and not one moved
  discrimination" is either a finding about skill descriptions or what a ceiling
  looks like, and this corpus cannot separate those.

Nobody audited the corpus for shortcuts before it was used, which makes it the
sixth entry in [`STATUS.md`](STATUS.md)'s table of measurements caught being
broken. The rebuild is [Track N](RESEARCH_PROGRAMME.md); the finding is
[here](../notebook/2026-08-13-the-corpus-is-89-percent-solved-by-counting-words.md).

The model tier is in no record. `--model` is a CLI default, so which tier
produced a given trigger number survives only as prose in a hand-written README.
Track N8.

We generate our own items, so we also own their biases. Public benchmarks are
contaminated, which is why we generate. The cost is item realism, and that cost
is now uncovered: the 10% human audit it rested on was retired on 2026-08-18,
along with every other step in these plans that waited on a person, and the
forced-choice probe replacing it cannot run until a human-written comparison
source clears the outside-data rule. Nothing measures realism today, and no
automatic gate would catch a template family that is subtly easier in the
treatment's favour. The distractor audit runs on the control arm only, which
prevents the most direct version of this leak but not all of it.

The distractor premise may be weaker than the design assumes. The 2026
GSM-Symbolic re-audit reduced the expected effect substantially, and its source
is a re-analysis rather than a peer-reviewed paper. If our own two-auditor
filter keeps a similarly small fraction, the flagship's effect may be too small
to detect at the N the budget supports. That outcome is a legitimate result, and
it is pre-registered as a possibility rather than a failure to work around.

Holdout secrecy is temporary and partial, and it got weaker on 2026-08-18. The
holdout regenerates from a seed kept in an uncommitted local file outside the
repository, not from a passphrase in anyone's head, because a secret only a
person can supply is a step that waits on a person. The cost is that any agent
with filesystem access can now read the seed, where a remembered passphrase was
not readable by one, so on this machine reconstruction no longer requires
guessing at all. We accept that rather than having missed it: the seed has to reach the
generator through an agent either way. Anyone who can run the generator with a
guessed seed could reconstruct items. Regeneration between runs is what manages
contamination, not secrecy, and that is the only reason the trade is affordable.

## The judges

Judge panels have a low effective sample size. Nine judges from seven families
are reported to yield a Kish n_eff of 2.18, 95% CI [2.07, 2.31]
(arXiv:2605.29800); the abstract states the result only as roughly two
independent votes' worth of information, and per that paper's own `refs.bib`
entry the 2.18 point estimate and its CI are unverified. Nobody has confirmed
them first-hand against the paper's tables, and a 2026-08-14 review of this
repository's own documentation found a claim to the contrary that did not hold
up (`docs/RELATED_WORK.md`). Until somebody reads the tables, quote the rounded
abstract form, "roughly two independent votes". That is what governs the design:
assume our three-judge panel carries roughly two independent votes, and it
reports its measured n_eff rather than its headcount. No primary metric is ever
a judge score.

Judges drift. Criteria drift (arXiv:2404.12272) means a judge calibrated once
does not stay calibrated. Recalibration is required whenever the pipeline or the
model changes, and a stale calibration blocks score emission. Between
recalibrations, though, judge-derived secondaries carry unquantified drift.

Local judge models are weaker. Ollama models supply genuine provider diversity
at zero cost, which is the active ingredient per RoPoLL, but they are small. We
buy diversity of failure mode at the price of individual judge quality, and that
trade is a design choice rather than a free win.

The distractor auditors are not independent, and Ollama is not installed. The
two-auditor filter is the gate the whole distractor claim rests on, and it
currently runs two Claude models of different capability: same trainer, same
data lineage, correlated failure modes. That is materially less independence
than the re-audit's methodology assumes, and it biases in the permissive
direction, because two correlated auditors agree more often than two independent
ones, so the filter admits more distractors than a genuinely independent pair
would. Read the acceptance rate as an upper bound on how strict this filter is.
The fix is to install Ollama and add a non-Claude auditor, and until then the
attrition number carries this caveat wherever anyone reports it.

## Scope

Five skills is what the budget supports, not what the space contains. The
framework survey in [`REJECTED.md`](REJECTED.md) records what was left out and
why. Several of those calls are defensible rather than certain, and the document
exists so a future run can overturn them cheaply.

Findings here are about decision-shaped tasks with computable ground truth. That
is a real restriction, and it is the same restriction SkillOpt has without
flagging it. Tasks whose quality is genuinely subjective are outside what this
harness can adjudicate, and any claim about them would rest on judge scores.
That is why judge scores are secondary.

A verdict is not a usability judgement. `NULL` means we have not shown a skill
works, not that it does not. The scorecard governs the public claim; it does not
govern what anyone installs.
