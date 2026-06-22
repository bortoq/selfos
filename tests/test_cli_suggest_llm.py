from __future__ import annotations

from pathlib import Path

import pytest

from selfos.cli import main


class FakeEngine:
    def __init__(self) -> None:
        self.rated: tuple[str, int] | None = None
        self.approved: str | None = None
        self.cache_cleared = False

    def get_suggestions(
        self,
        mode: str = "rules",
        provider: str | None = None,
    ) -> dict[str, object]:
        backend = "rules_fallback" if mode == "llm" else "rules"
        return {
            "backend_requested": mode,
            "backend_used": backend,
            "fallback_reason": "provider_unavailable" if mode == "llm" else None,
            "suggestions": [
                {
                    "id": "s1",
                    "title": "Review inbox",
                    "summary": "There are unread emails",
                    "backend_used": backend,
                    "confidence": 0.8,
                }
            ],
            "usage": {},
        }

    def approve_suggestion(self, suggestion_id: str) -> dict[str, object]:
        self.approved = suggestion_id
        return {"status": "approved", "suggestion_id": suggestion_id}

    def rate_suggestion(self, suggestion_id: str, rating: int) -> None:
        self.rated = (suggestion_id, rating)

    def get_stats(self) -> dict[str, object]:
        return {"requests": 1, "fallbacks": 1}

    def clear_cache(self) -> None:
        self.cache_cleared = True


@pytest.fixture
def isolated_llm_config(monkeypatch, tmp_path: Path) -> Path:
    config_path = tmp_path / "selfos.yaml"
    monkeypatch.setattr("selfos.config.config_file", lambda: config_path)
    return config_path


def test_cli_suggest_llm_falls_back_to_rules(monkeypatch, capsys) -> None:
    monkeypatch.setattr("selfos.cli._create_suggestion_engine", lambda: FakeEngine())
    main(["suggest", "--llm"])
    captured = capsys.readouterr()
    assert "fallback" in captured.out.lower()


def test_cli_suggest_approve_rate_stats_and_clear_cache(monkeypatch, capsys) -> None:
    engine = FakeEngine()
    monkeypatch.setattr("selfos.cli._create_suggestion_engine", lambda: engine)
    main(["suggest", "--approve", "s1"])
    main(["suggest", "--rate", "s1", "5"])
    main(["suggest", "--stats"])
    main(["suggest", "--clear-cache"])
    captured = capsys.readouterr()
    assert engine.approved == "s1"
    assert engine.rated == ("s1", 5)
    assert engine.cache_cleared is True
    assert "requests" in captured.out.lower()


def test_cli_config_llm_openai_prompts_for_cloud_opt_in(
    monkeypatch,
    capsys,
    isolated_llm_config: Path,
) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    main(["config", "llm", "--provider", "openai", "--api-key", "secret"])
    captured = capsys.readouterr()
    assert '"provider": "openai"' in captured.out
    assert '"cloud_opt_in": true' in captured.out.lower()
    assert "cloud_opt_in: true" in isolated_llm_config.read_text(encoding="utf-8")


def test_cli_config_llm_openai_rejects_without_cloud_opt_in(
    monkeypatch,
    isolated_llm_config: Path,
) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    with pytest.raises(SystemExit) as exc_info:
        main(["config", "llm", "--provider", "openai", "--api-key", "secret"])
    assert exc_info.value.code == 1
    assert not isolated_llm_config.exists()
