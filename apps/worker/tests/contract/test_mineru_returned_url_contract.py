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

from app.services.document_parser.providers.mineru import pdf_service
from shared.core.exceptions.domain_exceptions import MinerUServiceException


def test_returned_mineru_upload_url_requires_https_and_public_preflight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def valid_public_url(url: str) -> SimpleNamespace:
        calls.append(url)
        return SimpleNamespace(
            is_valid=True,
            validated_ip="203.0.113.10",
            error_message=None,
        )

    monkeypatch.setattr(
        pdf_service,
        "validate_http_url_and_resolve_ip",
        valid_public_url,
        raising=False,
    )

    with pytest.raises(MinerUServiceException, match="https"):
        pdf_service._validate_mineru_upload_url(
            "http://objects.example/upload?signature=abc"
        )
    assert calls == []

    upload_url = "https://objects.example/upload?signature=abc"
    assert pdf_service._validate_mineru_upload_url(upload_url) == upload_url
    assert calls == [upload_url]


def test_returned_mineru_upload_url_fails_closed_on_private_or_unresolved_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pdf_service,
        "validate_http_url_and_resolve_ip",
        lambda _url: SimpleNamespace(
            is_valid=False,
            validated_ip=None,
            error_message="hostname resolved to a private address",
        ),
        raising=False,
    )

    with pytest.raises(MinerUServiceException, match="returned upload URL"):
        pdf_service._validate_mineru_upload_url(
            "https://objects.example/upload?signature=abc"
        )


def test_mineru_upload_call_keeps_returned_url_validation_and_redirect_block_visible() -> None:
    source_path = Path(pdf_service.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_upload_file_to_mineru"
    )

    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_validate_mineru_upload_url"
        for node in ast.walk(function_node)
    )

    put_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "put"
    ]
    assert put_calls
    assert all(
        any(
            keyword.arg == "allow_redirects"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is False
            for keyword in call.keywords
        )
        for call in put_calls
    )
