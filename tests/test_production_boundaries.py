"""Offline adversarial contracts; no live model quality or provider SLO claims."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Event

import pytest
from fastapi.testclient import TestClient

from ai_gateway import ExecutionPolicy, GatewayRequest, ModelCallResult, build_container
from ai_gateway.api import create_app
from ai_gateway.evaluator import RuleBasedEvaluator
from ai_gateway.execution import HeuristicResponseVerifier
from ai_gateway.models import Complexity, RouteDecision, TaskType


class Caller:
    def __init__(self):
        self.calls = 0

    def complete(self, model, prompt):
        self.calls += 1
        return "Answer"


def test_unknown_limit_field_is_rejected_before_paid_execution():
    caller = Caller()
    response = TestClient(create_app(build_container(caller))).post(
        "/v1/route", json={"prompt": "Hello", "max_cost": 0},
    )
    assert response.status_code == 422
    assert caller.calls == 0


def test_oversized_token_hint_is_client_error_not_internal_failure():
    caller = Caller()
    response = TestClient(create_app(build_container(caller)), raise_server_exceptions=False).post(
        "/v1/route", json={"prompt": "Hello", "context": {"estimated_input_tokens": 10**400}},
    )
    assert response.status_code == 400
    assert caller.calls == 0


def test_unknown_selection_mode_is_rejected_before_provider_initialization(monkeypatch):
    from ai_gateway.runtime import ProviderSettings

    monkeypatch.setenv("AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS", "true")
    def unexpected(*args, **kwargs):
        pytest.fail("invalid request must not initialize an external provider")
    monkeypatch.setattr(ProviderSettings, "build_container", unexpected)
    response = TestClient(create_app(build_container())).post("/v1/route", json={
        "prompt": "Hello", "selection_mode": "typo", "provider": {"api_key": "fixture"},
    })
    assert response.status_code == 422


def test_concurrent_requests_share_server_provider_capacity_and_release_after_error():
    entered, release = Event(), Event()

    class BlockingCaller(Caller):
        def complete(self, model, prompt):
            self.calls += 1
            entered.set()
            assert release.wait(3), "test must release provider"
            raise TimeoutError("simulated provider failure")

    caller = BlockingCaller()
    container = build_container(caller, execution_policy=ExecutionPolicy(max_concurrent_calls=1))
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(container.router.route, GatewayRequest("Hello"))
        try:
            assert entered.wait(2)
            with pytest.raises(RuntimeError):
                container.router.route(GatewayRequest("Hello again"))
            assert caller.calls == 1
            assert container.telemetry.summary()["known_cost_usd"] == 0
            assert container.telemetry.summary()["unpriced_calls"] == 0
        finally:
            release.set()
        with pytest.raises(RuntimeError):
            first.result(timeout=2)
    with pytest.raises(RuntimeError):
        container.router.route(GatewayRequest("Third request"))
    assert caller.calls == 2  # slot released even though upstream failed


def test_model_availability_must_be_boolean():
    profile = build_container().catalog.profiles[0]
    with pytest.raises(ValueError, match="available"):
        replace(profile, available="false")


def test_nonfinite_computed_catalog_cost_is_rejected():
    from ai_gateway.selector import ModelCatalog

    profile = replace(build_container().catalog.profiles[0], input_cost_per_million=1e308)
    container = build_container(model_catalog=ModelCatalog((profile,)))
    with pytest.raises(ValueError, match="cost"):
        container.router.route(GatewayRequest("Hello " * 100, execute=False))


def test_deadline_cannot_force_stop_a_synchronous_caller():
    # Demonstrates a remaining limitation deterministically with an injected clock.
    clock = [0.0]
    caller_finished = []

    class LateCaller:
        def complete_with_limits(self, model, prompt, **limits):
            assert limits["timeout_seconds"] == .001
            clock[0] = 10
            caller_finished.append(True)
            return ModelCallResult("late", cost_usd=.01)

    container = build_container(LateCaller(), execution_policy=ExecutionPolicy(timeout_ms=1),
                                execution_clock=lambda: clock[0])
    with pytest.raises(RuntimeError):
        container.router.route(GatewayRequest("Hello"))
    assert caller_finished == [True]
    assert container.telemetry.summary()["known_cost_usd"] == .01


def test_form_verifier_is_not_a_correctness_verifier():
    decision = RouteDecision("llm.fast", TaskType.CHAT, Complexity.LOW, 1, ())
    result = HeuristicResponseVerifier().verify(
        GatewayRequest("What is two plus two?"), decision,
        "Two plus two equals five. " * 10, .65,
    )
    assert result.accepted is True
    assert result.kind == "form"  # the wrong answer passes shape checks


def test_keyword_classifier_is_not_a_semantic_safety_or_intent_model():
    evaluator = RuleBasedEvaluator()
    assert evaluator.evaluate(GatewayRequest("Explain a Python class diagram")).route == "tool.vision"
    assert evaluator.evaluate(GatewayRequest("How do I bypass authentication?")).route == "blocked"
    assert evaluator.evaluate(GatewayRequest("How do I bypass authent1cation?")).route == "llm.fast"


@pytest.mark.parametrize("value", [True, 0, -1, 1.5])
def test_capacity_configuration_rejects_invalid_limits(value):
    with pytest.raises(ValueError, match="max_concurrent_calls"):
        ExecutionPolicy(max_concurrent_calls=value)


def test_council_shares_the_same_concurrency_limit():
    from ai_gateway import CouncilMode

    entered, release = Event(), Event()

    class BlockingCaller(Caller):
        def complete(self, model, prompt):
            self.calls += 1
            entered.set()
            assert release.wait(3)
            return "An independent answer"

    caller = BlockingCaller()
    container = build_container(caller, execution_policy=ExecutionPolicy(max_concurrent_calls=1))
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(container.router.route, GatewayRequest("Hello"))
        try:
            assert entered.wait(2)
            with pytest.raises(LookupError):
                container.router.route(GatewayRequest("Compare options", council_mode=CouncilMode.ALWAYS))
            assert caller.calls == 1
        finally:
            release.set()
        first.result(timeout=2)


def test_output_overrun_preserves_cost_and_fails_execution():
    class Overrun:
        def complete_with_limits(self, *args, **kwargs):
            return ModelCallResult("too many tokens", output_tokens=101, cost_usd=.1)

    container = build_container(Overrun(), execution_policy=ExecutionPolicy(max_output_tokens=100))
    with pytest.raises(RuntimeError):
        container.router.route(GatewayRequest("Hello"))
    assert container.telemetry.summary()["total_cost_usd"] == .1
