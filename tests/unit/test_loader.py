"""Tests for template loading."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from decision_evals.generators.loader import (
    TEMPLATE_ROOT,
    TemplateLoadError,
    load_all,
    load_template,
)

Build = Callable[..., dict[str, Any]]


def _write(directory: Path, name: str, payload: object) -> Path:
    path = directory / f"{name}.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def test_a_valid_template_round_trips(tmp_path: Path, template_dict: Build) -> None:
    path = _write(tmp_path, "tst-001-example", template_dict())
    assert load_template(path).template_id == "tst-001-example"


def test_a_missing_file_is_a_load_error(tmp_path: Path) -> None:
    with pytest.raises(TemplateLoadError):
        load_template(tmp_path / "absent.yaml")


def test_malformed_yaml_is_a_load_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("key: [unclosed\n", encoding="utf-8")
    with pytest.raises(TemplateLoadError):
        load_template(path)


def test_a_non_mapping_document_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, "listy", ["not", "a", "mapping"])
    with pytest.raises(TemplateLoadError, match="expected a mapping"):
        load_template(path)


def test_validation_errors_name_the_file(tmp_path: Path, template_dict: Build) -> None:
    """Pydantic names the field; when fifty templates load, you need the file."""
    path = _write(tmp_path, "tst-001-example", template_dict(options=["only"]))
    with pytest.raises(TemplateLoadError, match="tst-001-example"):
        load_template(path)


def test_the_id_must_match_the_filename(tmp_path: Path, template_dict: Build) -> None:
    """So a failing item id locates its template without a search."""
    path = _write(tmp_path, "tst-002-different", template_dict())
    with pytest.raises(TemplateLoadError, match="does not match the filename"):
        load_template(path)


def test_load_all_sorts_by_id(tmp_path: Path, template_dict: Build) -> None:
    _write(tmp_path, "tst-002-beta", template_dict(template_id="tst-002-beta"))
    _write(tmp_path, "tst-001-alpha", template_dict(template_id="tst-001-alpha"))
    assert [t.template_id for t in load_all(tmp_path)] == ["tst-001-alpha", "tst-002-beta"]


def test_load_all_rejects_a_non_directory(tmp_path: Path) -> None:
    with pytest.raises(TemplateLoadError, match="is not a directory"):
        load_all(tmp_path / "nope")


def test_load_all_rejects_an_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(TemplateLoadError, match="no templates found"):
        load_all(tmp_path)


def test_the_shipped_corpus_loads(tmp_path: Path) -> None:
    """Defaulting to the real template root is the common path; exercise it."""
    templates = load_all()
    assert len(templates) >= 10
    assert TEMPLATE_ROOT.is_dir()
    assert all(t.template_id.startswith("rel-") for t in templates)
