from dataclasses import replace

import pytest

from ai_gateway import GatewayRequest, ModelCallResult, build_container
from ai_gateway.budget import SQLiteBudgetLedger
from ai_gateway.controls import CircuitBreaker, CircuitOpen, ExecutionPolicy
from ai_gateway.models import CouncilMode, ExecutionStrategy


class BoundedCaller:
    def __init__(self, cost=.000010):
        self.calls = []
        self.cost = cost

    def complete_with_limits(self, model, prompt, *, timeout_seconds, max_output_tokens):
        self.calls.append((timeout_seconds, max_output_tokens))
        return ModelCallResult("A sufficient answer with supporting detail. " * 5, cost_usd=self.cost)


def budget_policy(tmp_path, **changes):
    ledger = SQLiteBudgetLedger(tmp_path / "budget.sqlite")
    ledger.configure_account("a", 100)
    return replace(ExecutionPolicy(
        ledger=ledger, account="a", max_output_tokens=100, max_prompt_bytes=10000,
        charge_limits={"configured-fast": 30, "configured-reasoning": 40, "configured-code": 40},
    ), **changes)


def test_execution_reserves_then_settles_actual_cost(tmp_path):
    policy = budget_policy(tmp_path)
    caller = BoundedCaller()
    response = build_container(caller, execution_policy=policy).router.route(GatewayRequest("Hello"))
    assert caller.calls == [(None, 100)]
    assert policy.ledger.snapshot("a")["spent_microusd"] == 10
    assert policy.ledger.snapshot("a")["reserved_microusd"] == 0
    assert response.metadata["execution_controls"]["reservations"]


def test_unknown_billing_stays_reserved_and_blocks_further_calls(tmp_path):
    policy = budget_policy(tmp_path)
    caller = BoundedCaller(cost=None)
    container = build_container(caller, execution_policy=policy)
    for _ in range(3):
        container.router.route(GatewayRequest("Hello"))
    with pytest.raises(RuntimeError):
        container.router.route(GatewayRequest("Hello"))
    assert len(caller.calls) == 3
    assert policy.ledger.snapshot("a")["reserved_microusd"] == 90


def test_operator_limit_cannot_be_relaxed_by_request(tmp_path):
    caller = BoundedCaller()
    container = build_container(caller, execution_policy=budget_policy(tmp_path))
    container.router.route(GatewayRequest("Hello", max_output_tokens=500))
    assert caller.calls[0][1] == 100


def test_budget_requires_adapter_capability_before_any_call(tmp_path):
    class UnsafeCaller:
        def complete(self, model, prompt):
            raise AssertionError("must not call")

    with pytest.raises(ValueError, match="complete_with_limits"):
        build_container(UnsafeCaller(), execution_policy=budget_policy(tmp_path)).router.route(
            GatewayRequest("Hello")
        )


def test_shared_deadline_stops_fallback_and_preserves_late_charge(tmp_path):
    clock = [0.0]

    class SlowCaller(BoundedCaller):
        def complete_with_limits(self, *args, **kwargs):
            result = super().complete_with_limits(*args, **kwargs)
            clock[0] = 2
            return result

    caller = SlowCaller()
    policy = budget_policy(tmp_path, timeout_ms=1000)
    container = build_container(caller, execution_policy=policy, execution_clock=lambda: clock[0])
    with pytest.raises(RuntimeError):
        container.router.route(GatewayRequest("Compare options",
            execution_strategy=ExecutionStrategy.CASCADE, council_mode=CouncilMode.NEVER))
    assert len(caller.calls) == 1
    assert caller.calls[0][0] == 1.0
    assert policy.ledger.snapshot("a")["spent_microusd"] == 10
    assert container.telemetry.summary()["known_cost_usd"] == .000010


def test_circuit_half_open_allows_only_one_probe_and_ignores_old_success():
    clock = [0]
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=5, clock=lambda: clock[0])
    first = breaker.acquire("d")
    old = breaker.acquire("d")
    breaker.finish("d", first, success=False)
    breaker.finish("d", old, success=True)
    with pytest.raises(CircuitOpen):
        breaker.acquire("d")
    clock[0] = 6
    probe = breaker.acquire("d")
    with pytest.raises(CircuitOpen):
        breaker.acquire("d")
    breaker.finish("d", probe, success=True)
    breaker.acquire("d")


def test_overcharge_stops_execution_and_preserves_observed_cost(tmp_path):
    policy = budget_policy(tmp_path)
    container = build_container(BoundedCaller(cost=.000120), execution_policy=policy)
    with pytest.raises(RuntimeError):
        container.router.route(GatewayRequest("Hello"))
    assert policy.ledger.snapshot("a")["breached"] is True
    assert policy.ledger.snapshot("a")["spent_microusd"] == 120
    assert container.telemetry.summary()["total_cost_usd"] == .000120


def test_parallel_samples_share_account_budget(tmp_path):
    policy = budget_policy(tmp_path)
    policy.ledger.configure_account("a", 50)
    caller = BoundedCaller(cost=None)
    response = build_container(caller, execution_policy=policy).router.route(GatewayRequest(
        "Compare options", execution_strategy=ExecutionStrategy.SELF_CONSISTENCY,
    ))
    assert len(caller.calls) == 1
    assert response.metadata["execution_controls"]["provider_calls"] == 1
    assert response.metadata["usage"]["calls"] == 3
    assert response.metadata["usage"]["unpriced_calls"] == 1
    assert policy.ledger.snapshot("a")["reserved_microusd"] == 40


def test_circuit_denial_releases_only_its_unspent_reservation(tmp_path):
    class FailedCaller(BoundedCaller):
        def complete_with_limits(self, *args, **kwargs):
            self.calls.append(1)
            raise TimeoutError("provider may have billed")

    policy = budget_policy(tmp_path)
    caller = FailedCaller()
    container = build_container(caller, execution_policy=policy,
                                circuit_breaker=CircuitBreaker(failure_threshold=1))
    for _ in range(2):
        with pytest.raises(RuntimeError):
            container.router.route(GatewayRequest("Hello", context={"request_id": "known-request"}))
    assert len(caller.calls) == 1
    assert policy.ledger.snapshot("a")["reserved_microusd"] == 30
    pending = policy.ledger.pending("a")
    assert len(pending) == 1 and pending[0]["request_id"] == "known-request"
    assert container.telemetry.summary()["unpriced_calls"] == 1


def test_prompt_and_tool_paths_cannot_bypass_server_controls(tmp_path):
    caller = BoundedCaller()
    policy = budget_policy(tmp_path, max_prompt_bytes=5)
    container = build_container(caller, execution_policy=policy)
    with pytest.raises(RuntimeError):
        container.router.route(GatewayRequest("Hello there"))
    with pytest.raises(ValueError, match="tool handlers"):
        container.router.route(GatewayRequest("Latest news"))
    assert caller.calls == []
    assert policy.ledger.snapshot("a")["reserved_microusd"] == 0


def test_server_call_limit_preflights_entire_plan():
    caller = BoundedCaller()
    container = build_container(caller, execution_policy=ExecutionPolicy(max_model_calls=1))
    with pytest.raises(ValueError, match="server max_model_calls"):
        container.router.route(GatewayRequest("Compare options", council_mode=CouncilMode.ALWAYS))
    assert caller.calls == []


def test_server_controls_require_an_explicit_caller():
    with pytest.raises(ValueError, match="model_caller"):
        build_container(execution_policy=ExecutionPolicy(timeout_ms=1000))
