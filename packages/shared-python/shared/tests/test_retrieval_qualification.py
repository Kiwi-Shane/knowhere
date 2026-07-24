from __future__ import annotations

from shared.services.retrieval.knowledge_retrieval_result import (
    KnowledgeRetrievalResultContext,
    KnowledgeRetrievalResultLocator,
    serialize_knowledge_retrieval_result,
)
from shared.services.retrieval.qualification import (
    validate_knowledge_retrieval_result,
)


def _result() -> dict[str, object]:
    return serialize_knowledge_retrieval_result(
        {"score": 1.0},
        context=KnowledgeRetrievalResultContext(
            result_id="RET-001",
            request_id="REQ-001",
            memory_snapshot_id="MEM-001",
            memory_snapshot_sha256="a" * 64,
            knowhere_repository_sha="b" * 40,
            retrieval_configuration_sha256="c" * 64,
            source_id="SRC-001",
            source_version_id="SRC-001-V001",
            retrieval_reason="synthetic_match",
        ),
        locator=KnowledgeRetrievalResultLocator(
            section_path=("1. Scope",),
            native_page_start=1,
            native_page_end=1,
            extraction_block_ids=("BLK-001",),
            native_reference="SRC-001-V001:p1#BLK-001",
        ),
    )


def test_result_qualification_accepts_explicit_traceability_and_citation() -> None:
    issues = validate_knowledge_retrieval_result(
        _result(),
        allowed_source_ids={"SRC-001"},
        expected_request_id="REQ-001",
        expected_source_version_id="SRC-001-V001",
        expected_extraction_block_ids={"BLK-001"},
        current_memory_snapshot_id="MEM-001",
        current_memory_snapshot_sha256="a" * 64,
    )

    assert issues == ()


def test_result_qualification_rejects_unallowlisted_or_unlinked_results() -> None:
    result = _result()
    result["source_id"] = "SRC-OTHER"
    result["source_version_id"] = "SRC-OTHER-V001"
    result["extraction_block_ids"] = ["BLK-OTHER"]
    result["citation"] = {"native_reference": "SRC-OTHER-V001:p1"}
    result["readiness_status"] = "ready"

    issues = validate_knowledge_retrieval_result(
        result,
        allowed_source_ids={"SRC-001"},
        expected_request_id="REQ-001",
        expected_source_version_id="SRC-001-V001",
        expected_extraction_block_ids={"BLK-001"},
    )
    codes = {issue.code for issue in issues}

    assert {
        "source_not_allowlisted",
        "source_version_mismatch",
        "extraction_block_unlinked",
        "citation_mismatch",
        "forbidden_authority_field",
    } <= codes


def test_result_qualification_rejects_stale_and_invalidated_snapshots() -> None:
    issues = validate_knowledge_retrieval_result(
        _result(),
        allowed_source_ids={"SRC-001"},
        expected_request_id="REQ-001",
        expected_source_version_id="SRC-001-V001",
        expected_extraction_block_ids={"BLK-001"},
        current_memory_snapshot_id="MEM-002",
        current_memory_snapshot_sha256="d" * 64,
        invalidated=True,
    )
    codes = {issue.code for issue in issues}

    assert {"stale_result", "invalidated_result"} <= codes
