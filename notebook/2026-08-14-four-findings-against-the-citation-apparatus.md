# Four findings against the citation apparatus, checked from the files

**2026-08-14.** An adversarial reviewer raised four findings against
`paper/refs.bib`, `evals/src/decision_evals/citations.py`, and the living docs
that cite from them, plus two claims already on record as unresolved. Each was
treated as a hypothesis and re-derived from the raw files before being
believed, per the standing rule. Three of four findings held, in whole or in
part; both already-flagged claims turned out to be fine as they stand. A
second, independent agent then re-checked the fixes against the files without
seeing this reasoning and reported all five of its checks SURVIVED.

## Finding 1 — CONFIRMED: opposite verification states, same date

`paper/refs.bib`'s `ninejudges2026` entry (arXiv:2605.29800) states in its
`note`: *"n_eff = 2.18 and the 95% CI [2.07, 2.31] ... are not in the
abstract ... UNVERIFIED ... Neither the body reading nor the per-dataset
figures are confirmed first-hand here."* Its `harnessbench2026` entry
(arXiv:2605.27922) states: *"UNVERIFIED AND NOT IN THE ABSTRACT: the
'23.8-point swing from harness alone' ... a bare magnitude with no source
sentence."*

`docs/RELATED_WORK.md`'s "Correction to the correction" box (in the
arXiv:2605.23950 entry) said the opposite about both figures: *"The n_eff ≈
2.18 ... is confirmed in Table 2 ... And the 23.8-point swing in
`docs/HARNESS_DISCLOSURE.md` is arXiv:2605.27922's and is in its body. Neither
was a withdrawn figure; both were correct."* Neither claim has a `quote_body`
or any verbatim body text behind it anywhere in `refs.bib` — nobody had
actually opened the tables. Two paragraphs below, the file's own
`harnessbench2026` entry independently reached the right conclusion and
removed the 23.8 figure "rather than hedging it" — so the document
contradicted itself in two places on the same page, and the wrong claim
survived only because nobody read both.

`docs/LIMITATIONS.md` and `docs/HARNESS_DISCLOSURE.md` both carried the
overclaim too, unhedged.

**Fix:** added a dated correction box to `docs/RELATED_WORK.md` walking back
the "confirmed"/"correct" language and restoring *unverified*, with the
bib-note text quoted as evidence. Hedged `docs/LIMITATIONS.md`'s n_eff
paragraph the same way. Removed the 23.8-point / "76.2 against 52.4" claim
from `docs/HARNESS_DISCLOSURE.md` — the 76.2/52.4 sub-figures had no source at
all, not even an "unverified" flag; they trace to a notebook entry
(`2026-08-13-the-retraction-was-wrong-in-the-other-direction.md`) restating
the same over-claim, which is left in place as a dated record, uncorrected,
per the append-only convention. The genuinely-supported 7.80× figure (backed
by a `quote_body` with the verbatim §4.2/Table 2 text) was left untouched.

## Finding 2 — PARTIALLY CONFIRMED: `quote_body` is unrecognized, not exploited

`quote_body` exists exactly once, on the `vardecomp2026` entry
(arXiv:2605.23950), added 2026-08-13 to hold the verbatim body-section text
for four numbers not in that paper's abstract (7.80×, 13.0pp, 8.5pp, 6-out-of-9
— all cited with those magnitudes in `docs/HARNESS_DISCLOSURE.md` and
`docs/RELATED_WORK.md`). It is load-bearing: it is the *only* place those four
numbers have verbatim support.

Tested directly against `parse_bib` rather than assumed: an entry with
**only** `quote_body` and no plain `quote` correctly comes back
`has_quote=False` — the gate would refuse it, not wave it through. So the
reviewer's literal mechanism ("the gate would report green") does **not**
hold for that scenario. What actually kept the real entry green is that it
*also* carries a plain `quote` field (the abstract text, no numbers in it) —
the pre-existing, already-documented content-blind limitation ("a quote field
is not read against the number beside it, and cannot be"), not something
`quote_body` caused. Had that redundant `quote` field ever been deleted as
apparently-redundant, the entry would have gone from silently-passing (for the
wrong reason) to silently-passing-for-no-reason-at-all, or to failing loudly —
depending on nothing the gate controlled. That fragility is real even though
today's specific exploit isn't.

**Fix, in `evals/src/decision_evals/citations.py`:** added `QUOTE_BODY_FIELD`
and recognized it explicitly in `has_quote` (now checks both `quote` and
`quote_body`), and added `check_unknown_quote_fields`, wired into
`check_citations`, which refuses — loudly, unconditionally, not
baseline-exempt — any bib field starting with `quote` that is neither of the
two known names. A rename now fails the build instead of silently carrying no
verification weight. Eight new tests in `tests/unit/test_citations.py`; full
suite green (`.venv/Scripts/python.exe -m pytest tests/unit/test_citations.py
-q`, 82 passed after the additions).

## Finding 3 — CONFIRMED: AgentAtlas cited in three places, the note listed two

`agentatlas2026`'s note named only `docs/PROTOCOL.md` and
`docs/RELATED_WORK.md` as "the affected prose" carrying the v1-only
14-40pp figure. `docs/EVAL_SET_DATASHEET.md:87-101` carries the identical
figure and version caveat and was not in the list.

**Fix:** added the third location to the note.

## Finding 4 — CONFIRMED, extensively: 9 of 15 checked line-pointers were stale

Extracted every `docs/X.md NNN[-NNN]` style pointer from `refs.bib` notes (15
found) and checked each against current file content. Six were still
accurate (all near the top of `docs/RELATED_WORK.md`, before any correction
box had been inserted ahead of them). Nine were wrong, by margins from 2 lines
(`docs/RESEARCH_PROGRAMME.md`, recency2025rerank) to over 180
(`promptinginversion2025`'s `docs/RELATED_WORK.md` pointer: claimed 335-336,
the content is at 523-524). The mechanism is exactly what it looks like:
`docs/RELATED_WORK.md` has had several dated correction boxes inserted ahead
of earlier content over 2026-08-13 and 2026-08-14, and nothing re-derives the
line numbers cited from a point in time before those insertions. One case
(`askorassume2026`) pointed at a since-corrected sentence that no longer
exists as live prose at all, only inside a dated box.

**Fix:** corrected all nine pointers, and where a note described a defect in
the prose that has since been fixed in the living doc (the askorassume2026
"three counts" and the agentatlas2026 "magnitude comparison" claims), updated
the note to say so rather than continuing to assert the fix hasn't happened.
Each correction is marked inline `(LINE NUMBERS CORRECTED 2026-08-14, was
...)` so the change itself is auditable from the bib file alone.

## Already-flagged claim 1 — REFUTED as a live problem: arXiv:2605.23950

Current state: `docs/RELATED_WORK.md` §6 and `docs/HARNESS_DISCLOSURE.md` cite
the paper's abstract (no numerals, verified) for its qualitative claim, and
separately cite its body (§4.2, Table 2) for the four numbers, backed by a
`quote_body` field carrying the verbatim body text, with an explicit caveat
that the 7.80× is "one estimate from one 3×3 design on one task distribution."
This is the correct shape — abstract and body cited as what they are, numbers
backed by a quote — and needed no further fix beyond noting the `quote_body`
mechanism explicitly in `docs/HARNESS_DISCLOSURE.md`'s prose (done as part of
Finding 1's fix).

## Already-flagged claim 2 — REFUTED as a live problem: arXiv:2306.05685

Current `docs/RELATED_WORK.md` prose (§4): *"can match both controlled and
crowdsourced human preferences well, achieving over 80% agreement, the same
level of agreement between humans."* This is the paper's own wording,
verbatim, and correctly states parity rather than superiority. The old,
inequality-reversed "~85%, above human-human ~81%" survives only inside a
dated correction box and in the `refs.bib` note describing the historical
error — exactly where a retracted figure belongs. No fix needed; this
retraction had already propagated completely, as a prior notebook entry
(`2026-08-13-the-retraction-was-wrong-in-the-other-direction.md`) had already
found by repository-wide grep.

## Verification

- `.venv/Scripts/python.exe -m pytest tests/unit/test_citations.py -q` — all
  green, including the eight new tests for `quote_body` recognition and
  unknown-field refusal.
- `.venv/Scripts/python.exe -m decision_evals.cli check` (full, not `--fast`,
  per standing rule 4) — 13 of 16 steps pass; `citations` and `documentation`
  both pass. The three failures (`trigger sets`, `pytest` corpus-battery
  tests, and an initial `site` staleness before rebuild) are unrelated to
  this work: `datasets/triggers/decision-making/index.yaml` was observed at
  261 cases against an expected 120 mid-session, `docs/DECISIONS.md` was
  staged by someone else, and `evals/src/decision_evals/corpus.py` /
  `tests/unit/test_corpus_battery.py` were modified outside this session —
  another session's in-progress corpus work, per this repository's own
  documented convention for concurrent sessions. `de site` was re-run to
  clear the staleness the docs edits in this entry caused; that part of the
  failure was this session's to fix and is fixed.
- An independent agent, given only the fixed files and the five checks above
  (not this reasoning), reported all five SURVIVED its attempt to break them.

## What this leaves open

`docs/HARNESS_DISCLOSURE.md`'s notebook-sourced "76.2 against 52.4" figure
remains uncorrected inside
`notebook/2026-08-13-the-retraction-was-wrong-in-the-other-direction.md`,
by design — notebook entries are append-only dated records, not living
prose, and that entry already exists as the record of a retraction that
overcorrected. This entry is effectively a second such record for the same
underlying figure, one layer further down, and the pattern — "not in the
abstract" drifting to "confirmed" or "absent" without the tables ever being
opened — has now happened three times in this exact section of
`docs/RELATED_WORK.md`. That is worth someone actually reading
arXiv:2605.29800's and arXiv:2605.27922's tables rather than writing a fourth
correction box.
