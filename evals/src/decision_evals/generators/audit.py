"""The two-auditor distractor filter.

This is the most important gate in the dataset pipeline, because the premise of
the flagship skill depends on it. The original GSM-NoOp result reported a
collapse of up to 65% from a single irrelevant clause. A 2026 re-audit found
that most of those clauses were *ambiguous* rather than irrelevant -- material a
reasonable solver would fold into the calculation -- and after a two-auditor
filter kept 117 of 945 candidates (12.4%), the residual effect was
statistically indistinguishable from zero.

If our distractors are ambiguous in the same way, we would measure a real effect
and attribute it to the wrong cause: the model would not be failing to ignore
irrelevant information, it would be correctly incorporating information we had
mislabelled. So a distractor is admitted only if it clears two independent
checks.

**Check 1 is structural and proves invariance rather than sampling it.** A
distractor qualifies only if it shares no variables with the solution
expression. This is worth being precise about, because it would be easy to
overclaim here: the plan called for showing the computed solution is invariant to
the distractor's removal, and in this generator that is *trivially* true for
every fact. Answers are computed from sampled variables, never from fact text,
so an empirical remove-and-recompute test would pass for load-bearing facts too
and would prove nothing at all. The variable-overlap test is the version with
content -- it asks whether the distractor even mentions a quantity the answer
turns on, and a negative answer is a proof over all samplings rather than
evidence from some of them.

**Check 2 is semantic and needs judgement.** Structural independence does not
make a fact irrelevant to a *reader*. "The customer is on the Enterprise plan"
shares no variables with a refund-window calculation, but a reasonable solver
might treat it as grounds for discretion. Two independent auditors must agree
the fact is genuinely inert. Unanimity is required, so a single dissent rejects
-- the conservative direction, since the cost of a wrongly-admitted distractor is
a mismeasured headline effect and the cost of a wrongly-rejected one is a
template with fewer distractors.

Auditors are injected rather than constructed here, so the filter is testable
without model calls and ``de check`` stays free and deterministic.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from string import Formatter

from decision_evals.generators.safe_eval import referenced_names
from decision_evals.generators.schema import Distractor, Template

#: How many auditors must agree. Two independent passes, per the re-audit's
#: methodology.
REQUIRED_AUDITORS = 2


@dataclass(frozen=True)
class AuditorVote:
    """One auditor's judgement on one distractor."""

    irrelevant: bool
    rationale: str


#: An auditor receives a rendered prompt and returns a vote. Deliberately a
#: plain callable: the dev-arena implementation calls a local model, the tests
#: pass a stub, and neither is privileged in the type.
Auditor = Callable[[str], AuditorVote]


@dataclass(frozen=True)
class DistractorVerdict:
    """Whether one distractor may be used, and why."""

    template_id: str
    distractor_id: str
    shared_variables: frozenset[str]
    votes: tuple[AuditorVote, ...]

    @property
    def structurally_invariant(self) -> bool:
        """True when the distractor mentions no quantity the answer depends on."""
        return not self.shared_variables

    @property
    def unanimously_irrelevant(self) -> bool:
        return len(self.votes) >= REQUIRED_AUDITORS and all(vote.irrelevant for vote in self.votes)

    @property
    def accepted(self) -> bool:
        return self.structurally_invariant and self.unanimously_irrelevant

    @property
    def reason(self) -> str:
        """A one-line explanation, for the audit report."""
        if not self.structurally_invariant:
            shared = ", ".join(sorted(self.shared_variables))
            return f"shares solution variables ({shared}) so it is not provably inert"
        if len(self.votes) < REQUIRED_AUDITORS:
            return f"only {len(self.votes)} of {REQUIRED_AUDITORS} auditors voted"
        dissent = [vote.rationale for vote in self.votes if not vote.irrelevant]
        if dissent:
            return f"auditor dissent: {dissent[0]}"
        return "accepted: structurally inert and unanimously judged irrelevant"


@dataclass(frozen=True)
class AuditSummary:
    """Attrition across a set of verdicts.

    Reported in the paper next to the re-audit's 12.4%. If our attrition is far
    lower, the honest reading is that our filter is weaker than theirs, not that
    our distractors are better.
    """

    considered: int
    accepted: int

    @property
    def rejected(self) -> int:
        return self.considered - self.accepted

    @property
    def acceptance_rate(self) -> float:
        return self.accepted / self.considered if self.considered else 0.0


def template_variables(text: str) -> frozenset[str]:
    """The variable names a piece of template text interpolates."""
    return frozenset(
        field for _, field, _, _ in Formatter().parse(text) if field is not None and field
    )


def shared_solution_variables(template: Template, distractor: Distractor) -> frozenset[str]:
    """Variables the distractor mentions that the answer also depends on."""
    return template_variables(distractor.text) & referenced_names(template.solution.expr)


def _collision_note(distractor: Distractor) -> str:
    """Point the auditor at the exact judgement a colliding distractor turns on.

    A colliding distractor is deliberately built to sit close to the decision
    rule: same kind of quantity, excluded only by a qualifier in its own
    sentence. That is the whole design, and it is also precisely the region
    where a distractor stops being irrelevant and becomes ambiguous — the class
    the 2026 re-audit found had produced most of GSM-NoOp's reported effect.

    So the auditor is told about the collision rather than left to spot it. The
    phrasing puts the burden on the qualifier: the default reading is that a
    same-kind quantity *is* usable, and the fact has to earn its exclusion.
    """
    if distractor.collides_with is None:
        return ""
    return (
        f"\nNote: this candidate states a quantity of the same kind as "
        f"`{distractor.collides_with}`, which the answer depends on. It is "
        "intended to be excluded by a qualifier in its own sentence. Treat a "
        "same-kind quantity as usable unless that qualifier plainly rules it "
        "out.\n"
    )


def build_audit_prompt(template: Template, distractor: Distractor) -> str:
    """Render the question put to each auditor.

    Two deliberate choices. The auditor sees the *question and every relevant
    fact*, because irrelevance is a property of a statement in context rather
    than of the statement alone. And it is asked to judge whether a reasonable
    solver could *legitimately* use the fact -- not whether the fact is needed.
    The failure mode being screened for is ambiguity, and a fact can be
    unnecessary while still being a defensible input.
    """
    relevant = "\n".join(f"- {fact.text}" for fact in template.relevant_facts)
    return (
        "You are auditing a benchmark item for mislabelled distractors.\n\n"
        f"Question: {template.question}\n"
        f"Answer options: {', '.join(template.options)}\n\n"
        f"Facts established as relevant:\n{relevant}\n\n"
        f"Candidate distractor:\n- {distractor.text}\n"
        f"{_collision_note(distractor)}\n"
        "Could a careful, reasonable person legitimately use the candidate "
        "distractor as part of deciding this question -- even if it is not "
        "strictly necessary?\n"
        "Answer IRRELEVANT only if the candidate could play no defensible part "
        "in the decision. Answer AMBIGUOUS if a reasonable person might fold it "
        "in.\n"
        "Give one sentence of reasoning, then a final line reading exactly "
        "VERDICT: IRRELEVANT or VERDICT: AMBIGUOUS."
    )


def audit_distractor(
    template: Template, distractor: Distractor, auditors: Sequence[Auditor]
) -> DistractorVerdict:
    """Run both checks on one distractor.

    The auditors are skipped when the structural check already fails. That is a
    cost decision, not a correctness one -- the verdict is identical either way,
    and calling a model to confirm a rejection we have already proven would be
    spending quota to learn nothing.
    """
    shared = shared_solution_variables(template, distractor)
    if shared:
        return DistractorVerdict(
            template_id=template.template_id,
            distractor_id=distractor.id,
            shared_variables=shared,
            votes=(),
        )
    prompt = build_audit_prompt(template, distractor)
    return DistractorVerdict(
        template_id=template.template_id,
        distractor_id=distractor.id,
        shared_variables=shared,
        votes=tuple(auditor(prompt) for auditor in auditors),
    )


def audit_template(template: Template, auditors: Sequence[Auditor]) -> list[DistractorVerdict]:
    """Audit every distractor in a template, in declaration order."""
    if len(auditors) < REQUIRED_AUDITORS:
        raise ValueError(
            f"the filter requires at least {REQUIRED_AUDITORS} independent auditors, "
            f"got {len(auditors)}. A single auditor is not a filter, it is an opinion."
        )
    return [audit_distractor(template, d, auditors) for d in template.distractor_facts]


def summarise(verdicts: Sequence[DistractorVerdict]) -> AuditSummary:
    """Aggregate verdicts into an attrition report."""
    return AuditSummary(
        considered=len(verdicts),
        accepted=sum(1 for verdict in verdicts if verdict.accepted),
    )
