from __future__ import annotations

import importlib
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
                "source_scope": "source-url-download-contract",
                "authorization_id": "auth-source-url-download-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def _source_url_storage(monkeypatch: pytest.MonkeyPatch):
    storage_module = importlib.import_module("shared.services.storage.job_file_storage")
    monkeypatch.setattr(storage_module.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        storage_module.settings,
        "SOURCE_URL_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    return storage_module


def test_source_url_download_rejects_missing_authorization_before_url_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    storage_module = _source_url_storage(monkeypatch)
    exceptions_module = importlib.import_module(
        "shared.core.exceptions.domain_exceptions"
    )
    monkeypatch.setattr(
        storage_module,
        "validate_http_url_and_resolve_ip",
        lambda _url: pytest.fail("URL validation must not run before authorization"),
    )

    with pytest.raises(
        exceptions_module.PermissionDeniedException,
        match="source_url",
    ):
        storage_module.JobFileStorage().download_file_from_url(
            "https://example.test/source.pdf",
            temp_dir=str(tmp_path),
        )


def test_source_url_download_requires_operator_opt_in_before_authorization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    storage_module = importlib.import_module("shared.services.storage.job_file_storage")
    monkeypatch.setattr(storage_module.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        storage_module.settings,
        "SOURCE_URL_EXTERNAL_CALLS_ENABLED",
        False,
        raising=False,
    )
    monkeypatch.setattr(
        storage_module,
        "validate_http_url_and_resolve_ip",
        lambda _url: pytest.fail("URL validation must not run before opt-in"),
    )
    exceptions_module = importlib.import_module(
        "shared.core.exceptions.domain_exceptions"
    )

    with pytest.raises(
        exceptions_module.SystemSettingMissingException,
        match="SOURCE_URL_EXTERNAL_CALLS_ENABLED=true",
    ):
        storage_module.JobFileStorage().download_file_from_url(
            "https://example.test/source.pdf",
            temp_dir=str(tmp_path),
            job_metadata=_approved_source_url_metadata(),
        )


def test_source_url_download_forwards_approved_metadata_to_pinned_transfer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    storage_module = _source_url_storage(monkeypatch)
    metadata = _approved_source_url_metadata()
    transfer_calls: list[dict[str, object]] = []
    downloaded_path = tmp_path / "source.pdf"
    downloaded_path.write_bytes(b"synthetic source")

    def fake_validate(_url: str) -> SimpleNamespace:
        return SimpleNamespace(
            is_valid=True,
            url="https://example.test/source.pdf",
            validated_ip="93.184.216.34",
            error_message=None,
        )

    def fake_download(**kwargs: object) -> SimpleNamespace:
        transfer_calls.append(kwargs)
        return SimpleNamespace(status=200, temp_file_path=str(downloaded_path))

    monkeypatch.setattr(
        storage_module, "validate_http_url_and_resolve_ip", fake_validate
    )
    monkeypatch.setattr(
        storage_module,
        "download_pinned_outbound_file",
        fake_download,
    )

    result = storage_module.JobFileStorage().download_file_from_url(
        "https://example.test/source.pdf",
        temp_dir=str(tmp_path),
        job_metadata=metadata,
    )

    assert result == str(downloaded_path)
    assert transfer_calls == [
        {
            "url": "https://example.test/source.pdf",
            "pinned_ip": "93.184.216.34",
            "timeout_seconds": 300,
            "user_agent": "Knowhere-FileDownloader/1.0",
            "temp_dir": str(tmp_path),
        }
    ]


def test_source_url_type_resolution_rejects_disabled_external_calls_before_dns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url_file_type = importlib.import_module("shared.services.http.url_file_type")
    monkeypatch.setattr(url_file_type.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        url_file_type.settings,
        "SOURCE_URL_EXTERNAL_CALLS_ENABLED",
        False,
        raising=False,
    )
    monkeypatch.setattr(
        url_file_type,
        "validate_http_url_and_resolve_ip",
        lambda _url: pytest.fail("URL validation must not run before opt-in"),
    )
    exceptions_module = importlib.import_module(
        "shared.core.exceptions.domain_exceptions"
    )

    with pytest.raises(
        exceptions_module.SystemSettingMissingException,
        match="SOURCE_URL_EXTERNAL_CALLS_ENABLED=true",
    ):
        url_file_type.resolve_file_extension_sync("https://example.test/source.pdf")
