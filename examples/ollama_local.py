"""Call an already-installed Ollama model without a cloud API key."""

import os

from ai_gateway.adapters import OpenAICompatibleModelCaller


def main() -> None:
    model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
    caller = OpenAICompatibleModelCaller(
        api_key="ollama",  # Required by the client library; ignored by local Ollama.
        base_url="http://127.0.0.1:11434/v1",
        allow_insecure_loopback=True,
    )
    print(caller.complete(model, "Reply with exactly LOCAL_OK"))


if __name__ == "__main__":
    main()
