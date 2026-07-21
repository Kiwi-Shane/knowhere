from __future__ import annotations

import io
import os
import stat
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from app.services.common import file_loading
from shared.utils import zip_download


def _zip_bytes(*members: tuple[str, bytes]) -> bytes:
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        for name, content in members:
            zip_file.writestr(name, content)
    return archive.getvalue()


def test_load_file_bytes_routes_remote_content_through_guarded_downloader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, float]] = []

    class FakeJobFileStorage:
        def download_file_from_url(
            self,
            file_url: str,
            *,
            temp_dir: str | None = None,
            timeout_seconds: float = 0,
            job_metadata: dict[str, object] | None = None,
        ) -> str:
            del job_metadata
            assert temp_dir is not None
            calls.append((file_url, temp_dir, timeout_seconds))
            downloaded_path = Path(temp_dir) / "remote.bin"
            downloaded_path.write_bytes(b"guarded remote bytes")
            return str(downloaded_path)

    class ForbiddenHTTPXClient:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("raw httpx remote loading must not be used")

    monkeypatch.setattr(file_loading, "JobFileStorage", FakeJobFileStorage, raising=False)
    monkeypatch.setattr(
        file_loading,
        "httpx",
        SimpleNamespace(Client=ForbiddenHTTPXClient),
        raising=False,
    )

    assert (
        file_loading.load_file_bytes(
            "https://example.test/document.pdf",
            file_url="https://example.test/document.pdf",
        )
        == b"guarded remote bytes"
    )
    assert len(calls) == 1
    assert calls[0][0] == "https://example.test/document.pdf"
    assert calls[0][2] == 300.0


def test_download_and_extract_zip_rejects_invalid_url_before_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    requested = False

    def invalid_url(_url: str) -> SimpleNamespace:
        return SimpleNamespace(
            is_valid=False,
            url="https://example.test/result.zip",
            validated_ip=None,
            error_message="host is not allowed",
        )

    def forbidden_raw_get(*_args: object, **_kwargs: object) -> None:
        nonlocal requested
        requested = True
        raise AssertionError("raw requests.get must not be used")

    monkeypatch.setattr(zip_download, "validate_http_url_and_resolve_ip", invalid_url, raising=False)
    monkeypatch.setattr(
        zip_download,
        "requests",
        SimpleNamespace(get=forbidden_raw_get),
        raising=False,
    )

    with pytest.raises(ValueError, match="host is not allowed"):
        zip_download.download_and_extract_zip(
            "https://example.test/result.zip",
            tmp_path / "output",
            timeout=5,
            chunk_size=16,
        )

    assert requested is False


@pytest.mark.parametrize(
    "member_name",
    [
        "../escaped.json",
        "/absolute.json",
        "nested/../../escaped.json",
        r"..\escaped.json",
        r"C:\escaped.json",
    ],
)
def test_download_and_extract_zip_rejects_unsafe_archive_members(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    member_name: str,
) -> None:
    archive_bytes = _zip_bytes((member_name, b"must not escape"))
    destination = tmp_path / "output"
    pinned_archive = tmp_path / "pinned-result.zip"

    def valid_url(url: str) -> SimpleNamespace:
        return SimpleNamespace(
            is_valid=True,
            url=url,
            validated_ip="93.184.216.34",
            error_message=None,
        )

    def fake_pinned_download(**_kwargs: object) -> SimpleNamespace:
        pinned_archive.write_bytes(archive_bytes)
        return SimpleNamespace(status=200, temp_file_path=str(pinned_archive))

    class FakeRawResponse:
        def __enter__(self) -> FakeRawResponse:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_content(self, *, chunk_size: int) -> list[bytes]:
            assert chunk_size == 16
            return [archive_bytes]

    def fake_raw_get(*_args: object, **_kwargs: object) -> FakeRawResponse:
        return FakeRawResponse()

    monkeypatch.setattr(zip_download, "validate_http_url_and_resolve_ip", valid_url, raising=False)
    monkeypatch.setattr(
        zip_download,
        "download_pinned_outbound_file",
        fake_pinned_download,
        raising=False,
    )
    monkeypatch.setattr(
        zip_download,
        "requests",
        SimpleNamespace(get=fake_raw_get),
        raising=False,
    )

    with pytest.raises(ValueError, match="unsafe ZIP member"):
        zip_download.download_and_extract_zip(
            "https://example.test/result.zip",
            destination,
            timeout=5,
            chunk_size=16,
        )

    assert not (tmp_path / "escaped.json").exists()


def test_download_and_extract_zip_uses_pinned_download_and_filters_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive_bytes = _zip_bytes(
        ("nested/result.json", b"{}"),
        ("nested/drop.txt", b"not retained"),
    )
    destination = tmp_path / "output"
    captured: dict[str, object] = {}

    def valid_url(url: str) -> SimpleNamespace:
        return SimpleNamespace(
            is_valid=True,
            url=url,
            validated_ip="93.184.216.34",
            error_message=None,
        )

    def fake_pinned_download(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        temp_dir = Path(str(kwargs["temp_dir"]))
        pinned_archive = temp_dir / "pinned-result.zip"
        pinned_archive.write_bytes(archive_bytes)
        return SimpleNamespace(status=200, temp_file_path=str(pinned_archive))

    def forbidden_raw_get(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("raw requests.get must not be used")

    monkeypatch.setattr(zip_download, "validate_http_url_and_resolve_ip", valid_url)
    monkeypatch.setattr(zip_download, "download_pinned_outbound_file", fake_pinned_download)
    monkeypatch.setattr(
        zip_download,
        "requests",
        SimpleNamespace(get=forbidden_raw_get),
        raising=False,
    )

    zip_download.download_and_extract_zip(
        "https://example.test/result.zip",
        destination,
        headers={"Authorization": "Bearer test"},
        timeout=5,
        chunk_size=16,
    )

    assert (destination / "nested" / "result.json").read_bytes() == b"{}"
    assert not (destination / "nested" / "drop.txt").exists()
    assert captured["headers"] == {"Authorization": "Bearer test"}
    assert captured["pinned_ip"] == "93.184.216.34"
    assert captured["chunk_size"] == 16


def test_download_and_extract_zip_rejects_symlink_members(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    archive = io.BytesIO()
    symlink_info = zipfile.ZipInfo("link.json")
    symlink_info.create_system = 3
    symlink_info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr(symlink_info, "outside.json")
    archive_bytes = archive.getvalue()
    pinned_archive = tmp_path / "pinned-result.zip"

    def valid_url(url: str) -> SimpleNamespace:
        return SimpleNamespace(
            is_valid=True,
            url=url,
            validated_ip="93.184.216.34",
            error_message=None,
        )

    def fake_pinned_download(**_kwargs: object) -> SimpleNamespace:
        pinned_archive.write_bytes(archive_bytes)
        return SimpleNamespace(status=200, temp_file_path=str(pinned_archive))

    monkeypatch.setattr(zip_download, "validate_http_url_and_resolve_ip", valid_url)
    monkeypatch.setattr(zip_download, "download_pinned_outbound_file", fake_pinned_download)

    with pytest.raises(ValueError, match="unsafe ZIP member"):
        zip_download.download_and_extract_zip(
            "https://example.test/result.zip",
            tmp_path / "output",
            timeout=5,
            chunk_size=16,
        )
