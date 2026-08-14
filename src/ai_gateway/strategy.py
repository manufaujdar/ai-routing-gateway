from __future__ import annotations

from dataclasses import replace

from .models import (
    ExecutionPlan,
    ExecutionStrategy,
    GatewayRequest,
    ModelCandidate,
    OptimizationGoal,
    RouteDecision,
    StrategyRequirementError,
    TaskType,
)


class ExecutionPlanner:
    """Choose a bounded execution pattern after route and model selection."""

    def plan(self, request: GatewayRequest, decision: RouteDecision) -> RouteDecision:
        requested = request.execution_strategy
        if decision.route == "blocked" or decision.tools:
            if requested not in (ExecutionStrategy.AUTO, ExecutionStrategy.SINGLE):
                raise StrategyRequirementError(
                    f"strategy '{requested.value}' is incompatible with route '{decision.route}'"
                )
            return self._attach(
                decision,
                ExecutionPlan(
                    strategy=ExecutionStrategy.SINGLE,
                    reason="Specialized tool and blocked routes use their registered handler.",
                    model_sequence=(decision.model,) if decision.model else (),
                ),
            )

        if requested is ExecutionStrategy.COUNCIL:
            council = decision.council_plan
            if council is None or not council.enabled:
                raise StrategyRequirementError("requested council strategy is not available")
            return self._attach(
                decision,
                ExecutionPlan(
                    strategy=ExecutionStrategy.COUNCIL,
                    reason="A multi-model council was explicitly requested and passed policy.",
                    model_sequence=council.member_models,
                    estimated_cost_usd=council.estimated_cost_usd,
                    estimated_latency_ms=council.estimated_latency_ms,
                    verifier_threshold=request.verifier_threshold,
                    sample_count=len(council.member_models),
                ),
            )

        if requested is ExecutionStrategy.CASCADE:
            return self._attach(decision, self._cascade(request, decision, required=True))
        if requested is ExecutionStrategy.SELF_CONSISTENCY:
            return self._attach(decision, self._self_consistency(request, decision))
        if requested is ExecutionStrategy.SINGLE:
            return self._attach(decision, self._single(request, decision, "Single model requested."))

        council = decision.council_plan
        if council is not None and council.enabled:
            return self._attach(
                decision,
                ExecutionPlan(
                    strategy=ExecutionStrategy.COUNCIL,
                    reason="Auto strategy used the council selected by council policy.",
                    model_sequence=council.member_models,
                    estimated_cost_usd=council.estimated_cost_usd,
                    estimated_latency_ms=council.estimated_latency_ms,
                    verifier_threshold=request.verifier_threshold,
                    sample_count=len(council.member_models),
                ),
            )
        if (
            request.optimization is OptimizationGoal.COST
            and decision.task_type in (TaskType.REASONING, TaskType.CODE)
            and len(decision.model_candidates) >= 2
        ):
            cascade = self._cascade(request, decision, required=False)
            if len(cascade.model_sequence) >= 2:
                return self._attach(decision, cascade)
        if (
            request.optimization is OptimizationGoal.QUALITY
            and decision.task_type in (TaskType.REASONING, TaskType.CODE)
            and decision.complexity.value == "high"
        ):
            try:
                return self._attach(decision, self._self_consistency(request, decision))
            except StrategyRequirementError:
                pass
        return self._attach(
            decision,
            self._single(request, decision, "Auto strategy selected one model."),
        )

    def _cascade(
        self,
        request: GatewayRequest,
        decision: RouteDecision,
        *,
        required: bool,
    ) -> ExecutionPlan:
        candidates = sorted(
            decision.model_candidates,
            key=lambda candidate: (
                candidate.estimated_cost_usd,
                candidate.estimated_latency_ms,
                -candidate.quality,
                candidate.model,
            ),
        )[: request.strategy_model_limit]
        selected: list[ModelCandidate] = []
        cost = 0.0
        latency = 0
        for candidate in candidates:
            next_cost = cost + candidate.estimated_cost_usd
            next_latency = latency + candidate.estimated_latency_ms
            if request.max_cost_usd is not None and next_cost > request.max_cost_usd:
                continue
            if request.max_latency_ms is not None and next_latency > request.max_latency_ms:
                continue
            selected.append(candidate)
            cost = next_cost
            latency = next_latency
        if len(selected) < 2:
            if required:
                raise StrategyRequirementError(
                    "cascade requires at least two models within the total cost and latency budget"
                )
            return self._single(
                request,
                decision,
                "Cascade was not feasible; auto strategy fell back to one model.",
            )
        return ExecutionPlan(
            strategy=ExecutionStrategy.CASCADE,
            reason=(
                "Use lower-cost models first and escalate only when deterministic verification "
                "does not accept the response."
            ),
            model_sequence=tuple(candidate.model for candidate in selected),
            estimated_cost_usd=round(cost, 8),
            estimated_latency_ms=latency,
            verifier_threshold=request.verifier_threshold,
            sample_count=len(selected),
        )

    def _self_consistency(
        self, request: GatewayRequest, decision: RouteDecision
    ) -> ExecutionPlan:
        candidate = self._selected_candidate(decision)
        cost = candidate.estimated_cost_usd * (request.self_consistency_samples + 1)
        latency = candidate.estimated_latency_ms * 2
        self._require_budget(request, cost, latency, "self-consistency")
        return ExecutionPlan(
            strategy=ExecutionStrategy.SELF_CONSISTENCY,
            reason=(
                "Generate independent samples from the selected model and aggregate only when "
                "the quality budget permits."
            ),
            model_sequence=(candidate.model,),
            estimated_cost_usd=round(cost, 8),
            estimated_latency_ms=latency,
            verifier_threshold=request.verifier_threshold,
            sample_count=request.self_consistency_samples,
        )

    def _single(
        self, request: GatewayRequest, decision: RouteDecision, reason: str
    ) -> ExecutionPlan:
        candidate = self._selected_candidate(decision)
        self._require_budget(
            request,
            candidate.estimated_cost_usd,
            candidate.estimated_latency_ms,
            "single-model",
        )
        return ExecutionPlan(
            strategy=ExecutionStrategy.SINGLE,
            reason=reason,
            model_sequence=(candidate.model,),
            estimated_cost_usd=candidate.estimated_cost_usd,
            estimated_latency_ms=candidate.estimated_latency_ms,
            verifier_threshold=request.verifier_threshold,
        )

    @staticmethod
    def _selected_candidate(decision: RouteDecision) -> ModelCandidate:
        for candidate in decision.model_candidates:
            if candidate.model == decision.model:
                return candidate
        raise StrategyRequirementError("execution strategy requires a selected model candidate")

    @staticmethod
    def _require_budget(
        request: GatewayRequest,
        cost: float,
        latency: int,
        label: str,
    ) -> None:
        if request.max_cost_usd is not None and cost > request.max_cost_usd:
            raise StrategyRequirementError(
                f"{label} estimate ${cost:.6f} exceeds the total cost budget"
            )
        if request.max_latency_ms is not None and latency > request.max_latency_ms:
            raise StrategyRequirementError(
                f"{label} estimate {latency} ms exceeds the total latency budget"
            )

    @staticmethod
    def _attach(decision: RouteDecision, plan: ExecutionPlan) -> RouteDecision:
        return replace(
            decision,
            execution_plan=plan,
            reasons=(*decision.reasons, plan.reason),
        )
