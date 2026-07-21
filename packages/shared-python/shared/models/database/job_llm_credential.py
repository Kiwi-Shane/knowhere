"""Encrypted, job-scoped BYOK credential records."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.core.database import Base
from shared.utils.utc_now import utc_now_naive


class JobLLMCredentialStatus:
    """Lifecycle states for encrypted request-scoped LLM credentials."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class JobLLMCredential(Base):
    """One encrypted BYOK configuration bound to one Job and its owner."""

    __tablename__ = "job_llm_credentials"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"jllm_{uuid4().hex[:24]}"
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.job_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    config_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=JobLLMCredentialStatus.ACTIVE, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_job_llm_credentials_user_status", "user_id", "status"),
        Index("idx_job_llm_credentials_expires_at", "expires_at"),
    )

    def is_active(self, *, now: datetime | None = None) -> bool:
        """Return whether the record is active at the supplied naive UTC time."""
        effective_now = now or utc_now_naive()
        return (
            self.status == JobLLMCredentialStatus.ACTIVE
            and self.expires_at > effective_now
        )
