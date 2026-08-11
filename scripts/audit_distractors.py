"""Run the two-auditor distractor filter over the corpus.

The gate that matters most, and the one still standing between this corpus and
pre-registration. The 2026 GSM-NoOp re-audit kept 117 of 945 candidate
distractors (12.4%) once two independent auditors had to agree a fact was
genuinely irrelevant rather than plausibly foldable, and the residual effect on
frontier models became indistinguishable from zero. If our distractors are
ambiguous in the same way, we would measure a real effect and attribute it to
the wrong cause.

That risk went *up* with the collision rebuild, not down. A colliding distractor
is deliberately built to sit near the line: same kind of quantity as the one the
answer turns on, excluded only by a qualifier in its own sentence. Whether that
qualifier is sufficient is exactly the judgement being outsourced here.

**Auditor independence, stated honestly.** Two Claude models are not two
independent auditors in the sense RoPoLL and the ``n_eff`` work mean. Same
trainer, same data lineage, correlated failure modes -- nine judges from seven
families gave an effective sample size of about 2.18, and two from one family
give less than that. Local models via Ollama were the plan's answer and are not
installed, so the honest description of what runs here is *two models of
different capability from one provider*, and the attrition number should be read
as an upper bound on how strict this filter is.

Unanimity is required, so a single dissent rejects. That is the conservative
direction: a wrongly-admitted distractor mismeasures the headline effect, while
a wrongly-rejected one costs a template one distractor.

Usage:
    python -m uv run python scripts/audit_distractors.py [--budget 2.0]
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from decision_evals.budget import BudgetLedger
from decision_evals.generators import load_all
from decision_evals.generators.audit import (
    REQUIRED_AUDITORS,
    Auditor,
    AuditorVote,
    DistractorVerdict,
    audit_distractor,
)
from decision_evals.providers.claude_code import CliError, preflight
from decision_evals.providers.claude_code import run as cli_run

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS = REPO_ROOT / "results" / "audit" / "distractors.jsonl"

#: Two models of different capability. Not two independent auditors -- see the
#: module docstring. Ordered cheapest first so a budget stop loses the expensive
#: vote rather than both.
AUDITOR_MODELS = ("haiku", "sonnet")

#: The auditor is given no system prompt beyond the task. Nothing about this
#: repository, the skill under test, or the hypothesis should reach it.
AUDITOR_SYSTEM = (
    "You are a careful benchmark auditor. You answer the question asked, in the "
    "format requested, and nothing else."
)

#: What the re-audit's filter kept. Printed alongside ours: if our attrition is
#: far lower, the honest reading is that our filter is weaker than theirs.
REAUDIT_ACCEPTANCE = 0.124


def parse_vote(text: str) -> AuditorVote:
    """Read a verdict off the last matching line.

    Last rather than first, and exact rather than substring-anywhere: an auditor
    that reasons out loud will often write the word "ambiguous" mid-argument
    before concluding the opposite. An unreadable response is a dissent, because
    the alternative is admitting a distractor on the strength of a response
    nobody could parse.
    """
    verdict: bool | None = None
    for line in text.splitlines():
        stripped = line.strip().upper().removeprefix("**").removesuffix("**").strip()
        if stripped == "VERDICT: IRRELEVANT":
            verdict = True
        elif stripped == "VERDICT: AMBIGUOUS":
            verdict = False
    if verdict is None:
        return AuditorVote(irrelevant=False, rationale=f"unparseable response: {text[-200:]!r}")
    rationale = next(
        (line.strip() for line in reversed(text.splitlines()) if line.strip() and ":" not in line),
        "",
    )
    return AuditorVote(irrelevant=verdict, rationale=rationale)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=float, default=2.0)
    args = parser.parse_args()

    templates = load_all()
    candidates = sum(len(t.distractor_facts) for t in templates)
    print(f"{len(templates)} templates, {candidates} candidate distractors")
    print(f"auditors: {', '.join(AUDITOR_MODELS)} (see docstring on independence)")

    ledger = BudgetLedger(limit_usd=args.budget)

    with tempfile.TemporaryDirectory(prefix="de-audit-") as scratch:
        print(f"preflight against {AUDITOR_MODELS[0]} ...", flush=True)
        try:
            preflight(model=AUDITOR_MODELS[0], cwd=scratch)
        except CliError as exc:
            print(f"preflight failed: {exc}", file=sys.stderr)
            return 2

        auditors = [_auditor(model, scratch, ledger) for model in AUDITOR_MODELS]
        verdicts: list[DistractorVerdict] = []

        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        with RESULTS.open("w", encoding="utf-8") as handle:
            for template in templates:
                for distractor in template.distractor_facts:
                    verdict = audit_distractor(template, distractor, auditors)
                    verdicts.append(verdict)
                    handle.write(json.dumps(_record(verdict)) + "\n")
                    handle.flush()
                    mark = "keep" if verdict.accepted else "drop"
                    print(
                        f"  [{mark}] {template.template_id} {distractor.id}"
                        f"{' (collides)' if distractor.collides_with else ''}"
                        f" -- {verdict.reason}",
                        flush=True,
                    )

    return report(verdicts)


def _auditor(model: str, scratch: str, ledger: BudgetLedger) -> Auditor:
    """Bind one auditor to a model, charging the shared ledger."""

    def vote(prompt: str) -> AuditorVote:
        nonlocal ledger
        ledger.assert_can_afford(0.01)
        result = cli_run(prompt, system_prompt=AUDITOR_SYSTEM, model=model, cwd=scratch)
        ledger = ledger.record(result.cost_usd)
        return parse_vote(result.text)

    return vote


def _record(verdict: DistractorVerdict) -> dict[str, object]:
    payload = asdict(verdict)
    payload["shared_variables"] = sorted(verdict.shared_variables)
    payload["accepted"] = verdict.accepted
    payload["reason"] = verdict.reason
    return payload


def report(verdicts: list[DistractorVerdict]) -> int:
    """Print attrition, and fail if any template is left without a live collision."""
    accepted = [v for v in verdicts if v.accepted]
    rate = len(accepted) / len(verdicts) if verdicts else 0.0

    print(f"\n{'=' * 66}")
    print(f"accepted {len(accepted)} of {len(verdicts)} ({rate:.1%})")
    print(f"the 2026 re-audit's filter kept {REAUDIT_ACCEPTANCE:.1%}")
    if rate > REAUDIT_ACCEPTANCE * 2:
        print(
            "  Read this as our filter being weaker than theirs, not our\n"
            "  distractors being better. Theirs screened material written to be\n"
            "  irrelevant; ours screens material written to collide."
        )

    reasons = Counter(v.reason.split(":")[0] for v in verdicts if not v.accepted)
    if reasons:
        print("\nrejections by cause:")
        for reason, count in reasons.most_common():
            print(f"  {count:>3}  {reason}")

    surviving = Counter(v.template_id for v in accepted)
    starved = sorted(
        template.template_id
        for template in load_all()
        if surviving[template.template_id] < max(template.strata.distractors)
    )
    print("\n" + "=" * 66)
    if starved:
        print("templates left with too few admitted distractors for their strata:")
        for template_id in starved:
            print(f"  {template_id}: {surviving[template_id]} admitted")
        print("\nwrite replacements and re-audit; do not lower the strata to fit.")
        return 1
    print(f"every template retains enough admitted distractors ({REQUIRED_AUDITORS} auditors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
