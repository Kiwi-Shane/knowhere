from __future__ import annotations

import ast
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from app.services.document_parser.formats.pptx import parser as pptx_parser
from shared.core.exceptions.domain_exceptions import PermissionDeniedException


def _approved_metadata() -> dict[str, object]:
    return {
        "external_call_authorizations": {
            "iloveapi": {
                "approved": True,
                "provider": "iloveapi",
                "data_classification": "synthetic",
                "source_scope": "local synthetic PPTX fixture",
                "authorization_id": "ECA-ILOVEAPI-SYNTHETIC-20260721",
                "approved_by": "contract-test",
            }
        }
    }


def test_direct_iloveapi_conversion_requires_job_authorization_before_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pptx_parser.settings,
        "ILOVEAPI_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )

    class UnexpectedQuotaManager:
        def acquire_inflight(self) -> bool:
            pytest.fail("missing job authorization must fail before quota setup")

    monkeypatch.setattr(
        "shared.services.ai.iloveapi_quota_manager.get_iloveapi_quota_manager",
        lambda: UnexpectedQuotaManager(),
    )

    with pytest.raises(PermissionDeniedException):
        pptx_parser._pptx_bytes_to_pdf_bytes(
            b"synthetic-pptx",
            "synthetic.pptx",
            job_metadata={},
        )


def test_approved_iloveapi_conversion_reaches_only_fake_http_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pptx_parser.settings,
        "ILOVEAPI_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )

    calls: list[tuple[str, str, dict[str, object]]] = []

    class FakeResponse:
        status_code = 200
        headers: dict[str, str] = {}
        text = ""
        url = "https://api.ilovepdf.com/v1"

        def __init__(self, payload: dict[str, str] | None = None) -> None:
            self._payload = payload or {}
            self.content = b"%PDF-synthetic"

        def json(self) -> dict[str, str]:
            return self._payload

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        calls.append(("GET", url, kwargs))
        if url.endswith("/start/officepdf"):
            return FakeResponse({"server": "api.ilovepdf.com", "task": "task-1"})
        return FakeResponse()

    def fake_post(url: str, **kwargs: object) -> FakeResponse:
        calls.append(("POST", url, kwargs))
        if url.endswith("/upload"):
            return FakeResponse({"server_filename": "server-file-1"})
        return FakeResponse()

    class FakeQuotaManager:
        max_concurrent = 1

        def acquire_inflight(self) -> bool:
            return True

        def release_inflight(self) -> None:
            return None

        def get_inflight_count(self) -> int:
            return 1

        def mark_rate_limited(self, _token_id: str, _retry_after: int) -> None:
            return None

    monkeypatch.setattr(pptx_parser.requests, "get", fake_get)
    monkeypatch.setattr(pptx_parser.requests, "post", fake_post)
    monkeypatch.setattr(
        pptx_parser,
        "_get_iloveapi_token_lease",
        lambda: ("synthetic-token", SimpleNamespace(token_id="synthetic-token")),
    )
    monkeypatch.setattr(
        "shared.services.ai.iloveapi_quota_manager.get_iloveapi_quota_manager",
        lambda: FakeQuotaManager(),
    )

    result = pptx_parser._pptx_bytes_to_pdf_bytes(
        b"synthetic-pptx",
        "synthetic.pptx",
        job_metadata=_approved_metadata(),
    )

    assert result == b"%PDF-synthetic"
    assert [(method, url) for method, url, _ in calls] == [
        ("GET", "https://api.ilovepdf.com/v1/start/officepdf"),
        ("POST", "https://api.ilovepdf.com/v1/upload"),
        ("POST", "https://api.ilovepdf.com/v1/process"),
        ("GET", "https://api.ilovepdf.com/v1/download/task-1"),
    ]
    assert all(kwargs["allow_redirects"] is False for _, _, kwargs in calls)


def test_pptx_api_path_forwards_job_metadata_into_conversion() -> None:
    parser_tree = ast.parse(Path(pptx_parser.__file__).read_text(encoding="utf-8"))
    function_node = next(
        node
        for node in ast.walk(parser_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_parse_pptx_via_api"
    )
    conversion_call = next(
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_pptx_bytes_to_pdf_bytes"
    )

    assert any(
        keyword.arg == "job_metadata"
        and isinstance(keyword.value, ast.Name)
        and keyword.value.id == "job_metadata"
        for keyword in conversion_call.keywords
    )


def test_page_memory_path_forwards_job_metadata_into_conversion() -> None:
    normalizer_path = Path("apps/worker/app/services/page_memory/normalizer.py")
    tree = ast.parse(normalizer_path.read_text(encoding="utf-8"))
    function_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_normalize_pptx_to_pdf"
    )
    conversion_call = next(
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_pptx_bytes_to_pdf_bytes"
    )

    assert any(
        keyword.arg == "job_metadata"
        and isinstance(keyword.value, ast.Name)
        and keyword.value.id == "job_metadata"
        for keyword in conversion_call.keywords
    )
