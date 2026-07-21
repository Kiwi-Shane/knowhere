from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault(
    "WEBHOOK_MASTER_KEY",
    "GE5FgAG9t4a1C1xTRNiOC2GQHgp4YMSN7t8lTJq-FxY=",
)
os.environ.setdefault("S3_BUCKET_NAME", "contract-test-bucket")
os.environ.setdefault("S3_ACCESS_KEY_ID", "contract-test-access")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "contract-test-secret")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")

from shared.core.config import app_config
from shared.core.config.qstash import QStashConfig
from shared.models.database.webhook import WebhookEvent
from shared.services.webhook.delivery_client import (
    WebhookDeliveryResult,
    WebhookDeliveryTarget,
    WebhookTargetValidation,
)
from shared.services.webhook.event_delivery import WebhookEventDelivery


class _FakeResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


class _FakeAsyncSession:
    def __init__(self, job_metadata: dict[str, Any] | None) -> None:
        self.job_metadata = job_metadata
        self.execute_calls = 0
        self.added: list[Any] = []
        self.commit_calls = 0

    async def execute(self, statement: Any) -> _FakeResult:
        self.execute_calls += 1
        return _FakeResult(self.job_metadata)

    def add(self, value: Any) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        self.commit_calls += 1


class _FakeClient:
    def __init__(self) -> None:
        self.validate_calls = 0
        self.post_calls = 0

    async def validate_target(
        self, *, event_id: str, target_url: str
    ) -> WebhookTargetValidation:
        self.validate_calls += 1
        return WebhookTargetValidation(
            target=WebhookDeliveryTarget(
                target_url=target_url,
                pinned_ip="93.184.216.34",
            ),
            failure=None,
        )

    async def post_json(self, **kwargs: Any) -> WebhookDeliveryResult:
        self.post_calls += 1
        return WebhookDeliveryResult(
            success=True,
            status_code=202,
            duration_ms=1,
            error_message=None,
        )


class _FakeEnricher:
    async def enrich(self, event: WebhookEvent) -> dict[str, Any]:
        return dict(event.payload)


class _FakeSecretResolver:
    async def resolve_for_event(
        self, db: _FakeAsyncSession, event: WebhookEvent
    ) -> str:
        return "contract-webhook-secret"


def _event() -> WebhookEvent:
    return WebhookEvent(
        id="contract-manual-webhook-event",
        job_id="contract-manual-webhook-job",
        target_url="https://hooks.contract.test/jobs",
        payload={"event": "job.completed"},
        status="pending",
        attempts=0,
    )


def _authorization_metadata() -> dict[str, Any]:
    return {
        "external_call_authorizations": {
            "webhook": {
                "approved": True,
                "provider": "webhook",
                "data_classification": "synthetic",
                "source_scope": "fixture:manual-webhook-contract",
                "authorization_id": "auth-manual-webhook-contract-001",
                "approved_by": "test-operator",
            }
        }
    }


def _delivery(client: _FakeClient) -> WebhookEventDelivery:
    return WebhookEventDelivery(
        client=client,
        enricher=_FakeEnricher(),
        secret_resolver=_FakeSecretResolver(),
    )


def test_direct_webhook_external_calls_are_default_denied() -> None:
    assert QStashConfig().WEBHOOK_EXTERNAL_CALLS_ENABLED is False


def test_manual_webhook_authorization_is_checked_before_target_validation() -> None:
    source_path = Path("packages/shared-python/shared/services/webhook/event_delivery.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    class_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "WebhookEventDelivery"
    )
    send_node = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "send"
    )
    authorization_method = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_authorize_delivery"
    )
    authorization_calls = [
        node
        for node in ast.walk(authorization_method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_external_call_authorization"
        and any(
            keyword.arg == "provider"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "webhook"
            for keyword in node.keywords
        )
    ]
    authorization_method_calls = [
        node
        for node in ast.walk(send_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_authorize_delivery"
    ]
    validation_calls = [
        node
        for node in ast.walk(send_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "validate_target"
    ]
    assert authorization_calls
    assert authorization_method_calls
    assert validation_calls
    assert "WEBHOOK_EXTERNAL_CALLS_ENABLED" in source_path.read_text(
        encoding="utf-8"
    )
    assert min(node.lineno for node in authorization_method_calls) < min(
        node.lineno for node in validation_calls
    )


@pytest.mark.asyncio
async def test_manual_webhook_is_default_denied_before_database_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_config,
        "WEBHOOK_EXTERNAL_CALLS_ENABLED",
        False,
        raising=False,
    )
    client = _FakeClient()
    db = _FakeAsyncSession(_authorization_metadata())

    result = await _delivery(client).send(db=db, event=_event(), is_manual=True)

    assert result.success is False
    assert result.status_code == 403
    assert db.execute_calls == 0
    assert client.validate_calls == 0
    assert client.post_calls == 0


@pytest.mark.asyncio
async def test_manual_webhook_requires_job_authorization_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_config,
        "WEBHOOK_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    client = _FakeClient()
    db = _FakeAsyncSession({"document_id": "missing-authorization"})

    result = await _delivery(client).send(db=db, event=_event(), is_manual=True)

    assert result.success is False
    assert result.status_code == 403
    assert db.execute_calls == 1
    assert client.validate_calls == 0
    assert client.post_calls == 0


@pytest.mark.asyncio
async def test_authorized_manual_webhook_can_reach_fake_delivery_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_config,
        "WEBHOOK_EXTERNAL_CALLS_ENABLED",
        True,
        raising=False,
    )
    client = _FakeClient()
    db = _FakeAsyncSession(_authorization_metadata())

    result = await _delivery(client).send(db=db, event=_event(), is_manual=True)

    assert result.success is True
    assert result.status_code == 202
    assert db.execute_calls == 1
    assert client.validate_calls == 1
    assert client.post_calls == 1
