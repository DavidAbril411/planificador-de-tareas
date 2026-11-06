"""
Profiling de CPU: rechaza si orden_rapido deja de ganarle a orden_lento.

Guarda los dos perfiles de cProfile en reportes/ para verlos con SnakeViz.
"""

import cProfile
import pstats
import sys

import optimizaciones
import planificador as pl


def perfilar(funcion, tareas, salida):
    """Perfila una función y devuelve sus segundos totales."""
    perfil = cProfile.Profile()
    perfil.runcall(funcion, tareas)
    perfil.dump_stats(salida)
    return pstats.Stats(perfil).total_tt


if __name__ == "__main__":
    proyecto = optimizaciones.tareas_de_prueba(2000)
    lento = perfilar(pl.orden_lento, proyecto, "reportes/orden_lento.prof")
    rapido = perfilar(pl.orden_rapido, proyecto, "reportes/orden_rapido.prof")
    print(f"orden_lento {lento:.4f} s · orden_rapido {rapido:.4f} s")
    sys.exit(0 if rapido < lento else "RECHAZADO: orden_rapido no es más rápido")
