"""
Estimación de duraciones con IA (scikit-learn).

En una planta de producción, al cargar una tarea muchas veces no se sabe
cuánto va a durar. Se estima a partir del historial de tareas ya hechas, de
dos formas:

* sin IA: el promedio histórico de su tipo;
* con IA: un modelo de regresión que además mira la cantidad de unidades,
  los operarios y la máquina.

``comparar_estimadores`` mide las dos para decidir cuándo conviene la IA.
"""

import random
import time
import tracemalloc
from functools import lru_cache
from typing import Callable, Dict, List, Mapping, Tuple, TypedDict

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

TIPOS = ("corte", "soldadura", "pintura", "armado", "control")
MAQUINAS = ("vieja", "nueva")

# Minutos por unidad para un operario en la máquina nueva (los usa el
# historial sintético; los estimadores no los conocen).
MINUTOS_POR_UNIDAD = {"corte": 1.5, "soldadura": 4.0, "pintura": 2.5,
                      "armado": 3.0, "control": 0.8}
DEMORA_MAQUINA_VIEJA = 1.4


class Registro(TypedDict):
    """Una tarea del historial."""

    tipo: str
    cantidad: int
    operarios: int
    maquina: str
    duracion: float


def generar_historial(cantidad: int, semilla: int = 7) -> List[Registro]:
    """
    Historial sintético y reproducible de tareas ya hechas.

    La duración depende del tipo, de las unidades, de los operarios y de la
    máquina, más un 10 % de ruido, como en una planta real.
    """
    generador = random.Random(semilla)
    historial: List[Registro] = []
    for _ in range(cantidad):
        tipo = generador.choice(TIPOS)
        unidades = generador.randint(10, 200)
        operarios = generador.randint(1, 5)
        maquina = generador.choice(MAQUINAS)
        minutos = MINUTOS_POR_UNIDAD[tipo] * unidades / operarios
        if maquina == "vieja":
            minutos *= DEMORA_MAQUINA_VIEJA
        minutos *= generador.uniform(0.9, 1.1)
        historial.append({"tipo": tipo, "cantidad": unidades,
                          "operarios": operarios, "maquina": maquina,
                          "duracion": round(minutos, 1)})
    return historial


def caracteristicas(tarea: Mapping) -> List[float]:
    """Convierte una tarea en números: tipo y máquina en one-hot."""
    fila = [1.0 if tarea["tipo"] == tipo else 0.0 for tipo in TIPOS]
    fila += [float(tarea["cantidad"]), float(tarea["operarios"]),
             1.0 if tarea["maquina"] == "vieja" else 0.0,
             float(tarea["cantidad"]) / float(tarea["operarios"])]
    return fila


# ---------------------------------------------------------------------------
#  Sin IA: promedio por tipo
# ---------------------------------------------------------------------------

def entrenar_promedio(historial: List[Registro]) -> Dict[str, float]:
    """Duración promedio de cada tipo. Entrenar es O(n); estimar, O(1)."""
    sumas: Dict[str, float] = {}
    cuentas: Dict[str, int] = {}
    for registro in historial:
        tipo = registro["tipo"]
        sumas[tipo] = sumas.get(tipo, 0.0) + registro["duracion"]
        cuentas[tipo] = cuentas.get(tipo, 0) + 1
    return {tipo: suma / cuentas[tipo] for tipo, suma in sumas.items()}


# ---------------------------------------------------------------------------
#  Con IA: bosque aleatorio de regresión
# ---------------------------------------------------------------------------

def entrenar_modelo(historial: List[Registro]) -> RandomForestRegressor:
    """Entrena un RandomForestRegressor con el historial."""
    modelo = RandomForestRegressor(n_estimators=60, max_depth=12,
                                   random_state=0, n_jobs=1)
    modelo.fit([caracteristicas(r) for r in historial],
               [r["duracion"] for r in historial])
    return modelo


@lru_cache(maxsize=1)
def estimadores() -> Tuple[Dict[str, float], RandomForestRegressor]:
    """Los dos estimadores ya entrenados; se entrenan una sola vez (caché)."""
    historial = generar_historial(4000)
    return entrenar_promedio(historial), entrenar_modelo(historial)


def estimar(tarea: Mapping) -> Dict[str, float]:
    """
    Duración estimada de una tarea, en minutos, con y sin IA.

    Parámetros:
        tarea (dict): ``tipo``, ``cantidad``, ``operarios`` y ``maquina``.

    Retorna:
        dict: ``con_ia`` y ``sin_ia``.
    """
    promedio, modelo = estimadores()
    con_ia = float(modelo.predict([caracteristicas(tarea)])[0])
    return {"con_ia": round(con_ia, 1),
            "sin_ia": round(promedio[tarea["tipo"]], 1)}


# ---------------------------------------------------------------------------
#  Comparación medida
# ---------------------------------------------------------------------------

def medir(entrenar: Callable, predecir: Callable,
          historial: List[Registro], nuevas: List[Registro]) -> Dict:
    """Error, segundos de entrenamiento, µs por estimación y memoria (MB)."""
    tracemalloc.start()
    inicio = time.perf_counter()
    estimador = entrenar(historial)
    segundos_entrenar = time.perf_counter() - inicio
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    inicio = time.perf_counter()
    predichas = predecir(estimador, nuevas)
    por_estimacion = (time.perf_counter() - inicio) / len(nuevas)
    reales = [r["duracion"] for r in nuevas]
    return {"mae": mean_absolute_error(reales, predichas),
            "entrenar_s": segundos_entrenar,
            "estimar_us": por_estimacion * 1_000_000,
            "memoria_mb": pico / 1024 / 1024}


def comparar_estimadores(entrenamiento: int = 4000,
                         prueba: int = 1000) -> Dict[str, Dict]:
    """
    Mide los dos estimadores sobre tareas que no vieron al entrenar.

    Retorna:
        dict: para ``sin_ia`` y ``con_ia``, el error medio absoluto en
        minutos (``mae``), ``entrenar_s``, ``estimar_us`` y ``memoria_mb``.
    """
    historial = generar_historial(entrenamiento)
    nuevas = generar_historial(prueba, semilla=99)
    return {
        "sin_ia": medir(
            entrenar_promedio,
            lambda promedio, tareas: [promedio[t["tipo"]] for t in tareas],
            historial, nuevas),
        "con_ia": medir(
            entrenar_modelo,
            lambda modelo, tareas: list(modelo.predict(
                [caracteristicas(t) for t in tareas])),
            historial, nuevas),
    }


if __name__ == "__main__":
    for clave, valores in comparar_estimadores().items():
        print(clave, {k: round(v, 3) for k, v in valores.items()})
