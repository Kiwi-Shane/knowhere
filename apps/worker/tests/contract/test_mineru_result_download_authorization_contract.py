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


def _approved_mineru_metadata() -> dict[str, object]:
    return {
        "external_call_authorizations": {
            "mineru": {
                "approved": True,
                "provider": "mineru",
                "data_classification": "synthetic",
                "source_scope": "mineru-result-download-contract",
                "authorization_id": "auth-mineru-result-download-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def _disable_only_operator_check_for_synthetic_polling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.document_parser.providers.mineru import task_polling

    settings_type = type(task_polling.settings)
    monkeypatch.setattr(
        settings_type,
        "require_mineru_external_calls_enabled",
        lambda _settings: None,
    )
    monkeypatch.setattr(
        settings_type,
        "validate_mineru_endpoint",
        lambda _settings, _url=None: "https://mineru.example.test",
    )


def test_mineru_result_poll_rejects_missing_job_authorization_before_status_request(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.services.document_parser.providers.mineru import task_polling
    from shared.core.exceptions.domain_exceptions import PermissionDeniedException

    _disable_only_operator_check_for_synthetic_polling(monkeypatch)

    class UnexpectedSession:
        def get(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError(
                "MinerU status request must not run before authorization"
            )

    monkeypatch.setattr(task_polling, "get_mineru_session", lambda: UnexpectedSession())

    with pytest.raises(PermissionDeniedException, match="mineru"):
        task_polling.poll_mineru_task(
            status_url="https://mineru.example.test/status/job-1",
            task_id="task-1",
            output_dir=str(tmp_path),
            get_status=lambda _payload: None,
        )


def test_mineru_result_poll_forwards_authorized_metadata_to_zip_download(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.services.document_parser.providers.mineru import task_polling

    _disable_only_operator_check_for_synthetic_polling(monkeypatch)
    metadata = _approved_mineru_metadata()
    calls: dict[str, object] = {}

    class FakeResponse:
        status_code = 200

        def json(self) -> dict[str, object]:
            return {
                "code": 0,
                "data": {
                    "extract_result": {
                        "state": "done",
                        "full_zip_url": "https://objects.example.test/result.zip",
                    }
                },
            }

    class FakeSession:
        def get(self, url: str, **kwargs: object) -> FakeResponse:
            calls["status_request"] = {"url": url, **kwargs}
            return FakeResponse()

    class FakeQuotaManager:
        def acquire_request(
            self,
            *,
            operation: str,
            preferred_token_id: str | None = None,
        ) -> SimpleNamespace:
            calls["quota"] = {
                "operation": operation,
                "preferred_token_id": preferred_token_id,
            }
            return SimpleNamespace(token_id="token-1", api_key="synthetic-key")

    monkeypatch.setattr(task_polling, "get_mineru_session", lambda: FakeSession())
    monkeypatch.setattr(
        task_polling,
        "get_mineru_quota_manager",
        lambda: FakeQuotaManager(),
    )

    def fake_download_and_extract_zip(
        url: str,
        dest_dir: str,
        **kwargs: object,
    ) -> None:
        calls["zip_download"] = {
            "url": url,
            "dest_dir": dest_dir,
            **kwargs,
        }

    monkeypatch.setattr(
        task_polling,
        "download_and_extract_zip",
        fake_download_and_extract_zip,
    )

    task_polling.poll_mineru_task(
        status_url="https://mineru.example.test/status/job-1",
        task_id="task-1",
        output_dir=str(tmp_path),
        get_status=task_polling.get_batch_status,
        preferred_token_id="token-1",
        job_metadata=metadata,
    )

    assert calls["status_request"]["url"] == (
        "https://mineru.example.test/status/job-1"
    )
    assert calls["zip_download"] == {
        "url": "https://objects.example.test/result.zip",
        "dest_dir": str(tmp_path),
        "keep_exts": (".md", ".jpg", ".jpeg", ".png", ".gif", ".json"),
        "exclude_patterns": ("content_list", "middle.json", "model.json"),
    }


def test_parse_via_full_forwards_job_metadata_to_result_polling(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.services.document_parser.providers.mineru import pdf_service

    metadata = _approved_mineru_metadata()
    calls: dict[str, object] = {}
    settings_type = type(pdf_service.settings)
    monkeypatch.setattr(pdf_service.settings, "MINERU_UPLOAD_MODE_ENABLED", True)
    monkeypatch.setattr(
        settings_type,
        "require_mineru_external_calls_enabled",
        lambda _settings: None,
    )
    monkeypatch.setattr(
        settings_type,
        "validate_mineru_endpoint",
        lambda _settings, _url=None: "https://mineru.example.test",
    )
    monkeypatch.setattr(
        pdf_service,
        "_request_upload_target",
        lambda _pdf_url, _filename: (
            "batch-1",
            "https://objects.example.test/upload",
            "token-1",
        ),
    )
    monkeypatch.setattr(pdf_service, "_upload_file_to_mineru", lambda *_args: None)

    def fake_poll(**kwargs: object) -> None:
        calls.update(kwargs)

    monkeypatch.setattr(pdf_service, "poll_mineru_task", fake_poll)

    pdf_service.parse_via_full(
        str(tmp_path / "source.pdf"),
        "source.pdf",
        str(tmp_path / "output"),
        job_metadata=metadata,
    )

    assert calls["job_metadata"] is metadata
