# Stack tecnológico

Mi criterio: usar lo que Trycore prefiere (p. 4) y lo que mejor domino, y agregar una pieza solo si resuelve un problema concreto de este reto. Las versiones exactas están en `backend/pyproject.toml` y `frontend/package-lock.json`.

## Backend

| Pieza | Elección | Por qué | Descartado |
|-------|----------|---------|------------|
| Lenguaje | Python 3.12+ | Preferencia de Trycore y el lenguaje que más uso | Java/Spring: más ceremonia para un día |
| Framework | FastAPI | Genera OpenAPI a partir de los tipos; Swagger en `/api-docs` | Flask: OpenAPI manual |
| Validación | Pydantic v2 | Rangos 0–100, `Decimal` y errores 422 consistentes | — |
| ORM | SQLAlchemy 2.x (estilo tipado) | Consultas parametrizadas, mapeo claro | SQL crudo: más código repetido |
| Migraciones | Alembic | Es el script de inicialización de la base de datos | `create_all()`: no versiona el esquema |
| Base de datos | PostgreSQL 16 | Preferencia de Trycore; `NUMERIC` exacto y `CHECK` | SQLite: no maneja `NUMERIC` igual |
| Pruebas | pytest, pytest-cov, httpx, Hypothesis | Unitarias del dominio, propiedades e integración por endpoint | — |
| Calidad | Ruff (lint y formato, con reglas de complejidad, números mágicos y código comentado) y mypy estricto | Un linter configurado en el repo, como sugiere la p. 3 | flake8 + black + isort: tres herramientas para lo mismo |

## Frontend

| Pieza | Elección | Por qué | Descartado |
|-------|----------|---------|------------|
| Base | React 19 + TypeScript estricto (`noUncheckedIndexedAccess`) + Vite | Preferencia de Trycore; arranque rápido | Angular: más estructura de la que pide un dashboard |
| Estilos | Tailwind CSS 4 | Diseño consistente sin hoja de estilos a mano | Librerías de componentes: demasiado para 2 pantallas |
| Datos remotos | TanStack Query | Caché e invalidación: al editar una actividad se refrescan la tabla y los indicadores del proyecto | `useEffect` + `fetch` a mano |
| Formularios | React Hook Form + Zod | Validar 0–100 y montos ≥ 0 antes de llamar a la API | — |
| Gráficas | Recharts 3 (carga diferida) | Barras agrupadas PV/EV/AC en pocas líneas | ECharts: más potente, pero más pesado y no hace falta |
| Pruebas | Vitest + Testing Library | Mismo motor que Vite | Jest: configuración extra |
| Lint | oxlint | Rápido; reglas de React, import y unicorn; `--deny-warnings` en CI | ESLint: más lento, misma cobertura para este tamaño |

**El frontend no calcula EVM.** Solo da formato a lo que devuelve la API. Así hay una sola fuente de verdad, y no hay dos implementaciones de las fórmulas que puedan discrepar.

## Infraestructura

| Pieza | Elección | Nota |
|-------|----------|------|
| Contenedores | Docker Compose (PostgreSQL 16, API y nginx con la web) | `docker compose up --build` arranca todo, con migraciones y datos de ejemplo |
| CI | GitHub Actions | Lint, tipos, pruebas con un servicio PostgreSQL, cobertura con `fail_under = 80` y build de imágenes |
| Repositorio | GitHub (`DarwinMontiel/control-valor-ganado`) | Trycore necesita ver el historial |
