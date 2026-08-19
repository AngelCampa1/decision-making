# 2026-08-19 — the first docs sweep, and four things it found

Not a run. This is the first sweep under the new standing rule in `AGENTS.md`:
every third published run, read `README.md` and `docs/` for drift and land the
sweep here. `docs/RUN_INDEX.md` is the clock, because it is generated and cannot
itself drift. Thirteen runs are published, so the next sweep is due at sixteen.

The rule exists because nothing checks this. `de check` refuses a reference that
does not resolve and will never judge whether the sentence around it is true —
`docs.py` declines to become a prose linter on purpose, on the grounds that an
advisory gate becomes noise before somebody turns it off. So the failure is
silent by construction, and the way to find it is to go looking on a schedule.

## What drifted

Four, all found in one pass, none by anything failing:

| claim | where | actual |
|---|---|---|
| "Fourteen documents" | `docs/README.md` | 15 listed, 16 files including the index |
| "Four methods. It reads one." | site landing page | six procedures since `ae55b5b` |
| "Seven results are in" | `README.md` | thirteen in the generated index |
| "About 4,240 model calls" | `README.md`, landing page | predates four runs |

Every one drifted by accretion. Nobody decided any of them.

**The call total is left uncorrected, deliberately.** I could not recompute it
without inventing a number. `results/decision-making/*/` holds published copies
of calls that also sit in `results/triggers/*.jsonl` as working checkpoints, and
`rescored-*` files are re-scores that cost no call at all, so the JSONL line
count over the tree is 17,900 and the true figure is far lower. `STATUS.md`
last put it near 4,600 and that was before N5, N6, N7 and N9. Rather than guess,
`README.md` now points at the ledger and says the ledger's figure is stale.
Recounting it belongs to whoever next touches `STATUS.md`, and it needs a rule
for which files count.

## What was added

`docs/METHODS.md` — a human-facing account of the method, one section per
technique, each naming what it defends against, the code, and **whether it has
actually run**. That last column is the reason the file exists; several entries
say it has not.

## What the adversarial review found, and why the file is better for it

The draft went to an agent briefed to break it. It came back with a
do-not-publish verdict and it was right. The draft committed **the exact defect
this repository names as its worst recurring one**, in the section whose entire
job is to separate built from fired:

> "Every skill is measured against four arms on the same items: off, on,
> placebo, and cot."

Present indicative, every path correct, and false. `build_arm` has exactly one
production caller, `scripts/calibrate.py`, which asks for `off`. The runner
behind every published measurement does not import the module at all. There is
no placebo record and no cot record anywhere in `results/`. I caught this one
myself while the review was still running, which is luck of timing rather than
method — I only went looking because I had written the brief telling the
reviewer where to look.

Confirmed and fixed, in descending order of how badly they would have read:

- **§9 quoted ten description arms' results without the 2026-08-19
  retirement.** `DECISIONS.md` states that adding `council` and `hinge` rewrote
  the description field, so *no number anywhere in this repository may be
  presented as a measurement of the current description*. A reader would have
  finished the section believing those figures characterise the shipped skill.
  They characterise a string that was replaced the same day.
- **"Recall rose three to five points on every arm on disk"** — false. It fell
  on `opener-only`, 0.956 to 0.953. The source notebook's own headline says
  "every arm improved" against its own table; the draft hardened a loose
  headline into a quantified universal the data contradicts.
- **Counts, five of them.** `ZeroCause` has six members, not four. `prereg.py`
  implements six refusals, not five. The baseline pattern appears seven times,
  not four. Pre-registration defects number at least seven, not five — and two
  separate entries in `notebook/` both claim to be the fifth, so the running
  total is itself drift.
- **Primary metrics were attributed to the wrong module.** `parse_answer` and
  `score_item` have never touched a published trigger measurement; that is
  `TriggerReport` and `evaluate_routing`.
- **The judge policy was written as practice.** No judge panel has run here, and
  the robust aggregation estimator the protocol commits to has no
  implementation at all.
- **"Two published runs" recorded adversarial re-derivation with own parsing
  code and named objections.** Three runs record re-derivation and exactly one
  satisfies every condition; the sentence bundled the strongest attribute of
  each and asserted it of two.
- **§2 was eight days stale** — it left the reader at 261 items with twelve
  unapplied moves, which stopped being true on 2026-08-18 when the rewrite round
  resolved eleven of twelve and retired `l15`.
- Smaller: a `golden files` row in the `de check` table that is not a step, an
  `audit_distractors` row claiming a half-run with no artefact on disk, an
  unsourced discordant split, a block quote altered from its source, and a
  "two-of-one" that should read two-to-one.

The review also checked twenty-odd figures that were right, which is what makes
the list above worth trusting.

**The lesson is not "check your numbers".** It is that the draft passed
`check_citations` and `check_docs` with zero findings, and both gates are
working correctly. Every link resolved. Every identifier had a bib entry. That
is precisely the condition under which this repository's characteristic failure
hides, and `docs.py` says so in its own docstring. A green gate beside a
document nobody adversarially read is exactly as green as one beside a document
somebody did.

## Also changed

- `AGENTS.md` gained the sweep rule; `CLAUDE.md` regenerated by `de mirror`.
- The landing page gained `council` and `hinge`, and its stale counts moved. It
  went through `humanizer` and `third-grade-copy` per the writing rule one
  directory up. Two fixes came out of that pass: a 20-word sentence and a
  passive that hid who throws the corpus out. Grade 1.1, longest sentence 13
  words. The remaining `best` flags are factual superlatives about measured
  scores and are kept as a documented exception.
- The landing page and `README.md` had disagreed about the word-count-ruler
  margin — six points against nine, from citing different arms. Both now say
  nine and name the arm.

## Left open

- The call total, above.
- `docs/STATUS.md` is dated 2026-08-14 in its own header and has drifted three
  times on the same line. This sweep did not rewrite it, because corrections
  there are appended rather than rewritten and the recount it needs is a
  separate unit of work.
- `docs/index.html` is orphaned legacy from a superseded Pages setup. Nothing
  references it and Astro does not render it. Not removed here; removing it
  wants its own look at git history.
