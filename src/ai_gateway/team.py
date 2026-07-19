from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol


class TeamRole(str, Enum):
    TEAM_LEAD = "team_lead"
    PLANNER = "planner"
    RESEARCH = "research"
    DESIGNER = "designer"
    ENGINEER = "engineer"
    BUILDER = "builder"
    REVIEWER = "reviewer"
    QA = "qa"
    SAFETY_EVALUATION = "safety_evaluation"
    DOCUMENTATION = "documentation"
    MARKETER = "marketer"
    RELEASE = "release"


class ProjectTaskKind(str, Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    RESEARCH = "research"
    REVIEW = "review"
    QA = "qa"
    DOCUMENTATION = "documentation"
    MARKETING = "marketing"
    RELEASE = "release"


class RoleStatus(str, Enum):
    PASSED = "passed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RoleDefinition:
    role: TeamRole
    display_name: str
    skill_name: str
    purpose: str
    mutation_authority: str


ROLE_DEFINITIONS: tuple[RoleDefinition, ...] = (
    RoleDefinition(TeamRole.TEAM_LEAD, "Team Lead", "coordinate-ai-gateway-team", "Select roles, maintain the task contract, and consolidate gates.", "coordination only"),
    RoleDefinition(TeamRole.PLANNER, "Planner", "plan-ai-gateway-work", "Define outcomes, scope, non-goals, and acceptance criteria.", "planning artifacts only"),
    RoleDefinition(TeamRole.RESEARCH, "R&D", "research-ai-routing", "Gather evidence, compare options, and state uncertainty.", "research artifacts only"),
    RoleDefinition(TeamRole.DESIGNER, "Designer", "design-ai-gateway-experience", "Specify user, API, and CLI experience contracts.", "design artifacts only"),
    RoleDefinition(TeamRole.ENGINEER, "Engineer", "engineer-ai-gateway-systems", "Design boundaries, data flow, failure handling, and tests.", "technical design only"),
    RoleDefinition(TeamRole.BUILDER, "Builder", "build-ai-gateway-feature", "Implement approved production changes and focused tests.", "production implementation"),
    RoleDefinition(TeamRole.REVIEWER, "Reviewer", "review-ai-gateway-changes", "Independently review correctness and compatibility.", "report only"),
    RoleDefinition(TeamRole.QA, "QA", "test-ai-gateway-quality", "Independently verify behavior and acceptance criteria.", "test report only"),
    RoleDefinition(TeamRole.SAFETY_EVALUATION, "AI Safety & Evaluation", "evaluate-ai-gateway-safety", "Evaluate routing, privacy, cost, and safety policy.", "evaluation report only"),
    RoleDefinition(TeamRole.DOCUMENTATION, "Documentation", "document-ai-gateway", "Reconcile documentation with verified behavior.", "documentation only"),
    RoleDefinition(TeamRole.MARKETER, "Marketer", "market-ai-gateway", "Prepare evidence-grounded positioning and launch drafts.", "draft artifacts only"),
    RoleDefinition(TeamRole.RELEASE, "Release", "release-ai-gateway", "Run authorized delivery preflight and release mechanics.", "authorized release actions only"),
)

ROLE_REGISTRY_METADATA: dict[TeamRole, tuple[str, str, tuple[str, ...]]] = {
    TeamRole.TEAM_LEAD: ("team-lead", "leadership", ("planner", "research", "designer", "engineer")),
    TeamRole.PLANNER: ("planner", "product", ("engineer", "designer")),
    TeamRole.RESEARCH: ("research", "innovation", ("planner", "engineer")),
    TeamRole.DESIGNER: ("designer", "product", ("engineer", "builder")),
    TeamRole.ENGINEER: ("engineer", "engineering", ("builder",)),
    TeamRole.BUILDER: ("builder", "engineering", ("reviewer", "qa", "safety-evaluation")),
    TeamRole.REVIEWER: ("reviewer", "quality", ("builder", "documentation")),
    TeamRole.QA: ("qa", "quality", ("builder", "documentation")),
    TeamRole.SAFETY_EVALUATION: ("safety-evaluation", "quality", ("builder", "documentation")),
    TeamRole.DOCUMENTATION: ("documentation", "delivery", ("release", "marketer")),
    TeamRole.MARKETER: ("marketer", "growth", ("release",)),
    TeamRole.RELEASE: ("release", "delivery", ()),
}


@dataclass(frozen=True, slots=True)
class ProjectTask:
    objective: str
    kind: ProjectTaskKind = ProjectTaskKind.FEATURE
    requires_research: bool = False
    user_facing: bool = False
    affects_ai_policy: bool = False
    high_stakes: bool = False
    ambiguous: bool = False
    hard_to_reverse: bool = False
    multiple_viable_approaches: bool = False
    independent_views_useful: bool = False
    council_resources_fit: bool = False
    documentation_requested: bool = True
    marketing_requested: bool = False
    release_requested: bool = False
    external_actions_authorized: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective must not be empty")
        if not isinstance(self.kind, ProjectTaskKind):
            raise ValueError("kind must be a valid ProjectTaskKind")
        if self.external_actions_authorized and not self.release_requested:
            raise ValueError("external actions may be authorized only for a requested release")


@dataclass(frozen=True, slots=True)
class TeamStep:
    name: str
    roles: tuple[TeamRole, ...]
    reason: str
    parallel: bool = False
    gate: bool = False


@dataclass(frozen=True, slots=True)
class TeamPlan:
    task: ProjectTask
    steps: tuple[TeamStep, ...]
    council_recommended: bool
    council_reasons: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def roles(self) -> tuple[TeamRole, ...]:
        return tuple(role for step in self.steps for role in step.roles)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TeamPlanner:
    """Build an explainable role plan without calling a model or provider."""

    def plan(self, task: ProjectTask) -> TeamPlan:
        steps = [
            TeamStep("coordinate", (TeamRole.TEAM_LEAD,), "Every workflow has one accountable coordinator."),
        ]

        if task.kind is ProjectTaskKind.FEATURE:
            discovery_roles = []
            if task.requires_research:
                discovery_roles.append(TeamRole.RESEARCH)
            discovery_roles.append(TeamRole.PLANNER)
            if task.user_facing:
                discovery_roles.append(TeamRole.DESIGNER)
            steps.append(TeamStep("discover", tuple(discovery_roles), "Define evidence, scope, and experience before implementation.", parallel=len(discovery_roles) > 1))
            steps.append(TeamStep("design", (TeamRole.ENGINEER,), "Translate approved scope into buildable system boundaries."))
            steps.append(TeamStep("build", (TeamRole.BUILDER,), "A single implementation owner prevents conflicting production edits."))
            steps.append(self._certification_step(task))
        elif task.kind is ProjectTaskKind.BUGFIX:
            steps.extend((
                TeamStep("diagnose", (TeamRole.ENGINEER,), "Confirm the cause and define the smallest safe repair."),
                TeamStep("build", (TeamRole.BUILDER,), "Implement the focused repair and regression tests."),
                self._certification_step(task),
            ))
        elif task.kind is ProjectTaskKind.RESEARCH:
            steps.append(TeamStep("research", (TeamRole.RESEARCH, TeamRole.PLANNER), "Compare evidence and convert findings into a decision-ready recommendation.", parallel=True, gate=True))
        elif task.kind is ProjectTaskKind.REVIEW:
            roles = [TeamRole.REVIEWER]
            if task.affects_ai_policy:
                roles.append(TeamRole.SAFETY_EVALUATION)
            steps.append(TeamStep("review", tuple(roles), "Use independent evidence before accepting the change.", parallel=len(roles) > 1, gate=True))
        elif task.kind is ProjectTaskKind.QA:
            steps.append(TeamStep("verify", (TeamRole.QA,), "Reproduce behavior against explicit acceptance criteria.", gate=True))
        elif task.kind is ProjectTaskKind.DOCUMENTATION:
            steps.append(TeamStep("document", (TeamRole.DOCUMENTATION,), "Reconcile durable guidance with verified behavior."))
        elif task.kind is ProjectTaskKind.MARKETING:
            steps.append(TeamStep("position", (TeamRole.MARKETER,), "Prepare evidence-grounded draft messaging; publishing remains external."))
        elif task.kind is ProjectTaskKind.RELEASE:
            steps.append(self._certification_step(task))

        existing_roles = {role for step in steps for role in step.roles}
        if task.documentation_requested and task.kind in {ProjectTaskKind.FEATURE, ProjectTaskKind.BUGFIX, ProjectTaskKind.RELEASE} and TeamRole.DOCUMENTATION not in existing_roles:
            steps.append(TeamStep("document", (TeamRole.DOCUMENTATION,), "Update integration guidance after behavior is certified."))
        if task.marketing_requested and TeamRole.MARKETER not in existing_roles:
            steps.append(TeamStep("position", (TeamRole.MARKETER,), "Create launch drafts from verified capabilities."))
        if task.release_requested or task.kind is ProjectTaskKind.RELEASE:
            steps.append(TeamStep("release", (TeamRole.RELEASE,), "Run release preflight; external actions require explicit authorization.", gate=True))

        council_checks = (
            (task.kind in {ProjectTaskKind.FEATURE, ProjectTaskKind.RESEARCH}, "the task is product planning or research"),
            (task.high_stakes, "the decision is high-stakes"),
            (task.ambiguous, "the decision is ambiguous"),
            (task.hard_to_reverse, "the decision is hard to reverse"),
            (task.multiple_viable_approaches, "multiple viable approaches have material trade-offs"),
            (task.independent_views_useful, "independent views are likely to change the recommendation"),
            (task.council_resources_fit, "council cost and latency fit the request policy"),
        )
        council_recommended = all(passed for passed, _ in council_checks)
        if council_recommended:
            council_reasons = tuple(reason.capitalize() + "." for _, reason in council_checks)
        else:
            council_reasons = tuple(
                f"Council not recommended because {reason} was not established."
                for passed, reason in council_checks
                if not passed
            )

        reasons = (
            f"Selected workflow for task kind '{task.kind.value}'.",
            "Reviewer, QA, and safety roles are kept independent from Builder.",
            "Provider calls and external actions are not required by planning.",
        )
        return TeamPlan(task, tuple(steps), council_recommended, council_reasons, reasons)

    @staticmethod
    def _certification_step(task: ProjectTask) -> TeamStep:
        roles = [TeamRole.REVIEWER, TeamRole.QA]
        if task.affects_ai_policy:
            roles.append(TeamRole.SAFETY_EVALUATION)
        return TeamStep("certify", tuple(roles), "Independent gates must pass before documentation or release.", parallel=True, gate=True)


@dataclass(frozen=True, slots=True)
class RoleResult:
    role: TeamRole
    status: RoleStatus
    summary: str
    artifacts: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.role, TeamRole):
            raise ValueError("role must be a valid TeamRole")
        if not isinstance(self.status, RoleStatus):
            raise ValueError("status must be a valid RoleStatus")
        if not self.summary.strip():
            raise ValueError("summary must not be empty")


class TeamRoleHandler(Protocol):
    def run(self, task: ProjectTask, step: TeamStep, context: Mapping[str, Any]) -> RoleResult: ...


class TeamRoleRegistry:
    def __init__(self) -> None:
        self._handlers: dict[TeamRole, TeamRoleHandler] = {}

    def register(
        self, role: TeamRole, handler: TeamRoleHandler, *, replace: bool = False
    ) -> None:
        if not isinstance(role, TeamRole):
            raise ValueError("role must be a valid TeamRole")
        if role in self._handlers and not replace:
            raise ValueError(f"handler already registered for role '{role.value}'")
        self._handlers[role] = handler

    def get(self, role: TeamRole) -> TeamRoleHandler:
        try:
            return self._handlers[role]
        except KeyError as error:
            raise LookupError(f"no team handler registered for role '{role.value}'") from error

    @property
    def roles(self) -> tuple[TeamRole, ...]:
        return tuple(sorted(self._handlers, key=lambda role: role.value))

    def __contains__(self, role: TeamRole) -> bool:
        return role in self._handlers


@dataclass(frozen=True, slots=True)
class TeamRun:
    plan: TeamPlan
    results: tuple[RoleResult, ...]
    succeeded: bool
    stopped_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TeamExecutor:
    """Execute a precomputed plan through caller-supplied role handlers."""

    def __init__(self, registry: TeamRoleRegistry, *, parallel: bool = False, max_workers: int = 4) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self.registry = registry
        self.parallel = parallel
        self.max_workers = max_workers

    def execute(self, plan: TeamPlan, context: Mapping[str, Any] | None = None) -> TeamRun:
        required_handlers = {
            role
            for role in plan.roles
            if role is not TeamRole.RELEASE or plan.task.external_actions_authorized
        }
        missing = sorted({role.value for role in required_handlers if role not in self.registry})
        if missing:
            raise LookupError(f"no team handlers registered for: {', '.join(missing)}")

        base_context = dict(context or {})
        base_context["external_actions_authorized"] = plan.task.external_actions_authorized
        self._validate_independence(plan)
        results: list[RoleResult] = []
        for step in plan.steps:
            step_results = self._run_step(plan.task, step, base_context)
            results.extend(step_results)
            if any(result.status is not RoleStatus.PASSED for result in step_results):
                return TeamRun(plan, tuple(results), False, step.name)
        return TeamRun(plan, tuple(results), True)

    def _validate_independence(self, plan: TeamPlan) -> None:
        if TeamRole.BUILDER not in plan.roles or TeamRole.BUILDER not in self.registry:
            return
        builder = self.registry.get(TeamRole.BUILDER)
        certifiers = (TeamRole.REVIEWER, TeamRole.QA, TeamRole.SAFETY_EVALUATION)
        reused = [
            role.value
            for role in certifiers
            if role in plan.roles and role in self.registry and self.registry.get(role) is builder
        ]
        if reused:
            raise ValueError(
                "Builder handler cannot certify its own work as: " + ", ".join(reused)
            )

    def _run_step(self, task: ProjectTask, step: TeamStep, context: Mapping[str, Any]) -> tuple[RoleResult, ...]:
        if self.parallel and step.parallel and len(step.roles) > 1:
            workers = min(self.max_workers, len(step.roles))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(self._run_role, role, task, step, dict(context)) for role in step.roles]
                return tuple(future.result() for future in futures)
        return tuple(self._run_role(role, task, step, dict(context)) for role in step.roles)

    def _run_role(self, role: TeamRole, task: ProjectTask, step: TeamStep, context: Mapping[str, Any]) -> RoleResult:
        if role is TeamRole.RELEASE and not context["external_actions_authorized"]:
            return RoleResult(
                role,
                RoleStatus.BLOCKED,
                "Release execution requires explicit external-action authorization.",
                reasons=("Set both release_requested and external_actions_authorized explicitly.",),
            )
        try:
            result = self.registry.get(role).run(task, step, context)
        except Exception as error:  # role runtimes are integration boundaries
            return RoleResult(
                role,
                RoleStatus.FAILED,
                f"Handler failed: {type(error).__name__}",
                reasons=("Exception details were intentionally omitted.",),
            )
        if not isinstance(result, RoleResult):
            return RoleResult(
                role,
                RoleStatus.FAILED,
                "Handler returned an invalid result.",
                reasons=("Expected a RoleResult instance.",),
            )
        if result.role is not role:
            return RoleResult(role, RoleStatus.FAILED, "Handler returned a result for the wrong role.", reasons=(f"expected {role.value}, received {result.role.value}",))
        return result
