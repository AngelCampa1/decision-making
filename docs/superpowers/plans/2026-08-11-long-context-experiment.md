# Long-Context Decision Experiment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish whether decision quality degrades with context volume, and whether a decision skill buys robustness against that degradation — via an instrument that has been proven capable of answering the question *before* a quarter of a million tokens of corpus is authored.

**Architecture:** Three milestones gated on each other. **A** repairs the harness defects that only bite at length (cost authorisation, corpus fingerprint, checkpoint loading). **B** repairs the primary metric, which currently fails competent answers on a conjunct that was measuring the answer key rather than the model. **C** runs six cheap instrument gates on a pilot corpus, ending in a pre-registered go/no-go on whether the full grid gets built at all. Everything past the gate is a separate plan, named but deliberately not written yet.

**Tech Stack:** Python 3.13, `uv`, pydantic v2, pytest + hypothesis, ruff, mypy, Typer. Model backend is the Claude Code CLI (`claude -p`) on a Claude Max subscription — **no API key**. Local gate is `python -m uv run de check`.

---

## Where we are

Three corpora, three failures to measure anything, and the harness itself was the fourth problem.

| Corpus | Size | What varied | Result |
|---|---|---|---|
| `rel-*` single-turn | ~350 tok | distractor count, position | 0.946 — all 15 zeros were item defects, not model failures |
| `rel-*` rebuilt | ~700 tok | type-compatible colliding distractors | 0.971 — collisions bought 2.9pp |
| `probe-*` casefiles | ~1,650 tok | trap order 1–3, four consequence kinds, three framings | **27 trap opportunities, zero taken** |

The casefile probe is a clean negative and is recorded as one. Haiku 4.5 does order-1 through order-3 consequence reasoning reliably on 5–9-document professional casefiles, with an action menu, without one, and with no scaffolding at all. It computed a 4.12:1 leverage ratio unprompted, sequenced a waiver before publication, and surfaced the exact fact `s.46(3)` turns on from seven documents nobody had indexed for it.

**Every corpus built so far is under 2,000 tokens.** Trap sophistication, distractor type-compatibility and scaffolding have all been varied; the one variable the literature actually implicates — volume — has been held constant. Nothing built here is long-horizon.

**And this paragraph used to carry a number that does not exist.** It said context rot is documented at 30–50% in long-horizon settings, citing arXiv:2606.29718. That figure is not in the paper's abstract, was not found in its PDF, and appears in no secondary summary of it; checked 2026-08-12. What that paper does establish is a *mechanism* — **premature termination**, models giving up or answering uncertainly long before the context window is full, at a rate that rises with context length, across four flagship models and three search benchmarks. Its own headline figure is a 2.6–4.9% *gain* from behaviour-aware filtering.

The mechanism is enough to motivate this plan and is arguably a better fit for it than a degradation percentage would be: premature termination is a specific failure a decision procedure could plausibly interrupt. But the plan should be read knowing that **the size of the effect it is hunting was never established by the citation it leaned on**, so the Phase 0 control-admissibility band is doing more work than it looked like.

### What is already fixed (commit `c25d675`)

The harness could not have carried the experiment, and this was found for $0.45 before any corpus existed:

- **The prompt was an argv element.** Windows caps a command line near 32 KB; a 100k-token casefile is ~400 KB. Every call in the two longest strata would have died as a `CliError` scored `zero_cause="infrastructure"` — an entire stratum of nulls, indistinguishable in the summary from context collapse. The prompt now goes on **stdin**, with no short-prompt fast path (a conditional split makes the long path the rarely-exercised one and lets the two drift).
- **`usage.input_tokens` is the uncached remainder, not the prompt.** A 380 KB prompt reported **10** input tokens while `cache_creation_input_tokens` carried 24,285. `docs/HARNESS_DISCLOSURE.md` commits to reporting input tokens at p90/p99 — that disclosure would have been wrong by three orders of magnitude in exactly the stratum it exists to describe, and wrong by *more* the longer the prompt, so the error would have been **correlated with the independent variable**. Prompt is now `input + cache_creation + cache_read`, with the split retained.
- **`CHARS_PER_TOKEN` was 3.8 by guess; measured 6.01 for repetitive filler.** The run labelled "100,000 tokens" was really 63,313. Fourth prediction wrong in two days, again in the direction that flattered the experiment.

**The canary gate passed.** Three strings at 10/50/90% depth, asked back verbatim:

| Achieved tokens | Cost | Wall | Canaries |
|---|---|---|---|
| 1,533 | $0.005 | 8.1s | 3/3 verbatim |
| 25,489 | $0.030 | 6.6s | 3/3 verbatim |
| 63,313 | $0.071 | 6.2s | 3/3 verbatim |
| **101,142** | $0.230 | 7.8s | 3/3 verbatim |
| ~210,000 | $0 | — | `Prompt is too long` |

**The independent variable exists and the instrument can carry it.** `scripts/canary_long.py` re-runs this whenever the CLI version moves.

### What is still broken

| Defect | Site | Why it only bites at length |
|---|---|---|
| Flat cost authorisation | `evals/src/decision_evals/runner.py:109` | `expected_cost_usd=0.05` under-counts a 100k prompt ~5× and the ledger authorises before the call |
| Fingerprint blind to documents | `scripts/calibrate.py:98` | Hashes `item_id`/`question`/`answer`/facts only; a padded corpus resumes off a stale checkpoint silently |
| Silent record loss | `evals/src/decision_evals/runner.py:211` | `load_records` swallows `TypeError`, so adding a column makes every earlier record vanish without a word |
| Broken primary metric | `scripts/probe_casefile.py:449` | `admissible = ... and pivot_ok` — 5 of 6 probe failures were this conjunct alone |
| ~~Unfair placebo~~ | `skills/evidence-ledger/placebo.md` | **Struck. This entry was wrong.** The guard compares the placebo against the skill's *body*; 421w vs 445w is a ratio of 1.057 and it passes. The 0.71 counted YAML frontmatter as skill prose. What remains is a real but different concern — see Task 7. |

### The number that governs everything

**Twenty-one of twenty-one scored failures across three corpora were my answer key, not the model.** Fifteen of fifteen, then six of six. Twice the model produced a *better* answer than the key allowed. Padding multiplies the key's surface area roughly fiftyfold, and — critically — padding volume is the independent variable, so a key-error rate that grows with padding would be **indistinguishable from degradation**. That risk is what the gates in Milestone C exist to price.

---

## Where we want to be

One sentence, testable: **an interaction estimate for `arm × log2(context length)` on decision admissibility, with a pre-registered rejection region, from a venue that has been shown capable of producing a non-trivial answer.**

Concretely, at the end of the programme:

1. A **30-core corpus** across tax, employment and life decisions, at two confirmatory lengths (2k and 100k) with 10k/40k descriptive on a subset.
2. A **paired Wilcoxon signed-rank** on 30 per-core slope differences — exact, nonparametric, clustering handled by construction, MDE ≈ 21pp.
3. **`evidence-ledger` and `consequence-cascade`** each measured against the failure it claims to fix, with a discriminant table that fails both of them if both move everything.
4. A **tailoring sensitivity** result on life-decision triplets: `d = P(change | governing) − P(change | matched non-governing)`, reported as sensitivity/specificity plus Youden's J.
5. Either a `SHIP`/`PROVISIONAL`/`NULL` verdict in `SCORECARD.md`, **or** a documented instrument failure that says why the venue could not answer — which is a result, not a fourth dead corpus.

The user's design brief, verbatim, is what the life-decision stratum exists for:

> *"honestly what i want this repo to be is about life decisions (which encompass everything i guess) but i believe any decision ai helps the human make needs to be tailored to that human context"*

A decision skill earns its keep when the advice changes because of who is asking. The failure it must catch is **generically-correct advice that is wrong for this person**.

---

## The programme at a glance

| Milestone | What it establishes | Gate to pass | This plan? |
|---|---|---|---|
| **A** — harness integrity | The run loop cannot lie about cost, corpus identity, or record count | `de check` green; three new tests | ✅ Tasks 1–3 |
| **B** — metric integrity | Admissibility measures the model, not the key | Rescored probe deltas recorded in `notebook/` | ✅ Tasks 4–6 |
| **C** — instrument gates | The venue *can* answer the question | **Control admissibility at 100k lands in [0.25, 0.70]** | ✅ Tasks 7–15 |
| D — schema and generator | `casefile` becomes a first-class item kind | golden bijection holds, `rel-*` goldens unmoved | ⛔ separate plan |
| E — statistics | `stats/dose.py`, `stats/concordance.py` at the 100% floor | property tests pass | ⛔ separate plan |
| F — corpus | 30 cores, 750-doc library, all authoring gates | 10% human realism audit | ⛔ separate plan |
| G — skills and run | `consequence-cascade` + structure-matched placebos, full grid | pre-registration hash locked | ⛔ separate plan |

**Milestone C is a stop point, not a checkpoint.** If the control arm scores ≥ 0.90 at 100k there is nothing to explain and D–G do not happen. That decision is worth about 2% of the full run's quota.

### Notation used throughout

- **Core** — one decision case: the governing documents plus the question. The unit of clustering.
- **Padding** — non-governing documents drawn from a shared library to reach a target length.
- **Admissibility** — every required action taken, no prohibited action taken, no unjustified action taken. *After Milestone B.*
- **Positive control** — one fact stated once, explicitly, at a known depth, requiring no inference. The only instrument that separates *didn't see it* from *saw it and reasoned badly*.

---

## File structure

**Created by this plan:**

| Path | Responsibility |
|---|---|
| `evals/src/decision_evals/budget.py` *(modified)* | gains `estimate_cost_usd` — the only place prompt length becomes a dollar figure |
| `scripts/pad.py` | assemble a core + a padding draw into a prompt of a target length; owns the ablation invariance check |
| `scripts/separability.py` | surface-feature classifier over documents. No model calls, so it is free and runs in CI |
| `scripts/detect_core.py` | ask a fresh model instance which documents matter, with the question stripped |
| `datasets/library/tax/*.md` | pilot padding library, tax |
| `datasets/library/employment/*.md` | pilot padding library, employment |
| `tests/unit/test_pad.py` | invariance, draw determinism, no-document-dominates |
| `tests/unit/test_separability.py` | the feature extractor and the AUC computation |
| `notebook/2026-08-11-pivot-out-of-admissibility.md` | the rescored deltas |
| `notebook/2026-08-12-long-gate-prediction.md` | numeric predictions, written **before** the run |
| `notebook/2026-08-12-long-gate-scored.md` | what happened, and the go/no-go |

**Modified:** `runner.py`, `scripts/calibrate.py`, `scripts/probe_casefile.py`, `skills/evidence-ledger/placebo.md`, `tests/unit/test_locks.py`, `tests/unit/test_runner.py`, `tests/unit/test_calibrate.py`.

Each script owns one gate and can be read in one sitting. `scripts/pad.py` is the only one with real logic, and its logic is a deterministic draw plus two assertions.

---

# Milestone A — the harness cannot lie at length

Closes task **#24**.

### Task 1: Cost authorisation that scales with prompt length

**Files:**
- Modify: `evals/src/decision_evals/budget.py` (add after `project_cost`, around line 44)
- Modify: `evals/src/decision_evals/runner.py:101-141`
- Test: `tests/unit/test_locks.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_locks.py`. `BudgetError` is already imported there alongside `BudgetLedger`; add `estimate_cost_usd` to that same import line rather than writing a second one:

```python
import pytest

from decision_evals.budget import BudgetError, estimate_cost_usd


def test_a_long_prompt_is_authorised_at_more_than_a_short_one() -> None:
    assert estimate_cost_usd(prompt_chars=400_000) > 20 * estimate_cost_usd(prompt_chars=1_500)


def test_the_estimate_never_falls_below_the_floor() -> None:
    assert estimate_cost_usd(prompt_chars=0) == pytest.approx(0.005)


@pytest.mark.parametrize(
    ("achieved_tokens", "observed_usd"),
    [(1_533, 0.0052), (25_489, 0.0298), (63_313, 0.0714), (101_142, 0.2296)],
)
def test_the_estimate_covers_every_call_the_canary_actually_made(
    achieved_tokens: int, observed_usd: float
) -> None:
    """An authorisation that under-counts is a budget that is not a budget.

    Canary filler measured 6.01 chars/token; the estimator assumes 4.0. The
    mismatch is deliberate and one-directional -- it over-estimates.
    """
    assert estimate_cost_usd(prompt_chars=int(achieved_tokens * 6.0)) >= observed_usd


def test_a_negative_length_is_a_bug_not_a_free_call() -> None:
    with pytest.raises(BudgetError):
        estimate_cost_usd(prompt_chars=-1)
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m uv run pytest tests/unit/test_locks.py -k estimate -v
```

Expected: `ImportError: cannot import name 'estimate_cost_usd'`.

- [ ] **Step 3: Implement**

Add to `evals/src/decision_evals/budget.py`, after `project_cost`:

```python
#: Notional dollars per prompt token, taken from the most expensive call the
#: long canary made ($0.2296 for 101,142 tokens = $2.27e-6) and rounded up. It
#: is an upper bound on purpose: this figure authorises a call *before* it is
#: made, and an authorisation that under-counts is not a budget.
_USD_PER_TOKEN: Final = 2.5e-6

#: Conservative chars-per-token. Canary filler measured 6.01; real casefile
#: prose tokenises worse and lands nearer 4. Assuming 4 over-estimates the
#: token count for anything more repetitive than prose, which is the direction
#: an authorisation should err in.
_CHARS_PER_TOKEN: Final = 4.0

#: Below this, per-call overhead dominates and the linear model under-reads.
_FLOOR_USD: Final = 0.005


def estimate_cost_usd(*, prompt_chars: int) -> float:
    """Project one call's notional cost from the length of its prompt.

    The ledger authorises before the call, so this must never read low. Every
    constant here is set to over-estimate, and the test suite pins that against
    the four real calls the long canary made.

    Raises:
        BudgetError: A negative length. Silently clamping would authorise a call
            at the floor when the caller's length arithmetic is broken.
    """
    if prompt_chars < 0:
        raise BudgetError(f"prompt_chars cannot be negative, got {prompt_chars}")
    tokens = prompt_chars / _CHARS_PER_TOKEN
    return max(tokens * _USD_PER_TOKEN, _FLOOR_USD)
```

Add `Final` to the `typing` import at the top of the file:

```python
from typing import Final
```

- [ ] **Step 4: Run to verify it passes**

```bash
python -m uv run pytest tests/unit/test_locks.py -k estimate -v
```

Expected: 7 passed.

- [ ] **Step 5: Wire it into the run loop**

In `evals/src/decision_evals/runner.py`, change the `run_arm` signature (line 101–109) so the flat default becomes opt-in:

```python
def run_arm(
    items: Sequence[Item],
    arm: ArmPrompt,
    *,
    model: str,
    checkpoint: Path,
    call: CallFn,
    ledger: BudgetLedger,
    expected_cost_usd: float | None = None,
) -> list[RunRecord]:
```

Replace the body's per-item block (line 126–139) with:

```python
    with checkpoint.open("a", encoding="utf-8") as handle:
        for item in items:
            if (item.item_id, arm.arm) in done:
                continue

            prompt = render_item(item)
            authorised = (
                expected_cost_usd
                if expected_cost_usd is not None
                else estimate_cost_usd(prompt_chars=len(prompt) + len(arm.system_prompt))
            )
            try:
                ledger.assert_can_afford(authorised)
            except Exception as exc:
                raise RunError(f"stopping before {item.item_id}: {exc}") from exc

            record = _run_one(item, arm, model=model, call=call, prompt=prompt)
            ledger = ledger.record(record.cost_usd)
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
            handle.flush()
            produced.append(record)
    return produced
```

Change `_run_one` (line 144–146) to take the already-rendered prompt, so the string that was measured is the string that is sent:

```python
def _run_one(
    item: Item, arm: ArmPrompt, *, model: str, call: CallFn, prompt: str
) -> RunRecord:
    try:
        result = call(prompt, arm.system_prompt, arm.append)
```

Update the import at line 33:

```python
from decision_evals.budget import BudgetLedger, estimate_cost_usd
```

- [ ] **Step 6: Add the run-loop test**

Append to `tests/unit/test_runner.py`:

```python
def test_a_long_item_is_authorised_at_more_than_the_old_flat_rate(tmp_path: Path) -> None:
    """The flat $0.05 default under-counted a 100k prompt by roughly 5x.

    A ledger with room for exactly one flat-rate call must refuse a long item
    rather than authorising it and discovering the shortfall afterwards.
    """
    long_item = _item(facts=["x" * 400_000])
    ledger = BudgetLedger(limit_usd=0.06)

    with pytest.raises(RunError, match="stopping before"):
        run_arm(
            [long_item],
            build_arm("off"),
            model="haiku",
            checkpoint=tmp_path / "c.jsonl",
            call=_never_called,
            ledger=ledger,
        )
```

Where `_item` is the existing item factory in that module and `_never_called` raises if invoked — reuse whichever helpers `tests/unit/test_runner.py` already defines rather than adding new ones.

- [ ] **Step 7: Run the full gate**

```bash
python -m uv run de check
```

Expected: all steps pass.

- [ ] **Step 8: Commit**

```bash
git add evals/src/decision_evals/budget.py evals/src/decision_evals/runner.py tests/unit/test_locks.py tests/unit/test_runner.py && git commit -m "runner: authorise a call by its length, not by a flat guess"
```

---

### Task 2: The corpus fingerprint must see document bodies

**Files:**
- Modify: `scripts/calibrate.py:98-116`
- Test: `tests/unit/test_calibrate.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_calibrate.py`:

```python
def test_changing_a_document_body_changes_the_fingerprint() -> None:
    """Padding lives in documents, not in facts.

    A fingerprint blind to document bodies lets a padded corpus resume off a
    checkpoint built from the unpadded one and report a number computed half on
    each -- which is the single most damaging bug this harness could have.
    """
    before = _item_with_documents([("doc1", "The figure was 12.")])
    after = _item_with_documents([("doc1", "The figure was restated to 14.")])

    assert corpus_fingerprint([before]) != corpus_fingerprint([after])


def test_reordering_documents_changes_the_fingerprint() -> None:
    """Padding order is reshuffled between arms; a run must not resume across it."""
    a = _item_with_documents([("doc1", "alpha"), ("doc2", "beta")])
    b = _item_with_documents([("doc2", "beta"), ("doc1", "alpha")])

    assert corpus_fingerprint([a]) != corpus_fingerprint([b])
```

Add the helper at the top of the test module:

```python
def _item_with_documents(bodies: list[tuple[str, str]]) -> Item:
    """An Item carrying documents, which is what a casefile is."""
    item = _base_item()
    object.__setattr__(item, "documents", [{"id": i, "body": b} for i, b in bodies])
    return item
```

Reuse the module's existing item factory for `_base_item`.

- [ ] **Step 2: Run to verify it fails**

```bash
python -m uv run pytest tests/unit/test_calibrate.py -k fingerprint -v
```

Expected: FAIL — both fingerprints identical, because `corpus_fingerprint` never reads `documents`.

- [ ] **Step 3: Implement**

Replace the digest loop in `scripts/calibrate.py` (lines 108–116):

```python
    digest = hashlib.sha256()
    for item in items:
        digest.update(item.item_id.encode())
        digest.update(item.question.encode())
        digest.update(item.answer.encode())
        for fact in item.facts:
            digest.update(f"{fact.id}:{fact.text}".encode())
        # Documents carry the padding, which is the independent variable. They
        # are hashed in order because padding order is a stratum: reshuffling
        # it produces a different prompt and must not resume off the old one.
        for document in getattr(item, "documents", ()):
            digest.update(f"{document['id']}:{document['body']}".encode())
    return digest.hexdigest()
```

Extend the docstring with a second paragraph:

```python
    Document bodies are included for the same reason facts are, and it is the
    version of this bug that bites at length: item ids stay identical while a
    hundred thousand tokens of padding change underneath them.
```

- [ ] **Step 4: Run to verify it passes**

```bash
python -m uv run pytest tests/unit/test_calibrate.py -v
```

Expected: all pass, including the pre-existing fingerprint tests (facts still contribute).

- [ ] **Step 5: Commit**

```bash
git add scripts/calibrate.py tests/unit/test_calibrate.py && git commit -m "calibrate: the fingerprint sees document bodies and their order"
```

---

### Task 3: A checkpoint record that does not parse is an error, not a silence

**Files:**
- Modify: `evals/src/decision_evals/runner.py:211-221`
- Test: `tests/unit/test_runner.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_runner.py`:

```python
def test_a_record_from_an_older_schema_is_refused_loudly(tmp_path: Path) -> None:
    """Adding a stratum column must not make every earlier record vanish.

    load_records swallowed TypeError, so a schema change silently returned an
    empty list and the analysis reported a run that had not happened.
    """
    checkpoint = tmp_path / "c.jsonl"
    checkpoint.write_text('{"item_id": "rel-001-v0", "arm": "off"}\n', encoding="utf-8")

    with pytest.raises(RunError, match="schema"):
        load_records(checkpoint)


def test_a_truncated_final_line_is_tolerated(tmp_path: Path) -> None:
    """A crash mid-write leaves a partial line. That is expected and recoverable;
    a well-formed record with the wrong columns is not."""
    checkpoint = tmp_path / "c.jsonl"
    checkpoint.write_text(_record_json() + '\n{"item_id": "rel-', encoding="utf-8")

    assert len(load_records(checkpoint)) == 1
```

Where `_record_json()` returns one complete `RunRecord` serialised with `json.dumps(asdict(...))` — build it from the module's existing record factory.

- [ ] **Step 2: Run to verify it fails**

```bash
python -m uv run pytest tests/unit/test_runner.py -k schema -v
```

Expected: FAIL — `load_records` returns `[]` instead of raising.

- [ ] **Step 3: Implement**

Replace `load_records` in `evals/src/decision_evals/runner.py`:

```python
def load_records(checkpoint: Path) -> list[RunRecord]:
    """Read a checkpoint back for analysis.

    A JSON parse failure on the *final* line is tolerated: a run killed mid-write
    leaves a partial line and that is recoverable. Anything else is refused.

    A well-formed line that does not fit ``RunRecord`` used to be skipped, which
    meant adding a column made every earlier record disappear and the analysis
    reported a run that had not happened. That is the failure mode this function
    now exists to prevent.

    Raises:
        RunError: A record does not match the current schema.
    """
    if not checkpoint.exists():
        return []

    lines = checkpoint.read_text(encoding="utf-8").splitlines()
    records: list[RunRecord] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            if number == len(lines):
                break  # partial final write; the run was killed here
            raise RunError(f"{checkpoint}:{number} is not JSON and is not the last line")
        try:
            records.append(RunRecord(**payload))
        except TypeError as exc:
            raise RunError(
                f"{checkpoint}:{number} does not match the current RunRecord schema: {exc}\n"
                "Move the checkpoint aside and re-run rather than analysing a subset."
            ) from exc
    return records
```

- [ ] **Step 4: Run to verify it passes**

```bash
python -m uv run pytest tests/unit/test_runner.py -v
```

Expected: all pass.

- [ ] **Step 5: Run the full gate**

```bash
python -m uv run de check
```

- [ ] **Step 6: Commit and close task #24**

```bash
git add evals/src/decision_evals/runner.py tests/unit/test_runner.py && git commit -m "runner: a checkpoint record that does not fit the schema stops the analysis"
```

---

# Milestone B — the metric measures the model, not the key

Closes task **#25**.

### Task 4: Take the pivot conjunct out of admissibility

**Files:**
- Modify: `scripts/probe_casefile.py:421-470`
- Test: `tests/unit/test_scorers.py`

**Why:** Six of six probe failures were the answer key. Five were this conjunct alone — the scorer demanded the literal string `NONE` while the model named a real determinative unknown. On probe-09 it named *"evidence of a compliant written cure notice … served before the protected concern was raised"*, which is the exact fact `s.46(3)` turns on and a better pivot than the one written into the key. Naming a useful unknown is competent behaviour and the scorer was punishing it.

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_scorers.py`:

```python
def test_naming_a_real_unknown_no_longer_costs_admissibility() -> None:
    """probe-09: the model named the fact s.46(3) turns on and was scored zero."""
    case = _casefile(required={"a1"}, prohibited={"a7"}, pivot_present=False)
    parsed = _parsed(actions={"a1"}, missing="Evidence of a compliant cure notice.")

    assert score(case, parsed).admissible


def test_a_prohibited_action_still_costs_admissibility() -> None:
    case = _casefile(required={"a1"}, prohibited={"a7"}, pivot_present=False)
    parsed = _parsed(actions={"a1", "a7"}, missing="NONE")

    assert not score(case, parsed).admissible


def test_an_unjustified_action_now_costs_admissibility() -> None:
    """An action licensed only by a non-governing condition is a real failure and
    was previously diagnostic only."""
    case = _casefile(required={"a1"}, prohibited=set(), unjustified={"a4"}, pivot_present=False)
    parsed = _parsed(actions={"a1", "a4"}, missing="NONE")

    assert not score(case, parsed).admissible


def test_pivot_recall_is_still_recorded_as_a_secondary() -> None:
    case = _casefile(required={"a1"}, prohibited=set(), pivot_present=False)
    parsed = _parsed(actions={"a1"}, missing="Evidence of a compliant cure notice.")
    scored = score(case, parsed)

    assert scored.admissible
    assert scored.named_an_unknown
    assert not scored.pivot_ok
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m uv run pytest tests/unit/test_scorers.py -k "admissib or pivot" -v
```

Expected: FAIL — `Scored` has no attribute `named_an_unknown`; the first test fails on `pivot_ok`.

- [ ] **Step 3: Implement**

In `scripts/probe_casefile.py`, add one field to `Scored` (after `pivot_ok`, line 411):

```python
    named_an_unknown: bool = False
```

Replace the pivot block and the admissibility conjunction in `score` (lines 430–449):

```python
    pivot = case.raw.get("pivot") or {}
    if pivot.get("present"):
        haystack = parsed.missing.casefold()
        pivot_ok = any(phrase.casefold() in haystack for phrase in pivot.get("accepts", []))
    else:
        pivot_ok = parsed.missing.strip().upper().startswith("NONE")

    # Secondary, and the honest version of what the pivot was trying to measure.
    # Naming a determinative unknown is competent behaviour whether or not it is
    # the unknown I happened to write down. Five of six probe failures were this
    # distinction, and twice the model's unknown was better than mine.
    named_an_unknown = bool(parsed.missing.strip()) and not parsed.missing.strip().upper().startswith(
        "NONE"
    )

    unjustified_hit = bool(recommended & set(case.by_failure_kind("unjustified")))

    # The primary. Three conjuncts, all objective, none of them a judgement
    # about which unknown mattered most. An action is inadmissible when the case
    # requires it and it was skipped, when the case prohibits it, or when nothing
    # in the governing conditions licenses it.
    admissible = not missing_required and not took_prohibited and not unjustified_hit
```

Then in the returned `Scored`, replace `trap_hit=...`/`unjustified_hit=...` with:

```python
trap_hit = (bool(recommended & set(case.by_failure_kind("trap"))),)
unjustified_hit = (unjustified_hit,)
pivot_ok = (pivot_ok,)
named_an_unknown = (named_an_unknown,)
```

- [ ] **Step 4: Run to verify it passes**

```bash
python -m uv run pytest tests/unit/test_scorers.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/probe_casefile.py tests/unit/test_scorers.py && git commit -m "scoring: admissibility is required, prohibited and unjustified -- not my pivot"
```

---

### Task 5: A graded outcome, because binary admissibility is nearly a constant

**Files:**
- Modify: `scripts/probe_casefile.py` (`Scored`, `score`, and `report`)
- Test: `tests/unit/test_scorers.py`

**Why:** With 0/12 prohibited actions taken and 0/12 traps taken in the probe, essentially all of admissibility's observed variance came from the pivot conjunct just removed. Strip it and the primary carries about one bit. The likely real signature of degradation under long context is not a wrong answer but a longer, hedgier, less committed one — and a binary metric is blind to that.

- [ ] **Step 1: Write the failing test**

```python
def test_the_graded_score_separates_two_admissible_answers() -> None:
    """Both are admissible. One found every governing condition, one found half.
    A binary primary calls them identical."""
    case = _casefile(
        required={"a1"}, prohibited={"a7"}, governing={"c1", "c2", "c3", "c4"}, pivot_present=False
    )
    thorough = score(case, _parsed(actions={"a1"}, conditions={"c1", "c2", "c3", "c4"}))
    thin = score(case, _parsed(actions={"a1"}, conditions={"c1", "c2"}))

    assert thorough.admissible and thin.admissible
    assert thorough.graded > thin.graded


def test_the_graded_score_is_bounded() -> None:
    case = _casefile(required={"a1"}, prohibited={"a7"}, governing={"c1"}, pivot_present=False)
    perfect = score(case, _parsed(actions={"a1"}, conditions={"c1"}))
    empty = score(case, _parsed(actions=set(), conditions=set()))

    assert perfect.graded == pytest.approx(1.0)
    assert 0.0 <= empty.graded <= 1.0
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m uv run pytest tests/unit/test_scorers.py -k graded -v
```

Expected: `AttributeError: 'Scored' object has no attribute 'graded'`.

- [ ] **Step 3: Implement**

Add to `Scored` in `scripts/probe_casefile.py`:

```python
    @property
    def graded(self) -> float:
        """Admissibility's components, averaged rather than conjoined.

        Three equally weighted terms: the fraction of required actions taken,
        the fraction of prohibited-and-unjustified actions avoided, and the
        recall on governing conditions. Continuous, so two admissible answers of
        different quality are not the same number -- which is what the paired
        slope test needs and what the binary primary cannot supply.
        """
        return (self.required_taken + self.forbidden_avoided + self.condition_recall) / 3.0
```

Add the two supporting fields to `Scored`:

```python
    required_taken: float = 0.0
    forbidden_avoided: float = 1.0
```

And compute them in `score`, just before the return:

```python
n_required = len(required)
required_taken = (n_required - len(missing_required)) / n_required if n_required else 1.0

forbidden = prohibited | set(case.by_failure_kind("unjustified"))
hit_forbidden = recommended & forbidden
forbidden_avoided = (len(forbidden) - len(hit_forbidden)) / len(forbidden) if forbidden else 1.0
```

Pass both into the `Scored(...)` construction.

- [ ] **Step 4: Run to verify it passes**

```bash
python -m uv run pytest tests/unit/test_scorers.py -v
```

- [ ] **Step 5: Report the graded outcome**

In `report()` (around line 631), add a line beside the admissibility figure:

```python
    graded = sum(r["graded"] for r in rows) / len(rows)
    print(f"  graded admissibility        {graded:.3f}")
```

and add `"graded": scored.graded` and `"named_an_unknown": scored.named_an_unknown` to the row dict written at the checkpoint site (around line 605).

- [ ] **Step 6: Commit**

```bash
git add scripts/probe_casefile.py tests/unit/test_scorers.py && git commit -m "scoring: a graded outcome alongside the binary one"
```

---

### Task 6: Rescore the three existing probe runs and record the delta

**Files:**
- Read: `results/probe/casefile-probe.jsonl`, `casefile-probe-nomenu.jsonl`, `casefile-probe-bare.jsonl`
- Create: `notebook/2026-08-11-pivot-out-of-admissibility.md`

**No model calls.** The responses are already on disk; only the scorer changed.

- [ ] **Step 1: Rescore**

```bash
python -m uv run python scripts/probe_casefile.py --report
```

Repeat for the `--no-menu` and `--bare` checkpoints. Record, for each of the three runs: admissibility before, admissibility after, graded admissibility, and how many of the previously-failing items are now admissible.

- [ ] **Step 2: Write the notebook entry**

`notebook/2026-08-11-pivot-out-of-admissibility.md`. It must state, in this order:

1. The metric as it was, and the exact conjunction.
2. That 5 of 6 scored failures were this conjunct alone, with the probe-09 quotation.
3. The three before/after tables.
4. **The uncomfortable part:** how much of the probe's headline "27 trap opportunities, zero taken" result was already true and how much was hidden by a metric that failed competent answers. If the corrected admissibility is now above `ADMISSIBILITY_CEILING = 0.85`, say so plainly — it strengthens the negative result rather than weakening it, and it means the short-corpus venue has even less headroom than reported.
5. Whether the graded outcome has enough variance to be a primary, or whether it too is near-constant at 2k. If it is near-constant, that is a finding about the venue and belongs in the Milestone C prediction.

- [ ] **Step 3: Commit and close task #25**

```bash
git add notebook/2026-08-11-pivot-out-of-admissibility.md results/probe/ && git commit -m "notebook: what the probe scores were actually measuring"
```

---

# Milestone C — six instrument gates, then a go/no-go

The distinction this project has been missing: a **hypothesis falsifier** says the skill has nothing to fix. An **instrument falsifier** says the venue cannot answer the question and the run should not happen. Three corpora produced three nulls that each needed a paragraph of interpretation, because only the first kind was ever written down.

Every acceptance band below is fixed **before looking**.

| Gate | Cost | Kill condition | Task |
|---|---|---|---|
| Canary recall at 100k, three depths | $2 | any canary missing → the prompt is not arriving | ✅ passed |
| Placebo/skill structural diff | free | word ratio outside ±0.15 → confounded arm | ✅ passes at 1.057 |
| Placebo/skill *output-template* diff | free | treatment emits a block template, placebo does not → format confound | 7 |
| Surface-feature separability | free | a trivial classifier gets AUC > 0.70 → re-author | 9 |
| Padding-only ablation | $10 | model answers confidently with the core removed → invariance broken | 11 |
| Core-detection probe | $3 | core precision > 0.60 → padding is transparent | 12 |
| **Control admissibility at 100k** | $8 | **≥ 0.90 → nothing to explain, stop. ≤ 0.15 → a reading-stamina test, shorten. Target [0.25, 0.70]** | 14 |

### Task 7: The placebo mismatch the word-count guard cannot see

**Files:**
- Modify: `skills/evidence-ledger/placebo.md`
- Modify: `evals/src/decision_evals/solvers/arms.py` (`PlaceboMatch`)
- Test: `tests/unit/test_arms.py`

**The original premise here was wrong and is recorded as such.** `check_placebo_match` compares the placebo against the skill's *body*, and the body is 421 words against a 445-word placebo — a ratio of **1.057**, inside the ±0.15 tolerance. `de check`'s skill lint has been passing it all along. The "0.71" counted YAML frontmatter as skill prose; the model never sees the frontmatter.

**What survives is a different and sharper problem.** `SKILL.md` ends with an output template:

```
LEDGER
  1. <fact> — <what it decides>
SET ASIDE
  - <fact> — <why it is not load-bearing>
THEREFORE
  <the decision, following from the ledger alone>
```

The placebo ends with a paragraph about writing plainly. So the `on` arm receives *a second format instruction* and the `placebo` arm does not — and the venue already imposes a five-block contract of its own. Word count and heading count are both matched and both blind to this. An arm that emits more structure because it was told to emit more structure, scored on a structured contract, is a format effect wearing a decision effect's clothes.

This is the confound the plan flags for Milestone G, and it is cheaper to fix now.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_arms.py`:

```python
def test_a_placebo_without_the_skills_output_template_is_not_matched() -> None:
    """Word count and heading count are both blind to a fenced output block.

    A treatment that hands the model a template and a placebo that does not is
    an arm pair differing in how much structure was requested, which is exactly
    what the venue then scores.
    """
    skill = "# S\n\nsome guidance\n\n```\nBLOCK\n  <thing>\n```\n"
    placebo = "# P\n\nsome guidance\n\nwritten as ordinary prose instead.\n"

    assert not check_placebo_match(skill, placebo).templates_match


def test_matching_fenced_blocks_satisfy_the_template_check() -> None:
    skill = "# S\n\nguidance\n\n```\nBLOCK\n  <thing>\n```\n"
    placebo = "# P\n\nguidance\n\n```\nSECTION\n  <thing>\n```\n"

    assert check_placebo_match(skill, placebo).templates_match
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m uv run pytest tests/unit/test_arms.py -k template -v
```

Expected: `AttributeError: 'PlaceboMatch' object has no attribute 'templates_match'`.

- [ ] **Step 3: Add the check**

In `evals/src/decision_evals/solvers/arms.py`, extend `PlaceboMatch` with fenced-block counts and fold the new property into `ok`:

```python
skill_templates: int = 0
placebo_templates: int = 0


@property
def templates_match(self) -> bool:
    """Whether both documents request the same number of output templates.

    A fenced block in a skill is almost always an output contract. Length and
    heading count cannot see one, so a treatment carrying a template against
    a placebo carrying none passes both existing checks while differing in
    the one dimension the venue scores.
    """
    return self.skill_templates == self.placebo_templates


@property
def ok(self) -> bool:
    return self.words_match and self.structure_matches and self.templates_match
```

and count them in `check_placebo_match` with a `_count_fences` helper mirroring `_count_headings`.

- [ ] **Step 4: Rewrite the placebo's closing section**

Replace "A note on style" with a section that carries a fenced block of the same shape and no procedural content — a template that asks for the answer and nothing that would help produce it. It must not name a step that does work: no "list your evidence", no "state your assumptions", no "what would change your mind". Those are the active ingredient in prose.

Keep the word count inside ±15% of the 421-word body (358–484) and the heading count at 5.

Then read both files side by side with the titles removed and ask whether a colleague could tell which is the intervention. If yes, it is rewritten.

- [ ] **Step 5: Run the gate**

```bash
python -m uv run de check
```

- [ ] **Step 6: Commit**

```bash
git add skills/ evals/src/decision_evals/solvers/arms.py tests/unit/test_arms.py && git commit -m "arms: a placebo must match the skill's output template, not just its length"
```

---

### Task 8: The padding assembler, with invariance built in

**Files:**
- Create: `scripts/pad.py`
- Create: `tests/unit/test_pad.py`

**What it does:** takes a casefile core and a padding library, draws deterministically from the library by seed, interleaves the draw around the core at a fixed proportional depth band, and returns a prompt of a target length — refusing to return one if the draw would change the answer.

- [ ] **Step 1: Write the failing tests**

`tests/unit/test_pad.py`:

```python
"""The assembler is where the independent variable is manufactured.

Three properties, and each of them has a documented way of quietly failing:
the draw must be reproducible, the padding must not change the answer, and no
single library document may appear in enough cells to become a crossed random
effect that makes the standard errors wrong.
"""

from __future__ import annotations

import pytest

from pad import PaddingError, ablate, assemble, draw, governing_depths


def test_the_same_seed_draws_the_same_documents() -> None:
    assert draw(_library(40), target_tokens=10_000, seed=7) == draw(
        _library(40), target_tokens=10_000, seed=7
    )


def test_a_different_seed_draws_differently() -> None:
    assert draw(_library(40), target_tokens=10_000, seed=7) != draw(
        _library(40), target_tokens=10_000, seed=8
    )


def test_padding_that_mentions_a_governing_number_is_refused() -> None:
    """On-topic at the client level, off-topic at the decision level. A padding
    document that repeats a figure from the governing chain is neither."""
    core = _core(governing_text="The correction charge is $297,000.")
    poisoned = [_document("pad1", "The prior-year charge was $297,000.")]

    with pytest.raises(PaddingError, match="297,000"):
        assemble(core, poisoned, target_tokens=10_000, seed=1)


def test_governing_documents_sit_in_the_stated_depth_band() -> None:
    """Depth is held proportional so absolute distance varies with length while
    relative position does not. If this drifts, the dose curve is a position
    curve wearing a length label."""
    prompt = assemble(_core(), _library(200), target_tokens=40_000, seed=1)

    for depth in governing_depths(prompt, _core()):
        assert 0.30 <= depth <= 0.60


def test_no_library_document_dominates_the_draw() -> None:
    """A document drawn into many cells is a crossed random effect: one loud or
    one truth-perturbing document contaminates many cells and the standard
    errors are wrong in the anti-conservative direction."""
    library = _library(200)
    cells = [draw(library, target_tokens=40_000, seed=s) for s in range(30)]

    for document in library:
        appearances = sum(1 for cell in cells if document in cell)
        assert appearances / len(cells) <= 0.30


def test_a_library_too_small_for_the_target_is_an_error_not_a_short_prompt() -> None:
    """Silently returning 12k tokens when 100k was asked for would put the wrong
    length label on a whole stratum."""
    with pytest.raises(PaddingError, match="too small"):
        assemble(_core(), _library(3), target_tokens=100_000, seed=1)


def test_the_ablated_prompt_keeps_the_padding_and_drops_the_core() -> None:
    """Feeds the padding-only gate. If the core survives ablation the gate is
    testing nothing, and it would pass for that reason rather than a real one."""
    core = _core(governing_text="The correction charge is $297,000.")
    library = _library(200)

    ablated = ablate(core, library, target_tokens=40_000, seed=1)

    assert "$297,000" not in ablated
    assert any(document.body in ablated for document in library)
```

Add the `_library`, `_core` and `_document` factories at the top of the module.

- [ ] **Step 2: Run to verify it fails**

```bash
python -m uv run pytest tests/unit/test_pad.py -v
```

Expected: `ModuleNotFoundError: No module named 'pad'`.

- [ ] **Step 3: Implement `scripts/pad.py`**

The public surface is exactly four names:

```python
class PaddingError(ValueError):
    """The draw cannot produce a valid prompt at this length."""


def draw(library: Sequence[Document], *, target_tokens: int, seed: int) -> list[Document]:
    """Deterministically select padding documents summing to ``target_tokens``.

    Uses ``random.Random(seed)`` and shuffles a copy, never the caller's list.
    Raises PaddingError if the whole library is shorter than the target.
    """


def assemble(core: Core, library: Sequence[Document], *, target_tokens: int, seed: int) -> str:
    """Core plus a padding draw, rendered as one prompt.

    Runs the mechanical invariance check before returning: no padding document
    may contain a numeral, date, party name, or section number that appears
    anywhere in the governing chain. Raises PaddingError naming the collision.

    The rule is relaxed per-mechanism for near-miss authority items, which
    deliberately violate it -- and those are exactly the items where this check
    cannot protect the answer key, which is why they carry the heaviest share of
    the adversarial perturbation audit.
    """


def governing_depths(prompt: str, core: Core) -> list[float]:
    """Where each governing document landed, as a fraction of the prompt."""


def ablate(core: Core, library: Sequence[Document], *, target_tokens: int, seed: int) -> str:
    """The same prompt with every core document removed. Feeds the ablation gate."""
```

Implementation notes that are decisions, not detail:

- Measure the chars-per-token ratio **of the actual assembled text**, not of the canary filler. The canary measured 6.01 on repetitive filler; real casefile prose lands nearer 4. `scripts/canary_long.py:53` says this in a comment and it must not be borrowed.
- Interleave rather than block: the core documents are distributed inside the 30–60% band, with padding before, between and after. Padding *order* is reshuffled per arm from a derived seed so a single unlucky arrangement cannot drive a cell.
- The invariance check tokenises the governing chain into numerals, ISO and prose dates, capitalised party names and `s.NN(N)` section references, and greps each padding body for them.

- [ ] **Step 4: Run to verify it passes**

```bash
python -m uv run pytest tests/unit/test_pad.py -v
```

- [ ] **Step 5: Run the full gate**

```bash
python -m uv run de check
```

- [ ] **Step 6: Commit**

```bash
git add scripts/pad.py tests/unit/test_pad.py && git commit -m "pad: assemble a long prompt without changing its answer"
```

---

### Task 9: Surface-feature separability — the free gate

**Files:**
- Create: `scripts/separability.py`
- Create: `tests/unit/test_separability.py`

**Why this gate exists, and why it is the one most likely to fire:** prose written to *not matter* has a signature — fewer hard numerals, fewer deontic verbs, fewer citations, fewer dates with consequences attached, more hedging, flatter sentences. The core is dense with exactly those things *because that is what makes it the core*. On-topic-ness fixes **topical** separability and does nothing for **register** separability. A model doing salience-weighted attention would then find the core in constant time however long the file got, and the dose curve would come out flat — and the conclusion "no context rot at this scale" would be reported when the retrieval difficulty was never manipulated at all.

- [ ] **Step 1: Write the failing tests**

`tests/unit/test_separability.py`:

```python
from __future__ import annotations

import pytest

from separability import auc, features


def test_obviously_different_registers_are_separable() -> None:
    """The detector must have teeth before it is trusted to say 'no signal'."""
    core = [_doc("s.44(1) The employer must serve notice within 14 days of 3 March 2026.")] * 5
    padding = [_doc("The position is broadly unchanged and no variation was sought.")] * 20

    assert auc(features(core), features(padding)) > 0.90


def test_identical_registers_score_at_chance() -> None:
    same = [_doc("s.44(1) The employer must serve notice within 14 days.")] * 10
    assert auc(features(same[:5]), features(same[5:])) == pytest.approx(0.5, abs=0.05)


def test_the_feature_vector_names_every_feature_it_extracts() -> None:
    """Six features, and a reader must be able to see which one carried the AUC."""
    extracted = features([_doc("s.44(1) The employer must pay $12,000 by 3 March 2026.")])
    assert set(extracted[0]) == {
        "numerals",
        "citations",
        "deontic_verbs",
        "dates",
        "mean_sentence_length",
        "type_token_ratio",
    }
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m uv run pytest tests/unit/test_separability.py -v
```

- [ ] **Step 3: Implement**

`scripts/separability.py` exposes exactly two names:

```python
#: The six features, and the reason each is here. Prose written to not-matter
#: is thinner in every one of them, and the core is dense in every one of them
#: *because that is what makes it the core*.
FEATURES: Final = (
    "numerals",  # hard figures per 100 words
    "citations",  # s.NN(N) and similar references per 100 words
    "deontic_verbs",  # must / shall / may not / is required to
    "dates",  # ISO and prose dates per 100 words
    "mean_sentence_length",  # padding hedges, and hedging is long
    "type_token_ratio",  # padding repeats itself
)


def features(documents: Sequence[Document]) -> list[dict[str, float]]:
    """One feature vector per document, keyed by :data:`FEATURES`."""


def auc(core: Sequence[dict[str, float]], padding: Sequence[dict[str, float]]) -> float:
    """Area under the ROC for separating core from padding.

    Deliberately trivial -- the best single-feature AUC, or one logistic fit.
    The claim under test is *"a model could do this easily"*, and a trivial
    classifier succeeding is far stronger evidence for that than a tuned one
    succeeding. A tuned classifier failing would prove nothing either way.
    """
```

Report the per-feature AUC alongside the pooled figure. If the gate fails, the per-feature breakdown says which knob to turn — and it will usually be `numerals` or `citations`, which is exactly the tension Task 10 is authored against.

- [ ] **Step 4: Run to verify it passes**

```bash
python -m uv run pytest tests/unit/test_separability.py -v
```

- [ ] **Step 5: Commit**

```bash
git add scripts/separability.py tests/unit/test_separability.py && git commit -m "separability: can a trivial classifier find the core?"
```

---

### Task 10: The pilot padding library

**Files:**
- Create: `datasets/library/tax/` (~25 documents)
- Create: `datasets/library/employment/` (~25 documents)

**Scale — and the plan's arithmetic was wrong here by more than tenfold.**

A 100k-token prompt is 400,000 characters of padding. The twelve pilot documents authored so far average 938 characters and total 11,256 — they reach **2,814 tokens**. The gap is not marginal:

| Target | Chars needed | Documents drawn (at 938 ch) | Documents drawn (at 4,000 ch) |
|---|---|---|---|
| 10k | 40,000 | 43 | 10 |
| 40k | 160,000 | 171 | 40 |
| **100k** | **400,000** | **426** | **100** |

Under the 30% domination cap those become libraries of 1,421 and 333 respectively. The cap is now a parameter, and the Phase 0 pilot may relax it because it computes no standard errors — so the pilot floor is the *drawn* count, not the capped one.

**So the pilot needs roughly 100–120 documents of ~4,000 characters per domain to reach a 100k anchor.** That is about 480,000 characters of authored professional prose per domain, and it is the real cost of Milestone C. The plan's "~25 documents per domain" would not have reached 3k tokens.

This is authoring cost, not quota cost. The model-call gates (Tasks 11, 12, 14) are ~$21 notional between them and cannot run at all until the library exists.

Three ways to close it, and the choice belongs to whoever is paying the authoring:

1. **Author the full pilot library** — ~120 documents × 2 domains at ~4,000 chars. Keeps the 100k anchor, which is the length the canary proved and the length the hypothesis is about.
2. **Lower the top anchor** to what a smaller library supports — 40k needs 40 documents per domain at 4,000 chars. Cheaper, and 40k is still four times anything this project has measured, but it tests a weaker version of the claim.
3. **Fewer, longer documents** — facility agreements, handbooks and statute extracts run to 10,000+ characters legitimately. 100k then needs 40 documents. Realistic for authorities and schedules, not for correspondence, so it skews the register mix toward exactly the high-salience end the separability gate is most sensitive to.

**The authoring rule, and it is not the obvious one.** Padding must be **on-topic at the client level, off-topic at the decision level** — a tax matter file full of documents about the same client that have nothing to do with whether this year's amendment reopens the look-back window. Off-topic padding would repeat the GSM-NoOp mistake, where a distractor a reasonable reader folds into the calculation is not a distractor at all.

**And a substantial fraction must carry citations, hard numbers, deadlines and imperative language while being genuinely non-governing.** That is what Task 9 is measuring, and it makes padding nearly as expensive to author as core. The two threats are in direct tension: surface-matched padding is the only padding that makes the manipulation real, and it is the padding most likely to break invariance. "Deterministic draw from a shared library" is doing much less work than it sounds like.

- [ ] **Step 1: Author 10 documents per domain in the low-salience register**

Prior-year correspondence, filed and closed. Routine payroll queries. Board minutes on unrelated matters. Each with a date, an author, and a purpose.

- [ ] **Step 2: Author 15 documents per domain in the high-salience register**

Facility agreements with forty clauses of which none apply here. Bulletins on adjacent subsections. Deadlines that have already passed. Amounts that are large and irrelevant. These must read as if they *could* matter and must not.

- [ ] **Step 3: Run the invariance check against all four pilot cores**

```bash
python -m uv run python scripts/pad.py --check-invariance --cores probe-07 probe-09 probe-11 probe-12
```

Expected: no collisions. Any hit repairs that padding document.

- [ ] **Step 4: Run the separability gate**

```bash
python -m uv run python scripts/separability.py --library datasets/library --cores datasets/probe
```

Expected: pooled AUC ≤ 0.70. **If it exceeds 0.70, stop and re-author** — do not proceed to the model gates, because they will measure the wrong thing.

- [ ] **Step 5: Commit**

```bash
git add datasets/library/ && git commit -m "library: a pilot padding corpus that does not read like padding"
```

---

### Task 11: The padding-only ablation gate

**Files:**
- Uses: `scripts/pad.py:ablate`
- Appends to: `results/probe/long-gate.jsonl`

**~$10.** Delete the core, keep the padding, ask the question anyway. If the model answers confidently instead of declining, the padding carries signal and invariance is broken regardless of what the mechanical check said.

- [ ] **Step 1: Run**

```bash
python -m uv run python scripts/probe_casefile.py --ablate --lengths 40000 100000 --model haiku
```

- [ ] **Step 2: Read every response**

Not the summary — every response. The pass condition is that the model declines or flags the missing material. A confident answer built from padding alone is the gate failing.

- [ ] **Step 3: Record**

Append the count of confident answers to the run log. Any non-zero count names the specific padding documents responsible and sends them back to Task 10.

---

### Task 12: The core-detection probe

**Files:**
- Create: `scripts/detect_core.py`

**~$3.** Hand a fresh model instance an assembled file with the question stripped and ask which five documents a professional would need. This is a **gate, not a diagnostic**: a failed detectability probe means the whole dose curve is measuring "find the document that reads differently."

- [ ] **Step 1: Implement**

`scripts/detect_core.py` assembles each pilot core at 40k and 100k via `pad.assemble`, strips the question and the format contract, and asks for five document ids:

```python
DETECTION_PROMPT: Final = (
    "The file above is one professional matter. Name the five documents a "
    "professional advising on this matter would need to read. Output five "
    "document ids, one per line, and nothing else."
)


@dataclass(frozen=True)
class Detection:
    case_id: str
    target_tokens: int
    named: list[str]
    core_ids: list[str]
    n_documents: int

    @property
    def precision(self) -> float:
        """Fraction of the five named ids that were actually core."""
        return len(set(self.named) & set(self.core_ids)) / len(self.named) if self.named else 0.0

    @property
    def chance(self) -> float:
        """What precision a uniform random pick of five would get on this file.

        Reported alongside precision because the gate is 'above chance', and
        chance falls as the file grows -- so a fixed 0.60 threshold is stricter
        at 100k than at 40k, which is the correct direction.
        """
        return len(self.core_ids) / self.n_documents if self.n_documents else 0.0
```

Results append to `results/probe/core-detection.jsonl`; the summary prints precision and chance side by side per case per length.

- [ ] **Step 2: Run**

```bash
python -m uv run python scripts/detect_core.py --cores probe-07 probe-09 probe-11 probe-12 --lengths 40000 100000
```

- [ ] **Step 3: Apply the gate**

Core precision > 0.60 → the padding is transparent. Mitigation is structural, not cosmetic: author the file as **one matter end-to-end and designate core documents afterwards**, rather than writing core and filler separately. That is a Task 10 rewrite, not a tweak.

---

### Task 13: Two life-decision triplets

**Files:**
- Create: `datasets/probe/probe-13-*.yaml`, `probe-14-*.yaml` (each as three variants)

**Structure.** Same person, same question, same context length, three files:

1. **Base.**
2. **Governing fact changed** — six months of emergency fund becomes three weeks of runway with a lease renewal in forty days. The recommendation *should* move.
3. **Matched non-governing fact changed** — a perturbation of equal salience that should change nothing.

The third file is not optional. Without it the metric is **unidentified**: a model that flips on any perturbation whatsoever scores a perfect 1.0 and is indistinguishable from one that reads carefully.

**The perturbation must not cue itself.** A value change inside an otherwise byte-identical document — `"$4,200 emergency fund"` → `"$41,000"` — never an added or removed document. Variants match on document count, order, token length and register, and a build-time check asserts the diff is a single span in a document that is not first, last, longest or shortest.

**The metric is an elicited quantity, not a flip.** "Did the recommendation flip" punishes conditional answers — *"if your runway is under three months, do A; otherwise B"* never flips across the triplet and is the best available advice. That exact behaviour was praised in writing on probe-07 as *"better than my answer key"*, and then a metric was nearly shipped that scores it zero. So the response contract requires a **number** where the domain admits one — months of runway before the decision changes, a threshold amount, a date, a notice period — with the expected direction and magnitude band pre-registered.

**The authoring gate:** *could a licensed professional state in one sentence why the generic answer is wrong here, citing only the governing fact?* If not, the item is a preference survey and is cut. Governing facts are constrained to the quasi-objective — a visa condition, a notice period, a medical contraindication, a hard liquidity constraint — so the key is a fact rather than anyone's taste.

**No real personal data.** Every persona is invented; the datasheet says so, and the corpus carries no name, address, account number or identifier traceable to a person.

- [ ] **Step 1: Author both triplets**
- [ ] **Step 2: Assert the single-span diff mechanically**

```bash
python -m uv run python scripts/pad.py --check-triplet probe-13 probe-14
```

- [ ] **Step 3: Commit**

```bash
git add datasets/probe/probe-13-*.yaml datasets/probe/probe-14-*.yaml && git commit -m "probe: two life triplets with a governing and a matched arm"
```

---

### Task 14: Write the prediction, then run the gate

**Files:**
- Create: `notebook/2026-08-12-long-gate-prediction.md` **before any call**
- Appends to: `results/probe/long-gate.jsonl`

**~$8.** Four existing cores (probe-07 look-back revival, probe-09 cure notice, probe-11 write-off cross-default, probe-12 partial payment) plus two life triplets, at 2k / 40k / 100k, control arm, one repeat, plus one positive control per core per length.

- [ ] **Step 1: Write the prediction first**

It must contain a **numeric guess for admissibility at each length**, and for the positive-control pass rate at each length. My last five predictions were wrong in the same direction, and the chars-per-token estimate was wrong by 58% in the direction that flattered the experiment. The record needs to keep saying so, which it can only do if the number goes in before the run.

- [ ] **Step 2: Commit the prediction before running**

```bash
git add notebook/2026-08-12-long-gate-prediction.md && git commit -m "notebook: what I expect the long gate to show, before it shows it"
```

- [ ] **Step 3: Run**

```bash
python -m uv run python scripts/probe_casefile.py --long --lengths 2000 40000 100000 --model haiku
```

- [ ] **Step 4: Score the positive controls first**

One fact stated once, explicitly, at a known depth, requiring no inference. **Fail the positive control at 100k and the result is retrieval**, which is already documented and not ours. **Pass it and fail the real items and the result is reasoning-under-load**, which is novel. Without this split every long-context failure is uninterpretable, so it is read before anything else.

- [ ] **Step 5: Blind-adjudicate every failure**

Not optional, and the reason the whole plan exists in this shape. Every scored failure is re-read by a party blind to the key. If the model's answer is defensible on the corpus's own documents, it counts as correct and the key is amended. **Every amendment is logged.**

**Pre-registered: >20% post-hoc key amendment retires the corpus and the run is not reported as a result.** Given 21 of 21 scored failures so far having been the key, this is the falsifier most likely to fire.

---

### Task 15: The go/no-go

**Files:**
- Create: `notebook/2026-08-12-long-gate-scored.md`

- [ ] **Step 1: Apply the pre-registered band**

| Control admissibility at 100k | Decision |
|---|---|
| ≥ 0.90 | **Stop.** Nothing to explain. Volume is not the dial either, and the remaining hypothesis is that the failure needs the model's *own* prior outputs in context — genuine multi-turn accumulation, not rendered accumulation. That is a different harness and gets its own decision rather than being assumed. |
| ≤ 0.15 | **Shorten.** The venue is a reading-stamina test, not a decision test. Re-anchor the top length and re-run this gate. |
| **[0.25, 0.70]** | **Go.** Milestones D–G are authorised. |
| (0.15, 0.25) or (0.70, 0.90) | Marginal. Report the number, re-anchor lengths once, and re-run the gate exactly once. Not twice — that is p-hacking with extra steps. |

- [ ] **Step 2: Write the entry**

It records: the prediction versus the outcome (including how wrong, and in which direction); the positive-control split; the key amendment rate against the 20% threshold; the separability and core-detection AUCs; and the decision, in one sentence, with the band quoted.

- [ ] **Step 3: Commit**

```bash
git add notebook/2026-08-12-long-gate-scored.md results/probe/long-gate.jsonl && git commit -m "notebook: the long gate, and what it licenses"
```

---

# After the gate — the rest of the programme

Scoped, not planned. Each becomes its own plan document when Milestone C authorises it, because writing them now would be writing tasks against numbers that do not exist yet.

### Milestone D — `casefile` as a first-class item kind
→ `docs/superpowers/plans/YYYY-MM-DD-casefile-item-kind.md`

Nothing in `decision_evals` is polymorphic over item kind, so the change surface is larger than it looks:

| File | What has to change |
|---|---|
| `generators/schema.py:140` | `Template` is one flat model with `extra="forbid"`; needs a `kind` discriminator. `_check_collisions` (`:228`) hard-requires a colliding distractor and must not apply to casefiles |
| `generators/loader.py:37,58` | validates unconditionally, globs `datasets/templates/*.yaml` only |
| `generators/generate.py:64,354` | `Item.answer: str`; `_compute_answer` raises on non-str. A casefile's ground truth is a set of actions plus a cascade closure |
| `solvers/arms.py:43,52,119` | `BASE_FRAMING`, `FORMAT_CONTRACT` and `render_item` all assume facts-plus-options. `scripts/probe_casefile.py:53-138` already prototypes all four framing variants |
| `scorers/answer.py:82` | `Score` holds one bool; `ZeroCause` becomes per-component |
| `runner.py:41` | `RunRecord` gains stratum columns and a schema version — which Task 3 has already made safe to add |
| `datasets/golden/`, `tests/golden/test_generator_golden.py:69` | asserts a template↔golden bijection; casefile goldens are added and **`rel-*` goldens must not move** |

Cascade guards carry over unchanged: **the trap must bite** (an item labelled `trap_order: 2` must contain an action admissible at first order and inadmissible under the closure) and **the cascade must terminate** (cycle detection, hard depth cap, failing at load rather than hanging).

### Milestone E — statistics
→ `docs/superpowers/plans/YYYY-MM-DD-dose-response-statistics.md`

`stats/` is already kind-agnostic — it consumes arrays plus a cluster key — so this is additive:

- `stats/dose.py`: per core, the admissibility proportion at each length × arm, the slope on `log2(length)` per core per arm, then a **paired Wilcoxon signed-rank on the 30 values of `(slope_on − slope_off)`**. Exact, nonparametric, clustering handled by construction, and the test statistic *is* the hypothesis. Not a GLMM: with 30 clusters a random-slope model returns singular fits and cluster-robust SEs are anti-conservative below ~40 clusters.
- `stats/concordance.py`: pairwise concordance over a partial action order, ignoring incomparable pairs.
- Wire `stats/calibration.py` into the exposure dimension. It is property-tested at 100% coverage and **has never been called by anything**.
- `prereg.py` gains a declared `secondary_metrics` list.
- Secondary check: **wild cluster bootstrap with Rademacher weights**, exhaustively enumerable below ~20 clusters and estimated above.

Both new modules at the 100% line+branch floor with hypothesis property tests, matching `paired.py`.

### Milestone F — the corpus
→ `docs/superpowers/plans/YYYY-MM-DD-thirty-core-corpus.md`

**Thirty cores, ten per domain**, with the ten life cores built as triplets, plus one positive control per core per length. The count is not a guess: `stats/power.py:82` `required_pairs` runs against the Milestone C numbers before authoring starts, and the corpus size is whatever it returns for a 20pp MDE.

**Why 30 cores and only 2 lengths.** Cores buy power; length levels do not. MDE scales as 1/√cores and is flat in the number of length levels, and repeats are nearly worthless — for any ICC > 0 the between-item variance dominates the within-item sampling variance, so **24 cores × 1 repeat strictly dominates 12 cores × 2 repeats** at identical cost. At 12 cores the MDE on a paired binary outcome is roughly **30–50pp**, at or above the whole 14–40pp range the literature reports. A null would have been uninformative *by construction* and any "significant" result winner's-cursed: at 12 pairs an exact McNemar needs 6 discordant pairs all in one direction for p ≤ 0.05 — the skill would have to fix half of everything the control fails, with zero backfires.

So: 30 cores, 2 anchors (2k and 100k), 1 repeat. Same run count, MDE ≈ 21pp. Intermediate lengths run on a 10-core subset as a **descriptive** curve only, captioned as underpowered.

**Volume is collinear with position, span and needle density**, and the first draft could not have attributed the curve to any of them. Two responses, both needed: hold proportional depth constant at 30–60% and state plainly that the manipulation is absolute token count at fixed relative position; and run a **position control at 40k only** — core-front, core-interleaved, core-back, total tokens fixed, ~24 runs. If the front-to-back gap at fixed 40k is comparable to the 2k-to-100k gap, the headline curve is a position curve wearing a length label, and the write-up says so.

Gates, all on the `off` arm only: detectability and separability (as in Milestone C, at full scale); **clean-room per core** ≥ 0.95 at 2k — pooling is what let `rel-009` hide at 0.50 behind nine templates at 1.00; difficulty in [0.25, 0.70] at 100k; the extended two-auditor filter; and a **10% human realism audit**, currently at 0% and mattering far more here — a hundred thousand tokens of unconvincing correspondence is a worse artefact than three hundred tokens of it.

The four difficulty mechanisms, each carried by a named part of the file and each independently scoreable:

| Mechanism | How it is built | Metric |
|---|---|---|
| **Supersession** | A value stated early is explicitly revised later; ground truth computes from the revised value | stale-value rate |
| **Distributed conjunction** | The governing rule needs facts from four documents separated by tens of thousands of tokens | per-conjunct recall |
| **Near-miss authority** | A repealed version of the section, a bulletin on an adjacent subsection, a handbook for a different scheme | near-miss citation rate |
| **Conflicting authority** | Two rules appear to point different ways, with an **express priority clause 60k tokens away** from both | tie-breaker recall |

Conflicting authority was originally specified as *genuinely* unresolvable, which is unscoreable: if no resolution is correct, "took the required action" is undefined — and worse, a competent model invoking *lex specialis* would be **defensibly right against the key**. That is probe-09 again at fifty times the adjudication cost. Burying an express tie-breaker makes ground truth clean. Before authoring at scale, three blind instances resolve each conflict cold; non-convergence, or convergence on a resolution nobody wrote, retires the item. A small residual stratum keeps the unresolvable form, scored **only** on "named the conflict and did not silently pick a side", and it does not enter admissibility.

### Milestone G — skills and the confirmation run
→ `docs/superpowers/plans/YYYY-MM-DD-skill-confirmation-run.md`

`evidence-ledger` is measured **as written, unchanged**, so the venue and the skill are not tuned against each other. Its `description` already names this venue — *"a long thread, pasted logs, search results, several documents, a channel backlog"* — so the skill was authored for a corpus that did not exist yet, and the last three corpora were all below its own `Abort if` threshold.

One confound to design out rather than measure: the skill emits its own `LEDGER / SET ASIDE / THEREFORE` block, which collides with the venue's five-block contract. The `on` arm would receive two format instructions and could break a block for reasons unrelated to decision quality. The contract must place the skill's own output as working that *precedes* the five blocks, and per-arm parse rates stay a hard guard either way.

**`consequence-cascade`** is new and carries `verdict: UNTESTED`, so the promotion gate keeps it out of `plugin/skills/`.

The discriminant table **is** the experiment:

| | `evidence-ledger` predicts | `consequence-cascade` predicts |
|---|---|---|
| unjustified-action rate | down | unchanged |
| second-order trap rate | unchanged | down |
| tailoring / generic rate | down | unchanged |
| stale-value rate | down | unchanged |

If both skills move everything, neither is doing what it says and the venue is measuring "any structured prompt helps."

**Grid:**

| Tier | Role | Grid | Calls |
|---|---|---|---|
| Haiku 4.5 | screen | 30 cores × 2 lengths × 4 arms × 1 repeat | 240 |
| Haiku 4.5 | descriptive curve | 10 cores × 2 extra lengths × 4 arms | 80 |
| Haiku 4.5 | position control | 30 cores × 3 placements at 40k, control arm | 90 |
| Sonnet | confirm | same 30 × 2 × 4 | 240 |
| Opus | appendix | 30 cores × 2 lengths × `off`/`on` | 120 |

**The model-tier gate is on control-arm degradation, not on a skill effect.** Haiku is the right screen for whether degradation exists — the weakest model degrades first — but the wrong screen for whether a skill helps, since a skill that needs capacity to exploit may show nothing on Haiku and something on Sonnet. Gating Sonnet on a Haiku skill effect would gate out the condition where the effect lives.

**Primary test:** the `arm × log2(length)` interaction on graded admissibility, Haiku, pooled across domains and mechanisms. One number, one direction, one rejection region. **At most five secondaries**, Holm-corrected: on-vs-placebo interaction; on-vs-cot interaction; on-vs-off at 100k alone; the tailoring discrimination index; and the no-harm check at 2k with a 5pp non-inferiority margin. **Everything else is exploratory**, reported with effect sizes and intervals and *no p-values* — the naive comparison count across lengths × arms × mechanisms × domains × models runs into the hundreds, and at this cluster count any single significant cell is noise.

---

## Falsifiers, written down now

Recorded before the run so a null is a result rather than a fourth dead corpus. These are the **hypothesis** falsifiers; the **instrument** falsifiers are the Milestone C gate table, and the difference is the discipline this project has been missing.

1. **Admissibility flat across 2k → 100k.** Volume is not the dial either. The remaining hypothesis is that the failure needs the model's own prior outputs in context — a different harness, which gets its own decision.
2. **Parallel curves — off degrades, on degrades identically.** Skills do not buy robustness to volume. This is a *more* informative negative than "no degradation exists" and gets reported as such rather than as a disappointment.
3. **Placebo ≈ on.** The effect is instruction bulk, not instruction content. Pre-registered kill.
4. **CoT ≈ on.** The skill is a verbose chain-of-thought prompt in a markdown file. Pre-registered kill.
5. **Life triplets show no discrimination at any length** — `d ≈ 0`, flipping equally on governing and non-governing perturbations. Tailoring is then not a failure mode of this model, and the metric moves to the appendix, not the abstract.
6. **Key amendment rate > 20%.** The corpus is retired and the run is not reported. Given 21 of 21, this is the falsifier most likely to fire.
7. **Parse rates diverge by arm.** The run is void. A skill that wins on admissibility while breaking a block has not won.
8. **No-harm at 2k.** A skill that helps at 100k and costs more than 5pp at 2k is not a win.

**The primary is a rejection region, not a p-value:** if the 95% interval on the `arm × log2(length)` interaction excludes a benefit of **+10pp per 4× length**, the "skills buy robustness to volume" claim is dead in this venue. Written down before the number is computed.

---

## Risks taken on knowingly

1. **The library is authored by one model in one session.** Already a documented limitation; a 750-document library worsens it. The 10% human realism audit is the only real mitigation and it must actually happen.
2. **A declared cascade is not a real one.** Ground truth is internally consistent and computable, but its *realism* is authored. A good score means the model reasons forward correctly over a stated causal structure, not that it knows tax law. The datasheet says that in those words.
3. **Fictional authority costs ecological validity.** Deliberate: a real statute paraphrased slightly wrong means a model that knows the real rule answers correctly-in-the-world and scores wrong, which is indistinguishable in the traces from the failure being hunted.
4. **Life decisions have no authority at all**, which is why their ground truth is relational rather than propositional. If the triplet design does not hold up under audit, the life stratum is descriptive only and cannot carry a verdict.
5. **Not a lawyer, an accountant, or a financial adviser.** Every rule is stated in-item; the corpus is labelled rule-application and context-tailoring scenarios, not a professional-judgement benchmark.

---

## The budget, and why it is not dollars

Every model call goes through the Claude Code CLI on a **Claude Max subscription**. There is no API key and none should be added. `total_cost_usd` is a **notional API-equivalent price** — nothing is billed per call, and every dollar figure in this plan is a unit of account.

So: **do not design around dollars.** Do not drop a model tier, trim a stratum, or cut repeats to save money. There is no money to save.

**The budget is real, it is just denominated differently.** The binding constraints are the subscription's rolling usage quota and wall-clock time. A 101k-token call takes about 8 seconds, so the confirmatory grid is on the order of 800 long calls — hours of serial running spread across days and quota windows. That is why the runner is checkpointed and resumable, and why the `--model` tiers exist: to stay inside a quota, not inside a price.

`BudgetLedger` stays, reinterpreted. Reported cost scales with tokens, so it is the best available **burn meter** for quota consumption. It is not a spend cap and must not be described as one. Task 1 makes it track length so the meter reads correctly at 100k.

---

## Verification

Run at the end of every milestone:

```bash
python -m uv run de check
```

- `python -m uv run pytest tests/golden` — **`rel-*` goldens must not move.** Any diff means a change leaked into the old path.
- **Harness gate:** `python scripts/canary_long.py --model haiku --tokens 2000 40000 100000 160000` — re-run whenever the CLI version moves. A harness result from August is not a harness result in December.
- **Isolation canary at length:** plant a `CLAUDE.md` in the runner cwd and assert it is not followed. Casefiles this long make a leaked instruction easy to miss by eye. `--setting-sources ""` is the only flag that blocks project-memory injection — measured, and recorded in `notebook/2026-08-10-isolation-canary.md`.
- **Ablation:** removing every padding document leaves ground truth unchanged, per assembled file.
- `python scripts/calibrate.py --kind casefile` — clean-room and difficulty gates.
- Commits must be attributed to the GitHub noreply address; `de check` refuses otherwise.

## What carries over unchanged

Arenas, pre-registration hash locks, verdict vocabulary, the plugin promotion gate (a skill may not enter the shipped plugin while carrying `UNTESTED`), mirrors, the git-identity check, the four-arm design, and the whole `de check` pipeline. The single-turn `rel-*` corpus is retained as the clean-room stratum and the no-harm guard — a casefile cannot be clean by construction.
