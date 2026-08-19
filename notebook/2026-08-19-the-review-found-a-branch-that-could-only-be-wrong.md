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
