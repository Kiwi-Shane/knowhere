from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validate

from shared.services.page_memory.models import PageRetrievalRequest
from shared.services.page_memory.query import retrieve_pages

from .test_page_memory_contract import _snapshot


def _schema(repo_root: Path, filename: str) -> dict[str, Any]:
    return json.loads((repo_root / "schemas" / filename).read_text(encoding="utf-8"))


def test_page_memory_records_validate_against_the_published_schema(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[5]
    snapshot, _root, _manifest, _page_ids = _snapshot(tmp_path)
    schema = _schema(repo_root, "page-memory-record-v1.schema.json")

    for page in snapshot.to_dict()["pages"]:
        validate(page, schema)


def test_page_retrieval_results_validate_against_the_published_schema(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[5]
    snapshot, _root, _manifest, _page_ids = _snapshot(tmp_path)
    schema = _schema(repo_root, "page-retrieval-result-v1.schema.json")
    request = PageRetrievalRequest(
        request_id="REQ-001",
        case_namespace="case-alpha",
        allowed_source_ids=("SRC-A",),
        source_id="SRC-A",
        source_version_id="SRC-A-V1",
        native_sha256="a" * 64,
        query="methods",
        top_k=1,
    )

    results = retrieve_pages(request=request, snapshot=snapshot)

    for result in results:
        validate(result.to_dict(), schema)
