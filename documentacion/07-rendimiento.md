# Rendimiento

## Benchmarks

Medidos con pytest-benchmark sobre el proyecto de prueba de 2.000 tareas que inventa el programa, en una Mac:

| Operación | Mediana |
|---|---|
| `niveles` | 1,1 ms |
| `orden_rapido` | 2,1 ms |
| `cronograma` con 4 recursos | 2,8 ms |

El CI compara contra una línea base medida en el propio runner, y rechaza si la mediana empeora más del 100 %.

## Escalabilidad y Performance Gate

`ci/escalabilidad.py` mide con 1.000, 10.000 y 100.000 tareas (mediana de 5 corridas):

| Tareas | `orden_rapido` | Crecimiento |
|---:|---:|---:|
| 1.000 | 0,0010 s | |
| 10.000 | 0,013 s | 13x |
| 100.000 | 0,29 s | 23x |

La complejidad O(n + d) predice ~10x por cada 10 de entrada (un poco más por el log del heap), y así crece hasta 10.000. Con 100.000 crece 23x: las estructuras ya no entran en la caché del procesador, y las dependencias al azar obligan a ir a la RAM. Se comprobó midiendo el mismo tamaño con dependencias consecutivas: ahí crece 14x.

`orden_lento` (O(n²)) crece ~4x cada vez que se duplica la entrada, como predice la teoría.

**Performance Gate:** ordenar 100.000 tareas tiene que tardar menos de 1 s. Si no, el CI imprime `Performance Gate FAILED` y la integración queda bloqueada.

## Mejora de cada optimización

| Paso | Herramienta | Mejora |
|---|---|---|
| Elegir la próxima tarea | `heapq` | ~100x |
| Saber si una tarea terminó | `set` | ~150x |
| Calcular cuándo termina | `lru_cache` | ~800x |
| Repetir el plan | caché | ~15x |
| Guardar en archivo | buffer y lotes | ~5x |
| 8 tareas de CPU | `multiprocessing` | ~5x |

## Profiling

- **cProfile** en el CI: `orden_lento` 1,43 s contra `orden_rapido` 0,005 s.
- **Scalene**: el 25 % del CPU se iba en una línea de `orden_lento`.
- **py-spy**: más de la mitad del tiempo de `perfilar.py` es generar datos de prueba.

## Complejidad temporal

| Función | Complejidad |
|---|---|
| `orden_lento` | O(n²) |
| `orden_rapido`, `niveles` | O(n + d) más el log del heap |
| `cuando_termina` | O(2ⁿ) en el peor caso |
| `cuando_termina_memo` | O(n + d) |

Complejidad ciclomática: ninguna función supera 10 (Radon).

## Consumo de memoria

Con tracemalloc, sobre un archivo de 200.000 tareas:

| Forma de leer | Memoria máxima |
|---|---|
| Por lotes | 2,4 MB |
| Archivo entero | 14,1 MB |

El límite del CI es 5 MB: un poco más del doble de lo medido, para tolerar variaciones entre máquinas.
