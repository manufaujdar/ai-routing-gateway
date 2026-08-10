from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    CHAT = "chat"
    REASONING = "reasoning"
    CODE = "code"
    SEARCH = "search"
    VISION = "vision"
    UNSAFE = "unsafe"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OptimizationGoal(str, Enum):
    BALANCED = "balanced"
    COST = "cost"
    QUALITY = "quality"
    LATENCY = "latency"


class CouncilMode(str, Enum):
    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class CouncilRequirementError(ValueError):
    """Raised when an explicitly required council cannot be planned safely."""


@dataclass(frozen=True, slots=True)
class GatewayRequest:
    prompt: str
    execute: bool = True
    context: dict[str, Any] = field(default_factory=dict)
    allowed_routes: tuple[str, ...] | None = None
    allowed_models: tuple[str, ...] | None = None
    max_cost_usd: float | None = None
    max_latency_ms: int | None = None
    min_quality: float | None = None
    optimization: OptimizationGoal = OptimizationGoal.BALANCED
    council_mode: CouncilMode = CouncilMode.AUTO
    council_size: int = 3

    def __post_init__(self) -> None:
        if type(self.execute) is not bool:
            raise ValueError("execute must be a boolean")
        if self.max_cost_usd is not None and self.max_cost_usd < 0:
            raise ValueError("max_cost_usd must not be negative")
        if self.max_latency_ms is not None and self.max_latency_ms < 0:
            raise ValueError("max_latency_ms must not be negative")
        if self.min_quality is not None and not 0 <= self.min_quality <= 1:
            raise ValueError("min_quality must be between 0 and 1")
        if not isinstance(self.optimization, OptimizationGoal):
            raise TypeError("optimization must be a valid OptimizationGoal")
        if not isinstance(self.council_mode, CouncilMode):
            raise TypeError("council_mode must be a valid CouncilMode")
        if not 2 <= self.council_size <= 8:
            raise ValueError("council_size must be between 2 and 8")
        if self.council_mode is CouncilMode.ALWAYS and self.max_cost_usd is not None:
            raise CouncilRequirementError(
                "council_mode='always' cannot guarantee max_cost_usd without runtime "
                "usage metering"
            )


@dataclass(frozen=True, slots=True)
class ModelCandidate:
    model: str
    provider: str
    score: float
    quality: float
    estimated_cost_usd: float
    estimated_latency_ms: int


@dataclass(frozen=True, slots=True)
class CouncilPlan:
    enabled: bool
    mode: CouncilMode
    reason: str
    activation_score: float = 0.0
    member_models: tuple[str, ...] = ()
    chairman_model: str | None = None
    estimated_cost_usd: float = 0.0
    estimated_latency_ms: int = 0
    stages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RouteDecision:
    route: str
    task_type: TaskType
    complexity: Complexity
    confidence: float
    reasons: tuple[str, ...]
    model: str | None = None
    tools: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    model_candidates: tuple[ModelCandidate, ...] = ()
    council_plan: CouncilPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GatewayResponse:
    decision: RouteDecision
    output: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
