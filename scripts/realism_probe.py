"""Track N5: does the trigger corpus read as text a person sent?

**This is descriptive. It is not a gate, and no number it prints retires the
corpus.** No human-written comparison set is in this repository yet. Track N4
now has a route to one — a public human-written corpus rather than a person, see
below — but nothing has been fetched against it, so a judge's realism verdict
here is still a statement about one model's prior over message text, not about
whether the corpus is valid. What it produces is a *rate with an interval*,
reported and left alone.

The temptation this docstring exists to refuse: writing a threshold. Standing
rule 2 says a falsifier must be run against a known-good case before it may fail
anything, and there is no known-good case here — nothing in this repository is
known to be a real message, so nothing can show that a judge calling text
"composed" is right. A gate without that check is how a corpus gets tuned to a
judge, which is worse than no realism measurement at all.

**Single-item judgement, not forced choice, and that is a downgrade taken on
purpose, for now.** A forced choice between a real message and an authored one
is the sharper instrument — it cancels the judge's base rate, which is the exact
quantity that is unmeasurable with a single item. It needs real messages to pair
against, and Track N4 no longer says those cannot exist here: N4 is now routed
to a public human-written corpus rather than a person
(`notebook/2026-08-18-n4-the-licence-survey-and-what-it-could-not-verify.md`),
which makes the comparison set reachable without a person and supplies the
known-good case standing rule 2 demands — which item is actually human is a
fact, not a taste. That data has not been fetched, so the paired probe is not
implemented here. The available alternative today, pairing two *corpus* items
against each other, is an estimator that cannot answer the question asked: both
sides are model-authored, so it would sit at 0.5 by construction however
authored the whole set reads, and it would print a clean, plausible number
while doing it. That is the 2026-08-12 defect shape exactly.

**This deviates from the written plan and the deviation is recorded rather than
made quietly.** `docs/superpowers/plans/2026-08-13-trigger-corpus-v3.md` specifies
a mixed sample judged comparatively — "which turns look like a real message and
which look authored". That framing needs the two populations the plan assumes and
this repository does not have. The choice, and what would settle it, are in
`notebook/2026-08-13-n5-what-a-realism-probe-without-a-comparison-set-can-say.md`.

**The sample is one item per matched triple.** The corpus is 40 triples of three
turns each, sharing a byte-identical body in the long bands, so two items from
one triple are very nearly the same text and their verdicts are not two
observations. One per triple makes the 40 calls the track budgets fall out of the
corpus structure rather than being chosen. See :func:`sample` — including what it
costs, which is the whole matched-triple design.

**The judge is never told the label.** It is not told which turns the corpus
calls decisions, it is not told that the corpus is about decisions, and it is not
shown a skill. It is asked one question about the text.

Usage::

    python scripts/realism_probe.py --dry-run --stub mixed   # no model calls
    python scripts/realism_probe.py --model haiku            # 40 calls
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals" / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scipy.stats import norm  # noqa: E402

from decision_evals.providers.claude_code import (  # noqa: E402
    CliError,
    Conversation,
    IsolationError,
    isolated_cwd,
)
from decision_evals.triggers import TriggerCase, TriggerSet, load_trigger_set  # noqa: E402

#: The judge's whole context.
#:
#: Deliberately silent about decisions, about skills, and about what any turn is
#: labelled. It asks about provenance and nothing else, because a judge told the
#: corpus is a decision benchmark would be reading the turns for decisions.
#:
#: **It also does not say the item came from a collection.** An earlier draft
#: opened "you are helping check a collection of text", which tells the judge the
#: item belongs to a set somebody assembled -- that is the composed hypothesis,
#: asserted before the question is asked.
#:
#: The one debiasing sentence is about length, because length is the confound
#: this corpus was rebuilt to remove: the bands run from 25 words to 1,500, so a
#: judge with a quiet "long means written-up" prior would return a band effect
#: that is an artefact of the sampling frame. Beyond that the prompt offers
#: **no** theory of what authored text looks like: handing a judge a list of
#: cues and then reporting how often it finds them measures the list.
#:
#: Two known residual biases, neither of which this file can measure on its own:
#: ``real`` is named first and binary judgements anchor on the first option, and
#: asking for a cue on every reply is a mild instruction to find one. ``--system``
#: exists so that an ablation of this prompt is a flag rather than an edit.
SYSTEM = (
    "Below is one message. Judge one thing about it: does it read like a message "
    "a real person actually sent to someone, or like text composed as an example "
    "-- written to illustrate something, or for a tutorial, a dataset, or a "
    "test?\n\n"
    "Judge the writing, not the subject matter. Length is not the question: real "
    "messages are sometimes one line and sometimes very long.\n\n"
    "Answer with a single line of JSON and nothing else:\n"
    '{"verdict": "real"|"composed", "confidence": 0.0-1.0, '
    '"cue": "<the single strongest cue for your answer, one short phrase>"}'
)

VERDICTS = ("real", "composed")

CHECKPOINT = REPO_ROOT / "results" / "triggers" / "realism.jsonl"

#: Conventional two-sided level for the reported interval. Named rather than
#: buried in a 1.96: the interval is the output here, so the thing that sets its
#: width is a parameter of the report.
ALPHA = 0.05

#: Run parameters that change every number and are invisible once a checkpoint is
#: read back. Each is written into every row and each is refused if a resumed run
#: disagrees with the rows already there.
#:
#: This is the N8 defect and the label-versioning defect, which are the same
#: defect: a parameter recoverable only from somebody remembering what they
#: typed. `run_triggers.py` already learned it for `model` and `set_version`;
#: writing this file without them would have been the fifth instance.
STAMPED = ("model", "set_version", "prompt_sha", "corpus", "dry_run")

#: Typographic marks a phone keyboard does not produce. Reported per band beside
#: the verdict rates and **not** removed from the turns.
#:
#: The reason is a specific alias found by adversarial review before this run was
#: made: em and en dashes appear in every L and XL item of the sample and in none
#: of the S and M items. A judge keying on typography alone would therefore print
#: a perfect, clean band effect and it would be about punctuation. Printing the
#: prevalence beside the rates does not fix that, and is not meant to -- it makes
#: it visible, so "the long bands read as composed" cannot be written without
#: somebody having seen the column that also separates those bands perfectly.
#:
#: Written as escapes rather than as the characters themselves, so that this
#: table is not itself a source of the marks it counts.
TYPOGRAPHY: dict[str, str] = {
    "em/en dash": "[\u2013\u2014]",
    "curly quote": "[\u2018\u2019\u201c\u201d]",
    "ellipsis char": "\u2026",
}


# --------------------------------------------------------------------------- #
# Sampling
# --------------------------------------------------------------------------- #
def _natural_key(name: str) -> tuple[str, int, str]:
    """Sort ``s2`` before ``s10``.

    Lexicographic ordering is load-bearing here — the label alternates along it —
    so an unpadded id would silently scramble the assignment rather than fail.
    """
    match = re.match(r"^([^\d]*)(\d*)(.*)$", name)
    if not match:  # pragma: no cover - the pattern matches every string
        return name, 0, ""
    head, digits, tail = match.groups()
    return head, int(digits) if digits else -1, tail


def sample(trigger_set: TriggerSet) -> tuple[TriggerCase, ...]:
    """One item per matched triple, stratified by band and by domain.

    Three properties, each of which is the design rather than a convenience:

    * **One item per triple.** The triple is the resampling cluster — in the L
      and XL bands its three turns share a byte-identical body and differ only in
      the closing ask, so a judge shown two of them is being shown one text
      twice.
    * **Both labels appear.** Negatives are two thirds of the corpus, and a probe
      that only ever saw positives would have measured nothing about them. The
      alternation gives close to a 50/50 split rather than the corpus's 1:2,
      because balanced allocation minimises the wider of the two per-label
      standard errors; the corpus-weighted rate is recoverable by reweighting and
      is reported alongside.
    * **Deterministic.** No seed, no RNG. The sample is a function of the corpus
      alone and a re-run reproduces it exactly.

    **The alternation runs inside each domain, and that is a correction.** An
    earlier draft alternated on the triple index alone, which put every positive
    on an odd-numbered triple and every negative on an even one. The corpus
    rotates domain with the triple index, so parity inherited the rotation: the
    sample came out with six relationship positives against three, and a stub
    responding purely to *band* — exactly label-blind — still printed a six-point
    label gap. Alternating within each domain group removes that particular
    alias.

    **What it does not remove, and cannot.** With one item per triple, the label
    contrast is *between* clusters, so it is confounded with anything that varies
    across triples and is not balanced here — stakes, authoring order,
    typography. The matched-triple construction is the one design that would
    settle it, and this sample deliberately throws it away to buy breadth. So the
    ``by label`` row is the weakest number this script prints, it is printed with
    that caveat attached, and a within-triple design is what would replace it: 20
    triples × 2 items is the same 40 calls and answers the label question instead
    of the coverage question.

    Raises:
        ValueError: A case carries no ``triple``, or a triple spans two bands.
    """
    missing = [case.id for case in trigger_set.cases if not case.triple]
    if missing:
        raise ValueError(
            f"{len(missing)} case(s) carry no `triple` (first: {missing[0]!r}). The sample is "
            "one item per matched triple; without triples there is no cluster to sample from "
            "and the interval would be computed over correlated items."
        )

    by_triple: dict[str, list[TriggerCase]] = {}
    for case in trigger_set.cases:
        by_triple.setdefault(str(case.triple), []).append(case)

    for triple, cases in by_triple.items():
        bands_here = {case.band for case in cases}
        if len(bands_here) > 1:
            raise ValueError(
                f"triple {triple!r} spans bands {sorted(map(str, bands_here))}. The sample is "
                "stratified by band, so a triple in two bands would be counted in one of them "
                "on whichever case happened to load first."
            )

    # band -> domain -> triples, so the label alternates within a domain rather
    # than along the triple index the corpus rotates domain with.
    strata: dict[str, dict[str, list[str]]] = {}
    for triple, cases in by_triple.items():
        band = str(cases[0].band)
        domain = str(cases[0].domain)
        strata.setdefault(band, {}).setdefault(domain, []).append(triple)

    picked: list[TriggerCase] = []
    for band in sorted(strata):
        # The starting parity alternates across domain groups too, so a band with
        # many small domain groups does not accumulate positives.
        for group_index, domain in enumerate(sorted(strata[band])):
            for offset, triple in enumerate(sorted(strata[band][domain], key=_natural_key)):
                cases = by_triple[triple]
                positives = sorted((c for c in cases if c.should_fire), key=lambda c: c.id)
                negatives = sorted((c for c in cases if not c.should_fire), key=lambda c: c.id)
                want_positive = (group_index + offset) % 2 == 0
                if want_positive and positives:
                    picked.append(positives[0])
                elif negatives:
                    picked.append(negatives[(group_index + offset) // 2 % len(negatives)])
                elif positives:  # pragma: no cover - a triple with no negative
                    picked.append(positives[0])
    return tuple(sorted(picked, key=lambda c: _natural_key(c.id)))


# --------------------------------------------------------------------------- #
# Asking
# --------------------------------------------------------------------------- #
Reply = tuple[str | None, float | None, str | None]

#: Any single brace-delimited object with no nesting. The judge is asked for one
#: flat object, so this is the shape the answer takes when it arrives wrapped in
#: prose. Same expression as ``triggers._JSON``, for the same reason.
_FLAT_OBJECT = re.compile(r"\{[^{}]*\}")


def parse(text: str) -> Reply:
    """``(verdict, confidence, cue)``, with ``None`` where it could not be read.

    An unreadable reply is a missing measurement, not a "composed". Scoring a
    format failure as a verdict would put the judge's formatting into the rate
    this run reports, which is the same defect shape as scoring an unparseable
    adjudication as disagreement.

    A verdict outside :data:`VERDICTS` is discarded for the same reason: the
    parser must not decide that "probably real" means ``real``, because that is a
    judgement entering a number without a trace.
    """
    for chunk in _json_candidates(text):
        try:
            loaded = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if not isinstance(loaded, dict):
            continue
        verdict = loaded.get("verdict")
        if not isinstance(verdict, str) or verdict.strip().lower() not in VERDICTS:
            continue
        cue = loaded.get("cue", loaded.get("tell"))
        return (
            verdict.strip().lower(),
            _confidence(loaded.get("confidence")),
            str(cue).strip() if isinstance(cue, str) else None,
        )
    return None, None, None


def _confidence(raw: object) -> float | None:
    """A stated confidence in ``[0, 1]``, or ``None``.

    ``bool`` is excluded explicitly because it is a subclass of ``int``:
    ``{"confidence": true}`` would otherwise arrive as ``1.0`` and be averaged
    into the reported mean as a maximally confident judgement the model never
    made.
    """
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        return None
    return float(raw) if 0.0 <= raw <= 1.0 else None


def _json_candidates(text: str) -> list[str]:
    """Every substring worth trying, widest first.

    The outermost-braces slice alone is not enough, and the failure is easy to
    reach: a reply reading ``{"verdict": "real", ...} -- I say that because
    {the phrasing}`` spans from the first ``{`` to the last ``}`` and parses as
    nothing. Every such reply would land in the unparseable column, and a judge
    is more likely to preface a 1,500-word item with prose than a 20-word one, so
    the losses would be correlated with the band — which is the axis being
    reported.

    Widening the parser is not the same as coercing it. Each candidate still has
    to be a JSON object carrying a verdict from :data:`VERDICTS`.
    """
    stripped = text.strip()
    candidates = [stripped]
    start, end = stripped.find("{"), stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    candidates.extend(_FLAT_OBJECT.findall(stripped))
    return candidates


def ask(case: TriggerCase, model: str, system: str) -> str:
    """One judge's raw reply about one turn, in an isolated conversation."""
    prompt = f"## Message\n\n{case.turn}"
    with (
        isolated_cwd("de-realism-") as cwd,
        Conversation(system_prompt=system, model=model, cwd=cwd) as chat,
    ):
        result = chat.send(prompt)
        chat.receipt.assert_isolated()
    return result.text


def stub_responder(mode: str) -> Callable[[TriggerCase, str, str], str]:
    """A fake judge, for the dry run. **Never used when calls are real.**

    Five modes, and the reason there are five is standing rule: an estimator that
    cannot return a different value is not a measurement. ``real`` and
    ``composed`` drive the rate to its two extremes, ``mixed`` puts it in
    between, ``unparseable`` proves a format failure lands in its own column
    rather than in a verdict, and ``band`` responds *only* to the band — a
    label-blind judge — so the report can be checked for a label gap it should
    not be able to produce.

    ``mixed`` is a hash of the case id, so it is deterministic and is not a coin
    flip that happens to look like a result.
    """
    modes = {"real", "composed", "mixed", "unparseable", "band"}
    if mode not in modes:
        raise ValueError(f"unknown stub mode {mode!r}; expected one of {sorted(modes)}")

    def respond(case: TriggerCase, model: str, system: str) -> str:
        if mode == "unparseable":
            return "I would rather describe this in prose than answer in JSON."
        if mode == "band":
            verdict = "composed" if str(case.band) in {"l", "xl"} else "real"
            confidence = 0.8
        elif mode == "mixed":
            digest = hashlib.sha256(case.id.encode("utf-8")).digest()
            verdict = "composed" if digest[0] % 5 < 2 else "real"
            confidence = round(0.50 + (digest[1] % 50) / 100.0, 2)
        else:
            verdict, confidence = mode, 0.9
        return json.dumps({"verdict": verdict, "confidence": confidence, "cue": f"stub/{mode}"})

    return respond


# --------------------------------------------------------------------------- #
# Checkpointing
# --------------------------------------------------------------------------- #
class CheckpointMixError(RuntimeError):
    """A resumed run would have pooled two different runs into one report.

    Nothing in a JSONL record distinguishes one run parameter from another once
    the file is read back — a stub verdict from a model verdict, a ``haiku``
    verdict from an ``opus`` one, a verdict made under one prompt from a verdict
    made under an edited one. That is the shape of the label-versioning defect
    and of N8, and the count on it in this repository is four for four. So the
    file is refused rather than appended to.
    """


def load_done(path: Path) -> dict[str, dict[str, object]]:
    """Rows already recorded, keyed by case.

    **A row carrying an ``error`` is not done.** A ``CliError`` — an expired
    credential, a prompt over the window — used to be written as a row and then
    skipped on resume, so one bad quota window produced 40 permanently poisoned
    cases that could only be repaired by hand and read in the report as a judge
    that would not format. The row is kept, because losing the evidence of the
    failure is worse, and it is retried.
    """
    if not path.exists():
        return {}
    done: dict[str, dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("error"):
                continue
            done[str(row["case"])] = row
    return done


def _check_stamps(checkpoint: Path, stamps: dict[str, object]) -> None:
    """Refuse a checkpoint whose rows were made under different run parameters."""
    if not checkpoint.exists():
        return
    for line in checkpoint.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for field in STAMPED:
            if field in row and row[field] != stamps[field]:
                raise CheckpointMixError(
                    f"{checkpoint} holds a row for {row['case']!r} with {field}="
                    f"{row[field]!r}; this run has {field}={stamps[field]!r}. Two runs made "
                    "under different parameters are indistinguishable once pooled into one "
                    "report. Use a different --checkpoint."
                )


def collect(
    cases: tuple[TriggerCase, ...],
    model: str,
    system: str,
    *,
    checkpoint: Path,
    responder: Callable[[TriggerCase, str, str], str] | None = None,
    set_version: int = 0,
    corpus: str = "",
) -> dict[str, dict[str, object]]:
    """Every sampled case once, checkpointing after each call.

    One judge per turn, not three. Adjudication needs a majority because it moves
    labels; this run moves nothing, so a second opinion would buy precision on a
    number that is descriptive anyway, at the cost of the sample covering a third
    as many items. Breadth over the corpus is the more useful spend.
    """
    dry_run = responder is not None
    respond = responder if responder is not None else ask
    stamps: dict[str, object] = {
        "model": model,
        "set_version": set_version,
        "prompt_sha": prompt_sha(system),
        "corpus": corpus,
        "dry_run": dry_run,
    }
    _check_stamps(checkpoint, stamps)
    done = load_done(checkpoint)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    with checkpoint.open("a", encoding="utf-8") as handle:
        for index, case in enumerate(cases, start=1):
            if case.id in done:
                continue
            error: str | None = None
            try:
                raw = respond(case, model, system)
            except IsolationError:
                raise
            except CliError as exc:
                raw, error = "", str(exc)
                print(f"  {case.id}: call failed, will retry on resume -- {exc}")
            verdict, confidence, cue = parse(raw)
            row: dict[str, object] = {
                "case": case.id,
                "verdict": verdict,
                "confidence": confidence,
                "cue": cue,
                "error": error,
                "label": case.should_fire,
                "band": case.band,
                "triple": case.triple,
                "domain": case.domain,
                "stakes": case.stakes,
                "ask": case.ask,
                "kind": case.kind,
                "words": len(case.turn.split()),
                "raw": raw,
                **stamps,
            }
            handle.write(json.dumps(row) + "\n")
            handle.flush()
            if error is None:
                done[case.id] = row
            if index % 10 == 0 or index == len(cases):
                print(f"  {index}/{len(cases)}", flush=True)
    return done


def prompt_sha(system: str) -> str:
    """Short hash of the judge's prompt, stamped into every row.

    The prompt is a run parameter like the model tier. An edit between two runs
    that share a checkpoint would change every verdict and leave nothing in the
    record saying so.
    """
    return hashlib.sha256(system.encode("utf-8")).hexdigest()[:12]


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def wilson(successes: int, n: int, alpha: float = ALPHA) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Wilson rather than Wald because the rate can land near 0 or 1 on 40 items and
    a Wald interval runs off the end of the scale there, printing a bound below
    zero as though it were a measurement.

    **What the interval covers, stated precisely, because the obvious reading is
    wrong.** It is *not* an item-sampling interval: all 40 triples in the corpus
    are in the sample, so the cluster-level sampling fraction is 1.0 and there is
    no population left to have sampled from. What it covers is the **judge**: one
    call per item, each in its own isolated conversation, so each verdict is one
    Bernoulli draw from that judge's propensity on that item, and the interval is
    for the mean of those propensities over these 40 items.

    Three things it therefore does not cover: the other 80 items of the corpus,
    any other model tier, and the author. A second tier is another 40 calls and
    is the way to see the middle one.
    """
    if n <= 0:
        return 0.0, 1.0
    z = float(norm.ppf(1.0 - alpha / 2.0))
    p = successes / n
    denominator = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


@dataclass(frozen=True)
class Rate:
    """A composed-rate over some slice, with its interval."""

    label: str
    composed: int
    scored: int

    @property
    def rate(self) -> float:
        return self.composed / self.scored if self.scored else 0.0

    @property
    def interval(self) -> tuple[float, float]:
        return wilson(self.composed, self.scored)

    def line(self) -> str:
        """The rate, or ``--`` where nothing was scored.

        An empty slice has no rate. Printing ``0.000`` for it would be a zero
        that reads as a measurement, which is the failure mode this repository
        has shipped twice — a clean run, a full checkpoint and a plausible zero
        that no possible response could have moved.
        """
        low, high = self.interval
        rate = "  --  " if not self.scored else f"{self.rate:.3f}"
        return (
            f"{self.label:12s} {self.composed:3d}/{self.scored:<3d} {rate}"
            f"   [{low:.3f}, {high:.3f}]"
        )


@dataclass(frozen=True)
class ProbeOutcome:
    """Everything the run can say, and nothing it cannot.

    There is no ``passes`` property and there is not going to be one. The rate is
    the output; what a reader does with it is a judgement this script has no
    standing to make.
    """

    rows: tuple[dict[str, object], ...]

    @property
    def scored(self) -> tuple[dict[str, object], ...]:
        return tuple(row for row in self.rows if row.get("verdict") in VERDICTS)

    @property
    def unparseable(self) -> int:
        return len(self.rows) - len(self.scored)

    @property
    def errored(self) -> int:
        return sum(1 for row in self.rows if row.get("error"))

    @property
    def overall(self) -> Rate:
        return self._rate("all", self.scored)

    @property
    def verdicts_seen(self) -> tuple[str, ...]:
        return tuple(sorted({str(row["verdict"]) for row in self.scored}))

    @property
    def nothing_scored(self) -> bool:
        """No reply could be read at all. Distinct from every reply agreeing."""
        return not self.scored

    @property
    def single_verdict(self) -> bool:
        """Every scored reply said the same thing.

        Not an error and not a kill — a corpus could genuinely read as uniformly
        one or the other. It is printed because a single-valued column is also
        what a broken parser looks like, and this repository has shipped two
        clean runs whose measure could not have returned anything else.
        """
        return len(self.verdicts_seen) == 1

    @property
    def corpus_weighted(self) -> float | None:
        """The composed rate reweighted to the corpus's own 1:2 label ratio.

        The sample is balanced by label and the corpus is not, so the unweighted
        overall rate is a rate over the sample and not over the corpus. Both are
        printed; neither is the headline, because they answer different questions
        and picking one silently is how a denominator goes unstated.

        It is a point estimate with no interval, and deliberately so: the two
        per-label subsamples are the between-cluster halves described in
        :func:`sample`, so an interval on this number would advertise a precision
        the design does not have.

        ``None`` when either label has nothing scored — there is no reweighting
        to do, and returning the unweighted rate under a weighted name would put
        a different denominator behind the same label.
        """
        positive = self._rate("positive", self._slice("label", True))
        negative = self._rate("negative", self._slice("label", False))
        if not positive.scored or not negative.scored:
            return None
        return positive.rate / 3.0 + negative.rate * 2.0 / 3.0

    def band_adjusted_label_gap(self) -> float | None:
        """Positive minus negative, computed *within* each band and then pooled.

        **The raw ``by label`` gap can be produced by a judge that never sees the
        label.** The bands have odd triple counts, so the sample cannot hold
        positives and negatives in equal proportion inside every band: L and XL
        supply 9 of the 21 positives and 7 of the 19 negatives. A stub responding
        only to the band — exactly label-blind — therefore prints a six-point
        label gap, and it is arithmetic rather than a finding.

        Taking the difference inside each band first removes that particular
        composition, and it is checkable rather than asserted: the ``band`` stub
        scores **0.000** here by construction, which is what makes this line
        worth printing and the raw one worth distrusting.

        Weighted by the number of scored items in each band. It does not adjust
        for anything except band, so the between-triple caveat in :func:`sample`
        still stands in full — stakes, authoring order and typography are all
        still in this number.

        ``None`` when no band has both labels scored.
        """
        total = 0.0
        weight = 0.0
        for band in sorted({str(row.get("band")) for row in self.scored}):
            rows = self._slice("band", band, as_text=True)
            positive = self._rate("p", tuple(r for r in rows if r.get("label") is True))
            negative = self._rate("n", tuple(r for r in rows if r.get("label") is False))
            if not positive.scored or not negative.scored:
                continue
            here = float(positive.scored + negative.scored)
            total += (positive.rate - negative.rate) * here
            weight += here
        return total / weight if weight else None

    def by(self, key: str) -> tuple[Rate, ...]:
        values = sorted({str(row.get(key)) for row in self.scored})
        return tuple(self._rate(value, self._slice(key, value, as_text=True)) for value in values)

    def by_label(self) -> tuple[Rate, ...]:
        return (
            self._rate("positive", self._slice("label", True)),
            self._rate("negative", self._slice("label", False)),
        )

    def losses(self, key: str) -> tuple[tuple[str, int, int], ...]:
        """Unparseable and errored counts per slice, over **all** rows.

        Reported because :meth:`by` iterates the scored rows only, so a stratum
        that lost every reply would simply not print a line — no zero, no dash,
        no row at all. A silently absent stratum is the least visible way for a
        measurement to go missing, and the loss is exactly the quantity most
        likely to correlate with the band.
        """
        values = sorted({str(row.get(key)) for row in self.rows})
        out: list[tuple[str, int, int]] = []
        for value in values:
            rows = [row for row in self.rows if str(row.get(key)) == value]
            lost = sum(1 for row in rows if row.get("verdict") not in VERDICTS)
            out.append((value, lost, len(rows)))
        return tuple(out)

    def mean_confidence(self, verdict: str) -> float | None:
        values = [
            float(row["confidence"])
            for row in self.scored
            if row["verdict"] == verdict and isinstance(row.get("confidence"), int | float)
        ]
        return sum(values) / len(values) if values else None

    def cues(self, top: int = 8) -> tuple[tuple[str, int], ...]:
        counter = Counter(
            str(row["cue"]).lower() for row in self.scored if isinstance(row.get("cue"), str)
        )
        return tuple(counter.most_common(top))

    def stamp(self, field: str) -> str:
        values = sorted({str(row.get(field)) for row in self.rows})
        return ", ".join(values) if values else "(none)"

    def _slice(
        self, key: str, value: object, *, as_text: bool = False
    ) -> tuple[dict[str, object], ...]:
        if as_text:
            return tuple(row for row in self.scored if str(row.get(key)) == value)
        return tuple(row for row in self.scored if row.get(key) == value)

    @staticmethod
    def _rate(label: str, rows: tuple[dict[str, object], ...]) -> Rate:
        return Rate(
            label=label,
            composed=sum(1 for row in rows if row["verdict"] == "composed"),
            scored=len(rows),
        )


def typography(cases: tuple[TriggerCase, ...], key: str = "band") -> tuple[tuple[str, ...], ...]:
    """Prevalence of each mark in :data:`TYPOGRAPHY`, per slice of ``key``.

    Printed beside the verdict rates, never subtracted from them. See
    :data:`TYPOGRAPHY` for why this column exists.
    """
    values = sorted({str(getattr(case, key)) for case in cases})
    rows: list[tuple[str, ...]] = []
    for value in values:
        here = [case for case in cases if str(getattr(case, key)) == value]
        counts = [
            f"{sum(1 for case in here if re.search(pattern, case.turn))}/{len(here)}"
            for pattern in TYPOGRAPHY.values()
        ]
        rows.append((value, *counts))
    return tuple(rows)


def report(outcome: ProbeOutcome, cases: tuple[TriggerCase, ...] = ()) -> None:
    print("\n=== realism probe (descriptive) ===")
    print("  No threshold here retires the corpus. There is no human-written")
    print("  comparison set, so this is a rate from one model's prior, not a")
    print("  measurement of whether the corpus is valid.\n")
    for field in ("corpus", "set_version", "model", "prompt_sha", "dry_run"):
        print(f"  {field:12s} {outcome.stamp(field)}")
    print(f"\n  records      {len(outcome.rows)}")
    print(f"  unparseable  {outcome.unparseable}   (of which call failures: {outcome.errored})")
    print(f"  verdicts     {', '.join(outcome.verdicts_seen) or '(none)'}")

    weighted = outcome.corpus_weighted
    print(f"\n  composed rate  {outcome.overall.line()}")
    print(
        "  corpus-weighted (1 positive : 2 negatives, point estimate)  "
        + ("-- (a label has nothing scored)" if weighted is None else f"{weighted:.3f}")
    )

    print("\n  by label -- the weakest row here: with one item per triple this is a")
    print("  BETWEEN-triple contrast, so it carries whatever else varies across")
    print("  triples. See sample().")
    for rate in outcome.by_label():
        print(f"    {rate.line()}")
    positive, negative = outcome.by_label()
    adjusted = outcome.band_adjusted_label_gap()
    print(f"    {'raw gap':12s} {positive.rate - negative.rate:+.3f}")
    print(
        f"    {'band-adj.':12s} "
        + ("--" if adjusted is None else f"{adjusted:+.3f}")
        + "   a label-blind judge scores +0.000 here and not on the raw gap"
    )

    for key, note in (
        ("band", ""),
        ("ask", "  (`embedded` is positives-only: the corpus has no embedded negative)"),
        ("stakes", ""),
        ("kind", "  (negatives only -- positives carry no `kind`)"),
    ):
        rates = [rate for rate in outcome.by(key) if rate.label != "None"]
        if rates:
            print(f"\n  by {key}:{note}")
            for rate in rates:
                print(f"    {rate.line()}")

    if cases:
        print("\n  typography by band, printed so a band effect cannot be read as prose:")
        print(f"    {'band':12s} " + "  ".join(f"{name:>13s}" for name in TYPOGRAPHY))
        for row in typography(cases):
            print(f"    {row[0]:12s} " + "  ".join(f"{cell:>13s}" for cell in row[1:]))

    print("\n  unreadable replies by band (a stratum that loses every reply prints no rate):")
    for value, lost, total in outcome.losses("band"):
        if value != "None":
            print(f"    {value:12s} {lost:3d}/{total}")

    print("\n  mean stated confidence:")
    for verdict in VERDICTS:
        mean = outcome.mean_confidence(verdict)
        print(f"    {verdict:12s} {'--' if mean is None else f'{mean:.3f}'}")

    if outcome.cues():
        print("\n  most frequent cues:")
        for cue, count in outcome.cues():
            print(f"    {count:3d}  {cue[:80]}")

    print(
        f"\n  intervals are unadjusted {int((1 - ALPHA) * 100)}% Wilson, one per row and many"
        "\n  rows, so expect some to exclude the overall rate by chance. Cells below"
        "\n  about n=10 are printed for completeness, not for reading."
    )
    if outcome.nothing_scored:
        print(
            "\n  NOTHING SCORED: no reply could be read. This is not a rate of zero and\n"
            "  the report above has no content. Check the call failures column first."
        )
    elif outcome.single_verdict:
        print(
            "\n  SINGLE VERDICT: every scored reply said the same thing. That may be true\n"
            "  of the corpus, and it is also what a broken parser looks like. Run the dry\n"
            "  run across all five stub modes before reading anything into it."
        )
    else:
        print("\n  the measure varied across items, so it could have come out otherwise")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _display(path: Path) -> str:
    """Repository-relative where possible, absolute otherwise."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default="haiku",
        help=(
            "Tier for the judge. Default matches scripts/adjudicate.py so the two "
            "passes over this corpus are made by the same tier. A chosen default, not a "
            "derived one: what would settle it is running both tiers, which is 80 calls."
        ),
    )
    parser.add_argument(
        "--set",
        default=str(REPO_ROOT / "datasets" / "triggers" / "decision-making" / "index.yaml"),
    )
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument(
        "--system",
        default=None,
        help=(
            "Path to a file holding an alternative judge prompt. The default prompt has "
            "two biases it cannot measure on itself -- `real` is named first, and a cue is "
            "asked for on every reply -- so an ablation arm is a flag rather than an edit. "
            "The prompt is hashed into every record either way."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Exercise sampling, parsing and reporting with a stub judge and zero model calls.",
    )
    parser.add_argument(
        "--stub",
        default="mixed",
        choices=["real", "composed", "mixed", "unparseable", "band"],
        help="Which fake judge the dry run uses. All five exist so the report can be shown "
        "to move; a stub that only ever produced one rate would prove nothing. `band` is "
        "label-blind, so any label gap it prints is a confound rather than a finding.",
    )
    args = parser.parse_args(argv)

    corpus_path = Path(args.set)
    trigger_set = load_trigger_set(corpus_path)
    cases = sample(trigger_set)
    system = Path(args.system).read_text(encoding="utf-8") if args.system else SYSTEM

    if args.checkpoint:
        checkpoint = Path(args.checkpoint)
    elif args.dry_run:
        checkpoint = Path(tempfile.mkdtemp(prefix="de-realism-dry-")) / "realism-dryrun.jsonl"
    else:
        checkpoint = CHECKPOINT

    if not args.report_only:
        responder = stub_responder(args.stub) if args.dry_run else None
        kind = f"DRY RUN (stub={args.stub}, 0 model calls)" if args.dry_run else f"{args.model}"
        print(f"realism probe over {len(cases)} of {len(trigger_set.cases)} items -- {kind}")
        print(f"  one item per matched triple, checkpointed at {checkpoint}")
        collect(
            cases,
            args.model,
            system,
            checkpoint=checkpoint,
            responder=responder,
            set_version=trigger_set.version,
            corpus=_display(corpus_path),
        )

    done = load_done(checkpoint)
    if not done:
        print("no realism records")
        return 1
    report(ProbeOutcome(rows=tuple(done.values())), cases)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
