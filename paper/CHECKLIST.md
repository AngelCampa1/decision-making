# Reproducibility checklist

NeurIPS-style, filled in as the work happens rather than the week before
submission. `[x]` means the artifact exists and is committed; `[ ]` means it does
not. A box is never ticked on the strength of an intention.

Kept in the repository rather than only in the paper so the gap between what is
claimed and what exists is visible at every commit.

## Claims

- [ ] Every claim in the abstract and introduction is supported by a numbered
      result or a citation
- [ ] The scope of the claims matches the experiments: one harness, one model
      family, tasks with computable ground truth
- [ ] Limitations are stated in the paper, not only in the repository
      — source: [`../docs/LIMITATIONS.md`](../docs/LIMITATIONS.md)
- [x] Limitations were written *before* results existed, so they cannot be
      tuned to flatter them

## Experimental design

- [x] Standing protocol is versioned and public
      — [`../docs/PROTOCOL.md`](../docs/PROTOCOL.md) v1
- [ ] Hypotheses pre-registered before the confirmation run
- [ ] Pre-registration commits are ancestors of the result commits, verifiably
- [ ] Skill body and analysis script hashes locked in the pre-registration
- [ ] Stopping rule fixed in advance; no interim analysis
- [x] Control arm, placebo arm, and plain-CoT arm all specified
- [x] Response-format contract specified as common to every arm
- [x] Option menus held constant across arms

## Statistics

- [x] Test chosen for the data type: McNemar exact (paired binary), paired
      permutation (continuous)
- [x] Intervals from a cluster bootstrap over templates, not items
- [x] CLT deliberately avoided at this N, with the reason recorded
- [x] Multiplicity controlled across pre-registered primaries (BH, q = 0.10)
- [x] Guards left uncorrected by design, with the asymmetry stated
- [ ] Raw p and adjusted q both reported for every primary
- [ ] Effect sizes reported with intervals, never p-values alone
- [ ] Underpowered comparisons reported as `UNTESTED` with their MDE, not as
      nulls
- [x] Statistical code covered at 100% line and branch, with property tests
      pinning it against `scipy` and `statsmodels`
- [ ] Coverage simulation: 1,000 simulated clustered datasets with known Δ,
      empirical 95% CI coverage in [0.93, 0.97]

## Data

- [ ] Eval-set datasheet — `../docs/EVAL_SET_DATASHEET.md`
- [x] Ground truth computed from template rules, never authored
- [ ] Template schema published in full
- [ ] Distractor audit procedure and attrition rate reported
- [ ] Difficulty gates run on the control arm only, and stated as such
- [ ] Public/screen split committed
- [ ] Holdout seed published after the verdict
- [x] Generator output pinned by golden-file tests; regeneration requires an
      explicit bless step so the diff reaches review

## Code and environment

- [x] Code public from the first commit
      — `github.com/AngelCampa1/decision-making`
- [x] Apache-2.0 for code; CC-BY-4.0 intended for the paper
- [x] Dependencies pinned via `uv` lockfile
- [x] Full local gate (`de check`) runs lint, types, tests, coverage floors
- [ ] Zenodo DOI minted for the code and data release
- [ ] Exact CLI version and resolved model id recorded per run

## Harness

- [x] ETCSOVG disclosure documented
      — [`../docs/HARNESS_DISCLOSURE.md`](../docs/HARNESS_DISCLOSURE.md)
- [ ] Per-run `config.json` written and committed with results
- [ ] Isolation canary test passing (planted `CLAUDE.md` not followed)
- [ ] ≥2 independent runs per cell, with variance reported
- [ ] Arms interleaved per item, not run in blocks
- [x] Absence of sampling-parameter control stated rather than worked around

## Reporting

- [ ] Exact prompt text published for every arm
- [ ] Full transcripts published, not scores alone
- [ ] Placebo text published with its token count beside the skill's
- [ ] Every evaluated `SKILL.md` published at its pre-registered hash
- [ ] Means reported with p90 and p99
- [ ] Negative results reported at the same prominence as positive ones
- [ ] Figures generated from `results/` by `make paper`, never transcribed
- [ ] `de report --check` passes: committed scorecard matches the results

## Submission logistics

- [ ] arXiv endorsement for `cs.AI`/`cs.CL` confirmed — **check early, it can
      take weeks**
- [ ] `\draftmode` switched off, so `\TODO` expands to nothing
- [ ] All `% VERIFY` author lists in `refs.bib` checked against the PDFs
- [ ] Author, affiliation, and contact match the repository identity
      (Angel Campa, `AngelCampa1`)
- [ ] No `@ventoralabs.com` address anywhere in the source, PDF metadata, or
      commit history
