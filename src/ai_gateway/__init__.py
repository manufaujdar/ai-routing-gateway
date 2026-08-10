"""AI routing gateway."""

from ._version import __version__
from .container import GatewayContainer, build_container
from .council import CouncilPlanner, CouncilPolicy
from .council_handler import CouncilHandler, ModelCaller
from .models import (
    CouncilMode,
    CouncilRequirementError,
    GatewayRequest,
    GatewayResponse,
    OptimizationGoal,
    RouteDecision,
)
from .selector import ModelCatalog, ModelProfile, ModelSelector
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

__all__ = [
    "ROLE_DEFINITIONS",
    "CouncilHandler",
    "CouncilMode",
    "CouncilPlanner",
    "CouncilPolicy",
    "CouncilRequirementError",
    "GatewayContainer",
    "GatewayRequest",
    "GatewayResponse",
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
    "TeamExecutor",
    "TeamPlan",
    "TeamPlanner",
    "TeamRole",
    "TeamRoleHandler",
    "TeamRoleRegistry",
    "TeamRun",
    "TeamStep",
    "__version__",
    "build_container",
    "scaffold_team",
    "validate_scaffold",
]
