"""Server-owned execution limits and process-local provider circuit state."""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from math import isfinite
from types import MappingProxyType

from .budget import SQLiteBudgetLedger, _amount
from .models import ExecutionStrategy, GatewayRequest, GatewayResponse, RouteDecision
from .telemetry import InMemoryTelemetryStore, ModelCallResult


class CircuitOpen(RuntimeError):
    pass


class ExecutionLimitExceeded(RuntimeError):
    def __init__(self, message: str, result: ModelCallResult | None = None):
        super().__init__(message)
        self.result = result


@dataclass(slots=True)
class _CircuitState:
    epoch: int = 0
    failures: int = 0
    reopen_at: float | None = None
    probing: bool = False


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int = 3, cooldown_seconds: float = 30,
                 clock: Callable[[], float] = time.monotonic) -> None:
        if type(failure_threshold) is not int or failure_threshold < 1:
            raise ValueError("failure_threshold must be a positive integer")
        if (type(cooldown_seconds) not in (int, float) or not isfinite(cooldown_seconds)
                or cooldown_seconds <= 0):
            raise ValueError("cooldown_seconds must be finite and positive")
        self.failure_threshold, self.cooldown_seconds = failure_threshold, cooldown_seconds
        self.clock = clock
        self._states: dict[str, _CircuitState] = {}
        self._lock = threading.Lock()

    def acquire(self, deployment: str) -> int:
        with self._lock:
            state = self._states.setdefault(deployment, _CircuitState())
            if state.reopen_at is not None:
                if self.clock() < state.reopen_at or state.probing:
                    raise CircuitOpen("deployment circuit is open")
                state.probing = True
            return state.epoch

    def finish(self, deployment: str, epoch: int, *, success: bool) -> None:
        with self._lock:
            state = self._states[deployment]
            if state.epoch != epoch:
                return  # late completion from before the circuit changed state
            if success:
                state.failures = 0
                if state.probing:
                    state.epoch += 1
                    state.probing = False
                    state.reopen_at = None
            else:
                state.failures += 1
                if state.probing or state.failures >= self.failure_threshold:
                    state.epoch += 1
                    state.probing = False
                    state.reopen_at = self.clock() + self.cooldown_seconds

    def cancel(self, deployment: str, epoch: int) -> None:
        """Release a probe that was rejected locally before contacting the provider."""
        with self._lock:
            state = self._states[deployment]
            if state.epoch == epoch and state.probing:
                state.epoch += 1
                state.probing = False


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    timeout_ms: int | None = None
    max_output_tokens: int | None = None
    max_prompt_bytes: int | None = None
    max_model_calls: int = 17
    ledger: SQLiteBudgetLedger | None = field(default=None, repr=False)
    account: str | None = None
    charge_limits: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("timeout_ms", "max_output_tokens", "max_prompt_bytes", "max_model_calls"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError(f"{name} must be a positive integer")
        if self.timeout_ms is not None and self.timeout_ms > 300_000:
            raise ValueError("timeout_ms must not exceed 300000")
        if self.max_output_tokens is not None and self.max_output_tokens > 1_000_000:
            raise ValueError("max_output_tokens must not exceed 1000000")
        if type(self.max_model_calls) is not int or self.max_model_calls > 17:
            raise ValueError("max_model_calls must be between 1 and 17")
        for value in self.charge_limits.values():
            _amount(value)
        object.__setattr__(self, "charge_limits", MappingProxyType(dict(self.charge_limits)))
        if self.ledger is not None and (
            not self.account or not self.charge_limits or self.max_output_tokens is None
            or self.max_prompt_bytes is None
        ):
            raise ValueError("budget execution requires account, charge ceilings and prompt/output caps")
        if self.ledger is None and (self.account is not None or self.charge_limits):
            raise ValueError("account and charge ceilings require a ledger")


def planned_call_count(decision: RouteDecision) -> int:
    plan = decision.execution_plan
    if plan is None:
        return 0
    if plan.strategy is ExecutionStrategy.COUNCIL:
        return 2 * plan.sample_count + 1
    if plan.strategy is ExecutionStrategy.SELF_CONSISTENCY:
        return plan.sample_count + 1
    return len(plan.model_sequence)


def _minimum(*values: int | None) -> int | None:
    known = [value for value in values if value is not None]
    return min(known) if known else None


def _microusd(value: float, *, upper: bool) -> int:
    rounded = int((Decimal(str(value)) * 1_000_000).to_integral_value(
        rounding=ROUND_CEILING if upper else ROUND_FLOOR
    ))
    _amount(rounded)
    return rounded


class ControlledExecutionHandler:
    def __init__(self, caller, telemetry: InMemoryTelemetryStore, *, verifier=None,
                 policy: ExecutionPolicy | None = None, breaker: CircuitBreaker | None = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.caller, self.telemetry, self.verifier = caller, telemetry, verifier
        self.policy, self.breaker, self.clock = policy or ExecutionPolicy(), breaker, clock
        self.enforce_controls = self.policy != ExecutionPolicy() or breaker is not None

    def handle(self, request: GatewayRequest, decision: RouteDecision) -> GatewayResponse:
        from .council_handler import CouncilHandler
        from .execution import AdaptiveLLMHandler

        # Fresh attempt IDs prevent caller-supplied request IDs from replaying a charge.
        request = replace(request, context={**request.context,
            "request_id": str(request.context.get("request_id") or uuid.uuid4().hex)})
        session = _GuardedCaller(self.caller, request, decision, self.policy, self.breaker, self.clock)
        if decision.execution_plan.strategy is ExecutionStrategy.COUNCIL:
            handler = CouncilHandler(session, self.telemetry)
        else:
            handler = AdaptiveLLMHandler(session, self.telemetry, self.verifier)
        response = handler.handle(request, decision)
        session.remaining_seconds()  # verifier/aggregation time counts against the execution deadline
        response.metadata["execution_controls"] = {
            "admission_id": session.admission_id, "provider_calls": session.calls,
            "reservations": session.reservations,
            "max_output_tokens": session.output_limit,
            "deadline_semantics": "shared execution deadline; synchronous calls cannot be force-killed",
            "budget_semantics": "reserved operator-declared charge ceilings" if self.policy.ledger
                                else "planning estimates only",
        }
        return response


class _GuardedCaller:
    def __init__(self, caller, request, decision, policy, breaker, clock):
        self.caller, self.request, self.policy = caller, request, policy
        self.breaker, self.clock = breaker, clock
        self.admission_id = uuid.uuid4().hex
        self.calls = 0
        self.admissions = 0
        self.reservations: list[str] = []
        self.lock = threading.Lock()
        timeout = _minimum(policy.timeout_ms, request.execution_timeout_ms)
        self.deadline = clock() + timeout / 1000 if timeout is not None else None
        self.output_limit = _minimum(policy.max_output_tokens, request.max_output_tokens)
        self.call_limit = min(policy.max_model_calls, request.max_model_calls)
        self.deployments = {item.model: item.deployment_id for item in decision.model_candidates}
        self.request_limit = (_microusd(request.max_cost_usd, upper=False)
                              if request.max_cost_usd is not None and policy.ledger else None)
        if planned_call_count(decision) > self.call_limit:
            raise ValueError("plan exceeds server max_model_calls")
        if (timeout is not None or self.output_limit is not None) and not callable(
            getattr(caller, "complete_with_limits", None)
        ):
            raise ValueError("execution limits require an adapter implementing complete_with_limits")
        if policy.ledger is not None:
            for model in decision.execution_plan.model_sequence:
                if self.deployments[model] not in policy.charge_limits:
                    raise ValueError("missing operator charge ceiling for planned deployment")

    def remaining_seconds(self) -> float | None:
        if self.deadline is None:
            return None
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise ExecutionLimitExceeded("execution deadline exhausted")
        return remaining

    def complete(self, model: str, prompt: str) -> str:
        return self.complete_with_metrics(model, prompt).text

    def complete_with_metrics(self, model: str, prompt: str) -> ModelCallResult:
        remaining = self.remaining_seconds()
        if self.policy.max_prompt_bytes is not None and len(prompt.encode()) > self.policy.max_prompt_bytes:
            raise ExecutionLimitExceeded("expanded prompt exceeds server byte cap")
        deployment = self.deployments[model]
        attempt_id = uuid.uuid4().hex
        ledger = self.policy.ledger
        with self.lock:
            if self.admissions >= self.call_limit:
                raise ExecutionLimitExceeded("max_model_calls exhausted")
            # Count before dispatch, including in-flight calls from parallel strategies.
            self.admissions += 1
        if ledger is not None:
            ledger.reserve(self.policy.account, self.request.context["request_id"], attempt_id,
                           self.policy.charge_limits[deployment],
                           request_limit_microusd=self.request_limit)
            with self.lock:
                self.reservations.append(attempt_id)
        permit = None
        try:
            if self.breaker is not None:
                permit = self.breaker.acquire(deployment)
            remaining = self.remaining_seconds()
        except Exception:
            if ledger is not None:
                ledger.settle(self.policy.account, attempt_id, 0)
            if permit is not None:
                self.breaker.cancel(deployment, permit)
            raise
        result = None
        with self.lock:
            self.calls += 1
        try:
            if remaining is not None or self.output_limit is not None:
                raw = self.caller.complete_with_limits(model, prompt, timeout_seconds=remaining,
                                                       max_output_tokens=self.output_limit)
            elif callable(getattr(self.caller, "complete_with_metrics", None)):
                raw = self.caller.complete_with_metrics(model, prompt)
            else:
                raw = self.caller.complete(model, prompt)
            result = raw if isinstance(raw, ModelCallResult) else ModelCallResult(text=raw)
            if (ledger is not None and result.cost_usd is not None and
                ledger.settle(self.policy.account, attempt_id, _microusd(result.cost_usd, upper=True))):
                raise ExecutionLimitExceeded("provider exceeded declared charge ceiling", result)
            if self.output_limit is not None and result.output_tokens is not None and (
                result.output_tokens > self.output_limit
            ):
                raise ExecutionLimitExceeded("provider exceeded output token cap", result)
            self.remaining_seconds()
            if not result.text.strip():
                raise ExecutionLimitExceeded("provider returned empty output", result)
        except Exception:
            if permit is not None:
                self.breaker.finish(deployment, permit, success=False)
            if result is not None:
                raise ExecutionLimitExceeded("controlled execution failed", result) from None
            raise
        if permit is not None:
            self.breaker.finish(deployment, permit, success=True)
        return result
