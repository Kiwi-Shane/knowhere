"""Contract checks for the opt-in D2 local MinerU worker overlay."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
OVERLAY_PATH = REPO_ROOT / "deploy" / "local-dev" / "docker-compose.d2-local-mineru.yml"
DOCKERFILE_PATH = REPO_ROOT / "deploy" / "docker" / "Dockerfile.worker.local-mineru"
MODEL_CONFIG_PATH = REPO_ROOT / "deploy" / "docker" / "mineru.local.json"


class _ComposeLoader(yaml.SafeLoader):
    """Parse Compose-only tags while keeping the contract test offline."""


def _construct_compose_tag(loader: _ComposeLoader, node: yaml.Node) -> object:
    if node.id == "sequence":
        return loader.construct_sequence(node, deep=True)
    if node.id == "mapping":
        return loader.construct_mapping(node, deep=True)
    return loader.construct_scalar(node)


_ComposeLoader.add_constructor("!reset", _construct_compose_tag)
_ComposeLoader.add_constructor("!override", _construct_compose_tag)


def _config() -> dict[str, object]:
    config = yaml.load(OVERLAY_PATH.read_text(encoding="utf-8"), Loader=_ComposeLoader)
    assert isinstance(config, dict)
    return config


def _worker() -> dict[str, object]:
    services = _config()["services"]
    assert isinstance(services, dict)
    worker = services["worker"]
    assert isinstance(worker, dict)
    return worker


def test_local_overlay_replaces_only_worker_and_requires_named_context() -> None:
    config = _config()
    services = config["services"]
    assert isinstance(services, dict)
    assert set(services) == {"worker"}

    worker = _worker()
    build = worker["build"]
    assert isinstance(build, dict)
    assert build["dockerfile"] == "deploy/docker/Dockerfile.worker.local-mineru"
    additional_contexts = build["additional_contexts"]
    assert isinstance(additional_contexts, dict)
    assert "mineru-source" in additional_contexts
    args = build["args"]
    assert isinstance(args, dict)
    assert "MINERU_SOURCE_REVISION" in args
    assert worker["image"] == "knowhere-worker:d2-local-mineru"


def test_local_overlay_sets_fail_closed_runtime_environment() -> None:
    environment = _worker()["environment"]
    assert isinstance(environment, dict)
    assert environment["MINERU_PROVIDER"] == "local"
    assert environment["MINERU_LOCAL_PREFLIGHT_ON_STARTUP"] == "true"
    assert environment["MINERU_LOCAL_PROJECT_PATH"] == "/opt/mineru"
    assert environment["MINERU_LOCAL_UV_EXECUTABLE"] == "/usr/local/bin/uv"
    assert environment["MINERU_LOCAL_PYTHON_EXECUTABLE"] == (
        "/opt/mineru/.venv/bin/python"
    )
    assert environment["MINERU_LOCAL_MODEL_ROOT"] == "/mnt/models/mineru"
    assert environment["MINERU_MODEL_SOURCE"] == "local"
    assert environment["MINERU_TOOLS_CONFIG_JSON"] == "/opt/mineru/mineru.json"
    assert environment["WORKER_CONCURRENCY"] == "1"
    assert environment["MINERU_LOCAL_MAX_CONCURRENT_JOBS"] == "1"


def test_local_overlay_model_mount_is_read_only_and_reuses_d2_restrictions() -> None:
    worker = _worker()
    assert worker["ports"] == []
    assert worker["read_only"] is True
    assert "ALL" in worker["cap_drop"]
    assert "no-new-privileges:true" in worker["security_opt"]

    volumes = worker["volumes"]
    assert isinstance(volumes, list)
    model_mount = next(
        item for item in volumes if item["target"] == "/mnt/models/mineru"
    )
    assert model_mount["read_only"] is True
    assert "MINERU_MODEL_ROOT" in model_mount["source"]


def test_local_image_and_model_template_keep_source_and_model_contracts() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")
    assert "COPY --from=mineru-source" in dockerfile
    assert "uv sync --locked --no-dev --extra pipeline" in dockerfile
    assert "MINERU_SOURCE_REVISION" in dockerfile
    assert "MINERU_PROVIDER=local" in dockerfile

    model_config = json.loads(MODEL_CONFIG_PATH.read_text(encoding="utf-8"))
    assert model_config == {
        "models-dir": {"pipeline": "/mnt/models/mineru", "vlm": ""},
        "model-source": "local",
        "config_version": "1.3.2",
    }
