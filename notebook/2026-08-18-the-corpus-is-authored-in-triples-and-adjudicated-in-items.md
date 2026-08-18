# 2026-08-18 — the corpus is authored in triples and adjudicated in items

Not a run. A finding about the instrument, produced while trying to execute
"the freeze" — the single answer-key version bump that
[`docs/DECISIONS.md`](../docs/DECISIONS.md) has deferred to twice, on
2026-08-13 and again on 2026-08-14, each time saying the key moves **once**,
carrying every adjudicated move with it.

The freeze cannot be executed as written, and the reason is structural rather
than clerical.

## What was checked, and by whom

Six sub-agents were dispatched across Track N and the work order's backlog.
Two were given the same task independently and told nothing of each other:
re-derive the adjudicated move list from `results/triggers/adjudication.jsonl`
without trusting any prose. They agree with each other, with
`scripts/adjudicate.py --report-only`, and with a third derivation run by hand
afterwards:

| | |
|---|---|
| adjudicated | **261 of 261**, 3 judges each, 0 unparseable |
| moved | **12** — 10 negative → positive, 2 positive → negative |
| movement | **12/261 = 0.046** against the pre-registered 0.20 kill |
| per band | 0.042 s, 0.042 m, 0.045 l, 0.059 xl |
| agreement | Fleiss kappa 0.862, Krippendorff alpha 0.862, unanimity 0.904 |

**The corpus survives the kill by a factor of four, and survives it in every
band separately.** That matters more than the pooled figure: this repository
has had a pooled statistic hide a per-stratum problem before, so the per-band
column is reported beside it rather than after someone asks.

## The finding

**Every one of the 12 moves breaks the one-positive-two-negative invariant that
`corpus._check_triples` enforces.** Computed directly against the corpus and the
adjudication ledger, 12 of 12, with no exceptions:

- **The 10 negative → positive moves each land in a triple whose existing
  positive the same blind adjudication independently reconfirmed as positive.**
  Not one of those ten is a case of "the author labelled the wrong member" — in
  every one, the judges say *both* members should fire. Applying the move gives
  a triple with **two positives**.
- **The 2 positive → negative moves land in triples whose other two members were
  unanimously judged negative.** There is no member to promote. Applying the
  move gives a triple with **zero positives**.

`_check_triples` reports this as a **structural** finding, and structural
findings carry the `_UNBASELINEABLE` key on purpose — the module's own comment
says they "cannot be listed, because there is no backlog to defer." So there is
no path where the freeze lands and `de check` stays green while somebody sorts
this out later. It fails immediately, by design, and the design is right.

## Why this is the instrument's shape and not an accident

**The corpus is authored in triples and adjudicated in items.** A triple is one
body with three different closing asks, exactly one of which is supposed to
warrant firing. The judges were shown one turn at a time and asked whether *that
turn* should fire. Nothing in the adjudication protocol knows that two of the
turns it just judged share a body with a third and are competing for a single
positive slot.

So a 2-of-3 vote against the key does not mean "this item's label is wrong". It
means **the authored contrast did not land** — the ask that was supposed to be
inert reads, to three independent readers, as one that warrants firing. Those
are different claims with different remedies, and the plan's rule collapses them
into one line. [`docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md`](../docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md)
says: *"2-of-3 against me → I rewrite the turn or move the label, and say
which."* On a matched-triple corpus, **"move the label" is not always an
available branch**, and the plan never says so because when it was written the
question had not come up.

That the same class of problem was already met once, and correctly, is the
strongest evidence this is structural. `docs/DECISIONS.md`'s 2026-08-14 entry
records three items (`l12n1`, `l17n2`, `xl15n2`) reverted rather than promoted,
because accepting them "would have broken the one-positive-per-triple design."
That was treated as a side effect of one opener edit. It was not. It is the
general case, and the general case is **all twelve**.

## Where this leaves the freeze

Unresolved, deliberately, and recorded rather than decided quietly. The options
are not equivalent and at least one of them is a trap:

- **Retire the affected triples.** Mechanical, invents nothing, and costs 36
  items — 261 → 225, 87 → 75 triples. Its danger is that it deletes exactly the
  items blind judges found hardest, which makes the corpus *easier* rather than
  *better*, and it happens to close two of the three open shortcut findings.
  A corpus edit that turns gates green is the mechanism this repository has
  already named as the source of four generations of leak.
- **Rewrite the disputed ask and re-adjudicate.** The plan's own first-named
  remedy, and the one that preserves the item count and the difficulty. Costs
  authoring and a further adjudication round.
- **Swap roles inside the triple** — demote the existing positive. Ruled out:
  no judge supports it, and it would be asserting a label against the evidence
  that motivated the change.
- **Relax the invariant.** Corpus redesign, not a version bump, and it breaks
  the matched-null arithmetic that the triple construction exists to provide.

**Prediction, registered before the choice is made.** I expect retirement to
raise measured accuracy on the survivors, because the 36 retired items are by
construction the ones three readers found ambiguous. If a future run on the
225-item corpus scores *lower* than the same arm on the 261-item one, that
prediction is wrong and the retired items were not the hard ones.

**Where I expect to be wrong:** I have assumed the two positive → negative
triples are the same kind of problem as the ten negative → positive ones. They
may not be — a triple with zero positives has lost its reason to exist, while a
triple with two has an excess of signal, and the cheap remedy may differ.

An adversarial review of the retirement option is running as this is written and
its objections are not yet in. Nothing is applied. The corpus on disk is
unchanged, and `de check` is green against it.

## Two smaller corrections that fall out of the same audit

**`docs/STATUS.md` was stale by one commit, for the third time.** It read "192 of
261 items are now blind-adjudicated" and "seven adjudicated label moves" while
`30012d9` had closed the L/XL gap about an hour after that paragraph was
written. Corrected in place by appending, per that file's own rule.

**`30012d9`'s commit message says "Eleven of the twelve move negative to
positive."** It is ten. `m18p` and `s12p` both move positive → negative, and the
same commit's own table lists them correctly. History is the pre-registration
evidence and is not rewritten, so the correction lives in `STATUS.md` and here.

**`docs/RESEARCH_PROGRAMME.md` claimed "K5 is closed" and it has not been since
2026-08-14.** `paper/citations-baseline.txt` carries two identifiers,
`2412.06593` and `2505.02151`, added by the K3/K4 pass, and neither is in
`paper/refs.bib`. The claim was true on 2026-08-12 and the file never noticed
the backlog reopening under it.

---

## Correction and adversarial review, appended same day

The review briefed to break the retirement option came back, and it changed the
answer. Every number below was re-derived by me after reading it, not taken on
its word.

**One number above is wrong.** The entry says the existing positives were "9 of
10 unanimous". **It is 10 of 10** — every one of the ten triples receiving a
negative → positive move has its existing positive confirmed by all three judges.
The claim was understated in the direction that made the conflict look softer
than it is. Recomputed directly; the commit that carried the wrong figure is
`2601760` and history is not rewritten.

**Retirement is the wrong branch of the plan's own rule, and I had not read the
rule closely enough.** [The v3 plan](../docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md)
sets out three cases:

> - unanimous agreement with my label → keep
> - 2-of-3 against me → I rewrite the turn or move the label, and say which
> - split 3 ways → the triple is retired as genuinely undecidable

All 12 disputes are clean 3-0 or 2-1 majorities. **Not one is a three-way
split**, so retirement — which the entry above listed first and called
"mechanical" — is the remedy for a case none of these are. And the reviewer went
further, correctly: with **three binary judges a three-way split cannot occur**.
Outcomes are 3-0 or 2-1 and nothing else. **The retirement branch has been dead
code since the protocol was written**, which is why reaching for it here felt
available: nothing had ever tested whether it could fire.

So the plan's live branch is *rewrite the turn or move the label*. Moving the
label is structurally blocked, as the entry above establishes. **That leaves
rewriting, which the entry listed second and never costed.**

**Three further objections, each checked:**

- **Selection bias is measurable, not hypothetical.** Retiring the 12 removes
  implicit asks at 18.5% and embedded asks at 18.2% against explicit asks at
  7.9% — more than double the rate on the two ask forms v3 exists to add,
  because v2 was saturated with *"should I"*. By domain it removes 23.5% of
  technical and 22.2% of money while removing **0%** of relationships. The
  survivor corpus is easier along exactly the axes the redesign was built to
  stress.
- **Retirement costs N6 the power the long-band merge just bought.** Reusing
  that entry's own formula and design effect: SE 0.0346 → 0.0374, MDE **0.0970
  → 0.1047**, power at the registered 0.10 consequential threshold **0.823 →
  0.763**. The MDE crosses the effect the test is built around, and the power
  drops back under 0.80 — undoing most of the 0.577 → 0.823 gain that
  2026-08-14 recorded as making Q1 "a properly powered test now".
- **The favourable-numbers charge is weaker than I stated, and the reasoning is
  still wrong.** The reviewer computed that the retired triples are *less*
  extreme than the survivors on the two features whose findings close — 0.229
  against 0.283 on `sentence_count`, 0.292 against 0.393 on `type_token_ratio`
  — so this is not feature-retuning wearing an adjudication mask. But listing
  "two gates close" as a *merit* of the option is the shape of reasoning this
  repository has named as the source of four generations of leak, whatever the
  mechanism. Gate movement is a disclosed side effect, never a reason.

**And one prospective danger worth recording even though it is not today's
decision.** If retirement becomes the standing answer to adjudication
disagreement, the 20% kill can never fire again: whatever would move the number
gets deleted before it is counted, so every future round reads near zero
movement on a corpus pruned of exactly the disagreements. If retirement is ever
used, movement has to be reported **cumulatively over the corpus's whole
history** — every disagreement ever found over every item ever adjudicated —
rather than reset against the pruned base.

**So the freeze's remedy is rewrite-and-re-adjudicate**, on the plan's own rule,
at a cost of ~12 rewritten asks and 36 re-adjudication calls. There is no budget
to spend and no quota argument for the cheaper wrong thing. Retirement is held
back for any of the 12 that still fails to reach a key-consistent majority after
a genuine rewrite — which is the nearest thing to "genuinely undecidable" this
voting design can actually produce.

**One thing nobody can check yet, and it should not be papered over.** The plan
requires that a retirement be bias-checked by asking whether retired items were
*harder for the arms* — and **no run has ever been scored against this corpus**,
so that check cannot be run at all. The shortcut-battery features stand in for
it above. They are not the same claim.

**A drifted number, found in passing.** `datasets/triggers/corpus-baseline.txt`
quotes 3.82 and 4.27 null SE for the two open findings; live against `HEAD` they
read **3.11 and 4.14**, moved by intervening text-only edits. That is consistent
with that file's stated policy of leaving prose as a dated record — but whoever
executes the freeze re-runs the battery against `HEAD` rather than trusting
either figure.
