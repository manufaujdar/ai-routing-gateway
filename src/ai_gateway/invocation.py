"""Shared provider boundary for direct, cascade, sample, and council calls."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .budget import BudgetDenied
from .controls import CircuitOpen, ExecutionLimitExceeded
from .models import GatewayRequest, RouteDecision
from .telemetry import CallObservation, InMemoryTelemetryStore, ModelCallResult

if TYPE_CHECKING:
    from .council_handler import ModelCaller


class AttemptFailure(RuntimeError):
    def __init__(self, observation: CallObservation):
        self.observation = observation
        super().__init__(f"provider execution failed at {observation.stage} "
                         f"({observation.error_type})")


def invoke_model(caller: ModelCaller, telemetry: InMemoryTelemetryStore,
                 request: GatewayRequest, decision: RouteDecision, model: str,
                 stage: str, prompt: str) -> tuple[ModelCallResult, CallObservation]:
    candidate = next((item for item in decision.model_candidates if item.model == model), None)
    if candidate is None:
        raise LookupError(f"no selected candidate metadata for model '{model}'")
    started = time.perf_counter()
    common = {
        "request_id": request.context["request_id"], "route": decision.route,
        "task_type": decision.task_type, "strategy": decision.execution_plan.strategy,
        "stage": stage, "model": model, "provider": candidate.provider,
        "deployment_id": candidate.deployment_id or model,
        "estimated_cost_usd": candidate.estimated_cost_usd,
    }
    result = None
    try:
        if hasattr(caller, "complete_with_metrics"):
            raw = caller.complete_with_metrics(model, prompt or request.prompt)
        else:
            raw = caller.complete(model, prompt or request.prompt)
        elapsed_ms = (time.perf_counter() - started) * 1000
        result = raw if isinstance(raw, ModelCallResult) else ModelCallResult(text=raw)
        if not result.text.strip():
            raise ValueError("provider returned an empty response")
        observation = CallObservation(
            **common, success=True,
            latency_ms=result.latency_ms if result.latency_ms is not None else elapsed_ms,
            ttft_ms=result.ttft_ms, input_tokens=result.input_tokens,
            output_tokens=result.output_tokens, cached_tokens=result.cached_tokens,
            cost_usd=result.cost_usd,
        )
        return result, observation
    except Exception as error:  # noqa: BLE001 - sanitize provider failures at boundary
        if isinstance(error, ExecutionLimitExceeded):
            result = error.result or ModelCallResult(text="", cost_usd=0, input_tokens=0,
                                                    output_tokens=0, cached_tokens=0)
        elif isinstance(error, (BudgetDenied, CircuitOpen)):
            result = ModelCallResult(text="", cost_usd=0, input_tokens=0,
                                     output_tokens=0, cached_tokens=0)
        observation = CallObservation(
            **common, success=False,
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
            error_type=type(error).__name__,
            cost_usd=result.cost_usd if result is not None else None,
            input_tokens=result.input_tokens if result is not None else None,
            output_tokens=result.output_tokens if result is not None else None,
            cached_tokens=result.cached_tokens if result is not None else None,
        )
        telemetry.record(observation)
        raise AttemptFailure(observation) from None

