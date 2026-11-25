# Ficha del proyecto

Proyecto 9 de la guía de trabajos finales: **Optimizador de producción**.

## Objetivo

Planificar y ejecutar las tareas de una planta de producción que dependen unas de otras: decidir el orden, aprovechar los recursos en paralelo y estimar cuánto tarda cada tarea cuando no se sabe.

## Descripción

Cada tarea tiene una duración, una prioridad y las tareas que tiene que esperar. El sistema arma el orden de ejecución, calcula el cronograma con un límite de recursos, ejecuta las tareas en varios procesos y muestra todo en una web. Un modelo de IA estima la duración de las tareas nuevas a partir del historial.

## Requisitos funcionales

- Cargar tareas con duración, prioridad y dependencias.
- Detectar ciclos y dependencias inexistentes.
- Calcular el orden, los niveles y el cronograma con N recursos.
- Ejecutar las tareas con uno o varios procesos y mostrar el diagrama de Gantt.
- Guardar y leer proyectos grandes en archivos.
- Estimar la duración de una tarea nueva, con y sin IA.

## Requisitos de programación eficiente

| Requisito de la guía | Cómo se cumple |
|---|---|
| Algoritmo y complejidad | `orden_rapido` O(n + d) con heap, contra `orden_lento` O(n²) ([Diseño técnico](04-diseno-tecnico.md)) |
| Estructuras de datos | `dict`, `heapq`, `set`, `Queue`, `TypedDict` |
| Memoización y caché | `lru_cache` en `cuando_termina_memo` y en el modelo de IA; caché de planes |
| Generadores y batching | `leer_por_lotes` con `yield`, escritura por lotes con buffer |
| Concurrencia | `multiprocessing` con productor y consumidores |
| Profiling y optimización | cProfile, Scalene, SnakeViz, py-spy, Elastic APM |
| Pruebas unitarias | `unittest`, doctest y Hypothesis |
| Documentación | PEP 8 (Ruff, Pylint), docstrings, Sphinx y este vault |
| Interfaz gráfica | Web con Flask |
| IA | Estimación de duraciones con scikit-learn ([IA aplicada](11-ia-aplicada.md)) |
| CI | GitHub Actions con Performance Gate ([Controles del CI](10-controles-del-ci.md)) |

## IA aplicada

- **En la aplicación:** un `RandomForestRegressor` estima la duración de una tarea según su tipo, unidades, operarios y máquina, y se compara contra el promedio por unidad del tipo × la cantidad.
- **En el desarrollo:** Hypothesis genera casos de prueba automáticamente, y un asistente de IA (Claude) ayudó a escribir código y pruebas. Cada propuesta se validó con los controles del CI.

## Métricas de rendimiento

| Métrica | Valor |
|---|---|
| Ordenar 100.000 tareas | ~0,3 s (límite del gate: 1 s) |
| Crecimiento de `orden_rapido` por 10 de entrada | ~13x (lineal) |
| Crecimiento de `orden_lento` por 2 de entrada | ~4x (cuadrático) |
| Error de la IA contra el promedio | 8 min contra 74 min |
| Memoria leyendo por lotes | 2,4 MB contra 14,1 MB |
| Paralelismo, 8 tareas de CPU | ~5x más rápido |

Las mediciones completas están en [Rendimiento](07-rendimiento.md).

## Posibles mejoras

- Guardar el historial real de la planta en una base de datos para reentrenar el modelo.
- Recursos con capacidades distintas (máquinas especializadas).
- Ordenar las tareas para que sus datos queden contiguos en memoria y aprovechar la caché del procesador.
- Usuarios y permisos para publicar la web fuera de la computadora local.
