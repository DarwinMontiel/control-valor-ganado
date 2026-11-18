"""Datos de demostración: ``python -m app.seed``.

Tres proyectos pensados para mostrar cada lectura de EVM: uno con sobrecosto y retraso (el
ejemplo calculado a mano de docs/EVM_METHODOLOGY.md), uno favorable y uno con los casos borde.
Es idempotente: si un proyecto de demostración ya existe, no lo duplica.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.services import ActivityFields, ActivityService, ProjectFields, ProjectService
from app.infrastructure.database import get_session_factory
from app.infrastructure.models import ProjectModel

DEMO_CUTOFF = date(2026, 11, 17)


@dataclass(frozen=True)
class DemoProject:
    project: ProjectFields
    activities: tuple[ActivityFields, ...]


def _activity(name: str, bac: str, planned: str, actual: str, cost: str) -> ActivityFields:
    return ActivityFields(
        name=name,
        budget_at_completion=Decimal(bac),
        planned_progress=Decimal(planned),
        actual_progress=Decimal(actual),
        actual_cost=Decimal(cost),
    )


DEMO_PROJECTS = (
    DemoProject(
        project=ProjectFields(
            name="Portal de clientes",
            description="Sobrecosto y retraso. Es el ejemplo calculado a mano de la metodología.",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 2, 26),
            cutoff_date=DEMO_CUTOFF,
        ),
        activities=(
            _activity("Diseño", "10000000", "100", "100", "9000000"),
            _activity("Desarrollo", "20000000", "60", "40", "10000000"),
            _activity("Pruebas", "5000000", "20", "0", "0"),
        ),
    ),
    DemoProject(
        project=ProjectFields(
            name="Migración a la nube",
            description="Proyecto favorable: gasta menos de lo que avanza y va adelantado.",
            start_date=date(2026, 8, 3),
            end_date=date(2027, 1, 29),
            cutoff_date=DEMO_CUTOFF,
        ),
        activities=(
            _activity("Inventario de servidores", "8000000", "100", "100", "7200000"),
            _activity("Migración de bases de datos", "25000000", "50", "60", "13000000"),
            _activity("Pruebas de carga", "6000000", "10", "15", "800000"),
        ),
    ),
    DemoProject(
        project=ProjectFields(
            name="App móvil de pedidos",
            description="Casos especiales: avance sin costo, costo sin avance, trabajo adelantado "
            "y una actividad sin iniciar.",
            start_date=date(2026, 10, 5),
            end_date=date(2027, 4, 30),
            cutoff_date=DEMO_CUTOFF,
        ),
        activities=(
            _activity("Diseño UX", "6000000", "30", "30", "0"),
            _activity("Backend de pedidos", "15000000", "20", "0", "2500000"),
            _activity("Publicación en tiendas", "2000000", "0", "10", "300000"),
            _activity("Integración de pagos", "9000000", "0", "0", "0"),
        ),
    ),
)


def seed(session: Session) -> list[str]:
    """Crea los proyectos de demostración que falten. Devuelve los nombres creados."""
    existing = set(session.scalars(select(ProjectModel.name)))
    projects = ProjectService(session)
    activities = ActivityService(session)
    created = []
    for demo in DEMO_PROJECTS:
        if demo.project.name in existing:
            continue
        project_id = projects.create(demo.project).project.id
        for activity in demo.activities:
            activities.create(project_id, activity)
        created.append(demo.project.name)
    return created


def main() -> None:
    with get_session_factory()() as session, session.begin():
        created = seed(session)
    print(f"Proyectos de demostración creados: {len(created)}")


if __name__ == "__main__":
    main()
