from datetime import datetime, timedelta

import pytest
from cryptography.fernet import Fernet

from shared.models.database.job_llm_credential import (
    JobLLMCredential,
    JobLLMCredentialStatus,
)
from shared.models.schemas.llm_config import LLMConfig
from shared.services.ai.llm_endpoint_policy import (
    LLMEndpointPolicyError,
    normalize_provider_endpoint,
    validate_llm_config_endpoint_policy,
)
from shared.services.encryption.fernet_service import FernetService
from shared.services.jobs.job_llm_credential_service import (
    JobLLMCredentialResolutionError,
    JobLLMCredentialService,
)
from shared.core.config import settings


def _config(*, base_url: str = "https://api.example.test/v1") -> LLMConfig:
    return LLMConfig(
        api_key="sk-test-secret-value",
        model="test-model",
        base_url=base_url,
    )


def test_endpoint_policy_requires_explicit_opt_in_and_exact_allowlist() -> None:
    config = _config()

    with pytest.raises(LLMEndpointPolicyError, match="not explicitly enabled"):
        validate_llm_config_endpoint_policy(
            config,
            external_calls_enabled=False,
            allowed_endpoints="https://api.example.test/v1",
        )

    with pytest.raises(LLMEndpointPolicyError, match="not allowlisted"):
        validate_llm_config_endpoint_policy(
            config,
            external_calls_enabled=True,
            allowed_endpoints="https://other.example.test/v1",
        )


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://api.example.test/v1",
        "https://user:password@api.example.test/v1",
        "https://api.example.test/v1?redirect=https://evil.example",
        "https://127.0.0.1/v1",
        "https://10.0.0.7/v1",
    ],
)
def test_endpoint_policy_rejects_unsafe_provider_endpoints(endpoint: str) -> None:
    with pytest.raises(LLMEndpointPolicyError):
        normalize_provider_endpoint(endpoint)


def test_endpoint_normalization_is_deterministic() -> None:
    assert normalize_provider_endpoint(" HTTPS://API.EXAMPLE.TEST:443/v1/ ") == (
        "https://api.example.test/v1"
    )


def test_credential_payload_is_encrypted_and_lifecycle_is_bounded() -> None:
    encryption = FernetService(Fernet.generate_key().decode())
    expires_at = datetime.utcnow() + timedelta(hours=4)

    credential = JobLLMCredentialService.build(
        job_id="job_test_credential",
        user_id="user_test_credential",
        config=_config(),
        expires_at=expires_at,
        encryption_service=encryption,
    )

    assert isinstance(credential, JobLLMCredential)
    assert credential.id.startswith("jllm_")
    assert credential.status == JobLLMCredentialStatus.ACTIVE
    assert "sk-test-secret-value" not in credential.config_encrypted
    assert (
        JobLLMCredentialService.decrypt_config(
            credential.config_encrypted,
            encryption_service=encryption,
        ).api_key
        == "sk-test-secret-value"
    )
    assert credential.is_active(now=datetime.utcnow())
    assert not credential.is_active(now=expires_at + timedelta(seconds=1))


def test_credential_serialization_is_canonical_and_does_not_log_raw_values() -> None:
    encryption = FernetService(Fernet.generate_key().decode())
    credential = JobLLMCredentialService.build(
        job_id="job_canonical",
        user_id="user_canonical",
        config=_config(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        encryption_service=encryption,
    )

    assert credential.config_encrypted != credential.config_encrypted[::-1]
    assert "api_key" not in credential.config_encrypted


class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def one_or_none(self) -> object:
        return self._value


class _FakeSession:
    def __init__(self, value: object) -> None:
        self.value = value

    def execute(self, _statement: object) -> _FakeResult:
        return _FakeResult(self.value)


def test_worker_resolution_enforces_owner_and_rechecks_endpoint_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "LLM_EXTERNAL_CALLS_ENABLED", True)
    monkeypatch.setattr(
        settings,
        "LLM_ALLOWED_PROVIDER_ENDPOINTS",
        "https://api.example.test/v1",
    )
    encryption = FernetService(Fernet.generate_key().decode())
    credential = JobLLMCredentialService.build(
        job_id="job_resolve",
        user_id="user_resolve",
        config=_config(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        encryption_service=encryption,
    )

    resolved = JobLLMCredentialService.resolve_sync(
        _FakeSession((credential, "user_resolve")),
        job_id="job_resolve",
        requested_user_id="user_resolve",
        metadata={"llm_credential_id": credential.id},
        encryption_service=encryption,
    )

    assert resolved is not None
    assert resolved.api_key == "sk-test-secret-value"
    assert credential.last_used_at is not None

    with pytest.raises(JobLLMCredentialResolutionError, match="owner"):
        JobLLMCredentialService.resolve_sync(
            _FakeSession((credential, "user_resolve")),
            job_id="job_resolve",
            requested_user_id="different-user",
            metadata={"llm_credential_id": credential.id},
            encryption_service=encryption,
        )


def test_worker_resolution_fails_closed_for_legacy_raw_metadata() -> None:
    with pytest.raises(JobLLMCredentialResolutionError, match="missing"):
        JobLLMCredentialService.resolve_sync(
            _FakeSession(None),
            job_id="job_legacy",
            requested_user_id="user_legacy",
            metadata={"llm_config_present": True, "llm_config": {"api_key": "raw"}},
        )


def test_worker_resolution_marks_expired_credentials_before_rejecting() -> None:
    encryption = FernetService(Fernet.generate_key().decode())
    credential = JobLLMCredentialService.build(
        job_id="job_expired",
        user_id="user_expired",
        config=_config(),
        expires_at=datetime.utcnow() + timedelta(seconds=1),
        encryption_service=encryption,
    )

    with pytest.raises(JobLLMCredentialResolutionError, match="expired"):
        JobLLMCredentialService.resolve_sync(
            _FakeSession((credential, "user_expired")),
            job_id="job_expired",
            requested_user_id="user_expired",
            metadata={"llm_credential_id": credential.id},
            now=credential.expires_at + timedelta(seconds=1),
            encryption_service=encryption,
        )

    assert credential.status == JobLLMCredentialStatus.EXPIRED
