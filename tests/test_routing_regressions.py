from dataclasses import replace

import pytest

from ai_gateway import CallObservation, ExecutionStrategy, GatewayRequest, build_container
from ai_gateway.models import CouncilMode, TaskType
from ai_gateway.telemetry import InMemoryTelemetryStore, ModelCallResult

ANSWER = "Because there are several trade-offs, I recommend a measured rollout with clear " * 3


class Caller:
    def __init__(self, fail_first=False):
        self.calls = 0
        self.fail_first = fail_first

    def complete(self, model, prompt):
        return self.complete_with_metrics(model, prompt).text

    def complete_with_metrics(self, model, prompt):
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise TimeoutError("private provider detail")
        return ModelCallResult(text=ANSWER, deployment_id=model)


def test_cascade_recovers_provider_failure_and_accounts_for_every_attempt():
    caller = Caller(fail_first=True)
    container = build_container(caller)
    response = container.router.route(GatewayRequest(
        "Compare deployment strategies", execution_strategy=ExecutionStrategy.CASCADE,
        council_mode=CouncilMode.NEVER,
    ))
    assert response.output == ANSWER
    assert response.metadata["usage"]["calls"] == 2
    assert response.metadata["usage"]["cost_usd"] is None
    assert response.metadata["usage"]["unpriced_calls"] == 2
    observations = container.telemetry.observations
    assert len({item.request_id for item in observations}) == 1
    assert observations[0].deployment_id == "configured-fast"
    assert observations[1].deployment_id == "configured-reasoning"
    assert "private provider detail" not in str(response.to_dict())


def observation(request_id="r1", **changes):
    base = CallObservation(
        request_id=request_id, route="llm.fast", task_type=TaskType.CHAT,
        strategy=ExecutionStrategy.SINGLE, stage="single", model="m",
        provider="p", deployment_id="configured-fast", success=True,
        latency_ms=1, verifier_score=1,
    )
    return replace(base, **changes)


def test_form_checks_and_transport_success_are_not_accuracy_evidence():
    store = InMemoryTelemetryStore()
    for index in range(10):
        store.record(observation(str(index)))
    container = build_container(telemetry=store)
    assert container.optimizer.adjustment(container.catalog.profiles[0], TaskType.CHAT) == 0
    assert container.optimizer.propose().status == "insufficient_evidence"


def test_unknown_cost_is_not_zero_and_feedback_is_bounded():
    store = InMemoryTelemetryStore(max_observations=2)
    store.record(observation())
    with pytest.raises(ValueError):
        store.record_feedback("unknown", .8)
    store.record_feedback("r1", .3)
    store.record_feedback("r1", .9)
    aggregate = store.aggregates()[0]
    assert aggregate.average_feedback_score == .9
    assert store.summary()["total_cost_usd"] is None
    assert store.summary()["unpriced_calls"] == 1
    store.record(observation("r2"))
    store.record(observation("r3"))
    with pytest.raises(ValueError):
        store.record_feedback("r1", .9)


@pytest.mark.parametrize("field,value", [
    ("max_cost_usd", float("nan")), ("max_cost_usd", float("inf")),
    ("max_latency_ms", float("inf")), ("max_cost_usd", True),
    ("council_size", 2.5), ("strategy_model_limit", True),
])
def test_invalid_numeric_policy_is_rejected(field, value):
    with pytest.raises(ValueError):
        GatewayRequest("hello", **{field: value})


def test_council_accounts_for_all_calls_and_failure_fallback():
    caller = Caller(fail_first=True)
    container = build_container(caller)
    response = container.router.route(GatewayRequest(
        "Compare deployment strategies", council_mode=CouncilMode.ALWAYS,
    ))
    assert response.metadata["usage"]["calls"] == 2
    assert response.metadata["usage"]["cost_usd"] is None
    assert container.telemetry.summary()["failed_calls"] == 1
    assert len({item.request_id for item in container.telemetry.observations}) == 1


def test_call_limit_rejects_whole_plan_before_any_provider_call():
    caller = Caller()
    with pytest.raises(ValueError, match="max_model_calls"):
        build_container(caller).router.route(GatewayRequest(
            "Compare strategies", council_mode=CouncilMode.ALWAYS, max_model_calls=1,
        ))
    assert caller.calls == 0


def test_single_surviving_sample_does_not_count_as_majority():
    class PartialCaller:
        def complete(self, model, prompt):
            if "Candidate seed: 1." not in prompt:
                raise TimeoutError("failed sample")
            return ANSWER

    response = build_container(PartialCaller()).router.route(GatewayRequest(
        "Compare strategies", execution_strategy=ExecutionStrategy.SELF_CONSISTENCY,
    ))
    assert response.metadata["usage"]["calls"] == 3
    assert response.metadata["sample_count"] == 1
    assert response.metadata["consensus_reached"] is False
    assert response.metadata["aggregation_used"] is False


def test_feedback_only_updates_returned_attempt():
    store = InMemoryTelemetryStore()
    store.record(observation(stage="cascade_1", deployment_id="first"))
    store.record(observation(stage="cascade_2", deployment_id="returned"))
    store.mark_final("r1", "cascade_2")
    store.record_feedback("r1", .7)
    groups = {item.deployment_id: item for item in store.aggregates()}
    assert groups["first"].quality_samples == 0
    assert groups["returned"].average_quality_score == .7


def test_paid_empty_response_preserves_reported_cost():
    class EmptyCaller:
        def complete_with_metrics(self, model, prompt):
            return ModelCallResult(text="", cost_usd=.03, output_tokens=2)

    container = build_container(EmptyCaller())
    with pytest.raises(RuntimeError):
        container.router.route(GatewayRequest("Hello"))
    assert container.telemetry.summary()["total_cost_usd"] == .03
    assert container.telemetry.observations[0].output_tokens == 2


def test_invalid_api_numbers_and_unknown_feedback_are_client_errors():
    from fastapi.testclient import TestClient

    from ai_gateway.api import create_app

    client = TestClient(create_app(build_container()))
    invalid = client.post("/v1/route", content='{"prompt":"hello","max_cost_usd":NaN}',
                          headers={"content-type": "application/json"})
    assert invalid.status_code == 422
    assert "input" not in invalid.json()["detail"][0]
    assert client.post("/v1/feedback", json={"request_id": "unknown", "score": .8}).status_code == 400


def test_runtime_endpoints_have_distinct_deployment_identities(monkeypatch):
    from ai_gateway.runtime import ProviderSettings

    monkeypatch.setattr("ai_gateway.runtime.OpenAICompatibleModelCaller", lambda **kw: Caller())
    first = ProviderSettings("secret", base_url="https://first.example/v1").build_container()
    second = ProviderSettings("secret", base_url="https://second.example/v1").build_container()
    assert first.catalog.profiles[0].identity != second.catalog.profiles[0].identity
    assert "secret" not in repr(ProviderSettings("secret"))
