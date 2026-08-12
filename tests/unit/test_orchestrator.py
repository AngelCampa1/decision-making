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
    append_records,
    load_records,
    render_reports,
    run_tree,
    summarise,
)
from decision_evals.providers.claude_code import CliResult
from decision_evals.telemetry import OP_INVOKE_AGENT, OP_INVOKE_WORKFLOW, RECORD_SCHEMA_VERSION

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
