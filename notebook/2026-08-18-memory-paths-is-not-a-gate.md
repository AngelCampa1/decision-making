# 2026-08-18 — `memory_paths` is not a gate, checked live rather than assumed

Closing the "tested but does nothing" gap the maintainer's autonomous-work-order
table recorded as Track 0.6: `InitReceipt.assert_isolated()` raises on `tools`
and on `skills` and never inspects `memory_paths`, while the class docstring
said it "gates on `tools` and the rest is recorded." Two questions, not one —
the docstring was wrong about which fields the gate covers, and it was unclear
whether `memory_paths` *should* be gated.

## What was checked before deciding

Two live calls, both through the harness's full `ISOLATION_FLAGS` stack
(`--setting-sources "" --tools "" --disable-slash-commands --strict-mcp-config
--mcp-config {} --no-session-persistence`), claude-code 2.1.159, Haiku:

1. A fresh scratch `cwd`, no `CLAUDE.md`. The `system`/`init` event declared
   `"memory_paths":{"auto":"C:\\Users\\...\\memory\\"}`.
2. The same `cwd`, with a `CLAUDE.md` planted (the isolation-canary text from
   `notebook/2026-08-10-isolation-canary.md`). The event declared the *same*
   `memory_paths` value, unchanged.

Two things follow from that pair:

**The field is a mapping, not a list, and the parser was silently dropping
it.** `parse_init_receipt` read every list-shaped field with
`isinstance(value, list)`, correct for `tools`, `skills` and `agents`, but
`memory_paths` has never been a list on this CLI version — every event from
both calls above declares `{"auto": "<path>"}`. That check returned `()`
regardless of what the CLI said, on every call this harness has ever made. The
class docstring's claim that this field is "recorded" was false in production,
independent of whether it should also be gated. Fixed in `_memory_paths()`,
which accepts a mapping (reading its values) or a list (kept as a compatibility
branch — nothing pins the shape upstream, and it was the shape the fixture
originally assumed).

**A planted `CLAUDE.md` does not change this field at all**, because
`--setting-sources ""` blocks that file from being read in the first place —
the finding `2026-08-10-isolation-canary.md` already established for the
*response*, now confirmed for the *receipt* too. So `memory_paths` carries
exactly one value, `{"auto": "<cwd-keyed-path>"}`, on every isolated call
regardless of contamination, clean or not. There is currently no known shape
of this field that distinguishes the two states.

## The decision

**(b): leave `assert_isolated()` ungated on `memory_paths`, and correct the
docstring rather than the code.** Gating on non-empty `memory_paths` would
refuse every run this repository has ever made, not the contaminated ones —
the opposite of what `tools` and `skills` do, where empty is the healthy state
and non-empty is itself the anomaly. Adding a refusal with no known
distinguishing condition would be inventing a check that cannot pass any run,
which is the shape of defect this repository's standing rules already warn
against ("before believing an outcome, check that some possible response would
have scored above zero for this arm") — turned around: before adding a
refusal, check that some real input would *not* trigger it, and here nothing
does except the field being absent, which is not the same as isolation
succeeding.

The docstring was also wrong about something narrower and unambiguous:
`assert_isolated()` gates on `tools` **and `skills`**, not just `tools`. That
part is corrected regardless of the `memory_paths` question, because it is not
a judgement call — the code already does it and the prose just did not say so.

## What changed

- `evals/src/decision_evals/providers/claude_code.py` — `InitReceipt`'s
  docstring now names both gated fields and explains, with the evidence above,
  why `memory_paths` is recorded rather than gated. `_memory_paths()` added so
  the field is actually read from a live event instead of silently reading as
  `()`.
- `tests/unit/test_conversation.py` — `_INIT_EVENT`'s `memory_paths` fixture
  moved from an invented list shape to the real mapping shape; added
  regression tests for both shapes and for the "recorded, not gated" claim.
- `docs/AUTONOMOUS_WORK_ORDER.md` — Track 0.6's row cells only.

## What this does not settle

If a future CLI version reports something under `memory_paths` that *does*
distinguish a clean call from a contaminated one — a second key appearing only
when a file was actually read, say — this decision should be revisited against
that evidence rather than left standing on today's. The mapping-vs-list parser
fix means that evidence would now actually reach `InitReceipt` instead of being
silently discarded, which it was not doing before this entry.

---

## Confirmed independently, and one flag comment turns out to be wrong — appended same day

Every claim above was re-derived from two fresh live calls rather than taken
from the report that produced it. Both ran in a scratch cwd against
claude-code 2.1.159 at the `haiku` tier.

**The parser finding holds.** `memory_paths` came back as
`{'auto': '<cwd-keyed path>'}` — a `dict` — in both calls. `strings()`
required `isinstance(value, list)`, so the field read `()` on every call this
harness has ever made, exactly as reported.

**And the pair of calls did something the repository had not done for this
gate: it ran the falsifier against a known-good case *and* a known-bad one**,
which is standing rule 2 and which nothing here had ever demonstrated for
`assert_isolated`'s `skills` branch.

| | `tools` | `skills` | `mcp_servers` |
|---|---|---|---|
| full `ISOLATION_FLAGS` stack | `[]` | `[]` | `[]` |
| same stack minus `--disable-slash-commands` and the two MCP flags | `[]` | **13 entries** | **9 pending connectors** |

So the `skills` branch is reachable and live — it fires on a real
misconfiguration, not only on a synthetic fixture.

**Which makes `ISOLATION_FLAGS`' own comment wrong.** It reads: *"`--setting-sources ""` is the load-bearing one. The others close paths that
are **not currently open** but would be a confound if a future CLI version
changed a default."* They are currently open. Drop `--disable-slash-commands`
and this CLI declares thirteen skills; drop the MCP pair and it declares nine
connectors pending. Three of those five flags are load-bearing today, and the
comment invites a future reader to treat them as belt-and-braces they could
trim. Corrected in place.

**What this does not show.** Both calls were made from this machine, whose
user configuration is what supplies those thirteen skills and nine connectors.
A different machine would show a different bad case, possibly an empty one —
which is an argument for the flags rather than against them, since the harness
cannot know what a given machine would otherwise load.
