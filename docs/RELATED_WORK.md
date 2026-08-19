# Related work

The evidence base this project is built on, current as of August 2026. Organised
by what each finding *does* for the design rather than by topic, because several
of these changed decisions rather than merely informing them.

Confidence is flagged where it matters. A LessWrong re-analysis and an ICLR oral
are both cited here, and they should not be read as carrying the same weight.

---

## 1. The failure modes

### Distractor sensitivity and the 2026 correction

**Mirzadeh, Alizadeh, Shahrokhi, Tuzel, Bengio, Farajtabar (Apple),
"GSM-Symbolic"**, arXiv:2410.05229. Inserting a single topically relevant but
logically irrelevant clause dropped accuracy by up to 65%. This is the canonical
statement of the "it's raining in Paraguay, so grab a raincoat" failure, and the
source of our dataset methodology: parameterised templates with computed ground
truth.

**Revisiting GSM-Symbolic (2026 re-audit)**. A re-analysis found the collapse was
largely an artifact of *ambiguous* distractors that a reasonable solver would
fold into the calculation. After a two-auditor filter kept 117 of 945 candidates
(12.4%) as genuinely irrelevant, the residual drop on GPT-4o, Claude Opus 4.6 and
Haiku 4.5 was statistically indistinguishable from zero. Confidence: low-medium,
a LessWrong re-analysis, not peer-reviewed.
*Effect on design:* our distractor audit replicates the two-auditor filter, we
expect heavy attrition, and expected effect size is revised down, which raises
required N. This is the single largest threat to the flagship skill's premise,
and we treat it as one rather than omitting it.

**Chroma Research, "Context Rot"** (2025), 18 models including Claude Opus 4.
Models above 95% on short prompts fall to 60-70% with semantically related
distractors. One strong distractor hurts more than four weak ones, and coherent
context degrades attention *more* than shuffled context. 2026 commentary adds
that the U-shape holds only while context is under ~50% full.

**"Diagnosing and Mitigating Context Rot in Long-horizon Search"**,
arXiv:2606.29718. It relocates the effect into agentic search, where it is still
documented at 30-50% degradation. *Effect on design:* the flagship is aimed here
rather than at math-word-problem distractors.

**Liu et al., "Lost in the Middle"**, arXiv:2307.03172. U-shaped position
sensitivity in long contexts. **"Lost in the Middle at Birth"**
(arXiv:2603.10123) deepens that result rather than overturning it, with a
training-time theoretical account. The account implies the mitigation is
reordering and pruning, not prompting.

**Chen, Lin et al., "Benchmarking LLMs in RAG" (RGB)**, arXiv:2309.01431,
AAAI-24. LLMs are specifically weak at *negative rejection*: recognising that
retrieved context does not contain the answer.

### Does telling a model to ignore something work?

**"Unable to Forget"**, arXiv:2506.08184, and the I³C line
(arXiv:2403.12744). Bare negation instructions have marginal effect, and the
effect degrades further as the irrelevant item becomes more semantically
related. A two-step
*verify-then-discard* structure does work. *Effect on design:* the flagship
splits verification and discard into two visible steps, and this is the direct
justification for that structure.

**"Escaping the Context Bottleneck: Active Context Curation for LLM Agents via RL"**,
arXiv:2604.11462. A curator decoupled from a frozen executor lifted WebArena
36.4% → 41.2% with 8.8% *fewer* tokens, and cut DeepSearch tokens by 8×; a 7B
curator matched GPT-4o-level context management.
*Effect on design:* resolved the project's biggest open question. The forked
variant became primary and inline became a comparison arm.

**ACE, "Agentic Context Engineering"**, arXiv:2510.04618 (Stanford/SambaNova,
ICLR 2026 oral). Incremental playbook curation over Generator/Reflector/Curator
roles, which avoids brevity bias and context collapse; +10.6% on agent
benchmarks. We prefer it to whole-prompt rewriting for any self-improvement loop.

### Abstention, over-calling, and sycophancy

**AbstentionBench**, arXiv:2506.09038. Abstention is unsolved and does not
improve with scale; reasoning-tuned models are ~24% worse at abstaining than
their base counterparts.

**"To Call or Not to Call"**, arXiv:2605.18882. Models issue unwarranted tool
calls at a much higher rate than they correctly withhold warranted ones. Still
current, and we have found no 2026 work that contradicts it.

**"When Truth Is Overridden"**, arXiv:2508.02087. First-person prompts ("I
believe...") "consistently induce higher sycophancy rates than third-person
framings", because they perturb representations more strongly in deeper layers.
The direction is the paper's own; it states no rate, so none is given here.
*Effect on design:* the flagship restates user assertions in the third person
before evaluating them. That is an *extrapolation*, since a self-applied rewrite
is not the same manipulation the paper tested, and the skill's own evidence file
flags it as one.

**Malmqvist, "Sycophancy in Large Language Models: Causes and Mitigations"**,
arXiv:2411.15287. A single-author technical *survey* of the area, which reviews
other people's measurements rather than running any.

> **Correction, 2026-08-13.** This entry previously read "First-person opinion
> statements induce agreement with *incorrect* beliefs at 63.7% average across
> seven model families", attributed to arXiv:2411.15287. Its abstract contains
> no percentage of any kind and names no model family, and describes itself as
> a technical survey that reviews other people's measurements. We removed the
> figure rather than softening it, and we did *not* move it onto
> arXiv:2508.02087, whose abstract is directional and gives no rate either. If
> the 63.7% is real it belongs to one of the studies the survey reviews, and it
> may be cited once that study is opened. Verified first-hand against both
> abstracts.

**"The Bias is in the Details"**, arXiv:2509.22856. 45 LLMs, 2.8M responses,
8 biases. Bias-consistent behaviour in 17.8-57.3% of instances; scale reduced
bias in only ~39.5% of cases; more detailed prompts reduced most biases by up to
14.9% but *worsened* overattribution by up to 8.8%.

---

## 2. What to do instead

**AgentAtlas, "Beyond Outcome Leaderboards for LLM Agents"**, arXiv:2605.20530.
Six control gates (Act, Ask, Refuse, Stop, Confirm, Recover) with named failure
modes. (The category *missing irreversibility* this entry used to name is in
neither abstract and is unverified.) The taxonomy is unchanged across both
versions of the paper and is what we adopt. *Effect on design:* we take it as the
control taxonomy, and it is the reason option menus stay constant across all
arms.

The paper's own figure for removing the option menu is v1-only, and anyone using
it has to name v1:

> arXiv:2605.20530v1, 19 May 2026: "Removing the explicit label menu drops
> every model's trajectory accuracy by 14-40 pp to a tight 0.54-0.62 floor
> regardless of family."

v2 (26 May 2026) removed that sentence and replaced the quantity with "mapped
label agreement can change substantially", which is no number and a different
measure name. It also added that the synthetic study "should not be read as a
'definitive model comparison'". Both versions disclaim the run as a
demonstration on a synthetic 1,342-item set rather than a benchmark release: v1
as a "measurement-protocol demonstration", v2 as an "illustrative protocol
study". The phrase differs; the disclaimer does not. Verified first-hand
against both abstracts, 2026-08-13.

**"Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents"**,
arXiv:2603.26233. Decoupling underspecification detection from execution lifted
the task resolve rate from 61.20% to 69.40% on an underspecified variant of
SWE-bench Verified, for OpenHands + Claude Sonnet 4.5 (the v1 abstract's
configuration; v2 states the 69.40 across proprietary and open-weight frontier
models without naming a baseline). Both figures live inside the degraded
variant, and the abstract implies its own fully specified baseline sits *above*
the 69.40 headline, since it describes the scaffold as "closing the performance
gap" with it. That is an inference from the phrase, not a figure anyone read,
so this is not a SWE-bench Verified leaderboard movement and must not be read
beside one. The calibration result (fewer questions on easy
tasks) is qualitative in the abstract. It supersedes SAGE-Agent
(arXiv:2511.08798) as the primary citation for EVPI-gated clarification.

**Flyvbjerg, Holm, Buhl**, *JAPA* 2002, and Flyvbjerg 2006/2008: reference class
forecasting. Rail, bridge/tunnel and road overruns average 45%, 34% and 20%,
stable across decades and largely independent of project-specific planning
quality. The APA adopted it in 2005, as did the UK Treasury Green Book. A genuine
three-step algorithm, which is why it survived the framework cut.

**Tetlock & Gardner**, *Superforecasting* (2015): outside view before inside
view, Fermi decomposition, small frequent updates, calibration tracking.

**Kahneman, Sibony, Sunstein**, *Noise* (2021), ch. 25, the Mediating
Assessments Protocol: independent sub-assessments scored in isolation, combined
mechanically. It targets *noise* (variance), which is a different disease from
bias and needs saying plainly so the council's claims stay honest.

**Klein**, "Performing a Project Premortem", *HBR* Sept 2007. Prospective
hindsight improves identification of failure causes by roughly 30%.

**"Trust Over Fear"**, arXiv:2603.14373. Trust-framed system prompts surfaced
59% more hidden issues; fear-framing showed no significant gain over unframed.
*Effect on design:* it is why every skill and the shipped `AGENTS.md` block are
worded the way they are.

---

## 3. Calibration

**Tian, Mitchell, Zhou, Sharma, Rafailov, Yao, Finn, Manning, "Just Ask for
Calibration"**, arXiv:2305.14975, EMNLP 2023. For RLHF'd models, verbalised
confidence is better calibrated than token-level probabilities and cuts expected
calibration error by roughly 50%.

**OpenAI, "GPT-4 Technical Report"**, arXiv:2303.08774, Fig. 8. The pretrained
model is well calibrated on multiple choice; RLHF degrades it.

**Kadavath et al., "Language Models (Mostly) Know What They Know"**,
arXiv:2207.05221.

**"Calibration Drift Under Reasoning"**, arXiv:2606.11211. Calibration improves
then *degrades* past a reasoning-budget threshold, non-monotonically.
Confidence: directional, tested on Llama-3.1-8B/3.3-70B, with the 70B result
inconclusive. *Effect on design:* we treat "let the model think longer and its
confidence will improve" as false.

**smECE**, arXiv:2603.14092, and the smoothECE line. Debiased, kernel-smoothed
calibration error. *Effect on design:* it replaces raw-bin ECE as the headline
calibration estimator, and binned ECE stays as a secondary for comparability.

**ForecastBench**, arXiv:2409.19839, ICLR 2025. Contamination-proof by
construction (questions have no answer at submission time). Top LLMs ~0.122-0.136
Brier; superforecasters ~0.096; general public ~0.121.

**Murphy decomposition**, `Brier = Reliability − Resolution + Uncertainty`. The
reason a resolution floor is a hard guard: a forecaster that always predicts the
base rate is perfectly reliable and useless.

---

## 4. Judges and councils

**Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"**,
arXiv:2306.05685, NeurIPS 2023. Strong LLM judges like GPT-4 "can match both
controlled and crowdsourced human preferences well, achieving over 80%
agreement, the same level of agreement between humans."

> **Correction, 2026-08-13.** This read "GPT-4 judge agreement with humans
> ~85%, above human-human agreement ~81%", which asserts that the judge *beats*
> human-human agreement. The abstract claims parity, not superiority, and gives
> a floor ("over 80%") rather than the 85/81 pair, which is not in it. The
> inequality pointed the wrong way, which is the same defect shape as the
> arXiv:2605.29800 correction further down this same section.

**Liu et al., "G-Eval"**, arXiv:2303.16634, EMNLP 2023. CoT rubric
decomposition; Spearman 0.514 with humans on summarisation.

**Verga et al., "Replacing Judges with Juries" (PoLL)**, arXiv:2404.18796.
Three small judges from different providers beat a single GPT-4-class judge
across six datasets at ~7× lower cost, with reduced self-preference bias.
Superseded: see below.

**RoPoLL**, arXiv:2606.30931. PoLL incurs *unbounded* bias under any positive
contamination, regardless of jury size. A geometric-median estimator (breakdown
point ½) gives ~19% improvement under cross-dimensional attack; a 3-judge 38B
robust committee beat a 675B single judge by 1.31× under 30% corruption.
*Effect on design:* aggregation is a robust estimator, never a mean.

**"Nine Judges, Two Effective Votes"**, arXiv:2605.29800. Nine frontier LLMs
from seven families "effectively provide only about 2 independent votes' worth
of information", because they make the same mistakes on the same items. The
panel's accuracy "falls 8-22 percentage points short of what independent voting
would achieve, and the best single judge matches or outperforms the full panel
across all conditions". "Established methods close at most 11%" of
that gap even with access to the correct answers. *Effect on design:* this is a
structural ceiling, not an aggregation problem. We cap the council at three
judges chosen for divergent failure modes, and it must report effective sample
size or its diversity claim is decorative.

> **Correction, 2026-08-13.** This entry previously read "Panel lift over the
> best single judge: **+0.2pp** against a predicted-under-independence 22pp",
> which was wrong twice over. It reported the top of a range as a point value
> (the paper says 8-22 pp), the same defect this repository has recorded
> against a registered band that named a number without its estimator. And it
> compared two different quantities: the 8-22 pp is a *shortfall of the panel
> against a Condorcet independent-voting ideal*, while +0.2pp was a *lift of
> the panel over the best single judge*, a lift the abstract contradicts
> outright, since it says the best single judge matches or outperforms the
> panel. The effective sample size 2.18, its CI and the mean pairwise
> correlation 0.391 are not in the abstract and are unverified; "about 2
> independent votes' worth" is what the paper states, so that is what is
> quoted. Verified first-hand.

**Position bias**, arXiv:2406.07791 (15 judges, >150,000 instances; repetition
stability, position consistency, preference fairness), refined by
arXiv:2604.23178. **Self-preference**, arXiv:2410.21819. **Scoring bias**,
arXiv:2506.22316. **CALM bias framework**, arXiv:2410.02736.

**Shankar et al., "Who Validates the Validators?" (EvalGen)**, arXiv:2404.12272,
UIST 2024. *Criteria drift*, in the paper's own words: "users need criteria to
grade outputs, but grading outputs helps users define criteria". So a judge
aligned once does not stay aligned, and some criteria turn out to be *dependent*
on the outputs observed rather than definable a priori.
*Effect on design:* we report TPR and TNR separately against a deliberately
failure-heavy calibration set, and recalibrate whenever the pipeline changes.
(The agreeableness-bias figure this entry used to carry, "a judge can look
>90% accurate by blended agreement", is not in the abstract and is unverified,
so it is gone. The design decision rests on criteria drift, which is verbatim,
and is unaffected.)

### Multi-agent debate

**Du, Li, Torralba, Tenenbaum, Mordatch**, arXiv:2305.14325, ICML 2024. The
founding positive result.

**"Stop Overvaluing Multi-Agent Debate"**, arXiv:2502.08788. Five MAD methods ×
nine benchmarks × four models: debate often fails to beat single-agent CoT +
self-consistency despite far more compute. Model *heterogeneity* is what rescues
it.

**"The Cost of Consensus"**, arXiv:2605.00914. Isolated self-correction beats
unguided homogeneous debate on modern instruction-tuned models at 2.1-3.4× less
token cost.

**"Peacemaker or Troublemaker"**, arXiv:2509.23055. Debaters converge on the
most confidently asserted position rather than the most correct one.
*Effect on design:* in any second round, we strip author identity, score values
and confidence markers from the arguments judges see.

**Huang, Chen, Mishra, Zheng, Yu, Song, Zhou (DeepMind), "LLMs Cannot
Self-Correct Reasoning Yet"**, arXiv:2310.01798, ICLR 2024. Intrinsic
self-correction without external feedback can *degrade* performance. *Effect on
design:* the council's first decline gate is "would a test, query or lookup
settle this?", because a council over a verifiable question is self-correction
with extra steps.

**Wang et al., "Self-Consistency"**, arXiv:2203.11171. The cheap ensemble
baseline any council must beat at matched token budget.

---

## 5. Skills as an intervention

**Xu & Wu, "Skill Availability and Presentation Granularity in LLM Agents"**,
arXiv:2605.31408. A 30-task domain-balanced SkillsBench subset, 2 models,
six skill conditions, five trials, 1,800 rows. (An earlier draft of this entry
said "86 tasks, 11 domains", which confused this paper's scale with
SkillsBench's own, and SkillsBench is 87 tasks and 8 domains, so both halves
were wrong, in the direction that made this paper look bigger. Verified
first-hand 2026-08-12.) Skill availability: +26.7 to +36.0pp
(GPT-5.5), +18.0 to +26.0pp (DeepSeek V4-Flash). Granularity of the skill's
prose: +0.7pp (GPT-5.5), −6.7pp (DeepSeek), CIs crossing zero. Worked
examples: +0.7-1.3pp. *Effect on design:* engineering effort goes into triggering
and availability, not wordsmithing.

**SkillOpt, "Executive Strategy for Self-Evolving Agent Skills"**,
arXiv:2605.23904, Microsoft Research, code at `github.com/microsoft/SkillOpt`.
It treats `SKILL.md` as a trainable parameter: bounded edits ("textual learning
rate"), a held-out validation gate, a rejected-edit buffer, epoch-level
consolidation. Six benchmarks, seven target models, three execution harnesses.
On GPT-5.5 it lifts average no-skill accuracy by +23.5 points in direct
chat, +24.8 inside Codex and +19.1 inside Claude Code. The harness
must travel with the number, since it is the paper's own largest source of
spread and this document's own methodology section (arXiv:2605.23950) exists to
say so. An earlier version of this entry gave "+23.5pp" as an average across
benchmarks with no harness named.
*Caveats we take seriously:* no confidence intervals, no significance tests, and
no correction for the many implicit comparisons its accept-if-strictly-better
ratchet performs; benchmark selection restricted to tasks with crisp automatic
scoring, and not flagged as a limitation; a target-matched optimiser recovers
only 56-74% of the gain, which implies an unacknowledged distillation component.
*This paper and SkillsBench are in direct tension, and adjudicating it is one of
this project's stated contributions.*

**"On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents"**,
arXiv:2601.20404. 124 PRs across 10 repos. The abstract's figures are
medians: −28.64% runtime, −16.58% output tokens. (The −20.27% and −20.08%
*means* this entry used to lead with are not in the abstract and have not been
checked against the body; nor has the claim below. Verified first-hand
2026-08-12 as far as the abstract goes.) The benefit is said to concentrate in
a small number of very expensive runs rather than spreading uniformly.
*Effect on design:* we report p90/p99 alongside means.

**"Authoring Agent Skills: A Software-Engineering Approach"**, arXiv:2607.25032.
Single responsibility, interface/implementation separation enforced by loading
timing, low coupling, token economy. Its behavioural-evaluation loop supplies one
concrete safeguard we adopt: test with a fresh model instance, not the one that
drafted the skill. *Confidence: principles paper, no benchmark numbers.*

**"From Anatomy to Smells: An Empirical Study of SKILL.md"**, arXiv:2607.01456.
Defect taxonomy for skill files. We use it as a pre-ship self-audit.
*Prevalence figures unverified; the taxonomy is the usable part.*

**Agent Skills security study**, arXiv:2601.10338. 26.1% of a sampled skills
corpus contained at least one vulnerability across prompt-injection,
data-exfiltration, privilege-escalation and supply-chain categories.

---

## 6. Methodology

**"Stop Comparing LLM Agents Without Disclosing the Harness"**,
arXiv:2605.23950. A position paper, arguing the *Binding Constraint Thesis*: for
long-horizon tasks across models of comparable frontier capability, the harness
"is often a stronger determinant of agent performance than the model it wraps",
so current protocols "systematically misattribute harness-level gains to model
improvements". Its support is a control-theoretic formalisation, a survey of
published benchmarks and deployments, and a controlled variance decomposition in
which harness-induced variance "can substantially exceed" model-induced
variance, "including cases of model ranking reversal". It supplies the ETCSOVG
disclosure checklist. *This is the premise of the whole project: the scaffold is
the dominant variable, and it is the one nobody reports.*

The variance decomposition is the authors' own experiment, and its numbers are
in the body rather than the abstract (§4.2 and Table 2, verified first-hand
against `arxiv.org/html/2605.23950v1` on 2026-08-13). Three frontier models
"selected because they were tightly clustered on the LLM Stats coding
leaderboard" are crossed with three harness configurations "on a
difficulty-stratified 100-task subset of SWE-bench Verified", two independent
runs per cell:

> "Changing the harness moves GLM-5.1 by 13.0 percentage points and GPT-5.4 and
> Kimi K2.6 by 8.5 points each." … "Changing the model within a fixed harness
> moves scores by only 3.0, 2.5, and 5.0 points for H₁, H₂, H₃." … "Aggregate
> HV̄/MV̄ ratio: 7.80×." … "Ranking reversal pairs: 6 out of 9
> model-pair/harness-pair comparisons."

Because it is a single 3×3 design with two runs per cell, the 7.80× is one
estimate from one task distribution, not a general constant. The direction is
what this repository leans on, and it does not treat the ratio as transferable.

> **Correction, 2026-08-13.** This is the one that should worry a reader most.
> This entry read "Controlled 3×3 factorial, 100 SWE-bench Verified tasks:
> **harness variance / model variance ≈ 7.8×**. Harness changes moved scores
> 8.5-13 points, model changes 2.5-5 points, with **six ranking reversals in
> nine comparisons**." None of those four figures is in the abstract, and
> the paper is a position paper rather than the empirical study the phrasing
> implied. The abstract does describe a controlled variance decomposition, so
> the numbers may be its body's; they are *unverified*, not shown absent. The
> sentence they supported is the one this repository uses to justify its own
> existence, and a premise resting on a figure nobody opened is precisely the
> failure the citation gate was built for. The qualitative direction above
> survives intact and the design decisions that rest on it are unaffected.
>
> They are out of this file and out of `PROTOCOL.md` §9. They are still in
> two others, and an independent check found that, not the author: they
> remain in `docs/HARNESS_DISCLOSURE.md` (all four, plus arXiv:2605.27922's
> 23.8-point swing, in the opening paragraph of the file whose whole subject is
> disclosure discipline) and in `docs/LIMITATIONS.md` for the separate n_eff
> 2.18. A first draft of this notice said they were "out of the prose" full
> stop, which was false when written. A retraction is not done when the
> entry is fixed; it is done when every file carrying the figure is fixed, and
> nothing here checks that. The citation gate binds a number to a *quote*, not
> a withdrawn number to its other homes.

> **Correction to the correction, 2026-08-13, later the same day.** The
> retraction above was too broad, and the figures are restored. The notice was
> right that none of the four is in the abstract, and right to flag them as
> *unverified* rather than absent. But the retraction was then propagated as
> though "not in the abstract" meant "not in the paper". It does not. Two agents
> that did not share context fetched the full text at
> `arxiv.org/html/2605.23950v1`, and all four figures are in §4.2 and Table 2,
> verbatim, as the output of a 3×3 experiment the authors ran themselves. They
> are restored to the entry above with the section named.
>
> So the defect was never fabrication. It was citation hygiene: a body figure
> cited as though the abstract carried it, in a repository whose standing rule is
> to cite nothing you have not opened. The abstract had been opened; the paper
> had not. That is a real defect and the rule catches it. But the correct fix is
> to cite the section, not to delete the number.
>
> The premise of the project is therefore not uncited, and it does not rest on
> a position paper's argument alone. It rests on that paper's own controlled
> experiment, with the caveat now stated above: one 3×3 design, one task
> distribution, two runs per cell.
>
> Two further claims in the notice above do not survive either. The n_eff ≈ 2.18
> in `docs/LIMITATIONS.md` was never a `2605.23950` figure. It is
> arXiv:2605.29800's, where it is confirmed in Table 2 as "n_eff (Kish): 2.18
> [2.07, 2.31]" for nine judges from seven families, exactly as that file states.
> And the 23.8-point swing in `docs/HARNESS_DISCLOSURE.md` is arXiv:2605.27922's
> and is in its body. Neither was a withdrawn figure; both were correct.
>
> The lesson the first notice drew still stands and is now better evidenced: a
> retraction that propagates is as dangerous as one that stalls. This one
> reached two files on a finding that was labelled unverified in its own text,
> and would have deleted four correct figures from a third had a later unit not
> opened the paper. Verify before propagating, in both directions.

> **Correction, 2026-08-14.** The paragraph immediately above overreached in the
> other direction on its two "further claims". It said the n_eff ≈ 2.18 figure
> "is confirmed in Table 2" and that the 23.8-point swing "is in its body ...
> both were correct". Neither claim has a `quote_body`, or any verbatim body
> text, backing it in `paper/refs.bib`, and both bib entries say the opposite
> of "correct" in their own `note` fields: arXiv:2605.29800's entry states
> "n_eff = 2.18 and the 95% CI ... are not in the abstract ... UNVERIFIED ...
> Neither the body reading nor the per-dataset figures are confirmed first-hand
> here", and arXiv:2605.27922's entry states the 23.8-point swing is
> "UNVERIFIED AND NOT IN THE ABSTRACT ... a bare magnitude with no source
> sentence". This file's own entry for arXiv:2605.27922, two paragraphs below,
> already reached the correct conclusion independently and removed the 23.8
> figure rather than hedging it, so the error was confined to this box, and
> the disagreement between two passages of the same document caught it rather
> than anyone reading a table. Both numbers are restored to
> *unverified* pending a first-hand read of the tables named. This is now the
> third finding in this file's own history where "not in the abstract" drifted
> into "confirmed" or "absent" without anyone opening the body: see the two
> corrections above it. `docs/LIMITATIONS.md` and `docs/HARNESS_DISCLOSURE.md`
> carry the same walk-back.

**Harness-Bench: Measuring Harness Effects across Models in Realistic Agent
Workflows**, arXiv:2605.27922. 5,194 execution trajectories over 106
sandboxed offline tasks, across "representative harness configurations" and
"multiple model backends". The abstract's finding is qualitative: "substantial
variation in completion, process quality, efficiency, and failure behavior
across model-harness pairings", and it concludes that capability should be
reported at the model-harness configuration level rather than attributed to the
base model. Its named failure family, execution-alignment failures, "where
plausible reasoning becomes decoupled from tool feedback, workspace state,
evidence, or verifiable output contracts", is the prior for our own bottom-up
error coding.

> **Correction, 2026-08-13.** The "23.8-point swing from harness alone", the
> "6 harnesses × 8 model backends" grid, the claim that weaker models are more
> harness-dependent, and the failure-taxonomy percentages ("output-contract
> violations (36%)") are none of them in the abstract, and the 23.8 in
> particular was a bare magnitude with no source sentence anywhere. We removed
> them rather than hedging them. The trajectory and task counts are exact and
> the qualitative finding above is verbatim.

**Miller (Anthropic), "Adding Error Bars to Evals"**, arXiv:2411.00640.
Clustered standard errors, paired designs, power analysis. Qualified by
arXiv:2503.01747, which restricts CLT-based methods below a few hundred
effectively independent datapoints. *Effect on design:* exact and resampling
methods throughout.

**Biderman et al., "Lessons from the Trenches on Reproducible Evaluation of
Language Models"**, arXiv:2405.14782 (EleutherAI). Publish exact prompt
formatting; publish full transcripts, not just scores; version-pin the harness;
distrust cross-paper comparisons that use different templates.

**Husain**, "Your AI Product Needs Evals" and "A Field Guide to Rapidly Improving
AI Products": bottom-up error analysis to *saturation* rather than a fixed
sample size; binary verdict plus written critique rather than Likert; build the
eval for your problem instead of reaching for generic metrics.

**Pineau et al.**, JMLR 2021, the ML reproducibility checklist.
**Mitchell et al.**, arXiv:1810.03993, model cards.
**Musgrave et al.**, arXiv:2003.08505: never compare a tuned method against an
untuned baseline.
**Dodge et al.**, arXiv:1909.03004: report performance as a function of tuning
budget.

**Prompting Inversion**, arXiv:2510.22251. A sculpted prompt helped GPT-4o
(97% vs 93%) and *hurt* GPT-5 (94.00% vs 96.36% plain CoT).
**PromptBridge**, arXiv:2512.01420, cross-model prompt transfer; still the
current answer for cheap→expensive transfer.
**"Prompt Optimization Is a Coin Flip"**, arXiv:2604.14585; effectiveness varies
widely by task in compound systems.
**GEPA** (ICLR 2026 oral, DSPy's dominant optimiser): reflective, trace-based
optimisation that beats GRPO by up to 20% with up to 35× fewer rollouts.

---

## 7. Ecosystem

**Agent Skills open standard**, agentskills.io, published December 2025.
Six frontmatter fields: `name`, `description`, `license`, `compatibility`,
`metadata`, `allowed-tools`. Roughly 40 adopting products, with `.agents/skills/`
emerging as a shared discovery path across Codex, Cursor, Copilot, Gemini CLI,
Cline, Amp and OpenCode. Vendor extensions (`context: fork`,
`disable-model-invocation`) are hard errors elsewhere and must live in overlays.

**`tjboudreaux/cc-thinking-skills`** is the closest prior art. 28 skills, all
inline prompt text with no `scripts/` or `references/`, all with model invocation
disabled, and a README that states none is proven to improve accuracy. The evals
exist upstream but do not reach users through a normal plugin install.

**Inspect AI**, UK AISI, MIT-licensed, Python-native, first-class local-model
providers. **`inspect_swe`** (meridianlabs-ai) exposes CLI coding agents
including Claude Code as Inspect solvers, with `skills=[...]` and `system_prompt`
as parameters.

**Harbor** is Terminal-Bench's infrastructure. It contributes a useful ontology:
Harness / Environment / Verifier, with scoring on independently observed final
state rather than trajectory, and the verifier tested against fixtures before
anyone trusts it.

**LangChain's `eval-engineering` skill and "Towards Automating Eval Engineering"**.
A scaffolded authoring workflow rather than automated eval generation, and
honest about that. Its trace-mining half depends on LangSmith. Cited for the
Harness/Environment/Verifier vocabulary; not adopted as a dependency.
