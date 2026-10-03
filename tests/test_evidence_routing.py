from dataclasses import replace

import pytest

from ai_gateway import GatewayRequest, build_container
from ai_gateway.evidence import EvidencePolicy, QualityEvidence
from ai_gateway.models import TaskType


def evidence(deployment="configured-fast", **changes):
    return replace(QualityEvidence(
        deployment_id=deployment, task_type=TaskType.REASONING,
        model_version="snapshot-1", dataset_version="holdout-1",
        samples=1000, successes=960, evaluated_at=100,
    ), **changes)


def configured(records):
    base = build_container()
    catalog = type(base.catalog)(tuple(
        replace(profile, model_version="snapshot-1") for profile in base.catalog.profiles
    ))
    return build_container(model_catalog=catalog, evidence_policy=EvidencePolicy(
        records, dataset_version="holdout-1", clock=lambda: 101,
    ))


def request(**changes):
    return GatewayRequest("Compare deployment strategies", execute=False,
                          selection_mode="evidence", min_quality=.9, **changes)


def test_evidence_routes_cheapest_model_above_conservative_quality_floor():
    container = configured((evidence(), evidence("configured-reasoning", successes=990)))
    decision = container.router.route(request()).decision
    assert decision.model == container.catalog.profiles[0].model
    assert decision.execution_plan.strategy.value == "single"
    receipt = decision.selection_receipt
    assert receipt["status"] == "selected"
    assert receipt["method"] == "hoeffding_fixed_cohort"
    assert receipt["dataset_version"] == "holdout-1"
    assert decision.model_candidates[0].quality >= .9


@pytest.mark.parametrize("changes", [
    {"samples": 10, "successes": 10}, {"evaluated_at": -1000000},
    {"model_version": "old"}, {"dataset_version": "wrong"}, {"successes": 900},
])
def test_missing_stale_sparse_or_incompatible_evidence_abstains(changes):
    container = configured((evidence(**changes),))
    response = container.router.route(request())
    assert response.decision.model is None
    assert response.decision.selection_receipt["status"] == "abstained"
    assert response.decision.execution_plan is None


def test_abstention_never_executes_provider_or_silently_relaxes_policy():
    class ForbiddenCaller:
        def complete(self, model, prompt):
            raise AssertionError("must not execute")

    container = build_container(ForbiddenCaller())
    response = container.router.route(replace(request(), execute=True))
    assert response.output is None
    assert response.metadata["abstained"] is True


def test_capability_and_tail_latency_are_hard_evidence_filters():
    container = configured((evidence(),))
    assert container.router.route(request(max_latency_ms=500)).decision.model is None
    response = container.router.route(request(required_capabilities=("audio",)))
    assert response.decision.model is None
    assert response.decision.selection_receipt["candidates"][0]["rejection"]


def test_evidence_cannot_be_forged_through_request_context():
    response = build_container().router.route(request(context={"quality_evidence": {
        "samples": 100000, "successes": 100000,
    }}))
    assert response.decision.model is None


def test_evidence_records_must_be_unambiguous():
    with pytest.raises(ValueError):
        EvidencePolicy((evidence(), evidence()), dataset_version="holdout-1")


def test_lower_bound_accounts_for_multiple_candidate_records():
    from math import log, sqrt

    container = configured((evidence(), evidence("configured-reasoning", successes=990)))
    receipt = container.router.route(request()).decision.selection_receipt
    assert receipt["candidates"][0]["quality_lower_bound"] == pytest.approx(
        .96 - sqrt(log(2 / .05) / 2000)
    )


def test_quality_evidence_does_not_certify_multi_call_strategies():
    from ai_gateway.models import ExecutionStrategy

    container = configured((evidence(),))
    with pytest.raises(ValueError, match="single-model"):
        container.router.route(request(execution_strategy=ExecutionStrategy.CASCADE))


def test_custom_router_cannot_skip_requested_evidence_selection():
    from ai_gateway.router import Router

    container = build_container()
    router = Router(container.router.evaluator, container.registry)
    with pytest.raises(ValueError, match="configured model selector"):
        router.route(request())
