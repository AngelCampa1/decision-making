# The checklist ticked a function nothing calls

**2026-08-14.** An audit of `paper/CHECKLIST.md` against the repository, on the
file's own rule: `[x]` means the artifact exists and is committed, never that
it is intended. Twenty ticked boxes, checked one at a time rather than
spot-checked.

## The finding that prompted it, confirmed

`- [x] Multiplicity controlled across pre-registered primaries (BH, q = 0.10)`.
`decision_evals.stats.multiplicity.benjamini_hochberg` exists, is exported from
`stats/__init__.py`, is covered at 100% line and branch, and is property-tested.
Grepping every `.py` outside `stats/` and `tests/` for `benjamini_hochberg`,
`BenjaminiHochberg`, or `multiplicity` returns nothing. Confirmed independently:
implemented, never called.

This is the third occurrence of the shape `docs/AUTONOMOUS_WORK_ORDER.md`
already names twice — `triggers` tested to 100% and called by nothing,
`prereg.py` carrying every refusal `PROTOCOL.md` §3 promised while nothing
calls it.

## Why the existing `[tool.decision-evals.unwired]` register cannot record this one

The brief suggested declaring `benjamini_hochberg` unwired under
`[tool.decision-evals.unwired]`, the mechanism that already exists for exactly
this class of gap. Tested it directly against `decision_evals.wiring` rather
than assuming:

```
>>> reachable_modules(root)  # decision_evals.stats.multiplicity
True
```

`stats/multiplicity.py` **is** import-reachable — `stats/__init__.py` imports
it, and `cli.py` imports `stats`. Simulating the registration:

```
>>> declared = {"decision_evals.stats.multiplicity": "..."}
>>> "decision_evals.stats.multiplicity" in reachable and in declared
True
```

`check_wiring` treats any declared-and-reachable entry as an error — *"is
declared unwired but is now reachable. Delete the entry"* — so registering it
would make `de check` fail on exactly the entry meant to explain the gap.

**The register is calibrated to import-reachability, not call-reachability,
and those are different claims.** `stats/multiplicity.py` is reached because
Python imports the whole module graph eagerly; nothing about that import
proves `benjamini_hochberg` the function is ever invoked. The gate's own
docstring says as much in the abstract ("module... reachable by import") but
the concrete failure here is the first case where reachable-by-import and
actually-used come apart in a way the tooling cannot see.

## What I did instead

Not: force a caller into existence (would be manufacturing a consumer for
data — a family of pre-registered primaries — that does not exist yet, which
is the mirror image of ticking a box on intention). Not: register it as
unwired (mechanically wrong per above). Instead: corrected the checklist box
to `[ ]` with the actual state — implemented, tested, unused — and left
`multiplicity.py` and its tests untouched.

## The wiring gate's blind spot, argued both ways

**Worth closing:** the gate exists precisely to prevent a floored,
100%-covered module from being inert, and it just missed one.

**Not worth closing today:** a call-reachability checker over Python is a
different and much harder problem than the static import graph
`decision_evals.wiring` already does well. `benjamini_hochberg` is called
nowhere in production, but plenty of legitimate library functions in
`stats/__init__.py`'s `__all__` are exported for callers this repository does
not have yet, or are called only via test fixtures, `getattr` dispatch in
scorers, or CLI option wiring the AST walk does not follow. A checker built to
catch this one case without a false-positive budget would either flag half the
public API of `stats` or need a maintained allowlist that decays exactly like
the doc-scope registers this repository has already had to build twice.
Recommendation: leave `decision_evals.wiring` as import-reachability, and treat
"exported but never called" as something a periodic audit like this one
catches — which is what just happened — rather than something a gate blocks
every commit on.

## The corpus battery does not need BH, and someone had already shown why

`notebook/2026-08-14-the-battery-searches-176-cells-and-nobody-had-costed-that.md`,
written earlier the same day, computed that the shortcut battery's family is
176 band × view × feature cells and its fixed `MATCHED_Z = 3.0` is p = 0.0027
two-sided, giving ≈0.47 expected false findings across the whole family —
approximately FDR-safe by construction, independent of Benjamini-Hochberg. I
did not recompute this; I read it, checked the arithmetic (176 × 0.0027 =
0.4752), and cited it. What `benjamini_hochberg` was actually built for —
*"pre-registered primaries"*, plural skill-level hypotheses from a confirmation
run — has never run at all. Conflating the two would have been the wrong fix:
wiring BH into the battery just to give it a caller corrects a family that
does not need correcting and leaves the family it does need correcting
(un-run) uncorrected.

## Other corrections made

- `CC-BY-4.0 intended for the paper` was ticked alongside `Apache-2.0 for
  code` in one box. Apache-2.0 has a committed `LICENSE` file; CC-BY-4.0 has
  no committed artifact anywhere — no `paper/LICENSE`, no notice in
  `paper/main.tex` or `paper/refs.bib`. Split into two boxes; the code half
  stays `[x]`, the paper half is now `[ ]`.
- `property tests pinning it against scipy and statsmodels` — checked. McNemar
  is pinned against `scipy.stats.binomtest`
  (`test_matches_scipy_binomtest_on_discordant_pairs`). No test pins anything
  against `statsmodels`: `benjamini_hochberg` **is** a `statsmodels` call, and
  the test that used to compare a from-scratch step-up implementation against
  `statsmodels` was deliberately deleted, with a comment explaining that
  asserting statsmodels equals itself proves nothing. Grepped `statsmodels`
  across `evals/src/decision_evals/` — it appears only in `multiplicity.py`.
  Reworded rather than unticked, since 100% coverage and the scipy pin are
  both real.

## Boxes checked and left unchanged, with the evidence

| Claim | Verdict | Evidence |
|---|---|---|
| Limitations written before results existed | holds | `docs/LIMITATIONS.md` first committed `9097a60` (2026-08-10T18:22), first `results/` commit `4ac3638` (2026-08-10T20:41); `git merge-base --is-ancestor` confirms ancestry |
| Standing protocol versioned and public | holds | `docs/PROTOCOL.md` line 3: "Version 1." |
| Control/placebo/plain-CoT arms specified | holds | `docs/PROTOCOL.md` arm table and beats-placebo/beats-plain-CoT rows |
| Response-format contract common to every arm | holds | `docs/PROTOCOL.md`: "The response-format contract appears in every arm" |
| Option menus held constant | holds | `docs/PROTOCOL.md`: "Any option menus are held constant across arms" |
| McNemar exact + paired permutation | holds | `stats/paired.py`: `mcnemar_exact`, `paired_permutation_test` |
| Cluster bootstrap over templates, not items | holds | `stats/cluster.py` docstring and generic cluster-label API |
| CLT deliberately avoided, reason recorded | holds | `stats/__init__.py` docstring cites arXiv:2503.01747 |
| Guards left uncorrected by design, asymmetry stated | holds | `stats/multiplicity.py` docstring lines 12–15 — a documentation claim, true regardless of BH's caller status |
| 100% line+branch coverage on `stats/` | holds, measured today | `pytest tests/unit tests/property tests/golden --cov=decision_evals.stats` → `659 stmts, 0 miss, 220 branch, 0 miss, 100%` (excluding the two corpus/site tests currently mid-edit by another session) |
| Eval-set datasheet exists | holds | `docs/EVAL_SET_DATASHEET.md` |
| Ground truth from template rules, never authored | holds | `docs/EVAL_SET_DATASHEET.md`: "computed, never authored" |
| Golden-file generator tests + bless step | holds | `tests/golden/test_generator_golden.py`, `--bless` |
| Code public from first commit | holds | `gh api repos/AngelCampa1/decision-making-skills` → `"private": false`, `created_at` 2026-08-10T23:16, matching the first local commits |
| Dependencies pinned via `uv` lockfile | holds | `uv.lock` present, 125 pinned packages |
| Full `de check` runs lint/types/tests/coverage | holds | `cli.py check()`: ruff check, ruff format, mypy, then (non-`--fast`) pytest with coverage + `check_coverage_floors.py` |
| ETCSOVG disclosure documented | holds | `docs/HARNESS_DISCLOSURE.md` |
| Sampling-parameter absence stated | holds | present in both `docs/HARNESS_DISCLOSURE.md` and `docs/LIMITATIONS.md` |

Also spot-checked two `[ ]` boxes that could plausibly have flipped true and
had not: the isolation canary (`tests/integration/test_isolation.py` exists
and is well-built — positive control included — but is `DE_INTEGRATION=1`-gated,
excluded from `de check`, and there is no record of it having been run and
passed, so `[ ]` is correct) and per-run `config.json` (exists for exactly one
directory, `results/evidence-ledger/2026-08-10-baseline-corpus/`, not for the
trigger runs or the decision-making arm runs, so "committed with results" as a
general claim is correctly `[ ]`).

## What I am not claiming

I have not proven the paper text (`paper/sections/*.tex`) doesn't separately
misstate any of this — the audit scope given was the checklist against the
repository, not the checklist against the paper draft. That is a narrower and
different check and is not done here.

## Commit

`paper/CHECKLIST.md` edited: three boxes corrected (multiplicity unticked and
explained, the scipy/statsmodels pin reworded, the license box split).
`de check` (full, not `--fast`) run before commit.
