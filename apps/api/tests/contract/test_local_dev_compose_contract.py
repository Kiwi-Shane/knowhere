"""Contract checks for the local development Compose boundary."""

from __future__ import annotations

from pathlib import Path

import yaml


COMPOSE_PATH = (
    Path(__file__).resolve().parents[4]
    / "deploy"
    / "local-dev"
    / "docker-compose.dev.yml"
)


def _compose_config() -> dict[str, object]:
    config = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    assert isinstance(config, dict)
    return config


def test_local_dev_published_ports_are_loopback_only() -> None:
    services = _compose_config()["services"]
    assert isinstance(services, dict)

    for service_name, service in services.items():
        assert isinstance(service, dict), service_name
        for port in service.get("ports", []):
            assert str(port).startswith("127.0.0.1:"), (service_name, port)


def test_local_dev_services_declare_resource_limits() -> None:
    services = _compose_config()["services"]
    assert isinstance(services, dict)

    for service_name, service in services.items():
        assert isinstance(service, dict), service_name
        assert isinstance(service.get("mem_limit"), str), service_name
        assert float(service["cpus"]) > 0, service_name
        assert int(service["pids_limit"]) > 0, service_name
