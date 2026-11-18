# Arquitectura

## Vista general

```mermaid
flowchart LR
    U[Líder de proyecto] --> W[Web React<br/>Dashboard]
    W -- JSON /api/v1 --> A[API FastAPI]
    A --> S[Servicios de aplicación]
    S --> D[Motor EVM<br/>dominio puro]
    S --> R[Repositorios SQLAlchemy]
    R --> P[(PostgreSQL)]
```

## Capas del backend

```
backend/app/
├── domain/          # Reglas EVM. Python puro: sin FastAPI, sin SQLAlchemy.
│   ├── evm.py       #   calculate_activity_indicators(), consolidate()
│   ├── status.py    #   estados, interpretación y banda de tolerancia
│   └── alerts.py    #   evaluate_alerts(): reglas fijas sobre los indicadores
├── application/     # Casos de uso: orquesta repositorios + dominio.
│   └── services.py  #   ProjectService, ActivityService, analyze_project()
├── infrastructure/  # SQLAlchemy, sesión, repositorios.
└── api/             # Rutas, esquemas Pydantic, manejo de errores.
    └── v1/
```

Regla de dependencias: `api → application → domain` y `application → infrastructure`. El dominio no importa nada de las otras capas, por eso lo pruebo sin servidor ni base de datos.

**Por qué no usé una arquitectura hexagonal completa, con puertos e interfaces:** con dos entidades y una sola base de datos, una interfaz de repositorio por entidad duplica código sin un beneficio que se pueda mostrar. El límite que sí importa es el del dominio EVM, y ese se mantiene.

## Modelo de datos

```mermaid
erDiagram
    PROJECT ||--o{ ACTIVITY : contiene
    PROJECT {
        uuid id PK
        varchar name
        text description
        date start_date
        date end_date
        date cutoff_date "fecha de corte, por defecto hoy"
        timestamptz created_at
        timestamptz updated_at
    }
    ACTIVITY {
        uuid id PK
        uuid project_id FK
        varchar name
        numeric budget_at_completion "BAC > 0"
        numeric planned_progress "0..100"
        numeric actual_progress "0..100"
        numeric actual_cost "AC >= 0"
        timestamptz created_at
        timestamptz updated_at
    }
```

- Los indicadores **no se guardan**: se calculan al leer. Son derivados de 4 campos, y guardarlos permitiría que quedaran desactualizados.
- `ON DELETE CASCADE` de proyecto a actividades. La interfaz pide confirmación antes de borrar.
- Montos en `NUMERIC(18,2)` y porcentajes en `NUMERIC(5,2)`, con `CHECK` en la base de datos además de la validación de Pydantic.

## Flujo de un cálculo

```mermaid
sequenceDiagram
    participant W as Web
    participant R as Ruta GET /projects/{id}
    participant S as ProjectService
    participant Repo as Repositorio
    participant E as Motor EVM
    W->>R: GET
    R->>S: get(id)
    S->>Repo: actividades del proyecto
    Repo-->>S: filas
    S->>E: calculate_activity_indicators(cada actividad)
    S->>E: consolidate(actividades)
    S->>E: evaluate_alerts(proyecto y cada actividad)
    E-->>S: indicadores, estados y alertas
    S-->>R: ProjectAnalysis
    R-->>W: JSON (montos como texto decimal)
```

## API

| Método | Ruta | Respuesta |
|--------|------|-----------|
| POST | `/api/v1/projects` | 201 Proyecto |
| GET | `/api/v1/projects` | 200 Lista paginada con los indicadores consolidados de cada proyecto |
| GET | `/api/v1/projects/{id}` | 200 Proyecto + consolidado + actividades con indicadores + alertas · 404 |
| PUT | `/api/v1/projects/{id}` | 200 · 404 · 422 |
| DELETE | `/api/v1/projects/{id}` | 204 · 404 |
| POST | `/api/v1/projects/{id}/activities` | 201 · 404 · 422 |
| GET | `/api/v1/projects/{id}/activities` | 200 · 404 |
| GET | `/api/v1/activities/{id}` | 200 · 404 |
| PUT | `/api/v1/activities/{id}` | 200 · 404 · 422 |
| DELETE | `/api/v1/activities/{id}` | 204 · 404 |
| GET | `/health` | 200 |

Todos los errores usan el mismo formato: `{"error": {"code": "PROJECT_NOT_FOUND", "message": "...", "details": [...]}}`.
