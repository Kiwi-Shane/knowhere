"""Lifecycle service for encrypted, job-scoped BYOK configurations."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from loguru import logger

from shared.core.config import settings
from shared.core.state_machine.states import TERMINAL_STATES
from shared.models.database.job import Job
from shared.models.database.job_llm_credential import (
    JobLLMCredential,
    JobLLMCredentialStatus,
)
from shared.models.schemas.llm_config import LLMConfig, parse_llm_config
from shared.services.ai.llm_endpoint_policy import (
    LLMEndpointPolicyError,
    validate_llm_config_endpoint_policy,
)
from shared.services.encryption.fernet_service import (
    FernetService,
    get_fernet_service,
)
from shared.utils.utc_now import utc_now_naive


class JobLLMCredentialResolutionError(RuntimeError):
    """Raised when a job-scoped BYOK record cannot be safely resolved."""


def _serialize_config(config: LLMConfig) -> str:
    """Serialize a validated config deterministically before encryption."""
    return json.dumps(
        config.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )


class JobLLMCredentialService:
    """Build, resolve, and remove encrypted BYOK job credentials."""

    @staticmethod
    def build(
        *,
        job_id: str,
        user_id: str,
        config: LLMConfig,
        expires_at: datetime,
        encryption_service: FernetService | None = None,
    ) -> JobLLMCredential:
        """Build an unflushed credential record for the Job unit of work."""
        if expires_at <= utc_now_naive():
            raise ValueError("BYOK credential expiry must be in the future")
        parsed = parse_llm_config(config)
        if parsed is None:
            raise ValueError("BYOK credential configuration is invalid")

        service = encryption_service or get_fernet_service()
        encrypted = service.encrypt(_serialize_config(parsed))
        return JobLLMCredential(
            id=f"jllm_{uuid4().hex[:24]}",
            job_id=job_id,
            user_id=user_id,
            config_encrypted=encrypted,
            status=JobLLMCredentialStatus.ACTIVE,
            expires_at=expires_at,
        )

    @classmethod
    async def stage(
        cls,
        db: AsyncSession,
        *,
        job_id: str,
        user_id: str,
        config: LLMConfig,
        expires_at: datetime,
        encryption_service: FernetService | None = None,
    ) -> JobLLMCredential:
        """Stage an encrypted record; the caller commits it with the Job."""
        record = cls.build(
            job_id=job_id,
            user_id=user_id,
            config=config,
            expires_at=expires_at,
            encryption_service=encryption_service,
        )
        db.add(record)
        return record

    @staticmethod
    def decrypt_config(
        config_encrypted: str,
        *,
        encryption_service: FernetService | None = None,
    ) -> LLMConfig:
        """Decrypt and validate one stored config without exposing raw errors."""
        service = encryption_service or get_fernet_service()
        plaintext = service.decrypt(config_encrypted)
        if not plaintext:
            raise JobLLMCredentialResolutionError("BYOK credential decryption failed")
        try:
            parsed = parse_llm_config(json.loads(plaintext))
        except Exception as exc:
            raise JobLLMCredentialResolutionError(
                "BYOK credential payload is invalid"
            ) from exc
        if parsed is None:
            raise JobLLMCredentialResolutionError("BYOK credential payload is invalid")
        return parsed

    @classmethod
    def resolve_sync(
        cls,
        db: Session,
        *,
        job_id: str,
        requested_user_id: str | None,
        metadata: dict[str, object] | None,
        now: datetime | None = None,
        encryption_service: FernetService | None = None,
    ) -> LLMConfig | None:
        """Resolve a credential only after authoritative owner/lifecycle checks."""
        result = db.execute(
            select(JobLLMCredential, Job.user_id, Job.status)
            .join(Job, Job.job_id == JobLLMCredential.job_id)
            .where(JobLLMCredential.job_id == job_id)
        ).one_or_none()

        if result is None:
            stored_metadata = metadata or {}
            if (
                stored_metadata.get("llm_credential_id")
                or stored_metadata.get("llm_config_present")
                or stored_metadata.get("llm_config") is not None
            ):
                raise JobLLMCredentialResolutionError(
                    "BYOK credential reference is missing"
                )
            return None

        credential, owner_id, job_status = result
        if requested_user_id is not None and str(owner_id) != requested_user_id:
            raise JobLLMCredentialResolutionError(
                "BYOK credential owner does not match the worker owner"
            )
        if credential.user_id != str(owner_id):
            raise JobLLMCredentialResolutionError(
                "BYOK credential owner binding is invalid"
            )
        if job_status in TERMINAL_STATES:
            raise JobLLMCredentialResolutionError(
                "BYOK credential cannot be resolved for a terminal job"
            )

        effective_now = now or utc_now_naive()
        if credential.status != JobLLMCredentialStatus.ACTIVE:
            raise JobLLMCredentialResolutionError("BYOK credential is not active")
        if credential.expires_at <= effective_now:
            credential.status = JobLLMCredentialStatus.EXPIRED
            credential.revoked_at = effective_now
            raise JobLLMCredentialResolutionError("BYOK credential has expired")

        config = cls.decrypt_config(
            credential.config_encrypted,
            encryption_service=encryption_service,
        )
        try:
            validate_llm_config_endpoint_policy(
                config,
                external_calls_enabled=settings.LLM_EXTERNAL_CALLS_ENABLED,
                allowed_endpoints=settings.LLM_ALLOWED_PROVIDER_ENDPOINTS,
            )
        except LLMEndpointPolicyError as exc:
            raise JobLLMCredentialResolutionError(
                "BYOK endpoint policy rejected the credential"
            ) from exc

        credential.last_used_at = effective_now
        return config

    @classmethod
    def resolve_for_job(
        cls,
        *,
        job_id: str,
        requested_user_id: str | None,
        metadata: dict[str, object] | None,
        now: datetime | None = None,
        encryption_service: FernetService | None = None,
    ) -> LLMConfig | None:
        """Resolve through a short-lived worker sync DB session."""
        from shared.core.database_sync import get_sync_db_context

        with get_sync_db_context() as db:
            return cls.resolve_sync(
                db,
                job_id=job_id,
                requested_user_id=requested_user_id,
                metadata=metadata,
                now=now,
                encryption_service=encryption_service,
            )

    @staticmethod
    def delete_for_job_sync(db: Session, job_id: str) -> int:
        """Delete terminal/invalidated credential ciphertext for one Job."""
        result = db.execute(
            delete(JobLLMCredential).where(JobLLMCredential.job_id == job_id)
        )
        return int(result.rowcount or 0)

    @staticmethod
    def delete_for_terminal_job_sync(db: Session, job_id: str) -> int:
        """Delete credential ciphertext only when the Job is terminal."""
        terminal_job = select(Job.job_id).where(
            Job.job_id == job_id,
            Job.status.in_(TERMINAL_STATES),
        )
        result = db.execute(
            delete(JobLLMCredential).where(
                JobLLMCredential.job_id == job_id,
                JobLLMCredential.job_id.in_(terminal_job),
            )
        )
        return int(result.rowcount or 0)

    @staticmethod
    def delete_for_job(job_id: str) -> int:
        """Delete one Job's ciphertext using a short-lived worker session."""
        from shared.core.database_sync import get_sync_db_context

        try:
            with get_sync_db_context() as db:
                return JobLLMCredentialService.delete_for_job_sync(db, job_id)
        except Exception as exc:
            logger.error(
                "Failed to clean up job-scoped BYOK credential: "
                f"error_type={type(exc).__name__}"
            )
            return 0

    @staticmethod
    def delete_for_terminal_job(job_id: str) -> int:
        """Delete ciphertext only if the authoritative Job is terminal."""
        from shared.core.database_sync import get_sync_db_context

        try:
            with get_sync_db_context() as db:
                return JobLLMCredentialService.delete_for_terminal_job_sync(db, job_id)
        except Exception as exc:
            logger.error(
                "Failed to clean up terminal job-scoped BYOK credential: "
                f"error_type={type(exc).__name__}"
            )
            return 0

    @staticmethod
    def delete_expired_sync(
        db: Session,
        *,
        now: datetime | None = None,
        limit: int = 200,
    ) -> int:
        """Delete a bounded batch of expired credential ciphertext."""
        effective_now = now or utc_now_naive()
        ids = (
            db.execute(
                select(JobLLMCredential.id)
                .where(JobLLMCredential.expires_at <= effective_now)
                .order_by(JobLLMCredential.expires_at)
                .limit(limit)
            )
            .scalars()
            .all()
        )
        if not ids:
            return 0
        result = db.execute(
            delete(JobLLMCredential).where(JobLLMCredential.id.in_(ids))
        )
        return int(result.rowcount or 0)
