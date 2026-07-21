from __future__ import annotations

import ast
import asyncio
import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from shared.core.config.ai import AIConfig
from shared.core.exceptions.domain_exceptions import SystemSettingMissingException


def test_llm_external_calls_are_default_deny() -> None:
    config = AIConfig()

    assert config.LLM_EXTERNAL_CALLS_ENABLED is False
    with pytest.raises(SystemSettingMissingException):
        config.require_llm_external_calls_enabled()


def test_llm_external_calls_can_be_explicitly_enabled() -> None:
    config = AIConfig(LLM_EXTERNAL_CALLS_ENABLED=True)

    config.require_llm_external_calls_enabled()


def test_retrieval_llm_has_a_separate_default_deny_gate() -> None:
    config = AIConfig(LLM_EXTERNAL_CALLS_ENABLED=True)

    assert config.RETRIEVAL_LLM_EXTERNAL_CALLS_ENABLED is False
    with pytest.raises(SystemSettingMissingException):
        config.require_retrieval_llm_external_calls_enabled()

    enabled_config = AIConfig(
        LLM_EXTERNAL_CALLS_ENABLED=True,
        RETRIEVAL_LLM_EXTERNAL_CALLS_ENABLED=True,
    )
    enabled_config.require_retrieval_llm_external_calls_enabled()


def test_retrieval_llm_factories_do_not_construct_a_provider_without_retrieval_opt_in(
    monkeypatch,
) -> None:
    from shared.services.retrieval import llm_adapter

    monkeypatch.setattr(llm_adapter.settings, "LLM_MOCK_ENABLED", False)
    monkeypatch.setattr(llm_adapter.settings, "LLM_EXTERNAL_CALLS_ENABLED", True)
    monkeypatch.setattr(
        llm_adapter.settings,
        "RETRIEVAL_LLM_EXTERNAL_CALLS_ENABLED",
        False,
    )
    monkeypatch.setattr(llm_adapter, "_has_llm_credentials", lambda: True)

    def fail_if_provider_is_constructed(*_args, **_kwargs):
        raise AssertionError("retrieval provider must remain unconstructed")

    from shared.services.ai import openai_compatible_client_sync as client_module

    monkeypatch.setattr(
        client_module,
        "get_openai_client",
        fail_if_provider_is_constructed,
    )

    assert llm_adapter.create_retrieval_llm_fn() is None
    assert llm_adapter.create_retrieval_planner_fn() is None
    assert llm_adapter.create_retrieval_vlm_fn() is None


def test_retrieval_llm_factory_uses_fake_provider_only_after_both_opt_ins(
    monkeypatch,
) -> None:
    from shared.services.ai import openai_compatible_client_sync as client_module
    from shared.services.retrieval import llm_adapter

    class FakeClient:
        def chat_completion_with_usage(self, *_args, **_kwargs):
            return "fixture response", {"total_tokens": 0}

    monkeypatch.setattr(llm_adapter.settings, "LLM_MOCK_ENABLED", False)
    monkeypatch.setattr(llm_adapter.settings, "LLM_EXTERNAL_CALLS_ENABLED", True)
    monkeypatch.setattr(
        llm_adapter.settings,
        "RETRIEVAL_LLM_EXTERNAL_CALLS_ENABLED",
        True,
    )
    monkeypatch.setattr(llm_adapter, "_has_llm_credentials", lambda: True)
    monkeypatch.setattr(client_module, "get_openai_client", lambda **_kwargs: FakeClient())

    llm_fn = llm_adapter.create_retrieval_llm_fn()
    assert llm_fn is not None
    assert asyncio.run(llm_fn("fixture query")) == "fixture response"


def test_all_retrieval_factories_apply_the_retrieval_gate() -> None:
    source_path = Path("packages/shared-python/shared/services/retrieval/llm_adapter.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    factory_names = {
        "create_retrieval_llm_fn",
        "create_retrieval_planner_fn",
        "create_retrieval_vlm_fn",
    }
    factory_nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name in factory_names
    ]

    assert {node.name for node in factory_nodes} == factory_names
    for node in factory_nodes:
        gate_calls = [
            call
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "_retrieval_llm_external_calls_authorized"
        ]
        assert gate_calls, f"{node.name} must apply the retrieval LLM gate"


def test_openai_client_checks_opt_in_before_sdk_construction() -> None:
    source_path = Path(
        "packages/shared-python/shared/services/ai/openai_compatible_client_sync.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and node.name == "OpenAICompatibleClientSync"
    )
    init_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    authorization_calls = [
        node
        for node in ast.walk(init_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_llm_external_calls_enabled"
    ]
    sdk_calls = [
        node
        for node in ast.walk(init_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_build_client"
    ]
    assert authorization_calls
    assert sdk_calls
    assert min(node.lineno for node in authorization_calls) < min(
        node.lineno for node in sdk_calls
    )


def test_openai_client_default_deny_is_runtime_enforced(monkeypatch) -> None:
    from shared.services.ai import openai_compatible_client_sync as client_module

    monkeypatch.setattr(client_module.settings, "LLM_EXTERNAL_CALLS_ENABLED", False)
    with pytest.raises(SystemSettingMissingException):
        client_module.OpenAICompatibleClientSync(
            api_key="test-key",
            api_url="https://provider.example/v1",
            default_model="test-model",
        )


def test_worker_parse_requires_llm_job_authorization_when_enabled() -> None:
    source_path = Path(
        "apps/worker/app/services/document_ingestion/parse_execution.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "execute_document_parse"
    )
    authorization_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_external_call_authorization"
        and any(
            keyword.arg == "provider"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "llm"
            for keyword in node.keywords
        )
    ]
    parser_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "checkerboard_parse_output"
    ]
    assert authorization_calls
    assert parser_calls
    assert "LLM_EXTERNAL_CALLS_ENABLED" in source
    assert min(node.lineno for node in authorization_calls) < min(
        node.lineno for node in parser_calls
    )
