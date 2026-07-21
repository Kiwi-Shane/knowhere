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


def test_document_parse_requires_iloveapi_authorization_when_enabled() -> None:
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

    iloveapi_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_external_call_authorization"
        and any(
            keyword.arg == "provider"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "iloveapi"
            for keyword in node.keywords
        )
    ]
    assert iloveapi_calls
    assert "ILOVEAPI_EXTERNAL_CALLS_ENABLED" in source


def test_page_memory_pptx_requires_iloveapi_authorization_before_conversion() -> None:
    source_path = Path(
        "apps/worker/app/services/page_memory/normalizer.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_normalize_pptx_to_pdf"
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
            and keyword.value.value == "iloveapi"
            for keyword in node.keywords
        )
    ]
    conversion_calls = [
        node
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_pptx_bytes_to_pdf_bytes"
    ]
    assert authorization_calls
    assert conversion_calls
    assert min(node.lineno for node in authorization_calls) < min(
        node.lineno for node in conversion_calls
    )
