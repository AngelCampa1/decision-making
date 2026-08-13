---
name: Dispute a result
about: A published number looks wrong, or the measurement behind it does not measure what it claims
title: "result: "
labels: measurement
---

Eight measurements have already been caught being broken here, and **every one
produced a clean run, a full checkpoint and a plausible number.** None crashed.
So this template exists because the failure mode is real and quiet.
[`docs/STATUS.md`](../../docs/STATUS.md) has the table.

## Which run

The directory under `results/`, or the notebook entry.

## What you think is wrong

## Which shape it is, if you know

- [ ] The estimator could not have returned a non-zero value for that arm
- [ ] The scorer reads a different object in different arms
- [ ] A rate is quoted without its denominator
- [ ] The comparison spans two answer-key versions
- [ ] The corpus admits a shortcut that solves it without the model
- [ ] Something else

## What would settle it

The check that would show you right or wrong. If it can be run without model
calls, say so — that is cheap and can happen immediately.
