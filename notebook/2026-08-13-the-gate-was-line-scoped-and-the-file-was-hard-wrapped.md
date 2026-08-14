# The gate was line-scoped and the file was hard-wrapped

**2026-08-13.** No run, no prediction. This is an instrument repair and a
citation audit, recorded because both changed what the repository asserts.

---

## 1. The blind spot

`citations.py` enforced standing rule 5 by iterating `text.splitlines()` and
asking `asserts_a_number(line)` on the **same line** as the identifier. This
repository hard-wraps markdown at ~80 columns. So a claim and its citation land
on different lines whenever the paragraph happens to reflow there, and the check
never fires.

The worst case was in the file this repository calls the product:

```
CLAUDE.md:98  The wording is deliberate. Trust-framed system prompts surfaced 59% more hidden
CLAUDE.md:99  issues than unframed ones in a controlled comparison (arXiv:2603.14373), while
```

Number on 98, identifier on 99. **The gate enforcing standing rule 5 had never
checked the product file's own load-bearing citation**, and
`docs/AUTONOMOUS_WORK_ORDER.md:146-147` — the document that *states* standing
rule 5 — carried the same claim across the same wrap.

Scanned against the committed state, the widened gate catches **27 citations
across 19 distinct papers** that the line-scoped one reported as clean. The
line-scoped count on the same corpus is **0**.

## 2. The window rule, and a derivation that was wrong

The window is now the **markdown block the author wrote** — ended by a blank
line and by every structural boundary markdown defines (heading, thematic break
or setext underline, table row, list item, footnote or link definition, fenced
block), each tested after blockquote markers are stripped.

A fixed `±n` lines was rejected under standing rule 1: nobody derived it, and it
is wrong in both directions at once — it reaches across a blank line into an
unrelated paragraph and stops short inside a long one. A block boundary is
placed by the author, not by the gate.

**The first derivation of its width was wrong, and an adversarial review caught
it rather than the author.** I quoted blank-line blocks (n=3,309, mean 3.3,
median 3, p90 6) to justify a splitter that *also* splits on structure, and the
all-blocks population is dominated by thousands of one-line table rows and
headings that can never contain a citation. Re-derived over the rule as
implemented, restricted to the only population whose size can change an outcome:

| population | n | mean | median | p90 | max |
|---|---|---|---|---|---|
| all blocks | 4,785 | 2.40 | 1 | 5 | 78 |
| **blocks containing a citation** | **138** | **4.22** | **4** | **8** | **18** |

Both sets of numbers were real. Neither of the first ones described the thing
being justified, and both made the window look tighter than it is. **A
derivation of the wrong quantity satisfies standing rule 1 in form only.**

## 3. Standing rule 2, and what adversarial review found anyway

The falsifier was run against known-good cases **before** it was allowed to fail
anything: nine constructions a careful author would write where the number does
not belong to the citation (table of contents, adjacent paragraphs, heading
carrying a figure, table rows, horizontal rule, versions and years), plus four
that must fire. 9/9 passed and 4/4 fired before the sweep was run.

That was not enough. A reviewer briefed to break it found eight defects the
battery missed, two of them ship-blockers:

- `~~~` inside a ``` fence closed it, desynchronising the parser to end of file
  — and while a fence is open, blank lines stop separating anything, so every
  remaining citation pooled into one block.
- An unterminated fence did the same. The test that claimed to cover this
  asserted only that *a* block came back from a two-line input, which a splitter
  that pools everything passes trivially.
- Nothing inside a blockquote split at all, and there was a **live 21-line
  block** in this repository holding a quoted comparison table with two papers
  and two figures.
- A GFM table written without leading pipes was one block.
- `===` split differently from `---`.
- Consecutive footnote definitions ran together.
- `pp. 14-19` read as percentage points across a line join.
- A hard-wrapped line starting `202. That is ...` was read as an ordered-list
  item and silently split a real claim in half — the *same* class of defect the
  widening exists to remove, reintroduced by a rule added to prevent
  over-firing.

All eight are fixed and all eight are in the suite. The ordered-list bound is
CommonMark's own (a list may only interrupt a paragraph when it starts at 1),
not a threshold anybody picked.

**The lesson is not "write a better battery."** The battery was written in good
faith against the failure modes its author could imagine, and its author could
not imagine the ones that mattered. Every boundary rule added to stop
over-firing is also a way to wrap out of the gate's sight, and the author of a
rule is the worst-placed person to see that.

## 4. What the audit found

Six claims re-fetched first-hand. **All six confirmed by an independent agent
that re-fetched every abstract without seeing my reasoning.** Full detail in
`docs/RELATED_WORK.md` and `docs/PROTOCOL.md`, each carrying a dated correction
notice; nothing was softened into vagueness that no longer needs a citation.

| claim | verdict |
|---|---|
| `2411.15287` "63.7% across seven model families" | **unsupported** — single-author survey, no percentages in the abstract |
| `2605.20530` "14-40pp trajectory accuracy" | **v1 only**; v2 removed it and disclaims the reading |
| `2605.29800` "+0.2pp against a predicted 22pp" | **two quantities conflated**, and the direction reversed |
| `2603.26233` "SWE-bench Verified 61.2 → 69.4" | **an underspecified variant**, v1, OpenHands + Sonnet 4.5 |
| `2306.05685` "~85%, above human-human ~81%" | **not found; inequality reversed** — the abstract claims parity |
| `2605.23950` "7.8×, 3×3, six of nine reversals" | **position paper, no numerals in the abstract at all** |

The last two were not in the brief. The sixth is the one that should worry a
reader: it is the citation `docs/RELATED_WORK.md` calls *"the premise of the
whole project"*, and its abstract contains no arithmetic whatsoever.

## 5. The failure that has no gate

A first draft of the `2605.23950` correction said the retracted figures were
"out of the prose". **That was false when written.** The retraction landed in
`RELATED_WORK.md` and in `refs.bib` and did not propagate to
`docs/HARNESS_DISCLOSURE.md` (all four, plus Harness-Bench's 23.8, in the
opening paragraph of the file whose subject is disclosure discipline),
`docs/EVAL_SET_DATASHEET.md` (the 14-40pp with the disclaimed magnitude
comparison and no `v1`), or `docs/LIMITATIONS.md` (n_eff 2.18). An independent
check found that; the author did not.

**A retraction is not done when the entry is fixed. It is done when every file
carrying the figure is fixed** — and nothing here checks that. The citation gate
binds a number to a *quote*; it has no notion of a withdrawn number's other
homes. That is the next gate, and it is not written.

## 6. The percent check was aimed at the safe field

33 bare `%` sat inside `quote` fields. A bare `%` reaches the `.bbl`, where
LaTeX comments out the rest of the line — and the figure is what goes, since the
percent sign is what truncates.

The check was written for `quote`, and an independent check pointed out that
**that is the half that cannot break**: `quote` and `version` are non-standard
fields no standard style prints, while `note` — printed by `plain`, `plainnat`
and `abbrv` alike — held **35 of the remaining 36**. The worst is inside a
retraction: `THE 63.7% IS NOT IN THIS PAPER` truncates at the percent, and the
survivor reads as the opposite of what was meant. The rule now covers every
field. All 69 are escaped.

## 7. Parameters chosen rather than derived

- **The block boundary set.** Derived from CommonMark rather than invented, but
  *which* boundaries to honour is a judgement: I take every one markdown
  defines. What would measure it is a labelled set of claim/citation pairs with
  ground truth on whether the number belongs to the paper — this repository has
  no such set, and building one is the same authoring problem as the trigger
  corpus.
- **Residual over-firing is accepted deliberately.** Two sentences in one
  paragraph, one carrying a figure and one a citation, are flagged even when the
  figure belongs to neither. The gate cannot read a quote against a number in
  any case, so what it asks is whether somebody opened the paper cited in the
  paragraph asserting a figure. That costs one `quote` field.
- **Residual evasion is accepted and documented.** A blank line mid-sentence
  silences the gate. Nothing detects that, and nothing here proposes to.
