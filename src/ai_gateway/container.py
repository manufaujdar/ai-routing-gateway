from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from .council import CouncilPlanner
from .council_handler import CouncilHandler, MockModelCaller, ModelCaller
from .evaluator import RoutingConfig, RuleBasedEvaluator
from .handlers import BlockedHandler, Handler, MockHandler, ModelHandler, UnavailableHandler
from .registry import HandlerRegistry
from .router import Router
from .selector import ModelCatalog, ModelSelector, default_model_catalog


@dataclass(slots=True)
class GatewayContainer:
    router: Router
    registry: HandlerRegistry
    catalog: ModelCatalog

    def capabilities(self) -> dict[str, object]:
        """Describe configured routes and model metadata without provider secrets."""

        return {
            "routes": list(self.registry.routes),
            "models": [
                {
                    "model": profile.model,
                    "provider": profile.provider,
                    "task_types": [task.value for task in profile.task_types],
                    "quality": profile.quality,
                    "latency_ms": profile.latency_ms,
                    "capabilities": list(profile.capabilities),
                    "available": profile.available,
                }
                for profile in self.catalog.profiles
            ],
        }


def build_container(
    model_caller: ModelCaller | None = None,
    *,
    routing_config: RoutingConfig | None = None,
    route_handlers: Mapping[str, Handler] | None = None,
    require_configured_tools: bool = False,
) -> GatewayContainer:
    config = routing_config or RoutingConfig(
        fast_model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4.1-mini"),
        reasoning_model=os.getenv("REASONING_LLM_MODEL", "o4-mini"),
        code_model=os.getenv("CODE_LLM_MODEL", "gpt-4.1"),
    )
    registry = HandlerRegistry()
    if model_caller is None:
        registry.register("llm.fast", MockHandler("mock-llm"))
        registry.register("llm.reasoning", MockHandler("mock-reasoning-llm"))
        registry.register("llm.code", MockHandler("mock-code-llm"))
        registry.register("tool.web_search", MockHandler("mock-search"))
        registry.register("tool.vision", MockHandler("mock-vision"))
    else:
        model_handler = ModelHandler(model_caller)
        registry.register("llm.fast", model_handler)
        registry.register("llm.reasoning", model_handler)
        registry.register("llm.code", model_handler)
        if require_configured_tools:
            registry.register("tool.web_search", UnavailableHandler("web search"))
            registry.register("tool.vision", UnavailableHandler("vision"))
        else:
            registry.register("tool.web_search", MockHandler("mock-search"))
            registry.register("tool.vision", MockHandler("mock-vision"))
    registry.register("blocked", BlockedHandler())
    for route, handler in (route_handlers or {}).items():
        registry.register(route, handler)
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
        catalog=selector.catalog,
    )
