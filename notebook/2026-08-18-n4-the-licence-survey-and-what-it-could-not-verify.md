# 2026-08-18 — N4's licence survey, and the two sources it killed

**This entry exists because a claim reached `docs/STATUS.md` before its evidence
reached the repository.** Earlier today that file and a notebook entry both
gained the sentence *"four candidates are licence-cleared"*, and the survey
behind it lived only in a session transcript. An audit of Track N5 went looking
for the record, could not find it, and said so — correctly, and it is the same
defect shape as the model tier that survived only as prose in a README. The
survey is written down here, with its caveats, and anyone may now check it.

Eight candidate sources were surveyed first-hand by two agents against
[`AUTONOMOUS_WORK_ORDER.md`](../docs/AUTONOMOUS_WORK_ORDER.md)'s outside-data
rule: free, redistributable, read before it lands, digest pinned. **No data was
downloaded.** This is a licence review, not an acquisition.

## The requirement, and why redistribution is the binding term

N4's artefact is a set of selected human-written turns with adjudicated labels,
checked into the repository as an answer key. `lost_in_conversation` sets the
precedent that a *payload* need not be committed — `de fetch` downloads it and
`verify()` refuses a hash mismatch — but N4's excerpts and labels have to live
in the tree or there is no holdout to run against. That module's own docstring
already states the principle: *"Both permit redistribution, which is why
fetching rather than vendoring is a size decision and not a licensing one."*

So download rights alone are not enough.

## Cleared

| source | licence | terms that travel |
|---|---|---|
| **OASST1** | Apache-2.0 | retain licence and notices; mark modified files. No share-alike |
| **WildChat-1M** | ODC-BY 1.0 | attribution notice naming the database. No share-alike |
| **Anthropic hh-rlhf** | MIT | preserve the copyright notice. Cleanest of the eight |
| **Stack Exchange dumps** | CC BY-SA | attribution *and* share-alike — see the conditions below |

**OASST1** is the strongest fit on consent: roughly 13,500 volunteers wrote
turns knowing they would enter a public open dataset. Its weakness is content
fit — it is a purpose-built assistant-training corpus, so decision-shaped turns
must be mined rather than assumed.

**WildChat-1M** is organic usage rather than volunteer recruitment, so it is
closer to the deployment distribution, and AI2 relicensed it from the old gated
ImpACT terms to ODC-BY retroactively. It carries a documented de-identification
pipeline (Microsoft Presidio plus hand-written rules) with PII- and
toxicity-flagged conversations removed.

**hh-rlhf** is legally the cleanest and the worst fit: crowdworker prompts to a
chatbot, roughly half of it adversarial red-teaming, so the yield of genuine
decision turns would be low. Its card also asks that it not be used to train
dialogue agents — not a licence restriction and not what N4 would do, but
Anthropic's stated intent and worth respecting.

**Stack Exchange has the best content fit and the most expensive terms.** Whole
sub-sites are structurally "should I do X or Y". But CC BY-SA's ShareAlike
clause plausibly makes a labelled selection "Adapted Material", which would
push BY-SA-compatible terms onto the derived corpus *and the paper*, on top of
four attribution conditions (name the network, link the original question, name
the author, link the author's profile). Two further complications, both
material: since July 2024 the official download is login-gated behind a
click-through that asks the downloader to agree the file is not for LLM
training, and community mirrors report that Stack Exchange has been **seeding
deliberately fabricated data** into recent dumps as an anti-scraping measure.
If this source is used it must be the pre-gate archive.org copy, and the
poisoning risk is a data-integrity problem for a labelled holdout, not only a
legal one.

## Killed, and the reasons are worth keeping

**LMSYS-Chat-1M — not usable.** Its licence says: *"You should not distribute,
copy, disclose, assign, sublicense, embed, host, or otherwise transfer the
dataset to any third party."* Download is separately gated behind a login and
contact-sharing agreement. **This is the source closest to N4's ideal** — real
turns people sent to a chat assistant — and it fails on exactly the clause the
2026-08-18 prediction said to watch for: *"I would not be surprised if the
closest fit to the deployment distribution is the one that cannot be
redistributed."* That prediction was right.

**ShareGPT — not usable, and worse than LMSYS.** LMSYS at least has a licence
from someone entitled to grant one. ShareGPT's chain is: ChatGPT users → a
third-party sharing site → an anonymous bulk scrape → a HuggingFace upload
tagged Apache-2.0. **The tag is the uploader's, on content they did not own.**
The concern is public and unresolved on the record (FastChat issue #1284, opened
2023, no maintainer resolution), and there is no documented PII handling at all
— against WildChat's named pipeline, that is the difference between a considered
release and a dump.

**Reddit-derived corpora — not usable.** Two questions with different answers:
a mirror can tag its upload CC-BY-4.0, while Reddit's own API terms (quoted by a
dataset maintainer on their card) reserve rights and state that no right is
granted *"to use User Content for training a machine learning or AI model,
without express permission."* Pushshift's public API closed in 2023. And the
advice subreddits that would be most valuable here are the ones documented as
carrying the most self-disclosed personal detail.

**Ask MetaFilter — not usable, and not for a licence reason.** There is no
official full-text dump: the Infodump and the "MetaFilter Corpus" are metadata
and word-frequency tables, and the Infodump's own documentation says its length
fields are *"a raw character count of each field... not the actual content"*.
Getting turns would mean scraping live pages, and every attempt to read the
content policy that would govern that returned 403.

## What this survey did not establish, stated plainly

**The licences were read through a fetch tool that summarises rather than
scrapes byte-exact**, and both agents said so. Specifically:

- **OASST1's Apache-2.0 rests on the HuggingFace metadata tag**, checked three
  ways; no licence section was located in the dataset card itself. A secondary
  mirror describes the data as CC0, which could not be substantiated at source
  and is recorded here as unverified rather than adopted.
- **OpenAI's terms of use returned HTTP 403** on every attempt, so the claim
  that ChatGPT users own their outputs — which is what makes ShareGPT's chain
  fail — is second-hand. It does not change the verdict, because ShareGPT's
  problem is the *absence* of any grant, not the presence of a hostile one.
- **Reddit's User Agreement could not be opened directly.** The quoted
  no-AI-training clause comes from a dataset card reproducing it.
- **Stack Exchange's per-era CC BY-SA versions (2.5 / 3.0 / 4.0) are
  search-sourced**, not read from the licensing page, which the tool refused.

**So no source may be fetched on the strength of this entry alone.** Before
anything is downloaded, the chosen source's licence gets read directly, a sample
gets read for personal information rather than trusted on the licence, and a
digest gets pinned. That is four steps, all free, and this entry is the first of
them rather than a substitute for the rest.

## Where this leaves N4

**OASST1 is the recommendation**, on consent and on licence simplicity, with
WildChat-1M the alternative if the holdout needs to look more like real
assistant traffic and the weaker consent posture is judged acceptable. Stack
Exchange is the best content fit and should be treated as a considered choice
about accepting share-alike on the paper, not a default.

None of that is decided here, and the prediction registered this morning still
stands unmeasured: the human corpus should be **harder** than the authored one,
with the arms scoring lower and the between-arm spread narrowing. If the arms
score *higher* on human text, something is wrong with the authored corpus that
258 items of gating did not catch.
