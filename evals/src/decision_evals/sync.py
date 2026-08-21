"""Facts the repository already knows, written into the documents that state them.

``decision_evals.docs`` proves that a reference resolves. It cannot prove that a
sentence is true, and its own docstring says so. This module removes one class of
untrue sentence entirely, by taking the writing of it away from people.

A document marks a region with an HTML comment, invisible on github.com and in
the rendered site::

    <!-- de:generated de-commands -->
    | Command | What it does |
    | --- | --- |
    | `de check` | Run the full local gate. No model calls, fully deterministic. |
    <!-- /de:generated -->

``de sync`` writes what is between the markers. ``de check`` refuses a region
whose contents are not what its source would render right now. The document goes
on being prose written by a person; the enumerations inside it stop being.

The occasion was 2026-08-21: ``docs/ARCHITECTURE.md`` went through an
adversarial fact-check and still shipped four false set comparisons with every
path in it resolving. The full account is in ``docs/WHY_THESE_RULES.md``. What
caught them was reading the source and counting, which is the part a machine
does better.

There is a second marker for a number that has to stay inside a sentence::

    a corpus that is <!-- de:fact corpus-solvability -->89%<!-- /de:fact --> solvable

``de:fact`` renders the value from ``site/claims.json``, where the number is
already pinned to one exact sentence in one repository file by
:mod:`decision_evals.claims`. So a figure restated in a fourth document is the
registered one. When the source sentence moves, the anchor check refuses; when
the register is corrected, ``de sync`` carries that correction into every
restatement. That register owns whether
an id exists at all, in both directions and on both surfaces; this module only
renders what it declares.

**What this still does not do.** A region can be correct and the paragraph above
it wrong. Rendering the gate's steps says nothing about the sentence claiming
the gate is offline. That defect is invisible here, as it is everywhere else,
and :mod:`decision_evals.drift` is the answer to it.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: Where a marker is honoured. The same scope as the documentation gate, minus
#: its exclusions: a register or a dated plan is still a document somebody may
#: want a derived table inside, and refusing to render one there would be a
#: surprise with no failure behind it.
SCANNED: Final[tuple[str, ...]] = ("*.md", "docs/**/*.md")

#: The package the module inventory describes, relative to the repository root.
PACKAGE_ROOT: Final = "evals/src/decision_evals"

#: The shipped skill, whose procedure files the router table is checked against.
SKILL_ROOT: Final = "skills/decision-making"

#: The body is everything between the opening marker's newline and the closing
#: marker, its trailing newline included. Writing it as ``\n(?P<body>.*?)\n<!--``
#: instead cannot match an empty region, and a marker pair that fails to match is
#: not inert: the opener pairs with the *next* region's closer, and one
#: ``de sync`` overwrites everything in between. That is how the first run of
#: this module deleted two markers and the prose between them.
_BLOCK: Final = re.compile(
    r"<!--\s*de:generated\s+(?P<id>[a-z0-9-]+)\s*-->\n(?P<body>.*?)<!--\s*/de:generated\s*-->",
    re.DOTALL,
)

_INLINE: Final = re.compile(
    r"<!--\s*de:fact\s+(?P<id>[a-z0-9-]+)\s*-->(?P<body>.*?)<!--\s*/de:fact\s*-->",
    re.DOTALL,
)

_OPEN: Final = re.compile(r"<!--\s*de:(?P<kind>generated|fact)\s+(?P<id>[a-z0-9-]+)\s*-->")

_CLOSE: Final = re.compile(r"<!--\s*/de:(?P<kind>generated|fact)\s*-->")

#: One newline. Named because editing this module through a script turned the
#: escape into the character it stands for, twice, and a bare newline literal
#: in the middle of an expression is a syntax error that reads as a typo.
NEWLINE: Final = "\n"

#: A fence line: three or more backticks, and whatever language tag follows.
_FENCE_LINE: Final = re.compile(r"^(?P<ticks>`{3,})")

#: Python files that are not part of the inventory a reader wants.
_UNLISTED_MODULES: Final[frozenset[str]] = frozenset({"__init__.py"})


@dataclass(frozen=True)
class SyncIssue:
    """One region that is not what its source says."""

    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


@dataclass(frozen=True)
class Command:
    """A registered ``de`` subcommand and the first line of its docstring."""

    name: str
    summary: str


@dataclass(frozen=True)
class GateStep:
    """One step of ``de check``, and whether ``--fast`` keeps it."""

    name: str
    fast: bool


@dataclass(frozen=True)
class Procedure:
    """A file in the shipped skill, and whether ``SKILL.md`` routes to it."""

    filename: str
    routed: bool


@dataclass(frozen=True)
class Facts:
    """Everything the regions are rendered from, gathered once.

    Passed in rather than imported at check time, which is what lets the tests
    build a repository in ``tmp_path`` and exercise the gate against it. The
    pattern is :class:`decision_evals.provenance.GitFacts`, for the same reason.
    """

    commands: tuple[Command, ...]
    steps: tuple[GateStep, ...]
    #: Package label to the modules inside it, in declaration order.
    modules: tuple[tuple[str, tuple[str, ...]], ...]
    procedures: tuple[Procedure, ...]
    #: Arm name to what that arm answers.
    arms: tuple[tuple[str, str], ...]
    #: Claim id to the value the register publishes for it.
    values: Mapping[str, str]


# --------------------------------------------------------------------------- #
# Gathering
# --------------------------------------------------------------------------- #


def module_inventory(repo_root: Path) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """The harness package, top level first and then each subpackage by name."""
    root = repo_root / PACKAGE_ROOT
    if not root.is_dir():
        return ()

    def modules_in(directory: Path) -> tuple[str, ...]:
        return tuple(
            sorted(
                path.stem for path in directory.glob("*.py") if path.name not in _UNLISTED_MODULES
            )
        )

    inventory = [("decision_evals/", modules_in(root))]
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        found = modules_in(child)
        if found:
            inventory.append((f"decision_evals/{child.name}/", found))
    return tuple(inventory)


def procedures(repo_root: Path) -> tuple[Procedure, ...]:
    """Every file in the skill, and whether ``SKILL.md`` names it.

    Named anywhere in the body, not parsed out of the router table. The table's
    shape is the skill author's business and has changed once already; what
    matters to a reader is whether the file is reachable from the entry point at
    all. ``placebo.md`` is the file this exists to keep visible: it ships inside
    the skill, the router never names it, and a reader who assumes otherwise has
    misunderstood what the harness measures.
    """
    root = repo_root / SKILL_ROOT
    entry = root / "SKILL.md"
    if not entry.is_file():
        return ()
    named = set(re.findall(r"\b([a-z][a-z0-9-]*\.md)\b", entry.read_text(encoding="utf-8")))
    return tuple(
        Procedure(path.name, path.name in named)
        for path in sorted(root.glob("*.md"))
        if path.name != "SKILL.md"
    )


def collect_facts(
    repo_root: Path,
    *,
    commands: Iterable[Command],
    steps: Iterable[GateStep],
    arms: Iterable[tuple[str, str]],
    values: Mapping[str, str],
) -> Facts:
    """Gather every fact the regions render from.

    The keyword arguments are live objects the caller already holds -- the Typer
    app's command table, the gate's step table, the arm tuple, the claims
    register. Everything else is read from ``repo_root``, so a test can hand
    this a directory.
    """
    return Facts(
        commands=tuple(commands),
        steps=tuple(steps),
        modules=module_inventory(repo_root),
        procedures=procedures(repo_root),
        arms=tuple(arms),
        values=dict(values),
    )


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def _table(header: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def render_commands(facts: Facts) -> str:
    return _table(
        ("Command", "What it does"),
        ((f"`de {command.name}`", command.summary) for command in facts.commands),
    )


def render_steps(facts: Facts) -> str:
    return _table(
        ("#", "Step", "`--fast`"),
        (
            (str(number), step.name, "runs" if step.fast else "skipped")
            for number, step in enumerate(facts.steps, start=1)
        ),
    )


def render_modules(facts: Facts) -> str:
    return _table(
        ("Package", "Modules"),
        (
            (f"`{package}`", " · ".join(f"`{name}`" for name in names))
            for package, names in facts.modules
        ),
    )


def render_procedures(facts: Facts) -> str:
    return _table(
        ("File", "Named by `SKILL.md`"),
        (
            (f"`{procedure.filename}`", "yes" if procedure.routed else "no")
            for procedure in facts.procedures
        ),
    )


def render_arms(facts: Facts) -> str:
    return _table(
        ("Arm", "What it answers"),
        ((f"`{name}`", purpose) for name, purpose in facts.arms),
    )


#: Every region a document may declare. A renderer nothing renders is refused,
#: the same way an unreachable module with a coverage floor is: a derivation
#: with no reader is a claim about the repository that nobody ever reads.
REGIONS: Final[Mapping[str, Callable[[Facts], str]]] = {
    "de-commands": render_commands,
    "de-check-steps": render_steps,
    "harness-modules": render_modules,
    "skill-procedures": render_procedures,
    "arm-purposes": render_arms,
}


# --------------------------------------------------------------------------- #
# Reading a document
# --------------------------------------------------------------------------- #


def scanned_files(repo_root: Path) -> list[Path]:
    """Every document a marker is honoured in, deduplicated and sorted."""
    seen: dict[Path, None] = {}
    for pattern in SCANNED:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file():
                seen.setdefault(path, None)
    return list(seen)


def _relative(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def fenced_spans(text: str) -> list[tuple[int, int]]:
    """Character ranges inside a fenced code block.

    A document that explains the marker syntax has to be able to show it.
    `docs/DOCUMENTATION_MAP.md` writes the markers out in a fence, and without
    this every one of those would be a live region: the file would publish a
    figure it is only describing, and its unmatched closers would read as
    markers that never close.

    Fences are matched by tick count, so a ```` block wrapping a ``` example
    nests correctly, which is how that document writes it.
    """
    spans: list[tuple[int, int]] = []
    offset = 0
    opened: int | None = None
    ticks = 0
    for line in text.splitlines(keepends=True):
        match = _FENCE_LINE.match(line)
        if match is None:
            offset += len(line)
            continue
        found = len(match["ticks"])
        if opened is None:
            opened, ticks = offset, found
        elif found >= ticks:
            spans.append((opened, offset + len(line)))
            opened = None
        offset += len(line)
    if opened is not None:
        spans.append((opened, offset))
    return spans


def _quoted(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def unbalanced(text: str) -> list[str]:
    """Markers that do not pair up, named by the id that opened them.

    An opener with no closer swallows the rest of the document silently: the
    regex simply does not match, the region is not rendered, and the gate has
    nothing to compare. So the counts are checked before anything else.
    """
    spans = fenced_spans(text)
    opens = [match for match in _OPEN.finditer(text) if not _quoted(match.start(), spans)]
    closes = [match for match in _CLOSE.finditer(text) if not _quoted(match.start(), spans)]
    matched = len(regions_in(text)) + len(facts_in(text))
    if len(opens) == len(closes) == matched:
        return []
    return [
        f"has {len(opens)} marker(s) opened, {len(closes)} closed and {matched} that pair up. "
        "A marker that does not close renders nothing and is compared against nothing."
    ]


def regions_in(text: str) -> list[tuple[str, str]]:
    """Every generated region in a document: its id and its current contents."""
    spans = fenced_spans(text)
    return [
        (match["id"], match["body"])
        for match in _BLOCK.finditer(text)
        if not _quoted(match.start(), spans)
    ]


def facts_in(text: str) -> list[tuple[str, str]]:
    """Every inline fact in a document: its claim id and its current value."""
    spans = fenced_spans(text)
    return [
        (match["id"], match["body"])
        for match in _INLINE.finditer(text)
        if not _quoted(match.start(), spans)
    ]


def apply_text(text: str, facts: Facts) -> str:
    """The document as ``de sync`` would write it.

    An id nothing knows is left exactly as it is. Rewriting it would be a
    guess, and the gate is about to refuse it by name anyway.
    """

    spans = fenced_spans(text)

    def replaced(match: re.Match[str], value: str) -> str:
        whole = match.group(0)
        start = match.start("body") - match.start()
        end = match.end("body") - match.start()
        return whole[:start] + value + whole[end:]

    def block(match: re.Match[str]) -> str:
        renderer = REGIONS.get(match["id"])
        if renderer is None or _quoted(match.start(), spans):
            return match.group(0)
        return replaced(match, renderer(facts) + NEWLINE)

    def inline(match: re.Match[str]) -> str:
        value = facts.values.get(match["id"])
        if value is None or _quoted(match.start(), spans):
            return match.group(0)
        return replaced(match, value)

    return _INLINE.sub(inline, _BLOCK.sub(block, text))


# --------------------------------------------------------------------------- #
# Writing and refusing
# --------------------------------------------------------------------------- #


def sync(repo_root: Path, facts: Facts) -> list[str]:
    """Rewrite every region, returning the documents that changed."""
    changed: list[str] = []
    for path in scanned_files(repo_root):
        text = path.read_text(encoding="utf-8")
        updated = apply_text(text, facts)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(_relative(path, repo_root))
    return changed


def check_sync(repo_root: Path, facts: Facts) -> list[SyncIssue]:
    """Every region a document carries, checked against what it renders from.

    Both directions. A document naming a region that does not exist is refused,
    and so is a region that exists and no document uses -- a renderer with no
    reader is dead weight that will be wrong before anyone notices, which is the
    defect :mod:`decision_evals.wiring` exists to refuse in the harness.
    """
    issues: list[SyncIssue] = []
    used: set[str] = set()

    for path in scanned_files(repo_root):
        where = _relative(path, repo_root)
        text = path.read_text(encoding="utf-8")

        issues.extend(SyncIssue(where, message) for message in unbalanced(text))

        for region_id, body in regions_in(text):
            if _OPEN.search(body):
                issues.append(
                    SyncIssue(
                        where,
                        f"`{region_id}` has another marker inside it. Nesting is not a "
                        "thing markers do; this is an unclosed region reaching forward to "
                        "the next closer, and `de sync` would overwrite everything between.",
                    )
                )
                continue
            if region_id not in REGIONS:
                issues.append(
                    SyncIssue(
                        where,
                        f"declares a generated region `{region_id}`, which nothing renders. "
                        f"Known regions: {', '.join(sorted(REGIONS))}.",
                    )
                )
                continue
            used.add(region_id)
            expected = REGIONS[region_id](facts) + NEWLINE
            if body != expected:
                issues.append(
                    SyncIssue(
                        where,
                        f"`{region_id}` is not what it renders from. Run `de sync`. "
                        f"{_difference(body, expected)}",
                    )
                )

        # An id the register does not declare is left for
        # :mod:`decision_evals.claims`, which owns both directions of that
        # question across pages and documents alike. Refusing it here as well
        # would be two messages for one fix.
        for claim_id, value in facts_in(text):
            expected_value = facts.values.get(claim_id)
            if expected_value is not None and value != expected_value:
                issues.append(
                    SyncIssue(
                        where,
                        f"states `{claim_id}` as {value!r}; the register says "
                        f"{expected_value!r}. Run `de sync`.",
                    )
                )

    issues.extend(
        SyncIssue(
            "decision_evals.sync",
            f"renders `{region_id}` and no document uses it. Delete the renderer or "
            "put the region in the document that needs it.",
        )
        for region_id in sorted(set(REGIONS) - used)
    )
    return issues


def _difference(body: str, expected: str) -> str:
    """The first line that differs, which is almost always the whole story."""
    current = body.splitlines()
    wanted = expected.splitlines()
    for number, (left, right) in enumerate(zip(current, wanted, strict=False), start=1):
        if left != right:
            return f"Line {number} says {left!r}, and renders as {right!r}."
    if len(current) < len(wanted):
        return f"It is missing {len(wanted) - len(current)} line(s), from {wanted[len(current)]!r}."
    if len(current) > len(wanted):
        return f"It has {len(current) - len(wanted)} line(s) that nothing renders."
    return "Every line matches, so what differs is whitespace at an edge."


def census(repo_root: Path) -> tuple[int, int, int]:
    """Documents carrying a marker, regions used, and facts stated."""
    documents = 0
    regions = 0
    facts = 0
    for path in scanned_files(repo_root):
        text = path.read_text(encoding="utf-8")
        found = len(regions_in(text))
        stated = len(facts_in(text))
        if found or stated:
            documents += 1
        regions += found
        facts += stated
    return documents, regions, facts
