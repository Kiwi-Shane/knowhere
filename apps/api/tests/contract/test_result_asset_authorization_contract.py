from __future__ import annotations

import os
from types import SimpleNamespace

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
                "source_scope": "api-result-asset-contract",
                "authorization_id": "auth-api-result-asset-contract",
                "approved_by": "qa-contract",
            }
        }
    }


def test_document_chunk_asset_url_forwards_job_authorization() -> None:
    from app.services.documents.lifecycle_service import DocumentService

    metadata = _approved_object_storage_metadata()
    calls: list[dict[str, object]] = []

    class RecordingResultStorage:
        def normalize_artifact_ref(self, artifact_ref: str | None) -> str | None:
            return artifact_ref

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

    storage = RecordingResultStorage()
    chunk = SimpleNamespace(
        chunk_type="image",
        file_path="images/image.png",
        chunk_metadata={},
        id="chunk-row-1",
        chunk_id="chunk-1",
        section_id="section-1",
        content="image description",
        source_chunk_path=None,
        sort_order=0,
        created_at=None,
    )
    section = SimpleNamespace(section_path="Root")

    payload = DocumentService()._chunk_payload(
        chunk=chunk,  # type: ignore[arg-type]
        section=section,  # type: ignore[arg-type]
        job_id="job-1",
        job_metadata=metadata,
        include_asset_urls=True,
        result_storage=storage,  # type: ignore[arg-type]
    )

    assert payload["asset_url"] == "https://assets.example.test/image.png"
    assert calls[0]["job_metadata"] is metadata
