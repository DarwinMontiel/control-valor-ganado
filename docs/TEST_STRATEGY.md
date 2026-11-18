# Estrategia de pruebas

Mi regla: **una prueba vale si fallaría ante un número incorrecto.** No me sirven las que solo comprueban que una función "devuelve algo".

## Qué prueba cada capa

| Capa | Herramienta | Qué demuestra | Cantidad |
|------|-------------|---------------|----------|
| Dominio EVM | pytest | Cada fórmula contra valores **calculados a mano**, todos los casos borde y la consolidación ponderada | 21 |
| Tolerancia y EAC | pytest | Límites exactos de la banda (0,9499 / 0,95 / 1,00) y del 10 % de avance (9,99 % frente a 10 %), con los datos de la demo | 13 |
| Propiedades | Hypothesis | Invariantes con miles de entradas aleatorias: CV = EV − AC, las sumas consolidadas, estado coherente con el signo de la variación, EAC = BAC × AC / EV | 3 |
| Alertas | pytest | Cada regla, el umbral 0,90 en su límite exacto y que los proyectos sanos no generen alertas | 10 |
| Esquema | pytest + PostgreSQL | Las restricciones `CHECK` y el borrado en cascada funcionan aunque alguien salte la API. El esquema se crea con la migración real | 5 |
| Contrato HTTP | TestClient + PostgreSQL | Todos los endpoints: forma de la respuesta, códigos 201/204/404/422 y formato de error. Una prueba recorre el OpenAPI y exige resumen, 404 y 422 donde corresponde | 35 |
| Datos demo | pytest + PostgreSQL | Idempotencia y que aparezcan todos los estados | 2 |
| Frontend | Vitest + Testing Library | Formato es-CO, "—" en lugar de 0, ordenamiento con nulos al final, validación del formulario, semáforo con tolerancia, aviso de EAC y veredicto general | 25 |

## Decisiones

- **PostgreSQL real, no SQLite**, en las pruebas de integración: `NUMERIC`, `CHECK` y la cascada se comportan distinto en SQLite.
- **Las pruebas crean el esquema con Alembic** (`downgrade base` + `upgrade head`). Así la migración se prueba en cada ejecución.
- **El ejemplo de referencia se repite en tres capas** (dominio, API y datos de prueba del frontend) con las mismas cifras: 0,9474 / 0,7826 / 36.944.444,44.
- **Hypothesis encontró un caso que las pruebas de ejemplo no veían** (ver `EVM_METHODOLOGY.md`, sección Precisión). Ese caso tiene su propia prueba de regresión.

## Cobertura

`fail_under = 80` en `pyproject.toml`: la ejecución falla por debajo de ese mínimo. Hoy la cobertura es del 98,6 % en total y del 100 % en `app/domain`.

Lo que no está cubierto:
- La fábrica de sesiones de producción, que en las pruebas se reemplaza.
- El manejador de `InvalidActivityError`: Pydantic rechaza esos datos antes, así que queda solo como red de seguridad.

## Lo que falta

- No hay pruebas E2E con navegador (Playwright). El flujo completo lo verifico a mano: crear, editar el avance y ver cómo se recalculan los indicadores.
- No hay pruebas automáticas de accesibilidad (axe).
