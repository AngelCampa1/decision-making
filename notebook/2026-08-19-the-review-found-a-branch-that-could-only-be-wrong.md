# The review found a branch that could only be wrong

**2026-08-19.** An adversarial pass over the publishing change that landed as
`8e14a5f` and `619e68c`. Two sub-agents, one on the code and one on the prose,
each briefed to break it rather than approve it. They returned ten and thirteen
findings; this entry records what was confirmed, what was fixed, and the one
defect that neither of them found.

## What the code reviewer confirmed by mutation

Two of its findings came with the mutation already run, which is the only form
of "this test does not test that" worth acting on without re-deriving it.

- **The provenance writer's environment was untested.** `payload()` reads
  `RUN_URL` with `os.environ[...]`, and GitHub does not define it — the workflow
  step does. Deleting both `env:` lines left all 23 tests in `test_workflow.py`
  passing, because the contract test sets the variables itself with
  `monkeypatch` before building the payload. A deploy would have raised
  `KeyError` on the runner. Now derived from the writer's own source: every
  non-`GITHUB_*` key it reads must appear in the step's `env:`.
- **The concurrency group was checked by prefix and by substring, never
  whole.** `pages-${{ github.ref }}-${{ github.run_id }}` satisfies
  `startswith("pages")` and `"github.ref" in group` while meaning the opposite of
  what both assertions were for: a group containing the run id is unique per
  run, so nothing queues and two pushes race exactly as before. Pinned exactly.

Both mutations were re-run here after the fix and both now fail the way they
should. A third was added for the empty-build refusal in the writer, which had
gone in earlier the same day with no test behind it.

## The defect nobody reported

`fetch_provenance` cache-busts the URL and then refuses a redirect by comparing
what came back against what was asked for:

```python
if response.geturl().split("?")[0] != url:
```

The response's query is stripped; the caller's is not. For
`PROVENANCE_URL` — which has no query — that compares equal and the check works.
For any URL that already carries one, it compares `http://x` against
`http://x?a=1` and reports a redirect that did not happen, every time. The
function's own `separator = "&" if "?" in url else "?"` branch exists solely to
build a request down that path, so taking it guaranteed a wrong answer.

**This is the standing rule about estimators, arriving somewhere the rule was
not looking.** It is usually written about a measurement that cannot come back
non-zero. This is a *refusal* that cannot come back correct: the branch runs,
returns, and is wrong on every input that reaches it. Neither reviewer found it,
and neither did the test suite, because every existing test passes a URL with no
query string. It was found by writing the test for the branch — which is the
same lesson as the four before it, and the reason the fix is a comparison of two
stripped URLs rather than a deleted branch.

## Prose that had stopped being true

The publishing change was written the day the CI workflow was, and both
documents describing it were already stale by evening.

- `README.md` and `AGENTS.md` both said the `check` workflow "has not run yet".
  It had run three times: red on `018269b`, red on `76cdfb0`, green on
  `ada7b4a`. Both now say what happened instead, which is a better argument for
  the workflow than the claim they replaced.
- `AGENTS.md` said the last *three* steps of Landing the work are the ones
  nothing can check. `docs/AUTONOMOUS_WORK_ORDER.md` says two, and the work
  order is right: deploying stopped being a thing somebody remembers on
  2026-08-19, and `de deployed` answers it.
- `README.md`'s "Several of its steps check the method rather than the code" had
  lost its antecedent — two paragraphs about deploying went in above it, so
  "its" resolved to `de deployed`, a command with no steps.

## What the work order was missing

Step 9 confirms the *deploy* run and says nothing about the *check* run that the
same push starts. Given that the first such run went red on a tree whose local
gate was green, that was the most expensive omission in the section. It now
names both, with the command to block on the second, and states the gap rather
than papering over it: the two workflows do not gate each other, so the live
site can be serving a build of a commit `check` rejects. Chaining them would
trade a visible gap for a silent one.

## Not fixed, and why

`.github/workflows/check.yml` installs `@anthropic-ai/claude-code` from npm
unpinned, because the plugin-validation step shells out to it and
`test_a_missing_cli_fails_the_gate` deliberately pins that its absence is a
failure rather than a skip. Pinning the version trades a supply-chain surface
for a gate that goes stale silently, and that is the file's author's call rather
than this pass's. Recorded here rather than dropped.

## Addendum: a band over a coin toss

Pushing this branch was refused by `pre-push` on
`test_an_abort_keeps_the_calls_it_already_paid_for` — a test in the runner suite
that nothing in this change touches. It passed 5 of 5 times on its own and 3 of
3 times running its whole file, and failed twice under the load of a full
`de check`. That test had already been widened once the same day, after CI
returned `[5, 5, 5, 5, 5, 0, 5, 5]`, to allow `{0, len(items) - 1}`.

**My first diagnosis was wrong and is recorded here because it was.** The helper
chose its one failing call with `if not first.is_set(): first.set()`, a check and
a set rather than one step, with every thread released from a barrier at the same
instant. Two threads reading the flag before either wrote it would raise twice
and lose a success. I fixed it with a lock and moved on.

Then I measured it: 4000 trials of the bare pattern, then 120 trials of the real
experiment through `run_arm`, old helper and new, counting both survivors and
raisers.

| | raisers | survivors |
|---|---|---|
| check-then-set | `{1: 120}` | `{0: 119, 1: 1}` |
| locked | `{1: 120}` | `{0: 119, 5: 1}` |

**Exactly one call raised, every time, in both arms.** The race is real in
principle and was not the cause of anything. The lock fixed nothing.

The actual mechanism is in `run_arm`: it waits with `FIRST_COMPLETED`, so the
returned set holds whatever had finished *by then*. How many successes share a
batch with the failure is a timing property of the machine, not a property of the
drain — and 119 of 120 trials kept nothing at all, because the failure usually
arrives alone. No assertion over a survivor count can be true of that. The
`{0, n - 1}` band was not too strong or too weak; it was a band over a coin toss,
and both it and the `len(set(...)) == 1` before it were the same mistake
twice.

So the batch is now made whole by construction — `wait` is patched to
`ALL_COMPLETED` for that test — and the assertion is `[len(items) - 1] * 8`,
every trial, no band. Ten consecutive runs pass. Reintroducing the defect
(`raise` instead of `failure = failure or exc; continue`) fails it three times
out of three, with survivor counts `[4, 3, 4, 0, 3, 5, 2, 1]`,
`[2, 5, 3, 4, 2, 2, 2, 3]`, `[2, 5, 3, 4, 2, 2, 2, 4]` — the set-iteration-order
spread the test docstring has described from the beginning, and note that the
old band would have accepted the `0`s and `5`s in it.

**This is the estimator rule again, in its third costume today.** The first was a
refusal that could not return correct. The second was the same shape in a test:
an assertion whose subject was noise, so it could not fail *for the reason it
named*. It failed for load. The rule as written asks whether some possible
response would score above zero; the question it is really asking is whether the
thing being measured is the thing the sentence is about.
