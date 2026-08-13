"""Track M4: build the four-skill arm out of the one-skill bundle.

**The question.** `decision-making` ships as one entry with four procedures
behind a router. That choice is currently an extrapolation: skill shadowing is
measured at a **202-skill** library ([arXiv:2605.24050](https://arxiv.org/abs/2605.24050))
and the decision here was made at four. Nobody has measured shadowing at n=4.
M4 races the two structures against each other.

**The trap this module exists to avoid.** The obvious way to build a four-skill
arm is to write four descriptions. Then the race varies *structure* and *the
prose I happened to write* at once, and a difference is uninterpretable — which
is exactly why M4's own text refuses the historical four-skill tree at `9a16b18`
as an arm.

So nothing here is authored. Each of the four descriptions is **composed
mechanically from material already in the shipped `SKILL.md`**:

* the **condition** and the **product**, lifted verbatim from that procedure's
  row of the router table;
* the **shared opener and the shared exclusions**, lifted verbatim from the
  bundle's own ``description`` field and given to all four unchanged.

The four descriptions are therefore the one description's parts, redistributed.
Every word in the four-arm exists in the one-arm and vice versa, so the only
thing that varies is **how many entries the router has to choose between** —
which is the independent variable M4 names.

**What this deliberately does not model.** In a real harness, four skills would
also mean four separate bodies loaded on activation and four sets of
frontmatter. The trigger instrument never sees a body: what is in context when
a model decides whether to fire is the description. Measuring more would measure
a document that is not consulted at that moment. This is a proxy for the
*selection* half of shadowing, and the module says so rather than letting a
reader assume otherwise.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

#: A row of the router table: condition, file, product.
_ROW: Final = re.compile(
    r"^\|\s*(?P<condition>[^|]+?)\s*\|\s*`(?P<file>[^`]+)\.md`\s*\|\s*(?P<product>[^|]+?)\s*\|\s*$"
)

#: The first sentence of the bundle description, which states *when to use it at
#: all*. Shared by all four arms because it is the part that is not about which
#: procedure applies.
_OPENER_END: Final = "Routes to one of four"

#: The exclusions, which are also not about which procedure applies.
_EXCLUSIONS_START: Final = "Do not use for"


class UnbundleError(RuntimeError):
    """The bundle cannot be split, and guessing would author prose."""


@dataclass(frozen=True)
class Procedure:
    """One row of the router table, as its own skill entry."""

    name: str
    condition: str
    product: str

    def description(self, opener: str, exclusions: str) -> str:
        """This procedure's description, with the bundle's shared scope material.

        Word order follows the bundle's own: what it is for, then what it does,
        then what it is not for.
        """
        return f"{opener} {self.condition[0].upper()}{self.condition[1:]}. Produces {self.product}. {exclusions}"


def router_rows(body: str) -> list[Procedure]:
    """The router table, parsed. Raises rather than returning a partial table.

    The header and separator rows are skipped by requiring a backticked
    ``*.md`` in the middle cell, which no header has.
    """
    rows = [
        Procedure(
            name=match.group("file"),
            condition=match.group("condition").strip(),
            product=match.group("product").strip(),
        )
        for line in body.splitlines()
        if (match := _ROW.match(line.strip()))
    ]
    if not rows:
        raise UnbundleError("no router-table rows found; the table's shape has changed")
    return rows


def shared_scope(description: str) -> tuple[str, str]:
    """The opener and the exclusions, verbatim, from the bundle's description.

    Both halves must be found. A missing marker means the description has been
    rewritten and the split would have to be guessed, which is the one thing
    this module must not do — a guessed opener is authored prose wearing a
    mechanical derivation's clothes.
    """
    flat = " ".join(description.split())
    cut = flat.find(_OPENER_END)
    if cut < 0:
        raise UnbundleError(f"opener marker {_OPENER_END!r} not in the description")
    start = flat.find(_EXCLUSIONS_START)
    if start < 0:
        raise UnbundleError(f"exclusions marker {_EXCLUSIONS_START!r} not in the description")
    return flat[:cut].strip(), flat[start:].strip()


#: Track L5's variants, and every one is a **subtraction** from the shipped
#: description rather than a rewrite of it.
#:
#: L5 asks which way of writing a trigger is best, and it is a *primary* axis
#: because availability dominates whether a skill helps at all (+18 to 36pp,
#: [arXiv:2605.31408](https://arxiv.org/abs/2605.31408)). It is also the only
#: skill-variant axis this repository can currently power: firing has 73 items
#: and is stable across repeats, where routing has 14 and cannot reject.
#:
#: Subtraction, not rewriting, for the same reason `four_arm` derives rather than
#: authors. Three variants each removing one named part answers *what does that
#: part buy* — three fresh descriptions would answer *which prose did I like*.
DESCRIPTION_VARIANTS: Final = ("full", "no-exclusions", "opener-only", "no-opener")


def description_variant(description: str, variant: str) -> str:
    """One L5 arm, built by deleting a named part of the shipped description.

    * ``full`` — as shipped. The control.
    * ``no-exclusions`` — the "Do not use for…" list deleted. **The direct test
      of whether the clause authors agonise over does anything at all**; if the
      false-positive rate does not move, the exclusion list is decoration.
    * ``opener-only`` — the *when to use it* sentence alone, with both the
      routing summary and the exclusions gone. The narrowest description that
      still says what the skill is for.
    * ``no-opener`` — the routing summary and exclusions with the *when to use
      it* sentence deleted. The mirror of ``opener-only``, and the arm that says
      which half carries the firing decision.

    Raises:
        UnbundleError: on an unknown variant, or a description whose markers have
            moved so that the split would have to be guessed.
    """
    if variant not in DESCRIPTION_VARIANTS:
        raise UnbundleError(f"unknown variant {variant!r}; known: {DESCRIPTION_VARIANTS}")
    flat = " ".join(description.split())
    if variant == "full":
        return flat
    opener, exclusions = shared_scope(description)
    middle = flat[len(opener) : flat.find(exclusions)].strip()
    if variant == "no-exclusions":
        return f"{opener} {middle}".strip()
    if variant == "opener-only":
        return opener
    return f"{middle} {exclusions}".strip()


def four_arm(description: str, body: str) -> dict[str, str]:
    """Name-to-description for the unbundled arm.

    Args:
        description: the bundle's ``description`` frontmatter field.
        body: the bundle's markdown body, carrying the router table.

    Returns:
        One entry per router-table row, in table order.

    Raises:
        UnbundleError: if the table or the scope markers cannot be found.
    """
    return entries(description, body, len(router_rows(body)))


def entries(description: str, body: str, n: int) -> dict[str, str]:
    """The four procedures redistributed across ``n`` entries — Track M5.

    M4 raced 1 against 4 and found them level on firing while 4 routed better.
    M5 asks the shape of that: **where does the curve turn?** One entry, two, or
    four, with the same four procedures behind them either way.

    The partition is **contiguous in table order** and as even as possible, so it
    is a function of ``n`` alone. Choosing *which* procedures to group would be a
    second manipulation — pairing `cascade` with `timing` rather than with
    `ledger` is a hypothesis about their overlap, and it is M5's follow-up rather
    than a free parameter here.

    An entry covering several procedures lists their conditions in table order,
    joined by *"or"*, and its products likewise. That is the one join this module
    performs and it is declared: ``or`` is the only word added, it appears in
    every multi-procedure entry, and so it cannot differentiate them.

    **A confound this cannot remove, stated rather than hidden.** Mechanical
    joining reads worse than a human would write. At ``n=4`` every entry is one
    clean clause; at ``n=2`` each is *"…what it spends or the direction is
    settled and the question is when"*. So an n=2 disadvantage may be **prose
    quality rather than entry count**, and the only clean contrast in the whole
    curve is n=1 against n=4, where both arms are equally clumsy or equally not.
    Any middle point is suggestive and must be reported as such — writing four
    fluent merged descriptions would fix the prose and reintroduce exactly the
    authoring problem the module exists to avoid.

    Args:
        description: the bundle's ``description`` frontmatter field.
        body: the bundle's markdown body, carrying the router table.
        n: how many entries to produce, from 1 to the number of rows.

    Returns:
        ``n`` entries, keyed by the joined names of the procedures they cover,
        in table order.

    Raises:
        UnbundleError: on an ``n`` outside the table's size, or if the table or
            the scope markers cannot be found.
    """
    rows = router_rows(body)
    if not 1 <= n <= len(rows):
        raise UnbundleError(f"n must be 1..{len(rows)} for a {len(rows)}-row table, got {n}")

    # Contiguous, as even as possible: the first `len(rows) % n` groups get one
    # extra row. Deterministic in n, which is the point.
    size, extra = divmod(len(rows), n)
    grouping: list[tuple[str, ...]] = []
    start = 0
    for index in range(n):
        stop = start + size + (1 if index < extra else 0)
        grouping.append(tuple(row.name for row in rows[start:stop]))
        start = stop
    return entries_grouped(description, body, grouping)


def entries_grouped(
    description: str, body: str, grouping: Sequence[Sequence[str]]
) -> dict[str, str]:
    """The procedures redistributed across an **explicitly chosen** grouping — M6.

    M5 held the count fixed and let the partition fall out of table order, so its
    arm was a function of ``n`` alone. That deliberately left *which* procedures
    share an entry unmeasured, and it is not a neutral choice: the router table
    gives *order* to `cascade` and *when* to `timing`, and those two were
    diagnosed as colliding on 2026-08-12 before any of this ran. M5's contiguous
    partition puts the colliding pair **inside one entry**, where a confusion
    between them cannot be observed at all.

    M6 varies the grouping at fixed ``n`` to find out how much of M5's routing
    number was the collision being hidden.

    Clause order within an entry stays **table order** whatever the grouping, so
    that regrouping does not smuggle in a second manipulation of how the merged
    sentence reads.

    Args:
        description: the bundle's ``description`` frontmatter field.
        body: the bundle's markdown body, carrying the router table.
        grouping: the procedure names per entry. Must partition the table
            exactly — every row once, no row twice, no name the table lacks.

    Returns:
        One entry per group, keyed by the joined names of the procedures it
        covers, each group's names in table order.

    Raises:
        UnbundleError: if ``grouping`` is not an exact partition of the table.
    """
    rows = router_rows(body)
    order = {row.name: index for index, row in enumerate(rows)}

    flat = [name for group in grouping for name in group]
    if any(not group for group in grouping):
        raise UnbundleError("an empty group is not an entry")
    unknown = sorted(set(flat) - set(order))
    if unknown:
        raise UnbundleError(f"not in the router table: {', '.join(unknown)}")
    if len(flat) != len(set(flat)):
        raise UnbundleError("a procedure appears in more than one group")
    missing = sorted(set(order) - set(flat))
    if missing:
        # Dropping a procedure would change what the arm can do, not how it is
        # grouped, and the two would be inseparable in the result.
        raise UnbundleError(f"grouping must cover every procedure, missing: {', '.join(missing)}")

    opener, exclusions = shared_scope(description)
    by_name = {row.name: row for row in rows}
    out: dict[str, str] = {}
    for group in grouping:
        ordered = [by_name[name] for name in sorted(group, key=lambda name: order[name])]
        merged = Procedure(
            name="-".join(row.name for row in ordered),
            condition=" or ".join(row.condition[0].lower() + row.condition[1:] for row in ordered),
            product=" or ".join(row.product for row in ordered),
        )
        out[merged.name] = merged.description(opener, exclusions)
    return out


def covering(names: dict[str, str], procedure: str) -> str | None:
    """Which entry covers ``procedure``, or ``None`` if none does.

    Scoring an M5 arm needs this: at n=2 a case labelled ``ledger`` is routed
    correctly when the model picks the entry *containing* ``ledger``, not one
    named ``ledger``.

    **Accuracy across different ``n`` is not comparable and must not be plotted
    as one curve without saying so** — a 2-way choice has chance 0.5 and a 4-way
    choice has chance 0.25. Firing is the comparable outcome.
    """
    for name in names:
        if procedure in name.split("-"):
            return name
    return None
