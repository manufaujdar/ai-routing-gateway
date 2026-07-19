from __future__ import annotations

from typing import Protocol

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

class BlockedHandler:
    def handle(self, request: GatewayRequest, decision: RouteDecision) -> GatewayResponse:
        return GatewayResponse(
            decision=decision,
            output="Request was not executed because it matched a safety policy.",
            provider="policy",
        )
