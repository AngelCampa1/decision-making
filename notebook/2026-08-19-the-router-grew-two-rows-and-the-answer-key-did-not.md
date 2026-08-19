# The router grew two rows and the answer key did not

**2026-08-19.** Earlier today the shipped `skills/decision-making/SKILL.md`
router table went from four procedures to six — `council` and `hinge` joined
`ledger`, `fit`, `cascade` and `timing`. The answer key in `datasets/triggers/`
was not grown with it. Every `route:` label in the corpus still names one of the
original four.

That is a defect in the *estimator*, not a gap in the corpus, and it is worth
separating those two readings carefully because the first draft of this entry
did not.

## The structural half, which is just true

86 `route:` fields across `s`, `m`, `l` and `xl`: 19 `ledger`, 15 `fit`, 15
`cascade`, 12 `timing`, four two-element lists, 21 `~`. Zero `council`, zero
`hinge` — the six occurrences of the string "council" in the corpus are all the
British local-authority sense, sitting in turn text.

`evaluate_routing` scores `chosen in case.routes`. So a model that correctly
selects `council` on some turn cannot be credited: the answer can only increment
`incorrect`. Two of the six procedures the shipped description now advertises
are **wrong by construction**.

This is the fourth instance in this repository of *an estimator that cannot
return a non-zero value is not a measurement*, and the second caught in source
before any call was made. The three before it: the parser whitelist that
discarded every tool name an n=2 arm could offer; the routing report that graded
those names against names the arm never offered; and `PROCEDURES` hardcoding the
old four so a correct route to `council` could not be expressed. The last of
those was found this morning. This is the same edit's second consequence, one
layer further out — the vocabulary was fixed in the *instrument* and not in the
*key*.

`_check_routes` already enforced the other direction, and its docstring
describes this one in mirror image without noticing it applies both ways:

> a renamed procedure file would leave every routing label aimed at nothing
> **while every number kept computing** — accuracy would simply fall, and it
> would look like a model result.

Adding a procedure does exactly that from the other side.

## The half I got wrong

I wrote this up first as a block on N10, the 3,096-call re-measurement of the
six-procedure description. An adversarial review took that apart, and it was
right on three counts.

**N10 is not registered.** I have said "N10 registered, not started" more than
once today. `docs/RESEARCH_PROGRAMME.md` says `not started`, and says of the row
itself: *"This row states what must be registered; it does not register it."* No
notebook entry names N10. There is no registered routing readout for this
finding to invalidate, and "launch as registered" was never an available phrase.

**Routing is the secondary quantity and the template run does not report it.**
`datasets/triggers/decision-making.yaml` line 31: routing *"is a **secondary**
label: firing at all is the primary quantity."* N7 — N10's design template —
reports routing zero times, and its prediction entry registers no routing band.
Firing is untouched by any of this.

**The comparison I was afraid of is already refused mechanically.**
`trigger_arms.skill_versions_comparable` raises when one side of a comparison
stamps `skill_version` and the other does not, which is precisely the
six-against-four case. It landed in `6e2028c` — before I noticed this finding,
and by my own hand. I spent an hour arguing for a guard that was already there.

So the inference collapsed and the observation survived.

## What the size actually is

Not a rounding error, which is the one place the review came down on my side. 15
of 65 labelled items carry council- or hinge-shaped conditions. If every
currently-correct row on those flipped — the ceiling, not an estimate:

| arm | observed | ceiling | drop |
|---|---|---|---|
| stakes-shown | 0.792 | 0.631 | −16.2pp |
| full | 0.746 | 0.592 | −15.4pp |
| opener-only | 0.531 | 0.438 | −9.2pp |

The honest interval is 0 to about 16 points and nothing narrows it without the
run. Note also that the denominator is **65 items / 130 rows**, not the 86
labelled routes I first quoted — 86 counts the banded corpus, and the checkpoints
all record `labelled_rows=130`.

One thing cuts the other way: the 21 `route: ~` items are the council-shaped
ones — a family split two ways, a split team with one person deciding, a straight
choice between two named actions — and `evaluate_routing` skips unlabelled
positives. The corpus's sink for "several defensible positions" is already
outside the denominator.

## What now exists because of it

`_check_unreachable_procedures` in `evals/src/decision_evals/triggers.py`, wired
into both the top-level scan and the draft scan, so it covers both corpora. It
reports a procedure the router offers that no positive routes to.

It is a **finding**, not a hard issue — baselineable. Authoring positives for two
new procedures is a key change: a new `set_version`, and published numbers that
`label_versions_comparable` will refuse to compare across. That is a unit of work
with a governance cost, and a red gate on every commit until it is done would be
routed around within the day.

The key is `unreachable:council,hinge` — identity is the *set*, per the rule
`Finding` already documents, so a third unreachable procedure later produces a
different key and will not be covered by this baseline.

Standing rule 2, run before it was allowed to fail anything: silent on a corpus
covering all six; fires with `unreachable:fit` when one is missing; a different
key for a different set; silent on a version-2 corpus that labels no routes at
all. The known-good case was checked first, which is the whole point of the rule.

## What would make this wrong

- **The two new procedures turning out to be unreachable in practice too.** If no
  turn in the corpus would ever legitimately route to `council` or `hinge`, the
  gap is cosmetic and the right fix is dropping the rows, not authoring items.
  Nobody has read the 65 labelled turns against the two new router rows with that
  question in front of them; the 15-item flag above is keyword-shaped and was
  produced by an agent, not by a hand-read.
- **A run showing the leak rate is near zero.** The instrument now measures it —
  `default_procedures()` and `run_triggers._PROCEDURE_SCHEMA` both read the
  router table live, so a model can say `council`, it parses, and the name is
  stamped into every row. If the observed rate is ~0, the 16pp ceiling is a
  ceiling nobody approaches and this entry has overweighted it.
- **The baseline going stale in the wrong direction.** If the two entries stop
  matching because somebody edited the router table rather than the key, that is
  a real closure and the may-only-shrink rule will surface it — but it closes the
  finding without answering the question, and this line exists so that is visible
  when it happens.

## For the maintainer

Nothing here was measured. It is a source-level defect found before a run, a
check that now catches it, and a baseline entry saying so out loud. The
correction in the middle section matters more than the finding: I asserted a run
was registered when it was not, and argued for a guard I had already built. Both
were caught by an agent briefed to break the claim rather than to check it, which
is the third time today that has been the thing that worked.
