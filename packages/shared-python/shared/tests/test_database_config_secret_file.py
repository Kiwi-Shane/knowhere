"""Contract tests for file-backed database credentials."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp")
os.environ.setdefault("S3_BUCKET_NAME", "d2-test-bucket")
os.environ.setdefault("S3_ACCESS_KEY_ID", "d2-test-access")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "d2-test-secret")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from shared.core.config.database import DatabaseConfig


def test_runtime_database_url_reads_a_file_without_mutating_public_url(
    tmp_path,
) -> None:
    secret_path = tmp_path / "postgres_password"
    secret_path.write_text("synthetic-password\n", encoding="utf-8")
    public_url = "postgresql+asyncpg://root@postgres:5432/Knowhere"

    config = DatabaseConfig(
        DATABASE_URL=public_url,
        DATABASE_PASSWORD_FILE=str(secret_path),
    )

    assert config.DATABASE_URL == public_url
    assert config.get_runtime_database_url() == (
        "postgresql+asyncpg://root:synthetic-password@postgres:5432/Knowhere"
    )
    assert "synthetic-password" not in config.model_dump_json()


def test_runtime_database_url_fails_closed_for_missing_or_empty_secret_file(
    tmp_path,
) -> None:
    missing_path = tmp_path / "missing_password"
    empty_path = tmp_path / "empty_password"
    empty_path.write_text("\n", encoding="utf-8")

    for secret_path in (missing_path, empty_path):
        config = DatabaseConfig(
            DATABASE_URL="postgresql+asyncpg://root@postgres:5432/Knowhere",
            DATABASE_PASSWORD_FILE=str(secret_path),
        )
        with pytest.raises(ValueError, match="DATABASE_PASSWORD_FILE"):
            config.get_runtime_database_url()
