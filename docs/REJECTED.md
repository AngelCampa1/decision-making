# Rejected, deferred, and folded-in frameworks

We considered about eighteen decision and thinking frameworks for the v1 roster.
Five shipped. This records what happened to the rest and why, so the reasoning
is auditable and a later decision can overturn it.

The roster is deliberately small and explicitly revisable. Each additional skill
costs a full confirmation cycle against a subscription quota, so five is what
the budget supports today. That is not a claim that the other thirteen are
worthless. Once the harness exists, promoting something off the bench is a cheap
experiment rather than an act of faith.

## The bar

A framework had to clear four tests to ship as its own skill:

1. Procedure, not vocabulary. It must tell the model what to *do* next, not just
   what to call the situation.
2. An artifact. It must produce something inspectable: a ranked list, a number
   with a range, a decision record.
3. A stopping rule. It must say when it is finished.
4. A falsifiable claim. There must be a metric that could come out against it.

Most of what circulates as "thinking frameworks" fails test 1 or test 3.

## Folded into a shipping skill

Real techniques whose natural home is a step inside another procedure.

| Technique | Lives inside | Why not standalone |
| --- | --- | --- |
| Fermi decomposition | `base-rates` | A step in estimating, not a decision procedure |
| Bayesian updating (prior odds × likelihood ratio) | `base-rates` | The arithmetic goes in a script; the hard part is the inputs, and the inputs are what the reference class supplies |
| Premortem (Klein, *HBR* 2007) | `red-council` | Strong evidence, roughly 30% better identification of failure causes, but it is one prompt. It becomes the council's mandatory lens *and* its degraded single-agent mode |
| Steelmanning / devil's advocate | `red-council` | A lone contrarian without a rubric is sycophantic convergence pointed the other way |
| Verbalized confidence | `base-rates` | One line, ~50% ECE reduction (arXiv:2305.14975). Belongs in the forecast, not in a skill of its own |

## On the bench

Plausible, not yet justified. Promotion is a screening run, not a rewrite.

| Framework | Why it is waiting |
| --- | --- |
| **ACH** (Heuer, *Psychology of Intelligence Analysis*) | Procedurally clean, and the closest call in the whole survey. Cut because Dhami et al. (2019) found the canonical matrix orientation gave *no* significant reduction in confirmation bias versus plain text, and because it overlaps ~85% with `evidence-ledger` plus the council rubric. **Best candidate for promotion** if the ledger's diagnosticity scoring proves too weak |
| **Scenario planning** | The useful part, naming the failure world concretely, is already the premortem lens. Weak independent evidence on accuracy |
| **Five whys / root-cause analysis** | Debugging-shaped rather than decision-shaped, and a `systematic-debugging` skill already exists elsewhere in the ecosystem |
| **Theory of constraints, Jobs-to-be-Done, effectuation** | Genuine value inside their domains, but they are domain frameworks rather than general decision quality. Out of scope rather than wrong |

## Rejected

| Framework | Reason |
| --- | --- |
| **Cynefin** | Classification without a procedure. "This is complex, therefore probe-sense-respond" produces no artifact and no measurable delta. Its useful 20% (reversibility, and whether the answer is cheaply knowable) is absorbed into `decision-triage` |
| **OODA** | A description of what any agent loop already does. Adding it changes nothing about the model's behaviour, which means there is nothing to measure |
| **Decision matrices / weighted scoring / AHP** | Fabricated weights multiplied by fabricated scores. Manufactures false precision with no error bar, and the arithmetic lends the output a credibility the inputs have not earned. The defensible version is the council's MAP-style scoring, where sub-assessments are made independently and combined by median |
| **Monte Carlo / Bayesian networks** | The bottleneck is never the arithmetic, it is the inputs. Sophisticated propagation of confabulated priors is *worse* than a stated range, because it looks rigorous |
| **Kelly criterion / EV calculators** | Domain-specific, and financial-advice-adjacent in a way that a general decision skill should not be |
| **Noise audit** (Kahneman et al., *Noise*) | Requires many human judges scoring identical cases. An organizational intervention, not something an assistant skill can perform. The MAP protocol from the same book *is* used, inside `red-council` |
| **First-principles thinking, inversion, second-order thinking, Lindy, via negativa, circle of competence, TRIZ** | Slogans. No stopping rule, no artifact, nothing to score. Each is a real cognitive move that a capable model already makes when relevant; writing it on a card does not add a procedure |
| **Self-consistency** (arXiv:2203.11171) | Implemented as the **eval baseline the council must beat at matched token budget**, not as a skill. "Answer it five times independently" from a single context produces correlated samples, which is the exact defect the council is supposed to fix |

## Two rejections worth defending at length

Cynefin is the most popular framework here and the one most likely to draw an
objection. The objection would be that classifying a problem changes how you
approach it. That is true, and it is why the reversibility and knowability
questions survive inside `decision-triage`. What does not survive is the naming
step. A skill that emits "this is a complicated domain" has produced a label; a
skill that emits "this is reversible and cheap to check, so answer directly" has
produced an action. Only the second one has a metric.

Decision matrices are rejected despite being the thing most people mean by
"structured decision making". The problem is specific: an LLM asked to assign
weights will assign them, fluently, with no error bar and no way to distinguish a
weight it inferred from evidence from one it invented to fill the cell. The
output then carries the authority of arithmetic. Under
[`PROTOCOL.md`](PROTOCOL.md) that construction cannot pass a calibration guard,
because there is nothing to calibrate against, which is a reasonable summary of
why it does not belong in a decision skill.

## Reversing any of this

Everything above is a v1 judgement made before a single run. The screening arena
is cheap and explicitly permits iteration, so the cost of testing a bench
framework is one screening run rather than a redesign. A promotion needs: a
falsifiable claim in the table format used by the shipping skills, ~50 templates
passing the clean-room and difficulty gates, and a screening result that clears
the placebo and CoT arms. If it clears those, it gets pre-registered like
anything else, and this file gets an entry recording that the earlier call was
wrong.
