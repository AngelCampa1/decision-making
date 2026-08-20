# Methods

**Audience:** the evaluating reader.

**What this is.** A single page describing how the work in this repository is
done, for a reader who wants to judge the method rather than run it.
[`PROTOCOL.md`](PROTOCOL.md) is the normative spec and stays the source of
truth: `paper/sections/method.tex` renders from it, not from here. This file is
the narrative version, and it adds one thing the spec does not: for each
technique, whether it has **actually run**.

That last column is the point. Most of what follows is ordinary good practice.
What is unusual is that the repository distinguishes, in writing and in code,
between a mechanism that exists and a mechanism that has fired. There are
entries below in both states.

Every result here is `UNTESTED`. [`../SCORECARD.md`](../SCORECARD.md) is empty
on purpose. What follows is not evidence that the skills work; it is the
machinery that stops anyone claiming they do.

---

## 1. Primary metrics are deterministic. Judges are secondary, and never primary

Model-graded evaluation is convenient and it drifts. The policy here, in
[`PROTOCOL.md`](PROTOCOL.md) §7, is that **no primary metric is ever a judge
score**. Firing accuracy, precision, recall, false-positive rate and routing
all come out of deterministic code. For every published run that is
`TriggerReport` and `evaluate_routing` in
[`../evals/src/decision_evals/triggers.py`](../evals/src/decision_evals/triggers.py),
driven from [`../scripts/run_triggers.py`](../scripts/run_triggers.py);
[`../evals/src/decision_evals/trigger_arms.py`](../evals/src/decision_evals/trigger_arms.py)
opens by saying it "computes and does not judge": nothing in that module
decides an answer is wrong. A second scorer,
[`../evals/src/decision_evals/scorers/answer.py`](../evals/src/decision_evals/scorers/answer.py),
serves the four-arm design of §4 and has therefore only ever run on the
calibration corpus.

**The judge policy is written and has not been exercised.** No judge panel has
run here. The only two multi-model procedures in the repository are the
three-instance adjudicator in §2, which has run, and a two-auditor distractor
filter, which has not; neither is a judge scoring model output. So what follows
is what `PROTOCOL.md` §7 *commits to*, not a description of something running:
a judge would emit a binary verdict plus a written critique rather than a
Likert rating; TPR and TNR would be reported separately, because blended
accuracy lets a judge that agrees with everything score well on a balanced set
while catching almost no real failures; and panels would stay small and
heterogeneous, since nine frontier judges from seven families supply "only
about 2 independent votes' worth of information" (arXiv:2605.29800). The
commitment to a robust aggregation estimator rather than a mean, on the grounds
that mean aggregation carries unbounded bias under any positive contamination
(arXiv:2606.30931), is a commitment with **no implementation in this
repository**: there is no such estimator in `stats/`.

**A zero is classified rather than assumed.** `ZeroCause` in that same scorer
module admits six causes (`agent_wrong`, `format_violation`, `infrastructure`,
`item_defect`, `verifier_defect`, `environment_leak`), and `Score` carries the
field as mandatory, though it accepts `None` for a scoring item and three of
the six need a person reading the trace. Splitting `item_defect` from
`verifier_defect` is the deliberate departure the module argues for: a bad item
and a bad checker have completely different fixes. It shares `answer.py`'s
scope, so no zero in a published trigger run has been through it. The runner's
preflight check
([`../evals/src/decision_evals/runner.py`](../evals/src/decision_evals/runner.py))
exists because `claude auth status` once reported a live session while every
call returned a revoked-token 401; without it a run records hundreds of auth
failures that look exactly like a model getting everything wrong.

---

## 2. The answer key is blind-adjudicated, not authored

The failure this defends against is specific and was measured: **21 of 21 scored
failures across three corpora turned out to be the answer key rather than the
model.** An eval whose labels are written by the person hoping for a result is
not an eval.

[`../scripts/adjudicate.py`](../scripts/adjudicate.py) relabels the corpus with
three independent model instances per item. Blinding is enforced rather than
intended. Each judge sees the turn and the skill's own abort conditions, and
does **not** see the maintainer's label, the reasoning behind it, the case id,
the band, the triple, or the other judges. It also does not see the skill
description under test. That is deliberate: a judge shown the description would
reproduce the description's reading of the turn instead of judging the turn.
Every call runs inside a fresh temporary working directory, and the isolation
receipt is asserted on every one of them.

The resolution rule is mechanical and was fixed before the run: unanimous
agreement keeps the label, two-of-three against moves it, and a two-to-one
split *agreeing* keeps it and records the item as contested. **A pre-registered
kill threshold retires the corpus if more than 20% of labels move**, checked by
a function rather than by anyone's judgement afterwards.

One more distinction the code makes and most pipelines do not: an unparseable
reply is a **missing measurement, not a disagreement**. Three judges of whom one
produced nothing is not the same evidence as two judges who agreed, so the
majority vote and the recorded rating shape are kept separately.

**This ran.** 261 of 261 items, three judges each, **zero unparseable**. Twelve
labels moved, ten negative to positive and two positive to negative, for
movement of **12/261 = 0.046 against the 0.20 kill**. Fleiss kappa 0.862,
Krippendorff alpha 0.862, unanimity 0.904, with per-band movement 0.042 / 0.042
/ 0.045 / 0.059, so no single band sits near the kill in a way the pooled
figure would hide. Agreement statistics are in
[`../evals/src/decision_evals/stats/agreement.py`](../evals/src/decision_evals/stats/agreement.py),
which reports kappa rather than raw agreement because at this corpus's class
balance two judges who have learned nothing at all still agree most of the
time.

**Kappa says how much the judges agree. It does not say how many judges this
is**, and the two get read as one number. Kohli (arXiv:2605.29800) finds nine
frontier judges from seven model families "effectively provide only about 2
independent votes' worth of information". Dividing the rater count by the design
effect of the agreement above puts this panel at **1.10 effective raters**:
three judges carrying roughly one judge's worth of information, and 1.07 at the
post-rewrite kappa of 0.898. `effective_raters` computes it, and the
adjudication report prints it beside the panel's composition, which here is one
model sampled three times.

That number is the weaker of the two claims available, and it is not Kohli's
cross-family figure. It cannot be: agreement because the item is clear and
agreement because the judges share a model are not separately identified from
ratings one model produced. What it rules out is the reading kappa alone
invites, that 0.862 across three judges is three independent confirmations.

**Two weaknesses.** The key is *model-labelled*: a bias the judges share with
the adjudicators is invisible to this check, and three instances bound that
without removing it. `PROTOCOL.md` §7 said *human-labelled* until 2026-08-18,
when everything waiting on a person came out of these plans. The change was
from an unavailable key to an available one, not from a better one to a worse
one, and it is recorded either way. Second, all twelve moves broke a corpus
invariant, so "apply the adjudicated labels" was not an executable instruction.
The resolution, on 2026-08-18, was to rewrite the twelve asks (by agents never
shown a judge's reasoning) and re-adjudicate blind: eleven of the twelve then
agreed with the key, `l15` was retired whole, corpus movement fell to 0.004,
and **no label moved**. The figures above are therefore the state on
2026-08-14. The corpus now stands at 330 items in 110 triples, after answer
key v5 added twenty-four on 2026-08-20 so that `council` and `hinge` have
positives to be correct about. Those twenty-four have not been adjudicated and
the figures here do not cover them. See
[`2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md`](../notebook/2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md).

---

## 3. The answer key is versioned, and comparing across versions is refused in code

On 2026-08-13 a single label moved from the positives to the negatives on a
decision that was **correct**. Every arm on disk was re-scored against the new
labels and recall rose on four of the five, by 3.5 to 5.1 points; on
`opener-only` it fell slightly, 0.956 to 0.953. The shipped skill gained five
points of recall that afternoon. Not one call was re-made. The checkpoints were
valid, every instrument check passed, the parse rate was 100%, and the number
moved in the direction an author would like.

Unlike the defects in §7, that was not a bug, which is what makes it worse:
nothing in a record distinguishes a label correction from a model result. So
the key carries a version, `set_version` is stamped into **every record at
write time**, and `label_versions_comparable` in `trigger_arms.py` refuses a
comparison that straddles a version boundary. A published run's README must
state its key version, and the gate cross-checks that line against the records
sitting beside it.

Three sibling guards make the same move on other axes: `models_comparable`
refuses comparing arms served by different model tiers, `venue_comparable`
refuses comparing a substituted system prompt against an appended one, and
`skill_versions_comparable` refuses comparing arms that saw different versions
of the skill itself. The treatment of a *missing* stamp differs between them,
and the reasoning is written down in each case: an absent key version defaults
to 1 because that is what those records are, while an absent model is unknown
rather than defaulted, because filling one in would be inventing a parameter.

**The gap, on record and still open:** these guards protect *comparisons*, not
*statements*. A single-arm number quoted from a stale checkpoint is refused by
nothing, and a single-arm number is what goes into a README.
[`STATUS.md`](STATUS.md) carries this as an open defect.

---

## 4. Controls, and instrument checks that run before results are believed

**The design, and the part of it that has not run.**
[`PROTOCOL.md`](PROTOCOL.md) §1 specifies four arms on the same items: **off**,
**on**, **placebo**, and **cot**. A skill that beats *off* but not *placebo* is
a length effect. A skill that does not beat *cot* is an expensive way to say
"think." The placebo
([`../skills/decision-making/placebo.md`](../skills/decision-making/placebo.md))
is token- and structure-matched filler, and the match is enforced rather than
eyeballed: `check_placebo_match` refuses a placebo of the wrong size or shape,
because an unmatched placebo is worse than none: it looks like a control while
silently failing to control.

**No published run has used the placebo or cot arm.** Every call on record is a
trigger measurement, comparing variants of the skill's *description* against
each other to ask whether the skill fires when it should. The four-arm
comparison is what a confirmation run would do, and no confirmation run has
happened. That describes a design and a written control, not a result: the
placebo exists, its matching guard runs in `de check`, and it has never stood
in for anything.

Two structural guards belong to that same unrun path, and they are design
rather than practice: the format contract is concatenated into every arm's
system prompt with no way to omit it, and the option menu lives in the
arm-independent rendering path, so neither can vary between arms by
construction. Both live in the module `calibrate.py` alone calls. The published
trigger runs build their prompts elsewhere, in
[`../scripts/run_triggers.py`](../scripts/run_triggers.py), and are not
governed by either.

**The standing rule:** *an estimator that cannot return a non-zero value is not
a measurement, and it does not announce itself.* Two defects on 2026-08-12 each
produced a clean run, a full checkpoint and a plausible zero: a parser
whitelist that discarded every tool name one arm could offer, and a routing
report grading those names against names the arm never offered. Nothing
crashed. Firing was correct in both. So before an outcome is believed, someone
checks that **some** possible response would have scored above zero for that
arm.

The standing negative controls, all in [`../scripts/`](../scripts/):

| Check | What it asks | Status |
|---|---|---|
| `canary_long.py` | Does the harness carry text at depth before any long-context claim is made? | **Ran**, verified to 101k tokens |
| `separability.py` | Can a trivial classifier tell real documents from padding? | **Ran**, four passes, and the first found the defect in the gate itself |
| `calibrate.py` | Is the corpus in the intended difficulty band? | **Ran**, one gate passed and one failed on a ceiling |
| `tree_smoke.py` | Does an ablation survive when surviving text is pinned? | **Ran**, and the unpinned first version was confounded |
| `probe_casefile.py` | Does a candidate venue produce any signal at all? | **Ran**, clean negative, venue closed |
| `realism_probe.py` | Does the corpus read as text a person sent? | **Ran**, descriptive only, no threshold |
| `audit_distractors.py` | Do two auditors unanimously agree a distractor is irrelevant? | **Built; never run**, with no record on disk, and the two auditors are one provider's models rather than independent ones |
| `pad.py` | Long-context padding assembler | **Built and unit-tested; never run as an experiment** |

`realism_probe.py` is worth reading for what it refuses to do. It declines to
set a pass threshold, because a falsifier must be run against a known-good case
before it may fail anything, and nothing in this repository is known to be a
real human message. A gate without that check is how a corpus gets tuned to a
judge, which is worse than no realism measurement at all. It reports a rate with
an interval and stops.

---

## 5. Pre-registration: two mechanisms, and only one has ever run

**The one that runs.** A dated prediction is committed to
[`../notebook/`](../notebook/) *before* the run. This is enforced, not trusted:
[`../evals/src/decision_evals/provenance.py`](../evals/src/decision_evals/provenance.py)
refuses a published run whose README does not name a prediction whose **first
commit is a git ancestor of the run's commit**. A prediction that cannot be
shown to predate its data is not evidence. The run directory name carries the
seven-character commit sha of the code that produced it, which is what makes the
ancestry check possible at all.

Predictions are appended, never edited. When one turns out wrong, the entry says
so.

Two qualifications on "enforced". `results/provenance-baseline.txt` exempts two
pre-convention runs by name, and that list may only shrink. And one published
run states in its own README that its prediction was authored before the first
call but **committed after it**, so for that run only the author's word places
the entry before the data, and the README says exactly that rather than letting
the gate's green stand in for it.

**The one that does not run.**
[`../evals/src/decision_evals/prereg.py`](../evals/src/decision_evals/prereg.py)
implements the six refusals `PROTOCOL.md` §3 enumerates: a registration that is
uncommitted or dirty; one whose commit is not an ancestor of HEAD or that
postdates existing results; a skill body whose hash changed after registration;
an analysis script whose hash changed; control accuracy outside the registered
difficulty band; and a projected cost over the registered budget. Hashing the
**analysis script** and not only the skill is the part most pre-registered ML
work leaves open.

It has never been called. It is scoped to the `confirm` arena and no
confirmation run has happened, so it is declared in
`[tool.decision-evals.unwired]` with the condition that would wire it. It
carries a 100% branch floor and no caller. `AGENTS.md` puts the consequence in
one line: **"A tested refusal with no caller is inert, and the gate reports
green either way."**

**A registered band names its estimator and its denominator, not just its
number.** At least seven pre-registration defects are on record, and the ledger
does not agree with itself about the count: two separate entries claim to be
the fifth, so the running total in `notebook/` is itself one of the things that
has drifted. The shapes are what matter. One asked for a statistic on task
families that had no correctness measure available, so it could not be scored
at all. One was written after its run had started. One launched 365 calls with
no bands. One named a measure without saying what it divided by, and happened
to fall inside the band either way, which is luck rather than method. One
re-derived an earlier run's thresholds from a later run's observed numbers
while citing the earlier run by name, which flipped the verdict.

**The ledger separates the ones found after the run from the ones found before
it**, and that distinction is worth more than the count. The first five were
all found after their calls were spent. Two later ones were caught beforehand
(a band that could not be reached at any corpus size the project would build,
and one flagged in the entry that registered it), and those are the cheapest on
the list, because nothing had been run yet. A third was *visible* before its
run and still not acted on, which is a different and worse case. Each defect
was recorded rather than dropped.

A related rule, learned the same way: **a recall band is set against the
observed per-item ceiling, not a round number.** One registered band demanded
16 of 17 positives when one of those items had never fired in any arm on any
version, a fact stated in that same prediction's own "where I expect to be
wrong" section.

---

## 6. Statistics chosen for the sample size that exists

Everything in
[`../evals/src/decision_evals/stats/`](../evals/src/decision_evals/stats/) is
exact or resampling-based rather than CLT-based, because at these item counts
the normal approximation is not reliable.

- **Templates, not items, are the resampling unit** (`cluster.py`). Items
  generated from one template are correlated, and treating them as independent
  produces intervals that are too narrow. The module also reports ICC, design
  effect and effective sample size, which mattered: one confirmatory run
  measured an ICC far below the value its own power arithmetic had assumed. That
  is conservative rather than optimistic, so it invalidated nothing, but the
  planning figure may not be reused, and the run's README says so.
- **Paired tests for paired designs** (`paired.py`): exact McNemar and a paired
  permutation test. Arm comparisons here are within-item, so the discordant
  counts and their split are reported alongside the p-value rather than the
  p-value alone. In one run two arms landed on identical precision to four
  decimal places while disagreeing on 33 of 258 items, split 16 to 17: matching
  aggregates there are cancellation, not equivalence.
- **Calibration goes through the Murphy decomposition** (`calibration.py`), so a
  "skill" that improves its Brier score by hedging every forecast toward the base
  rate is caught by the resolution term instead of scored as a win. Kernel-smoothed
  calibration error is the headline estimator, with binned ECE retained for
  comparability.
- **Repeat counts are derived, not chosen** (`reliability.py`). Measured ICC of
  0.83–0.85 said two repeats, not five, and that cut every subsequent arm by 60%.
  The same module reproduces the aptitude/unreliability split that shows most of
  a reported multi-turn collapse is scatter rather than lost capability
  (arXiv:2505.06120).
- **Coefficients refuse to return a number when one is undefined.**
  `DegenerateAgreementError` exists so an agreement statistic cannot silently
  come back as zero or NaN and be read as a finding.

The statistics package sits at 100% line and branch coverage, and roughly fifty
property-based tests assert the things that matter: the Murphy identity to
floating-point precision, cross-implementation agreement between this McNemar
and SciPy's, and the cluster bootstrap reducing **exactly** to an item bootstrap
when every cluster is a singleton.

**Benjamini–Hochberg is implemented, exported, property-tested, and nothing
calls it.** A reproducibility checklist box claiming multiplicity was
controlled had been ticked; it was un-ticked when this was found. The wiring
gate in §7 missed it because the *module* is import-reachable, and importable
is not used. It is at least the third tested function with no caller found
here; the ledger disagrees with itself on whether it is the third or the
fourth, and that disagreement is left visible rather than resolved by picking
the larger number.

---

## 7. Gates, not discipline

The organising claim of this repository is that **every confident wrong number
it has produced was caught by somebody checking, never by somebody being
careful.** So the checks are mechanical. `de check` runs nineteen steps at the
time of writing, and the count moves as gates are added; the ones that are about
method rather than lint:

| Step | Refuses | Added after |
|---|---|---|
| run provenance | a published run with no answer-key version, no prediction, or a prediction that does not predate it | predictions that could not be shown to predate their data |
| decision register | a commit touching the answer key or the shipped skill with no written entry | a label move being invisible in a checkpoint |
| label corrections | a version the answer key has reached that no line of `datasets/triggers/corrections.jsonl` accounts for | the register above proves a commit was explained in prose, which cannot be joined against a record |
| integrity wiring | a module with a coverage floor that no entry point can reach | two shipped modules tested to 100% and called by nothing |
| checkpoint label versions | two checkpoints disagreeing about the answer key with no re-scored bridge | §3 |
| citations | an arXiv identifier with no bib entry, or a claim number beside one with no verbatim source quote | three misattributed figures in one morning, all citing real papers |
| documentation | a `de` command, path or component named in the docs that does not exist | the README advertising two commands and a directory that never existed |
| site | a published build older than the files it renders | a site that renders this repo's markdown in place, so it cannot silently drift |
| skill lint | an `UNTESTED` skill in the shipped plugin; a verdict outside the vocabulary | a typo in a verdict is a false claim |
| trigger sets | a trigger set describing a skill that no longer exists | a set tested to 100% that nothing called |

Golden files belong in the same family and are enforced one level down, inside
the `pytest` step rather than as a step of their own: the generated corpus is
pinned byte-exact, and regenerating it takes `pytest --bless` so the diff lands
in review. A benchmark that changes silently makes every earlier number
incomparable with every later one.

Two design choices inside that table do real work. The citation gate is
**block-scoped**: it asks whether a claim number appears in the same markdown
block as a citation, and demands the bib entry carry the source sentence
verbatim. A presence check ("does this identifier exist?") would have caught
none of the three failures that motivated it. And the **baseline pattern**
appears seven times across the production modules: a named exemption list that
**may only shrink**, where `de check` fails when a listed item no longer has an
issue, because a baseline that does not shrink when work is done has stopped
measuring anything.

**What the gates cannot see, stated so nobody reads green as correct.** The
documentation gate checks whether a reference *resolves*, never whether the
sentence around it is *true*. It was added after a protocol section described,
in the present tense and with every path correct, a refusal that has never run.
The site gate proves the site was **built**, never that it was **pushed**; `de
check` is offline by design and cannot consult the deploy branch. A coverage
floor proves a module is tested, not that anything calls it. None of these
holes is a bug; each is a boundary, and each is written into the module that
has it.

---

## 8. How the work is run

Rules that are about process rather than statistics, each in
[`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md) because the failure it
prevents already happened here.

**Never invent a missing parameter.** Derive it, or record the choice as a
choice. A threshold nobody can trace is indistinguishable from a threshold
chosen to pass.

**A falsifier must be run against a known-good case before it may fail
anything.** Before a gate is allowed to kill a venue, construct a case that
should pass and confirm the gate passes it.

**Nothing is believed until it is confirmed.** Work is dispatched to
sub-agents, every artefact goes to a different agent whose brief is to break it
rather than approve it, and a result is a hypothesis until an independent agent
re-derives it from the raw records. The rule is that a reviewer returning
"looks good" has not run the task. Three published runs record an independent
re-derivation, and they are not equivalent: one re-derived every figure with
its own loading and counting code and named three adopted objections; one
re-derived through the repository's own estimators and named three; one wrote
its own parser and its own interval implementation but recorded no adopted
objection. Only the first satisfies every condition, and separating them is the
point: "independently confirmed" is not one thing.

**Corrections are appended, never rewritten.** History is the pre-registration
evidence, so a wrong number in a commit message is corrected in the ledger
rather than by amending the commit. [`STATUS.md`](STATUS.md) records its own
summary line drifting three times, always in the direction of claiming more than
the tables beneath it held, and says the lesson "was recorded and not learned."
A published run's README carries an in-place downgrade of its own earlier claim.
[`HARNESS_DISCLOSURE.md`](HARNESS_DISCLOSURE.md) deletes a citation of its own.

Runs are also checkpointed and resumable, appended to JSONL after every call,
with completed keys read back on restart. Arms interleave per item rather than
running in blocks, so arm is not confounded with model drift or quota state.
Isolation flags are prepended to every call with no way to switch them off,
after the measured finding that a planted instruction file is still injected
when the system prompt is fully replaced: **replacing the system prompt is not
an isolation mechanism.**

---

## 9. What has actually been shown

Nothing here measures whether a decision skill improves a decision. Every
number on record measures something upstream: whether a skill **fires** when it
should, which decides whether it is worth having installed at all. The section
is short, and keeping that answer legible is the job.

**And as of 2026-08-19, none of it measures the skill that ships.** Two
procedures were added that day, which rewrote the `description` field the
measurements are made against. Ten description arms had been run against the
old string, the last six of them over 3,096 calls, and the decision register
states the consequence without softening it: *"Not one of them describes the
string that now ships. No number anywhere in this repository may be presented
as a measurement of the current description, and the six-arm table in
`docs/STATUS.md` and `docs/RESEARCH_PROGRAMME.md` is from today a historical
comparison between description forms at a fixed procedure set."* The internal
comparisons survive, since every arm saw the same items. The external one does
not. Everything below is a comparison between description *forms* at a fixed
procedure set, which is a narrower claim than it was the day before. Read
[`DECISIONS.md`](DECISIONS.md) before quoting any of it.

The through-line as [`../README.md`](../README.md) states it, at the point it
was written:

> Five independent manipulations of a skill description, covering structure,
> content, entry count and composition twice, and not one moved how well it
> discriminates. Every one moved only where it sits on the precision/recall
> frontier.

Two findings cut against what this repository originally claimed. **Skill
shadowing did not appear at four entries**: one bundled entry and four separate
ones were indistinguishable on firing accuracy, 0.956 against 0.951, paired
Wilcoxon p = 0.83, so the 202-skill shadowing result (arXiv:2605.24050) may no
longer be cited as though it reached down to four. And **the corpus behind
every one of those numbers was 89% solvable by counting words**: turn length
alone separated the labels well enough that a bare "fire if long" rule beat
most of what the arms were competing over. Track N rebuilt it, and on the
rebuilt corpus the best shortcut is a depth-2 stump at 0.7054 against a 0.6667
baseline.

One published run is **void** and answers nothing: 70 of its 516 responses were
unparseable against a void condition registered in advance, and no accuracy,
precision, recall or false-positive rate is computed from it anywhere. Recovering
decisions by re-reading the prose would be post-hoc scoring of a voided run
against a rule invented after seeing it.

[`STATUS.md`](STATUS.md) is the ledger: every run, what it showed, and the
measurements caught being broken. That last count is around eleven and the
ledger contradicts itself about it in two places, which is fitting. What holds
across them is that **none was caught by anything failing**: no crash, no red
test. Almost all share the same shape: a clean run, a full checkpoint, and a
plausible number. Two sit outside that shape rather than outside the rule: one
surfaced through adversarial review of a run that had already voided on its own
parse-rate condition, and one was found in a module rather than in a run at
all.

And the bottom line, unchanged: [`../SCORECARD.md`](../SCORECARD.md) reads
**proven: 0**.

---

## Where to look next

| Question | File |
|---|---|
| The normative spec, versioned | [`PROTOCOL.md`](PROTOCOL.md) |
| What is wrong with the harness, statistics, datasets and judges | [`LIMITATIONS.md`](LIMITATIONS.md) |
| Every run and what it showed | [`STATUS.md`](STATUS.md) |
| What may be publicly claimed, and the verdict vocabulary | [`../SCORECARD.md`](../SCORECARD.md) |
| The corpus, as a datasheet | [`EVAL_SET_DATASHEET.md`](EVAL_SET_DATASHEET.md) |
| The harness configuration, disclosed | [`HARNESS_DISCLOSURE.md`](HARNESS_DISCLOSURE.md) |
| The literature this is built against | [`RELATED_WORK.md`](RELATED_WORK.md) |
| How the work is run | [`AUTONOMOUS_WORK_ORDER.md`](AUTONOMOUS_WORK_ORDER.md) |
