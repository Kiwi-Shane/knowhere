"""Add encrypted job-scoped BYOK credential records.

Revision ID: c7d8e9f0a1b2
Revises: fbe1c2d3e4f5
Create Date: 2026-07-21 15:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "fbe1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the encrypted BYOK credential boundary."""
    op.create_table(
        "job_llm_credentials",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("config_encrypted", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", name="uq_job_llm_credentials_job_id"),
    )
    op.create_index(
        "idx_job_llm_credentials_user_status",
        "job_llm_credentials",
        ["user_id", "status"],
    )
    op.create_index(
        "idx_job_llm_credentials_expires_at",
        "job_llm_credentials",
        ["expires_at"],
    )


def downgrade() -> None:
    """Drop the encrypted BYOK credential boundary."""
    op.drop_index(
        "idx_job_llm_credentials_expires_at",
        table_name="job_llm_credentials",
    )
    op.drop_index(
        "idx_job_llm_credentials_user_status",
        table_name="job_llm_credentials",
    )
    op.drop_table("job_llm_credentials")
