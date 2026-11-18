"""Tablas de la base de datos.

Los indicadores EVM no se guardan: se derivan de los cuatro campos de la actividad al leer, así
nunca quedan desactualizados.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base

NAME_MAX_LENGTH = 120
MONEY = Numeric(18, 2)
PERCENT = Numeric(5, 2)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProjectModel(TimestampMixin, Base):
    __tablename__ = "project"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_project_dates"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    cutoff_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())

    activities: Mapped[list["ActivityModel"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ActivityModel.created_at",
    )


class ActivityModel(TimestampMixin, Base):
    __tablename__ = "activity"
    __table_args__ = (
        CheckConstraint("budget_at_completion > 0", name="ck_activity_bac_positive"),
        CheckConstraint("actual_cost >= 0", name="ck_activity_ac_non_negative"),
        CheckConstraint(
            "planned_progress BETWEEN 0 AND 100", name="ck_activity_planned_progress_range"
        ),
        CheckConstraint(
            "actual_progress BETWEEN 0 AND 100", name="ck_activity_actual_progress_range"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    budget_at_completion: Mapped[Decimal] = mapped_column(MONEY)
    planned_progress: Mapped[Decimal] = mapped_column(PERCENT)
    actual_progress: Mapped[Decimal] = mapped_column(PERCENT)
    actual_cost: Mapped[Decimal] = mapped_column(MONEY)

    project: Mapped[ProjectModel] = relationship(back_populates="activities")
