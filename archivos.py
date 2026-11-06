"""
Archivos grandes de tareas: buffer, lotes y procesamiento en paralelo.

Una tarea por línea: ``nombre;duracion;prioridad;dependencias``.
"""

import time
from multiprocessing import Process, Queue
from typing import Dict, Iterator, List

from planificador import Tarea, Tareas

TAMANIO_LOTE = 10_000
BUFFER_GRANDE = 1024 * 1024        # 1 MB


def linea_de_tarea(nombre: str, tarea: Tarea) -> str:
    """
    Convierte una tarea en una línea del archivo.

    >>> tarea = {"duracion": 1.5, "prioridad": 2, "depende_de": ["A"]}
    >>> linea_de_tarea("B", tarea)
    'B;1.5;2;A\\n'
    """
    dependencias = ",".join(tarea["depende_de"])
    campos = [nombre, str(tarea["duracion"]), str(tarea["prioridad"]),
              dependencias]
    return ";".join(campos) + "\n"


def escribir_linea_por_linea(ruta: str, tareas: Tareas) -> float:
    """Versión lenta, para comparar: va al disco una vez por tarea."""
    inicio = time.perf_counter()
    with open(ruta, "w", encoding="utf-8", buffering=1) as archivo:
        for nombre, tarea in tareas.items():
            archivo.write(linea_de_tarea(nombre, tarea))
    return time.perf_counter() - inicio


def escribir_por_lotes(ruta: str, tareas: Tareas,
                       tamanio_lote: int = TAMANIO_LOTE) -> float:
    """Escribe con un buffer de 1 MB, de a lotes de líneas."""
    inicio = time.perf_counter()
    with open(ruta, "w", encoding="utf-8", buffering=BUFFER_GRANDE) as archivo:
        lote = []
        for nombre, tarea in tareas.items():
            lote.append(linea_de_tarea(nombre, tarea))
            if len(lote) == tamanio_lote:
                archivo.writelines(lote)
                lote = []
        archivo.writelines(lote)
    return time.perf_counter() - inicio


def leer_por_lotes(ruta: str,
                   tamanio_lote: int = TAMANIO_LOTE) -> Iterator[List[str]]:
    """Generador: devuelve el archivo de a ``tamanio_lote`` líneas."""
    with open(ruta, encoding="utf-8", buffering=BUFFER_GRANDE) as archivo:
        lote = []
        for linea in archivo:
            lote.append(linea)
            if len(lote) == tamanio_lote:
                yield lote
                lote = []
        if lote:
            yield lote


def resumir_lote(lineas: List[str]) -> Dict[str, float]:
    """
    Resume un lote: cantidad, duración, dependencias y prioridad máxima.

    >>> resumir_lote(["A;2.0;1;\\n", "B;1.5;2;A\\n"])
    {'tareas': 2, 'duracion': 3.5, 'dependencias': 1, 'prioridad_maxima': 2}
    """
    duracion = 0.0
    dependencias = 0
    prioridad_maxima = 0
    for linea in lineas:
        _, texto_duracion, texto_prioridad, texto_dependencias = (
            linea.rstrip("\n").split(";"))
        duracion += float(texto_duracion)
        prioridad_maxima = max(prioridad_maxima, int(texto_prioridad))
        if texto_dependencias:
            dependencias += texto_dependencias.count(",") + 1
    return {"tareas": len(lineas), "duracion": duracion,
            "dependencias": dependencias, "prioridad_maxima": prioridad_maxima}


def juntar_resumenes(resumenes: List[Dict[str, float]]) -> Dict[str, float]:
    """Combina los resúmenes de todos los lotes en uno solo."""
    return {
        "tareas": sum(r["tareas"] for r in resumenes),
        "duracion": sum(r["duracion"] for r in resumenes),
        "dependencias": sum(r["dependencias"] for r in resumenes),
        "prioridad_maxima": max(r["prioridad_maxima"] for r in resumenes),
    }


def procesar_secuencial(ruta: str) -> Dict[str, float]:
    """Lee por lotes y procesa cada lote en este mismo proceso."""
    return juntar_resumenes([resumir_lote(lote)
                             for lote in leer_por_lotes(ruta)])


def resumir_de_la_cola(cola_lotes: Queue, cola_resumenes: Queue) -> None:
    """Consumidor: resume lotes de la cola hasta recibir ``None``."""
    while True:
        lote = cola_lotes.get()
        if lote is None:
            return
        cola_resumenes.put(resumir_lote(lote))


def procesar_en_paralelo(ruta: str, procesos: int) -> Dict[str, float]:
    """
    Productor: lee los lotes y los pone en una Queue para los consumidores.

    La cola tiene tamaño máximo, así hay pocos lotes en memoria a la vez.
    """
    cola_lotes: Queue = Queue(maxsize=procesos * 2)
    cola_resumenes: Queue = Queue()
    consumidores = [Process(target=resumir_de_la_cola,
                            args=(cola_lotes, cola_resumenes))
                    for _ in range(procesos)]
    for consumidor in consumidores:
        consumidor.start()

    cantidad_lotes = 0
    for lote in leer_por_lotes(ruta):
        cola_lotes.put(lote)
        cantidad_lotes += 1
    for _ in consumidores:
        cola_lotes.put(None)

    resumenes = [cola_resumenes.get() for _ in range(cantidad_lotes)]
    for consumidor in consumidores:
        consumidor.join()
    return juntar_resumenes(resumenes)
