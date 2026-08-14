# 2026-08-14 — the ask-derivation bug, and two checks it had been hiding

**Prediction, before running anything.** Fixing `_shared_body`'s word-boundary
cut to respect a newline would change what `ask` and `open` contain on every
triple built from a real shared body (XL and the shared-body `L` triples), and
the matched within-triple statistic for `word_count` would move on `ask`
because the leaked word's presence or absence is not identical across a
triple's three members in every case. Wrong in the second half, right in a way
that mattered more: `matched:ask:word_count` did not move at all, and two
findings that had never fired before crossed the gate.

## The bug

`_shared_body` (`evals/src/decision_evals/corpus.py`) computes the raw
byte-identical prefix across a triple's three turns, then cuts it back to the
last **space** so the remainder starts at a whole word. Every authored body in
this corpus ends with a **newline** before the ask begins, and a newline is
not a space. `rfind(" ")` cannot see it, so the cut landed one word short of
where the newline actually was, and that word — `"believed."` in the shipped
XL band, `"today."` in the regression fixture below — leaked into every
derived `ask` and `open` as their shared, constant opening word.

Confirmed directly before touching anything:

```
body tail repr: ', which I have never entirely '
xl01p ask[:60]= 'believed.\nI have to say something by the 26th, ...'
xl01n1 ask[:60]= 'believed.\nTwo things I want answered before I have an opinion...'
xl01n2 ask[:60]= 'believed.\nDo the arithmetic for me, all three service figures...'
```

All three members of `xl01` opened their derived `ask` with the identical
leaked word. Fixed by preferring the last newline in the raw common prefix,
falling back to the last space only when no newline is present:

```python
newline = head.rfind("\n")
if newline >= 0:
    return head[: newline + 1]
boundary = head.rfind(" ")
return head[: boundary + 1] if boundary >= 0 else ""
```

After the fix, the same triple:

```
xl01p ask[:60]= 'I have to say something by the 26th, which is Thursday week...'
xl01n1 ask[:60]= 'Two things I want answered before I have an opinion about an...'
xl01n2 ask[:60]= 'Do the arithmetic for me, all three service figures, side b...'
```

A regression test (`TestTheDerivedAsk::test_the_body_is_cut_at_a_newline_rather_than_one_word_short_of_it`,
`tests/unit/test_corpus_battery.py`) was written and confirmed to **fail on
the pre-fix code** (asserting `asks["t0decides"] == "today.\nShould I..."` was
what the old code actually produced) before the fix landed, then confirmed to
pass after. Standing rule 2, applied to a bug fix rather than a gate: a test
that has not been shown to fail on the broken code has not been shown to test
anything.

## What this had been hiding

This is exactly the shape `CLAUDE.md` names as the fourth-through-fifth
instance in this repository: opener features (`imperative_opener`,
`first_person_rate`, and now `question_marks`/`terminal_question` on `open`)
read a constant value across every triple with a real shared body, because the
first word of the derived text was the same leaked word every time. A feature
pinned to one value cannot separate anything, so it read exactly 0.500 and
passed — not because there was no signal, but because the instrument could not
see it. `attainable_auc`/`matched_attainable` already existed as the guard
against exactly this (an interval that cannot leave `[0.5, 0.5]` is not a
passing check, it is an untested one), and once the leaked word stopped being
constant, two matched findings that the guard had never been able to fire on
crossed the z = 3.0 gate for the first time:

```
matched:open:question_marks   -- 0.566 matched, 3.47 null SE (pre-merge, T=64)
matched:open:terminal_question -- 0.566 matched, 3.47 null SE (same triples)
```

(Both moved again the same day when the long-band merge in `a38d2d8` added 23
more triples: 0.629, 6.12 SE. The finding did not change identity — same key,
same direction — only its magnitude, which is why the baseline entry records
both snapshots rather than silently updating the first.)

**What did *not* move, and why that is informative rather than a null
result.** `matched:turn:word_count` and `matched:ask:word_count` — the two
findings already baselined before this fix — read bit-identically before and
after (0.66015625 both times, to the last printed digit). The reason is
mechanical rather than coincidental: the leaked word was present in **all
three** members of an affected triple, so removing it subtracts the same
count from all three and cannot change their relative order. A within-triple
rank statistic is blind to anything that shifts every member of a triple
equally; only a rank-*sensitive* feature computed on the affected sentence
itself (which word opens it, whether it is a question) could see the leak,
and `open`'s `question_marks`/`terminal_question` are exactly that. The pooled
AUC for `ask`:`word_count` did move very slightly (0.50238 -> 0.50299),
because pooled comparisons cross triples with different original lengths and
are not blind to a triple-uniform shift the way the matched statistic is —
consistent with, and a small additional confirmation of, the module's
existing point that pooled and matched read different things.

## The guard, checked against the new work

Per the standing instruction that a new feature or view must be provable
capable of failing, not merely added: `sentence_count` (added earlier the same
day, alongside `open`) was inert in every view of the module's own known-good
fixture (`_rotating_corpus` in `test_corpus_battery.py`) — its three fixed
shapes all produced two sentences, so the feature could not move regardless of
which label fell where. `TestTheGuardPassesACorpusItShouldPass::test_no_feature_is_inert_in_all_three_views`
failed on it. Fixed by giving one shape (`generates`) a third short sentence
so `sentence_count` takes more than one value across the fixture's three
shapes; the fixture's docstring and `attainable_auc` requirement is otherwise
unchanged. Re-run, `sentence_count` is no longer inert anywhere in the
fixture, and it fires for real on the shipped corpus (`cancel:turn:sentence_count`,
`cancel:ask:sentence_count` — a dispersion finding, not a mean-shift one; see
`corpus-baseline.txt`).

`open` itself needed no fixture repair — it was already live on the
known-good fixture — but a second synthetic fixture
(`TestThePlantedLeaksAreCaught._closing_leak`, an order-swap over two
sentences) turned out to leak on `open` as well as `close`, symmetrically,
because reversing a two-element sequence swaps which element is first exactly
as much as which is last. A constant third sentence placed in front of the
swap does not fix this: `_shared_body` finds the raw byte-identical prefix, so
anything that never varies is *body* by that function's own definition and
gets folded into it regardless of where it sits relative to the "intended"
ask. `TestTheBaselineIsNarrowRatherThanBlanket`'s baseline-construction helper
was widened to capture every finding the fixture currently produces (it had
been hand-picking a subset, itself an instance of a baseline test being
narrower than the thing it was supposed to prove was narrow) rather than
attempting to suppress the open-view leak.

## Numbers that moved, for the record

| Finding | Before fix (T=64) | After fix, before merge (T=64) | After long-band merge (T=87, `a38d2d8`) |
|---|---|---|---|
| `matched:turn:word_count` | 0.660, z 3.24 | 0.660, z 3.24 (unchanged) | 0.546, z 1.09 — **closed** |
| `matched:ask:word_count` | 0.660, z 3.24 | 0.660, z 3.24 (unchanged) | 0.546, z 1.09 — **closed** |
| pooled AUC, `ask`:`word_count` | 0.50238 | 0.50299 | 0.503 |
| `matched:open:question_marks` | not measurable (feature pinned; did not exist as a firing check) | 0.566, z 3.47 — **new** | 0.629, z 6.12 |
| `matched:open:terminal_question` | not measurable | 0.566, z 3.47 — **new** | 0.629, z 6.12 |

The `word_count` closure and the `T=87` numbers are not this fix's doing —
they are `a38d2d8`, the concurrent long-band merge, whose own entry in this
file and in `docs/DECISIONS.md` covers them. They are included here only so
the table reads as one timeline instead of two disconnected snapshots.

## What was found but not fixed, and why

`MIN_LEAKS_PER_VIEW`'s own docstring table (P(>=k) false-failure rates) and
the derived-view null-rate tests in `TestTheThresholdIsDerivedRatherThanChosen`
were calibrated at 40 triples and are now measurably stale at 87 — a larger
corpus has a tighter permutation null, so every rate in that class has fallen
(turn, leaks=1: 0.0094 at T=64 per the `MATCHED_Z` table, 0.00175 today). The
qualitative argument the threshold rests on still holds (gating one feature at
a time on a derived view still fails a clean corpus ~48x more often than the
count gate that shipped), so the two affected tests were re-pinned to current
measurements with that argument stated rather than silently re-thresholded.
Re-deriving `MIN_LEAKS_PER_VIEW` itself against a corpus that is still being
merged would be measuring a moving target; that re-derivation is left for
whoever settles the corpus at a final size.

Two hardcoded assumptions outside this module's tests turned out stale for the
same reason (corpus size) and were left alone as out of scope: `test_realism_probe.py`
assumes a fixed 40-item probe sample and near-equal label balance that no
longer holds at 87 triples, and `test_triggers.py::TestADraftCorpusIsCheckedWhereItLives`
still asserts `len(draft.cases) == 120`, a count that predates even the
2026-08-13 growth to 192. Neither touches `corpus.py` or the shortcut battery;
both are the responsibility of whichever track owns the realism probe and the
"draft corpus" concept respectively.
