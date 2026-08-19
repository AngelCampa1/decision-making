## What this changes

## Why

<!--
No CI gates this repository. `de check` is the only thing between a mistake and the
published record, so the checklist below is the review.
-->

## Checklist

- [ ] `uv run de check` passes — the full gate, not `--fast`
- [ ] Commits are attributed to the GitHub noreply address
- [ ] If this touches `datasets/triggers/` or `skills/`, there is an entry in
      [`docs/DECISIONS.md`](../docs/DECISIONS.md) naming these commits
- [ ] If this changes a skill, `de mirror` was run and the mirrors agree
- [ ] If this regenerates a golden file, it was done with `pytest --bless` and
      the diff is in this PR
- [ ] If this publishes a run, its README states the answer-key version and
      names a prediction committed *before* the run, and `de index` was run
- [ ] If this adds a notebook entry, it is dated and appended — no existing
      entry was edited

## If this adds or changes a measurement

- [ ] What is computed, from which records, over which denominator, by which
      function — written down before the run
- [ ] Some possible response would have scored above zero for every arm
- [ ] The scorer reads the same object in every arm
