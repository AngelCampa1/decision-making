# Agent instructions

This file is read by Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
and others. Claude Code reads `CLAUDE.md`; the two carry the same content here.

**It is also the product.** Skill *availability* is the dominant term in whether
a skill helps at all — SkillsBench measures +18 to +36pp from having the right
skill present, against +0.7pp from polishing its prose, with intervals crossing
zero. So the block below is not documentation about the skills. It is the part
that makes them fire, and it is meant to be copied into your own project.

---

## Copy this into your project's `AGENTS.md` or `CLAUDE.md`

```markdown
## Decision skills

Reach for these when the shape of the problem matches. They are cheap to enter
and cheap to leave — each one opens with the conditions under which it should
skip itself, so invoking one on a case it does not fit costs a few tokens rather
than a detour.

- **evidence-ledger** — when a decision depends on a pile of accumulated context
  (a long thread, pasted logs, search results, a channel backlog) and what the
  answer turns on has to be separated from what merely arrived. Skip it for a
  short prompt with one or two facts, or a lookup with one obvious source.

Trust your own read on when these apply. They are procedures, not policies:
if one of them is producing worse answers than working directly, that is worth
knowing and worth saying.
```

The wording is deliberate. Trust-framed system prompts surfaced 59% more hidden
issues than unframed ones in a controlled comparison (arXiv:2603.14373), while
fear-framing — threats, consequences, "you MUST" — showed no gain over saying
nothing. So nothing here threatens the model, and the closing line invites it to
report that a skill is not working.

---

## Installing the skills

The canonical skills use only the six portable frontmatter fields defined by the
[Agent Skills standard](https://agentskills.io), so they need no conversion.

```bash
# Cross-tool: Codex, Cursor, Copilot, Gemini CLI, Cline, Amp, OpenCode
cp -r .agents/skills/evidence-ledger ~/.agents/skills/

# Claude Code, project-scoped
cp -r skills/evidence-ledger .claude/skills/
```

Vendor-only frontmatter (`context: fork`, `disable-model-invocation`) is a hard
error in most of those tools, so it never appears in the canonical source. Any
Claude-specific keys live in the plugin overlay.

---

## What is actually proven

**Nothing yet.** `evidence-ledger` currently carries `verdict: UNTESTED` and
ships as `experimental`. See [`SCORECARD.md`](SCORECARD.md) for the verdict
vocabulary and what each one licenses you to claim.

That is not false modesty and it is not a reason to avoid the skill — use it if
it helps you. It is the difference between "we have not shown this works" and
"this works", and the whole point of the repository is to keep those two
statements apart. A skill may not enter the shipped plugin while carrying
`UNTESTED`; `de check` enforces that rather than trusting anyone to remember it.

---

## Working in this repository

If you are an agent contributing here rather than a user installing the skills:

- `python -m uv run de check` is the full local gate — lint, types, tests,
  coverage floors, skill validation. There is no cloud CI. Run it before you
  believe anything works.
- Commits must be attributed to the GitHub noreply address; `de check` refuses
  otherwise.
- Golden files pin the generated corpus byte-exact. Regenerating them needs
  `pytest --bless` and the diff belongs in review — a benchmark that changes
  silently makes every earlier number incomparable with every later one.
- `notebook/` is append-only and dated. Predictions go in *before* runs. If a
  prediction turns out wrong, the entry says so rather than being edited.
