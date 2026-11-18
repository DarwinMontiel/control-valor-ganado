"""Casos de uso: coordinan los repositorios con el motor EVM.

Los controladores HTTP solo llaman a estos servicios; aquí no hay nada de HTTP.
"""

import uuid
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.application.errors import ActivityNotFoundError, ProjectNotFoundError
from app.domain.alerts import Alert, AlertSeverity, evaluate_alerts
from app.domain.evm import (
    ActivityProgress,
    EvmIndicators,
    calculate_activity_indicators,
    consolidate,
)
from app.infrastructure.models import ActivityModel, ProjectModel
from app.infrastructure.repositories import ActivityRepository, ProjectRepository


@dataclass(frozen=True, slots=True)
class ProjectFields:
    name: str
    description: str | None
    start_date: date | None
    end_date: date | None
    cutoff_date: date | None


@dataclass(frozen=True, slots=True)
class ActivityFields:
    name: str
    budget_at_completion: Decimal
    planned_progress: Decimal
    actual_progress: Decimal
    actual_cost: Decimal

    def to_progress(self) -> ActivityProgress:
        """Valida las reglas de negocio antes de tocar la base de datos."""
        return ActivityProgress(
            budget_at_completion=self.budget_at_completion,
            planned_progress=self.planned_progress,
            actual_progress=self.actual_progress,
            actual_cost=self.actual_cost,
        )


@dataclass(frozen=True, slots=True)
class ActivityAnalysis:
    activity: ActivityModel
    indicators: EvmIndicators


@dataclass(frozen=True, slots=True)
class ScopedAlert:
    """Alerta con el alcance que la originó: el proyecto completo o una actividad."""

    alert: Alert
    activity_id: uuid.UUID | None
    scope_name: str


@dataclass(frozen=True, slots=True)
class ProjectAnalysis:
    project: ProjectModel
    indicators: EvmIndicators
    activities: list[ActivityAnalysis]
    alerts: list[ScopedAlert]


@dataclass(frozen=True, slots=True)
class ProjectPage:
    items: list[ProjectAnalysis]
    total: int


def analyze_project(project: ProjectModel) -> ProjectAnalysis:
    progress = [_progress_of(activity) for activity in project.activities]
    indicators = consolidate(progress)
    activities = [
        ActivityAnalysis(activity=activity, indicators=calculate_activity_indicators(item))
        for activity, item in zip(project.activities, progress, strict=True)
    ]
    return ProjectAnalysis(
        project=project,
        indicators=indicators,
        activities=activities,
        alerts=_collect_alerts(project, indicators, activities),
    )


def _collect_alerts(
    project: ProjectModel, indicators: EvmIndicators, activities: list[ActivityAnalysis]
) -> list[ScopedAlert]:
    """Primero las del proyecto, luego las de cada actividad; las de severidad alta arriba."""
    scoped = [ScopedAlert(alert, None, project.name) for alert in evaluate_alerts(indicators)]
    for item in activities:
        scoped += [
            ScopedAlert(alert, item.activity.id, item.activity.name)
            for alert in evaluate_alerts(item.indicators)
        ]
    return sorted(scoped, key=lambda item: item.alert.severity is not AlertSeverity.HIGH)


def analyze_activity(activity: ActivityModel) -> ActivityAnalysis:
    return ActivityAnalysis(
        activity=activity, indicators=calculate_activity_indicators(_progress_of(activity))
    )


def _progress_of(activity: ActivityModel) -> ActivityProgress:
    return ActivityProgress(
        budget_at_completion=activity.budget_at_completion,
        planned_progress=activity.planned_progress,
        actual_progress=activity.actual_progress,
        actual_cost=activity.actual_cost,
    )


class ProjectService:
    def __init__(self, session: Session) -> None:
        self._projects = ProjectRepository(session)

    def create(self, fields: ProjectFields) -> ProjectAnalysis:
        project = self._projects.add(ProjectModel(**_without_empty_cutoff(fields)))
        return analyze_project(self._require(project.id))

    def get(self, project_id: uuid.UUID) -> ProjectAnalysis:
        return analyze_project(self._require(project_id))

    def list(self, *, offset: int, limit: int, search: str | None) -> ProjectPage:
        projects, total = self._projects.list(offset=offset, limit=limit, search=search)
        return ProjectPage(items=[analyze_project(project) for project in projects], total=total)

    def update(self, project_id: uuid.UUID, fields: ProjectFields) -> ProjectAnalysis:
        project = self._require(project_id)
        for name, value in _without_empty_cutoff(fields).items():
            setattr(project, name, value)
        return analyze_project(self._projects.save(project))

    def delete(self, project_id: uuid.UUID) -> None:
        self._projects.delete(self._require(project_id))

    def _require(self, project_id: uuid.UUID) -> ProjectModel:
        project = self._projects.get(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project


class ActivityService:
    def __init__(self, session: Session) -> None:
        self._projects = ProjectRepository(session)
        self._activities = ActivityRepository(session)

    def create(self, project_id: uuid.UUID, fields: ActivityFields) -> ActivityAnalysis:
        self._require_project(project_id)
        fields.to_progress()
        activity = self._activities.add(ActivityModel(project_id=project_id, **asdict(fields)))
        return analyze_activity(activity)

    def list_for_project(self, project_id: uuid.UUID) -> list[ActivityAnalysis]:
        self._require_project(project_id)
        return [analyze_activity(item) for item in self._activities.list_for_project(project_id)]

    def get(self, activity_id: uuid.UUID) -> ActivityAnalysis:
        return analyze_activity(self._require(activity_id))

    def update(self, activity_id: uuid.UUID, fields: ActivityFields) -> ActivityAnalysis:
        activity = self._require(activity_id)
        fields.to_progress()
        for name, value in asdict(fields).items():
            setattr(activity, name, value)
        return analyze_activity(self._activities.save(activity))

    def delete(self, activity_id: uuid.UUID) -> None:
        self._activities.delete(self._require(activity_id))

    def _require(self, activity_id: uuid.UUID) -> ActivityModel:
        activity = self._activities.get(activity_id)
        if activity is None:
            raise ActivityNotFoundError(activity_id)
        return activity

    def _require_project(self, project_id: uuid.UUID) -> None:
        if self._projects.get(project_id) is None:
            raise ProjectNotFoundError(project_id)


def _without_empty_cutoff(fields: ProjectFields) -> dict[str, object]:
    """Si no se envía fecha de corte, la base de datos usa la fecha del día."""
    values = asdict(fields)
    if values["cutoff_date"] is None:
        del values["cutoff_date"]
    return values
