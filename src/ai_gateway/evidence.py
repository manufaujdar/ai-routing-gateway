"""Fixed-cohort quality gates. No model calls, learned router, or online claims.

The one-sided Hoeffding bound uses a union bound across the fixed record set.
It requires independent held-out binary outcomes representative of each deployed
task cohort. It is not a per-query correctness guarantee or conformal router.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from math import isfinite, log, sqrt

from .models import GatewayRequest, ModelCandidate, OptimizationGoal, RouteDecision, TaskType
from .selector import ModelCatalog, ModelSelector


@dataclass(frozen=True, slots=True)
class QualityEvidence:
    deployment_id: str
    task_type: TaskType
    model_version: str
    dataset_version: str
    samples: int
    successes: int
    evaluated_at: float

    def __post_init__(self) -> None:
        if type(self.samples) is not int or self.samples < 1:
            raise ValueError("samples must be a positive integer")
        if type(self.successes) is not int or not 0 <= self.successes <= self.samples:
            raise ValueError("successes must be an integer between zero and samples")
        if any(not isinstance(value, str) or not value.strip() for value in (
            self.deployment_id, self.model_version, self.dataset_version,
        )):
            raise ValueError("evidence requires nonempty deployment, model and dataset versions")
        if not isinstance(self.task_type, TaskType):
            raise TypeError("task_type must be a TaskType")
        if type(self.evaluated_at) not in (int, float) or not isfinite(self.evaluated_at):
            raise ValueError("evaluated_at must be a finite Unix timestamp")


@dataclass(frozen=True, slots=True)
class EvidencePolicy:
    records: tuple[QualityEvidence, ...]
    dataset_version: str = field(kw_only=True)
    minimum_samples: int = 100
    delta: float = .05
    max_age_seconds: float = 86400
    clock: Callable[[], float] = field(default=time.time, repr=False, compare=False)
    version: str = field(init=False)

    def __post_init__(self) -> None:
        minimum_samples, delta = self.minimum_samples, self.delta
        max_age_seconds, dataset_version = self.max_age_seconds, self.dataset_version
        if type(minimum_samples) is not int or minimum_samples < 1:
            raise ValueError("minimum_samples must be a positive integer")
        if type(delta) not in (int, float) or not 0 < delta < 1:
            raise ValueError("delta must be between zero and one")
        if (type(max_age_seconds) not in (int, float) or not isfinite(max_age_seconds)
                or max_age_seconds <= 0):
            raise ValueError("max_age_seconds must be finite and positive")
        if not isinstance(dataset_version, str) or not dataset_version.strip():
            raise ValueError("dataset_version is required")
        object.__setattr__(self, "records", tuple(self.records))
        keys = [(item.deployment_id, item.task_type) for item in self.records]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate deployment/task evidence")
        payload = json.dumps({
            "records": sorted((asdict(item) for item in self.records),
                              key=lambda item: (item["deployment_id"], item["task_type"])),
            "dataset_version": dataset_version, "minimum_samples": minimum_samples,
            "delta": delta, "max_age_seconds": max_age_seconds,
        }, sort_keys=True)
        object.__setattr__(self, "version", hashlib.sha256(payload.encode()).hexdigest()[:16])

    def select(self, catalog: ModelCatalog, request: GatewayRequest,
               decision: RouteDecision) -> RouteDecision:
        if request.min_quality is None:
            raise ValueError("evidence selection requires min_quality")
        now = self.clock()
        if not isfinite(now):
            raise ValueError("evidence clock must be finite")
        tokens = ModelSelector._estimated_tokens(request, decision)
        family_size = max(1, len(self.records))
        records = {(item.deployment_id, item.task_type): item for item in self.records}
        candidates = []
        receipts = []
        for profile in catalog.profiles:
            cost = ModelSelector._estimated_cost(profile, *tokens)
            latency = profile.p95_latency_ms
            record = records.get((profile.identity, decision.task_type))
            lower = None
            rejection = None
            if not profile.available or decision.task_type not in profile.task_types:
                rejection = "unavailable or unsupported task"
            elif request.allowed_models is not None and profile.model not in request.allowed_models:
                rejection = "not in allowed_models"
            elif not set(request.required_capabilities).issubset(profile.capabilities):
                rejection = "missing required capabilities"
            elif record is None:
                rejection = "missing quality evidence"
            elif record.dataset_version != self.dataset_version:
                rejection = "dataset version mismatch"
            elif record.model_version != profile.model_version:
                rejection = "model version mismatch"
            elif not 0 <= now - record.evaluated_at <= self.max_age_seconds:
                rejection = "stale or future-dated evidence"
            elif record.samples < self.minimum_samples:
                rejection = "insufficient quality samples"
            else:
                lower = max(0.0, record.successes / record.samples - sqrt(
                    log(family_size / self.delta) / (2 * record.samples)
                ))
                if lower < request.min_quality:
                    rejection = "quality lower bound below minimum"
                elif request.max_cost_usd is not None and cost > request.max_cost_usd:
                    rejection = "estimated cost exceeds budget"
                elif request.max_latency_ms is not None and (
                    latency <= 0 or latency > request.max_latency_ms
                ):
                    rejection = "p95 latency estimate missing or exceeds limit"
            receipts.append({
                "deployment_id": profile.identity, "model_version": profile.model_version,
                "samples": record.samples if record else 0,
                "quality_lower_bound": lower, "estimated_cost_usd": cost,
                "p95_latency_ms": latency, "rejection": rejection,
            })
            if rejection is None:
                candidates.append(ModelCandidate(
                    model=profile.model, provider=profile.provider, score=lower,
                    quality=lower, estimated_cost_usd=cost,
                    estimated_latency_ms=latency or profile.latency_ms,
                    deployment_id=profile.identity, estimated_ttft_ms=profile.ttft_ms,
                    success_probability=profile.success_probability,
                ))
        def rank(item):
            if request.optimization is OptimizationGoal.QUALITY:
                return -item.quality, item.estimated_cost_usd, item.estimated_latency_ms, item.model
            if request.optimization is OptimizationGoal.LATENCY:
                return item.estimated_latency_ms, item.estimated_cost_usd, -item.quality, item.model
            return item.estimated_cost_usd, item.estimated_latency_ms, -item.quality, item.model

        candidates.sort(key=rank)
        selected = candidates[0].model if candidates else None
        receipt = {
            "status": "selected" if selected else "abstained",
            "method": "hoeffding_fixed_cohort", "policy_version": self.version,
            "dataset_version": self.dataset_version, "delta": self.delta,
            "family_size": family_size, "evaluated_at": now,
            "quality_scope": "fixed task cohort; no per-query accuracy guarantee",
            "cost_source": "catalog estimate", "latency_source": "catalog p95 estimate",
            "candidates": receipts,
        }
        reason = (f"Evidence policy selected {selected} within the quality floor."
                  if selected else "Abstained: no model satisfies the evidence policy.")
        return replace(decision, model=selected, model_candidates=tuple(candidates),
                       selection_receipt=receipt, reasons=(*decision.reasons, reason))
