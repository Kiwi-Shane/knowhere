from __future__ import annotations

import ast
from pathlib import Path


def test_qstash_publish_requires_webhook_job_authorization_before_publish() -> None:
    source_path = Path(
        "packages/shared-python/shared/services/webhook/qstash_publisher.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and node.name == "QStashWebhookPublisher"
    )
    function_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "publish_event"
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
            and keyword.value.value == "webhook"
            for keyword in node.keywords
        )
    ]
    publish_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "publish_webhook"
    ]
    assert authorization_calls
    assert publish_calls
    assert "Job.job_metadata" in source
    assert min(node.lineno for node in authorization_calls) < min(
        node.lineno for node in publish_calls
    )
