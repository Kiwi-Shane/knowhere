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


def test_result_storage_rejects_remote_artifact_url_without_job_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from shared.core.exceptions.domain_exceptions import PermissionDeniedException
    from shared.services.storage.result_storage import JobResultStorage

    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.presign_calls: list[dict[str, object]] = []

        def generate_presigned_url(self, *args: object, **kwargs: object) -> str:
            self.presign_calls.append({"args": args, "kwargs": kwargs})
            return "https://assets.example.test/file"

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobResultStorage(
        results_bucket="test-results",
        storage_adapter=adapter,  # type: ignore[arg-type]
    )

    with pytest.raises(PermissionDeniedException, match="object_storage"):
        storage.generate_artifact_url(
            job_id="job-1",
            artifact_ref="images/asset.png",
        )

    assert adapter.presign_calls == []


def test_result_storage_rejects_remote_raw_verification_without_job_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from shared.core.exceptions.domain_exceptions import PermissionDeniedException
    from shared.services.storage.result_storage import JobResultStorage

    class RecordingStorageAdapter:
        def exists(self, *args: object, **kwargs: object) -> bool:
            del args, kwargs
            raise AssertionError("remote result verification must be denied first")

        def get_object_size(self, *args: object, **kwargs: object) -> int:
            del args, kwargs
            raise AssertionError("remote result verification must be denied first")

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    storage = JobResultStorage(
        results_bucket="test-results",
        storage_adapter=RecordingStorageAdapter(),  # type: ignore[arg-type]
    )

    with pytest.raises(PermissionDeniedException, match="object_storage"):
        storage.verify_raw_exists(
            job_id="job-1",
            relative_path="source.pdf",
        )


def test_result_storage_passes_job_authorization_to_raw_and_artifact_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from shared.services.storage.result_storage import JobResultStorage

    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.presign_calls: list[dict[str, object]] = []
            self.exists_calls: list[tuple[str, str | None]] = []

        def generate_presigned_url(self, *args: object, **kwargs: object) -> str:
            self.presign_calls.append({"args": args, "kwargs": kwargs})
            return "https://assets.example.test/file"

        def exists(self, key: str, bucket: str | None = None) -> bool:
            self.exists_calls.append((key, bucket))
            return True

        def get_object_size(self, key: str, bucket: str | None = None) -> int:
            del key, bucket
            return 1

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobResultStorage(
        results_bucket="test-results",
        storage_adapter=adapter,  # type: ignore[arg-type]
    )
    metadata = _approved_object_storage_metadata()

    assert (
        storage.generate_artifact_url(
            job_id="job-1",
            artifact_ref="images/asset.png",
            job_metadata=metadata,
        )
        == "https://assets.example.test/file"
    )
    assert (
        storage.generate_raw_file_url(
            job_id="job-1",
            relative_path="source.pdf",
            job_metadata=metadata,
        )
        == "https://assets.example.test/file"
    )
    assert storage.verify_raw_exists(
        job_id="job-1",
        relative_path="source.pdf",
        job_metadata=metadata,
    )

    assert [
        call["args"][0] for call in adapter.presign_calls
    ] == [
        "results/job-1/images/asset.png",
        "results/job-1/source.pdf",
    ]
    assert adapter.exists_calls == [("results/job-1/source.pdf", "test-results")]


def test_page_pdf_crop_forwards_job_authorization_to_result_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from shared.services.storage import page_pdf_crop

    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"synthetic source")
    metadata = _approved_object_storage_metadata()
    calls: list[dict[str, object]] = []

    class RecordingResultStorage:
        def verify_raw_exists(
            self,
            *,
            job_id: str,
            relative_path: str,
            job_metadata: dict[str, object] | None = None,
        ) -> bool:
            calls.append(
                {
                    "operation": "verify_raw_exists",
                    "job_id": job_id,
                    "relative_path": relative_path,
                    "job_metadata": job_metadata,
                }
            )
            return relative_path == "source.pdf"

        def download_raw_to_temp(
            self,
            *,
            job_id: str,
            relative_path: str,
            suffix: str,
            temp_dir: str,
            job_metadata: dict[str, object] | None = None,
        ) -> str:
            del suffix, temp_dir
            calls.append(
                {
                    "operation": "download_raw_to_temp",
                    "job_id": job_id,
                    "relative_path": relative_path,
                    "job_metadata": job_metadata,
                }
            )
            return str(source_path)

        def upload_raw_file(
            self,
            *,
            job_id: str,
            relative_path: str,
            local_file_path: str,
            job_metadata: dict[str, object] | None = None,
        ) -> None:
            del local_file_path
            calls.append(
                {
                    "operation": "upload_raw_file",
                    "job_id": job_id,
                    "relative_path": relative_path,
                    "job_metadata": job_metadata,
                }
            )

        def generate_artifact_url(
            self,
            *,
            job_id: str,
            artifact_ref: str,
            expires_in: int = 3600,
            job_metadata: dict[str, object] | None = None,
        ) -> str:
            del expires_in
            calls.append(
                {
                    "operation": "generate_artifact_url",
                    "job_id": job_id,
                    "artifact_ref": artifact_ref,
                    "job_metadata": job_metadata,
                }
            )
            return "https://assets.example.test/cropped.pdf"

    def fake_write_cropped_pdf(**kwargs: object) -> None:
        output_path = Path(str(kwargs["output_path"]))
        output_path.write_bytes(b"synthetic cropped pdf")

    monkeypatch.setattr(page_pdf_crop, "_write_cropped_pdf", fake_write_cropped_pdf)

    result = page_pdf_crop.crop_source_pdf_pages(
        job_id="job-1",
        pages=[1, 2],
        storage=RecordingResultStorage(),  # type: ignore[arg-type]
        temp_dir=str(tmp_path),
        job_metadata=metadata,
    )

    assert result == "https://assets.example.test/cropped.pdf"
    assert calls
    assert all(call["job_metadata"] is metadata for call in calls)


@pytest.mark.asyncio
async def test_retrieval_asset_url_forwards_job_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from shared.services.retrieval.hydration import assets

    metadata = _approved_object_storage_metadata()
    calls: list[dict[str, object]] = []

    class RecordingResultStorage:
        def normalize_artifact_ref(self, artifact_ref: str | None) -> str | None:
            if artifact_ref and artifact_ref.startswith("images/"):
                return artifact_ref
            return None

        def generate_artifact_url(
            self,
            *,
            job_id: str,
            artifact_ref: str,
            expires_in: int = 3600,
            job_metadata: dict[str, object] | None = None,
        ) -> str:
            del expires_in
            calls.append(
                {
                    "job_id": job_id,
                    "artifact_ref": artifact_ref,
                    "job_metadata": job_metadata,
                }
            )
            return "https://assets.example.test/image.png"

    monkeypatch.setattr(
        assets,
        "get_result_storage",
        lambda: RecordingResultStorage(),
    )

    enriched = await assets.enrich_rows_with_retrieval_asset_url(
        [
            {
                "chunk_id": "chunk-1",
                "chunk_type": "image",
                "job_id": "job-1",
                "file_path": "images/image.png",
                "_job_metadata": metadata,
            }
        ],
        log_context="contract",
    )

    assert enriched[0]["asset_url"] == "https://assets.example.test/image.png"
    assert calls[0]["job_metadata"] is metadata
