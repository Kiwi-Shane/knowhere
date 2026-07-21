from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from app.services.document_parser.formats.pdf import parser as pdf_parser


def _approved_object_storage_metadata() -> dict[str, object]:
    return {
        "external_call_authorizations": {
            "object_storage": {
                "approved": True,
                "provider": "object_storage",
                "data_classification": "synthetic",
                "source_scope": "pdf-shard-cleanup-contract",
                "authorization_id": "auth-pdf-shard-cleanup-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def test_pdf_shard_cleanup_forwards_trusted_job_metadata_to_storage_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    class RecordingStorage:
        def delete_upload_file(
            self,
            storage_key: str,
            *,
            job_metadata: dict[str, object] | None = None,
        ) -> bool:
            calls.append({"storage_key": storage_key, "job_metadata": job_metadata})
            return True

    monkeypatch.setattr(pdf_parser, "JobFileStorage", RecordingStorage)
    job_metadata = _approved_object_storage_metadata()

    pdf_parser._cleanup_temp_shard_s3_assets(
        ["tmp/mineru-shards/job-1/shard_0.pdf"],
        job_metadata=job_metadata,
    )

    assert calls == [
        {
            "storage_key": "tmp/mineru-shards/job-1/shard_0.pdf",
            "job_metadata": job_metadata,
        }
    ]


def test_checkerboard_parser_carries_job_metadata_into_parse_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.services.document_parser import parse_service

    captured: dict[str, object] = {}
    job_metadata = _approved_object_storage_metadata()

    def capture_parse_input(parse_input: object) -> object:
        captured["parse_input"] = parse_input
        return object()

    monkeypatch.setattr(parse_service, "run_parse_pipeline", capture_parse_input)
    parse_service.checkerboard_parse_output(
        file_full_path=str(tmp_path / "source.pdf"),
        filename="source.pdf",
        output_dir=str(tmp_path / "output"),
        internal_output_filename="source.pdf",
        job_id="job-1",
        s3_key="uploads/job-1.pdf",
        job_metadata=job_metadata,
    )

    assert getattr(captured["parse_input"], "job_metadata") == job_metadata
