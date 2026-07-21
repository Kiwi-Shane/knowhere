from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.schemas.llm_config import LLMConfig, LLMProviderConfig
from shared.services.ai.llm_overrides import (
    reset_llm_overrides_async,
    set_llm_overrides_async,
)
from shared.services.ai.llm_endpoint_policy import LLMEndpointPolicyError
from shared.services.retrieval import cache_service
from shared.services.retrieval.execution.query_request import RetrievalQuery
from shared.services.retrieval.workflow.plan_service import (
    _build_workflow_cache_identity,
)


def _query(*, llm_config: LLMConfig) -> RetrievalQuery:
    return RetrievalQuery.from_parameters(
        db=cast(AsyncSession, object()),
        user_id="user-1",
        namespace="case-1",
        query="find the verified result",
        top_k=5,
        exclude_document_ids=[],
        exclude_sections=[],
        llm_config=llm_config,
    )


def test_build_cache_extra_propagates_canonical_provider_endpoints() -> None:
    extra = _query(
        llm_config=LLMConfig(
            text=LLMProviderConfig(
                api_key="sk-text-cache-secret",
                model="text-model",
                base_url="https://provider.example.test/v1/",
            ),
            vision=LLMProviderConfig(
                api_key="sk-vision-cache-secret",
                model="vision-model",
                base_url="https://vision.example.test/v1",
            ),
        )
    ).build_cache_extra()

    assert extra["llm_text_endpoint"] == "https://provider.example.test/v1"
    assert extra["llm_vision_endpoint"] == "https://vision.example.test/v1"
    assert "api_key" not in extra
    assert "sk-text-cache-secret" not in repr(extra)
    assert "sk-vision-cache-secret" not in repr(extra)


def test_build_cache_extra_rejects_local_provider_endpoint() -> None:
    query = _query(
        llm_config=LLMConfig(
            text=LLMProviderConfig(
                api_key="sk-local-cache-secret",
                model="text-model",
                base_url="http://localhost/v1",
            )
        )
    )

    with pytest.raises(LLMEndpointPolicyError):
        query.build_cache_extra()


def test_workflow_cache_identity_uses_active_provider_without_credentials() -> None:
    token = set_llm_overrides_async(
        LLMConfig(
            text=LLMProviderConfig(
                api_key="sk-workflow-text-secret",
                model="workflow-text-model",
                base_url="https://workflow.example.test/v1/",
            ),
            vision=LLMProviderConfig(
                api_key="sk-workflow-vision-secret",
                model="workflow-vision-model",
                base_url="https://workflow-vision.example.test/v1",
            ),
        )
    )
    try:
        identity = _build_workflow_cache_identity()
    finally:
        reset_llm_overrides_async(token)

    assert identity == {
        "llm_text_model": "workflow-text-model",
        "llm_vision_model": "workflow-vision-model",
        "llm_text_endpoint": "https://workflow.example.test/v1",
        "llm_vision_endpoint": "https://workflow-vision.example.test/v1",
    }
    assert "api_key" not in repr(identity)
    assert "sk-workflow-text-secret" not in repr(identity)
    assert "sk-workflow-vision-secret" not in repr(identity)


@pytest.mark.asyncio
async def test_workflow_plan_key_changes_when_text_endpoint_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _version(*, user_id: str, namespace: str) -> int:
        return 0

    monkeypatch.setattr(
        cache_service,
        "get_retrieval_namespace_cache_version",
        _version,
    )
    common = {
        "user_id": "user-1",
        "namespace": "case-1",
        "query": "find the verified result",
        "top_k": 5,
        "llm_text_model": "workflow-text-model",
    }

    first = await cache_service._workflow_plan_cache_key(
        **common,
        llm_text_endpoint="https://one.example.test/v1",
    )
    second = await cache_service._workflow_plan_cache_key(
        **common,
        llm_text_endpoint="https://two.example.test/v1",
    )

    assert first != second
