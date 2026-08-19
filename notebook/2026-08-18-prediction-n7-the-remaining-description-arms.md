# 2026-08-18 — prediction: N7, the remaining description arms on v4

Registered **before the first call**, and committed before the run is launched
rather than while it runs — which is the specific thing
[N5's write-up](2026-08-18-n5-the-probe-ran-and-the-headline-prediction-was-wrong.md)
recorded against me four hours ago.

## What runs

Three arms — **`no-exclusions`, `no-opener`, `stakes-named`** — × 258 items × 2
repeats = **1,548 calls**, `haiku`, answer key **v4**. These are the
`--description` variants N6 did not run. Together with N6's `full`,
`stakes-shown` and `opener-only`, all six description arms will have been
measured on a corpus whose trivial-feature ceiling is 0.7054 rather than 0.890.

**Descriptive, as the programme row says.** No arm is being promoted and no band
retires anything. The predictions below exist so that a null is a result.

## What will be computed, from which records, over which denominator

- **Per arm:** `trigger_arms.summarise` over 516 parsed records — accuracy,
  precision, recall, FPR, item-weighted and record-weighted (identical under
  balanced repeats).
- **By band:** FPR and accuracy per `s`/`m`/`l`/`xl`, because N6's most useful
  finding was that a pooled FPR hid a single band coming apart.
- **Against N6:** `label_versions_comparable` and `models_comparable` must both
  return `None` before any cross-arm subtraction. Same key, same tier.
- **Not computed:** no `bootstrap_rate_difference` band is registered here and
  no p-value is offered. Six arms compared pairwise is fifteen comparisons and
  this run has no multiplicity control.

## Predictions

1. **`no-exclusions` has a higher FPR than `full`'s 0.0785.** L5 measured the
   exclusion clause at −5.8pp of false firing on v2; deleting it should cost
   precision. Direction registered, magnitude not.
2. **`no-opener` has a lower recall than `full`'s 0.9651.** The opener is the
   clause that says what the skill is for.
3. **`stakes-named` has a lower recall than `stakes-shown`'s 0.9942.** L7 found
   `stakes-named` refusing positives `stakes-shown` accepts — `x-n03` at 0/2
   against 2/2 — and read it as naming a criterion making the model apply it
   strictly. v4 is a different corpus; the mechanism should carry if it was a
   mechanism.
4. **`no-exclusions`' false firing concentrates in `l` and `xl`**, not spread
   evenly. Every arm N6 measured put its false positives in the long bands, and
   `opener-only` put more than half of `l`-band negatives wrong while `m` stayed
   at 0.104.
5. **The headline, and the one worth being wrong about: no arm beats both
   `stakes-shown`'s recall (0.9942) and `full`'s FPR (0.0785).** L7's band 4 —
   one arm at FPR ≤ 0.06 *and* recall ≥ 0.94 — failed on v2/v3, and its
   conclusion was that a description moves *where on the frontier* the skill
   sits, not the frontier. **N7 is the first chance to ask whether that frontier
   was a property of the descriptions or of a corpus solvable by counting
   words.** If some arm clears both, the frontier was an artefact of the ruler
   and seven arms of L-track conclusions need revisiting.

## Where I expect to be wrong

**Prediction 3 is the shakiest and it is the one I most want to run.** L7's
evidence for it is two items, both of which were positives kept on a
maintainer's judgement, and both were in the v2/v3 key. Whether the mechanism —
*naming* a criterion is applied more strictly than *showing* it — exists at all
is not established by two items. If `stakes-named` and `stakes-shown` land on
top of each other on v4, the honest reading is that L7 found two idiosyncratic
items rather than a mechanism.

**Prediction 5 could be met for an uninteresting reason.** If every arm lands
inside a point of `full`, the frontier is not being tested — the descriptions
would simply not differ enough on this corpus to reach it. The check is whether
the arms *spread*: N6's three spanned 0.8295 to 0.9477, which is spread enough
for the question to be live. If N7's three cluster tightly, prediction 5 passes
without meaning anything and the entry reporting it must say so.
