"""The OpenAI-compatible provider.

Everything here runs against a fake ``urlopen`` or a fake ``_post``. The live
half is ``tests/integration/test_ollama.py``, marked ``llm`` and skipped unless
a server is actually running, for the same reason the CLI provider splits the
two: a unit suite that needs a model is a unit suite that stops being run.

The isolation tests are the ones that matter. A Modelfile ``SYSTEM`` line is
the local analogue of a planted ``CLAUDE.md``, and
``notebook/2026-08-10-isolation-canary.md`` is the record of what happens when
that channel is assumed shut rather than checked.
"""

from __future__ import annotations

import io
import json
import urllib.error
from typing import Any

import pytest

from decision_evals.providers.claude_code import (
    AuthenticationError,
    CliError,
    IsolationError,
    PromptTooLongError,
)
from decision_evals.providers.openai_compatible import (
    Endpoint,
    ModelCard,
    _number,
    _post,
    assert_isolated,
    build_payload,
    ollama,
    parse_completion,
    preflight,
    run,
    show,
)


def _completion(
    *,
    content: str = "ready",
    model: str = "qwen3:4b",
    prompt_tokens: int = 12,
    completion_tokens: int = 3,
) -> dict[str, Any]:
    return {
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _fake_urlopen(monkeypatch: pytest.MonkeyPatch, outcome: Any) -> list[Any]:
    """Install a fake ``urlopen``; returns the list it records requests into."""
    seen: list[Any] = []

    def fake(request: Any, timeout: float = 0.0) -> Any:
        seen.append(request)
        if isinstance(outcome, Exception):
            raise outcome
        return _FakeResponse(outcome)

    monkeypatch.setattr("urllib.request.urlopen", fake)
    return seen


def _http_error(code: int, body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "http://x/v1/chat/completions", code, "err", {}, io.BytesIO(body.encode())
    )


# --------------------------------------------------------------------------- #
# The endpoint
# --------------------------------------------------------------------------- #


def test_ollama_is_reachable_and_carries_a_receipt() -> None:
    endpoint = ollama()
    assert endpoint.base_url == "http://127.0.0.1:11434/v1"
    assert endpoint.native_url == "http://127.0.0.1:11434/api"
    assert endpoint.has_receipt


def test_a_host_override_moves_both_surfaces() -> None:
    endpoint = ollama("http://box:9999")
    assert endpoint.base_url == "http://box:9999/v1"
    assert endpoint.native_url == "http://box:9999/api"


def test_an_endpoint_without_a_native_surface_says_so() -> None:
    """The absence is recorded, not assumed away."""
    assert not Endpoint(base_url="http://x/v1", label="vllm").has_receipt


def test_local_inference_costs_zero_and_the_field_exists() -> None:
    """`BudgetLedger` is a burn meter; a free call is a fact, not a gap."""
    assert ollama().cost_usd == 0.0


# --------------------------------------------------------------------------- #
# The model id and the arena gate
# --------------------------------------------------------------------------- #


def test_the_label_prefix_is_stripped_before_the_request() -> None:
    """The server has never heard of the recording convention."""
    payload = build_payload(prompt="p", system_prompt="s", model="ollama/qwen3:4b", label="ollama")
    assert payload["model"] == "qwen3:4b"


def test_a_bare_model_name_is_sent_unchanged() -> None:
    payload = build_payload(prompt="p", system_prompt="s", model="qwen3:4b", label="ollama")
    assert payload["model"] == "qwen3:4b"


def test_the_recorded_model_carries_the_prefix_the_dev_arena_gates_on() -> None:
    """`arenas.py` matches `ollama`, so a local result cannot reach a verdict."""
    from decision_evals.arenas import ARENAS

    result = parse_completion(_completion(), label="ollama", duration_ms=1, cost_usd=0.0)
    assert result.model == "ollama/qwen3:4b"
    assert result.model.startswith(ARENAS["dev"].model_prefixes[1])
    assert not ARENAS["dev"].emits_verdict


def test_both_roles_are_sent_and_sampling_is_off_by_default() -> None:
    payload = build_payload(prompt="p", system_prompt="s", model="m", label="ollama")
    assert [message["role"] for message in payload["messages"]] == ["system", "user"]
    assert payload["temperature"] == 0.0
    assert payload["stream"] is False


def test_temperature_is_settable_for_a_venue_that_wants_scatter() -> None:
    payload = build_payload(
        prompt="p", system_prompt="s", model="m", label="ollama", temperature=0.7
    )
    assert payload["temperature"] == 0.7


# --------------------------------------------------------------------------- #
# Parsing a completion
# --------------------------------------------------------------------------- #


def test_a_well_formed_completion_parses() -> None:
    result = parse_completion(_completion(), label="ollama", duration_ms=42, cost_usd=0.0)
    assert result.text == "ready"
    assert result.input_tokens == 12
    assert result.output_tokens == 3
    assert result.duration_ms == 42


def test_prompt_tokens_are_not_summed_with_cache_fields() -> None:
    """The CLI provider sums three fields to correct a quirk this path lacks.

    `usage.prompt_tokens` is already the whole prompt. Copying the CLI's
    arithmetic would double-count it.
    """
    result = parse_completion(
        _completion(prompt_tokens=100), label="ollama", duration_ms=1, cost_usd=0.0
    )
    assert result.input_tokens == 100
    assert result.cache_creation_tokens == 0
    assert result.cache_read_tokens == 0


def test_a_non_object_response_is_refused() -> None:
    with pytest.raises(CliError, match="expected a completion object"):
        parse_completion(["nope"], label="ollama", duration_ms=1, cost_usd=0.0)


def test_an_error_field_is_refused() -> None:
    with pytest.raises(CliError, match="model not found"):
        parse_completion({"error": "model not found"}, label="ollama", duration_ms=1, cost_usd=0.0)


@pytest.mark.parametrize("choices", [None, "nope", []])
def test_a_response_with_no_usable_choices_is_refused(choices: Any) -> None:
    with pytest.raises(CliError, match="carries no choices"):
        parse_completion({"choices": choices}, label="ollama", duration_ms=1, cost_usd=0.0)


@pytest.mark.parametrize(
    "choice",
    ["not a dict", {"message": "not a dict"}, {"message": {"content": None}}, {}],
)
def test_a_choice_with_no_string_content_is_refused(choice: Any) -> None:
    with pytest.raises(CliError, match="no string content"):
        parse_completion({"choices": [choice]}, label="ollama", duration_ms=1, cost_usd=0.0)


@pytest.mark.parametrize("model", [None, "", 7])
def test_an_unresolved_model_falls_back_to_the_label(model: Any) -> None:
    """A record that cannot name the weights still says which server answered."""
    payload = _completion()
    payload["model"] = model
    result = parse_completion(payload, label="ollama", duration_ms=1, cost_usd=0.0)
    assert result.model == "ollama"


def test_missing_usage_is_zero_rather_than_an_error() -> None:
    payload = _completion()
    del payload["usage"]
    result = parse_completion(payload, label="ollama", duration_ms=1, cost_usd=0.0)
    assert result.input_tokens == 0
    assert result.output_tokens == 0


def test_a_context_window_is_recorded_when_the_server_reports_one() -> None:
    payload = _completion()
    payload["usage"]["context_window"] = 40
    result = parse_completion(payload, label="ollama", duration_ms=1, cost_usd=0.0)
    assert result.context_window == 40
    assert result.context_fraction == pytest.approx(15 / 40)


@pytest.mark.parametrize(
    ("value", "expected"), [(None, 0.0), (3, 3.0), ("4", 4.0), ("nope", 0.0), ([], 0.0)]
)
def test_usage_numbers_survive_whatever_a_server_puts_there(value: Any, expected: float) -> None:
    assert _number(value) == expected


# --------------------------------------------------------------------------- #
# Transport
# --------------------------------------------------------------------------- #


def test_a_successful_post_decodes_json(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_urlopen(monkeypatch, json.dumps({"ok": True}).encode())
    assert _post("http://x", {}, api_key=None, timeout=1.0) == {"ok": True}


def test_no_api_key_means_no_authorization_header(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _fake_urlopen(monkeypatch, b"{}")
    _post("http://x", {}, api_key=None, timeout=1.0)
    assert "Authorization" not in seen[0].headers


def test_an_api_key_is_sent_as_a_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _fake_urlopen(monkeypatch, b"{}")
    _post("http://x", {}, api_key="sekrit", timeout=1.0)
    assert seen[0].headers["Authorization"] == "Bearer sekrit"


@pytest.mark.parametrize("code", [401, 403])
def test_a_refused_credential_raises_authentication_error(
    monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    _fake_urlopen(monkeypatch, _http_error(code, "no"))
    with pytest.raises(AuthenticationError):
        _post("http://x", {}, api_key=None, timeout=1.0)


@pytest.mark.parametrize(
    "body",
    [
        "prompt exceeds the context window",
        "This model's maximum context length is 4096",
        "context length exceeded",
    ],
)
def test_an_oversized_prompt_raises_its_own_error(
    monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    """The runner scores this differently from a transport failure."""
    _fake_urlopen(monkeypatch, _http_error(400, body))
    with pytest.raises(PromptTooLongError):
        _post("http://x", {}, api_key=None, timeout=1.0)


def test_any_other_http_error_is_a_cli_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_urlopen(monkeypatch, _http_error(500, "boom"))
    with pytest.raises(CliError, match="returned 500"):
        _post("http://x", {}, api_key=None, timeout=1.0)


def test_an_unreachable_server_says_how_to_start_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The overwhelmingly common failure, and a bare refusal does not say so."""
    _fake_urlopen(monkeypatch, urllib.error.URLError("connection refused"))
    with pytest.raises(CliError, match="ollama serve"):
        _post("http://x", {}, api_key=None, timeout=1.0)


def test_a_non_json_body_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_urlopen(monkeypatch, b"<html>502</html>")
    with pytest.raises(CliError, match="did not return JSON"):
        _post("http://x", {}, api_key=None, timeout=1.0)


# --------------------------------------------------------------------------- #
# Isolation
# --------------------------------------------------------------------------- #


def test_a_bare_model_card_is_isolated() -> None:
    assert ModelCard(model="m", system="", template="{{ .Prompt }}", parameters="").is_isolated


def test_a_whitespace_only_system_line_is_still_isolated() -> None:
    assert ModelCard(model="m", system="   \n ", template="", parameters="").is_isolated


def test_a_baked_in_system_prompt_is_not_isolated() -> None:
    card = ModelCard(model="m", system="You are a helpful assistant.", template="", parameters="")
    assert not card.is_isolated


def test_a_template_alone_does_not_fail_the_gate() -> None:
    """Every instruct tag has one; refusing it would refuse every usable model."""
    card = ModelCard(model="m", system="", template="<|im_start|>{{ .System }}", parameters="")
    assert card.is_isolated
    assert assert_isolated(card) is None


def test_assert_isolated_refuses_a_planted_system_prompt() -> None:
    card = ModelCard(model="qwen3:4b", system="Always mention bananas.", template="", parameters="")
    with pytest.raises(IsolationError, match="baked-in system prompt"):
        assert_isolated(card)


def test_the_refusal_quotes_what_it_found() -> None:
    """A gate that says only `failed` cannot be acted on."""
    card = ModelCard(model="m", system="Always mention bananas.", template="", parameters="")
    with pytest.raises(IsolationError, match="bananas"):
        assert_isolated(card)


def test_a_model_card_is_read_from_the_native_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, payload: dict[str, Any], **kwargs: Any) -> Any:
        captured["url"] = url
        captured["payload"] = payload
        return {"system": "", "template": "T", "parameters": "P"}

    monkeypatch.setattr("decision_evals.providers.openai_compatible._post", fake_post)
    card = show("ollama/qwen3:4b", endpoint=ollama())
    assert captured["url"] == "http://127.0.0.1:11434/api/show"
    assert captured["payload"] == {"model": "qwen3:4b"}
    assert card == ModelCard(model="qwen3:4b", system="", template="T", parameters="P")


def test_a_bare_name_reaches_show_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, payload: dict[str, Any], **kwargs: Any) -> Any:
        captured["payload"] = payload
        return {}

    monkeypatch.setattr("decision_evals.providers.openai_compatible._post", fake_post)
    show("qwen3:4b", endpoint=ollama())
    assert captured["payload"] == {"model": "qwen3:4b"}


def test_an_absent_card_field_reads_as_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "decision_evals.providers.openai_compatible._post",
        lambda *a, **k: {},
    )
    assert show("m", endpoint=ollama()) == ModelCard(
        model="m", system="", template="", parameters=""
    )


def test_a_non_object_card_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "decision_evals.providers.openai_compatible._post",
        lambda *a, **k: ["nope"],
    )
    with pytest.raises(CliError, match="expected a model card"):
        show("m", endpoint=ollama())


def test_an_endpoint_with_no_receipt_refuses_to_pretend() -> None:
    """Silence must not pass for a pass."""
    with pytest.raises(CliError, match="no model-card surface"):
        show("m", endpoint=Endpoint(base_url="http://x/v1", label="vllm"))


# --------------------------------------------------------------------------- #
# Running
# --------------------------------------------------------------------------- #


def test_run_posts_to_chat_completions_and_parses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, payload: dict[str, Any], **kwargs: Any) -> Any:
        captured["url"] = url
        captured["payload"] = payload
        return _completion()

    monkeypatch.setattr("decision_evals.providers.openai_compatible._post", fake_post)
    result = run("p", system_prompt="s", model="ollama/qwen3:4b")
    assert captured["url"] == "http://127.0.0.1:11434/v1/chat/completions"
    assert captured["payload"]["model"] == "qwen3:4b"
    assert result.text == "ready"
    assert result.cost_usd == 0.0
    assert result.duration_ms >= 0


def test_run_honours_an_explicit_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, payload: dict[str, Any], **kwargs: Any) -> Any:
        captured["url"] = url
        return _completion()

    monkeypatch.setattr("decision_evals.providers.openai_compatible._post", fake_post)
    endpoint = Endpoint(base_url="http://box:8000/v1", label="vllm", cost_usd=0.0)
    run("p", system_prompt="s", model="vllm/llama", endpoint=endpoint)
    assert captured["url"] == "http://box:8000/v1/chat/completions"


def test_preflight_asks_for_one_word(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail before item 1 rather than 300 items in."""
    captured: dict[str, Any] = {}

    def fake_post(url: str, payload: dict[str, Any], **kwargs: Any) -> Any:
        captured["payload"] = payload
        return _completion()

    monkeypatch.setattr("decision_evals.providers.openai_compatible._post", fake_post)
    assert preflight(model="ollama/qwen3:4b").text == "ready"
    assert "ready" in captured["payload"]["messages"][1]["content"]
