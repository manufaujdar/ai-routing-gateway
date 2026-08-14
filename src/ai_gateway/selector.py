from __future__ import annotations

from dataclasses import dataclass, replace
from typing import ClassVar, Protocol

from .models import (
    Complexity,
    GatewayRequest,
    ModelCandidate,
    OptimizationGoal,
    RouteDecision,
    TaskType,
)


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Offline model metadata used by the deterministic selector.

    Pricing and latency are planning estimates. Production deployments should refresh
    profiles from provider catalogs and observed telemetry before selecting a model.
    """

    model: str
    provider: str
    task_types: tuple[TaskType, ...]
    quality: float
    input_cost_per_million: float
    output_cost_per_million: float
    latency_ms: int
    capabilities: tuple[str, ...] = ()
    available: bool = True
    deployment_id: str = ""
    ttft_ms: int = 0
    p95_latency_ms: int = 0
    success_probability: float = 1.0
    quality_by_task: tuple[tuple[TaskType, float], ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.quality <= 1:
            raise ValueError("model quality must be between 0 and 1")
        if self.input_cost_per_million < 0 or self.output_cost_per_million < 0:
            raise ValueError("model prices must not be negative")
        if self.latency_ms < 0:
            raise ValueError("model latency must not be negative")
        if self.ttft_ms < 0 or self.p95_latency_ms < 0:
            raise ValueError("model latency percentiles must not be negative")
        if not 0 <= self.success_probability <= 1:
            raise ValueError("model success_probability must be between 0 and 1")
        if any(not 0 <= quality <= 1 for _, quality in self.quality_by_task):
            raise ValueError("task-specific quality must be between 0 and 1")

    @property
    def identity(self) -> str:
        return self.deployment_id or f"{self.provider}:{self.model}"

    def quality_for(self, task_type: TaskType) -> float:
        return dict(self.quality_by_task).get(task_type, self.quality)


class SelectionOptimizer(Protocol):
    def adjustment(self, profile: ModelProfile, task_type: TaskType) -> float: ...


class ModelCatalog:
    def __init__(self, profiles: tuple[ModelProfile, ...]) -> None:
        if not profiles:
            raise ValueError("model catalog must contain at least one profile")
        if len({profile.identity for profile in profiles}) != len(profiles):
            raise ValueError("model deployment identities must be unique")
        if len({profile.model for profile in profiles}) != len(profiles):
            raise ValueError(
                "model identifiers must be unique because the caller dispatch contract uses them"
            )
        self._profiles = profiles

    @property
    def profiles(self) -> tuple[ModelProfile, ...]:
        """Return immutable metadata for diagnostics and operator interfaces."""

        return self._profiles

    def candidates(self, task_type: TaskType) -> tuple[ModelProfile, ...]:
        return tuple(
            profile
            for profile in self._profiles
            if profile.available and task_type in profile.task_types
        )


class ModelSelector:
    """Filters hard constraints, then ranks the feasible Pareto-style candidate set."""

    WEIGHTS: ClassVar[dict[OptimizationGoal, tuple[float, float, float]]] = {
        OptimizationGoal.BALANCED: (0.55, 0.25, 0.20),
        OptimizationGoal.COST: (0.20, 0.70, 0.10),
        OptimizationGoal.QUALITY: (0.80, 0.10, 0.10),
        OptimizationGoal.LATENCY: (0.25, 0.10, 0.65),
    }
    OUTPUT_TOKENS: ClassVar[dict[Complexity, int]] = {
        Complexity.LOW: 250,
        Complexity.MEDIUM: 750,
        Complexity.HIGH: 1_500,
    }

    def __init__(
        self,
        catalog: ModelCatalog,
        optimizer: SelectionOptimizer | None = None,
    ) -> None:
        self.catalog = catalog
        self.optimizer = optimizer

    def select(self, request: GatewayRequest, decision: RouteDecision) -> RouteDecision:
        if decision.route == "blocked":
            return decision

        input_tokens, output_tokens = self._estimated_tokens(request, decision)
        feasible: list[tuple[ModelProfile, float]] = []
        rejected: list[str] = []

        for profile in self.catalog.candidates(decision.task_type):
            estimated_cost = self._estimated_cost(profile, input_tokens, output_tokens)
            rejection = self._rejection_reason(
                profile,
                profile.quality_for(decision.task_type),
                estimated_cost,
                request,
            )
            if rejection:
                rejected.append(f"{profile.model}: {rejection}")
            else:
                feasible.append((profile, estimated_cost))

        if not feasible:
            detail = "; ".join(rejected) or "no model supports the evaluated task type"
            raise LookupError(f"no feasible model for route '{decision.route}': {detail}")

        qualities = [profile.quality_for(decision.task_type) for profile, _ in feasible]
        costs = [cost for _, cost in feasible]
        latencies = [profile.latency_ms for profile, _ in feasible]
        quality_weight, cost_weight, latency_weight = self.WEIGHTS[request.optimization]

        ranked: list[ModelCandidate] = []
        for profile, cost in feasible:
            quality = profile.quality_for(decision.task_type)
            score = (
                quality_weight * self._normalize(quality, qualities)
                + cost_weight * self._normalize_inverse(cost, costs)
                + latency_weight * self._normalize_inverse(profile.latency_ms, latencies)
            )
            if self.optimizer is not None:
                score += self.optimizer.adjustment(profile, decision.task_type)
            ranked.append(
                ModelCandidate(
                    model=profile.model,
                    provider=profile.provider,
                    score=round(score, 6),
                    quality=quality,
                    estimated_cost_usd=round(cost, 8),
                    estimated_latency_ms=profile.latency_ms,
                    deployment_id=profile.identity,
                    estimated_ttft_ms=profile.ttft_ms,
                    success_probability=profile.success_probability,
                )
            )

        ranked.sort(key=lambda candidate: (-candidate.score, candidate.model))
        selected = ranked[0]
        selection_reason = (
            f"Selected {selected.model} from {len(ranked)} feasible model(s) for the "
            f"{request.optimization.value} objective (estimated cost "
            f"${selected.estimated_cost_usd:.6f}, latency {selected.estimated_latency_ms} ms, "
            f"quality {selected.quality:.2f})."
        )
        return replace(
            decision,
            model=selected.model,
            reasons=(*decision.reasons, selection_reason),
            model_candidates=tuple(ranked),
        )

    @classmethod
    def _estimated_tokens(
        cls, request: GatewayRequest, decision: RouteDecision
    ) -> tuple[int, int]:
        input_tokens = request.context.get("estimated_input_tokens")
        output_tokens = request.context.get("estimated_output_tokens")
        if not isinstance(input_tokens, int) or input_tokens <= 0:
            input_tokens = max(1, (len(request.prompt) + 3) // 4)
        if not isinstance(output_tokens, int) or output_tokens <= 0:
            output_tokens = cls.OUTPUT_TOKENS[decision.complexity]
        return input_tokens, output_tokens

    @staticmethod
    def _estimated_cost(profile: ModelProfile, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * profile.input_cost_per_million
            + output_tokens * profile.output_cost_per_million
        ) / 1_000_000

    @staticmethod
    def _rejection_reason(
        profile: ModelProfile,
        quality: float,
        estimated_cost: float,
        request: GatewayRequest,
    ) -> str | None:
        if request.allowed_models is not None and profile.model not in request.allowed_models:
            return "not in allowed_models"
        if request.max_cost_usd is not None and estimated_cost > request.max_cost_usd:
            return f"estimated cost ${estimated_cost:.6f} exceeds budget"
        if request.max_latency_ms is not None and profile.latency_ms > request.max_latency_ms:
            return f"estimated latency {profile.latency_ms} ms exceeds limit"
        if request.min_quality is not None and quality < request.min_quality:
            return f"quality {quality:.2f} is below minimum"
        return None

    @staticmethod
    def _normalize(value: float, values: list[float] | list[int]) -> float:
        low, high = min(values), max(values)
        return 1.0 if low == high else (value - low) / (high - low)

    @classmethod
    def _normalize_inverse(cls, value: float, values: list[float] | list[int]) -> float:
        return 1.0 - cls._normalize(value, values)


def default_model_catalog(
    fast_model: str, reasoning_model: str, code_model: str
) -> ModelCatalog:
    """Return stable example profiles; callers may inject a telemetry-backed catalog."""

    general_tasks = (TaskType.CHAT, TaskType.SEARCH, TaskType.VISION)
    return ModelCatalog(
        (
            ModelProfile(
                model=fast_model,
                provider="configured-fast",
                task_types=general_tasks + (TaskType.REASONING, TaskType.CODE),
                capabilities=("text", "tools", "vision"),
                quality=0.76,
                input_cost_per_million=0.40,
                output_cost_per_million=1.60,
                latency_ms=450,
                deployment_id="configured-fast",
                ttft_ms=180,
                p95_latency_ms=900,
                success_probability=0.98,
            ),
            ModelProfile(
                model=reasoning_model,
                provider="configured-reasoning",
                task_types=(TaskType.REASONING, TaskType.CODE),
                capabilities=("text", "reasoning", "tools"),
                quality=0.94,
                input_cost_per_million=1.10,
                output_cost_per_million=4.40,
                latency_ms=1_400,
                deployment_id="configured-reasoning",
                ttft_ms=500,
                p95_latency_ms=2_800,
                success_probability=0.97,
            ),
            ModelProfile(
                model=code_model,
                provider="configured-code",
                task_types=(TaskType.CODE,),
                capabilities=("text", "code", "tools"),
                quality=0.90,
                input_cost_per_million=1.00,
                output_cost_per_million=4.00,
                latency_ms=850,
                deployment_id="configured-code",
                ttft_ms=320,
                p95_latency_ms=1_700,
                success_probability=0.97,
            ),
        )
    )
