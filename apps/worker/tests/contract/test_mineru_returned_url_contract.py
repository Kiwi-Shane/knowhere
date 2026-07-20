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
from shared.core.exceptions.domain_exceptions import (
    MinerUServiceException,
    SystemSettingMissingException,
)


def test_returned_mineru_upload_url_requires_https_and_public_preflight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        pdf_service.settings,
        "MINERU_RETURNED_UPLOAD_ALLOWED_HOSTS",
        "objects.example",
        raising=False,
    )

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
    validated_url, validated_ip = pdf_service._validate_mineru_upload_url(upload_url)
    assert validated_url == upload_url
    assert validated_ip == "203.0.113.10"
    assert calls == [upload_url]


def test_returned_mineru_upload_url_fails_closed_on_private_or_unresolved_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pdf_service.settings,
        "MINERU_RETURNED_UPLOAD_ALLOWED_HOSTS",
        "objects.example",
        raising=False,
    )
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


def test_returned_mineru_upload_url_requires_destination_approval_before_dns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        pdf_service.settings,
        "MINERU_RETURNED_UPLOAD_ALLOWED_HOSTS",
        "",
        raising=False,
    )
    monkeypatch.setattr(
        pdf_service,
        "validate_http_url_and_resolve_ip",
        lambda url: calls.append(url),
        raising=False,
    )

    with pytest.raises(
        SystemSettingMissingException,
        match="MINERU_RETURNED_UPLOAD_ALLOWED_HOSTS",
    ):
        pdf_service._validate_mineru_upload_url(
            "https://objects.example/upload?signature=abc"
        )
    assert calls == []


def test_returned_mineru_upload_url_rejects_unapproved_destination_before_dns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        pdf_service.settings,
        "MINERU_RETURNED_UPLOAD_ALLOWED_HOSTS",
        "approved.example",
        raising=False,
    )
    monkeypatch.setattr(
        pdf_service,
        "validate_http_url_and_resolve_ip",
        lambda url: calls.append(url),
        raising=False,
    )

    with pytest.raises(MinerUServiceException, match="approved destination"):
        pdf_service._validate_mineru_upload_url(
            "https://objects.example/upload?signature=abc"
        )
    assert calls == []


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

    pinned_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "upload_pinned_outbound_file"
    ]
    assert pinned_calls
    assert all(
        {keyword.arg for keyword in call.keywords}
        >= {
            "url",
            "pinned_ip",
            "file_path",
            "connect_timeout_seconds",
            "read_timeout_seconds",
        }
        for call in pinned_calls
    )


def test_mineru_upload_call_uses_validated_ip_pinned_transfer() -> None:
    source_path = Path(pdf_service.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_upload_file_to_mineru"
    )

    pinned_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "upload_pinned_outbound_file"
    ]
    assert pinned_calls
    assert all(
        {keyword.arg for keyword in call.keywords}
        >= {
            "url",
            "pinned_ip",
            "file_path",
            "connect_timeout_seconds",
            "read_timeout_seconds",
        }
        for call in pinned_calls
    )
