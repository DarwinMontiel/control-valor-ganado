# Control de Valor Ganado

Herramienta interna para que un líder de proyecto registre el avance de sus actividades y sepa **de un vistazo** si su proyecto va bien o mal en costo y cronograma, con la metodología de Valor Ganado (Earned Value Management, PMI).

![Vista de un proyecto](docs/img/proyecto-light.png)

## Qué hace

- **Proyectos y actividades:** se pueden crear, consultar, editar y eliminar. Cada actividad registra su presupuesto (BAC), el avance planificado y el real a la fecha de corte, y el costo real (AC).
- **Indicadores:** PV, EV, CV, SV, CPI, SPI, EAC y VAC por actividad y consolidados por proyecto, con la interpretación de CPI y SPI. El consolidado suma las cifras base y recalcula los índices; no promedia.
- **Casos borde explícitos:** si un índice no se puede calcular (por ejemplo, CPI con AC = 0), la API devuelve `null` y un estado que lo explica. Nunca un 0 inventado.
- **Semáforo con tolerancia:** un CPI o SPI de 0,95 a 1 se ve en amarillo («En línea»), no en rojo. El estado de la API sigue siendo estricto.
- **EAC poco confiable:** con menos del 10 % de avance real, el costo final estimado se marca como poco confiable.
- **Alertas:** reglas fijas sobre los indicadores (CPI o SPI bajo 1, costo sin avance, avance sin costo, sobrecosto proyectado). Cada una dice qué indicador la disparó y con qué valor.
- **Dashboard:** veredicto general del proyecto, CPI y SPI con semáforo (siempre con texto y símbolo, no solo color), tabla de actividades que se puede ordenar y gráfica PV / EV / AC por actividad.
- **Swagger** en `/api-docs`: cada operación trae descripción, esquemas y códigos de error.

## Arranque rápido (Docker)

Requisitos: Docker con Compose.

```bash
docker compose up --build
```

| Servicio | URL |
|----------|-----|
| Dashboard | http://localhost:8080 |
| Swagger | http://localhost:8080/api-docs (o http://localhost:8000/api-docs) |
| Health check | http://localhost:8000/health |

Al arrancar, la API aplica las migraciones (el script de inicialización de la base de datos) y carga tres proyectos de ejemplo. Para no cargarlos: `SEED_DEMO_DATA=false docker compose up --build`.

## Desarrollo local sin Docker

Requisitos: Python 3.12+, Node 24+ y PostgreSQL 16+.

```bash
# 1. Base de datos
createdb valor_ganado

# 2. API
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp ../.env.example .env                              # ajuste DATABASE_URL
alembic upgrade head                                 # script de inicialización de la BD
python -m app.seed                                   # datos de ejemplo (opcional)
uvicorn app.main:app --reload                        # http://localhost:8000/api-docs

# 3. Web (otra terminal)
cd frontend
npm ci
npm run dev                                          # http://localhost:5173
```

### Variables de entorno

| Variable | Por defecto | Uso |
|----------|-------------|-----|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/valor_ganado` | Conexión de la API |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Orígenes permitidos en desarrollo |
| `TEST_DATABASE_URL` | `.../valor_ganado_test` | Base de datos de las pruebas de integración (se borra en cada ejecución) |
| `SEED_DEMO_DATA` | `true` (solo en Compose) | Carga los datos de ejemplo al arrancar |

## Pruebas y calidad

```bash
# Backend: unitarias + integración contra PostgreSQL, con cobertura mínima del 80 %
cd backend
createdb valor_ganado_test
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/valor_ganado_test pytest --cov
ruff check . && ruff format --check . && mypy

# Frontend
cd frontend
npm run typecheck && npm run lint && npm test && npm run build
```

| | Pruebas | Cobertura |
|-|---------|-----------|
| Backend | 89 (47 unitarias del dominio, 42 de integración) | 98,6 % total · 100 % del dominio |
| Frontend | 25 | — |

El CI (GitHub Actions) repite todo en cada PR y además construye las imágenes Docker. Detalle en [`docs/TEST_STRATEGY.md`](docs/TEST_STRATEGY.md).

## Arquitectura

```mermaid
flowchart LR
    W[React + TypeScript] -- /api/v1 --> A[FastAPI: rutas]
    A --> S[Casos de uso]
    S --> D[Motor EVM y alertas<br/>Python puro]
    S --> R[Repositorios SQLAlchemy]
    R --> P[(PostgreSQL)]
```

- El **motor EVM** (`backend/app/domain`) no depende de FastAPI ni de la base de datos, y se prueba en milisegundos.
- Las rutas solo traducen HTTP ↔ casos de uso. **No hay cálculos en los controladores.**
- El frontend **no calcula EVM**: presenta lo que devuelve la API. Hay una sola fuente de verdad.
- Montos en `Decimal` / `NUMERIC` de punta a punta. En JSON viajan como texto (`"36944444.44"`).

Más en [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`AI_PROCESS.md`](AI_PROCESS.md) | Mi proceso con IA |
| [`docs/EVM_METHODOLOGY.md`](docs/EVM_METHODOLOGY.md) | Fórmulas, casos borde y ejemplo calculado a mano |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Capas, modelo de datos y API |
| [`docs/TECH_STACK.md`](docs/TECH_STACK.md) | Qué elegí, qué descarté y por qué |
| [`docs/TEST_STRATEGY.md`](docs/TEST_STRATEGY.md) | Qué prueba cada capa |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Medidas y límites conocidos |
| [`docs/PLAN.md`](docs/PLAN.md) | Requisitos de Trycore, decisiones iniciales y fases |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Lo que quedó fuera y por qué |

## Estructura

```
backend/
  app/domain/          motor EVM, estados y alertas (Python puro)
  app/application/     casos de uso
  app/infrastructure/  SQLAlchemy, repositorios
  app/api/             rutas, esquemas y errores HTTP
  alembic/             migraciones (inicialización de la BD)
  tests/unit/          dominio
  tests/integration/   API y esquema contra PostgreSQL
frontend/
  src/api/             cliente y hooks de TanStack Query
  src/components/      tabla, gráfica, panel de indicadores, formularios
  src/pages/           lista de proyectos y vista de proyecto
docs/                  documentación técnica y capturas
```

## Flujo de trabajo

Gitflow: `main` (producción), `develop` (integración) y una rama `feature/*` por funcionalidad, integrada a `develop` con un Pull Request. La entrega pasa por `release/1.0.0` antes de llegar a `main`.

| Proyectos | Móvil | Swagger |
|-----------|-------|---------|
| ![Proyectos](docs/img/proyectos.png) | ![Móvil](docs/img/proyecto-movil.png) | ![Swagger](docs/img/swagger.png) |
