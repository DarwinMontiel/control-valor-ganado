"""Acceso a datos. Solo consultas: ninguna regla de negocio vive aquí."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.models import ActivityModel, ProjectModel


class ProjectRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: ProjectModel) -> ProjectModel:
        self._session.add(project)
        self._session.flush()
        self._session.refresh(project)
        return project

    def get(self, project_id: uuid.UUID) -> ProjectModel | None:
        statement = (
            select(ProjectModel)
            .options(selectinload(ProjectModel.activities))
            .where(ProjectModel.id == project_id)
        )
        return self._session.scalars(statement).one_or_none()

    def list(
        self, *, offset: int, limit: int, search: str | None
    ) -> tuple[list[ProjectModel], int]:
        filters = [] if not search else [ProjectModel.name.ilike(f"%{search}%")]
        total = self._session.scalar(select(func.count(ProjectModel.id)).where(*filters)) or 0
        statement = (
            select(ProjectModel)
            .options(selectinload(ProjectModel.activities))
            .where(*filters)
            .order_by(ProjectModel.created_at.desc(), ProjectModel.id)
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.scalars(statement)), total

    def save(self, project: ProjectModel) -> ProjectModel:
        self._session.flush()
        self._session.refresh(project)
        return project

    def delete(self, project: ProjectModel) -> None:
        self._session.delete(project)
        self._session.flush()


class ActivityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, activity: ActivityModel) -> ActivityModel:
        self._session.add(activity)
        self._session.flush()
        self._session.refresh(activity)
        return activity

    def get(self, activity_id: uuid.UUID) -> ActivityModel | None:
        return self._session.get(ActivityModel, activity_id)

    def list_for_project(self, project_id: uuid.UUID) -> list[ActivityModel]:
        statement = (
            select(ActivityModel)
            .where(ActivityModel.project_id == project_id)
            .order_by(ActivityModel.created_at, ActivityModel.id)
        )
        return list(self._session.scalars(statement))

    def save(self, activity: ActivityModel) -> ActivityModel:
        self._session.flush()
        self._session.refresh(activity)
        return activity

    def delete(self, activity: ActivityModel) -> None:
        self._session.delete(activity)
        self._session.flush()
