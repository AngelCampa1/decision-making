# 2026-08-19 — the same whitelist defect, third instance, caught before it ran

Adding `council.md` and `hinge.md` to the shipped skill left two places naming
the old four procedures:

- `evals/src/decision_evals/triggers.py:36` — `PROCEDURES: Final = ("ledger",
  "fit", "cascade", "timing")`, the default whitelist for `decision()`.
- `scripts/run_triggers.py`'s `SYSTEM`, `SYSTEM_CONFIDENCE` and `SYSTEM_FOUR`
  prompt strings, whose JSON contract reads `"procedure":
  "ledger"|"fit"|"cascade"|"timing"|null` and whose prose says *"which of the
  tool's four procedures applies"*.

**A model that routed correctly to `council` or `hinge` could not have said
so.** The contract does not offer the name, and if it offered one anyway the
whitelist would discard it. The run would have completed, checkpointed cleanly,
and reported a routing accuracy computed over a set that structurally excludes
two of six procedures.

## This is the third instance of one defect

`docs/STATUS.md`'s table already carries two:

- *"parser whitelist dropped every entry name an n=2 arm offers"*
- *"routing graded against names the arm never offered"*

Both are the same mechanism — **the estimator's vocabulary and the arm's
vocabulary drifting apart, with nothing that notices.** Both produced clean
runs and plausible zeros. The standing rule written after them says: *before
believing an outcome, check that some possible response would have scored above
zero for this arm.*

**What is new is only when it was caught.** The first two were found in the
numbers, after the calls were made. This one was found in the source, before a
single call, and not by the change's author — it came out of a sub-agent's
closing paragraph on a task about something else entirely, listing what it had
noticed and deliberately not touched. That is worth naming, because the fix for
the first two was a rule about reading results more carefully, and the rule did
not catch the third. **Reporting what you noticed and left alone did.**

## Why it does not go in the defect table

`STATUS.md`'s *Measurements caught being broken* is a table of measurements —
every row produced a run, a checkpoint and a number that somebody could have
believed. This produced nothing, because no run was launched against the
six-procedure skill. Putting it there would inflate a count that exists to be
uncomfortable. It is recorded here and in
[`docs/DECISIONS.md`](../docs/DECISIONS.md) beside the change that caused it.

## What the fix has to preserve

`PROCEDURES` is a *default* whitelist and an M5 arm overrides it with its own
entry names — an n=2 arm offers `ledger-fit` and `cascade-timing`, and
`routing_is_by_name()` exists so routing is not graded when the arm does not
offer the names. That is the machinery that caught instance two. Deriving the
names from the router table must not flatten it, and a regression test that
passes against both the old hardcoded list and the new derivation has tested
nothing.

**At the time of writing the fix is in progress and unverified.** Nothing here
claims it works.
