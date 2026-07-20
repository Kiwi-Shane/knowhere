from __future__ import annotations

import ast
from pathlib import Path


def test_document_parse_requires_job_authorization_before_parser_dispatch() -> None:
    source_path = Path(
        "apps/worker/app/services/document_ingestion/parse_execution.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
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
    ]
    assert authorization_calls

    parser_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "checkerboard_parse_output"
    ]
    assert parser_calls
    assert min(node.lineno for node in authorization_calls) < min(
        node.lineno for node in parser_calls
    )
