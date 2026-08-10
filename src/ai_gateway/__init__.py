"""AI routing gateway."""

from ._version import __version__
from .container import GatewayContainer, build_container
from .council import CouncilPlanner, CouncilPolicy
from .council_handler import CouncilHandler, ModelCaller
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
    "CallObservation",
    "CouncilHandler",
    "CouncilMode",
    "CouncilPlanner",
    "CouncilPolicy",
    "CouncilRequirementError",
    "ExecutionPlan",
    "ExecutionPlanner",
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
    "RoleResult",
    "RoleStatus",
    "RouteDecision",
    "RoutingPolicyProposal",
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
