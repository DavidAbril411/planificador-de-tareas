# Diseño técnico

## Estructuras de datos

| Estructura | Dónde | Por qué |
|---|---|---|
| `TypedDict` `Tarea` | Cada tarea | Los tipos quedan controlados por mypy |
| `dict` | Tareas y dependencias pendientes | Consulta en O(1) |
| `heapq` | Tareas listas para empezar | Saca la más urgente en O(log n) |
| `set` | Tareas terminadas en `orden_lento` | Búsqueda en O(1) |
| `Queue` | Comunicación entre procesos | Productor y consumidor |

## Algoritmos importantes

- **`orden_rapido`**: anota cuántas dependencias le faltan a cada tarea y usa un heap con las disponibles. Complejidad O(n + d), con n tareas y d dependencias (más el log del heap).
- **`cronograma`**: simula el tiempo; asigna tareas a recursos libres y avanza hasta la próxima que termina.
- **`cuando_termina_memo`**: recursión con `lru_cache`; cada tarea se calcula una sola vez.
- **`ejecutar_en_procesos`**: productor y consumidores; cuando termina una tarea, las que la esperaban van a la cola.

## Decisiones de implementación

| Decisión | Motivo |
|---|---|
| `multiprocessing` en vez de hilos | Las tareas son trabajo de CPU, y por el GIL los hilos no calculan a la vez |
| Colas en vez de ejecutar por niveles | Por niveles, una tarea corta esperaba a una larga que no necesitaba: 7 s contra 4 s |
| Conservar `orden_lento` | Es la referencia para comparar; el planificador no la usa para ordenar |
| Trabajo en bloques fijos | Hace que el tiempo real sea proporcional a la duración de la tarea |
| `List` y `Optional` de `typing` | Es la forma que enseña el material (PEP 484) |
