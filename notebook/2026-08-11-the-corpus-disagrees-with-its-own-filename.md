# The corpus disagrees with its own filename

**2026-08-11.** Track A1 prerequisite. No model calls — a download and four counts.

## What happened

Vendored the sharded corpus released with arXiv:2505.06120, pinned at
`microsoft/lost_in_conversation@c865793`, SHA-256 recorded in
`datasets/vendor/lost_in_conversation.lock.json`. 30,352,135 bytes, MIT code,
CDLA-Permissive-2.0 data. `de fetch` downloads it; the loader refuses anything
whose hash does not match, and says in the error message not to re-pin the lock
to make the refusal go away.

The payload is not committed. 28.9 MB of byte-identical-upstream data does not
belong in a git history, and the lock makes "we ran the published corpus" a
checkable claim without it.

## Then I counted, and three things were wrong

None of these are upstream's fault. All three are things **we** had written down
without opening the file.

| We had written | The file says |
|---|---|
| 600 instructions | **627 records** |
| 7 task families | **6**: actions, code, data2text, database, math, summary |
| sharded "across ~6 turns" | mean **5.97**, median **6**, range **3–12** |

The 600 comes from the filename, which is `sharded_instructions_600.json` and
holds 627 records. The seventh family is `translation` and ships as a separate
file we had not noticed. Excluding `code` — Unix-only eval, so it would score as
failure on this machine for reasons unrelated to multi-turn degradation — leaves
527 records, mean 5.78.

## The uncomfortable one

The work order's Rule 1 exists because of the "~6 turns" figure. It was invented,
written into the programme, and would have been designed around. The rule says an
invented parameter is indistinguishable from a measured one three days later.

**It was right.** Mean 5.97, median exactly 6.

That is the worst possible outcome for learning the lesson, and it is worth
writing down for exactly that reason. Being right does not make it measured, and
the next invented parameter will not be right. The rule is not "guess carefully";
it is "do not guess", and a guess that happens to land does not retire it.

## What actually changes the design

The range, which nobody had. **3 to 12 turns**, not a fixed length:

- Any per-item comparison has to carry turn count as a covariate rather than
  assume it away. A 3-turn item and a 12-turn item are not the same treatment.
- **A2 cannot reuse A1's items.** A2 holds total turns fixed while moving a
  decisive fact between first, middle and last. That design needs a constant turn
  count, and this corpus does not have one. Either A2 subsets to a single shard
  count — 6 shards is 233 records, the largest stratum — or it needs its own
  items. Recorded here as an open design question rather than resolved, because
  the choice changes A2's item count and therefore its MDE.

## What I did not do

- Did not download or run their simulator. The download is data only; their
  Python would have to be read before executing, and we do not need it — the
  Track 0 design call is to script the orchestrator ourselves.
- Did not write the `model_claude_code.py` shim yet. That is the remaining A1
  prerequisite.
- Did not compute A1's MDE. `p_discordant` is not known and must not be invented
  (Rule 1, again). It comes from a screening run or it comes as a sensitivity
  range, and either way it is the next unit.

## State

- `evals/src/decision_evals/corpora/` at 100% line+branch, 32 unit tests.
- `de fetch` with 6 tests, network stubbed.
- Verified end to end against the real 29 MB file: loads, verifies, reproduces
  every number above. Rule 2 satisfied — the gate was run against a known-good
  case before being trusted to fail anything.
- `de check` green, 9 of 9.
