"""Synthetic integration example, not a model-performance benchmark. No network."""

import json
from dataclasses import replace

from ai_gateway import (
    EvidencePolicy,
    GatewayRequest,
    ModelCatalog,
    QualityEvidence,
    build_container,
)
from ai_gateway.models import TaskType
from ai_gateway.replay import ReplayCase, ReplayOutcome, replay_policies


def main() -> None:
    base = build_container()
    profiles = tuple(replace(item, model_version="synthetic-v1") for item in base.catalog.profiles)
    catalog = ModelCatalog(profiles)
    evidence = tuple(QualityEvidence(
        deployment_id=item.identity, task_type=TaskType.REASONING,
        model_version="synthetic-v1", dataset_version="synthetic-calibration-v1",
        samples=1000, successes=960 if index == 0 else 990, evaluated_at=100,
    ) for index, item in enumerate(profiles[:2]))
    policy = EvidencePolicy(evidence, dataset_version="synthetic-calibration-v1", clock=lambda: 101)
    container = build_container(model_catalog=catalog, evidence_policy=policy)
    request = GatewayRequest("Compare deployment options", execute=False,
                             selection_mode="evidence", min_quality=.9, max_latency_ms=3000)
    response = container.router.route(request)
    # Invented outcomes solely exercise the replay API. Real adoption needs independent labels.
    cases = tuple(ReplayCase(f"test-{index}", TaskType.REASONING, 100, 200, {
        profiles[0].model: ReplayOutcome(index != 0, .001, 300 + index * 10),
        profiles[1].model: ReplayOutcome(True, .005, 900 + index * 10),
    }) for index in range(5))
    reports = replay_policies(cases, {
        "evidence": (container.router.model_selector, request),
        "weighted": (container.router.model_selector, replace(request, selection_mode="weighted")),
    }, calibration_ids=frozenset(f"calibration-{index}" for index in range(1000)))
    print(json.dumps({"synthetic": True, "decision": response.to_dict(), "replay": reports}, indent=2))


if __name__ == "__main__":
    main()
