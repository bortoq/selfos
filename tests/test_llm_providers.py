from __future__ import annotations

import httpx

from selfos.llm.providers import AnthropicProvider, OllamaProvider, OpenAIProvider


class FakeHTTPClient:
    def __init__(
        self,
        responses: list[httpx.Response] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.responses = responses or []
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def get(self, url: str, **kwargs: object) -> httpx.Response:
        self.calls.append(("GET", url))
        if self.error:
            raise self.error
        return self.responses.pop(0)

    def post(self, url: str, **kwargs: object) -> httpx.Response:
        self.calls.append(("POST", url))
        if self.error:
            raise self.error
        return self.responses.pop(0)


def test_ollama_provider_reports_unavailable_on_http_error() -> None:
    provider = OllamaProvider(http_client=FakeHTTPClient(error=httpx.ConnectError("down")))
    assert provider.is_available() is False


def test_ollama_provider_complete_parses_response() -> None:
    provider = OllamaProvider(
        model="llama3.2",
        http_client=FakeHTTPClient(
            responses=[
                httpx.Response(
                    200,
                    json={
                        "response": "{\"suggestions\": []}",
                        "prompt_eval_count": 12,
                        "eval_count": 8,
                    },
                ),
            ]
        ),
    )
    response = provider.complete("hello")
    assert response.content == "{\"suggestions\": []}"
    assert response.input_tokens == 12
    assert response.output_tokens == 8


def test_openai_provider_requires_api_key_for_availability() -> None:
    provider = OpenAIProvider(api_key="")
    assert provider.is_available() is False


def test_openai_provider_complete_reads_chat_response() -> None:
    provider = OpenAIProvider(
        api_key="secret",
        http_client=FakeHTTPClient(
            responses=[
                httpx.Response(
                    200,
                    json={
                        "choices": [{"message": {"content": "{\"suggestions\": []}"}}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 6},
                    },
                )
            ]
        ),
    )
    response = provider.complete("hello")
    assert response.content == "{\"suggestions\": []}"
    assert response.input_tokens == 10
    assert response.output_tokens == 6


def test_anthropic_provider_complete_reads_message_response() -> None:
    provider = AnthropicProvider(
        api_key="secret",
        http_client=FakeHTTPClient(
            responses=[
                httpx.Response(
                    200,
                    json={
                        "content": [{"type": "text", "text": "{\"suggestions\": []}"}],
                        "usage": {"input_tokens": 11, "output_tokens": 5},
                    },
                )
            ]
        ),
    )
    response = provider.complete("hello")
    assert response.content == "{\"suggestions\": []}"
    assert response.input_tokens == 11
    assert response.output_tokens == 5
