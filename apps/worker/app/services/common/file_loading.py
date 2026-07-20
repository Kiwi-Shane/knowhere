"""Sync file-loading helpers for worker parsing paths."""

from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import ParseResult

from shared.services.storage.job_file_storage import JobFileStorage


def is_remote(path: object) -> bool:
    """Return True if `path` is an HTTP(S) URL."""
    if path is None or not isinstance(path, str):
        return False
    return path.startswith("http://") or path.startswith("https://")


def load_file_bytes(
    file_path: str | Path,
    *,
    file_url: str | ParseResult = "",
    timeout: float | None = None,
) -> bytes:
    """Load bytes from local path or remote URL synchronously."""
    if isinstance(file_path, str) and is_remote(file_path):
        url_to_use = file_path
        if not isinstance(file_url, str):
            file_url = file_url.geturl()
        if file_url:
            url_to_use = file_url

        effective_timeout = 300.0 if timeout is None else timeout
        with TemporaryDirectory(prefix="knowhere-remote-file-") as temp_dir:
            downloaded_path = JobFileStorage().download_file_from_url(
                url_to_use,
                temp_dir=temp_dir,
                timeout_seconds=effective_timeout,
            )
            return Path(downloaded_path).read_bytes()

    return Path(file_path).read_bytes()
