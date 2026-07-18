"""Build the opt-in Knowhere knowledge retrieval result contract.

This module is deliberately a pure boundary adapter.  It serializes one
already-ranked retrieval row only when the caller supplies the source-owned
memory, source-version, and native-locator context.  The normal retrieval
routes do not call it yet; inferring native extraction blocks from a database
chunk id would weaken the provenance contract.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


CONTRACT_VERSION = "knowledge-retrieval-result-v1"
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REPOSITORY_SHA_PATTERN = re.compile(r"^[0-9a-f]{7,64}$")
_SCORE_FIELDS = (
    "score",
    "evidence_score",
    "agent_score",
    "discovery_score",
    "importance_raw_score",
    "importance_multiplier",
)


class KnowledgeRetrievalResultSerializationError(ValueError):
    """Raised when a result cannot be serialized without inventing provenance."""


@dataclass(frozen=True)
class KnowledgeRetrievalResultContext:
    """Explicit request, memory, source, and retrieval context for one result."""

    result_id: str
    request_id: str
    memory_snapshot_id: str
    memory_snapshot_sha256: str
    knowhere_repository_sha: str
    retrieval_configuration_sha256: str
    source_id: str
    source_version_id: str
    retrieval_reason: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeRetrievalResultLocator:
    """Native source locator explicitly mapped from a producer-owned artifact."""

    section_path: tuple[str, ...]
    native_page_start: int
    native_page_end: int
    extraction_block_ids: tuple[str, ...]
    native_reference: str
    linked_table_ids: tuple[str, ...] = ()
    linked_image_ids: tuple[str, ...] = ()


def serialize_knowledge_retrieval_result(
    row: Mapping[str, Any],
    *,
    context: KnowledgeRetrievalResultContext,
    locator: KnowledgeRetrievalResultLocator,
) -> dict[str, Any]:
    """Serialize one ranked row into ``knowledge-retrieval-result-v1``.

    ``locator`` is required instead of being inferred from ``chunk_id`` or a
    section string.  This keeps database retrieval identifiers separate from
    the native extraction identifiers that a reviewer would need to verify.
    """

    if not isinstance(row, Mapping):
        raise KnowledgeRetrievalResultSerializationError("row must be a mapping")

    normalized_context = _validate_context(context)
    normalized_locator = _validate_locator(locator)
    score_components = _score_components(row)
    warnings = _warnings(context.warnings, row)
    native_reference = normalized_locator.pop("native_reference")

    return {
        "contract_version": CONTRACT_VERSION,
        **normalized_context,
        **normalized_locator,
        "retrieval_reason": _required_text(
            context.retrieval_reason, "retrieval_reason"
        ),
        "score_components": score_components,
        "citation": {"native_reference": native_reference},
        "warnings": warnings,
        "native_source_verification_status": "unverified",
        "not_source_sufficiency_decision": True,
    }


def _validate_context(context: KnowledgeRetrievalResultContext) -> dict[str, str]:
    if not isinstance(context, KnowledgeRetrievalResultContext):
        raise KnowledgeRetrievalResultSerializationError(
            "context must be KnowledgeRetrievalResultContext"
        )

    return {
        "result_id": _required_text(context.result_id, "result_id"),
        "request_id": _required_text(context.request_id, "request_id"),
        "memory_snapshot_id": _required_text(
            context.memory_snapshot_id, "memory_snapshot_id"
        ),
        "memory_snapshot_sha256": _validated_hash(
            context.memory_snapshot_sha256,
            "memory_snapshot_sha256",
            _SHA256_PATTERN,
        ),
        "knowhere_repository_sha": _validated_hash(
            context.knowhere_repository_sha,
            "knowhere_repository_sha",
            _REPOSITORY_SHA_PATTERN,
        ),
        "retrieval_configuration_sha256": _validated_hash(
            context.retrieval_configuration_sha256,
            "retrieval_configuration_sha256",
            _SHA256_PATTERN,
        ),
        "source_id": _required_text(context.source_id, "source_id"),
        "source_version_id": _required_text(
            context.source_version_id, "source_version_id"
        ),
    }


def _validate_locator(
    locator: KnowledgeRetrievalResultLocator,
) -> dict[str, Any]:
    if not isinstance(locator, KnowledgeRetrievalResultLocator):
        raise KnowledgeRetrievalResultSerializationError(
            "locator must be KnowledgeRetrievalResultLocator"
        )

    section_path = _string_sequence(locator.section_path, "section_path", minimum=1)
    extraction_block_ids = _string_sequence(
        locator.extraction_block_ids,
        "extraction_block_ids",
        minimum=1,
    )
    linked_table_ids = _string_sequence(
        locator.linked_table_ids,
        "linked_table_ids",
        minimum=0,
    )
    linked_image_ids = _string_sequence(
        locator.linked_image_ids,
        "linked_image_ids",
        minimum=0,
    )
    page_start = _positive_page(locator.native_page_start, "native_page_start")
    page_end = _positive_page(locator.native_page_end, "native_page_end")
    if page_end < page_start:
        raise KnowledgeRetrievalResultSerializationError(
            "native_page_end must be greater than or equal to native_page_start"
        )

    return {
        "section_path": section_path,
        "native_page_start": page_start,
        "native_page_end": page_end,
        "extraction_block_ids": extraction_block_ids,
        "linked_table_ids": linked_table_ids,
        "linked_image_ids": linked_image_ids,
        "native_reference": _required_text(
            locator.native_reference, "native_reference"
        ),
    }


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeRetrievalResultSerializationError(
            f"{field_name} must be a non-empty string"
        )
    return value.strip()


def _validated_hash(value: object, field_name: str, pattern: re.Pattern[str]) -> str:
    normalized = _required_text(value, field_name)
    if pattern.fullmatch(normalized) is None:
        raise KnowledgeRetrievalResultSerializationError(
            f"{field_name} must be lowercase hexadecimal"
        )
    return normalized


def _string_sequence(
    values: object,
    field_name: str,
    *,
    minimum: int,
) -> list[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise KnowledgeRetrievalResultSerializationError(
            f"{field_name} must be a sequence of strings"
        )

    normalized: list[str] = []
    for value in values:
        normalized.append(_required_text(value, field_name))
    if len(normalized) < minimum:
        raise KnowledgeRetrievalResultSerializationError(
            f"{field_name} must contain at least {minimum} item(s)"
        )
    return normalized


def _positive_page(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise KnowledgeRetrievalResultSerializationError(
            f"{field_name} must be a positive integer"
        )
    return value


def _score_components(row: Mapping[str, Any]) -> dict[str, Any]:
    explicit = row.get("score_components")
    if isinstance(explicit, Mapping) and explicit:
        components = dict(explicit)
        try:
            json.dumps(components, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise KnowledgeRetrievalResultSerializationError(
                "score_components must be JSON serializable"
            ) from error
        return components

    components: dict[str, float | int] = {}
    for field_name in _SCORE_FIELDS:
        if field_name not in row or row[field_name] is None:
            continue
        value = row[field_name]
        if isinstance(value, bool):
            raise KnowledgeRetrievalResultSerializationError(
                f"score component {field_name} must be numeric"
            )
        try:
            numeric = float(value)
        except (TypeError, ValueError) as error:
            raise KnowledgeRetrievalResultSerializationError(
                f"score component {field_name} must be numeric"
            ) from error
        if not math.isfinite(numeric):
            raise KnowledgeRetrievalResultSerializationError(
                f"score component {field_name} must be finite"
            )
        components[field_name] = value if isinstance(value, (int, float)) else numeric

    if not components:
        raise KnowledgeRetrievalResultSerializationError(
            "row must contain at least one score component"
        )
    return components


def _warnings(context_warnings: object, row: Mapping[str, Any]) -> list[str]:
    warnings = _string_sequence(context_warnings, "warnings", minimum=0)
    content_source = str(row.get("content_source") or "").strip().lower()
    if content_source and content_source != "content":
        warnings.append("retrieval_content_is_derivative")

    return list(dict.fromkeys(warnings))
