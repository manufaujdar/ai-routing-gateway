from ai_gateway import GatewayRequest, build_container

gateway = build_container().router
response = gateway.route(
    GatewayRequest(
        prompt="Compare two deployment strategies",
        execute=False,
    )
)

print(response.decision.to_dict())
