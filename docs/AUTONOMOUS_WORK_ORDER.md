# Autonomous work order

**For an agent pointed at this repository and left running for hours or days.**

Read this before [`RESEARCH_PROGRAMME.md`](RESEARCH_PROGRAMME.md). The programme
says what the work is. This says what you may do without a human, and — more
importantly — what you must stop for.

The rules below are not general good practice. Every one of them exists because
the specific failure it prevents has already happened here, and the reference is
given so you can check rather than take it on trust.

---

## The five standing rules

### 1. Never invent a missing parameter. Stop and record.

If a number you need is not written down — an item count, a threshold, a turn
count — **do not choose one.** Write what is missing to `notebook/`, stop that
unit of work, and move to the next independent one.

*Why.* The programme said Track A1 would shard casefiles "across ~6 turns". That
figure had no source; the paper it came from sweeps 2→8 and reports no mean. It
was invented, written down, and would have been designed around. An invented
parameter is indistinguishable from a measured one three days later.

### 2. A falsifier must be run against a known-good case before it may fail anything.

Before any gate is allowed to kill a venue, construct a case you are confident
*should pass*, and confirm the gate passes it. If it does not, the gate is wrong.

*Why.* Two falsifiers were wrong on 2026-08-11. Track 0's required `cache_read`
to climb turn over turn; measured, it stays at **0** while context demonstrably
carries, so a healthy venue would have been declared dead
([`notebook/2026-08-11-multi-turn-already-worked.md`](../notebook/2026-08-11-multi-turn-already-worked.md)).
Track A's kill condition would have terminated the whole programme on a null
that was underpowered by construction — 12 items against the ~127 pairs needed.
Both were written without being run against anything.

### 3. Never score a model output against an answer key without a human read.

You may **run** experiments and **record** raw outputs. You may not decide that
a response is wrong, and you may not report an accuracy figure derived from that
decision.

*Why.* **Twenty-one of twenty-one** scored failures across three corpora were
the answer key being wrong, not the model
([`docs/FAILURE_TAXONOMY.md`](FAILURE_TAXONOMY.md)). Twice the model produced a
*better* answer than the key allowed. Track B3 requires adjudication by a party
blind to the key — **you cannot be blind to a key you or another agent wrote.**
This is structural, not a matter of care.

Decision tasks here have no executable verifier. That is the difference between
this repository and SkillRevise's setting, and it is why this rule has no
exceptions.

### 4. Run the full `de check`, not `--fast`, before calling a unit done.

```bash
python -m uv run de check
```

*Why.* `--fast` is what the pre-commit hook runs and **it skips tests and
coverage**. Two skill tests were broken by a refactor on 2026-08-11 and survived
several commits because every one of them passed `--fast`. A green pre-commit
hook is not a green build.

### 5. Cite nothing you have not opened.

A search-result summary is not the paper. Before asserting any number beside an
arXiv identifier, fetch `https://arxiv.org/abs/<id>` and put the verbatim
sentence in the `quote` field of its `paper/refs.bib` entry. `de check` enforces
this; see [`citations.py`](../evals/src/decision_evals/citations.py).

*Why.* Three numbers were misattributed here in a single morning, **all citing
real papers that existed and said something adjacent** — the hardest kind to
catch. One reached the file this repository calls the product and was used to
justify a design decision.

---

## What you may run unattended

Everything here has a machine-checkable success condition and requires no
judgement about an answer key.

| Work | Done when |
|---|---|
| **Track K5 backlog** — resolve baselined identifiers in `paper/citations-baseline.txt`, one paper at a time: fetch, add the entry, add the `quote`, delete the line | `de check` green with a shorter baseline |
| **Track 0.5** — OTel GenAI span attributes on `RunRecord`/`NodeRecord` | tests pass at the coverage floor |
| **Track 0.6** — assert on the `system/init` isolation receipt | a planted `CLAUDE.md` is proven absent from `memory_paths` and `tools` |
| **Fold the `stream-json` transport** into `providers/claude_code.py` beside the single-shot path | the multi-turn canary reproduces: `input_tokens` climbs *and* turn-*n* recalls turn-1 content |
| **Vendor the sharded corpus** from arXiv:2505.06120 and write `model_claude_code.py` against its `generate()` interface | it runs; upstream commit SHA recorded in the datasheet |
| **Compute the MDE** for A1–A5 with `stats/power.py`, and write it into the programme beside each experiment | numbers exist where "sized from the MDE" currently is |
| **Track I1** — `stats/reliability.py` | 100% line+branch with property tests, matching `paired.py` |
| **Track K1–K4, K6** — the decision-frameworks review | `docs/DECISION_FRAMEWORKS.md` exists, every claim carrying a `quote` |
| **Delete or wire the `inspect-ai` dependency** — declared in `pyproject.toml`, imported nowhere | either it is imported or it is gone |

---

## What you must stop for

Not "be careful with" — **stop, write to `notebook/`, and wait.**

1. **Any scoring of model output against an answer key.** Rule 3.
2. **Authoring corpus items.** Three corpora were built and discarded. The
   published sharded corpus exists precisely so this is not needed for Track A.
3. **Any decision about scope** — which tracks run, which are cut. An adversarial
   review argued the honest minimum is `0 → A5 → I → E4`; that is a
   recommendation the maintainer has not ruled on.
4. **Relaxing `--tools ""`.** It opens two channels that are currently inert: six
   declared subagents, and an auto-memory path keyed on the working directory
   that would become cross-run state a checkpointed record cannot see.
5. **Spending significant quota.** The budget is the subscription's rolling
   usage window and wall-clock, not dollars. A long serial grid is hours spread
   across days. Say what a run will cost in calls before starting it.
6. **Any claim that a skill works.** Nothing here has been shown to work. The
   verdict vocabulary in [`SCORECARD.md`](../SCORECARD.md) governs what may be
   said; `UNTESTED` is the honest state of every skill in this repository.

---

## Working discipline

- **One unit per commit**, full `de check` green before each.
- **`notebook/` is append-only and dated.** Predictions go in *before* runs. A
  prediction that turned out wrong stays in the record saying so — it is not
  edited. Five consecutive predictions have been wrong in the same direction
  (toward the experiment working), and that record is evidence.
- **Commits attributed to the GitHub noreply address**; `de check` refuses
  otherwise.
- **Golden files pin the corpus byte-exact.** Regeneration needs `pytest
  --bless` and the diff belongs in review.
- **Report what happened, not what was attempted.** If a step was skipped, say
  which and why. If tests fail, quote the output.

## When you stop

Leave behind, in `notebook/` and dated:

1. What was completed, and the commit for each.
2. What was stopped for, which rule above, and exactly what decision is needed.
3. Anything measured that contradicts a document in this repository — including
   this one. Two falsifiers and three citations were wrong on the day this was
   written, and each was found by someone checking rather than assuming.
