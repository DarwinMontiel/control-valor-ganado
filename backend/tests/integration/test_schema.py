"""La base de datos protege sus invariantes aunque alguien salte la API."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.models import ActivityModel, ProjectModel

pytestmark = pytest.mark.integration


def _project(session: Session) -> uuid.UUID:
    project = ProjectModel(name="Portal")
    session.add(project)
    session.flush()
    return project.id


@pytest.mark.parametrize(
    "overrides",
    [
        {"budget_at_completion": Decimal("0")},
        {"planned_progress": Decimal("100.01")},
        {"actual_progress": Decimal("-1")},
        {"actual_cost": Decimal("-0.01")},
    ],
)
def test_check_constraints_reject_invalid_activity(
    session_factory: sessionmaker[Session], overrides: dict[str, Decimal]
) -> None:
    values = {
        "name": "Diseño",
        "budget_at_completion": Decimal("1000"),
        "planned_progress": Decimal("50"),
        "actual_progress": Decimal("40"),
        "actual_cost": Decimal("300"),
    } | overrides
    with session_factory() as session:
        session.add(ActivityModel(project_id=_project(session), **values))
        with pytest.raises(IntegrityError):
            session.flush()


def test_deleting_project_cascades_to_activities(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session, session.begin():
        project_id = _project(session)
        session.add(
            ActivityModel(
                project_id=project_id,
                name="Diseño",
                budget_at_completion=Decimal("1000"),
                planned_progress=Decimal("50"),
                actual_progress=Decimal("40"),
                actual_cost=Decimal("300"),
            )
        )
    with session_factory() as session, session.begin():
        session.delete(session.get(ProjectModel, project_id))
    with session_factory() as session:
        assert session.query(ActivityModel).count() == 0
