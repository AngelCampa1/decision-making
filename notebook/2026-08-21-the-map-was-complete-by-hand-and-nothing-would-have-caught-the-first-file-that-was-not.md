# The map was complete by hand, and nothing would have caught the first file that was not

**2026-08-21.** The documentation here had a real index and no gate on it. This
entry records what the widened gate found on its first run, what moved, and what
the new checks still cannot see.

## What was there

32,598 lines of markdown across 204 files. `docs/README.md` listed every
document under `docs/` and doubled as the site's `/docs/` page.
`docs/VOICE.md`, written the day before, defined four audiences and said a
document serving two serves neither. `docs.py` refused a `de` command or a path
that did not resolve.

Three holes.

`SCANNED` was `("*.md", "docs/*.md")`, one level deep, from 2026-08-13. So
`docs/reviews/` and `docs/superpowers/` were rendered by the site and linked
from the index, and read by no gate. Eight days.

The index was complete because somebody had kept it that way.

The audience line was a convention.

## What the widened gate found

`SCANNED` became `("*.md", "docs/**/*.md")`. The scan went from 23 living
documents to 38 and reported 23 unresolvable references, every one of them in
`docs/superpowers/plans/2026-08-11-long-context-experiment.md`: four plans it
proposed and never wrote, `scripts/detect_core.py`, a
`skills/evidence-ledger/` since deleted, two notebook entries, two gitignored
probe checkpoints, `datasets/library/employment/`, and nine line-range
references like `runner.py:211-221` that moved the next time those files were
touched.

All of that is correct history. `docs/superpowers/plans/` went into a new
`EXCLUDED_PREFIXES` as a class, not as the file that failed. The other plan in
that directory is clean and is now ungated too, which is the price of a rule
somebody can write to.

Then two new checks:

- `check_docs_index` compares `docs/README.md` against `docs/` in both
  directions, requires every subdirectory to be named, and requires every living
  document under one to be linked from somewhere. It found
  `docs/superpowers/drafts/s9-ledger-replacement/README.md`: 315 lines
  describing a candidate replacement for `ledger`, reachable only by listing the
  directory.
- `check_audience_lines` refuses a living document that declares no audience. It
  found `docs/STATUS.md`, which is linked from `AGENTS.md`, `README.md`,
  `CONTRIBUTING.md` and six documents under `docs/`.

Both are the two-directional comparison `check_component_table` already made for
the README's map of the repository, one level down.

The same run refused two `de` commands and a deleted path in the prose of the
two documents written to announce the gate: `de command` and `de surface`, both
from mermaid node labels, and `skills/evidence-ledger/` from the paragraph
explaining why plans are excluded. That is the argument for the gate rather than
the convention, made against its own author within the hour.

## What moved

`docs/RESEARCH_PROGRAMME.md` was 2,550 lines and 66 commits, the most-edited
file in this history. It is now a 466-line map and eight part files under
`docs/programme/`. The split went by exact line boundaries and rewrapped
nothing, because `citations.py` binds a claim number to its `paper/refs.bib`
quote by markdown **block**.

Five programme-wide sections at the end (`## Cross-cutting rules` through
`## The claim ladder`) had been nested under `# Part 8` by heading level while
applying to every part. They are back at the top level.

Two documents are new. `docs/ARCHITECTURE.md` describes the system and how a run
flows through it, in six diagrams; nothing had covered that.
`docs/DOCUMENTATION_MAP.md` describes the documentation itself: the four
audiences, the three classes, and where a new document goes.

The diagrams are ```` ```mermaid ```` fences, which github.com renders for free.
The site gained `site/src/lib/remark-mermaid.mjs` and a client island that
imports mermaid only when a diagram is on the page. Before the script arrives,
and for anyone it never reaches, the figure holds the diagram source as text.

## Two defects found while writing it

An adversarial fact-check re-derived every claim in both documents from source
and returned eighteen. Most were mine to fix. Two were not.

**`site.py` said something false about its own design.** The comment on
`INPUTS_PATH` read "Read by this module *and* by `site/src/content.config.ts`,
so the two cannot drift." `content.config.ts` imports nothing from
`inputs.json`; it hardcodes its globs and carries a comment asking the next
author to keep them in step. They had already drifted in two entries:
`inputs.json` globs `*.md` where `content.config.ts` names four root documents
explicitly, and `inputs.json` lists `plugin/skills/README.md` where
`content.config.ts` has no collection at all. The comment is corrected. The
drift is not, and it is the kind a gate could catch.

**One diagram rendered as an error graphic and nobody would have seen it.** A
node named `call` collides with mermaid's flowchart grammar. The parse error
threw out of `mermaid.run()` over the whole batch, which also killed the
theme-change observer, so five working diagrams stopped re-rendering on a theme
switch because of one bad id. Rendering is now per-diagram inside a `try`. The
gate hashes the page and cannot read it, so this was caught by opening the page
in a browser and asking each figure for its `aria-roledescription`.

## What these checks still cannot see

The standing limitation `docs.py` already registers, unchanged: a reference can
resolve while the sentence around it is false. `check_docs_index` proves the map
lists what exists and proves nothing about whether a row still describes its
document. `check_audience_lines` tests for the marker and not for whether the
document is written to the audience it names, which `docs/ARCHITECTURE.md`
demonstrated by declaring two audiences and passing.

The drift sweep in `AGENTS.md` is still the only thing that reads.
