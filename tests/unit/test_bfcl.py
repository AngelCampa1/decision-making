"""BFCL's AST match, tested against the vendored key before it is trusted.

The verifier is tested before it is believed -- the discipline `scorers/answer.py`
already states, and the one that found 21 of 21 key errors. Two properties carry
most of these tests: the reference shape is asserted rather than assumed, and a
parse failure is a distinct outcome from a wrong answer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from decision_evals.corpora import load_corpus
from decision_evals.scorers.bfcl import (
    CALL_FORMAT,
    OPTIONAL,
    BfclParseError,
    Call,
    match,
    parse_reference,
    parse_response,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

HISTOGRAM = [
    {"create_histogram": {"data": [[1, 2, 3]], "bins": [5]}},
    {"create_histogram": {"data": [[4, 5, 6]], "bins": [5]}},
]


class TestParseReference:
    def test_it_reads_the_vendored_shape(self) -> None:
        calls = parse_reference(HISTOGRAM)
        assert [c.name for c in calls] == ["create_histogram", "create_histogram"]
        assert calls[0].arguments == {"data": [[1, 2, 3]], "bins": [5]}

    def test_a_non_list_reference_is_refused(self) -> None:
        with pytest.raises(BfclParseError, match="expected a list"):
            parse_reference({"create_histogram": {}})

    def test_an_empty_reference_is_refused(self) -> None:
        with pytest.raises(BfclParseError, match="expected a list"):
            parse_reference([])

    def test_a_multi_key_call_is_refused(self) -> None:
        with pytest.raises(BfclParseError, match="single-key dict"):
            parse_reference([{"a": {}, "b": {}}])

    def test_non_dict_parameters_are_refused(self) -> None:
        with pytest.raises(BfclParseError, match="not a dict"):
            parse_reference([{"a": [1, 2]}])

    def test_a_bare_parameter_value_is_refused(self) -> None:
        """Every one of the 776 measured parameters is a list of alternatives."""
        with pytest.raises(BfclParseError, match="list of acceptable values"):
            parse_reference([{"create_histogram": {"bins": 5}}])

    def test_every_actions_record_in_the_corpus_parses(self) -> None:
        """The shape claim in the module docstring, checked against the corpus."""
        corpus = [i for i in load_corpus(REPO_ROOT, check_hash=False) if i.task == "actions"]
        assert len(corpus) == 105
        for item in corpus:
            calls = parse_reference(item.payload["reference_answer"])
            assert 2 <= len(calls) <= 8, item.task_id


class TestParseResponse:
    def test_it_finds_a_fenced_array(self) -> None:
        text = 'Here you go.\n```json\n[{"name": "f", "arguments": {"x": 1}}]\n```\nDone.'
        assert parse_response(text) == [Call(name="f", arguments={"x": 1})]

    def test_arguments_may_be_omitted(self) -> None:
        assert parse_response('[{"name": "f"}]') == [Call(name="f", arguments={})]

    def test_prose_with_no_array_is_a_parse_failure_not_a_wrong_answer(self) -> None:
        with pytest.raises(BfclParseError, match="no JSON array"):
            parse_response("I would use create_histogram twice, with five bins each.")

    def test_malformed_json_is_a_parse_failure(self) -> None:
        with pytest.raises(BfclParseError, match="not valid JSON"):
            parse_response('[{"name": "f",}]')

    def test_a_call_without_a_name_is_refused(self) -> None:
        with pytest.raises(BfclParseError, match="missing a `name`"):
            parse_response('[{"arguments": {"x": 1}}]')

    def test_non_object_arguments_are_refused(self) -> None:
        with pytest.raises(BfclParseError, match="not an object"):
            parse_response('[{"name": "f", "arguments": [1, 2]}]')


class TestMatch:
    def test_the_reference_matches_itself(self) -> None:
        reference = parse_reference(HISTOGRAM)
        supplied = [
            Call("create_histogram", {"data": [1, 2, 3], "bins": 5}),
            Call("create_histogram", {"data": [4, 5, 6], "bins": 5}),
        ]
        assert match(supplied, reference).matched

    def test_order_does_not_matter(self) -> None:
        """`parallel` means the calls may be issued in any order."""
        reference = parse_reference(HISTOGRAM)
        supplied = [
            Call("create_histogram", {"data": [4, 5, 6], "bins": 5}),
            Call("create_histogram", {"data": [1, 2, 3], "bins": 5}),
        ]
        assert match(supplied, reference).matched

    def test_a_wrong_argument_value_fails_with_its_reason(self) -> None:
        reference = parse_reference(HISTOGRAM)
        supplied = [
            Call("create_histogram", {"data": [1, 2, 3], "bins": 5}),
            Call("create_histogram", {"data": [4, 5, 6], "bins": 10}),
        ]
        result = match(supplied, reference)
        assert not result.matched
        assert any("bins" in reason for reason in result.reasons)

    def test_the_wrong_number_of_calls_fails_immediately(self) -> None:
        result = match(
            [Call("create_histogram", {"data": [1, 2, 3], "bins": 5})], parse_reference(HISTOGRAM)
        )
        assert not result.matched
        assert "1 call(s) issued, 2 required" in result.reasons[0]

    def test_an_empty_string_alternative_makes_a_parameter_optional(self) -> None:
        reference = parse_reference([{"f": {"a": [1], "b": [2, OPTIONAL]}}])
        assert match([Call("f", {"a": 1})], reference).matched
        assert match([Call("f", {"a": 1, "b": 2})], reference).matched

    def test_a_missing_required_argument_fails(self) -> None:
        reference = parse_reference([{"f": {"a": [1], "b": [2]}}])
        result = match([Call("f", {"a": 1})], reference)
        assert not result.matched
        assert "missing required argument 'b'" in result.reasons[0]

    def test_an_unexpected_argument_fails(self) -> None:
        reference = parse_reference([{"f": {"a": [1]}}])
        result = match([Call("f", {"a": 1, "z": 9})], reference)
        assert not result.matched
        assert "unexpected argument(s) ['z']" in result.reasons[0]

    def test_a_wrong_function_name_fails(self) -> None:
        reference = parse_reference([{"f": {"a": [1]}}])
        result = match([Call("g", {"a": 1})], reference)
        assert not result.matched
        assert "name 'g' != 'f'" in result.reasons[0]

    def test_five_and_five_point_zero_are_the_same_argument(self) -> None:
        reference = parse_reference([{"f": {"n": [5]}}])
        assert match([Call("f", {"n": 5.0})], reference).matched

    def test_a_bool_is_not_an_int(self) -> None:
        """`True == 1` in Python, and a flag set to True is not a count of 1."""
        reference = parse_reference([{"f": {"n": [1]}}])
        assert not match([Call("f", {"n": True})], reference).matched

    def test_case_and_padding_in_a_string_argument_are_not_graded(self) -> None:
        reference = parse_reference([{"f": {"data": ["data_random_forest"]}}])
        assert match([Call("f", {"data": " Data_Random_Forest "})], reference).matched

    def test_a_list_argument_compares_elementwise(self) -> None:
        reference = parse_reference([{"f": {"xs": [[1, 2, 3]]}}])
        assert match([Call("f", {"xs": [1.0, 2, 3]})], reference).matched
        assert not match([Call("f", {"xs": [1, 2]})], reference).matched

    def test_a_non_scalar_falls_back_to_equality(self) -> None:
        reference = parse_reference([{"f": {"cfg": [{"a": 1}]}}])
        assert match([Call("f", {"cfg": {"a": 1}})], reference).matched
        assert not match([Call("f", {"cfg": {"a": 2}})], reference).matched

    def test_two_identical_reference_calls_need_two_response_calls(self) -> None:
        """The bijection is real: one response call cannot satisfy two references."""
        reference = parse_reference([{"f": {"a": [1]}}, {"f": {"a": [1]}}])
        supplied = [Call("f", {"a": 1}), Call("f", {"a": 1})]
        assert match(supplied, reference).matched
        assert not match([Call("f", {"a": 1}), Call("f", {"a": 2})], reference).matched


def test_the_call_format_states_the_shape_the_parser_accepts() -> None:
    """A contract the scorer cannot read is a scorer that measures formatting.

    The example in the prompt must itself be valid JSON. It was not on the first
    attempt -- it used a bare ``value`` placeholder -- and a model copying that
    shape would have produced unparseable output that looked like a reasoning
    failure in the traces.
    """
    assert parse_response(CALL_FORMAT) == [
        Call(name="function_name", arguments={"parameter": "value"})
    ]
