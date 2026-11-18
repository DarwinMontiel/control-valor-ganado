# Cambios

## 1.0.1 · 2026-11-18

- `AI_PROCESS.md`: cómo usé la IA en el proyecto, qué acepté, qué ajusté y cómo verifiqué los números.

## 1.0.0 · 2026-11-17

Primera entrega.

- API REST `/api/v1` para crear, consultar, editar y eliminar proyectos y actividades, con Swagger en `/api-docs`.
- Motor EVM: PV, EV, CV, SV, CPI, SPI, EAC y VAC por actividad y consolidados por proyecto, con interpretación de CPI y SPI y casos borde explícitos.
- Semáforo con tolerancia del 5 % y aviso de EAC poco confiable con menos del 10 % de avance real.
- Alertas deterministas sobre los indicadores.
- Dashboard React:
  - Veredicto general del proyecto.
  - Índices con semáforo.
  - Tabla de actividades que se puede ordenar.
  - Gráfica PV / EV / AC.
- PostgreSQL con migraciones de Alembic y datos de ejemplo.
- Docker Compose y CI en GitHub Actions.
