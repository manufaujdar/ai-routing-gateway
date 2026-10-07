import pytest
from fastapi.testclient import TestClient

from ai_gateway import GatewayRequest, build_container
from ai_gateway.api import create_app


def test_tenant_access_protects_routes_telemetry_feedback_and_documentation():
    first, second = build_container(), build_container()
    client = TestClient(create_app(tenants={"first-secret": first, "second-secret": second}))
    assert client.get("/health").status_code == 200
    for path in ("/", "/ready", "/docs", "/redoc", "/docs/oauth2-redirect", "/openapi.json",
                 "/assets/app.js", "/assets/styles.css", "/v1/telemetry", "/v1/capabilities",
                 "/v1/config", "/v1/policy/proposal"):
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"Authorization": "Bearer first-secret"}).status_code == 200
    assert client.post("/v1/route", json={"prompt": "Hello"}).status_code == 401
    assert client.post("/v1/feedback", json={"request_id": "unknown", "score": 1}).status_code == 401
    headers = {"Authorization": "Bearer first-secret"}
    assert client.get("/openapi.json", headers=headers).status_code == 200
    assert client.get("/ready", headers={"Authorization": "Bearer wrong"}).status_code == 401
    response = client.post("/v1/route", headers=headers, json={"prompt": "Hello", "execute": False})
    assert response.status_code == 200
    assert "first-secret" not in response.text
    assert client.get("/v1/config", headers=headers).json()["runtime_credentials_allowed"] is False


def test_feedback_and_telemetry_cannot_cross_tenant_boundary():
    class Caller:
        def complete(self, model, prompt):
            return "A response"

    first, second = build_container(Caller()), build_container(Caller())
    response = first.router.route(GatewayRequest("Hello"))
    request_id = response.metadata["request_id"]
    client = TestClient(create_app(tenants={"first-secret": first, "second-secret": second}))
    headers = {"Authorization": "Bearer second-secret"}
    assert client.get("/v1/telemetry", headers=headers).json()["observation_count"] == 0
    assert client.post("/v1/feedback", headers=headers,
                       json={"request_id": request_id, "score": 1}).status_code == 400
    assert client.post("/v1/feedback", headers={"Authorization": "Bearer first-secret"},
                       json={"request_id": request_id, "score": 1}).status_code == 200


def test_authenticated_clients_cannot_replace_server_provider(monkeypatch):
    monkeypatch.setenv("AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS", "true")
    client = TestClient(create_app(tenants={"first-secret": build_container()}))
    response = client.post("/v1/route", headers={"Authorization": "Bearer first-secret"},
                           json={"prompt": "Hello", "provider": {"api_key": "untrusted"}})
    assert response.status_code == 400
    assert "untrusted" not in response.text


def test_tenant_mode_refuses_shared_telemetry_and_empty_configuration():
    container = build_container()
    with pytest.raises(ValueError, match="isolated"):
        create_app(tenants={"one": container, "two": container})
    with pytest.raises(ValueError):
        create_app(tenants={})


def test_runtime_override_cannot_bypass_limits_in_local_mode(monkeypatch):
    from ai_gateway.controls import ExecutionPolicy

    class Caller:
        def complete(self, model, prompt):
            raise AssertionError("must not execute")

    monkeypatch.setenv("AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS", "true")
    client = TestClient(create_app(build_container(Caller(), execution_policy=ExecutionPolicy(
        timeout_ms=1000,
    ))))
    assert client.get("/v1/config").json()["runtime_credentials_allowed"] is False
    response = client.post("/v1/route", json={"prompt": "Hello", "provider": {"api_key": "new-key"}})
    assert response.status_code == 400
    assert "cannot bypass" in response.json()["detail"]["message"]


def test_tenants_cannot_share_budget_account_through_a_symlink(tmp_path):
    from ai_gateway import ExecutionPolicy, SQLiteBudgetLedger

    class Caller:
        def complete(self, model, prompt):
            raise AssertionError("must not execute")

    original = SQLiteBudgetLedger(tmp_path / "budget.sqlite")
    alias = tmp_path / "alias.sqlite"
    alias.symlink_to(original.path)
    linked = SQLiteBudgetLedger(alias)

    def container(ledger):
        return build_container(Caller(), execution_policy=ExecutionPolicy(
            ledger=ledger, account="shared", charge_limits={"configured-fast": 30},
            max_output_tokens=10, max_prompt_bytes=100,
        ))

    with pytest.raises(ValueError, match="share a budget account"):
        create_app(tenants={"one": container(original), "two": container(linked)})
