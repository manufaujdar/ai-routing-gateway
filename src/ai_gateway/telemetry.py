from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, replace
from typing import Any

from .models import ExecutionStrategy, TaskType


@dataclass(frozen=True, slots=True)
class ModelCallResult:
    text: str
    provider: str | None = None
    deployment_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: float | None = None
    ttft_ms: float | None = None
    finish_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CallObservation:
    request_id: str
    route: str
    task_type: TaskType
    strategy: ExecutionStrategy
    stage: str
    model: str
    provider: str
    deployment_id: str
    success: bool
    latency_ms: float
    ttft_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    cost_usd: float | None = None
    verifier_score: float | None = None
    error_type: str | None = None
    created_at: float = 0.0


@dataclass(frozen=True, slots=True)
class DeploymentAggregate:
    deployment_id: str
    model: str
    provider: str
    task_type: TaskType
    calls: int
    successes: int
    success_rate: float
    average_latency_ms: float
    p95_latency_ms: float
    average_ttft_ms: float | None
    total_cost_usd: float
    average_verifier_score: float | None
    average_feedback_score: float | None


class InMemoryTelemetryStore:
    """Thread-safe, prompt-free observations for local routing adaptation."""

    def __init__(self, max_observations: int = 10_000) -> None:
        if max_observations < 1:
            raise ValueError("max_observations must be positive")
        self.max_observations = max_observations
        self._observations: list[CallObservation] = []
        self._feedback: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def record(self, observation: CallObservation) -> None:
        if not observation.request_id:
            raise ValueError("telemetry request_id must not be empty")
        if observation.latency_ms < 0:
            raise ValueError("telemetry latency must not be negative")
        stamped = observation if observation.created_at else replace(
            observation, created_at=time.time()
        )
        with self._lock:
            self._observations.append(stamped)
            if len(self._observations) > self.max_observations:
                del self._observations[: len(self._observations) - self.max_observations]

    def record_feedback(self, request_id: str, score: float) -> None:
        if not request_id:
            raise ValueError("feedback request_id must not be empty")
        if not 0 <= score <= 1:
            raise ValueError("feedback score must be between 0 and 1")
        with self._lock:
            self._feedback.setdefault(request_id, []).append(score)

    @property
    def observations(self) -> tuple[CallObservation, ...]:
        with self._lock:
            return tuple(self._observations)

    def aggregates(self) -> tuple[DeploymentAggregate, ...]:
        with self._lock:
            observations = tuple(self._observations)
            feedback = {key: tuple(values) for key, values in self._feedback.items()}
        groups: dict[tuple[str, TaskType], list[CallObservation]] = {}
        for observation in observations:
            groups.setdefault(
                (observation.deployment_id, observation.task_type), []
            ).append(observation)

        aggregates: list[DeploymentAggregate] = []
        for (deployment_id, task_type), calls in sorted(
            groups.items(), key=lambda item: (item[0][0], item[0][1].value)
        ):
            latencies = sorted(call.latency_ms for call in calls)
            ttfts = [call.ttft_ms for call in calls if call.ttft_ms is not None]
            verifier_scores = [
                call.verifier_score for call in calls if call.verifier_score is not None
            ]
            feedback_scores = [
                score for call in calls for score in feedback.get(call.request_id, ())
            ]
            successes = sum(call.success for call in calls)
            aggregates.append(
                DeploymentAggregate(
                    deployment_id=deployment_id,
                    model=calls[0].model,
                    provider=calls[0].provider,
                    task_type=task_type,
                    calls=len(calls),
                    successes=successes,
                    success_rate=round(successes / len(calls), 6),
                    average_latency_ms=round(sum(latencies) / len(latencies), 3),
                    p95_latency_ms=round(_percentile(latencies, 0.95), 3),
                    average_ttft_ms=(
                        round(sum(ttfts) / len(ttfts), 3) if ttfts else None
                    ),
                    total_cost_usd=round(
                        sum(call.cost_usd or 0.0 for call in calls), 8
                    ),
                    average_verifier_score=(
                        round(sum(verifier_scores) / len(verifier_scores), 6)
                        if verifier_scores
                        else None
                    ),
                    average_feedback_score=(
                        round(sum(feedback_scores) / len(feedback_scores), 6)
                        if feedback_scores
                        else None
                    ),
                )
            )
        return tuple(aggregates)

    def summary(self) -> dict[str, Any]:
        observations = self.observations
        return {
            "privacy": "prompt and response content are not stored",
            "observation_count": len(observations),
            "successful_calls": sum(observation.success for observation in observations),
            "failed_calls": sum(not observation.success for observation in observations),
            "total_cost_usd": round(
                sum(observation.cost_usd or 0.0 for observation in observations), 8
            ),
            "deployments": [asdict(aggregate) for aggregate in self.aggregates()],
        }


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    index = min(len(values) - 1, max(0, round((len(values) - 1) * quantile)))
    return values[index]
