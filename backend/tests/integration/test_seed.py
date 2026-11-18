"""Los datos de demostración cubren las lecturas que se quieren mostrar."""

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.application.services import ProjectService
from app.domain.status import CostStatus, ScheduleStatus
from app.seed import DEMO_PROJECTS, seed

pytestmark = pytest.mark.integration


def test_seed_is_idempotent(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session, session.begin():
        first = seed(session)
    with session_factory() as session, session.begin():
        second = seed(session)

    assert len(first) == len(DEMO_PROJECTS)
    assert second == []


def test_demo_covers_every_reading(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session, session.begin():
        seed(session)
        page = ProjectService(session).list(offset=0, limit=10, search=None)

    projects = {item.project.name: item for item in page.items}
    activities = [a.indicators for item in page.items for a in item.activities]
    cost_statuses = {indicators.cost_status for indicators in activities}
    schedule_statuses = {indicators.schedule_status for indicators in activities}

    assert projects["Portal de clientes"].indicators.cost_status is CostStatus.OVER_BUDGET
    assert projects["Migración a la nube"].indicators.cost_status is CostStatus.UNDER_BUDGET
    assert projects["Migración a la nube"].indicators.schedule_status is ScheduleStatus.AHEAD
    assert set(CostStatus) <= cost_statuses | {CostStatus.ON_BUDGET}
    assert set(ScheduleStatus) <= schedule_statuses | {ScheduleStatus.ON_SCHEDULE}
