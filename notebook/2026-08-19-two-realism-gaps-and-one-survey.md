# 2026-08-19 — there are two realism gaps here, and the survey only closed one

An agent sent to verify OASST1's licence came back with a shape objection:
OASST1 is open-domain assistant chat with no option menu and no computed
answer, so a judge in a forced choice could separate it from this repository's
items on structure alone — measuring genre detection rather than realism. It
declined to settle which corpus N4 actually feeds and left it open rather than
guessing, which was the right call and is the reason this entry exists.

**Checked, and the objection does not land where it was aimed — it lands
somewhere nobody was looking.**

## The two corpora

This repository has two generated corpora and both have a realism problem, and
they are not the same problem.

| | the trigger corpus | the word-problem corpus |
|---|---|---|
| what an item is | a message ending in a question about what to do | facts, a question, an option menu, a computed answer |
| where | `datasets/triggers/decision-making/` | `docs/EVAL_SET_DATASHEET.md`'s 10 templates |
| the realism gap | N4/N5 | the retired 10% human audit |
| what a human comparison set looks like | real messages people sent | word problems people wrote |

`RESEARCH_PROGRAMME.md`'s N4 row asks for **"~20 turns drawn from a public
human-written corpus"** and N5's forced choice is **"one corpus turn beside one
human turn, blind judge, which was sent by a person."** Turns. Messages. That
is the trigger corpus, and **OASST1's shape is a good match for it** — its
user-side messages are exactly the object N4 wants. The objection was raised
against a target N4 does not have.

## What the survey did not cover, and nobody noticed

`EVAL_SET_DATASHEET.md` says its retired audit will be replaced by a forced
choice needing **"a public human-written word-problem source"**, and lists the
absence under *Known problems*. The 2026-08-18 survey evaluated eight
candidates and **all of them are conversational corpora.** Not one is a
word-problem source. So:

- N4's need (human *turns*) — surveyed, four candidates clear, OASST1 leads.
- The datasheet's need (human *word problems*) — **never surveyed at all.**

Both documents were written correctly. The survey was scoped to N4 and did its
job. The gap is that the datasheet's paragraph and the programme's N4 row have
been read as one requirement, and fetching OASST1 would have closed one of them
while the other stayed open with nothing recording that it had.

## What is not claimed here

The agent named GSM8K and AQuA-RAT as the right family for the second gap.
**Their licences have not been read and they are not endorsed here** — naming a
family is not clearing a source, and the outside-data rule is unchanged: free
to obtain *and* free to redistribute, licence read directly, a sample read for
personal information, digest pinned.

The OASST1 verification itself came back **partly unresolved and is recorded
that way**: an actual Apache-2.0 `LICENSE` file exists inside the dataset repo,
which is stronger evidence than the metadata tag the earlier survey rested on,
but its copyright-holder block is unfilled and no document naming who licenses
the *conversational content*, or recording contributor consent to
redistributable release, was located first-hand. One conversation thread was
read for personal information — `pii: 0`, UUID user ids, no names — which is one
thread out of 84,437 and is a spot check, not an audit.

**So nothing is fetched and the bar has not moved.** What changed is that the
repository now knows it has two holes and one survey, instead of believing it
had one hole and a plan.
