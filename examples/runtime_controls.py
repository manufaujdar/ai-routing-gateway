"""Offline accounting example; all prices and provider results are synthetic."""

from pathlib import Path
from tempfile import TemporaryDirectory

from ai_gateway import (
    CircuitBreaker,
    ExecutionPolicy,
    GatewayRequest,
    ModelCallResult,
    SQLiteBudgetLedger,
    build_container,
)


class FixtureCaller:
    def complete_with_limits(self, model, prompt, *, timeout_seconds, max_output_tokens):
        assert 0 < timeout_seconds <= 1
        assert max_output_tokens == 100
        return ModelCallResult("Synthetic answer.", cost_usd=0.000010, output_tokens=3)


with TemporaryDirectory() as directory:
    ledger = SQLiteBudgetLedger(Path(directory) / "budget.sqlite")
    ledger.configure_account("demo", 100)  # 100 micro-USD; fake amounts, not provider prices
    policy = ExecutionPolicy(
        timeout_ms=1000, max_output_tokens=100, max_prompt_bytes=10000,
        ledger=ledger, account="demo",
        charge_limits={"configured-fast": 30, "configured-reasoning": 40, "configured-code": 40},
    )
    gateway = build_container(FixtureCaller(), execution_policy=policy,
                              circuit_breaker=CircuitBreaker())
    result = gateway.router.route(GatewayRequest("Hello"))
    print("SYNTHETIC OFFLINE EXAMPLE", result.metadata["execution_controls"])
    print(ledger.snapshot("demo"))
    assert ledger.snapshot("demo")["spent_microusd"] == 10
    assert ledger.snapshot("demo")["reserved_microusd"] == 0
