# 2026-08-10 — Choosing a model backend, and the `--bare` dead end

## Constraint

No API keys. The harness has to drive Claude Code itself, billed against a
subscription rather than per-token. This was a hard requirement, not a
preference, and it shaped more of the architecture than expected.

## What I wanted

A way to send an item to a model with the skill text as a system prompt, get a
structured answer back, and record cost and token usage — with none of Claude
Code's own scaffolding (tool instructions, environment info, other installed
skills, project `CLAUDE.md`) leaking into the measurement. Any of those would be
an uncontrolled confound sitting between the skill and the outcome.

## Dead end: `--bare`

`--bare` looked like exactly the right flag. Its help text promises to skip
hooks, LSP, plugin sync, auto-memory, and `CLAUDE.md` auto-discovery — the whole
confound list in one switch.

It is unusable here. The same help text states:

> Anthropic auth is strictly `ANTHROPIC_API_KEY` or `apiKeyHelper` via
> `--settings` (OAuth and keychain are never read).

So `--bare` requires the very thing we don't have. The isolation flag and the
auth mode are mutually exclusive.

Recording this because it is a genuinely non-obvious interaction and I would
otherwise have tried it again in a month.

## What we use instead

Isolation assembled from individual flags, all of which work under OAuth:

```bash
claude -p "<rendered item>" \
  --system-prompt "<arm-specific system prompt>" \
  --tools "" \
  --disable-slash-commands \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --setting-sources "" \
  --no-session-persistence \
  --model sonnet \
  --json-schema '<answer schema>' \
  --output-format json
```

- `--system-prompt` **replaces** the default system prompt rather than appending
  to it. This is the main lever: it removes the harness scaffolding wholesale.
- `--tools ""` removes tool definitions, which otherwise change behaviour even
  when no tool is called.
- `--disable-slash-commands` stops other installed skills from firing. Without
  it, the machine's existing plugin set is part of the experiment.
- `--setting-sources ""` ignores user/project/local settings.
- `--json-schema` enforces the answer contract, which should remove most parse
  failures as a source of noise.
- `--output-format json` returns `total_cost_usd`, `usage`, and the resolved
  model id, so run records stay complete even though nothing is being billed
  per-token.

## Two guards, because "should be isolated" is not "is isolated"

1. The runner's working directory is a scratch path **outside `D:\code`**, since
   `CLAUDE.md` discovery walks up the tree and `D:\code\CLAUDE.md` exists.
2. A canary test: plant a `CLAUDE.md` containing a distinctive instruction in the
   runner's cwd and assert the model does not follow it. If isolation silently
   breaks in a future CLI version, this fails loudly instead of quietly
   contaminating a run.

## Consequences to state in the paper

- **No temperature control.** `claude -p` exposes none. Runs use the default, and
  we report run-to-run variance across repeats rather than claiming determinism.
  This is less of a loss than it appears: temperature 0 is not deterministic on a
  hosted API anyway, because of batching, load balancing, and MoE routing.
- **The budget is rate limits, not dollars.** The runner must be checkpointed and
  resumable so a confirmation run can span days.
- **`--system-prompt` measures a clean injection**, which is not identical to how
  a skill loads in a live session (appended to an existing large system prompt).
  A secondary in-situ arm using `--append-system-prompt` tests whether that
  difference matters. If the two disagree, that is a finding worth reporting on
  its own.

## Open question

Whether to hand-roll an Inspect AI `ModelAPI` provider around this, or use
`inspect_swe`'s `claude_code()` solver, which already runs the real CLI as an
Inspect agent and exposes `skills=[...]` and `system_prompt` as parameters —
i.e. our independent variable is already a config field. Spiking that next,
timeboxed to a day. **Prediction: it works, but the sandbox requirement makes it
awkward for a subscription-auth setup, and I end up with the custom provider
anyway.** Writing that down now so the answer can't be retrofitted.
