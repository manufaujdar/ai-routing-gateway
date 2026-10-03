"""Check the research illustration's decision-relevant arithmetic and limits."""

import importlib.util
import sys
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "docs/company/experiments/tradeoffs.py"
SPEC = importlib.util.spec_from_file_location("company_tradeoffs", PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_cascade_counts_false_accepts_and_conditional_rescue() -> None:
    plan = MODULE.cascade(0.05, 0.1)
    assert plan.quality == pytest.approx(0.98795)
    assert plan.cost_usd == pytest.approx(0.003575)
    assert plan.miss_rate(2000) == pytest.approx(0.2275)
    assert plan.p95_ms() == 2870


def test_accept_everything_degenerates_to_cheap_quality_with_verifier_overhead() -> None:
    plan = MODULE.cascade(1.0, 0.0)
    assert plan.quality == pytest.approx(0.85)
    assert plan.cost_usd == pytest.approx(0.0013)
    assert plan.miss_rate(2000) == 0


def test_reject_everything_pays_both_and_uses_conditional_rescue_quality() -> None:
    plan = MODULE.cascade(0.0, 1.0, rescue_quality=0.6)
    assert plan.quality == pytest.approx(0.6)
    assert plan.cost_usd == pytest.approx(0.0113)
    assert plan.miss_rate(2000) == 1


def test_quality_floor_and_deadline_change_best_route() -> None:
    plans = (
        MODULE.Plan("middle", 0.94, 0.0031, ((1.0, 920),)),
        MODULE.Plan("strong", 0.97, 0.0101, ((1.0, 2420),)),
        MODULE.cascade(0.05, 0.1),
    )
    assert MODULE.choose(plans, 0.92, 2000, 0.05) == "middle"
    assert MODULE.choose(plans, 0.95, 5000, 0.05) == "cascade"
    assert MODULE.choose(plans, 0.99, 2000, 0.05) == "abstain"


def test_cheap_but_bad_verifier_does_not_satisfy_quality_floor() -> None:
    poor = MODULE.cascade(0.6, 0.05)
    assert poor.quality == pytest.approx(0.90795)
    assert MODULE.choose((poor,), 0.95, 5000, 0.05) == "abstain"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.01, 1.01])
def test_invalid_probability_is_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        MODULE.cascade(value, 0.1)


def test_invalid_latency_distribution_is_rejected() -> None:
    with pytest.raises(ValueError):
        MODULE.Plan("bad", 0.9, 0.01, ((0.2, 400), (0.2, 2400)))
