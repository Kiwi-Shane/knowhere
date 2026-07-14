from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from app.services.document_parser.providers.mineru.runtime_preflight import (
    LocalMinerURuntimeStatus,
    LocalMinerURuntimeError,
    _probe_writable,
    check_local_mineru_runtime,
    require_local_mineru_runtime,
)
from scripts import check_local_mineru_runtime as preflight_cli


GIB = 1024**3


def _local_config(tmp_path: Path, **overrides: object) -> SimpleNamespace:
    project = tmp_path / "private MinerU project"
    project.mkdir()
    uv = tmp_path / "private tools" / "uv.exe"
    uv.parent.mkdir()
    uv.write_bytes(b"uv")
    python = project / ".venv" / ("Scripts" if os.name == "nt" else "bin") / (
        "python.exe" if os.name == "nt" else "python"
    )
    python.parent.mkdir(parents=True)
    python.write_bytes(b"python")
    temp_root = tmp_path / "private temp"
    temp_root.mkdir()
    values: dict[str, object] = {
        "MINERU_PROVIDER": "local",
        "MINERU_LOCAL_PROJECT_PATH": str(project),
        "MINERU_LOCAL_UV_EXECUTABLE": str(uv),
        "MINERU_LOCAL_PYTHON_EXECUTABLE": "",
        "MINERU_LOCAL_MIN_FREE_DISK_GB": 10,
        "MINERU_LOCAL_MIN_AVAILABLE_MEMORY_GB": 8,
        "TMP_PATH": str(temp_root),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _Commands:
    def __init__(self, *, adapter_return_code: int = 0) -> None:
        self.adapter_return_code = adapter_return_code
        self.calls: list[tuple[list[str], dict[str, Any]]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append((argv, kwargs))
        return_code = self.adapter_return_code if "-I" in argv else 0
        return subprocess.CompletedProcess(
            argv,
            return_code,
            stdout="private subprocess output api_key=never-report-this",
            stderr="C:\\private\\model-path",
        )


def test_cloud_runtime_bypasses_every_local_probe() -> None:
    def fail_probe(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("cloud mode must not inspect the local runtime")

    status = check_local_mineru_runtime(
        SimpleNamespace(MINERU_PROVIDER="cloud"),
        run_command=fail_probe,
        disk_usage=fail_probe,
        virtual_memory=fail_probe,
        write_probe=fail_probe,
    )

    assert status.to_dict() == {
        "schema_version": "local-mineru-runtime/1.0",
        "provider": "cloud",
        "ready": True,
        "checks": {},
        "free_disk_bytes": 0,
        "available_memory_bytes": 0,
        "error_codes": [],
    }


def test_ready_local_runtime_is_content_free_and_uses_offline_argv(
    tmp_path: Path,
) -> None:
    config = _local_config(tmp_path)
    commands = _Commands()

    status = check_local_mineru_runtime(
        config,
        run_command=commands,
        disk_usage=lambda _path: SimpleNamespace(free=20 * GIB),
        virtual_memory=lambda: SimpleNamespace(available=16 * GIB),
        write_probe=lambda _path: True,
    )

    assert status.to_dict() == {
        "schema_version": "local-mineru-runtime/1.0",
        "provider": "local",
        "ready": True,
        "checks": {
            "project": True,
            "uv": True,
            "python": True,
            "adapter": True,
            "temp_writable": True,
            "disk": True,
            "memory": True,
        },
        "free_disk_bytes": 20 * GIB,
        "available_memory_bytes": 16 * GIB,
        "error_codes": [],
    }
    project = Path(config.MINERU_LOCAL_PROJECT_PATH)
    expected_python = project / ".venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    assert commands.calls[0][0] == [config.MINERU_LOCAL_UV_EXECUTABLE, "--version"]
    assert commands.calls[1][0] == [
        str(expected_python.resolve()),
        "-I",
        "-c",
        "import mineru.integrations.knowhere.cli",
    ]
    assert all(call[1]["shell"] is False for call in commands.calls)
    assert all(call[1]["timeout"] == 10 for call in commands.calls)
    assert all(call[1]["env"]["HF_HUB_OFFLINE"] == "1" for call in commands.calls)
    serialized = json.dumps(status.to_dict())
    assert str(tmp_path) not in serialized
    assert "never-report-this" not in serialized
    assert "model-path" not in serialized


def test_local_runtime_reports_stable_codes_for_all_capacity_failures(
    tmp_path: Path,
) -> None:
    config = _local_config(
        tmp_path,
        MINERU_LOCAL_PROJECT_PATH=str(tmp_path / "missing-project"),
    )
    commands = _Commands(adapter_return_code=7)

    status = check_local_mineru_runtime(
        config,
        run_command=commands,
        disk_usage=lambda _path: SimpleNamespace(free=2 * GIB),
        virtual_memory=lambda: SimpleNamespace(available=3 * GIB),
        write_probe=lambda _path: False,
    )

    assert status.ready is False
    assert set(status.error_codes) == {
        "project_missing",
        "python_missing",
        "adapter_unavailable",
        "temp_not_writable",
        "disk_below_minimum",
        "memory_below_minimum",
    }
    with pytest.raises(LocalMinerURuntimeError) as captured:
        require_local_mineru_runtime(
            config,
            run_command=commands,
            disk_usage=lambda _path: SimpleNamespace(free=2 * GIB),
            virtual_memory=lambda: SimpleNamespace(available=3 * GIB),
            write_probe=lambda _path: False,
        )
    assert captured.value.error_codes == status.error_codes


def test_local_runtime_reports_missing_uv_without_launching_subprocess(
    tmp_path: Path,
) -> None:
    config = _local_config(
        tmp_path,
        MINERU_LOCAL_UV_EXECUTABLE=str(tmp_path / "missing-uv.exe"),
    )
    commands = _Commands()

    status = check_local_mineru_runtime(
        config,
        run_command=commands,
        disk_usage=lambda _path: SimpleNamespace(free=20 * GIB),
        virtual_memory=lambda: SimpleNamespace(available=16 * GIB),
        write_probe=lambda _path: True,
    )

    assert status.ready is False
    assert status.error_codes == ("uv_missing", "adapter_unavailable")
    assert commands.calls == []


def test_temp_probe_maps_cleanup_failure_to_not_writable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_path = "C:\\private\\customer-temp"

    def fail_cleanup(_path: Path, *, missing_ok: bool = False) -> None:
        del missing_ok
        raise PermissionError(private_path)

    monkeypatch.setattr(Path, "unlink", fail_cleanup)

    assert _probe_writable(tmp_path) is False


@pytest.mark.parametrize(("ready", "exit_code"), [(True, 0), (False, 1)])
def test_preflight_cli_prints_only_status_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    ready: bool,
    exit_code: int,
) -> None:
    status = LocalMinerURuntimeStatus(
        provider="local",
        ready=ready,
        checks={"project": ready},
        free_disk_bytes=20 * GIB,
        available_memory_bytes=16 * GIB,
        error_codes=() if ready else ("project_missing",),
    )
    monkeypatch.setattr(
        preflight_cli,
        "check_local_mineru_runtime",
        lambda _settings: status,
    )

    result = preflight_cli.main([])

    captured = capsys.readouterr()
    assert result == exit_code
    assert json.loads(captured.out) == status.to_dict()
    assert captured.err == ""
