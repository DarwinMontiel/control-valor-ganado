"""Errores de los casos de uso."""

import uuid

from app.domain.errors import DomainError


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class ProjectNotFoundError(NotFoundError):
    code = "PROJECT_NOT_FOUND"

    def __init__(self, project_id: uuid.UUID) -> None:
        super().__init__(f"No existe el proyecto {project_id}.")


class ActivityNotFoundError(NotFoundError):
    code = "ACTIVITY_NOT_FOUND"

    def __init__(self, activity_id: uuid.UUID) -> None:
        super().__init__(f"No existe la actividad {activity_id}.")
