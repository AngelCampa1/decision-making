# 2026-08-10 — Spike verdict: `inspect_swe` is the wrong shape, for a sharper reason than predicted

## The question

D1 left one thing open: use `inspect_swe`'s `claude_code()` solver, which already
runs the real Claude Code CLI as an Inspect agent with `skills=[...]`,
`system_prompt` and `replace_system_prompt` as first-class parameters — or build
a custom Inspect `ModelAPI` shelling out to `claude -p`.

The recorded prediction, from
[`2026-08-10-harness-backend-selection.md`](2026-08-10-harness-backend-selection.md):

> Prediction: it works, but the sandbox requirement makes it awkward for a
> subscription-auth setup, and I end up with the custom provider anyway.

## What the spike found

Both packages install cleanly — `inspect-ai` 0.3.255, `inspect-swe` alongside it,
85 packages, no build friction. `inspect_swe` exposes `claude_code`, `codex_cli`,
`gemini_cli`, `opencode`, `kimi_code`, `mini_swe_agent` and interactive variants.
The API surface is genuinely good, and the parameters map almost exactly onto our
experimental design: `system_prompt` and `replace_system_prompt` are separate
arguments, which is precisely our in-situ / isolated arm distinction, and
`skills=[...]` makes the independent variable a first-class parameter.

Then the docstring for `model_config`:

> Purely the displayed identity — calls are still bridged to the served Inspect
> model regardless.

And the source confirms the mechanism directly:

```
_claude_code/claude_code.py:356:  "ANTHROPIC_BASE_URL": f"http://localhost:{bridge.port}"
_mini_swe_agent/mini_swe_agent.py:168:  "ANTHROPIC_API_KEY": "sk-none"
_opencode/opencode.py:227:  "ANTHROPIC_API_KEY": "sk-none"
```

`claude_code()` points the CLI at a **local bridge** and serves generation from
Inspect's own model provider behind it. The `sk-none` sentinel in the sibling
agents makes the intent unambiguous: the key is deliberately a placeholder,
because no real Anthropic credential is ever used.

## Why that settles it

`inspect_swe` transplants Claude Code's **agent scaffold** onto **whatever model
Inspect is configured to serve**. That is a well-designed tool for a real
question — *how much of an agent's performance comes from its harness rather than
its model* — which is, not coincidentally, exactly the harness-variance question
this project cites as its central justification.

But it is the opposite decomposition from the one we need. We hold the model
fixed and vary a markdown file. `inspect_swe` holds the scaffold fixed and varies
the model. Routing through the bridge would mean supplying an Inspect-configured
model, which means an API key — and "no API keys, drive the subscription" is not
a preference here, it is the constraint the whole harness was designed around.

The sandbox requirement is real too (`sandbox` parameter, `SandboxPlatform`,
"running in a sandbox" in the first line of the docstring), but it turns out to
be the *second* reason rather than the first.

**Decision: custom Inspect `ModelAPI` shelling out to `claude -p`.**

## Prediction scoring

Called correctly, for the wrong reason. I predicted friction from the sandbox
requirement; the actual blocker is that generation never touches subscription
auth at all. Recording that distinction because "I was right" and "I was right
for the reason I gave" are different claims, and only the second one licenses
trusting the next prediction from the same reasoning.

The specific error is worth naming: I reasoned about the *deployment* awkwardness
of a tool without checking where its tokens come from. That is a
cheap check — one grep — and it inverted the argument. Generalising: for any
harness dependency, establish the credential path before evaluating the API
surface. A pleasant API over the wrong auth model is still the wrong dependency.

## What we keep from `inspect_swe`

Not a dependency, but three things worth copying:

1. **The parameter vocabulary.** `system_prompt` versus `replace_system_prompt`
   as distinct arguments is a cleaner encoding of the arm distinction than
   anything I had drafted, and the custom provider should adopt those names.
2. **The bridge pattern itself**, as a fallback. If subscription auth proves too
   unreliable to run a multi-day confirmation (see
   [`2026-08-10-subscription-auth-blocker.md`](2026-08-10-subscription-auth-blocker.md)),
   a local bridge in front of Ollama is how the dev arena runs the *same* code
   path as the confirm arena rather than a parallel one.
3. **`inspect-ai` proper stays in.** Only the `inspect_swe` agent layer is
   rejected. The eval framework, its scorers, and `mockllm` for the free
   deterministic end-to-end CI run are all still the plan.

## Status

The packaging half of the spike is complete and the decision is made. The
empirical half — running the flag stack end-to-end and proving the isolation
canary — is blocked on the credential outage recorded in the companion entry, and
is not affected by this decision either way.
