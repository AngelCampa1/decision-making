# Harness disclosure

Every run in this repository records its harness configuration against the
**ETCSOVG** checklist. This is not bureaucracy. In a controlled 3×3 factorial on
100 SWE-bench Verified tasks, harness variance exceeded model variance by roughly
**7.8×**, producing **six ranking reversals in nine comparisons**
(arXiv:2605.23950); Harness-Bench found a **23.8-point swing** from harness alone
across 5,194 trajectories (arXiv:2605.27922). An agent result reported without its
harness is not reproducible, and most published ones are not.

Since the independent variable here is a markdown file and the model is held
fixed, the harness is not background detail — it is the largest thing in the
room, and it has to be nailed down and written down.

## Preconditions

**A replicator must verify that the CLI can actually authenticate, because
`claude auth status` will not tell them.**

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

1. **Preflight.** Every run makes one throwaway call before item 1 and aborts on
   a 401. A confirmation run is checkpointed and resumable across days precisely
   because rate limits are the budget, which means a token can rotate *between*
   sessions of a single run.
2. **Triage.** `authentication` is an explicit subtype of the
   infrastructure-error category in the zero-score classification, so a run that
   silently loses its credential is never recorded as a few hundred model
   failures.

## The record

Every run writes `results/<skill>/<date>-<sha7>/config.json` containing the
fields below. The analysis refuses to aggregate runs whose harness fields differ,
so a mid-experiment change surfaces as an error rather than as noise.

### E — Execution

| Field | Value |
| --- | --- |
| Agent | Claude Code CLI, non-interactive (`claude -p`) |
| CLI version | Recorded per run |
| Resolved model id | Recorded per run from `--output-format json` |
| Auth | Subscription OAuth. **No API key.** `--bare` is unusable: its help states auth is strictly `ANTHROPIC_API_KEY`/`apiKeyHelper` and OAuth is never read. See *Preconditions* below — this is the harness's most fragile assumption |
| Sampling parameters | **Not exposed.** No temperature control — see [`LIMITATIONS.md`](LIMITATIONS.md) |
| Repeats | ≥2 independent runs per cell; variance reported |
| Working directory | A scratch directory **outside `D:\code`** |

### T — Tools

| Field | Value |
| --- | --- |
| Tools | `--tools ""` — none |
| Slash commands | `--disable-slash-commands` |
| MCP | `--strict-mcp-config --mcp-config '{"mcpServers":{}}'` |
| Settings sources | `--setting-sources ""` — no user, project, or enterprise settings |
| Other skills | Excluded by the empty settings sources; asserted by test |

The skill under test is the only intervention. Anything else in scope would be a
confound, and the tool budget is zero so that "the agent looked it up" can never
be an explanation for a difference between arms.

### C — Context

| Field | Value |
| --- | --- |
| System prompt | `--system-prompt` — **full replacement**, arm-specific |
| In-situ arm | `--append-system-prompt` on top of the default prompt |
| Session persistence | `--no-session-persistence` — every item is a cold start |
| `CLAUDE.md` discovery | Blocked by the scratch cwd, and **proven by a canary test** rather than assumed |
| Item rendering | Byte-exact prompt text published with results, per Biderman et al. (arXiv:2405.14782) |

**The canary test.** A `CLAUDE.md` containing a distinctive, harmless instruction
is planted in the runner's working directory, and the test asserts the model does
not follow it. Isolation that is merely configured is isolation that will
silently break; this makes it a failing test instead.

### S — Scheduling

| Field | Value |
| --- | --- |
| Concurrency | Serial within a cell; arms interleaved per item so quota drift cannot align with an arm |
| Checkpointing | Resumable across sessions — rate limits, not dollars, are the budget |
| Ordering | Item order seeded and recorded |
| Wall-clock | Recorded but **not a metric** — it is not comparable across days on a shared quota |

Interleaving matters more than it looks. A run that completes all `off` items on
Monday and all `on` items on Tuesday confounds the arm with everything that
changed in between, including the served model.

### O — Observability

| Field | Value |
| --- | --- |
| Output format | `--output-format json` — returns `total_cost_usd`, `usage`, resolved model id |
| Answer contract | `--json-schema` |
| Transcripts | Full transcripts published, not just scores |
| Token accounting | Input and output tokens per item; medians and **p90/p99** reported |

Tail percentiles are reported because the AGENTS.md impact study
(arXiv:2601.20404) found the benefit of an instruction artifact concentrates in a
small number of expensive runs rather than spreading uniformly. A mean-only report
can hide the entire effect.

### V — Verification

| Field | Value |
| --- | --- |
| Ground truth | Computed from template rules, never authored |
| Verifier | Deterministic code where the answer is objective |
| Verifier testing | Fixtures of known-correct, known-wrong, paraphrased, and boundary responses, run **before** the verifier is trusted |
| Zero-score triage | Every zero classified as agent failure / verifier defect / environment leak / infrastructure error |
| Judges | Secondary metrics only; binary verdict plus written critique; TPR and TNR reported separately |

### G — Governance

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
makes the configuration reproducible and the gaps visible — the gaps themselves
are in [`LIMITATIONS.md`](LIMITATIONS.md).
