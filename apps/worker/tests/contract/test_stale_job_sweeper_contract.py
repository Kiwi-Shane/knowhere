from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from support.contract_database import insert_contract_job, insert_contract_user


def _build_file_job_metadata() -> dict[str, str]:
    return {
        "document_id": f"doc_{uuid4().hex[:12]}",
        "namespace": "worker-contract",
        "source_type": "file",
    }


def _load_worker_modules() -> tuple[Any, Engine]:
    import app.core.tasks.stale_job_sweeper as stale_job_sweeper
    from shared.core.database_sync import get_sync_engine

    return stale_job_sweeper, get_sync_engine()


def test_should_expire_stale_jobs_and_persist_failure_state(
    worker_contract_environment: None,
) -> None:
    stale_job_id = f"job_stale_{uuid4().hex[:12]}"
    fresh_job_id = f"job_fresh_{uuid4().hex[:12]}"
    user_id = f"worker-user-{uuid4().hex[:12]}"

    stale_job_sweeper, engine = _load_worker_modules()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stale_updated_at = now - timedelta(days=1)

    with engine.begin() as connection:
        insert_contract_user(connection, user_id=user_id)
        insert_contract_job(
            connection,
            job_id=stale_job_id,
            user_id=user_id,
            status="running",
            source_type="file",
            webhook_enabled=False,
            job_metadata=_build_file_job_metadata(),
            created_at=stale_updated_at - timedelta(minutes=5),
            updated_at=stale_updated_at,
        )
        insert_contract_job(
            connection,
            job_id=fresh_job_id,
            user_id=user_id,
            status="waiting-file",
            source_type="file",
            webhook_enabled=False,
            job_metadata=_build_file_job_metadata(),
            created_at=now - timedelta(minutes=5),
            updated_at=now,
        )

    result = stale_job_sweeper.expire_stale_jobs()

    assert result == {
        "status": "success",
        "expired": 1,
        "skipped": 0,
        "expired_credentials": 0,
    }

    with engine.begin() as connection:
        stale_job_row = (
            connection.execute(
                text(
                    """
                    SELECT status, error_code, error_message
                    FROM jobs
                    WHERE job_id = :job_id
                    """
                ),
                {"job_id": stale_job_id},
            )
            .mappings()
            .one()
        )
        fresh_job_row = (
            connection.execute(
                text(
                    """
                    SELECT status
                    FROM jobs
                    WHERE job_id = :job_id
                    """
                ),
                {"job_id": fresh_job_id},
            )
            .mappings()
            .one()
        )
        audit_log_row = (
            connection.execute(
                text(
                    """
                    SELECT from_state, to_state, transition_reason, transition_metadata
                    FROM job_state_audit_logs
                    WHERE job_id = :job_id
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"job_id": stale_job_id},
            )
            .mappings()
            .one()
        )

    audit_metadata = dict(audit_log_row["transition_metadata"])

    assert stale_job_row["status"] == "failed"
    assert stale_job_row["error_code"] == stale_job_sweeper.JOB_EXPIRED_ERROR_CODE
    assert stale_job_row["error_message"] == stale_job_sweeper.JOB_EXPIRED_ERROR_MESSAGE
    assert fresh_job_row["status"] == "waiting-file"
    assert audit_log_row["from_state"] == "running"
    assert audit_log_row["to_state"] == "failed"
    assert audit_log_row["transition_reason"] == "mark_failed"
    assert audit_metadata["sweeper"] is True
    assert audit_metadata["stale_status"] == "running"
    assert audit_metadata["error_code"] == stale_job_sweeper.JOB_EXPIRED_ERROR_CODE


def test_should_skip_duplicate_beat_firing_with_the_real_periodic_redis_lock(
    worker_contract_environment: None,
) -> None:
    stale_job_sweeper, _ = _load_worker_modules()

    first_result = stale_job_sweeper.expire_stale_jobs()
    second_result = stale_job_sweeper.expire_stale_jobs()

    assert first_result == {
        "status": "success",
        "expired": 0,
        "skipped": 0,
        "expired_credentials": 0,
    }
    assert second_result == {
        "status": "skipped",
        "reason": "duplicate Beat firing",
    }


def test_terminal_credential_cleanup_does_not_delete_active_job_credentials(
    worker_contract_environment: None,
) -> None:
    from shared.core.database_sync import get_sync_db_context
    from shared.services.jobs.job_llm_credential_service import (
        JobLLMCredentialService,
    )

    terminal_job_id = f"job_terminal_cleanup_{uuid4().hex[:12]}"
    active_job_id = f"job_active_cleanup_{uuid4().hex[:12]}"
    terminal_credential_id = f"jllm_{uuid4().hex[:24]}"
    active_credential_id = f"jllm_{uuid4().hex[:24]}"
    user_id = f"worker-user-{uuid4().hex[:12]}"
    _, engine = _load_worker_modules()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    with engine.begin() as connection:
        insert_contract_user(connection, user_id=user_id)
        insert_contract_job(
            connection,
            job_id=terminal_job_id,
            user_id=user_id,
            status="failed",
            source_type="file",
            webhook_enabled=False,
            job_metadata=_build_file_job_metadata(),
            created_at=now,
            updated_at=now,
        )
        insert_contract_job(
            connection,
            job_id=active_job_id,
            user_id=user_id,
            status="running",
            source_type="file",
            webhook_enabled=False,
            job_metadata=_build_file_job_metadata(),
            created_at=now,
            updated_at=now,
        )
        connection.execute(
            text(
                """
                INSERT INTO job_llm_credentials (
                    id, job_id, user_id, config_encrypted, status,
                    expires_at, created_at
                ) VALUES (
                    :terminal_id, :terminal_job_id, :user_id, :terminal_ciphertext,
                    'active', :expires_at, :created_at
                ), (
                    :active_id, :active_job_id, :user_id, :active_ciphertext,
                    'active', :expires_at, :created_at
                )
                """
            ),
            {
                "terminal_id": terminal_credential_id,
                "terminal_job_id": terminal_job_id,
                "terminal_ciphertext": "terminal-ciphertext",
                "active_id": active_credential_id,
                "active_job_id": active_job_id,
                "active_ciphertext": "active-ciphertext",
                "user_id": user_id,
                "expires_at": now + timedelta(hours=1),
                "created_at": now,
            },
        )

    with get_sync_db_context() as db:
        deleted_count = JobLLMCredentialService.delete_for_terminal_job_sync(
            db,
            terminal_job_id,
        )

    assert deleted_count == 1
    with engine.begin() as connection:
        remaining_rows = (
            connection.execute(
                text(
                    """
                    SELECT id, job_id
                    FROM job_llm_credentials
                    WHERE id IN (:terminal_id, :active_id)
                    ORDER BY id
                    """
                ),
                {
                    "terminal_id": terminal_credential_id,
                    "active_id": active_credential_id,
                },
            )
            .mappings()
            .all()
        )

    assert remaining_rows == [{"id": active_credential_id, "job_id": active_job_id}]
