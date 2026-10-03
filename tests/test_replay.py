import pytest

from ai_gateway import GatewayRequest, build_container
from ai_gateway.models import TaskType
from ai_gateway.replay import ReplayCase, ReplayOutcome, replay_policies


def setup_case():
    selector = build_container().router.model_selector
    case = ReplayCase("test-1", TaskType.CHAT, 10, 20, {
        "gpt-4.1-mini": ReplayOutcome(False, .01, 20),
    })
    return selector, case


def test_replay_uses_measured_outcomes_and_keeps_abstentions_in_denominator():
    selector, case = setup_case()
    report = replay_policies((case,), {
        "weighted": (selector, GatewayRequest("unused")),
        "evidence": (selector, GatewayRequest("unused", selection_mode="evidence", min_quality=.9)),
    }, calibration_ids=frozenset({"train-1"}))
    assert report["weighted"]["total_cost_usd"] == .01
    assert report["weighted"]["accuracy_on_answered"] == 0
    assert report["weighted"]["cost_per_correct"] is None
    assert report["evidence"]["abstained"] == 1
    assert report["evidence"]["correct_per_input"] == 0
    assert report["evidence"]["accuracy_on_answered"] is None


def test_replay_rejects_calibration_leakage():
    selector, case = setup_case()
    with pytest.raises(ValueError, match="disjoint"):
        replay_policies((case,), {"a": (selector, GatewayRequest("unused"))},
                        calibration_ids=frozenset({"test-1"}))


def test_replay_rejects_missing_counterfactual_outcomes():
    selector, _ = setup_case()
    case = ReplayCase("test-1", TaskType.REASONING, 10, 20, {})
    with pytest.raises(ValueError, match="every eligible model"):
        replay_policies((case,), {"a": (selector, GatewayRequest("unused"))},
                        calibration_ids=frozenset())
