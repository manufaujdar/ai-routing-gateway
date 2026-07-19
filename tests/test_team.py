from __future__ import annotations

from dataclasses import dataclass
from threading import Barrier
from typing import Any, Mapping

import pytest

from ai_gateway import (
    ProjectTask,
    ProjectTaskKind,
    RoleResult,
    RoleStatus,
    TeamExecutor,
    TeamPlanner,
    TeamRole,
    TeamRoleRegistry,
)
from ai_gateway.team import TeamStep


def test_feature_plan_is_deterministic_and_explainable() -> None:
    task = ProjectTask(
        "Add tenant-aware routing",
        requires_research=True,
        user_facing=True,
        affects_ai_policy=True,
        high_stakes=True,
        ambiguous=True,
        hard_to_reverse=True,
        multiple_viable_approaches=True,
        independent_views_useful=True,
        council_resources_fit=True,
        marketing_requested=True,
        release_requested=True,
    )

    first = TeamPlanner().plan(task)
    second = TeamPlanner().plan(task)

    assert first == second
    assert [step.name for step in first.steps] == [
        "coordinate",
        "discover",
        "design",
        "build",
        "certify",
        "document",
        "position",
        "release",
    ]
    assert first.steps[4].roles == (
        TeamRole.REVIEWER,
        TeamRole.QA,
        TeamRole.SAFETY_EVALUATION,
    )
    assert all(step.reason for step in first.steps)
    assert first.council_recommended is True


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (ProjectTaskKind.RESEARCH, {TeamRole.TEAM_LEAD, TeamRole.RESEARCH, TeamRole.PLANNER}),
        (ProjectTaskKind.REVIEW, {TeamRole.TEAM_LEAD, TeamRole.REVIEWER}),
        (ProjectTaskKind.QA, {TeamRole.TEAM_LEAD, TeamRole.QA}),
        (
            ProjectTaskKind.DOCUMENTATION,
            {TeamRole.TEAM_LEAD, TeamRole.DOCUMENTATION},
        ),
        (ProjectTaskKind.MARKETING, {TeamRole.TEAM_LEAD, TeamRole.MARKETER}),
    ],
)
def test_focused_task_kinds_keep_the_team_minimal(
    kind: ProjectTaskKind, expected: set[TeamRole]
) -> None:
    plan = TeamPlanner().plan(ProjectTask("Focused work", kind=kind))
    assert set(plan.roles) == expected


def test_routine_work_does_not_recommend_a_council() -> None:
    plan = TeamPlanner().plan(ProjectTask("Fix typo", kind=ProjectTaskKind.BUGFIX))
    assert plan.council_recommended is False
    assert plan.council_reasons


def test_council_requires_every_eligibility_condition() -> None:
    plan = TeamPlanner().plan(
        ProjectTask(
            "Choose an architecture",
            high_stakes=True,
            ambiguous=True,
            hard_to_reverse=True,
            multiple_viable_approaches=True,
            independent_views_useful=True,
            council_resources_fit=False,
        )
    )
    assert plan.council_recommended is False
    assert any("cost and latency" in reason for reason in plan.council_reasons)


def test_invalid_task_is_rejected() -> None:
    with pytest.raises(ValueError, match="objective"):
        ProjectTask("   ")
    with pytest.raises(ValueError, match="external actions"):
        ProjectTask("test", external_actions_authorized=True)


@dataclass
class RecordingHandler:
    role: TeamRole
    calls: list[TeamRole]
    status: RoleStatus = RoleStatus.PASSED
    barrier: Barrier | None = None

    def run(
        self, task: ProjectTask, step: TeamStep, context: Mapping[str, Any]
    ) -> RoleResult:
        self.calls.append(self.role)
        if self.barrier is not None:
            self.barrier.wait(timeout=2)
        return RoleResult(self.role, self.status, f"{self.role.value} complete")


def _registry_for(plan, calls, *, blocked_role=None, barrier=None):
    registry = TeamRoleRegistry()
    for role in plan.roles:
        status = RoleStatus.BLOCKED if role is blocked_role else RoleStatus.PASSED
        registry.register(
            role,
            RecordingHandler(
                role,
                calls,
                status,
                barrier if role in {TeamRole.REVIEWER, TeamRole.QA} else None,
            ),
        )
    return registry


def test_executor_preflights_all_handlers_before_running() -> None:
    plan = TeamPlanner().plan(ProjectTask("Build feature"))
    calls: list[TeamRole] = []
    registry = TeamRoleRegistry()
    registry.register(TeamRole.TEAM_LEAD, RecordingHandler(TeamRole.TEAM_LEAD, calls))

    with pytest.raises(LookupError, match="no team handlers registered"):
        TeamExecutor(registry).execute(plan)
    assert calls == []


def test_failed_certification_stops_documentation_and_release() -> None:
    plan = TeamPlanner().plan(ProjectTask("Build feature", release_requested=True))
    calls: list[TeamRole] = []
    registry = _registry_for(plan, calls, blocked_role=TeamRole.REVIEWER)

    run = TeamExecutor(registry).execute(plan)

    assert run.succeeded is False
    assert run.stopped_at == "certify"
    assert TeamRole.QA in calls
    assert TeamRole.DOCUMENTATION not in calls
    assert TeamRole.RELEASE not in calls


def test_parallel_certification_returns_results_in_plan_order() -> None:
    plan = TeamPlanner().plan(
        ProjectTask("Fix issue", kind=ProjectTaskKind.BUGFIX, documentation_requested=False)
    )
    calls: list[TeamRole] = []
    registry = _registry_for(plan, calls, barrier=Barrier(2))

    run = TeamExecutor(registry, parallel=True).execute(plan)

    assert run.succeeded is True
    certification = [result.role for result in run.results[-2:]]
    assert certification == [TeamRole.REVIEWER, TeamRole.QA]


def test_handler_exception_is_an_observable_failure() -> None:
    class BrokenHandler:
        def run(self, task, step, context):
            raise RuntimeError("private details")

    task = ProjectTask("Verify", kind=ProjectTaskKind.QA)
    plan = TeamPlanner().plan(task)
    registry = TeamRoleRegistry()
    registry.register(
        TeamRole.TEAM_LEAD,
        RecordingHandler(TeamRole.TEAM_LEAD, []),
    )
    registry.register(TeamRole.QA, BrokenHandler())

    run = TeamExecutor(registry).execute(plan)

    assert run.succeeded is False
    assert run.results[-1].status is RoleStatus.FAILED
    assert run.results[-1].summary == "Handler failed: RuntimeError"
    assert "private details" not in " ".join(run.results[-1].reasons)


def test_release_handler_is_not_called_without_explicit_authorization() -> None:
    task = ProjectTask(
        "Prepare release",
        kind=ProjectTaskKind.RELEASE,
        documentation_requested=False,
    )
    plan = TeamPlanner().plan(task)
    calls: list[TeamRole] = []
    registry = _registry_for(plan, calls)

    run = TeamExecutor(registry).execute(plan)

    assert run.succeeded is False
    assert run.stopped_at == "release"
    assert run.results[-1].role is TeamRole.RELEASE
    assert run.results[-1].status is RoleStatus.BLOCKED
    assert TeamRole.RELEASE not in calls


def test_explicitly_authorized_release_handler_can_run() -> None:
    task = ProjectTask(
        "Perform release",
        kind=ProjectTaskKind.RELEASE,
        release_requested=True,
        external_actions_authorized=True,
        documentation_requested=False,
    )
    plan = TeamPlanner().plan(task)
    calls: list[TeamRole] = []

    run = TeamExecutor(_registry_for(plan, calls)).execute(plan)

    assert run.succeeded is True
    assert TeamRole.RELEASE in calls


def test_registry_rejects_accidental_replacement() -> None:
    registry = TeamRoleRegistry()
    handler = RecordingHandler(TeamRole.QA, [])
    registry.register(TeamRole.QA, handler)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(TeamRole.QA, handler)
    registry.register(TeamRole.QA, handler, replace=True)


def test_malformed_handler_result_is_an_observable_failure() -> None:
    class MalformedHandler:
        def run(self, task, step, context):
            return None

    task = ProjectTask("Verify", kind=ProjectTaskKind.QA)
    plan = TeamPlanner().plan(task)
    registry = TeamRoleRegistry()
    registry.register(TeamRole.TEAM_LEAD, RecordingHandler(TeamRole.TEAM_LEAD, []))
    registry.register(TeamRole.QA, MalformedHandler())

    run = TeamExecutor(registry).execute(plan)

    assert run.succeeded is False
    assert run.results[-1].summary == "Handler returned an invalid result."


def test_builder_handler_cannot_be_reused_for_certification() -> None:
    plan = TeamPlanner().plan(ProjectTask("Build feature", documentation_requested=False))
    registry = TeamRoleRegistry()
    shared = RecordingHandler(TeamRole.BUILDER, [])
    for role in plan.roles:
        handler = (
            shared
            if role in {TeamRole.BUILDER, TeamRole.REVIEWER}
            else RecordingHandler(role, [])
        )
        registry.register(role, handler)

    with pytest.raises(ValueError, match="cannot certify its own work"):
        TeamExecutor(registry).execute(plan)
