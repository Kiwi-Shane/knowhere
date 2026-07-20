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
START_SCRIPT_PATH = COMPOSE_PATH.parent / "start-dev.sh"


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


def test_local_dev_network_is_internal() -> None:
    networks = _compose_config()["networks"]
    assert isinstance(networks, dict)

    for network_name, network in networks.items():
        assert isinstance(network, dict), network_name
        assert network.get("internal") is True, network_name


def test_local_dev_launcher_summary_stays_loopback_and_secret_free() -> None:
    script = START_SCRIPT_PATH.read_text(encoding="utf-8")

    assert "--host 127.0.0.1" in script
    assert "--host 0.0.0.0" not in script
    assert "root/root123" not in script
