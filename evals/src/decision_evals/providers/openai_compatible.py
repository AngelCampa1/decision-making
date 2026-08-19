"""An OpenAI-compatible server as a model backend.

``docs/PROTOCOL.md`` §2 has declared a ``dev`` arena on ``Ollama`` since it was
written, and :mod:`decision_evals.arenas` has carried ``model_prefixes=("mockllm",
"ollama")`` for as long. Nothing was ever behind it. This is the backend.

**Why it is worth having, in programme terms.** Every call this repository has
ever made went through one Claude CLI on one subscription. Two consequences.
The claim ladder promises a sentence about "frontier models", plural, which one
family cannot support. And every instrument shakedown -- every falsifier run
against a known-good case, every check that some possible response would have
scored above zero -- spends quota, which is the binding budget here. A local
server costs nothing and has no quota, so the rules in
``docs/AUTONOMOUS_WORK_ORDER.md`` become cheap enough to always follow rather
than expensive enough to skip.

**Why OpenAI-compatible rather than Ollama-native.** The same wire format is
spoken by Ollama, vLLM, LM Studio and ``llama.cpp``'s server, so one module
reaches all of them and a second served model is configuration rather than a
new provider. Ollama is simply the first server pointed at. The native API
would be marginally tidier for exactly one of those and would have to be
rewritten for the rest.

**Why no HTTP dependency.** One POST of JSON. :mod:`decision_evals.corpora`
already fetches a 29 MB corpus with :mod:`urllib.request`, and a dependency
added for one request is a claim about the design that the code contradicts --
the note in ``pyproject.toml`` about the removed ``inspect-ai`` declaration is
this repository's own record of what that costs.

**Isolation is not free here, which was the surprise.** The reasoning that
almost shipped was: the Claude CLI needs :data:`~decision_evals.providers.claude_code.ISOLATION_FLAGS`
and a ``system``/``init`` receipt because it reads ``CLAUDE.md``, skills and MCP
config off disk, whereas an HTTP server reads nothing from the client's
filesystem, so the prompt is the whole context and isolation is structural.

The first half is right and the conclusion is wrong. An Ollama model is a
Modelfile, and a Modelfile may carry its own ``SYSTEM`` instruction and its own
prompt ``TEMPLATE``. A baked-in system prompt is exactly a planted ``CLAUDE.md``
one layer down: invisible in the request, present in every generation, and
attributable to the skill under test if nobody looks. ``qwen3`` and several
published tags ship non-empty templates as a matter of course.

So there is a receipt, and :func:`assert_isolated` asserts it. It reads
Ollama's native ``/api/show`` -- deliberately outside the OpenAI-compatible
surface, because the OpenAI surface cannot express the question -- and refuses
a model whose card carries a ``system`` prompt. For a server that is not Ollama
no equivalent exists, and :class:`Endpoint` makes the caller say so rather than
letting the silence pass for a pass. **Recording "no receipt was available" is
not the same as recording "isolation was verified", and the whole reason Track
0.3 forced the streaming transport onto every node was to stop those two being
confused.**
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Final

from decision_evals.providers.claude_code import (
    AuthenticationError,
    CliError,
    CliResult,
    IsolationError,
    PromptTooLongError,
)

#: Ollama's OpenAI-compatible endpoint. Loopback rather than ``localhost`` so
#: the call cannot take a DNS path on a machine with an unusual hosts file.
OLLAMA_BASE_URL: Final = "http://127.0.0.1:11434/v1"

#: Ollama's native API, which is where the model card lives. The
#: OpenAI-compatible surface has no equivalent of ``/api/show``.
OLLAMA_NATIVE_URL: Final = "http://127.0.0.1:11434/api"

#: HTTP statuses that mean the credential, not the request, was refused.
_AUTH_STATUSES: Final[frozenset[int]] = frozenset({401, 403})

#: Substrings a server uses to say the prompt exceeded the context window.
#: Matched case-insensitively against the error body. ``llama.cpp`` says the
#: first, vLLM the second, Ollama the third.
_TOO_LONG_MARKERS: Final[tuple[str, ...]] = (
    "exceeds the context window",
    "maximum context length",
    "context length exceeded",
)


@dataclass(frozen=True)
class Endpoint:
    """One OpenAI-compatible server, and what can be proven about it.

    ``label`` is prefixed onto every recorded model id and is what
    :mod:`decision_evals.arenas` gates on: ``ollama/qwen3:4b`` matches the
    ``dev`` arena's ``ollama`` prefix, so a local result can never reach an
    arena that emits a verdict. The prefix is stripped before the request,
    because the server knows the model by its bare name.

    ``native_url`` is the honest field. When it is set, :func:`assert_isolated`
    can read the model card and refuse a baked-in system prompt. When it is
    ``None`` the server offers no such surface, no receipt is obtainable, and
    that is recorded as an absence rather than assumed away.
    """

    base_url: str
    label: str
    native_url: str | None = None
    api_key: str | None = None
    #: Local inference bills nothing. Kept explicit and recorded as ``0.0``
    #: rather than omitted: ``BudgetLedger`` is a burn meter, and a call that
    #: genuinely burns no quota is a fact about the run, not a missing field.
    cost_usd: float = 0.0

    @property
    def has_receipt(self) -> bool:
        """Whether isolation can be checked rather than assumed."""
        return self.native_url is not None


def ollama(host: str = "http://127.0.0.1:11434") -> Endpoint:
    """The local Ollama server, with its model-card receipt available."""
    return Endpoint(
        base_url=f"{host}/v1",
        label="ollama",
        native_url=f"{host}/api",
    )


@dataclass(frozen=True)
class ModelCard:
    """What a server declares about a model before it is used.

    The Ollama analogue of
    :class:`~decision_evals.providers.claude_code.InitReceipt`, and it exists
    for the same reason: strictly better evidence than inferring a clean venue
    from a response that looked clean.
    """

    model: str
    system: str
    template: str
    parameters: str

    @property
    def is_isolated(self) -> bool:
        """No baked-in system prompt.

        ``template`` is deliberately *not* part of this. A chat template is the
        wire format -- it is how a role-tagged message becomes tokens, and every
        instruct-tuned tag has one. Refusing a non-empty template would refuse
        every usable model, which is the shape of gate that gets turned off. The
        `system` field is the one that injects content the caller did not write,
        and it is recorded either way.
        """
        return not self.system.strip()


def _post(url: str, payload: dict[str, Any], *, api_key: str | None, timeout: float) -> Any:
    """POST JSON and return the decoded response.

    The single seam every request goes through, so that the unit tests exercise
    parsing and error mapping against a fake rather than a live server.

    Raises:
        AuthenticationError: The server refused the credential.
        PromptTooLongError: The prompt exceeded the context window.
        CliError: Any other transport or protocol failure.
    """
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key is not None:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        if exc.code in _AUTH_STATUSES:
            raise AuthenticationError(
                f"{url} refused the credential ({exc.code}): {detail}"
            ) from exc
        lowered = detail.lower()
        for marker in _TOO_LONG_MARKERS:
            if marker in lowered:
                raise PromptTooLongError(detail) from exc
        raise CliError(f"{url} returned {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        # The overwhelmingly common case is that nobody started the server, and
        # a bare "connection refused" three frames down does not say so.
        raise CliError(
            f"could not reach {url}: {exc.reason}. Is the server running? "
            "For Ollama: `ollama serve`, then `ollama pull <model>`."
        ) from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliError(f"{url} did not return JSON: {raw[:200]!r}") from exc


def build_payload(
    *,
    prompt: str,
    system_prompt: str,
    model: str,
    label: str,
    temperature: float = 0.0,
) -> dict[str, Any]:
    """The request body for one single-turn completion.

    The ``label/`` prefix is stripped: it is a recording convention that makes
    :mod:`decision_evals.arenas` able to gate the result, and the server has
    never heard of it.

    ``temperature`` defaults to 0. The arms differ by a markdown file and
    nothing else, so sampling noise is variance this design has no use for --
    :mod:`decision_evals.stats.reliability` exists to measure scatter that is
    part of the phenomenon, not scatter the harness introduced.
    """
    bare = model[len(label) + 1 :] if model.startswith(f"{label}/") else model
    return {
        "model": bare,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "stream": False,
    }


def parse_completion(payload: Any, *, label: str, duration_ms: int, cost_usd: float) -> CliResult:
    """Turn a ``/chat/completions`` response into a :class:`CliResult`.

    Token accounting deliberately does *not* copy
    :func:`~decision_evals.providers.claude_code.parse_result`, which sums
    ``input_tokens`` with the two cache fields. That sum corrects a quirk of one
    CLI, where the reported input count is the uncached remainder. OpenAI-shaped
    ``usage.prompt_tokens`` is already the whole prompt, so adding anything to it
    would double-count. There is no prompt cache in this path and the cache
    fields stay at their zero defaults, which is true of the call rather than
    merely unrecorded.

    Raises:
        CliError: The response was not a well-formed completion.
    """
    if not isinstance(payload, dict):
        raise CliError(f"expected a completion object, got {payload!r}")

    error = payload.get("error")
    if error:
        raise CliError(str(error))

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise CliError(f"response carries no choices: {payload!r}")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(text, str):
        raise CliError(f"first choice has no string content: {choices[0]!r}")

    # The id the server resolved, not the one that was asked for -- the same
    # rule the CLI provider applies to `modelUsage`. A tag like `qwen3:4b` moves
    # when it is re-pulled, and a record naming the request cannot say which
    # weights answered.
    resolved = payload.get("model")
    model = f"{label}/{resolved}" if isinstance(resolved, str) and resolved else label

    usage = payload.get("usage") or {}
    return CliResult(
        text=text,
        model=model,
        cost_usd=cost_usd,
        input_tokens=int(_number(usage.get("prompt_tokens"))),
        output_tokens=int(_number(usage.get("completion_tokens"))),
        duration_ms=duration_ms,
        session_id="",
        context_window=int(_number(usage.get("context_window"))),
    )


def _number(value: Any) -> float:
    """Coerce a possibly-absent, possibly-null usage field to a number."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def show(model: str, *, endpoint: Endpoint, timeout: float = 30.0) -> ModelCard:
    """Read a model's card from a server that has one.

    Raises:
        CliError: The endpoint offers no native surface, or the card is
            malformed.
    """
    if endpoint.native_url is None:
        raise CliError(
            f"{endpoint.label} exposes no model-card surface, so isolation cannot be "
            "checked. Record the absence rather than asserting a clean venue."
        )
    bare = model[len(endpoint.label) + 1 :] if model.startswith(f"{endpoint.label}/") else model
    payload = _post(
        f"{endpoint.native_url}/show",
        {"model": bare},
        api_key=endpoint.api_key,
        timeout=timeout,
    )
    if not isinstance(payload, dict):
        raise CliError(f"expected a model card, got {payload!r}")
    return ModelCard(
        model=bare,
        system=str(payload.get("system") or ""),
        template=str(payload.get("template") or ""),
        parameters=str(payload.get("parameters") or ""),
    )


def assert_isolated(card: ModelCard) -> None:
    """Refuse a model that answers with content the caller did not write.

    Raises:
        IsolationError: The model card declares a ``SYSTEM`` prompt.
    """
    if card.is_isolated:
        return
    raise IsolationError(
        f"{card.model} carries a baked-in system prompt of "
        f"{len(card.system)} characters, which would be present in every "
        f"generation and attributed to whatever is under test: "
        f"{card.system[:200]!r}. Build a bare tag with an empty SYSTEM line, or "
        f"pick a model whose card has none."
    )


def run(
    prompt: str,
    *,
    system_prompt: str,
    model: str,
    endpoint: Endpoint | None = None,
    temperature: float = 0.0,
    timeout: float = 900.0,
) -> CliResult:
    """Run one item against an OpenAI-compatible server.

    No ``cwd`` parameter, and its absence is the one real difference from
    :func:`~decision_evals.providers.claude_code.run`. That signature requires a
    working directory because the CLI discovers ``CLAUDE.md`` from it. Nothing
    here reads the filesystem, so there is no directory to get wrong -- but see
    the module docstring for the channel that replaces it, and call
    :func:`assert_isolated` on the model card before believing a run.

    The default timeout matches the CLI provider's. A 4B model on a laptop GPU
    is slower per token than a hosted frontier model, and a run that times out is
    scored as infrastructure failure rather than retried.
    """
    endpoint = endpoint or ollama()
    payload = build_payload(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        label=endpoint.label,
        temperature=temperature,
    )
    started = time.monotonic()
    response = _post(
        f"{endpoint.base_url}/chat/completions",
        payload,
        api_key=endpoint.api_key,
        timeout=timeout,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    return parse_completion(
        response,
        label=endpoint.label,
        duration_ms=duration_ms,
        cost_usd=endpoint.cost_usd,
    )


def preflight(*, model: str, endpoint: Endpoint | None = None) -> CliResult:
    """One throwaway call, to fail loudly before item 1 rather than during it.

    The same role as
    :func:`~decision_evals.providers.claude_code.preflight`, against a different
    failure. There is no credential to have been revoked; what goes wrong here is
    that the server is not running, or the tag was never pulled, and both are
    cheaper to discover now than 300 items in.
    """
    return run(
        "Reply with the word: ready",
        system_prompt="You are a test fixture. Reply with exactly the word requested.",
        model=model,
        endpoint=endpoint,
        timeout=120.0,
    )
