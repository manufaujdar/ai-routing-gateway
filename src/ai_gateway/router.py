from __future__ import annotations

from .council import CouncilPlanner
from .evaluator import Evaluator
from .handlers import Handler
from .models import GatewayRequest, GatewayResponse
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
        if self.model_selector is not None:
            decision = self.model_selector.select(request, decision)
        if self.council_planner is not None:
            decision = self.council_planner.plan(request, decision)
        if self.execution_planner is not None:
            decision = self.execution_planner.plan(request, decision)
        if not request.execute:
            return GatewayResponse(decision=decision)
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
