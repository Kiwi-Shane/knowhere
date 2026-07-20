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
from shared.core.exceptions.domain_exceptions import SystemSettingMissingException
from shared.services.storage.adapters import FileSystemStorageAdapter, S3StorageAdapter


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
