from __future__ import annotations

import json
from contextlib import AbstractAsyncContextManager
from typing import Callable, cast

import pytest
from httpx import AsyncClient
from pytest import MonkeyPatch

from tests.support.contract_database import ContractDatabase


def _payload() -> dict[str, object]:
    return {
        "source_type": "file",
        "file_name": "contract-byok.pdf",
        "llm_config": {
            "api_key": "sk-contract-raw-secret",
            "model": "contract-model",
            "base_url": "https://example.com/v1",
        },
    }


@pytest.mark.asyncio
async def test_byok_job_persists_only_an_opaque_reference_and_ciphertext(
    developer_api_client_factory: Callable[
        [], AbstractAsyncContextManager[AsyncClient]
    ],
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_EXTERNAL_CALLS_ENABLED", "true")
    monkeypatch.setenv("LLM_ALLOWED_PROVIDER_ENDPOINTS", "https://example.com/v1")

    async with developer_api_client_factory() as api_client:
        response = await api_client.post("/api/v2/jobs", json=_payload())

    assert response.status_code == 200
    job_id = cast(str, response.json()["job_id"])
    job = await ContractDatabase.fetch_job(job_id)
    assert job is not None

    metadata = cast(dict[str, object], job["job_metadata"])
    assert metadata["llm_config_present"] is True
    credential_id = cast(str, metadata["llm_credential_id"])
    assert credential_id.startswith("jllm_")
    assert "llm_config" not in metadata
    assert "sk-contract-raw-secret" not in json.dumps(metadata)

    credential = await ContractDatabase.fetch_one(
        """
        SELECT job_id, user_id, status, config_encrypted
        FROM job_llm_credentials
        WHERE id = :credential_id
        """,
        {"credential_id": credential_id},
    )
    assert credential is not None
    assert credential["job_id"] == job_id
    assert credential["status"] == "active"
    assert "sk-contract-raw-secret" not in str(credential["config_encrypted"])


@pytest.mark.asyncio
async def test_byok_job_is_default_denied_without_external_call_opt_in(
    developer_api_client_factory: Callable[
        [], AbstractAsyncContextManager[AsyncClient]
    ],
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_ALLOWED_PROVIDER_ENDPOINTS", "https://example.com/v1")

    async with developer_api_client_factory() as api_client:
        response = await api_client.post("/api/v2/jobs", json=_payload())

    assert response.status_code in {400, 422}
    body = response.json()
    assert "not authorized" in json.dumps(body).lower()
