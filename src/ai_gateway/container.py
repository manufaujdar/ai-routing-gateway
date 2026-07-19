from __future__ import annotations

import os
from dataclasses import dataclass

from .evaluator import RoutingConfig, RuleBasedEvaluator
from .council import CouncilPlanner
from .council_handler import CouncilHandler, MockModelCaller, ModelCaller
from .handlers import BlockedHandler, MockHandler
from .registry import HandlerRegistry
from .router import Router
from .selector import ModelSelector, default_model_catalog


@dataclass(slots=True)
class GatewayContainer:
    router: Router
    registry: HandlerRegistry


def build_container(model_caller: ModelCaller | None = None) -> GatewayContainer:
    config = RoutingConfig(
        fast_model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4.1-mini"),
        reasoning_model=os.getenv("REASONING_LLM_MODEL", "o4-mini"),
    )
    registry = HandlerRegistry()
    registry.register("llm.fast", MockHandler("mock-llm"))
    registry.register("llm.reasoning", MockHandler("mock-reasoning-llm"))
    registry.register("llm.code", MockHandler("mock-code-llm"))
    registry.register("tool.web_search", MockHandler("mock-search"))
    registry.register("tool.vision", MockHandler("mock-vision"))
    registry.register("blocked", BlockedHandler())
    selector = ModelSelector(
        default_model_catalog(config.fast_model, config.reasoning_model, config.code_model)
    )
    return GatewayContainer(
        router=Router(
            RuleBasedEvaluator(config),
            registry,
            selector,
            CouncilPlanner(),
            CouncilHandler(model_caller or MockModelCaller()),
        ),
        registry=registry,
    )
