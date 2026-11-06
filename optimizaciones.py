"""
Los pasos del planificador, con y sin su optimización (los usa la web).
"""

import os
import random
import tempfile
import time
from functools import lru_cache
from typing import Callable, Dict, List

import archivos
import planificador as pl


@lru_cache(maxsize=None)
def tareas_de_prueba(cantidad: int) -> pl.Tareas:
    """Tareas al azar (siempre las mismas); se generan una sola vez."""
    generador = random.Random(42)
    tareas: pl.Tareas = {}
    for i in range(cantidad):
        cuantas = min(i, generador.randint(0, 3))
        anteriores = generador.sample(range(i), cuantas)
        tareas[f"T{i}"] = {"duracion": 1.0,
                           "prioridad": generador.randint(1, 10),
                           "depende_de": [f"T{j}" for j in anteriores]}
    return tareas


def tareas_encadenadas(cantidad: int) -> pl.Tareas:
    """Cada tarea depende de las dos anteriores, como Fibonacci."""
    return {f"T{i}": {"duracion": 1.0, "prioridad": 1,
                      "depende_de": [f"T{j}" for j in (i - 1, i - 2)
                                     if j >= 0]}
            for i in range(cantidad)}


# ---------------------------------------------------------------------------
#  Un paso por optimización: (con, sin)
# ---------------------------------------------------------------------------

def ordenar(con: bool) -> None:
    """Ordena 2.000 tareas con heap (O(n + d)) o recorriendo todo (O(n²))."""
    tareas = tareas_de_prueba(2000)
    if con:
        pl.orden_rapido(tareas)
    else:
        pl.orden_lento(tareas)


def consultar_terminadas(con: bool) -> None:
    """Pregunta 3.000 veces si una tarea terminó: en un set o en una lista."""
    nombres = [f"T{i}" for i in range(10_000)]
    terminadas = set(nombres) if con else nombres
    for i in range(3000):
        _ = f"T{9999 - i % 10}" in terminadas


def calcular_fin(con: bool) -> None:
    """Cuándo termina la tarea 25 de una cadena: con memoización o sin."""
    tareas = tareas_encadenadas(25)
    if con:
        pl.cuando_termina_memo(tareas, "T24")
    else:
        pl.cuando_termina(tareas, "T24")


def pedir_plan(con: bool) -> None:
    """Pide 50 veces el plan de 5.000 tareas: guardado en caché o no."""
    tareas = tareas_de_prueba(5000)
    pl.planes_guardados.clear()
    for _ in range(50):
        if con:
            pl.plan_con_cache("plan", tareas)
        else:
            pl.niveles(tareas)


def guardar_archivo(con: bool) -> None:
    """Guarda 200.000 tareas: con buffer y lotes, o línea por línea."""
    ruta = os.path.join(tempfile.gettempdir(), "tareas_interfaz.txt")
    tareas = tareas_de_prueba(200_000)
    if con:
        archivos.escribir_por_lotes(ruta, tareas)
    else:
        archivos.escribir_linea_por_linea(ruta, tareas)
    os.remove(ruta)


PASOS: List[Dict] = [
    {"clave": "algoritmo", "funcion": ordenar,
     "paso": "Elegir cuál es la próxima tarea",
     "nombre": "Fila por urgencia", "biblioteca": "heapq",
     "sin": "recorre las 2.000 tareas cada vez preguntando si ya puede "
            "empezar",
     "con": "una fila que siempre tiene adelante la más urgente"},
    {"clave": "estructura", "funcion": consultar_terminadas,
     "paso": "Saber si una tarea ya terminó",
     "nombre": "Conjunto", "biblioteca": "set",
     "sin": "compara una por una con la lista de terminadas",
     "con": "con el nombre va directo al lugar donde estaría"},
    {"clave": "memo", "funcion": calcular_fin,
     "paso": "Calcular cuándo termina cada tarea",
     "nombre": "Memoización", "biblioteca": "functools.lru_cache",
     "sin": "repite millones de veces las mismas cuentas",
     "con": "anota cada resultado y después lo lee"},
    {"clave": "cache", "funcion": pedir_plan,
     "paso": "Pedir otra vez el mismo plan",
     "nombre": "Caché", "biblioteca": "dict",
     "sin": "vuelve a planificar todo",
     "con": "devuelve el plan que ya tenía guardado"},
    {"clave": "buffer", "funcion": guardar_archivo,
     "paso": "Guardar las tareas en un archivo",
     "nombre": "Buffer y lotes", "biblioteca": "open(buffering=1 MB)",
     "sin": "va al disco una vez por cada tarea",
     "con": "junta 10.000 líneas y las escribe de una vez"},
]

FUNCIONES: Dict[str, Callable[[bool], None]] = {
    paso["clave"]: paso["funcion"] for paso in PASOS}


def medir_paso(clave: str, con: bool) -> float:
    """Segundos que tarda un paso, con o sin su optimización."""
    inicio = time.perf_counter()
    FUNCIONES[clave](con)
    return time.perf_counter() - inicio
