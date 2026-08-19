# 2026-08-19 — Track G's padding shelf is under 3k tokens, so length is not reachable

Recorded before any decision is made about it, because the fact is
independent of what gets decided.

Track G is the long-context track: **does context length make the turn and
handoff effects worse?** Its premise needs long contexts. It cannot currently
build one.

## What was measured

`datasets/library/tax/` is the only padding library that has passed Track G's
separability gate (AUC 0.679). Counted directly:

| | |
|---|---|
| files | 12 |
| bytes | 11,471 |
| tokens, at the usual 4:1 estimate | **~2,867** |

`scripts/pad.py:draw()` samples **without replacement**, so that is a ceiling
rather than a starting point. The existing probe corpus already sits at about
2k. **There is no rung above it to climb to.** Reaching 40k or 100k is not a
configuration change; it is the ~960k characters of pilot-library authoring
that Track G's own section put on hold.

A reconnaissance pass reported 11,256 bytes against my 11,471. The gap is
trivial and moves nothing — under 3k tokens either way — and is noted only
because it is the kind of small discrepancy that gets quoted into a design and
then inherited.

## Three things in the plan are prose, not code

Checked by looking for them rather than by reading the task list:

- `scripts/detect_core.py` — **does not exist.**
- `scripts/pad.py` — **no CLI**; no `argparse`, no `__main__`.
- `scripts/probe_casefile.py` — has no `--ablate` or `--long` flags, which the
  plan's own worked example commands use.

`scripts/pad.py` and `scripts/separability.py` are real and tested, and
`separability.py` has a working CLI that has actually run and produced the
0.679.

This is the fourth time this repository has found documented machinery that
does not exist or does not run — `triggers` tested and called by nothing,
`prereg.py` with every refusal and no caller, `PROTOCOL.md` §3's refusal in the
present indicative, and now three entries in a plan's command examples. The
standing rule already covers it: prose describing a mechanism names the arena
it runs in and the tense it runs in.

## What this does not decide

**It does not close Track G.** It says the cheap version does not exist: any
length rung above ~2.8k must be authored first, which means committing to a
corpus *before* learning whether length produces the headroom the track is
premised on. Whether that is worth spending is a judgement and it is being
made separately.

It also does not rescue the alternative. Track G's 2k venue already **fails
both gates** — admissibility 0.917 against a 0.85 ceiling, trap rate 0.000 —
so staying at 2k is not a fallback, it is the fifth closed venue under another
name.

**And the dates defect is inherited either way.** All 82 probe-casefile
documents contain zero dates, so realistically-dated padding is a perfect tell.
Any material authored from here carries dates in both cores and padding, and a
probe reusing the dateless cores is testing an artificially easier corpus than
the real one would be.

---

## Correction, appended same day: the 4:1 token estimate is wrong for this material

The table above converts 11,471 bytes at the usual 4 chars/token and prints
~2,867 tokens. **This repository has measured its own filler and it is not
4:1.** `results/probe/canary-long.jsonl` row 6 records 101,142 input tokens
against a 608,305-character prompt — **6.01 chars/token**.

If the tax library tokenises like the canary filler, the shelf is nearer
**~1,900 tokens** than 2,867. That is not asserted as measured — the canary's
filler and the tax library are not the same text and nobody has tokenised the
library itself — but 4:1 is a convention, 6.01 is a measurement, and the
convention is the one that flatters the number. **The conclusion holds either
way and holds harder: the shelf is smaller than reported, not larger.**

It also makes the authoring bill *bigger*. Characters per token going up means
more characters are needed per token of context, so a 40k or 100k rung costs
more to author than a 4:1 estimate implies, not less.

## And two rows of the canary are junk that must not be averaged

Found while checking the above. `canary-long.jsonl` carries eight rows and two
of them are broken:

| row | prompt_chars | input_tokens |
|---|---|---|
| 1 | 152,305 | **10** |
| 2 | 380,305 | **10** |
| 4 | 152,305 | 25,489 |
| 5 | 380,305 | 63,313 |

Rows 1 and 2 are an earlier sweep that recorded ten tokens for prompts of
152k and 380k characters. Rows 4 and 5 are the same prompts measured properly.
**Nothing in the file marks rows 1 and 2 as void**, so anything averaging
`input_tokens` across this file silently mixes them in — the same shape as the
scorer defects already on `STATUS.md`'s list, sitting in a results file rather
than in code. Row 7 is the 350,000-token attempt and is an error record with no
data.
