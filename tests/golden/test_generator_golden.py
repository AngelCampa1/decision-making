"""Golden-file pinning for the generator.

The nastiest bug an eval harness can have is a benchmark that drifts between
runs. Nothing in the analysis would catch it: the items still generate, the
scorer still scores, and every number computed before the drift silently becomes
incomparable with every number after it.

So the full generated output is committed, byte for byte, and regenerating it
requires ``pytest --bless``. That forces the diff into review rather than
letting it ride along inside an unrelated change.

    python -m uv run pytest tests/golden --bless --no-cov
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from decision_evals.generators import generate, load_all, load_template
from decision_evals.generators.loader import REPO_ROOT

#: Fixed for the golden corpus. Not the seed any real run uses -- the holdout is
#: regenerated from a seed kept in an uncommitted local file outside the repository.
GOLDEN_SEED = 1

GOLDEN_ROOT = REPO_ROOT / "datasets" / "golden"
TEMPLATE_ROOT = REPO_ROOT / "datasets" / "templates"


def _template_paths() -> list[Path]:
    return sorted(TEMPLATE_ROOT.glob("*.yaml"))


def _serialise(path: Path) -> str:
    template = load_template(path)
    items = [item.model_dump(mode="json") for item in generate(template, GOLDEN_SEED)]
    # sort_keys so a dict-ordering change in pydantic cannot look like a
    # benchmark change; trailing newline so the file is well-formed for git.
    return json.dumps(items, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


@pytest.mark.parametrize("path", _template_paths(), ids=lambda p: p.stem)
def test_generated_items_match_the_golden_file(path: Path, bless: bool) -> None:
    produced = _serialise(path)
    golden = GOLDEN_ROOT / f"{path.stem}.json"

    if bless:
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(produced, encoding="utf-8")
        pytest.skip(f"blessed {golden.name}")

    assert golden.exists(), f"{golden} is missing. Run pytest --bless to create it."
    assert produced == golden.read_text(encoding="utf-8"), (
        f"{path.stem} no longer generates its committed items. If this change is "
        "intended, re-bless and commit the diff; if it is not, the generator has "
        "drifted and every prior result on this template is now incomparable."
    )


def test_generation_is_reproducible_within_a_process() -> None:
    """Same inputs, same output -- the property the golden files assume."""
    for template in load_all():
        assert generate(template, GOLDEN_SEED) == generate(template, GOLDEN_SEED)


def test_every_template_has_a_golden_file() -> None:
    """A new template cannot slip in unpinned."""
    templates = {path.stem for path in _template_paths()}
    goldens = {path.stem for path in GOLDEN_ROOT.glob("*.json")}
    assert templates == goldens, (
        f"templates without goldens: {sorted(templates - goldens)}; "
        f"goldens without templates: {sorted(goldens - templates)}"
    )
