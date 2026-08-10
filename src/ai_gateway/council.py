from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .models import (
    Complexity,
    CouncilMode,
    CouncilPlan,
    CouncilRequirementError,
    ExecutionStrategy,
    GatewayRequest,
    ModelCandidate,
    OptimizationGoal,
    RouteDecision,
    TaskType,
)


@dataclass(frozen=True, slots=True)
class CouncilPolicy:
    activation_threshold: float = 0.65
    review_cost_multiplier: float = 1.5
    synthesis_cost_multiplier: float = 1.5


class CouncilPlanner:
    """Decide whether multi-model deliberation is worth its extra cost and latency."""

    DELIBERATION = re.compile(
        r"\b(council|debate|multiple perspectives|second opinion|controversial|uncertain|"
        r"high[- ]stakes|critical decision|irreversible|independent opinions)\b",
        re.IGNORECASE,
    )

    def __init__(self, policy: CouncilPolicy | None = None) -> None:
        self.policy = policy or CouncilPolicy()

    def plan(self, request: GatewayRequest, decision: RouteDecision) -> RouteDecision:
        if request.execution_strategy not in (
            ExecutionStrategy.AUTO,
            ExecutionStrategy.COUNCIL,
        ):
            return self._attach(
                decision,
                request,
                False,
                f"Council was bypassed for explicit {request.execution_strategy.value} strategy.",
            )
        if request.council_mode is CouncilMode.NEVER:
            return self._attach(decision, request, False, "Council was disabled by request policy.")
        if decision.route == "blocked":
            return self._reject(decision, request, "Council is disabled for blocked requests.")
        if not decision.route.startswith("llm.") or decision.tools:
            return self._reject(
                decision,
                request,
                "Council is only compatible with direct LLM routes that do not use tools.",
            )
        if request.max_cost_usd is not None:
            return self._reject(
                decision,
                request,
                "Council is disabled when max_cost_usd is set because catalog estimates "
                "cannot guarantee a hard runtime spend limit without usage metering.",
            )

        members = self._diverse_members(decision.model_candidates, request.council_size)
        if len(members) < 2:
            return self._reject(
                decision,
                request,
                "Council requires at least two feasible models from the model selector.",
            )

        chairman = max(members, key=lambda candidate: (candidate.quality, candidate.score))
        estimated_cost = self._estimated_cost(members, chairman)
        estimated_latency = 2 * max(member.estimated_latency_ms for member in members)
        estimated_latency += chairman.estimated_latency_ms

        if request.max_latency_ms is not None and estimated_latency > request.max_latency_ms:
            return self._reject(
                decision,
                request,
                f"Council estimate {estimated_latency} ms exceeds the end-to-end latency limit.",
                estimated_cost=estimated_cost,
                estimated_latency=estimated_latency,
            )

        activation_score, signals = self._activation_score(request, decision)
        required = self._required(request)
        enabled = required or (
            decision.task_type is TaskType.REASONING
            and activation_score >= self.policy.activation_threshold
        )
        if required:
            reason = "Council was explicitly required and its estimated budget and latency fit."
        elif enabled:
            reason = "Council activated because " + ", ".join(signals) + "."
        elif decision.task_type is not TaskType.REASONING:
            reason = "Council auto mode is limited to open-ended reasoning tasks."
        else:
            reason = (
                f"Council activation score {activation_score:.2f} is below the "
                f"{self.policy.activation_threshold:.2f} threshold."
            )

        return self._attach(
            decision,
            request,
            enabled,
            reason,
            activation_score,
            members,
            chairman,
            estimated_cost,
            estimated_latency,
        )

    def _estimated_cost(
        self, members: tuple[ModelCandidate, ...], chairman: ModelCandidate
    ) -> float:
        stage1 = sum(member.estimated_cost_usd for member in members)
        review = stage1 * self.policy.review_cost_multiplier
        synthesis = chairman.estimated_cost_usd * self.policy.synthesis_cost_multiplier
        return round(stage1 + review + synthesis, 8)

    @classmethod
    def _reject(
        cls,
        decision: RouteDecision,
        request: GatewayRequest,
        reason: str,
        estimated_cost: float = 0.0,
        estimated_latency: int = 0,
    ) -> RouteDecision:
        if cls._required(request):
            raise CouncilRequirementError(reason)
        return cls._attach(
            decision,
            request,
            False,
            reason,
            estimated_cost=estimated_cost,
            estimated_latency=estimated_latency,
        )

    def _activation_score(
        self, request: GatewayRequest, decision: RouteDecision
    ) -> tuple[float, list[str]]:
        score = 0.0
        signals: list[str] = []
        if decision.task_type is TaskType.REASONING:
            score += 0.25
            signals.append("the task needs open-ended reasoning")
        if decision.complexity is Complexity.HIGH:
            score += 0.40
            signals.append("complexity is high")
        elif decision.complexity is Complexity.MEDIUM:
            score += 0.15
            signals.append("complexity is medium")
        if decision.confidence < 0.75:
            score += 0.15
            signals.append("route confidence is low")
        if request.context.get("stakes") == "high":
            score += 0.40
            signals.append("the application marked the decision high-stakes")
        if request.context.get("requires_consensus") is True:
            score += 0.40
            signals.append("the application requested independent consensus")
        if self.DELIBERATION.search(request.prompt):
            score += 0.40
            signals.append("the prompt asks for deliberation or independent perspectives")
        if request.optimization is OptimizationGoal.QUALITY:
            score += 0.10
            signals.append("the request prioritizes quality")
        elif request.optimization in (OptimizationGoal.COST, OptimizationGoal.LATENCY):
            score -= 0.25
            signals.append(f"the request prioritizes {request.optimization.value}")
        return max(0.0, min(1.0, score)), signals

    @staticmethod
    def _diverse_members(
        candidates: tuple[ModelCandidate, ...], size: int
    ) -> tuple[ModelCandidate, ...]:
        selected: list[ModelCandidate] = []
        providers: set[str] = set()
        for candidate in candidates:
            if candidate.provider not in providers:
                selected.append(candidate)
                providers.add(candidate.provider)
            if len(selected) == size:
                return tuple(selected)
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) == size:
                break
        return tuple(selected)

    @staticmethod
    def _attach(
        decision: RouteDecision,
        request: GatewayRequest,
        enabled: bool,
        reason: str,
        activation_score: float = 0.0,
        members: tuple[ModelCandidate, ...] = (),
        chairman: ModelCandidate | None = None,
        estimated_cost: float = 0.0,
        estimated_latency: int = 0,
    ) -> RouteDecision:
        plan = CouncilPlan(
            enabled=enabled,
            mode=request.council_mode,
            reason=reason,
            activation_score=round(activation_score, 4),
            member_models=tuple(member.model for member in members) if enabled else (),
            chairman_model=chairman.model if enabled and chairman else None,
            estimated_cost_usd=estimated_cost,
            estimated_latency_ms=estimated_latency,
            stages=("independent_answers", "blind_peer_review", "chairman_synthesis")
            if enabled
            else (),
        )
        return replace(decision, reasons=(*decision.reasons, reason), council_plan=plan)

    @staticmethod
    def _required(request: GatewayRequest) -> bool:
        return (
            request.council_mode is CouncilMode.ALWAYS
            or request.execution_strategy is ExecutionStrategy.COUNCIL
        )
