# Related work

The evidence base this project is built on, current as of August 2026. Organised
by what each finding *does* for the design rather than by topic, because several
of these changed decisions rather than merely informing them.

Confidence is flagged where it matters. A LessWrong re-analysis and an ICLR oral
are both cited here, and they should not be read as carrying the same weight.

---

## 1. The failure modes

### Distractor sensitivity — and the 2026 correction

**Mirzadeh, Alizadeh, Shahrokhi, Tuzel, Bengio, Farajtabar (Apple), "GSM-Symbolic"**
— arXiv:2410.05229. Inserting a single topically-relevant but logically
irrelevant clause dropped accuracy by up to 65%. This is the canonical statement
of the "it's raining in Paraguay, so grab a raincoat" failure, and the source of
our dataset methodology: parameterised templates with computed ground truth.

**Revisiting GSM-Symbolic (2026 re-audit)** — a re-analysis found the collapse
was largely an artifact of *ambiguous* distractors that a reasonable solver would
fold into the calculation. After a two-auditor filter kept 117 of 945 candidates
(12.4%) as genuinely irrelevant, the residual drop on GPT-4o, Claude Opus 4.6 and
Haiku 4.5 was statistically indistinguishable from zero.
**Confidence: low-medium — LessWrong re-analysis, not peer-reviewed.**
*Effect on design:* our distractor audit replicates the two-auditor filter, we
expect heavy attrition, and expected effect size is revised down, which raises
required N. This is the single largest threat to the flagship skill's premise and
is treated as such rather than omitted.

**Chroma Research, "Context Rot"** (2025), 18 models including Claude Opus 4 —
models above 95% on short prompts fall to 60–70% with semantically related
distractors. One strong distractor hurts more than four weak ones, and coherent
context degrades attention *more* than shuffled context. 2026 commentary adds
that the U-shape holds only while context is under ~50% full.

**"Diagnosing and Mitigating Context Rot in Long-horizon Search"** —
arXiv:2606.29718. Relocates the effect into agentic search, where it is still
documented at 30–50% degradation. *Effect on design:* the flagship is aimed here
rather than at math-word-problem distractors.

**Liu et al., "Lost in the Middle"** — arXiv:2307.03172. U-shaped position
sensitivity in long contexts. Deepened, not overturned, by
**"Lost in the Middle at Birth"** (arXiv:2603.10123), which gives a training-time
theoretical account — implying the mitigation is reordering and pruning, not
prompting.

**Chen, Lin et al., "Benchmarking LLMs in RAG" (RGB)** — arXiv:2309.01431,
AAAI-24. LLMs are specifically weak at *negative rejection*: recognising that
retrieved context does not contain the answer.

### Does telling a model to ignore something work?

**"Unable to Forget"** — arXiv:2506.08184, and the I³C line
(arXiv:2403.12744). Bare negation instructions have marginal effect, degrading
further as the irrelevant item becomes more semantically related. A two-step
*verify-then-discard* structure does work. *Effect on design:* the flagship
splits verification and discard into two visible steps, and this is the direct
justification for that structure.

**"Escaping the Context Bottleneck: Active Context Curation for LLM Agents via RL"**
— arXiv:2604.11462. A curator decoupled from a frozen executor lifted WebArena
36.4% → 41.2% with 8.8% *fewer* tokens, and achieved an 8× token reduction on
DeepSearch; a 7B curator matched GPT-4o-level context management.
*Effect on design:* resolved the project's biggest open question. The forked
variant became primary and inline became a comparison arm.

**ACE, "Agentic Context Engineering"** — arXiv:2510.04618 (Stanford/SambaNova,
ICLR 2026 oral). Incremental playbook curation over Generator/Reflector/Curator
roles, avoiding brevity bias and context collapse; +10.6% on agent benchmarks.
Preferred over whole-prompt rewriting for any self-improvement loop.

### Abstention, over-calling, and sycophancy

**AbstentionBench** — arXiv:2506.09038. Abstention is unsolved and does not
improve with scale; reasoning-tuned models are **~24% worse** at abstaining than
their base counterparts.

**"To Call or Not to Call"** — arXiv:2605.18882. Models issue unwarranted tool
calls at a much higher rate than they correctly withhold warranted ones. Still
current; no contradicting 2026 work found.

**"Sycophancy in Large Language Models"** — arXiv:2411.15287. First-person
opinion statements induce agreement with *incorrect* beliefs at 63.7% average
across seven model families. **"When Truth Is Overridden"** (arXiv:2508.02087)
shows first-person framing perturbs internal representations more than
third-person framing of the same claim. *Effect on design:* the flagship restates
user assertions in the third person before evaluating them — though note this is
an *extrapolation*, since a self-applied rewrite is not the same manipulation the
paper tested. Flagged as such in the skill's own evidence file.

**"The Bias is in the Details"** — arXiv:2509.22856. 45 LLMs, 2.8M responses,
8 biases. Bias-consistent behaviour in 17.8–57.3% of instances; scale reduced
bias in only ~39.5% of cases; more detailed prompts reduced most biases by up to
14.9% but *worsened* overattribution by up to 8.8%.

---

## 2. What to do instead

**AgentAtlas, "Beyond Outcome Leaderboards for LLM Agents"** — arXiv:2605.20530.
Six control gates — **Act, Ask, Refuse, Stop, Confirm, Recover** — with named
failure modes including *missing irreversibility*. Removing explicit option menus
dropped trajectory accuracy 14–40pp across all 8 models, compressing them into a
0.54–0.62 band regardless of family. *Effect on design:* adopted as the control
taxonomy, and the reason option menus are held constant across all arms.

**"Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents"** —
arXiv:2603.26233. Decoupling underspecification detection from execution lifted
SWE-bench Verified 61.2% → 69.4%, with calibrated behaviour (fewer questions on
easy tasks). Supersedes SAGE-Agent (arXiv:2511.08798) as the primary citation for
EVPI-gated clarification.

**Flyvbjerg, Holm, Buhl**, *JAPA* 2002, and Flyvbjerg 2006/2008 — reference class
forecasting. Rail, bridge/tunnel and road overruns average 45%, 34% and 20%,
stable across decades and largely independent of project-specific planning
quality. Adopted by the APA (2005) and the UK Treasury Green Book. A genuine
three-step algorithm, which is why it survived the framework cut.

**Tetlock & Gardner**, *Superforecasting* (2015) — outside view before inside
view, Fermi decomposition, small frequent updates, calibration tracking.

**Kahneman, Sibony, Sunstein**, *Noise* (2021), ch. 25 — the Mediating
Assessments Protocol: independent sub-assessments scored in isolation, combined
mechanically. Targets *noise* (variance), which is a different disease from bias
and needs saying plainly so the council's claims stay honest.

**Klein**, "Performing a Project Premortem", *HBR* Sept 2007 — prospective
hindsight improves identification of failure causes by roughly 30%.

**"Trust Over Fear"** — arXiv:2603.14373. Trust-framed system prompts surfaced
59% more hidden issues; fear-framing showed no significant gain over unframed.
*Effect on design:* how every skill and the shipped `AGENTS.md` block are worded.

---

## 3. Calibration

**Tian, Mitchell, Zhou, Sharma, Rafailov, Yao, Finn, Manning, "Just Ask for
Calibration"** — arXiv:2305.14975, EMNLP 2023. For RLHF'd models, verbalised
confidence is better calibrated than token-level probabilities, cutting expected
calibration error by roughly 50%.

**OpenAI, "GPT-4 Technical Report"** — arXiv:2303.08774, Fig. 8. The pretrained
model is well calibrated on multiple choice; RLHF degrades it.

**Kadavath et al., "Language Models (Mostly) Know What They Know"** —
arXiv:2207.05221.

**"Calibration Drift Under Reasoning"** — arXiv:2606.11211. Calibration improves
then *degrades* past a reasoning-budget threshold, non-monotonically.
**Confidence: directional — tested on Llama-3.1-8B/3.3-70B, 70B inconclusive.**
*Effect on design:* "let the model think longer and its confidence will improve"
is treated as false.

**smECE** — arXiv:2603.14092, and the smoothECE line. Debiased, kernel-smoothed
calibration error. *Effect on design:* replaces raw-bin ECE as the headline
calibration estimator; binned ECE is retained as a secondary for comparability.

**ForecastBench** — arXiv:2409.19839, ICLR 2025. Contamination-proof by
construction (questions have no answer at submission time). Top LLMs ~0.122–0.136
Brier; superforecasters ~0.096; general public ~0.121.

**Murphy decomposition** — `Brier = Reliability − Resolution + Uncertainty`. The
reason a resolution floor is a hard guard: a forecaster that always predicts the
base rate is perfectly reliable and useless.

---

## 4. Judges and councils

**Zheng et al., "Judging LLM-as-a-Judge"** — arXiv:2306.05685, NeurIPS 2023.
GPT-4 judge agreement with humans ~85%, above human-human agreement ~81%.

**Liu et al., "G-Eval"** — arXiv:2303.16634, EMNLP 2023. CoT rubric
decomposition; Spearman 0.514 with humans on summarisation.

**Verga et al., "Replacing Judges with Juries" (PoLL)** — arXiv:2404.18796.
Three small judges from different providers beat a single GPT-4-class judge
across six datasets at ~7× lower cost, with reduced self-preference bias.
**Superseded — see below.**

**RoPoLL** — arXiv:2606.30931. PoLL incurs *unbounded* bias under any positive
contamination, regardless of jury size. A geometric-median estimator (breakdown
point ½) gives ~19% improvement under cross-dimensional attack; a 3-judge 38B
robust committee beat a 675B single judge by 1.31× under 30% corruption.
*Effect on design:* aggregation is a robust estimator, never a mean.

**"Nine Judges, Two Effective Votes"** — arXiv:2605.29800. Nine judges from seven
families gave an effective sample size of **2.18** (95% CI [2.07, 2.31]), mean
pairwise correlation 0.391. Panel lift over the best single judge: **+0.2pp**
against a predicted-under-independence 22pp. *Effect on design:* this is a
structural ceiling, not an aggregation problem. The council is capped at three
judges chosen for divergent failure modes, and must report effective sample size
or its diversity claim is decorative.

**Position bias** — arXiv:2406.07791 (15 judges, >150,000 instances; repetition
stability, position consistency, preference fairness), refined by
arXiv:2604.23178. **Self-preference** — arXiv:2410.21819. **Scoring bias** —
arXiv:2506.22316. **CALM bias framework** — arXiv:2410.02736.

**Shankar et al., "Who Validates the Validators?" (EvalGen)** — arXiv:2404.12272,
UIST 2024. *Criteria drift*: grading outputs changes the grader's own criteria,
so a judge aligned once does not stay aligned. Judges also show agreeableness
bias — high TPR paired with badly low TNR — meaning a judge can look >90%
"accurate" by blended agreement while catching almost no real failures.
*Effect on design:* TPR and TNR reported separately against a deliberately
failure-heavy calibration set; recalibration whenever the pipeline changes.

### Multi-agent debate

**Du, Li, Torralba, Tenenbaum, Mordatch** — arXiv:2305.14325, ICML 2024. The
founding positive result.

**"Stop Overvaluing Multi-Agent Debate"** — arXiv:2502.08788. Five MAD methods ×
nine benchmarks × four models: debate often fails to beat single-agent CoT +
self-consistency despite far more compute. Model *heterogeneity* is what rescues
it.

**"The Cost of Consensus"** — arXiv:2605.00914. Isolated self-correction beats
unguided homogeneous debate on modern instruction-tuned models at 2.1–3.4× less
token cost.

**"Peacemaker or Troublemaker"** — arXiv:2509.23055. Debaters converge on the
most confidently asserted position rather than the most correct one.
*Effect on design:* in any second round, judges see arguments with author
identity, score values and confidence markers stripped.

**Huang, Chen, Mishra, Zheng, Yu, Song, Zhou (DeepMind), "LLMs Cannot Self-Correct
Reasoning Yet"** — arXiv:2310.01798, ICLR 2024. Intrinsic self-correction without
external feedback can *degrade* performance. *Effect on design:* the council's
first decline gate is "would a test, query or lookup settle this?" — because a
council over a verifiable question is self-correction with extra steps.

**Wang et al., "Self-Consistency"** — arXiv:2203.11171. The cheap ensemble
baseline any council must beat at matched token budget.

---

## 5. Skills as an intervention

**Xu & Wu, "Skill Availability and Presentation Granularity in LLM Agents"** —
arXiv:2605.31408. A **30-task** domain-balanced SkillsBench subset, **2 models**,
six skill conditions, five trials, 1,800 rows. (An earlier draft of this entry
said "86 tasks, 11 domains", which is this paper's scale confused with
SkillsBench's own — and SkillsBench is 87 tasks and 8 domains, so both halves
were wrong, in the direction that made this paper look bigger. Verified
first-hand 2026-08-12.) Skill availability: **+26.7 to +36.0pp**
(GPT-5.5), **+18.0 to +26.0pp** (DeepSeek V4-Flash). Granularity of the skill's
prose: **+0.7pp** (GPT-5.5), **−6.7pp** (DeepSeek), CIs crossing zero. Worked
examples: +0.7–1.3pp. *Effect on design:* engineering effort goes into triggering
and availability, not wordsmithing.

**SkillOpt, "Executive Strategy for Self-Evolving Agent Skills"** —
arXiv:2605.23904, Microsoft Research, code at `github.com/microsoft/SkillOpt`.
Treats `SKILL.md` as a trainable parameter: bounded edits ("textual learning
rate"), a held-out validation gate, a rejected-edit buffer, epoch-level
consolidation. +23.5pp average on GPT-5.5 across six benchmarks, evaluated inside
Claude Code and Codex CLI harnesses.
*Caveats we take seriously:* no confidence intervals, no significance tests, and
no correction for the many implicit comparisons its accept-if-strictly-better
ratchet performs; benchmark selection restricted to tasks with crisp automatic
scoring, not flagged as a limitation; a target-matched optimiser recovers only
56–74% of the gain, implying an unacknowledged distillation component.
*This paper and SkillsBench are in direct tension, and adjudicating it is one of
this project's stated contributions.*

**"On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents"** —
arXiv:2601.20404. 124 PRs across 10 repos. The abstract's figures are
**medians**: −28.64% runtime, −16.58% output tokens. (The −20.27% and −20.08%
*means* this entry used to lead with are not in the abstract and have not been
checked against the body; nor has the claim below. Verified first-hand
2026-08-12 as far as the abstract goes.) **The benefit is said to concentrate in
a small number of very expensive runs rather than spreading uniformly.**
*Effect on design:* p90/p99 are reported alongside means.

**"Authoring Agent Skills: A Software-Engineering Approach"** — arXiv:2607.25032.
Single responsibility, interface/implementation separation enforced by loading
timing, low coupling, token economy. Its behavioural-evaluation loop supplies one
concrete safeguard we adopt: **test with a fresh model instance, not the one that
drafted the skill.** *Confidence: principles paper, no benchmark numbers.*

**"From Anatomy to Smells: An Empirical Study of SKILL.md"** — arXiv:2607.01456.
Defect taxonomy for skill files. Used as a pre-ship self-audit.
*Prevalence figures unverified — the taxonomy is the usable part.*

**Agent Skills security study** — arXiv:2601.10338. 26.1% of a sampled skills
corpus contained at least one vulnerability across prompt-injection,
data-exfiltration, privilege-escalation and supply-chain categories.

---

## 6. Methodology

**"Stop Comparing LLM Agents Without Disclosing the Harness"** — arXiv:2605.23950.
Controlled 3×3 factorial, 100 SWE-bench Verified tasks: **harness variance /
model variance ≈ 7.8×**. Harness changes moved scores 8.5–13 points, model
changes 2.5–5 points, with **six ranking reversals in nine comparisons**.
Supplies the ETCSOVG disclosure checklist. *This validates the premise of the
whole project: the scaffold is the dominant variable, and it is the one nobody
reports.*

**Harness-Bench** — arXiv:2605.27922. 5,194 trajectories, 6 harnesses × 8 model
backends × 106 tasks. A 23.8-point swing from harness alone; weaker models are
more harness-dependent. Failure taxonomy: output-contract violations (36%),
tool/recovery failures (25%), evidence/grounding gaps, artifact-commitment
failures, state/continuation issues — used as the prior for our own bottom-up
error coding.

**Miller (Anthropic), "Adding Error Bars to Evals"** — arXiv:2411.00640.
Clustered standard errors, paired designs, power analysis.
**Qualified by** arXiv:2503.01747, which restricts CLT-based methods below a few
hundred effectively independent datapoints. *Effect on design:* exact and
resampling methods throughout.

**Biderman et al., "Lessons from the Trenches on Reproducible Evaluation of
Language Models"** — arXiv:2405.14782 (EleutherAI). Publish exact prompt
formatting; publish full transcripts, not just scores; version-pin the harness;
distrust cross-paper comparisons using different templates.

**Husain**, "Your AI Product Needs Evals" and "A Field Guide to Rapidly Improving
AI Products" — bottom-up error analysis to *saturation* rather than a fixed
sample size; binary verdict plus written critique rather than Likert; build the
eval for your problem instead of reaching for generic metrics.

**Pineau et al.**, JMLR 2021 — ML reproducibility checklist.
**Mitchell et al.** arXiv:1810.03993 — model cards.
**Musgrave et al.** arXiv:2003.08505 — never compare a tuned method against an
untuned baseline.
**Dodge et al.** arXiv:1909.03004 — report performance as a function of tuning
budget.

**Prompting Inversion** — arXiv:2510.22251. A sculpted prompt helped GPT-4o
(97% vs 93%) and *hurt* GPT-5 (94.00% vs 96.36% plain CoT).
**PromptBridge** — arXiv:2512.01420, cross-model prompt transfer; still the
current answer for cheap→expensive transfer.
**"Prompt Optimization Is a Coin Flip"** — arXiv:2604.14585; effectiveness varies
widely by task in compound systems.
**GEPA** (ICLR 2026 oral, DSPy's dominant optimiser) — reflective, trace-based
optimisation beating GRPO by up to 20% with up to 35× fewer rollouts.

---

## 7. Ecosystem

**Agent Skills open standard** — agentskills.io, published December 2025.
Six frontmatter fields: `name`, `description`, `license`, `compatibility`,
`metadata`, `allowed-tools`. Roughly 40 adopting products, with `.agents/skills/`
emerging as a shared discovery path across Codex, Cursor, Copilot, Gemini CLI,
Cline, Amp and OpenCode. Vendor extensions (`context: fork`,
`disable-model-invocation`) are hard errors elsewhere and must live in overlays.

**`tjboudreaux/cc-thinking-skills`** — the closest prior art. 28 skills, all
inline prompt text with no `scripts/` or `references/`, all with model invocation
disabled, and a README stating none is proven to improve accuracy. The evals
exist upstream but do not reach users through a normal plugin install.

**Inspect AI** — UK AISI, MIT-licensed, Python-native, first-class local-model
providers. **`inspect_swe`** (meridianlabs-ai) exposes CLI coding agents
including Claude Code as Inspect solvers, with `skills=[...]` and `system_prompt`
as parameters.

**Harbor** — Terminal-Bench's infrastructure. Contributes a useful ontology:
Harness / Environment / Verifier, scoring independently-observed final state
rather than trajectory, and testing the verifier against fixtures before trusting
it.

**LangChain's `eval-engineering` skill and "Towards Automating Eval Engineering"**
— a scaffolded authoring workflow rather than automated eval generation, and
honest about that. Its trace-mining half depends on LangSmith. Cited for the
Harness/Environment/Verifier vocabulary; not adopted as a dependency.
