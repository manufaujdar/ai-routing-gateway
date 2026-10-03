"""AI routing gateway."""

from ._version import __version__
from .budget import BudgetDenied, SQLiteBudgetLedger
from .container import GatewayContainer, build_container
from .controls import CircuitBreaker, ExecutionPolicy
from .council import CouncilPlanner, CouncilPolicy
from .council_handler import CouncilHandler, ModelCaller
from .evidence import EvidencePolicy, QualityEvidence
from .execution import AdaptiveLLMHandler, HeuristicResponseVerifier, VerificationResult
from .models import (
    CouncilMode,
    CouncilRequirementError,
    ExecutionPlan,
    ExecutionStrategy,
    GatewayRequest,
    GatewayResponse,
    OptimizationGoal,
    RouteDecision,
    StrategyRequirementError,
)
from .optimization import AdaptiveRoutingAgent, RoutingPolicyProposal
from .selector import ModelCatalog, ModelProfile, ModelSelector
from .strategy import ExecutionPlanner
from .team import (
    ROLE_DEFINITIONS,
    ProjectTask,
    ProjectTaskKind,
    RoleResult,
    RoleStatus,
    TeamExecutor,
    TeamPlan,
    TeamPlanner,
    TeamRole,
    TeamRoleHandler,
    TeamRoleRegistry,
    TeamRun,
    TeamStep,
)
from .team_scaffold import scaffold_team, validate_scaffold
from .telemetry import CallObservation, InMemoryTelemetryStore, ModelCallResult

__all__ = [
    "ROLE_DEFINITIONS",
    "AdaptiveLLMHandler",
    "AdaptiveRoutingAgent",
    "BudgetDenied",
    "CallObservation",
    "CircuitBreaker",
    "CouncilHandler",
    "CouncilMode",
    "CouncilPlanner",
    "CouncilPolicy",
    "CouncilRequirementError",
    "EvidencePolicy",
    "ExecutionPlan",
    "ExecutionPlanner",
    "ExecutionPolicy",
    "ExecutionStrategy",
    "GatewayContainer",
    "GatewayRequest",
    "GatewayResponse",
    "HeuristicResponseVerifier",
    "InMemoryTelemetryStore",
    "ModelCallResult",
    "ModelCaller",
    "ModelCatalog",
    "ModelProfile",
    "ModelSelector",
    "OptimizationGoal",
    "ProjectTask",
    "ProjectTaskKind",
    "QualityEvidence",
    "RoleResult",
    "RoleStatus",
    "RouteDecision",
    "RoutingPolicyProposal",
    "SQLiteBudgetLedger",
    "StrategyRequirementError",
    "TeamExecutor",
    "TeamPlan",
    "TeamPlanner",
    "TeamRole",
    "TeamRoleHandler",
    "TeamRoleRegistry",
    "TeamRun",
    "TeamStep",
    "VerificationResult",
    "__version__",
    "build_container",
    "scaffold_team",
    "validate_scaffold",
]
