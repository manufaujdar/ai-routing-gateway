from __future__ import annotations

from fastapi.testclient import TestClient

from ai_gateway import (
    CallObservation,
    ExecutionStrategy,
    GatewayRequest,
    InMemoryTelemetryStore,
    ModelCallResult,
    build_container,
)
from ai_gateway.api import create_app
from ai_gateway.models import CouncilMode, TaskType


class SequencedCaller:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[str, str]] = []

    def complete_with_metrics(self, model: str, prompt: str) -> ModelCallResult:
        self.calls.append((model, prompt))
        output = self.outputs[min(len(self.calls) - 1, len(self.outputs) - 1)]
        return ModelCallResult(
            text=output,
            provider="test-provider",
            deployment_id=model,
            input_tokens=10,
            output_tokens=20,
            latency_ms=12,
            cost_usd=0.001,
        )

    def complete(self, model: str, prompt: str) -> str:
        return self.complete_with_metrics(model, prompt).text


def test_cascade_escalates_after_verification_rejects_first_response() -> None:
    caller = SequencedCaller(
        [
            "Too short",
            (
                "I recommend the second option because it balances reliability, operational "
                "cost, and latency while preserving a clear rollback path for the deployment."
            ),
        ]
    )
    container = build_container(caller)

    response = container.router.route(
        GatewayRequest(
            prompt="Compare deployment strategies and recommend one",
            execution_strategy=ExecutionStrategy.CASCADE,
            council_mode=CouncilMode.NEVER,
        )
    )

    assert response.metadata["strategy"] == "cascade"
    assert response.metadata["escalations"] == 1
    assert response.metadata["verification"]["accepted"] is True
    assert len(caller.calls) == 2
    assert container.telemetry.summary()["observation_count"] == 2


def test_self_consistency_returns_majority_without_aggregation() -> None:
    answer = "A consistent answer with enough supporting detail to pass the basic verifier."
    caller = SequencedCaller([answer])

    response = build_container(caller).router.route(
        GatewayRequest(
            prompt="Write a careful comparison",
            execution_strategy=ExecutionStrategy.SELF_CONSISTENCY,
            self_consistency_samples=3,
        )
    )

    assert response.output == answer
    assert response.metadata["sample_count"] == 3
    assert response.metadata["aggregation_used"] is False
    assert len(caller.calls) == 3


def test_telemetry_and_policy_endpoints_never_expose_prompt_content() -> None:
    telemetry = InMemoryTelemetryStore()
    telemetry.record(
        CallObservation(
            request_id="request-1",
            route="llm.fast",
            task_type=TaskType.CHAT,
            strategy=ExecutionStrategy.SINGLE,
            stage="single",
            model="fast-model",
            provider="provider",
            deployment_id="fast-deployment",
            success=True,
            latency_ms=80,
            cost_usd=0.001,
            verifier_score=0.9,
        )
    )
    client = TestClient(create_app(build_container(telemetry=telemetry)))

    summary = client.get("/v1/telemetry").json()
    proposal = client.get("/v1/policy/proposal").json()
    feedback = client.post(
        "/v1/feedback", json={"request_id": "request-1", "score": 0.8}
    )

    assert summary["observation_count"] == 1
    assert summary["privacy"] == "prompt and response content are not stored"
    assert "prompt" not in str(summary).lower().replace("prompt and response content", "")
    assert proposal["automatic_changes_applied"] is False
    assert proposal["status"] == "insufficient_evidence"
    assert feedback.status_code == 200


def test_decision_only_api_exposes_bounded_execution_plan() -> None:
    response = TestClient(create_app(build_container())).post(
        "/v1/route",
        json={
            "prompt": "Compare deployment strategies and recommend one",
            "execute": False,
            "execution_strategy": "cascade",
            "council_mode": "never",
        },
    )

    assert response.status_code == 200
    plan = response.json()["decision"]["execution_plan"]
    assert plan["strategy"] == "cascade"
    assert len(plan["model_sequence"]) >= 2
    assert plan["hard_budget_respected"] is True


def test_adaptive_agent_waits_for_evidence_then_emits_reviewable_proposal() -> None:
    telemetry = InMemoryTelemetryStore()
    container = build_container(telemetry=telemetry)
    fast_profile = next(
        profile for profile in container.catalog.profiles if profile.identity == "configured-fast"
    )
    assert container.optimizer.adjustment(fast_profile, TaskType.CHAT) == 0

    for index in range(5):
        telemetry.record(
            CallObservation(
                request_id=f"request-{index}",
                route="llm.fast",
                task_type=TaskType.CHAT,
                strategy=ExecutionStrategy.SINGLE,
                stage="single",
                model=fast_profile.model,
                provider=fast_profile.provider,
                deployment_id=fast_profile.identity,
                success=True,
                latency_ms=50,
                verifier_score=0.95,
            )
        )

    assert container.optimizer.adjustment(fast_profile, TaskType.CHAT) > 0
    proposal = container.optimizer.propose()
    assert proposal.status == "ready_for_offline_evaluation"
    assert proposal.automatic_changes_applied is False
    assert proposal.recommendations[0]["preferred_deployment"] == "configured-fast"
