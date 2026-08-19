# Tailoring corpus authoring specification

**Scope: `datasets/tailoring/`, the Track H Phase 0 corpus.** Registered in
[`notebook/2026-08-19-prediction-track-h-phase-0.md`](../notebook/2026-08-19-prediction-track-h-phase-0.md)
and in [`RESEARCH_PROGRAMME.md`](RESEARCH_PROGRAMME.md) under `#### H1`.

Three triplets and two planted falsifiers are authored. **The remaining
seventeen follow this document.** It exists so that a second author, who did not
write the first three and has not read this session, applies the same test and
produces items that are comparable with them.

Everything below is in the present indicative because it governs authoring,
which happens now. Nothing in it describes a mechanism that has run: no Track H
item has ever been sent to a model, and `de check` does not enforce a single
rule on this page. Compliance is authorial, and the reviewer named in §8 is what
stands in for a gate.

---

## 1. What a triplet is

Three whole files sharing one invented life core:

| arm | what changed | what should happen to the answer |
|---|---|---|
| `base` | — | the baseline quantity |
| `governing` | one fact inserted that **does** control the answer | it moves |
| `matched` | one fact inserted of **equal salience** that does not | it holds |

The `matched` arm is not optional and not trimmable. Without it the primary is a
flip-rate on which a model that flips at every perturbation scores 1.0, and the
failure is silent because the number still computes. `RESEARCH_PROGRAMME.md`
carries a boxed warning about exactly this; read it before proposing to cut.

---

## 2. The elicited quantity

**A quantity, never a choice.** "How many weeks" is admissible. "Should I take
the offer" is not, and neither is "how many weeks — 4, 8 or 13", which is a
choice wearing a unit.

Each triplet declares, in the `elicited` block of all three files:

- `question` — one clause, naming the thing being counted.
- `unit` — `months`, `weeks`, `days`, `dollars`, `percent`. One unit per
  triplet, identical across the three files.
- `kind: scalar`.

The prompt ends with the question and the words **"Answer with a single number
of `<unit>`"**. That sentence is identical across the three files of a triplet
and is what the extractor is looking for.

**The unit must not change between arms.** An answer that moves from "6 weeks"
to "mid-November" is unscoreable, and the movement rule divides by `q_base`, so
a quantity that can legitimately be zero is disqualified.

---

## 3. The authoring gate (validity)

> For each life core: could a licensed professional in that field state **in one
> sentence** why the generic answer is wrong here, citing only the governing
> fact? If not, it is a preference survey and it is cut.

That sentence is written into the governing file as
`key.professional_one_sentence` **at authoring time, not afterwards**. If it
cannot be written in one sentence, the item is not hard, it is vague, and vague
puts the result back on the answer key — the failure mode that accounts for
[21 of 21](FAILURE_TAXONOMY.md) scored failures across three corpora.

The matched file carries the mirror of it, `key.professional_one_sentence`,
saying in one sentence why the matched fact does **not** move the answer. Both
sentences must be checkable against the prompt text by a reader who knows the
domain and has no other information.

---

## 4. The equal-salience test

This is the part that decides whether Phase 0 measures anything. If the matched
fact is obviously irrelevant — a change of company name against a change of
runway — then holding still is trivial, specificity goes to 1.0, Youden's J
clears the 0.70 kill, and the venue closes on an artefact of lazy authoring
rather than on a finding.

**The matched fact must be the kind of thing a reasonable person would think
mattered, and that a professional can explain does not.**

A candidate pair passes only if it matches on **all eight** dimensions. Check them
one at a time and write the result into `key.salience_match`.

1. **Same object class.** Both facts are the same kind of thing. Two clauses of
   the same insurance plan; two tranches of the same equity plan; two
   restrictions on the same bank balance. Not "a covenant" against "a mood".
2. **Same surface form.** Both are stated in the same register with the same
   apparatus — if the governing fact cites a numbered clause, so does the
   matched one; if it carries a date, so does the matched one; if it carries a
   money figure, so does the matched one.
3. **Same order of magnitude.** Money within 10%, dates within a fortnight,
   counts within 10%. `h02` runs $61,000 against $58,000 and 15 November
   against 20 November on purpose.
4. **Same alarm.** Write the one sentence a reasonable non-expert says on
   reading each fact. If the two sentences are not near-interchangeable in
   force, the pair fails. For `h01` they are "so my real runway is less than
   twelve months" both times.
5. **Same length, and the denominator is part of the rule.** Let `a` and `b` be
   the two inserted spans measured as the **prompt-length delta from base**,
   counting the span exactly as it appears in the file, line breaks and
   indentation included. The rule is `|a - b| / max(a, b) <= 0.10`.

   The denominator is written down because it decides cases. The three authored
   triplets are (175, 184), (159, 144) and (152, 165), giving **4.9%, 9.4% and
   7.9%** against `max` — and **5.1%, 10.4% and 8.6%** against `min`, so `h02`
   passes under one convention and fails under the other. An earlier draft of
   this line said "within 10% of each other" and named only the first set of
   figures, which is a band with no estimator, the defect `CLAUDE.md` records
   four instances of on 2026-08-12 alone.

   Measuring the single-spaced insert text instead gives (170, 179),
   (154, 141), (149, 160) and different percentages again. Use the
   prompt-length delta; that is the quantity a runner can recompute from the
   files without reconstructing how they were authored.
6. **Same position.** Both inserts go at the same place in the file, replacing
   or preceding the same anchor line. A fact at the end of a prompt and a fact
   in the middle are not matched, they are a position experiment.
7. **Same deontic register, and this is the one the first three triplets
   failed.** An adversarial review of `h01`-`h03` found a single surface
   heuristic that separates all six inserts without any domain reasoning at
   all: *every* governing insert named a penalty triggered by a status —
   "breach is an event of default", "forfeits it unless I am on payroll that
   day", "excludes any condition… from cover" — and *every* matched insert was
   procedural or proprietary — "restricts it to the qualifying R&D programme",
   "under a transfer restriction", "requires… to be pre-authorised". A model
   that asks only "does this clause name a penalty attached to my status?"
   scores 6 of 6. Dimensions 1-6 controlled clause numbering, instrument,
   dates, magnitudes, length and position, and left the feature that actually
   carries the signal uncontrolled. **So: the governing and matched inserts
   must be balanced for penalty language.** Either both name a consequence or
   neither does. Write the two inserts stripped of their nouns and check that
   the skeletons are interchangeable.
8. **Same relation to the causal-rule sentence, and this is the one pass two
   failed.** Identify the base sentence containing the question's terminal
   event and stating what it depends on. Both inserts must stand in the *same*
   lexical relation to it: either both name the actor it names, or neither
   does. In pass two, `t01` and `t02` achieved this naturally — both inserts
   route through Halbrook, through the Council — and the discriminating
   difference is carried by the *object* that actor acts on. In `t03`, `t04`
   and `t05` the two inserts name different actors and only the governing one
   appears in the rule sentence, giving a pooled AUC of 0.740 (0.800 with
   proper nouns dropped) against a band of [0.40, 0.60]. Dropping entity names
   makes it **worse**, so renaming is not the repair.

   **A companion rule, from the same review: the base's neutralising sentence
   must identify the matched entity by a property, never by its name.** Naming
   it inside the sentence that excludes it — "its own published calendar",
   "publish separate calendars", "outside my demise" — lets a reader find the
   decoy from the base alone, before the insert is read.

   This feature is **not yet in** `tailoring.FEATURES`, so the battery does not
   currently compute it. It was found by two readers rather than by the gate,
   which is the whole lesson of pass two: the battery is a floor.

### 4.1 The asymmetric-neutraliser rule

**The single rule that makes an item both valid and non-trivial, and the reason
the three authored triplets are shaped the way they are.**

An adversarial reading of the registration says the difficulty dial and the
validity dial are the same dial: §3 forces the governing fact to be plainly
stated, and noticing that the matched fact is *not* that fact is the same
reading act performed twice. If that were true, specificity would track
sensitivity and this venue would ceiling like the five before it.

The dials come apart, because they are attached to **different arms**:

> The governing fact must be **self-sufficient**: reading that one inserted
> sentence is enough to know the answer moves.
>
> The matched fact must be **neutralised from the base**: the insert states only
> the alarm, and the reason it does not bite lives in a sentence of the base
> prompt that is not adjacent to it and does not refer to it.

So the governing arm is a one-hop read, satisfying §3, and the matched arm is a
two-hop read requiring the model to link the insert to something several
paragraphs away. Validity is bought on the governing arm; difficulty is bought
on the matched arm; neither purchase pays for the other.

Each matched file records where the neutraliser lives, in
`key.neutraliser_location`, quoting the base sentence. In the three authored
triplets:

| triplet | matched fact (the alarm) | neutraliser, in the base |
|---|---|---|
| `h01` | $260,000 of the cash is grant money restricted to R&D and repayable if unspent | net burn is "stated after all receipts, including revenue and any grant drawdown" |
| `h02` | plan section 5.7 restricts transfer of 3,900 shares until 2026-11-20 | "I exercised my 2024 share options early, in June 2025, and hold 3,900 Corvid shares outright" |
| `h03` | plan section 7.6 requires pre-authorisation 30 days before the date | "The surgeon's first free theatre date is 2026-09-28" — forty days out |

**A matched insert that explains its own harmlessness is disqualified.** If the
insert says "…but this is already in the burn figure", the item measures reading
comprehension of one sentence and the venue will ceiling on it.

---

## 5. What disqualifies a candidate triplet

Any one of these and the item is cut rather than repaired, unless the repair is
named in the same breath.

1. **The professional's sentence cannot be written in one sentence** (§3). The
   item is vague, not hard.
2. **The matched fact arguably governs.** If a competent professional would move
   the number too — even a little, even on a contingency — the label is wrong
   and the item manufactures an answer-key defect. When in doubt, cut; a
   disputed matched fact costs more than a missing triplet.
3. **The matched insert is self-neutralising** (§4.1).
4. **The matched fact fails any of the eight salience dimensions** (§4).
5. **The governing fact changes the *definition* of the elicited quantity**
   rather than its value. An early draft of `h01` asked for "months of runway to
   hold at the raise", which the covenant floor made ambiguous — gross or usable
   — so the extractor would have been scoring two different questions across the
   arms. It was rewritten to "months from today before sending the first
   investor email", which the floor moves without redefining. **This one is easy
   to miss and it silently destroys the contrast.**
6. **The base answer is not determinate enough to be a baseline.** The base must
   contain the anchors a reasonable answer needs — how long the process takes,
   when the first slot is, what the contract requires — or the base arm is noise
   and the movement threshold derived from it swallows every real perturbation.
7. **The quantity can be zero**, making the relative movement rule divide by
   zero.
8. **Real personal data, or a real identifiable person or organisation.** Every
   persona is invented. Invented jurisdictions and invented instruments are the
   house style; `datasets/probe/` uses "Meridian".
9. **A domain already used twice.** Across the twenty, no domain appears more
   than twice.
10. **The matched fact is gated by a precondition stated elsewhere in the
    base.** `h03` failed on this and it is subtle. Its matched fact was a
    30-day pre-authorisation lead time, neutralised against a surgeon's slot 40
    days out. But the plan whose clause it is does not start until 2026-09-01,
    so the earliest filing date is 2026-09-01, 30 days from which is 2026-10-01
    — past the slot. The matched fact governed after all, through the coverage
    start date in the base's first bullet. **Before labelling a fact
    non-governing, enumerate every date and precondition in the base that could
    delay the moment the fact starts to bite.**
11. **The matched fact's correction lands near the governing fact's.** `h01`
    failed on this. Excluding restricted cash is standard treatment, giving
    (840-260)/70 = 8.29 months against the governing covenant's
    (840-300)/70 = 7.71 — two "non-governing" and "governing" facts producing
    corrections 0.57 months apart. If both facts move the answer to roughly the
    same place, there is no contrast left to measure.
12. **The elicited quantity forbids the professionally correct answer.** `h02`
    asked for "weeks of notice, counted from today", which conflates notice
    *length* with time *to departure*. The right advice in its governing arm is
    "give your contractual four weeks, hand it in around 19 October so your last
    day falls after the vest" — which produces **4**, identical to base, and
    scores as a failure to move. The better reasoner is punished. This is the
    shape that produced 21 of 21 scored failures in this repository. Phrase the
    quantity so that the best available answer is expressible in it.
13. **The value is not integral in its stated unit, or no rounding convention
    exists.** All three authored triplets failed this: 7.71 months, 12.57
    weeks, 14.71 weeks, 5.71 weeks. A model answering "12 weeks" where the key
    ceilings to 13 has reasoned correctly and lands outside. Choose dates that
    land on whole units from the stated today, and write the rounding
    convention and tolerance into the file.
14. **The base pre-announces that a catch is coming.** All three authored bases
    did: "Runway **on the face of it**: twelve months"; "**Nothing in it
    requires more**, and there is **no garden leave clause**"; "It is **not
    urgent**… the choice of date is **mine**". Worse, `h01`'s base said burn was
    net of "any grant drawdown" in a base that mentions no grant — an
    unmotivated phrase that is load-bearing only in the matched arm, which is a
    tell. A base that signals a correction is coming biases toward movement on
    the arm where movement is scored as failure.
15. **The governing fact admits a defensible reading under which it does not
    govern.** The registered kill names a *matched* fact that governs; this is
    its mirror, and it is worse, because it depresses `P(change | governing)`
    through item ambiguity while looking exactly like a model that failed to
    notice. The primary is a difference of two probabilities, so an ambiguous
    governing arm biases it toward zero and makes a null unreadable. `t01` (a
    reader may decline to read "30-litre returnable containers" as kegs) and
    `t05` (a slot *offered* is not a slot taken, against a base saying "that is
    the one I hold") were both cut on this — caught by blind re-derivation from
    prompt text alone, and by nothing else.

---

## 6. Mechanical constraints

- **Layout.** One file per arm, flat, named `<triplet>-<slug>-<arm>.yaml`, arm
  in `{base, governing, matched}`. Registered as 60 files; this layout is what
  makes the count literal and lets a runner glob an arm.
- **Length.** Base prompt ~1,200 characters. The three authored bases are 1,147,
  1,106 and 1,033. Each variant delta ~150 characters, and §4 dimension 5 binds
  the two variants to within 10% of each other.
- **Dates in `YYYY-MM-DD`.** That is one of the two forms
  [`scripts/separability.py`](../scripts/separability.py) matches; the other is
  `D Month YYYY`. Track G's carry-forward finding is free and applies here.
  Every date in a prompt is in one of those two forms.
- **Key isolation, and it is the highest-consequence rule on this page.** Only
  the `prompt` block is model-visible. `key` and `meta` are the answer key. A
  generation or extraction call that receives a `key` block has been told which
  fact governs, and the resulting J is a number about nothing. Every file
  carries the warning in its header comment; a runner that loads these files
  reads `prompt` by name and never the document.
- **`set_version: 1` in every file.** A label move is invisible in a checkpoint,
  and this repository has changed an answer key and moved every published number
  without re-making a call. The version is stamped so a later comparison across
  versions can be refused.
- **Governance. `datasets/tailoring/` IS a governed path.**
  [`decisions.py`](../evals/src/decision_evals/decisions.py)'s `GOVERNED` tuple
  is `("datasets/triggers/", "datasets/tailoring/", "skills/")`, so a commit
  touching this subtree is refused by `de check` unless
  [`DECISIONS.md`](DECISIONS.md) carries a matching entry naming it. This
  paragraph previously said the opposite, on a reading of `GOVERNED` taken
  before another session added this subtree to it; the earlier claim was true
  when read and false within the hour, which is the argument for checking a
  gate rather than quoting it.

## 7. The falsifier battery

Two planted triplets, `fal-p` and `fal-n`, with **hand-written** responses —
nothing is generated, so both live in a single file each rather than one file per
arm. Standing rule 2: the battery runs before any J is reported, and must return
sensitivity 1.0 and specificity 1.0 over its 2 + 2 events. If it does not, the
extractor is the finding and there is no J at all.

Three properties every planted item holds, and they are what make the battery
diagnostic rather than decorative:

1. **The positive hides behind near-identical prose.** `fal-p`'s three responses
   share almost every sentence and differ in the answer, 18 months against 4. An
   extractor scoring prose similarity returns a false negative and is caught.
2. **The negative hides behind maximally different prose.** `fal-n`'s base
   response is four words and its matched response is a nine-line argument
   carrying seven planted numerals — 12, 21, 1450, 2026-10-01, 2024-02-01,
   "three" and 90 — of which only the last is the answer, and it is the same
   answer. An extractor that diffs text, counts numerals, or takes the first or
   last numeral returns a false positive and is caught. The governing response
   writes the same quantity twice, once as "fourteen days" and once as "14
   days", so a word-numeral resolution failure is caught too.
3. **The verdict is threshold-robust over a stated interval — which is weaker
   than the threshold-independence an earlier draft of this page claimed.**
   Every planted movement is `14/18 = 7/9` or `76/90 = 38/45`, and every
   planted non-movement is exactly 0. So the battery returns the same verdict
   for any threshold in the half-open interval `[0, 7/9)`. **State it as the
   exact rational `7/9`, not as 0.778**: the earlier draft advertised
   `(0, 0.778)` and `0.778 > 7/9 = 0.7777...`, so a threshold of 0.7778 sat
   inside the advertised interval and would have failed the battery. An
   endpoint rounded outward is an endpoint that lies.

That interval lets the battery run before the base arm exists, which is the
ordering problem worth naming: standing rule 2 requires the battery to pass
before any J, and the registered movement threshold is derived from the base
arm, which does not exist until 120 generation calls are made.

**But robustness over a wide interval is bought by margins so extreme that the
battery never exercises the thing that will actually break.** Two consequences,
and neither is optional:

- **The battery tests extraction, not the movement rule.** At margins of 0 and
  0.78 every candidate implementation agrees: absolute or relative difference,
  `>` or `>=`, `q_base` or `q_variant` in the denominator, either sign
  convention. So a scorer that divides by the wrong term, or compares with the
  wrong operator, passes 4 of 4 and then decides real contrasts wrongly. A
  **near-threshold tier is required**, authored with planted margins just above
  and just below τ and run *after* τ is derived from the base arm, before J is
  computed. The extraction tier and the rule tier are different gates and only
  the first can run early.
- **The margins must not all point the same way.** Both planted movements
  currently go *down* (18 to 4, 90 to 14) while most governing arms in the
  corpus expect the quantity to go *up*. A scorer with a sign error passes this
  battery and returns zero sensitivity on the arms that matter. **At least one
  planted positive must move upward.**

Any further falsifier authored here holds the exact-rational endpoint, adds to
rather than narrows the direction coverage, and does not place the answer where
a bare first-or-last-numeral regex would find it — the current pair fails that
last test, which is recorded here rather than repaired silently.

## 8. Review

Every triplet is reviewed by an author who did not write it, briefed to break it
rather than approve it, and specifically to argue **that the matched fact
governs**. That is disqualifier 2 and it is the one that manufactures an
answer-key defect. A review returning "looks good" has not run.

Where the reviewer's objection to a matched fact is not clearly wrong, the item
is cut. Twenty triplets is a screening size, not a powered one; nineteen good
triplets beat twenty with one disputed label in them.
