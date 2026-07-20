"""Contract checks for the opt-in D2 hardened dependency harness."""

from __future__ import annotations

from pathlib import Path

import yaml


COMPOSE_PATH = (
    Path(__file__).resolve().parents[4]
    / "deploy"
    / "local-dev"
    / "docker-compose.dev.yml"
)
D2_OVERRIDE_PATH = COMPOSE_PATH.parent / "docker-compose.d2.yml"
D2_VERIFIER_PATH = COMPOSE_PATH.parent / "verify-d2.ps1"


class _ComposeLoader(yaml.SafeLoader):
    """Parse Compose-only tags while keeping the contract test offline."""


def _construct_reset(loader: _ComposeLoader, node: yaml.Node) -> object:
    if node.id == "sequence":
        return loader.construct_sequence(node, deep=True)
    if node.id == "mapping":
        return loader.construct_mapping(node, deep=True)
    return loader.construct_scalar(node)


_ComposeLoader.add_constructor("!reset", _construct_reset)
_ComposeLoader.add_constructor("!override", _construct_reset)


def _d2_config() -> dict[str, object]:
    config = yaml.load(D2_OVERRIDE_PATH.read_text(encoding="utf-8"), Loader=_ComposeLoader)
    assert isinstance(config, dict)
    return config


def test_d2_services_remove_host_published_ingress_and_use_internal_network() -> None:
    config = _d2_config()
    services = config["services"]
    assert isinstance(services, dict)
    assert set(services) == {"redis", "postgres", "localstack", "api", "worker"}

    for service_name in ("redis", "postgres", "localstack", "api", "worker"):
        service = services[service_name]
        assert isinstance(service, dict), service_name
        assert service["ports"] == [], service_name
        assert str(service["container_name"]).startswith("knowhere_d2_"), service_name

    networks = config["networks"]
    assert isinstance(networks, dict)
    network = networks["knowhere_network"]
    assert isinstance(network, dict)
    assert network["internal"] is True
    assert network["name"] == "knowhere_d2_internal"


def test_d2_services_declare_minimum_runtime_restrictions() -> None:
    services = _d2_config()["services"]
    assert isinstance(services, dict)

    for service_name, service in services.items():
        assert isinstance(service, dict), service_name
        assert service["read_only"] is True, service_name
        assert "ALL" in service["cap_drop"], service_name
        assert "no-new-privileges:true" in service["security_opt"], service_name
        assert service["restart"] == "no", service_name


def test_d2_entrypoints_receive_only_the_capabilities_they_need() -> None:
    services = _d2_config()["services"]
    assert isinstance(services, dict)
    assert set(services["redis"]["cap_add"]) == {"SETUID", "SETGID"}
    assert set(services["postgres"]["cap_add"]) == {
        "CHOWN",
        "DAC_OVERRIDE",
        "FOWNER",
        "SETGID",
        "SETUID",
    }


def test_d2_images_are_pinned_to_the_characterized_digests() -> None:
    services = _d2_config()["services"]
    assert isinstance(services, dict)

    for service_name in ("redis", "postgres", "localstack"):
        service = services[service_name]
        assert isinstance(service, dict), service_name
        assert "@sha256:" in str(service["image"]), service_name


def test_d2_application_images_bind_to_the_current_source_revision() -> None:
    services = _d2_config()["services"]
    assert isinstance(services, dict)

    for service_name, dockerfile in (("api", "deploy/docker/Dockerfile.api"), ("worker", "deploy/docker/Dockerfile.worker")):
        service = services[service_name]
        assert service["build"]["context"] == "../..", service_name
        assert service["build"]["dockerfile"] == dockerfile, service_name
        assert service["build"]["args"]["GIT_COMMIT"] == "c564a363", service_name


def test_d2_application_services_are_internal_telemetry_off_and_secret_file_backed() -> None:
    services = _d2_config()["services"]
    assert isinstance(services, dict)
    assert {"api", "worker"}.issubset(services)

    for service_name in ("api", "worker"):
        service = services[service_name]
        assert isinstance(service, dict), service_name
        assert service["ports"] == [], service_name
        assert service["read_only"] is True, service_name
        assert "ALL" in service["cap_drop"], service_name
        assert "no-new-privileges:true" in service["security_opt"], service_name
        assert service["mem_limit"], service_name
        assert float(service["cpus"]) > 0, service_name
        assert int(service["pids_limit"]) > 0, service_name
        assert service["secrets"] == ["postgres_password"], service_name

        environment = service["environment"]
        assert isinstance(environment, dict), service_name
        assert environment["TELEMETRY_ENABLED"] == "false", service_name
        assert environment["DATABASE_PASSWORD_FILE"] == (
            "/run/secrets/postgres_password"
        ), service_name
        assert "DATABASE_URL" in environment, service_name
        assert "d2-synthetic" not in str(environment["DATABASE_URL"]), service_name

    assert services["api"]["expose"] == ["5005"]
    assert services["worker"]["environment"]["WORKER_HEARTBEAT_FILE"] == (
        "/tmp/knowhere-worker-heartbeat.json"
    )


def test_d2_postgres_uses_a_file_backed_secret() -> None:
    config = _d2_config()
    postgres = config["services"]["postgres"]
    assert isinstance(postgres, dict)
    environment = postgres["environment"]
    assert isinstance(environment, dict)
    assert "POSTGRES_PASSWORD" not in environment
    assert environment["POSTGRES_PASSWORD_FILE"] == "/run/secrets/postgres_password"
    assert postgres["secrets"] == ["postgres_password"]
    secrets = config["secrets"]
    assert isinstance(secrets, dict)
    assert secrets["postgres_password"]["file"] == "./.d2-secrets/postgres_password"


def test_d2_localstack_has_no_host_bridge_or_docker_socket() -> None:
    localstack = _d2_config()["services"]["localstack"]
    assert isinstance(localstack, dict)
    assert localstack["extra_hosts"] == []
    assert localstack["environment"]["DOCKER_HOST"] == ""
    assert "lambda" not in str(localstack["environment"]["SERVICES"])
    assert "/var/run/docker.sock" not in str(localstack.get("volumes", []))
    assert "/root/.cache" in localstack["tmpfs"]


def test_d2_verifier_is_repeatable_and_does_not_teardown_the_harness() -> None:
    script = D2_VERIFIER_PATH.read_text(encoding="utf-8")
    assert "docker" in script
    assert '"compose"' in script
    assert "docker port" in script
    assert "_localstack/health" in script
    assert "knowhere_d2_api" in script
    assert "knowhere_d2_worker" in script
    assert "5005/health" in script
    assert "WORKER_HEARTBEAT_FILE" in script
    assert "TELEMETRY_ENABLED" in script
    assert "DATABASE_PASSWORD_FILE" in script
    assert "d2_backup_smoke" in script
    assert "-eq 5" in script
    assert " down" not in script
