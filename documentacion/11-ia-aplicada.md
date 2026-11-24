# IA aplicada

## Qué resuelve

Al cargar una tarea de producción muchas veces no se sabe cuánto va a durar. El sistema la estima a partir del historial de tareas ya hechas (`ia.py`).

## Las dos soluciones

| | Sin IA | Con IA |
|---|---|---|
| Método | Promedio de duración del tipo | `RandomForestRegressor` de scikit-learn |
| Qué mira | Solo el tipo | Tipo, unidades, operarios y máquina |
| Estructura | `dict`, estimar es O(1) | 60 árboles de hasta 12 niveles |

El historial es sintético y reproducible: 4.000 tareas con una duración que depende de esos datos, más un 10 % de ruido.

## Comparación medida

Sobre 1.000 tareas que ninguno de los dos vio al entrenar (`ia.comparar_estimadores()`):

| Estimador | Error medio | Por estimación | Entrenar | Memoria |
|---|---|---|---|---|
| Sin IA | 92,6 min | 0,05 µs | 1 ms | 0,001 MB |
| Con IA | 8,0 min | ~9 µs | ~0,45 s | 1,5 MB |

## Cuándo conviene

La IA se equivoca 11,6 veces menos porque usa los datos que realmente cambian la duración. Cuesta unas 200 veces más por estimación, pero siguen siendo microsegundos: para planificar conviene. Si la planta tuviera un solo tipo de tarea y siempre la misma cantidad, el promedio alcanzaría, sería más simple y no necesitaría scikit-learn.

El modelo se entrena una sola vez y queda en caché (`lru_cache`).

## En la web

La sección 4 estima una tarea y la agrega a la tabla. En la demo, 1 hora de producción equivale a 1 segundo.

## IA en el desarrollo

- **Hypothesis** (slide 378) genera cientos de proyectos al azar y comprueba propiedades: el orden respeta las dependencias, la versión lenta y la rápida coinciden, y con más recursos nunca se tarda más que de a una.
- Un asistente de IA (Claude) propuso código y pruebas. Nada se integró sin pasar por los controles del CI, y las propuestas que no se pudieron medir no se aceptaron.
