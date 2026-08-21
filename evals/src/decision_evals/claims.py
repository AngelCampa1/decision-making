"""A published page whose facts can still be shown to come from somewhere.

The site renders this repository's markdown in place, so a *rendered document*
cannot disagree with its source. The pages around those documents can, and
nothing could see them. :mod:`decision_evals.docs` scans ``*.md`` and
``docs/*.md`` and never opens a ``.astro`` file; :mod:`decision_evals.site`
hashes those files for staleness and never reads what is inside them. So a
figure typed into a page was checked by nobody, and on 2026-08-19 three were
wrong at once:

- the landing page offered *"Four methods. It reads one."* while
  ``skills/decision-making/SKILL.md`` routes to **six** -- ``council.md`` and
  ``hinge.md`` shipped that day and the page never mentioned them.
- the same page hardcoded **13** published runs while
  ``site/src/pages/results/index.astro`` derives its count from the collection
  and printed **12**. The site contradicted itself across two pages.
- the results index published headroom of *"about six points"*, a figure
  ``docs/STATUS.md`` retracts in its own words -- *"This read '0.956 ... about
  six points' until the checkpoints were reconciled"* -- against a live figure
  of nine.

**And the existing gate launders it.** Editing ``SKILL.md`` makes the build
manifest stale; ``de site`` rehashes; the page that now contradicts the skill
republishes green. Staleness is a property of bytes, and this is a property of
sentences.

So: one register, :data:`CLAIMS_PATH`, naming every fact a page publishes, the
document it comes from, and the sentence in that document it comes from. The
page reads it and the gate reads it -- one file, two readers, the same shape as
``site/inputs.json``, so the published number and the checked number are the
same string rather than two copies of it.

**What this cannot catch, stated so nobody mistakes green for correct.** It
proves a published string still appears in a sentence that still exists. It
does not prove the sentence is true, and it cannot see a fact a page states in
prose rather than routing through ``claim()`` -- the gate reaches exactly as
far as the page hands it. A correction *appended below* an anchor is invisible
too unless the claim declares ``latest``, which is why ``total-model-calls``
does: ``docs/STATUS.md`` holds ``~4,240``, ``~4,600`` and ``~4,816`` as three
true sentences, and only their order says which one is current. The same
standing limitation is registered for :mod:`decision_evals.site`,
:mod:`decision_evals.docs`, :mod:`decision_evals.provenance` and
:mod:`decision_evals.wiring`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from decision_evals.site import input_files, site_present
from decision_evals.sync import FACT_IDS

#: Every fact a page publishes, and what backs it. Read by this module *and* by
#: the page that renders a claim, so the published string and the checked string
#: are one string. It is not in ``pyproject.toml`` for the reason
#: ``site/inputs.json`` is not: TypeScript cannot read TOML without another
#: dependency, and a generated second copy would recreate the disagreement this
#: whole design exists to prevent.
CLAIMS_PATH: Final = "site/claims.json"

#: Where a published claim can be stated. Astro pages are the site's prose,
#: ``.ts`` carries the shared data the pages map over, and ``.svelte`` is the
#: router demo island.
#:
#: This comment said ``.svelte`` "is not used today" in the commit that added
#: ``site/src/components/RouterDemo.svelte`` and imported it into the landing
#: page. Two independent reviews found it on 2026-08-19. A comment describing
#: the arena a check runs in is exactly the kind of sentence this module exists
#: to stop being wrong, and it was wrong about itself.
SCANNED_PAGES: Final[tuple[str, ...]] = (
    "site/src/**/*.astro",
    "site/src/**/*.ts",
    "site/src/**/*.svelte",
)

#: Where a document can state a claim, through a ``de:fact`` marker.
#:
#: Added 2026-08-21, when three living documents were found restating the
#: broken-measurement count and this register's own notes recorded that they had
#: once said ten, around eleven and eight. A page was never the only surface a
#: figure could go stale on. It was the only surface with a gate.
#:
#: Retractions are deliberately not checked across these. A retracted phrase's
#: own correction quotes it, and ``docs/STATUS.md`` carries both, so scanning
#: documents for a retracted phrase would refuse the document that retracts it.
SCANNED_DOCUMENTS: Final[tuple[str, ...]] = ("*.md", "docs/**/*.md")

#: ``claim('total-model-calls')``, and ``shown(...)`` for the same call inside a
#: template expression. Ids are kebab-case, which keeps this from matching every
#: single-argument function call on the page.
_CALL: Final = re.compile(r"\b(?:claim|shown)\(\s*['\"]([a-z0-9-]+)['\"]\s*\)")

#: Never scanned, for :mod:`decision_evals.site`'s reason: the build's own
#: output is not the site's source.
_IGNORED_PARTS: Final = frozenset({"node_modules", "dist", ".astro", ".astro-cache"})

#: Emphasis a markdown document carries and a published sentence does not.
#: ``**~4,816**`` and ``~4,816`` are the same claim.
_MARKUP: Final = str.maketrans("", "", "*`_")

#: Decoration a published number carries and ``float`` will not parse:
#: ``~4,816`` is approximate, ``89%`` is a rate, and both are published exactly
#: as written. Stripped before the rounding comparison and nowhere else.
_DECORATION: Final = str.maketrans("", "", "~%,")

_CLAIM_FIELDS: Final[tuple[str, ...]] = ("id", "value", "source", "quote", "why")
_CLAIM_OPTIONAL: Final[tuple[str, ...]] = ("rounded", "latest")
_RETRACTION_FIELDS: Final[tuple[str, ...]] = ("phrase", "source", "quote", "why")

#: Top-level keys the register may carry. Anything else is a misspelt section,
#: which reads as an absent one -- see the check in :func:`check_claims`.
_SECTIONS: Final[tuple[str, ...]] = ("note", "claims", "retractions")


@dataclass(frozen=True)
class ClaimIssue:
    """One published fact that no longer resolves to a document."""

    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


@dataclass(frozen=True)
class Claim:
    """A fact a page publishes, and the sentence it came from."""

    id: str
    value: str
    rounded: str | None
    source: str
    quote: str
    latest: str | None
    why: str


@dataclass(frozen=True)
class Retraction:
    """A phrase this repository has withdrawn, and where it said so."""

    phrase: str
    source: str
    quote: str
    why: str


def normalise(text: str) -> str:
    """Drop markdown emphasis and collapse every run of whitespace.

    An anchor is a sentence, and a sentence in a hard-wrapped document is split
    across lines at a column nobody chose on purpose. Without this the gate
    fails on real documents on the day it ships: this repository's records carry
    anchors like ``**1,095 isolated `claude -p`\\ncalls**``, which is one
    sentence written as two lines and three kinds of markup.
    """
    return " ".join(text.translate(_MARKUP).split())


def _relative(path: Path, repo_root: Path) -> str:
    return str(path.relative_to(repo_root)).replace("\\", "/")


def _document(repo_root: Path) -> dict[str, object]:
    """The register as JSON, or an empty mapping if it cannot be read as one."""
    path = repo_root / CLAIMS_PATH
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _section(document: dict[str, object], key: str) -> list[object]:
    section = document.get(key, [])
    return section if isinstance(section, list) else []


def _optional(entry: dict[str, object], field: str) -> str | None:
    value = entry.get(field)
    return value if isinstance(value, str) else None


def _missing_fields(
    entry: dict[str, object], required: tuple[str, ...], optional: tuple[str, ...]
) -> list[str]:
    """Fields that are absent, or present as something other than a string."""
    problems = [field for field in required if not isinstance(entry.get(field), str)]
    problems += [
        field
        for field in optional
        if entry.get(field) is not None and not isinstance(entry.get(field), str)
    ]
    return problems


def _unknown_fields(entry: dict[str, object], known: tuple[str, ...]) -> list[str]:
    """Keys nobody reads.

    Every guard in this module is opt-in: a claim without ``latest`` is not
    checked for currency, and one without ``rounded`` is not checked for
    arithmetic. So a key that is merely ignored is a guard that is merely
    absent, and the two are indistinguishable from the outside.

    An adversarial review on 2026-08-19 spelled ``latest`` as ``lastest`` and
    appended a superseded total to the real ``docs/STATUS.md``: green, silently,
    with the guard gone. ``round`` for ``rounded`` did the same to the rounding
    check, and ``retraction`` for ``retractions`` deleted the entire retraction
    register while the step went on printing "0 retraction(s)" as though that
    were the design.

    A typo in a register is a typo. A typo that turns a check off without
    saying so is the failure this module exists to make impossible.
    """
    return sorted(key for key in entry if key not in known)


def load_claims(repo_root: Path) -> tuple[list[Claim], list[Retraction]]:
    """Every well-formed claim and retraction, in the order they are declared.

    An entry missing a required field is dropped rather than guessed at.
    :func:`check_claims` reports those before it ever calls this, so a dropped
    entry is never a silently ignored one.
    """
    document = _document(repo_root)
    claims = [
        Claim(
            id=str(entry["id"]),
            value=str(entry["value"]),
            rounded=_optional(entry, "rounded"),
            source=str(entry["source"]),
            quote=str(entry["quote"]),
            latest=_optional(entry, "latest"),
            why=str(entry["why"]),
        )
        for entry in _section(document, "claims")
        if isinstance(entry, dict) and not _missing_fields(entry, _CLAIM_FIELDS, _CLAIM_OPTIONAL)
    ]
    retractions = [
        Retraction(
            phrase=str(entry["phrase"]),
            source=str(entry["source"]),
            quote=str(entry["quote"]),
            why=str(entry["why"]),
        )
        for entry in _section(document, "retractions")
        if isinstance(entry, dict) and not _missing_fields(entry, _RETRACTION_FIELDS, ())
    ]
    return claims, retractions


def scanned_pages(repo_root: Path) -> list[Path]:
    """Every page a claim can be published from, deduplicated and sorted."""
    seen: dict[Path, None] = {}
    for pattern in SCANNED_PAGES:
        for path in repo_root.glob(pattern):
            if not path.is_file():
                continue
            if any(part in _IGNORED_PARTS for part in path.parts):
                continue
            seen.setdefault(path, None)
    return sorted(seen, key=lambda path: _relative(path, repo_root))


def referenced_ids(repo_root: Path) -> dict[str, list[str]]:
    """Claim id to the pages that publish it, so a refusal can name the page."""
    found: dict[str, list[str]] = {}
    for page in scanned_pages(repo_root):
        where = _relative(page, repo_root)
        for claim_id in sorted(set(_CALL.findall(page.read_text(encoding="utf-8")))):
            found.setdefault(claim_id, []).append(where)
    return found


def scanned_documents(repo_root: Path) -> list[Path]:
    """Every document a claim can be stated in, deduplicated and sorted."""
    seen: dict[Path, None] = {}
    for pattern in SCANNED_DOCUMENTS:
        for path in repo_root.glob(pattern):
            if path.is_file():
                seen.setdefault(path, None)
    return sorted(seen, key=lambda path: _relative(path, repo_root))


def published_ids(repo_root: Path) -> dict[str, list[str]]:
    """Claim id to everywhere it is published: a page that calls it, a document
    that marks it.

    One mapping rather than two, because the question every check below asks is
    whether anything publishes this, and a figure restated in prose is published
    exactly as much as one rendered on a page.
    """
    found = referenced_ids(repo_root)
    for path in scanned_documents(repo_root):
        where = _relative(path, repo_root)
        for claim_id in sorted(set(FACT_IDS.findall(path.read_text(encoding="utf-8")))):
            found.setdefault(claim_id, []).append(where)
    return found


def anchor_issues(repo_root: Path, where: str, source: str, quote: str) -> list[str]:
    """Whether one anchor still names a sentence, and exactly one of them.

    Shared by claims and retractions because the failure is the same failure: a
    retraction whose correction has been rewritten away is no more enforceable
    than a claim whose source sentence has.
    """
    path = repo_root / source
    if not path.is_file():
        return [
            f"{where} cites `{source}`, which does not exist. An anchor into a document "
            "that is not there pins nothing."
        ]

    text = normalise(path.read_text(encoding="utf-8"))
    occurrences = text.count(normalise(quote))
    if occurrences == 0:
        return [
            f"{where} quotes a sentence `{source}` no longer contains. Either the "
            "document moved on and the page did not, or the quote was never exact. "
            "Re-read the source and update both."
        ]
    if occurrences > 1:
        return [
            f"{where} quotes a sentence that appears {occurrences} times in `{source}`. "
            "An anchor that matches twice can go on matching the stale one: "
            "`docs/STATUS.md` holds ~4,240, ~4,600 and ~4,816 as three true sentences, "
            "and a quote that does not tell them apart checks nothing. Quote more of "
            "the sentence."
        ]
    return []


def _numeric_issues(claim: Claim, source_text: str) -> list[str]:
    """Whether the published number is the one the anchored sentence carries."""
    where = f"claim `{claim.id}`"

    if normalise(claim.value) not in normalise(claim.quote):
        return [
            f"{where} publishes `{claim.value}`, which is not in the sentence it quotes. "
            "The anchor pins the sentence and not the number, so the quote would go on "
            "resolving while the page published anything at all."
        ]

    issues: list[str] = []
    if claim.latest is not None:
        try:
            pattern = re.compile(claim.latest)
        except re.error as error:
            return [
                f"{where} declares `latest` as `{claim.latest}`, which is not a regular "
                f"expression ({error.msg}). Nothing can be checked against a pattern "
                "that does not compile."
            ]
        # Group 1 when the pattern has one, so `latest` can carry the context
        # that identifies the figure without that context becoming part of what
        # is compared. Without it the pattern has to be a bare number shape,
        # which either misses the next correction or matches every unrelated
        # number below it -- both of which happened on 2026-08-19, in that
        # order, to this claim.
        found = [
            match.group(1) if match.groups() else match.group(0)
            for match in pattern.finditer(source_text)
        ]
        if not found:
            issues.append(
                f"{where} declares `latest` as `{claim.latest}` and nothing in "
                f"`{claim.source}` matches it. A guard against an appended correction "
                "that matches nothing cannot see one."
            )
        elif found[-1] != claim.value:
            issues.append(
                f"{where} publishes `{claim.value}` and the last `{claim.latest}` in "
                f"`{claim.source}` is `{found[-1]}`. Corrections there are appended "
                "rather than rewritten, so the last one is the live figure and the page "
                "is publishing a superseded one."
            )

    if claim.rounded is not None:
        # `value` is the published string, so it may carry `~`, `%` or thousands
        # separators. Strip that decoration before parsing, and compare numbers.
        bare_value = claim.value.translate(_DECORATION)
        bare_rounded = claim.rounded.translate(_DECORATION)
        try:
            exact, shown = float(bare_value), float(bare_rounded)
        except ValueError:
            issues.append(
                f"{where} declares `rounded` as `{claim.rounded}` against a value of "
                f"`{claim.value}`, and the two do not both parse as numbers. `rounded` "
                "is a claim about arithmetic; it needs arithmetic to check."
            )
        else:
            places = len(bare_rounded.partition(".")[2])
            if round(exact, places) != shown:
                issues.append(
                    f"{where} rounds `{claim.value}` to `{claim.rounded}`. To {places} "
                    f"decimal places it is `{round(exact, places):.{places}f}`. A rounded "
                    "figure is the one most readers take away, so it is the one worth "
                    "being wrong in."
                )
    return issues


def _shape_issues(
    entry: object, where: str, required: tuple[str, ...], optional: tuple[str, ...]
) -> list[ClaimIssue]:
    if not isinstance(entry, dict):
        return [ClaimIssue(CLAIMS_PATH, f"{where} is not an object.")]
    issues = [
        ClaimIssue(
            CLAIMS_PATH,
            f"{where} has no string `{field}`. Every field is required, `why` included: "
            "a register entry with no stated reason is the note that outlives the "
            "situation it describes, which is how the last two dead integrity modules "
            "stayed invisible.",
        )
        for field in _missing_fields(entry, required, optional)
    ]
    issues += [
        ClaimIssue(
            CLAIMS_PATH,
            f"{where} has `{field}`, which nothing reads. Known fields are "
            f"{', '.join(f'`{name}`' for name in (*required, *optional))}. Every guard "
            "here is opt-in, so a key nobody reads is a check nobody runs: `lastest` "
            "for `latest` turned off the currency check and passed a superseded total, "
            "silently.",
        )
        for field in _unknown_fields(entry, (*required, *optional))
    ]
    return issues


def _claim_issues(repo_root: Path, claims: list[Claim]) -> list[ClaimIssue]:
    issues: list[ClaimIssue] = []
    seen: set[str] = set()
    for claim in claims:
        if claim.id in seen:
            issues.append(
                ClaimIssue(
                    CLAIMS_PATH,
                    f"declares `{claim.id}` twice. Which of the two a page publishes "
                    "depends on read order, so one of them is checked and the other is "
                    "decoration.",
                )
            )
        seen.add(claim.id)

    for claim in claims:
        anchors = anchor_issues(repo_root, f"claim `{claim.id}`", claim.source, claim.quote)
        if anchors:
            issues += [ClaimIssue(CLAIMS_PATH, message) for message in anchors]
            continue
        source_text = normalise((repo_root / claim.source).read_text(encoding="utf-8"))
        issues += [
            ClaimIssue(CLAIMS_PATH, message) for message in _numeric_issues(claim, source_text)
        ]
    return issues


def _reference_issues(repo_root: Path, claims: list[Claim]) -> list[ClaimIssue]:
    published = published_ids(repo_root)
    declared = {claim.id for claim in claims}

    issues = [
        ClaimIssue(
            CLAIMS_PATH,
            f"declares `{claim.id}` and nothing publishes it. A claim nothing publishes "
            "is a note that outlives the situation it describes: delete it, call "
            f"`claim('{claim.id}')` from the page that states it, or mark it with "
            f"`de:fact {claim.id}` in the document that does. Like every other register "
            "here, this one may only shrink.",
        )
        for claim in claims
        if claim.id not in published
    ]
    issues += [
        ClaimIssue(
            where[0],
            f"publishes `{claim_id}` and `{CLAIMS_PATH}` does not declare it. An "
            "undeclared claim renders as nothing and is backed by nothing.",
        )
        for claim_id, where in sorted(published.items())
        if claim_id not in declared
    ]
    # A marker in the claim's own source would let `de sync` rewrite the
    # sentence the register quotes, from the value that sentence is supposed to
    # be checked against. The anchor would still resolve and check nothing.
    issues += [
        ClaimIssue(
            claim.source,
            f"marks `{claim.id}` in the document the register quotes for it. `de sync` "
            "would then rewrite the anchor sentence from the value the anchor exists to "
            "verify. Restate the figure somewhere else, or quote a different sentence.",
        )
        for claim in claims
        if claim.source in published.get(claim.id, [])
    ]
    return issues


def _retraction_issues(repo_root: Path, retractions: list[Retraction]) -> list[ClaimIssue]:
    pages = {
        _relative(page, repo_root): page.read_text(encoding="utf-8")
        for page in scanned_pages(repo_root)
    }

    issues: list[ClaimIssue] = []
    seen: set[str] = set()
    for retraction in retractions:
        issues += [
            ClaimIssue(
                where,
                f"publishes `{retraction.phrase}`, which `{retraction.source}` retracts. "
                f"{retraction.why}",
            )
            for where, text in pages.items()
            if retraction.phrase in text
        ]
        issues += [
            ClaimIssue(CLAIMS_PATH, message)
            for message in anchor_issues(
                repo_root, f"retraction `{retraction.phrase}`", retraction.source, retraction.quote
            )
        ]
        if retraction.phrase in seen:
            issues.append(
                ClaimIssue(
                    CLAIMS_PATH,
                    f"retracts `{retraction.phrase}` twice, with two reasons. The second "
                    "is unreachable and will rot unread.",
                )
            )
        seen.add(retraction.phrase)
    return issues


def check_claims(repo_root: Path) -> list[ClaimIssue]:
    """Refuse a site publishing a fact this repository can no longer show."""
    if not site_present(repo_root):
        return []

    path = repo_root / CLAIMS_PATH
    if not path.is_file():
        return [
            ClaimIssue(
                CLAIMS_PATH,
                "is missing. It is the one list of what the pages publish and what backs "
                "it, read by this gate and by the pages themselves, so without it the "
                "site states figures nothing can check.",
            )
        ]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [
            ClaimIssue(
                CLAIMS_PATH,
                f"is not parseable JSON ({error.msg}, line {error.lineno}). A truncated "
                "write must not read as `this site claims nothing`, which is what every "
                "check below would then report.",
            )
        ]

    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        return [
            ClaimIssue(
                CLAIMS_PATH,
                "has no `claims` array at the top level. The register's shape is "
                "`{note, claims, retractions}`; anything else reads as an empty register "
                "and reports green over a page full of numbers.",
            )
        ]

    # Same reasoning as `_unknown_fields`, one level up and worse. `retraction`
    # for `retractions` deletes the whole retraction register, and the step goes
    # on printing "0 retraction(s)" as though nothing were wrong -- an absent
    # section and a misspelt one are indistinguishable to every check below.
    stray = sorted(key for key in data if key not in _SECTIONS)
    if stray:
        return [
            ClaimIssue(
                CLAIMS_PATH,
                f"has top-level {', '.join(f'`{key}`' for key in stray)}, which nothing "
                f"reads. The register's shape is {', '.join(f'`{k}`' for k in _SECTIONS)}. "
                "A misspelt section is an empty section, and an empty section is green.",
            )
        ]

    if path.resolve() not in {candidate.resolve() for candidate in input_files(repo_root)}:
        return [
            ClaimIssue(
                CLAIMS_PATH,
                "is not one of the site's inputs. Add it to the `site` array in "
                "`site/inputs.json`, which lists files by name rather than by glob. "
                "Until it does, this file can change without the build manifest going "
                "stale — so a claim could be edited to agree with a page that was never "
                "rebuilt.",
            )
        ]

    issues: list[ClaimIssue] = []
    for index, entry in enumerate(_section(data, "claims")):
        issues += _shape_issues(entry, f"claim {index}", _CLAIM_FIELDS, _CLAIM_OPTIONAL)
    for index, entry in enumerate(_section(data, "retractions")):
        issues += _shape_issues(entry, f"retraction {index}", _RETRACTION_FIELDS, ())
    if issues:
        return issues

    claims, retractions = load_claims(repo_root)
    return [
        *_claim_issues(repo_root, claims),
        *_reference_issues(repo_root, claims),
        *_retraction_issues(repo_root, retractions),
    ]


def census(repo_root: Path) -> tuple[int, int, int, int]:
    """``(claims_declared, phrases_retracted, pages_scanned, documents_scanned)``.

    An empty claims list is deliberately *not* a refusal, which is the one place
    this module departs from :mod:`decision_evals.site`. A manifest over no
    inputs is current by construction, so ``site.py`` has to refuse it. Here
    non-vacuity comes from the other side: a page calling ``claim()`` with
    nothing declared is refused, so a site that makes no unbacked claims and
    declares none is correctly green rather than vacuously so.
    """
    if not site_present(repo_root):
        return (0, 0, 0, 0)
    claims, retractions = load_claims(repo_root)
    return (
        len(claims),
        len(retractions),
        len(scanned_pages(repo_root)),
        len(scanned_documents(repo_root)),
    )
