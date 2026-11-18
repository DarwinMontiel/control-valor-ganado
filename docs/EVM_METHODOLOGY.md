# Metodología EVM

Cómo calcula el sistema cada indicador y qué hace en los casos borde.

## Las cuatro cifras base

| Sigla | Pregunta que responde |
|-------|----------------------|
| **BAC** | ¿Cuánto cuesta la actividad completa, según el plan? |
| **PV** | ¿Cuánto trabajo, en dinero, debería estar hecho a la fecha de corte? `PV = %plan/100 × BAC` |
| **EV** | ¿Cuánto trabajo, en dinero, está hecho de verdad? `EV = %real/100 × BAC` |
| **AC** | ¿Cuánto se ha gastado de verdad? |

La idea clave: **EV es la cifra que se compara contra las otras dos.**
- EV contra AC es el costo: ¿lo hecho costó lo que debía?
- EV contra PV es el cronograma: ¿se hizo lo que tocaba?

Con el ejemplo del propio documento de Trycore, gastar el 60 % del presupuesto con el 40 % del trabajo hecho: con BAC = 100, EV = 40 y AC = 60, así que CPI = 0,67. Por cada peso gastado se obtienen 67 centavos de trabajo.

## Indicadores derivados

| Indicador | Fórmula | Lectura |
|-----------|---------|---------|
| CV | EV − AC | > 0 ahorro · < 0 sobrecosto |
| SV | EV − PV | > 0 adelanto · < 0 retraso (en dinero, no en días) |
| CPI | EV / AC | > 1 bajo presupuesto · = 1 en presupuesto · < 1 sobre presupuesto |
| SPI | EV / PV | > 1 adelantado · = 1 a tiempo · < 1 atrasado |
| EAC | BAC / CPI | Costo final si se mantiene la eficiencia actual. Equivale a BAC × AC / EV |
| VAC | BAC − EAC | > 0 terminará por debajo del presupuesto · < 0 por encima |

## Consolidación por proyecto

Sumo BAC, PV, EV y AC de las actividades y aplico de nuevo las fórmulas. **No promedio** los CPI ni los SPI.

Un promedio simple le da el mismo peso a una actividad de 1 millón que a una de 20 millones. El índice calculado sobre las sumas pondera cada actividad por su tamaño, que es lo que le importa al presupuesto.

## Casos borde

Regla general: **si un índice no se puede calcular, la API devuelve `null` y un estado explícito. Nunca un 0 inventado.**

| # | Situación | CPI | SPI | EAC / VAC | Decisión |
|---|-----------|-----|-----|-----------|----------|
| 1 | AC = 0 y EV = 0 (no ha empezado) | `null` | según PV | `null` | Estado de costo `NOT_STARTED` |
| 2 | AC = 0 y EV > 0 (avance sin costo registrado) | `null` (sería infinito) | según PV | `null` | Estado `NOT_CALCULABLE`; posible dato faltante |
| 3 | PV = 0 y EV = 0 | según AC | `null` | — | Estado de cronograma `NOT_STARTED` |
| 4 | PV = 0 y EV > 0 (trabajo hecho antes de lo planeado) | según AC | `null` (sería infinito) | — | `AHEAD` sin índice numérico |
| 5 | AC > 0 y EV = 0 (se gastó y no hay avance) | 0 | según PV | `null`: BAC / 0 | El CPI existe (es 0), pero el EAC no |
| 6 | Proyecto sin actividades | `null` | `null` | `null` | Totales en 0; ambos estados `NOT_STARTED` y `activity_count = 0` |
| 7 | BAC = 0 | — | — | — | Se rechaza en la entrada (422): una actividad sin presupuesto no se puede medir con EVM |
| 8 | AC > BAC | normal | normal | normal | Válido: es un sobrecosto real; se genera alerta |
| 9 | % fuera de 0–100 | — | — | — | Se rechaza (422) |

**Por qué el caso 2 es `NOT_CALCULABLE` y el 4 es `AHEAD`:** hacer trabajo antes de lo planeado es posible. Avanzar sin gastar nada casi siempre significa que falta cargar el costo, y no quiero decirle al líder que va "bajo presupuesto" por un dato faltante.

**El estado sale de las variaciones, no del índice redondeado.** CPI > 1 equivale a EV > AC cuando AC > 0. Comparar EV con AC evita que un CPI de 0,99996 (que se muestra como 1,0000) se lea como "en presupuesto" o al revés.

### Semáforo con tolerancia

El estado (`cost_status`, `schedule_status`) es estricto: un CPI de 0,99 es «sobre presupuesto», como dice la definición de EVM. Pero en pantalla un 0,99 no debe verse igual de grave que un 0,60. Por eso la API agrega una banda:

| Índice | Banda | Semáforo |
|--------|-------|----------|
| ≥ 1 | `FAVORABLE` | Verde |
| de 0,95 a menos de 1 | `WITHIN_TOLERANCE` | Amarillo, «En línea» |
| < 0,95 | `UNFAVORABLE` | Rojo |
| no calculable | `NOT_AVAILABLE` | Según el estado |

La tolerancia solo suaviza las desviaciones desfavorables: un índice de 1,00 o mayor siempre es verde.

### EAC poco confiable

EAC = BAC / CPI supone que el resto del trabajo se hará con la eficiencia actual. Con muy poco avance, esa eficiencia todavía no es representativa. En la demo «App móvil de pedidos», una sola actividad que gastó 2,5 M sin avanzar lleva el EAC a 44,8 M frente a 32 M de presupuesto, con apenas el 6,25 % del trabajo hecho.

Por eso, si el avance real (EV / BAC) es **menor al 10 %**, la API marca `estimate_is_reliable = false` y el dashboard muestra «Poco confiable» junto al EAC y al VAC. La fórmula no cambia; solo se advierte.

### Precisión

- Todo en `Decimal`; en PostgreSQL, `NUMERIC`.
- PV, EV, AC y BAC se redondean a centavos (`ROUND_HALF_UP`) **antes** de derivar el resto. Las variaciones, los índices y los estados salen de esas cifras, las mismas que ve el usuario.
- Los índices van a 4 decimales.
- EAC se calcula como BAC × AC / EV para no arrastrar el redondeo del CPI.

Esta regla nació de un caso que encontró una prueba de propiedades (Hypothesis): una actividad con BAC = 0,01 y 0,01 % planificado. PV valía 0,000001 y se mostraba como 0,00, pero el estado decía "Atrasado" y SV salía como `-0.00`.

## Ejemplo verificado a mano

Proyecto "Portal de clientes" (cifras en COP):

| Actividad | BAC | % plan | % real | AC | PV | EV | CV | SV | CPI | SPI | EAC | VAC |
|-----------|----:|------:|------:|---:|---:|---:|---:|---:|----:|----:|----:|----:|
| A. Diseño | 10.000.000 | 100 | 100 | 9.000.000 | 10.000.000 | 10.000.000 | 1.000.000 | 0 | 1,1111 | 1,0000 | 9.000.000 | 1.000.000 |
| B. Desarrollo | 20.000.000 | 60 | 40 | 10.000.000 | 12.000.000 | 8.000.000 | −2.000.000 | −4.000.000 | 0,8000 | 0,6667 | 25.000.000 | −5.000.000 |
| C. Pruebas | 5.000.000 | 20 | 0 | 0 | 1.000.000 | 0 | 0 | −1.000.000 | — | 0,0000 | — | — |
| **Proyecto** | **35.000.000** | | | **19.000.000** | **23.000.000** | **18.000.000** | **−1.000.000** | **−5.000.000** | **0,9474** | **0,7826** | **36.944.444,44** | **−1.944.444,44** |

Lectura: el proyecto va sobre presupuesto (CPI < 1) y atrasado (SPI < 1). Si sigue así, costará unos 1,94 millones más de lo planeado.

Comprobación de la regla de consolidación: el promedio simple de los CPI calculables sería (1,1111 + 0,8000) / 2 = **0,9556**, distinto del **0,9474** correcto. Este caso tiene su propia prueba.
