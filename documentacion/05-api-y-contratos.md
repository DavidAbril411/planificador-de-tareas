# API y contratos

La referencia de cada función se genera con Sphinx (`./ejecutar_parcial2.sh docs`). Acá están los contratos principales.

## Formato de las tareas

```json
{
  "A": {"duracion": 2.0, "prioridad": 1, "depende_de": []},
  "B": {"duracion": 1.5, "prioridad": 2, "depende_de": ["A"]}
}
```

## Rutas de la web

| Ruta | Entrada | Salida |
|---|---|---|
| `GET /` | | La página |
| `POST /plan` | `tareas`, `procesos` | `orden`, `cronograma`, `duracion`, `duracion_1_proceso` |
| `POST /ejecutar` | `tareas`, `procesos` | `registro`, `total` |
| `GET /pasos` | | Pasos del planificador |
| `POST /medir` | `clave`, `con` | `segundos` |

## Errores

Las rutas `/plan` y `/ejecutar` responden `{"error": "mensaje"}` si no hay tareas, si una tarea dura más de 5 s, si depende de una que no existe o si hay un ciclo.

## Ejemplo de uso

```bash
curl -X POST http://127.0.0.1:5050/plan \
  -H 'Content-Type: application/json' \
  -d '{"tareas": {"A": {"duracion": 1, "prioridad": 1, "depende_de": []}}, "procesos": 1}'
```

## Funciones de Python

| Función | Entrada | Salida | Caso especial |
|---|---|---|---|
| `orden_rapido(tareas)` | Tareas | Lista de nombres | `None` si hay un ciclo |
| `niveles(tareas)` | Tareas | Lista de niveles | |
| `cronograma(tareas, recursos)` | Tareas, recursos | `{tarea: (inicio, fin, recurso)}` | `None` es sin límite |
| `ejecutar(tareas, procesos)` | Tareas, procesos | `{tarea: (inicio, fin, proceso)}` | 1 proceso es sin paralelismo |
