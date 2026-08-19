# 2026-08-19 — H1's first authoring pass failed, and the objection it was built to answer survived

Three exemplar triplets were authored for Track H Phase 0 and put to two
adversarial reviewers. **The form does not survive. The other 17 must not be
authored against it.** Nothing was committed and no call was made.

## The claim that failed, stated first because it was mine

The registration carries an objection: *the gate that makes an item valid is
the same gate that makes it easy*, because validity requires the governing
fact to be plainly stated, and a plainly stated fact is one the model can
read. The authoring pass claimed to dissolve it — that the two dials come
apart because they attach to **different arms**: the governing fact
self-sufficient (buys validity), the matched fact neutralised from a
non-adjacent base sentence (buys difficulty).

**That claim is false as executed.** Making the matched fact non-obvious made
it *actually govern* in two of three triplets. Verified by re-derivation:

- **h03.** The matched insert requires pre-authorisation ≥ 30 days before the
  scheduled date. Cover starts 2026-09-01 and she cannot pre-authorise before
  she is a member, so the earliest authorised date is 2026-10-01 — **past the
  surgeon's 2026-09-28 slot.** The matched fact moves the answer, through a
  precondition sitting in the base.
- **h01.** Excluding restricted cash is standard treatment, giving
  (840 − 260)/70 = **8.29 months** against the governing arm's 7.71. Both arms
  move the answer and their corrections land **0.57 months apart.**

The one triplet that stayed clean, h02, did so by having a matched fact silent
on termination — which is under-specification, not difficulty. Early-exercised
shares under a transfer restriction is exactly where a repurchase-on-termination
right lives.

**So the objection is not disproved. A counter-construction was attempted and
it failed.** That is the finding, and it is worth more than three triplets.

## And the corpus had a shortcut, found before any call

| | governing insert | matched insert |
|---|---|---|
| h01 | breach is an **event of default** | **restricts** it to the qualifying R&D programme |
| h02 | **forfeits** it unless I am **on payroll** that day | under a **transfer restriction** |
| h03 | **excludes** any condition from cover | **requires** pre-authorisation |

Every governing insert names a **penalty attached to a status change**. Every
matched insert is **procedural**. One surface feature separates the arms
**6 of 6** with no domain reasoning at all.

This is the trigger corpus's word-count shortcut in a new corpus — that one was
89% solvable by counting words and **was not audited until after every Track L
and M number had been computed on it.** The difference is entirely the
timing: this was caught before the corpus was used, by an adversarial pass whose
brief was to break it. Nothing mechanical caught it, which is the gap named
below.

## The falsifier battery is broken five ways

Registered under standing rule 2 as the thing that must pass before any J is
reported. It would have passed while measuring nothing:

- a bare **last-numeral regex passes 4 of 4**, which was the exact extractor
  the battery claimed to catch;
- **both planted movements go down** (18→4, 90→14), while two of three real
  governing arms move *up* — a sign-error scorer passes the battery and zeroes
  sensitivity on two-thirds of the corpus;
- `fal-n` is **not a known-good negative**: its variants delete a base sentence
  rather than insert, so they are replacements;
- the published threshold-independence interval is wrong **in the unsafe
  direction** — 14/18 = 0.7777…, so the advertised 0.778 endpoint excludes a
  τ that fails;
- the battery tests **extraction only** and never the movement rule, so a wrong
  denominator, absolute-versus-relative, or `>` versus `>=` all pass.

## What is registered now, before another attempt

**Authoring until it passes is corpus p-hacking**, and nothing in the
registration stops it — H1's kill governs the *run*, not the *authoring*. So,
recorded as a choice rather than derived, because no principled number exists:

> **Two further authoring passes.** A pass fails if any matched fact is shown
> to govern, or if any single surface feature separates the arms in every
> triplet. If passes two and three also fail, **the construct is not authorable
> at this effort and Track H closes** — with the reason being that valid and
> non-trivial could not be had together, which is a result about the venue and
> not about the skill.

Two is a choice. The argument for it: this review turned the spec from three
salience dimensions into seven and from five disqualifiers into fourteen, so
pass two is genuinely better informed rather than a retry. The argument
against: each pass is another chance for an author to satisfy a checklist while
missing a new shortcut, and the checklist grows only where somebody already
looked.

**And the shortcut audit must become mechanical.** `datasets/triggers/` has a
shortcut battery that `de check` runs. `datasets/tailoring/` has none, and the
6-of-6 register split was found by a reader. A corpus whose shortcut audit
depends on someone thinking to look is the corpus this repository already
shipped once.

## What was corrected in place

The authoring agent's own governance claim — that `datasets/tailoring/` is
ungoverned — **was true when read and false when written**, because a parallel
session added it to `GOVERNED` meanwhile. Every link in the spec resolved and
the prose was wrong, which is `docs/PROTOCOL.md` §3's failure mode exactly.
Corrected in the spec and in `index.yaml`.

Two defects in the spec remain uncorrected and are recorded rather than fixed:
§7's threshold-independence claim, and §4 dimension 5's missing denominator —
`/max` or `/min` changes h02 from 9.4% to 10.4%, failing its own rule.
