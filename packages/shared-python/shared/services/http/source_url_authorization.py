"""Authorization gates for outbound source URL inspection and download."""

from __future__ import annotations

from typing import Any

from shared.core.exceptions.domain_exceptions import SystemSettingMissingException
from shared.models.schemas.job_metadata import JobMetadataHelper

_DEVELOPMENT_ENVIRONMENTS = frozenset({"dev", "development", "local"})


def _current_settings():
    """Resolve the current config instance after test/runtime module reloads."""
    from shared.core.config import settings

    return settings


def require_source_url_external_calls_enabled() -> None:
    """Require operator opt-in before source URL validation or inspection."""
    settings = _current_settings()
    if (
        settings.ENVIRONMENT.lower() in _DEVELOPMENT_ENVIRONMENTS
        and not settings.SOURCE_URL_EXTERNAL_CALLS_ENABLED
    ):
        return

    if settings.SOURCE_URL_EXTERNAL_CALLS_ENABLED:
        return

    raise SystemSettingMissingException(
        internal_message=(
            "Source URL downloads are not explicitly enabled; set "
            "SOURCE_URL_EXTERNAL_CALLS_ENABLED=true to authorize outbound "
            "source URL operations"
        )
    )


def require_source_url_job_authorization(
    job_metadata: dict[str, Any] | None,
) -> None:
    """Require operator opt-in and a traceable authorization for one job."""
    settings = _current_settings()
    if (
        settings.ENVIRONMENT.lower() in _DEVELOPMENT_ENVIRONMENTS
        and not settings.SOURCE_URL_EXTERNAL_CALLS_ENABLED
    ):
        return

    require_source_url_external_calls_enabled()
    JobMetadataHelper.require_external_call_authorization(
        job_metadata,
        provider="source_url",
    )


def require_source_url_resolution_authorization(
    job_metadata: dict[str, Any] | None,
) -> None:
    """Gate URL validation and optional HEAD inspection before they run."""
    if job_metadata is None:
        require_source_url_external_calls_enabled()
        return

    require_source_url_job_authorization(job_metadata)
