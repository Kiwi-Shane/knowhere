from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any

import pytest
from pytest import MonkeyPatch

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault(
    "WEBHOOK_MASTER_KEY",
    "GE5FgAG9t4a1C1xTRNiOC2GQHgp4YMSN7t8lTJq-FxY=",
)
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

from shared.core.exceptions.domain_exceptions import QStashServiceException
from shared.services.webhook import qstash_client


def _configure_qstash(monkeypatch: MonkeyPatch, *, enabled: bool) -> None:
    monkeypatch.setattr(
        qstash_client.app_config,
        "QSTASH_WEBHOOK_ENABLED",
        enabled,
        raising=False,
    )
    monkeypatch.setattr(
        qstash_client.app_config,
        "QSTASH_TOKEN",
        "contract-qstash-token",
    )
    monkeypatch.setattr(
        qstash_client.app_config,
        "QSTASH_CALLBACK_BASE_URL",
        "https://callbacks.contract.test/api/v1",
    )


def test_qstash_publish_requires_explicit_opt_in_before_client_initialization(
    monkeypatch: MonkeyPatch,
) -> None:
    _configure_qstash(monkeypatch, enabled=False)
    adapter = qstash_client.QStashClientAdapter()
    client_initialization_attempts = 0

    def unexpected_client_initialization() -> Any:
        nonlocal client_initialization_attempts
        client_initialization_attempts += 1
        raise AssertionError("disabled QStash delivery must not initialize a client")

    monkeypatch.setattr(adapter, "get_client", unexpected_client_initialization)

    with pytest.raises(QStashServiceException, match="not explicitly enabled"):
        adapter.publish_webhook(
            target_url="https://hooks.contract.test/worker",
            payload={"event": "job.failed"},
            signature="contract-signature",
            event_id="contract-event",
        )

    assert client_initialization_attempts == 0


def test_qstash_client_cannot_initialize_when_explicit_opt_in_is_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    _configure_qstash(monkeypatch, enabled=False)
    adapter = qstash_client.QStashClientAdapter()

    with pytest.raises(QStashServiceException, match="not explicitly enabled"):
        adapter.get_client()


def test_qstash_publish_can_proceed_only_after_explicit_opt_in(
    monkeypatch: MonkeyPatch,
) -> None:
    _configure_qstash(monkeypatch, enabled=True)
    adapter = qstash_client.QStashClientAdapter()
    published_calls: list[dict[str, Any]] = []

    class FakeMessageClient:
        def publish(self, **kwargs: Any) -> SimpleNamespace:
            published_calls.append(kwargs)
            return SimpleNamespace(message_id="contract-message")

    monkeypatch.setattr(
        adapter,
        "get_client",
        lambda: SimpleNamespace(message=FakeMessageClient()),
    )

    message_id = adapter.publish_webhook(
        target_url="https://hooks.contract.test/worker",
        payload={"event": "job.failed"},
        signature="contract-signature",
        event_id="contract-event",
    )

    assert message_id == "contract-message"
    assert published_calls[0]["url"] == "https://hooks.contract.test/worker"
    assert published_calls[0]["callback"] == (
        "https://callbacks.contract.test/api/v1/webhooks/qstash/callback"
    )
