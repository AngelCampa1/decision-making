# 2026-08-11 — Multi-turn already worked, and the falsifier would have killed it

Six model calls. An infrastructure agent claimed Track 0's hard gate was not a
gate; this entry is the independent reproduction, because a claim that unblocks
a whole part of the programme is exactly the claim to check rather than accept.

## The claim

Track 0 stated that `--no-session-persistence` blocks multi-turn, making a
harness change the prerequisite for every experiment in Parts 4–6.

**It blocks `--resume`, which is cross-process. It does not block multi-turn.**
With `--input-format stream-json`, turns go to one live subprocess's stdin and
context carries in-process.

## Reproduced, with the full isolation stack and no flag relaxed

`--setting-sources "" --tools "" --disable-slash-commands --strict-mcp-config
--mcp-config {} --no-session-persistence`, Haiku, three turns:

| Turn | `input_tokens` | `cache_creation` | `cache_read` | Response |
|---|---|---|---|---|
| 1 | 179 | 0 | 0 | "Acknowledged: MARMALADE-7" |
| 2 | 410 | 0 | 0 | "4" |
| 3 | 513 | 0 | 0 | **"MARMALADE-7"** |

Turn 3 recalled a codeword given in turn 1, with an unrelated turn in between.
Context carries. `apiKeySource` reports `none`, so this is subscription auth.

## The falsifier was wrong, and wrong in the direction that costs most

Track 0's instrument falsifier read: *"`cache_read` must climb turn over turn"*.

**`cache_read` was 0 on every turn while context demonstrably carried.** Prompt
caching is a billing optimisation, not a transcript mechanism, and short turns
never reach the cache threshold at all. Had 0.1 been run as written, it would
have reported the venue dead and sent the programme looking for a different
backend.

The correct evidence is **`input_tokens` climbing monotonically** — 179 → 410 →
513 — with a behavioural recall check alongside it. Both are now the falsifier.

This is the second time in one day that a falsifier was pointed at the wrong
quantity; the other was Track A's kill condition firing on an underpowered null.
A falsifier written without being run against a known-good case is a guess, and
guesses fail in whichever direction the author was already leaning.

## Two channels the init receipt advertises, and what they actually mean

`--output-format stream-json --verbose` emits a `system/init` event, which is a
free machine-readable isolation receipt. It reports `tools=[]` and `skills=[]`,
confirming those flags hold. It also reports two things the disclosure does not
mention:

```
agents=['claude', 'claude-code-guide', 'Explore',
        'general-purpose', 'Plan', 'statusline-setup']
memory_paths={'auto': 'C:\\Users\\Angel\\.claude\\projects\\<cwd-hash>\\memory\\'}
```

**Tested rather than assumed.** A run in a fixed working directory, asked
directly to remember something for future sessions, wrote nothing: the directory
was never created. With `--tools ""` there is no Task tool to reach the agents
and no memory tool to write the path.

So these are **latent, not active**. The precise statement is the one that
matters for planning: *both channels go live the moment `--tools` is relaxed* —
and Track F plans exactly that, to run the real Task tool as an ecological check.
At that point the auto-memory path becomes a **cross-run state channel keyed on
the working directory**, which is the shape of contamination a checkpointed
experiment is least able to detect, because run N would inherit from run N−1
while looking identical in every record.

`--bare` disables auto-memory and is **not usable here**: its own help text says
Anthropic auth becomes strictly `ANTHROPIC_API_KEY` or `apiKeyHelper`, and OAuth
and keychain are never read. It would trade an isolation channel for the
subscription itself.

The mitigation is a fresh working directory per run plus an assertion on
`memory_paths` in the init receipt, and it is cheap. Recorded now rather than
when Track F reaches it.

## What this changes

- **Track 0 is no longer a hard gate for A1 and A2.** The transport is ~80 lines
  of `Popen` plus JSONL. Track A's real prerequisite was never the harness; it is
  the MDE calculation and the item count.
- **Assert on the init receipt**, not only on the behavioural `CLAUDE.md` canary.
  A machine-readable declaration of tools, skills, agents and memory paths is
  strictly better evidence than inferring isolation from a response.
- `docs/HARNESS_DISCLOSURE.md` gains the two latent channels.

## Predictions, logged before the corpus exists

Track A1 will use the published sharded corpus from arXiv:2505.06120 rather than
an authored one, so the prediction is against their instrument:

- Degradation appears by **two shards**, not six.
- The split reproduces qualitatively: aptitude roughly flat, unreliability up
  sharply. I am not predicting their −16% / +112% magnitudes on Haiku 4.5.
- **The "~6 turns" figure in the programme was mine and has no source.** The
  paper sweeps 2→8 and reports no mean shard count. Measure it from
  `sharded_instructions_600.json` before designing anything around it.
