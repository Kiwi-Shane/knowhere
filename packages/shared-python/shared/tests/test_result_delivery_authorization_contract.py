from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from shared.services.jobs.result_delivery import JobResultDeliveryResolver


def _approved_object_storage_metadata() -> dict[str, object]:
    return {
        "external_call_authorizations": {
            "object_storage": {
                "approved": True,
                "provider": "object_storage",
                "data_classification": "synthetic",
                "source_scope": "result-delivery-contract",
                "authorization_id": "auth-result-delivery-contract",
                "approved_by": "qa-contract",
            }
        }
    }


class _RecordingStorage:
    results_bucket = "contract-results"

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_download_url(
        self,
        storage_key: str,
        *,
        bucket: str,
        expires_in: int = 3600,
        job_metadata: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "storage_key": storage_key,
                "bucket": bucket,
                "expires_in": expires_in,
                "job_metadata": job_metadata,
            }
        )
        return {"download_url": "signed://contract", "expires_in": expires_in}


def test_result_delivery_propagates_job_metadata_to_download_url() -> None:
    storage = _RecordingStorage()
    resolver = JobResultDeliveryResolver(storage=storage)  # type: ignore[arg-type]
    metadata = _approved_object_storage_metadata()

    delivery = resolver.resolve(
        SimpleNamespace(
            inline_payload=None,
            result_s3_key="results/job-1.zip",
        ),
        job_metadata=metadata,
    )

    assert delivery.result_url == "signed://contract"
    assert storage.calls == [
        {
            "storage_key": "results/job-1.zip",
            "bucket": "contract-results",
            "expires_in": 3600,
            "job_metadata": metadata,
        }
    ]


def test_result_delivery_enrichment_propagates_job_metadata() -> None:
    storage = _RecordingStorage()
    resolver = JobResultDeliveryResolver(storage=storage)  # type: ignore[arg-type]
    metadata = _approved_object_storage_metadata()
    payload = {"event": "job.completed", "job_id": "job-1"}

    enriched = resolver.enrich_payload(
        payload,
        job_result=SimpleNamespace(
            inline_payload=None,
            result_s3_key="results/job-1.zip",
        ),
        job_metadata=metadata,
    )

    assert enriched["result_url"] == "signed://contract"
    assert storage.calls[0]["job_metadata"] == metadata
