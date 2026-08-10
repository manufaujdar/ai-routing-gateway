from __future__ import annotations

import sys
from types import ModuleType

import pytest

from ai_gateway.adapters import OpenAICompatibleModelCaller


def _install_recording_openai(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    created_clients: list[dict[str, object]] = []
    module = ModuleType("openai")

    class RecordingOpenAI:
        def __init__(self, **kwargs: object) -> None:
            created_clients.append(kwargs)

    module.OpenAI = RecordingOpenAI
    monkeypatch.setitem(sys.modules, "openai", module)
    return created_clients


@pytest.mark.parametrize(
    "base_url",
    [
        "https://api.example.com/v1",
        "https://api.example.com:8443/openai/v1",
        "https://127.0.0.1/v1",
    ],
)
def test_https_base_urls_are_accepted_without_network(
    base_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_clients = _install_recording_openai(monkeypatch)

    OpenAICompatibleModelCaller("test-key", base_url)

    assert created_clients == [
        {"api_key": "test-key", "base_url": base_url, "timeout": 120.0}
    ]


@pytest.mark.parametrize(
    "base_url",
    [
        "http://localhost:8000/v1",
        "http://localhost.:8000/v1",
        "http://127.0.0.1:8000/v1",
        "http://127.99.1.2:8000/v1",
        "http://[::1]:8000/v1",
    ],
)
def test_explicit_insecure_loopback_base_urls_are_accepted_without_network(
    base_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_clients = _install_recording_openai(monkeypatch)

    OpenAICompatibleModelCaller(
        "test-key",
        base_url,
        allow_insecure_loopback=True,
    )

    assert len(created_clients) == 1


@pytest.mark.parametrize(
    "base_url",
    [
        "http://localhost:8000/v1",
        "http://127.0.0.1:8000/v1",
        "http://[::1]:8000/v1",
        "http://api.example.com/v1",
        "http://127.0.0.1.example.com/v1",
        "https://user@example.com/v1",
        "https://user:password@example.com/v1",
        "https://example.com/v1?api-version=1",
        "https://example.com/v1#fragment",
        "https://example.com:invalid/v1",
        "https://bad_host.example/v1",
        "https://example..com/v1",
        "https://example.com/%not-escaped",
        "https://example.com\\@localhost/v1",
        "https://",
        "https:///v1",
        "example.com/v1",
        "ftp://example.com/v1",
        "",
        None,
    ],
)
def test_unsafe_or_malformed_base_urls_are_rejected_before_client_creation(
    base_url: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_clients = _install_recording_openai(monkeypatch)

    with pytest.raises(ValueError, match="base_url"):
        OpenAICompatibleModelCaller("test-key", base_url)

    assert created_clients == []


@pytest.mark.parametrize(
    "base_url",
    [
        "http://api.example.com/v1",
        "http://127.0.0.1.example.com/v1",
        "http://192.168.1.20:8000/v1",
    ],
)
def test_insecure_loopback_option_still_rejects_external_http(
    base_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_clients = _install_recording_openai(monkeypatch)

    with pytest.raises(ValueError, match="HTTP is allowed only for loopback"):
        OpenAICompatibleModelCaller(
            "test-key",
            base_url,
            allow_insecure_loopback=True,
        )

    assert created_clients == []


@pytest.mark.parametrize("invalid_flag", ["true", "false", 1, 0, None])
def test_insecure_loopback_option_requires_a_boolean(
    invalid_flag: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_clients = _install_recording_openai(monkeypatch)

    with pytest.raises(ValueError, match="allow_insecure_loopback must be a boolean"):
        OpenAICompatibleModelCaller(
            "test-key",
            "http://127.0.0.1:8000/v1",
            allow_insecure_loopback=invalid_flag,
        )

    assert created_clients == []
