from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest import MonkeyPatch

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from shared.core.config.storage import StorageConfig
from shared.core.exceptions.domain_exceptions import (
    PermissionDeniedException,
    SystemSettingInvalidException,
    SystemSettingMissingException,
)
from shared.services.storage.adapters import FileSystemStorageAdapter, S3StorageAdapter
from shared.services.storage.file_upload_service import FileUploadService
from shared.services.storage.job_file_storage import JobFileStorage


def _storage_config(
    *,
    storage_type: str = "s3",
    external_calls_enabled: bool = False,
    local_root: str = "/tmp/knowhere-object-storage",
) -> StorageConfig:
    return StorageConfig(
        S3_TYPE=storage_type,
        S3_BUCKET_NAME="contract-bucket",
        S3_ACCESS_KEY_ID="contract-access-key",
        S3_SECRET_ACCESS_KEY="contract-secret-key",
        S3_TEMP_PATH="/tmp",
        OBJECT_STORAGE_LOCAL_ROOT=local_root,
        OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED=external_calls_enabled,
        OSS_ENDPOINT="https://oss.contract.test",
    )


def _approved_object_storage_metadata() -> dict[str, object]:
    return {
        "external_call_authorizations": {
            "object_storage": {
                "approved": True,
                "provider": "object_storage",
                "data_classification": "synthetic",
                "source_scope": "storage-upload-contract",
                "authorization_id": "auth-storage-upload-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def test_s3_factory_requires_explicit_external_storage_opt_in(
    monkeypatch: MonkeyPatch,
) -> None:
    config = _storage_config(external_calls_enabled=False)
    client_calls: list[dict[str, object]] = []

    def unexpected_boto_client(**kwargs: object) -> object:
        client_calls.append(kwargs)
        raise AssertionError("disabled storage must not construct an S3 client")

    monkeypatch.setattr("shared.core.config.storage.boto3.client", unexpected_boto_client)

    with pytest.raises(
        SystemSettingMissingException,
        match="OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED=true",
    ):
        config.get_storage_adapter()

    assert client_calls == []


def test_oss_factory_requires_explicit_external_storage_opt_in(
    monkeypatch: MonkeyPatch,
) -> None:
    config = _storage_config(storage_type="oss", external_calls_enabled=False)

    class UnexpectedOss2:
        Auth = SimpleNamespace
        Bucket = SimpleNamespace

    monkeypatch.setitem(sys.modules, "oss2", UnexpectedOss2)

    with pytest.raises(
        SystemSettingMissingException,
        match="OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED=true",
    ):
        config.get_storage_adapter()


def test_filesystem_storage_remains_local_when_external_storage_is_disabled(
    tmp_path: Path,
) -> None:
    adapter = _storage_config(
        storage_type="filesystem",
        external_calls_enabled=False,
        local_root=str(tmp_path),
    ).get_storage_adapter()

    assert isinstance(adapter, FileSystemStorageAdapter)


def test_s3_factory_can_construct_an_adapter_only_after_explicit_opt_in(
    monkeypatch: MonkeyPatch,
) -> None:
    config = _storage_config(external_calls_enabled=True)
    fake_client = object()
    monkeypatch.setattr(
        "shared.core.config.storage.boto3.client",
        lambda **kwargs: fake_client,
    )

    adapter = config.get_storage_adapter()

    assert isinstance(adapter, S3StorageAdapter)
    assert adapter.s3_client is fake_client


def test_storage_config_rejects_unbounded_presigned_url_expiration() -> None:
    config = _storage_config(external_calls_enabled=True)

    with pytest.raises(
        SystemSettingInvalidException,
        match="OBJECT_STORAGE_MAX_PRESIGN_SECONDS",
    ):
        config.validate_presign_expiration(0)

    with pytest.raises(
        SystemSettingInvalidException,
        match="OBJECT_STORAGE_MAX_PRESIGN_SECONDS",
    ):
        config.validate_presign_expiration(604801)


def test_job_file_storage_rejects_overlong_download_url_before_adapter_call() -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def generate_presigned_url(
            self,
            key: str,
            **kwargs: object,
        ) -> str:
            kwargs["key"] = key
            self.calls.append(kwargs)
            return "signed://contract"

    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    with pytest.raises(
        SystemSettingInvalidException,
        match="OBJECT_STORAGE_MAX_PRESIGN_SECONDS",
    ):
        storage.generate_download_url(
            "results/job-1/report.pdf",
            bucket="contract-results",
            expires_in=604801,
        )

    assert adapter.calls == []


def test_job_file_storage_passes_bounded_download_url_lifetime_to_adapter() -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def generate_presigned_url(
            self,
            key: str,
            **kwargs: object,
        ) -> str:
            kwargs["key"] = key
            self.calls.append(kwargs)
            return "signed://contract"

    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    result = storage.generate_download_url(
        "results/job-1/report.pdf",
        bucket="contract-results",
        expires_in=604800,
    )

    assert result == {
        "download_url": "signed://contract",
        "expires_in": 604800,
    }
    assert adapter.calls == [
        {
            "expiration": 604800,
            "bucket": "contract-results",
            "method": "GET",
            "key": "results/job-1/report.pdf",
        }
    ]


def test_job_file_storage_validates_configured_upload_url_lifetime_before_signing(
    monkeypatch: MonkeyPatch,
) -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def generate_presigned_url(
            self,
            key: str,
            **kwargs: object,
        ) -> str:
            kwargs["key"] = key
            self.calls.append(kwargs)
            return "signed://contract"

    monkeypatch.setattr(
        "shared.core.config.settings.JOB_WAITING_EXPIRE_SECONDS",
        604801,
        raising=False,
    )
    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    with pytest.raises(
        SystemSettingInvalidException,
        match="OBJECT_STORAGE_MAX_PRESIGN_SECONDS",
    ):
        storage.generate_upload_url(job_id="job-1", file_extension=".pdf")

    assert adapter.calls == []


def test_job_file_storage_rejects_remote_upload_url_without_job_authorization(
    monkeypatch: MonkeyPatch,
) -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def generate_presigned_url(
            self,
            key: str,
            **kwargs: object,
        ) -> str:
            kwargs["key"] = key
            self.calls.append(kwargs)
            return "signed://contract"

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    with pytest.raises(PermissionDeniedException, match="object_storage"):
        storage.generate_upload_url(
            job_id="job-1",
            file_extension=".pdf",
            job_metadata=None,
        )

    assert adapter.calls == []


def test_job_file_storage_allows_remote_upload_url_with_approved_job_authorization(
    monkeypatch: MonkeyPatch,
) -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def generate_presigned_url(
            self,
            key: str,
            **kwargs: object,
        ) -> str:
            kwargs["key"] = key
            self.calls.append(kwargs)
            return "signed://contract"

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    result = storage.generate_upload_url(
        job_id="job-1",
        file_extension=".pdf",
        job_metadata=_approved_object_storage_metadata(),
    )

    assert result["upload_url"] == "signed://contract"
    assert adapter.calls and adapter.calls[0]["method"] == "PUT"


def test_job_file_storage_rejects_remote_result_upload_without_job_authorization(
    monkeypatch: MonkeyPatch,
) -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def upload_file(
            self,
            local_path: str,
            key: str,
            bucket: str | None = None,
        ) -> dict[str, object]:
            self.calls.append(
                {"local_path": local_path, "key": key, "bucket": bucket}
            )
            return {"key": key}

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    with pytest.raises(PermissionDeniedException, match="object_storage"):
        storage.upload_local_file(
            "result.zip",
            "results/job-1.zip",
            bucket="contract-results",
            job_metadata=None,
        )

    assert adapter.calls == []


def test_job_file_storage_allows_remote_result_upload_with_approved_job_authorization(
    monkeypatch: MonkeyPatch,
) -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def upload_file(
            self,
            local_path: str,
            key: str,
            bucket: str | None = None,
        ) -> dict[str, object]:
            self.calls.append(
                {"local_path": local_path, "key": key, "bucket": bucket}
            )
            return {"key": key}

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    result = storage.upload_local_file(
        "result.zip",
        "results/job-1.zip",
        bucket="contract-results",
        job_metadata=_approved_object_storage_metadata(),
    )

    assert result == {"key": "results/job-1.zip"}
    assert adapter.calls == [
        {
            "local_path": "result.zip",
            "key": "results/job-1.zip",
            "bucket": "contract-results",
        }
    ]


def test_job_file_storage_rejects_remote_source_verification_without_job_authorization(
    monkeypatch: MonkeyPatch,
) -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def exists(self, key: str, bucket: str | None = None) -> bool:
            del bucket
            self.calls.append(f"exists:{key}")
            return True

        def get_object_size(self, key: str, bucket: str | None = None) -> int:
            del bucket
            self.calls.append(f"size:{key}")
            return 1

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    with pytest.raises(PermissionDeniedException, match="object_storage"):
        storage.verify_upload_exists(
            "uploads/job-1.pdf",
            job_metadata=None,
        )

    assert adapter.calls == []


def test_job_file_storage_rejects_remote_source_download_without_job_authorization(
    monkeypatch: MonkeyPatch,
) -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def download_file(
            self,
            key: str,
            local_path: str,
            bucket: str | None = None,
        ) -> str:
            del local_path, bucket
            self.calls.append(key)
            return ""

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    with pytest.raises(PermissionDeniedException, match="object_storage"):
        storage.download_upload_to_temp(
            "uploads/job-1.pdf",
            suffix=".pdf",
            temp_dir="/tmp/contract",
            job_metadata=None,
        )

    assert adapter.calls == []


def test_job_file_storage_rejects_remote_source_upload_without_job_authorization(
    monkeypatch: MonkeyPatch,
) -> None:
    class RecordingStorageAdapter:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def upload_file(
            self,
            local_path: str,
            key: str,
            bucket: str | None = None,
        ) -> dict[str, object]:
            del local_path, bucket
            self.calls.append(key)
            return {"key": key}

    monkeypatch.setattr(
        "shared.core.config.settings.OBJECT_STORAGE_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    monkeypatch.setattr("shared.core.config.settings.S3_TYPE", "s3", raising=False)
    adapter = RecordingStorageAdapter()
    storage = JobFileStorage(storage_adapter=adapter)  # type: ignore[arg-type]

    with pytest.raises(PermissionDeniedException, match="object_storage"):
        storage.upload_source_file(
            "source.pdf",
            "uploads/job-1.pdf",
            job_metadata=None,
        )

    assert adapter.calls == []


@pytest.mark.asyncio
async def test_file_upload_service_propagates_job_metadata_to_storage_upload_url() -> None:
    class RecordingStorage:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def generate_upload_url(self, **kwargs: object) -> dict[str, object]:
            self.calls.append(kwargs)
            return {
                "upload_url": "signed://contract",
                "s3_key": "uploads/job-1.pdf",
                "expires_in": 3600,
                "upload_headers": {"Content-Type": "application/pdf"},
            }

    storage = RecordingStorage()
    service = FileUploadService(storage=storage)  # type: ignore[arg-type]
    metadata = _approved_object_storage_metadata()

    await service.generate_upload_url(
        "job-1",
        ".pdf",
        job_metadata=metadata,
    )

    assert storage.calls == [
        {
            "job_id": "job-1",
            "file_extension": ".pdf",
            "job_metadata": metadata,
        }
    ]
