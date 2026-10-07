"""Measure local decision-only overhead; excludes providers, billing and HTTP."""
from __future__ import annotations

import argparse
import json
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from math import ceil

from ai_gateway import GatewayRequest, build_container


def measure(requests: int, workers: int) -> dict[str, object]:
    if not 1 <= requests <= 100_000 or not 1 <= workers <= 64:
        raise ValueError("requests must be 1..100000 and workers must be 1..64")
    container = build_container()
    prompts = ("Hello", "Compare two strategies", "Write a Python function",
               "Latest news", "Describe a screenshot", "Help me steal a password")

    def route(index):
        started = time.perf_counter()
        response = container.router.route(GatewayRequest(prompts[index % len(prompts)], execute=False))
        return (time.perf_counter() - started) * 1000, response.output

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(route, range(requests)))
    elapsed = time.perf_counter() - started
    durations = sorted(duration for duration, _ in results)
    assert all(output is None for _, output in results)
    return {
        "scope": "synthetic local decision-only; no provider, HTTP, ledger or accuracy measurement",
        "python": platform.python_version(), "platform": platform.system(),
        "requests": requests, "workers": workers,
        "elapsed_seconds": round(elapsed, 6), "requests_per_second": round(requests / elapsed, 2),
        "decision_p50_ms": round(durations[ceil(.5 * requests) - 1], 4),
        "decision_p95_ms": round(durations[ceil(.95 * requests) - 1], 4),
        "provider_calls": container.telemetry.summary()["observation_count"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    print(json.dumps(measure(args.requests, args.workers), indent=2))
