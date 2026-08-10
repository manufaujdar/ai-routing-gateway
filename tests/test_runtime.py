from __future__ import annotations

import pytest

from ai_gateway.runtime import ProviderSettings, settings_from_environment


def test_environment_settings_are_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert settings_from_environment() is None


def test_environment_settings_use_documented_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "test-key")
    monkeypatch.setenv("AI_GATEWAY_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("DEFAULT_LLM_MODEL", "fast-model")
    monkeypatch.setenv("REASONING_LLM_MODEL", "reasoning-model")
    monkeypatch.setenv("CODE_LLM_MODEL", "code-model")

    settings = settings_from_environment()

    assert settings is not None
    assert settings.api_key == "test-key"
    assert settings.base_url == "https://gateway.example/v1"
    assert settings.code_model == "code-model"


@pytest.mark.parametrize("model", ["", " leading", "trailing ", "two words"])
def test_provider_model_identifiers_are_strict(model: str) -> None:
    with pytest.raises(ValueError, match="model identifier"):
        ProviderSettings(api_key="test", fast_model=model)


def test_provider_timeout_is_bounded() -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        ProviderSettings(api_key="test", timeout_seconds=301)
