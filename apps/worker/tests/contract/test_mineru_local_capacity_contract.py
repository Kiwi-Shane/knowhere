from __future__ import annotations

import threading
from contextlib import contextmanager
import os
from pathlib import Path
from typing import Iterator

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from app.services.document_parser.providers.mineru import local_pdf_service
from app.services.document_parser.providers.mineru.artifact_contract import (
    MinerUArtifactBundle,
    MinerUArtifactContractError,
    MinerUArtifactManifest,
)
from app.services.document_parser.providers.mineru.local_capacity import (
    LocalMinerUCapacityError,
    LocalMinerUCapacityGuard,
    get_local_capacity_guard,
)
from app.services.document_parser.providers.mineru.local_process import (
    LocalMinerUError,
)


def _configure_local_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source = tmp_path / "private-customer-source.pdf"
    source.write_bytes(b"%PDF")
    project = tmp_path / "MinerU"
    project.mkdir()
    uv = tmp_path / "uv.exe"
    uv.write_bytes(b"uv")
    monkeypatch.setattr(
        local_pdf_service.settings,
        "MINERU_LOCAL_PROJECT_PATH",
        str(project),
    )
    monkeypatch.setattr(
        local_pdf_service.settings,
        "MINERU_LOCAL_UV_EXECUTABLE",
        str(uv),
    )
    monkeypatch.setattr(
        local_pdf_service.settings,
        "MINERU_LOCAL_MAX_CONCURRENT_JOBS",
        1,
    )
    monkeypatch.setattr(
        local_pdf_service.settings,
        "MINERU_LOCAL_ADMISSION_TIMEOUT_SECONDS",
        1,
    )
    return source


def _bundle(output_root: Path) -> MinerUArtifactBundle:
    output_root.mkdir(parents=True, exist_ok=True)
    markdown = output_root / "document.md"
    markdown.write_text("# result\n", encoding="utf-8")
    middle = output_root / "middle.json"
    middle.write_text("{}", encoding="utf-8")
    content = output_root / "content.json"
    content.write_text("[]", encoding="utf-8")
    content_v2 = output_root / "content-v2.json"
    content_v2.write_text("[]", encoding="utf-8")
    images = output_root / "images"
    images.mkdir()
    manifest_path = output_root / "mineru_manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    log_path = output_root.parent / "logs" / "mineru.log"
    log_path.parent.mkdir()
    log_path.write_text("safe", encoding="utf-8")
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
        output_root=output_root,
        markdown_path=markdown,
        middle_json_path=middle,
        content_list_path=content,
        content_list_v2_path=content_v2,
        images_dir=images,
        manifest=manifest,
    )


def test_one_lease_blocks_a_second_lease_when_limit_is_one() -> None:
    guard = LocalMinerUCapacityGuard(limit=1, timeout_seconds=1)
    contender_started = threading.Event()
    contender_acquired = threading.Event()

    def contend() -> None:
        contender_started.set()
        with guard.acquire():
            contender_acquired.set()

    with guard.acquire():
        thread = threading.Thread(target=contend)
        thread.start()
        assert contender_started.wait(timeout=0.5)
        assert not contender_acquired.wait(timeout=0.05)

    assert contender_acquired.wait(timeout=0.5)
    thread.join(timeout=0.5)
    assert not thread.is_alive()


def test_capacity_timeout_is_content_free_and_does_not_release_without_a_lease() -> None:
    source_metadata = "private-customer-source.pdf"

    class UnavailableSemaphore:
        def __init__(self) -> None:
            self.release_calls = 0

        def acquire(self, *, timeout: float) -> bool:
            assert timeout == 0.25
            return False

        def release(self) -> None:
            self.release_calls += 1

    semaphore = UnavailableSemaphore()
    guard = LocalMinerUCapacityGuard(limit=1, timeout_seconds=0.25)
    guard._semaphore = semaphore

    with pytest.raises(LocalMinerUCapacityError) as captured:
        with guard.acquire():
            pytest.fail("an unavailable lease must not enter the protected block")

    assert source_metadata not in str(captured.value)
    assert str(captured.value) == "Local MinerU capacity is unavailable"
    assert semaphore.release_calls == 0


def test_guard_is_reused_for_the_same_process_configuration() -> None:
    first = get_local_capacity_guard(2, 3)
    repeated = get_local_capacity_guard(2, 3.0)
    different = get_local_capacity_guard(1, 3)

    assert repeated is first
    assert different is not first


def test_capacity_timeout_happens_before_runner_or_temporary_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _configure_local_runtime(tmp_path, monkeypatch)
    runner_calls: list[str] = []

    class UnavailableGuard:
        @contextmanager
        def acquire(self) -> Iterator[None]:
            raise LocalMinerUCapacityError("Local MinerU capacity is unavailable")
            yield

    class UnexpectedRunner:
        def __init__(self, **_kwargs: object) -> None:
            runner_calls.append("constructed")

    monkeypatch.setattr(
        local_pdf_service,
        "get_local_capacity_guard",
        lambda *_args, **_kwargs: UnavailableGuard(),
        raising=False,
    )
    monkeypatch.setattr(local_pdf_service, "LocalMinerURunner", UnexpectedRunner)
    output = tmp_path / "output"

    with pytest.raises(LocalMinerUCapacityError):
        local_pdf_service.parse_via_local(
            str(source),
            source.name,
            str(output),
        )

    assert runner_calls == []
    assert not output.exists()


@pytest.mark.parametrize(
    "outcome",
    ["success", "process_error", "artifact_error", "publication_error"],
)
def test_capacity_lease_releases_after_every_local_transaction_outcome(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
) -> None:
    source = _configure_local_runtime(tmp_path, monkeypatch)
    guard = LocalMinerUCapacityGuard(limit=1, timeout_seconds=0.05)

    class FakeRunner:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def run(self, request: object) -> MinerUArtifactBundle:
            if outcome == "process_error":
                raise LocalMinerUError(
                    "child failed",
                    return_code=2,
                    timed_out=False,
                    stderr_tail="",
                    log_path=request.output_root.parent / "logs" / "mineru.log",
                )
            if outcome == "artifact_error":
                raise MinerUArtifactContractError("invalid artifact")
            return _bundle(request.output_root)

    monkeypatch.setattr(local_pdf_service, "LocalMinerURunner", FakeRunner)
    monkeypatch.setattr(
        local_pdf_service,
        "get_local_capacity_guard",
        lambda *_args, **_kwargs: guard,
        raising=False,
    )
    if outcome == "publication_error":
        monkeypatch.setattr(
            local_pdf_service,
            "_publish",
            lambda *_args: (_ for _ in ()).throw(OSError("publish failed")),
        )

    expected_error = {
        "success": None,
        "process_error": LocalMinerUError,
        "artifact_error": MinerUArtifactContractError,
        "publication_error": OSError,
    }[outcome]
    if expected_error is None:
        local_pdf_service.parse_via_local(
            str(source), source.name, str(tmp_path / "output")
        )
    else:
        with pytest.raises(expected_error):
            local_pdf_service.parse_via_local(
                str(source), source.name, str(tmp_path / "output")
            )

    with guard.acquire():
        pass


@pytest.mark.parametrize(
    ("limit", "timeout_seconds"),
    [(0, 1), (-1, 1), (1, 0), (1, -0.5)],
)
def test_capacity_guard_rejects_nonpositive_values(
    limit: int,
    timeout_seconds: float,
) -> None:
    with pytest.raises(ValueError, match="positive"):
        LocalMinerUCapacityGuard(limit, timeout_seconds)
