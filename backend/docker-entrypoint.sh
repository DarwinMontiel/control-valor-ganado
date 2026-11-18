#!/bin/sh
# Aplica las migraciones (script de inicialización de la base), carga los datos de
# demostración si se pide y arranca la API.
set -eu

alembic upgrade head

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python -m app.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
