"""Tests for the Track N5 realism probe.

The probe is descriptive and cannot be checked against a truth it does not have,
so what these tests check instead is that it is *capable of saying different
things*, and that the things it says are not artefacts of how the sample was
drawn. Two instruments in this repository shipped clean runs, full checkpoints
and plausible zeros on 2026-08-12 — a parser whitelist that discarded every name
an arm could offer, and a routing report grading answers against names the arm
never offered. Neither crashed and neither could have returned anything else.

Two tests carry most of the weight:

* :func:`test_estimator_moves_across_stub_modes` drives the full sampling,
  parsing and reporting path with five different fake judges and requires five
  different reports.
* :func:`test_a_label_blind_judge_scores_zero_on_the_adjusted_gap` is the
  known-good case for the label contrast. A stub that responds only to the band
  cannot know the label, so any label gap it produces is composition. The raw
  gap fails that check and the band-adjusted one passes it, which is why both
  are printed and why only one of them is trustworthy.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from decision_evals.triggers import TriggerCase, TriggerSet


def _load() -> ModuleType:
    """Import ``scripts/realism_probe.py``, which is not part of the package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "realism_probe.py"
    spec = importlib.util.spec_from_file_location("realism_probe", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["realism_probe"] = module
    spec.loader.exec_module(module)
    return module


probe = _load()

CORPUS = (
    Path(__file__).resolve().parents[2] / "datasets" / "triggers" / "decision-making" / "index.yaml"
)


@pytest.fixture(scope="module")
def trigger_set() -> Any:
    from decision_evals.triggers import load_trigger_set

    return load_trigger_set(CORPUS)


def _case(
    case_id: str,
    *,
    fires: bool,
    triple: str,
    band: str = "s",
    domain: str = "career",
) -> TriggerCase:
    return TriggerCase(
        id=case_id,
        turn=f"turn {case_id}",
        should_fire=fires,
        why="",
        band=band,
        triple=triple,
        domain=domain,
        kind=None if fires else "lookup",
    )


def _triple_number(case: TriggerCase) -> int:
    return int("".join(char for char in str(case.triple) if char.isdigit()))


# --------------------------------------------------------------------------- #
# Sampling
# --------------------------------------------------------------------------- #
def test_sample_takes_exactly_one_item_per_triple(trigger_set: Any) -> None:
    picked = probe.sample(trigger_set)
    triples = [case.triple for case in picked]
    assert len(triples) == len(set(triples))
    assert set(triples) == {case.triple for case in trigger_set.cases}


def test_sample_is_forty_items_and_matches_the_track_budget(trigger_set: Any) -> None:
    assert len(probe.sample(trigger_set)) == 40


def test_sample_represents_both_labels(trigger_set: Any) -> None:
    """Negatives are two thirds of the corpus; a positives-only probe measures nothing."""
    picked = probe.sample(trigger_set)
    positives = [case for case in picked if case.should_fire]
    negatives = [case for case in picked if not case.should_fire]
    assert positives
    assert negatives
    assert abs(len(positives) - len(negatives)) <= 2


def test_sample_does_not_alias_the_label_with_triple_parity(trigger_set: Any) -> None:
    """The defect an adversarial review found before this ever ran.

    Alternating on the triple index alone put every positive on an odd triple and
    every negative on an even one. The corpus rotates domain with the triple
    index, so the label inherited the rotation.
    """
    picked = probe.sample(trigger_set)
    for fires in (True, False):
        parities = [_triple_number(case) % 2 for case in picked if case.should_fire is fires]
        odd = sum(parities)
        assert 0 < odd < len(parities), "the label is a function of triple parity"


def test_sample_balances_domain_across_the_labels(trigger_set: Any) -> None:
    picked = probe.sample(trigger_set)
    for domain in {case.domain for case in picked}:
        here = [case for case in picked if case.domain == domain]
        positives = sum(1 for case in here if case.should_fire)
        assert abs(positives - (len(here) - positives)) <= 2, f"{domain} is skewed by label"


def test_sample_covers_every_band(trigger_set: Any) -> None:
    picked = probe.sample(trigger_set)
    assert {case.band for case in picked} == {case.band for case in trigger_set.cases}


def test_sample_covers_both_negative_slots(trigger_set: Any) -> None:
    negatives = [c.id for c in probe.sample(trigger_set) if not c.should_fire]
    assert any(case_id.endswith("n1") for case_id in negatives)
    assert any(case_id.endswith("n2") for case_id in negatives)


def test_sample_is_deterministic(trigger_set: Any) -> None:
    first = [case.id for case in probe.sample(trigger_set)]
    second = [case.id for case in probe.sample(trigger_set)]
    assert first == second


def test_sample_refuses_a_set_without_triples() -> None:
    """A version 2 set has no clusters, and sampling one would give a bad interval."""
    unclustered = TriggerSet(
        skill="decision-making",
        cases=(TriggerCase(id="p01", turn="x", should_fire=True, why=""),),
    )
    with pytest.raises(ValueError, match="no `triple`"):
        probe.sample(unclustered)


def test_sample_refuses_a_triple_that_spans_two_bands() -> None:
    straddling = TriggerSet(
        skill="decision-making",
        cases=(
            _case("a", fires=True, triple="t1", band="s"),
            _case("b", fires=False, triple="t1", band="xl"),
        ),
    )
    with pytest.raises(ValueError, match="spans bands"):
        probe.sample(straddling)


def test_triples_sort_naturally_rather_than_lexicographically() -> None:
    """`s2` before `s10`. The label alternates along this order."""
    assert probe._natural_key("s2") < probe._natural_key("s10")
    assert probe._natural_key("s01") < probe._natural_key("s02")


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"verdict": "real", "confidence": 0.8, "cue": "typos"}', ("real", 0.8, "typos")),
        ('{"verdict": "COMPOSED", "confidence": 0.5, "cue": "x"}', ("composed", 0.5, "x")),
        # The older field name still reads, so a checkpoint from an earlier
        # prompt does not silently lose its cues.
        ('{"verdict": "real", "confidence": 0.5, "tell": "y"}', ("real", 0.5, "y")),
        (
            'Sure!\n{"verdict": "real", "confidence": 0.2, "cue": "a"}\nHope that helps.',
            ("real", 0.2, "a"),
        ),
        ('{"verdict": "real"}', ("real", None, None)),
        ('{"verdict": "real", "confidence": 4}', ("real", None, None)),
        ('{"verdict": "real", "confidence": "high"}', ("real", None, None)),
        # `bool` is a subclass of `int`; admitting it would average a maximally
        # confident judgement the model never made into the reported mean.
        ('{"verdict": "real", "confidence": true}', ("real", None, None)),
        # A chatty judge whose prose also contains braces. The outermost-braces
        # slice parses as nothing here, so the flat-object scan is what saves it.
        (
            '{"verdict": "composed", "confidence": 0.6, "cue": "tidy"} -- '
            "I say that because {the phrasing} is very even.",
            ("composed", 0.6, "tidy"),
        ),
        (
            'Thinking about {the opening} first.\n{"verdict": "real", "confidence": 0.3, '
            '"cue": "abrupt"}',
            ("real", 0.3, "abrupt"),
        ),
    ],
)
def test_parse_reads_a_verdict(text: str, expected: tuple[Any, ...]) -> None:
    assert probe.parse(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "no json here at all",
        "{not json}",
        '{"verdict": "probably real", "confidence": 0.9}',
        '{"verdict": true}',
        '{"confidence": 0.9}',
        "[1, 2, 3]",
    ],
)
def test_parse_returns_a_missing_measurement_rather_than_a_verdict(text: str) -> None:
    """An unreadable reply must not become a `real`, and must not become a `composed`."""
    assert probe.parse(text) == (None, None, None)


# --------------------------------------------------------------------------- #
# The estimator can move. This is the test the run is not believed without.
# --------------------------------------------------------------------------- #
def _run(tmp_path: Path, mode: str, cases: tuple[TriggerCase, ...]) -> Any:
    done = probe.collect(
        cases,
        "stub-model",
        probe.SYSTEM,
        checkpoint=tmp_path / f"{mode}.jsonl",
        responder=probe.stub_responder(mode),
    )
    return probe.ProbeOutcome(rows=tuple(done.values()))


def test_estimator_moves_across_stub_modes(tmp_path: Path, trigger_set: Any) -> None:
    """Five fake judges, five different reports."""
    cases = probe.sample(trigger_set)

    all_real = _run(tmp_path, "real", cases)
    all_composed = _run(tmp_path, "composed", cases)
    mixed = _run(tmp_path, "mixed", cases)
    band = _run(tmp_path, "band", cases)
    broken = _run(tmp_path, "unparseable", cases)

    assert all_real.overall.rate == 0.0
    assert all_composed.overall.rate == 1.0
    assert 0.0 < mixed.overall.rate < 1.0
    assert 0.0 < band.overall.rate < 1.0

    rates = {all_real.overall.rate, all_composed.overall.rate, mixed.overall.rate}
    assert len(rates) == 3

    # A format failure lands in its own column instead of being scored.
    assert broken.unparseable == len(cases)
    assert broken.overall.scored == 0
    assert broken.corpus_weighted is None


def test_a_label_blind_judge_scores_zero_on_the_adjusted_gap(
    tmp_path: Path, trigger_set: Any
) -> None:
    """The known-good case for the label contrast.

    The `band` stub cannot see the label, so a non-zero label gap from it is
    composition and nothing else. The raw gap fails this; the band-adjusted gap
    passes it. That is the whole reason both are printed.
    """
    outcome = _run(tmp_path, "band", probe.sample(trigger_set))
    positive, negative = outcome.by_label()
    assert positive.rate != negative.rate, "the raw gap is not confound-free"
    assert outcome.band_adjusted_label_gap() == pytest.approx(0.0)


def test_the_adjusted_gap_still_moves_when_the_label_really_matters(tmp_path: Path) -> None:
    """Zero on a label-blind judge is only useful if it is not always zero."""
    cases = tuple(
        _case(f"c{i}", fires=i % 2 == 0, triple=f"t{i}", band="s", domain=f"d{i % 3}")
        for i in range(12)
    )

    def label_driven(case: TriggerCase, model: str, system: str) -> str:
        verdict = "composed" if case.should_fire else "real"
        return json.dumps({"verdict": verdict, "confidence": 0.9, "cue": "stub"})

    done = probe.collect(cases, "m", "s", checkpoint=tmp_path / "c.jsonl", responder=label_driven)
    outcome = probe.ProbeOutcome(rows=tuple(done.values()))
    assert outcome.band_adjusted_label_gap() == pytest.approx(1.0)


def test_nothing_scored_is_distinct_from_every_reply_agreeing(
    tmp_path: Path, trigger_set: Any
) -> None:
    """The message used to say "every scored reply agreed" when none had been."""
    cases = probe.sample(trigger_set)
    broken = _run(tmp_path, "unparseable", cases)
    assert broken.nothing_scored
    assert not broken.single_verdict

    uniform = _run(tmp_path, "real", cases)
    assert uniform.single_verdict
    assert not uniform.nothing_scored

    varied = _run(tmp_path, "mixed", cases)
    assert not varied.single_verdict
    assert not varied.nothing_scored


def test_unknown_stub_mode_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown stub mode"):
        probe.stub_responder("plausible")


# --------------------------------------------------------------------------- #
# Checkpointing
# --------------------------------------------------------------------------- #
def test_collect_resumes_without_repeating_a_call(tmp_path: Path) -> None:
    cases = (_case("a", fires=True, triple="t1"), _case("b", fires=False, triple="t2"))
    checkpoint = tmp_path / "c.jsonl"
    calls: list[str] = []

    def counting(case: TriggerCase, model: str, system: str) -> str:
        calls.append(case.id)
        return json.dumps({"verdict": "real", "confidence": 0.5, "cue": "t"})

    probe.collect(cases, "m", "s", checkpoint=checkpoint, responder=counting)
    assert calls == ["a", "b"]
    probe.collect(cases, "m", "s", checkpoint=checkpoint, responder=counting)
    assert calls == ["a", "b"], "a resumed run re-made a call it had already made"


def test_a_failed_call_is_recorded_and_retried_rather_than_frozen(tmp_path: Path) -> None:
    """One bad quota window used to poison every remaining case permanently."""
    from decision_evals.providers.claude_code import CliError

    cases = (_case("a", fires=True, triple="t1"),)
    checkpoint = tmp_path / "c.jsonl"
    attempts: list[str] = []

    def flaky(case: TriggerCase, model: str, system: str) -> str:
        attempts.append(case.id)
        if len(attempts) == 1:
            raise CliError("credential expired")
        return json.dumps({"verdict": "real", "confidence": 0.5, "cue": "t"})

    probe.collect(cases, "m", "s", checkpoint=checkpoint, responder=flaky)
    rows = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["error"] == "credential expired"
    assert probe.load_done(checkpoint) == {}, "an errored row must not count as done"

    probe.collect(cases, "m", "s", checkpoint=checkpoint, responder=flaky)
    assert attempts == ["a", "a"]
    assert probe.load_done(checkpoint)["a"]["verdict"] == "real"


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        ("model", {"model": "opus"}),
        ("set_version", {"set_version": 4}),
        ("corpus", {"corpus": "elsewhere.yaml"}),
    ],
)
def test_a_resumed_run_may_not_change_a_stamped_parameter(
    tmp_path: Path, field: str, kwargs: dict[str, Any]
) -> None:
    """The N8 defect: a parameter that changes every number and is only remembered."""
    checkpoint = tmp_path / "c.jsonl"
    base: dict[str, Any] = {
        "model": "haiku",
        "set_version": 3,
        "corpus": "here.yaml",
    }
    first = dict(base)
    probe.collect(
        (_case("a", fires=True, triple="t1"),),
        first.pop("model"),
        probe.SYSTEM,
        checkpoint=checkpoint,
        responder=probe.stub_responder("real"),
        **first,
    )
    second = {**base, **kwargs}
    with pytest.raises(probe.CheckpointMixError, match=field):
        probe.collect(
            (_case("b", fires=False, triple="t2"),),
            second.pop("model"),
            probe.SYSTEM,
            checkpoint=checkpoint,
            responder=probe.stub_responder("real"),
            **second,
        )


def test_a_resumed_run_may_not_change_the_prompt(tmp_path: Path) -> None:
    checkpoint = tmp_path / "c.jsonl"
    probe.collect(
        (_case("a", fires=True, triple="t1"),),
        "m",
        probe.SYSTEM,
        checkpoint=checkpoint,
        responder=probe.stub_responder("real"),
    )
    with pytest.raises(probe.CheckpointMixError, match="prompt_sha"):
        probe.collect(
            (_case("b", fires=False, triple="t2"),),
            "m",
            probe.SYSTEM + "\n\nAlso mention typography.",
            checkpoint=checkpoint,
            responder=probe.stub_responder("real"),
        )


def test_a_dry_run_may_not_share_a_checkpoint_with_a_real_run(tmp_path: Path) -> None:
    """A stub verdict and a model verdict are indistinguishable once written."""
    checkpoint = tmp_path / "c.jsonl"
    cases = (_case("a", fires=True, triple="t1"),)
    probe.collect(cases, "m", "s", checkpoint=checkpoint, responder=probe.stub_responder("real"))

    # `responder=None` is the real-model path. The refusal has to happen before
    # any call is made, which is why this test can run it with no model behind it.
    with pytest.raises(probe.CheckpointMixError, match="dry_run"):
        probe.collect(
            (_case("b", fires=False, triple="t2"),),
            "m",
            "s",
            checkpoint=checkpoint,
            responder=None,
        )


def test_prompt_sha_changes_with_the_prompt() -> None:
    assert probe.prompt_sha("a") != probe.prompt_sha("b")
    assert probe.prompt_sha(probe.SYSTEM) == probe.prompt_sha(probe.SYSTEM)


# --------------------------------------------------------------------------- #
# Rates and intervals
# --------------------------------------------------------------------------- #
def test_wilson_stays_inside_the_unit_interval_at_the_extremes() -> None:
    low, high = probe.wilson(0, 40)
    assert low == 0.0
    assert 0.0 < high < 1.0
    low, high = probe.wilson(40, 40)
    assert high == 1.0
    assert 0.0 < low < 1.0


def test_wilson_narrows_as_n_grows() -> None:
    small = probe.wilson(5, 10)
    large = probe.wilson(500, 1000)
    assert (large[1] - large[0]) < (small[1] - small[0])


def test_wilson_on_no_observations_is_uninformative_rather_than_zero() -> None:
    assert probe.wilson(0, 0) == (0.0, 1.0)


def test_empty_slice_prints_a_dash_rather_than_a_rate() -> None:
    assert "--" in probe.Rate(label="x", composed=0, scored=0).line()
    assert "0.000" in probe.Rate(label="x", composed=0, scored=4).line()


def test_corpus_weighting_uses_the_one_to_two_ratio() -> None:
    rows = tuple(
        {"verdict": "composed" if i < 2 else "real", "label": True, "band": "s"} for i in range(4)
    ) + tuple({"verdict": "real", "label": False, "band": "s"} for _ in range(4))
    outcome = probe.ProbeOutcome(rows=rows)
    assert outcome.overall.rate == pytest.approx(0.25)
    # positives 0.5, negatives 0.0 -> 0.5/3
    assert outcome.corpus_weighted == pytest.approx(0.5 / 3.0)


def test_losses_are_reported_for_a_stratum_that_scored_nothing() -> None:
    """`by()` iterates scored rows, so a wiped-out band would print no line at all."""
    rows: tuple[dict[str, object], ...] = (
        {"verdict": "real", "band": "s", "label": True},
        {"verdict": None, "band": "xl", "label": True},
        {"verdict": None, "band": "xl", "label": False},
    )
    outcome = probe.ProbeOutcome(rows=rows)
    assert [row.label for row in outcome.by("band")] == ["s"]
    assert {band: lost for band, lost, _ in outcome.losses("band")} == {"s": 0, "xl": 2}


def test_typography_counts_marks_per_band() -> None:
    cases = (
        _case("a", fires=True, triple="t1", band="s"),
        TriggerCase(
            id="b",
            turn="a sentence — with a dash",
            should_fire=False,
            why="",
            band="xl",
            triple="t2",
        ),
    )
    rows = {row[0]: row[1] for row in probe.typography(cases)}
    assert rows["s"] == "0/1"
    assert rows["xl"] == "1/1"


def test_the_corpus_aliases_dashes_with_the_long_bands(trigger_set: Any) -> None:
    """Recorded as a test because it is the most likely confound in the real run.

    If this ever stops being true the report's typography column becomes less
    load-bearing, which is worth knowing at that moment rather than later.
    """
    rows = {row[0]: row[1] for row in probe.typography(probe.sample(trigger_set))}
    assert rows["s"].startswith("0/")
    assert rows["m"].startswith("0/")
    for band in ("l", "xl"):
        count, total = rows[band].split("/")
        assert count == total, f"band {band} no longer carries a dash in every item"


# --------------------------------------------------------------------------- #
# The human audit sample
# --------------------------------------------------------------------------- #
def test_audit_sample_is_twelve_items_stratified_by_band(trigger_set: Any) -> None:
    picked = probe.audit_sample(probe.sample(trigger_set))
    assert len(picked) == probe.AUDIT_ITEMS
    bands = [case.band for case in picked]
    assert {bands.count(band) for band in set(bands)} == {3}


def test_audit_sample_holds_the_corpus_label_ratio(trigger_set: Any) -> None:
    picked = probe.audit_sample(probe.sample(trigger_set))
    positives = sum(1 for case in picked if case.should_fire)
    assert (positives, len(picked) - positives) == (4, 8)


def test_audit_sample_is_drawn_from_the_probe_sample(trigger_set: Any) -> None:
    """The overlap is the only anchor the machine probe's base rate has."""
    probed = probe.sample(trigger_set)
    picked = probe.audit_sample(probed)
    assert {case.id for case in picked} <= {case.id for case in probed}


def test_audit_sample_uses_distinct_triples(trigger_set: Any) -> None:
    picked = probe.audit_sample(probe.sample(trigger_set))
    assert len({case.triple for case in picked}) == len(picked)


def test_audit_sample_refuses_a_shape_it_cannot_honour() -> None:
    """It used to emit zero positives at five bands and keep claiming a 1:2 split."""
    five_bands = tuple(
        _case(f"c{i}", fires=i % 3 == 0, triple=f"t{i}", band=f"b{i % 5}") for i in range(15)
    )
    with pytest.raises(ValueError, match="does not divide"):
        probe.audit_sample(five_bands)


def test_audit_order_does_not_put_the_positives_first(trigger_set: Any) -> None:
    """The ordering was the leak: positives were items 1, 4, 7 and 10."""
    picked = probe.audit_sample(probe.sample(trigger_set))
    positions = [index for index, case in enumerate(probe.audit_order(picked)) if case.should_fire]
    assert positions != [0, 3, 6, 9]
    assert positions != sorted(range(len(positions)))


def test_audit_order_is_deterministic(trigger_set: Any) -> None:
    picked = probe.audit_sample(probe.sample(trigger_set))
    assert [c.id for c in probe.audit_order(picked)] == [c.id for c in probe.audit_order(picked)]


def test_audit_sheet_does_not_leak_the_label(trigger_set: Any) -> None:
    picked = probe.audit_sample(probe.sample(trigger_set))
    sheet, key = probe.render_audit(picked, set_version=3)
    for case in picked:
        assert case.id not in sheet, "the case id encodes the label"
        assert case.turn in sheet
    for band in ("band s", "band m", "band l", "band xl"):
        assert band not in sheet.lower()
    loaded = json.loads(key)
    assert sorted(loaded) == [f"A{i:02d}" for i in range(1, probe.AUDIT_ITEMS + 1)]
    assert {entry["case"] for entry in loaded.values()} == {case.id for case in picked}
    assert all(entry["set_version"] == 3 for entry in loaded.values())


# --------------------------------------------------------------------------- #
# End to end, zero model calls
# --------------------------------------------------------------------------- #
def test_dry_run_completes_the_whole_path(capsys: pytest.CaptureFixture[str]) -> None:
    assert probe.main(["--dry-run", "--stub", "mixed"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "0 model calls" in out
    assert "composed rate" in out
    assert "the measure varied across items" in out


def test_dry_run_says_plainly_that_it_is_not_a_gate(capsys: pytest.CaptureFixture[str]) -> None:
    probe.main(["--dry-run", "--stub", "mixed"])
    out = capsys.readouterr().out
    assert "No threshold here retires the corpus" in out


def test_the_report_states_its_own_run_parameters(capsys: pytest.CaptureFixture[str]) -> None:
    probe.main(["--dry-run", "--stub", "mixed"])
    out = capsys.readouterr().out
    for field in ("corpus", "set_version", "model", "prompt_sha", "dry_run"):
        assert field in out
    assert "index.yaml" in out


def test_the_report_shows_the_typography_alias(capsys: pytest.CaptureFixture[str]) -> None:
    probe.main(["--dry-run", "--stub", "band"])
    out = capsys.readouterr().out
    assert "typography by band" in out
    assert "em/en dash" in out


def test_an_alternative_prompt_can_be_supplied(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The default prompt has biases it cannot measure on itself."""
    other = tmp_path / "system.txt"
    other.write_text('Answer {"verdict": "real"} always.', encoding="utf-8")
    assert probe.main(["--dry-run", "--stub", "mixed", "--system", str(other)]) == 0
    assert probe.prompt_sha(probe.SYSTEM)[:8] not in capsys.readouterr().out


def test_emit_audit_writes_both_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(probe, "AUDIT_SAMPLE", tmp_path / "sheet.md")
    monkeypatch.setattr(probe, "AUDIT_KEY", tmp_path / "key.json")
    assert probe.main(["--emit-audit", "--set", str(CORPUS)]) == 0
    assert (tmp_path / "sheet.md").exists()
    assert json.loads((tmp_path / "key.json").read_text(encoding="utf-8"))
    capsys.readouterr()


def test_emit_audit_honours_an_explicit_destination(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The default lands in a gitignored directory; a filled-in sheet is evidence."""
    sheet = tmp_path / "nested" / "sheet.md"
    key = tmp_path / "nested" / "key.json"
    assert (
        probe.main(
            [
                "--emit-audit",
                "--set",
                str(CORPUS),
                "--audit-out",
                str(sheet),
                "--audit-key-out",
                str(key),
            ]
        )
        == 0
    )
    assert sheet.exists()
    assert len(json.loads(key.read_text(encoding="utf-8"))) == probe.AUDIT_ITEMS
    capsys.readouterr()


def test_report_only_with_no_records_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = probe.main(["--report-only", "--checkpoint", str(tmp_path / "missing.jsonl")])
    assert code == 1
    assert "no realism records" in capsys.readouterr().out


def test_the_prompt_never_mentions_the_label_or_the_skill() -> None:
    """The judge is asked a text question, not a decision question."""
    lowered = probe.SYSTEM.lower()
    for leak in ("decide", "decision", "skill", "positive", "negative", "label", "trigger"):
        assert leak not in lowered, f"the judge's prompt leaks {leak!r}"


def test_the_prompt_does_not_assert_the_item_came_from_a_collection() -> None:
    """An earlier opener stated the composed hypothesis before asking the question."""
    assert "collection" not in probe.SYSTEM.lower()
