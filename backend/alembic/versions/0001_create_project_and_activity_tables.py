"""create project and activity tables

Revision ID: 0001
Revises:
Create Date: 2026-11-17 16:39:37.108056
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("cutoff_date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_project_dates"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "activity",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("budget_at_completion", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("planned_progress", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("actual_progress", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("actual_cost", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("actual_cost >= 0", name="ck_activity_ac_non_negative"),
        sa.CheckConstraint(
            "actual_progress BETWEEN 0 AND 100", name="ck_activity_actual_progress_range"
        ),
        sa.CheckConstraint("budget_at_completion > 0", name="ck_activity_bac_positive"),
        sa.CheckConstraint(
            "planned_progress BETWEEN 0 AND 100", name="ck_activity_planned_progress_range"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_activity_project_id"), "activity", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_project_id"), table_name="activity")
    op.drop_table("activity")
    op.drop_table("project")
