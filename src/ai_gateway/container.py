from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .controls import CircuitBreaker, ControlledExecutionHandler, ExecutionPolicy
from .council import CouncilPlanner
from .council_handler import CouncilHandler, MockModelCaller, ModelCaller
from .evaluator import RoutingConfig, RuleBasedEvaluator
from .evidence import EvidencePolicy
from .execution import ResponseVerifier
from .handlers import BlockedHandler, Handler, MockHandler, ModelHandler, UnavailableHandler
from .optimization import AdaptiveRoutingAgent
from .registry import HandlerRegistry
from .router import Router
from .selector import ModelCatalog, ModelSelector, default_model_catalog
from .strategy import ExecutionPlanner
from .telemetry import InMemoryTelemetryStore


@dataclass(slots=True)
class GatewayContainer:
    router: Router
    registry: HandlerRegistry
    catalog: ModelCatalog
    telemetry: InMemoryTelemetryStore
    optimizer: AdaptiveRoutingAgent

    def capabilities(self) -> dict[str, object]:
        """Describe configured routes and model metadata without provider secrets."""

        return {
            "routes": list(self.registry.routes),
            "models": [
                {
                    "model": profile.model,
                    "provider": profile.provider,
                    "deployment_id": profile.identity,
                    "task_types": [task.value for task in profile.task_types],
                    "quality": profile.quality,
                    "latency_ms": profile.latency_ms,
                    "ttft_ms": profile.ttft_ms,
                    "p95_latency_ms": profile.p95_latency_ms,
                    "success_probability": profile.success_probability,
                    "capabilities": list(profile.capabilities),
                    "available": profile.available,
                }
                for profile in self.catalog.profiles
            ],
            "selection_modes": ["weighted", "evidence"],
            "execution_strategies": [
                "auto",
                "single",
                "cascade",
                "self_consistency",
                "council",
            ],
        }


def build_container(
    model_caller: ModelCaller | None = None,
    *,
    routing_config: RoutingConfig | None = None,
    route_handlers: Mapping[str, Handler] | None = None,
    require_configured_tools: bool = False,
    telemetry: InMemoryTelemetryStore | None = None,
    verifier: ResponseVerifier | None = None,
    model_catalog: ModelCatalog | None = None,
    evidence_policy: EvidencePolicy | None = None,
    enable_adaptive_ranking: bool = False,
    execution_policy: ExecutionPolicy | None = None,
    circuit_breaker: CircuitBreaker | None = None,
    execution_clock: Callable[[], float] = time.monotonic,
) -> GatewayContainer:
    if model_caller is None and (
        execution_policy is not None or circuit_breaker is not None
    ):
        raise ValueError("server execution controls require an explicit model_caller")
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
    telemetry_store = telemetry or InMemoryTelemetryStore()
    optimizer = AdaptiveRoutingAgent(telemetry_store)
    selector = ModelSelector(
        model_catalog
        or default_model_catalog(config.fast_model, config.reasoning_model, config.code_model),
        optimizer=optimizer if enable_adaptive_ranking else None,
        evidence_policy=evidence_policy,
    )
    strategy_handler = (
        ControlledExecutionHandler(model_caller, telemetry_store, verifier=verifier,
                                   policy=execution_policy, breaker=circuit_breaker,
                                   clock=execution_clock)
        if model_caller is not None
        else None
    )
    return GatewayContainer(
        router=Router(
            RuleBasedEvaluator(config),
            registry,
            selector,
            CouncilPlanner(),
            strategy_handler or CouncilHandler(MockModelCaller()),
            ExecutionPlanner(),
            strategy_handler,
        ),
        registry=registry,
        catalog=selector.catalog,
        telemetry=telemetry_store,
        optimizer=optimizer,
    )
