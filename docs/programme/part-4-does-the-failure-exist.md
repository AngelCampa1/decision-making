# Part 4: does the failure exist

**Audience:** the evaluating reader, and in particular anyone picking up a track.

Tracks A and B. Replicating the context failure the whole programme assumes, and
attributing it. Three corpora were built before anyone asked this.

Part 4 of eight. The tracks table, the venue map, the sequencing and the
claim ladder are in [`RESEARCH_PROGRAMME.md`](../RESEARCH_PROGRAMME.md).
Headings below start at `###`, carried over from the split so that a track's
anchor is the one it had in the monolith.

---

Before asking whether a skill fixes a failure, show the failure happens here.
Three corpora were built without this.

### Track A: replication

The question: do the failures the literature reports actually happen on our
stack, our models, our tasks?

Why it matters. This is the repository's cardinal error, stated plainly: three
corpora were built to fix a failure that was never shown to exist here. A skill
cannot help with a failure that does not occur. Track A is cheap, roughly 1,200
calls and a few hours of wall clock, and it can kill or redirect everything
downstream before a single document is authored.

Run this first. It is the highest-value work in the programme.

Instrument falsifier. If A1 to A5 are all flat, the failures do not exist at
this scale on this stack, and the programme needs a harder task family before
any skill work. That is a real finding and it gets written up as one.

| # | Experiment | Design | Prediction registered before |
|---|---|---|---|
| A1 | Multi-turn drop | Adopted, and now vendored. `microsoft/lost_in_conversation` (MIT), corpus CDLA-Permissive-2.0, pinned at commit `c865793` with a SHA-256 in `datasets/vendor/lost_in_conversation.lock.json`; `de fetch` downloads it and the loader refuses anything that does not match. This removes the activity with this repo's worst record: three discarded corpora, 21/21 key errors. Still needed: a `model_claude_code.py` shim; their only backend is OpenAI. Three things were measured on retrieval, each contradicting something we had written down. See below. | yes |
| A2 | Recency over-weighting | Decisive fact placed at first / middle / last turn, total turns fixed. Flat means no recency effect here and Track C changes shape. | yes |
| A3 | Handoff loss | Sub-agent reads the documents and reports; orchestrator decides from the report alone vs from raw documents. The gap is compression loss. Also: *which* facts survive. | yes |
| A4 | Does delegating even help? | One agent with everything vs orchestrator + sub-agents, same task. If single wins, the skill's job changes from "delegate better" to "know when not to delegate." | yes |
| A5 | Reliability | *k* repeats per item at each venue. Measure the scatter, not the mean. | yes |

What the vendored corpus actually contains, measured 2026-08-11 by
`decision_evals.corpora.shard_summary` rather than read off the paper:

| We had written | The file says |
|---|---|
| 600 instructions | 627 records, so the filename is wrong, not the count |
| 7 task families | 6 present: actions, code, data2text, database, math, summary. The seventh, `translation`, is a separate file (`data/sharded_translation.json`) |
| sharded "across ~6 turns", flagged as invented | mean 5.97, median 6, range 3 to 12. The invented figure was *right*, and it was still invented. It is now measured |
| skip `code` (Unix-only eval) | leaves 527 records, mean 5.78, median 6 |

The turn-count spread is the part that changes a design. A corpus running 3 to 12
turns is not a fixed-length instrument, so any per-item comparison has to carry
turn count as a covariate rather than assume it away. A2, which holds total
turns fixed while moving a fact, cannot simply reuse A1's items.

The A1 pilot ran on 2026-08-12, and forty of its sixty records were void. The
run completed cleanly: 30 pairs, 190 generations, 0 failures, all 30
conversations accumulating. But `database` was asked for SQL with no schema in
the prompt and `actions` was asked to call a function with none offered. Both
families carry that material in the corpus (`schema_sql`, `function`); the
runner never rendered it. Those twenty items were unanswerable, not hard.

It survived a first reading because the traces are good. Asked which countries'
TV channels air a Todd Casey cartoon, with no database, the model said it has no
access to TV listings and suggested IMDb, the right answer to the question it
was actually asked.

Three things follow, and they outlast the pilot:

- `math` was not "the only family with a mechanical key". It was the only
  family whose task was fully delivered; a word problem carries its own numbers.
  The `p_discordant` = 0.10 measured on it stands, and it is still near ceiling.
- A run can be clean and void at once. Every instrument check passed. What was
  missing was a check that the task arrived, which is now `TASK_CONTEXT_FIELD`:
  declared per family, no default, refusing to run an item that is declared to
  need context and does not carry it.
- `ShardedRecord` stores the system prompt verbatim. The defect lived there and
  nothing in the record showed it.

Neither `database` nor `actions` can be graded here even repaired. Spider's
metric is execution accuracy and the databases are not vendored; BFCL's is an AST
match on a parsed call, and nothing in the run asks for a parseable call.
Substituting for either is authoring a key while pointing at a vendored one, so
they report format compliance and, for `database`, a string match labelled as a
lower bound.

The re-run on 2026-08-12 closes `math` as an A1 venue. 30 pairs, 180
generations, 0 failures, $1.45. The repair is visible in one number: `database`
went from prose about TV listings to 10/10 producing SQL in both conditions.

| Family | Measure | Discordant | full | sharded |
|---|---|---|---|---|
| `math` | correct (GSM8K key) | 0/10 | 10 | 10 |
| `database` | produced SQL | 0/10 | 10 | 10 |
| `actions` | named the required function | 2/10 | 10 | 8 |

`p_discordant` on `math` is 0.000, so the family has no power at any sample
size: McNemar's effect is bounded by the discordant share. The first pilot's
0.10 was one item, and repeating the identical condition got that item right;
`math` per-item agreement across the two runs is 19/20, so the aggregate was
stable and the single disagreement *was* the entire signal. Third appearance of
the aptitude-versus-unreliability split ([arXiv:2505.06120](https://arxiv.org/abs/2505.06120)),
and the cleanest.

The signal is in `actions`, which inverts the earlier reading. Two of ten pairs
discordant on function-naming, both in the paper's direction (p = 0.25 exact at
n=10, nowhere near significant, and the only non-zero discordance the pilot
produced). `math` looked like the family to build on only because it was the one
whose task had been delivered; with all three delivered it is the one with
nothing left to measure.

So A1 cannot be sized from `math`. Three options, and the choice is a corpus
decision: size on `actions` function-naming and accept a capability floor as the
outcome; vendor the spider databases so execution accuracy becomes available;
or find harder `math` items, since GSM8K at 10/10 is not the hard end of
anything. None of this says the multi-turn effect is absent. It says this venue
cannot currently see it, which is a Phase 0 result rather than a finding.

`actions` closed too, later on 2026-08-12, after three runs and 1,105
generations. Option 1 above is dead. Not for lack of an effect, but because no
object is comparable across the arms. The scorer reads `final_response`; `full`
has one turn and `sharded` has five to eleven. Four different objects were tried
on the same 100 responses and each gave a different verdict:

| what is scored | `full` | `sharded` |
|---|---|---|
| final response, no closing turn | 45 named | 23 |
| final response, with closing turn | 50 named / 47 AST | 4 / 1 |
| the last shard's reply | 50 / 47 | 27 / 13 |
| naming anywhere in the conversation | 50 | ~49 |
| the union of all calls emitted | n/a | breaks BFCL's bijection: 8 calls against a reference of 4 |

The number that ends it: of the 23 sharded conversations whose last shard
carried no parseable call, 23 had emitted one earlier. No exceptions. The arm is
not failing to call. It calls, correctly formatted, and then keeps talking.

And no wording escapes it. *"Give your final answer now, complete and
self-contained"* means *the calls* in an arm that has said nothing yet and *a
summary of the results* in an arm that made them four turns ago. Both arms get
both instructions and resolve them differently because they are in different
states, and the state difference *is* the independent variable. An instruction
demanding the calls be repeated at the end would measure whether a model
restates finished work.

So the two closures are different and must not be merged in the write-up:
`math` answers the question and says no (`p_discordant` = 0.000, a real
measurement); `actions` says the question cannot be put this way (the
measurement does not exist).

What survives is instrument, and it is not nothing. `--call-format` took the
single-turn arm from 18/43 parsed to 50/50 named and 47/50 matching on BFCL's
own published AST metric, so the harness can grade this family. It just cannot
pair it. Two guards now encode the defect rather than a memory of it:
`final_responses_comparable` refuses a run with no closing instruction, and
`actions_report` refuses the paired naming comparison without a call contract.
Both defects had already produced a publishable-looking false replication
(45/50 against 23/50, discordance 24-to-2 in the predicted direction).

Option 2 is now the leading one and nothing in it waits on a person. Vendoring
the spider databases means downloading a third-party dataset, which is precisely
what [`AUTONOMOUS_WORK_ORDER.md`](../AUTONOMOUS_WORK_ORDER.md)'s outside-data rule
is for: free, redistributable, licence read first-hand, a sample read for
personal information, a digest pinned in `datasets/vendor/*.lock.json`. The rule
is the decision procedure, so executing it is the approval. Four steps, all
free, and a source failing any one of them is not vendored. Whether Spider's own
terms clear that bar is not asserted here, and reading them is the first of the
four.

One consequence for the rest of Track A, and it is good news. A1 compares a
one-turn arm against a six-turn arm, which is why no object is comparable. A2
does not: it holds total turns fixed and moves a decisive fact between
positions, so both arms have the same turn count, the same shards and the same
place for the answer to land. A2 is immune to the defect that closed A1 by
construction, and it is the next A-track experiment for that reason as well as
its own.

What A2 still needs is headroom, which is option 3 rather than option 2. A
position effect cannot be seen at 10/10, and `math` sits at 10/10 in both arms,
so A2 inherits A1's need for harder items even though it escapes A1's
measurement problem. Those are two separate blockers and only one of them has
been solved.

Also recorded: prediction 7 of that run was unscoreable as written. It asked
for `p_discordant` on families that have no correctness measure here, which was
known when it was registered. A pre-registered band needs the estimator named,
not only the number.

Sample sizes and detectable effects, consolidated on 2026-08-18. Three of these
numbers already exist, scattered across two notebook entries, a CLI table
(`de power`) and the prose above; two of the five experiments have never had a
pair count, a repeat count or a design effect written down anywhere in this
repository, and a grep of the whole tree comes up empty for both. The table
below calls `stats/power.required_pairs` and `minimum_detectable_effect`
directly, and it counts the
corpus on disk rather than trusting the figures already written about it, the
same discipline the 527-to-315 correction above cost an hour to learn.

The `design_effect ≈ 2.0` used throughout the A-track prose above is not
derived. It is `cluster.py`'s own worked-example number (six variants per
template, ICC 0.2), carried in as a stand-in. Nothing in the vendored corpus has
the structure to compute an ICC from: the only groupable unit is task family,
and three to six families is too few groups for `intraclass_correlation` to
return anything stable. So it has never been replaced with a measured value the
way Track N replaced its own placeholder with
`design_effect(m=3, icc=0.315) = 1.63`. What would replace it: an ICC computed
from repeated draws within one task family, which needs the same repeat
measurements A5 is supposed to produce.

| # | Paired unit | Pairs available (counted off the corpus, not read from prose) | Repeats | Design effect | MDE @ 80% power | Status |
|---|---|---|---|---|---|---|
| A1 | one instruction (`task_id`), full-condition response vs. sharded-condition response | 315: `actions` 105 + `database` 107 + `math` 103, each carrying that family's own full-setting field (`fully_specified_question` or `question`). Counted directly off `sharded_instructions_600.json`; matches the pre-registered figure | 1. No repeats were run; no ICC has ever been measured for this venue | assumed 2.0 (see above) | 5.4 to 9.9pp unadjusted, 7.6 to 13.9pp at the assumed design effect, `p_discordant` swept 0.15 to 0.50 | closed, and not by reaching that MDE. `math`'s observed `p_discordant` is 0.000, so `minimum_detectable_effect` raises `ValueError`: no effect is detectable at any `n`. `database` and `actions` closed on instrument grounds (no gradable object, no comparable object across arms), so the run that actually closed them used 10 pairs per family, not 315 |
| A2 | one instruction at a fixed shard count, decisive fact at first / middle / last turn | 212, counted directly off `sharded_instructions_600.json` for the 6-turn stratum across the five non-`code` families. Not 233: the figure this document and `cli.py`'s `POWER_ROWS` both carry for "the largest shard-count stratum" still includes `code`, which every other line in Track A treats as ungradable on this stack. Restricted further to the three families A1 actually established as gradable (`actions` / `database` / `math`), the largest single-turn stratum is 103 (4 turns), not 212 and not 233 | never written down | assumed 2.0, same as A1, never computed | 6.6 to 12.0pp unadjusted / 9.3 to 16.9pp at DE=2.0, `n`=212; 9.4 to 17.1pp / 13.1 to 24.0pp at `n`=103 if restricted to gradable families | not yet run. Which of the three pairwise position comparisons is the primary registered test is also not stated anywhere |
| A3 | undecided; provisionally, one document set handed to a sub-agent, orchestrator decides from the report vs. from the raw documents | never written down. No corpus exists; A3 needs Track 0's multi-agent transport, which needs `--tools ""` relaxed and has not run | never written down | never computed | not computable: there is no `n` to hand either power function | not run |
| A4 | undecided; provisionally, one task, single agent with everything vs. orchestrator + sub-agents | never written down, same Track 0 dependency as A3 | never written down | never computed | not computable | not run |
| A5 | *k* repeats per item, at whichever of A1 to A4's venues it runs against | n/a: A5 is a repeat-count question, not a pair-count question | never written down. `stats/reliability.repeats_for_reliability(icc, target)` is exactly the function this needs, but it takes an ICC as input, and no venue in A1 to A4 has ever had a repeat measured to compute one from | n/a | not computable: the repeat count needs the ICC and the ICC needs the pilot A5 itself would be | not run |

Confirmed against
[`notebook/2026-08-11-twelve-items-could-not-have-found-anything.md`](../../notebook/2026-08-11-twelve-items-could-not-have-found-anything.md),
whose own line already said it: *"A3, A4 and A5 have no item count yet because
they have no corpus yet."* Nothing built since has changed that, and this table
is the first place it is said about repeats and the design effect too, not
only about item counts.

Depends on Track 0.

Done when there are five notebook entries, each with its numeric prediction
written *before* the run, and one table saying which effects reproduce and how
big they are on our stack.

### Track B: attribution

The question: when the system produces a bad decision, which node caused it?

Why it matters. Twenty-one of twenty-one scored failures so far were answer key
errors, not model errors. A multi-node trace multiplies the surface area for
that mistake. Nothing downstream can be believed without this.

MAST is the citable prior, confirmed or refuted against our traces. Confirming
it that way is the same bottom-up method `docs/FAILURE_TAXONOMY.md` already
uses, which is what caught the false "appeals to real-world considerations" signal.

| # | Experiment |
|---|---|
| B1 | Port MAST's 14 modes into a codebook mapped onto our trace schema; mark which are unreachable in each venue, as `FAILURE_TAXONOMY.md` already does. |
| B2 | Per-node scorer: score a trace at every node, not only at the final answer. |
| B3 | Blind adjudication extended to multi-node traces. The pre-registered >20% key-amendment kill carries over unchanged. |
| B4 | Inter-annotator agreement on our own coding, reported. MAST reports κ=0.88; a number below that is a result about our codebook. |

Depends on Track 0 for trace structure; runs alongside Track A on its traces.

Done when every Track A failure has been read and coded, agreement is reported,
and the amendment rate is under 20%.
