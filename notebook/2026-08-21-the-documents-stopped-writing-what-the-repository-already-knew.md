# The documents stopped writing what the repository already knew

**2026-08-21.** The documentation gate proved a reference resolves. It could not
prove a sentence is true, and its own module docstring said so. This entry
records what had drifted underneath that, what is now derived, what is now
pinned to one source, and what the new checks still cannot see.

## What had drifted

Four sets, each of which a machine could have compared, and every path in every
sentence resolved.

**The arms.** `docs/PROTOCOL.md` §1, `docs/METHODS.md` and `README.md` said the
harness has four arms. `solvers/arms.py` has five. `docs/programme/part-3-the-instrument.md`
said "the other five arms" in one line and pointed at `ARM_NAMES, line 40` in
another.

**The broken-measurement count**, restated in `docs/STATUS.md`,
`docs/METHODS.md` and `docs/RESEARCH_PROGRAMME.md`. `site/claims.json` already
carried the record of these three disagreeing once: ten, around eleven, eight.

**The site's globs**, written out in `site/inputs.json`,
`site/src/content.config.ts` and `RENDERED` in
`site/src/lib/remark-rewrite-links.mjs`, kept in step by a comment asking the
next person to remember. Two of the three had already moved.

**The architecture document**, whose hand-typed lists last session's fact-check
found dropping two `stats/` modules, calling five arms four, omitting three of
sixteen gate steps, and stating the plugin promotion condition wrongly.

## What is now derived

`de sync` fills five regions marked by HTML comments, invisible on github.com
and in the Astro render: the `de` subcommands and their first docstring lines,
the gate's steps with their `--fast` flag, the harness modules, the files the
skill ships, and the arms with what each answers. Four sit in
`docs/ARCHITECTURE.md`, one in `docs/METHODS.md`.

Each renders from the live object itself, never from parsed source text. The
gate's step list was a straight-line sequence of calls; it is now `gate_steps()`, a table
with two readers, so `check` and the document cannot disagree about what runs
or in what order. Adding a subcommand without the table growing a row is a
failing build.

## What is now pinned

`site/claims.json` bound a number published on a site page to one exact sentence
in one repository file. It now scans markdown too. Seven inline markers across
`docs/LIMITATIONS.md`, `docs/METHODS.md` and `docs/RESEARCH_PROGRAMME.md` state
four registered figures, and each is rewritten from the register by `de sync`.
A figure in prose is therefore pinned to its source transitively, and moves when
the source moves.

Three refusals were demonstrated by breaking them before being believed: a
marker naming a claim nothing declares, a claim nothing publishes, and a marker
placed inside the claim's own source, where `de sync` would have rewritten the
sentence the anchor exists to verify.

Retractions are deliberately not scanned across documents. `docs/STATUS.md`
legitimately contains a retracted phrase inside its own correction, and a check
that could not tell those apart would demand the correction be deleted.

## What `de drift` can and cannot see

A document's dependencies are the repository files it names, which
`docs.py` already extracted to prove they resolve. Directories were in that set
for one day: they put `docs/README.md` thirteen commits behind and
`docs/PROTOCOL.md` eleven on other sessions' commits inside `notebook/` and
`results/`, all of it noise, so a directory is now a place rather than a
dependency.
`[tool.decision-evals.reviewed]` records the commit somebody read each document
at, 36 entries, baselined at each document's last-touched commit on the
reasoning that whoever last edited a document had read it. `de drift` prints the
documents whose named paths have moved since, furthest behind first, with the
line to paste back. `de check` refuses one more than ten commits past its
review.

It cannot see a rubber stamp. Nothing stops anybody pasting the line back
without reading anything, and the module docstring says so.

It cannot see a paragraph that is wrong while every path it names has sat still.
`docs/PROTOCOL.md` once described, in the present indicative, a refusal that had
never run, with every path in it correct. That class of defect is unchanged by
any of this.

It cannot see a region that is correct under a sentence that contradicts it.
Rendering the gate's steps says nothing about a paragraph claiming the gate is
offline, and nothing here reads that paragraph.

## Two calls made deliberately

`docs/STATUS.md` cites `run_triggers.py:918` for a parse-rate gate whose floor
now sits at line 1220. The plan called for replacing the line number with the
function name. Left alone: that row describes what the code looked like on
2026-08-19, the line number is a snapshot like every other figure in it, and
`notebook/` and `docs/STATUS.md` are append-only because a record rewritten for
accuracy is a record destroyed. The row already names
`parse_rate_over_all_repeats()` in its own correction.

`README.md` still says a confirmation run has four arms, which is true.
`docs/PROTOCOL.md` §1 keeps its four-arm table and gains a note that the harness
names five, because `in_situ` holds the treatment fixed and changes the venue,
a question about ecological validity that belongs elsewhere. Version 1 is unchanged and no
completed run was conducted under anything else.

## Two dead ends

The first version of the region regex required a newline between the opening
marker and the closing one, so it could not match an empty region. An opener
paired with the *next* region's closer, and one `de sync` overwrote two markers
and the prose between them. Recovered from git. The body now includes its own
trailing newline, `check_sync` refuses a nested marker, and a test asserts that
an empty region is a region.

Then `docs/DOCUMENTATION_MAP.md` was given fenced examples showing the marker
syntax, and `de sync` filled them in. A document explaining a mechanism has to
be able to show it without becoming an instance of it. Fenced spans are now
excluded from every scan, and the ids in that document are deliberately not
real.

## What this cost

The gate gained two steps, one of which runs under `--fast`. A concurrent
session added a third on the same day, so the absolute count is a moving
number and this entry does not state one. Both new modules
carry 100% coverage floors. `de check` is still offline and still
deterministic, and no step writes: every generator has a step that refuses its
stale output instead, because a gate that repaired the tree while reading it
would be reporting on a tree nobody is about to commit.
