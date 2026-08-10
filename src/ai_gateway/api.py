from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, SecretStr, StrictBool, field_validator

from ._version import __version__
from .container import GatewayContainer, build_container
from .models import CouncilMode, GatewayRequest, OptimizationGoal
from .runtime import ProviderSettings, runtime_credentials_allowed, settings_from_environment

STATIC_DIR = Path(__file__).with_name("static")


class RuntimeProviderRequest(BaseModel):
    api_key: SecretStr = Field(min_length=1)
    base_url: str = "https://api.openai.com/v1"
    fast_model: str = "gpt-4.1-mini"
    reasoning_model: str = "o4-mini"
    code_model: str = "gpt-4.1"
    timeout_seconds: float = Field(default=120, gt=0, le=300)
    allow_insecure_loopback: StrictBool = False

    @field_validator("fast_model", "reasoning_model", "code_model")
    @classmethod
    def validate_model_identifier(cls, value: str) -> str:
        if not value or value.strip() != value or any(character.isspace() for character in value):
            raise ValueError("model identifiers must be non-empty and contain no whitespace")
        return value

    def to_settings(self) -> ProviderSettings:
        return ProviderSettings(
            api_key=self.api_key.get_secret_value(),
            base_url=self.base_url,
            fast_model=self.fast_model,
            reasoning_model=self.reasoning_model,
            code_model=self.code_model,
            timeout_seconds=self.timeout_seconds,
            allow_insecure_loopback=self.allow_insecure_loopback,
        )


class RouteRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100_000)
    execute: StrictBool = True
    context: dict[str, Any] = Field(default_factory=dict)
    allowed_routes: list[str] | None = None
    allowed_models: list[str] | None = None
    max_cost_usd: float | None = Field(default=None, ge=0)
    max_latency_ms: int | None = Field(default=None, ge=0)
    min_quality: float | None = Field(default=None, ge=0, le=1)
    optimization: OptimizationGoal = OptimizationGoal.BALANCED
    council_mode: CouncilMode = CouncilMode.AUTO
    council_size: int = Field(default=3, ge=2, le=8)
    provider: RuntimeProviderRequest | None = None


def create_app(container: GatewayContainer | None = None) -> FastAPI:
    environment_settings = settings_from_environment() if container is None else None
    environment_container = container or (
        environment_settings.build_container() if environment_settings else build_container()
    )
    application = FastAPI(title="AI Routing Gateway", version=__version__)
    application.state.container = environment_container
    application.state.execution_mode = (
        "custom_container"
        if container is not None
        else "environment_provider"
        if environment_settings is not None
        else "mock"
    )
    application.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

    @application.get("/", response_class=FileResponse, include_in_schema=False)
    def local_console() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @application.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "version": __version__}

    @application.get("/ready")
    def ready() -> dict[str, Any]:
        current: GatewayContainer = application.state.container
        return {
            "status": "ready",
            "execution_mode": application.state.execution_mode,
            "routes": current.registry.routes,
        }

    @application.get("/v1/config")
    def configuration() -> dict[str, object]:
        return {
            "execution_mode": application.state.execution_mode,
            "runtime_credentials_allowed": runtime_credentials_allowed(),
            "credentials_stored": False,
            "supported_provider_protocol": "OpenAI-compatible chat completions",
            "specialized_tools": "application-supplied handlers required",
        }

    @application.get("/v1/capabilities")
    def capabilities() -> dict[str, object]:
        current: GatewayContainer = application.state.container
        return current.capabilities()

    @application.post("/v1/route")
    def route(payload: RouteRequest) -> dict[str, Any]:
        request_id = uuid.uuid4().hex
        started = time.perf_counter()
        try:
            selected_container = _container_for_request(payload, application.state.container)
            response = selected_container.router.route(
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
            result = asdict(response)
            result["request"] = {
                "id": request_id,
                "elapsed_ms": round((time.perf_counter() - started) * 1_000, 3),
            }
            return result
        except (ValueError, PermissionError, LookupError, RuntimeError) as error:
            raise HTTPException(
                status_code=400,
                detail={"message": str(error), "request_id": request_id},
            ) from error

    return application


def _container_for_request(
    payload: RouteRequest,
    default_container: GatewayContainer,
) -> GatewayContainer:
    if payload.provider is None:
        return default_container
    if not runtime_credentials_allowed():
        raise PermissionError(
            "runtime provider credentials are disabled; configure server environment variables "
            "or set AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS=true for a trusted local deployment"
        )
    return payload.provider.to_settings().build_container()


app = create_app()
