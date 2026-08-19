"""The staleness gate over the published site.

The site renders this repository's markdown **in place** -- ``docs/``,
``notebook/``, ``results/`` and ``skills/`` are read by the build rather than
copied into it. That is what stops a second ``STATUS.md`` existing to disagree
with the first, and it is exactly what makes every build a snapshot that rots
silently: a published page that is a week behind its source looks identical to
one that is current.

So every test here is a refusal. The module is pure -- no ``subprocess``, no
``npm`` -- precisely so that every branch of that refusal is reachable from a
``tmp_path`` with no Node toolchain anywhere near it.

Three of these encode a mistake that was available while writing it. A manifest
over an empty input list is *current by construction* and would report green
for any site at all, which is the ``prereg.py`` failure one level down: a check
that cannot return a non-zero answer is not a check. A digest taken over raw
bytes makes a Windows checkout and a Linux one disagree about identical content,
so the gate would fail for whichever machine did not build last. And hashing the
build's own output would make the manifest a record of itself.
"""

from __future__ import annotations

import json
from pathlib import Path

from decision_evals.site import (
    INPUTS_PATH,
    MANIFEST_PATH,
    SiteIssue,
    census,
    changed_inputs,
    check_site,
    input_files,
    load_inputs,
    manifest_is_current,
    render_manifest,
    site_present,
)


def _repo(
    tmp_path: Path,
    files: dict[str, str] | None = None,
    *,
    inputs: dict[str, object] | str | None = None,
) -> Path:
    """A repository with a ``site/`` directory and some rendered documents."""
    (tmp_path / "site").mkdir(parents=True, exist_ok=True)
    for relative, body in (files or {}).items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    if inputs is not None:
        text = inputs if isinstance(inputs, str) else json.dumps(inputs)
        (tmp_path / INPUTS_PATH).write_text(text, encoding="utf-8")
    return tmp_path


def _build(repo: Path) -> None:
    """What ``de site`` writes after a successful build."""
    (repo / MANIFEST_PATH).write_text(render_manifest(repo), encoding="utf-8")


DOCS = {"docs/STATUS.md": "# status\n", "README.md": "# readme\n"}
INPUTS: dict[str, object] = {"content": ["*.md", "docs/**/*.md"], "site": []}


# --------------------------------------------------------------------------- #
# Presence
# --------------------------------------------------------------------------- #
def test_absent_site_is_not_a_failure(tmp_path: Path) -> None:
    """The gate ships before the site does.

    Otherwise the commit adding ``site/`` is the only commit that can turn the
    gate green, and there is no green step to add it to.
    """
    assert not site_present(tmp_path)
    assert check_site(tmp_path) == []
    assert census(tmp_path) == (0, 0)


def test_present_site_is_gated(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    assert site_present(repo)


# --------------------------------------------------------------------------- #
# The input list
# --------------------------------------------------------------------------- #
def test_missing_inputs_file_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS)
    issues = check_site(repo)
    assert [issue.where for issue in issues] == [INPUTS_PATH]
    assert "missing" in issues[0].message


def test_unparseable_inputs_file_refuses(tmp_path: Path) -> None:
    """A truncated write must not read as "this site renders nothing"."""
    repo = _repo(tmp_path, DOCS, inputs='{"content": [')
    assert load_inputs(repo) == []
    issues = check_site(repo)
    assert [issue.where for issue in issues] == [INPUTS_PATH]
    assert "no inputs" in issues[0].message


def test_inputs_file_that_is_not_an_object_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs="[]")
    assert load_inputs(repo) == []
    assert check_site(repo)[0].where == INPUTS_PATH


def test_empty_input_list_refuses(tmp_path: Path) -> None:
    """A manifest over nothing is current by construction.

    This is the branch that would have made the whole gate decorative, and it
    fails green rather than red, so nothing else would have caught it.
    """
    repo = _repo(tmp_path, DOCS, inputs={"content": [], "site": []})
    _build(repo)
    assert manifest_is_current(repo)  # vacuously, which is the point
    issues = check_site(repo)
    assert [issue.where for issue in issues] == [INPUTS_PATH]
    assert "green for any site at all" in issues[0].message


def test_non_list_sections_are_ignored(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs={"content": "*.md", "site": ["site/*.json"]})
    assert load_inputs(repo) == ["site/*.json"]


def test_absent_inputs_file_loads_as_empty(tmp_path: Path) -> None:
    assert load_inputs(tmp_path) == []


def test_sections_load_in_declared_order(tmp_path: Path) -> None:
    repo = _repo(tmp_path, inputs={"content": ["a/*.md"], "site": ["site/*.json"]})
    assert load_inputs(repo) == ["a/*.md", "site/*.json"]


# --------------------------------------------------------------------------- #
# Which files are inputs
# --------------------------------------------------------------------------- #
def test_directories_are_not_hashed(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"docs/STATUS.md": "# status\n"}, inputs={"content": ["docs/*"]})
    (repo / "docs" / "nested").mkdir()
    assert [p.name for p in input_files(repo)] == ["STATUS.md"]


def test_build_output_is_never_an_input(tmp_path: Path) -> None:
    """Hashing ``dist/`` would make the manifest a record of itself."""
    repo = _repo(
        tmp_path,
        {
            "site/src/pages/index.astro": "page\n",
            "site/dist/index.html": "built\n",
            "site/node_modules/astro/package.json": "{}\n",
            "site/.astro-cache/data-store.json": "{}\n",
        },
        inputs={"content": [], "site": ["site/**/*"]},
    )
    names = [str(p.relative_to(repo)).replace("\\", "/") for p in input_files(repo)]
    assert names == ["site/inputs.json", "site/src/pages/index.astro"]


def test_overlapping_globs_count_a_file_once(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs={"content": ["*.md", "README.md"], "site": []})
    assert len(input_files(repo)) == 1


def test_line_endings_do_not_change_the_digest(tmp_path: Path) -> None:
    """A Windows checkout and a Linux one must agree about identical content.

    Without the normalisation the gate fails for whichever machine did not
    build last, which is a gate people switch off rather than fix.
    """
    repo = _repo(tmp_path, inputs={"content": ["*.md"], "site": []})
    (repo / "README.md").write_bytes(b"# readme\nline two\n")
    lf = render_manifest(repo)
    (repo / "README.md").write_bytes(b"# readme\r\nline two\r\n")
    assert render_manifest(repo) == lf


# --------------------------------------------------------------------------- #
# Staleness
# --------------------------------------------------------------------------- #
def test_missing_manifest_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    issues = check_site(repo)
    assert [issue.where for issue in issues] == [MANIFEST_PATH]
    assert "`de site`" in issues[0].message
    assert not manifest_is_current(repo)


def test_a_fresh_build_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    _build(repo)
    assert manifest_is_current(repo)
    assert check_site(repo) == []
    assert census(repo) == (2, 0)


def test_an_edited_document_refuses_and_names_it(tmp_path: Path) -> None:
    """The difference between a gate people run and a gate people disable.

    Per-file hashes rather than one aggregate digest, so the refusal can say
    which document moved.
    """
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    _build(repo)
    (repo / "docs" / "STATUS.md").write_text("# status\n\nand a correction\n", encoding="utf-8")

    assert changed_inputs(repo) == ["docs/STATUS.md"]
    issues = check_site(repo)
    assert [issue.where for issue in issues] == [MANIFEST_PATH]
    assert "docs/STATUS.md" in issues[0].message
    assert census(repo) == (2, 1)


def test_a_new_document_refuses(tmp_path: Path) -> None:
    """60 notebook entries in four days is this repository's commonest action."""
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    _build(repo)
    (repo / "docs" / "NEW.md").write_text("# new\n", encoding="utf-8")
    assert changed_inputs(repo) == ["docs/NEW.md"]
    assert check_site(repo)[0].where == MANIFEST_PATH


def test_a_deleted_document_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    _build(repo)
    (repo / "docs" / "STATUS.md").unlink()
    assert changed_inputs(repo) == ["docs/STATUS.md"]
    assert check_site(repo)[0].where == MANIFEST_PATH


def test_a_changed_source_file_refuses(tmp_path: Path) -> None:
    """Editing the link rewriter changes every page without touching a document."""
    repo = _repo(
        tmp_path,
        {"README.md": "# readme\n", "site/src/lib/rewrite.mjs": "export default a;\n"},
        inputs={"content": ["*.md"], "site": ["site/src/**/*"]},
    )
    _build(repo)
    (repo / "site/src/lib/rewrite.mjs").write_text("export default b;\n", encoding="utf-8")
    assert changed_inputs(repo) == ["site/src/lib/rewrite.mjs"]
    assert check_site(repo)[0].where == MANIFEST_PATH


def test_a_long_change_list_is_truncated(tmp_path: Path) -> None:
    """A refusal that prints 400 paths is a refusal nobody reads to the end of."""
    repo = _repo(tmp_path, {"README.md": "# readme\n"}, inputs=INPUTS)
    _build(repo)
    for index in range(14):
        (repo / "docs").mkdir(exist_ok=True)
        (repo / "docs" / f"E{index:02d}.md").write_text("# entry\n", encoding="utf-8")

    message = check_site(repo)[0].message
    assert "14 input(s) changed" in message
    assert "docs/E00.md" in message
    assert "docs/E13.md" not in message
    assert "... and 4 more" in message


def test_a_hand_edited_manifest_refuses(tmp_path: Path) -> None:
    """Serialisation is compared exactly, the same way ``index_is_current`` does."""
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    _build(repo)
    path = repo / MANIFEST_PATH
    path.write_text(
        path.read_text(encoding="utf-8").replace('"inputs"', '"Inputs"'), encoding="utf-8"
    )
    assert not manifest_is_current(repo)
    assert check_site(repo)[0].where == MANIFEST_PATH


def test_manifest_line_endings_do_not_matter(tmp_path: Path) -> None:
    """The manifest is committed, so git's autocrlf may have rewritten it."""
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    _build(repo)
    path = repo / MANIFEST_PATH
    path.write_bytes(path.read_text(encoding="utf-8").replace("\n", "\r\n").encode())
    assert manifest_is_current(repo)


def test_an_unparseable_manifest_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    (repo / MANIFEST_PATH).write_text('{"inputs": ', encoding="utf-8")
    assert changed_inputs(repo) == ["README.md", "docs/STATUS.md"]
    assert check_site(repo)[0].where == MANIFEST_PATH


def test_a_manifest_with_no_inputs_key_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    (repo / MANIFEST_PATH).write_text('{"generated_by": "de site"}', encoding="utf-8")
    assert changed_inputs(repo) == ["README.md", "docs/STATUS.md"]
    assert check_site(repo)[0].where == MANIFEST_PATH


def test_a_manifest_that_is_not_an_object_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    (repo / MANIFEST_PATH).write_text("[]", encoding="utf-8")
    assert check_site(repo)[0].where == MANIFEST_PATH


def test_changed_inputs_is_empty_with_no_manifest_and_no_files(tmp_path: Path) -> None:
    repo = _repo(tmp_path, inputs=INPUTS)
    assert changed_inputs(repo) == []


# --------------------------------------------------------------------------- #
# The record itself
# --------------------------------------------------------------------------- #
def test_the_manifest_says_it_is_generated_and_what_it_cannot_prove(tmp_path: Path) -> None:
    """A generated file somebody hand-edits is worse than no generated file."""
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    payload = json.loads(render_manifest(repo))
    assert payload["generated_by"] == "de site"
    assert "Do not edit" in payload["note"]
    # The limitation the note has to keep stating. The wording moved on
    # 2026-08-19 when publishing became a workflow: the manifest never proved
    # the build was pushed, and it still does not prove anybody is serving it.
    assert "never that anybody is serving it" in payload["note"]
    assert "de deployed" in payload["note"]
    assert sorted(payload["inputs"]) == ["README.md", "docs/STATUS.md"]


def test_the_manifest_ends_with_one_newline(tmp_path: Path) -> None:
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    text = render_manifest(repo)
    assert text.endswith("}\n")
    assert not text.endswith("\n\n")


def test_paths_are_posix_on_every_platform(tmp_path: Path) -> None:
    """The manifest is committed and read on both, so it cannot carry backslashes."""
    repo = _repo(tmp_path, DOCS, inputs=INPUTS)
    assert all("\\" not in name for name in json.loads(render_manifest(repo))["inputs"])


def test_an_issue_reads_as_a_sentence(tmp_path: Path) -> None:
    assert str(SiteIssue("site/x.json", "is missing.")) == "site/x.json: is missing."
