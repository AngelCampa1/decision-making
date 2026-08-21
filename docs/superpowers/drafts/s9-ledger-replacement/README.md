# Track S9 — a replacement candidate for `ledger`, drafted and not shipped

**Audience:** the record.

**2026-08-14. Draft only.** Nothing in this directory is wired into
`skills/decision-making/`, `SKILL.md`'s router table, or
`datasets/triggers/`. The candidate procedure lives beside this file at
[`widen.md`](widen.md), marked `draft: true` in its own frontmatter so a stray
`cp` cannot promote it by accident.

**Why draft-only, restated so the constraint is not just asserted.**
`skills/` and `datasets/triggers/` are governed paths under
[`docs/DECISIONS.md`](../../../DECISIONS.md)'s rule: a change to either moves
numbers already published and needs a decision-register entry. The live
trigger corpus (`datasets/triggers/decision-making.yaml`, version 2, 73 items)
labels three positives `route: ledger` by name, and a second, larger corpus
under construction (`datasets/triggers/decision-making/{s,m,l,xl}.yaml`,
version 3, 261 items across 87 triples, not yet live) labels nineteen. Another
session was actively editing that corpus while this track ran. Swapping
`ledger` for anything is a corpus change, a router change, and an answer-key
version bump, all at once — not a thing to do inside a "draft a candidate"
task.

---

## 1. What `ledger.md` actually does, in its own terms

Read at
[`skills/decision-making/ledger.md`](../../../../skills/decision-making/ledger.md).
It is a triage procedure for a specific shape of failure: **a pile of
material has arrived — several sources, most of it true and on-topic — and it
is not obvious which parts of it actually bear on the decision.** Its abort
condition names the case it is *not* for explicitly: "fewer than four distinct
facts," "a lookup with one obvious source." Its three steps are verify item by
item ("what would it take for that item to matter"), discard and name why,
then answer from what survives. The worked example in the file's own header —
"it's raining in Paraguay" not becoming "bring a raincoat" in a decision about
a flight that touches neither city — is about **irrelevant-but-true material
crowding out what matters**, not about too few options being considered.

**Which corpus items route to it, and what they share.** I recounted directly
against both corpora rather than trusting the historical figure.

- **Live corpus (v2, governed, what `run_triggers.py` actually measures):**
  73 items, 3 positives labelled `route: ledger` (`p01`, `p02`, `p03`).
- **Draft corpus (v3, under construction, not yet live):** 261 items across
  87 triples (one positive + two hard negatives per triple). **19 of the 87
  triples route to `ledger`** — 3 in band S, 4 in M, 6 in L, 6 in XL. The
  task brief's figure of "10 ledger-labelled positives at 40 triples" is an
  earlier state of this same corpus mid-authoring; the current count, recounted
  directly with `grep` against all four band files rather than assumed, is 19
  of 87.

Reading all nineteen `v3` positives in full (they run from a one-line S-band
turn to an eleven-source, several-hundred-word XL turn) shows one shared
structure, present in every one without exception: **multiple named sources
that disagree or do not obviously connect, at least one deadline, and either
no question mark or a closing line that states the actual problem is not
knowing what the pile turns on.** Recurring closers across the set: *"I
genuinely could not tell you what the actual question is,"* *"what is this
really turning on?"*, *"which of these two do I take"* — followed immediately
by a sentence naming that the pile itself, not a choice between named options,
is the obstacle. Domains vary (money, career, relationships, one technical
RFC-review case) and stakes vary, but the shape is constant: **volume and
disagreement across sources, not a shortage of candidate actions.** Several of
the nineteen turns (`l01p`, `xl14p`, `xl08p`) explicitly *already contain* two
or more named options (two job offers, two academic posts, a cash settlement
versus a pension-sharing order) — the difficulty in those turns is which facts
in the pile decide between the options already on the table, not generating
more of them.

That last observation turns out to matter for section 3.

---

## 2. The draft candidate

[`widen.md`](widen.md) — "generate two or three candidate answers
independently before evaluating any of them, then compare, rather than
producing one answer and refining it." Same shape as the four shipped
procedures: an `Abort if`, three numbered steps, a fenced `Output` template.
It operationalises K6's Rank 2 candidate, "generate options concurrently,"
which is itself the narrow, evidenced slice of WRAP's "widen your options"
letter — not the whole four-step WRAP process, which K1/K2 still grades `none
located` after four search passes.

Placed under `docs/superpowers/drafts/`, not `skills/`, per the task
constraint. Its own frontmatter (`draft: true`, `not-shipped: true`) is a
second guard against accidental promotion, on top of its location.

---

## 3. What the evidence supports, and what it does not

The three sources are all already in `paper/refs.bib` with verbatim `quote`
fields from K2's fourth pass — reused here, nothing re-fetched, nothing
re-cited:

- **Basu & Savani (2017), *OBHDP* 139** (`basusavani2017`): seven lab
  experiments, ≈2,892 participants total. Presenting options **simultaneously
  rather than sequentially** raised the rate of choosing the objectively
  dominating option by 7–16 percentage points, every comparison significant
  (p ≤ .02, one at p < .0001). This is the strongest leg: multiple
  experiments, a real effect size, a clear operational definition of
  "optimal."
- **Dow et al. (2010), *ACM TOCHI* 17(4)** (`dow2010parallel`): n=33,
  between-subjects. Designers who produced multiple prototypes **in
  parallel** before feedback beat designers who iterated **serially**, on a
  real behavioural outcome (click-through, 445.0 vs 397.9 per million
  impressions, p<.05) and expert ratings (p<.05).
- **Hauschildt & Gemünden (1985), *EJOR* 22(2)** (`hauschildtgemunden1985`):
  correlational, not a trial — 83 real executive-board decisions at one firm,
  finding "alternative designing has a strong positive impact on decision
  quality."

**What this is evidence of, stated at the strength it earns and no further:**
*humans*, choosing among *already-described* options or producing *design
prototypes*, do better when the options are generated or presented
**concurrently** rather than **one after another and revised**. That is a
real, multiply-replicated, still-standing effect on the human side of the
question.

**What it is not evidence of, and this is the exact extrapolation this
repository keeps catching and naming when it catches it elsewhere:** it is
not evidence that *a language model*, prompted to generate candidate
recommendations, decides better when it generates them "concurrently"
(whatever that means for a single autoregressive pass, or even for a
sub-agent fan-out) rather than developing one answer and revising it. No
participant in any of the three studies was a language model. Basu & Savani's
manipulation is about how options are **presented to a human chooser** who is
picking among them; Dow et al.'s is about **how a human designer's own
work process** is structured over calendar time. Neither manipulates how a
reasoning process — human or model — internally generates candidates before
committing to one. Transplanting "concurrent beats sequential for a human
choosing or prototyping" onto "concurrent beats sequential for an LLM
generating recommendations in one context window or across sub-agents" is an
inference the cited papers do not make and were not designed to test.

This is stated plainly because K1/K2's own document names the general
failure mode by example — Goh et al.'s human trial "does not validate the
`fit` procedure" and "is not evidence about life decisions," it only
establishes "the axis is real and moves under assistance." The same
discipline applies here with less charity available: Goh et al. at least
studied people making decisions with LLM assistance. Basu & Savani, Dow et
al., and Hauschildt & Gemünden studied no LLM at all, in any role.

---

## 4. K4's test, applied

K4's test, closed today in `docs/DECISION_FRAMEWORKS.md`, is: a framework is
a skill candidate only if it targets a failure the model — not a human —
actually makes. K4's own table already ran this test against "widen your
options" and the verdict is on record, not something this draft is
introducing:

> "The LLM-side target — does the model default to a narrow, single-option
> answer — is still **assumed**, not documented; it is adjacent to the
> anchoring evidence above (a first option can anchor the same way a first
> hint does) but no study tests option-generation breadth directly."

I looked for anything that would upgrade this before drafting `widen.md` and
did not find one — no LLM-specific study of option-generation breadth is
cited anywhere in `docs/DECISION_FRAMEWORKS.md`, and nothing in this
repository's own Track A output touches it either (Track A's closed families,
`math` and `actions`, test multi-turn accuracy drop and an unmeasurable
object comparison, neither of which is about option breadth). So: **the
target failure is assumed, not documented, and this draft inherits that
label rather than resolving it.** `widen.md`'s own opening paragraph — "a
model asked to help decide tends to produce one answer and then improve it" —
is written as a claim about model behaviour and should be read as a
hypothesis stated in prose, not a finding. Nothing in this repository has
measured whether it is true.

**A second, independent problem section 1 already surfaced:** even granting
the hypothesis, it targets a *different* failure than `ledger` was built to
catch. `ledger`'s abort condition and its nineteen corpus positives are about
a glut of disagreeing sources obscuring what is load-bearing. `widen.md` is
about a shortage of generated candidates. Three of the nineteen `ledger`
positives (`l01p`, `xl08p`, `xl14p`) already contain two-plus fully specified
options in the turn itself — more options would not help there; picking the
right *fact* among the ones already given would. A model that already
produces several options but cannot tell which pasted fact decides between
them is not helped by `widen.md`, and a model buried in one pile with no
named options in it is not the case `widen.md`'s evidence base was measured
against either (Basu & Savani's participants were shown options that already
existed).

So this candidate fails K4's test on two independent grounds, not one: the
LLM-failure side is unmeasured, and separately, the specific failure it
targets does not match the failure the thing it would replace was built
to catch.

---

## 5. Migration cost

Costed against both corpora, on the counterfactual that `ledger` were retired
and `widen.md` took its slot in the router table.

**Live corpus (v2, governed, 73 items):**
- 3 positives (`p01`, `p02`, `p03`) currently score correct only when the
  model names `ledger`. All three are pile-of-sources turns with no
  option-generation content — under a `widen.md` router entry they would have
  no correct route at all, unless hand-relabelled to one of the remaining
  three procedures (`fit`, `cascade`, `timing`), none of which is a good fit
  for "several sources, unclear what's load-bearing" either. Realistically
  they would need to become **new negatives** (turns the retooled skill
  should not fire on) or be dropped, either of which is a corpus edit
  requiring a `docs/DECISIONS.md` entry per the standing rule.
- The corpus header already documents what one label move costs: moving a
  single item (`x-n21`) from positive to negative on 2026-08-13 "raised
  recall on every arm by 3 to 5 points... without any model being re-run."
  Three items moving is a larger version of exactly that.
- `de check`'s `trigger_arms.label_versions_comparable` rule would apply: a
  version bump (v2 → v3) makes every existing firing/routing number computed
  under v2 incomparable with anything measured after the swap, by design —
  which is the correct behaviour, but it means the M4/M5/L5 numbers currently
  in `docs/DECISION_FRAMEWORKS.md` and `SCORECARD.md` would need a footnote
  saying they no longer describe the live router.

**Draft corpus (v3, 261 items / 87 triples, not yet live, blind adjudication
— Track N3 — not yet run):**
- 19 triples, 57 items (19 positives + 38 hard negatives sharing their
  scenario), authored specifically around the pile-of-sources shape. These
  were written, in the corpus's own words, to test "the ledger problem," and
  several of the `why` fields name the ledger construct explicitly ("that is
  the ledger's job stated by the asker"). None of the 57 tests whether a
  model generates options narrowly. Retargeting `ledger`'s router slot to
  `widen.md` orphans this entire block — it does not become wrong, it
  becomes untested by anything, because it was never measuring the construct
  `widen.md` would need measured.
- Authoring 19-triple's worth of new material that actually tests narrow
  option generation (an LLM given a decision-shaped prompt, scored on whether
  it produces one option and elaborates it versus several and compares) is a
  fresh authoring task, not a relabel — the existing turns cannot be reused
  because their difficulty is contradiction-across-sources, not
  option-scarcity.
- This corpus has not been blind-adjudicated yet (the standing pre-registered
  kill is retirement above 20% of labels moving). Swapping the router target
  before adjudication would mean adjudicating labels for a construct
  (`ledger`) that might no longer be the one being shipped, which is wasted
  work in either direction.

**Router table (`SKILL.md`):** the four-row table's `ledger` row reads "A
pile of context arrived and it is unclear what the answer turns on." A
`widen.md` row would read something like "the answer looks like it will be
one option, elaborated" — a materially different trigger condition, which is
exactly the M4/M5 finding that router-table wording moves firing and routing
numbers. Swapping the *content* behind an unchanged *label* would be the
labelling defect CLAUDE.md warns about generally; swapping the *label* too
(so the router table drops "ledger" for something like "widen") makes the
corpus incompatibility explicit rather than silent, which is the lesser evil
if a swap is ever made.

**Bottom line: nothing currently published in `SCORECARD.md` breaks**,
because that table is empty — no skill has been measured on outcome quality
yet, only on firing (`docs/DECISION_FRAMEWORKS.md`'s own K3 section and
`CLAUDE.md`'s M4/M5/L5 figures). Those firing/routing figures **would** need
re-running under a new answer-key version, and the 57-item v3 block built for
`ledger` specifically would need to be either repurposed for a different
router slot or replaced outright.

---

## 6. Recommendation

**Not on this evidence.** Two independent reasons, either one sufficient on
its own:

1. **K4's test is failed on the LLM-failure axis.** The human evidence for
   concurrent option generation is real and multiply replicated; the claim
   that a language model's own unaided reasoning defaults to a narrow,
   single-option answer is, in K4's own words, `assumed`, not `documented`.
   Nothing produced today changes that. Shipping on an assumed failure mode
   is the exact pattern K1's founding critique names — "skills based on
   really nothing" — with better-dressed evidence attached to the wrong half
   of the claim.
2. **Even granting the assumption, the target does not match `ledger`'s
   job.** `ledger` catches a glut of disagreeing sources; `widen.md` would
   catch a shortage of generated options. The nineteen corpus items built to
   exercise `ledger` are not evidence for or against `widen.md`, in either
   direction, because they were never testing that construct. A "replacement"
   that shares a router slot with something it does not actually address is
   not a like-for-like swap — it is retiring one procedure and shipping an
   unrelated one under the old procedure's parking space.

**`ledger` being invented is real and stays true** — Track S7 and
`docs/DECISION_FRAMEWORKS.md`'s own audit table both say so, and nothing
here disputes it. But "the current procedure has no named framework behind
it" and "here is a framework-derived procedure that solves the same problem"
are different claims, and only the second licenses a swap. Today's evidence
supports the first half of that sentence for `ledger` and does not supply the
second half for `widen.md`.

**What would change this recommendation, stated so it is checkable rather
than just asserted:**
- An LLM-specific study — even a small one — showing a model's own unaided
  generation defaults to a single option that then gets refined, the way
  Vu et al. (arXiv:2412.06593) showed for anchoring and Sun & Li
  (arXiv:2505.02151) showed for overconfidence. That would move K4's grade
  from `assumed` to `documented` and remove reason 1.
- A corpus, authored fresh, that tests option-scarcity rather than
  source-glut — at which point `widen.md` would be a candidate for a *fifth*
  procedure, or a replacement for whichever existing procedure turns out to
  overlap most with narrow-option-generation failures (plausibly `fit`, since
  both are about a generic answer that may not hold), rather than for
  `ledger` specifically.

If a replacement for `ledger` is wanted on the evidence already in
`docs/DECISION_FRAMEWORKS.md`, the better-targeted candidate is not on this
track's list at all: K6's own Rank 1, **elicited confidence with scoring**,
has the strongest human effect in the whole catalogue and needs no new
corpus, because the calibration module already exists. It is not a `ledger`
replacement either — calibration is orthogonal to context triage — which is
itself the same lesson section 3 and 4 apply here: evidence strength and job
fit are two different questions, and K6's ranking answers only the first one.
