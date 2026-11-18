"""Fixtures de integración contra un PostgreSQL real.

La URL sale de TEST_DATABASE_URL. El esquema se crea con las migraciones de Alembic (no con
``create_all``), así las pruebas también validan la migración.
"""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient

from app.infrastructure.database import get_session
from app.main import create_app

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:5432/valor_ganado_test"
)


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    config = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    config.attributes["database_url"] = database_url
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    test_engine = create_engine(database_url)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE project, activity CASCADE"))
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    def override_session() -> Iterator[Session]:
        with session_factory() as session, session.begin():
            yield session

    application = create_app()
    application.dependency_overrides[get_session] = override_session
    with TestClient(application) as test_client:
        yield test_client
