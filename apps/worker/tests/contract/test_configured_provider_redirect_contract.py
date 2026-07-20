from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from app.services.document_parser.formats.pptx import parser as pptx_parser
from app.services.document_parser.providers.mineru import client as mineru_client


def _requests_calls(source_path: Path) -> list[ast.Call]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id == "requests" and node.func.attr in {"get", "post"}:
            calls.append(node)
    return calls


def _keyword_value(call: ast.Call, name: str) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def test_mineru_session_fails_closed_on_redirects() -> None:
    session = mineru_client.build_mineru_session()

    assert session.max_redirects == 0


def test_iloveapi_requests_have_explicit_timeout_and_no_redirects() -> None:
    calls = _requests_calls(Path(pptx_parser.__file__))

    assert calls, "the iLoveAPI parser must keep its outbound request inventory visible"
    assert all(_keyword_value(call, "timeout") is not None for call in calls)
    assert all(
        isinstance(_keyword_value(call, "allow_redirects"), ast.Constant)
        and _keyword_value(call, "allow_redirects").value is False
        for call in calls
    )


def test_iloveapi_server_url_is_limited_to_approved_host_family() -> None:
    assert pptx_parser._build_iloveapi_server_url("api.ilovepdf.com") == (
        "https://api.ilovepdf.com/v1"
    )

    with pytest.raises(ValueError, match="approved iLoveAPI host"):
        pptx_parser._build_iloveapi_server_url("attacker.example")

    with pytest.raises(ValueError, match="approved iLoveAPI host"):
        pptx_parser._build_iloveapi_server_url("api.ilovepdf.com.evil.example")


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_redirect_statuses_are_not_treated_as_success(status: int) -> None:
    assert status not in range(200, 300)
