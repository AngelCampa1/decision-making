# 2026-08-11 — The harness could not have carried the experiment

Before authoring a single long casefile, four questions about the instrument.
All four had answers, three of them were wrong, and one of them would have
produced a fake result.

## 1. The prompt was on the command line

`providers/claude_code.py` passed the rendered item as an argv element:

```python
command = ["claude", "-p", prompt, prompt_flag, system_prompt, ...]
```

Fine for a 350-token item. Windows caps a whole command line near 32 KB, and the
corpus this is being pointed at runs to 100k tokens — roughly 400 KB. Every call
in the two longest strata would have failed as a `CliError` and been scored
`zero_cause="infrastructure"`.

That is the failure mode worth naming precisely: it does not look like a crash.
It looks like **an entire stratum of nulls**, which is indistinguishable in the
summary from a model that collapsed under context. I would have reported context
rot and been describing an operating-system limit.

`claude -p` reads the prompt from stdin when no prompt argument is given, so the
fix is `subprocess.run(..., input=prompt)`. No short-prompt fast path: a
conditional argv/stdin split makes the long path the rarely-exercised one and
lets the two drift, which is the harness variance this repository exists to
measure.

## 2. The token column was wrong by three orders of magnitude

The first canary run, after the stdin fix:

```
  2,000 tokens  ->   1,533 in   0.0048 usd
 40,000 tokens  ->      10 in   0.0596 usd
100,000 tokens  ->      10 in   0.1450 usd
```

Ten input tokens for a 380 KB prompt, while the cost scaled correctly. The raw
payload says why:

```json
"usage": {
  "input_tokens": 10,
  "cache_creation_input_tokens": 24285,
  "cache_read_input_tokens": 0
}
```

`usage.input_tokens` is the **uncached remainder**, not the prompt.

`docs/HARNESS_DISCLOSURE.md` commits to reporting input tokens at p90/p99. That
disclosure would have been wrong by three orders of magnitude in exactly the
stratum it exists to describe, and the error grows with prompt length — so it
would have been *correlated with the independent variable*.

The prompt is `input_tokens + cache_creation + cache_read`. The split is kept
alongside the total because it is not noise: the second repeat of an item arrives
as `cache_read` and costs less while being the identical prompt. Cheaper is not
smaller, and without the split the two repeats of one cell look like two
different items.

`contextWindow` is also reported (200,000 for Haiku 4.5) and is now recorded, so
how full the window was is a per-item covariate rather than an assumption — the
U-shape in the context-rot literature holds only below about half full.

## 3. The independent variable does exist

The question that gates everything: does a long prompt reach the model, or does
something between here and it truncate, compact, or summarise?

Three canary strings at 10%, 50% and 90% depth, asked back verbatim.

| Nominal | Achieved | Cost | Wall | Canaries |
|---|---|---|---|---|
| 2,000 | 1,533 | $0.0052 | 8.1s | 3/3 verbatim |
| 40,000 | 25,489 | $0.0298 | 6.6s | 3/3 verbatim |
| 100,000 | 63,313 | $0.0714 | 6.2s | 3/3 verbatim |
| 160,000 | **101,142** | $0.2296 | 7.8s | 3/3 verbatim |
| 350,000 | — | $0 | — | `Prompt is too long` |

**A 101,142-token prompt round-trips with every canary intact.** No truncation,
no compaction, no silent loss at any depth. The manipulation is real and the
instrument can carry it.

Past the window the CLI fails loudly and spends nothing, which is the good
outcome — but it needed its own exception. An overflowing prompt is deterministic
and is an authoring defect in the item; bucketing it as `infrastructure` hides a
reproducible mistake behind a retry loop. Hence `PromptTooLongError`.

## 4. My token estimate was wrong, in the direction that flatters

I guessed 3.8 characters per token from the usual figure for English prose. The
measured ratio was **6.01**, consistently, at both 40k and 160k — so the run
labelled "100,000 tokens" was really 63,313.

Repetitive text tokenises far better than varied text. That matters for the
corpus and not just for this script: bland filler is *cheaper per character* than
the core documents it is meant to hide, which is one more surface on which
padding and core differ. Real casefile prose will land nearer 4, and the corpus
builder has to measure its own ratio rather than borrowing this one.

It is also the fourth prediction I have got wrong in two days, and again in the
direction that made the experiment look better than it was.

## What this cost, and what it bought

Six calls and about $0.45. It found one defect that would have manufactured a
false negative, one that would have made the harness disclosure wrong in the
stratum it describes, and it confirmed that the one thing the whole next phase
rests on — that 100k tokens actually reach the model — is true.

The gate has a script now, `scripts/canary_long.py`, so it runs again whenever
the CLI version moves. A harness result from August is not a harness result in
December.
