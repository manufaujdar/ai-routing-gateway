from fastapi.testclient import TestClient

from ai_gateway.api import app


def test_local_console_loads() -> None:
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "AI Routing Gateway console" in response.text
    assert "execute:false" in response.text


def test_console_route_contract_supports_decision_only() -> None:
    response = TestClient(app).post(
        "/v1/route",
        json={"prompt": "Write a Python function", "execute": False},
    )
    assert response.status_code == 200
    assert response.json()["decision"]["route"] == "llm.code"
