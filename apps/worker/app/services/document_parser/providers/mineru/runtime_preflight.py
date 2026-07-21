"""Content-free readiness checks for an explicitly selected local MinerU runtime."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Protocol

import psutil


RUNTIME_SCHEMA_VERSION = "local-mineru-runtime/1.0"
_GIB = 1024**3
_ERROR_CODES = {
    "project": "project_missing",
    "uv": "uv_missing",
    "python": "python_missing",
    "adapter": "adapter_unavailable",
    "models": "models_missing",
    "temp_writable": "temp_not_writable",
    "disk": "disk_below_minimum",
    "memory": "memory_below_minimum",
}
_OFFLINE_ENVIRONMENT = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "MODELSCOPE_OFFLINE": "1",
}


class _RuntimeConfig(Protocol):
    MINERU_PROVIDER: Literal["cloud", "local"]
    MINERU_LOCAL_PROJECT_PATH: str
    MINERU_LOCAL_UV_EXECUTABLE: str
    MINERU_LOCAL_PYTHON_EXECUTABLE: str
    MINERU_LOCAL_MODEL_ROOT: str
    MINERU_LOCAL_MIN_FREE_DISK_GB: int
    MINERU_LOCAL_MIN_AVAILABLE_MEMORY_GB: int
    TMP_PATH: str


RunCommand = Callable[..., subprocess.CompletedProcess[str]]
DiskUsage = Callable[[Path], Any]
VirtualMemory = Callable[[], Any]
WriteProbe = Callable[[Path], bool]


@dataclass(frozen=True)
class LocalMinerURuntimeStatus:
    provider: str
    ready: bool
    checks: dict[str, bool]
    free_disk_bytes: int
    available_memory_bytes: int
    error_codes: tuple[str, ...]
    schema_version: str = RUNTIME_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "provider": self.provider,
            "ready": self.ready,
            "checks": dict(self.checks),
            "free_disk_bytes": self.free_disk_bytes,
            "available_memory_bytes": self.available_memory_bytes,
            "error_codes": list(self.error_codes),
        }


class LocalMinerURuntimeError(RuntimeError):
    """Raised when explicit local mode cannot safely accept work."""

    def __init__(self, error_codes: tuple[str, ...]) -> None:
        self.error_codes = error_codes
        super().__init__(
            "Local MinerU runtime is not ready: " + ",".join(error_codes)
        )


def _resolve_uv(value: str) -> Path | None:
    normalized = value.strip()
    if not normalized:
        return None
    configured = Path(normalized).expanduser()
    if configured.is_absolute():
        return configured.resolve()
    located = shutil.which(normalized)
    return Path(located).resolve() if located else None


def _resolve_mineru_python(config: _RuntimeConfig, project: Path) -> Path:
    configured = config.MINERU_LOCAL_PYTHON_EXECUTABLE.strip()
    if configured:
        return Path(configured).expanduser().resolve()
    relative = Path(
        "./.venv/Scripts/python.exe" if os.name == "nt" else "./.venv/bin/python"
    )
    return (project / relative).resolve()


def _probe_writable(root: Path) -> bool:
    descriptor: int | None = None
    temporary: Path | None = None
    writable = False
    try:
        root.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(dir=root, prefix=".mineru-preflight-")
        temporary = Path(name)
        os.close(descriptor)
        descriptor = None
        writable = True
    except OSError:
        writable = False
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                writable = False
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                writable = False
    return writable


def _probe_adapter(
    uv_executable: Path,
    mineru_python: Path,
    *,
    run_command: RunCommand,
) -> bool:
    environment = os.environ.copy()
    environment.update(_OFFLINE_ENVIRONMENT)
    commands = (
        [str(uv_executable), "--version"],
        [
            str(mineru_python),
            "-I",
            "-c",
            "import mineru.integrations.knowhere.cli",
        ],
    )
    try:
        return all(
            run_command(
                argv,
                check=False,
                capture_output=True,
                text=True,
                shell=False,
                timeout=10,
                env=environment,
            ).returncode
            == 0
            for argv in commands
        )
    except (OSError, subprocess.SubprocessError):
        return False


def _available_bytes(probe: Callable[[], Any], attribute: str) -> int:
    try:
        return int(getattr(probe(), attribute))
    except (AttributeError, OSError, TypeError, ValueError):
        return 0


def check_local_mineru_runtime(
    config: _RuntimeConfig,
    *,
    run_command: RunCommand = subprocess.run,
    disk_usage: DiskUsage = shutil.disk_usage,
    virtual_memory: VirtualMemory = psutil.virtual_memory,
    write_probe: WriteProbe = _probe_writable,
) -> LocalMinerURuntimeStatus:
    """Return a path-free readiness result without loading models or networking."""

    if config.MINERU_PROVIDER != "local":
        return LocalMinerURuntimeStatus(
            provider="cloud",
            ready=True,
            checks={},
            free_disk_bytes=0,
            available_memory_bytes=0,
            error_codes=(),
        )

    project_value = config.MINERU_LOCAL_PROJECT_PATH.strip()
    project = (
        Path(project_value).expanduser().resolve() if project_value else Path()
    )
    uv_executable = _resolve_uv(config.MINERU_LOCAL_UV_EXECUTABLE)
    mineru_python = _resolve_mineru_python(config, project)
    model_root_value = getattr(config, "MINERU_LOCAL_MODEL_ROOT", "").strip()
    model_root = Path(model_root_value).expanduser().resolve() if model_root_value else None
    temp_root = Path(config.TMP_PATH).expanduser().resolve()
    temp_writable = write_probe(temp_root)
    try:
        free_disk_bytes = int(disk_usage(temp_root).free) if temp_writable else 0
    except (AttributeError, OSError, TypeError, ValueError):
        free_disk_bytes = 0
    available_memory_bytes = _available_bytes(virtual_memory, "available")

    checks = {
        "project": bool(project_value) and project.is_dir(),
        "uv": uv_executable is not None and uv_executable.is_file(),
        "python": mineru_python.is_file(),
        "models": model_root is None or model_root.is_dir(),
        "adapter": False,
        "temp_writable": temp_writable,
        "disk": free_disk_bytes
        >= config.MINERU_LOCAL_MIN_FREE_DISK_GB * _GIB,
        "memory": available_memory_bytes
        >= config.MINERU_LOCAL_MIN_AVAILABLE_MEMORY_GB * _GIB,
    }
    if checks["project"] and checks["uv"] and checks["python"]:
        assert uv_executable is not None
        checks["adapter"] = _probe_adapter(
            uv_executable,
            mineru_python,
            run_command=run_command,
        )
    error_codes = tuple(
        code for check, code in _ERROR_CODES.items() if not checks[check]
    )
    return LocalMinerURuntimeStatus(
        provider="local",
        ready=not error_codes,
        checks=checks,
        free_disk_bytes=free_disk_bytes,
        available_memory_bytes=available_memory_bytes,
        error_codes=error_codes,
    )


def require_local_mineru_runtime(
    config: _RuntimeConfig,
    *,
    run_command: RunCommand = subprocess.run,
    disk_usage: DiskUsage = shutil.disk_usage,
    virtual_memory: VirtualMemory = psutil.virtual_memory,
    write_probe: WriteProbe = _probe_writable,
) -> LocalMinerURuntimeStatus:
    """Return readiness or raise a stable error containing only allowlisted codes."""

    status = check_local_mineru_runtime(
        config,
        run_command=run_command,
        disk_usage=disk_usage,
        virtual_memory=virtual_memory,
        write_probe=write_probe,
    )
    if not status.ready:
        raise LocalMinerURuntimeError(status.error_codes)
    return status
