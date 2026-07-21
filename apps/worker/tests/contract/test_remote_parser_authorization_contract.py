from __future__ import annotations

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


def _approved_source_url_metadata() -> dict[str, object]:
    return {
        "external_call_authorizations": {
            "source_url": {
                "approved": True,
                "provider": "source_url",
                "data_classification": "synthetic",
                "source_scope": "remote-parser-contract",
                "authorization_id": "auth-remote-parser-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def _parse_session(metadata: dict[str, object]) -> SimpleNamespace:
    return SimpleNamespace(
        base_url="https://example.test/source.docx",
        base_llm_paras={},
        file_full_path="https://example.test/source.docx",
        filename="source.docx",
        full_output_dir="/tmp/knowhere-output",
        fragment_content="",
        job_id="job-remote-parser",
        job_metadata=metadata,
        output_dir="/tmp/knowhere-output",
        profile=SimpleNamespace(),
        relative_root="source.docx",
        s3_key=None,
    )


def test_load_file_bytes_forwards_job_metadata_to_guarded_downloader(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.services.common import file_loading

    metadata = _approved_source_url_metadata()
    calls: list[dict[str, object]] = []

    class RecordingJobFileStorage:
        def download_file_from_url(
            self,
            file_url: str,
            *,
            temp_dir: str | None = None,
            timeout_seconds: float = 0,
            job_metadata: dict[str, object] | None = None,
        ) -> str:
            calls.append(
                {
                    "file_url": file_url,
                    "temp_dir": temp_dir,
                    "timeout_seconds": timeout_seconds,
                    "job_metadata": job_metadata,
                }
            )
            downloaded_path = tmp_path / "remote.bin"
            downloaded_path.write_bytes(b"authorized remote bytes")
            return str(downloaded_path)

    monkeypatch.setattr(file_loading, "JobFileStorage", RecordingJobFileStorage)

    assert (
        file_loading.load_file_bytes(
            "https://example.test/document.pdf",
            file_url="https://example.test/document.pdf",
            job_metadata=metadata,
        )
        == b"authorized remote bytes"
    )
    assert len(calls) == 1
    assert calls[0]["file_url"] == "https://example.test/document.pdf"
    assert calls[0]["temp_dir"] is not None
    assert calls[0]["timeout_seconds"] == 300.0
    assert calls[0]["job_metadata"] is metadata


def test_parser_adapters_forward_job_metadata_to_remote_input_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.document_parser.orchestration import format_adapters
    from app.services.document_parser.formats.html import document_parser as html_parser
    from app.services.document_parser.formats.image import parser as image_parser
    from app.services.document_parser.formats.markdown import parser as markdown_parser
    from app.services.document_parser.formats.pptx import parser as pptx_parser
    from app.services.document_parser.formats.text import parser as text_parser

    metadata = _approved_source_url_metadata()
    session = _parse_session(metadata)
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        text_parser,
        "parse_texts",
        lambda **kwargs: captured.update(text=kwargs) or [],
    )
    monkeypatch.setattr(
        markdown_parser,
        "parse_md",
        lambda *args, **kwargs: captured.update(markdown=kwargs) or "text-output",
    )
    format_adapters.TextParseAdapter("text").parse(session)
    assert captured["text"]["job_metadata"] is metadata
    assert captured["markdown"]["job_metadata"] is metadata

    format_adapters.MarkdownParseAdapter("markdown").parse(session)
    assert captured["markdown"]["job_metadata"] is metadata

    monkeypatch.setattr(
        image_parser,
        "parse_image",
        lambda *args, **kwargs: captured.update(image=kwargs) or "image-output",
    )
    format_adapters.ImageParseAdapter("image").parse(session)
    assert captured["image"]["job_metadata"] is metadata

    monkeypatch.setattr(
        pptx_parser,
        "parse_pptx",
        lambda *args, **kwargs: captured.update(pptx=kwargs) or "pptx-output",
    )
    format_adapters.PptxParseAdapter("pptx").parse(session)
    assert captured["pptx"]["job_metadata"] is metadata

    monkeypatch.setattr(
        html_parser,
        "parse_html",
        lambda *args, **kwargs: captured.update(html=kwargs) or "html-output",
    )
    format_adapters.HtmlParseAdapter("html").parse(session)
    assert captured["html"]["job_metadata"] is metadata

    monkeypatch.setattr(
        format_adapters,
        "_parse_docx_path",
        lambda _path, parse_session: (
            captured.update(docx=parse_session) or "docx-output"
        ),
    )
    format_adapters.DocxParseAdapter("docx").parse(session)
    assert captured["docx"].job_metadata is metadata

    monkeypatch.setattr(
        format_adapters,
        "_parse_xlsx_path",
        lambda _path, parse_session: (
            captured.update(xlsx=parse_session) or "xlsx-output"
        ),
    )
    format_adapters.XlsxParseAdapter("xlsx").parse(session)
    assert captured["xlsx"].job_metadata is metadata
