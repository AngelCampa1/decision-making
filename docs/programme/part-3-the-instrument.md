# Part 3: the instrument

**Audience:** the evaluating reader, and in particular anyone picking up a track.

Tracks 0 and N. Multi-turn and delegation, and whether the trigger corpus behind
every published number is a fair test. Two instruments, one of them audited. This
part blocks the measurement and leaves the product free to ship.

Part 3 of eight. The tracks table, the venue map, the sequencing and the
claim ladder are in [`RESEARCH_PROGRAMME.md`](../RESEARCH_PROGRAMME.md).
Headings below start at `###`, carried over from the split so that a track's
anchor is the one it had in the monolith.

---

Blocks the measurement. Does not block the product.

Two instruments, and only one of them was ever audited. Track 0 is the
transport: can this stack run a multi-turn, delegating system under control.
Track N is the *corpus* that every Track L and Track M number was computed
from, and until 2026-08-13 nobody had asked whether it was a fair test. It was
not.

### Track 0, instrument

The question: can this stack run a genuinely multi-turn, genuinely delegating
system under experimental control?

Why it matters. `ISOLATION_FLAGS` in
`evals/src/decision_evals/providers/claude_code.py` hard-codes `--tools ""` and
`--no-session-persistence`. The first blocks sub-agent dispatch; the second
blocks session resume. Nothing in V2, V3 or V4 can run today. This is the
same class of blocker as the argv-length defect: the instrument cannot produce
the phenomenon, and it would have been discovered after authoring the corpus.

And the flags are not incidental. `notebook/2026-08-10-isolation-canary.md`
records that a `CLAUDE.md` planted in the working directory is injected even
when the system prompt is fully replaced; `--setting-sources ""` is the flag
that actually stops it. Opening `--tools` reopens paths that were closed for a
measured reason. Every relaxation needs its own canary.

The design call: scripted orchestration, not the real Task tool. The
orchestrator is our Python code driving separate isolated `claude -p` calls, one
per node. We then control exactly what each node sees, can ablate or substitute
a sub-agent report, and keep `--tools ""` at every node. The real Task tool is
ecologically truer and experimentally useless, because we could not hold
anything fixed. It returns in Track F as a validity check, not as the
instrument.

> Resolved 2026-08-11, before any of this ran, and the falsifier was wrong.
> Multi-turn already works, under the full isolation stack with no flag
> relaxed. `--no-session-persistence` blocks `--resume`, which is
> cross-process; it does not block multi-turn, because with `--input-format
> stream-json` turns go to one live subprocess's stdin and context carries
> in-process. Reproduced: turn 3 recalled a codeword from turn 1 with an
> unrelated turn between, `input_tokens` 179 → 410 → 513.
>
> The original falsifier read "`cache_read` must climb turn over turn".
> `cache_read` was 0 on every turn while context demonstrably carried.
> Caching is a billing optimisation, not a transcript mechanism, and short turns
> never reach the threshold. Run as written, 0.1 would have declared a healthy
> venue dead.
>
> So Track 0 is not a hard gate for A1 and A2. The transport is ~80 lines of
> `Popen` plus JSONL. Track A's real prerequisite is the MDE calculation, not
> the harness. Full record in
> [`notebook/2026-08-11-multi-turn-already-worked.md`](../../notebook/2026-08-11-multi-turn-already-worked.md).

Instrument falsifier, corrected. Prior turns are in context iff
`input_tokens` climbs monotonically *and* a behavioural recall check passes.
Two independent signals, because the first can be explained by a longer question
and the second by a lucky guess. `cache_read` is not evidence either way.

| # | Experiment | Cost |
|---|---|---|
| 0.1 | ~~Session-resume canary~~ Done, and folded in. `Conversation` now lives in `providers/claude_code.py` beside the single-shot path, sharing `build_command` so the isolation flags cannot be forgotten on the streaming form either. Re-verified through the shipped class: `input_tokens` 179 → 334 → 422, turn 3 recalled the turn-1 codeword with an unrelated turn between, `cache_read` 0 on every turn. The transport is unit-tested against a fake process at 100% line+branch, and `tests/integration/test_multiturn.py` (marked `llm`) asserts the corrected falsifier against a live model. | done |
| 0.2 | Done 2026-08-12. `decision_evals/orchestrator.py`, 100% line+branch. 1 orchestrator + 3 sub-agents, fan out once and aggregate once, per-node `NodeRecord`s carrying node/parent/operation. The split is scripted rather than model-chosen, because a model-chosen split varies between arms. `Dispatch.transform` is the seam the module exists for: pass through is the control, drop is an ablation, substitute is Track B's attribution. The record stores *both* what the node said and what the parent read, because when they differ that difference is the manipulation. Ran live: 8 nodes across 2 trees, $0.039 notional. | done |
| 0.3 | Done 2026-08-12, and it forced a design decision. The isolation receipt is the `system`/`init` event, which only `--output-format stream-json` emits, and the single-shot JSON form gives no receipt at all. So asserting isolation *at every node* forces the streaming transport everywhere, including single-turn nodes. The alternative was asserting at the root and assuming for the leaves, which is the assumption a delegation experiment least deserves. 8/8 receipts asserted; fresh cwd per node, because the auto-memory path is keyed on it. | done |
| 0.4 | Done 2026-08-12. `summarise()` reports cost, prompt tokens and wall-clock over a call *tree*, split by node name. Measured on the smoke run: orchestrator $0.023 against $0.005 to 0.006 per sub-agent, because the root reads all three reports and so costs about four times any leaf. A single total cannot tell "delegation is expensive" from "aggregation is expensive", and those are different design problems. Wall-clock is summed, not maximised, and says so: the tree runs serially. | done |
| 0.7 | New, and it is a rule rather than an experiment. The first ablation this repository ran was confounded: the second pass re-dispatched every sub-agent, and `customer-impact` answered on the control pass and declined on the ablation pass *from the identical prompt*. Two things differed and nothing in the run could say which caused the orchestrator's change. An ablation must hold the surviving inputs fixed, or it measures resampling, which is Track I's scatter finding arriving somewhere new. Pinning is the same `transform` seam handed a constant. Applies to every track from B onward. See [`notebook/2026-08-12-the-ablation-that-measured-resampling.md`](../../notebook/2026-08-12-the-ablation-that-measured-resampling.md). Implemented 2026-08-13: `pin`, `pinned_dispatches`, `ablation_is_identified` and `run_ablation`, at 100% line+branch. The rule had sat in this table for a day with nothing enforcing it, so the only thing standing between the next ablation and the last one was somebody remembering. Two things the implementation forced that the rule as written did not say: pinning takes what the parent read, not what the node said, or a control that was itself transforming would move two things at once; and the guard reads node names, not pinned reports, because an ablated node and a node that was never dispatched both drop out of the pinned set and those are different runs. The second is a fan-out manipulation wearing an ablation's name. | free |
| 0.5 | Done. `decision_evals/telemetry.py` pins the vocabulary at `open-telemetry/semantic-conventions-genai@8d3e4a0`, every name read from the registry at that commit; `RunRecord` gains `schema_version`, `conversation_id`, `node_name`, `node_id`, `parent_node_id`, `turn_index`. The fields default rather than being required, because a single `claude -p` call genuinely has no parent and no turn index, so `None` is true of it, and `schema_version` defaults to 1 so an older record describes itself accurately. Every published `RunRecord` checkpoint still loads, asserted in the test suite; an unknown column still fails loudly. Two things the earlier note got right and one it did not: `gen_ai.agent.name` is absent from the inference-span document and present in the registry, so checking one page would have wrongly retired it. Original text follows. `RunRecord` gains node identity, parent, turn index, and a trace id, using OpenTelemetry GenAI semantic-convention attribute names (`gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.conversation.id`, `gen_ai.usage.*`, `gen_ai.evaluation.*`), with parent/child span nesting giving node parent and turn index for free. `opentelemetry-api` + `opentelemetry-sdk` is a 4-package pure-Python Apache-2.0 closure; `ConsoleSpanExporter(out=file)` opens no socket. Hand-rolling a trace schema when a vendor-neutral one exists is a real weakness, and MAST-style attribution needs structured traces regardless. Adopt the names, not the package's constants: the spec is status `Development`, zero releases, Schema URL `TODO`, and has already renamed `gen_ai.system` → `gen_ai.provider.name`. Hardcode the strings in one module, pin the SDK, record the semconv commit SHA per run. Old records must fail loudly, not silently vanish. | free |
| 0.6 | Done. `InitReceipt` + `parse_init_receipt` + `assert_isolated()`, raising `IsolationError` when the CLI declares tools or picks a skill off disk. Rule 2 satisfied: run against a known-good live call first, where it passes, and the receipt reads `tools=()`, `skills=()`, `apiKeySource='none'`, 6 agents declared, 0 memory paths. Declared agents deliberately do *not* fail the gate: they are latent under `--tools ""` and only go live when it is relaxed. Original text follows. Assert on the `system/init` event, which `--output-format stream-json --verbose` emits as a free machine-readable isolation receipt: `tools`, `skills`, `agents`, `memory_paths`, `apiKeySource`. Strictly better evidence than inferring isolation from a response. Two channels it advertises are latent, not active: with `--tools ""` there is no Task tool to reach the six declared agents and no memory tool to write the auto-memory path (tested: nothing was created). Both go live the moment `--tools` is relaxed, which Track F plans. The auto-memory path is keyed on the working directory, so it would become a cross-run state channel that a checkpointed run cannot see. Mitigation: fresh cwd per run, plus an assertion on `memory_paths`. `--bare` would disable auto-memory and is unusable, because it forces `ANTHROPIC_API_KEY` auth and never reads OAuth. | free |

Depends on nothing. This is the gate on everything else.

Done when a canary trace shows turn-*n* context containing turn-1 content
by token accounting; a 4-node scripted run completes with per-node records; the
isolation canary passes at every node; `de check` green.

---

### Track N, the trigger corpus

Full design:
[`docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md`](../superpowers/plans/2026-08-13-trigger-corpus-v3.md).

The question: every Track L and Track M result was computed from one corpus of
73 turns. Is that corpus a test of the thing it claims to test?

Why it matters, and this is not a hypothetical. Asked for the first time
on 2026-08-13, prompted by the maintainer pointing out that nothing in the set
was longer than 25 words while real users write paragraphs. Two defects, and
they are different problems that arrived together:

- Coverage. No turn exceeded 23 words; 46 of 73 were ten words or fewer.
  The `ledger` procedure exists for *"a pile of context ending in a question
  about what to do"* and the corpus had never contained a pile: the longest
  positive was one sentence *describing* one.
- A shortcut. Positives ran at a median of 18 words and negatives at 8, so
  turn length alone separated the labels at AUC 0.850 and a bare *"fire if
  ≥ 18 words"* rule scored 0.890 accuracy with no model involved on the
  version 2 key. The best description arm on that key is `stakes-shown` at
  0.9795 and the highest firing accuracy on record is `confidence` at
  0.9863; on the version 1 key the same ruler scores 0.877, against
  `no-opener` at 0.967 and `confidence` at 0.973. Nine points either way, and
  the two pairs must not be crossed. 0.956, the figure this paragraph carried until 2026-08-13, is
  the `full` arm at version 1 quoted against a version 2 ruler.

So every result in Tracks L and M was competing for about nine points over a
ruler, and the through-line those tracks report, five manipulations of a
description and none of them moved discrimination, now carries a second reading
that cannot be dismissed: there was nine points of room, and five nulls is
what a ceiling looks like. Neither reading is established. Both are reported
until this track closes.

Fixing coverage without fixing the shortcut makes the shortcut worse, since
adding long positives to a set where long already means positive widens the gap,
so both are fixed by one construction, the matched triple: one positive and two
negatives written to the same length, sharing a body in the long bands and
differing only in what is asked of it.

Version 3 also stops being a single-question instrument. The same 120 calls per
arm answer length, domain, stakes, ask form and negative kind, because each is a
column on the case rather than a property the set happens to have.

| # | Experiment | Cost | State |
|---|---|---|---|
| N1 | The shortcut battery. `corpus.py`: eight trivial features, each held to a two-sided [0.40, 0.60]. The one-sided `MAX_LENGTH_SEPARABILITY = 0.70` it replaces would have passed a set at AUC 0.05, which is solved by a ruler pointing the other way. Plus a depth-2 stump over all eight capped at 0.70, because a battery of singles misses interactions. | free | done |
| N2 | Author the corpus. 40 triples, 120 items, four bands (≤25 / 40 to 90 / 200 to 400 / 900 to 1500 words), 1:2 positive-to-negative in every band so the ratio holds across the set and not only inside it. ~11k words of authored bodies. | free | done. Authored at 40 triples / 120 items and since grown by two merges to 87 triples, 261 items, then shrunk to **86 triples, 258 items** (S 24, M 24, L 21, XL 17) when `l15` was retired on 2026-08-18, then grown again to **110 triples, 330 items** (S 30, M 30, L 28, XL 22) by answer key v5 on 2026-08-20, every gate in N1 passing. The v5 items were adjudicated on 2026-08-21, which closes what N3 owed. See below |
| N3 | Blind label adjudication. Three independent instances label each turn with no access to mine. Pre-registered kill: >20% label movement retires the corpus. 21 of 21 scored failures across three corpora were the answer key, and a 1,200-word turn has fifty times the surface for that. | 360 calls | done 2026-08-14 across two continuations, 261 of 261 items, 3 judges each, 0 unparseable. Movement 12/261 = 0.046 against the 0.20 kill, so the corpus survives by a factor of four, and no band is near it (0.042 s, 0.042 m, 0.045 l, 0.059 xl). Fleiss kappa 0.862. The 12 moves were resolved the same day by rewriting the asks rather than relabelling: 11 of 12 then agreed with the key, `l15` was retired, and movement fell to 0.004. **Continued 2026-08-21** over the 72 items answer key v5 added: 216 calls, 3 judges each, 0 unparseable, movement 3/72 = 0.042, Fleiss kappa 0.839, under the kill in every band. All 330 items now carry a record. The three moves break the triple invariant the same way the twelve did and have not been rewritten. See below |
| N4 | The human-authored holdout. The threat no gate above touches: a model is authoring the corpus that will evaluate a model. Blind adjudication does not fix it, because the adjudicator is also a model. ~20 turns are drawn from a public human-written corpus that clears the outside-data rule; the labels stay with N3's blind adjudication. Every arm is reported twice. Orderings agree → the threat is bounded by a measurement. Orderings disagree → the model-authored corpus is decoration, and we know it. | ~120 calls | source survey done 2026-08-18: eight candidates, four clear redistribution, OASST1 recommended. No step waits on a person; see below |
| N5 | Realism. The descriptive machine probe, which asks whether turns read as real or as authored-for-a-benchmark, plus, once N4 lands, a forced choice against N4's human turns: one corpus turn beside one human turn, blind judge, which was sent by a person. That is the instrument `realism_probe.py`'s own docstring names as the sharper one and declines to build for want of real messages, and it carries the known-good case standing rule 2 demands, because which item is human is a fact rather than a taste. 0.5 will mean indistinguishable; above it, the corpus reads as authored and the probe will say by how much. It will still not be a gate: it retires nothing on its own, and it has not run. | 86 done + ~86 to come | descriptive half done 2026-08-18: 86 calls, 0 unparseable, `composed` rate 0.302 [0.215, 0.406] against a registered prediction of >0.50, which is falsified. Band and em-dash presence are the same partition of the sample, so no band claim survives. [Run](../../results/decision-making/2026-08-18-0ee75d4-n5-realism-probe/README.md). The 10% human audit is retired: its own sheet recorded that the only auditor available authored the corpus, so it was a self-assessment wearing the words *ground truth*. See below |
| N6 | Confirmatory re-run: `full`, `stakes-shown`, `opener-only` × 258 × 2 repeats. Two repeats, not five: ICC 0.83 to 0.85 (Track I). | 1,548 calls | done 2026-08-18, 0 unparseable. Q1 met (+0.0976 [0.0459, 0.1493]), Q2's sign holds (+0.0079), Q3 met, with `ledger` worst-routed in all three arms. Q4 falsified: `settled` is at the bottom, not the top. All three arms clear the 0.7054 stump. [Run](../../results/decision-making/2026-08-18-e632659-n6-confirmatory/README.md) |
| N7 | Descriptive re-run: the remaining three `--description` arms (`no-exclusions`, `no-opener`, `stakes-named`; N6 already ran `full`, `stakes-shown` and `opener-only`) × 258 × 2 repeats. | 1,548 calls | done 2026-08-19, 0 unparseable. All six arms now on one corpus. Only 1 of 5 predictions met cleanly. The top three arms, `no-opener`, `stakes-shown` and `full`, are not distinguishable at n=258 (p=0.86, p=0.35); deleting the exclusion list is the one change that measurably matters (−11pp accuracy, 3× FPR). L7's band 4 still fails, since no arm reaches FPR ≤ 0.06, and this run's own prediction 5 substituted thresholds and would have reported it broken. [Run](../../results/decision-making/2026-08-19-d52236a-n7-remaining-arms/README.md) |
| N8 | Stamp the model into the record. `--model` is a CLI argument with a default and the tier survives only as prose in a hand-written README; the verdict records carry `case`, `fired`, `route`, `repeat` and no model at all. Same shape as the label-versioning defect: a run parameter that changes every number, recoverable only from someone remembering to type it. Needs a comparability guard beside `label_versions_comparable`. | free | done 2026-08-13. `run_triggers.py` writes `model`; `models_comparable` refuses a comparison spanning tiers, and `compare` raises on it. An absent `model` is unknown, not the default: `--model` could have been passed and the record would look identical, so filling in `haiku` would be standing rule 1's invented parameter. Two unstamped arms therefore still compare (no published comparison is retroactively voided) and a stamped arm against an unstamped one is refused, which is the transition where the risk is real |
| N9 | Proxy validation. `run_triggers.py`'s own module docstring names the gap and this table has never scheduled the measurement: the harness shows the model a description and one message and asks whether it would fire; deployment shows it a description *appended to* a longer system prompt, mid-session, after other turns. N9 takes the first, cheapest step: the same 258-item corpus, key v4, `haiku`, the `full` description, sent through `Conversation(in_situ=True)` (`--append-system-prompt`) instead of `--system-prompt`, one turn, against the existing N6 `full` arm as the unmodified reference. Conversation length is held at one turn on both sides; see below for why. | 516 calls | ran 2026-08-19 and is void. All 516 calls made and refused: the gate reads repeat 0 only and saw 0.8566 against its 0.90 floor; the aggregate over all 516 is 0.8643. No prediction is scored. None of the 70 unparseable responses contains a `"fire"` key, the substring "fire", or any JSON at all. They are prose, the model answering as Claude Code rather than emitting the contract. Parse rate splits into two clusters, not a gradient: `technical`/`money`/`career` 0.9135 against `relationships`/`health` 0.7892, Fisher p = 0.00011, while no adjacent pair in the sorted order is distinguishable. Identity-refusal language never appears in `technical` or `career`. The gate's blindness to repeat 1 is a standing instrument gap and is recorded rather than fixed. The venue question stays open and will need an in-situ arm whose output contract survives the host prompt, which is a new pre-registration rather than a re-score of this one. [Run](../../results/decision-making/2026-08-19-505b236-n9-in-situ-void/README.md) |
| N10 | Re-measure the six-procedure description. `docs/DECISIONS.md`'s 2026-08-19 entry retired all ten prior description arms, M4, M5, L5, L7's two, N6's three and N7's three, because none of them describes the string `SKILL.md` ships at `0.3.0`. N10 will re-run the same instrument `unbundle.py` already provides: all six `DESCRIPTION_VARIANTS` (`full`, `no-exclusions`, `opener-only`, `no-opener`, `stakes-named`, `stakes-shown`, unchanged names with new inputs, since `description_variant` derives each from whatever `SKILL.md` currently ships) × 258 items (`datasets/triggers/decision-making/index.yaml` v4) × 2 repeats, mirroring N6+N7's combined design exactly so the two are comparable in scope if nothing else. This run will not be able to separate why any difference appears. One commit (`ae55b5b`) changed three things at once: the description's enumeration clause (four conditions → six), the procedure set the router table names (four rows → six), and `ledger`'s router-row wording. Every arm in this run will see all three simultaneously, so a divergence from N6/N7 will be a statement about the shipped edit as a whole, not about any one part of it. What will be separable: the six arms will still vary wording alone against each other, holding the new router table fixed across all six, so the L5/L7-shaped question ("does this description edit move firing accuracy") will stay answerable within this run exactly as it did in N6/N7. Only the cross-run question ("did the 2026-08-19 edit help") will be confounded, and constructing an arm that separates the three sub-changes would mean shipping a description that misstates the procedure set, the exact inconsistency the maintainer ruled out when landing `ae55b5b`. `ledger`'s routing accuracy under its rewritten row will be a new instrument reading, not a continuation of the six prior figures (0.105 to 0.579); a notebook entry naming the estimator, its denominator, and a numeric band will need to be registered before this run launches, and this row does not attempt that prediction. No `description_version` or `skill_version` field exists in the verdict record schema (`scripts/run_triggers.py`'s row dict carries `set_version`, `model`, `in_situ` and nothing that identifies which `SKILL.md` revision produced the description) so no verdict row identifies which `SKILL.md` revision produced its description. The guard itself is no longer missing: `skill_versions_comparable` was built in `6e2028c` and is wired into `compare()`, and it refuses a comparison where one side stamps `skill_version` and the other does not, exactly the N10-against-N6 case. This row claimed otherwise for a day after the guard existed, which is the same defect the guard's own paragraph below records about itself. What remains is narrower: the guard keys on a field `run_triggers.py` stamps from `metadata.version`, so two arms built from *different* description text under the *same* skill version would still compare, and N10 will need that distinction registered before its numbers are set against anything published before it. | 3,096 calls | not started |

#### N10: the six-procedure description, and what one run cannot separate

Why now, and why the whole battery rather than one arm. `docs/DECISIONS.md`'s
2026-08-19 entry is explicit: *"Not one of them describes the string that now
ships. No number anywhere in this repository may be presented as a measurement
of the current description."* Re-running only `full`, the shipped string
verbatim, would answer whether the description that ships still fires
correctly, but it would leave every comparative claim from L5 and L7 (does
`stakes-shown` beat `full`, does the exclusion list do anything) permanently
retired: those claims are about the *shape* of the description, and shape is
what the other five arms exist to isolate. N10 will therefore rerun the full
six-arm battery, not a subset, for the same reason N7 finished what N6 started
rather than leaving three arms unmeasured against the current corpus.

The arms, unchanged in name and mechanism. `unbundle.py`'s
`DESCRIPTION_VARIANTS` is `("full", "no-exclusions", "opener-only",
"no-opener", "stakes-named", "stakes-shown")`, read from the file today, and
identical to the tuple N6 and N7 ran against. Nothing about the module
changed; `description_variant(description, variant)` still derives each arm
mechanically from whatever `description` it is handed, via `shared_scope`'s
`_OPENER_END` / `_EXCLUSIONS_START` markers. What changed is only the input:
handed `SKILL.md`'s `0.3.0` frontmatter instead of `0.2.1`'s, the same six
functions produce six different strings, because the opener's routing-summary
sentence itself now enumerates six conditions instead of four. The variant
names are therefore a coincidence of counting, not a relationship. Six
`DESCRIPTION_VARIANTS` measuring a description that names six procedures is
two unrelated sixes landing in the same row, worth stating so a reader does
not infer a connection that is not there.

Call count, derived. 258 items (index.yaml v4, 86
triples: s 24, m 24, l 21, xl 17, confirmed against N3's closure figures) ×
2 repeats (ICC 0.83 to 0.85, Track I, the same repeat count N6, N7 and N9
already used) × 6 arms = 3,096 calls, identical to N6's 1,548 plus N7's 1,548,
because N10 is those two runs' design repeated against a different input
rather than a new design.

What separates and what does not.
Commit `ae55b5b` moved three things at once, verified by reading the diff
`docs/DECISIONS.md`'s entry names:

1. The description's routing-summary clause: four conditions rewritten to
   six, one sentence.
2. The router table itself: four rows to six, `council.md` and `hinge.md`
   added.
3. `ledger`'s router-row wording, rewritten independently of the count change,
   per the 2026-08-19 Track S9 entry, to separate it from `cascade`.

Every arm N10 runs will see all three at once, because they already live in
one `SKILL.md` today and `description_variant` reads the whole frontmatter/body
pair. A run comparing N10 against N6/N7 will not be able to attribute a
difference to any one of the three. It will only be able to say the shipped
artifact, taken whole, scored differently or the same. This is not a gap this
row failed to close; it is very likely not closeable without shipping an
inconsistent artifact.
An arm that varies (2) while holding (1) at "four conditions" would ship a
description that undercounts its own router table, exactly the defect
`docs/DECISIONS.md` names as the reason `ae55b5b` was landed as one change
rather than deferred. Isolating (1) from (3) is more plausible in principle
(a router-row rewrite that does not touch the description's own text) but is
not attempted here and is not free: it is Track 0.7's ablation machinery,
applied to a skill body rather than a sub-agent dispatch, and it is new
scope, not a natural extension of this row.

What will separate and will not be confounded. The comparison among
N10's six arms, the L5/L7 question, "does this wording choice move firing
accuracy", will hold the router table and the procedure set fixed across all
six, exactly as N6 and N7's six arms did. So N10 will answer the wording
question cleanly, the same way its two predecessors did; what it will not be
able to answer cleanly is whether the 2026-08-19 edit as a whole helped,
because "as a whole" is three changes bundled into one comparison.

The routing question is a prediction, not written here. `ledger` was the
worst-routed procedure in all six prior arms (0.105 to 0.579, Q3 in N6,
restated in the 2026-08-19 Track S9 entry alongside the `ledger → cascade`
count: 77 of the confusion-pair traffic across N6+N7's six checkpointed arms).
Its router row was rewritten specifically to separate it from `cascade`.
Whether the new row helps is exactly the kind of claim the registered-band
rule in `CLAUDE.md` exists for, and it is not this row's to answer: a notebook
entry will need to name the estimator (first-route match rate against
`ledger`-labelled items, most likely, mirroring N6's Q3, though that choice
belongs in the prediction rather than here), its denominator (the count of
`route == "ledger"` items, 19 in N6's construction, subject to change now the
corpus may resolve differently against six new arms), and a numeric band set
against the observed ceiling rather than a round number, per the L7
recall-band defect this file already recorded. That entry must exist and its
first commit must be an ancestor of N10's run commit before N10 launches, per
the run-provenance rule. This row states what must be registered; it does not
register it.

The comparability gap. `trigger_arms.py`
carries three guards: `label_versions_comparable` (keyed on the record's
`set_version`), `models_comparable` (keyed on `model`) and `venue_comparable`
(keyed on `in_situ`), each raising `ArmError` inside `compare()` when two
arms differ on the field it checks. Reading `scripts/run_triggers.py`'s
verdict-row construction (`row = {...}`, in `main()`'s scoring loop) shows
what is and is not stamped: `case`, `repeat`, `fired`, `procedure`, `covers`,
`set_version`, `model`, `in_situ`, `p_fire`, `should_fire`, `route`, and the
full `routes` tuple. Nothing identifies which revision of `SKILL.md`
produced the description a given verdict was scored against. `set_version`
tracks the answer key (`datasets/triggers/`), not the skill; a description
edit with no corpus edit moves `set_version` not at all, which is exactly the
2026-08-13 label-versioning defect's shape one axis over: a run parameter
that changes every number in the run, recoverable today only from a human
remembering which commit was checked out. `compare()` would run an N10 `full`
arm against N6's `full` arm and return a p-value with no refusal at all,
because none of the three existing guards inspects the field that changed.

**Built on 2026-08-19 in `6e2028c`, and this paragraph described it as a recommendation for a day after it existed.** `skill_versions_comparable` is at `trigger_arms.py` and wired into `compare()`'s guard chain; `run_triggers.py` stamps a `skill_version` field into every verdict row, sourced from the `SKILL.md`'s `metadata.version`. What follows is the argument that produced it, kept because the reasoning is the useful part.

Recommendation: add a fourth guard, `skill_versions_comparable`, before
N10's numbers are compared against anything published before it. The shape
already exists three times over. Stamp `SKILL.md`'s frontmatter
`metadata.version` (`0.2.1`, `0.3.0`, …) into each verdict row at write time,
the same way `model` and `in_situ` are stamped now; add a `*_comparable`
function reading that field the way the other three read theirs; wire it into
`compare()`'s guard chain. An absent value on a pre-N10 record reads as
`0.2.1` rather than *unknown*: every record on disk today was in fact scored
against that version or an earlier one, no CLI flag could have silently
produced a different value the way `--model` could, so the record is telling
the truth by omission, the same reasoning `venue_comparable`'s docstring gives
for treating an absent `in_situ` as `False`. This is a recommendation, not an
implementation, and it belongs beside N10's launch rather than inside this
document.

---

#### N9: the proxy the module docstring names, and the cheapest step toward closing it

The gap, in the module's own words. `scripts/run_triggers.py`'s
module docstring says plainly what the instrument is not: *"The real harness
decides differently: the description sits among other skills, in a longer
context, with the model mid-task. This measures the description's
discriminative content, not the deployed firing rate."* The word "proxy"
appears nowhere else in this document (`grep -n "proxy"
docs/RESEARCH_PROGRAMME.md` matches only that docstring's own paraphrase
above), and no row before this one schedules the measurement that would bound
the gap. Every number in Track L, every number in Track M, and all three of
N6's arms were measured in a venue where the description is the entire system
prompt and the turn under test is the only message sent.

What is compared: the same four constants N6 already fixed, 258 items,
key v4, `haiku`, the `full` description, run once more with the description
appended rather than substituted, against N6's own `full` arm (accuracy
0.9360, precision 0.8601, recall 0.9651, FPR 0.0785;
[`results/decision-making/2026-08-18-e632659-n6-confirmatory/`](../../results/decision-making/2026-08-18-e632659-n6-confirmatory/README.md))
as the reference. No new reference run is needed; N6 already paid for it.

The two mechanisms this reuses already exist, checked by reading the code:

1. A secure multi-turn transport, already used by every trigger call.
   `Conversation` (`evals/src/decision_evals/providers/claude_code.py`, line
   511). Its class docstring states the isolation finding directly:
   `--no-session-persistence` (one of `ISOLATION_FLAGS`, line 54) blocks
   `--resume`, which is cross-process, but does not block turns sent
   in-process over `--input-format stream-json`. Multi-turn needed no
   isolation flag relaxed to work. `run_triggers.py`'s `ask()` function
   already opens a `Conversation` at line 212 and sends exactly one turn at
   line 214.
2. An `in_situ` mechanism, already a first-class parameter.
   `build_command` (same file, `def build_command` at line 163) sets
   `prompt_flag = "--append-system-prompt" if in_situ else "--system-prompt"`
   at line 209; `Conversation.__init__` (line 547) already accepts and
   threads through `in_situ: bool = False`. `evals/src/decision_evals/solvers/arms.py`
   already treats `in_situ` as a fifth named arm (`ARM_NAMES`, line 40) for
   Track G, deliberately ordered last because "it answers a different
   question from the other four: not 'does the skill help' but 'does it
   still help when it is not the only thing in the prompt'" (lines 37 to 39).
   `run_triggers.py` has no such arm and no `--in-situ` flag. Wiring one
   through is the only new code this row needs; both machines it calls
   already run.

Call count, derived. One new arm (`full`, in_situ) ×
258 items × 2 repeats = 516 calls. Two repeats, not five, for the reason
N6 and N7 already used: Track I measured ICC 0.83 to 0.85 for this instrument.

The risk in the design. An `in_situ`
arm that *also* inserts turns before the one under test confounds two changes
in a single comparison, prompt position (appended vs substituted) and
conversation length (one turn vs several), and a divergence from N6 could
then be credited to either. N9 holds conversation length fixed at one turn on
both sides and moves only position. That is a deliberate scope cut, not an
oversight: how many prior turns, what they should discuss, and how they
should be authored is exactly the kind of unmeasured parameter standing rule
1 forbids inventing. The docstring's "longer context, mid-task" clause names
a real second gap but supplies no number for turn count or content, and
authoring that corpus is separate work this row does not fund.

What a large divergence would mean, and what it would not. If N9's arm
lands outside N6's `full` arm's interval, every published trigger number,
all of Track L, all of Track M, N6's three arms, is a statement about a
venue nobody deploys in, measuring the description's discriminative content
in a position it never occupies at inference time. That is not a hypothetical
tacked on for effect; it is the stated reason this row exists. A null
result, N9 inside N6's interval, says position alone does not move firing
behaviour, which is one of the two gaps the docstring names, not both.

What N9 does not settle. It moves the venue one step closer to
deployment and no further. After it runs, the residual gap is exactly the
half of the docstring's sentence N9 does not touch: "the turn under test
arrives after other turns". A real session has other skills present, a task
already under way, and a context this corpus does not supply. Closing that
half needs its own row, its own derived turn count, and its own check against
N9's position-only result so the two effects are not read as one.

#### N4's route changed on 2026-08-18, and the threat it controls did not

The maintainer will not hand-author the ~20 holdout turns. Recorded as a
decision rather than left as a blocked row, because a blocked row that nobody
retires is how a track stalls for weeks: N4 has sat on
[`STATUS.md`](../STATUS.md)'s maintainer list since it was written and no turn has
ever been supplied.

So N4 will be built from a public human-written corpus instead. What it
controls for is the *provenance of the text*: the three leaks Track N has
closed so far were authoring habits (a word-count ruler at 0.890, an `open`-view
opener at 0.779, and `_shared_body` cutting at a space), all of them in text a
model wrote, all of them hunted by gates a model built. Human text breaks that
loop whether or not the human is the maintainer.

The labels will come from N3's three-judge blind adjudication, unchanged.
That is a real weakening, and it is stated plainly: the
adjudicator is still a model. But the contamination being controlled sits in the
*text*, not the key, so a model-labelled human corpus is materially less
circular than a model-authored one, and it is reachable without a person.

Two things this costs, both accepted:

- The distribution shifts. Forum posts are written for strangers and chat
  logs were sent to a different assistant. The holdout therefore asks *does this
  generalise off our own writing*, not *does this work on the maintainer's
  inbox*. The first is the question worth answering; the second was never quite
  what N4 asked either.
- A source must clear the outside-data rule before anything is fetched:
  free, redistributable, sampled and read, digest pinned. See
  [`AUTONOMOUS_WORK_ORDER.md`](../AUTONOMOUS_WORK_ORDER.md). Nothing here has a
  budget, so a source that costs money is not a source.

A label-free fallback exists if no corpus clears that bar. N4's payload is
whether the arms *rank the same* on human text as on authored text; a weaker
version measures only how much the arms disagree with each other on
unlabelled human turns. Divergence on authored text and convergence on human
text would be a finding, and it needs no key at all.

#### N3 closed, and the freeze it feeds cannot be executed as written (2026-08-18)

261 of 261 items blind-adjudicated, 3 judges each, 12 moves, movement
0.046 against the 0.20 kill. Derived independently three times, by two
sub-agents told nothing of each other and then by hand, and agreeing on every
figure. The corpus survives the kill by a factor of four and survives it in
every band separately (0.042 s, 0.042 m, 0.045 l, 0.059 xl), which is stated
because a pooled rate has hidden a per-stratum problem here before.

All 12 moves break the one-positive-two-negative invariant, and that is a
fact about the design rather than about the labels. In each of the 10
negative → positive moves, the same adjudication unanimously reconfirmed
that triple's *existing* positive, 10 of 10, all three judges, so the judges
say both members should fire, and applying the move yields two positives. The
2 positive → negative moves land in triples whose other members were
unanimously negative, which yields none. `corpus._check_triples` reports this
as structural, which carries the `_UNBASELINEABLE` key by design: there is no
version of the freeze that lands and defers this.

The mechanism: the corpus is authored in triples and adjudicated in items.
A judge sees one turn and is asked whether that turn should fire. Nothing in
the protocol knows the turn shares a body with two others and is competing for
a single positive slot. So a 2-of-3 vote against the key does not say *this
label is wrong*; it says the authored contrast did not land. The v3 plan's
rule, *"2-of-3 against me → I rewrite the turn or move the label, and say
which"*, assumes both branches are always available. On a matched-triple
corpus "move the label" sometimes is not, and the plan does not say so
because the case had not arisen when it was written.

It had arisen once, and was read as a local accident. `docs/DECISIONS.md`'s
2026-08-14 entry reverted `l12n1`, `l17n2` and `xl15n2` rather than promoting
them, "because accepting would have put two positives in a one-positive-per-
triple design." That was the general case seen through one opener edit.

The freeze is therefore open, and the choice is not neutral. Retiring the
12 affected triples is mechanical and invents nothing, and it deletes exactly
the 36 items three blind readers found hardest, which makes the corpus easier
rather than better and incidentally closes two of the three open shortcut
findings. A corpus edit that turns gates green is the mechanism this repository
has already named as the source of four generations of leak. Rewriting the
disputed ask and re-adjudicating preserves difficulty and costs authoring plus
another adjudication round. Demoting the existing positive is ruled out: no
judge supports it. Relaxing the invariant is a corpus redesign, not a version
bump.

The remedy is rewrite-and-re-adjudicate, and an adversarial review settled
it against the cheaper option. Retirement of the 12 triples was the obvious
move and is the wrong branch of the plan's own rule, which sends a 2-of-3
disagreement to *rewrite the turn or move the label* and reserves retirement
for a *three-way split*. All 12 disputes are clean 3-0 or 2-1 majorities, and
with three binary judges a three-way split cannot occur at all, so the
retirement branch has been unreachable since the protocol was written, which is
why it read as available. Moving the label is structurally blocked, so
rewriting is the only live branch. Three checks, each re-derived:

- Retirement biases the survivors along the axes v3 exists to test. It
  removes implicit asks at 18.5% and embedded at 18.2% against explicit at
  7.9%, the two forms added because v2 was saturated with *"should I"*, and
  23.5% of technical and 22.2% of money against 0% of relationships.
- It costs N6 the power the long-band merge just bought. SE 0.0346 →
  0.0374, MDE 0.0970 → 0.1047, power at the registered 0.10 threshold
  0.823 → 0.763. The MDE crosses the effect the test is built around.
- It closes two of the three open shortcut findings, and that is a side
  effect rather than a reason. The retired triples are in fact *less* extreme
  than the survivors on both features (0.229 vs 0.283, 0.292 vs 0.393), so this
  is not disguised feature-retuning. But citing a gate closure as a merit is
  the reasoning this repository has named as the source of four generations of
  leak.

Retirement is held for any of the 12 that still fails to reach a key-consistent
majority after a genuine rewrite. And if it is ever used, movement must be
reported cumulatively over the corpus's whole history, because pruning the
disputed items is otherwise a way of making the 20% kill structurally unable to
fire again.

Resolved 2026-08-18, and the corpus survived it. All 12 asks were rewritten
to one rule, *an inert ask asks about one thing, and may not put two options in
a frame that invites ranking them*, diagnosed from `s02n2` and applied by agents
never shown a judge's rationale, since a rewrite aimed at a stated objection is
tuned to that judge. On blind re-adjudication, 36 calls, 0 unparseable, 11 of
12 now agree with the key against a registered band of 8. Judge agreement on
those twelve went 0.611 → 1.000 pairwise and corpus-wide movement 0.046 →
0.004. `l15` is retired whole, as the one item still disputed after the
single round the protocol allowed, so the corpus stood at 258 items, 86
triples: s 24, m 24, l 21, xl 17. Answer key v5 took it to 330 items in 110
triples on 2026-08-20; the adjudication described here does not cover those.

No label moved and no version was bumped, so no published number is
affected. No gate crossed, `imperative_opener` did not pick up the *"Restate…"*
rewrites, and the two `sentence_count` findings ended *stronger* at 3.18σ,
after a mid-round correction, because three rewrites had changed their turn's
sentence count and pushed that habit under its 3.0 gate, which would have had a
label fix quietly close two open shortcut findings.

One prediction registered before the round was wrong: the two positive →
negative items were expected to be harder and possibly to retire. Both fixed on
the first attempt.

Working:
[`notebook/2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md`](../../notebook/2026-08-18-the-corpus-is-authored-in-triples-and-adjudicated-in-items.md).

#### N5's human audit is retired, and the plan has no step left that waits on a person (2026-08-18)

The 10% audit was a gate on a person and it is removed, on a maintainer
instruction to take every such gate out of the plans. It is not being removed
because nobody filled it in, and that distinction is the whole of the
justification. The audit sheet's own standing caveat said it: *"The only auditor
available authored this corpus, so these answers are a self-assessment."* A
self-assessment by the author is not the ground truth the sheet's header claimed
for it, so the audit was mislabelled from the day it was written, and 138 items
were added under it without the sheet ever being regenerated. It was still
addressed to a 120-item corpus at answer key v3, against 258 items at v4.

What replaces it is stronger than what it replaced, and only because N4 moved.
`realism_probe.py`'s docstring already names the sharper instrument and declined
to build it: a forced choice cancels the judge's base rate, which is the one
quantity a single-item realism verdict cannot recover, and it was unavailable
because, in that docstring's words as they stood at `90f1653`, this morning's
commit, *"There is no human-written comparison set in this repository."* N4 no
longer waits for a person to write one. It draws on a public human-written
corpus, so the comparison set becomes reachable, and with it the known-good case
standing rule 2 demands before any falsifier may fail anything: which turn is
human is a fact on the record, not a taste. N5 therefore now depends on N4
rather than on anybody's calendar.

What this costs. The retired audit was the
only place in the programme where a reader outside the model loop was ever going
to look at this corpus. Nothing replaces that, and the forced choice does not:
its judge is a model too. What it gains is a ground truth the audit never had.
The corpus remains model-authored, model-adjudicated and model-probed, and Track
N4's row is the only thing that moves the provenance of the *text* out of that
loop.

No output from `scripts/realism_probe.py` exists on disk, so the descriptive
half of N5 has not run either. That is a call budget, not a gate.

One naming collision is worth fixing before it reaches a paper. Commit
`30012d9` and its notebook entry call themselves "N7". They are a continuation
of N3, closing the L/XL adjudication gap, and not the N7 in the table above,
which is the descriptive re-run of the remaining three arms and has never
started.

---

Depends on nothing. Like Track 0, it is a gate rather than a question.

Blocks every *future* claim from Tracks L and M, and it retro-qualifies every
past one. It does not block Track S: the skill ships and is usable either way,
which is the distinction `SCORECARD.md` exists to draw.

Falsifiers.

1. N1's gates cannot be met without writing turns nobody would send. Then the
   length/label correlation is intrinsic to the task, long messages really are
   more often decisions, and that is a finding to report rather than engineer
   around. The corpus ships with the honest AUC and every claim is conditional
   on it.
2. N3 moves more than 20% of labels. Corpus retired, not reported.
3. N4's orderings disagree. Every trigger result in this repository becomes a
   statement about model-authored text and nothing else.
4. Accuracy is flat across bands and the arms re-order anyway. Then the trigger
   instrument does not have the resolution for the questions Tracks L and M have
   been asking it, which is a larger result than any of them.

Done when all eight features and the stump are inside their gates on a 120-item
set; adjudication is under the kill threshold; the holdout exists and has been
run; N6 is published with its bands registered first; and every
`results/**/README.md` carries the ruler caveat.

#### N2 closed, 2026-08-13, and the gates it closed against had never run

The corpus is 120 items: 40 positives, 80 negatives, four bands. The XL band is
7 triples of 900 to 1,500 words in which the positive and its two negatives
share a byte-identical body and differ only in the closing ask, so `ledger` has
for the first time been shown the pile of context it exists for. Working:
[`notebook/2026-08-13-the-xl-band-and-two-rulers-that-cancelled.md`](../../notebook/2026-08-13-the-xl-band-and-two-rulers-that-cancelled.md).

The corpus was outside every gate written for it. `check_trigger_sets` globs
`datasets/triggers/*.yaml`; the bands are one directory down. The shortcut
battery, the stump and the balance rules could not see any of the 99 items
already authored, and `de check` was green on every commit that added them. That
is the third tested-with-no-caller defect on record, after `triggers` at 100%
coverage and `prereg.py`'s unreachable refusals, and the first found before
anything had been published from it. A `_check_drafts` step now holds a corpus
under construction to the live rules without making it live, because the entry
point may not move before adjudication.

A pooled AUC of 0.5 is not evidence that a band is clean. `word_count` read
0.511 over the whole set while the L band sat at 0.769 and the XL band at 0.301,
one authoring habit seen from two sides, cancelling in the pool. Length inside a
band is available at inference, so this was a real shortcut and not a
bookkeeping curiosity. The depth-2 stump caught it at a lift of 0.117 against a
0.100 cap; the per-feature battery could not, by construction. After re-mixing
the ask lengths the set reads:

| | | | |
|---|---|---|---|
| says_should_i 0.575 | first_person_rate 0.554 | word_count 0.511 | question_marks 0.500 |
| imperative_opener 0.494 | paste_cues 0.489 | char_count 0.481 | type_token_ratio 0.471 |

stump 0.750 against a majority baseline of 0.667: lift 0.083, cap 0.100.

Per-band separability is reported and not gated, and the reason is arithmetic
rather than convenience. At 7 positives and 14 negatives an XL-band AUC rests on
98 pairs, a null standard error of ~0.137 under independent sampling, so a
[0.40, 0.60] gate would fire on a clean corpus roughly half the time, eight
times per band. The matched-triple construction makes the true null variance
smaller than that by an unknown amount, so the figure bounds the noise rather
than measuring it, and whether a per-band gate is affordable is open. What is
not open is that the pooled number alone was hiding two rulers.

Neighbouring work, not duplicated here: `provenance.py`, `wiring.py` and
`de index` gate whether a published run has a prediction that predates it. They
were built in a parallel session and are the same class of fix, aimed at the
write-up rather than the corpus.
