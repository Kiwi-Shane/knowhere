from __future__ import annotations

import pytest

from shared.services.retrieval.knowledge_retrieval_result import (
    KnowledgeRetrievalResultContext,
    KnowledgeRetrievalResultLocator,
    KnowledgeRetrievalResultSerializationError,
    serialize_knowledge_retrieval_result,
)


def _context() -> KnowledgeRetrievalResultContext:
    return KnowledgeRetrievalResultContext(
        result_id="RET-001",
        request_id="REQ-001",
        memory_snapshot_id="MEM-001",
        memory_snapshot_sha256="a" * 64,
        knowhere_repository_sha="b" * 40,
        retrieval_configuration_sha256="c" * 64,
        source_id="SRC-001",
        source_version_id="SRC-001-V001",
        retrieval_reason="classic_top_k_match",
        warnings=("native_source_verification_required",),
    )


def _locator() -> KnowledgeRetrievalResultLocator:
    return KnowledgeRetrievalResultLocator(
        section_path=("test.pdf", "1. Scope"),
        native_page_start=2,
        native_page_end=3,
        extraction_block_ids=("blk-001", "blk-002"),
        linked_table_ids=("tbl-001",),
        linked_image_ids=("img-001",),
        native_reference="SRC-001-V001:p2-p3#blk-001,blk-002",
    )


def test_serializer_emits_only_the_source_owned_contract_fields() -> None:
    row = {
        "chunk_id": "chunk-001",
        "score": 0.92,
        "evidence_score": 0.92,
        "agent_score": 0.7,
        "discovery_score": 0.8,
        "content_source": "summary",
        "readiness_status": "ready",
    }

    result = serialize_knowledge_retrieval_result(
        row,
        context=_context(),
        locator=_locator(),
    )

    assert result == {
        "contract_version": "knowledge-retrieval-result-v1",
        "result_id": "RET-001",
        "request_id": "REQ-001",
        "memory_snapshot_id": "MEM-001",
        "memory_snapshot_sha256": "a" * 64,
        "knowhere_repository_sha": "b" * 40,
        "retrieval_configuration_sha256": "c" * 64,
        "source_id": "SRC-001",
        "source_version_id": "SRC-001-V001",
        "section_path": ["test.pdf", "1. Scope"],
        "native_page_start": 2,
        "native_page_end": 3,
        "extraction_block_ids": ["blk-001", "blk-002"],
        "linked_table_ids": ["tbl-001"],
        "linked_image_ids": ["img-001"],
        "retrieval_reason": "classic_top_k_match",
        "score_components": {
            "score": 0.92,
            "evidence_score": 0.92,
            "agent_score": 0.7,
            "discovery_score": 0.8,
        },
        "citation": {
            "native_reference": "SRC-001-V001:p2-p3#blk-001,blk-002",
        },
        "warnings": [
            "native_source_verification_required",
            "retrieval_content_is_derivative",
        ],
        "native_source_verification_status": "unverified",
        "not_source_sufficiency_decision": True,
    }
    assert "readiness_status" not in result
    assert "chunk_id" not in result


def test_serializer_rejects_missing_explicit_native_locator() -> None:
    locator = KnowledgeRetrievalResultLocator(
        section_path=("test.pdf",),
        native_page_start=1,
        native_page_end=1,
        extraction_block_ids=(),
        native_reference="SRC-001-V001:p1",
    )

    with pytest.raises(
        KnowledgeRetrievalResultSerializationError,
        match="extraction_block_ids",
    ):
        serialize_knowledge_retrieval_result(
            {"score": 0.5, "chunk_id": "must-not-be-used"},
            context=_context(),
            locator=locator,
        )


def test_serializer_never_uses_chunk_id_as_an_extraction_block_id() -> None:
    with pytest.raises(
        KnowledgeRetrievalResultSerializationError,
        match="extraction_block_ids",
    ):
        serialize_knowledge_retrieval_result(
            {"score": 0.5, "chunk_id": "chunk-001"},
            context=_context(),
            locator=KnowledgeRetrievalResultLocator(
                section_path=("test.pdf",),
                native_page_start=1,
                native_page_end=1,
                extraction_block_ids=(),
                native_reference="SRC-001-V001:p1",
            ),
        )


def test_serializer_rejects_invalid_snapshot_hash() -> None:
    invalid_context = KnowledgeRetrievalResultContext(
        result_id="RET-001",
        request_id="REQ-001",
        memory_snapshot_id="MEM-001",
        memory_snapshot_sha256="not-a-sha",
        knowhere_repository_sha="b" * 40,
        retrieval_configuration_sha256="c" * 64,
        source_id="SRC-001",
        source_version_id="SRC-001-V001",
        retrieval_reason="classic_top_k_match",
    )
    invalid_locator = KnowledgeRetrievalResultLocator(
        section_path=("test.pdf",),
        native_page_start=3,
        native_page_end=2,
        extraction_block_ids=("blk-001",),
        native_reference="SRC-001-V001:p3-p2",
    )

    with pytest.raises(
        KnowledgeRetrievalResultSerializationError,
        match="memory_snapshot_sha256",
    ):
        serialize_knowledge_retrieval_result(
            {"score": 0.5},
            context=invalid_context,
            locator=invalid_locator,
        )


def test_serializer_rejects_reversed_page_range_and_non_finite_score() -> None:
    invalid_locator = KnowledgeRetrievalResultLocator(
        section_path=("test.pdf",),
        native_page_start=3,
        native_page_end=2,
        extraction_block_ids=("blk-001",),
        native_reference="SRC-001-V001:p3-p2",
    )

    with pytest.raises(
        KnowledgeRetrievalResultSerializationError,
        match="native_page_end",
    ):
        serialize_knowledge_retrieval_result(
            {"score": 0.5},
            context=_context(),
            locator=invalid_locator,
        )

    with pytest.raises(
        KnowledgeRetrievalResultSerializationError,
        match="score component score must be finite",
    ):
        serialize_knowledge_retrieval_result(
            {"score": float("nan")},
            context=_context(),
            locator=_locator(),
        )
