from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pytest
from loguru import logger

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from app.services.document_parser.providers.mineru.artifact_contract import (
    MinerUArtifactBundle,
    MinerUArtifactContractError,
    MinerUArtifactManifest,
)
from app.services.document_parser.providers.mineru.local_capacity import (
    LocalMinerUCapacityError,
)
from app.services.document_parser.providers.mineru.local_process import LocalMinerUError
from shared.core.exceptions.domain_exceptions import MinerUServiceException
from shared.core.config.mineru import MineruConfig

from app.services.document_parser.providers.mineru import local_pdf_service, provider


@contextmanager
def _capture_provider_logs() -> Iterator[list[Any]]:
    messages: list[Any] = []
    sink_id = logger.add(messages.append, level="INFO")
    try:
        yield messages
    finally:
        logger.remove(sink_id)


def _provider_records(messages: list[Any]) -> list[dict[str, Any]]:
    return [
        message.record
        for message in messages
        if message.record["extra"].get("event") == "mineru.provider"
    ]


def _bundle(request: object) -> MinerUArtifactBundle:
    root = request.output_root
    root.mkdir(parents=True, exist_ok=True)
    markdown = root / "document.md"
    markdown.write_text("# Local result\n", encoding="utf-8")
    middle = root / "middle.json"
    middle.write_text("{}", encoding="utf-8")
    content = root / "content.json"
    content.write_text("[]", encoding="utf-8")
    content_v2 = root / "content-v2.json"
    content_v2.write_text("[]", encoding="utf-8")
    images = root / "images"
    images.mkdir()
    (images / "figure.png").write_bytes(b"png")
    manifest_path = root / "mineru_manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    log_path = root.parent / "logs" / "mineru.log"
    log_path.parent.mkdir()
    log_path.write_text("safe local log", encoding="utf-8")
    manifest = MinerUArtifactManifest(
        schema_version="knowhere-mineru-artifacts/1.0",
        status="completed",
        source={},
        parser={},
        execution={},
        document={},
        artifacts={},
        warnings=(),
        raw={},
    )
    return MinerUArtifactBundle(
        manifest_path=manifest_path,
        output_root=root,
        markdown_path=markdown,
        middle_json_path=middle,
        content_list_path=content,
        content_list_v2_path=content_v2,
        images_dir=images,
        manifest=manifest,
    )


def test_cloud_provider_is_default_and_delegates_all_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", "cloud")
    monkeypatch.setattr(
        provider,
        "parse_via_full",
        lambda *args, **kwargs: calls.append((*args, kwargs)),
    )
    monkeypatch.setattr(
        provider,
        "parse_via_local",
        lambda *args, **kwargs: pytest.fail("local provider must not be called"),
    )

    provider.parse_pdf("source.pdf", "document.pdf", str(tmp_path), s3_key="in/key")

    assert calls == [
        ("source.pdf", "document.pdf", str(tmp_path), {"s3_key": "in/key"})
    ]
    assert MineruConfig().MINERU_PROVIDER == "cloud"


def test_local_provider_materializes_artifacts_without_cloud_or_raw_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF")
    project = tmp_path / "MinerU"
    project.mkdir()
    uv = tmp_path / "uv.exe"
    uv.write_bytes(b"uv")
    output = tmp_path / "output"

    class FakeRunner:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def run(self, request: object) -> MinerUArtifactBundle:
            return _bundle(request)

    monkeypatch.setattr(local_pdf_service, "LocalMinerURunner", FakeRunner)
    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", "local")
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_PROJECT_PATH", str(project))
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_UV_EXECUTABLE", str(uv))
    monkeypatch.setattr(
        provider,
        "parse_via_full",
        lambda *args, **kwargs: pytest.fail("cloud provider must not be called"),
    )

    provider.parse_pdf(str(source), source.name, str(output), s3_key="ignored/key")

    assert (output / "full.md").read_text(encoding="utf-8") == "# Local result\n"
    assert (output / "images" / "figure.png").read_bytes() == b"png"
    assert (output / "logs" / "mineru.log").read_text(encoding="utf-8") == (
        "safe local log"
    )
    assert not any(path.name.startswith(".mineru-local-") for path in output.iterdir())
    assert MineruConfig().MINERU_LOCAL_SHARD_CONCURRENCY == 1


@pytest.mark.parametrize(
    ("source", "project", "uv", "message"),
    [
        ("https://example.test/document.pdf", "configured", "configured", "local file"),
        ("source.pdf", "", "configured", "project"),
        ("source.pdf", "configured", "", "uv"),
    ],
)
def test_local_provider_rejects_remote_or_missing_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    project: str,
    uv: str,
    message: str,
) -> None:
    local_source = tmp_path / "source.pdf"
    local_source.write_bytes(b"%PDF")
    project_path = tmp_path / "MinerU"
    project_path.mkdir()
    uv_path = tmp_path / "uv.exe"
    uv_path.write_bytes(b"uv")
    source_value = source if source.startswith("https") else str(local_source)
    project_value = str(project_path) if project else ""
    uv_value = str(uv_path) if uv else ""
    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", "local")
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_PROJECT_PATH", project_value)
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_UV_EXECUTABLE", uv_value)

    with pytest.raises(MinerUServiceException) as captured:
        provider.parse_pdf(source_value, "document.pdf", str(tmp_path / "output"))

    assert captured.value.internal_message.endswith("configuration")
    assert isinstance(captured.value.original_exception, ValueError)
    assert message in str(captured.value.original_exception)


def test_local_provider_failure_removes_partial_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF")
    project = tmp_path / "MinerU"
    project.mkdir()
    uv = tmp_path / "uv.exe"
    uv.write_bytes(b"uv")
    output = tmp_path / "output"

    class FailingRunner:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def run(self, request: object) -> None:
            request.output_root.mkdir(parents=True)
            (request.output_root / "partial.md").write_text("partial", encoding="utf-8")
            raise LocalMinerUError(
                "local failed",
                return_code=2,
                timed_out=False,
                stderr_tail="",
                log_path=request.output_root.parent / "logs" / "mineru.log",
            )

    monkeypatch.setattr(local_pdf_service, "LocalMinerURunner", FailingRunner)
    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", "local")
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_PROJECT_PATH", str(project))
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_UV_EXECUTABLE", str(uv))

    with pytest.raises(MinerUServiceException) as captured:
        provider.parse_pdf(str(source), source.name, str(output))

    assert captured.value.internal_message.endswith("process_exit")
    assert isinstance(captured.value.original_exception, LocalMinerUError)
    assert not (output / "full.md").exists()
    assert not (output / "images").exists()
    assert not any(path.name.startswith(".mineru-local-") for path in output.iterdir())


@pytest.mark.parametrize(
    ("provider_name", "expected_backend"),
    [("cloud", "cloud"), ("local", "pipeline")],
)
def test_provider_success_emits_one_allowlisted_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider_name: str,
    expected_backend: str,
) -> None:
    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", provider_name)
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_BACKEND", "pipeline")
    monkeypatch.setattr(provider, "parse_via_full", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(provider, "parse_via_local", lambda *_args, **_kwargs: None)
    ticks = iter((10.0, 10.1234))
    monkeypatch.setattr(
        provider.time,
        "perf_counter",
        lambda: next(ticks),
        raising=False,
    )

    with _capture_provider_logs() as messages:
        provider.parse_pdf(
            "private-source.pdf",
            "private-filename.pdf",
            str(tmp_path / "private-output"),
            s3_key="private/s3/key",
        )

    records = _provider_records(messages)
    assert len(records) == 1
    assert records[0]["extra"] == {
        "event": "mineru.provider",
        "provider": provider_name,
        "backend": expected_backend,
        "status": "ok",
        "elapsed_ms": 123,
    }


def _local_failure(kind: str, tmp_path: Path) -> Exception:
    secret = "customer-secret.pdf API_KEY=top-secret child-stderr-secret"
    if kind == "capacity":
        return LocalMinerUCapacityError(secret)
    if kind == "configuration":
        return ValueError(secret)
    if kind == "process_timeout":
        return LocalMinerUError(
            secret,
            return_code=None,
            timed_out=True,
            stderr_tail=secret,
            log_path=tmp_path / secret,
        )
    if kind == "process_exit":
        return LocalMinerUError(
            secret,
            return_code=7,
            timed_out=False,
            stderr_tail=secret,
            log_path=tmp_path / secret,
        )
    if kind == "artifact_contract":
        return MinerUArtifactContractError(secret)
    if kind == "publication":
        return OSError(secret)
    return RuntimeError(secret)


@pytest.mark.parametrize(
    "expected_category",
    [
        "capacity",
        "configuration",
        "process_timeout",
        "process_exit",
        "artifact_contract",
        "publication",
        "unknown",
    ],
)
def test_local_provider_failure_is_safe_and_never_falls_back_to_cloud(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    expected_category: str,
) -> None:
    error = _local_failure(expected_category, tmp_path)
    cloud_calls: list[str] = []
    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", "local")
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_BACKEND", "pipeline")
    monkeypatch.setattr(
        provider,
        "parse_via_full",
        lambda *_args, **_kwargs: cloud_calls.append("cloud"),
    )
    monkeypatch.setattr(
        provider,
        "parse_via_local",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
    )
    ticks = iter((20.0, 20.042))
    monkeypatch.setattr(
        provider.time,
        "perf_counter",
        lambda: next(ticks),
        raising=False,
    )

    with _capture_provider_logs() as messages:
        with pytest.raises(MinerUServiceException) as captured:
            provider.parse_pdf(
                "customer-secret.pdf",
                "private-filename.pdf",
                str(tmp_path / "private-output"),
                s3_key="private/s3/key",
            )

    records = _provider_records(messages)
    assert len(records) == 1
    assert records[0]["extra"] == {
        "event": "mineru.provider",
        "provider": "local",
        "backend": "pipeline",
        "status": "error",
        "elapsed_ms": 42,
        "error_category": expected_category,
    }
    rendered_log = "\n".join(str(message) for message in messages)
    bound_fields = repr(records[0]["extra"])
    for sensitive in (
        "customer-secret.pdf",
        "private-filename.pdf",
        "private/s3/key",
        "top-secret",
        "child-stderr-secret",
    ):
        assert sensitive not in rendered_log
        assert sensitive not in bound_fields
        assert sensitive not in captured.value.internal_message
        assert sensitive not in captured.value.user_message
        assert sensitive not in repr(captured.value.details)
    assert captured.value.details == {"service": "document_processing"}
    assert cloud_calls == []


def test_cloud_provider_failure_keeps_original_exception_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cloud_error = RuntimeError("cloud failure")
    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", "cloud")
    monkeypatch.setattr(
        provider,
        "parse_via_full",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(cloud_error),
    )

    with _capture_provider_logs() as messages:
        with pytest.raises(RuntimeError) as captured:
            provider.parse_pdf("source.pdf", "source.pdf", "output")

    assert captured.value is cloud_error
    records = _provider_records(messages)
    assert len(records) == 1
    assert records[0]["extra"]["provider"] == "cloud"
    assert records[0]["extra"]["status"] == "error"
