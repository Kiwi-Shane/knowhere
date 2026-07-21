"""Deterministic admission policy for request-scoped LLM endpoints."""

from __future__ import annotations

from collections.abc import Iterable
from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit

from shared.models.schemas.llm_config import LLMConfig, LLMProviderConfig


class LLMEndpointPolicyError(ValueError):
    """Raised when a BYOK endpoint is not explicitly safe and authorized."""


def normalize_provider_endpoint(value: str) -> str:
    """Return the canonical endpoint form used for exact allowlist matching.

    This function intentionally does not resolve DNS or contact the endpoint.
    Runtime egress controls are a separate boundary.
    """
    if not isinstance(value, str) or not value.strip():
        raise LLMEndpointPolicyError("provider endpoint must be a non-empty URL")

    raw = value.strip()
    if any(character.isspace() for character in raw):
        raise LLMEndpointPolicyError("provider endpoint must not contain whitespace")

    try:
        parsed = urlsplit(raw)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as exc:
        raise LLMEndpointPolicyError("provider endpoint is malformed") from exc

    if parsed.scheme.lower() != "https":
        raise LLMEndpointPolicyError("provider endpoint must use https")
    if not hostname:
        raise LLMEndpointPolicyError("provider endpoint must include a host")
    if parsed.username or parsed.password:
        raise LLMEndpointPolicyError(
            "provider endpoint must not contain embedded credentials"
        )
    if parsed.query or parsed.fragment:
        raise LLMEndpointPolicyError(
            "provider endpoint must not contain a query or fragment"
        )

    try:
        address = ip_address(hostname)
    except ValueError:
        address = None
    if hostname in {"localhost", "localhost.localdomain"} or (
        address is not None
        and (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_unspecified
            or address.is_multicast
        )
    ):
        raise LLMEndpointPolicyError(
            "provider endpoint must not target a local or private address"
        )

    display_host = f"[{hostname}]" if ":" in hostname else hostname
    display_port = f":{port}" if port is not None and port != 443 else ""
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", f"{display_host}{display_port}", path, "", ""))


def parse_allowed_provider_endpoints(
    value: str | Iterable[str] | None,
) -> frozenset[str]:
    """Normalize an operator-provided comma-separated endpoint allowlist."""
    if value is None:
        return frozenset()
    raw_values = value.split(",") if isinstance(value, str) else value
    normalized: set[str] = set()
    for item in raw_values:
        if isinstance(item, str) and item.strip():
            normalized.add(normalize_provider_endpoint(item))
    return frozenset(normalized)


def _effective_providers(config: LLMConfig) -> tuple[LLMProviderConfig, ...]:
    providers: list[LLMProviderConfig] = []
    for provider in (config.text_effective(), config.vision_effective()):
        if provider is not None and provider not in providers:
            providers.append(provider)
    return tuple(providers)


def validate_llm_config_endpoint_policy(
    config: LLMConfig | None,
    *,
    external_calls_enabled: bool,
    allowed_endpoints: str | Iterable[str] | None,
) -> tuple[str, ...]:
    """Validate every effective BYOK endpoint and return canonical endpoints."""
    if config is None:
        return ()
    if not external_calls_enabled:
        raise LLMEndpointPolicyError("LLM external calls are not explicitly enabled")

    allowlist = parse_allowed_provider_endpoints(allowed_endpoints)
    if not allowlist:
        raise LLMEndpointPolicyError("LLM provider endpoint allowlist is empty")

    endpoints: list[str] = []
    for provider in _effective_providers(config):
        endpoint = normalize_provider_endpoint(provider.base_url)
        if endpoint not in allowlist:
            raise LLMEndpointPolicyError(
                f"provider endpoint {endpoint!r} is not allowlisted"
            )
        endpoints.append(endpoint)
    return tuple(endpoints)
