from shared.models.schemas.job import JobCreateV2
from shared.models.schemas.job_metadata import JobMetadataHelper


def test_job_metadata_keeps_only_an_opaque_byok_reference_marker() -> None:
    payload = JobCreateV2(
        source_type="file",
        file_name="sample.pdf",
        llm_config={
            "api_key": "sk-raw-secret-that-must-not-be-persisted",
            "model": "test-model",
            "base_url": "https://api.example.test/v1",
        },
    )

    metadata = JobMetadataHelper.create_from_request(payload, api_version="v2")

    assert metadata["llm_config_present"] is True
    assert "llm_config" not in metadata
    assert "llm_config" not in metadata["original_request"]
    assert "sk-raw-secret-that-must-not-be-persisted" not in repr(metadata)
    assert JobMetadataHelper.get_request_llm_config(payload).api_key == (
        "sk-raw-secret-that-must-not-be-persisted"
    )


def test_job_metadata_without_byok_has_no_credential_marker() -> None:
    payload = JobCreateV2(source_type="file", file_name="sample.pdf")

    metadata = JobMetadataHelper.create_from_request(payload, api_version="v2")

    assert "llm_config_present" not in metadata
    assert "llm_credential_id" not in metadata
