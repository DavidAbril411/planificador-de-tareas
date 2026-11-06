"""
Ejecución de las tareas en paralelo con multiprocessing.

Cada tarea hace trabajo de CPU; por el GIL, los hilos no ayudarían.
"""

import heapq
import os
import time
from multiprocessing import Process, Queue
from typing import Dict, List, Tuple

from planificador import (
    Tareas,
    clave_de_prioridad,
    liberar_siguientes,
    orden_rapido,
    preparar_grafo,
)

# Cada bloque tarda unos 4 ms: 240 bloques son aproximadamente 1 segundo.
TAMANIO_BLOQUE = 10_000
BLOQUES_POR_SEGUNDO = 240

Registro = Tuple[str, float, float, int]


def contar_primos(hasta: int) -> int:
    """
    Cuenta los primos menores que ``hasta``: trabajo de CPU.

    >>> contar_primos(20)
    8
    """
    cantidad = 0
    for numero in range(2, hasta):
        es_primo = True
        divisor = 2
        while divisor * divisor <= numero:
            if numero % divisor == 0:
                es_primo = False
                break
            divisor += 1
        if es_primo:
            cantidad += 1
    return cantidad


def trabajar(pedido: Tuple[str, float]) -> Registro:
    """Hace el trabajo de una tarea y anota cuándo empezó, terminó y dónde."""
    nombre, duracion = pedido
    inicio = time.time()
    for _ in range(round(duracion * BLOQUES_POR_SEGUNDO)):
        contar_primos(TAMANIO_BLOQUE)
    return nombre, inicio, time.time(), os.getpid()


def pedidos(tareas: Tareas, nombres: List[str]) -> List[Tuple[str, float]]:
    """Lo que se le manda a cada proceso: nombre y duración."""
    return [(nombre, tareas[nombre]["duracion"]) for nombre in nombres]


def ejecutar(tareas: Tareas, procesos: int) -> Dict[str, Tuple]:
    """
    Ejecuta las tareas de verdad y devuelve cuándo corrió cada una.

    Parámetros:
        tareas (dict): las tareas a ejecutar.
        procesos (int): cuántos procesos pueden trabajar a la vez.

    Retorna:
        dict: para cada tarea, ``(inicio, fin, proceso)`` en segundos.
    """
    if procesos == 1:
        comienzo = time.time()
        orden = orden_rapido(tareas) or []
        registros = [trabajar(p) for p in pedidos(tareas, orden)]
    else:
        registros = ejecutar_en_procesos(tareas, procesos)
        comienzo = min(inicio for _, inicio, _, _ in registros)

    carriles: Dict[int, int] = {}
    resultado = {}
    for nombre, inicio, fin, pid in registros:
        carril = carriles.setdefault(pid, len(carriles))
        resultado[nombre] = (inicio - comienzo, fin - comienzo, carril)
    return resultado


def consumidor(cola_tareas: Queue, cola_resultados: Queue) -> None:
    """Consumidor: saca tareas de la cola hasta recibir ``None``."""
    while True:
        pedido = cola_tareas.get()
        if pedido is None:
            return
        cola_resultados.put(trabajar(pedido))


def iniciar_consumidores(procesos: int, cola_tareas: Queue,
                         cola_resultados: Queue) -> List[Process]:
    """Arranca un proceso consumidor por cada recurso."""
    trabajadores = [Process(target=consumidor,
                            args=(cola_tareas, cola_resultados))
                    for _ in range(procesos)]
    for trabajador in trabajadores:
        trabajador.start()
    return trabajadores


def cerrar_consumidores(trabajadores: List[Process],
                        cola_tareas: Queue) -> None:
    """Avisa a cada consumidor que no hay más tareas y espera que termine."""
    for _ in trabajadores:
        cola_tareas.put(None)
    for trabajador in trabajadores:
        trabajador.join()


def ejecutar_en_procesos(tareas: Tareas, procesos: int) -> List[Registro]:
    """
    Productor: pone en la cola las tareas que ya pueden empezar.

    Apenas termina una, las que la esperaban van a la cola, así ninguna
    espera a otra que no necesita.
    """
    cola_tareas: Queue = Queue()
    cola_resultados: Queue = Queue()
    trabajadores = iniciar_consumidores(procesos, cola_tareas, cola_resultados)

    pendientes, siguientes = preparar_grafo(tareas)
    listas = [clave_de_prioridad(tareas, n) for n in tareas
              if pendientes[n] == 0]
    heapq.heapify(listas)
    registros: List[Registro] = []
    en_curso = 0
    while listas or en_curso:
        while listas and en_curso < procesos:
            _, nombre = heapq.heappop(listas)
            cola_tareas.put(pedidos(tareas, [nombre])[0])
            en_curso += 1

        registro = cola_resultados.get()
        registros.append(registro)
        en_curso -= 1
        for liberada in liberar_siguientes(registro[0], pendientes,
                                           siguientes):
            heapq.heappush(listas, clave_de_prioridad(tareas, liberada))

    cerrar_consumidores(trabajadores, cola_tareas)
    return registros


def tiempo_total(tareas: Tareas, procesos: int) -> float:
    """Segundos que tarda ejecutar todas las tareas."""
    return max(fin for _, fin, _ in ejecutar(tareas, procesos).values())
