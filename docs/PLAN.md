# Plan

## Qué pide Trycore

| # | Requisito | Página del PDF |
|---|-----------|---------------|
| R1 | API REST para crear, editar y eliminar proyectos y actividades | 2 |
| R2 | Cada actividad registra: nombre, BAC, % planificado, % real y AC | 2 |
| R3 | Calcular PV, EV, CV, SV, CPI, SPI, EAC y VAC por actividad y consolidados por proyecto | 2 |
| R4 | La API devuelve la interpretación de CPI y SPI (bajo/sobre presupuesto, adelantado/atrasado) | 2–3 |
| R5 | Dashboard: ingresar y editar actividades y ver el resultado en tiempo real | 3 |
| R6 | Tabla de actividades con indicadores, consolidados del proyecto, indicación visual de CPI/SPI y gráfica PV vs EV vs AC | 3 |
| R7 | Pruebas unitarias del cálculo con casos borde (AC = 0, sin actividades, avance real 0); cobertura ≥ 80 % en la capa de negocio | 3 |
| R8 | Una prueba de integración por endpoint que valide el contrato | 3 |
| R9 | Cero code smells; linter configurado en el repo; nada de lógica de negocio en los controladores | 3 |
| R10 | Gitflow: main, develop, feature/*, al menos un release/*, PR por feature, commits en imperativo | 3 |
| R11 | OpenAPI en `/api-docs` o `/swagger-ui` con descripción, esquemas y errores | 3 |
| R12 | README con instrucciones y script de inicialización de la base de datos | 4 |
| R13 | `AI_PROCESS.md` | 4 |
| R14 | Video de máximo 10 minutos | 4–5 |

## Decisiones iniciales

| Decisión | Elegí | Alternativas | Por qué |
|----------|-------|--------------|---------|
| Stack | Python (FastAPI) + React, con PostgreSQL | Java/Spring + Angular; Python + Angular | Es lo que más uso y lo que mejor puedo explicar. FastAPI genera el Swagger que Trycore valora |
| Alcance | Lo pedido + pocos extras | Solo lo obligatorio; muchas funciones adicionales | Lo que más pesa es el video y el proceso. Prefiero pocas cosas bien hechas y entendidas |
| Nombre | `control-valor-ganado` | `evm-tracker`, `trycore-evm` | Dice qué hace |

Extras, solo si lo obligatorio está terminado: datos de ejemplo para la demo, alertas y arranque con Docker.

## Fases

| Fase | Qué hago | La cierro cuando |
|------|----------|------------------|
| 0 | Plan y decisiones iniciales | Este documento |
| 1 | Aprender EVM y validar las fórmulas a mano | Calculo un ejemplo sin ayuda y coincide |
| 2 | Motor de cálculo con pruebas | Las pruebas usan cifras calculadas a mano |
| 3 | Base de datos y API REST | Un test de integración por endpoint y Swagger completo |
| 4 | Dashboard | Edito una actividad y veo cómo cambian los indicadores |
| 5 | Calidad: linter, CI y extras | CI en verde |
| 6 | Entrega: release, README y video | Checklist de Trycore completo |
