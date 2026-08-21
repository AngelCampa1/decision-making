# Decision register

**Every change to `datasets/triggers/`, `datasets/tailoring/` or `skills/`
needs an entry here, and `de check` refuses one that does not have it.**

Those paths are answer keys, or the product. A change to any of them moves
numbers that are already published: on 2026-08-13 one turn moved from the
positives to the negatives, recall rose 3 to 5 points on every arm on disk, and
**not one call was re-made**. That was a correct maintainer decision, and in a
JSONL file it is indistinguishable from a model result. The reasoning has to
live somewhere a reader of the numbers can reach.

The reasoning already existed — in commit bodies, and they are good ones. But
`git log` is not greppable by topic and is invisible to anyone reading `docs/`.
Commit trailers were considered as the store and rejected: commit messages here
cannot be amended, because the history *is* the pre-registration evidence, so a
trailer somebody forgot would be permanently unfixable. A file can be amended.

**Entries below the first heading are backfilled** from the commit bodies that
already carried the reasoning. They are transcriptions and point at the commit
for the full argument; nothing here was reconstructed from memory.

Format: `## <date> — <title>`, a `**Commits:**` line, then why.

---

## 2026-08-19 — The merge that carried `c55d4af` onto `item-analysis`

**Commits:** `b83384d`

A merge commit, and it is here because it is a governed commit like any other.
Against its first parent it changes one governed file:
`datasets/triggers/decision-making.yaml`'s header comment, arriving from
`c55d4af` on `main`. Against its second parent it carries this branch's
`datasets/triggers/decision-making/index.yaml` and `s.yaml` — `eb99e81`'s
annotation correction and ancestry block — onto the merged history.

**No label moves and no `set_version` bumps in either direction.** Every change
under a governed path in this commit is already explained by the entry for the
commit that made it: `eb99e81` and `c55d4af`, both below. Nothing computed from
the key changes and no published number is affected.

The entry exists because `_governed_commits` reads `git log` over the governed
paths and a merge that touches them is in that list, so the gate refuses
without it. That is the right behaviour rather than a gap to route around: a
merge is exactly where a label could move with no commit of its own to name,
and the register is where a reader would find out whether one did. This one
records that none did.

## 2026-08-20 — The key version says that labels moved, and nothing said which

**Commits:** `5d4c80c`

Adds `datasets/triggers/corrections.jsonl` and the `de check` step that keeps it
complete. Governed path, hence this entry.

This register is where the reasoning behind a label move lives, and that is the
right home for reasoning. It is the wrong home for a *record*: prose cannot be
joined against a checkpoint, and a reader holding a number and asking "which
label moved between the version this was scored on and the version I am reading
now" has to read the register end to end and hope. `set_version` answers whether
two runs are comparable. Nothing answered what changed.

One line per change, naming the item, both labels, the version moved into, the
date, the adjudicator, and the heading here that argued for it. The gate refuses
a version the corpus has reached that no line accounts for, and refuses a line
whose `decision` names no heading in this file.

**The backfill is three lines and it was read out of git.** The labels in
`datasets/triggers/decision-making.yaml` were parsed from the commits either
side of each bump and diffed, rather than transcribed from the entries below.
Exactly one `should_fire` has ever changed on an item present before and after:
`x-n21`, true to false, at `d43c490`, with the version stamp landing at
`903169c` and moving nothing further. Version 3 is `rebuilt` -- a different
corpus, no item id carrying across, nothing ever scored against it. Version 4 is
`none` -- an identity fix, and the rewrite round that followed changed twelve
asks and moved no label either.

That agrees with the entries below, which is the point of checking it a second
way rather than a reason not to have.

**What this cannot do.** It does not diff the corpus against its own history to
find a move nobody declared, so a line missing from *inside* a bump that was
otherwise declared is invisible to it. The version 2 to version 3 transition
replaced the corpus wholesale, so there is no item-level diff to take across it
even in principle. What the gate catches is an undeclared bump, which is the
failure that has happened here.

**The coupling this creates, named because it is deliberate.** Authoring
positives for `council` and `hinge` means a new key version, and this gate will
refuse the tree until a line here says what moved into it. That is the intended
cost of a version bump, and it is the reason the file exists.

## 2026-08-20 — `s13p`'s annotation named a directory no verdict has been written to

**Commits:** `8ce3ba0`

Closes the "Outstanding, 2026-08-19" note on the entry below, which is the only
thing that entry left standing.

The corrected `why` it describes cites its fourteen rows as being in
`results/triggers/`. No verdict file has ever been written there:
`run_triggers.py` writes `verdicts-<description>.jsonl` beside the run README,
so the seven v4 files sit under `results/decision-making/`, in the three runs
the entry below names. The copy in `docs/DECISIONS.md` was corrected in place at
the time; the copy in `datasets/triggers/decision-making/s.yaml` is a governed
path and was left for its own commit, which is this one.

The replacement wording points at the register rather than repeating the three
run directories inside the answer key. Two copies of a list is how the first
version of this annotation went wrong -- descent was recorded only in `why`
prose, prose cannot be diffed, and an annotation about the v2 item kept reading
as an annotation about the v4 one. A pointer has one home.

**No label moved, no turn text moved, and `set_version` stays at 4.** The same
distinction the entry below draws, for the same reason: an annotation correction
and a label move are the same size in a diff, and the register is where a reader
of the numbers finds out which one happened. Nothing already published is
invalidated by this.

**What still is not checked.** The documentation gate resolves backticked paths
in root `*.md` and `docs/*.md`, and this path was in neither -- it was in a YAML
file the gate does not read, and it survived a full `de check` for a day
alongside a register entry that named it. Widening the gate to corpus
annotations was considered and is not done here: `why` fields are prose about
runs that have happened, which is the same class as `notebook/` and
`results/**/README.md`, and those are excluded on purpose because a dated record
necessarily names things that later moved. So this one was caught by reading,
and the next one will be too.

## 2026-08-19 — `s13p` is not the turn `x-n22` was, and its annotation said it was

**Commits:** `eb99e81`

Corrects an annotation, and adds the block that would have caught it.

`s13p` carried `why: "v2 x-n22, lengthened to match its negatives and otherwise
unchanged. It has never fired in any arm on any version, and it stays, because
dropping it would raise recall for free on a maintainer's opinion."` The first
two sentences are false on the version 4 corpus. The v2 turn was "The build is
green. Can I deploy?" — seven words, and it fired in no arm on any version. The
v4 turn is "The build is green and the release notes are written. Can I deploy,
or is there something I'm missing?", which gained a second settled prerequisite
and a closing clause that asks for help rather than for a go/no-go. It fires in
11 of the 14 rows across the seven v4 verdict files — `verdicts-{full,opener-only,stakes-shown}.jsonl`
under `results/decision-making/2026-08-18-e632659-n6-confirmatory/`,
`verdicts-{no-exclusions,no-opener,stakes-named}.jsonl` under
`results/decision-making/2026-08-19-d52236a-n7-remaining-arms/`, and
`verdicts-in-situ.jsonl` under
`results/decision-making/2026-08-19-505b236-n9-in-situ-void/` — 0/2 only in the
in-situ arm.

**No label moved and no turn text changed.** The answer key stays at version 4,
`should_fire` stays true on the 2026-08-13 reasoning — a green build answers
whether the code compiles, not whether to ship — and nothing already published
is invalidated by this entry. That distinction is the reason this entry is short
and the reason it exists anyway: an annotation correction and a label move are
the same size in a diff, and the register is where a reader of the numbers finds
out which one happened.

`index.yaml` gains an `ancestry:` block — the thirteen v4 items that descend
from a v2 item, their ancestor, and whether the text is `verbatim`, `edited` or
`rewritten`. **Descent was recorded only inside `why` prose, and prose cannot be
diffed.** Nothing could ask "is `s13p` still the turn `x-n22` was?", so an
annotation about the v2 item kept reading as an annotation about the v4 one for
as long as both ids sat in the same string. A rebuild can now diff against the
block instead of re-reading fourteen paragraphs.

**Outstanding, 2026-08-19.** The replacement `why` this entry describes cites
those fourteen rows as being in `results/triggers/`, and no verdict file has
ever been written there — `run_triggers.py` writes `verdicts-<description>.jsonl`
beside the run README, and the paths are the seven named above. The same wrong
directory was written into this entry and is corrected in place here; the copy
in `datasets/triggers/decision-making/s.yaml` is a governed path and needs its
own commit and its own entry, so it is left standing and named here instead.

`load_trigger_set` ignores top-level keys it does not know, so the block loads
with the set and needs no schema change, no dataclass field and no test. It is
data for a future pass to check `text:` against, not something the gate scores —
stated here so nobody later reads its presence as enforcement. Only direct
descent is recorded: `l08p` and `xl07p` say "like v2's p12", which is a
comparison rather than ancestry, and they are deliberately absent.

## 2026-08-19 — The answer key's header described a four-row router table

**Commits:** `c55d4af`

`datasets/triggers/decision-making.yaml`'s header said `route` "names which of
the four procedures the SKILL.md router should select". The table has offered
six since `ae55b5b`. Corrected to say which procedure, and to name the gap
rather than write around it: no positive in this file routes to `council` or
`hinge`, which is deferred on the record in `corpus-baseline.txt`.

**Comment only.** No `route` line is touched, no label moves, and `set_version`
does not bump — so nothing computed from this key changes and no published
number is affected. The entry exists because the path is governed and the gate
refuses a governed commit without one, not because a label moved.

The reason this is registered rather than folded into a prose sweep: a header
that undercounts the table is how the unreachable-procedure gap stayed
invisible in the first place. `_check_unreachable_procedures` now reports it
mechanically, and this sentence no longer disagrees with it.

## 2026-08-19 — Track H authoring pass two: five triplets authored, one clean, three cut, one blocked

**Commits:** `91f2313`, `b84e7c0`, `e5dc197`, `b1d97bd`

Adds `t01`–`t05` and `index-pass2.yaml` under `datasets/tailoring/`. The
authoring landed over two commits on each of two branches, and all four are
named because all four moved the answer key: `91f2313` carried the fifteen
scenario files in as a pre-switch checkpoint and `b84e7c0` added pass two's
dispositions to `index-pass2.yaml`; `e5dc197` and `b1d97bd` are those same two
changes as they reached `main`, the triplets landing separately there because
they had been committed on a shared branch by another session and had never
reached `main`. An entry naming only the dispositions leaves the commit that
wrote the files unexplained. `index.yaml`
is untouched, so the shortcut battery does not see them and
`corpus-baseline.txt` is neither relied on nor invalidated. `h01`–`h03` are
byte-identical to their committed form: they are evidence of the pass-one shape
and are not edited or deleted.

Labels carry `set_version: 2`. Pass-two labels sharing `1` with the `h` corpus
would be a silent collision of exactly the kind `label_versions_comparable`
exists to refuse.

**The registered kill did not fire.** No matched fact was shown to govern — the
reviewer briefed to prove it reported it could not — and no single surface
feature separates the arms in every triplet: causal-rule overlap reaches 3 of 5,
a sharper reviewer formulation 4 of 5, and `t01` resists both. The kill closes
Track H only if passes two *and* three fail, so the closure condition can no
longer be satisfied and **the track survives**. That is a literal reading, applied
in the same direction as the refusal earlier the same day to treat 3 of 5 as
"every".

**Not firing the kill and being clean are different statements.** That feature's
pooled AUC is 0.740, and 0.800 with proper nouns dropped, far outside
`SEPARABILITY_BAND` — so this corpus cannot be merged as it stands, and would
raise a finding the moment the feature is coded.

**Three cuts by three different checks**, which is the useful part of the record
rather than the count. `t02` on maintainer ruling: over-determined neutralisation
where either settler alone closes it, plus a shared-venue objection that could
not be designed away. `t01` and `t05` on blind re-derivation, which read only
`elicited` and `prompt` and found their *governing* arms admit a defensible
reading under which they do not govern — a failure class the kill does not name,
now disqualifier 15, and worse than the one it does name because it biases the
primary toward zero while looking like a model that failed to notice.

`t04` is **blocked pending τ, not cut**. Its relative movement is 0.333, τ has
never been derived, and any τ above 1/3 makes its governing arm a guaranteed
false negative. Counting it usable would invent a bound for an underived
parameter, which is standing rule 1. If a derived τ lands at or below 1/3 it
returns unchanged.

**The dissent is recorded rather than resolved.** The adversarial reviewer rated
`t01` the strongest of the five and the only item resisting both shortcut
formulations, and would have cut `t04` where this register only blocks it. Both
readings can hold at once — the readers were answering different questions — and
`index-pass2.yaml` carries the reviewer's reasoning intact so a later pass can
overturn the cut.

**Reviewer B never reported.** Clause 1 therefore rests on one adversarial
reviewer plus the blind re-derivation, and the notebook entry says so rather than
implying two independent confirmations.

## 2026-08-19 — `council` and `hinge` are the correct answer for no positive, and that is deferred rather than fixed

**Commits:** `19c4e7c`, `2ccfdb6`

The shipped router table grew from four procedures to six earlier the same day.
The answer key did not grow with it: every `route:` label in both corpora still
names one of the original four, and the six occurrences of "council" in the
corpus text are all the local-authority sense.

`evaluate_routing` scores `chosen in case.routes`. So `council` and `hinge` are
**wrong by construction** — a model that correctly selects one cannot be
credited, and the answer can only ever land in `incorrect`. That is the fourth
instance here of *an estimator that cannot return a non-zero value is not a
measurement*, and the second caught in source before any call was made. The
morning's `PROCEDURES` fix was the same edit's first consequence; this is the
second, one layer further out — the vocabulary was repaired in the instrument
and not in the key.

`_check_unreachable_procedures` now reports it, wired into both the top-level
scan and the draft scan. It is a **finding**, not a hard issue, and both corpora
are listed in `datasets/triggers/corpus-baseline.txt`.

**Why deferred rather than fixed.** Authoring positives for two new procedures
is a change to the answer key: a new `set_version`, and published numbers that
`trigger_arms.label_versions_comparable` will refuse to compare across. That is
a unit of work with a governance cost, not a typo. A gate that reddens every
commit until it is done gets routed around within the day, which is worse than
one that prints the gap on every run — and the may-only-shrink rule means it
cannot quietly stay open.

**The first write-up overstated it and the correction is part of the record.** It
was drafted as a block on N10. An agent briefed to break the claim found three
things: N10 is not registered at all (`docs/RESEARCH_PROGRAMME.md` says the row
"does not register it"); routing is the *secondary* label and N7, N10's design
template, reports it zero times; and the cross-arm comparison the finding was
written to prevent is already refused mechanically by
`skill_versions_comparable`, which landed in `6e2028c` before the finding was
noticed. What survived is narrower and still not small: a pooled routing accuracy
computed here is a six-way choice scored against a four-way key, and the ceiling
cost of that is 0 to about 16 points, over a denominator of 65 items / 130 rows.

**Closed by** positives authored for both procedures, the key version bumped, and
the arms re-run rather than re-scored — or by dropping the two rows from the
router table, which is a real option and not the assumed one.

## 2026-08-19 — a baseline for `datasets/tailoring/`, so the shortcut battery's finding does not permanently redden the gate

**Commits:** `2d848b2`

`f12b444` gave the tailoring corpus a shortcut battery
(`check_tailoring_step` in [`cli.py`](../evals/src/decision_evals/cli.py),
logic in [`tailoring.py`](../evals/src/decision_evals/tailoring.py)) and it
correctly fires on the three triplets authored so far: `delta_word_count`
(pooled AUC 0.611), `numeral_count` (0.722), `has_date` (0.667) and
`penalty_lexicon_gap` (1.000, matched 1.000 too) all separate governing
deltas from matched deltas alone. That corpus is committed as evidence of a
form that failed adversarial review (`c010b06`, `fb295c8`) — nothing may be
authored against it — so the finding is correct and permanent, and a battery
that stays red forever stops being a signal every other session in this
repository can read.

**The fix is the same one `datasets/triggers/corpus-baseline.txt` already
uses, carried over exactly.** `check_shortcuts` in `tailoring.py` used to
return plain `str`, so no finding carried a stable identity a baseline could
name. It now returns `decision_evals.corpus.Finding` — the type the trigger
corpus already uses, not a parallel one — and the four leaking features are
folded into one combined key, `leak:delta:delta_word_count,has_date,
numeral_count,penalty_lexicon_gap`, sorted and comma-joined, the same way
`corpus._check_leaks` keys a *derived* trigger-corpus view (`ask`/`close`/
`open`) rather than the gated one. `datasets/tailoring/corpus-baseline.txt`
lists that one entry, printed on every `de check` run as
`known-open (baselined)` so a green gate is never read as a clean corpus, and
the file may only shrink — an improvement nobody recorded is an improvement
the baseline has stopped being able to see.

**Why a combined key rather than one baseline entry per feature.** Identity
is the whole set of things that went wrong, not any one feature in it: a
fifth feature joining the leak, or a fourth dropping out, changes the key and
the existing baseline entry stops matching, which fails the build until
somebody edits the file with eyes on the new finding. Per-feature keys would
also have caught a genuinely new feature, but would have let the *set*
narrow or widen silently as individual keys came and went — the combined key
makes the whole shape of the defect the thing under version control.
`tests/unit/test_tailoring_battery.py::TestAFifthLeakingFeatureIsNotDeferredByTheShippedBaseline`
constructs a synthetic corpus that leaks on all five columns in
`FEATURES` and confirms the shipped four-feature baseline does not defer it.

`decision_evals.corpus.load_corpus_baseline` and `apply_corpus_baseline` were
generalised (a new `load_baseline_file(repo_root, relative_path)` helper, and
an optional `baseline_path` parameter on `apply_corpus_baseline` for the
stale-entry message) rather than duplicated, so both corpora's baselines run
through one parser and one may-only-shrink rule.

Whether a baseline is the right call here at all, rather than deleting the
corpus outright: the corpus is already inert by the terms of `fb295c8` —
nothing may be authored against it and no fourth triplet may be added — so
what a baseline buys is exactly the same "on the record, not forgotten"
property `datasets/triggers/corpus-baseline.txt` buys for closed findings,
applied to a corpus that will not close by editing but by replacement. That
is a real argument for deleting the three triplets instead and carrying the
finding as prose alone. It was not taken here because the corpus is itself
evidence — of the register-split defect a human reader caught and the
battery now catches mechanically — and deleting evidence to stop a gate
turning red is the wrong direction to resolve that tension in.

## 2026-08-19 — `datasets/tailoring/` added to the decision register

**Commits:** `fb295c8`

Track H's Phase 0 corpus at `datasets/tailoring/` carries an answer key in
exactly the sense this register exists for: each triplet's arms are labelled
*governing* (the answer should move) or *matched non-governing* (nothing
should move). A label move there is invisible in a checkpoint and would shift
every number computed from it — the same failure mode as the 2026-08-13
trigger incident this register was built for, where one turn moved from the
positives to the negatives and recall rose 3 to 5 points on every arm on disk
with not one call re-made.

`GOVERNED` in [`decisions.py`](../evals/src/decision_evals/decisions.py) now
reads `("datasets/triggers/", "datasets/tailoring/", "skills/")`.
[`docs/TAILORING_CORPUS_SPEC.md`](TAILORING_CORPUS_SPEC.md) §6 had already
flagged this as an open maintainer question — *"whether this subtree should be
added is a maintainer question and `index.yaml` raises it"* — and this entry
answers it. That spec's governance note now describes the old state and should
be updated in the same pass that fills in the commit above.

**Not widened to `datasets/` as a whole, on purpose.** `datasets/golden/`
already carries a stronger obligation than a register entry: golden files are
pinned byte-exact, and regenerating them needs an explicit `pytest --bless`
whose diff goes through review. Stacking a second, weaker gate on top of that
one is not an improvement. `datasets/library/` carries no labels — it is
padding prose, not an answer key — so gating it would be exactly the noise
this register's own module docstring warns against: gating every path would be
noise, and noise is what an advisory gate becomes before somebody turns it
off.

**`datasets/probe/` is left open, deliberately.** It carries admissibility
labels and is arguably in the same position as `datasets/tailoring/`, but
nothing published currently depends on it moving. That is a separate decision
for whoever is working that track to make and record, not decided here.

**The ordering problem, and it is sharper here than `730e14a`'s.** `730e14a`
named a commit (`ae55b5b`) that itself touched `skills/` — a genuinely
governed path — so once it existed, citing it satisfied `check_decisions`
cleanly; the only wait was for the sha to exist. This entry is different: the
commit that adds the `datasets/tailoring/` prefix touches only
`evals/src/decision_evals/decisions.py` and `tests/unit/test_decisions.py`,
neither of which is itself a governed path. `check_decisions` requires every
cited commit to be one that *touched* a governed path
(`test_an_entry_naming_an_ungoverned_commit_is_refused` pins this), so naming
that commit here will not just be pending — it will fail validation outright
once filled in, the same way an unrelated sha would.

So the `**Commits:**` line above is left as an explicit placeholder rather
than a sha, and `de check` will report this entry as incomplete until one of
two things happens, which is a call for whoever lands the commit rather than
one made here: either the code change is folded into a commit that also
touches a governed path (for instance, alongside the first authored file
landing under `datasets/tailoring/`), which then has a real commit this entry
can legitimately cite — or the maintainer decides this particular entry
documents a decision about the gate itself rather than a change the gate's
mechanical rule was built to catch, and is exempted the way `docs/DECISIONS.md`
already allows for prose that predates the first heading. Either way, this is
not decided in this entry.

**Resolved 2026-08-19: the first option.** `fb295c8` carries the `GOVERNED` change, the corpus and the spec in one commit, so the sha above names a commit that genuinely touched `datasets/tailoring/` and `check_decisions` accepts it on the same rule as every other entry. The exemption route was not taken — an entry that documents the gate is still a change to a governed path once the corpus lands beside it, and carving out a special case for the commit that installs a rule is the kind of exception that is invisible later.

**A regression test pins the coupling.**
`tests/unit/test_decisions.py::test_the_tailoring_corpus_is_governed` asserts
`touches_governed(["datasets/tailoring/tri-001.yaml"])`, which fails against
the old two-entry tuple — confirmed by running it before this change:
`AssertionError: assert False where False = touches_governed(['datasets/tailoring/tri-001.yaml'])`.

## 2026-08-19 — the shipped description now enumerates six procedures, and that retires ten arms

**Commits:** `ae55b5b`

This entry exists because no single one of the three changes landing today could
see it. S5 added `council.md`, S6 added `hinge.md`, S9 rewrote `ledger`'s router
row. Each was scoped correctly and each was reviewed on its own terms. **The
consequence is only visible when all three are in the tree at once:
`SKILL.md`'s `description` field enumerates the procedures by name**, so adding
two rewrites the exact string that Tracks L, M and N have been measuring.

The description now reads *"one of six procedures ... too much context, advice
that may not fit this person, downstream consequences, timing, several
positions that are each defensible, or a missing fact that may or may not
matter"* against the previous four-item list. `dm-1` loses "all four", `dm-4`
now says the ledger → fit → cascade → timing chain is the four and that
`council` and `hinge` run outside it, and the body heading reads six.
Version bumped `0.2.1` → `0.3.0`; the procedure set changed, not the wording.

**What this costs, stated plainly.** Ten description arms have been run against
the four-procedure string — M4, M5, L5, L7's two, and N6/N7's six across 3,096
calls. **Not one of them describes the string that now ships.** No number
anywhere in this repository may be presented as a measurement of the current
description, and the six-arm table in `docs/STATUS.md` and
`docs/RESEARCH_PROGRAMME.md` is from today a historical comparison between
*description forms* at a fixed procedure set, which is a narrower claim than it
was yesterday. The internal comparisons survive intact — every arm still saw
the same items — but the external one does not.

**What is not claimed.** Nothing here says the new description routes better,
worse, or the same. It has never been run. The same applies to `ledger`'s new
router row: all six routing figures on record (0.105 to 0.579) were measured
against the old row, and a future run scoring the new one is a different
instrument, not a continuation.

**One consequence found immediately, before it could produce a number.**
`triggers.py`'s `PROCEDURES` whitelist and `run_triggers.py`'s `SYSTEM` prompt
contracts both still enumerated the old four names, so a model routing
correctly to `council` or `hinge` could not have expressed it and would have
been discarded if it had. That is the third instance of a defect this
repository has recorded twice — the estimator's vocabulary and the arm's
vocabulary drifting apart — and the first caught in the source rather than in
the numbers. Recorded in
[`notebook/2026-08-19-the-third-instance-of-a-defect-caught-before-it-ran.md`](../notebook/2026-08-19-the-third-instance-of-a-defect-caught-before-it-ran.md).
**No trigger run may be launched against the six-procedure skill until that is
fixed and its regression tests are shown to fail against the old lists.**

**Why this was landed rather than deferred.** The alternative was a router table
listing six procedures beside a description promising four, which ships a
description that is simply wrong about the product. An inconsistent skill is a
worse artefact than an unmeasured one, and this repository's verdict vocabulary
already has a word for unmeasured — `UNTESTED`, which is what `decision-making`
has carried since it was written. The re-measurement is a new run against the
existing `unbundle.py` variants, not new machinery.

---

## 2026-08-19 — Track S5: the council / adversarial-review procedure

**Commits:** `ae55b5b`

Adds `council.md`, the fifth procedure behind the `decision-making` router. S5
was named in the founding brief and left unwritten in the S1–S9 table since
2026-08-11: "a council / adversarial-review procedure — argue the positions
before deciding." It fires where the hard part is none of the other four's —
not too much context, not advice that may not fit, not downstream consequences,
not timing — but that two or three positions are each genuinely defensible and
the one argued first has an unfair advantage over the rest.

Traces to `docs/DECISION_FRAMEWORKS.md`'s K6, Rank 3: consider-the-opposite,
"as a procedure and not a prompt," named there as the mechanism behind exactly
this skill ("It is also the framework whose form maps cleanly onto
sub-agents"). The evidence behind it is **partial**: Lord, Lepper & Preston
1984 beat a "be fair and unbiased" instruction in two experiments, and a later
replication attempt moved in the predicted direction without reaching
significance (same file's K1 evidence table). That puts `council.md` on the
same footing as `cascade.md`, `fit.md` and `timing.md` — traced to a named
mechanism, not backed by strong controlled evidence — and ahead of `ledger.md`,
which traces to nothing and is invented outright.

Ships `experimental` / `verdict: UNTESTED`, matching the other four. Nothing
has measured it — this entry records that a procedure was written, not that it
works. `council.md` carries no YAML frontmatter, matching `cascade.md`,
`fit.md`, `ledger.md` and `timing.md`: only `SKILL.md` does, and its six
frontmatter fields are unaffected by this change. `SKILL.md`'s router table
gains a fifth row in the same change (or the one immediately following); its
"one of four procedures" language and the `dm-1`/`dm-4` claims about "the
stated order" should be re-read against five, since `council.md` does not
currently have a stated place in the `ledger → fit → cascade → timing` chain —
it runs alone, before any of the other four, when it applies at all.

**Addendum, same day — an adversarial review of this and the S6 change found
two real defects touching `council.md`, both acted on and neither measured.**

First: `council.md`'s opening example was "Fight the layoff or take the
package." `cascade.md` opens on resigning and `timing.md` uses resigning as its
undo-cost example, so a real layoff-adjacent question was a three-way collision
magnet by construction — the same subject matter dressed as three different
kinds of hard. `cascade.md` and `timing.md` were left untouched, per the
review's own scope; `council.md`'s example was replaced with "sell the company
or keep building it," a domain none of the other five procedures uses, and the
one illustrative fact later in Step 3 (previously severance/search-time, itself
layoff language) was swapped to match.

Second: the file ran 526 words against 421/434/395/425 for the other four
non-`hinge.md` procedures — noticeably longer for no stated reason. Trimmed to
433 by cutting, not compressing: shorter sentences, fewer restated clauses,
the "three is the practical ceiling" aside shortened. The Step 1/2/3 structure
and the cross-examination test are unchanged.

`SKILL.md`'s `## Choosing` section was also found to never mention `council.md`
or `hinge.md` at all — the "runs alone, before any of the other four" placement
stated two paragraphs above existed only here, in this changelog, not in the
artefact a reader of the skill actually reads. `SKILL.md` now states it
directly: `council.md` and `hinge.md` sit outside the four-chain, and outside
each other, each running alone before `ledger → fit → cascade → timing` when
they apply. That edit lives in `SKILL.md`, not here; this entry only records
that it was prompted by re-reading this one's own "it runs alone" line above.

Nothing here is a routing claim. The new example, the trim, and the `Choosing`
section have not been run against anything.

## 2026-08-19 — Track S6: the clarify-or-decide procedure

**Commits:** `ae55b5b`

Adds `hinge.md`, another new procedure behind the `decision-making` router. S6
was named in the founding brief and left unwritten in the S1–S9 table since
2026-08-11: "a clarify-or-decide procedure — ask for more, or decide under
incomplete information." It fires where the hard part is that a fact is
missing and it is unclear whether that fact is worth waiting for — not too much
context (`ledger.md`), not advice that may not fit the person (`fit.md`), not
downstream consequences (`cascade.md`), not timing of an already-settled
direction (`timing.md`), and not multiple defensible positions (`council.md`,
added the same day by Track S5). The procedure's own test: answer the decision
under each plausible value of the missing fact; if the answer does not move,
asking is stalling and the decision is made now; if it does move, the fact is
load-bearing and either gets asked for (one question, if obtainable in time) or
guessed at explicitly (stated as a guess, not delivered as settled).

No framework trace was attempted for this entry. S7 (2026-08-12) audited the
original four against `docs/DECISION_FRAMEWORKS.md` and found three traced to
named mechanisms and one (`ledger.md`) invented; that audit predates `hinge.md`
and was not rerun here — a future S7-style pass should either trace this
procedure's information-value test to the decision-analysis literature already
cited for `fit.md` (breakeven analysis / value of information, K6) or mark it
invented, rather than assume the trace.

Ships `experimental` / `verdict: UNTESTED`, matching the other four (five, with
`council.md`). Nothing has measured it. `hinge.md` carries no YAML frontmatter,
matching the rest: only `SKILL.md` does, and its six portable frontmatter
fields are unaffected by this change. `SKILL.md`'s router table needs a new row
distinguishing this procedure by what is hard about the decision (a missing
fact of unclear consequence) rather than by what the procedure does — left for
the change that integrates this alongside `council.md`, since both land the
same day and `SKILL.md` should gain both rows, its "one of four procedures"
language, and its `dm-1`/`dm-4` claims about "the stated order," in one pass
rather than two.

**Addendum, same day — an adversarial review found two real defects touching
`hinge.md`, both acted on and neither measured.**

First: this entry's own paragraph above says "the fact is load-bearing," and
`ledger.md` Step 1 says "an item is load-bearing only if changing it would
change the answer" — the identical test, in the identical phrase, in two
procedures that sit on each other's boundary (a fact *present* in a pile versus
a fact *absent* from it). `load-bearing` appeared four times in `ledger.md` and
once in `hinge.md`; a router already confused between `ledger` and `cascade`
was being asked to also separate `ledger` from a procedure written in
`ledger`'s own words. `hinge.md` Step 2 was rewritten to test the same thing —
answer the decision twice, once per plausible value of the missing fact, which
is unchanged and was the part worth keeping — in its own vocabulary: a fact
that swings the answer is now called "the hinge," not "load-bearing."
`ledger.md` was not touched.

The review also supplied a scenario built to fit both `SKILL.md` router rows as
they stood: a pile of layoff-adjacent signals (a manager's hint, an HR memo, two
teammates' warnings, a competing offer with a two-week deadline) plus "nobody
will tell me if my role specifically is on the list." Both rows' wording —
"unclear which fact decides it" (`ledger`) and "something needed to answer is
missing" (`hinge`) — could plausibly be read as describing that gap. The rows
were sharpened on the present-versus-absent distinction Step 1 above already
made: `ledger`'s row now reads "which already-known fact decides it," and
`hinge`'s reads "the fact the decision actually turns on was never given, not
just buried in what's already known." Reasoning through the scenario against
the new rows: every fact in it (the hint, the memo, the warnings, the deadline)
is already known, and the one fact the answer actually turns on — whether this
specific role is on the list — was asked for and refused, so it separates to
`hinge`, not `ledger`. That is a reasoned check against wording, not a run
against the corpus.

Second: the file ran 610 words, well past the other five (395–434). Trimmed to
431, again by cutting rather than compressing — shorter sentences throughout,
the Abort bullets tightened, Step 3 shortened. Step 2's twice-over test and its
structure are unchanged, since the review flagged it as the part worth keeping.

`SKILL.md`'s `## Choosing` section, previously silent on where `council.md` and
`hinge.md` sit, now states both run alone, outside the four-chain, before it
when they apply — recorded in the S5 addendum above rather than twice. Nothing
above is a routing claim: the rewritten test, the sharpened rows, the trim, and
the reasoned check against the reviewer's scenario have not been run against
anything.

## 2026-08-19 — Track S9 (first half): `ledger`'s router row, tightened against its confusion pair

**Commits:** `ae55b5b`

**Router only. `ledger.md` itself is untouched, and this does not bear on the
content-replacement question S9 opened.** `docs/RESEARCH_PROGRAMME.md`'s S9
subsection (2026-08-19) is explicit that three lines now name `ledger` and only
two of them — framework provenance (S7/K6) and the ranked outside candidate
(K6) — bear on the procedure's *content*. The third, `ledger` being
worst-routed in all six description arms measured (0.474, 0.579, 0.105, 0.526,
0.395, 0.474), is a router finding, and the subsection's own words are "it does
not by itself add weight to a content-replacement case." This entry acts on
that third line alone, the way the M-track router-table defect (`cascade`
claimed "the order," `timing` claimed "when," fixed by editing the table, not
either procedure) was acted on without touching the procedures it named.

**The confusion pair, found by reading the actual mis-routes rather than
guessing one.** Across the six checkpointed arms in
`results/decision-making/2026-08-18-e632659-n6-confirmatory/` and
`results/decision-making/2026-08-19-d52236a-n7-remaining-arms/`, counting every
record where the answer key's `route` is `ledger` but the model's `procedure`
differs: 77 went to `cascade`, 32 to `timing`, 16 to `fit`. `ledger → cascade`
is not just the largest bucket, it is larger than the other two combined.
Reading the specific items confirmed it is a real content confusion, not
sampling noise: the heaviest-misrouted cases (`xl08p` 12/12, `xl14p` 12/12,
`l01p` 10/12, `xl01p` 10/10, `s21p` 9/10, `l19p` 9/9, `l16p` 9/9) are all
multi-source piles narrating high-stakes situations — a pension division, a
redundancy letter with an alternative role, a custody variation, a care-home
fee dispute, an insurance claim, an unpaid holiday split — where the actual
difficulty named in each item's `why` field is *which fact the still-open
choice turns on* ("what in all of it actually decides"), not what a chosen
action would set in motion. Contrasting against correctly-routed `cascade`
items of similar length and stakes (`xl06p`, `xl11p`) shows the real
differentiator: `cascade`'s items state the action is already fine and ask
what it starts or spends; the misrouted `ledger` items never settle on an
action at all. The traffic runs almost entirely one direction — only 5 records
in the same six arms show a non-`ledger` item wrongly landing on `ledger` (3
`cascade`, 2 `timing`) — so the row needed to pull `ledger`'s own items back,
not to stop tourists from arriving.

**The edit.** Old row: *"A pile of context arrived and it is unclear what the
answer turns on."* New row: *"A pile of context arrived and it is unclear which
fact decides it — the choice itself, not what acting on it would set off."*
The added clause names the excluded case explicitly, the same edit class used
for the `cascade`/`timing` collision: give the confused-with row's condition
the clause that the other row already implicitly relies on.

**This invalidates comparability, and says so rather than leaving it
implicit.** All six routing figures quoted above (0.474 through 0.900 across
arms, per S9's table) were measured against the *old* row. None of them
describe the row now in `SKILL.md`. Nothing has run against the new row, so
nothing may be claimed about it — not "better," not "fixed," not even
"different" — until a fresh N6/N7-shaped routing run is scored against it, at
which point the two are two different instruments and a comparison needs
`label_versions_comparable`-style bookkeeping, not a before/after read of the
same number.

## 2026-08-18 — Version 3 named four different corpora, so it moves to 4 before N6 runs

**Commits:** `19a44c2`

**This corrects the reasoning in the entry below, on the same day.** That entry
concluded that because the rewrite round altered no `should_fire`, no published
number was affected and `set_version` could stay where it was. The first half is
true. The second does not follow, and an independent check of N6's readiness
found why.

**`version: 3` has named four different corpora** — 120 items when authored, 192
after the short-band merge, 261 after the long-band merge, 258 after `l15` was
retired. `label_versions_comparable` compares that integer and nothing else, and
`run_triggers.py`'s resume keys on `(case_id, repeat)` and never hashes a case's
text. So a version that moves only when a label flips **cannot see a corpus
whose text changed underneath it**, which is precisely what happened: eleven
asks rewritten, three items removed, every `should_fire` untouched.

**It has been harmless for exactly one reason: nothing has ever been scored
against any of the four.** Zero records on disk carry `set_version: 3` — 2,555
at version 1, 3,139 at version 2, 4,810 unstamped, none at 3. N6 would be the
first, and it would stamp 1,548 records with a number that does not identify a
corpus.

So the bump happens **before** the first call rather than after. It costs
nothing, because there is nothing to be made incomparable, and it means the
version in N6's records denotes exactly one corpus.

**The pinned `assert draft.version == 3` in `tests/unit/test_triggers.py` is
what turned this into a reviewed edit rather than a silent one**, which is what
a pinned literal is for. It is updated to 4, not removed. The count beside it
stays recomputed rather than pinned, for the opposite reason given there.

Working, including N6's recomputed power at the smaller corpus:
[`the addendum`](../notebook/2026-08-18-n6-addendum-the-corpus-shrank-and-the-version-had-to-move.md).

---

## 2026-08-18 — Twelve disputed asks rewritten, one triple retired, and the key still has not moved

**Commits:** `08eda89`

**Twelve turns change and no label does.** N3's blind adjudication left 12 items
where the judges' majority disagreed with the key. Applying those moves is
impossible: all 12 land in triples that would end up with two positives or none,
because in each of the ten negative → positive cases the same adjudication
**unanimously** reconfirmed that triple's existing positive. So the disagreement
was never evidence that a label was wrong — it was evidence that **the authored
contrast did not land**, which the v3 plan's rule sends to *rewrite the turn*.

**The rule the rewrites were written to:** an inert ask asks about one thing. It
may share every noun with the positive; it may not put two options in a frame
that invites ranking them. Diagnosed from `s02n2` and applied to all twelve
without the rewriters being shown any judge's rationale — a rewrite aimed at a
stated objection is tuned to that judge.

**Result: 11 of 12 now agree with the key** on blind re-adjudication (36 calls,
0 unparseable), against a registered band of 8. Judge agreement on those twelve
went from 0.611 pairwise to 1.000, and corpus-wide movement from 12/261 = 0.046
to **1/261 = 0.004**.

**`l15` is retired whole** — `l15n2` still moves unanimously after its rewrite,
and the registered rule is one round only. The plan's rule that a retired body
retires its triple applies, and retiring one member would leave a structure the
corpus forbids. **The corpus goes from 261 items / 87 triples to 258 / 86** —
s 24, m 24, l 21, xl 17.

**No gate crossed and no baseline entry was orphaned**, which took a correction
mid-round. Three initial rewrites changed their turn's sentence count and pushed
a corpus-wide habit sitting at 3.01–3.11σ under its 3.0 gate, which would have
had a label fix quietly closing two open shortcut findings — the pattern this
register has already named four times. Rephrased to preserve sentence counts;
the two `sentence_count` findings now read **3.18σ**, stronger than before the
round. `datasets/triggers/corpus-baseline.txt` is unchanged: same three entries,
same keys.

**The answer key still has not moved and no version has been bumped.** Nothing
in this change alters a `should_fire`, so no published number is affected and
`set_version` stays where it was. The freeze — if one is still wanted — now has
one disputed item instead of twelve, and that item is gone.

Protocol registered before the round in
[`notebook/2026-08-18-prediction-the-rewrite-round-and-its-stopping-rule.md`](../notebook/2026-08-18-prediction-the-rewrite-round-and-its-stopping-rule.md);
outcome, including a registered prediction that turned out wrong, in
[`notebook/2026-08-18-the-rewrite-round-eleven-of-twelve-and-one-retirement.md`](../notebook/2026-08-18-the-rewrite-round-eleven-of-twelve-and-one-retirement.md).

---

## 2026-08-14 — The opener leak closed by touching both sides, not one

**Commits:** `cee9329`

A 20,000-draw permutation sweep of the full 4-band x 4-view x 11-feature
family (`notebook/2026-08-14-the-battery-searches-176-cells-and-nobody-had-
costed-that.md`) found `question_marks`/`terminal_question` on the `open`
view as the strongest survivors of Benjamini-Hochberg correction across all
176 cells: AUC 0.779 in `xl`/`open`, 0.716 in `l`/`open`, p < 0.001 both.
Measured directly before any edit: in `l`, 10 of 22 positives opened their
ask with a question against 1 of 44 negatives; in `xl`, 10 of 17 against 1
of 34 — whichever triple member led with a question scored as the positive
nineteen times out of twenty in the long bands.

**The fix is variety, not a direction.** Every earlier generation of this
defect (`word_count`, closed 2026-08-14 earlier the same day) came from a
rule pushed one way — this one touches both sides of the label instead: 4
positives per band (5 in `xl`) had their opener reordered, or given a
one-clause statement lead-in where the whole ask was a single question, so
the question no longer opens the ask; 10 `l` and 9 `xl` negatives — drawn
from `lookup`/`compute` kinds whose asks are already determinate questions —
had their existing question moved to the front instead. Every edit is a
reordering or small addition strictly after each triple's true shared
prefix; `corpus._shared_body` recomputed on every touched triple returns the
same length as before the edit. Resulting rates: `l` 6/22 positives vs
10/44 negatives (27.3% vs 22.7%), `xl` 5/17 vs 9/34 (29.4% vs 26.5%) — not
exact, because three items that would have made it exact were reverted (next
paragraph) rather than kept for the sake of a round number.

**Three items moved label under re-adjudication and were reverted, not
accepted.** A first pass touched 29 items (11 `l` and 10 `xl` negatives).
Blind re-adjudication on all 29 — 3 judges, `scripts/adjudicate.py` — found
3 moved 2-of-3 or 3-of-3 against the original label, all negative-to-positive:
`l12n1`, `l17n2`, `xl15n2`. Investigated rather than accepted, because
accepting would have put two positives in a one-positive-per-triple design.
In all three, moving the existing question to the front of the ask also
pushed a short framing clause ("One process question, separate from the
above." and similar) from leading to trailing — that clause was decoupling
a determinate lookup from an emotionally loaded shared body, and losing it
made the same question read as part of the decision rather than apart from
it. All three reverted to original text (confirmed byte-identical via
`git diff`) and dropped from the touched set; re-adjudication on the
remaining 26 items: 0 moved. Fresh adjudication records for the reverted
three's flawed text were excluded from the merge into
`results/triggers/adjudication.jsonl` rather than appended.

**Verified against the full family, not just the targeted cells.** Re-ran
the 176-cell sweep after the final edit (post-revert): all four target cells
clear BH by a wide margin (AUC 0.523/0.515, q = 1.0, was q <= 0.0044).
`l/close/type_token_ratio` and `xl/open/type_token_ratio`, named by the same
notebook as adjacent leaks, both improved without being touched directly.
Two cells newly cross BH (`l/ask/type_token_ratio`, `xl/ask/sentence_count`);
both checked and are pre-existing signal exposed by removing larger leaks
that were absorbing the correction budget, not the leak relocated by an
unbalanced push — see the notebook entry for the per-cell reasoning.
Independently, the task-giver re-ran the same test with a different
implementation against the corpus after the first (pre-revert) pass: 18
cells crossing p<0.05 before (8.8 expected) and 7 BH survivors (5 this leak)
against 10 crossing / 0 surviving after.

**The corpus's own gate.** `matched:open:question_marks` and
`matched:open:terminal_question` no longer reproduce and are removed from
`corpus-baseline.txt` (may-only-shrink). One gate finding,
`cancel:close:type_token_ratio`, briefly crossed 3.0 (to 3.04) during the
first pass — two of the three reverted items' reordering shifted a couple of
closing sentences by a clause — and closed the same day when those three
were reverted (measured after: 2.985, under the gate). The underlying skew
is real, corpus-wide (positive is the highest/lowest vocabulary-diversity
triple member in 66 of 87 triples, every band), predates this session at
~2.9 null SE, and needs a length/complexity-neutral rewrite of closing
sentences corpus-wide to actually close — out of scope here, and not added
to the baseline because it never shipped as a crossing finding on the
committed corpus.

**A claim raised and refuted.** The task-giver's read of the near-exact
pre-revert opener rates was that `matched_attainable` on these cells must now
be degenerate by construction (every permutation gives 0.500, the
`_shared_body`-bug signature). Checked directly against `corpus.py`'s own
functions rather than transcribed: only 8 of 22 `l` triples and 8 of 17 `xl`
triples have all three members agreeing on opener form; `null_se` is nonzero
and `matched_attainable`'s reach from 0.5 clears `MATCHED_Z * null_se` on
both bands (`Check.inert` is `False`, both axes, both bands, verified on the
final corpus). The band-level rate came from mixing which triples lean which
way, not from flattening each triple, so the check that closed this leak
stays capable of catching a regression.

**Two tests re-pinned in the same commit.** `test_corpus_battery.py` pinned
the shipped baseline's deferred-finding count at 5 and one per-band figure at
`xl 0.235` for `sentence_count`'s `cancel:` finding on `turn`. Both are
data-driven pins against the live corpus rather than assertions about
mechanism: the count drops to 3 as the two `question_marks`/
`terminal_question` findings above close, and `xl 0.235` moves to `xl 0.309`
because several `xl` positives gained a lead-in sentence, which shifts
`sentence_count`'s distribution. The reporting format itself (one
`band value` pair per band) is unchanged — checked before re-pinning rather
than assumed, since a changed message would have meant something broke
rather than moved.

Full derivation, before/after opener counts, the three-item investigation,
and the complete 176-cell before/after table:
`notebook/2026-08-14-the-opener-leak-closed-by-touching-both-sides.md`.

## 2026-08-14 — The ask cut stopped one word short of every shared body's newline

**Commits:** `6707c38`

`_shared_body` cut the raw byte-identical prefix of a triple's three turns
back to the last SPACE so the remainder starts at a whole word. Every
authored body ends with a NEWLINE before the ask, and a newline is not a
space — the cut landed one word short of where the newline actually was, and
that word ("believed." in the shipped XL band) leaked into every derived
`ask` and `open` as their shared, constant opening word. A regression test
was confirmed to fail against the pre-fix code before the fix landed.

**What the bug had been hiding.** A feature reading a constant leaked word
across an affected triple cannot separate anything and reads exactly 0.500 —
indistinguishable from a clean pass. Once the leak stopped being constant,
two matched within-triple findings crossed the z = 3.0 gate for the first
time: `matched:open:question_marks` and `matched:open:terminal_question`,
0.566 at 3.47 null SE pre-merge, baselined in `corpus-baseline.txt` with a
`CLOSED BY` condition. `matched:turn:word_count` and `matched:ask:word_count`
read bit-identically before and after this fix (0.66015625 both times) — the
leaked word was present in all three members of an affected triple, so
removing it shifts all three equally and a within-triple rank statistic
cannot see a shift common to the whole triple. Both findings closed the same
day, but by the concurrent long-band merge (`a38d2d8`, see the entry below),
not by this fix.

**The guard, checked against the day's other additions.** `sentence_count`
(added earlier the same day alongside the `open` view) was inert in every
view of the known-good fixture — its three fixed shapes all produced two
sentences, so the feature could not move regardless of label. Fixed by giving
one shape a third short sentence. The planted closing-leak fixture turned out
to leak on `open` as well as `close`, symmetrically — reversing a
two-sentence tail swaps which sentence is first exactly as much as which is
last, and a constant sentence placed in front of the swap does not shield
`open` because `_shared_body` folds anything that never varies into the body
regardless of position. The baseline-narrowness test's helper was widened to
capture every finding the fixture currently produces rather than a
hand-picked subset that predated the `open` view.

Full account, including the per-finding numbers before and after the
concurrent merge: `notebook/2026-08-14-the-ask-derivation-bug-and-two-checks-it-had-been-hiding.md`.

---

## 2026-08-14 — Twenty-three long-band triples, and a leak that closed sideways

**Commits:** `a38d2d8`

`l.yaml` gains `l10`–`l22` (13 triples) and `xl.yaml` gains `xl08`–`xl17` (10),
the rebuild that was "mid-rebuild and unmerged" in the entry below. The corpus
goes from 192 items (64 triples) to 261 (87). **No label on an existing item
changes here.** The three moves N3's adjudication found (`s02n2`, `s12p`,
`xl05n2`) are still not applied — this change merges the authored triples only
and does not touch that backlog, so "the freeze" the entry below anticipated is
still open on that point.

**Both `word_count` findings closed, but not by the condition the previous entry
named.** That entry called for a rank roughly uniform across longest, middle and
shortest. Measured on the 23 new triples: 16 positive-shortest, 5 positive-middle,
2 positive-longest — the mirror image of the 49-of-64 positive-longest bias
projected against, not a uniform split. `word_count` closed anyway, from matched
0.660 (3.24 null SE) to 0.546 (1.09), because `l` and `xl` swung from
positive-longest bias (0.778, 0.393) to positive-shortest bias (0.455, 0.294),
which happened to average against `s` and `m`'s unchanged positive-longest bias
and land the pooled/matched figure under the gate.

**The same swing opened two findings the previous corpus did not have.**
`sentence_count`, which tracks `word_count` closely, crosses the *dispersion*
gate on both `turn` and `ask` views (3.82 null SE, `cancel:` not `matched:` — the
mean stays near chance at 0.480 but the positive sits at an extreme of its triple
far more often than chance). `type_token_ratio` on the `ask` view crosses the
*matched* gate outright (0.316, 4.27 SE, below chance in all four bands). Not
retuned to close them: three features reading the same closing-sentence habit
through different rulers, and per-item retuning against whichever one is
currently over the line is the mechanism `docs/DECISIONS.md`'s own entries have
already named four times.

**`datasets/triggers/corpus-baseline.txt`:** the two `word_count` entries are
deleted; three replace them —
`cancel:turn:sentence_count`, `cancel:ask:sentence_count`,
`matched:ask:type_token_ratio` — with the same rank-uniformity condition named as
what would close them, corpus-wide. A concurrent session's `matched:open:
question_marks` / `matched:open:terminal_question` entries, added the same day
for an unrelated `_shared_body` measurement fix, are left as that session wrote
them; this merge shifts their numbers too (0.566→0.629 matched, 3.47→6.12 SE)
but the key still matches, so the gate still reads them as open and baselined.

Full battery, before/after per-band figures, and the rank-count measurement are
in `notebook/2026-08-14-the-long-band-merge-closed-one-leak-and-opened-two.md`.

## 2026-08-13 — Twenty-four short-band triples, and a statistic the design had always deserved

**Commits:** `e07c5ef`

`s.yaml` gains ten triples (`s15`–`s24`) and `m.yaml` fourteen. The corpus goes
from 120 items to 192. **No label on an existing item changes here** — the three
moves N3's adjudication found (`s02n2`, `s12p`, `xl05n2`) are recorded in the
notebook and are deliberately *not* applied, because the key must move once, at
the freeze, with the long-band rebuild in the same version bump. Two bumps means
two sets of incomparable records.

**Why the short bands and not the long ones.** A power analysis nobody had run
before the corpus was authored: at the measured design effect of 1.63 the short
arm is the binding constraint, and Fisher-exact confirms it — with `n_short`
held at 24 triples, taking `n_long` to 400 still reaches only 0.798. Widening
the long bands first would have bought nothing.

**The extension closed both seeded entries in `datasets/triggers/corpus-baseline.txt`,
and neither was closed by moving a threshold.** `paste_cues` is no longer inert
in every view; the four-feature `close`-view leak no longer holds with that
feature set. They are deleted rather than kept, which is the may-only-shrink
rule working in the direction it was written for.

**And it opened two, which is the exceptional case for that file.** The battery
gained a matched within-triple check — a positive against its own two negatives,
over the body they share, which is the only comparison a matched design actually
controls. `word_count` sits above both its negatives in 0.660 of comparisons,
3.24 null standard errors from chance, on both the `turn` and `ask` views. The
pooled AUC over the same corpus is 0.517 and 0.502.

**Read those two numbers together, because that is the finding.** A pooled AUC
ranks positives against negatives from *other* triples, where body variation
swamps the ask, so it is structurally blind to a rank held inside a triple. The
corpus was built as a matched design and evaluated as an unmatched one, and
every "the corpus is ruler-proof" claim on record rests on the wrong statistic.
Four separate pooled-cancellations were found by four separate people over one
day, each after the fact; the matched check found all of them in one run.

**What it does not license.** An arm sees one turn and never sees the other two
members of its triple, so it cannot use a within-triple rank directly. This is a
defect in the *construction*, not a demonstrated exploit, and per-band pooled AUC
remains the exploitability measure. Both are baselined and printed on every run
rather than treated as either fatal or fine.

**Not fixable in this change.** 23 long-band triples are mid-rebuild and
unmerged. An assignment rule pairing close rank with ask form was tried and
*measured to make it worse*: only 15 of 64 positives are `embedded` and can carry
shortest or middle rank, so 49 of 64 would be forced to positive-longest, which
projects ~0.766 against the observed 0.660. The close condition is a roughly
uniform rank distribution reached by assignment at authoring time, never by
editing negatives toward a target — four generations of leak on 2026-08-13 came
from per-item bounds pushed in one direction.

## 2026-08-13 — The XL band, and two rulers that cancelled

**Commits:** `74b7f5f`

Seven triples of 900–1,500 words completes the corpus at 120 items. `ledger` has
for the first time been shown a pile of context; version 2's longest positive
was one sentence describing one.

**The gates written for this corpus had never read it.** `check_trigger_sets`
globs `datasets/triggers/*.yaml` and the bands are one directory down, so 99
authored items sat outside the battery, the stump and the balance rules while
`de check` reported green. Third instance of a tested check with no caller, and
the first caught before anything was published from it. A draft-corpus step now
holds it to the live rules **without making it live** — the entry point may not
move before adjudication has run its 20% kill.

**A pooled AUC of 0.5 did not mean the bands were clean.** `word_count` read
0.511 across the set while L was at 0.769 and XL at 0.301 — a `ledger` positive
ends in four words and a `compute` negative in ninety, so the same habit pointed
opposite ways in the two bands and cancelled. Length inside a band is available
at inference, so it was a real shortcut. The depth-2 stump caught it at a lift
of 0.117; the per-feature battery could not. Mixing the ask lengths took it to
0.083 against a 0.100 cap.

Per-band separability is reported and not gated: 98 pairs in the XL band gives a
null SE around 0.137, so a [0.40, 0.60] gate would fire on a clean corpus about
half the time.

## 2026-08-13 — The L band, and a scale error in the gate rather than in the corpus

**Commits:** `bf88664`

Nine shared bodies, 27 turns. All eight single-feature shortcuts landed inside
[0.40, 0.60] on 33 triples. `first_person_rate` had read 0.680 after S and M —
ten S-band negatives sat at exactly zero against the positives' 0.10 — and was
fixed by asking the identical question in the first person. A shared body needs
no such repair, which is the argument for the construction.

The stump found a defect in the gate. `MAX_STUMP_ACCURACY = 0.70` was borrowed
from the AUC target, and accuracy does not transfer across base rates: version 2
was 77% negative so "never fire" scored 0.767 there, against 0.667 here. One
flat threshold asked v3 for 3.3 points of headroom and v2 for 13.3. It became a
**lift over the majority-class baseline** capped at 0.10.

On that gate the corpus **failed at 0.101 against a cap of 0.100** and the
commit says so rather than rounding it. `majority_baseline` became a function,
because an arm that never fires scores 0.667 and looks like caution.

## 2026-08-13 — The S and M bands, and a battery that checks more than length

**Commits:** `ee96088`

24 triples, 72 turns, two of four bands. Each triple is one positive and two
negatives written to the same length, so **the label cannot come from a word
count**. Band M is the band version 2 skipped entirely: a paragraph of situation
with the question inside it rather than as the whole turn.

The shortcut battery earned its keep on the first measurement — `word_count`
fell to 0.531 from version 2's 0.850, and `first_person_rate` came out at 0.680
and failed the gate. A battery that only checked length would have passed the
corpus and missed the next ruler.

## 2026-08-13 — The corpus is 89% solved by counting words

**Commits:** `fffa4a2`

The maintainer observed that real users write paragraphs. Checking it found a
confound rather than only a gap: positives run at a median of 18 words against
the negatives' 8, no turn exceeds 25 words, and **"fire if the turn is at least
18 words" scores 0.890 with no model involved** against a best measured arm of
0.956. Separability is AUC 0.850 where the long-context plan had already set a
0.70 gate — a gate never pointed at this set.

This does not invalidate the arm comparisons; every arm saw the same 73 turns.
It caps what any of them could have shown, and it gives Track M's headline a
second reading: five manipulations moved firing accuracy nowhere, and there were
about six points of room above a word count.

**Correction, 2026-08-13, appended rather than rewritten.** The two numbers in
the paragraphs above are at different label versions and comparing them is the
move `trigger_arms.label_versions_comparable` refuses. 0.890 is the ruler on the
**version 2** key; 0.956 is the `full` arm on the **version 1** key, where the
same ruler scores 0.877. Within a version the headroom is about **nine** points
either way: v2 ruler 0.890 against 0.9795 (`stakes-shown`) to 0.9863
(`confidence`), v1 ruler 0.877 against 0.967 (`no-opener`) to 0.973
(`confidence`). 0.956 was also never the best arm at either
version — `no-opener` and `confidence` both beat it at v1 and no document had computed it, because L5
published precision, recall, FPR and routing and no accuracy column. The
six-point figure is withdrawn; the decision it supported, that the corpus needs
rebuilding, is unaffected and if anything better supported.

## 2026-08-13 — Version the answer key

**Commits:** `903169c`

Re-scoring the arms on disk against the new labels raised recall 3 to 5 points
on almost all of them with no call re-made. It has every property the three
earlier defects had — valid checkpoints, every instrument check passing, 100%
parse rate, the number moving the way an author would like — and one they did
not: **it is not a bug.** The new labels are better. The improvement is real as
a label correction and would be a fabrication as a model result.

So the set carries `version: 2`, every record carries `set_version`, and
`trigger_arms` refuses a comparison spanning revisions.

## 2026-08-13 — Four label decisions, and a turn may have two acceptable routes

**Commits:** `d43c490`

`x-n21` *"the disk is at 99%, do we need to act"* moves to the negatives: the
question asked has an obvious answer, so there is no trade-off to weigh, and the
nuance is in how to act — which the turn does not ask.

`x-n22` *"the build is green, can I deploy"* stays a positive against four
versions that all declined to fire. A green build answers whether the code
compiles, not whether to ship; dependencies, prerequisites, who needs telling
and the maintenance window are all still open. That reasoning is also why it
gains `cascade` as a second route.

The line between them is written into both `why` fields: `x-n21` looks settled
and is, `x-n22` looks settled and is not.

## 2026-08-12 — The two cases that disagreed with me stay in the set

**Commits:** `0438306`

Removing `x-n21` and `x-n22` as "contested" because they failed to fire would
have been **selection on the outcome**. All five `x-n*` cases have the same
provenance — one sitting, one author, promotion argument and label together — so
pulling only the two that disagreed with that judgement would have deleted the
evidence against it and raised recall by doing so.

They are scored like everything else. The `x-` prefix is the reader's escape
hatch, and any recall figure leaning on them should be given both ways.

## 2026-08-12 — Fired but routed nowhere is an abort condition

**Commits:** `94da7cf`

Both runs that day produced cases where the model fired and returned
`procedure: null` — the skill's own *Abort if* clause arriving one step late,
after it had committed to running. The router table said what to do when several
procedures apply and nothing about when none does, leaving "pile is usually the
problem → ledger.md" as the only fallback. That is the wrong one: it turns a
lookup into a decision procedure instead of sending it back to *Abort if*.

Skill version 0.2.0 → 0.2.1.

## 2026-08-12 — Repairing p07 and p08, and what the repair showed

**Commits:** `88995e5`

Both cases were rewritten to carry no time word: temporal language had been put
into the two cases meant to test consequence reasoning, so the cascade/timing
confusion was partly an authoring defect.

The repair worked on its own terms — `p08` now routes correctly — and **routing
accuracy was identical to three decimal places with a different set of errors**.
That is the finding, not the repair.

## 2026-08-12 — A trigger set that described a skill which had stopped existing

**Commits:** `8541d46`

`datasets/triggers/evidence-ledger.yaml` named a skill retired the previous day
when the four procedures were consolidated behind one router, and the skill that
actually ships had no trigger set at all. Neither surfaced for a day, because
`load_trigger_set` was written, tested to 100%, and **called by nothing**.

`de check` gained the trigger-sets step. The same shape recurred later with
`prereg.py`, which is why `de check` now also refuses an unreachable integrity
lock.

## 2026-08-11 — One entry, four procedures behind it

**Commits:** `ca6b669`

Four separate decision skills would carry four descriptions that all read as
"help me decide", and overlapping descriptions are the documented mechanism by
which agents pick the wrong skill. Progressive disclosure reconciles the two
findings that look opposed: one description resident in context, one procedure
file read when it fires.

**Superseded in part by M4** (2026-08-12), which measured four entries against
one and found shadowing did not appear at four. The structure stands; the
citation that justified it no longer reaches down to this scale. See
`notebook/2026-08-12-m4-shadowing-did-not-appear-at-four.md`.

## 2026-08-11 — Three skills you can install today, and the review that was skipped

**Commits:** `9a16b18`

Re-reading the founding prompt rather than a twice-compacted summary of it
surfaced two things asked for on day one and absent from everything built. The
first: research on decision-making itself, before picking a direction. The
programme had eleven tracks on LLM failure modes and none on decision
frameworks — the "skills based on really nothing" the brief warned against.
That became Track K, and it runs first.

## 2026-08-11 — A placebo must match the skill's output template

**Commits:** `220cfa2`

Includes a correction: the plan claimed `evidence-ledger`'s placebo failed the
repo's own guard at a word ratio of 0.71. It did not — `check_placebo_match`
compares against the skill's *body*, and 421w vs 445w is 1.057, inside
tolerance. The 0.71 counted YAML frontmatter as skill prose, which the model
never sees.

What survived was sharper and invisible to both existing checks: matching length
is not matching structure, and a placebo that omits the output template lets the
treatment arm win on format alone.

## 2026-08-10 — Positive/negative trigger sets, and no F-score

**Commits:** `488331e`

Trigger quality is measured and reported separately from task accuracy, never
blended. **There is deliberately no F-score**: a single number would let a
description trade away precision, which is the property that degrades daily use.
A suite that lifts accuracy 10pp while firing on 60% of ordinary turns is a net
loss to whoever installed it, and an accuracy-only evaluation reports it as a
win.

## 2026-08-10 — The runner, the first skill, and a real validator

**Commits:** `a602794`

The runner is checkpointed and resumable because rate limits rather than dollars
are the budget and a confirmation run may span days. Records append to JSONL and
a resumed run skips item/arm pairs already present, so a crash costs the current
call and nothing else. A truncated final line is ignored rather than fatal —
refusing to resume over a partial write would throw away a whole checkpoint to
avoid re-running one item.

## 2026-08-20 — council and hinge get positives, and the key moves to version 5

**Commits:** `069df14`, `a84626b`

Twenty-four triples added to the banded corpus, seventy-two items. Twelve
positives route to `council` and twelve to `hinge`, three of each in every band.
No existing label moved and no existing turn was edited.

The defect this closes was recorded in `datasets/triggers/corpus-baseline.txt`
on 2026-08-19 and is a measurement defect rather than a gap in coverage.
`evaluate_routing` scores `chosen in case.routes`. The router table grew from
four rows to six on 2026-08-19 and the key did not grow with it, so a model that
correctly named `council` could only ever be counted wrong, and an arm offered
six procedures carried two ways to be wrong that a four-procedure arm did not
have. That reads as a description effect and is a menu-size artefact.

The baseline entry named two ways to close it and did not assume either.
Authoring the positives is the one taken; dropping the two rows from the router
table was the other and would have meant shipping a smaller skill to make a
number computable.

**Why the version moves rather than the labels being edited in place.** A
routing number computed on version 4 is a six-way choice graded against a
four-way key. It is not comparable with one computed here, and
`label_versions_comparable` is what refuses that comparison. Moving the integer
is how the refusal happens; leaving it would let a v4 routing figure sit beside
a v5 one with nothing to say they are graded against different-sized keys.

Nothing had been scored against version 4 — zero records on disk carry
`set_version: 4` — so no published number is invalidated. What changes is the
denominator every future one is computed over: 258 items across 86 triples
becomes 330 across 110, and routed positives go from 65 over four procedures to
89 over six, at ledger 19, cascade 16, fit 15, timing 15, council 12, hinge 12.

**What the shortcut battery said, and what was done about it.** The first draft
of the 24 triples left `matched:turn:type_token_ratio` firing at 3.61 standard
errors. That was a real authoring defect with a nameable cause: the positive
asks were written as deliberation and the negative ones as task requests, so the
positives carried runs of function words that the negatives did not. Rewriting
the twelve long-band positive asks at the negatives' lexical density closed the
key and took the pre-existing `matched:ask:type_token_ratio` from 4.28 to 3.03
in passing.

`cancel:close:type_token_ratio` crossed the z = 3.0 gate and is baselined with
its arithmetic rather than tuned away. The positive is at an extreme of its own
triple on the closing sentence in 79 of the 86 pre-existing triples and in 22 of
the 24 new ones — 0.9186 against 0.9167 — so the rate did not move and only `n`
did. This is the finding the 2026-08-14 close-out already described as
corpus-wide and one clause-shift below the gate; twenty-four more triples at the
same rate is what put it one clause-shift above.

Four items were retuned against that key before the mechanism was obvious, and
it moved the wrong way, 3.10 to 3.23. The tuning stopped there. The baseline
file names per-item retuning against whichever feature is currently over the
line as the thing that produced four generations of leak in this corpus, and a
fifth was not started.

**A second commit under the same heading.** `a84626b` rebuilds the thirty-six
long-band items from their bodies and closings. `textwrap.fill` had been wrapping
on hyphens, so "five-year" was stored as "five- year", and the new `xl` bodies
carried no em dash where every other long-band item in the set does. Both are
authoring defects in items this entry introduced, so they belong to this
decision rather than to a separate one. No label moved and no closing ask
changed meaning.

**Not yet adjudicated.** These labels are the author's, and the corpus rule is
blind three-judge adjudication with a pre-registered kill at more than 20% of
labels moving. That has not run on these items and no number may be published
against version 5 until it has.

**`datasets/triggers/decision-making.yaml` is not fixed.** The version 2 corpus
still has no `council` or `hinge` positive and its baseline entry stays. It is
the superseded set, and closing it would mean either authoring the same triples
again for a corpus nothing will run against or claiming a fix that was not made.

## 2026-08-20 — The changelog records a version that added items rather than moved labels

**Commits:** `a34923a`

Bumps the banded corpus to version 5 and writes the `corrections.jsonl` line
that accounts for the move, which the gate added this morning requires before
the bump will pass.

The line needed a kind that did not exist. `moved` names an item and both of its
labels and there is no such item here. `rebuilt` says item ids do not carry
across, which is false — every version 4 id is still present and unchanged.
`none` says the bump moved no label, which is true and is the whole problem: it
would have been silent about seventy-two items that were not there before, and a
reader comparing a version 4 figure with a version 5 one needs to know the
denominator changed even when nothing was relabelled.

So `extended` — items added, no existing label moved — with the denominators in
the reason field. The register of kinds may grow when a real event has no
accurate one; what it may not do is have an event described by the nearest
inaccurate kind.

## 2026-08-21 — The version 2 corpus is exempt from the adjudication gate, and says why

**Commits:** `8bdc1a5`

Adds `datasets/triggers/adjudication-baseline.txt`, which is a governed path, so
the reasoning belongs here rather than in the commit body.

`de check` now refuses a trigger set on disk carrying an item with no
three-judge blind adjudication record. Two answer keys load, and one of them
would be refused on the first run: `datasets/triggers/decision-making.yaml` at
version 2, whose items predate the rule. Blind adjudication arrived with version
3 and has never run against these ids. The ledger holds banded ids like `s01p`
and this file's are `p04` and `x-n21`, so its coverage is zero.

**It is baselined rather than adjudicated, and the reason is not the cost of the
calls.** This is the corpus `SCORECARD.md` records as 89% solvable by counting
words, AUC 0.850 on turn length alone, against which a bare "fire if >= 18
words" rule scores 0.890. Adjudicating its labels would buy a clean answer key
for an instrument whose measurements still would not travel. The eight published
runs scored against it stay published with that caveat attached.

The line may only shrink, on the same terms as
`results/provenance-baseline.txt`: the gate refuses a baselined set that turns
out to be fully adjudicated, and refuses a line naming no set that loads. Remove
it if the set is ever adjudicated, or when it is retired.

**Why the gate reads the live key and not only the published runs.** It reads
both. A run declares a version and the corpus file moves on, so a run-keyed
check alone would be computed against records while the key drifted; a key-keyed
check alone is computed against whatever the corpus holds now, and retiring an
item erases the evidence that a published number stood on an unadjudicated
label. Three ids in the ledger today, `l15p` and its two negatives, are that
erasure having already happened in the direction that cost nothing.

## 2026-08-21 — Three disputed asks are rewritten, and the key moves to version 6

**Commits:** `d3ec913`

Blind adjudication of the seventy-two items version 5 added disputed three
labels: `l24n1` and `m29n2` read as fire against a negative key, and `m25p` read
as no-fire against a positive one. Movement was 3/72 = 0.042 and the corpus
survived the pre-registered kill.

**The labels were not applied, because none of the three can be.** Each move
breaks the invariant `corpus._check_triples` enforces. `l24p` and `m29p` were
independently confirmed positive by the same judges, so promoting a negative
beside them gives a triple with two positives; `m25`'s other two members are
unanimously negative, so demoting its positive gives a triple with none. That is
2026-08-18's finding repeating on the new items at 3 of 3 where it was 12 of 12.

So the remedy is the one that round settled on, and it is the plan's live
branch: rewrite the disputed ask and judge it again. Retirement is the remedy
for a three-way split, and three binary judges cannot produce one.

**What changed.** Three closing asks. Every body is untouched, every
`should_fire` is unchanged, and each triple stays inside its own length
tolerance. `m25p` now asks which way to go rather than for both cases to be put,
which is the ask the label always meant. `m29n2` asks what happens during the
wait rather than whether there is any point ringing. `l24n1` states the decision
as already taken and asks for two figures on the chosen branch.

**`l24n1` is the one worth reading.** Its ask was already arithmetic and three
judges read the turn as a decision anyway. No ask alone fixed it: the body spends
241 words establishing that three people must agree before probate completes,
and that pressure survives whatever sentence closes it. What worked was a
sentence conceding the choice, which puts the item in the shipped definition's
own negative branch, a task whose decision has already been made and stated.
Re-adjudication returned 3-0 with the key on all three.

**Why the version moves, recorded as a choice.** No record on disk carries
`set_version: 5`, so leaving it alone makes nothing incomparable. It moves
because the 3 to 4 bump on 2026-08-18 was this fact pattern exactly, and its
reasoning holds verbatim: a version that moves only when a label flips cannot
see a corpus whose text changed under it. Leaving it at 5 would have one version
naming two corpora.

**One shortcut finding closed as a side effect, and is disclosed rather than
claimed.** `matched:ask:type_token_ratio` fell from 3.03 to 2.91 null standard
errors and left `datasets/triggers/corpus-baseline.txt`, which may only shrink.
Three asks out of 330 items moved it, which is the same one-clause sensitivity
that file already records for this statistic in the other direction on
2026-08-14. The rewrites were written to the shipped definition by agents that
never saw a judge's verdict or that file.
