# Consigna del Parcial 2: dónde está cada punto

Cada punto dice **dónde está en el código** y **de qué slide del material sale**
(`Programacion-eficiente (6).pptx`). Todo se agrega sobre el Parcial 1
(copia en `anterior/parcial1.py`).

| # | Punto de la consigna | Dónde está | Material |
|---|---|---|---|
| 1 | **Eliminar código redundante** | `planificador.py`: `preparar_grafo` (l. 37), `liberar_siguientes` (l. 62) y `clave_de_prioridad` (l. 83). Antes, esos pasos estaban copiados en `orden_rapido`, `niveles` y `duracion_con_recursos`. `duracion_con_recursos` (l. 232) ahora reutiliza `cronograma` (l. 190). Comparación con el Parcial 1: `parcial2.py`, `punto_2_codigo_redundante` (l. 146). | Slides 133–137 |
| 2 | **Herramientas de optimización (Python)** | **Scalene**: `scalene run --cpu-only perfilar.py` → `reportes/scalene.txt` y `scalene.html`. **SnakeViz**: `python3 -m cProfile -o reportes/perfilar.prof perfilar.py` y `snakeviz reportes/perfilar.prof`; también `parcial2.py`, `punto_5_perfilado` (l. 267), que guarda `reportes/orden_lento.prof`. **py-spy**: `./ejecutar_parcial2.sh pyspy` → `reportes/pyspy.svg`. | Slides 164, 176–178, 264–267 |
| 3 | **Herramienta general** (YourKit, New Relic, Elastic APM) | **Elastic APM**: `apm/docker-compose.yml` levanta Elasticsearch, APM Server y Kibana en local. En `app.py` (líneas del principio), `ElasticAPM(app)` conecta Flask y mide cada pedido a la web. `./ejecutar_parcial2.sh apm` → Kibana en http://localhost:5601/app/apm, servicio `planificador-de-tareas`. | Slides 183–185 |
| 4 | **Archivos grandes: buffer** | `archivos.py`: `escribir_por_lotes` (l. 47) con `open(..., buffering=BUFFER_GRANDE)` (1 MB, l. 17), contra `escribir_linea_por_linea` (l. 34) con `buffering=1`. | Slides 191–195, 207 |
| 4 | **Archivos grandes: batching** | `archivos.py`: lotes de `TAMANIO_LOTE` = 10.000 líneas (l. 16), al escribir (`escribir_por_lotes`) y al leer (`leer_por_lotes`, l. 67, un generador con `yield`). | Slides 196–206 (generadores: 89–92) |
| 4 | **Archivos grandes: procesamiento en paralelo** | `archivos.py`: `procesar_en_paralelo` (l. 131). Productor y consumidores con `multiprocessing.Process` + `Queue`. | Slides 117, 122, 203 |
| — | **Paralelismo** (en lugar de la concurrencia del Parcial 1) | `paralelo.py`: `ejecutar` (l. 79), `consumidor` (l. 112) y `ejecutar_en_procesos` (l. 127). Usa `multiprocessing.Process` + `Queue`; cada tarea hace trabajo de CPU (cuenta primos). | Slides 114–122 (primos: 117, GIL: 120, Queue: 122) |
| 5 | **Legibilidad y mantenibilidad: nombres** | Todos los módulos. Ejemplos: `liberar_siguientes`, `clave_de_prioridad`; constantes `TAMANIO_LOTE`, `BUFFER_GRANDE`, `BLOQUES_POR_SEGUNDO`. | Slides 214–216 |
| 5 | **Comentarios y docstrings** | Todas las funciones tienen docstring con "Parámetros:" y "Retorna:", como en la slide 217, y type hints (`typing`). | Slides 217–219, 239 |
| 5 | **Organización y formato: PEP 8** | `flake8 *.py` → 0 avisos (`reportes/flake8_parcial2.txt`). El Parcial 1 tenía 82 (`reportes/flake8_parcial1.txt`). | Slides 223–235 |
| 6 | **Generador de documentación** | Sphinx con `sphinx.ext.autodoc`: `docs/conf.py` y un `.rst` por módulo. `./ejecutar_parcial2.sh docs` → `docs/_build/html/index.html`. | Slides 240–241, 332–338 |
| 7 | **Herramienta de análisis de calidad** | **pylint** (en vez de SonarQube; la consigna permite cualquier herramienta): 9,00/10 en el Parcial 1 → 10,00/10 (`reportes/pylint_*.txt`). También flake8. | Slides 242, 249–250, 235 |
| 8 | **Refactorización** | Extract Method (punto 1), nombres descriptivos, números mágicos → constantes, código duplicado → una función. Que el comportamiento no cambió lo comprueban `punto_2_codigo_redundante` y los tests. | Slides 243–258 (bad smells: 253–258) |
| 9 | **Testing** | `test_planificador.py`: 7 clases de `unittest` (orden, duración, cronograma, interfaz, caché, archivos, paralelo) más los `doctest` de los docstrings (`load_tests`, l. 198). `./ejecutar_parcial2.sh tests` → 34 OK. | Slides 272–284 (doctest: 280) |
| 10 | **Uso de algún framework** | **Flask**: `app.py` (rutas `/`, `/plan`, `/ejecutar`, `/pasos`, `/medir`) y `templates/index.html` con `render_template`. `./ejecutar_parcial2.sh web`. | Slides 316–319 |

## Qué no sale del material

- **Módulos auxiliares de la biblioteca estándar**: `os`, `tempfile`, `pathlib`
  y `sys`, solo para rutas y archivos temporales. No son técnicas de la
  materia.
- **`random`, `heapq` y `lru_cache`** ya estaban en el Parcial 1 (y en las
  slides 61 y 107–108).
- Lo que no estaba en el material se reemplazó: `Pool.apply_async`,
  `Pool.imap`, `pstats`, `jsonify` y la extensión `viewcode` de Sphinx.

## Herramienta general: cómo mostrarla

1. Abrir Docker Desktop.
2. Correr `./ejecutar_parcial2.sh apm` (la primera vez tarda unos minutos).
3. Usar la web: ejecutar tareas y medir optimizaciones.
4. Abrir http://localhost:5601/app/apm → servicio `planificador-de-tareas`.
   Ahí se ve cuánto tarda cada pedido (`POST /ejecutar`, `POST /medir`) y
   cuántos pedidos hubo.
5. Para apagarlo: `cd python/parcial2/apm && docker compose down`.
