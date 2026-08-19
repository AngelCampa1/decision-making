# The gate that could not read the page

**2026-08-19.** The landing page said the skill had four procedures. It had six,
and had had six since `0.3.0`. `de check` was green the whole time.

That is not a bug in `docs.py`. Its scope is `("*.md", "docs/*.md")` and it does
what it says: it resolves references inside markdown. `site.py` hashes the
inputs and reports whether the site was built from the current tree. Neither one
opens a `.astro` file, so between them they proved the site was rebuilt from
documents whose links all resolve, and said nothing at all about whether the
page agreed with them.

Worse, the pair actively laundered the disagreement. Editing `SKILL.md` made the
manifest stale; `de site` rehashed and rebuilt; the wrong page republished, and
the gate went green on the strength of the rebuild it had just demanded.

## What else was wrong at the same time

Found by reading, not by any check:

| Published | Source | |
|---|---|---|
| "Four methods. It reads one." | `SKILL.md` routes to six | wrong since `0.3.0` |
| `13` runs published | `getCollection('results')` sees 12 | wrong, and hand-introduced while fixing the row above |
| "about six points" | `STATUS.md` retracts that exact phrase; it is nine | live on `results/index.astro` |
| `4,240` model calls | `STATUS.md` totals `~8,550` after four appended corrections | two corrections behind |
| `8` tests found broken | `STATUS.md` says eleven | stale |
| `v0.2.1 · experimental` | frontmatter says `0.3.0` | stale |
| og description: "Four methods… the eight times" | both superseded | this is the social card |

Seven claims, one file each, none caught by anything, because the site was the
last artefact here checked by reading it.

## What was built

Two mechanisms, because the claims split cleanly into two kinds.

**Structural facts are derived.** `site/src/lib/facts.ts` parses the routing
table out of `skills/decision-making/SKILL.md` and the page loops over what it
finds. The count, the order, the filenames, the version, the status and the
verdict are no longer typed anywhere. Three details matter more than the idea:

- It parses the *table*, not the directory. The table is what an agent actually
  routes on, so `placebo.md` is excluded structurally rather than by an
  exclusion list somebody has to remember to update.
- The check runs **both ways**. A file present under `decision-making/` and
  absent from the table is a build error naming the file. That is the rule that
  catches the original defect: `council.md` and `hinge.md` were on disk and
  unmentioned, and a one-way check would have stayed silent.
- Copy is a lookup, never a source. `requireCopy` refuses a partial join in
  either direction, so a hand-written map can fail loudly but can never decide
  how many procedures exist. An array is how the page came to say four.

**Measured numbers are gated.** `site/claims.json` binds a value to a sentence
in a document, and `evals/src/decision_evals/claims.py` refuses to pass when the
sentence moves. It runs in `de check` immediately after the documentation step
and is not behind `--fast`, because the edit most likely to break it is a
routine `STATUS.md` append, which is when the fix is cheapest.

## The estimator that could not return a non-zero answer

The `latest` field exists because `STATUS.md` corrects by appending and now
holds four true totals at once. A quote-match alone will happily keep matching
the oldest one forever.

It was written as `(?<=therefore )~[0-9],[0-9]{3}` against the sentence *"The
total is therefore ~4,816"*. The newest correction is a **table row**, not a
sentence, so the lookahead could not match it. The gate reported green while the
page published `~4,816` against a live `~8,550`: **3,734 calls short, with the
guard for exactly that failure installed and inert.**

This is the second time this shape has been recorded here, after the two trigger
instrument defects of 2026-08-12, and the standing rule caught it:

> Before believing an outcome, check that some possible response would have
> scored above zero for this arm.

Anchored to the table row instead, the guard fires. It was then tested by moving
the number: appending a newer `~9,100` row makes `de check` name both figures
and refuse.

Four negative tests were run by hand, one at a time, each restored from a file
copy:

| Provocation | Result |
|---|---|
| delete `hinge.md` from the routing table | build exits 1 naming the file; `de site` leaves the manifest unchanged |
| change the total in `STATUS.md` | claims step refuses: quote no longer present |
| append a newer total to `STATUS.md` | claims step refuses: page publishes a superseded figure |
| put `about six points` on a page | claims step refuses, citing the retraction |

## What the call total is not

It stays gated rather than derived, and the reasoning is worth keeping because
somebody will want to "fix" it:

- `results/triggers/` holds rescored `.jsonl` whose own rows say no call was
  made. Any glob needs a rule, and encoding that rule moves the prose judgement
  into Python without removing it.
- 6,825 and `~8,550` count different sets. The ledger covers seven families,
  most with no run directory. Publishing 6,825 as "model calls" would silently
  redefine the number.
- `results/calibration/off-arm.jsonl` duplicates the evidence-ledger copy
  byte-for-byte, so a naive glob double-counts.
- `STATUS.md`'s appended corrections *are* the evidence. A derived integer would
  force them rewritten in place, destroying it.

## Found while looking at the rendered page

The redesign was the occasion, not the finding, but two defects only a browser
could see are worth recording because no gate here can reach them.

**Sixteen elements failed WCAG AA on contrast, and all sixteen were two
tokens.** `--ink-muted` measured 3.99:1 to 4.25:1 and `--ink-faint` 2.66:1 to
2.83:1, at sizes between 10px and 15px. `--ink-faint` carried a comment reading
*"NOT body text. Licensed for >=19px, non-text bounds, and disabled chrome"* and
had twelve text call sites. The law was written and then ignored. It is now
enforced rather than loosened: the token is gone, `--ink-muted` is set from the
worst surface it has to survive, and a near-black ground turns out to leave room
for exactly one quiet grey that clears AA, which is why there were two that did
not.

**At 375px the theme toggle sat past the right edge of the viewport with the
document reporting no horizontal overflow at all** (`scrollWidth === clientWidth
=== 360`). It was clipped, not overflowing, so the obvious check could not see
it. `dark` could not be pressed on a phone.

## What this does not fix

The claims gate binds a number to a sentence. **It cannot tell whether that
sentence is still the document's answer.** `latest` narrows this where a
correction has a numeric shape and does nothing where it is phrased in words.
The retractions list is the manual remedy, so that hole closes one commit late.

It also cannot tell a published claim from a comment describing one. A comment
in `Base.astro` quoting the old wording failed the gate that exists to catch the
old wording, and was reworded rather than exempted.

That is the same shape as the two limits already on record. `docs.py` reads
whether a reference exists, never whether the sentence is true. `site.py` proves
the site was built, never that it was pushed. Three gates, three standing
limits: each proves a correspondence, none proves currency.

## Appended the same day: two more, both found by checking rather than by care

**The 375px toggle fix was scoped one breakpoint too narrow, and the same
control was clipped again at 768.** The remedy above was a two-row header under
`@media (max-width: 32rem)`. At 768px the header is still one row, the `46rem`
query that hides the wide nav item has not fired, and `.theme-toggle` — which
carries `overflow: hidden` because that is what clips its buttons to the rounded
border — had no `flex-shrink: 0`. So the flex row ran out of room and the group
shrank, amputating `dark` by 23px while `document.scrollWidth` again reported no
overflow. Identical failure, identical invisibility, one breakpoint up.

Pinning the toggle then moved the failure rather than removing it: nothing
clipped, and the row overflowed the viewport by 4px instead, because a flex item
does not shrink below its min-content width unless told to. The nav is the part
that can degrade gracefully, so `flex-wrap: wrap` and `min-width: 0` went there.
Measured clean at 375, 414, 540, 640, 753 and 1425.

The lesson is not "check more widths". It is that the first fix was written
against the width where the bug was reported, and a fix scoped to the report is
scoped to nothing.

**And `test_the_published_checkpoints_were_actually_found` asserted `len(...) >=
2` over a glob that finds two files only on a machine that has already run the
experiments.** Its own docstring said it existed so the parametrised test above
it could not be "vacuously green". Exactly one RunRecord checkpoint is
committed; every other one lives under `results/calibration/`,
`results/track-a/`, `results/track-0/` or `results/triggers/`, all gitignored on
purpose. So on any clean checkout the guard against vacuity failed, and on this
machine it passed for a reason unrelated to what it claimed to check.

It now names the tracked file instead of counting. That is strictly stronger
where it can be: a layout move or a first-line shape change fails with the path
in the message, rather than with an integer that means nothing on its own. It
was confirmed live by pointing it at a moved path and watching it fail, because
an estimator that cannot return a non-zero value is not a measurement.

This is the fourth thing on this page that reported green, or red, for a reason
that had nothing to do with the thing it was watching.

## Correction, appended 2026-08-19: four things this entry got wrong

Four adversarial reviewers were run over this branch. Two of them read this
entry. Corrections go below rather than above, because the entry is the record.

**The quotation in the contrast paragraph was invented.** It reads:

> `--ink-faint` carried a comment reading *"NOT body text. Licensed for >=19px,
> non-text bounds, and disabled chrome"*

The comment at `f12b444:site/src/styles/base.css:36-37` is:

```
/* NOT body text. 3.56:1 -- licensed for >=19px, non-text bounds, and the
 * em-dash null glyph only. */
```

Three departures, presented in italics inside quotation marks as verbatim: the
ratio is dropped, `licensed` is recapitalised, and **"disabled chrome" replaces
"the em-dash null glyph only"** — a wider licence than the comment granted, in
a paragraph arguing the licence was ignored. This is the defect `509cc13`
records two commits earlier on this same branch, *"the confirming review found
a quote I had invented"*, committed by me, two hours before I did it again.

**"twelve text call sites" is six.** `git grep "ink-faint" f12b444 -- site/`
returns ten lines: three are the token's own definitions across the three theme
blocks, one is a `stroke:`. Six `color:` call sites across four files.

**"the lookahead could not match it" is a lookbehind.** `(?<=therefore )` is
lookbehind syntax. `site/claims.json` gets it right in the same commit, which
means the two records of one event disagree about the mechanism.

**"Seven claims, one file each" is seven claims across five files.** Three of
them — four procedures, ~4,240 calls, eight broken tests — were all in
`docs/index.html`, which is the page that turned out to be the one actually
being served. The phrase was an echo of the README's "Four instances, one file
each" and did not survive being counted.

**And the diagnosis at the top of this entry is narrower than it reads.** It
says neither `docs.py` nor `site.py` opens a `.astro` file, which is true and
was not the whole story: the live page was `docs/index.html`, and the claims
gate built here scans `site/src/**` and would not have opened that file either.
`eb966b2` deleted it and repointed Pages at the Astro build. The gate this entry
is about would not have caught three of the seven claims it opens by counting.

None of the four were found by a gate. Three were found by a reviewer briefed to
break the work, and the fourth by that reviewer counting something I had
asserted. The entry's own closing line — that everything on this page reported
green for a reason unrelated to what it was watching — now includes the entry.
