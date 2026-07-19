import pytest

from ai_gateway import (
    CouncilMode,
    CouncilRequirementError,
    GatewayRequest,
    OptimizationGoal,
    build_container,
)
from ai_gateway.council_handler import aggregate_rankings, parse_complete_ranking


class RecordingCaller:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, model: str, prompt: str) -> str:
        self.prompts.append(prompt)
        if prompt.startswith("[COUNCIL_STAGE:review]"):
            return "FINAL RANKING:\n1. Candidate A\n2. Candidate B"
        if prompt.startswith("[COUNCIL_STAGE:synthesis]"):
            return "anonymous synthesis"
        return "independent answer"


class OneMemberFailureCaller(RecordingCaller):
    def complete(self, model: str, prompt: str) -> str:
        if model == "gpt-4.1-mini":
            raise RuntimeError("provider failed")
        return super().complete(model, prompt)


def test_auto_council_stays_off_for_ordinary_reasoning() -> None:
    response = build_container().router.route(
        GatewayRequest(prompt="Compare three launch strategies", execute=False)
    )

    assert response.decision.council_plan is not None
    assert response.decision.council_plan.enabled is False
    assert "below" in response.decision.council_plan.reason


def test_auto_council_activates_for_high_complexity_reasoning() -> None:
    prompt = "Analyze this difficult decision carefully. " + "constraint " * 125
    response = build_container().router.route(GatewayRequest(prompt=prompt, execute=False))

    plan = response.decision.council_plan
    assert plan is not None
    assert plan.enabled is True
    assert plan.member_models == ("o4-mini", "gpt-4.1-mini")
    assert plan.chairman_model == "o4-mini"
    assert plan.stages == (
        "independent_answers",
        "blind_peer_review",
        "chairman_synthesis",
    )


@pytest.mark.parametrize(
    "context",
    [{"stakes": "high"}, {"requires_consensus": True}],
)
def test_application_signals_can_activate_auto_council(context: dict[str, object]) -> None:
    response = build_container().router.route(
        GatewayRequest(prompt="Analyze the available options", context=context, execute=False)
    )
    assert response.decision.council_plan is not None
    assert response.decision.council_plan.enabled is True


def test_cost_objective_avoids_automatic_council() -> None:
    prompt = "Analyze this difficult decision carefully. " + "constraint " * 125
    response = build_container().router.route(
        GatewayRequest(
            prompt=prompt,
            execute=False,
            optimization=OptimizationGoal.COST,
        )
    )
    assert response.decision.council_plan is not None
    assert response.decision.council_plan.enabled is False


def test_auto_council_is_disabled_when_hard_cost_budget_is_requested() -> None:
    gateway = build_container().router
    budget = gateway.route(
        GatewayRequest(
            prompt="Analyze this high-stakes decision with multiple perspectives",
            execute=False,
            max_cost_usd=0.05,
        )
    )

    assert budget.decision.council_plan is not None
    assert budget.decision.council_plan.enabled is False
    assert "without usage metering" in budget.decision.council_plan.reason


def test_always_council_rejects_hard_cost_budget_without_runtime_metering() -> None:
    with pytest.raises(CouncilRequirementError, match="without runtime usage metering"):
        GatewayRequest(
            prompt="Analyze the options",
            council_mode=CouncilMode.ALWAYS,
            max_cost_usd=0.05,
        )


def test_always_council_rejects_unsatisfied_latency_requirement() -> None:
    gateway = build_container().router

    with pytest.raises(CouncilRequirementError, match="end-to-end latency limit"):
        gateway.route(
            GatewayRequest(
                prompt="Analyze the options",
                execute=False,
                council_mode=CouncilMode.ALWAYS,
                max_latency_ms=2_000,
            )
        )


def test_always_council_rejects_insufficient_members() -> None:
    gateway = build_container().router

    with pytest.raises(CouncilRequirementError, match="at least two feasible models"):
        gateway.route(
            GatewayRequest(
                prompt="Analyze the options",
                execute=False,
                council_mode=CouncilMode.ALWAYS,
                allowed_models=("o4-mini",),
            )
        )


@pytest.mark.parametrize(
    ("prompt", "expected_provider"),
    [
        ("What is the latest weather today?", "mock-search"),
        ("Describe this screenshot", "mock-vision"),
    ],
)
def test_auto_council_does_not_bypass_tool_routes(
    prompt: str, expected_provider: str
) -> None:
    caller = RecordingCaller()
    response = build_container(model_caller=caller).router.route(GatewayRequest(prompt=prompt))

    assert response.provider == expected_provider
    assert response.decision.council_plan is not None
    assert response.decision.council_plan.enabled is False
    assert "direct LLM routes" in response.decision.council_plan.reason
    assert caller.prompts == []


def test_always_council_rejects_tool_routes_instead_of_bypassing_handler() -> None:
    caller = RecordingCaller()
    gateway = build_container(model_caller=caller).router

    with pytest.raises(CouncilRequirementError, match="direct LLM routes"):
        gateway.route(
            GatewayRequest(
                prompt="What is the latest weather today?",
                council_mode=CouncilMode.ALWAYS,
            )
        )

    assert caller.prompts == []


def test_never_mode_overrides_auto_signals() -> None:
    response = build_container().router.route(
        GatewayRequest(
            prompt="Analyze this high-stakes decision with multiple perspectives",
            execute=False,
            council_mode=CouncilMode.NEVER,
        )
    )
    assert response.decision.council_plan is not None
    assert response.decision.council_plan.enabled is False


def test_enabled_council_executes_all_three_stages_offline() -> None:
    response = build_container().router.route(
        GatewayRequest(
            prompt="Analyze the options",
            council_mode=CouncilMode.ALWAYS,
        )
    )

    council = response.metadata["council"]
    assert response.provider == "llm-council"
    assert response.output == "Council synthesis generated by o4-mini."
    assert len(council["stage1"]) == 2
    assert len(council["stage2"]) == 2
    assert len(council["aggregate_rankings"]) == 2
    assert set(council["label_to_model"]) == {"Candidate A", "Candidate B"}
    assert council["fallback_used"] is None


def test_chairman_synthesis_keeps_model_identities_anonymous() -> None:
    caller = RecordingCaller()
    response = build_container(model_caller=caller).router.route(
        GatewayRequest(prompt="Analyze the options", council_mode=CouncilMode.ALWAYS)
    )
    synthesis_prompt = next(
        prompt for prompt in caller.prompts if prompt.startswith("[COUNCIL_STAGE:synthesis]")
    )

    assert response.output == "anonymous synthesis"
    assert "o4-mini" not in synthesis_prompt
    assert "gpt-4.1-mini" not in synthesis_prompt
    assert "Candidate A" in synthesis_prompt


def test_council_degrades_to_single_successful_member() -> None:
    response = build_container(model_caller=OneMemberFailureCaller()).router.route(
        GatewayRequest(prompt="Analyze the options", council_mode=CouncilMode.ALWAYS)
    )
    council = response.metadata["council"]

    assert response.provider == "llm-council-degraded"
    assert response.output == "independent answer"
    assert council["fallback_used"] == "only_one_member_succeeded"
    assert council["stage2"] == ()


def test_ranking_parser_rejects_partial_or_duplicate_ballots() -> None:
    labels = ("Candidate A", "Candidate B")
    valid = "Review\nFINAL RANKING:\n1. Candidate B\n2. Candidate A"
    partial = "FINAL RANKING:\n1. Candidate A"
    duplicate = "FINAL RANKING:\n1. Candidate A\n2. Candidate A"

    assert parse_complete_ranking(valid, labels) == ("Candidate B", "Candidate A")
    assert parse_complete_ranking(partial, labels) == ()
    assert parse_complete_ranking(duplicate, labels) == ()


def test_aggregate_rankings_use_only_valid_complete_ballots() -> None:
    aggregate = aggregate_rankings(
        [("Candidate B", "Candidate A"), ("Candidate A", "Candidate B")],
        {"Candidate A": "model-a", "Candidate B": "model-b"},
    )
    assert aggregate == (
        {"model": "model-a", "average_rank": 1.5, "valid_votes": 2},
        {"model": "model-b", "average_rank": 1.5, "valid_votes": 2},
    )


def test_council_request_validation() -> None:
    with pytest.raises(ValueError, match="council_size"):
        GatewayRequest(prompt="test", council_size=1)
