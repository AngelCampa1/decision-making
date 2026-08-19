# H1 authoring pass two: five authored, one clean

**2026-08-19.** Pass one failed on two counts — two of three matched facts
governed, and a single register feature separated all six inserts. Pass two was
one of two remaining attempts under the kill registered in
[the pass-one entry](2026-08-19-the-h1-form-failed-and-the-two-dials-are-one-dial.md):

> **Two further authoring passes.** A pass fails if any matched fact is shown to
> govern, or if any single surface feature separates the arms in every triplet.
> If passes two and three also fail, **the construct is not authorable at this
> effort and Track H closes**.

## The verdict, and it is narrower than it sounds

**Neither clause fired.** No matched fact was shown to govern — the reviewer
briefed to prove exactly that reported it could not. No single surface feature
separates the arms in every triplet: the strongest found reaches four of five.

The kill closes the track only if passes two *and* three fail. One did not, so
the closure condition can no longer be satisfied. **Track H survives its
registered kill.**

That reading is literal on purpose. The same wording was read literally in the
other direction earlier the same day, when a feature separating three of five was
declined as "every" — a criterion that is read strictly when it would fail and
loosely when it would pass is not a criterion.

**Surviving the kill is not viability, and the yield is the real finding.** Five
authored, **one clean**, one blocked on a parameter nobody has derived, three
cut. And the corpus cannot be merged regardless.

## What the design changed, and what it bought

Pass one neutralised its matched facts by **margin** — a 30-day lead time against
a slot 40 days out. That is what killed it: a precondition in the base ate the
margin in `h03`, and in `h01` the matched fact's own correction landed 0.57
months from the governing one.

Pass two neutralises **categorically**: the matched fact constrains an object with
no arithmetic channel to the elicited quantity. There is no margin to eat and the
correction is exactly zero. Two triplets additionally carry a direction property
— the matched fact can only move a date earlier, so no reading of it produces a
larger answer.

It worked. Both pass-one failure modes are absent, and neither reviewer nor the
blind re-derivation recovered them. Disqualifier 10 fires nowhere; disqualifier
11 fires nowhere, with corrections 4 weeks, 6 weeks, 4 weeks, 2 months and 14
days apart against `h01`'s fatal 0.57.

**The failure moved rather than disappearing**, which is the honest summary:

| triplet | disposition | caught by |
|---|---|---|
| `t01` cider | cut | blind re-derivation — governing arm ambiguous |
| `t02` radiography | cut | maintainer ruling — over-determined, shared venue |
| `t03` recruitment | **clean**, repairs named | — |
| `t04` bakery | **blocked pending τ** | reviewer — smallest movement in the set |
| `t05` van | cut | blind re-derivation — governing arm ambiguous |

## The check nobody had run

An agent read only `elicited` and `prompt` — never the `key:` block — and
recovered all fifteen values. Every governing arm moves; every matched arm lands
exactly on base. Pass one never demonstrated its corpus was answerable without
the key, and this is the single most valuable thing pass two produced.

It also found a failure class **the kill does not name**. In `t05` the earlier
slot is *offered*, not accepted, against a base that has the persona say of the
original date "that is the one I hold" — so the base value is defensible. In
`t01` there is a fork at 6 versus 10 weeks depending on whether a 30-litre
returnable container is necessarily a keg.

An ambiguous *governing* arm is the mirror of the defect the kill names, and it
is worse: it depresses `P(change | governing)` through item ambiguity while
looking identical to a model that failed to notice. The primary is a difference
of two probabilities, so it biases toward zero and makes a null unreadable. Now
disqualifier 15 in
[the spec](../docs/TAILORING_CORPUS_SPEC.md).

## The leak the battery could not see

Content-word overlap between each insert and the base sentence stating the causal
rule: **pooled AUC 0.740, and 0.800 with proper nouns dropped** — far outside
`SEPARABILITY_BAND` of [0.40, 0.60]. A reviewer's sharper formulation, reading the
requirement sentence rather than the rule sentence, reaches four of five.

Dropping entity names makes it *worse*, so the leak is causal vocabulary rather
than proper nouns and renaming is not the repair. `t01` resists both
formulations, which is why the clause did not fire.

**Three things were decided about it and each is worth stating separately.**

The criterion does not move and the band does not move — relaxing a registered
kill after seeing the data it fails is the move this repository exists to avoid.
The **detector set may grow**, because adding a feature is asymmetrically safe: a
new feature can only ever make the gate fail more, never less. And the repair is a
**spec rule written before it is applied** — `t01` and `t02` already have the good
shape naturally, both inserts routing through the actor the rule sentence names,
so it is a design rule rather than a per-item patch. Pass two's files stay exactly
as they are, as the evidence that the rule was needed.

The authoring agent declined to apply that repair unprompted, on the grounds that
coding a feature and then editing until it stops firing is tuning to a metric
after seeing its value. That was correct and it is the reason this entry can be
believed at all.

## `t04` is blocked, not cut, and the reason generalises

Relative movements: `t01` 0.667, `t02` 1.000, `t03` 1.000, **`t04` 0.333**, `t05`
0.500. **τ has never been derived.** Any τ above 1/3 makes `t04`'s governing arm a
guaranteed false negative — structurally impossible rather than hard. Counting it
usable would be inventing a bound for an underived parameter, which is standing
rule 1. If a derived τ lands at or below 1/3 it returns unchanged.

The generalisable part is a rule for pass three, not a fact about `t04`:
**downward corrections are bounded — a date can only come forward as far as today
— while upward ones are not.** So down-arms sit lowest on relative movement by
construction. The deliberate three-up/two-down split bought sign-robustness and
paid for it in threshold headroom, which nobody anticipated when the split was
chosen.

## What a green battery is worth here

All five features are live channels — a planted leak on any one is caught, so an
earlier claim in this session that three checks "could not have failed" was too
strong. `Check.inert` reports non-attainability over *observed* values, which is a
narrower statement than undetectability.

The real bound: **a shortcut confined to one triplet is invisible at n=5** —
register fires at 2 of 5, numerals at 3 of 5. And `causal_rule_overlap` was
invisible to all five because it was not among them.

## What would make this entry wrong

- **Reviewer B, which never reported.** Clause 1 rests on one adversarial reviewer
  failing to show a matched fact governs, plus the blind re-derivation. A second
  reviewer finding one in `t03` would take the yield to zero, and this entry
  would be wrong about the only item it calls clean.
- **`t01`'s cut being the wrong call.** The reviewer rated it the *strongest* of
  the five and the only item resisting both shortcut formulations. Both readings
  can hold at once — the readers were answering different questions — but if a
  later pass shows a professional cannot defensibly decline the kegs reading, the
  cut was wrong and the dissent recorded in `index-pass2.yaml` is where to start.
- **A derived τ at or below 1/3**, which would return `t04` and make the yield two
  rather than one.
- **The whole approach being priced wrong.** One clean triplet from five authored,
  at this effort, is the number that decides whether Track H is worth continuing
  — and nothing here has costed what a powered corpus would take at that rate.
  That question is not answered by this entry and should not be read out of it.

## For the maintainer

The registered kill did not fire, so Track H does not close, and the corpus still
cannot be merged: `causal_rule_overlap` raises a finding the moment it is coded.
The next unit is **deriving τ**, which needs its own pre-registration and is not a
pass three. `causal_rule_overlap` is not yet in `tailoring.FEATURES`; adding it
needs an explicit per-item rule-sentence annotation, because a heuristic extractor
would be the same check-that-cannot-fail defect in new clothes.
