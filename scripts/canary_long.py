"""Does a long prompt reach the model at all?

The cheapest experiment in this project and the one that gates every other. A
dose-response curve on context volume is worth nothing if the harness or the CLI
silently truncates, compacts, or summarises the prompt before the model sees it
-- the manipulation would never have happened and the null would be about
plumbing.

So: plant three canary strings at 10%, 50% and 90% depth in a prompt of a stated
size and ask for them back verbatim. A missing canary means that region did not
arrive. Run it at each length the corpus intends to use, *before* authoring any
of it.

    python scripts/canary_long.py --model haiku --tokens 2000 40000 100000

Roughly $2 for the full sweep. It also exercises the stdin path in
``providers.claude_code``, which is the other thing that has never been run at
length.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

from decision_evals.providers.claude_code import CliError  # noqa: E402
from decision_evals.providers.claude_code import run as cli_run  # noqa: E402

RESULTS: Final = REPO_ROOT / "results" / "probe" / "canary-long.jsonl"

#: Depths, as a fraction of the assembled prompt, at which a canary is planted.
#: 10/50/90 covers both ends of the documented U-shape plus the middle, which is
#: where degradation is reported to bite first.
DEPTHS: Final[tuple[float, ...]] = (0.10, 0.50, 0.90)

#: Characters per token *for this filler*, measured rather than assumed: 6.01 at
#: both 40k and 160k. The first version guessed 3.8 from the usual figure for
#: English prose, and the "100,000 token" run was really 63,313 -- repetitive
#: text tokenises far better than varied text does.
#:
#: So ``--tokens`` is a nominal label and the achieved count is what the report
#: prints. Real casefile prose will land nearer 4, which means the corpus builder
#: must measure its own ratio rather than borrowing this one.
CHARS_PER_TOKEN: Final = 6.0

SYSTEM_PROMPT: Final = (
    "You are reading a long file. Answer only the question asked, exactly in the "
    "format requested, with nothing else."
)

QUESTION: Final = (
    "Three lines in the file above begin with MERIDIAN-CANARY. Reproduce all "
    "three of those lines verbatim, one per line, in the order they appear. "
    "Output nothing else."
)

#: Filler. Deliberately bland and repetitive: this probe is not testing whether
#: the model can find a needle in *interesting* hay, it is testing whether the
#: bytes arrive. Realistic padding is a separate and much more expensive problem.
_FILLER: Final = (
    "The regional operations review notes that scheduling for the period was "
    "carried out under the standing arrangements, that no variation was sought, "
    "and that the position is unchanged from the previous reporting cycle. "
)


def canary(index: int) -> str:
    return f"MERIDIAN-CANARY-{index:02d}-{'ABCDEFGH'[index % 8]}{index * 7919 % 10000:04d}"


def build_prompt(target_tokens: int) -> tuple[str, list[str]]:
    """Assemble a prompt of roughly ``target_tokens`` with canaries at DEPTHS."""
    target_chars = int(target_tokens * CHARS_PER_TOKEN)
    body = (_FILLER * (target_chars // len(_FILLER) + 1))[:target_chars]

    canaries = [canary(i) for i in range(len(DEPTHS))]
    # Insert from the deepest first so earlier insertions do not shift later
    # offsets -- an off-by-one here would move a canary out of its stated band
    # and quietly weaken the claim.
    for offset, text in sorted(zip(DEPTHS, canaries, strict=True), reverse=True):
        cut = int(len(body) * offset)
        body = f"{body[:cut]}\n{text}\n{body[cut:]}"

    return f"{body}\n\n{'=' * 60}\n\n{QUESTION}", canaries


@dataclass(frozen=True)
class CanaryResult:
    model: str
    target_tokens: int
    prompt_chars: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    found: list[str]
    missing: list[str]
    verbatim: bool
    response: str

    @property
    def ok(self) -> bool:
        return not self.missing


def probe(model: str, target_tokens: int, cwd: str) -> CanaryResult:
    prompt, canaries = build_prompt(target_tokens)
    result = cli_run(prompt, system_prompt=SYSTEM_PROMPT, model=model, cwd=cwd, timeout=900.0)

    found = [c for c in canaries if c in result.text]
    missing = [c for c in canaries if c not in result.text]
    lines = [line.strip() for line in result.text.splitlines() if line.strip()]

    return CanaryResult(
        model=result.model,
        target_tokens=target_tokens,
        prompt_chars=len(prompt),
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        duration_ms=result.duration_ms,
        found=found,
        missing=missing,
        verbatim=lines == canaries,
        response=result.text,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--tokens", type=int, nargs="+", default=[2_000, 40_000, 100_000])
    args = parser.parse_args()

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    results: list[CanaryResult] = []

    with tempfile.TemporaryDirectory() as scratch, RESULTS.open("a", encoding="utf-8") as sink:
        for target in args.tokens:
            started = time.monotonic()
            try:
                result = probe(args.model, target, scratch)
            except CliError as exc:
                print(f"{target:>7,} tokens  FAILED  {exc}", flush=True)
                sink.write(json.dumps({"target_tokens": target, "error": str(exc)}) + "\n")
                sink.flush()
                continue

            results.append(result)
            sink.write(json.dumps(asdict(result)) + "\n")
            sink.flush()

            status = "ok" if result.ok else f"MISSING {len(result.missing)}"
            print(
                f"{target:>7,} tokens  -> {result.input_tokens:>7,} in  "
                f"{result.cost_usd:>7.4f} usd  {time.monotonic() - started:>5.1f}s  "
                f"{len(result.found)}/{len(DEPTHS)} canaries  "
                f"{'verbatim' if result.verbatim else 'not verbatim'}  {status}",
                flush=True,
            )

    if not results:
        print("\nno successful calls -- the harness cannot carry a long prompt")
        return 1

    # The ratio is worth printing on its own. If reported input tokens stop
    # tracking prompt size, something between here and the model is discarding
    # material, which is the failure this probe exists to catch.
    print("\nprompt chars per reported input token:")
    for result in results:
        print(
            f"  {result.target_tokens:>7,} -> {result.prompt_chars / max(result.input_tokens, 1):.2f}"
        )

    failed = [r for r in results if not r.ok]
    if failed:
        print(f"\nGATE FAIL: {len(failed)} length(s) lost a canary -- the prompt is not arriving")
        return 1

    print("\nGATE PASS: every canary came back at every length")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
