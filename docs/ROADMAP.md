# Roadmap

Lo que dejé fuera de la versión 1.0.0 a propósito, en orden de valor.

| # | Capacidad | Por qué no entró | Cómo encajaría |
|---|-----------|------------------|----------------|
| 1 | **Cortes históricos** (snapshots por fecha de corte) | El reto pide el avance *a la fecha de corte*. Una serie histórica es otro modelo de datos y mezclarlo confundiría | Tabla `progress_snapshot(activity_id, cutoff_date, planned, actual, cost)`; el motor EVM no cambia porque recibe los mismos 4 valores. Permitiría la curva S |
| 2 | Autenticación y permisos por proyecto | Ver `SECURITY.md` | OIDC + una dependencia de FastAPI que entregue el usuario actual |
| 3 | E2E con Playwright | Prioricé las pruebas de cálculo y de contrato | Flujo: crear proyecto → 3 actividades → editar avance → comprobar indicadores |
| 4 | Exportar a CSV o Excel | Poco valor frente al riesgo para un día | Endpoint que reutilice `analyze_project` para exportar las mismas cifras |
| 5 | Escenarios de EAC | El reto define EAC = BAC / CPI. PMI tiene otras variantes (por ejemplo, AC + (BAC − EV) / (CPI × SPI)) | Una función por variante en `domain/evm.py`, mostradas como escenarios, nunca como resultado observado |
| 6 | Umbrales configurables | 0,90 (alertas), 5 % (tolerancia) y 10 % (EAC) son supuestos razonables, no reglas de una empresa | Llevar las constantes a la configuración |
| 7 | Moneda por proyecto | Todo está en COP | Campo `currency` en el proyecto y formato con `Intl` |
