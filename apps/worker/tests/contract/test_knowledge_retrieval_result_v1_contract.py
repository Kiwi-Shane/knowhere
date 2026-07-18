from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCHEMA = ROOT / "schemas" / "knowledge-retrieval-result-v1.schema.json"
FIXTURE = (
    ROOT
    / "examples"
    / "contracts"
    / "knowledge-retrieval-result-v1"
    / "example.json"
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_knowledge_retrieval_result_schema_and_fixture_are_source_owned() -> None:
    schema = _load(SCHEMA)
    fixture = _load(FIXTURE)

    assert schema["title"] == "Knowhere knowledge retrieval result v1"
    assert schema["properties"]["contract_version"]["const"] == (
        "knowledge-retrieval-result-v1"
    )
    assert fixture["contract_version"] == "knowledge-retrieval-result-v1"
    assert fixture["native_source_verification_status"] == "unverified"
    assert fixture["not_source_sufficiency_decision"] is True
    assert "evidence_status" not in fixture
    assert "readiness_status" not in fixture
    assert "regulatory_conclusion" not in fixture


def test_knowledge_retrieval_result_schema_requires_provenance_and_locator() -> None:
    schema = _load(SCHEMA)
    required = schema["required"]

    assert {
        "contract_version",
        "result_id",
        "memory_snapshot_id",
        "memory_snapshot_sha256",
        "source_id",
        "source_version_id",
        "native_page_start",
        "native_page_end",
        "extraction_block_ids",
        "citation",
    } <= set(required)
