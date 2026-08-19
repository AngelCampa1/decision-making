"""The gate over facts a page publishes rather than renders.

The site renders this repository's markdown in place, so a rendered document
cannot disagree with its source. The pages *around* those documents can, and
nothing could see them: ``docs.py`` opens ``*.md`` and never a ``.astro`` file,
``site.py`` hashes those files and never reads them. On 2026-08-19 the landing
page offered four procedures against a skill that routes to six, hardcoded a run
count the results page derived differently, and the results index published a
headroom figure ``docs/STATUS.md`` retracts in its own words.

So every test here is a refusal, and the module is pure -- no Astro, no Node, no
network -- precisely so that every branch of that refusal is reachable from a
``tmp_path``.

Four of these encode a mistake that was available while writing it. A quote
compared literally fails on real documents on day one, because every anchor in
this repository is a hard-wrapped sentence split at a column nobody chose. A
quote that matches *twice* is the shape ``docs/STATUS.md`` actually has -- it
holds ``~4,240``, ``~4,600`` and ``~4,816`` as three true sentences -- and an
anchor that cannot tell them apart can go on matching the stale one, which fails
green and so is caught by nothing else. Without ``latest`` the gate can only see
a corrected sentence and never an appended one, and the test for that asserts
the weaker guarantee rather than pretending to the stronger. And an empty claims
list is deliberately *not* refused here, which is the one place this module
departs from ``site.py``, asserted so nobody restores the analogy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from decision_evals.claims import (
    CLAIMS_PATH,
    Claim,
    ClaimIssue,
    Retraction,
    anchor_issues,
    census,
    check_claims,
    load_claims,
    normalise,
    referenced_ids,
    scanned_pages,
)

#: The anchor this whole file is built on: a real sentence from
#: ``docs/STATUS.md``, hard-wrapped there and emphasised in the middle.
SOURCE = "docs/STATUS.md"
QUOTE = "The total is therefore **~4,816**, not ~4,600."
DOC = f"# Status\n\nSome earlier prose.\n\n{QUOTE}\nSee the notebook entry.\n"
PAGE = "site/src/pages/index.astro"
INPUTS: dict[str, object] = {"content": [], "site": ["site/claims.json"]}


def _claim(**overrides: Any) -> dict[str, Any]:
    """One well-formed claim, before whatever this test breaks about it."""
    entry: dict[str, Any] = {
        "id": "total-model-calls",
        "value": "~4,816",
        "rounded": None,
        "source": SOURCE,
        "quote": QUOTE,
        "latest": None,
        "why": "The headline figure, and the one that has already drifted twice.",
    }
    entry.update(overrides)
    return entry


def _retraction(**overrides: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "phrase": "about six points",
        "source": SOURCE,
        "quote": "See the notebook entry.",
        "why": "The live figure is nine.",
    }
    entry.update(overrides)
    return entry


def _repo(
    tmp_path: Path,
    files: dict[str, str] | None = None,
    *,
    claims: dict[str, Any] | str | None = None,
    inputs: dict[str, object] | None = None,
) -> Path:
    """A repository with a ``site/``, a source document and a page."""
    (tmp_path / "site").mkdir(parents=True, exist_ok=True)
    for relative, body in {SOURCE: DOC, **(files or {})}.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (tmp_path / "site" / "inputs.json").write_text(
        json.dumps(INPUTS if inputs is None else inputs), encoding="utf-8"
    )
    if claims is not None:
        text = claims if isinstance(claims, str) else json.dumps(claims)
        (tmp_path / CLAIMS_PATH).write_text(text, encoding="utf-8")
    return tmp_path


def _published(*ids: str) -> dict[str, str]:
    """A page that publishes each id through ``claim()``."""
    calls = "\n".join(f"  <span>{{claim('{name}')}}</span>" for name in ids)
    return {PAGE: f"---\nimport {{ claim }} from '../lib/claims.ts';\n---\n<p>\n{calls}\n</p>\n"}


def _register(*claims: dict[str, Any], retractions: list[dict[str, Any]] | None = None) -> dict:
    return {"note": "n", "claims": list(claims), "retractions": retractions or []}


# --------------------------------------------------------------------------- #
# Presence
# --------------------------------------------------------------------------- #
def test_absent_site_is_not_a_failure(tmp_path: Path) -> None:
    """The gate ships before the site does, exactly as ``site.py`` does."""
    assert check_claims(tmp_path) == []
    assert census(tmp_path) == (0, 0, 0)


def test_a_missing_register_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _published("total-model-calls"))
    issues = check_claims(repo)
    assert [issue.where for issue in issues] == [CLAIMS_PATH]
    assert "is missing" in issues[0].message


def test_an_unparseable_register_refuses(tmp_path: Path) -> None:
    """A truncated write must not read as "this site claims nothing"."""
    repo = _repo(tmp_path, _published("total-model-calls"), claims='{"claims": [')
    issues = check_claims(repo)
    assert [issue.where for issue in issues] == [CLAIMS_PATH]
    assert "not parseable JSON" in issues[0].message
    assert load_claims(repo) == ([], [])


def test_a_register_that_is_not_an_object_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, claims="[]")
    assert check_claims(repo)[0].message.startswith("has no `claims` array")
    assert load_claims(repo) == ([], [])


def test_a_register_with_no_claims_list_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, claims={"note": "n", "claims": "several"})
    assert check_claims(repo)[0].message.startswith("has no `claims` array")


def test_a_claims_file_outside_inputs_refuses(tmp_path: Path) -> None:
    """``site/inputs.json`` lists files by name, so an omission is silent.

    Unhashed, the register can be edited to agree with a page that was never
    rebuilt, and the staleness gate reports green over both.
    """
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim()),
        inputs={"content": [], "site": ["site/inputs.json"]},
    )
    issues = check_claims(repo)
    assert [issue.where for issue in issues] == [CLAIMS_PATH]
    assert "site/inputs.json" in issues[0].message


# --------------------------------------------------------------------------- #
# The shape of an entry
# --------------------------------------------------------------------------- #
def test_a_missing_field_refuses_and_names_it(tmp_path: Path) -> None:
    entry = _claim()
    del entry["why"]
    repo = _repo(tmp_path, claims=_register(entry))
    assert "has no string `why`" in check_claims(repo)[0].message


def test_a_non_string_field_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, claims=_register(_claim(id=7)))
    assert "has no string `id`" in check_claims(repo)[0].message


def test_a_non_string_optional_field_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, claims=_register(_claim(rounded=0.71)))
    assert "has no string `rounded`" in check_claims(repo)[0].message


def test_an_entry_that_is_not_an_object_refuses(tmp_path: Path) -> None:
    repo = _repo(tmp_path, claims=_register("total-model-calls"))  # type: ignore[arg-type]
    assert check_claims(repo)[0].message == "claim 0 is not an object."
    assert load_claims(repo) == ([], [])


def test_a_malformed_retraction_refuses(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        claims=_register(_claim(), retractions=[{"phrase": "about six points"}]),
    )
    assert "retraction 0 has no string `source`" in str(check_claims(repo)[0])
    assert load_claims(repo)[1] == []


def test_a_non_list_retractions_section_is_not_a_register(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims={"note": "n", "claims": [_claim()], "retractions": "none yet"},
    )
    assert check_claims(repo) == []


def test_a_duplicate_id_refuses(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim(), _claim(why="and again")),
    )
    assert "declares `total-model-calls` twice" in check_claims(repo)[0].message


# --------------------------------------------------------------------------- #
# Anchors
# --------------------------------------------------------------------------- #
def test_a_green_register_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _published("total-model-calls"), claims=_register(_claim()))
    assert check_claims(repo) == []
    assert census(repo) == (1, 0, 1)


def test_a_missing_source_refuses(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim(source="docs/GONE.md")),
    )
    assert "does not exist" in check_claims(repo)[0].message


def test_a_changed_digit_refuses(tmp_path: Path) -> None:
    """The whole point: the document moved on and the page did not."""
    repo = _repo(
        tmp_path,
        {SOURCE: DOC.replace("~4,816", "~4,817"), **_published("total-model-calls")},
        claims=_register(_claim()),
    )
    assert "no longer contains" in check_claims(repo)[0].message


def test_a_reflowed_quote_still_matches(tmp_path: Path) -> None:
    """Anchors here are hard-wrapped sentences broken at an arbitrary column.

    ``docs/STATUS.md`` splits this very sentence between ``The total is`` and
    ``therefore``. Compared literally, the gate would fail on real documents on
    the day it shipped.
    """
    reflowed = DOC.replace(QUOTE, "The total is\ntherefore **~4,816**,\nnot ~4,600.")
    repo = _repo(
        tmp_path,
        {SOURCE: reflowed, **_published("total-model-calls")},
        claims=_register(_claim()),
    )
    assert check_claims(repo) == []


def test_added_bold_does_not_break_an_anchor(tmp_path: Path) -> None:
    emphasised = DOC.replace(QUOTE, "The **total** is therefore **~4,816**, not `~4,600`.")
    repo = _repo(
        tmp_path,
        {SOURCE: emphasised, **_published("total-model-calls")},
        claims=_register(_claim()),
    )
    assert check_claims(repo) == []


def test_a_quote_matching_twice_refuses(tmp_path: Path) -> None:
    """``docs/STATUS.md``'s actual shape: a live paragraph and a retracted one.

    Corrections there are appended rather than rewritten, so the superseded
    sentence stays on the page above the live one. An anchor that matches both
    can go on matching the stale one after the live one changes, and it reports
    green while doing it — nothing else here would catch that.
    """
    doubled = f"{DOC}\n**Correction, appended.** {QUOTE}\n"
    repo = _repo(
        tmp_path,
        {SOURCE: doubled, **_published("total-model-calls")},
        claims=_register(_claim()),
    )
    assert "appears 2 times" in check_claims(repo)[0].message


def test_anchor_issues_is_shared_by_both_registers(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert anchor_issues(repo, "claim `x`", SOURCE, QUOTE) == []
    assert anchor_issues(repo, "claim `x`", SOURCE, "never written") != []


# --------------------------------------------------------------------------- #
# The number inside the anchor
# --------------------------------------------------------------------------- #
def test_a_value_outside_its_quote_refuses(tmp_path: Path) -> None:
    """An anchor pins a sentence, and a sentence is not a number.

    Without this the quote goes on resolving while the page publishes anything
    at all.
    """
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim(value="~9,999")),
    )
    issues = check_claims(repo)
    assert len(issues) == 1
    assert "not in the sentence it quotes" in issues[0].message


def test_an_appended_correction_refuses_via_latest(tmp_path: Path) -> None:
    """The failure the quote alone cannot see.

    ``docs/STATUS.md`` is corrected by appending, so the anchored sentence stays
    word-for-word true while a newer total sits below it.
    """
    appended = f"{DOC}\n**Correction, appended.** The total is therefore ~5,100, not ~4,816.\n"
    repo = _repo(
        tmp_path,
        {SOURCE: appended, **_published("total-model-calls")},
        claims=_register(_claim(latest="(?<=therefore )~[0-9],[0-9]{3}")),
    )
    issues = check_claims(repo)
    assert len(issues) == 1
    assert "the last `(?<=therefore )~[0-9],[0-9]{3}`" in issues[0].message
    assert "is `~5,100`" in issues[0].message


def test_a_claim_without_latest_ignores_a_later_number(tmp_path: Path) -> None:
    """The documented weaker guarantee, asserted rather than assumed.

    A claim with no ``latest`` promises that its sentence still exists — never
    that nothing below it supersedes the sentence.
    """
    appended = f"{DOC}\n**Correction, appended.** The total is therefore ~5,100, not ~4,816.\n"
    repo = _repo(
        tmp_path,
        {SOURCE: appended, **_published("total-model-calls")},
        claims=_register(_claim()),
    )
    assert check_claims(repo) == []


def test_a_latest_that_stays_current_passes(tmp_path: Path) -> None:
    """A pattern has to survive the correction *format*, not just the number.

    ``docs/STATUS.md`` writes a correction as "therefore <new>, not <old>", so a
    bare ``~[0-9],[0-9]{3}`` ends on the superseded figure and refuses a page
    that is right. Narrowing it to the phrasing is the opposite trap and has
    already been paid for: a ``(?<=therefore )`` pattern armed at a form the
    next correction did not use could not fire at all. Both are the inert-guard
    failure, and only running the pattern against the real document tells them
    apart.
    """
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim(latest="(?<=therefore )~[0-9],[0-9]{3}")),
    )
    assert check_claims(repo) == []


def test_a_latest_matching_nothing_refuses(tmp_path: Path) -> None:
    """A guard that can never fire is not a guard."""
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim(latest="calls made in [0-9]{4}")),
    )
    assert "nothing in `docs/STATUS.md` matches it" in check_claims(repo)[0].message


def test_an_uncompilable_latest_refuses(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim(latest="~[0-9")),
    )
    assert "is not a regular expression" in check_claims(repo)[0].message


def test_a_correct_rounding_passes(tmp_path: Path) -> None:
    """``~`` and thousands separators are published decoration, not arithmetic."""
    doc = "# Scorecard\n\nthe stump reads 0.7054 against a majority baseline.\n"
    repo = _repo(
        tmp_path,
        {"SCORECARD.md": doc, **_published("word-trick-ceiling")},
        claims=_register(
            _claim(
                id="word-trick-ceiling",
                value="0.7054",
                rounded="0.71",
                source="SCORECARD.md",
                quote="the stump reads 0.7054 against a majority baseline.",
            )
        ),
    )
    assert check_claims(repo) == []


def test_a_wrong_rounding_refuses(tmp_path: Path) -> None:
    doc = "# Scorecard\n\nthe stump reads 0.7054 against a majority baseline.\n"
    repo = _repo(
        tmp_path,
        {"SCORECARD.md": doc, **_published("word-trick-ceiling")},
        claims=_register(
            _claim(
                id="word-trick-ceiling",
                value="0.7054",
                rounded="0.70",
                source="SCORECARD.md",
                quote="the stump reads 0.7054 against a majority baseline.",
            )
        ),
    )
    issues = check_claims(repo)
    assert "To 2 decimal places it is `0.71`" in issues[0].message


def test_an_unroundable_value_refuses(tmp_path: Path) -> None:
    """Several live figures are words, and a word does not round to anything."""
    counted = "eleven measurements were caught being broken."
    repo = _repo(
        tmp_path,
        {"docs/COUNTS.md": f"# Counts\n\n{counted}\n", **_published("broken-measurements")},
        claims=_register(
            _claim(
                id="broken-measurements",
                value="eleven",
                rounded="11",
                source="docs/COUNTS.md",
                quote=counted,
            )
        ),
    )
    assert "do not both parse as numbers" in check_claims(repo)[0].message


# --------------------------------------------------------------------------- #
# What the pages say
# --------------------------------------------------------------------------- #
def test_a_claim_no_page_publishes_refuses(tmp_path: Path) -> None:
    """Shrink-only, the same discipline as `unwired` and `docs-absent-commands`."""
    repo = _repo(tmp_path, claims=_register(_claim()))
    issues = check_claims(repo)
    assert [issue.where for issue in issues] == [CLAIMS_PATH]
    assert "no page publishes it" in issues[0].message


def test_an_undeclared_call_refuses_and_names_the_page(tmp_path: Path) -> None:
    repo = _repo(tmp_path, _published("headroom-points"), claims=_register())
    issues = check_claims(repo)
    assert [issue.where for issue in issues] == [PAGE]
    assert "does not declare it" in issues[0].message


def test_an_empty_claims_list_with_no_calls_is_green(tmp_path: Path) -> None:
    """The one place this module departs from ``site.py``, asserted on purpose.

    ``site.py`` must refuse an empty input list, because a manifest over nothing
    is current by construction. Here non-vacuity comes from the other side: a
    page calling ``claim()`` with nothing declared refuses, so a site making no
    unbacked claims and declaring none is correctly green rather than vacuously
    so. Restoring the analogy would refuse the site on the day the gate lands.
    """
    repo = _repo(tmp_path, claims=_register())
    assert check_claims(repo) == []
    assert census(repo) == (0, 0, 0)


def test_both_call_spellings_are_seen(tmp_path: Path) -> None:
    page = "<p>{claim('a-figure')} and {shown('another-figure')} and notAClaim('x')</p>\n"
    repo = _repo(tmp_path, {PAGE: page})
    assert referenced_ids(repo) == {"a-figure": [PAGE], "another-figure": [PAGE]}


def test_build_output_is_never_scanned(tmp_path: Path) -> None:
    """A stale copy in ``dist/`` must not refuse a page that was already fixed."""
    repo = _repo(
        tmp_path,
        {
            PAGE: "<p>{claim('a-figure')}</p>\n",
            "site/src/dist/old.astro": "<p>{claim('deleted-figure')}</p>\n",
            "site/src/node_modules/pkg/index.ts": "claim('vendored')\n",
        },
    )
    assert list(referenced_ids(repo)) == ["a-figure"]


def test_a_directory_named_like_a_page_is_not_read(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {PAGE: "<p>{claim('a-figure')}</p>\n"})
    (repo / "site" / "src" / "pages" / "archive.astro").mkdir()
    assert [path.name for path in scanned_pages(repo)] == ["index.astro"]


# --------------------------------------------------------------------------- #
# Retractions
# --------------------------------------------------------------------------- #
def test_a_retracted_phrase_on_a_page_refuses(tmp_path: Path) -> None:
    page = "<p>the headroom above a ruler is about six points.</p>\n"
    repo = _repo(tmp_path, {PAGE: page}, claims=_register(retractions=[_retraction()]))
    issues = check_claims(repo)
    assert [issue.where for issue in issues] == [PAGE]
    assert "publishes `about six points`" in issues[0].message
    assert "The live figure is nine." in issues[0].message


def test_a_retraction_whose_correction_vanished_refuses(tmp_path: Path) -> None:
    """A retraction outliving its own evidence is a rule nobody can check.

    Same failure as a claim whose source sentence was rewritten, so it goes
    through the same helper rather than a second implementation of it.
    """
    repo = _repo(
        tmp_path,
        claims=_register(retractions=[_retraction(quote="a sentence nobody wrote")]),
    )
    issues = check_claims(repo)
    assert "retraction `about six points` quotes a sentence" in issues[0].message


def test_a_duplicate_retraction_refuses(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        claims=_register(retractions=[_retraction(), _retraction(why="and again")]),
    )
    assert "retracts `about six points` twice" in check_claims(repo)[-1].message


def test_a_retraction_alone_is_a_working_register(tmp_path: Path) -> None:
    repo = _repo(tmp_path, claims=_register(retractions=[_retraction()]))
    assert check_claims(repo) == []
    assert census(repo) == (0, 1, 0)


# --------------------------------------------------------------------------- #
# The record itself
# --------------------------------------------------------------------------- #
def test_normalise_strips_markup_and_collapses_whitespace() -> None:
    assert normalise("**1,095 isolated `claude -p`\ncalls**") == "1,095 isolated claude -p calls"
    assert normalise("a  _b_\t c") == "a b c"


def test_load_claims_reads_both_registers(tmp_path: Path) -> None:
    repo = _repo(tmp_path, claims=_register(_claim(), retractions=[_retraction()]))
    claims, retractions = load_claims(repo)
    assert claims == [
        Claim(
            id="total-model-calls",
            value="~4,816",
            rounded=None,
            source=SOURCE,
            quote=QUOTE,
            latest=None,
            why="The headline figure, and the one that has already drifted twice.",
        )
    ]
    assert retractions == [
        Retraction(
            phrase="about six points",
            source=SOURCE,
            quote="See the notebook entry.",
            why="The live figure is nine.",
        )
    ]


def test_load_claims_on_a_repository_with_no_register(tmp_path: Path) -> None:
    assert load_claims(tmp_path) == ([], [])


def test_an_issue_reads_as_a_sentence() -> None:
    assert str(ClaimIssue("site/claims.json", "is missing.")) == "site/claims.json: is missing."


# --------------------------------------------------------------------------- #
# Keys nobody reads
#
# Every guard here is opt-in, so a key that is merely ignored is a guard that is
# merely absent. An adversarial review on 2026-08-19 turned three of them off
# with one-character typos and the gate stayed green each time.
# --------------------------------------------------------------------------- #
def test_a_misspelt_latest_refuses_rather_than_disabling_the_guard(tmp_path: Path) -> None:
    """`lastest` passed a superseded total, silently. That is the whole point."""
    appended = f"{DOC}\n**Correction, appended.** The total is therefore ~5,100, not ~4,816.\n"
    repo = _repo(
        tmp_path,
        {SOURCE: appended, **_published("total-model-calls")},
        claims=_register(_claim(lastest="(?<=therefore )~[0-9],[0-9]{3}")),
    )
    issues = check_claims(repo)
    assert len(issues) == 1
    assert "`lastest`, which nothing reads" in issues[0].message
    assert "`latest`" in issues[0].message


def test_a_misspelt_rounded_refuses(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim(round="~4,800")),
    )
    issues = check_claims(repo)
    assert len(issues) == 1
    assert "`round`, which nothing reads" in issues[0].message


def test_a_misspelt_retractions_section_refuses(tmp_path: Path) -> None:
    """The worst of the three: the whole register vanishes and the step says so.

    ``census`` went on reporting ``0 retraction(s)`` as though that were the
    design, which is indistinguishable from a register that declares none.
    """
    register = _register(_claim())
    register["retraction"] = register.pop("retractions")
    repo = _repo(tmp_path, _published("total-model-calls"), claims=register)
    issues = check_claims(repo)
    assert len(issues) == 1
    assert "top-level `retraction`" in issues[0].message
    assert "misspelt section is an empty section" in issues[0].message


def test_a_known_field_set_still_passes(tmp_path: Path) -> None:
    """The negative control: every declared key, and no complaint about any."""
    repo = _repo(
        tmp_path,
        _published("total-model-calls"),
        claims=_register(_claim(rounded=None, latest=None)),
    )
    assert check_claims(repo) == []


# --------------------------------------------------------------------------- #
# An anchored `latest`
# --------------------------------------------------------------------------- #
def test_latest_compares_group_one_when_the_pattern_captures(tmp_path: Path) -> None:
    """So the anchor can name the figure without becoming part of it.

    Without this a `latest` has to be a bare number shape, which either misses
    the next correction or matches every unrelated number below it. Both
    happened to `total-model-calls` on 2026-08-19, in that order.
    """
    appended = f"{DOC}\n| **new total** | **~9,900** | earlier + more |\n"
    repo = _repo(
        tmp_path,
        {SOURCE: appended, **_published("total-model-calls")},
        claims=_register(
            _claim(latest=r"(?:new total|total is)[^\n0-9~]{0,30}(~?[0-9]{1,3}(?:,[0-9]{3})+)")
        ),
    )
    issues = check_claims(repo)
    assert len(issues) == 1
    assert "is `~9,900`" in issues[0].message


def test_an_anchored_latest_ignores_an_unrelated_number_below_it(tmp_path: Path) -> None:
    """The false refusal a bare number shape produces, asserted as absent.

    A per-run figure appended under the total is not a correction to the total,
    and a guard that reads it as one refuses with the wrong number named.
    """
    appended = f"{DOC}\nThat run made 1,548 calls of its own.\n"
    repo = _repo(
        tmp_path,
        {SOURCE: appended, **_published("total-model-calls")},
        claims=_register(
            _claim(latest=r"(?:new total|total is)[^\n0-9~]{0,30}(~?[0-9]{1,3}(?:,[0-9]{3})+)")
        ),
    )
    assert check_claims(repo) == []
