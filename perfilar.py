"""
Programa corto para los perfiladores (Scalene, SnakeViz y py-spy).

Corre a propósito la versión lenta y la rápida del orden, para comparar.
"""

import os
import tempfile

import archivos
import planificador as pl
from optimizaciones import tareas_de_prueba as tareas_al_azar


def main() -> None:
    """Las partes más pesadas: el orden lento y el archivo grande."""
    pl.orden_lento(tareas_al_azar(2000))
    pl.orden_rapido(tareas_al_azar(200_000))

    ruta = os.path.join(tempfile.gettempdir(), "perfilar_parcial2.txt")
    archivos.escribir_por_lotes(ruta, tareas_al_azar(300_000))
    archivos.procesar_secuencial(ruta)
    os.remove(ruta)


if __name__ == "__main__":
    main()
