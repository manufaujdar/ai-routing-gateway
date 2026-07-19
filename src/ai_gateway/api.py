from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ._version import __version__
from .container import build_container
from .models import CouncilMode, GatewayRequest, OptimizationGoal

app = FastAPI(title="AI Routing Gateway", version=__version__)
container = build_container()


class RouteRequest(BaseModel):
    prompt: str = Field(min_length=1)
    execute: bool = True
    context: dict[str, Any] = Field(default_factory=dict)
    allowed_routes: list[str] | None = None
    allowed_models: list[str] | None = None
    max_cost_usd: float | None = Field(default=None, ge=0)
    max_latency_ms: int | None = Field(default=None, ge=0)
    min_quality: float | None = Field(default=None, ge=0, le=1)
    optimization: OptimizationGoal = OptimizationGoal.BALANCED
    council_mode: CouncilMode = CouncilMode.AUTO
    council_size: int = Field(default=3, ge=2, le=8)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "routes": container.registry.routes}


@app.post("/v1/route")
def route(payload: RouteRequest) -> dict[str, Any]:
    try:
        response = container.router.route(
            GatewayRequest(
                prompt=payload.prompt,
                execute=payload.execute,
                context=payload.context,
                allowed_routes=(
                    tuple(payload.allowed_routes) if payload.allowed_routes is not None else None
                ),
                allowed_models=(
                    tuple(payload.allowed_models) if payload.allowed_models is not None else None
                ),
                max_cost_usd=payload.max_cost_usd,
                max_latency_ms=payload.max_latency_ms,
                min_quality=payload.min_quality,
                optimization=payload.optimization,
                council_mode=payload.council_mode,
                council_size=payload.council_size,
            )
        )
        return asdict(response)
    except (ValueError, PermissionError, LookupError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
