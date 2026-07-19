from __future__ import annotations


class OpenAICompatibleModelCaller:
    """Optional adapter for OpenAI-compatible gateways such as OpenRouter or Vercel."""

    def __init__(self, api_key: str, base_url: str, timeout: float = 120.0) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        if not base_url.startswith(("https://", "http://")):
            raise ValueError("base_url must be an HTTP(S) URL")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("install the 'openai' optional dependency to use this adapter") from error
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def complete(self, model: str, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError(f"model '{model}' returned an empty response")
        return content
