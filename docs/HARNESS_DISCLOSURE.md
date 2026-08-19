# Harness disclosure

Every run in this repository records its harness configuration against the
ETCSOVG checklist. This is not bureaucracy. In the controlled 3×3 factorial
that arXiv:2605.23950 runs on "a difficulty-stratified 100-task subset of
SWE-bench Verified", two runs per cell, the aggregate harness-to-model variance
ratio was 7.80×, with ranking reversals in "6 out of 9
model-pair/harness-pair comparisons" (§4.2 and Table 2; those figures are in
the paper's body, not its abstract, and `paper/refs.bib` carries the verbatim
body text in a `quote_body` field). Harness-Bench (arXiv:2605.27922) separately
runs 5,194 execution trajectories over 106 sandboxed tasks across
"representative harness configurations" and "multiple model backends", and
finds "substantial variation in completion, process quality, efficiency, and
failure behavior across model-harness pairings", which is its abstract's own
wording, and qualitative rather than a magnitude. An agent result reported
without its harness is not reproducible, and most published ones are not.

> **Correction, 2026-08-14.** This paragraph previously also gave a
> 23.8-point gap between Harness-Bench's best- and worst-scoring
> configurable harness, 76.2 against 52.4. That figure has no source sentence
> anywhere: it is not in the abstract, `paper/refs.bib`'s entry for
> arXiv:2605.27922 states it as unverified, and this repository's own
> `docs/RELATED_WORK.md` entry for the same paper already removed it rather
> than hedging it, for the same reason. It is removed here too, along with the
> 76.2/52.4 sub-figures, which never had any source at all (not even an
> "unverified" note) and were introduced by a notebook entry restating a
> different, since-corrected passage.

The 7.80× is narrower than it looks, and the narrowing is the point rather than
a footnote: it is one estimate from one 3×3 design on one task distribution.
What it supports is the direction, that harness choice can move a result by
more than model choice does, and it is not a constant to carry into another
setting. This file does not use it as one.

Since the independent variable here is a markdown file and the model is held
fixed, the harness is not background detail. It is the largest thing in the
room, and it has to be nailed down and written down.

## Preconditions

A replicator must verify that the CLI can actually authenticate, because
`claude auth status` will not tell them.

The harness's first claimed property is that it runs on a consumer subscription
with no API key. That rests on an assumption worth stating as one: that a
subscription-authed CLI invoked as a subprocess will authenticate. It can fail
while every visible indicator says otherwise. Observed on 2026-08-10:

```
$ claude auth status
{"loggedIn": true, "authMethod": "claude.ai", "subscriptionType": "max"}

$ claude -p "Say OK" --model haiku --output-format json
{"is_error": true, "api_error_status": 401,
 "result": "Failed to authenticate. API Error: 401 OAuth access token has been revoked."}
```

`loggedIn: true` is read from local state and is not validated against the
server, so it means only that a credential file exists. A token rotated by a
login elsewhere is revoked rather than expired, and no refresh recovers it. The
fix is `claude auth login`.

Two consequences are built into the runner rather than left to the operator:

1. Preflight. Every run makes one throwaway call before item 1 and aborts on
   a 401. A confirmation run is checkpointed and resumable across days precisely
   because rate limits are the budget, which means a token can rotate *between*
   sessions of a single run.
2. Triage. `authentication` is an explicit subtype of the
   infrastructure-error category in the zero-score classification, so a run that
   silently loses its credential is never recorded as a few hundred model
   failures.

## The record

Every run writes `results/<skill>/<date>-<sha7>/config.json` containing the
fields below. The analysis refuses to aggregate runs whose harness fields differ,
so a mid-experiment change surfaces as an error rather than as noise.

### E: Execution

| Field | Value |
| --- | --- |
| Agent | Claude Code CLI, non-interactive (`claude -p`). Every published number. A second backend exists from 2026-08-19, `providers/openai_compatible.py`, an OpenAI-compatible HTTP server. It is `dev`-arena only, has produced nothing published, and is disclosed separately below |
| CLI version | Recorded per run |
| Resolved model id | Recorded per run from `--output-format json` |
| Auth | Subscription OAuth. No API key. `--bare` is unusable: its help states auth is strictly `ANTHROPIC_API_KEY`/`apiKeyHelper` and OAuth is never read. See *Preconditions* below; this is the harness's most fragile assumption |
| Sampling parameters | Not exposed. No temperature control; see [`LIMITATIONS.md`](LIMITATIONS.md) |
| Repeats | ≥2 independent runs per cell; variance reported |
| Working directory | A fresh temporary directory per call, outside `D:\code`, via `providers.claude_code.isolated_cwd`. The CLI's auto-memory path is keyed on cwd, so a shared directory would let one call's state reach the next |
| Temp-directory cleanup | Errors ignored. On Windows the CLI subprocess does not reliably release its cwd before the directory is removed, and a 365-call run died at call 348 with `WinError 32`, raised by the cleanup, after every call had succeeded. Leaked directories are left for the OS to reclaim |

**The second backend, disclosed separately because it is a different harness.**
That is the whole finding of the two papers above: a result reported without its
harness is not reproducible, so folding a local server into the table above
would be the error this document exists to avoid.

| Field | Value |
| --- | --- |
| Agent | An OpenAI-compatible HTTP server. Ollama first; the same module reaches vLLM, LM Studio and `llama.cpp` |
| Arena | `dev` only, enforced in code on the `ollama` model prefix. Emits no verdict |
| Resolved model id | Recorded per call from the response's `model` field, prefixed with the server label |
| Auth | None locally. A bearer token where an endpoint wants one |
| Sampling parameters | **Exposed**, unlike the CLI, and defaulted to `temperature=0` |
| Cost | `0.0`, recorded rather than omitted. Local inference bills nothing and consumes no subscription quota |
| Working directory | Not applicable. Nothing reads the filesystem |
| Isolation receipt | The model card from Ollama's native `/api/show`, refused when it carries a `SYSTEM` prompt. A Modelfile `SYSTEM` line is the local analogue of a planted `CLAUDE.md`. Where a server offers no card, the absence of a receipt is recorded and is **not** reported as a receipt that passed |
| In-situ arm | **Refused.** There is no pre-existing system prompt to append to, so the call would be the isolated arm under another arm's label |
| Reasoning output | Returned in a field separate from the answer and **recorded**. Measured on `qwen3:4b`, 2026-08-19: 277 completion tokens for a `content` of `"4"`, the other 276 in `reasoning` |

**The `cot` arm is not safely measurable against a reasoning model, and this is
a live threat rather than a note.** `solvers/arms.py` compares a
chain-of-thought arm against the others by asking for reasoning in the prompt.
A reasoning model reasons whether or not it is asked, and emits the chain in its
own field. So on `qwen3:4b` the `cot` and `off` arms would differ in what the
prompt requested and not in what the model did, which is the same defect as
running the in-situ arm here: two arms with one meaning, and nothing downstream
able to separate them.

Two things follow. Token counts and scored text describe different objects
whenever `reasoning` is non-empty, so the p90/p99 figures this document commits
to reporting must be split by whether a chain was emitted or they will read as
inflated. And any `dev`-arena grid involving `cot` needs either a non-reasoning
tag or a pre-registered decision about what the arm means there. Neither has
been made; nothing has been measured on this backend.

### T: Tools

| Field | Value |
| --- | --- |
| Tools | `--tools ""`, none |
| Slash commands | `--disable-slash-commands` |
| MCP | `--strict-mcp-config --mcp-config '{"mcpServers":{}}'` |
| Settings sources | `--setting-sources ""`, the load-bearing isolation control. Measured: a planted `CLAUDE.md` is still injected under a full `--system-prompt` replacement, and this flag alone blocks it. See [the canary ablation](../notebook/2026-08-10-isolation-canary.md) |
| Other skills | Excluded by the empty settings sources; asserted by test |
| Isolation receipt | The CLI's `system`/`init` event, parsed and asserted per conversation. Carries the tool list, the skill list, declared agents, memory file paths, the API-key source, the resolved model and the cwd |

The skill under test is the only intervention. Anything else in scope would be a
confound, and the tool budget is zero so that "the agent looked it up" can never
be an explanation for a difference between arms.

The receipt is a stronger control than the flags, and it is new. Every row
above it describes what was *requested*. The `init` event describes what the CLI
actually loaded, and the two can differ: a flag can be renamed, deprecated, or
silently ignored by a version bump, and nothing in a passing run would show it.
`InitReceipt.assert_isolated()` raises if any tool or any skill is present.

It is asserted once per conversation rather than once per run. A receipt that
changed partway through a multi-turn item is exactly the confound the check
exists for, and a per-run assertion cannot see it.

There are two disclosed gaps in the receipt. It does *not* raise on declared
sub-agents, because Track B deliberately runs them; an arm that should have none
must check that field itself. And a receipt only reports what the CLI chose to
put in the event: absence of a field is not evidence of absence of the thing.

### C: Context

| Field | Value |
| --- | --- |
| System prompt | `--system-prompt`, a full replacement, arm-specific |
| In-situ arm | `--append-system-prompt` on top of the default prompt |
| Session persistence | `--no-session-persistence`. Every item is a cold start. It does *not* prevent multi-turn; see below |
| Multi-turn transport | `--input-format stream-json` with `--output-format stream-json --verbose`. Turns are written to one live subprocess's stdin and context carries in-process |
| Prompt delivery | stdin, always. Never an argv element: Windows caps a command line near 32 KB and a 100k-token casefile is ~400 KB, so every long call would have died as a `CliError` and been triaged as infrastructure |
| `CLAUDE.md` discovery | Blocked by the scratch cwd, and proven by a canary test rather than assumed |
| Item rendering | Byte-exact prompt text published with results, per Biderman et al. (arXiv:2405.14782) |

The canary test plants a `CLAUDE.md` containing a distinctive, harmless
instruction in the runner's working directory, and asserts the model does not
follow it. Isolation that is merely configured is isolation that will silently
break; this makes it a failing test instead.

It ships with a positive control that asserts the same instruction *is*
followed without the isolation flag. A canary that cannot fire proves nothing,
and an isolation test that quietly stopped working would be worse than none: it
would license exactly the confidence it no longer earns.

The ablation behind the table above is why `--system-prompt` is listed as an
experimental control and not as an isolation mechanism. Replacing the system
prompt governs what the model is *told*; it does not govern what the model
*discovers*.

`--no-session-persistence` does not make multi-turn impossible, and reading it
that way would have killed a whole track. It blocks the *cross-process*
channel: `--resume` cannot pick a session back up, and there is no transcript on
disk between calls. Turns delivered to a single live process over
`--input-format stream-json` are unaffected, because the accumulation happens
inside that process and never touches persistence. Verified live rather than
argued: across three turns the prompt grew 179 → 334 → 422 tokens and turn three
recalled a nonce word planted in turn one.

The distinction is worth stating precisely because the disclosure above says
"every item is a cold start" and that remains true. Items are cold starts;
turns within an item are not, and are not meant to be.

### S: Scheduling

| Field | Value |
| --- | --- |
| Concurrency | Serial within a cell, and every published number was produced that way; arms interleaved per item so quota drift cannot align with an arm. `run_arm` gained a concurrent path on 2026-08-19 and it defaults to 1 |
| Checkpointing | Resumable across sessions: rate limits, not dollars, are the budget |
| Ordering | Item order seeded and recorded |
| Wall-clock | Recorded but not a metric, since it is not comparable across days on a shared quota |

Interleaving matters more than it looks. A run that completes all `off` items on
Monday and all `on` items on Tuesday confounds the arm with everything that
changed in between, including the served model.

**Concurrency is refused on the one backend where it was measured, and that is
the disclosure.** Running 40 items three times on `ollama/qwen3:4b` at
`temperature=0` gave two serial passes agreeing on the exact text of 31 of 40
items and a concurrent pass at `concurrency=8` agreeing on 0 of 40, with the
scored answer itself moving on 6 of 39. `input_tokens` matched exactly across
all three arms, so the prompts were byte-identical and the change is the
server's: batching concurrent requests changes the reduction order, and a
reasoning chain thousands of tokens long gives one flipped token room to
propagate. `runner.CONCURRENCY_UNSAFE` refuses the combination rather than
recording it here and hoping.

The Claude CLI backend has **not** been measured this way, and unmeasured is not
safe. Any future grid that wants concurrency on it needs its own falsifier
first, against its own serial floor. Recorded in
[`notebook/2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md`](../notebook/2026-08-19-concurrency-changes-every-answer-on-a-batching-server.md).

### O: Observability

| Field | Value |
| --- | --- |
| Output format | `--output-format json`, which returns `total_cost_usd`, `usage`, resolved model id |
| Answer contract | `--json-schema` |
| Transcripts | Full transcripts published, not just scores |
| Token accounting | Input and output tokens per item; medians and p90/p99 reported. "Input" means `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`; see below |
| Cache split | The three components are kept separately as well as summed |

Tail percentiles are reported because the AGENTS.md impact study
(arXiv:2601.20404) found the benefit of an instruction artifact concentrates in a
small number of expensive runs rather than spreading uniformly. A mean-only report
can hide the entire effect.

`usage.input_tokens` is not the prompt, and this disclosure would have been
wrong by three orders of magnitude without saying so. It is the *uncached
remainder*. A 380 KB casefile reported 10 input tokens while
`cache_creation_input_tokens` carried the other 24,285 and the cost tracked the
real figure. Reporting `input_tokens` alone would have put ~10 in the token
column of every long item, and the error would have grown with prompt length,
so it would have been correlated with the independent variable in exactly the
stratum this section exists to describe.

There are two things the cache is not. It is not a transcript channel: across a
verified three-turn conversation `cache_read_input_tokens` measured 0 on
every turn while context demonstrably carried, so cache reads are not the
mechanism by which turns accumulate and their absence is not evidence that they
did not. And it is not a change in what was sampled: on a second repeat of an
item the identical prompt arrives as `cache_read`, which moves cost without
moving the observation. That is why the split is published rather than only the
sum: a cost difference between two repeats of one item is a billing artifact,
and a reader given only `total_cost_usd` could not tell.

### V: Verification

| Field | Value |
| --- | --- |
| Ground truth | Computed from template rules, never authored |
| Verifier | Deterministic code where the answer is objective |
| Verifier testing | Fixtures of known-correct, known-wrong, paraphrased, and boundary responses, run before the verifier is trusted |
| Zero-score triage | Every zero classified as agent failure / verifier defect / environment leak / infrastructure error |
| Judges | Secondary metrics only; binary verdict plus written critique; TPR and TNR reported separately |

### G: Governance

| Field | Value |
| --- | --- |
| Pre-registration | `preregistration/<skill>-v<n>.yaml`, committed before the run |
| Hash locks | `skill_sha256` and `analysis_script_sha256` both verified at run start |
| Arena | `dev` / `screen` / `confirm`; only `confirm` emits a verdict, and only `confirm` is hash-locked |
| Stopping rule | Fixed N, no interim analysis |
| Attribution | Commits attributed to Angel Campa via GitHub noreply; enforced by `de check` |

## What this does not cover

Disclosure is not control. Recording the resolved model id does not protect
against a silent server-side change within the same id; recording that sampling
parameters are unavailable does not make the runs deterministic. The checklist
makes the configuration reproducible and the gaps visible. The gaps themselves
are in [`LIMITATIONS.md`](LIMITATIONS.md).
