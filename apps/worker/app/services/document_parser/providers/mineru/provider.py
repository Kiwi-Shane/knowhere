"""PDF MinerU provider dispatcher with cloud-preserving defaults."""

from __future__ import annotations

import time
from typing import Literal

from loguru import logger

from app.services.document_parser.providers.mineru.artifact_contract import (
    MinerUArtifactContractError,
)
from app.services.document_parser.providers.mineru.local_capacity import (
    LocalMinerUCapacityError,
)
from app.services.document_parser.providers.mineru.local_pdf_service import (
    parse_via_local,
)
from app.services.document_parser.providers.mineru.local_process import LocalMinerUError
from app.services.document_parser.providers.mineru.pdf_service import parse_via_full
from app.services.document_parser.providers.mineru.runtime_preflight import (
    LocalMinerURuntimeError,
)
from shared.core.config import settings
from shared.core.exceptions.domain_exceptions import MinerUServiceException


LocalErrorCategory = Literal[
    "capacity",
    "configuration",
    "process_timeout",
    "process_exit",
    "artifact_contract",
    "publication",
    "unknown",
]


class LocalMinerUServiceException(MinerUServiceException):
    """Safe local failure whose canonical log omits traceback diagnostics."""

    def logging(self, **extra_context: object) -> None:
        from shared.core.logging import LogEvent, get_log_context

        logger.bind(
            event=LogEvent.EXCEPTION_SYSTEM.value,
            **self.to_log(),
            **get_log_context(),
            **extra_context,
        ).error(self.internal_message)


def _local_error_category(error: Exception) -> LocalErrorCategory:
    if isinstance(error, LocalMinerUCapacityError):
        return "capacity"
    if isinstance(error, MinerUArtifactContractError):
        return "artifact_contract"
    if isinstance(error, LocalMinerUError):
        return "process_timeout" if error.timed_out else "process_exit"
    if isinstance(error, (ValueError, LocalMinerURuntimeError)):
        return "configuration"
    if isinstance(error, OSError):
        return "publication"
    return "unknown"


def _elapsed_milliseconds(started_at: float) -> int:
    return max(0, round((time.perf_counter() - started_at) * 1000))


def _observe_provider(
    *,
    provider_name: str,
    backend: str,
    status: Literal["ok", "error"],
    elapsed_ms: int,
    error_category: LocalErrorCategory | None = None,
) -> None:
    fields: dict[str, str | int] = {
        "event": "mineru.provider",
        "provider": provider_name,
        "backend": backend,
        "status": status,
        "elapsed_ms": elapsed_ms,
    }
    if error_category is not None:
        fields["error_category"] = error_category
    logger.bind(**fields).info("MinerU provider observation")


def parse_pdf(
    pdf_path: str,
    filename: str,
    output_dir: str,
    *,
    s3_key: str | None = None,
) -> None:
    """Parse a PDF through the configured provider without silent fallback."""

    provider_name = settings.MINERU_PROVIDER
    backend = settings.MINERU_LOCAL_BACKEND if provider_name == "local" else "cloud"
    started_at = time.perf_counter()
    try:
        if provider_name == "cloud":
            parse_via_full(pdf_path, filename, output_dir, s3_key=s3_key)
        elif provider_name == "local":
            parse_via_local(pdf_path, filename, output_dir, s3_key=s3_key)
        else:
            raise ValueError(f"Unsupported MinerU provider: {provider_name!r}")
    except Exception as error:
        category = (
            _local_error_category(error)
            if provider_name == "local"
            else "configuration"
            if provider_name not in {"cloud", "local"}
            else "unknown"
        )
        _observe_provider(
            provider_name=(
                provider_name if provider_name in {"cloud", "local"} else "unknown"
            ),
            backend=backend if provider_name in {"cloud", "local"} else "unknown",
            status="error",
            elapsed_ms=_elapsed_milliseconds(started_at),
            error_category=category,
        )
        if provider_name == "local":
            raise LocalMinerUServiceException(
                internal_message=f"Local MinerU provider failed: {category}",
            ) from None
        raise

    _observe_provider(
        provider_name=provider_name,
        backend=backend,
        status="ok",
        elapsed_ms=_elapsed_milliseconds(started_at),
    )
