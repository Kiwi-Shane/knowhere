"""Typed records used by the page-memory assist implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.services.page_memory.contracts import (
    PAGE_MEMORY_CONTRACT_VERSION,
    PAGE_RETRIEVAL_CONTRACT_VERSION,
    PageMemoryContractError,
    is_valid_case_namespace,
    required_text,
)


@dataclass(frozen=True)
class PageMemoryPage:
    page_id: str
    source_id: str
    source_version_id: str
    page_number: int
    page_manifest_sha256: str
    render_sha256: str
    native_text_sha256: str | None
    image_relative_path: str
    native_text_relative_path: str | None
    native_text: str
    lexical_index_status: str
    visual_index_status: str
    visual_embedding_backend_id: str | None
    visual_embedding_artifact_sha256: str | None
    visual_embedding: tuple[float, ...] | None
    adjacent_page_ids: tuple[str, ...]
    coarse_section_hints: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": PAGE_MEMORY_CONTRACT_VERSION,
            "page_id": self.page_id,
            "source_id": self.source_id,
            "source_version_id": self.source_version_id,
            "page_number": self.page_number,
            "page_manifest_sha256": self.page_manifest_sha256,
            "render_sha256": self.render_sha256,
            "native_text_sha256": self.native_text_sha256,
            "lexical_index_status": self.lexical_index_status,
            "visual_index_status": self.visual_index_status,
            "visual_embedding_backend_id": self.visual_embedding_backend_id,
            "visual_embedding_artifact_sha256": self.visual_embedding_artifact_sha256,
            "adjacent_page_ids": list(self.adjacent_page_ids),
            "coarse_section_hints": list(self.coarse_section_hints),
            "warnings": list(self.warnings),
            "verification_status": "exploratory_unverified",
        }


@dataclass(frozen=True)
class PageMemorySnapshot:
    contract_version: str
    memory_snapshot_id: str
    case_namespace: str
    source_id: str
    source_version_id: str
    native_sha256: str
    page_manifest_sha256: str
    lexical_index_status: str
    visual_index_status: str
    visual_embedding_backend_id: str | None
    visual_embedding_artifact_sha256: str | None
    pages: tuple[PageMemoryPage, ...]
    ranking_weights: dict[str, float]
    warnings: tuple[str, ...]
    verification_status: str = "exploratory_unverified"
    external_model_calls: bool = False
    network_calls: bool = False
    invalidated: bool = False

    def __post_init__(self) -> None:
        if self.contract_version != PAGE_MEMORY_CONTRACT_VERSION:
            raise PageMemoryContractError("unsupported page-memory contract version")
        if not is_valid_case_namespace(self.case_namespace):
            raise PageMemoryContractError("case_namespace is invalid")
        required_text(self.memory_snapshot_id, "memory_snapshot_id")
        if self.verification_status != "exploratory_unverified":
            raise PageMemoryContractError(
                "page memory snapshots must remain exploratory_unverified"
            )
        if self.external_model_calls or self.network_calls:
            raise PageMemoryContractError(
                "page memory assist must not make external model or network calls"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "memory_snapshot_id": self.memory_snapshot_id,
            "case_namespace": self.case_namespace,
            "source_id": self.source_id,
            "source_version_id": self.source_version_id,
            "native_sha256": self.native_sha256,
            "page_manifest_sha256": self.page_manifest_sha256,
            "lexical_index_status": self.lexical_index_status,
            "visual_index_status": self.visual_index_status,
            "visual_embedding_backend_id": self.visual_embedding_backend_id,
            "visual_embedding_artifact_sha256": self.visual_embedding_artifact_sha256,
            "pages": [page.to_dict() for page in self.pages],
            "adjacent_page_expansion": True,
            "ranking_weights": dict(self.ranking_weights),
            "warnings": list(self.warnings),
            "verification_status": self.verification_status,
            "external_model_calls": self.external_model_calls,
            "network_calls": self.network_calls,
        }


@dataclass(frozen=True)
class PageRetrievalRequest:
    request_id: str
    case_namespace: str
    allowed_source_ids: tuple[str, ...]
    source_id: str
    source_version_id: str
    native_sha256: str
    query: str = ""
    top_k: int = 5
    visual_query: tuple[float, ...] | None = None
    visual_backend_id: str | None = None
    expand_adjacent: bool = False
    adjacent_radius: int = 0

    def __post_init__(self) -> None:
        required_text(self.request_id, "request_id")
        if not is_valid_case_namespace(self.case_namespace):
            raise PageMemoryContractError("case_namespace is invalid")
        if isinstance(self.allowed_source_ids, (str, bytes)):
            raise PageMemoryContractError("allowed_source_ids must be a sequence")
        if any(not isinstance(value, str) or not value.strip() for value in self.allowed_source_ids):
            raise PageMemoryContractError("allowed_source_ids must contain text")
        required_text(self.source_id, "source_id")
        required_text(self.source_version_id, "source_version_id")
        required_text(self.native_sha256, "native_sha256")
        if not isinstance(self.query, str):
            raise PageMemoryContractError("query must be text")
        if isinstance(self.top_k, bool) or not isinstance(self.top_k, int) or not 1 <= self.top_k <= 100:
            raise PageMemoryContractError("top_k must be between 1 and 100")
        if isinstance(self.adjacent_radius, bool) or not isinstance(self.adjacent_radius, int):
            raise PageMemoryContractError("adjacent_radius must be an integer")
        if self.adjacent_radius < 0 or self.adjacent_radius > 1:
            raise PageMemoryContractError("adjacent_radius is bounded to zero or one")
        if self.visual_query is None and self.visual_backend_id is not None:
            raise PageMemoryContractError(
                "visual_backend_id requires a visual_query"
            )
        if self.visual_query is not None and not self.visual_backend_id:
            raise PageMemoryContractError(
                "visual_query requires an explicit visual_backend_id"
            )


@dataclass(frozen=True)
class PageRetrievalResult:
    contract_version: str
    request_id: str
    result_id: str
    memory_snapshot_id: str
    source_id: str
    source_version_id: str
    page_id: str
    page_number: int
    native_page_locator: str
    match_modes: tuple[str, ...]
    score_components: dict[str, float]
    rank: int
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    verification_status: str = "unverified"
    evidence_status: str = "evidence_lead_only"
    not_verified_absence: bool = True

    def __post_init__(self) -> None:
        if self.contract_version != PAGE_RETRIEVAL_CONTRACT_VERSION:
            raise PageMemoryContractError("unsupported page-retrieval contract version")
        if self.verification_status != "unverified":
            raise PageMemoryContractError("retrieval results must remain unverified")
        if self.evidence_status != "evidence_lead_only":
            raise PageMemoryContractError(
                "retrieval results must remain evidence_lead_only"
            )
        if self.not_verified_absence is not True:
            raise PageMemoryContractError(
                "retrieval results must not assert verified absence"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "request_id": self.request_id,
            "result_id": self.result_id,
            "memory_snapshot_id": self.memory_snapshot_id,
            "source_id": self.source_id,
            "source_version_id": self.source_version_id,
            "page_id": self.page_id,
            "page_number": self.page_number,
            "native_page_locator": self.native_page_locator,
            "match_modes": list(self.match_modes),
            "score_components": dict(self.score_components),
            "rank": self.rank,
            "reason_codes": list(self.reason_codes),
            "warnings": list(self.warnings),
            "verification_status": self.verification_status,
            "evidence_status": self.evidence_status,
            "not_verified_absence": self.not_verified_absence,
        }


__all__ = [
    "PageMemoryPage",
    "PageMemorySnapshot",
    "PageRetrievalRequest",
    "PageRetrievalResult",
]
