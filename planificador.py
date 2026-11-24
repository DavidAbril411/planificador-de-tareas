"""
Planificador de tareas con dependencias (núcleo del Parcial 1, refactorizado).
"""

import heapq
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, TypedDict


class Tarea(TypedDict):
    """Lo que se sabe de cada tarea."""

    duracion: float
    prioridad: int
    depende_de: List[str]


Tareas = Dict[str, Tarea]

TAREAS_EJEMPLO: Tareas = {
    "A": {"duracion": 2.0, "prioridad": 1, "depende_de": []},
    "B": {"duracion": 1.5, "prioridad": 2, "depende_de": ["A"]},
    "C": {"duracion": 1.0, "prioridad": 1, "depende_de": ["A"]},
    "D": {"duracion": 0.5, "prioridad": 3, "depende_de": ["B", "C"]},
}


# --- Pasos comunes (en el Parcial 1 estaban repetidos en 3 funciones) ---

def preparar_grafo(
        tareas: Tareas) -> Tuple[Dict[str, int], Dict[str, List[str]]]:
    """
    Cuántas dependencias le faltan a cada tarea y quién espera a cada una.

    >>> pendientes, siguientes = preparar_grafo(TAREAS_EJEMPLO)
    >>> pendientes["D"], siguientes["A"]
    (2, ['B', 'C'])
    """
    pendientes = {nombre: len(tareas[nombre]["depende_de"])
                  for nombre in tareas}
    siguientes: Dict[str, List[str]] = {nombre: [] for nombre in tareas}
    for nombre in tareas:
        for anterior in tareas[nombre]["depende_de"]:
            siguientes[anterior].append(nombre)
    return pendientes, siguientes


def liberar_siguientes(nombre: str, pendientes: Dict[str, int],
                       siguientes: Dict[str, List[str]]) -> List[str]:
    """
    Marca ``nombre`` como terminada y devuelve las tareas que quedan libres.

    Parámetros:
        nombre (str): la tarea que acaba de terminar.
        pendientes (dict): dependencias que faltan (se modifica).
        siguientes (dict): qué tareas esperan a cada una.

    Retorna:
        list: las tareas a las que ya no les falta ninguna dependencia.
    """
    liberadas = []
    for siguiente in siguientes[nombre]:
        pendientes[siguiente] -= 1
        if pendientes[siguiente] == 0:
            liberadas.append(siguiente)
    return liberadas


def clave_de_prioridad(tareas: Tareas, nombre: str) -> Tuple[int, str]:
    """
    Clave del heap: mayor prioridad primero; si empatan, por nombre.

    >>> clave_de_prioridad(TAREAS_EJEMPLO, "D")
    (-3, 'D')
    """
    return (tareas[nombre]["prioridad"], nombre)


# --- Orden de ejecución ---

def orden_lento(tareas: Tareas) -> Optional[List[str]]:
    """
    Versión lenta, solo para comparar: recorre todas las tareas cada vuelta.

    >>> orden_lento(TAREAS_EJEMPLO)
    ['A', 'B', 'C', 'D']
    """
    terminadas = set()
    orden: List[str] = []
    while len(orden) < len(tareas):
        disponibles = [
            nombre for nombre in tareas
            if nombre not in terminadas
            and all(a in terminadas for a in tareas[nombre]["depende_de"])
        ]
        if not disponibles:
            return None
        elegida = min(disponibles,
                      key=lambda nombre: clave_de_prioridad(tareas, nombre))
        orden.append(elegida)
        terminadas.add(elegida)
    return orden


def orden_rapido(tareas: Tareas) -> Optional[List[str]]:
    """
    Orden de ejecución con un heap: O(n + d).

    Parámetros:
        tareas (dict): las tareas a ordenar.

    Retorna:
        list: los nombres en orden de ejecución, o ``None`` si hay un ciclo.

    >>> orden_rapido(TAREAS_EJEMPLO)
    ['A', 'B', 'C', 'D']
    >>> ciclo = {"X": {"duracion": 1, "prioridad": 1, "depende_de": ["X"]}}
    >>> orden_rapido(ciclo)
    """
    pendientes, siguientes = preparar_grafo(tareas)
    listas = [clave_de_prioridad(tareas, n) for n in tareas
              if pendientes[n] == 0]
    heapq.heapify(listas)

    orden = []
    while listas:
        _, nombre = heapq.heappop(listas)
        orden.append(nombre)
        for liberada in liberar_siguientes(nombre, pendientes, siguientes):
            heapq.heappush(listas, clave_de_prioridad(tareas, liberada))

    return orden if len(orden) == len(tareas) else None


def niveles(tareas: Tareas) -> List[List[str]]:
    """
    Tareas agrupadas en niveles: las de un mismo nivel pueden ir juntas.

    >>> niveles(TAREAS_EJEMPLO)
    [['A'], ['B', 'C'], ['D']]
    """
    pendientes, siguientes = preparar_grafo(tareas)
    actual = sorted(n for n in tareas if pendientes[n] == 0)
    resultado = []
    while actual:
        resultado.append(actual)
        proximo = []
        for nombre in actual:
            proximo += liberar_siguientes(nombre, pendientes, siguientes)
        actual = sorted(proximo)
    return resultado


# --- Duración del plan ---

def duracion_minima(tareas: Tareas) -> float:
    """
    Duración sin límite de recursos (camino crítico).

    >>> duracion_minima(TAREAS_EJEMPLO)
    4.0
    """
    fin: Dict[str, float] = {}
    for nombre in orden_rapido(tareas) or []:
        anteriores = [fin[a] for a in tareas[nombre]["depende_de"]]
        fin[nombre] = max(anteriores, default=0) + tareas[nombre]["duracion"]
    return max(fin.values())


def cronograma(tareas: Tareas,
               recursos: Optional[int] = None) -> Dict[str, Tuple]:
    """
    Cuándo empieza y termina cada tarea, y en qué recurso corre.

    Parámetros:
        tareas (dict): las tareas a planificar.
        recursos (int): tareas a la vez; ``None`` es sin límite.

    Retorna:
        dict: para cada tarea, la tupla ``(inicio, fin, recurso)``.

    >>> cronograma(TAREAS_EJEMPLO, 1)["C"]
    (3.5, 4.5, 0)
    """
    if recursos is None:
        recursos = len(tareas)

    pendientes, siguientes = preparar_grafo(tareas)
    listas = [clave_de_prioridad(tareas, n) for n in tareas
              if pendientes[n] == 0]
    heapq.heapify(listas)

    libres = list(range(recursos))
    en_curso: List[Tuple[float, str, int]] = []
    resultado = {}
    reloj = 0.0
    while listas or en_curso:
        while listas and libres:
            _, nombre = heapq.heappop(listas)
            recurso = heapq.heappop(libres)
            fin = reloj + tareas[nombre]["duracion"]
            resultado[nombre] = (reloj, fin, recurso)
            heapq.heappush(en_curso, (fin, nombre, recurso))

        reloj, terminada, recurso = heapq.heappop(en_curso)
        heapq.heappush(libres, recurso)
        for liberada in liberar_siguientes(terminada, pendientes, siguientes):
            heapq.heappush(listas, clave_de_prioridad(tareas, liberada))
    return resultado


def duracion_con_recursos(tareas: Tareas,
                          recursos: Optional[int] = None) -> float:
    """
    Duración del plan con un límite de recursos.

    >>> duracion_con_recursos(TAREAS_EJEMPLO, 1)
    5.0
    >>> duracion_con_recursos(TAREAS_EJEMPLO, 2)
    4.0
    """
    if recursos is None:
        return duracion_minima(tareas)
    return max(fin for _, fin, _ in cronograma(tareas, recursos).values())


# --- Memoización y caché ---

def cuando_termina(tareas: Tareas, nombre: str) -> float:
    """
    Cuándo termina ``nombre``, sin memoria: repite cuentas, O(2^n).

    >>> cuando_termina(TAREAS_EJEMPLO, "D")
    4.0
    """
    anteriores = tareas[nombre]["depende_de"]
    inicio = max((cuando_termina(tareas, a) for a in anteriores), default=0)
    return inicio + tareas[nombre]["duracion"]


def cuando_termina_memo(tareas: Tareas, nombre: str) -> float:
    """
    Lo mismo con ``lru_cache``: cada tarea se calcula una vez.

    >>> cuando_termina_memo(TAREAS_EJEMPLO, "D")
    4.0
    """
    @lru_cache(maxsize=None)
    def resolver(actual: str) -> float:
        anteriores = tareas[actual]["depende_de"]
        inicio = max((resolver(a) for a in anteriores), default=0)
        return inicio + tareas[actual]["duracion"]

    return resolver(nombre)


planes_guardados: Dict[str, List[List[str]]] = {}


def plan_con_cache(nombre: str, tareas: Tareas) -> List[List[str]]:
    """Devuelve el plan guardado; si no está, lo calcula y lo guarda."""
    if nombre not in planes_guardados:
        planes_guardados[nombre] = niveles(tareas)
    return planes_guardados[nombre]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
