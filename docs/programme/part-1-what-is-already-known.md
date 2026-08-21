# Part 1: what is already known

**Audience:** the evaluating reader, and in particular anyone picking up a track.

Tracks K and M. The decision-framework review this project skipped, graded by
evidence, and what the literature already settles about how a skill should be
built. Free, no instrument, and it changes what everything else is testing.

Part 1 of eight. The tracks table, the venue map, the sequencing and the
claim ladder are in [`RESEARCH_PROGRAMME.md`](../RESEARCH_PROGRAMME.md).
Headings below start at `###`, carried over from the split so that a track's
anchor is the one it had in the monolith.

---

Free, no instrument, and it changes what everything else is testing. Runs first.

### Track K, decision frameworks: the review this project skipped

The question: what is already known about how to make good decisions, and which
of it can be written down as a skill?

Why it matters. The founding brief asked for research on *decision making*
before any direction was chosen: "how to make great decisions." Every skill in
this repository was instead invented from first principles by a model. That is
the "skills based on really nothing" the brief warned against, and
SkillsBench's finding that self-generated skills yield negligible or negative
gains while curated ones yield +16.6pp is the same warning with a number on it.

This track runs first. It is free, it needs no instrument, and it changes
what every other track is testing.

| # | Work |
|---|---|
| K1 | Review the normative and applied decision literature: decision analysis and expected value, reference-class forecasting and base rates, calibration training, pre-mortems, Kepner-Tregoe, WRAP, OODA, satisficing vs maximising, option value and reversibility, dominance and elimination-by-aspects. One page each: what it claims, what evidence supports it, what it costs to run. |
| K2 | Review the *prescriptive* evidence: which of these actually improve human decisions in trials, not which are popular. Many are folklore with a book attached, and the write-up must say which. |
| K3 | Mine [cc-thinking-skills](https://github.com/tjboudreaux/cc-thinking-skills) and comparable prompt libraries: what frameworks are already encoded, in what form, with what evidence behind them. The maintainer installed it and reports it did not help. That is data about form, not about the frameworks. |
| K4 | Map framework → failure mode. A framework is only a skill candidate if it targets a failure an LLM actually makes. Cross against Track A's results. |
| K5 | Citation audit, and it is worse than a coverage gap. Counts drift with the glob, so `de check` computes them rather than prose asserting them. Measured 2026-08-11: 67 unique identifiers cited across `docs/`, `notebook/`, `skills/` and the product files; `paper/refs.bib` holds 49 entries, 39 carrying arXiv ids. Nine of the ten papers in the headline literature table are absent from the bibliography, and only 2605.31408 is present. So the bib and the programme cite disjoint literatures. Work: resolve every identifier against arxiv.org; add the missing entries; and make `de check` fail when a number is asserted beside an arXiv id without a `quote:` field in the bib entry holding the verbatim source sentence. Presence-checking alone would not have caught any of the three misattributions found on 2026-08-11. All three cited real papers that existed and said something adjacent. |
| K6 | Output: `docs/DECISION_FRAMEWORKS.md`, the catalogue, with a shortlist of framework-derived skill candidates ranked by evidence strength. |

Skill candidates already named in the brief and not yet written: a council /
adversarial-review skill (multiple positions argued before deciding, which is
also the sub-agent architecture question), and a clarify-or-decide skill (when
to ask for more information versus decide under incomplete information).

Done when `docs/DECISION_FRAMEWORKS.md` exists and every current skill is
either traced to a documented framework or explicitly marked as invented.

#### First pass done, 2026-08-12: [`docs/DECISION_FRAMEWORKS.md`](../DECISION_FRAMEWORKS.md)

Eleven frameworks catalogued and graded on *prescriptive* evidence rather than
popularity. K2's *none located* rows still want a database search. Four results
bear on what the rest of the programme should build.

K5 closed on 2026-08-12 and reopened on 2026-08-14, and this paragraph did not notice. `paper/citations-baseline.txt` carries two identifiers again: `2412.06593` (anchoring) and `2505.02151` (overconfidence), added by the K3/K4 pass with their quotes recorded in [`DECISION_FRAMEWORKS.md`](../DECISION_FRAMEWORKS.md) rather than in `paper/refs.bib`, because another session held that file at the time. Neither is in the bibliography today. **Both were added on 2026-08-18** (`paper/refs.bib` carries `lou2024anchoring` and `sun2025overconfident` with their quotes, and `paper/citations-baseline.txt` records the closure), so this sentence was true from 2026-08-14 to 2026-08-18 and is appended to rather than rewritten, the same way the sentence it corrects was. A backlog that may only shrink can still be added to, and the sentence below was true when written and has been false since. What follows is the 2026-08-12 audit as it stood.

All 27 baselined
identifiers were fetched first-hand: 67 cited, 67 in the bibliography, 0
exempted. Of the eight that assert a number, six survive. In-Context Prompting's
three failure-rate pairs, PerspectiveGap's 17.2% and 62.0%, and MAST's 14 modes /
1600+ traces / κ=0.88 are exact. Two do not:

- Xu & Wu is 30 tasks and 2 models, not "86 tasks, 11 domains". That was
  SkillsBench's scale, misremembered, and SkillsBench is 87 tasks and 8 domains,
  so both halves were wrong, in the direction that made the smaller paper look
  larger. The +18 to +36pp in `CLAUDE.md` and `AGENTS.md` is correct: it is
  the union of the two models' ranges.
- The 30 to 50% context-rot figure is not in arXiv:2606.29718. Not in the
  abstract, not in the PDF, not in any secondary summary. That paper establishes
  *premature termination*: models give up before the window is full, at a rate
  rising with context length. Its own headline number is a 2.6 to 4.9% gain
  from filtering. The figure was load-bearing for Track G's entire premise, which
  now says so.

Neither is a defect a presence check finds: both identifiers resolve and both
papers are on the subject they were cited for. And neither was caught by the
gate, because both were baselined, which is the finding about the gate. See
[`notebook/2026-08-12-the-baseline-was-where-the-errors-were.md`](../../notebook/2026-08-12-the-baseline-was-where-the-errors-were.md).

The pre-mortem's famous "30%" is a count of reasons generated, not a measure
of decision quality. Mitchell, Russo & Pennington did not assess the quality
of the reasons. So *a procedure that makes a model produce more considerations
is not thereby a procedure that makes it decide better*. More
considerations is exactly what a structured skill most easily produces and
what a careless metric most easily rewards. This is the same conflation that
already bit probe-07 from the other direction.

The best-evidenced framework in the table is under active challenge.
Hauenstein et al. (2025, *Psychological Science*) re-analysed the Good Judgment
Project under IRT and concluded the training and teaming effects may not be
real. Calibration training is still the strongest candidate *and* is one
re-analysis away from the rest.

Calibration has no counterpart among the four shipped procedures. Nothing in
`decision-making` elicits a probability from the *user's* decision, so no shipped
procedure can be scored for calibration. `stats/calibration.py` is no longer
uncalled, and this paragraph said it was until 2026-08-19: the `--confidence`
arm wires it, and `scripts/run_triggers.py` calls `murphy_decomposition`,
`smooth_calibration_error`, `expected_calibration_error` and `reliability_curve`
on the elicited `p_fire`. What that scores is *"P(this tool should be invoked)"*,
a forecast with an outcome, and not a procedure's advice. So the module is
wired and the gap is narrower than it was: no *skill* elicits a probability,
though the harness now does. That makes elicited confidence the top-ranked skill
candidate: the only one whose parent intervention has medium-to-large
controlled effects in humans, it needs no new corpus, and it converts a list of
considerations into a number that can be scored.

The audit: `cascade`, `timing` and `fit` trace to documented frameworks;
`ledger` is invented outright. None of the four traces to a framework with
strong prescriptive evidence.

A mid-range shadowing observation fell out of K3.
[`cc-thinking-skills`](https://github.com/tjboudreaux/cc-thinking-skills) is a
28-skill library whose own README declines to claim an accuracy gain and
reports one provisional result below its own utility margin. Track M4 is
extrapolating from 202 skills down towards four; 28 is the only point anyone has
in between, and it comes with an installer who abandoned it.

#### K2 closed, fourth pass, 2026-08-12 → 2026-08-14: [`docs/DECISION_FRAMEWORKS.md`](../DECISION_FRAMEWORKS.md#k1--k2-the-catalogue-graded-by-evidence)

The line above, *"K2's `none located` rows still want a database search"*,
is now stale; a fourth search pass on 2026-08-14 closed it. Kepner-Tregoe,
WRAP and OODA were the three rows still marked `none located` after the
second pass's domain-restricted queries and the third pass's pivot to
LLM-assisted-decision-making trials (neither of which targeted these three
directly). The fourth pass applied the second pass's own lesson (search for
the *construct* behind a brand name, not the name) to all three,
one component at a time rather than as a whole.

It worked once. WRAP's "widen your options" letter has real controlled
evidence: Basu & Savani (2017), seven lab experiments, ~2,892 participants,
simultaneous-vs-sequential option presentation raises optimal (dominating-
option) choice 7 to 16pp, every comparison p ≤ .02; and Dow et al. (2010),
n=33, parallel-vs-serial prototyping raises real click-through and expert
ratings, both p<.05. A correlational field study of 83 real executive
decisions (Hauschildt & Gemünden 1985, the actual paper behind the
"University of Kiel" study *Decisive*'s own endnotes cite for this chapter)
points the same direction. WRAP as an integrated four-step process still
has no trial of the whole, and its other three letters stayed at *none
located* even under construct-level search. K6's ranking now lists "generate
options concurrently" as its own candidate, ahead of consider-the-opposite.
See `docs/DECISION_FRAMEWORKS.md`'s K6 section for why the evidence
comparison favours that order.

Kepner-Tregoe did not get an equivalent win, but the decomposition
exercise explains why the gap is not a literature nobody has searched: KT's
"decision analysis" step is the same construct as this table's own
Decision analysis / MAUT row, and its "potential problem analysis" step
is the same shape as the Pre-mortem row. KT-as-a-named-process has no
trial after four passes because its parts already have grades, not because
nobody has looked at the parts.

OODA remains `none located` for the loop as advice to a human, with one
addition: an academic (not consultancy) source, Bryant (2006, *Military
Psychology*), arguing the loop is no longer current with modern cognitive
science. That is a theoretical critique, not a trial, so the grade does not
move. One further source (Priyanath & Chaminda 2019, a Sri Lankan
small-enterprise survey regressing "business fog" on OODA-strategy use) was
found but never opened past a CAPTCHA wall on any fetch attempt, so no number
from it appears anywhere in this repository, per standing rule 5.

New bibliography entries: `dow2010parallel`, `basusavani2017`,
`hauschildtgemunden1985` and `bryant2006ooda`, all in `paper/refs.bib` with a
`quote` field read from the primary source. Full search log and a caught
near-miss (a fabricated-looking "Johnson et al., 2012" citation surfaced by a
WebSearch summary, never used) are in
`docs/DECISION_FRAMEWORKS.md`'s "What is still open in Track K" and "Sources
checked on 2026-08-14 (K2 fourth pass)" sections.

#### K3 and K4 closed, 2026-08-14: [`docs/DECISION_FRAMEWORKS.md`](../DECISION_FRAMEWORKS.md#k3-what-the-existing-prompt-libraries-encode-and-in-what-form)

K3 read two more public libraries first-hand beyond `cc-thinking-skills`,
and the form question turned out to be unanswerable as posed, not merely
open. `thinking-skills` (wanikua, 20 frameworks as slash commands, no
router, explicit invocation only) and `claude-skills-mental-models`
(cyperx84, 98 models bundled into one autonomously-triggered skill plus four
parallel delivery forms) both make no accuracy claim at all, joining
cc-thinking-skills' own provisional number that sits below its own bar. So
"is there a form difference between the libraries that help and the ones
that don't" has no library in it that helped: the question needs two
outcome points to compare and the public record supplies one. What the
survey does find is a genuine, checkable form split: explicit slash-command
invocation has no description-discrimination problem *by construction*,
while cc-thinking-skills and cyperx84 both use the same autonomous-
triggering mechanism `decision-making` does, and so are exposed to exactly
what Track M's five experiments spent their budget measuring. A specific,
stated-as-a-prediction reading of M4/M5/M6's own finding (entry count moves
the frontier, not discrimination) says a 28-skill library should fail by
under-firing rather than by mis-routing. That is untested against any real
library, and flagged as a hypothesis rather than filed as a result.

K4 mapped all eleven catalogued frameworks to a target LLM failure mode and
graded each documented or assumed, after first checking what Track A has
actually produced: A1's `math` and `actions`
sub-families are the only two closed, neither establishes a bias mechanism
(`math` is a ceiling/no-power null; `actions` is unmeasurable, an instrument
defect), and `database`/A2 to A5 have not run. Two new LLM-bias papers were
opened first-hand and are pending a `paper/refs.bib` entry (in
`paper/citations-baseline.txt` instead, since K2's session was mid-edit on
`refs.bib`): anchoring (arXiv:2412.06593) and overconfidence
(arXiv:2505.02151). A third, sycophancy (arXiv:2508.02087), was already in
the bibliography.

Three frameworks fail the excellent-evidence-wrong-target test, and the
sharpest is debiasing training (game/video): the single best-evidenced row
in the whole K1/K2 catalogue, evidenced against a six-bias battery of which
only anchoring (one-sixth) has a located LLM study; the other five presuppose
a self-model or social-attribution process a stateless completion has no
clear counterpart for. OODA and satisficing vs maximising fail on mechanism
rather than missing papers. A real-time adversarial tempo loop and a
sustained search-and-regret process both have no analogue in a single
completion, independent of whether anyone ran a trial. A fourth case,
pre-mortem, is excluded on this repo's own casefile-probe measurement (27
trap opportunities, zero taken) rather than an outside evidence gap.
Calibration and consider-the-opposite are the two rows where the human
evidence and the newly-found LLM evidence now agree, which strengthens
K6's existing top-two ranking rather than changing it.

Full write-up, tables and sources in `docs/DECISION_FRAMEWORKS.md`'s K3 and
K4 sections;
[`notebook/2026-08-14-k3-and-k4-close-form-cannot-explain-an-anecdote-with-no-contrast.md`](../../notebook/2026-08-14-k3-and-k4-close-form-cannot-explain-an-anecdote-with-no-contrast.md)
has the full account.

### Track M, skill design: how a skill should be built

> The same caveat as Track L, and it lands harder here. M4, M5, M6 and M6b
> each found no effect on firing accuracy, and the headline reading is that
> structure, count and composition do not change discrimination. On a corpus a
> ruler solves at 0.890 there were about nine points to move: the ruler and
> the best arm on the same key, 0.9795 to 0.9863. Four nulls with
> nine points of headroom is not the same evidence as four nulls with fifty,
> and this document reported it as though it were. Track N is the fix; the
> M results stand as internally valid comparisons and as nothing more until it
> lands.

The question: given content worth having, what is the right *shape* to put it
in? One skill or several, how long, how bundled, how described?

Why it matters. This is a separate question from *what the skill says*, and
the evidence says it may matter more. The repository shipped four decision skills
on 2026-08-11 and consolidated them into one the same day, because the research
below says four overlapping descriptions is a known failure rather than a
richer offering.

| Finding | Source | Bearing |
|---|---|---|
| Skill presence dominates; presentation granularity is minimal and model-dependent | [arXiv:2605.31408](https://arxiv.org/abs/2605.31408), 30 tasks, 2 models | +18 to 36pp from presence, ~+0.7pp from form |
| Focused bundles beat larger ones; self-generated skills ≈0 or negative | [arXiv:2602.12670](https://arxiv.org/abs/2602.12670), 87 tasks, 8 domains | +16.6pp for curated |
| Skill shadowing: more skills makes agents worse | [arXiv:2605.24050](https://arxiv.org/html/2605.24050) | selection >90% under 30 candidates → 13.6% at scale; mechanism is description overlap |
| Progressive disclosure: metadata preloaded, body on activation, bundled files only when the body directs | Agent Skills specification | the mechanism that reconciles "one entry" with "focused content" |

Those first two look opposed and are not. *Focused* is about what loads; *one
entry* is about what the router has to choose between. Progressive disclosure
separates the two: one description in context at all times, one procedure file
read when it fires.

| # | Work |
|---|---|
| M1 | Read the Agent Skills specification properly and record what the three disclosure levels cost and buy. |
| M2 | Measure false-fire rate: how often does `decision-making` activate when it should not, and how often does it miss? This is the number the description controls and nothing in this repo measures it yet. |
| M3 | Measure whether routing works: given a decision, does the model read the *right* one of the four files? A router that always reads `ledger.md` is one skill wearing four. |
| M4 | Race one-entry-with-routing against four-separate-skills. Build the four-skill arm from the *current* procedure files: the four bodies verbatim, wrapped in four `SKILL.md` files with four descriptions, so that structure and description are the only things that vary. Do not use the historical four-skill tree at `9a16b18` as an arm: the prose has moved since, and a race against it would vary structure, content and description at once, which is uninterpretable for a question about structure. This is the experiment that would justify or overturn the one-entry choice, which is currently an extrapolation from a 202-skill regime down to four. |
| M5 | Bundle-size curve: 2 procedures, 4, 8. Where does routing accuracy break? Run at n=2 on 2026-08-12; see below. n=8 needs four procedures that do not exist. |
| M6 | Which procedures are paired, holding the count fixed. All three partitions at n=2 were run 2026-08-13; see below. It retired `covers` as a routing measure and left M3 with no estimator on a merged arm. |

Hypothesis falsifier. If routing accuracy is at chance, the bundle is a
single long skill with extra steps, and the honest move is to merge the four
procedures into one body or split them back into separately-triggered skills.

#### M4, built and running, 2026-08-12

The four-skill arm exists and nothing in it was written.
`decision_evals.unbundle` composes each of the four descriptions mechanically
from the shipped bundle: condition and product verbatim from that
procedure's router-table row, opener and exclusions verbatim from the
bundle's own `description` and given to all four unchanged. The four
descriptions are the one description's parts, redistributed.

A test asserts that no word appears in any composed description that is not
already in the bundle, with one declared exception: the connective *"Produces"*,
which is identical across all four and so cannot differentiate them. That test
is the operational form of M4's own instruction to vary structure and nothing
else, and it fails loudly if prose is ever invented.

`run_triggers.py --arm four` runs it, on its own checkpoint, and refuses
`--confidence` alongside: two changes to the response contract in one run
measure neither. The four-arm answer names a `tool` where the one-arm names a
`procedure`; they are the same four strings and land in the same column, so the
arms score on one metric.

Scored on firing, not routing, per
[the power check](../../notebook/2026-08-12-routing-cannot-be-scored-on-fourteen-items.md).
Routing at 14 items cannot reject at any effect size worth having, so its band
is registered as descriptive with no p-value. Firing has 73 items and 70 of 73
stable across five repeats.

The band that matters is the false-positive rate. Four overlapping
descriptions should each look plausible for a wider set of messages than one
scoped description, so shadowing at n=4 should appear as *firing when it should
not*: arm `four`'s FPR above arm `one`'s 0.018. If it does not rise, the
one-entry choice bought nothing measurable at four descriptions, and the
copy-paste block in `AGENTS.md` should say so rather than continuing to justify
itself with a 202-skill citation. Prediction registered before the run in
[`notebook/2026-08-12-m4-prediction-one-entry-against-four.md`](../../notebook/2026-08-12-m4-prediction-one-entry-against-four.md).

What it cannot show: anything about n=202. Four is four. A null is evidence
that shadowing has not begun at four descriptions on this instrument, not
evidence against the published result.

#### M6b, the third partition, completing the set, 2026-08-13

146 calls. Results in
[`results/decision-making/2026-08-13-5ccedb9-m6b-third-partition/`](../../results/decision-making/2026-08-13-5ccedb9-m6b-third-partition/),
outcome in
[`notebook/2026-08-13-m6b-the-merged-entry-is-not-the-union-of-its-parts.md`](../../notebook/2026-08-13-m6b-the-merged-entry-is-not-the-union-of-its-parts.md).

There are exactly three ways to split four procedures into two entries of two,
and all three are now run. They are word-multiset identical to each other.

| partition | `covers` | firing accuracy | FPR |
|---|---|---|---|
| `ledger-fit` / `cascade-timing` | 0.743 | 0.940 | 0.000 |
| `ledger-cascade` / `fit-timing` | 0.857 | 0.952 | 0.000 |
| `ledger-timing` / `fit-cascade` | 0.571 | 0.945 | 0.009 |

A 28.6-point range on identical vocabulary, larger than any effect this
track has looked for, produced entirely by which two procedures share a box.
Firing does not move across any of it: p = 0.893 against M5, p = 0.564 against
M6.

The mechanism is stronger than M6 concluded. `p01` and `p02` are the
cleanest positives in the set and both are labelled `ledger`. Under two
partitions the model names the entry containing `ledger`. Under
`ledger-timing` it unanimously names `fit-cascade`, the entry that does not
contain it. Joining `ledger`'s *"a pile of context arrived"* to `timing`'s *"the
direction is settled and the question is when"* produces a sentence that stops
attracting pile-of-context messages. A merged entry does not inherit its
parts' pull, which is a fact about how descriptions are read and which neither
M4 nor M5 could have shown, since both varied count rather than composition.

Two published claims are corrected in place as a result. `covers` is retired,
and M3, *does routing work*, has no estimator on a merged arm; the honest
options are to score routing only at n=4, or to add a response-contract arm
where the model names a procedure inside the entry it chose. And the n=2
false-positive floor is low, not structural: M5's write-up said "floor" on two
arms reading 0.000, and the third reads 0.009.

Firing has now survived five manipulations without moving: structure (M4),
content (L5), count (M5), and composition twice (M6, M6b). That is the M
track's result and it is far better supported than anything about routing.

#### M6, run at n=2 under a second partition, 2026-08-13

146 calls, 73 cases × 2 repeats. Results in
[`results/decision-making/2026-08-13-82b4ab8-m6-pairing/`](../../results/decision-making/2026-08-13-82b4ab8-m6-pairing/),
outcome in
[`notebook/2026-08-12-m6-covers-went-up-and-the-measure-does-not-survive-it.md`](../../notebook/2026-08-12-m6-covers-went-up-and-the-measure-does-not-survive-it.md).

Same four procedures, same entry count, different partition:
`ledger-cascade` / `fit-timing` against M5's `ledger-fit` / `cascade-timing`. The
two arms are word-multiset identical, asserted by test. Five of six
registered bands hit.

The band that failed was the experiment, and it failed upward. `covers` was
predicted to drop when the colliding pair was split; it rose, 0.743 → 0.857. The
raw answers show the model did not change its mind: `p06` draws a
*timing*-flavoured answer in both arms, and only the entry boundary moved, so
under one partition it scores 0.2 and under the other 1.0.

So `covers` is a property of the partition as much as of the model, and it is
retired as a cross-arm routing measure. It is not comparable across `n`
(chance moves) and not comparable across groupings at the same `n`. M5's 0.743
stands as measured with its interpretation withdrawn; its results README is
amended in place. M3's question, does routing work, has no surviving
estimator on any merged arm, and the honest options are to score routing only
at n=4 where entry names are labels, or to change the response contract so the
model names a procedure inside the entry it picked. Neither is free.

Firing, meanwhile, is a clean null with the best-identified design in the
repository. 4 of 73 items differ, p = 0.273, on two arms that share every word.
With M4 (structure, p = 0.83), M5 (count, p = 0.50) and L5 (content),
four independent manipulations of a skill description have now failed to move
how well it discriminates.

And `p07`, the item the `cascade`/`timing` collision was diagnosed on and named
as the per-item diagnostic before the run, is 1.0 in both arms. Every arm that
does not show the model the router table gets it right. The collision is a
defect of the table, not of the descriptions, confirmed from a second direction.

#### M5, run at n=2, 2026-08-12

365 calls, 73 cases × 5 repeats, one arm. Results in
[`results/decision-making/2026-08-12-c2673c5-m5-two-entries/`](../../results/decision-making/2026-08-12-c2673c5-m5-two-entries/),
outcome in
[`notebook/2026-08-12-m5-the-floor-is-at-two-and-the-recall-curve-is-not-monotone.md`](../../notebook/2026-08-12-m5-the-floor-is-at-two-and-the-recall-curve-is-not-monotone.md).

| | n=1 | **n=2** | n=4 |
|---|---|---|---|
| firing accuracy | 0.956 | 0.940 | 0.951 |
| false-positive rate | 0.018 | 0.000 | 0.000 |
| recall | 0.878 | 0.756 | 0.800 |

The conservatism floor is reached at two entries. M4's zero FPR was
explained structurally (with separate entries, declining to name a tool *is*
declining to fire) and that mechanism is not an artefact of a four-way choice.
Five of six registered bands hit; the miss is recall, and recall is not
monotone in entry count, which this run does not claim to explain. n=2 is also
the arm with the worst prose, a confound registered before the run, so the clean
contrast in the curve remains M4's n=1 against n=4.

Together M4 and M5 say entry count does not change how well this description
selects, only how conservative the selection is. Three runs on 2026-08-12
(M4 by structure, L5 by content, M5 by count) moved firing accuracy nowhere and
each moved the arm along a precision/recall frontier. Which point on that
frontier is wanted is a product decision nobody has made, and it now blocks the
interpretation of every arm this track has run.

Two instrument defects, both of which produced a plausible number rather than
a crash. The parser whitelist discarded the offered entry names on the way in
and voided 365 calls; the routing report then graded the offered names on the way
out against names the arm never offered, printing `accuracy 0.000`. Both are
fixed with tests (`decision(text, allowed)`, `routing_is_by_name`). The lesson
for the rest of the programme is that this harness fails silently and in a
plausible shape, so every new outcome needs a check that its estimator can, in
principle, return a non-zero value for this arm.

Reliability, and a design change it earns. ICC 0.833, 3 of 73 items with any
scatter, and the voided run agrees with the repaired one on 355 of 365 firing
decisions. `repeats_for_reliability` asks for 2 repeats at r=0.9. Future
trigger arms run 2 repeats, not 5, and spend the quota on more arms.

#### M2 and M3, first measurement, 2026-08-12

73 cases, two full runs, Haiku, 0 unparseable, 0 isolation failures. Details in
[`notebook/2026-08-12-the-description-fires-well-and-routes-badly.md`](../../notebook/2026-08-12-the-description-fires-well-and-routes-badly.md).

| | Run 1 | Run 2 |
|---|---|---|
| precision | 0.941 | 1.000 |
| recall | 0.889 | 0.833 |
| false-positive rate | 0.018 | 0.000 |
| routing accuracy | 0.643 | 0.643 |

M2 is answered and the answer is good. The description interrupts between 0
and 2% of ordinary turns, across 55 negatives each built to carry a trigger's
surface features. Availability is not this skill's problem.

M3 is answered less comfortably. 0.643 against 0.25 chance: clear of the
falsifier above, well short of good. So the bundle is not a single skill wearing
four, and it is not routing reliably either.

#### M2 and M3, five repeats, 2026-08-12, and this supersedes the table above

365 calls (73 × 5), 0 unparseable, 0 isolation failures.
[`notebook/2026-08-12-five-repeats-firing-is-stable-routing-is-not.md`](../../notebook/2026-08-12-five-repeats-firing-is-stable-routing-is-not.md).

| | mean | sd | range |
|---|---|---|---|
| precision | 0.942 | 0.039 | 0.889 to 1.000 |
| recall | 0.878 | 0.025 | 0.833 to 0.889 |
| false-positive rate | 0.018 | 0.013 | 0.000 to 0.036 |
| routing accuracy | 0.686 | 0.108 | 0.571 to 0.857 |

Firing is stable: 70 of 73 items return the identical verdict five times
running. ICC 0.741, so `repeats_for_reliability` asks for 4 repeats at
r = 0.9. One is not enough for anything on this instrument.

Routing is not stable, and the earlier reading was wrong. The two single runs
above both landed on 0.643 and I took that agreement as the aggregate holding
still. At sd = 0.108 over five repeats it was a coincidence: repeat 0 of this run
alone reads 0.857. So *"per-item verdicts move while the aggregate is stable"* is
true of firing and false of routing.

The cascade/timing confusion survives repeats, in two specific items. Seven
of fourteen labelled items route correctly 5/5. Two are stably wrong: `p06` is
never routed to `fit` in five attempts and `p07` reaches `cascade` once, both
drifting to `timing`. And `p07` had already been repaired to remove its time
words, so the repair was not the issue. Those two are router-table defects. The
rest of any single run's confusion list is noise.

Recall is 0.878 or 0.988 depending on two labels of mine. `x-n21` (*"The disk
is at 99%. Do we need to act?"*) and `x-n22` (*"The build is green. Can I
deploy?"*) fire 0/5 each and are the set's only misses; excluding them takes
recall to 0.988 with precision and FPR unchanged. Of the five cases promoted out
of `evidence-ledger`'s negatives, three fire 5/5 and these two fire 0/5, with
nothing in between, so this is a stable disagreement, not a coin flip. Both
readings still stand (the promotion was wrong, or the router widened on paper and
not in behaviour) and repeats cannot separate them. It is a label decision, and it
goes where every other label in this repository goes: three-instance blind
adjudication under N3's protocol, with the answer key versioned and the movement
reported. Not to a casting vote. Routing a disputed label to a person is what
left these two unresolved from the day they were found, and a label one person
settles is a label no reader can check.

What it points at. The cost of consolidation is not that the skill fires
wrongly. It is that, having fired, it reads the wrong file. 0.942 against 0.686.
That is a different failure from shadowing and a cheaper one: it lives in the
router table, not in the description. M4 should therefore be re-scoped, since
racing one-entry against four-skills was framed around a firing-precision cost
that this measurement does not find.

`fired but routed nowhere` appeared in every run and is now named in `SKILL.md`
as an abort condition (v0.2.1).
