from __future__ import annotations

from dataclasses import replace

from .council import CouncilPlanner
from .evaluator import Evaluator
from .handlers import Handler
from .models import CouncilMode, ExecutionStrategy, GatewayRequest, GatewayResponse
from .registry import HandlerRegistry
from .selector import ModelSelector
from .strategy import ExecutionPlanner


class Router:
    def __init__(
        self,
        evaluator: Evaluator,
        registry: HandlerRegistry,
        model_selector: ModelSelector | None = None,
        council_planner: CouncilPlanner | None = None,
        council_handler: Handler | None = None,
        execution_planner: ExecutionPlanner | None = None,
        strategy_handler: Handler | None = None,
    ) -> None:
        self.evaluator = evaluator
        self.registry = registry
        self.model_selector = model_selector
        self.council_planner = council_planner
        self.council_handler = council_handler
        self.execution_planner = execution_planner
        self.strategy_handler = strategy_handler

    def route(self, request: GatewayRequest) -> GatewayResponse:
        decision = self.evaluator.evaluate(request)
        if (request.selection_mode == "evidence" and self.model_selector is None
                and decision.route != "blocked"):
            raise ValueError("evidence selection requires a configured model selector")
        if self.model_selector is not None:
            decision = self.model_selector.select(request, decision)
        if decision.selection_receipt.get("status") == "abstained":
            return GatewayResponse(decision=decision, metadata={"abstained": True})
        if request.selection_mode == "evidence" and decision.route != "blocked":
            if (request.execution_strategy not in (ExecutionStrategy.AUTO, ExecutionStrategy.SINGLE)
                    or request.council_mode is CouncilMode.ALWAYS):
                raise ValueError("evidence policy currently validates single-model execution only")
            if decision.tools:
                raise ValueError("evidence policy does not certify application-supplied tool handlers")
            request = replace(request, execution_strategy=ExecutionStrategy.SINGLE,
                              council_mode=CouncilMode.NEVER)
        if self.council_planner is not None:
            decision = self.council_planner.plan(request, decision)
        if self.execution_planner is not None:
            decision = self.execution_planner.plan(request, decision)
        plan = decision.execution_plan
        if plan is not None and decision.route.startswith("llm."):
            calls = (2 * plan.sample_count + 1 if plan.strategy is ExecutionStrategy.COUNCIL
                     else plan.sample_count + 1 if plan.strategy is ExecutionStrategy.SELF_CONSISTENCY
                     else len(plan.model_sequence))
            if calls > request.max_model_calls:
                raise ValueError(f"execution plan requires up to {calls} model calls; "
                                 f"max_model_calls is {request.max_model_calls}")
        if not request.execute:
            return GatewayResponse(decision=decision)
        if decision.tools and (
            request.execution_timeout_ms is not None or request.max_output_tokens is not None
            or getattr(self.strategy_handler, "enforce_controls", False)
        ):
            raise ValueError("execution controls require a direct LLM route; tool handlers are not covered")
        if decision.council_plan is not None and decision.council_plan.enabled:
            if self.council_handler is None:
                raise LookupError("council was selected but no council handler is configured")
            return self.council_handler.handle(request, decision)
        if (
            self.strategy_handler is not None
            and decision.execution_plan is not None
            and decision.route.startswith("llm.")
        ):
            return self.strategy_handler.handle(request, decision)
        return self.registry.get(decision.route).handle(request, decision)
