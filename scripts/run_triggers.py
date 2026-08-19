"""Measure the shipped skill's description: does it fire when it should?

Track M / Track S. Skill availability is the dominant term in whether a skill
helps at all, and availability is decided by the description. This has never
been measured here on any skill.

**It needs no answer key**, which is why it is worth running now. The labels are
trigger labels -- did it fire, and did the router pick the procedure its own
table names -- not judgements about answer quality. That sidesteps the failure
mode behind 21 of 21 scored errors in this repository.

**It is a proxy and says so.** The model is shown the description and asked
whether it would invoke the skill. The real harness decides differently: the
description sits among other skills, in a longer context, with the model
mid-task. This measures the description's discriminative content, not the
deployed firing rate.

Each case is one isolated call with a fresh working directory and the isolation
receipt asserted, so nothing on disk can influence the decision.

Usage:
    python scripts/run_triggers.py [--model haiku] [--skill decision-making]
                                   [--repeats 5] [--confidence] [--arm one|four]
                                   [--set PATH] [--band s|m|l|xl] [--in-situ]

``--set`` names the corpus. It defaults to ``datasets/triggers/<skill>.yaml``,
which is version 2 and is what every published number was measured on, and the
version 3 corpus is reached by pointing it at
``datasets/triggers/decision-making/index.yaml``. **A non-default set gets its
own checkpoint**, because two corpora are two answer keys: a resume against a
shared path would skip a case id that exists in the file under a different
label, and the run would look complete. That is the same shape as the label
move on 2026-08-13 that gave every arm five points it did not earn.

``--band`` runs one length stratum. It does *not* change the checkpoint — a band
is a subset of the same items under the same labels, so a band run and a later
full run resume into each other, which is the point of running the cheap bands
first. A band the set does not contain is refused rather than run: zero cases
would produce a clean, complete, empty run, and this instrument has twice
shipped an estimator that could only return zero.

``--confidence`` additionally elicits a probability and scores it. It writes to
its own checkpoint: asking for a probability changes the response contract, so a
confidence run and a plain one are two runs, not one run with an extra column.

``--arm four`` is Track M4: the same four procedures presented as four separate
tools instead of one tool with a router. Its descriptions are composed
mechanically by :mod:`decision_evals.unbundle` from the shipped bundle, so the
race varies structure and nothing else. Its own checkpoint, for the same reason
as ``--confidence`` -- and the two flags are refused together, because two
changes to the response contract in one run measure neither.

``--in-situ`` is Track N9: the same one-turn call, description and question
unchanged, sent via ``--append-system-prompt`` instead of ``--system-prompt``
so the description joins the CLI's own system prompt rather than replacing
it -- the position every deployed call actually uses. It moves the venue, not
the response contract, so it is refused alongside ``--confidence``,
``--entries``/``--arm four`` and a non-``full`` ``--description``: combining
any of them would confound venue with a second manipulation. Its own
checkpoint, for the same reason as the arms above.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decision_evals.corpus import BANDS  # noqa: E402
from decision_evals.providers.claude_code import (  # noqa: E402
    CliError,
    Conversation,
    IsolationError,
    isolated_cwd,
)
from decision_evals.skills import parse_skill  # noqa: E402
from decision_evals.trigger_arms import (  # noqa: E402
    ArmError,
    bootstrap_rate,
    bootstrap_rate_difference,
    false_positive_rate_by_kind,
    format_bands,
    format_difference,
    format_negative_kinds,
    format_rate,
    format_routing,
    routing_by_procedure,
    summarise,
    summarise_by_band,
)
from decision_evals.triggers import (  # noqa: E402
    TRIGGERS_DIR,
    TriggerCase,
    TriggerSet,
    Verdict,
    decision,
    default_procedures,
    evaluate,
    evaluate_routing,
    load_trigger_set,
    routing_is_by_name,
)
from decision_evals.unbundle import (  # noqa: E402
    DESCRIPTION_VARIANTS,
    UnbundleError,
    covering,
    description_variant,
    entries,
    entries_grouped,
)

#: The procedure names from the shipped skill's own router table, as the
#: ``"name"|"name"|...`` fragment the JSON contract below shows the model.
#: Built from :func:`~decision_evals.triggers.default_procedures` rather than
#: listed here, so a procedure added to or removed from the router table
#: changes what the judge is offered without this file being edited.
#:
#: Read at import: unlike ``default_procedures`` inside ``triggers.py`` (which
#: resolves lazily precisely because it is imported by nearly everything in
#: the package), ``SYSTEM`` and ``SYSTEM_CONFIDENCE`` below are module-level
#: strings this script's tests read as data (``runner.SYSTEM``), so they must
#: exist as values rather than calls -- and this script is never imported for
#: anything but running or testing itself, so the narrower blast radius is
#: acceptable here in a way it is not for ``triggers.py``.
_PROCEDURE_SCHEMA = "|".join(f'"{name}"' for name in default_procedures())
_N_PROCEDURES = len(default_procedures())

#: The judge sees the skill's own description and router table and nothing else.
#: Not the procedure bodies: what the harness has in context when it decides
#: whether to fire is the frontmatter description, and giving it more would
#: measure a document that is never consulted at that moment.
SYSTEM = (
    "You decide whether a tool should be used. You are given one tool's "
    "description and one message a user sent. Answer with a single line of "
    "JSON and nothing else:\n"
    f'{{"fire": true|false, "procedure": {_PROCEDURE_SCHEMA}|null}}\n'
    "`fire` is whether this tool should be invoked for this message. "
    f"`procedure` is which of the tool's {_N_PROCEDURES} procedures applies, or "
    "null if you would not invoke it or cannot tell."
)

#: The same task with a probability attached. Track K6 ranks *elicited
#: confidence* above every other framework-derived skill candidate on evidence
#: strength, and `stats/calibration.py` had been property-tested to 100% coverage
#: since the first week without ever being called by anything. **This arm is what
#: called it**, and the sentence above stayed in the past tense only from
#: 2026-08-19, when a Track S update quoted it as still true. A comment that
#: describes a gap its own code closed is the documentation defect this
#: repository keeps finding; the tense is the fix. This is the first forecast
#: this repository has asked a model for.
#:
#: It asks for **P(this tool should be invoked)**, not for confidence in the
#: model's own answer. The two are different quantities and only the first is a
#: forecast: it has an outcome -- the case's label -- so Brier, the Murphy
#: decomposition and a reliability diagram all apply directly. "How sure are you"
#: about one's own output has no outcome to score against without deciding the
#: output was wrong, which is the act this repository does not perform.
#:
#: `fire` stays a separate hard decision so the firing metrics keep their shape
#: and the two runs stay comparable on that axis -- but only on that axis. Asking
#: for a probability changes the response contract, which can change the decision,
#: so a confidence run gets its own checkpoint and must not be pooled with a
#: plain one.
SYSTEM_CONFIDENCE = (
    "You decide whether a tool should be used. You are given one tool's "
    "description and one message a user sent. Answer with a single line of "
    "JSON and nothing else:\n"
    f'{{"fire": true|false, "procedure": {_PROCEDURE_SCHEMA}|null, '
    '"p_fire": 0.0}\n'
    "`fire` is whether this tool should be invoked for this message. "
    f"`procedure` is which of the tool's {_N_PROCEDURES} procedures applies, or "
    "null if you would not invoke it or cannot tell. "
    "`p_fire` is your probability between 0 and 1 that this tool should be "
    "invoked -- not how confident you are in your own answer. Use the full range: "
    "0.5 means genuinely undecided, and a well-calibrated 0.7 is right about "
    "seven times in ten."
)

#: Track M4's other arm: the shipped procedures presented as **separate
#: tools** rather than one tool with a router.
#:
#: The task is deliberately the same shape — fire or do not, and name which — so
#: the two arms score on one metric and differ only in how many entries the
#: model is choosing between. What changes is where the choice happens: in the
#: one-entry arm the model decides to fire and *then* routes inside the tool; in
#: this arm firing and routing are a single act, because declining to name a tool
#: is declining to fire.
#:
#: That collapse is not a flaw in the design, it **is** the hypothesis. Skill
#: shadowing's stated mechanism is description overlap at selection time
#: (arXiv:2605.24050), and four descriptions that share an opener and an
#: exclusion list are overlapping by construction. If the one-entry choice is
#: right, this arm should fire *less* accurately.
SYSTEM_FOUR = (
    "You decide whether a tool should be used. You are given several tools' "
    "descriptions and one message a user sent. Answer with a single line of "
    "JSON and nothing else:\n"
    '{"fire": true|false, "tool": "<tool name>"|null}\n'
    "`fire` is whether any of these tools should be invoked for this message. "
    "`tool` is the name of the one to invoke, or null if you would not invoke "
    "any of them."
)


def four_arm_block(descriptions: dict[str, str]) -> str:
    """The four tools, rendered as the prompt's tool section.

    Order is the router table's, held fixed across cases. Shuffling per case
    would add a nuisance factor to a run whose whole point is a between-arm
    comparison, and shuffling per *arm* is meaningless when the other arm has
    one entry. Position effects within the four are M5's question, not M4's.
    """
    return "\n\n".join(f"### {name}\n\n{text}" for name, text in descriptions.items())


def ask(
    description: str,
    case: TriggerCase,
    model: str,
    system: str,
    allowed: tuple[str, ...] | None = None,
    *,
    in_situ: bool = False,
) -> tuple[Verdict, str]:
    """The verdict **and the raw reply**.

    The raw text is returned so it can be stored, because on 2026-08-12 a parser
    whitelist discarded every answer in a 365-call run and the records kept
    nothing to recover from — the run had to be repeated. ``ShardedRecord`` had
    already learned this and says so in its own docstring; this runner had not.

    ``allowed`` defaults to ``None``, which :func:`~decision_evals.triggers.decision`
    resolves to :func:`~decision_evals.triggers.default_procedures` itself --
    the shipped skill's own procedures, not a list copied here.

    ``in_situ`` is Track N9's venue switch. ``Conversation`` already threads it
    to ``build_command``, which sends ``--append-system-prompt`` instead of
    ``--system-prompt`` -- the description joins the CLI's own system prompt
    rather than replacing it, which is the position every deployed call
    actually uses. Conversation length is untouched: still one turn, still a
    fresh isolated process per call. Only where the description sits changes.
    """
    header = "Tool descriptions" if system is SYSTEM_FOUR else "Tool description"
    prompt = f"## {header}\n\n{description}\n\n## User message\n\n{case.turn}"
    with (
        isolated_cwd("de-trigger-") as cwd,
        Conversation(system_prompt=system, model=model, cwd=cwd, in_situ=in_situ) as chat,
    ):
        result = chat.send(prompt)
        chat.receipt.assert_isolated()
    return decision(result.text, allowed), result.text


CHECKPOINT = REPO_ROOT / "results" / "triggers" / "verdicts.jsonl"

#: A separate file, not a column. Asking for a probability changes the response
#: contract and can change the decision, so the two runs are not one run with an
#: extra field -- and a shared path plus a resume would have silently merged them.
CHECKPOINT_CONFIDENCE = REPO_ROOT / "results" / "triggers" / "verdicts-confidence.jsonl"

#: Track M4's four-skill arm, again on its own file. Same reason: a different
#: response contract is a different run, and a shared path plus a resume would
#: have merged the two arms of the experiment into one indistinguishable pile.
CHECKPOINT_FOUR = REPO_ROOT / "results" / "triggers" / "verdicts-four.jsonl"

#: Track N9's venue arm, again on its own file. `--confidence` and `--arm four`
#: earn a separate checkpoint because they change the *response contract*;
#: `in_situ` changes neither the question asked nor the schema of the answer,
#: but it changes what the model sees when it answers -- the description sits
#: beside the CLI's own system prompt instead of replacing it. That is a
#: different venue producing the number, by the same reasoning the file's
#: module docstring already gives for corpora and description variants: a
#: shared path plus a resume would silently merge N9's arm into N6's reference
#: run, and N9 exists specifically to keep the two comparable rather than
#: conflated.
CHECKPOINT_IN_SITU = REPO_ROOT / "results" / "triggers" / "verdicts-in-situ.jsonl"


def load_done(path: Path) -> dict[tuple[str, int], dict[str, object]]:
    """Verdicts already collected, keyed by (case id, repeat)."""
    if not path.exists():
        return {}
    done = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            done[(str(row["case"]), int(row["repeat"]))] = row
    return done


def parse_rate_over_all_repeats(
    trigger_set: TriggerSet, done: dict[tuple[str, int], dict[str, object]], repeats: int
) -> tuple[int, int]:
    """``(unparseable, total)`` over every call the run was asked to make.

    Every one of ``repeats`` repeats for every case in ``trigger_set``, not
    repeat 0 alone. The parse-rate floor exists to catch format compliance
    breaking down, and format compliance is a per-call property: a repeat that
    came back as unparseable prose is a failure in that repeat regardless of
    whether a sibling repeat of the same item happened to parse. Averaging
    that away at the item level -- "parseable if any repeat parsed" -- would
    let a lucky repeat mask a broken one; on Track N9's data it reads 0.957
    (247 of 258 items have at least one parseable repeat) against 0.8643 over
    all 516 calls, a ten-point gap that would have flipped N9's disposition
    from void to published.

    This also keeps "unparseable" meaning the same thing everywhere in this
    file: it is the same per-call test :func:`decision_evals.trigger_arms.summarise`
    already applies when it excludes ``fired is None`` rows from every rate.

    A case with no row at all for a given repeat -- collection stopped early
    or crashed before reaching it -- counts as unparseable rather than being
    dropped from the denominator, for the same reason the old repeat-0 loop
    treated a missing row that way: a smaller denominator from missing calls
    must not let an interrupted run look cleaner than a completed one.

    Before this function existed the floor read ``done.get((case.id, 0))``
    only, so a 2-repeat run's void decision was made on half its calls. Track
    N9 (``results/decision-making/2026-08-19-505b236-n9-in-situ-void/``)
    exposed it: repeat 0 alone parses at 0.8566, repeat 1 alone at 0.8721, the
    aggregate this function computes at 0.8643. All three sit below the 90%
    floor so N9's void was the right call, but only by luck -- a run whose
    repeat 0 happened to clear 0.90 while repeat 1 dragged the true rate under
    it would have exited 0 and been published as a passing run.
    """
    total = len(trigger_set.cases) * repeats
    unparseable = sum(
        1
        for case in trigger_set.cases
        for repeat in range(repeats)
        if (row := done.get((case.id, repeat))) is None or row["fired"] is None
    )
    return unparseable, total


def collect(
    trigger_set: TriggerSet,
    description: str,
    model: str,
    repeats: int,
    *,
    system: str = SYSTEM,
    checkpoint: Path = CHECKPOINT,
    entry_names: dict[str, str] | None = None,
    in_situ: bool = False,
    skill_version: str | None = None,
) -> dict[tuple[str, int], dict[str, object]]:
    """Run every case `repeats` times, checkpointing after each call.

    Resumable, because two runs already showed the item verdicts moving and the
    honest number needs enough repeats that a lost run would be expensive to
    redo.

    `skill_version` is `metadata.version` from the `SKILL.md` that produced
    `description` -- `main()` reads it via `parse_skill` rather than this
    function hardcoding one, because a run of `collect()` against a synthetic
    or historical description (an `--entries` arm, a `--description` variant)
    is not necessarily scoring the shipped file at all. `None` is a legitimate
    caller choice, not an omission: it is what every call site outside
    `main()` should pass when there is no `SKILL.md` behind the description,
    and `skill_versions_comparable` (`trigger_arms.py`) already treats an
    absent value as unknown rather than a default.
    """
    done = load_done(checkpoint)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    cases = trigger_set.cases
    total = len(cases) * repeats

    with checkpoint.open("a", encoding="utf-8") as handle:
        for repeat in range(repeats):
            for index, case in enumerate(cases):
                if (case.id, repeat) in done:
                    continue
                allowed = tuple(entry_names) if entry_names else default_procedures()
                try:
                    (fired, procedure, p_fire), raw = ask(
                        description, case, model, system, allowed, in_situ=in_situ
                    )
                except IsolationError:
                    raise
                except CliError as error:
                    fired, procedure, p_fire, raw = None, None, None, str(error)
                    print(f"  r{repeat} {case.id}: call failed -- {error}")
                # ``covers`` is the routing outcome that survives a changing
                # entry count: at n=2 the model names ``ledger-fit`` and the
                # label is ``ledger``, so equality is the wrong test. Computed
                # mechanically by ``covering`` -- no judgement is applied to a
                # response here.
                covers: bool | None = None
                if case.route:
                    wanted = covering(entry_names, case.route) if entry_names else case.route
                    covers = procedure is not None and procedure == wanted
                row = {
                    "case": case.id,
                    "repeat": repeat,
                    "fired": fired,
                    "procedure": procedure,
                    "covers": covers,
                    # The label revision this verdict was scored against. A run
                    # made before 2026-08-13 sits at version 1, where `x-n21`
                    # was a positive; moving it raised recall 3-5pp on every arm
                    # with no call re-made. Stored so a comparison can refuse.
                    "set_version": trigger_set.version,
                    # The tier that produced it. Same defect as `set_version`,
                    # one axis over: `--model` is an argument with a default, it
                    # moves every number in the run, and until this line existed
                    # the tier survived only as prose in a hand-written README.
                    # `models_comparable` refuses a comparison that spans it.
                    "model": model,
                    # N9's venue. True means the description was appended to
                    # the CLI's own system prompt (`--append-system-prompt`,
                    # the position every deployed call actually uses); False
                    # means it replaced the system prompt outright, which is
                    # every arm published before this row existed.
                    #
                    # Always written, unlike `model`. An absent `model` had to
                    # be read as *unknown* (N8) because `--model` already had a
                    # default that could be silently overridden before the
                    # stamp existed, so an unstamped record's tier genuinely
                    # could have been anything. `in_situ` has no such history:
                    # before this parameter existed, `ask()` built every
                    # `Conversation` with no `in_situ` argument at all, which
                    # `Conversation.__init__`'s own default resolves to
                    # `in_situ=False` -- there is no call this file ever made
                    # that could have been in situ without this stamp. So
                    # `venue_comparable` (trigger_arms.py) treats an absent
                    # value as False, the same way `label_versions_comparable`
                    # treats an absent `set_version` as 1: it states what
                    # happened rather than declaring the past unrecoverable.
                    "in_situ": in_situ,
                    # `metadata.version` from the `SKILL.md` that produced
                    # `description`, or `None` when the caller has none to
                    # give. `set_version` above tracks the *corpus* label
                    # revision; this tracks the *skill* revision, and they
                    # move independently -- the 2026-08-19 bump rewrote the
                    # frontmatter `description` (four procedures to six)
                    # without touching a single label. Unlike `in_situ`, an
                    # absent value here is read as unknown rather than a
                    # fact: `metadata.version` has moved three times on
                    # record (0.2.0, 0.2.1, 0.3.0) and the description text
                    # changed with it each time, so a record written before
                    # this stamp existed could have run against any of them.
                    # `skill_versions_comparable` (`trigger_arms.py`) refuses
                    # a comparison spanning a stamped arm and an unstamped
                    # one for exactly that reason -- the same call it makes
                    # for `model`, not the one it makes for `in_situ`.
                    "skill_version": skill_version,
                    "p_fire": p_fire,
                    "should_fire": case.should_fire,
                    "route": case.route,
                    # The **whole** routes tuple, not only its first element.
                    #
                    # `route` is `routes[0]` and `covers` above is equality
                    # against it, while `evaluate_routing` accepts any member —
                    # two live scoring rules that disagree on three v3 items.
                    # Stamping the data rather than a second derived boolean
                    # lets either rule be computed from a checkpoint alone, and
                    # leaves `covers` meaning on new records exactly what it
                    # means on the published ones. A field whose definition
                    # changed silently between records is the defect this
                    # instrument keeps shipping; a field that is simply absent
                    # from older records is not.
                    "routes": list(case.routes),
                    # The version 3 strata, copied onto every row rather than
                    # left to be joined back from the YAML at scoring time.
                    #
                    # A checkpoint that names only the case id is readable only
                    # beside the exact revision of the set that produced it, and
                    # this repository has already published four numbers that
                    # moved because a set changed under records nobody re-made.
                    # `band` and `triple` in particular are what
                    # `summarise_by_band` and `bootstrap_rate` read, and a run
                    # whose rows lack them cannot be read per band at all --
                    # which is exactly what both functions refuse to pretend.
                    "band": case.band,
                    "triple": case.triple,
                    "domain": case.domain,
                    "stakes": case.stakes,
                    "ask": case.ask,
                    "kind": case.kind,
                    "raw": raw,
                }
                handle.write(json.dumps(row) + "\n")
                handle.flush()
                done[(case.id, repeat)] = row
                seen = repeat * len(cases) + index + 1
                if seen % 25 == 0 or seen == total:
                    print(f"  {seen}/{total}")
    return done


def report_stability(
    trigger_set: object, done: dict[tuple[str, int], dict[str, object]], repeats: int
) -> None:
    """Per-item stability, and how many repeats the aggregate actually needs."""
    import numpy as np

    from decision_evals.stats import per_item_reliability, repeats_for_reliability

    cases = trigger_set.cases  # type: ignore[attr-defined]
    rows = []
    unstable_fire: list[str] = []
    unstable_route: list[str] = []

    for case in cases:
        verdicts = [done.get((case.id, r)) for r in range(repeats)]
        if any(v is None or v["fired"] is None for v in verdicts):
            continue
        fired = [bool(v["fired"]) for v in verdicts]  # type: ignore[index]
        rows.append([1.0 if f == case.should_fire else 0.0 for f in fired])
        if len(set(fired)) > 1:
            unstable_fire.append(f"{case.id}({sum(fired)}/{repeats})")
        if case.should_fire and case.route:
            chosen = {v["procedure"] for v in verdicts}  # type: ignore[index]
            if len(chosen) > 1:
                unstable_route.append(
                    f"{case.id}({'/'.join(str(c) for c in sorted(chosen, key=str))})"
                )

    scores = np.array(rows, dtype=float)
    print(f"\n{'=' * 60}\nSTABILITY across {repeats} repeats\n{'=' * 60}")
    print(f"  items scored          {len(rows)}")
    print(f"  firing flipped on     {len(unstable_fire)} item(s)")
    for entry in unstable_fire:
        print(f"      {entry}")
    print(f"  routing varied on     {len(unstable_route)} labelled item(s)")
    for entry in unstable_route:
        print(f"      {entry}")

    # `aptitude` and `scatter` are one value PER ITEM -- that is the whole point
    # of the per-item estimator, and the reason it can feed a paired test. The
    # first version of this printed them as scalars and died on the format
    # string, after all 365 calls had been made.
    result = per_item_reliability(scores)
    unsteady = int(np.count_nonzero(result.scatter))
    print(f"\n  ICC                   {result.icc:.3f}")
    print(f"  aptitude (p90)  mean  {float(np.mean(result.aptitude)):.3f}")
    print(f"  scatter (p90-p10) mean {float(np.mean(result.scatter)):.3f}")
    print(f"  items with any scatter {unsteady}/{result.n_items}")
    for target in (0.8, 0.9):
        try:
            k = repeats_for_reliability(result.icc, target)
            print(f"  repeats for r={target}   {k}")
        except ValueError as error:
            print(f"  repeats for r={target}   n/a ({error})")


def report_bands(done: dict[tuple[str, int], dict[str, object]]) -> None:
    """Firing per length band, with intervals that resample triples.

    **The per-band table is the point of version 3 and the pooled figure above it
    cannot substitute.** Everything this repository has published was measured on
    turns of 25 words or fewer. If accuracy holds from ``s`` to ``xl``, the six
    points of room above a word-count ruler were real and five null results
    stand; if it falls, those nulls were an artefact of the band. One number over
    all four bands is consistent with both.

    The intervals cluster on ``triple`` because three items built from one body
    are one authored artefact seen three times. The item-level width is printed
    beside the clustered one rather than described, so a reader can see what the
    wrong unit would have claimed.

    Printed rather than raised when the records cannot support it: a version 2
    checkpoint has no bands, and a run that made every call should not lose its
    report to a format error at the end -- which has happened here, after 365
    calls.
    """
    rows = list(done.values())
    print(f"\n{'=' * 60}\nPER BAND -- across every repeat\n{'=' * 60}")
    try:
        # Item-weighted, and reported rather than raised. Row weighting puts a
        # band collected at three repeats ahead of its neighbours at two, which
        # is the routine state of a resumed `--band` run and biases exactly the
        # short-against-long comparison this table exists to make. Raising on a
        # half-collected band would cost the other three bands' rows for no
        # correctness at all, and `collect` iterates the positives before the
        # negatives so an interrupted run leaves precisely that shape.
        bands = summarise_by_band(rows, weight="item", on_unscoreable="report")
    except ArmError as error:
        print(f"  not available: {error}")
        return
    for line in format_bands(bands):
        print(line)
    report_long_against_short(rows)

    print("\n  Clustered on `triple`; the item-level width is the one to distrust.")
    subsets: tuple[tuple[str, list[dict[str, object]]], ...] = (
        ("accuracy", rows),
        ("recall (positives)", [row for row in rows if row["should_fire"]]),
        ("specificity (negatives)", [row for row in rows if not row["should_fire"]]),
    )
    for name, subset in subsets:
        try:
            clustered = bootstrap_rate(subset, seed=0)
            per_item = bootstrap_rate(subset, cluster_on="case", seed=0)
        except ArmError as error:
            print(f"  {name:24s} not available -- {error}")
            continue
        for line in format_rate(name, clustered):
            print(line)
        print(
            f"  {'':24s} item-level bootstrap would have said {per_item.width:.3f} wide "
            f"against {clustered.width:.3f}"
        )


def report_long_against_short(rows: list[dict[str, object]]) -> None:
    """Q1 of the N6 pre-registration: does firing accuracy fall on the long bands?

    S+M against L+XL — 72 items in 24 triples against 48 in 16. Different items,
    different clusters, nothing pairing them, so neither ``compare`` nor
    ``cluster_bootstrap_diff`` applies: both need the treatment values in the
    same item order as the control. **And the interval cannot be recovered by
    subtracting the two per-group intervals printed above**, which is the
    obvious thing to do by eye and answers a different question.

    The registered band is ``accuracy(S+M) − accuracy(L+XL)`` between −0.05 and
    +0.10, so the short bands go in as the treatment and the long ones as the
    control, and the printed sign is the registered one.
    """
    short = [row for row in rows if row.get("band") in ("s", "m")]
    long = [row for row in rows if row.get("band") in ("l", "xl")]
    print("\n  Q1 -- the registered comparison. S+M against L+XL, unpaired.")
    if not short or not long:
        print("    not available: this run does not hold both halves of the corpus.")
        return
    try:
        difference = bootstrap_rate_difference(
            long, short, name_control="L+XL", name_treatment="S+M", seed=0
        )
    except ArmError as error:
        print(f"    not available -- {error}")
        return
    for line in format_difference(difference):
        print(line)
    print(
        f"    registered band [-0.050, +0.100]: "
        f"{'INSIDE' if difference.within(-0.05, 0.10) else 'OUTSIDE'}"
    )
    print(
        "    Nominal 95% here is nearer 93% at 16 and 24 clusters -- measured, not "
        "assumed; see tests/unit/test_group_estimators.py."
    )


def report_routing_by_procedure(
    done: dict[tuple[str, int], dict[str, object]], trigger_set: TriggerSet
) -> None:
    """Q3: how does ``ledger`` route now that the corpus contains piles?

    Printed under **both** rules, always, because the two live in this
    repository and disagree: the ``covers`` stamp is equality against
    ``routes[0]`` and ``evaluate_routing`` accepts any member of ``routes``.
    Three v3 positives carry a second defensible route, so the rules differ on
    the verdicts *and* on the per-procedure denominators — 8 / 8 / 7 / 10 against
    8 / 10 / 8 / 10. Printing one of them would be picking a rule silently.
    """
    rows = list(done.values())
    routes = {case.id: case.routes for case in trigger_set.positives if case.routes}
    print(f"\n{'=' * 60}\nROUTING PER PROCEDURE -- Q3\n{'=' * 60}")
    for rule in ("first", "any"):
        try:
            result = routing_by_procedure(rows, rule=rule, routes=routes)  # type: ignore[arg-type]
        except ArmError as error:
            print(f"  rule {rule!r} not available -- {error}")
            continue
        for line in format_routing(result):
            print(line)
        worst = min(result.groups, key=lambda name: result.groups[name].over_items)
        print(f"  worst-routed under {rule!r}: {worst}")
        print("  Descriptive only. Ten items detects nothing; no p-value is offered.\n")


def report_negative_kinds(done: dict[tuple[str, int], dict[str, object]]) -> None:
    """Q4: do twinned negatives fire more than hand-written ones?

    The cross-version comparison the pre-registration wanted is refused by
    ``label_versions_comparable`` and is not attempted. What is available is the
    false-positive rate by ``kind`` inside version 3, and the registered band is
    that ``settled`` is the highest of the seven.

    ``summarise`` cannot produce this table: it refuses a subgroup holding one
    label, and a ``kind`` subgroup is all negatives by definition. Every row
    carries an interval because two of the seven kinds hold four items and one
    holds five, and a point estimate of 0.000 over five items is not evidence of
    a floor.
    """
    print(f"\n{'=' * 60}\nFALSE POSITIVES BY KIND OF NEGATIVE -- Q4\n{'=' * 60}")
    try:
        kinds = false_positive_rate_by_kind(list(done.values()))
    except ArmError as error:
        print(f"  not available: {error}")
        return
    for line in format_negative_kinds(kinds):
        print(line)
    highest = max(kinds, key=lambda name: kinds[name].over_items)
    others = [rate for name, rate in kinds.items() if name != highest]
    separated = all(kinds[highest].separated_from(other) for other in others)
    print(f"\n  highest: {highest} ({kinds[highest].n_items} item(s))")
    print(
        f"  its interval {'excludes' if separated else 'contains'} every other kind's point "
        "estimate."
    )
    if not separated:
        print("  So the ranking is a description of this run, not a difference between kinds.")


def report_calibration(done: dict[tuple[str, int], dict[str, object]]) -> None:
    """Is the elicited probability worth anything?

    Reported as the Murphy decomposition rather than as a single Brier score,
    because Brier alone cannot tell a calibrated forecaster from a hedging one.
    A model that answers 0.74 to everything is perfectly reliable and completely
    useless: reliability near zero, **resolution** near zero. Resolution is the
    number that says the forecast discriminates at all, and it is the one to read
    first.

    Skipped silently below ten forecasts. Every estimator here is biased at small
    n, and a reliability diagram over six points is a decoration.
    """
    import numpy as np

    from decision_evals.stats.calibration import (
        expected_calibration_error,
        murphy_decomposition,
        reliability_curve,
        smooth_calibration_error,
    )

    rows = [
        row
        for row in done.values()
        if isinstance(row.get("p_fire"), int | float) and row.get("fired") is not None
    ]
    print(f"\n{'=' * 60}\nCALIBRATION of the elicited p_fire\n{'=' * 60}")
    print(f"  forecasts returned    {len(rows)}/{len(done)}")
    if len(rows) < 10:
        print("  too few to estimate anything; every measure here is biased at small n")
        return

    forecasts = np.array([float(row["p_fire"]) for row in rows])  # type: ignore[arg-type]
    outcomes = np.array([1.0 if row["should_fire"] else 0.0 for row in rows])

    murphy = murphy_decomposition(forecasts, outcomes)
    print(f"  distinct values used  {murphy.n_groups}   <- 1 or 2 means it is not forecasting")
    print(f"  base rate             {murphy.base_rate:.3f}")
    print(f"  Brier                 {murphy.brier:.4f}   (lower better)")
    print(f"  reliability           {murphy.reliability:.4f}   (lower better)")
    print(f"  resolution            {murphy.resolution:.4f}   (HIGHER better -- read this one)")
    print(f"  uncertainty           {murphy.uncertainty:.4f}   (the question set, not the model)")
    print(
        f"  Brier skill score     {murphy.skill_score:+.4f}   (vs always answering the base rate)"
    )
    print(f"  smoothed cal. error   {smooth_calibration_error(forecasts, outcomes):.4f}")
    print(f"  binned ECE (10)       {expected_calibration_error(forecasts, outcomes):.4f}")

    print("\n  stated    n     observed")
    for calibration_bin in reliability_curve(forecasts, outcomes):
        print(
            f"  [{calibration_bin.lower:.1f},{calibration_bin.upper:.1f})"
            f"  {calibration_bin.count:4d}   {calibration_bin.observed_frequency:.3f}"
            f"   (mean stated {calibration_bin.mean_forecast:.3f})"
        )

    if murphy.skill_score <= 0:
        print("\n  *** No skill over always answering the base rate. The forecast is not")
        print("  *** carrying information about these labels.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--skill", default="decision-making")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--set",
        type=Path,
        help=(
            "corpus to run, defaulting to datasets/triggers/<skill>.yaml. A non-default "
            "set is a different answer key and gets its own checkpoint"
        ),
    )
    parser.add_argument(
        "--band",
        choices=BANDS,
        help="run one length stratum. Shares the full run's checkpoint; both resume",
    )
    parser.add_argument(
        "--confidence",
        action="store_true",
        help="also elicit p_fire and score it; writes a separate checkpoint",
    )
    parser.add_argument(
        "--in-situ",
        action="store_true",
        help=(
            "N9: send the description via --append-system-prompt instead of "
            "--system-prompt. Conversation length is unchanged -- still one turn. "
            "Own checkpoint; refused alongside --confidence, --entries/--arm four "
            "and a non-'full' --description, which vary the response contract "
            "rather than the venue"
        ),
    )
    parser.add_argument(
        "--arm",
        choices=("one", "four"),
        default="one",
        help="M4: one entry with a router, or the same four procedures as four tools",
    )
    parser.add_argument(
        "--entries",
        type=int,
        help="M5: spread the four procedures across N entries. --arm four is N=4",
    )
    parser.add_argument(
        "--pairing",
        help=(
            "M6: which procedures share an entry, at a count this fixes. "
            "Groups separated by commas, names within a group by '+', e.g. "
            "'ledger+cascade,fit+timing'. Must cover every procedure once"
        ),
    )
    parser.add_argument(
        "--description",
        choices=DESCRIPTION_VARIANTS,
        default="full",
        help="L5: which part of the shipped description to delete. Own checkpoint",
    )
    args = parser.parse_args()

    if args.arm == "four" and args.entries is not None:
        print("--arm four is --entries 4. Pass one of them, not both.")
        return 1
    # --pairing fixes the count by naming the groups, so --entries would either
    # agree redundantly or contradict it. Refusing both keeps the arm's identity
    # in one place.
    if args.pairing is not None and (args.entries is not None or args.arm == "four"):
        print("--pairing already fixes the entry count. Pass one of them, not both.")
        return 1
    grouping = [group.split("+") for group in args.pairing.split(",")] if args.pairing else None
    n_entries: int | None = 4 if args.arm == "four" else args.entries
    if grouping is not None:
        n_entries = len(grouping)

    # One manipulation per run. --description changes the trigger text;
    # --entries and --confidence change the response contract. Two at once
    # measures neither, and the run would look clean while doing it.
    if n_entries is not None and args.confidence:
        print("An entry-count arm and --confidence are two changes to the contract.")
        print("Run them separately or the run measures neither.")
        return 1
    if args.description != "full" and (n_entries is not None or args.confidence):
        print("--description varies the trigger text; --entries and --confidence vary")
        print("the response contract. Two manipulations in one run measure neither.")
        return 1
    # N9 moves one thing: where the description sits (--append-system-prompt vs
    # --system-prompt), holding the question, the schema and the description
    # text fixed at N6's `full` arm so the comparison is against a single
    # reference run rather than a moving target. --confidence and --entries/
    # --arm four change the response contract; --description changes the text
    # itself. Combining any of them with --in-situ would confound venue with a
    # second manipulation, the same reasoning the two checks above already use.
    if args.in_situ and (n_entries is not None or args.confidence or args.description != "full"):
        print("--in-situ moves only where the description sits. --confidence and")
        print("--entries/--arm four change the response contract; --description changes")
        print("the text. Two manipulations in one run measure neither -- run them separately.")
        return 1

    default_set = REPO_ROOT / TRIGGERS_DIR / f"{args.skill}.yaml"
    set_path = Path(args.set).resolve() if args.set else default_set
    trigger_set = load_trigger_set(set_path)

    if args.band is not None:
        banded = tuple(case for case in trigger_set.cases if case.band == args.band)
        if not banded:
            # Nothing would crash. The run would finish, checkpoint cleanly and
            # report a rate over zero calls, which is the failure this
            # instrument keeps producing: a plausible number nothing could have
            # moved. Version 2 declares no bands at all, so this is the likely
            # way to reach it.
            print(f"{set_path} has no case in band {args.band!r}; there is nothing to run.")
            print("Version 2 declares no bands. Point --set at a banded corpus.")
            return 1
        # `replace` rather than reconstructing: the set's `version` is the label
        # revision stamped onto every record, and building a bare TriggerSet
        # would silently default it to 1 and make the run look like a pre-2026
        # one on paper.
        trigger_set = replace(trigger_set, cases=banded)

    document = parse_skill(REPO_ROOT / "skills" / args.skill / "SKILL.md")
    description = str(document.frontmatter["description"]).strip()
    # `metadata.version` at the moment this description was read -- stamped
    # onto every row `collect()` writes so `skill_versions_comparable`
    # (`trigger_arms.py`) can refuse a comparison spanning a revision bump
    # like 2026-08-19's 0.2.1 -> 0.3.0, which rewrote this same frontmatter
    # `description` (four procedures to six) under an unchanged `set_version`.
    _metadata = document.frontmatter.get("metadata")
    skill_version = (
        str(_metadata["version"])
        if isinstance(_metadata, dict) and "version" in _metadata
        else None
    )

    try:
        description = description_variant(description, args.description)
    except UnbundleError as error:
        print(f"cannot build the {args.description} description: {error}")
        return 1

    entry_names: dict[str, str] | None = None
    if n_entries is not None:
        try:
            entry_names = (
                entries_grouped(description, document.body, grouping)
                if grouping is not None
                else entries(description, document.body, n_entries)
            )
        except UnbundleError as error:
            print(f"cannot build a {n_entries}-entry arm: {error}")
            return 1
        description = four_arm_block(entry_names)
        print(f"{n_entries}-entry arm: {', '.join(entry_names)}")

    band_note = f" band {args.band}" if args.band else ""
    print(
        f"{args.skill}{band_note}: {len(trigger_set.positives)} positive, "
        f"{len(trigger_set.negatives)} negative"
    )
    print(f"set: {set_path.name} (label version {trigger_set.version})")
    print(f"description: {len(description)} chars, {args.repeats} repeat(s)\n")

    system = SYSTEM_CONFIDENCE if args.confidence else SYSTEM
    checkpoint = CHECKPOINT_CONFIDENCE if args.confidence else CHECKPOINT
    if n_entries is not None:
        system = SYSTEM_FOUR
        if grouping is not None:
            # Named after the arm, not after n: two M6 pairings share a count and
            # must never share a checkpoint.
            stem = "-".join("+".join(group) for group in grouping)
            checkpoint = CHECKPOINT.with_name(f"verdicts-pairing-{stem}.jsonl")
        else:
            checkpoint = (
                CHECKPOINT_FOUR
                if n_entries == 4
                else CHECKPOINT.with_name(f"verdicts-{n_entries}-entries.jsonl")
            )
    if args.description != "full":
        checkpoint = CHECKPOINT.with_name(f"verdicts-{args.description}.jsonl")
    if args.in_situ:
        # N9's venue, on its own file for the reason `CHECKPOINT_IN_SITU`'s own
        # comment gives: `--confidence` and `--arm four` earn a separate
        # checkpoint because they change the response contract, and `in_situ`
        # earns one because it changes the venue the same call is made from. A
        # shared path plus a resume would silently pool an appended-prompt
        # verdict with a substituted-prompt one under one case id. Mutually
        # exclusive with the three branches above by the refusal already run,
        # so this assignment cannot be overwritten by any of them.
        checkpoint = CHECKPOINT_IN_SITU
    if set_path != default_set:
        # A different corpus is a different answer key, so it cannot share a
        # checkpoint with any arm above. `load_done` resumes on (case id,
        # repeat) and nothing else: a case id present under one label in version
        # 2 and another in version 3 would be skipped as already collected, and
        # the run would finish clean carrying a verdict scored against a label
        # it never saw. That is the 2026-08-13 defect with a file path instead
        # of a YAML edit.
        #
        # The marker composes with the arm suffixes rather than replacing them,
        # because the arm and the corpus are two independent axes and a name
        # that drops either would collide.
        marker = set_path.parent.name if set_path.name == "index.yaml" else set_path.stem
        checkpoint = checkpoint.with_name(
            f"{checkpoint.stem}-{marker}-v{trigger_set.version}{checkpoint.suffix}"
        )
    # `--band` deliberately does not appear here. A band is a subset of the same
    # items under the same labels, so a band run and a later full run resume into
    # each other, which is what makes running the cheap bands first worth doing.
    print(f"checkpoint: {checkpoint.name}\n")
    try:
        done = collect(
            trigger_set,
            description,
            args.model,
            args.repeats,
            system=system,
            checkpoint=checkpoint,
            entry_names=entry_names,
            in_situ=args.in_situ,
            skill_version=skill_version,
        )
    except IsolationError as error:
        print(f"ISOLATION FAILURE, stopping: {error}")
        return 1

    if args.repeats > 1:
        report_stability(trigger_set, done, args.repeats)
    if args.confidence:
        report_calibration(done)

    # The parse-rate floor is decided over every repeat the run made, not
    # repeat 0 alone -- see `parse_rate_over_all_repeats` for why repeat 0 is
    # not a stand-in for the run and why "every call" is the denominator
    # rather than "every item with at least one parseable repeat". This check
    # runs before the repeat-0 report below is built, so a run that fails it
    # never reaches a report that could only ever describe half the calls.
    gate_unparseable, gate_total = parse_rate_over_all_repeats(trigger_set, done, args.repeats)
    gate_rate = (gate_total - gate_unparseable) / gate_total if gate_total else 0.0
    if gate_rate < 0.9:
        print(
            f"\n*** parse rate {gate_rate:.0%} over all {gate_total} call(s) across "
            f"{args.repeats} repeat(s), below the 90% floor."
        )
        print("*** This measured format compliance rather than firing. Stopping.")
        return 1

    # The single-run report below describes repeat 0, and is kept because
    # precision and recall are what the skill is judged on. With repeats > 1 the
    # stability block above is the one that says whether to believe it.
    verdicts: dict[str, bool] = {}
    routes: dict[str, str | None] = {}
    unparseable: list[str] = []
    for case in trigger_set.cases:
        row = done.get((case.id, 0))
        if row is None or row["fired"] is None:
            unparseable.append(case.id)
            continue
        verdicts[case.turn] = bool(row["fired"])
        routes[case.turn] = row["procedure"]  # type: ignore[assignment]

    scored = tuple(c for c in trigger_set.cases if c.turn in verdicts)

    # `replace`, not a fresh TriggerSet: reconstructing one from `skill` and
    # `cases` alone drops `version` back to its default of 1, which is the field
    # that decides whether two runs may be compared at all.
    subset = replace(trigger_set, cases=scored)
    report = evaluate(subset, lambda turn: verdicts[turn])
    routing = evaluate_routing(subset, lambda turn: routes[turn])

    # The header says which repeat, because it is repeat 0 only and that number
    # is not the arm's rate. On 2026-08-13 this block printed "false-positive
    # rate 0.000" for an arm whose rate across both repeats was 0.018 -- two
    # negatives fired in repeat 1 and the headline could not see them. A
    # plausible number with a silent denominator is this instrument's signature
    # failure, and it had one more place to hide.
    scope = "repeat 0 only" if args.repeats > 1 else "the single repeat"
    print(f"\n{'=' * 60}\nFIRING  (primary) -- {scope}\n{'=' * 60}")
    if args.repeats > 1:
        rows_all = list(done.values())
        # Item-weighted, and the observed repeat count rather than `--repeats`.
        # A `--band` run shares a checkpoint with the full run on purpose, so a
        # band collected three times beside bands collected twice is the normal
        # state and not an edge case. Row weighting then hands the
        # over-collected band extra weight in the headline, and the header line
        # claimed "ALL 2 REPEATS" over a file that held three.
        collected = sorted({int(row["repeat"]) for row in rows_all})  # type: ignore[call-overload]
        every = summarise(rows_all, weight="item")
        by_record = summarise(rows_all)
        print(
            f"  ACROSS {len(collected)} REPEAT(S) {collected}, WEIGHTED BY ITEM: "
            f"precision {every.precision:.3f}  recall {every.recall:.3f}  "
            f"FPR {every.false_positive_rate:.3f}  accuracy {every.accuracy:.3f}"
        )
        print(
            f"  weighted by row instead:            precision {by_record.precision:.3f}  "
            f"recall {by_record.recall:.3f}  FPR {by_record.false_positive_rate:.3f}  "
            f"accuracy {by_record.accuracy:.3f}"
        )
        if abs(every.accuracy - by_record.accuracy) > 5e-4:
            print(
                "  ^ the two differ, so the repeats are uneven and the row figure is "
                "weighted toward whichever items were collected most."
            )
        print(f"  {every.n_items} item(s) over {every.n_records} row(s)")
        print(f"  never fired: {', '.join(every.missed) or 'none'}")
        print("  ^ this is the arm's rate. The block below is one repeat of it.\n")
    print(f"  precision            {report.precision:.3f}")
    print(f"  recall               {report.recall:.3f}")
    print(f"  false-positive rate  {report.false_positive_rate:.3f}   <- the daily-use cost")
    print(
        f"  tp {report.true_positives}  fp {report.false_positives}  "
        f"tn {report.true_negatives}  fn {report.false_negatives}"
    )
    if report.missed:
        print(f"  missed: {', '.join(report.missed)}")

    report_bands(done)
    report_negative_kinds(done)
    if entry_names is None:
        # The per-procedure table grades against the four procedure names. An
        # M5-style arm offering `ledger-fit` cannot be scored that way and
        # reports `covers` below instead -- the same defect that graded 365
        # calls against names an arm never offered, one table over.
        report_routing_by_procedure(done, trigger_set)

    print(f"\n{'=' * 60}\nROUTING  (secondary -- the easier question)\n{'=' * 60}")
    if entry_names is not None and not routing_is_by_name(entry_names):
        # Exact-name accuracy here is guaranteed 0.000 and says nothing: this arm
        # offers entry names the labels cannot equal. Report ``covers`` instead.
        # Both denominators, because M5 registered `covers` naming the measure
        # and not what it divided by, and the two differ by 15pp. `landed` is
        # every labelled call, a non-answer counting as a miss -- the
        # denominator `evaluate_routing` uses for the arms that can be scored by
        # name, and therefore the one that is reported.
        landed = [row for row in done.values() if row["covers"] is not None]
        answered = [row for row in landed if row["fired"]]
        hits = sum(1 for row in landed if row["covers"])
        chance = 1 / len(entry_names)
        print(f"  NOT REPORTED as accuracy -- this arm offers {', '.join(entry_names)},")
        print("  which no label can equal. Exact-name accuracy would read 0.000")
        print("  whatever the model did. The outcome for this arm is `covers`.")
        print(
            f"\n  covers     {hits / len(landed):.3f} over {len(landed)} labelled call(s), "
            f"chance {chance:.3f}"
        )
        if answered:
            print(
                f"             {sum(1 for r in answered if r['covers']) / len(answered):.3f} "
                f"over the {len(answered)} that fired -- reported for completeness, "
                "not the registered denominator"
            )
        print("  Not comparable across n: chance moves with the number of entries.")
        print("  Not comparable across pairings either, which M6 measured: regrouping")
        print("  changes which confusions the entry boundaries forgive.")
    else:
        print(
            f"  accuracy   {routing.accuracy:.3f} over {routing.n_scored} labelled "
            f"({routing.unlabelled} excluded as open)"
        )
        for case_id, wanted, got in routing.confusions:
            print(f"    {case_id}: wanted {wanted}, got {got}")

    print(f"\nexcluded {len(unparseable)}: {', '.join(unparseable) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
