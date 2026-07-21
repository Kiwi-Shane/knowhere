from __future__ import annotations

import os
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

def _approved_object_storage_metadata() -> dict[str, object]:
    return {
        "external_call_authorizations": {
            "object_storage": {
                "approved": True,
                "provider": "object_storage",
                "data_classification": "synthetic",
                "source_scope": "mineru-url-storage-contract",
                "authorization_id": "auth-mineru-url-storage-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def _rejected_object_storage_metadata() -> dict[str, object]:
    metadata = _approved_object_storage_metadata()
    authorization = metadata["external_call_authorizations"]["object_storage"]
    assert isinstance(authorization, dict)
    authorization["approved"] = False
    return metadata


class _RecordingStorageAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def exists(self, storage_key: str, bucket: str | None = None) -> bool:
        self.calls.append(("exists", (storage_key, bucket)))
        raise AssertionError("storage adapter must not run before authorization")

    def get_object_size(self, storage_key: str, bucket: str | None = None) -> int:
        self.calls.append(("get_object_size", (storage_key, bucket)))
        raise AssertionError("storage adapter must not run before authorization")


def _enable_remote_storage_authorization(monkeypatch: pytest.MonkeyPatch):
    storage_module = importlib.import_module(
        "shared.services.storage.job_file_storage"
    )
    monkeypatch.setattr(
        storage_module.settings,
        "OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setenv("S3_TYPE", "s3")
    return storage_module


def test_mineru_storage_boundary_rejects_missing_authorization_before_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage_module = _enable_remote_storage_authorization(monkeypatch)
    exceptions_module = importlib.import_module(
        "shared.core.exceptions.domain_exceptions"
    )
    adapter = _RecordingStorageAdapter()
    storage = storage_module.JobFileStorage(
        storage_adapter=adapter,  # type: ignore[arg-type]
        uploads_bucket="test-uploads",
    )

    with pytest.raises(exceptions_module.PermissionDeniedException, match="object_storage"):
        storage.verify_upload_exists("uploads/job-1.pdf")

    assert adapter.calls == []


def test_mineru_storage_boundary_rejects_invalid_authorization_before_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage_module = _enable_remote_storage_authorization(monkeypatch)
    exceptions_module = importlib.import_module(
        "shared.core.exceptions.domain_exceptions"
    )
    adapter = _RecordingStorageAdapter()
    storage = storage_module.JobFileStorage(
        storage_adapter=adapter,  # type: ignore[arg-type]
        uploads_bucket="test-uploads",
    )

    with pytest.raises(exceptions_module.PermissionDeniedException, match="object_storage"):
        storage.verify_upload_exists(
            "uploads/job-1.pdf",
            job_metadata=_rejected_object_storage_metadata(),
        )

    assert adapter.calls == []


def test_mineru_url_source_helpers_forward_approved_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pdf_service = importlib.import_module(
        "app.services.document_parser.providers.mineru.pdf_service"
    )
    metadata = _approved_object_storage_metadata()
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"synthetic pdf")
    calls: list[dict[str, object]] = []

    class RecordingJobFileStorage:
        def verify_upload_exists(
            self,
            storage_key: str,
            *,
            job_metadata: dict[str, object] | None = None,
        ) -> dict[str, object]:
            calls.append(
                {
                    "operation": "verify",
                    "storage_key": storage_key,
                    "job_metadata": job_metadata,
                }
            )
            return {"exists": False}

        def upload_source_file(
            self,
            local_file_path: str,
            storage_key: str,
            *,
            job_metadata: dict[str, object] | None = None,
        ) -> dict[str, object]:
            calls.append(
                {
                    "operation": "upload",
                    "local_file_path": local_file_path,
                    "storage_key": storage_key,
                    "job_metadata": job_metadata,
                }
            )
            return {"key": storage_key}

        def generate_upload_download_url(
            self,
            storage_key: str,
            *,
            expires_in: int,
            job_metadata: dict[str, object] | None = None,
        ) -> dict[str, object]:
            calls.append(
                {
                    "operation": "presign",
                    "storage_key": storage_key,
                    "expires_in": expires_in,
                    "job_metadata": job_metadata,
                }
            )
            return {"download_url": "https://assets.example.test/source.pdf"}

    monkeypatch.setattr(pdf_service, "JobFileStorage", RecordingJobFileStorage)
    monkeypatch.setattr(pdf_service.settings, "MINERU_UPLOAD_MODE_ENABLED", False)
    settings_type = type(pdf_service.settings)
    monkeypatch.setattr(
        settings_type,
        "require_mineru_external_calls_enabled",
        lambda _settings: None,
    )
    monkeypatch.setattr(
        settings_type,
        "validate_mineru_endpoint",
        lambda _settings: "https://mineru.example.test",
    )
    monkeypatch.setattr(
        pdf_service,
        "_submit_url_task",
        lambda _presigned_url, _filename: ("batch-1", "token-1"),
    )
    monkeypatch.setattr(pdf_service, "poll_mineru_task", lambda **_kwargs: None)

    pdf_service.parse_via_full(
        str(source_path),
        source_path.name,
        str(tmp_path / "output"),
        s3_key="uploads/job-1.pdf",
        job_metadata=metadata,
    )

    assert [call["operation"] for call in calls] == [
        "verify",
        "upload",
        "presign",
    ]
    assert all(call["job_metadata"] is metadata for call in calls)


def test_mineru_provider_forwards_job_metadata_to_cloud(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = importlib.import_module(
        "app.services.document_parser.providers.mineru.provider"
    )
    metadata = _approved_object_storage_metadata()
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", "cloud")

    def fake_parse_via_full(
        pdf_path: str,
        filename: str,
        output_dir: str,
        *,
        s3_key: str | None = None,
        job_metadata: dict[str, object] | None = None,
    ) -> None:
        calls.append(
            {
                "pdf_path": pdf_path,
                "filename": filename,
                "output_dir": output_dir,
                "s3_key": s3_key,
                "job_metadata": job_metadata,
            }
        )

    monkeypatch.setattr(provider, "parse_via_full", fake_parse_via_full)
    monkeypatch.setattr(
        provider,
        "parse_via_local",
        lambda *_args, **_kwargs: pytest.fail("local provider must not be called"),
    )

    provider.parse_pdf(
        "source.pdf",
        "document.pdf",
        str(tmp_path),
        s3_key="uploads/job-1.pdf",
        job_metadata=metadata,
    )

    assert calls == [
        {
            "pdf_path": "source.pdf",
            "filename": "document.pdf",
            "output_dir": str(tmp_path),
            "s3_key": "uploads/job-1.pdf",
            "job_metadata": metadata,
        }
    ]


def test_pdf_parser_forwards_job_metadata_to_standard_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pdf_parser = importlib.import_module(
        "app.services.document_parser.formats.pdf.parser"
    )
    PdfRoutingCategory = importlib.import_module(
        "app.services.document_parser.profiling.taxonomy"
    ).PdfRoutingCategory
    metadata = _approved_object_storage_metadata()
    calls: list[dict[str, object]] = []

    def fake_parse_pdf(
        _pdf_path: str,
        _filename: str,
        _output_dir: str,
        *,
        s3_key: str | None = None,
        job_metadata: dict[str, object] | None = None,
    ) -> None:
        calls.append({"s3_key": s3_key, "job_metadata": job_metadata})

    monkeypatch.setattr(pdf_parser, "parse_pdf", fake_parse_pdf)
    monkeypatch.setattr(pdf_parser, "parse_md", lambda *_args, **_kwargs: {"ok": True})

    result = pdf_parser.parse_pdfs(
        str(tmp_path / "source.pdf"),
        "source.pdf",
        str(tmp_path / "output"),
        {},
        profile=SimpleNamespace(
            routing_category=PdfRoutingCategory.GENERIC,
            anatomy=None,
            page_count=1,
        ),
        s3_key="uploads/job-1.pdf",
        job_metadata=metadata,
    )

    assert result == {"ok": True}
    assert calls == [{"s3_key": "uploads/job-1.pdf", "job_metadata": metadata}]


def test_pdf_shard_fast_path_forwards_job_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    pdf_parser = importlib.import_module(
        "app.services.document_parser.formats.pdf.parser"
    )
    markdown_parser = importlib.import_module(
        "app.services.document_parser.formats.markdown.parser"
    )
    shard_merger = importlib.import_module(
        "app.services.document_parser.formats.pdf.shard_merger"
    )
    shard_splitter = importlib.import_module(
        "app.services.document_parser.formats.pdf.shard_splitter"
    )
    metadata = _approved_object_storage_metadata()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    calls: list[dict[str, object]] = []

    def fake_parse_pdf(
        _pdf_path: str,
        filename: str,
        out_dir: str,
        *,
        s3_key: str | None = None,
        job_metadata: dict[str, object] | None = None,
    ) -> None:
        calls.append(
            {
                "filename": filename,
                "s3_key": s3_key,
                "job_metadata": job_metadata,
            }
        )
        Path(out_dir, "full.md").write_text("1. Introduction\nBody\n", encoding="utf-8")

    monkeypatch.setattr(pdf_parser, "parse_pdf", fake_parse_pdf)
    monkeypatch.setattr(
        shard_splitter,
        "bin_pack_shards",
        lambda _shards, max_pages: [
            SimpleNamespace(
                shard_index=0,
                page_start=1,
                page_end=2,
                page_count=min(2, max_pages),
            )
        ],
    )
    monkeypatch.setattr(markdown_parser, "merge_html_tables", lambda lines: lines)
    monkeypatch.setattr(
        markdown_parser,
        "eval_md_headings",
        lambda lines, *_args, **_kwargs: [
            f"# {line}" if line.startswith("1.") else line for line in lines
        ],
    )
    monkeypatch.setattr(
        shard_merger,
        "merge_shard_lines",
        lambda line_groups, **_kwargs: [line for lines in line_groups for line in lines],
    )
    monkeypatch.setattr(
        pdf_parser,
        "parse_md",
        lambda *_args, **kwargs: {"lines": kwargs["lines_with_heading"]},
    )

    profile = SimpleNamespace(
        anatomy=SimpleNamespace(
            shard_plan=SimpleNamespace(shards=[SimpleNamespace(page_start=1)]),
            toc_hierarchies=[],
            toc_result=None,
        )
    )

    result = pdf_parser._parse_pdf_via_shards(
        str(tmp_path / "source.pdf"),
        "source.pdf",
        str(output_dir),
        {"smart_title_parse": False, "model_name": "test-model"},
        profile=profile,
        s3_key="uploads/job-1.pdf",
        job_metadata=metadata,
    )

    assert calls == [
        {
            "filename": "source.pdf",
            "s3_key": "uploads/job-1.pdf",
            "job_metadata": metadata,
        }
    ]
    assert result == {"lines": ["# 1. Introduction", "Body"]}


def test_cached_rendered_pdf_inspection_forwards_job_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rendered_transform = importlib.import_module(
        "app.services.document_parser.formats.pdf.rendered_transform"
    )
    metadata = _approved_object_storage_metadata()
    calls: list[dict[str, object]] = []

    def fake_get_existing(
        storage_key: str,
        *,
        job_metadata: dict[str, object] | None = None,
    ) -> None:
        calls.append({"storage_key": storage_key, "job_metadata": job_metadata})
        return None

    monkeypatch.setattr(
        rendered_transform,
        "get_existing_mineru_source_s3_key",
        fake_get_existing,
    )

    result = rendered_transform.parse_cached_rendered_pdf(
        rendered_pdf_s3_key="transform/job-1.rendered.pdf",
        filename="source.pptx",
        output_dir=str(tmp_path),
        base_llm_paras={},
        relative_root=None,
        job_metadata=metadata,
    )

    assert result is None
    assert calls == [
        {
            "storage_key": "transform/job-1.rendered.pdf",
            "job_metadata": metadata,
        }
    ]
