from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, SecretStr, StrictBool, field_validator

from ._version import __version__
from .container import GatewayContainer, build_container
from .controls import ExecutionPolicy
from .models import CouncilMode, ExecutionStrategy, GatewayRequest, OptimizationGoal
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
    max_cost_usd: float | None = Field(default=None, ge=0, strict=True, allow_inf_nan=False)
    max_latency_ms: int | None = Field(default=None, ge=0, strict=True)
    min_quality: float | None = Field(default=None, ge=0, le=1, strict=True, allow_inf_nan=False)
    optimization: OptimizationGoal = OptimizationGoal.BALANCED
    council_mode: CouncilMode = CouncilMode.AUTO
    council_size: int = Field(default=3, ge=2, le=8, strict=True)
    execution_strategy: ExecutionStrategy = ExecutionStrategy.AUTO
    strategy_model_limit: int = Field(default=3, ge=1, le=8, strict=True)
    self_consistency_samples: int = Field(default=3, ge=2, le=8, strict=True)
    verifier_threshold: float = Field(default=0.65, ge=0, le=1, strict=True, allow_inf_nan=False)
    max_model_calls: int = Field(default=17, ge=1, le=17, strict=True)
    execution_timeout_ms: int | None = Field(default=None, gt=0, le=300_000, strict=True)
    max_output_tokens: int | None = Field(default=None, gt=0, le=1_000_000, strict=True)
    selection_mode: str = "weighted"
    required_capabilities: list[str] = Field(default_factory=list)
    provider: RuntimeProviderRequest | None = None


class FeedbackRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    score: float = Field(ge=0, le=1, strict=True, allow_inf_nan=False)


def create_app(container: GatewayContainer | None = None, *,
               tenants: Mapping[str, GatewayContainer] | None = None) -> FastAPI:
    tenant_mode = tenants is not None
    tenant_containers: dict[bytes, GatewayContainer] = {}
    if tenant_mode:
        if not tenants or container is not None:
            raise ValueError("tenant mode requires a nonempty mapping and no default container")
        if len({id(item.telemetry) for item in tenants.values()}) != len(tenants):
            raise ValueError("tenant containers must have isolated telemetry stores")
        budget_accounts = set()
        for token, item in tenants.items():
            if not isinstance(token, str) or not 1 <= len(token) <= 4096 or any(c.isspace() for c in token):
                raise ValueError("tenant bearer credentials must be nonempty without whitespace")
            policy = getattr(item.router.strategy_handler, "policy", None)
            if policy is not None and policy.ledger is not None:
                account_key = (policy.ledger.path, policy.account)
                if account_key in budget_accounts:
                    raise ValueError("tenant containers must not share a budget account")
                budget_accounts.add(account_key)
            tenant_containers[hashlib.sha256(token.encode()).digest()] = item
    environment_settings = settings_from_environment() if container is None and not tenant_mode else None
    environment_container = container or (
        environment_settings.build_container() if environment_settings else build_container()
    )
    application = FastAPI(title="AI Routing Gateway", version=__version__)
    @application.exception_handler(RequestValidationError)
    async def invalid_request(_request, error: RequestValidationError):
        # Pydantic input values can include credentials or non-JSON NaN/Infinity.
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": item["loc"], "type": item["type"], "msg": item["msg"]}
            for item in error.errors()
        ]})

    @application.middleware("http")
    async def bind_tenant(request: Request, call_next):
        if tenant_mode and request.url.path != "/health":
            authorization = request.headers.get("authorization", "")
            scheme, _, token = authorization.partition(" ")
            selected = (tenant_containers.get(hashlib.sha256(token.encode()).digest())
                        if scheme.lower() == "bearer" and 1 <= len(token) <= 4096 else None)
            if selected is None:
                return JSONResponse(status_code=401, content={"detail": "invalid bearer credentials"},
                                    headers={"WWW-Authenticate": "Bearer"})
            request.state.container = selected
        else:
            request.state.container = application.state.container
        return await call_next(request)

    def current_container(request: Request) -> GatewayContainer:
        return request.state.container

    container_dependency = Depends(current_container)
    application.state.container = environment_container
    application.state.execution_mode = (
        "tenant_containers" if tenant_mode else "custom_container"
        if container is not None or tenant_mode
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
    def ready(current: GatewayContainer = container_dependency) -> dict[str, Any]:
        return {
            "status": "ready",
            "execution_mode": application.state.execution_mode,
            "routes": current.registry.routes,
        }

    @application.get("/v1/config")
    def configuration(current: GatewayContainer = container_dependency) -> dict[str, object]:
        return {
            "execution_mode": application.state.execution_mode,
            "runtime_credentials_allowed": (
                not tenant_mode and not _has_server_controls(current)
                and runtime_credentials_allowed()
            ),
            "authentication": "bearer_tenant" if tenant_mode else "trusted_local",
            "credentials_stored": False,
            "supported_provider_protocol": "OpenAI-compatible chat completions",
            "specialized_tools": "application-supplied handlers required",
            "execution_strategies": [strategy.value for strategy in ExecutionStrategy],
            "adaptive_policy": "advisory by default; opt-in ranking requires operator configuration",
        }

    @application.get("/v1/capabilities")
    def capabilities(current: GatewayContainer = container_dependency) -> dict[str, object]:
        return current.capabilities()

    @application.get("/v1/telemetry")
    def telemetry(current: GatewayContainer = container_dependency) -> dict[str, Any]:
        return current.telemetry.summary()

    @application.get("/v1/policy/proposal")
    def policy_proposal(current: GatewayContainer = container_dependency) -> dict[str, Any]:
        return current.optimizer.report()

    @application.post("/v1/feedback")
    def feedback(payload: FeedbackRequest,
                 current: GatewayContainer = container_dependency) -> dict[str, object]:
        try:
            current.telemetry.record_feedback(payload.request_id, payload.score)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"accepted": True, "request_id": payload.request_id}

    @application.post("/v1/route")
    def route(payload: RouteRequest,
              current: GatewayContainer = container_dependency) -> dict[str, Any]:
        request_id = uuid.uuid4().hex
        started = time.perf_counter()
        try:
            if tenant_mode and payload.provider is not None:
                raise PermissionError("tenant execution uses its server-configured provider")
            selected_container = _container_for_request(payload, current)
            response = selected_container.router.route(
                GatewayRequest(
                    prompt=payload.prompt,
                    execute=payload.execute,
                    context={**payload.context, "request_id": request_id},
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
                    execution_strategy=payload.execution_strategy,
                    strategy_model_limit=payload.strategy_model_limit,
                    self_consistency_samples=payload.self_consistency_samples,
                    verifier_threshold=payload.verifier_threshold,
                    max_model_calls=payload.max_model_calls,
                    execution_timeout_ms=payload.execution_timeout_ms,
                    max_output_tokens=payload.max_output_tokens,
                    selection_mode=payload.selection_mode,
                    required_capabilities=tuple(payload.required_capabilities),
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


def _has_server_controls(container: GatewayContainer) -> bool:
    handler = container.router.strategy_handler
    return (getattr(handler, "policy", ExecutionPolicy()) != ExecutionPolicy()
            or getattr(handler, "breaker", None) is not None)


def _container_for_request(
    payload: RouteRequest,
    default_container: GatewayContainer,
) -> GatewayContainer:
    if payload.provider is None:
        return default_container
    if _has_server_controls(default_container):
        raise PermissionError("runtime provider overrides cannot bypass server execution controls")
    if not runtime_credentials_allowed():
        raise PermissionError(
            "runtime provider credentials are disabled; configure server environment variables "
            "or set AI_GATEWAY_ALLOW_RUNTIME_CREDENTIALS=true for a trusted local deployment"
        )
    return payload.provider.to_settings().build_container(default_container.telemetry)


app = create_app()
