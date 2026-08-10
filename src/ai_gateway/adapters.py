from __future__ import annotations

import re
from ipaddress import ip_address
from urllib.parse import urlsplit

_HOST_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")
_PERCENT_ESCAPE = re.compile(r"%[0-9A-Fa-f]{2}")


def _is_loopback(hostname: str) -> bool:
    if hostname.rstrip(".").lower() == "localhost":
        return True
    try:
        return ip_address(hostname).is_loopback
    except ValueError:
        return False


def _has_valid_percent_escapes(value: str) -> bool:
    index = 0
    while (index := value.find("%", index)) != -1:
        if _PERCENT_ESCAPE.fullmatch(value[index : index + 3]) is None:
            return False
        index += 3
    return True


def _is_valid_hostname(hostname: str) -> bool:
    try:
        ip_address(hostname)
        return True
    except ValueError:
        pass

    try:
        ascii_hostname = hostname.rstrip(".").encode("idna").decode("ascii")
    except UnicodeError:
        return False
    return bool(ascii_hostname) and all(
        _HOST_LABEL.fullmatch(label) is not None
        for label in ascii_hostname.split(".")
    )


def _validate_base_url(base_url: str, *, allow_insecure_loopback: bool) -> None:
    if (
        not isinstance(base_url, str)
        or not base_url
        or any(character.isspace() or ord(character) < 32 for character in base_url)
        or not _has_valid_percent_escapes(base_url)
    ):
        raise ValueError("base_url must be a well-formed HTTP(S) URL")

    try:
        parsed = urlsplit(base_url)
        hostname = parsed.hostname
        _ = parsed.port  # force urllib to validate the port
    except ValueError as error:
        raise ValueError("base_url must be a well-formed HTTP(S) URL") from error

    if parsed.scheme not in {"http", "https"} or not parsed.netloc or hostname is None:
        raise ValueError("base_url must be a well-formed HTTP(S) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("base_url must not include userinfo")
    if not _is_valid_hostname(hostname):
        raise ValueError("base_url must contain a valid hostname")
    if parsed.query or parsed.fragment:
        raise ValueError("base_url must not include a query or fragment")
    if parsed.scheme == "http" and not (
        allow_insecure_loopback and _is_loopback(hostname)
    ):
        raise ValueError(
            "base_url must use HTTPS; HTTP is allowed only for loopback when "
            "allow_insecure_loopback=True"
        )


class OpenAICompatibleModelCaller:
    """Optional adapter for OpenAI-compatible gateways such as OpenRouter or Vercel."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float = 120.0,
        *,
        allow_insecure_loopback: bool = False,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        if type(allow_insecure_loopback) is not bool:
            raise ValueError("allow_insecure_loopback must be a boolean")
        _validate_base_url(
            base_url,
            allow_insecure_loopback=allow_insecure_loopback,
        )
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
