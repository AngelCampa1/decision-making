# 2026-08-18 — there is no budget, and N4 stops waiting on a person

Two maintainer decisions, taken together because the second follows from the
first, and both are recorded because neither existed in writing anywhere.

## 1. Nothing may be purchased

**"this is a side project. i don't have a budget to purchase vendors or whatever
you're suggesting here. whatever you can get for free (and make sure it's safe)
get it"** — maintainer, 2026-08-18.

This had been true since the first commit and had never been written down. It is
the same defect shape as the model tier that survived only as prose in a
hand-written README: a parameter that governs every decision, recoverable only
from someone remembering it. It is now in [`CLAUDE.md`](../CLAUDE.md) beside the
subscription note, and `AGENTS.md` carries the same bytes.

**It was also triggered by a genuine misreading, and that is worth keeping.** I
proposed *vendoring* a public corpus, meaning checking a copy into
`datasets/vendor/` — the pattern `lost_in_conversation` already follows, free
data at a pinned SHA. It was read as hiring a vendor. The word does mean both
things and this repository only ever meant one of them, so the new bullet names
the ambiguity rather than assuming the next reader resolves it correctly.

The operational half is in
[`AUTONOMOUS_WORK_ORDER.md`](../docs/AUTONOMOUS_WORK_ORDER.md) as a fifth item
under things that need care: licence read first-hand, redistribution rights
checked separately from download rights, a sample actually read for personal
information rather than trusted on the strength of a licence, and a digest
pinned so the loader refuses drift. **`de fetch` downloads; it does not vet.**

## 2. N4 will not come from the maintainer

**The ~20 human-authored holdout turns will not be supplied.** N4 has sat on
`STATUS.md`'s maintainer list since it was written, and no turn has ever
arrived. A blocked row nobody retires is how a track stalls indefinitely, so it
is retired here and replaced rather than left open.

The replacement: a public human-written corpus, labelled by N3's three-judge
blind adjudicator, unchanged.

**What that preserves.** N4 controls for the *provenance of the text*. Every
leak Track N has closed was an authoring habit — the word-count ruler at 0.890,
the `open`-view opener at 0.779 in XL, `_shared_body` cutting at the last space
— and every one was in text a model wrote, hunted by a gate a model built. The
loop is broken by human text, whoever the human is.

**What it costs, stated rather than argued away.** The adjudicator is still a
model, so the key is not independent of the thing being tested; only the text
is. That is materially less circular than a model authoring both, and it is not
zero. And the distribution shifts — forum posts are written for strangers, chat
logs were sent to a different assistant — so the holdout asks *does this
generalise off our own writing* rather than *does this work on the maintainer's
inbox*.

**Prediction, before any source is fetched.** I expect the human corpus to be
*harder* than the authored one: the arms should score lower on it, and the
between-arm spread should narrow, because real messages are noisier and carry
less of the clean positive/negative contrast the matched-triple design creates
by construction. If instead the arms score *higher* on human text, something is
wrong with the authored corpus that 261 items of gating did not catch.

**Where I expect to be wrong:** the licence survey. I named WildChat,
LMSYS-Chat-1M, ShareGPT, the Stack Exchange dumps and Ask MetaFilter as
candidates without opening a single licence, which is exactly what standing
rule 5 forbids. None of them may be cited as usable until read first-hand, and I
would not be surprised if the closest fit to the deployment distribution — real
turns sent to a chat assistant — is the one that cannot be redistributed.

**A label-free fallback exists** if nothing clears the bar. N4's payload is
whether the arms rank the same on human text as on authored text; a weaker
version measures only how far the arms diverge **from each other** on unlabelled
human turns. No key, no adjudication, and divergence on authored text beside
convergence on human text would still be a finding.
