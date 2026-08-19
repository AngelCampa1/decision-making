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

1. The first `workflow_dispatch` from `site/pages-deploy` builds green and the
   `deploy` job is **skipped**, because it is gated on `refs/heads/main`. If it
   instead *runs* and fails, the `if:` is wrong.
2. After Pages is flipped to `build_type: workflow`, the first push to `main`
   deploys green and `de deployed` exits 0.
3. The live site does not 404 at any point in the switchover, because GitHub
   keeps serving the last deployment until a new one supersedes it. **This is
   the prediction I am least sure of** — I have not verified that GitHub
   continues serving a legacy branch deployment after the source is changed to
   Actions, and if it does not, there is a window between the flip and the first
   successful Actions run where the site is unavailable. The rollback if so is
   to flip the source back to `gh-pages`, which is why the branch is not deleted
   until after a verified deploy.
4. `de deployed` reports *behind* rather than *current* if run within a minute
   or two of a merge, because Pages sits behind a CDN. If that never happens,
   the cache TTL is shorter than I think.

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
