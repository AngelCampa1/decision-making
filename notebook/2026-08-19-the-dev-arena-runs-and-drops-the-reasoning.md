# 2026-08-19 — The `dev` arena runs, and its first real call showed the parser dropping three quarters of the output

`docs/PROTOCOL.md` §2 has declared a `dev` arena on Ollama since it was written,
and `arenas.py` has carried `model_prefixes=("mockllm", "ollama")` for as long.
Nothing was behind it. Now something is, and running it against real weights
found a defect the unit suite could not have.

## What ran

Ollama 0.32.14, standalone zip, models under a scratch directory rather than the
user profile. `qwen3:4b` on an RTX 5060 Laptop, 8 GB, driver 592.82, compute
capability 12.0. Seven integration tests, all passing, 122 s.

First real call:

```
card:     system=0 chars, template=1506 chars -> isolated=True
model:    ollama/qwen3:4b
tokens:   in=33 out=247
duration: 3586 ms
cost:     0.0
text:     '4'
```

## The isolation gate was right, and for a reason I guessed at

The design question was whether a non-empty `TEMPLATE` should fail
`assert_isolated` alongside a non-empty `SYSTEM`. It does not, on the argument
that a chat template is the wire format, every instruct-tuned tag has one, and a
gate that refuses every usable model is a gate somebody turns off.

`qwen3:4b`'s card is `system=0, template=1506`. So the version that gated on
templates would have refused the first model it was ever pointed at. The
argument was written before the number was known; the number agrees with it.
Worth recording because it as easily could not have.

## The defect: 247 output tokens, one character of answer

`out=247` for `text='4'` did not add up, and the raw response says why:

```
message keys: ['role', 'content', 'reasoning']
  content:   '4'
  reasoning: 'Okay, the user asked "What is 2+2? ..."'
usage: {'prompt_tokens': 33, 'completion_tokens': 277, 'total_tokens': 310}
```

`qwen3` is a reasoning model. It returns its chain in a `reasoning` field beside
`content`, and `parse_completion` was reading `content` and discarding the rest.
So `output_tokens` counted 277 tokens of which the scorer would see one, and
nothing in the record said so.

This is the third instance of one shape here, and the first two are published:
the parser whitelist that discarded every tool name an n=2 arm could offer, and
the routing report that graded names the arm never emitted. Each produced a
clean run, a full checkpoint, and a number about the wrong object. This one had
not measured anything yet, which is the only difference.

Fixed: `CliResult` gains `reasoning`, `parse_completion` reads both spellings
(`reasoning`, and `reasoning_content` which several shims use), and a live test
asserts that a large token count with a short answer must come with a recorded
chain. It fails rather than passing quietly if the chain goes somewhere the
record cannot see.

## What is not fixed, and is the more serious half

**The `cot` arm is not safely measurable against a reasoning model.**
`solvers/arms.py` distinguishes the chain-of-thought arm by *asking* for
reasoning in the prompt. A reasoning model reasons whether or not it is asked.
So on `qwen3:4b` the `cot` and `off` arms would differ in what the prompt
requested and not in what the model did.

That is the same defect as running the in-situ arm against a raw completion
endpoint, which this provider refuses for exactly this reason: two arms with one
meaning, and nothing downstream able to separate them. The difference is that
in-situ can be refused mechanically and this cannot, because whether a tag
reasons is a property of the weights rather than of the request.

Recorded in `docs/HARNESS_DISCLOSURE.md` and not resolved. Any `dev`-arena grid
involving `cot` needs either a non-reasoning tag or a pre-registered decision
about what the arm means there. Neither exists. Nothing has been measured on
this backend, so nothing is contaminated yet — this is a note written before the
run rather than after it, which is the whole point of the ordering.

A second consequence: the p90/p99 token figures `docs/HARNESS_DISCLOSURE.md`
commits to reporting will read as inflated on any reasoning model unless split
by whether a chain was emitted. Also recorded, also unresolved.

## What this does not license

Nothing. `dev` emits no verdict, `arenas.py` enforces that on the model prefix,
and no measurement has been made. What the arena buys is that a falsifier can be
run against a known-good case before it is trusted, and that an estimator can be
checked for whether any possible response would score above zero, without
spending quota on either. Those are standing rules that were expensive and are
now free.
