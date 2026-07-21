from __future__ import annotations

from shared.services.retrieval.cache_service import _query_cache_key


def _key(
    *,
    llm_text_model: str | None = None,
    llm_vision_model: str | None = None,
    llm_text_endpoint: str | None = None,
    llm_vision_endpoint: str | None = None,
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
        llm_text_endpoint=llm_text_endpoint,
        llm_vision_endpoint=llm_vision_endpoint,
    )


def test_cache_key_accepts_byok_model_identity_fields() -> None:
    key = _key(llm_text_model="text-model", llm_vision_model="vision-model")

    assert key.startswith("retrieval:query:user-1:case-1:v0:")


def test_cache_key_changes_when_text_model_changes() -> None:
    assert _key(llm_text_model="text-model-a") != _key(llm_text_model="text-model-b")


def test_cache_key_changes_when_vision_model_changes() -> None:
    assert _key(llm_vision_model="vision-model-a") != _key(
        llm_vision_model="vision-model-b"
    )


def test_cache_key_changes_when_text_endpoint_changes() -> None:
    assert _key(llm_text_endpoint="https://one.example.test/v1") != _key(
        llm_text_endpoint="https://two.example.test/v1"
    )


def test_cache_key_changes_when_vision_endpoint_changes() -> None:
    assert _key(llm_vision_endpoint="https://one.example.test/v1") != _key(
        llm_vision_endpoint="https://two.example.test/v1"
    )


def test_cache_key_normalizes_endpoint_trailing_slash() -> None:
    assert _key(llm_text_endpoint="https://provider.example.test/v1/") == _key(
        llm_text_endpoint="https://provider.example.test/v1"
    )


def test_cache_key_keeps_text_and_vision_endpoint_channels_distinct() -> None:
    assert _key(
        llm_text_endpoint="https://text.example.test/v1",
        llm_vision_endpoint="https://vision.example.test/v1",
    ) != _key(
        llm_text_endpoint="https://vision.example.test/v1",
        llm_vision_endpoint="https://text.example.test/v1",
    )


def test_absent_endpoint_values_are_deterministic() -> None:
    assert _key(llm_text_endpoint=None) == _key(llm_text_endpoint="")
    assert _key(llm_vision_endpoint=None) == _key(llm_vision_endpoint="")


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
        llm_text_endpoint="https://provider.invalid/v1",
    )

    assert "sk-test-secret" not in key
    assert "https://provider.invalid/v1" not in key
