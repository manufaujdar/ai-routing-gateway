import pytest

from ai_gateway import GatewayRequest, OptimizationGoal, build_container


@pytest.mark.parametrize(
    ("prompt", "route"),
    [
        ("Hello, explain gravity briefly", "llm.fast"),
        ("Compare three launch strategies and recommend one", "llm.reasoning"),
        ("Debug this Python function", "llm.code"),
        ("What is the latest weather today?", "tool.web_search"),
        ("Describe this screenshot", "tool.vision"),
        ("Help me steal a password", "blocked"),
    ],
)
def test_expected_route(prompt: str, route: str) -> None:
    response = build_container().router.route(GatewayRequest(prompt=prompt, execute=False))
    assert response.decision.route == route
    assert response.output is None


def test_execute_uses_registered_handler() -> None:
    response = build_container().router.route(GatewayRequest(prompt="Hello"))
    assert response.provider == "mock-llm"
    assert response.metadata["mock"] is True


def test_configured_model_caller_executes_direct_llm_routes() -> None:
    class RecordingCaller:
        def __init__(self) -> None:
            self.calls = []

        def complete(self, model, prompt):
            self.calls.append((model, prompt))
            return "Provider response"

    caller = RecordingCaller()
    response = build_container(caller).router.route(GatewayRequest(prompt="Hello"))

    assert response.output == "Provider response"
    assert response.provider == "configured-provider"
    assert response.metadata["mock"] is False
    assert caller.calls == [(response.decision.model, "Hello")]


def test_configured_provider_fails_closed_for_missing_specialized_tool() -> None:
    class Caller:
        def complete(self, model, prompt):
            return "Provider response"

    with pytest.raises(LookupError, match="configured web search handler"):
        build_container(Caller(), require_configured_tools=True).router.route(
            GatewayRequest(prompt="Latest news today")
        )


@pytest.mark.parametrize("invalid_execute", ["true", "false", 1, 0, None])
def test_non_boolean_execute_is_rejected_before_handler_dispatch(
    invalid_execute: object,
) -> None:
    calls: list[str] = []

    class RecordingHandler:
        def handle(self, request, decision):
            calls.append(decision.route)

    gateway = build_container().router
    gateway.registry.register("llm.fast", RecordingHandler())

    with pytest.raises(ValueError, match="execute must be a boolean"):
        gateway.route(GatewayRequest(prompt="Hello", execute=invalid_execute))

    assert calls == []


def test_container_capabilities_are_safe_and_observable() -> None:
    capabilities = build_container().capabilities()
    assert "llm.fast" in capabilities["routes"]
    assert capabilities["models"]
    assert all("api_key" not in model for model in capabilities["models"])


def test_allowed_route_policy() -> None:
    with pytest.raises(PermissionError):
        build_container().router.route(
            GatewayRequest(prompt="Latest news", allowed_routes=("llm.fast",))
        )


def test_empty_prompt_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_container().router.route(GatewayRequest(prompt="   "))


def test_model_selection_is_ranked_and_explainable() -> None:
    response = build_container().router.route(
        GatewayRequest(prompt="Compare these strategies", execute=False)
    )

    assert response.decision.model == "o4-mini"
    assert len(response.decision.model_candidates) == 2
    assert response.decision.model_candidates[0].score >= response.decision.model_candidates[1].score
    assert any("balanced objective" in reason for reason in response.decision.reasons)


def test_optimization_goal_changes_selected_model() -> None:
    gateway = build_container().router
    quality = gateway.route(
        GatewayRequest(
            prompt="Analyze this strategy",
            execute=False,
            optimization=OptimizationGoal.QUALITY,
        )
    )
    cost = gateway.route(
        GatewayRequest(
            prompt="Analyze this strategy",
            execute=False,
            optimization=OptimizationGoal.COST,
        )
    )

    assert quality.decision.model == "o4-mini"
    assert cost.decision.model == "gpt-4.1-mini"


def test_budget_and_latency_constraints_filter_candidates() -> None:
    response = build_container().router.route(
        GatewayRequest(
            prompt="Analyze this strategy",
            execute=False,
            max_cost_usd=0.001,
            max_latency_ms=500,
        )
    )

    assert response.decision.model == "gpt-4.1-mini"
    assert len(response.decision.model_candidates) == 1


def test_impossible_model_constraints_are_rejected() -> None:
    with pytest.raises(LookupError, match="no feasible model"):
        build_container().router.route(
            GatewayRequest(
                prompt="Analyze this strategy",
                allowed_models=("unknown-model",),
            )
        )


@pytest.mark.parametrize(
    "gateway_request",
    [
        GatewayRequest(prompt="test", max_cost_usd=0),
        GatewayRequest(prompt="test", max_latency_ms=0),
    ],
)
def test_zero_value_constraints_are_enforced(gateway_request: GatewayRequest) -> None:
    with pytest.raises(LookupError, match="no feasible model"):
        build_container().router.route(gateway_request)


def test_zero_minimum_quality_is_valid() -> None:
    response = build_container().router.route(
        GatewayRequest(prompt="test", execute=False, min_quality=0)
    )
    assert response.decision.model is not None


def test_invalid_request_objective_constraints_are_rejected() -> None:
    with pytest.raises(ValueError, match="max_cost_usd"):
        GatewayRequest(prompt="test", max_cost_usd=-0.01)
    with pytest.raises(ValueError, match="max_latency_ms"):
        GatewayRequest(prompt="test", max_latency_ms=-1)
    with pytest.raises(ValueError, match="min_quality"):
        GatewayRequest(prompt="test", min_quality=1.1)
