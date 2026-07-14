from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest
from pytest import MonkeyPatch


def _configure_mineru_startup(
    monkeypatch: MonkeyPatch,
    worker_bootstrap: ModuleType,
    *,
    provider: str,
    enabled: bool,
) -> None:
    monkeypatch.setattr(worker_bootstrap.settings, "MINERU_PROVIDER", provider)
    monkeypatch.setattr(
        worker_bootstrap.settings,
        "MINERU_LOCAL_PREFLIGHT_ON_STARTUP",
        enabled,
    )


def _patch_worker_startup_side_effects(
    monkeypatch: MonkeyPatch,
    worker_bootstrap: ModuleType,
    events: list[str],
) -> None:
    monkeypatch.setattr(worker_bootstrap, "setup_logging", lambda **_: None)
    monkeypatch.setattr(
        worker_bootstrap,
        "start_worker_heartbeat",
        lambda: events.append("heartbeat"),
    )


def test_should_register_worker_task_modules_for_celery_consumers(
    worker_contract_environment: None,
) -> None:
    from app.core import worker_bootstrap
    from shared.core.celery_app import celery_app

    expected_task_names: tuple[str, ...] = (
        "app.core.tasks.document_ingestion_tasks.upload_url_file_task",
        "app.core.tasks.document_ingestion_tasks.parse_task",
        "app.core.tasks.kb_tasks.upload_url_file_task",
        "app.core.tasks.kb_tasks.parse_task",
        "app.core.tasks.stale_job_sweeper.expire_stale_jobs",
        "app.core.tasks.webhook_tasks.recover_orphaned_webhooks",
    )
    task_module_names: tuple[str, ...] = (
        "app.core.tasks.document_ingestion_tasks",
        "app.core.tasks.stale_job_sweeper",
        "app.core.tasks.webhook_tasks",
    )

    for task_name in expected_task_names:
        celery_app.tasks.pop(task_name, None)

    for module_name in task_module_names:
        sys.modules.pop(module_name, None)

    worker_bootstrap._register_task_modules()

    for task_name in expected_task_names:
        assert task_name in celery_app.tasks


def test_should_consume_current_and_legacy_ingestion_queues(
    worker_contract_environment: None,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.core import worker_bootstrap

    worker_main_calls: list[list[str]] = []
    beat_commands: list[list[str]] = []

    class FakeBeatProcess:
        pass

    def record_beat_command(command: list[str]) -> FakeBeatProcess:
        beat_commands.append(command)
        return FakeBeatProcess()

    def record_worker_main(args: list[str]) -> None:
        worker_main_calls.append(args)

    monkeypatch.setattr(worker_bootstrap.subprocess, "Popen", record_beat_command)
    monkeypatch.setattr(worker_bootstrap.celery_app, "worker_main", record_worker_main)

    worker_bootstrap.run_worker()

    assert beat_commands != []
    assert len(worker_main_calls) == 1

    worker_args = worker_main_calls[0]
    queue_arg = worker_args[worker_args.index("-Q") + 1]
    consumed_queues = set(queue_arg.split(","))

    assert {
        "document_ingestion_high",
        "document_ingestion_medium",
        "document_ingestion_low",
        "kb_high",
        "kb_medium",
        "kb_low",
    }.issubset(consumed_queues)


def test_worker_startup_skips_mineru_preflight_in_cloud_mode(
    worker_contract_environment: None,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.core import worker_bootstrap

    events: list[str] = []
    _configure_mineru_startup(
        monkeypatch,
        worker_bootstrap,
        provider="cloud",
        enabled=True,
    )
    _patch_worker_startup_side_effects(monkeypatch, worker_bootstrap, events)
    monkeypatch.setattr(
        worker_bootstrap,
        "require_local_mineru_runtime",
        lambda _: pytest.fail("cloud mode must not execute the local preflight"),
        raising=False,
    )

    worker_bootstrap.init_worker()

    assert events == ["heartbeat"]


def test_worker_startup_requires_ready_local_mineru_when_enabled(
    worker_contract_environment: None,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.core import worker_bootstrap

    events: list[str] = []
    _configure_mineru_startup(
        monkeypatch,
        worker_bootstrap,
        provider="local",
        enabled=True,
    )
    _patch_worker_startup_side_effects(monkeypatch, worker_bootstrap, events)
    monkeypatch.setattr(
        worker_bootstrap,
        "require_local_mineru_runtime",
        lambda _: (
            events.append("preflight")
            or SimpleNamespace(
                ready=True,
                free_disk_bytes=20 * 1024**3,
                available_memory_bytes=16 * 1024**3,
            )
        ),
    )

    worker_bootstrap.init_worker()

    assert events[:2] == ["preflight", "heartbeat"]


def test_worker_startup_fails_before_heartbeat_for_invalid_local_runtime(
    worker_contract_environment: None,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.core import worker_bootstrap
    from app.services.document_parser.providers.mineru.runtime_preflight import (
        LocalMinerURuntimeError,
    )

    events: list[str] = []
    _configure_mineru_startup(
        monkeypatch,
        worker_bootstrap,
        provider="local",
        enabled=True,
    )
    _patch_worker_startup_side_effects(monkeypatch, worker_bootstrap, events)

    def fail_preflight(_: object) -> None:
        events.append("preflight")
        raise LocalMinerURuntimeError(("project_missing",))

    monkeypatch.setattr(
        worker_bootstrap,
        "require_local_mineru_runtime",
        fail_preflight,
        raising=False,
    )

    with pytest.raises(LocalMinerURuntimeError):
        worker_bootstrap.init_worker()

    assert events == ["preflight"]


def test_worker_startup_can_defer_preflight_when_operator_disables_it(
    worker_contract_environment: None,
    monkeypatch: MonkeyPatch,
) -> None:
    from app.core import worker_bootstrap

    events: list[str] = []
    _configure_mineru_startup(
        monkeypatch,
        worker_bootstrap,
        provider="local",
        enabled=False,
    )
    _patch_worker_startup_side_effects(monkeypatch, worker_bootstrap, events)
    monkeypatch.setattr(
        worker_bootstrap,
        "require_local_mineru_runtime",
        lambda _: pytest.fail("disabled startup preflight must be skipped"),
        raising=False,
    )

    worker_bootstrap.init_worker()

    assert events == ["heartbeat"]
