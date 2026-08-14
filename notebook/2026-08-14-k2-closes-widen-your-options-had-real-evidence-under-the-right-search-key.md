# K2 closes: "widen your options" had real evidence all along, and it was hiding behind the wrong search key

**2026-08-14.** Not a run — a desk review, closing Track K2 (the *prescriptive*
evidence pass over the eleven-framework catalogue). Full write-up in
[`docs/DECISION_FRAMEWORKS.md`](../docs/DECISION_FRAMEWORKS.md). K3 and K4 were
being worked concurrently in the same file by another session; both files were
re-read immediately before each edit rather than once at the start, and the
table and prose were reconciled against the other session's changes several
times mid-task rather than merged at the end.

## What K2 still owed

Three rows of the K1/K2 catalogue stood at `none located` after two passes on
2026-08-12: Kepner-Tregoe, WRAP, OODA. The second pass had already found the
productive move once — searching for "structured decision support" instead of
named frameworks turned up the patient-decision-aids literature (209 RCTs) —
but had not yet applied that move to the three remaining rows individually. The
task was to run a fourth pass that did, and to report, for each, one of: a
trial with an effect size; evidence that measures something other than
decision quality; or genuinely nothing after a real search.

## What moved

**WRAP.** The framework's four letters were searched one at a time as
constructs rather than as one brand name. Three of the four ("reality-test",
"attain distance", "prepare to be wrong") still returned nothing. The fourth —
"widen your options" — resolved cleanly to a testable claim: does considering
more than one option, or considering them concurrently rather than serially,
produce a better choice? That claim has been tested, more than once,
independently:

- Basu & Savani (2017), *OBHDP* 139: seven lab experiments, ≈2,892 participants
  total. Presenting options simultaneously rather than sequentially raised the
  rate of choosing the objectively dominating option by 7–16 percentage
  points, every comparison significant (Exp 1 p=.007, Exp 2 p=.02, Exp 3
  p<.0001). Verified first-hand via the NTU institutional-repository copy,
  after ResearchGate and ScienceDirect both blocked WebFetch with a
  verification wall.
- Dow et al. (2010), *ACM TOCHI* 17(4): n=33, between-subjects. Designers who
  produced multiple ad prototypes in parallel before feedback beat designers
  who iterated serially, on both a real behavioural outcome (click-through:
  445.0 vs 397.9 per million impressions, p<.05) and expert ratings (p<.05).
- Hauschildt & Gemünden (1985), *EJOR* 22(2): correlational, not a trial —
  archival analysis of 83 real executive-board decisions at one German firm.
  "Alternative designing has a strong positive impact on decision quality."
  This turned out to be the actual paper behind the "University of Kiel"
  study *Decisive*'s own endnotes cite for this exact chapter — found by
  fetching the endnotes PDF directly rather than trusting a book summary.

None of this rescues WRAP as an integrated four-step procedure — no trial of
the whole four steps together exists, and this evidence is silent on the other
three letters. But it means one quarter of a framework this document had
graded `none located` had real, multiply-replicated, still-standing evidence,
and the only reason it hadn't surfaced by 2026-08-12 was that "WRAP" and
"Heath & Heath" are not what the relevant researchers call it.

**This changes K6's ranking, not just K1/K2's table, and is reported as such
rather than folded in quietly.** "Generate options concurrently" now enters
K6 at Rank 2, ahead of consider-the-opposite — Basu & Savani's evidence
(seven experiments, all significant) is stronger by this document's own
standard than consider-the-opposite's (two original experiments plus a later
replication that moved the right direction without reaching significance).
Both stay below calibration training, which remains the strongest single
effect in the table despite being contested.

**Kepner-Tregoe** got no equivalent win, and a fourth search — brand name plus
constructs like "structured problem-solving training" and "weighted decision
matrix training" — still found nothing. But the decomposition exercise that
worked for WRAP clarified *why* KT stays empty: its "decision analysis" step
is the same construct this table already grades as **Decision analysis /
MAUT** ("normative, not prescriptive"), and its "potential problem analysis"
step is the same shape as **Pre-mortem** ("misreported"). KT's `none located`
verdict was never really about an unstudied idea — it was about an unstudied
*bundle* of two ideas that already have grades elsewhere in the same table.

**OODA** stays `none located` for the loop as advice to a human, with one
addition: Bryant (2006, *Military Psychology*) is an academic, not a
consultancy, source arguing the loop "is no longer current with modern
theories of human cognition" — read first-hand to the abstract (full text
paywalled). It is a theoretical critique, not a trial, so the grade does not
move, but it is a better-grounded "no" than the marketing and simulation
material the second and third passes turned up.

## What was found and not used

Priyanath & Chaminda (2019), a Sri Lankan small-enterprise survey regressing
"business fog" on OODA-strategy use, kept surfacing in search results with a
plausible-sounding result (mostly non-significant, one significant
coefficient). Every fetch attempt — ResearchGate, direct PDF — returned a
CAPTCHA or verification wall. No number from it appears anywhere in this
repository. Even if it had opened, it would not have moved the OODA grade: it
measures a self-reported "fog" construct, not decision quality, so its proper
home was always the "measures something else" bucket, not a fourth supported
row — worth writing down since the temptation to use an unopened source is
strongest exactly when the number it promises is convenient.

**A near-miss that the citation rule caught before it entered the document.**
While researching Kepner-Tregoe, one WebSearch tool call summarised a result
as: "Research indicated that individuals who received training in this
method demonstrated improved decision-making skills... (Johnson et al.,
2012)." No journal, no title, and a direct follow-up search found no
resolvable paper behind it. Not used. This is the same failure standing rule
5 exists to prevent — a plausible citation nobody opened — except the source
this time was a search engine's own summarisation rather than a human
recalling from memory. Worth flagging as a variant: **a tool's synthesis of
search results is not itself a source**, and needs the same "did I actually
open this" check as a half-remembered paper does.

## Mechanical notes

Direct `WebFetch` returned unparseable binary/FlateDecode-stream content for
every academic PDF tried on this pass, across four different hosts (Stanford
HCI, CMU, aaalab.stanford.edu, and a signed NTU repository URL). The
`r.jina.ai` text-extraction proxy worked reliably on the same URLs and is how
every verbatim quote in this pass's `paper/refs.bib` entries was obtained —
recorded per entry rather than silently, since it is a different verification
path than the "fetched the identifier directly" pattern used earlier in this
document.

New bibliography entries, each with a `quote` field read from the primary
source: `dow2010parallel`, `basusavani2017`, `hauschildtgemunden1985`,
`bryant2006ooda`.

## What is not closed

K1/K2's table now has real evidence for one quarter of one previously-empty
framework. It does not license shipping "WRAP" or even "widen your options"
as a skill without also checking K4's failure-mode question — does this
model's own unaided reasoning actually default to a narrow, single-option
answer? That question is still `assumed`, not `documented`, per K4's table
(closed concurrently by another session today). The K6 promotion is
evidence-side only; the LLM-failure-side case for it is exactly as open as it
was before this pass.

## Sources

Full list with verbatim quotes in
[`docs/DECISION_FRAMEWORKS.md`](../docs/DECISION_FRAMEWORKS.md#sources-checked-on-2026-08-14-k2-fourth-pass).
