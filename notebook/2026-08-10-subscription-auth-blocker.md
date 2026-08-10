# 2026-08-10 — The subscription-auth premise fails its first test

## What happened

The spike's first action was the cheapest possible smoke test: run the full
isolation flag stack against Haiku and check that a nested `claude -p` returns a
number.

```
{"is_error":true,"api_error_status":401,
 "result":"Failed to authenticate. API Error: 401 OAuth access token has been revoked."}
```

Then, to find which flag broke it, the same call with every flag removed:

```
claude -p "Say OK" --model haiku --output-format json
→ 401 OAuth access token has been revoked
```

So it is not the isolation flags. It is the credential.

## Diagnosis

`claude auth status` reports `loggedIn: true`, `authMethod: "claude.ai"`,
`subscriptionType: "max"`. The CLI believes it is authenticated. The server
disagrees.

Two hypotheses, tested in order:

1. **The nested-session environment is interfering.** The host sets a large
   number of `CLAUDE_CODE_*` variables, including
   `CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH` and `CLAUDE_CODE_SDK_HAS_OAUTH_REFRESH`
   — names that strongly suggest the host process holds the live token in memory
   and refreshes it itself, rather than the child reading it from disk.
   `ANTHROPIC_BASE_URL` is also set and inherited.
   **Tested:** re-ran with all of those stripped, including `ANTHROPIC_BASE_URL`.
   Identical 401. **Rejected.**
2. **The on-disk credential is genuinely revoked.** The status output is read
   from local state, not validated against the server, so `loggedIn: true` only
   means a credential file exists. The most likely cause is token rotation: a
   newer login elsewhere superseded this one, and the CLI's stored access token
   was revoked rather than merely expiring. "Revoked" is the server's word, and
   it is not the word you get for an expired token that a refresh would fix.
   **Consistent with all evidence.**

The fix is `claude auth login`, which is an interactive OAuth flow and belongs to
the account holder, not to this session.

## Why this is worth a notebook entry rather than a bug report

Architecture decision D1 — *drive Claude Code itself, no API keys* — rests on an
assumption I never wrote down as an assumption: **that a subscription-authed CLI
can be invoked as a subprocess and will authenticate.** That is not a property of
the design, it is a property of the credential store, and it is now demonstrably
capable of being false while every visible indicator says otherwise.

That matters beyond today's outage, for two reasons.

**It is a reproducibility hazard for anyone replicating this work.** The paper's
first claimed contribution is a harness reproducible on a consumer subscription
with no API key. A replicator whose token has silently rotated gets a 401 from a
CLI that reports itself logged in. That needs to be in
`docs/HARNESS_DISCLOSURE.md` as a named precondition with the exact check, not
discovered by each person independently.

**It is a silent-failure risk mid-run.** A confirmation run is checkpointed and
resumable across days because rate limits, not dollars, are the budget. If a
token rotates between sessions, the runner must fail loudly at item 1 rather than
recording a few hundred authentication errors as model failures. Every zero score
gets classified as agent failure / verifier defect / environment leak /
infrastructure error, and this is exactly the fourth category — but only if the
runner is built to notice. A preflight auth check that makes one throwaway call
and aborts the run on 401 is now a requirement, not a nicety.

## What this does not change

Nothing about the design is invalidated. The flag stack was never exercised, so
it is neither confirmed nor refuted; the isolation guards, the arena separation,
and the statistics are all untouched. This is a credential outage, not a
falsification.

It does mean the empirical half of the spike — `inspect_swe`'s `claude_code()`
solver versus a custom provider shelling to `claude -p` — cannot be settled
today. The packaging question (does `inspect-swe` install, what does it expose)
does not need auth and proceeds.

## Recorded prediction

Unchanged from
[`2026-08-10-harness-backend-selection.md`](2026-08-10-harness-backend-selection.md):
`inspect_swe` works, but its sandbox requirement makes it awkward for a
subscription-auth setup and the custom provider wins anyway.

**New prediction, recorded now so it cannot be retrofitted:** once auth is
restored, the flag stack works as designed and the isolation canary passes on the
first attempt. The flags are individually documented and independently verified in
`claude --help`; the risk was always the auth path, which is precisely the part
that just broke. If the canary *fails* — if a planted `CLAUDE.md` is followed
despite a scratch cwd outside `D:\code` — that is a much more serious finding
than today's, because it would mean the isolation is not achievable with the
flags the CLI exposes.

## Action items

- [ ] `claude auth login` — account holder's action, blocks all LLM runs
- [ ] Preflight auth check in the runner: one throwaway call, abort the run on
      401 rather than scoring the failures
- [ ] Name the precondition in `docs/HARNESS_DISCLOSURE.md`, with the observation
      that `claude auth status` reporting `loggedIn: true` is not evidence of a
      working credential
- [ ] Add `authentication` as an explicit subtype of the infrastructure-error
      category in the zero-score triage
