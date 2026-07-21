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
                "source_scope": "result-upload-contract",
                "authorization_id": "auth-result-upload-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def test_result_storage_passes_job_authorization_before_remote_bundle_upload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from shared.services.storage.result_storage import JobResultStorage

    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.uploaded_keys: list[str] = []

        def upload_file(
            self,
            local_path: str,
            key: str,
            bucket: str | None = None,
        ) -> dict[str, object]:
            del local_path, bucket
            self.uploaded_keys.append(key)
            return {"key": key}

        def generate_presigned_url(self, *args: object, **kwargs: object) -> str:
            del args, kwargs
            return "https://assets.example.test/file"

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)

    result_dir = tmp_path / "result"
    result_dir.mkdir()
    (result_dir / "source.pdf").write_bytes(b"synthetic source")
    zip_path = tmp_path / "result.zip"
    zip_path.write_bytes(b"synthetic zip")

    adapter = RecordingStorageAdapter()
    storage = JobResultStorage(
        results_bucket="test-results",
        storage_adapter=adapter,  # type: ignore[arg-type]
    )

    bundle = storage.upload(
        job_id="job-1",
        result_dir=str(result_dir),
        zip_file_path=str(zip_path),
        artifact_refs={"source.pdf"},
        job_metadata=_approved_object_storage_metadata(),
    )

    assert bundle.zip_key == "results/job-1.zip"
    assert adapter.uploaded_keys == [
        "results/job-1.zip",
        "results/job-1/source.pdf",
    ]


def test_worker_result_upload_forwards_job_metadata_to_result_storage(
    tmp_path: Path,
) -> None:
    from app.services.document_ingestion.success_finalization import (
        _upload_result_package,
    )

    result_dir = tmp_path / "result"
    result_dir.mkdir()
    zip_path = tmp_path / "result.zip"
    zip_path.write_bytes(b"synthetic zip")
    metadata = _approved_object_storage_metadata()
    calls: dict[str, object] = {}

    class RecordingResultStorage:
        def upload(self, **kwargs: object) -> object:
            calls.update(kwargs)
            return SimpleNamespace(zip_key="results/job-1.zip")

    result_package = SimpleNamespace(
        chunks=[],
        artifact=SimpleNamespace(add_dir=str(result_dir)),
    )
    generated_package = SimpleNamespace(zip_file_path=str(zip_path))

    result = _upload_result_package(
        result_package=result_package,
        generated_package=generated_package,
        job_id="job-1",
        job_metadata=metadata,
        result_storage_factory=lambda: RecordingResultStorage(),  # type: ignore[return-value]
    )

    assert result == "results/job-1.zip"
    assert calls["job_metadata"] is metadata
