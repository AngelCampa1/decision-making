# 2026-08-19 — Publishing was a thing somebody had to remember, and twice in one morning nobody did

`de site --deploy` force-pushed whatever local `HEAD` happened to be to a
`gh-pages` branch, and nothing checked that it had ever run. Both halves of that
failed today, before this change was written:

- **11:38.** A build of `91f2313` was published to the local `gh-pages` branch.
  That commit is a work-in-progress commit on `site/instrument-redesign` and is
  not on `main`. It was caught and replaced by hand nine minutes later, by
  `d912c4c`; the correcting commit on `main` is titled *"site: the manifest
  described a different branch's tree"*. It never reached the remote, and only
  because somebody looked.
- **12:29.** `origin/gh-pages` held a build of `bd86e86` while `origin/main` was
  at `f01d325`: 43 minutes and one commit behind, with nothing anywhere saying
  so.

Earlier in the same week the gap had turned out to be wider still. Pages was
configured `source: {branch: main, path: /docs}`, so for six days the served
site was a hand-written `docs/index.html` that nothing in this repository had
ever touched, while `de site --deploy` printed *published* and the site gate
reported the manifest current. Both were true. Neither asks what the host
serves.

## What changed

`.github/workflows/deploy-site.yml` builds and deploys on push to `main`,
through first-party actions only. The `--deploy` flag, the `ghp-import`
dependency and the `docs` dependency group are gone, and the `gh-pages` branch
is retired. Publishing is now a function of `main` rather than of a person.

`de deployed` is the evidence half, and it is a separate thing from the fix. The
workflow can be green while the site is stale: a run can be dropped by the
concurrency group, the Pages source can be pointed elsewhere, a deployment can
be rolled back in the web UI. So the deploy writes `deploy-provenance.json` into
the tree it uploads, and `de deployed` reads it back over HTTPS from the live
URL. That is the only reading that asks what visitors actually get, which is the
lesson of the six-day failure above.

It exits 2 when it cannot tell, which is deliberately not 0. A verification
command that exits 0 on a timeout would be this repository's own thesis
inverted in one line.

It is **not** a `de check` step, and that is a choice rather than an oversight.
The gate is offline and deterministic by design; a step that can fail because a
CDN is slow is a step people learn to ignore.

## Three things checked rather than assumed

Each of these would have shipped a broken or subtly wrong workflow, and each was
wrong in my first draft:

1. `actions/upload-pages-artifact` tars with `--exclude=.[^/]*` unless
   `include-hidden-files` is set. Read from its `action.yml`, not assumed. It
   would have silently dropped `dist/.nojekyll`.
2. `configure-pages`'s `static_site_generator` input accepts only `nuxt`,
   `next`, `gatsby` and `sveltekit`. Astro is not a value it takes. `site` and
   `base` are already committed in `astro.config.mjs`, and injecting them from
   the runner is how a deployed base path comes to disagree with the config.
3. The current action majors are `checkout@v7`, `setup-node@v7`,
   `configure-pages@v6`, `upload-pages-artifact@v5`, `deploy-pages@v5`. My first
   draft used `v4`/`v3`. A sub-agent reported five of these and got
   `configure-pages` wrong (it said v5); the API said v6. That is the standing
   rule about not believing one agent's result working exactly as intended.

## What nothing here checks

The documentation gate cannot see any of the prose corrections this change
required. `docs._COMMAND` is `\bde\s+([a-z][a-z0-9-]*)`, so every stale
`de site --deploy` parses as `site`, which still exists and still resolves.
Every one of the doc edits was a hand edit, and a missed one would have stayed
green. That is the same shape as the failure the gate was built for, arriving
through the door the gate leaves open.

## Predictions, written before the switchover

The switchover has not happened as this is written. Recorded now so the outcome
can be read against it rather than after:

1. ~~The first `workflow_dispatch` from `site/pages-deploy` builds green and the
   `deploy` job is skipped, because it is gated on `refs/heads/main`.~~
   **Wrong, and found before it ran rather than after.** A workflow cannot be
   dispatched at all until it exists on the *default* branch. Checked, not
   reasoned about: `gh workflow run "Deploy site" --ref site/pages-deploy` →
   *could not find any workflows named Deploy site*, and `gh workflow list
   --all` shows only the legacy `pages-build-deployment`.

   So the plan's "prove the workflow from a branch before merging" step does not
   exist for a *new* workflow. The `if: github.ref == 'refs/heads/main'` guard
   is not useless — it is what makes every *future* change to this workflow
   testable from a branch — but it buys nothing for this switchover, and I had
   written the plan as though it did.
2. Therefore the order is: **merge first**, accept one red run, then flip. The
   merge's push runs the workflow; `build` succeeds and `deploy` **fails**,
   because Pages is still `build_type: legacy`. That red run is expected and is
   recorded here so the next reader does not diagnose a broken workflow. The
   live site is untouched throughout, still served from `gh-pages`.

   Merging first rather than flipping first is deliberate: it proves the build,
   the provenance writer and the artifact upload all work while the site is
   still being served by the old path. Flipping first would put the unknown and
   the outage in the same step.
3. After the flip, re-running the failed run deploys green and `de deployed`
   exits 0.
4. There is a window between the flip and that first successful run where the
   site may 404, and I could not close it. **I have not verified whether GitHub
   keeps serving a legacy branch deployment after the source is switched to
   Actions.** If it does, there is no outage; if it does not, the site is down
   for the length of one build, roughly two minutes. The rollback is to flip the
   source back to `gh-pages`, which is why that branch is not deleted until
   after a verified deploy.
5. `de deployed` reports *behind* rather than *current* if run within a minute
   or two of a merge, because Pages sits behind a CDN. If that never happens,
   the cache TTL is shorter than I think.
6. Between the merge and the flip, `de deployed` exits **2**, not 1 — the
   gh-pages-served site has no `deploy-provenance.json` at all, so the fetch
   404s. Honest, and the right code, but worth predicting so it is not read as a
   bug.

## A measure that was removed before it ever ran

The first version of `de deployed` took a second verdict from
`build_manifest_sha256`: if the live site was built from the right commit but
against a different `site/build-manifest.json`, it reported *behind*. Writing
the paragraph above is what exposed it, and it was wrong in both directions at
once.

Compared against the **working tree**, it fires whenever the checkout is not
sitting exactly on the deployed commit. Checked rather than argued: in this
worktree, on the branch that adds the feature, the working-tree manifest and the
one committed at `HEAD` already disagreed, because the tree had been rebuilt
after the commit. It would have reported drift on a site that was perfectly
current, nearly every time it was run.

Compared against the manifest **in the deployed commit**, it can never disagree,
because that is the file the workflow hashed. That is an estimator with no
non-zero outcome, which this repository has a standing rule against shipping and
has already been caught by twice.

There is no third option, because the commit SHA already determines the tree.
So the field stays in `deploy-provenance.json`, where it is worth having when a
human is working out what happened, and no verdict is taken from it. The
reasoning is in `manifest_digest`'s docstring and pinned by
`test_a_differing_manifest_is_not_reported_as_drift`, so that restoring the
comparison later reads as a reversal rather than an improvement.

The general form, which is the part worth keeping: **a second signal that agrees
with the first by construction is not corroboration.** It felt like defence in
depth and was arithmetic.

## What the adversarial review found

Dispatched against the finished branch with a brief to break it. It re-derived
the manifest defect above independently, which is the confirmation rule working
rather than a coincidence, and found eight things I had not:

- **A comment describing a mechanism that does not run.** The workflow claimed
  `configure-pages` would fail clearly if Pages were not workflow-sourced. Read
  from the action's source: with `enablement` at its default of `false` it
  fetches the existing site and returns it without inspecting `build_type`. The
  failure actually arrives later, at `deploy-pages`, in the other job —
  precisely the "confusing one further down" the comment claimed to prevent.
  This is the repository's own named defect class, committed in a comment about
  a gate, three commits after the rule was restated.
- **`_distance` could print "0 commit(s) behind"** beside a verdict of *behind*,
  if `main` were ever force-pushed backwards. `rev-list --count A..B` answers
  "commits on B not on A", which is "how far behind" only when A is an ancestor
  of B. Ancestry is checked first now.
- **`_git` had no timeout**, so the module's stated promise that "an unreachable
  host is an answer rather than a hang" covered only the HTTP half. `ls-remote`
  is a network call too. `GIT_TERMINAL_PROMPT=0` went in beside it, because on
  this machine the credential helper can raise a GUI prompt at a process nobody
  is watching.
- **The concurrency group was fixed at `pages`**, so a build-only dispatch from
  a branch shared a slot with real deployments and could cancel a queued `main`
  deploy. Keyed on the ref now.
- **Four tests that could not fail.** Nothing asserted the site was built at
  all, or that `npm` ran in `site/`, or that the provenance step ran before the
  upload and without a `working-directory` of its own. `test_the_deploy_flag_is_gone`
  asserted only a non-zero exit, which any breakage of `de site` satisfies.

The two it raised that I have not acted on, recorded rather than quietly
dropped: the test that greps the writer for a literal path string is
refactor-brittle, and `README.md` briefly leads reality between the merge and
the Pages flip. The second is bounded by prediction 2 above.
