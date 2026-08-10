from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any

from .models import TaskType
from .selector import ModelProfile
from .telemetry import DeploymentAggregate, InMemoryTelemetryStore


@dataclass(frozen=True, slots=True)
class RoutingPolicyProposal:
    version: str
    status: str
    sample_count: int
    recommendations: tuple[dict[str, Any], ...]
    promotion_gate: str
    automatic_changes_applied: bool = False


class AdaptiveRoutingAgent:
    """Prompt-free contextual-bandit advisor over observed deployment outcomes.

    The agent influences ranking only after a minimum sample count. It proposes
    policy changes but never mutates configuration, publishes, or calls a model.
    """

    def __init__(
        self,
        telemetry: InMemoryTelemetryStore,
        *,
        minimum_samples: int = 5,
        maximum_adjustment: float = 0.12,
    ) -> None:
        if minimum_samples < 1:
            raise ValueError("minimum_samples must be positive")
        if not 0 <= maximum_adjustment <= 0.5:
            raise ValueError("maximum_adjustment must be between 0 and 0.5")
        self.telemetry = telemetry
        self.minimum_samples = minimum_samples
        self.maximum_adjustment = maximum_adjustment

    def adjustment(self, profile: ModelProfile, task_type: TaskType) -> float:
        aggregates = self._matching(profile, task_type)
        calls = sum(aggregate.calls for aggregate in aggregates)
        if calls < self.minimum_samples:
            return 0.0
        success = _weighted(aggregates, "success_rate")
        verifier = _optional_weighted(aggregates, "average_verifier_score")
        feedback = _optional_weighted(aggregates, "average_feedback_score")
        observed_quality = feedback if feedback is not None else verifier
        if observed_quality is None:
            observed_quality = success
        exploitation = 0.65 * observed_quality + 0.35 * success
        total_calls = max(1, len(self.telemetry.observations))
        exploration = min(1.0, math.sqrt(2 * math.log(total_calls + 1) / calls))
        centered = (exploitation - 0.5) * 0.16 + exploration * 0.02
        return round(
            max(-self.maximum_adjustment, min(self.maximum_adjustment, centered)),
            6,
        )

    def propose(self) -> RoutingPolicyProposal:
        aggregates = self.telemetry.aggregates()
        sample_count = sum(aggregate.calls for aggregate in aggregates)
        recommendations: list[dict[str, Any]] = []
        for task_type in TaskType:
            task_aggregates = [
                aggregate for aggregate in aggregates if aggregate.task_type is task_type
            ]
            if not task_aggregates:
                continue
            ranked = sorted(
                task_aggregates,
                key=lambda aggregate: (
                    -_aggregate_utility(aggregate),
                    aggregate.average_latency_ms,
                    aggregate.deployment_id,
                ),
            )
            best = ranked[0]
            recommendations.append(
                {
                    "task_type": task_type.value,
                    "preferred_deployment": best.deployment_id,
                    "observed_utility": round(_aggregate_utility(best), 6),
                    "samples": best.calls,
                    "reason": (
                        "Highest observed quality/reliability utility after latency and cost "
                        "penalties; validate with replay and canary before promotion."
                    ),
                }
            )
        status = "ready_for_offline_evaluation" if sample_count >= self.minimum_samples else (
            "insufficient_evidence"
        )
        content = json.dumps(recommendations, sort_keys=True, separators=(",", ":"))
        version = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        return RoutingPolicyProposal(
            version=f"proposal-{version}",
            status=status,
            sample_count=sample_count,
            recommendations=tuple(recommendations),
            promotion_gate=(
                "Replay on a versioned evaluation set, pass safety/cost/latency gates, then "
                "require explicit maintainer approval and canary rollout."
            ),
        )

    def report(self) -> dict[str, Any]:
        return asdict(self.propose())

    def _matching(
        self, profile: ModelProfile, task_type: TaskType
    ) -> tuple[DeploymentAggregate, ...]:
        return tuple(
            aggregate
            for aggregate in self.telemetry.aggregates()
            if aggregate.deployment_id == profile.identity
            and aggregate.task_type is task_type
        )


def _weighted(aggregates: tuple[DeploymentAggregate, ...], field: str) -> float:
    total = sum(aggregate.calls for aggregate in aggregates)
    return sum(getattr(aggregate, field) * aggregate.calls for aggregate in aggregates) / total


def _optional_weighted(
    aggregates: tuple[DeploymentAggregate, ...], field: str
) -> float | None:
    available = [
        aggregate for aggregate in aggregates if getattr(aggregate, field) is not None
    ]
    if not available:
        return None
    return _weighted(tuple(available), field)


def _aggregate_utility(aggregate: DeploymentAggregate) -> float:
    quality = (
        aggregate.average_feedback_score
        if aggregate.average_feedback_score is not None
        else aggregate.average_verifier_score
        if aggregate.average_verifier_score is not None
        else aggregate.success_rate
    )
    latency_penalty = min(0.25, aggregate.average_latency_ms / 100_000)
    cost_per_call = aggregate.total_cost_usd / max(1, aggregate.calls)
    cost_penalty = min(0.25, cost_per_call * 10)
    return quality * 0.7 + aggregate.success_rate * 0.3 - latency_penalty - cost_penalty
