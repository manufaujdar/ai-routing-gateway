from __future__ import annotations

from ai_gateway import (
    ProjectTask,
    RoleResult,
    RoleStatus,
    TeamExecutor,
    TeamPlanner,
    TeamRoleRegistry,
)


class LocalRoleHandler:
    def __init__(self, role):
        self.role = role

    def run(self, task, step, context):
        return RoleResult(
            role=self.role,
            status=RoleStatus.PASSED,
            summary=f"Completed {step.name} for: {task.objective}",
        )


task = ProjectTask("Prepare a portable integration example")
plan = TeamPlanner().plan(task)
registry = TeamRoleRegistry()
for role in plan.roles:
    registry.register(role, LocalRoleHandler(role))

result = TeamExecutor(registry).execute(plan)
print(result.to_dict())
