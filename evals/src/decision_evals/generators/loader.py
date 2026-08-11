"""Loading templates from disk."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from decision_evals.generators.schema import Template

#: Repository root, four levels up from this file
#: (``evals/src/decision_evals/generators/loader.py``).
REPO_ROOT = Path(__file__).resolve().parents[4]

TEMPLATE_ROOT = REPO_ROOT / "datasets" / "templates"


class TemplateLoadError(ValueError):
    """A template file was missing, malformed, or failed validation."""


def load_template(path: Path) -> Template:
    """Load and validate one template file.

    Validation errors are re-raised with the file path attached. Pydantic's
    message alone names the field but not the file, and when a load of fifty
    templates fails, the file is the part you need.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TemplateLoadError(f"{path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise TemplateLoadError(f"{path}: expected a mapping, got {type(raw).__name__}")
    try:
        template = Template.model_validate(raw)
    except ValidationError as exc:
        raise TemplateLoadError(f"{path}: {exc}") from exc

    if template.template_id != path.stem:
        raise TemplateLoadError(
            f"{path}: template_id {template.template_id!r} does not match the filename. "
            "They are kept identical so a template can be located from a failing item id."
        )
    return template


def load_all(root: Path | None = None) -> list[Template]:
    """Load every template under ``root``, sorted by id.

    Sorted rather than filesystem-ordered so that generation, golden files, and
    any pooled analysis see templates in the same sequence on every platform.
    """
    directory = TEMPLATE_ROOT if root is None else root
    if not directory.is_dir():
        raise TemplateLoadError(f"{directory} is not a directory")
    templates = [load_template(path) for path in sorted(directory.glob("*.yaml"))]
    if not templates:
        raise TemplateLoadError(f"no templates found in {directory}")
    return sorted(templates, key=lambda template: template.template_id)
