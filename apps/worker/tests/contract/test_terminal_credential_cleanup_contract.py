from __future__ import annotations

from shared.core.exceptions.domain_exceptions import PermissionDeniedException


def test_failure_handler_uses_terminal_scoped_cleanup_when_finalization_is_already_terminal(
    worker_contract_environment: None,
    monkeypatch,
) -> None:
    from app.core.tasks.base_task import DocumentIngestionBaseTask
    from shared.services.jobs.job_llm_credential_service import (
        JobLLMCredentialService,
    )

    cleanup_calls: list[str] = []

    class _AlreadyTerminalLifecycle:
        def finalize_job_failure(self, **_kwargs: object) -> bool:
            return False

    monkeypatch.setattr(
        "shared.services.jobs.lifecycle.service.get_sync_job_lifecycle_service",
        lambda: _AlreadyTerminalLifecycle(),
    )
    monkeypatch.setattr(
        JobLLMCredentialService,
        "delete_for_terminal_job",
        lambda job_id: cleanup_calls.append(job_id),
    )

    DocumentIngestionBaseTask().on_failure(
        PermissionDeniedException(),
        "task-terminal-cleanup",
        ("job-terminal-cleanup",),
        {},
        None,
    )

    assert cleanup_calls == ["job-terminal-cleanup"]
