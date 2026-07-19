from __future__ import annotations

import argparse
import json

from .container import build_container
from .models import CouncilMode, GatewayRequest, OptimizationGoal


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate and route an AI prompt")
    parser.add_argument("prompt")
    parser.add_argument("--decision-only", action="store_true")
    parser.add_argument(
        "--optimize",
        choices=[goal.value for goal in OptimizationGoal],
        default=OptimizationGoal.BALANCED.value,
    )
    parser.add_argument("--max-cost-usd", type=float)
    parser.add_argument("--max-latency-ms", type=int)
    parser.add_argument("--min-quality", type=float)
    parser.add_argument(
        "--council",
        choices=[mode.value for mode in CouncilMode],
        default=CouncilMode.AUTO.value,
        help="Use council automatically, always, or never",
    )
    parser.add_argument("--council-size", type=int, default=3)
    args = parser.parse_args()
    response = build_container().router.route(
        GatewayRequest(
            prompt=args.prompt,
            execute=not args.decision_only,
            optimization=OptimizationGoal(args.optimize),
            max_cost_usd=args.max_cost_usd,
            max_latency_ms=args.max_latency_ms,
            min_quality=args.min_quality,
            council_mode=CouncilMode(args.council),
            council_size=args.council_size,
        )
    )
    print(json.dumps(response.to_dict(), indent=2))


if __name__ == "__main__":
    main()
