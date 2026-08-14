# 2026-08-14 — adversarial re-derivation of the long-band merge

Dispatched to break the claims in `a38d2d8`/`8342165` (23 long-band triples
merged, `word_count` leak reported closed). Re-derived every number from the
raw YAML with a script written from scratch against the documented formulas in
`corpus.py` (`matched_separability`, `matched_null_se`, `matched_dispersion_z`,
`_shared_body`/`_ask_view`) rather than by importing or running that module's
own report path.

## The six claims

All six held, on independently reproduced numbers:

1. **261 items / 87 triples, no collisions.** `s`=24, `m`=24, `l`=22 (`l01`-`l22`),
   `xl`=17 (`xl01`-`xl17`) triples; 261 unique ids, zero duplicates.
2. **`word_count` matched: 0.660 (z=3.24) → 0.546 (z=1.09).** Reproduced exactly,
   including on the `ask` view (identical to `turn` for this feature — expected,
   since subtracting an identical shared body from all three triple members
   cannot change their pairwise word-count ranking).
3. **Post-merge per-band word_count: s 0.604, m 0.750, l 0.455, xl 0.294.**
   Exact match.
4. **23 new triples, word_count rank: 16 shortest / 5 middle / 2 longest.**
   Exact match, verified per-triple.
5. **Two new leaks: `sentence_count` dispersion 3.82 SE, `type_token_ratio`
   ask matched 0.316 (z=4.27).** Exact match, and cross-checked against a live
   `de check` run's own `battery_report` output — identical to four decimal
   places on every number printed.
6. **`de check --fast` passes all 13 steps.** True as stated (`--fast` is
   defined in `cli.py` to skip exactly `site`, `pytest`, and `coverage floors`
   — the three steps that do fail; see below).

## The central question: cancellation, and what it does and does not mean

The commit's own account is right that `word_count` closed by cross-band
cancellation, not rank uniformity, and that `l`'s and `xl`'s per-band figures
swung *past* 0.5 rather than toward it. Restated with deviations from chance:
`l` moved from |0.278| to |0.045| (closer to chance — genuinely better), `xl`
moved from |0.107| to |0.206| (twice as far from chance as before, and
further than the 0.660 pooled figure — |0.160| — that motivated the whole
exercise). So on the per-band matched statistic alone, `xl` did get worse.

**But per-band matched separability is not what an arm can exploit, and
testing the thing an arm can actually use changes the answer.** An arm at
inference sees one turn and its band (band is visible — a 1,200-word turn is
self-evidently XL), never its triple-mates. So the exploitable quantity is a
*band-restricted plain AUC* (positives vs. all negatives in the band, no
pairing) on a feature computable from the turn alone — not the matched
statistic, which requires the specific two negatives from the same triple.

Computed directly (permutation test, 20,000 draws, two-sided):

| feature | view | band | plain AUC (band-restricted) | perm p |
|---|---|---|---|---|
| word_count | turn | xl | 0.457 | 0.63 |
| word_count | ask | xl | 0.407 | 0.28 |
| sentence_count | ask | xl | 0.299 | 0.014 |
| type_token_ratio | ask | l | 0.315 | 0.014 |
| type_token_ratio | ask | xl | 0.330 | 0.050 |
| sentence_count | ask | l | 0.403 | 0.17 |

**`word_count` is fairly characterized as a construction defect rather than a
demonstrated exploit** — the whole-turn plain AUC in `xl` is 0.457, statistically
indistinguishable from chance, because the shared pasted body dilutes it exactly
as `corpus.py`'s own comments predict. But **`sentence_count` and
`type_token_ratio`, read on the `ask` view specifically, do not get that
defense** — their band-restricted plain AUC is significant at conventional
(uncorrected) thresholds in both `l` and `xl`. The `ask` segment is not
something only the corpus's own measurement code can see; it is the literal
closing portion of the turn the arm receives, so a model that attends to
sentence count or vocabulary diversity in the closing ask has real,
band-usable signal on two of the three post-merge findings. The "an arm sees
one turn and cannot use a within-triple rank" defense in the notebook entry
and `corpus-baseline.txt` is accurate for `word_count` and optimistic for the
other two.

## Is xl at 0.294 shippable?

Yes, provisionally, and no differently than before the merge — with one
caveat now attached that wasn't there before. The matched-statistic
degradation in `xl` is real but is the *construction* signal (a bookkeeping
property of how each triple's three items relate to each other), and the
direct exploitability test above shows the feature that produced it
(`word_count`) does not survive contact with a same-band, unpaired AUC. What
does survive is `sentence_count`/`type_token_ratio` on the ask view, and
those are already correctly flagged open in `corpus-baseline.txt` — this
entry adds that their risk is not purely theoretical.

## Other checks run

- **corpus-baseline.txt may-only-shrink:** legitimate. `MATCHED_Z = 3.0` is
  unchanged in `corpus.py` across the merge; independently confirmed the two
  closed entries crossed *under* that fixed threshold (1.09 < 3.0) and the
  three new entries crossed *over* it (3.82, 3.82, 4.27 > 3.0) — not a
  threshold moved to accommodate anything.
- **Golden files:** confirmed unrelated. `tests/golden/test_generator_golden.py`
  pins `datasets/templates/*.yaml` → `datasets/golden/*.json` via a template
  generator that never reads `datasets/triggers/`. No `--bless` was needed.
- **Same-object-per-band:** no defect found. `word_count`/`sentence_count`
  read identically on `turn` and `ask` by mathematical necessity (subtracting
  an identical shared prefix from three items cannot change their pairwise
  order); `type_token_ratio` genuinely differs by view, as expected for a
  non-additive statistic. Not the `final_response`-vs-turn-count shape of bug.
- **Estimator cannot fail:** refuted directly — two features in this same
  battery run scored well outside chance (0.316 at z=4.27, 3.82 SE
  dispersion) in the same pass that reported 0.546 as closed.
- **The three deferred label moves (`s02n2`, `s12p`, `xl05n2`):** confirmed
  still unapplied — `s02n2` and `xl05n2` are still under `negative:`, `s12p`
  still under `positive:`. The 2026-08-13 entry in `docs/DECISIONS.md` said
  the key would move "once, at the freeze, with the long-band rebuild in the
  same version bump." The long-band rebuild happened and the moves did not
  ride with it. The 2026-08-14 entry discloses this itself rather than
  hiding it ("'the freeze' the entry below anticipated is still open on that
  point"), so this is a disclosed plan slip, not a concealed defect — but the
  corpus is not in the state the earlier entry said this point would reach.
- **A minor undercount, found rather than sought:** the notebook entry
  describes one deliberately unroutable new triple (`l17`, `route: ~`). The
  new batch actually has two (`l17` and `xl16`); two more (`l08`, `xl07`)
  predate the merge, for four `route: ~` cases corpus-wide. Immaterial to any
  of the six claims, noted for completeness.

## `de check`, run in full (not `--fast`)

Not run by the merging agent; run twice here directly via
`.venv/Scripts/python.exe -m decision_evals.cli check`. Both runs: **3 of 16
steps failed** (composition of failing steps varied slightly between the two
runs because a second, unrelated session was live-committing in the same
working tree throughout — see below).

**Attributable to `a38d2d8`/`8342165`:** the `site` step fails because
`docs/DECISIONS.md` changed in `8342165` and `site/build-manifest.json` was
not rebuilt in the same change set, which is a direct instance of the rule
CLAUDE.md states explicitly ("editing a document means rebuilding the site in
the same change").

**Attributable to the corpus growing, but not newly introduced by this
merge:** `pytest` fails on `tests/unit/test_realism_probe.py::
test_sample_is_forty_items_and_matches_the_track_budget` and
`::test_sample_represents_both_labels`, both hardcoded to a 40-item / 40-triple
sampling budget. `test_sample_takes_exactly_one_item_per_triple` (which
passes) requires the sample to cover every triple in the corpus exactly once,
which is only consistent with a fixed budget of 40 if the corpus has exactly
40 triples — true only before the 2026-08-13 short-band merge (`e07c5ef`),
which took the corpus to 64 triples and already broke this invariant a full
day before today's merge. Nobody had run the full test suite across either
corpus-growing merge to notice. A third test with the same shape
(`test_the_repository_draft_is_reached_and_is_the_whole_corpus`, hardcoded to
`== 120`) was already being fixed, uncommitted, in a concurrently live
session's working tree at the time of this check (converted to recompute the
expected count from the band files rather than pin a literal) — confirming
the defect is real and independently noticed, not an artifact of this audit.

**Not attributable to this merge:** a `citations` failure (9 issues) in one
of the two runs traced to `paper/refs.bib`/`paper/citations-baseline.txt`,
which were mid-edit, uncommitted, in the same concurrent session; a
transient `decision register` failure in the first run named commit `6707c38`
(an unrelated `_shared_body` fix from that same concurrent session), which
was registered and passing by the second run.

## Where I could be wrong

The band-restricted permutation p-values above are uncorrected for the six
comparisons run; at Bonferroni (α≈0.0083) none individually survive, though
two (`sentence_count` ask/xl, `type_token_ratio` ask/l) sit close (0.014).
This entry treats them as "worth the caveat," not as a proven exploit — the
same standard the corpus's own `matched` gate applies to itself.

Full script: written to a scratch path outside the repository for this
session; the formulas and results are reproduced in full above rather than
attached, since the point of an adversarial re-derivation is the numbers
matching independently, not the script matching.
