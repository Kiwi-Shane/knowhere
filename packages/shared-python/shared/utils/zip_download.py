"""Download-and-extract helpers for remote ZIP artifacts."""

import fnmatch
import os
import shutil
import stat
import tempfile
import zipfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import cast

from shared.services.http.pinned_outbound import download_pinned_outbound_file
from shared.services.http.url_security import validate_http_url_and_resolve_ip


def _safe_member_path(destination: Path, member_name: str) -> Path:
    """Return a destination path only when a ZIP member stays inside it."""
    if not member_name or "\x00" in member_name:
        raise ValueError(f"unsafe ZIP member: {member_name!r}")

    normalized_name = member_name.replace("\\", "/")
    posix_member = PurePosixPath(normalized_name)
    windows_member = PureWindowsPath(normalized_name)
    if (
        posix_member.is_absolute()
        or windows_member.is_absolute()
        or windows_member.drive
    ):
        raise ValueError(f"unsafe ZIP member: {member_name!r}")

    parts = tuple(part for part in posix_member.parts if part not in ("", "."))
    if not parts or ".." in parts or any(":" in part for part in parts):
        raise ValueError(f"unsafe ZIP member: {member_name!r}")

    root = destination.resolve()
    candidate = (root / Path(*parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"unsafe ZIP member: {member_name!r}") from exc

    current = root
    for part in candidate.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"unsafe ZIP member: {member_name!r}")

    return candidate


def _is_zip_symlink(member: zipfile.ZipInfo) -> bool:
    mode = (member.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def _extract_zip_safely(
    extracted_zip: zipfile.ZipFile,
    destination: Path,
) -> None:
    for member in extracted_zip.infolist():
        if _is_zip_symlink(member):
            raise ValueError(f"unsafe ZIP member: {member.filename!r}")

        extracted_path = _safe_member_path(destination, member.filename)
        if member.is_dir():
            extracted_path.mkdir(parents=True, exist_ok=True)
            continue

        extracted_path.parent.mkdir(parents=True, exist_ok=True)
        with extracted_zip.open(member, "r") as source, extracted_path.open("wb") as target:
            shutil.copyfileobj(source, target)


def download_and_extract_zip(
    url: str,
    dest_dir: str | os.PathLike[str],
    *,
    filename: str = "parsed.zip",
    headers: Mapping[str, str] | None = None,
    timeout: int | None = None,
    chunk_size: int | None = None,
    keep_exts: tuple[str, ...] = (".md", ".json"),
    exclude_patterns: tuple[str, ...] = (),
    clean_empty_dirs: bool = True,
) -> None:
    """Download a ZIP file, extract it, and keep only the requested artifacts."""
    from shared.core.constants import APIConstants, ProcessingConstants

    if timeout is None:
        timeout = APIConstants.S3_FILE_DOWNLOAD_TIMEOUT
    if chunk_size is None:
        chunk_size = ProcessingConstants.IMG_CHUNK_SIZE
    effective_timeout = cast(float, timeout)

    destination = Path(dest_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    validation = validate_http_url_and_resolve_ip(url)
    if not validation.is_valid or not validation.validated_ip:
        raise ValueError(f"Invalid ZIP URL: {validation.error_message or 'URL validation failed'}")

    with tempfile.TemporaryDirectory(prefix="knowhere-zip-download-") as download_dir:
        zip_path = _safe_member_path(Path(download_dir), filename)
        download_result = download_pinned_outbound_file(
            url=validation.url,
            pinned_ip=validation.validated_ip,
            timeout_seconds=effective_timeout,
            user_agent="Knowhere-ZipDownloader/1.0",
            temp_dir=download_dir,
            headers=headers,
            chunk_size=chunk_size,
        )
        os.replace(download_result.temp_file_path, zip_path)

        with zipfile.ZipFile(zip_path, "r") as extracted_zip:
            _extract_zip_safely(extracted_zip, destination)

    for extracted_path in destination.rglob("*"):
        if not extracted_path.is_file():
            continue

        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in extracted_path.name or fnmatch.fnmatch(extracted_path.name, pattern):
                should_exclude = True
                break

        if should_exclude:
            extracted_path.unlink()
        elif extracted_path.suffix.lower() not in keep_exts:
            extracted_path.unlink()

    if clean_empty_dirs:
        for directory in sorted(
            [path for path in destination.rglob("*") if path.is_dir()],
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            try:
                next(directory.iterdir())
            except StopIteration:
                directory.rmdir()
