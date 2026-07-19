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
    "GatewayContainer",
    "CouncilHandler",
    "CouncilMode",
    "CouncilRequirementError",
    "CouncilPlanner",
    "CouncilPolicy",
    "GatewayRequest",
    "GatewayResponse",
    "ModelCatalog",
    "ModelProfile",
    "ModelSelector",
    "ModelCaller",
    "OptimizationGoal",
    "RouteDecision",
    "ROLE_DEFINITIONS",
    "ProjectTask",
    "ProjectTaskKind",
    "RoleResult",
    "RoleStatus",
    "TeamExecutor",
    "TeamPlan",
    "TeamPlanner",
    "TeamRole",
    "TeamRoleHandler",
    "TeamRoleRegistry",
    "TeamRun",
    "TeamStep",
    "build_container",
    "scaffold_team",
    "validate_scaffold",
    "__version__",
]
