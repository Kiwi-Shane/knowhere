from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from shared.core.exceptions.domain_exceptions import PermissionDeniedException
from shared.models.schemas.job_metadata import JobMetadataHelper


def _authorization(
    *,
    provider: str = "mineru",
    data_classification: str = "synthetic",
    approved: bool = True,
) -> dict[str, object]:
    return {
        "approved": approved,
        "provider": provider,
        "data_classification": data_classification,
        "source_scope": "fixture:external-call-boundary",
        "authorization_id": "auth-external-call-contract-001",
        "approved_by": "test-operator",
    }


def test_missing_job_external_call_authorization_fails_closed() -> None:
    with pytest.raises(
        PermissionDeniedException,
        match="External call authorization",
    ):
        JobMetadataHelper.require_external_call_authorization(
            {},
            provider="mineru",
        )


@pytest.mark.parametrize(
    "data_classification",
    ["private", "customer", "unknown"],
)
def test_private_or_unknown_data_classification_is_not_authorized(
    data_classification: str,
) -> None:
    metadata = {
        "external_call_authorizations": {
            "mineru": _authorization(data_classification=data_classification),
        }
    }

    with pytest.raises(
        PermissionDeniedException,
        match="External call authorization",
    ):
        JobMetadataHelper.require_external_call_authorization(
            metadata,
            provider="mineru",
        )


@pytest.mark.parametrize("data_classification", ["synthetic", "megaforce_test", "fda_test"])
def test_approved_test_data_classification_is_returned(
    data_classification: str,
) -> None:
    authorization = _authorization(data_classification=data_classification)
    metadata = {"external_call_authorizations": {"mineru": authorization}}

    assert JobMetadataHelper.require_external_call_authorization(
        metadata,
        provider="mineru",
    ) == authorization


def test_authorization_is_provider_specific_and_requires_explicit_approval() -> None:
    metadata = {
        "external_call_authorizations": {
            "mineru": _authorization(provider="iloveapi"),
        }
    }

    with pytest.raises(PermissionDeniedException):
        JobMetadataHelper.require_external_call_authorization(
            metadata,
            provider="mineru",
        )

    metadata["external_call_authorizations"]["mineru"] = _authorization(
        approved=False,
    )
    with pytest.raises(PermissionDeniedException):
        JobMetadataHelper.require_external_call_authorization(
            metadata,
            provider="mineru",
        )


@pytest.mark.parametrize("field", ["source_scope", "authorization_id", "approved_by"])
def test_authorization_requires_traceable_non_empty_fields(field: str) -> None:
    authorization = _authorization()
    authorization[field] = ""
    metadata = {"external_call_authorizations": {"mineru": authorization}}

    with pytest.raises(PermissionDeniedException):
        JobMetadataHelper.require_external_call_authorization(
            metadata,
            provider="mineru",
        )
