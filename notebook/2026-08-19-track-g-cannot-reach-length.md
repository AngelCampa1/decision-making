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
