"""Synthetic economics, not measured model performance or a production router.

Run from the repository root: python3 docs/company/experiments/tradeoffs.py
All amounts, quality probabilities, and latencies are invented assumptions.
Floating point is used for illustration only, not billing or reservations.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    name: str
    quality: float
    cost_usd: float
    latency_paths: tuple[tuple[float, float], ...]  # probability, milliseconds

    def __post_init__(self) -> None:
        if not math.isfinite(self.quality) or not 0 <= self.quality <= 1:
            raise ValueError("quality must be a finite probability")
        if not math.isfinite(self.cost_usd) or self.cost_usd < 0:
            raise ValueError("cost must be finite and nonnegative")
        if not self.latency_paths or any(
            not math.isfinite(p) or not 0 <= p <= 1 or not math.isfinite(ms) or ms < 0
            for p, ms in self.latency_paths
        ):
            raise ValueError("invalid latency distribution")
        if not math.isclose(sum(p for p, _ in self.latency_paths), 1.0):
            raise ValueError("latency path probabilities must sum to one")

    def miss_rate(self, deadline_ms: float) -> float:
        return sum(p for p, ms in self.latency_paths if ms > deadline_ms)

    def p95_ms(self) -> float:
        cumulative = 0.0
        for probability, milliseconds in sorted(self.latency_paths, key=lambda p: p[1]):
            cumulative += probability
            if cumulative >= 0.95:
                return milliseconds
        return max(ms for _, ms in self.latency_paths)


def cascade(
    false_accept: float, false_reject: float, rescue_quality: float = 0.98
) -> Plan:
    """false_accept=P(accept|wrong), false_reject=P(reject|correct).

    rescue_quality is P(strong correct | cheap rejected), not the strong model's
    unconditional quality. Verifier cost/time is paid on every cheap attempt.
    The strong answer is returned without another modeled verifier.
    """
    for value in (false_accept, false_reject, rescue_quality):
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("rates must be finite probabilities")
    cheap_quality = 0.85
    escalate = cheap_quality * false_reject + (1 - cheap_quality) * (1 - false_accept)
    correct_accepted = cheap_quality * (1 - false_reject)
    return Plan(
        "cascade",
        correct_accepted + escalate * rescue_quality,
        0.0001 + 0.001 + 0.0002 + escalate * 0.01,
        ((1 - escalate, 470.0), (escalate, 2870.0)),
    )


def choose(
    plans: tuple[Plan, ...], quality_floor: float, deadline_ms: float, miss_limit: float
) -> str:
    if not math.isfinite(quality_floor) or not 0 <= quality_floor <= 1:
        raise ValueError("quality floor must be a finite probability")
    if not math.isfinite(miss_limit) or not 0 <= miss_limit <= 1:
        raise ValueError("miss limit must be a finite probability")
    if not math.isfinite(deadline_ms) or deadline_ms < 0:
        raise ValueError("deadline must be finite and nonnegative")
    feasible = [
        p for p in plans
        if p.quality >= quality_floor and p.miss_rate(deadline_ms) <= miss_limit
    ]
    if not feasible:
        return "abstain"
    return min(feasible, key=lambda p: (p.cost_usd, p.miss_rate(deadline_ms), p.name)).name


def main() -> None:
    plans = (
        Plan("fast", 0.85, 0.0011, ((1.0, 420.0),)),
        Plan("middle", 0.94, 0.0031, ((1.0, 920.0),)),
        Plan("strong", 0.97, 0.0101, ((1.0, 2420.0),)),
        cascade(0.05, 0.10),
    )
    poor = cascade(0.60, 0.05)
    rows = []
    for plan in (*plans, poor):
        rows.append({
            "plan": "poor_verifier_cascade" if plan is poor else plan.name,
            "quality_assumption": round(plan.quality, 6),
            "expected_cost_usd": round(plan.cost_usd, 6),
            "cost_per_success_usd": round(plan.cost_usd / plan.quality, 6),
            "expected_latency_ms": round(sum(p * ms for p, ms in plan.latency_paths), 3),
            "modeled_p95_ms": plan.p95_ms(),
            "miss_rate_at_2000_ms": round(plan.miss_rate(2000), 6),
        })
    print(json.dumps({
        "warning": "SYNTHETIC ASSUMPTIONS ONLY; no providers called or measured",
        "plans": rows,
        "interactive_92pct_2000ms": choose(plans, 0.92, 2000, 0.05),
        "quality_95pct_5000ms": choose(plans, 0.95, 5000, 0.05),
        "impossible_99pct_2000ms": choose(plans, 0.99, 2000, 0.05),
    }, indent=2))


if __name__ == "__main__":
    main()
