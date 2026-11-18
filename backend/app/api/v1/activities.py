"""Rutas de actividades. Solo traducen HTTP ↔ casos de uso."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import NOT_FOUND_RESPONSE, VALIDATION_RESPONSE
from app.api.v1.schemas import ActivityIn, ActivityOut
from app.application.services import ActivityService
from app.infrastructure.database import get_session

router = APIRouter(tags=["Actividades"])


def get_activity_service(session: Annotated[Session, Depends(get_session)]) -> ActivityService:
    return ActivityService(session)


Service = Annotated[ActivityService, Depends(get_activity_service)]


@router.post(
    "/projects/{project_id}/activities",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una actividad",
    description="Crea la actividad y devuelve sus indicadores EVM calculados.",
    responses={404: NOT_FOUND_RESPONSE, 422: VALIDATION_RESPONSE},
)
def create_activity(project_id: uuid.UUID, payload: ActivityIn, service: Service) -> ActivityOut:
    return ActivityOut.from_analysis(service.create(project_id, payload.to_fields()))


@router.get(
    "/projects/{project_id}/activities",
    summary="Listar las actividades de un proyecto",
    responses={404: NOT_FOUND_RESPONSE},
)
def list_activities(project_id: uuid.UUID, service: Service) -> list[ActivityOut]:
    return [ActivityOut.from_analysis(item) for item in service.list_for_project(project_id)]


@router.get(
    "/activities/{activity_id}",
    summary="Consultar una actividad",
    responses={404: NOT_FOUND_RESPONSE},
)
def get_activity(activity_id: uuid.UUID, service: Service) -> ActivityOut:
    return ActivityOut.from_analysis(service.get(activity_id))


@router.put(
    "/activities/{activity_id}",
    summary="Editar una actividad",
    description="Reemplaza los datos de la actividad (por ejemplo, el avance a una nueva "
    "fecha de corte) y devuelve los indicadores recalculados.",
    responses={404: NOT_FOUND_RESPONSE, 422: VALIDATION_RESPONSE},
)
def update_activity(activity_id: uuid.UUID, payload: ActivityIn, service: Service) -> ActivityOut:
    return ActivityOut.from_analysis(service.update(activity_id, payload.to_fields()))


@router.delete(
    "/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una actividad",
    responses={404: NOT_FOUND_RESPONSE},
)
def delete_activity(activity_id: uuid.UUID, service: Service) -> None:
    service.delete(activity_id)
