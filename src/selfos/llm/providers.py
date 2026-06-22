from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, cast

import httpx

from selfos.llm.models import LLMResponse


class BaseLLMProvider(ABC):
    name: str
    model: str

    def __init__(self, model: str, http_client: httpx.Client | Any | None = None) -> None:
        self.model = model
        self._http = http_client or httpx.Client(timeout=30.0)

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://127.0.0.1:11434",
        http_client: httpx.Client | Any | None = None,
    ) -> None:
        super().__init__(model=model, http_client=http_client)
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        try:
            response = self._http.get(f"{self.base_url}/api/tags")
            return response.status_code < 400
        except httpx.HTTPError:
            return False

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> LLMResponse:
        response = self._http.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )
        if response.status_code >= 400:
            raise ValueError(f"ollama request failed: {response.status_code}")
        payload = cast(dict[str, Any], response.json())
        return LLMResponse(
            content=str(payload.get("response", "")),
            input_tokens=int(payload.get("prompt_eval_count", self.count_tokens(prompt))),
            output_tokens=int(payload.get("eval_count", 0)),
            raw=payload,
        )


class OpenAIProvider(BaseLLMProvider):
    name = "openai"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        http_client: httpx.Client | Any | None = None,
    ) -> None:
        super().__init__(model=model, http_client=http_client)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> LLMResponse:
        response = self._http.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        if response.status_code >= 400:
            raise ValueError(f"openai request failed: {response.status_code}")
        payload = cast(dict[str, Any], response.json())
        choices = payload.get("choices", [])
        usage = payload.get("usage", {})
        content = choices[0]["message"]["content"] if choices else ""
        return LLMResponse(
            content=str(content),
            input_tokens=int(usage.get("prompt_tokens", self.count_tokens(prompt))),
            output_tokens=int(usage.get("completion_tokens", 0)),
            raw=payload,
        )


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-latest",
        api_key: str = "",
        base_url: str = "https://api.anthropic.com/v1",
        http_client: httpx.Client | Any | None = None,
    ) -> None:
        super().__init__(model=model, http_client=http_client)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> LLMResponse:
        response = self._http.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if response.status_code >= 400:
            raise ValueError(f"anthropic request failed: {response.status_code}")
        payload = cast(dict[str, Any], response.json())
        content_items = payload.get("content", [])
        usage = payload.get("usage", {})
        text = ""
        for item in content_items:
            if item.get("type") == "text":
                text = str(item.get("text", ""))
                break
        return LLMResponse(
            content=text,
            input_tokens=int(usage.get("input_tokens", self.count_tokens(prompt))),
            output_tokens=int(usage.get("output_tokens", 0)),
            raw=payload,
        )
