"""The pinned GenAI attribute vocabulary, and node identity on a record.

The test that matters most is ``test_every_published_run_record_still_loads``:
every record already published under ``results/`` must survive the schema
change. A change that quietly orphans the runs the notebook cites is worse than
no change at all.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from decision_evals import telemetry
from decision_evals.runner import RunRecord, load_records
from decision_evals.telemetry import (
    AGENT_NAME,
    ARM,
    CONVERSATION_ID,
    EVALUATION_NAME,
    EVALUATION_SCORE,
    NODE_PARENT_ID,
    OP_CHAT,
    OP_INVOKE_AGENT,
    OPERATION_NAME,
    PROVIDER_ANTHROPIC,
    PROVIDER_NAME,
    RECORD_SCHEMA_VERSION,
    REQUEST_MODEL,
    RESPONSE_MODEL,
    SCHEMA_VERSION,
    TURN_INDEX,
    USAGE_INPUT_TOKENS,
    USAGE_OUTPUT_TOKENS,
    NodeIdentity,
    provenance,
    span_attributes,
    span_name,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _is_run_record_checkpoint(path: Path) -> bool:
    """Whether a JSONL file holds :class:`RunRecord` lines.

    ``results/probe/`` holds casefile-probe records, which are a different
    dataclass keyed on ``case_id`` and were never readable by ``load_records``.
    Selecting by first-line shape rather than by directory keeps this honest if
    either layout moves.
    """
    with path.open(encoding="utf-8") as handle:
        first = handle.readline()
    return bool(first.strip()) and "item_id" in json.loads(first)


#: Published checkpoints that are RunRecord JSONL, discovered rather than listed.
_RUN_RECORD_CHECKPOINTS = sorted(
    path for path in (REPO_ROOT / "results").rglob("*.jsonl") if _is_run_record_checkpoint(path)
)

#: The RunRecord checkpoints that are *committed*, so the guard below means the
#: same thing on a clean checkout as it does on a machine that has run the
#: experiments. Untracked local run data is still discovered and still
#: parametrised above; it just cannot be what makes the guard pass. Add a name
#: here when a run's records are published, not when they appear on disk.
_TRACKED_CHECKPOINTS = ("results/evidence-ledger/2026-08-10-baseline-corpus/off-arm.jsonl",)


class TestPinnedVocabulary:
    """The names are data, so the tests pin them as data."""

    def test_every_name_is_in_the_gen_ai_namespace_or_explicitly_ours(self) -> None:
        theirs = [
            OPERATION_NAME,
            PROVIDER_NAME,
            CONVERSATION_ID,
            AGENT_NAME,
            REQUEST_MODEL,
            RESPONSE_MODEL,
            USAGE_INPUT_TOKENS,
            USAGE_OUTPUT_TOKENS,
            EVALUATION_NAME,
            EVALUATION_SCORE,
        ]
        assert all(name.startswith("gen_ai.") for name in theirs)

    def test_our_own_attributes_are_namespaced_away_from_theirs(self) -> None:
        """The point of adopting a vocabulary is lost if ours look like theirs."""
        ours = [NODE_PARENT_ID, TURN_INDEX, ARM, SCHEMA_VERSION]
        assert all(name.startswith("decision_evals.") for name in ours)

    def test_the_renamed_field_is_not_used(self) -> None:
        """``gen_ai.system`` was renamed to ``gen_ai.provider.name`` upstream."""
        assert PROVIDER_NAME == "gen_ai.provider.name"

    def test_the_provider_value_is_a_registry_well_known_value(self) -> None:
        assert PROVIDER_ANTHROPIC == "anthropic"

    def test_provenance_pins_a_commit_not_a_branch(self) -> None:
        recorded = provenance()
        assert len(recorded["semconv_commit"]) == 40
        assert recorded["semconv_stability"] == "development"

    def test_no_opentelemetry_package_is_imported(self) -> None:
        """Adopting the names must not become a runtime dependency or a socket."""
        source = (REPO_ROOT / "evals" / "src" / "decision_evals" / "telemetry.py").read_text(
            encoding="utf-8"
        )
        assert "import opentelemetry" not in source
        assert "from opentelemetry" not in source


class TestSpanName:
    def test_it_follows_the_specified_convention(self) -> None:
        assert span_name(OP_CHAT, "claude-haiku-4-5") == "chat claude-haiku-4-5"


class TestNodeIdentity:
    def test_a_single_call_has_no_parent_and_no_turn(self) -> None:
        identity = NodeIdentity(conversation_id="run-1")
        assert identity.is_root
        assert identity.turn_index is None

    def test_a_dispatched_node_is_not_root(self) -> None:
        identity = NodeIdentity(conversation_id="run-1", node_id="sub-2", parent_node_id="root")
        assert not identity.is_root


class TestSpanAttributes:
    def test_the_required_attributes_are_always_present(self) -> None:
        attrs = span_attributes(
            NodeIdentity(conversation_id="run-1"), request_model="claude-haiku-4-5"
        )
        assert attrs[OPERATION_NAME] == OP_CHAT
        assert attrs[PROVIDER_NAME] == PROVIDER_ANTHROPIC
        assert attrs[CONVERSATION_ID] == "run-1"
        assert attrs[SCHEMA_VERSION] == RECORD_SCHEMA_VERSION

    def test_absent_optionals_are_omitted_rather_than_set_to_none(self) -> None:
        """A null and a missing key mean different things to a trace consumer."""
        attrs = span_attributes(
            NodeIdentity(conversation_id="run-1"), request_model="claude-haiku-4-5"
        )
        for name in (RESPONSE_MODEL, USAGE_INPUT_TOKENS, NODE_PARENT_ID, TURN_INDEX, ARM):
            assert name not in attrs

    def test_present_optionals_are_emitted(self) -> None:
        attrs = span_attributes(
            NodeIdentity(
                conversation_id="run-1",
                node_id="sub-2",
                parent_node_id="root",
                turn_index=3,
                operation=OP_INVOKE_AGENT,
            ),
            request_model="claude-haiku-4-5",
            response_model="claude-haiku-4-5-20251001",
            input_tokens=1200,
            output_tokens=340,
            arm="on",
            evaluation_name="admissibility",
            evaluation_score=1.0,
        )
        assert attrs[NODE_PARENT_ID] == "root"
        assert attrs[TURN_INDEX] == 3
        assert attrs[USAGE_INPUT_TOKENS] == 1200
        assert attrs[USAGE_OUTPUT_TOKENS] == 340
        assert attrs[EVALUATION_NAME] == "admissibility"
        assert attrs[EVALUATION_SCORE] == 1.0
        assert attrs[ARM] == "on"

    def test_turn_index_zero_is_emitted_and_not_swallowed_as_falsy(self) -> None:
        """The classic bug in an ``if value`` filter. Turn 0 is a real turn."""
        attrs = span_attributes(
            NodeIdentity(conversation_id="run-1", turn_index=0),
            request_model="m",
            input_tokens=0,
            evaluation_score=0.0,
        )
        assert attrs[TURN_INDEX] == 0
        assert attrs[USAGE_INPUT_TOKENS] == 0
        assert attrs[EVALUATION_SCORE] == 0.0

    def test_the_response_model_is_recorded_separately_from_the_request(self) -> None:
        """A subscription can serve a different build than the alias asked for."""
        attrs = span_attributes(
            NodeIdentity(conversation_id="r"),
            request_model="claude-haiku-4-5",
            response_model="claude-haiku-4-5-20251001",
        )
        assert attrs[REQUEST_MODEL] != attrs[RESPONSE_MODEL]


class TestRecordSchema:
    def test_a_new_record_carries_the_current_schema_version(self) -> None:
        record = RunRecord(
            item_id="i",
            template_id="t",
            arm="off",
            model="m",
            n_distractors=0,
            position="none",
            expected="x",
            parsed="x",
            parse_status="parsed",
            correct=True,
            zero_cause=None,
            cost_usd=0.0,
            input_tokens=1,
            output_tokens=1,
            duration_ms=1,
            response="r",
            schema_version=RECORD_SCHEMA_VERSION,
        )
        assert record.schema_version == 2

    def test_an_old_record_defaults_to_schema_one(self, tmp_path: Path) -> None:
        """It describes itself accurately rather than claiming to be current."""
        payload = {
            "item_id": "i",
            "template_id": "t",
            "arm": "off",
            "model": "m",
            "n_distractors": 0,
            "position": "none",
            "expected": "x",
            "parsed": "x",
            "parse_status": "parsed",
            "correct": True,
            "zero_cause": None,
            "cost_usd": 0.0,
            "input_tokens": 1,
            "output_tokens": 1,
            "duration_ms": 1,
            "response": "r",
        }
        checkpoint = tmp_path / "old.jsonl"
        checkpoint.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        loaded = load_records(checkpoint)
        assert loaded[0].schema_version == 1
        assert loaded[0].conversation_id is None
        assert loaded[0].turn_index is None

    def test_an_unknown_column_still_fails_loudly(self, tmp_path: Path) -> None:
        """Defaults must not have turned the loud failure back into a silent one."""
        from decision_evals.runner import RunError

        checkpoint = tmp_path / "future.jsonl"
        checkpoint.write_text(json.dumps({"item_id": "i", "invented": 1}) + "\n", encoding="utf-8")
        with pytest.raises(RunError, match="does not match the current RunRecord schema"):
            load_records(checkpoint)

    @pytest.mark.parametrize("checkpoint", _RUN_RECORD_CHECKPOINTS, ids=lambda p: p.name)
    def test_every_published_run_record_still_loads(self, checkpoint: Path) -> None:
        """The point of the defaults.

        These are the runs the notebook cites. A schema change that orphaned
        them would make the cited numbers unrecomputable, which is a worse
        outcome than never adding the columns.
        """
        records = load_records(checkpoint)
        assert records
        assert all(record.schema_version == 1 for record in records)

    def test_the_published_checkpoints_were_actually_found(self) -> None:
        """Otherwise an empty glob would make the test above vacuously green.

        This asserted ``len(...) >= 2`` until 2026-08-19 and could only pass on
        a machine that had already run the experiments. Every other RunRecord
        checkpoint lives under ``results/calibration/``, ``results/track-a/``,
        ``results/track-0/`` or ``results/triggers/``, all gitignored on
        purpose by ``.gitignore``; exactly one is committed. So the guard
        against vacuity was itself satisfied by data the repository does not
        carry, and the parametrised test above ran over one item everywhere
        else while this one failed.

        Naming the tracked file fixes both halves. The discovery still cannot
        silently return nothing, and it now says which file it expects, so a
        layout move or a first-line shape change fails with the name in the
        message rather than with an integer that means nothing on its own.
        """
        found = {path.relative_to(REPO_ROOT).as_posix() for path in _RUN_RECORD_CHECKPOINTS}
        missing = sorted(set(_TRACKED_CHECKPOINTS) - found)
        assert not missing, (
            f"{missing} is committed RunRecord JSONL that the discovery did not find. "
            "Either the layout moved or the first line stopped carrying `item_id`, and "
            "either way test_every_published_run_record_still_loads is not covering "
            "what it claims to."
        )


def test_the_module_declares_which_names_it_pinned() -> None:
    """Guards against the vocabulary drifting without the provenance moving."""
    assert telemetry.SEMCONV_REPO.endswith("semantic-conventions-genai")
