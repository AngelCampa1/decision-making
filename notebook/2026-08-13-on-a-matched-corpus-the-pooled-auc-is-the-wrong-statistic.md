# 2026-08-13 — on a matched corpus, the pooled AUC is the wrong statistic

The shortcut battery has measured this corpus with pooled AUC since it was
written. Every gate, every published separability number, every "the corpus is
ruler-proof" claim rests on it.

A within-triple check was added today. Run against the merged 192-item corpus,
the two statistics disagree completely:

```
within its own triple, the positive's 'word_count' sits above its two negatives
in 0.660 of comparisons -- 3.24 null standard errors from chance

per band: s 0.604, m 0.750, l 0.778, xl 0.393
pooled AUC: 0.517 (turn view), 0.502 (ask view)
```

**Pooled AUC 0.517 is as clean a number as this battery can print. The matched
statistic is 0.660 at 3.24 standard errors.**

## Why pooled is blind here, structurally

A pooled AUC ranks every positive against every negative — including negatives
from *other* triples. Across triples the bodies differ by hundreds or thousands
of words, and that variation swamps the ask entirely. Two-thirds of the
comparisons in the pooled statistic are between items that share nothing, and
they are noise with respect to the property the design is controlling.

The matched comparison uses only the comparisons the design creates: **this
positive against its own two negatives, over a body they share.** That is the
whole point of building matched triples, and until today nothing measured it.

**So the corpus was built as a matched design and evaluated as an unmatched
one.** The gate was answering a question the construction had already made
uninformative.

## What it caught

`m` at 0.750 and `l` at 0.778 — the positive holds a length rank inside its own
triple in three cases out of four. `xl` at 0.393 points the other way and pulls
the pooled figure back to innocence. **That is the fourth pooled-cancellation
recorded today**, after terminal `?` (0.569 pooled, 0.643 in XL), the four
`close`-view features, and ask sentence count (0.504 pooled, 0.625 in `m`
against 0.296 in XL).

Four separate people found four separate instances of this leak over the course
of a day, each individually, each after the fact. **The matched statistic found
all of it in one run.**

## The recommendation

The matched statistic should be the primary gate and the pooled AUC a reported
summary. That is offered rather than imposed — the person who built it did the
false-positive arithmetic for the derived views before switching them on, which
nobody else here has done for any gate, and the threshold question is theirs.

What is not in doubt: **a pooled AUC near 0.5 on a matched corpus is weak
evidence of anything**, and this repository has been treating it as strong
evidence since the corpus was designed.

## The fifth inert estimator, in the module that hunts inert estimators

`corpus._shared_body` cuts the common prefix back to the last **space**. A body
ends with a **newline** before the ask, so the body's final word leaks into every
derived ask and becomes the ask's first "sentence". Opener features are therefore
constant within every triple and read **exactly 0.500** in XL.

It was caught by an authoring unit precisely *because* the number was exactly
0.500 — the reasoning behind the new `attainable_auc` guard, applied by a person
before the guard could apply it.

Worth noting what it implies about the guard's message: a feature that is inert
for a **derivation** reason looks identical to one inert for a **corpus** reason,
and the current wording sends the reader to re-author the corpus when the bug is
in the splitter.

## What this does not resolve

The matched statistic is right about the comparison it makes. It says nothing
about whether an *arm* — a model reading the description — is affected by a rank
it could only exploit by seeing all three members of a triple, which it never
does. An arm sees one turn.

So a within-triple rank is a defect in the **construction**, and it is the right
thing for a corpus gate to refuse. Whether it is a defect in the **measurement**
depends on whether the property that produces the rank also separates the labels
in a way a single-turn reader can use — which is what the pooled AUC was trying
to ask, badly.

**Both statistics are answering real questions. Neither answers the other's.**
That is worth saying plainly, because the temptation after a finding like this is
to declare the old number worthless, and it is not — it is under-powered and it
was over-trusted.
