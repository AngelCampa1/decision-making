# The falsifier had three holes, and one claim was cherry-picked

**2026-08-19.** The unreachable-procedure check landed this morning
([entry](2026-08-19-the-router-grew-two-rows-and-the-answer-key-did-not.md)) and
was reviewed adversarially before the branch landed. The reviewer's brief was to
break it. It did, in four places, and every finding below was re-derived from the
files before it was acted on.

## The claim that was wrong when it was written

That entry says:

> the 21 `route: ~` items are the council-shaped ones — a family split two ways,
> a split team with one person deciding, a straight choice between two named
> actions — and `evaluate_routing` skips unlabelled positives. The corpus's sink
> for "several defensible positions" is already outside the denominator.

**It is a generalisation from three of twenty-one.** Those three phrases are
lifted verbatim from `s20p`, `s22p` and `xl16p`. Reading all 21 `why` fields, the
rest are annotated as the *absence* of a dominant procedure, not as several
defensible positions: `l17p` says "none of the four dominates", `s09p` "no
obvious dominant difficulty", `l08p` "no dominant difficulty", and `s10p`,
`m19p`, `m21p`, `xl07p` similarly. `route: ~` in this corpus means **open among
the original four**, authored when the table had four rows. It is not a council
sink.

So the sentence that softened the 0-to-16-point ceiling interval does not hold,
and the interval stands unsoftened. The entry is not edited; this is the
correction, which is how the record works here.

**What it does not change:** the `CLOSED BY` condition in
[`corpus-baseline.txt`](../datasets/triggers/corpus-baseline.txt) already
required positives to be *authored* for `council` and `hinge`, with the key
version bumped and the arms re-run. It never offered relabelling the 21 as a
route to closure. Checked rather than assumed, because the reviewer expected it
to be contaminated and it was not.

## Three holes in the check itself

**A branch nothing can reach.** `if not offered: return []` was dead:
`router_rows` raises `UnbundleError` on an empty table rather than returning an
empty list, so no input reaches it. `triggers.py` carries no per-module coverage
floor, so the global 95% would never have surfaced it. Gone — and the module's
own `_scope` docstring, seventy lines above, already says an unreachable branch
is a branch nothing can test.

**An escape hatch justified by an example that does not exist.** The check
returned silently when a set labelled no routes at all, commented as "a
version-2 corpus, archived rather than fixed". The only version-2 corpus on disk
is `datasets/triggers/decision-making.yaml`, and it labels four routes and fires
this check. No set on disk has zero labels.

What the hatch actually bought was silence on the input where the finding is
loudest — a corpus authored with positives and no `route:` labels yet, where
*every* procedure is unreachable. That is the strongest possible finding
converted into nothing, and `_check_routes` does not cover it either, since it
only iterates labels that exist. The hatch is gone. Silence cannot be baselined
and cannot be noticed; a finding can be both.

**A test whose name and body disagreed.** `test_the_key_names_the_whole_set`
carried a docstring about `Finding` identity being the set of things that went
wrong — and a body asserting `== []` on the zero-label hatch. The property in the
name was checked nowhere. Removing the hatch made the same fixture test the
property it was named for: a corpus labelling nothing leaves both procedures
unreachable, and the key must name both.

## Two assertions that were satisfied by the bug they were meant to catch

`a56cd8f` exists to put the corpus path in the message, because the two shipped
corpora otherwise raise byte-identical strings and a reader cannot tell which is
being reported. **Nothing asserted it.** The unit test checked the key and one
phrase; the battery test counted two messages containing one substring, which two
identical strings satisfy. Reverting `a56cd8f` passed the whole suite.

Both now assert the discriminating property — the message's path prefix, and that
the two messages name two *distinct* corpora. This is the fifth time here that a
check has been found green for a reason unrelated to what it claims, and the
second time in this one unit.

## The programme contradicted itself for a day

`docs/RESEARCH_PROGRAMME.md`'s N10 row said `trigger_arms.py` "has no fourth
`*_comparable` guard". `skill_versions_comparable` was built in `6e2028c` and is
wired into `compare()`, and the paragraph 110 lines below the N10 row says so —
including a note recording that *it* had described the guard as a recommendation
for a day after it existed. The same document made the same mistake twice, and
this morning's sweep corrected only the second instance. Fixed, with the narrower
gap that actually remains stated in its place: the guard keys on `skill_version`,
so two arms built from different description text under the same version would
still compare.

## What is still open

- **`datasets/triggers/decision-making.yaml`'s header** said "which of the four
  procedures" until this change. Corrected, and registered in
  [`DECISIONS.md`](../docs/DECISIONS.md) because it is a governed path — the edit
  is a comment and moves no label, which the register entry says explicitly.
- **Closure is satisfiable by one token.** There is no minimum-count threshold:
  adding `route: [ledger, council]` to a single existing positive clears the
  finding while `evaluate_routing` still cannot credit `council` on 64 of 65
  items. Nothing mechanical catches that; only a human reading the
  may-only-shrink diff would. Recorded rather than fixed, because a threshold
  would be an invented parameter.
