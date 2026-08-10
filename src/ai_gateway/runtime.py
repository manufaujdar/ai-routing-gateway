from __future__ import annotations

import os
from dataclasses import dataclass

from .adapters import OpenAICompatibleModelCaller
from .container import GatewayContainer, build_container
from .evaluator import RoutingConfig
from .telemetry import InMemoryTelemetryStore


@dataclass(frozen=True, slots=True)
class ProviderSettings:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    fast_model: str = "gpt-4.1-mini"
    reasoning_model: str = "o4-mini"
    code_model: str = "gpt-4.1"
    timeout_seconds: float = 120.0
    allow_insecure_loopback: bool = False

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("api_key must not be empty")
        for name in ("fast_model", "reasoning_model", "code_model"):
            value = getattr(self, name)
            if not value or value.strip() != value or any(character.isspace() for character in value):
                raise ValueError(f"{name} must be a non-empty model identifier without whitespace")
        if not 0 < self.timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be greater than 0 and at most 300")

    def build_container(
        self, telemetry: InMemoryTelemetryStore | None = None
    ) -> GatewayContainer:
        caller = OpenAICompatibleModelCaller(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            allow_insecure_loopback=self.allow_insecure_loopback,
        )
        return build_container(
            caller,
            routing_config=RoutingConfig(
                fast_model=self.fast_model,
                reasoning_model=self.reasoning_model,
                code_model=self.code_model,
            ),
            require_configured_tools=True,
            telemetry=telemetry,
        )


def settings_from_environment() -> ProviderSettings | None:
    api_key = os.getenv("AI_GATEWAY_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return ProviderSettings(
        api_key=api_key,
        base_url=os.getenv("AI_GATEWAY_BASE_URL", "https://api.openai.com/v1"),
        fast_model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4.1-mini"),
        reasoning_model=os.getenv("REASONING_LLM_MODEL", "o4-mini"),
        code_model=os.getenv("CODE_LLM_MODEL", "gpt-4.1"),
        timeout_seconds=float(os.getenv("AI_GATEWAY_TIMEOUT_SECONDS", "120")),
        allow_insecure_loopback=_strict_environment_boolean(
            "AI_GATEWAY_ALLOW_INSECURE_LOOPBACK", False
        ),
    )


def runtime_credentials_allowed() -> bool:
    return _strict_environment_boolean("AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS", False)


def _strict_environment_boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")
