from __future__ import annotations

import threading
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from math import ceil, isfinite
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

    def __post_init__(self) -> None:
        _validate_metrics(self)
        if not isinstance(self.text, str):
            raise TypeError("response text must be a string")


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
    quality_score: float | None = None
    estimated_cost_usd: float | None = None
    is_final: bool = False


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
    total_cost_usd: float | None
    average_verifier_score: float | None
    average_feedback_score: float | None
    quality_samples: int
    average_quality_score: float | None
    unpriced_calls: int


class InMemoryTelemetryStore:
    """Thread-safe, prompt-free observations for local routing adaptation."""

    def __init__(self, max_observations: int = 10_000) -> None:
        if type(max_observations) is not int or max_observations < 1:
            raise ValueError("max_observations must be positive")
        self.max_observations = max_observations
        self._observations: list[CallObservation] = []
        self._feedback: dict[str, float] = {}
        self._lock = threading.Lock()

    def record(self, observation: CallObservation) -> None:
        if not observation.request_id:
            raise ValueError("telemetry request_id must not be empty")
        _validate_metrics(observation)
        stamped = observation if observation.created_at else replace(
            observation, created_at=time.time()
        )
        with self._lock:
            self._observations.append(stamped)
            if len(self._observations) > self.max_observations:
                del self._observations[: len(self._observations) - self.max_observations]
                retained = {item.request_id for item in self._observations}
                self._feedback = {key: value for key, value in self._feedback.items()
                                  if key in retained}

    def record_feedback(self, request_id: str, score: float) -> None:
        if not request_id:
            raise ValueError("feedback request_id must not be empty")
        if type(score) not in (int, float) or not isfinite(score) or not 0 <= score <= 1:
            raise ValueError("feedback score must be between 0 and 1")
        with self._lock:
            if not any(item.request_id == request_id for item in self._observations):
                raise ValueError("feedback request_id is unknown or expired")
            self._feedback[request_id] = score

    def mark_final(self, request_id: str, stage: str) -> None:
        """Attribute outcome feedback to the actual returned attempt only."""
        with self._lock:
            self._observations = [
                replace(item, is_final=item.stage == stage) if item.request_id == request_id
                else item for item in self._observations
            ]

    @property
    def observations(self) -> tuple[CallObservation, ...]:
        with self._lock:
            return tuple(self._observations)

    def aggregates(self) -> tuple[DeploymentAggregate, ...]:
        with self._lock:
            observations = tuple(self._observations)
            feedback = dict(self._feedback)
        return self._aggregate_snapshot(observations, feedback)

    @staticmethod
    def _aggregate_snapshot(
        observations: tuple[CallObservation, ...], feedback: dict[str, float],
    ) -> tuple[DeploymentAggregate, ...]:
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
                feedback[call.request_id] for call in calls
                if call.request_id in feedback and (call.is_final or call.stage == "single")
            ]
            quality_scores = [
                feedback[call.request_id]
                if call.request_id in feedback and (call.is_final or call.stage == "single")
                else call.quality_score
                for call in calls
                if call.quality_score is not None or (
                    call.request_id in feedback and (call.is_final or call.stage == "single")
                )
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
                    total_cost_usd=_known_total(calls),
                    unpriced_calls=sum(call.cost_usd is None for call in calls),
                    quality_samples=len(quality_scores),
                    average_quality_score=(sum(quality_scores) / len(quality_scores)
                                           if quality_scores else None),
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
        with self._lock:
            observations = tuple(self._observations)
            feedback = dict(self._feedback)
        return {
            "privacy": "prompt and response content are not stored",
            "observation_count": len(observations),
            "successful_calls": sum(observation.success for observation in observations),
            "failed_calls": sum(not observation.success for observation in observations),
            "total_cost_usd": _known_total(observations),
            "known_cost_usd": round(sum(item.cost_usd or 0 for item in observations), 8),
            "unpriced_calls": sum(item.cost_usd is None for item in observations),
            "deployments": [asdict(item) for item in self._aggregate_snapshot(observations, feedback)],
        }


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    index = min(len(values) - 1, max(0, ceil(len(values) * quantile) - 1))
    return values[index]


def _known_total(observations: Sequence[CallObservation]) -> float | None:
    if any(item.cost_usd is None for item in observations):
        return None
    return round(sum(item.cost_usd for item in observations), 8)


def _validate_metrics(value: ModelCallResult | CallObservation) -> None:
    for name in ("cost_usd", "latency_ms", "ttft_ms", "estimated_cost_usd", "created_at"):
        number = getattr(value, name, None)
        if number is not None and (
            type(number) not in (int, float) or not isfinite(number) or number < 0
        ):
            raise ValueError(f"{name} must be finite and nonnegative")
    for name in ("input_tokens", "output_tokens", "cached_tokens"):
        number = getattr(value, name, None)
        if number is not None and (type(number) is not int or number < 0):
            raise ValueError(f"{name} must be a nonnegative integer")
    for name in ("verifier_score", "quality_score"):
        number = getattr(value, name, None)
        if number is not None and (
            type(number) not in (int, float) or not isfinite(number) or not 0 <= number <= 1
        ):
            raise ValueError(f"{name} must be between zero and one")


def summarize_usage(observations: tuple[CallObservation, ...]) -> dict[str, Any]:
    unpriced = sum(item.cost_usd is None for item in observations)
    usage = {
        "calls": len(observations), "unpriced_calls": unpriced,
        "known_cost_usd": round(sum(item.cost_usd or 0 for item in observations), 8),
        "cost_usd": _known_total(observations),
        "provider_duration_sum_ms": round(sum(item.latency_ms for item in observations), 3),
        "cost_source": "provider_reported" if not unpriced else "incomplete",
    }
    for name in ("input_tokens", "output_tokens", "cached_tokens"):
        values = [getattr(item, name) for item in observations]
        usage[name] = sum(values) if all(value is not None for value in values) else None
    return usage
