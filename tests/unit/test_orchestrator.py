"""The scripted call tree.

Most of these test seams rather than behaviour, because the seams are what the
module exists for: a tree you cannot ablate a report inside is an expensive way
to make four calls, and a tree whose records cannot say what the orchestrator
actually read cannot attribute anything.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from decision_evals.budget import BudgetError, BudgetLedger
from decision_evals.orchestrator import (
    ABLATED,
    ROOT,
    Dispatch,
    NodeRecord,
    OrchestratorError,
    TreeResult,
    _default_runner,
    ablation_is_identified,
    append_records,
    load_records,
    pin,
    pinned_dispatches,
    render_reports,
    run_ablation,
    run_tree,
    summarise,
)
from decision_evals.providers.claude_code import CliResult
from decision_evals.telemetry import (
    AGENT_NAME,
    CONVERSATION_ID,
    NODE_PARENT_ID,
    OP_INVOKE_AGENT,
    OP_INVOKE_WORKFLOW,
    OPERATION_NAME,
    RECORD_SCHEMA_VERSION,
    REQUEST_MODEL,
    RESPONSE_MODEL,
    USAGE_INPUT_TOKENS,
    USAGE_OUTPUT_TOKENS,
)

TEMPLATE = "Task: {task}\n\n{reports}"


def _result(text: str, *, cost: float = 0.001, tokens: int = 100) -> CliResult:
    return CliResult(
        text=text,
        model="claude-haiku-4-5-20251001",
        cost_usd=cost,
        input_tokens=tokens,
        output_tokens=20,
        duration_ms=500,
        session_id="s",
    )


class ScriptedRunner:
    """Returns a canned response per node name and records what it was asked."""

    def __init__(self, responses: dict[str, str]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, str]] = []

    def __call__(self, system_prompt: str, prompt: str, node_name: str) -> CliResult:
        self.calls.append((system_prompt, prompt, node_name))
        return _result(self.responses.get(node_name, f"reply from {node_name}"))

    def prompt_for(self, node_name: str) -> str:
        return next(prompt for _, prompt, name in self.calls if name == node_name)


def _dispatches(*names: str) -> list[Dispatch]:
    return [Dispatch(name=name, system_prompt="s", prompt=f"do {name}") for name in names]


def _run(dispatches: list[Dispatch], runner: ScriptedRunner, *, limit: float = 10.0) -> TreeResult:
    return run_tree(
        task="decide",
        orchestrator_system_prompt="root",
        orchestrator_template=TEMPLATE,
        dispatches=dispatches,
        conversation_id="c1",
        ledger=BudgetLedger(limit_usd=limit),
        runner=runner,
    )


class TestShape:
    def test_every_node_gets_a_record_and_the_root_is_last(self) -> None:
        runner = ScriptedRunner({})
        result = _run(_dispatches("a", "b", "c"), runner)
        assert result.n_nodes == 4
        assert [r.node_name for r in result.records] == ["a", "b", "c", ROOT]

    def test_sub_agents_run_before_the_orchestrator(self) -> None:
        """Fan out once, aggregate once. If the root ran first it could not have
        seen a report, and the module would be three unrelated calls."""
        runner = ScriptedRunner({})
        _run(_dispatches("a", "b"), runner)
        assert [name for _, _, name in runner.calls] == ["a", "b", ROOT]

    def test_the_root_has_no_parent_and_the_leaves_point_at_it(self) -> None:
        result = _run(_dispatches("a", "b"), ScriptedRunner({}))
        root = next(r for r in result.records if r.node_name == ROOT)
        assert root.parent_node_id is None
        assert root.operation == OP_INVOKE_WORKFLOW
        for record in result.records:
            if record.node_name != ROOT:
                assert record.parent_node_id == root.node_id
                assert record.operation == OP_INVOKE_AGENT

    def test_node_ids_are_unique(self) -> None:
        result = _run(_dispatches("a", "b", "c"), ScriptedRunner({}))
        ids = [r.node_id for r in result.records]
        assert len(set(ids)) == len(ids)

    def test_final_response_is_the_orchestrators(self) -> None:
        runner = ScriptedRunner({ROOT: "the answer", "a": "a report"})
        assert _run(_dispatches("a"), runner).final_response == "the answer"

    def test_final_response_refuses_a_tree_with_no_root(self) -> None:
        empty = TreeResult(conversation_id="c", records=(), ledger=BudgetLedger(limit_usd=1.0))
        with pytest.raises(OrchestratorError, match="no orchestrator record"):
            _ = empty.final_response

    def test_a_record_carries_no_correctness_field(self) -> None:
        """Rule 3, enforced by the schema rather than by remembering."""
        forbidden = {"correct", "score", "admissible", "passed", "verdict"}
        assert forbidden.isdisjoint(NodeRecord.__dataclass_fields__)


class TestNodeRecordCarriesTelemetryAttributes:
    """Track 0.5's production call site.

    ``telemetry.span_attributes()`` was tested to 100% but had no caller
    outside ``tests/unit/test_telemetry.py``. This tree is the multi-node run
    the module's own docstring says the vocabulary was written for -- every
    node already carries a parent, an operation and a trace id -- so every
    :class:`NodeRecord` now reshapes them through ``span_attributes()`` rather
    than the mapping only ever existing in a test.
    """

    def test_a_leaf_records_the_pinned_attribute_mapping(self) -> None:
        result = _run(_dispatches("a"), ScriptedRunner({"a": "A"}))
        leaf = next(r for r in result.records if r.node_name == "a")
        assert leaf.attributes[OPERATION_NAME] == OP_INVOKE_AGENT
        assert leaf.attributes[CONVERSATION_ID] == "c1"
        assert leaf.attributes[AGENT_NAME] == "a"
        assert leaf.attributes[NODE_PARENT_ID] == leaf.parent_node_id
        assert leaf.attributes[USAGE_INPUT_TOKENS] == leaf.prompt_tokens
        assert leaf.attributes[USAGE_OUTPUT_TOKENS] == leaf.output_tokens

    def test_the_root_records_no_parent_attribute(self) -> None:
        """The root is the degenerate case ``span_attributes`` was built for:
        an absent optional is omitted, not set to ``None``."""
        result = _run(_dispatches("a"), ScriptedRunner({}))
        root = next(r for r in result.records if r.node_name == ROOT)
        assert root.attributes[OPERATION_NAME] == OP_INVOKE_WORKFLOW
        assert NODE_PARENT_ID not in root.attributes

    def test_request_and_response_model_are_recorded_separately(self) -> None:
        """The tree asked for ``haiku``; the CLI answered as a dated build."""
        result = _run(_dispatches("a"), ScriptedRunner({}))
        leaf = next(r for r in result.records if r.node_name == "a")
        assert leaf.attributes[REQUEST_MODEL] == "haiku"
        assert leaf.attributes[RESPONSE_MODEL] == "claude-haiku-4-5-20251001"
        assert leaf.attributes[REQUEST_MODEL] != leaf.attributes[RESPONSE_MODEL]

    def test_a_record_predating_this_field_defaults_to_an_empty_mapping(self) -> None:
        """Backward compatibility for every checkpoint already on disk, e.g.
        ``results/track-0/tree_smoke.jsonl``, which has no ``attributes`` key."""
        record = NodeRecord(
            conversation_id="c",
            node_name="a",
            node_id="c/0",
            parent_node_id="c/orchestrator",
            operation=OP_INVOKE_AGENT,
            model="m",
            prompt="p",
            response="r",
            report_seen_by_parent="r",
            prompt_tokens=1,
            output_tokens=1,
            cost_usd=0.0,
            duration_ms=1,
        )
        assert record.attributes == {}

    def test_records_carry_the_current_schema_version(self) -> None:
        result = _run(_dispatches("a"), ScriptedRunner({}))
        assert all(r.schema_version == RECORD_SCHEMA_VERSION for r in result.records)


class TestReportsReachTheOrchestrator:
    def test_the_orchestrator_prompt_contains_every_report(self) -> None:
        runner = ScriptedRunner({"a": "ALPHA", "b": "BETA"})
        _run(_dispatches("a", "b"), runner)
        prompt = runner.prompt_for(ROOT)
        assert "ALPHA" in prompt
        assert "BETA" in prompt
        assert "decide" in prompt

    def test_a_transform_changes_what_the_parent_reads_not_what_was_said(self) -> None:
        dispatches = [
            Dispatch(name="a", system_prompt="s", prompt="p", transform=lambda _: "SUBSTITUTED")
        ]
        runner = ScriptedRunner({"a": "ORIGINAL"})
        result = _run(dispatches, runner)

        record = result.records[0]
        assert record.response == "ORIGINAL"
        assert record.report_seen_by_parent == "SUBSTITUTED"
        assert record.was_transformed
        assert "SUBSTITUTED" in runner.prompt_for(ROOT)
        assert "ORIGINAL" not in runner.prompt_for(ROOT)

    def test_an_untransformed_report_is_not_marked_transformed(self) -> None:
        result = _run(_dispatches("a"), ScriptedRunner({"a": "R"}))
        assert not result.records[0].was_transformed

    def test_an_ablated_report_still_leaves_its_heading(self) -> None:
        """An orchestrator that can see a sub-agent returned nothing and one that
        cannot see it was dispatched are different conditions."""
        dispatches = [Dispatch(name="a", system_prompt="s", prompt="p", transform=lambda _: None)]
        runner = ScriptedRunner({"a": "ORIGINAL"})
        result = _run(dispatches, runner)

        prompt = runner.prompt_for(ROOT)
        assert "Report from a" in prompt
        assert ABLATED in prompt
        assert "ORIGINAL" not in prompt
        assert result.records[0].report_seen_by_parent is None
        assert not result.records[0].was_transformed

    def test_render_reports_refuses_a_length_mismatch(self) -> None:
        with pytest.raises(OrchestratorError, match="misattribute"):
            render_reports(_dispatches("a", "b"), ["only one"])


class TestRefusals:
    def test_a_tree_with_no_sub_agents_is_refused(self) -> None:
        with pytest.raises(OrchestratorError, match="single call"):
            _run([], ScriptedRunner({}))

    def test_duplicate_dispatch_names_are_refused(self) -> None:
        with pytest.raises(OrchestratorError, match="unique"):
            _run(_dispatches("a", "a"), ScriptedRunner({}))

    def test_a_sub_agent_may_not_be_called_orchestrator(self) -> None:
        with pytest.raises(OrchestratorError, match="reserved"):
            _run(_dispatches(ROOT), ScriptedRunner({}))

    @pytest.mark.parametrize("template", ["no placeholders", "only {task}", "only {reports}"])
    def test_a_malformed_template_is_refused_before_any_call(self, template: str) -> None:
        """Before, not after. Finding out afterwards costs the sub-agents' quota
        and leaves half a tree in the records."""
        runner = ScriptedRunner({})
        with pytest.raises(OrchestratorError, match="missing"):
            run_tree(
                task="t",
                orchestrator_system_prompt="s",
                orchestrator_template=template,
                dispatches=_dispatches("a"),
                conversation_id="c1",
                ledger=BudgetLedger(limit_usd=10.0),
                runner=runner,
            )
        assert runner.calls == []


class TestBudgetOverTheTree:
    def test_cost_accumulates_across_every_node(self) -> None:
        result = _run(_dispatches("a", "b", "c"), ScriptedRunner({}))
        assert result.total_cost_usd == pytest.approx(0.004)
        assert result.ledger.spent_usd == pytest.approx(0.004)

    def test_prompt_tokens_accumulate_across_every_node(self) -> None:
        assert _run(_dispatches("a", "b"), ScriptedRunner({})).total_prompt_tokens == 300

    def test_a_tree_that_cannot_afford_its_second_node_stops_there(self) -> None:
        """A per-call limit cannot stop a run that makes four calls per item."""
        runner = ScriptedRunner({})
        with pytest.raises(BudgetError):
            _run(_dispatches("a", "b", "c"), runner, limit=0.0055)
        assert [name for _, _, name in runner.calls] == ["a"]


class TestCheckpoint:
    def test_a_tree_round_trips_through_jsonl(self, tmp_path: Path) -> None:
        result = _run(_dispatches("a", "b"), ScriptedRunner({"a": "A"}))
        path = tmp_path / "nested" / "tree.jsonl"
        append_records(path, result)
        assert load_records(path) == list(result.records)

    def test_two_trees_append_rather_than_overwrite(self, tmp_path: Path) -> None:
        path = tmp_path / "tree.jsonl"
        append_records(path, _run(_dispatches("a"), ScriptedRunner({})))
        append_records(path, _run(_dispatches("a"), ScriptedRunner({})))
        assert len(load_records(path)) == 4

    def test_a_missing_checkpoint_is_empty_not_an_error(self, tmp_path: Path) -> None:
        assert load_records(tmp_path / "absent.jsonl") == []

    def test_blank_lines_are_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "tree.jsonl"
        append_records(path, _run(_dispatches("a"), ScriptedRunner({})))
        path.write_text(path.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
        assert len(load_records(path)) == 2

    def test_an_unknown_column_fails_loudly(self, tmp_path: Path) -> None:
        """A loader that swallows TypeError makes every earlier line vanish the
        moment a field is added, and the run looks empty rather than incompatible."""
        path = tmp_path / "tree.jsonl"
        path.write_text(json.dumps({"unexpected": 1}) + "\n", encoding="utf-8")
        with pytest.raises(OrchestratorError, match="does not match NodeRecord"):
            load_records(path)


class TestSummarise:
    def test_it_splits_cost_by_node_name(self) -> None:
        """A tree whose orchestrator costs eight times each sub-agent is a
        different design problem from one where the sub-agents dominate."""
        results = [_run(_dispatches("a", "b"), ScriptedRunner({})) for _ in range(3)]
        report = summarise(results)
        assert report.n_trees == 3
        assert report.n_nodes == 9
        assert report.total_cost_usd == pytest.approx(0.009)
        assert report.by_node == pytest.approx({"a": 0.003, "b": 0.003, ROOT: 0.003})
        assert report.usd_per_tree == pytest.approx(0.003)

    def test_wall_clock_is_summed_because_the_tree_runs_serially(self) -> None:
        report = summarise([_run(_dispatches("a", "b"), ScriptedRunner({}))])
        assert report.total_duration_ms == 1500

    def test_no_trees_divides_by_nothing(self) -> None:
        report = summarise([])
        assert report.n_trees == 0
        assert report.usd_per_tree == 0.0


class TestDefaultRunner:
    def test_it_asserts_the_receipt_at_every_node(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """0.3. Asserting at the root and assuming for the leaves is the
        assumption a sub-agent experiment least deserves."""
        asserted: list[str] = []
        seen_cwds: list[str] = []

        class FakeReceipt:
            def assert_isolated(self) -> None:
                asserted.append("ok")

        class FakeConversation:
            def __init__(self, *, system_prompt: str, model: str, cwd: str) -> None:
                seen_cwds.append(cwd)
                self.receipt = FakeReceipt()

            def __enter__(self) -> FakeConversation:
                return self

            def __exit__(self, *exc: object) -> None:
                return None

            def send(self, text: str) -> CliResult:
                return _result("reply")

        monkeypatch.setattr("decision_evals.orchestrator.Conversation", FakeConversation)
        runner, count = _default_runner("haiku")

        assert runner("sys", "p", "a").text == "reply"
        assert runner("sys", "p", "b").text == "reply"
        assert asserted == ["ok", "ok"]
        assert count() == 2
        # Fresh cwd per node: the CLI's auto-memory path is keyed on it, so a
        # shared directory would be a cross-node channel a checkpoint cannot see.
        assert len(set(seen_cwds)) == 2

    def test_run_tree_reports_how_many_receipts_it_asserted(self) -> None:
        runner = ScriptedRunner({})
        assert _run(_dispatches("a", "b"), runner).receipts_asserted == 0

    def test_run_tree_without_an_injected_runner_uses_the_isolated_one(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The production path. Every other test here injects a runner, so
        without this the default branch ships unexercised -- and it is the branch
        that decides whether a real run asserts isolation at all."""
        asserted: list[str] = []

        class FakeReceipt:
            def assert_isolated(self) -> None:
                asserted.append("ok")

        class FakeConversation:
            def __init__(self, *, system_prompt: str, model: str, cwd: str) -> None:
                self.receipt = FakeReceipt()

            def __enter__(self) -> FakeConversation:
                return self

            def __exit__(self, *exc: object) -> None:
                return None

            def send(self, text: str) -> CliResult:
                return _result("reply")

        monkeypatch.setattr("decision_evals.orchestrator.Conversation", FakeConversation)
        result = run_tree(
            task="t",
            orchestrator_system_prompt="s",
            orchestrator_template=TEMPLATE,
            dispatches=_dispatches("a", "b"),
            conversation_id="c1",
            ledger=BudgetLedger(limit_usd=10.0),
        )
        assert result.n_nodes == 3
        assert len(asserted) == 3
        assert result.receipts_asserted == 3


class TestAblationPinning:
    """Track 0.7. The rule existed in the programme and nothing implemented it.

    The first ablation this repository ran re-dispatched every sub-agent, and
    `customer-impact` answered on the control pass and declined on the ablation
    pass from an identical prompt. Two things differed and the records could not
    say which moved the orchestrator.
    """

    def _control(self, runner: ScriptedRunner) -> TreeResult:
        return _run(_dispatches("a", "b", "c"), runner)

    def _ablate(
        self, control: TreeResult, runner: ScriptedRunner, *, ablate: str = "b"
    ) -> TreeResult:
        return run_ablation(
            control,
            ablate=ablate,
            task="decide",
            orchestrator_system_prompt="root",
            orchestrator_template=TEMPLATE,
            dispatches=_dispatches("a", "b", "c"),
            conversation_id="c2",
            ledger=BudgetLedger(limit_usd=10.0),
            runner=runner,
        )

    def test_pin_takes_what_the_parent_read_not_what_the_node_said(self) -> None:
        """A control arm may itself transform. Pinning the raw text would move two things."""
        dispatches = [
            Dispatch(name="a", system_prompt="s", prompt="do a", transform=lambda _: "REWRITTEN"),
            Dispatch(name="b", system_prompt="s", prompt="do b"),
        ]
        control = _run(dispatches, ScriptedRunner({"a": "original", "b": "from b"}))
        assert pin(control) == {"a": "REWRITTEN", "b": "from b"}

    def test_the_orchestrator_is_ablated_by_exactly_one_report(self) -> None:
        control = self._control(ScriptedRunner({"a": "A1", "b": "B1", "c": "C1"}))
        # Every sub-agent resamples into a different answer, which is the
        # condition the first ablation ran under.
        ablated = self._ablate(control, ScriptedRunner({"a": "A2", "b": "B2", "c": "C2"}))
        assert pin(ablated) == {"a": "A1", "c": "C1"}
        assert ABLATED in ablated.records[-1].prompt
        assert "A1" in ablated.records[-1].prompt
        assert "A2" not in ablated.records[-1].prompt

    def test_the_records_still_hold_what_the_node_actually_said(self) -> None:
        """Pinning must not erase the resampled response, only what the parent read."""
        control = self._control(ScriptedRunner({"a": "A1", "b": "B1", "c": "C1"}))
        ablated = self._ablate(control, ScriptedRunner({"a": "A2", "b": "B2", "c": "C2"}))
        node_a = next(r for r in ablated.records if r.node_name == "a")
        assert node_a.response == "A2"
        assert node_a.report_seen_by_parent == "A1"
        assert node_a.was_transformed

    def test_ablating_a_node_that_is_not_dispatched_is_refused(self) -> None:
        control = self._control(ScriptedRunner({}))
        with pytest.raises(OrchestratorError, match="cannot ablate"):
            self._ablate(control, ScriptedRunner({}), ablate="absent")

    def test_an_unpinned_surviving_node_is_refused(self) -> None:
        with pytest.raises(OrchestratorError, match="no pinned report"):
            pinned_dispatches(_dispatches("a", "b"), {"a": "A1"}, ablate="a")

    def test_a_surviving_report_that_moved_is_refused_after_the_call(self) -> None:
        """The guard reads the records, so a transform inside `dispatches` cannot defeat it.

        This is the 2026-08-12 run exactly: `b` is properly ablated, and `a` was
        left to resample.
        """
        control = self._control(ScriptedRunner({"a": "A1", "b": "B1", "c": "C1"}))
        unpinned = _run(
            [
                Dispatch(name="a", system_prompt="s", prompt="do a"),
                Dispatch(name="b", system_prompt="s", prompt="do b", transform=lambda _: None),
                Dispatch(name="c", system_prompt="s", prompt="do c", transform=lambda _: "C1"),
            ],
            ScriptedRunner({"a": "A9", "b": "B9", "c": "C9"}),
        )
        reason = ablation_is_identified(control, unpinned, ablate="b")
        assert reason is not None
        assert "measures resampling" in reason
        assert "['a']" in reason

    def test_an_ablation_whose_report_survived_is_refused(self) -> None:
        control = self._control(ScriptedRunner({"a": "A1", "b": "B1", "c": "C1"}))
        assert ablation_is_identified(control, control, ablate="b") is not None

    def test_dropping_the_dispatch_instead_of_the_report_is_refused(self) -> None:
        """An ablated node is still dispatched and its heading still rendered.

        Omitting it makes the arm narrower by one, which is a fan-out
        manipulation wearing an ablation's name — and it is indistinguishable
        from a correct ablation to a check that reads only the pinned reports,
        because both drop out of `pin`.
        """
        control = self._control(ScriptedRunner({"a": "A1", "b": "B1", "c": "C1"}))
        narrower = _run(_dispatches("a", "b"), ScriptedRunner({"a": "A1", "b": "B1"}))
        reason = ablation_is_identified(control, narrower, ablate="c")
        assert reason is not None
        assert "different nodes" in reason

    def test_a_pinned_ablation_is_identified(self) -> None:
        """The estimator returns None as well as a reason, which is the check."""
        control = self._control(ScriptedRunner({"a": "A1", "b": "B1", "c": "C1"}))
        ablated = self._ablate(control, ScriptedRunner({"a": "A2", "b": "B2", "c": "C2"}))
        assert ablation_is_identified(control, ablated, ablate="b") is None

    def test_run_ablation_refuses_a_result_that_is_not_identified(self) -> None:
        """The post-call guard, reached by handing it a tree the control did not run.

        Pinning makes an ablation identified by construction, so this is the
        path where the caller's own `dispatches` disagree with the control —
        which reads as an ablation and is a fan-out change.
        """
        control = self._control(ScriptedRunner({"a": "A1", "b": "B1", "c": "C1"}))
        with pytest.raises(OrchestratorError, match="different nodes"):
            run_ablation(
                control,
                ablate="b",
                task="decide",
                orchestrator_system_prompt="root",
                orchestrator_template=TEMPLATE,
                dispatches=_dispatches("a", "b"),
                conversation_id="c3",
                ledger=BudgetLedger(limit_usd=10.0),
                runner=ScriptedRunner({"a": "A1", "b": "B1"}),
            )
