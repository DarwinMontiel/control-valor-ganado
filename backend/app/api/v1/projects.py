"""Rutas de proyectos. Solo traducen HTTP ↔ casos de uso."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.errors import NOT_FOUND_RESPONSE, VALIDATION_RESPONSE
from app.api.v1.schemas import ProjectDetailOut, ProjectIn, ProjectOut, ProjectPageOut
from app.application.services import ProjectService
from app.infrastructure.database import get_session

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

router = APIRouter(prefix="/projects", tags=["Proyectos"])


def get_project_service(session: Annotated[Session, Depends(get_session)]) -> ProjectService:
    return ProjectService(session)


Service = Annotated[ProjectService, Depends(get_project_service)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear un proyecto",
    responses={422: VALIDATION_RESPONSE},
)
def create_project(payload: ProjectIn, service: Service) -> ProjectDetailOut:
    return ProjectDetailOut.from_analysis(service.create(payload.to_fields()))


@router.get(
    "",
    summary="Listar proyectos",
    description="Lista paginada, del más reciente al más antiguo, con los indicadores "
    "consolidados de cada proyecto.",
    responses={422: VALIDATION_RESPONSE},
)
def list_projects(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=120, description="Filtra por nombre.")] = None,
) -> ProjectPageOut:
    page = service.list(offset=offset, limit=limit, search=search)
    return ProjectPageOut(
        items=[ProjectOut.from_analysis(item) for item in page.items],
        total=page.total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{project_id}",
    summary="Consultar un proyecto",
    description="Devuelve el proyecto, sus indicadores consolidados y cada actividad con sus "
    "propios indicadores.",
    responses={404: NOT_FOUND_RESPONSE},
)
def get_project(project_id: uuid.UUID, service: Service) -> ProjectDetailOut:
    return ProjectDetailOut.from_analysis(service.get(project_id))


@router.put(
    "/{project_id}",
    summary="Editar un proyecto",
    responses={404: NOT_FOUND_RESPONSE, 422: VALIDATION_RESPONSE},
)
def update_project(project_id: uuid.UUID, payload: ProjectIn, service: Service) -> ProjectDetailOut:
    return ProjectDetailOut.from_analysis(service.update(project_id, payload.to_fields()))


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un proyecto",
    description="Elimina el proyecto y todas sus actividades.",
    responses={404: NOT_FOUND_RESPONSE},
)
def delete_project(project_id: uuid.UUID, service: Service) -> None:
    service.delete(project_id)
