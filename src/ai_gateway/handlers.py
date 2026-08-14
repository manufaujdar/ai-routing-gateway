from __future__ import annotations

from typing import Protocol

from .council_handler import ModelCaller
from .models import GatewayRequest, GatewayResponse, RouteDecision


class Handler(Protocol):
    def handle(self, request: GatewayRequest, decision: RouteDecision) -> GatewayResponse: ...


class MockHandler:
    """Safe default that makes route execution observable without external calls."""

    def __init__(self, provider: str) -> None:
        self.provider = provider

    def handle(self, request: GatewayRequest, decision: RouteDecision) -> GatewayResponse:
        return GatewayResponse(
            decision=decision,
            output=f"[{decision.route}] Would process: {request.prompt}",
            provider=self.provider,
            metadata={"mock": True},
        )


class ModelHandler:
    """Execute a selected direct LLM route through a provider-neutral caller."""

    def __init__(self, caller: ModelCaller, provider: str = "configured-provider") -> None:
        self.caller = caller
        self.provider = provider

    def handle(self, request: GatewayRequest, decision: RouteDecision) -> GatewayResponse:
        if decision.model is None:
            raise LookupError(f"route '{decision.route}' did not select a model")
        try:
            output = self.caller.complete(decision.model, request.prompt)
        except Exception as error:
            raise RuntimeError(
                f"provider execution failed ({type(error).__name__})"
            ) from error
        if not output.strip():
            raise ValueError(f"model '{decision.model}' returned an empty response")
        return GatewayResponse(
            decision=decision,
            output=output,
            provider=self.provider,
            metadata={"mock": False},
        )


class UnavailableHandler:
    """Fail closed when a specialized tool route has no configured implementation."""

    def __init__(self, capability: str) -> None:
        self.capability = capability

    def handle(self, request: GatewayRequest, decision: RouteDecision) -> GatewayResponse:
        raise LookupError(
            f"route '{decision.route}' requires a configured {self.capability} handler"
        )


class BlockedHandler:
    def handle(self, request: GatewayRequest, decision: RouteDecision) -> GatewayResponse:
        return GatewayResponse(
            decision=decision,
            output="Request was not executed because it matched a safety policy.",
            provider="policy",
        )
