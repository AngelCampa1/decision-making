"""Can a trivial classifier tell the core from the padding?

The gate that decides whether the volume manipulation is real.

Prose written to *not matter* has a register. It carries fewer hard numerals,
fewer deadlines, fewer citations, more hedging, flatter sentences. The core
documents are dense in exactly those things **because that is what makes them
the core**. So padding that is on-topic at the client level fixes *topical*
separability and does nothing about *register* separability -- and a model doing
salience-weighted attention would then find the core in constant time however
long the file got.

The failure that produces is the worst one available: a flat dose-response curve,
reported as "no context rot at this scale", when the retrieval difficulty was
never manipulated at all.

The classifier here is deliberately trivial -- the best single feature, by AUC.
The claim under test is *"a model could do this easily"*, and a trivial
classifier succeeding is far stronger evidence for that than a tuned one
succeeding. A tuned classifier failing would prove nothing either way.

    python -m uv run python scripts/separability.py --library datasets/library

Free. No model calls, so it runs in the local gate.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Above this, the padding is transparent and the manipulation is cosmetic.
AUC_CEILING: Final = 0.70

#: The six features, and why each is here. Every one of them is something the
#: core has more of *for the reason it is the core*, which is what makes the
#: register problem structural rather than a matter of writing care.
FEATURES: Final[tuple[str, ...]] = (
    "numerals",  # hard figures per 100 words
    "citations",  # section references per 100 words
    "deontic_verbs",  # must / shall / may not / is required to
    "dates",  # deadlines with consequences attached
    "mean_sentence_length",  # padding hedges, and hedging is long
    "type_token_ratio",  # padding repeats itself
)

#: Words per window for the standardised type-token ratio.
#:
#: Raw TTR falls mechanically with document length, so an unstandardised version
#: measures how long a document is rather than how varied its vocabulary is --
#: the exact confound every other feature is divided per-hundred-words to avoid.
#: The first run of this gate scored 0.776 on raw TTR and the reading "my padding
#: repeats itself" was half length artefact.
_TTR_WINDOW: Final = 100

_WORD: Final = re.compile(r"\b[\w'-]+\b")
_NUMERAL: Final = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
_CITATION: Final = re.compile(
    r"\b(?:s\.\s?\d+|section\s+\d+|reg\.\s?\d+|cl\.\s?\d+)", re.IGNORECASE
)
_DEONTIC: Final = re.compile(
    r"\b(?:must|shall|may not|must not|is required to|are required to|obliged to)\b",
    re.IGNORECASE,
)
_DATE: Final = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\s+(?:January|February|March|April|May|June|July|"
    r"August|September|October|November|December)\s+\d{4}\b",
)
_SENTENCE: Final = re.compile(r"[.!?]+\s+|\n\n")


def features(bodies: Sequence[str]) -> list[dict[str, float]]:
    """One feature vector per document body, keyed by :data:`FEATURES`."""
    return [_features_of(body) for body in bodies]


def _features_of(body: str) -> dict[str, float]:
    words = _WORD.findall(body.lower())
    per_hundred = 100.0 / len(words) if words else 0.0
    sentences = [part for part in _SENTENCE.split(body) if part.strip()]

    return {
        "numerals": len(_NUMERAL.findall(body)) * per_hundred,
        "citations": len(_CITATION.findall(body)) * per_hundred,
        "deontic_verbs": len(_DEONTIC.findall(body)) * per_hundred,
        "dates": len(_DATE.findall(body)) * per_hundred,
        "mean_sentence_length": statistics.fmean(
            len(_WORD.findall(sentence)) for sentence in sentences
        )
        if sentences
        else 0.0,
        "type_token_ratio": _standardised_ttr(words),
    }


def _standardised_ttr(words: list[str]) -> float:
    """Mean type-token ratio over fixed-size windows.

    Raw TTR is a length measure in disguise: a 200-word note will beat a
    2,000-word schedule on vocabulary variety whatever either of them says.
    Averaging over windows of :data:`_TTR_WINDOW` removes that, so the feature
    reports variety rather than brevity.
    """
    if not words:
        return 0.0
    windows = [words[i : i + _TTR_WINDOW] for i in range(0, len(words), _TTR_WINDOW)]
    # A trailing stub is dropped rather than measured: a 7-word remainder scores
    # 1.0 on variety and says nothing.
    full = [window for window in windows if len(window) == _TTR_WINDOW] or windows[:1]
    return statistics.fmean(len(set(window)) / len(window) for window in full)


def feature_auc(
    core: Sequence[dict[str, float]], padding: Sequence[dict[str, float]]
) -> dict[str, float]:
    """Per-feature AUC, folded so 0.5 is chance and 1.0 is perfect separation.

    Folded because direction does not matter: a padding corpus that is reliably
    *denser* in numerals separates just as well as one that is reliably thinner,
    and either would let a model find the core.
    """
    return {name: _folded_auc(core, padding, name) for name in FEATURES}


def auc(core: Sequence[dict[str, float]], padding: Sequence[dict[str, float]]) -> float:
    """The best single feature's AUC. Chance is 0.5.

    The pooled figure is a maximum rather than a fit, because the question is
    whether *any* easily-computed surface signal separates the two sets, not
    whether some weighted combination does.
    """
    if not core or not padding:
        return 0.5
    return max(feature_auc(core, padding).values())


def _folded_auc(
    core: Sequence[dict[str, float]], padding: Sequence[dict[str, float]], name: str
) -> float:
    """Mann-Whitney U as a probability, with ties counted as half."""
    if not core or not padding:
        return 0.5
    wins = 0.0
    for left in core:
        for right in padding:
            if left[name] > right[name]:
                wins += 1.0
            elif left[name] == right[name]:
                wins += 0.5
    raw = wins / (len(core) * len(padding))
    return max(raw, 1.0 - raw)


def _read(directory: Path) -> list[tuple[str, str]]:
    """Every document under ``directory``, as (id, body).

    Markdown files are one document each. Casefile YAML carries its documents in
    a list, and those are read out individually -- comparing a whole casefile
    against a single padding note would be comparing document *counts*, which is
    a feature of the corpus rather than of the prose.
    """
    documents: list[tuple[str, str]] = []
    for path in sorted(directory.rglob("*.md")):
        if path.is_file():
            documents.append((path.stem, path.read_text(encoding="utf-8")))
    for path in sorted(directory.rglob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        for document in raw.get("documents", []):
            documents.append((f"{path.stem}:{document['id']}", document["body"]))
    return documents


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", default="datasets/library", help="padding documents")
    parser.add_argument("--cores", default="datasets/probe", help="governing documents")
    args = parser.parse_args()

    library_dir = REPO_ROOT / args.library
    if not library_dir.exists():
        print(f"no library at {library_dir} -- author it first", file=sys.stderr)
        return 2

    padding = _read(library_dir)
    core = _read(REPO_ROOT / args.cores)
    if not padding or not core:
        print(f"need documents in both {library_dir} and {args.cores}", file=sys.stderr)
        return 2

    core_features = features([body for _, body in core])
    padding_features = features([body for _, body in padding])
    per_feature = feature_auc(core_features, padding_features)
    pooled = max(per_feature.values())

    print(f"{len(core)} core documents against {len(padding)} padding documents\n")
    print(f"  {'feature':<22} {'AUC':>6}  {'core':>8} {'padding':>8}  direction")
    for name, value in sorted(per_feature.items(), key=lambda pair: -pair[1]):
        core_median = statistics.median(vector[name] for vector in core_features)
        padding_median = statistics.median(vector[name] for vector in padding_features)
        # Direction matters for the fix even though it does not for the gate: a
        # padding corpus that is reliably *denser* in dates is as findable as one
        # that is thinner, but the two need opposite edits.
        direction = "core higher" if core_median > padding_median else "padding higher"
        print(
            f"  {name:<22} {value:>6.3f}  {core_median:>8.2f} {padding_median:>8.2f}  {direction}"
        )

    print(f"\npooled (best single feature)  {pooled:.3f}   need <= {AUC_CEILING}")
    if pooled > AUC_CEILING:
        print(
            "\nGATE FAIL: the padding is separable on surface features alone, so a "
            "model can find the core in constant time and the dose curve would be "
            "measuring 'find the document that reads differently'.\n"
            "The fix is structural: author each file as one matter end-to-end and "
            "designate core documents afterwards, rather than writing core and "
            "filler separately."
        )
        return 1

    print("\nGATE PASS: no single surface feature separates the two sets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
