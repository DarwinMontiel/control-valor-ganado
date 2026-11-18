# Mi proceso con IA

**Proyecto:** Control de Valor Ganado · Prueba técnica Ingeniero de Desarrollo, Trycore Colombia
**Repositorio:** https://github.com/DarwinMontiel/control-valor-ganado

## 1. Resumen del proceso

Utilicé inteligencia artificial como apoyo principal durante la construcción del proyecto, especialmente para acelerar la implementación, estructurar las pruebas y preparar la documentación.

Mi participación se concentró en definir el alcance, orientar el desarrollo, estudiar la metodología de Valor Ganado, revisar las propuestas técnicas y validar que los resultados respondieran a los requisitos de la prueba. También evalué las decisiones que afectaban la interpretación de los indicadores y definí ajustes cuando la solución inicial no ofrecía la lectura que consideraba más adecuada para el usuario.

La IA fue una herramienta de apoyo para implementar y explorar alternativas; la revisión del resultado y las decisiones sobre qué aceptar, ajustar o descartar hicieron parte de mi responsabilidad.

## 2. Herramientas

| Herramienta | Para qué la usé |
|-------------|-----------------|
| ChatGPT | Analizar el PDF de la prueba y preparar un primer prompt de arranque. |
| Claude Code (app de escritorio de Claude) | Apoyar la implementación del backend, frontend, pruebas, Docker, CI y documentación, además de tareas de Git y GitHub. |

FastAPI, React, PostgreSQL, pytest, Hypothesis, Ruff, mypy y GitHub Actions son herramientas de desarrollo utilizadas en el proyecto, no herramientas de IA. El detalle está en `docs/TECH_STACK.md`.

## 3. Cómo fue el proceso, en orden

### 3.1 Arranque: definir un alcance viable

Le entregué a Claude Code el PDF de la prueba y un prompt inicial que había preparado con ChatGPT. Ese primer planteamiento contemplaba una solución más amplia, denominada «EVM Intelligence Platform», con capacidades adicionales a las solicitadas.

Durante el arranque, Claude Code me consultó tres aspectos:

| Pregunta | Decisión |
|----------|----------|
| ¿Cuánta autonomía darle a la herramienta? | «Autónomo». |
| ¿Qué alcance implementar? | «Obligatorio + 3 extras», en lugar de desarrollar toda la plataforma inicialmente propuesta. |
| ¿El repositorio debía ser público? | «Sí, público, ahora». |

Elegí limitar el alcance a los requisitos principales y algunos extras. La razón fue práctica: priorizar una solución que pudiera revisar, probar y explicar dentro del tiempo disponible, evitando agregar funcionalidades que no aportaran proporcionalmente al objetivo de la prueba.

### 3.2 Construcción e implementación

Claude Code apoyó la implementación del motor de Valor Ganado, la API, el dashboard, las pruebas y la configuración de Docker. Después revisé esas decisiones de diseño y su correspondencia con los requisitos.

Entre las decisiones técnicas revisadas estuvieron:

- separar el motor de cálculo (`backend/app/domain`) de FastAPI y de la persistencia;
- utilizar `Decimal` para los cálculos monetarios;
- devolver `null` cuando un índice no se puede calcular, en lugar de presentar un cero que podría interpretarse como un resultado válido;
- incluir la fecha de corte para contextualizar los indicadores.

### 3.3 Revisión de cálculos y decisiones

Realicé una sesión de revisión en la que Claude Code planteó escenarios y preguntas para comprobar la interpretación de Valor Ganado y revisar decisiones del sistema.

**Ronda 1 · Comprobar la interpretación de Valor Ganado.**

Se utilizó un ejemplo con BAC 100, 50 % planificado, 40 % real y AC 60.

- Identifiqué un CPI aproximado de 0,67, que indica que el costo incurrido es superior al valor del trabajo realizado.
- Identifiqué un SPI de 0,8, que indica un avance inferior al planificado.
- También comparé dos formas de consolidar el CPI de un proyecto: sumar EV y AC y luego dividir (0,947), frente a promediar los CPI de las actividades (0,956). Elegí la primera alternativa porque pondera cada actividad según sus valores de trabajo y costo, en lugar de asignar el mismo peso a actividades de tamaños diferentes.

**Ronda 2 · Revisar decisiones de diseño.**

Revisé y acepté las siguientes reglas porque mantenían una interpretación consistente de los indicadores:

- si AC = 0, el CPI no se puede calcular y no debe presentarse como 0;
- si existe avance sin costo registrado, mostrar «Falta el costo»;
- si BAC = 0, rechazar el cálculo con un mensaje;
- realizar los cálculos en el backend;
- calcular los indicadores al consultar, en lugar de almacenarlos como valores derivados;
- utilizar 0,90 como umbral para las alertas de severidad alta.

**Ronda 3 · Ajustes de interpretación para el usuario.**

Claude Code me presentó puntos de su implementación que consideraba discutibles, sin recomendar una opción. En dos de ellos decidí no mantener la solución inicial:

1. **Tolerancia del semáforo.** Un CPI de 0,99 se clasificaba en rojo igual que uno de 0,60. Consideré que esa presentación no diferenciaba suficientemente una desviación pequeña de una desviación considerable y podía reducir la utilidad visual de las alertas. Por eso decidí incorporar una banda de tolerancia.
2. **EAC con poco avance.** En el proyecto de ejemplo «App móvil», la estimación de costo final era de 44,8 millones frente a un presupuesto de 32 millones, con solo 6,25 % de avance real. Consideré que, con una base de avance tan pequeña, el EAC debía presentarse con una advertencia sobre su confiabilidad y no como una proyección concluyente.

**Ronda 4 · Definir los umbrales.**

Acordé utilizar una tolerancia del 5 % y un avance real mínimo del 10 % para advertir sobre la confiabilidad del EAC. Son criterios de presentación y control definidos para este proyecto, no valores que se estén presentando como una norma universal. Por eso quedaron configurados como constantes fáciles de modificar.

### 3.4 Implementación de los ajustes

- **PR #7 · Tolerancia.** Durante las pruebas se identificó que una tolerancia simétrica entre 0,95 y 1,05 podía clasificar un SPI exactamente igual a 1,00 como amarillo. Se ajustó la regla para aplicar la banda de tolerancia hacia abajo: desde 0,95 y por debajo de 1,00 se considera «En línea».
  También se mantuvo separado el estado estricto de la API (`cost_status`), que continúa indicando «sobre presupuesto» cuando CPI < 1, de la banda visual (`cost_band`). Esta separación permite conservar la regla del reto y, al mismo tiempo, ofrecer una lectura visual más útil.
- **PR #8 · Confiabilidad del EAC.** Cuando el avance real es inferior al 10 %, la API devuelve `estimate_is_reliable: false` y el dashboard identifica el EAC con un asterisco para advertir al usuario.

### 3.5 Publicación con Gitflow

El código se publicó por etapas en el repositorio, siguiendo Gitflow: ramas `feature/*` y Pull Requests hacia `develop`, integración en `release/1.0.0` y publicación en `main`.

Claude Code apoyó la ejecución de tareas de Git y GitHub. Los ajustes de tolerancia y confiabilidad del EAC quedaron registrados en los PR #7 y #8, respectivamente.

### 3.6 Profundización y comprensión de la solución

Además de implementar la solución, dediqué una etapa a estudiar la metodología y los componentes construidos para poder explicar sus resultados y decisiones. Solicité una guía detallada de los conceptos, siglas, fórmulas y arquitectura, y utilicé esa documentación como material de estudio.

Contrasté los valores del dashboard con cálculos manuales y revisé cómo se relacionaban las fórmulas con los datos de entrada. Este paso fue importante para no depender únicamente de que las pruebas automáticas terminaran correctamente: también necesitaba comprender qué significaban los resultados desde el punto de vista de la gestión del proyecto.

## 4. Qué acepté, qué ajusté y por qué

**Propuestas que acepté tras revisarlas:**

- **Consolidar sumando y luego dividiendo**, en lugar de promediar índices. La comparación dio 0,947 frente a 0,956 y confirmé que la primera opción pondera las actividades por sus valores de EV y AC.
- **No mostrar 0 cuando un índice no se puede calcular.** Un CPI igual a cero y un CPI no calculable representan situaciones distintas.
- **Incorporar pruebas basadas en propiedades con Hypothesis.** Estas pruebas generaron casos límite y detectaron una situación con BAC = 0,01 y 0,01 % planificado: PV se mostraba como 0,00, pero el estado indicaba «Atrasado» y SV aparecía como −0,00. Se ajustó la precisión para redondear PV, EV, AC y BAC a centavos antes de calcular los demás indicadores (`docs/EVM_METHODOLOGY.md`, sección Precisión). El caso quedó cubierto por una prueba.

**Decisiones en las que apliqué un criterio distinto o pedí ajustes:**

- **Alcance:** el primer planteamiento preparado con ChatGPT proponía una plataforma más amplia. Prioricé los requisitos de la prueba y un conjunto limitado de extras para mantener el desarrollo enfocado y verificable.
- **Semáforo y EAC:** en estos dos puntos no seguí la implementación propuesta por la IA y pedí cambiarla, como se describe en la sección 3.3. El objetivo era evitar que desviaciones pequeñas y proyecciones con poco avance se interpretaran sin suficiente contexto.

Durante la implementación también se corrigieron detalles detectados en la revisión, como excluir del repositorio una carpeta generada durante la compilación mediante `.gitignore` y ajustar el comportamiento de la tabla del dashboard en pantallas pequeñas. Estos casos reforzaron la importancia de revisar tanto el funcionamiento como la presentación final, incluso cuando la implementación se apoya en IA.

## 5. Decisión de diseño y criterio aplicado

La arquitectura en capas (dominio, casos de uso, API e infraestructura) fue propuesta durante el desarrollo y la mantuve después de revisar su separación de responsabilidades.

Una decisión en la que sí intervine directamente fue el tratamiento de la tolerancia del semáforo. En lugar de modificar el significado del estado estricto de la API, se separó ese estado de la banda utilizada para la presentación visual. Así, el sistema conserva la clasificación exigida por el reto y añade una interpretación visual que ayuda a distinguir desviaciones pequeñas.

## 6. Cómo verifiqué los números

1. **Cálculo manual del ejemplo.** Antes de confiar en el resultado del sistema, comprobé un escenario con BAC 100, 50 % planificado, 40 % real y AC 60.

   | Indicador | Cuenta | Resultado |
   |-----------|--------|-----------|
   | PV | 50 % × 100 | 50 |
   | EV | 40 % × 100 | 40 |
   | CV | 40 − 60 | −20 |
   | SV | 40 − 50 | −10 |
   | CPI | 40 ÷ 60 | 0,6667 |
   | SPI | 40 ÷ 50 | 0,80 |
   | EAC | 100 ÷ 0,6667 | 150 |
   | VAC | 100 − 150 | −50 |

2. **Comparación con el dashboard.** El proyecto de ejemplo «Portal de clientes» presenta CPI 0,9474, SPI 0,7826 y EAC 36.944.444,44. Contrasté estos valores con el cálculo documentado en `docs/EVM_METHODOLOGY.md`. En el video también se crea un proyecto nuevo y se comprueban sus cifras con calculadora.
3. **Pruebas automatizadas.** El reporte documenta 89 pruebas en backend y 25 en frontend, con 98,6 % de cobertura del backend y 100 % en el dominio.
   - Las 89 pruebas del backend se distribuyen así: 37 del motor de cálculo, 10 de alertas y 42 de integración contra PostgreSQL.
   - Las pruebas comparan valores esperados calculados manualmente, además de verificar el comportamiento de las funciones.

## 7. Qué mejoraría en una siguiente iteración

- **Llevar una bitácora continua.** Mantendría un registro desde el inicio con los prompts, las decisiones aceptadas o descartadas, sus motivos y las pruebas utilizadas para verificarlas. Esto facilitaría la trazabilidad del proceso.
- **Ampliar el manejo de cortes históricos.** La solución actual trabaja con una fecha de corte, de acuerdo con el alcance definido para la prueba. Como evolución, incorporaría varios cortes para analizar tendencias y construir una curva S.
- **Agregar pruebas de extremo a extremo con navegador.** Complementaría las pruebas actuales con Playwright para automatizar recorridos completos de usuario en la interfaz.

## 8. Aprendizajes

Este proyecto me permitió utilizar IA para acelerar tareas de implementación y, al mismo tiempo, reconocer que la calidad de una solución no depende únicamente de producir código. También requiere entender el problema, cuestionar los resultados, validar los cálculos y tomar decisiones sobre cómo presentar la información.

El mayor aprendizaje fue combinar la velocidad de la asistencia de IA con una revisión técnica consciente: comprobar las fórmulas, identificar escenarios límite y ajustar la solución cuando la interpretación del resultado podía mejorar. Esa es la forma en que considero que la IA aporta valor al trabajo de desarrollo.
