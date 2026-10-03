"""Paired, prompt-free offline evaluation of single-model selection policies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from math import ceil, isfinite

from .models import Complexity, GatewayRequest, RouteDecision, TaskType
from .selector import ModelSelector


@dataclass(frozen=True, slots=True)
class ReplayOutcome:
    correct: bool
    cost_usd: float
    latency_ms: float

    def __post_init__(self) -> None:
        if type(self.correct) is not bool:
            raise ValueError("correct must be a measured binary outcome")
        for value in (self.cost_usd, self.latency_ms):
            if type(value) not in (int, float) or not isfinite(value) or value < 0:
                raise ValueError("replay costs and latencies must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class ReplayCase:
    case_id: str
    task_type: TaskType
    input_tokens: int
    output_tokens: int
    outcomes: Mapping[str, ReplayOutcome]  # catalog model identifiers

    def __post_init__(self) -> None:
        if not self.case_id or not isinstance(self.task_type, TaskType):
            raise ValueError("replay case requires an id and task type")
        if any(type(value) is not int or value < 1 for value in (
            self.input_tokens, self.output_tokens,
        )):
            raise ValueError("replay token estimates must be positive integers")


def replay_policies(
    cases: tuple[ReplayCase, ...],
    policies: Mapping[str, tuple[ModelSelector, GatewayRequest]],
    *, calibration_ids: frozenset[str],
) -> dict[str, dict[str, object]]:
    """Replay identical cases; abstentions count as uncovered, never as successes.

    The caller supplies outcomes for every eligible model, avoiding comparison on
    selectively logged chosen-model outcomes. This checks ID overlap, not semantic
    duplicates or whether the caller's labels and versions are trustworthy.
    """
    ids = {case.case_id for case in cases}
    if not cases or len(ids) != len(cases) or ids & calibration_ids:
        raise ValueError("replay requires unique, nonempty evaluation data disjoint from calibration")
    if not policies:
        raise ValueError("at least one replay policy is required")
    for selector, _ in policies.values():
        for case in cases:
            expected = {item.model for item in selector.catalog.candidates(case.task_type)}
            if not expected.issubset(case.outcomes):
                raise ValueError("paired replay requires outcomes for every eligible model")
    reports = {}
    for name, (selector, template) in policies.items():
        selected = []
        decisions = []
        for case in cases:
            request = replace(template, execute=False, context={
                **template.context, "estimated_input_tokens": case.input_tokens,
                "estimated_output_tokens": case.output_tokens,
            })
            decision = RouteDecision("llm.replay", case.task_type, Complexity.MEDIUM, 1, ())
            try:
                decision = selector.select(request, decision)
                model = decision.model
            except LookupError:
                model = None
            decisions.append({"case_id": case.case_id, "model": model})
            if model is not None:
                selected.append(case.outcomes[model])
        count = len(selected)
        correct = sum(item.correct for item in selected)
        latency = sorted(item.latency_ms for item in selected)
        total_cost = sum(item.cost_usd for item in selected)
        reports[name] = {
            "cases": len(cases), "answered": count, "abstained": len(cases) - count,
            "coverage": count / len(cases),
            "accuracy_on_answered": correct / count if count else None,
            "correct_per_input": correct / len(cases),
            "total_cost_usd": total_cost,
            "cost_per_correct": total_cost / correct if correct else None,
            "p95_latency_ms": latency[ceil(.95 * count) - 1] if count else None,
            "decisions": decisions,
            "scope": "single-model selection only; excludes router overhead and multi-call execution",
        }
    return reports
