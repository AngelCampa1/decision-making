# 2026-08-18 — prediction: N5's descriptive probe, which has never run

Registered **before** the first call. N5's realism row has sat at "never run"
since it was written; the human audit half was retired this afternoon
([entry](2026-08-18-every-human-gate-comes-out-of-the-plans.md)), and what is
left is a call budget rather than a gate.

## What will be computed, from which records, over which denominator, by which function

Written out because four pre-registration slips on 2026-08-12 came from not
writing this sentence.

- **Estimator:** the `composed` rate — the share of judged turns a blind judge
  calls *authored for a benchmark* rather than *a message a real person sent*.
  Computed by `scripts/realism_probe.py`'s report path.
- **Records:** one JSONL checkpoint, one record per item, stamped with
  `set_version`, `model` and `prompt_sha`.
- **Denominator:** **parsed replies**, not items sampled. Unparseable replies
  are reported separately and excluded, and the report prints unreadable
  replies per band so a stratum that loses every reply cannot print a rate.
- **Sample:** **86 items, one per matched triple**, over 258 items / 86 triples
  at answer key **v4**. One per triple is forced by the design, not chosen: the
  long bands share a byte-identical body across all three members, so two items
  from one triple are very nearly the same text and their verdicts are not two
  observations.
- **Tier:** `haiku`, the probe's default, which matches `scripts/adjudicate.py`
  so the two passes over this corpus are made by the same tier. **A chosen
  default, not a derived one** — the script says so itself, and what would
  settle it is running both tiers.
- **Calls:** 86.

## What this cannot say, and it is most of what one would want

**There is still no human-written comparison set.** So a `composed` rate is a
statement about one model's prior over message text, not about whether this
corpus is valid. It is descriptive by construction: **no threshold here retires
the corpus**, and the number is reported and left alone. The forced choice that
would carry a ground truth waits on N4's source clearing the outside-data rule,
and nothing has been fetched.

The dry-run harness was exercised first with the `mixed` stub — 86 records, 0
unparseable, an interior rate with a Wilson interval, and the report's own
non-degeneracy line printing *"the measure varied across items, so it could
have come out otherwise."* That is standing rule 2's check in the only form
available here: not that the falsifier is right, but that some possible response
would have scored differently.

## Predictions

- **The `composed` rate will exceed 0.50.** The corpus was written to a grid —
  matched triples, a fixed 1:2 ratio in every band, four length bands with hard
  boundaries — and three authoring leaks have already been found in it (a
  word-count ruler at AUC 0.890, an `open`-view opener at 0.779, `_shared_body`
  cutting at a space). A judge asked *"did a person send this"* over text built
  that way should say no more often than yes.
- **The rate will be higher in `l` and `xl` than in `s` and `m`.** A 25-word ask
  gives a judge almost nothing to catch; 1,200 words of authored situation gives
  it a great deal. This is the direction the long-context plan already worries
  about — *"a hundred thousand tokens of unconvincing correspondence is a worse
  artefact than three hundred tokens of it."*
- **The rate will not differ much by label.** The judge is never told the corpus
  is about decisions and never sees a skill, so a positive/negative gap would be
  a property of how the two were authored rather than of what the judge was
  asked. If a large gap appears, the interesting reading is that the negatives
  were written to be inert and read as exercises because of it.

## Where I expect to be wrong

**The band prediction may be an artefact of the instrument rather than the
corpus.** The typography table already shows every `l` and `xl` item carrying an
em or en dash and no `s` or `m` item carrying one — a real difference in the
text, and one a judge could be keying on entirely apart from whether the writing
reads authored. If the band gap appears *and* tracks that column, the finding is
about punctuation, not realism, and the entry that reports it has to say so.

**And the whole thing may be uninformative in a way no number will announce.**
If the rate comes back near 0.5 with wide intervals everywhere, the honest
reading is that a single-item verdict cannot recover the judge's base rate —
which is the argument `realism_probe.py`'s own docstring makes for why this
instrument was a downgrade taken on purpose.
