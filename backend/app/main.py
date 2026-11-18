"""Punto de entrada de la API."""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.errors import register_error_handlers
from app.api.v1 import activities, projects
from app.core.config import get_settings
from app.infrastructure.database import get_session

API_DESCRIPTION = """
Control de proyectos con **Valor Ganado** (Earned Value Management, PMI).

Cada actividad registra su presupuesto (BAC), su avance planificado y real a la fecha de corte
y su costo real (AC). La API calcula PV, EV, CV, SV, CPI, SPI, EAC y VAC por actividad y
consolidados por proyecto, e interpreta CPI y SPI.

- Los montos viajan como texto decimal (`"1000.00"`) para no perder precisión.
- Un índice en `null` no se puede calcular (por ejemplo, CPI con AC = 0); el estado lo explica.
"""


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Valor Ganado API",
        version="1.0.1",
        description=API_DESCRIPTION,
        docs_url="/api-docs",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )
    register_error_handlers(app)
    app.include_router(projects.router, prefix=settings.api_prefix)
    app.include_router(activities.router, prefix=settings.api_prefix)

    @app.get("/health", tags=["Sistema"], summary="Estado del servicio y de la base de datos")
    def health(session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
        session.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
