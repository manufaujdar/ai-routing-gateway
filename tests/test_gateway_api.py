from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

from fastapi.testclient import TestClient

from ai_gateway.api import app, create_app
from ai_gateway.container import build_container
from ai_gateway.models import GatewayResponse


def test_local_console_and_assets_load() -> None:
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "AI Routing Gateway" in response.text
    assert "Provider connection" in response.text
    assert client.get("/assets/styles.css").status_code == 200
    javascript = client.get("/assets/app.js")
    assert javascript.status_code == 200
    assert "innerHTML" not in javascript.text


def test_health_readiness_and_configuration_are_safe() -> None:
    client = TestClient(app)

    assert client.get("/health").json()["status"] == "ok"
    readiness = client.get("/ready").json()
    assert readiness["status"] == "ready"
    configuration = client.get("/v1/config").json()
    assert configuration["credentials_stored"] is False
    assert "api_key" not in configuration


def test_console_route_contract_supports_decision_only() -> None:
    response = TestClient(app).post(
        "/v1/route",
        json={"prompt": "Write a Python function", "execute": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["route"] == "llm.code"
    assert body["output"] is None
    assert len(body["request"]["id"]) == 32
    assert body["request"]["elapsed_ms"] >= 0


def test_runtime_credentials_are_rejected_by_default(monkeypatch) -> None:
    monkeypatch.delenv("AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS", raising=False)
    client = TestClient(create_app())
    secret = "must-not-appear-in-response"

    response = client.post(
        "/v1/route",
        json={
            "prompt": "Hello",
            "execute": True,
            "provider": {"api_key": secret},
        },
    )

    assert response.status_code == 400
    assert "runtime provider credentials are disabled" in response.text
    assert secret not in response.text


def test_enabled_runtime_provider_executes_without_storing_secret(monkeypatch) -> None:
    secret = "runtime-test-secret"
    module = ModuleType("openai")

    class FakeOpenAI:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == secret
            completion = SimpleNamespace(
                create=lambda **_kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="Live response"))]
                )
            )
            self.chat = SimpleNamespace(completions=completion)

    module.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", module)
    monkeypatch.setenv("AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS", "true")
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(create_app())

    response = client.post(
        "/v1/route",
        json={
            "prompt": "Hello",
            "execute": True,
            "council_mode": "never",
            "provider": {"api_key": secret},
        },
    )

    assert response.status_code == 200
    assert response.json()["output"] == "Live response"
    assert response.json()["metadata"]["mock"] is False
    assert secret not in response.text
    assert client.get("/v1/config").json()["credentials_stored"] is False


def test_custom_container_can_supply_a_specialized_tool_handler(monkeypatch) -> None:
    class SearchHandler:
        def handle(self, request, decision):
            return GatewayResponse(
                decision=decision,
                output="Sanitized search result",
                provider="test-search",
            )

    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    custom = build_container(route_handlers={"tool.web_search": SearchHandler()})
    client = TestClient(create_app(custom))

    response = client.post(
        "/v1/route",
        json={"prompt": "Latest news today", "execute": True},
    )

    assert response.status_code == 200
    assert response.json()["output"] == "Sanitized search result"
    assert client.get("/v1/config").json()["execution_mode"] == "custom_container"
