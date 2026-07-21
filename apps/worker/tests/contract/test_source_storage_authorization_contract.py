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


def _approved_object_storage_metadata() -> dict[str, object]:
    return {
        "external_call_authorizations": {
            "object_storage": {
                "approved": True,
                "provider": "object_storage",
                "data_classification": "synthetic",
                "source_scope": "source-storage-contract",
                "authorization_id": "auth-source-storage-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def test_source_preparation_forwards_job_metadata_to_storage_reads(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.services.document_ingestion import source_preparation

    source_path = tmp_path / "source.txt"
    source_path.write_text("synthetic source", encoding="utf-8")
    calls: list[dict[str, object]] = []

    class RecordingJobFileStorage:
        def verify_upload_exists(
            self,
            storage_key: str,
            *,
            job_metadata: dict[str, object] | None = None,
        ) -> dict[str, object]:
            calls.append({"operation": "verify", "key": storage_key, "metadata": job_metadata})
            return {"exists": True, "size": source_path.stat().st_size}

        def download_upload_to_temp(
            self,
            storage_key: str,
            *,
            suffix: str,
            temp_dir: str,
            job_metadata: dict[str, object] | None = None,
        ) -> str:
            calls.append(
                {
                    "operation": "download",
                    "key": storage_key,
                    "suffix": suffix,
                    "temp_dir": temp_dir,
                    "metadata": job_metadata,
                }
            )
            return str(source_path)

    monkeypatch.setattr(source_preparation, "JobFileStorage", RecordingJobFileStorage)
    metadata = _approved_object_storage_metadata()

    prepared = source_preparation.prepare_source_file(
        job_id="job-1",
        job_context=SimpleNamespace(
            job_metadata=metadata,
            s3_key="uploads/job-1.txt",
        ),
        input_dir=str(tmp_path / "input"),
    )

    assert Path(prepared.local_file_path).read_text(encoding="utf-8") == "synthetic source"
    assert [call["operation"] for call in calls] == ["verify", "download"]
    assert all(call["metadata"] is metadata for call in calls)


def test_url_upload_source_transfer_forwards_job_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.services.workload import url_upload_transfer

    calls: list[dict[str, object]] = []

    class RecordingJobFileStorage:
        def upload_source_file(
            self,
            local_file_path: str,
            storage_key: str,
            *,
            job_metadata: dict[str, object] | None = None,
        ) -> dict[str, object]:
            calls.append(
                {
                    "local_file_path": local_file_path,
                    "storage_key": storage_key,
                    "metadata": job_metadata,
                }
            )
            return {"key": storage_key}

    monkeypatch.setattr(url_upload_transfer, "JobFileStorage", RecordingJobFileStorage)
    metadata = _approved_object_storage_metadata()
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"synthetic source")

    url_upload_transfer.upload_temp_file_to_source_storage(
        temp_file_path=str(source_path),
        s3_key="uploads/job-1.pdf",
        job_metadata=metadata,
    )

    assert calls == [
        {
            "local_file_path": str(source_path),
            "storage_key": "uploads/job-1.pdf",
            "metadata": metadata,
        }
    ]
