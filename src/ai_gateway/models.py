from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from math import isfinite
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


class ExecutionStrategy(str, Enum):
    AUTO = "auto"
    SINGLE = "single"
    CASCADE = "cascade"
    SELF_CONSISTENCY = "self_consistency"
    COUNCIL = "council"


class CouncilRequirementError(ValueError):
    """Raised when an explicitly required council cannot be planned safely."""


class StrategyRequirementError(ValueError):
    """Raised when an explicitly requested execution strategy cannot satisfy policy."""


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
    execution_strategy: ExecutionStrategy = ExecutionStrategy.AUTO
    strategy_model_limit: int = 3
    self_consistency_samples: int = 3
    verifier_threshold: float = 0.65
    max_model_calls: int = 17
    required_capabilities: tuple[str, ...] = ()
    selection_mode: str = "weighted"
    execution_timeout_ms: int | None = None
    max_output_tokens: int | None = None

    def __post_init__(self) -> None:
        for name in ("execution_timeout_ms", "max_output_tokens"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value <= 0):
                raise ValueError(f"{name} must be a positive integer")
        if self.execution_timeout_ms is not None and self.execution_timeout_ms > 300_000:
            raise ValueError("execution_timeout_ms must not exceed 300000")
        if self.max_output_tokens is not None and self.max_output_tokens > 1_000_000:
            raise ValueError("max_output_tokens must not exceed 1000000")
        for name in ("max_cost_usd", "min_quality", "verifier_threshold"):
            value = getattr(self, name)
            if value is not None and (type(value) not in (int, float) or not isfinite(value)):
                raise ValueError(f"{name} must be a finite number")
        for name in ("max_latency_ms", "council_size", "strategy_model_limit",
                     "self_consistency_samples", "max_model_calls"):
            value = getattr(self, name)
            if not (name == "max_latency_ms" and value is None) and type(value) is not int:
                raise ValueError(f"{name} must be an integer")
        if not 1 <= self.max_model_calls <= 17:
            raise ValueError("max_model_calls must be between 1 and 17")
        if self.selection_mode not in ("weighted", "evidence"):
            raise ValueError("selection_mode must be weighted or evidence")
        if self.selection_mode == "evidence" and self.min_quality is None:
            raise ValueError("evidence selection requires an explicit min_quality")
        if not isinstance(self.required_capabilities, tuple) or any(
            not isinstance(item, str) or not item for item in self.required_capabilities
        ):
            raise ValueError("required_capabilities must be a tuple of nonempty strings")
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
        if not isinstance(self.execution_strategy, ExecutionStrategy):
            raise TypeError("execution_strategy must be a valid ExecutionStrategy")
        if not 2 <= self.council_size <= 8:
            raise ValueError("council_size must be between 2 and 8")
        if not 1 <= self.strategy_model_limit <= 8:
            raise ValueError("strategy_model_limit must be between 1 and 8")
        if not 2 <= self.self_consistency_samples <= 8:
            raise ValueError("self_consistency_samples must be between 2 and 8")
        if not 0 <= self.verifier_threshold <= 1:
            raise ValueError("verifier_threshold must be between 0 and 1")
        if (
            self.execution_strategy is ExecutionStrategy.COUNCIL
            and self.council_mode is CouncilMode.NEVER
        ):
            raise StrategyRequirementError(
                "execution_strategy='council' conflicts with council_mode='never'"
            )
        if (
            self.council_mode is CouncilMode.ALWAYS
            and self.execution_strategy
            not in (ExecutionStrategy.AUTO, ExecutionStrategy.COUNCIL)
        ):
            raise StrategyRequirementError(
                "council_mode='always' conflicts with the requested execution strategy"
            )
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
    deployment_id: str = ""
    estimated_ttft_ms: int = 0
    success_probability: float = 1.0


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    strategy: ExecutionStrategy
    reason: str
    model_sequence: tuple[str, ...] = ()
    estimated_cost_usd: float = 0.0
    estimated_latency_ms: int = 0
    verifier_threshold: float = 0.65
    sample_count: int = 1
    hard_budget_respected: bool = False
    budget_semantics: str = "cost and latency are planning estimates, not spending guarantees"


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
    execution_plan: ExecutionPlan | None = None
    selection_receipt: dict[str, Any] = field(default_factory=dict)

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
