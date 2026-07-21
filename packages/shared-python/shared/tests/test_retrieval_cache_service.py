from __future__ import annotations

from shared.services.retrieval.cache_service import _query_cache_key


def _key(
    *,
    llm_text_model: str | None = None,
    llm_vision_model: str | None = None,
) -> str:
    return _query_cache_key(
        user_id="user-1",
        namespace="case-1",
        version=0,
        query="find the verified result",
        top_k=5,
        exclude_document_ids=[],
        exclude_sections=[],
        chunk_types=["text"],
        signal_paths=["content"],
        filter_mode="delete",
        channels=["content"],
        channel_weights={"content": 2.0},
        rerank=False,
        threshold=0.0,
        internal_recall_k=20,
        use_agentic=False,
        decomposition_enabled=True,
        llm_text_model=llm_text_model,
        llm_vision_model=llm_vision_model,
    )


def test_cache_key_accepts_byok_model_identity_fields() -> None:
    key = _key(llm_text_model="text-model", llm_vision_model="vision-model")

    assert key.startswith("retrieval:query:user-1:case-1:v0:")


def test_cache_key_changes_when_text_model_changes() -> None:
    assert _key(llm_text_model="text-model-a") != _key(
        llm_text_model="text-model-b"
    )


def test_cache_key_changes_when_vision_model_changes() -> None:
    assert _key(llm_vision_model="vision-model-a") != _key(
        llm_vision_model="vision-model-b"
    )


def test_cache_key_is_deterministic_and_normalizes_absent_model_values() -> None:
    assert _key(llm_text_model="text-model", llm_vision_model="vision-model") == _key(
        llm_text_model="text-model", llm_vision_model="vision-model"
    )
    assert _key(llm_text_model=None) == _key(llm_text_model="")
    assert _key(llm_vision_model="  vision-model  ") == _key(
        llm_vision_model="vision-model"
    )


def test_cache_key_does_not_expose_representative_secret_or_endpoint_text() -> None:
    key = _key(
        llm_text_model="text-model",
        llm_vision_model="vision-model",
    )

    assert "sk-test-secret" not in key
    assert "https://provider.invalid/v1" not in key
