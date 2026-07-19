from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from .models import Complexity, GatewayRequest, RouteDecision, TaskType


class Evaluator(Protocol):
    def evaluate(self, request: GatewayRequest) -> RouteDecision: ...


@dataclass(frozen=True, slots=True)
class RoutingConfig:
    fast_model: str = "gpt-4.1-mini"
    reasoning_model: str = "o4-mini"
    code_model: str = "gpt-4.1"


class RuleBasedEvaluator:
    """Transparent baseline evaluator; replace or compose with an LLM classifier later."""

    CURRENT = re.compile(r"\b(latest|today|current|news|weather|price|score|recent)\b", re.I)
    VISION = re.compile(r"\b(image|photo|picture|screenshot|diagram|visual)\b", re.I)
    CODE = re.compile(
        r"\b(code|bug|debug|function|class|api|sql|python|javascript|typescript|repository)\b",
        re.I,
    )
    REASONING = re.compile(
        r"\b(analy[sz]e|compare|plan|strategy|evaluate|recommend|trade-?offs?|step by step)\b",
        re.I,
    )
    HIGH_RISK = re.compile(
        r"\b(steal (?:a )?password|deploy ransomware|make a bomb|bypass authentication)\b",
        re.I,
    )

    def __init__(self, config: RoutingConfig | None = None) -> None:
        self.config = config or RoutingConfig()

    def evaluate(self, request: GatewayRequest) -> RouteDecision:
        prompt = request.prompt.strip()
        if not prompt:
            raise ValueError("prompt must not be empty")

        if self.HIGH_RISK.search(prompt):
            decision = RouteDecision(
                route="blocked",
                task_type=TaskType.UNSAFE,
                complexity=Complexity.HIGH,
                confidence=0.98,
                reasons=("Prompt matched a high-risk safety rule.",),
                risk_flags=("high_risk_request",),
            )
        elif self.CURRENT.search(prompt):
            decision = RouteDecision(
                route="tool.web_search",
                task_type=TaskType.SEARCH,
                complexity=Complexity.MEDIUM,
                confidence=0.88,
                reasons=("Prompt appears to require current external information.",),
                tools=("web_search",),
                model=self.config.fast_model,
            )
        elif self.VISION.search(prompt):
            decision = RouteDecision(
                route="tool.vision",
                task_type=TaskType.VISION,
                complexity=Complexity.MEDIUM,
                confidence=0.85,
                reasons=("Prompt refers to visual input or output.",),
                tools=("vision",),
                model=self.config.fast_model,
            )
        elif self.CODE.search(prompt):
            decision = RouteDecision(
                route="llm.code",
                task_type=TaskType.CODE,
                complexity=self._complexity(prompt),
                confidence=0.84,
                reasons=("Prompt contains software-engineering intent.",),
                model=self.config.code_model,
            )
        elif self.REASONING.search(prompt) or self._complexity(prompt) is Complexity.HIGH:
            decision = RouteDecision(
                route="llm.reasoning",
                task_type=TaskType.REASONING,
                complexity=self._complexity(prompt),
                confidence=0.80,
                reasons=("Prompt benefits from deliberate multi-step reasoning.",),
                model=self.config.reasoning_model,
            )
        else:
            decision = RouteDecision(
                route="llm.fast",
                task_type=TaskType.CHAT,
                complexity=self._complexity(prompt),
                confidence=0.72,
                reasons=("No specialized capability was required.",),
                model=self.config.fast_model,
            )

        return self._enforce_policy(decision, request)

    @staticmethod
    def _complexity(prompt: str) -> Complexity:
        words = len(prompt.split())
        if words > 120 or prompt.count("\n") >= 5:
            return Complexity.HIGH
        if words > 35 or prompt.count("?") > 1:
            return Complexity.MEDIUM
        return Complexity.LOW

    @staticmethod
    def _enforce_policy(decision: RouteDecision, request: GatewayRequest) -> RouteDecision:
        if request.allowed_routes is not None and decision.route not in request.allowed_routes:
            raise PermissionError(f"route '{decision.route}' is not allowed for this request")
        return decision
